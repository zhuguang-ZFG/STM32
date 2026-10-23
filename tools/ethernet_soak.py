#!/usr/bin/env python3
"""Deadline-bounded TCP echo soak runner and fault-injection peer.

Wire format: magic ``ST32``, payload length, sequence, client monotonic ns,
followed by a deterministic payload. The server echoes the exact frame.
JSONL records are append-only and contain no credentials or customer payloads.
"""

from __future__ import annotations

import argparse
import json
import socket
import struct
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

MAGIC = b"ST32"
HEADER = struct.Struct("!4sIQQ")
MAX_PAYLOAD = 64 * 1024


@dataclass
class ProbeFailure(Exception):
    stage: str
    reason: str

    def __str__(self) -> str:
        return f"{self.stage}: {self.reason}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def remaining(deadline: float) -> float:
    value = deadline - time.monotonic()
    if value <= 0:
        raise ProbeFailure("deadline", "expired")
    return value


def send_all(sock: socket.socket, data: bytes, deadline: float) -> None:
    view = memoryview(data)
    while view:
        sock.settimeout(remaining(deadline))
        try:
            count = sock.send(view)
        except socket.timeout as exc:
            raise ProbeFailure("send", "timeout") from exc
        except OSError as exc:
            raise ProbeFailure("send", f"{exc.__class__.__name__}:{exc.errno}") from exc
        if count == 0:
            raise ProbeFailure("send", "peer_closed")
        view = view[count:]


def recv_exact(sock: socket.socket, size: int, deadline: float) -> bytes:
    chunks: list[bytes] = []
    received = 0
    while received < size:
        sock.settimeout(remaining(deadline))
        try:
            chunk = sock.recv(size - received)
        except socket.timeout as exc:
            raise ProbeFailure("receive", "timeout") from exc
        except OSError as exc:
            raise ProbeFailure("receive", f"{exc.__class__.__name__}:{exc.errno}") from exc
        if not chunk:
            raise ProbeFailure("receive", "peer_closed")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def payload_for(sequence: int, size: int) -> bytes:
    return bytes(((sequence + index * 17) & 0xFF) for index in range(size))


def frame_for(sequence: int, payload_size: int, started_ns: int) -> bytes:
    payload = payload_for(sequence, payload_size)
    return HEADER.pack(MAGIC, len(payload), sequence, started_ns) + payload


def read_frame(sock: socket.socket, deadline: float) -> tuple[int, bytes]:
    header = recv_exact(sock, HEADER.size, deadline)
    magic, payload_size, sequence, _started_ns = HEADER.unpack(header)
    if magic != MAGIC:
        raise ProbeFailure("protocol", "bad_magic")
    if payload_size > MAX_PAYLOAD:
        raise ProbeFailure("protocol", "payload_too_large")
    return sequence, header + recv_exact(sock, payload_size, deadline)


def probe_once(host: str, port: int, sequence: int, payload_size: int,
               timeout: float) -> float:
    began = time.monotonic()
    deadline = began + timeout
    frame = frame_for(sequence, payload_size, time.monotonic_ns())
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(remaining(deadline))
        try:
            sock.connect((host, port))
        except socket.timeout as exc:
            raise ProbeFailure("connect", "timeout") from exc
        except OSError as exc:
            raise ProbeFailure("connect", f"{exc.__class__.__name__}:{exc.errno}") from exc
        send_all(sock, frame, deadline)
        echoed = recv_exact(sock, len(frame), deadline)
        if echoed != frame:
            raise ProbeFailure("protocol", "echo_mismatch")
        return (time.monotonic() - began) * 1000.0
    finally:
        sock.close()


def append_jsonl(handle: BinaryIO, record: dict) -> None:
    handle.write((json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    handle.flush()


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return round(ordered[index], 3)

def run_probe(args: argparse.Namespace) -> int:
    log_path = Path(args.log)
    summary_path = Path(args.summary)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    started_utc = utc_now()
    stop_at = started + args.duration
    sequence = 0
    successes = 0
    failures: dict[str, int] = {}
    latencies: list[float] = []

    with log_path.open("ab") as log:
        while time.monotonic() < stop_at:
            sequence += 1
            attempt_started = time.monotonic()
            record = {
                "utc": utc_now(),
                "monotonic_ns": time.monotonic_ns(),
                "sequence": sequence,
                "target": f"{args.host}:{args.port}",
                "timeout_ms": round(args.timeout * 1000),
                "payload_bytes": args.payload_size,
            }
            try:
                latency_ms = probe_once(
                    args.host, args.port, sequence, args.payload_size, args.timeout
                )
                record.update(result="ok", latency_ms=round(latency_ms, 3))
                latencies.append(latency_ms)
                successes += 1
            except ProbeFailure as exc:
                key = f"{exc.stage}:{exc.reason}"
                failures[key] = failures.get(key, 0) + 1
                record.update(result="error", stage=exc.stage, reason=exc.reason)
            append_jsonl(log, record)

            next_attempt = attempt_started + args.interval
            delay = next_attempt - time.monotonic()
            if delay > 0:
                time.sleep(min(delay, max(0.0, stop_at - time.monotonic())))

    summary = {
        "started_utc": started_utc,
        "duration_s": round(time.monotonic() - started, 3),
        "target": f"{args.host}:{args.port}",
        "attempts": sequence,
        "successes": successes,
        "failures": failures,
        "latency_ms": {
            "min": round(min(latencies), 3) if latencies else None,
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "max": round(max(latencies), 3) if latencies else None,
        },
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if successes > 0 else 1


def handle_server_client(client: socket.socket, peer: tuple[str, int],
                         connection_id: int, args: argparse.Namespace) -> None:
    deadline = time.monotonic() + args.timeout
    result = "echo"
    try:
        if args.close_every and connection_id % args.close_every == 0:
            result = "injected_close"
            return
        _sequence, frame = read_frame(client, deadline)
        if args.stall_every and connection_id % args.stall_every == 0:
            result = "injected_stall"
            time.sleep(args.stall_seconds)
            return
        if args.delay_every and connection_id % args.delay_every == 0:
            result = "injected_delay"
            time.sleep(args.delay_ms / 1000.0)
        send_all(client, frame, deadline)
    except ProbeFailure as exc:
        result = str(exc)
    finally:
        client.close()
        print(json.dumps({
            "utc": utc_now(), "connection": connection_id,
            "peer": peer[0], "result": result,
        }, sort_keys=True), flush=True)


def run_server(args: argparse.Namespace) -> int:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((args.bind, args.port))
    listener.listen(args.backlog)
    actual_port = listener.getsockname()[1]
    print(json.dumps({"event": "ready", "bind": args.bind, "port": actual_port}), flush=True)
    connection_id = 0
    finite_threads: list[threading.Thread] = []
    try:
        while args.max_connections == 0 or connection_id < args.max_connections:
            client, peer = listener.accept()
            connection_id += 1
            thread = threading.Thread(
                target=handle_server_client,
                args=(client, peer, connection_id, args),
                daemon=args.max_connections == 0,
            )
            thread.start()
            if args.max_connections:
                finite_threads.append(thread)
    finally:
        listener.close()
    for thread in finite_threads:
        thread.join()
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    probe = commands.add_parser("probe", help="run a deadline-bounded soak against an echo target")
    probe.add_argument("--host", required=True)
    probe.add_argument("--port", type=int, required=True)
    probe.add_argument("--duration", type=float, default=86_400.0)
    probe.add_argument("--interval", type=float, default=1.0)
    probe.add_argument("--timeout", type=float, default=2.0)
    probe.add_argument("--payload-size", type=int, default=256)
    probe.add_argument("--log", default="ethernet-soak.jsonl")
    probe.add_argument("--summary", default="ethernet-soak-summary.json")

    serve = commands.add_parser("serve", help="echo frames and inject deterministic peer faults")
    serve.add_argument("--bind", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=9000)
    serve.add_argument("--backlog", type=int, default=8)
    serve.add_argument("--timeout", type=float, default=5.0)
    serve.add_argument("--max-connections", type=int, default=0)
    serve.add_argument("--close-every", type=int, default=0)
    serve.add_argument("--stall-every", type=int, default=0)
    serve.add_argument("--stall-seconds", type=float, default=3.0)
    serve.add_argument("--delay-every", type=int, default=0)
    serve.add_argument("--delay-ms", type=float, default=250.0)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "probe":
        if not 0 <= args.payload_size <= MAX_PAYLOAD:
            raise SystemExit(f"payload size must be 0..{MAX_PAYLOAD}")
        if args.duration <= 0 or args.interval <= 0 or args.timeout <= 0:
            raise SystemExit("duration, interval, and timeout must be positive")
        return run_probe(args)
    return run_server(args)


if __name__ == "__main__":
    sys.exit(main())
