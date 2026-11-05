#!/usr/bin/env python3
"""device-console.py —— 双板串口协议主机工具（knowledge-reliability 任务）。

线上格式与 code/common/reliability/protocol.* 完全一致，但本文件的 codec 是
独立实现（CRC 用 binascii.crc_hqx 充当第三方法典），供互相交叉验证：

    线上帧 = COBS(raw) + 0x00
    raw    = version:u8=1 | type:u8 | sequence:u16LE | length:u16LE
             | payload[0..64] | crc:u16LE（CRC-16/CCITT-FALSE，覆盖 CRC 之前的全部 raw 字节）

命令：
    self-test              离线自测（标准库，不碰串口）；--c-helper 附加 C↔Python 交叉验证
    info                   连接后先发 INFO，打印 schema/platform/能力位
    status                 先 INFO（拿平台号）再 STATUS，打印运行状态与复位原因
    command --type N       发送任意请求（默认单次尝试，不自动重试）
    fault --fault N        发送 TEST_FAULT(0x7f)，仅测试固件支持，绝不自动重试
    log                    只收不发，持续解码并落 CSV，直到 Ctrl+C

公共参数：--port（必填，不做自动探测）、--baud（默认 115200）、
--timeout（单次尝试期限，秒）、--output（CSV 日志路径）。

退出码：0 成功；1 自测/用法失败；2 设备拒绝（status != OK）；3 超时；4 串口错误。
响应超时不算成功；重试前先补发一个同步分隔符 0x00；响应必须同时匹配
sequence 与 response type，无关帧只记日志、不延长等待期限。
开口不主动拉 RTS/DTR 复位（保持两者非有效），但部分 USB 转串口驱动在
打开瞬间仍可能产生毫秒级瞬态——上电顺序与复位行为以上板实测为准。
"""

import argparse
import json
import math
import binascii
import csv
import os
import struct
import subprocess
import sys
import time

PAYLOAD_MAX = 64
RAW_MAX = 72          # 6 头 + 64 负载 + 2 CRC
ENCODED_MAX = 73      # COBS 后（raw <= 72 < 254，开销恒为 1）
WIRE_MAX = 74         # 含结尾分隔符

TYPE_INFO = 0x01
TYPE_STATUS = 0x02
TYPE_TEST_FAULT = 0x7F
RESPONSE_FLAG = 0x80

STATUS_OK = 0
STATUS_NAMES = {0: "OK", 1: "UNSUPPORTED", 2: "BAD_PAYLOAD", 3: "BUSY", 4: "INTERNAL_ERROR"}

EXIT_OK, EXIT_SELFTEST, EXIT_REJECTED, EXIT_TIMEOUT, EXIT_SERIAL = 0, 1, 2, 3, 4

INFO_SCHEMA = 1
PLATFORM_NAMES = {1: "STM32F407", 2: "ESP32-S3"}
CAPABILITIES = ((1 << 3, "logger"), (1 << 0, "protocol"), (1 << 1, "health"), (1 << 2, "test_fault"))
STATUS_SCHEMA = 1
STATUS_FLAGS = ((1 << 0, "grace"), (1 << 1, "restart_latched"))


class FrameError(Exception):
    """解码失败；携带与人对照的简短原因。"""


def crc16(data):
    """CRC-16/CCITT-FALSE（poly=0x1021, init=0xffff, 不反射，xorout=0）。

    binascii.crc_hqx 是标准库里的独立 CCITT 实现，与 C 版互为第三方法典；
    检查串 "123456789" 必须得到 0x29b1。
    """
    return binascii.crc_hqx(bytes(data), 0xFFFF)


def cobs_encode(data):
    """返回 COBS 编码；输入<=RAW_MAX，输出长度 = 输入长度+1（本协议范围内）。"""
    raw = bytes(data)
    if len(raw) > RAW_MAX:
        raise FrameError("cobs: raw too long")
    out = bytearray([1])
    code_at = 0
    for byte in raw:
        if byte == 0:
            out[code_at] = len(out) - code_at
            code_at = len(out)
            out.append(1)
        else:
            out.append(byte)
    out[code_at] = len(out) - code_at
    return bytes(out)


def cobs_decode(data):
    """COBS 解码；任何非法布局抛 FrameError。"""
    src = bytes(data)
    if not src or len(src) > ENCODED_MAX:
        raise FrameError("cobs: size")
    out = bytearray()
    pos = 0
    while pos < len(src):
        code = src[pos]
        pos += 1
        if code == 0 or (code - 1) > len(src) - pos:
            raise FrameError("cobs: code block")
        chunk = src[pos:pos + code - 1]
        pos += len(chunk)
        if 0 in chunk:
            raise FrameError("cobs: zero inside block")
        out += chunk
        if code != 0xFF and pos < len(src):
            out.append(0)
    return bytes(out)


def build_frame(frame_type, sequence, payload):
    """构造完整线上帧（含结尾分隔符）。任何非法输入在此拒绝。"""
    payload = bytes(payload)
    if frame_type < 1 or frame_type > 0xFF:
        raise FrameError("type out of range")
    if not 0 <= sequence <= 0xFFFF:
        raise FrameError("sequence out of range")
    if len(payload) > PAYLOAD_MAX:
        raise FrameError("payload too long")
    raw = bytearray(struct.pack("<BBHH", 1, frame_type, sequence, len(payload)))
    raw += payload
    raw += struct.pack("<H", crc16(raw))
    return cobs_encode(raw) + b"\x00"


def parse_frame(segment):
    """解码一段无分隔符的 COBS 字节；返回 dict，失败抛 FrameError。"""
    raw = cobs_decode(segment)
    if len(raw) < 8:
        raise FrameError("short raw")
    version, frame_type, sequence, length = struct.unpack("<BBHH", raw[:6])
    if version != 1:
        raise FrameError("version")
    if length > PAYLOAD_MAX or len(raw) != length + 8:
        raise FrameError("length")
    if struct.unpack("<H", raw[6 + length:8 + length])[0] != crc16(raw[:6 + length]):
        raise FrameError("crc")
    return {
        "type": frame_type, "sequence": sequence, "length": length,
        "payload": raw[6:6 + length],
    }


def frame_wire(frame):
    """frame dict -> 线上帧（测试与交叉验证用）。"""
    return build_frame(frame["type"], frame["sequence"], frame["payload"])


class FrameLogger:
    """CSV 日志：time, direction, type, sequence, payload_hex, note。csv 模块自动转义。"""

    def __init__(self, path):
        self.path = path
        self._new = not (path and os.path.exists(path) and os.path.getsize(path) > 0)
        self._fh = open(path, "a", newline="", encoding="utf-8") if path else None
        if self._fh and self._new:
            csv.writer(self._fh).writerow(
                ["time", "direction", "type", "sequence", "payload_hex", "note"])

    def write(self, direction, frame_or_none, note, segment=b""):
        if not self._fh:
            return
        frame = frame_or_none or {}
        csv.writer(self._fh).writerow([
            f"{time.time():.3f}", direction, frame.get("type", ""),
            frame.get("sequence", ""), bytes(segment).hex(), note])

    def close(self):
        if self._fh:
            self._fh.close()


class StreamParser:
    """按 0x00 分段解码的接收侧。残段留在缓冲；完整段解码后无论成败都清掉。

    与固件侧协议解析的差别：CLI 是主动读方，不存在字节级超时状态机；
    分段语义与 code/common/reliability 的 EMPTY/COLLECT/DISCARD 等价——
    一个分隔符一个段，坏段丢弃并记原因，不把坏段尾部拼进下一帧。
    """

    def __init__(self, on_frame):
        self.on_frame = on_frame
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer += bytes(data)
        while True:
            idx = self.buffer.find(0)
            if idx < 0:
                break
            segment = bytes(self.buffer[:idx])
            del self.buffer[:idx + 1]
            if not segment:
                self.on_frame(None, "sync-delimiter", segment)
                continue
            try:
                self.on_frame(parse_frame(segment), "ok", segment)
            except FrameError as exc:
                self.on_frame(None, str(exc), segment)


class Transport:
    """串口子命令共用的收发面；自测里用 FakeTransport 注入脚本化对端。"""

    def __init__(self, port, baud, logger):
        import serial  # 仅串口子命令才加载 pyserial（离线自测不 import）
        try:
            # rts/dtr 显式置低：不主动拉复位线（见模块 docstring 的驱动瞬态说明）
            self.ser = serial.Serial(port=port, baudrate=baud, timeout=0.02,
                                     write_timeout=0.5, rts=False, dtr=False)
        except Exception as exc:  # noqa: BLE001 —— 统一成串口错误退出码
            raise SerialError(f"打开 {port} 失败: {exc}") from exc
        self.logger = logger
        self.parser = StreamParser(self._on_frame)
        self.received = []          # (frame, note)
        self.pending = None         # 当前挂起请求 (type, sequence)

    def _on_frame(self, frame, note, segment):
        self.logger.write("rx", frame, note, segment)
        if frame is not None:
            self.received.append((frame, note))
        # 响应类型帧交还上层匹配；无关帧只留日志
        self.last_frame = (frame, note)

    def write(self, data, note=""):
        self.ser.write(bytes(data))
        self.logger.write("tx", None, note, bytes(data))

    def wait_response(self, req_type, sequence, deadline):
        """在绝对期限内等 (type|0x80, sequence) 的响应；无关帧不延长期限。"""
        want = req_type | RESPONSE_FLAG
        while time.monotonic() < deadline:
            data = self.ser.read(256)
            if data:
                self.parser.feed(data)
            for frame, _note in self.received:
                if frame["sequence"] == sequence and frame["type"] == want:
                    self.received.clear()
                    self.pending = None
                    return frame
            self.received.clear()
        self.pending = None
        return None

    def request(self, req_type, payload, timeout, retries):
        """一次挂一个请求；info/status 有限重试且重试前补同步分隔符。"""
        sequence = self.next_seq
        self.next_seq = (self.next_seq + 1) & 0xFFFF
        wire = build_frame(req_type, sequence, payload)
        for attempt in range(retries + 1):
            if attempt:
                self.write(b"\x00", "sync")
            self.pending = (req_type, sequence)
            self.received.clear()
            self.write(wire, f"request attempt {attempt + 1}/{retries + 1}")
            frame = self.wait_response(req_type, sequence, time.monotonic() + timeout)
            if frame is not None:
                return frame
        raise TimeoutError(f"type 0x{req_type:02x} seq {sequence} 在 {retries + 1} 次尝试内无匹配响应")

    def reconnect(self):
        """重连：废弃旧挂起请求，残余半段清空。"""
        self.pending = None
        self.parser.buffer.clear()
        self.received.clear()

    def close(self):
        self.ser.close()
        self.logger.close()


class SerialError(Exception):
    pass


class FakeTransport:
    """脚本化对端：recorded_writes 记录主机写序，responses 是 (delay, bytes) 队列。"""

    def __init__(self, script):
        self.script = list(script)
        self.recorded_writes = []
        self.ser = self  # Device 复用同一读取面
        self.logger = FrameLogger(None)
        self.parser = StreamParser(self._on_frame)
        self.received = []
        self.last_frame = (None, "")
        self.next_seq = 0
        self.pending = None

    def _on_frame(self, frame, note, segment):
        self.last_frame = (frame, note)
        if frame is not None:
            self.received.append((frame, note))

    def write(self, data, note=""):
        self.recorded_writes.append(bytes(data))
        self.parser.feed(bytes(data))       # 回环：主机发的请求也进解析器（真实串口不会，但无妨）

    def read(self, size):
        if not self.script:
            return b""
        delay, data = self.script[0]
        if delay:
            time.sleep(delay)
        self.script.pop(0)
        return data

    def wait_response(self, req_type, sequence, deadline):
        want = req_type | RESPONSE_FLAG
        while time.monotonic() < deadline:
            data = self.read(256)
            if data:
                self.parser.feed(data)
            for frame, _note in self.received:
                if frame["sequence"] == sequence and frame["type"] == want:
                    self.received.clear()
                    self.pending = None
                    return frame
            self.received.clear()
        self.pending = None
        return None

    def request(self, req_type, payload, timeout, retries):
        sequence = self.next_seq
        self.next_seq = (self.next_seq + 1) & 0xFFFF
        wire = build_frame(req_type, sequence, payload)
        for attempt in range(retries + 1):
            if attempt:
                self.write(b"\x00", "sync")
            self.pending = (req_type, sequence)
            self.received.clear()
            self.write(wire, f"request attempt {attempt + 1}/{retries + 1}")
            frame = self.wait_response(req_type, sequence, time.monotonic() + timeout)
            if frame is not None:
                return frame
        raise TimeoutError("no response")

    def reconnect(self):
        self.pending = None
        self.parser.buffer.clear()
        self.received.clear()


def device_session(args):
    """打开真实串口的会话；非串口子命令不会走到这里。"""
    return Transport(args.port, args.baud, FrameLogger(args.output))


# ---------------------------------------------------------------- self-test

def vector_payloads():
    """确定性向量：全长度 + 关键边界值，伪随机来自固定种子 LCG（与 C 测试同族）。"""
    payloads = []
    state = 0x1BADF00D
    for length in range(PAYLOAD_MAX + 1):
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        data = bytearray((state >> (8 * (i % 4))) & 0xFF for i in range(length))
        if length > 2:
            data[length // 2] = 0        # 负载内嵌零：COBS 关键路径
        if length > 5:
            data[3] = 0xFF
        payloads.append(bytes(data))
    return payloads


def self_test(helper=None):
    failures = []

    def check(name, condition):
        if not condition:
            failures.append(name)

    # 1) CRC 第三方法典：检查串必须 0x29b1
    check("crc check value", crc16(b"123456789") == 0x29B1)

    # 2) 全长度往返 + 线长公式 + 结尾分隔符
    for seq in (0, 1, 65535):
        for payload in vector_payloads():
            wire = build_frame(TYPE_INFO, seq, payload)
            check(f"wire tail seq={seq} len={len(payload)}", wire[-1] == 0)
            raw_len = len(payload) + 8
            check(f"wire len seq={seq} len={len(payload)}",
                  len(wire) == raw_len + 1 + 1)  # raw + COBS 开销1 + 分隔符1（raw<=72）
            frame = parse_frame(wire[:-1])
            check(f"roundtrip type seq={seq}", frame["type"] == TYPE_INFO)
            check(f"roundtrip seq seq={seq}", frame["sequence"] == seq)
            check(f"roundtrip payload seq={seq} len={len(payload)}",
                  frame["payload"] == payload)

    # 3) 序号回绕：65535 -> 0（模 65536）
    wire = build_frame(TYPE_INFO, 65535, b"")
    frame = parse_frame(wire[:-1])
    check("seq wrap encode", frame["sequence"] == 65535)

    # 4) 坏帧拒绝：CRC/版本/长度/截断/超长。坏帧从原始字节构造再重编码，位置确定。
    good = build_frame(TYPE_INFO, 7, b"\x01\x02\x03")
    raw = bytearray(struct.pack("<BBHH", 1, TYPE_INFO, 7, 3)) + b"\x01\x02\x03"
    raw += struct.pack("<H", crc16(raw))
    bad_crc = bytearray(raw)
    bad_crc[-1] ^= 1
    check("crc error", _expect_error(cobs_encode(bad_crc), "crc"))
    bad_version = bytearray(raw)
    bad_version[0] = 2
    check("version error", _expect_error(cobs_encode(bad_version), "version"))
    bad_length = bytearray(raw)
    bad_length[4] = 65
    check("length error", _expect_error(cobs_encode(bad_length), "length"))
    check("truncated error", _expect_error(good[:6], "any"))
    check("cobs zero inside block", _expect_error(bytes([2, 0, 3]), "any"))
    oversized = build_frame(TYPE_INFO, 7, bytes(PAYLOAD_MAX))
    check("payload max ok", parse_frame(oversized[:-1])["length"] == PAYLOAD_MAX)

    # 5) 会话行为：无关响应不延长期限（有期限上限证明）
    correct = frame_wire({"type": TYPE_INFO | RESPONSE_FLAG, "sequence": 0, "payload": b"\x00"})
    wrong = frame_wire({"type": TYPE_STATUS | RESPONSE_FLAG, "sequence": 0, "payload": b"\x00"})
    fake = FakeTransport([(0.0, wrong), (0.05, correct)])
    started = time.monotonic()
    frame = fake.request(TYPE_INFO, b"", timeout=1.0, retries=0)
    elapsed = time.monotonic() - started
    check("unrelated frame no match", frame["type"] == TYPE_INFO | RESPONSE_FLAG)
    check("deadline not extended", elapsed < 0.95)  # 若无关帧延期，elapsed 会超过 1.0s

    # 6) 错 type/sequence 拒绝匹配 → 超时
    fake = FakeTransport([(0.0, correct)])
    try:
        fake.request(TYPE_STATUS, b"", timeout=0.2, retries=0)
        check("wrong type must timeout", False)
    except TimeoutError:
        check("wrong type must timeout", True)

    # 7) INFO/STATUS 有限重试；重试前补同步 0x00
    fake = FakeTransport([(0.3, b""), (0.3, b""), (0.0, correct)])
    frame = fake.request(TYPE_INFO, b"", timeout=0.25, retries=2)
    check("retry then succeed", frame["type"] == TYPE_INFO | RESPONSE_FLAG)
    writes = fake.recorded_writes
    check("sync before retry", writes[1] == b"\x00")
    check("attempt count", sum(1 for w in writes if w != b"\x00") == 3)

    # 8) 序号 65535 -> 0 回绕 + 重连废弃旧挂起
    fake = FakeTransport([])
    fake.next_seq = 65535
    try:
        fake.request(TYPE_INFO, b"", timeout=0.05, retries=0)
    except TimeoutError:
        pass
    check("seq wraps 65535->0", fake.next_seq == 0)
    fake.reconnect()
    check("reconnect clears pending", fake.pending is None)

    # 9) fault 绝不自动重试（单次尝试）
    fake = FakeTransport([])
    try:
        fake.request(TYPE_TEST_FAULT, b"\x01\x00", timeout=0.1, retries=0)
        check("fault single attempt", False)
    except TimeoutError:
        check("fault single attempt", True)

    # 10) C↔Python 交叉验证：C 编→Python 解，Python 编→C 解
    if helper:
        _c_cross_check(helper, failures)

    if failures:
        for name in failures:
            print(f"self-test FAIL: {name}", file=sys.stderr)
        return False
    print("self-test passed: codec vectors + session matching + sync/retry"
          + (" + C cross-validation" if helper else ""))
    return True


def _expect_error(wire_segment, reason):
    try:
        parse_frame(wire_segment)
        return False
    except FrameError as exc:
        return str(exc) == reason or reason == "any"


def _c_cross_check(helper, failures):
    env_vectors = [(TYPE_INFO, 1, bytes(range(4))), (TYPE_INFO, 65535, b"\x00\xff\x00"),
                   (TYPE_STATUS, 0, bytes(range(PAYLOAD_MAX))),
                   (TYPE_TEST_FAULT, 3, b"\x01\x01"), (TYPE_INFO, 0, b"")]
    for frame_type, seq, payload in env_vectors:
        proc = subprocess.run([helper, "encode", str(frame_type), str(seq), payload.hex()],
                              capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            failures.append(f"c-helper encode rc={proc.returncode}")
            continue
        c_wire = bytes.fromhex(proc.stdout.strip())
        try:
            frame = parse_frame(c_wire[:-1])
        except FrameError as exc:
            failures.append(f"c encode -> py decode: {exc}")
            continue
        if frame["type"] != frame_type or frame["sequence"] != seq \
                or frame["payload"] != payload:
            failures.append(f"c encode -> py decode mismatch ({frame_type},{seq})")
        py_wire = build_frame(frame_type, seq, payload)
        if py_wire != c_wire:
            failures.append(f"wire mismatch py-vs-c ({frame_type},{seq}): "
                            f"{py_wire.hex()} != {c_wire.hex()}")
        proc = subprocess.run([helper, "decode", py_wire.hex()],
                              capture_output=True, text=True, timeout=10)
        expected = f"{frame_type} {seq} {payload.hex()}".strip()
        if proc.returncode != 0 or proc.stdout.strip() != expected:
            failures.append(f"py encode -> c decode mismatch ({frame_type},{seq}): "
                            f"rc={proc.returncode} out={proc.stdout.strip()!r}")


# ---------------------------------------------------------------- decoding

def parse_tlvs(payload, offset):
    fields = {}
    while offset < len(payload):
        if offset + 2 > len(payload):
            raise FrameError("truncated TLV header")
        tag, length = payload[offset:offset+2]
        offset += 2
        if offset + length > len(payload):
            raise FrameError("truncated TLV value")
        fields[tag] = payload[offset:offset+length]
        offset += length
    return fields


def describe_logger_tlvs(payload, offset):
    fields = parse_tlvs(payload, offset)
    result = []
    if 1 in fields and len(fields[1]) == 2:
        sensor, running = fields[1]
        result.append(f"sensor={sensor} running={bool(running)}")
    if 2 in fields and len(fields[2]) == 13:
        schema, period, shift, generation, saved = struct.unpack("<HHBII", fields[2])
        result.append(f"config schema={schema} period={period}ms shift={shift} generation={generation} saved={saved}")
    if 3 in fields and len(fields[3]) == 18:
        samples, dropped, sensor_error, storage_error, high = struct.unpack("<IIIIH", fields[3])
        result.append(f"samples={samples} dropped={dropped} sensor_error={sensor_error} storage_error={storage_error} queue_high={high}")
    if 4 in fields and len(fields[4]) == 8:
        acc, gyro = struct.unpack("<II", fields[4])
        result.append(f"raw scale divisors={acc}/{gyro} (ADC uses raw counts)")
    if 5 in fields and len(fields[5]) == 5:
        valid, mask = struct.unpack("<BI", fields[5])
        result.append(f"previous fault valid={bool(valid)} mask={mask:#x}")
    return "\n  ".join(result)


def parse_sample(payload):
    if len(payload) != 64:
        raise FrameError("SAMPLE must contain exactly 64 bytes")
    values = struct.unpack("<IIIBBH6i6i", payload)
    return dict(sequence=values[0], timestamp_ms=values[1], generation=values[2],
                sensor=values[3], valid_mask=values[4], status=values[5],
                raw=list(values[6:12]), filtered=list(values[12:18]))


def run_logger_control(args):
    kind = dict(start=3, stop=4, configure=5, save=6)[args.command]
    payload = b""
    if kind == 5:
        if not (100 <= args.period <= 1000 and args.period % 10 == 0 and 0 <= args.filter_shift <= 6):
            raise FrameError("period must be 100..1000ms in 10ms steps; filter-shift 0..6")
        payload = struct.pack("<BHB", 1, args.period, args.filter_shift)
    transport = device_session(args)
    try:
        frame = transport.request(kind, payload, args.timeout, retries=0)
        code = frame["payload"][0] if frame["payload"] else None
        print(f"{args.command}: {STATUS_NAMES.get(code, code)} payload={frame['payload'].hex()}")
        return EXIT_OK if code == 0 else EXIT_REJECTED
    finally:
        transport.close()


def run_record(args):
    if not math.isfinite(args.seconds) or args.seconds <= 0 or not args.output:
        raise FrameError("record requires --output and positive --seconds")
    # Keep the decoded CSV separate from the existing raw-frame logging format.
    target = args.output
    args.output = None
    transport = device_session(args)
    count = 0
    try:
        with open(target, "w", newline="", encoding="utf-8") as f:
            columns = ["sequence", "timestamp_ms", "generation", "sensor", "valid_mask", "status", "raw", "filtered"]
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            deadline = time.monotonic() + args.seconds
            while time.monotonic() < deadline:
                data = transport.ser.read(256)
                if data:
                    transport.parser.feed(data)
                for frame, _ in transport.received:
                    if frame["type"] == 0x10:
                        sample = parse_sample(frame["payload"])
                        sample["raw"] = json.dumps(sample["raw"])
                        sample["filtered"] = json.dumps(sample["filtered"])
                        writer.writerow(sample)
                        count += 1
                transport.received.clear()
        print(f"recorded {count} samples to {target}")
        return EXIT_OK if count else EXIT_TIMEOUT
    finally:
        transport.close()


def describe_info(payload):
    if len(payload) < 5:
        return "INFO 负载不足 5 字节"
    status, schema, platform = payload[0], payload[1], payload[2]
    caps = struct.unpack("<H", payload[3:5])[0]
    cap_names = [name for bit, name in CAPABILITIES if caps & bit] or ["无"]
    return (f"status={STATUS_NAMES.get(status, status)} schema={schema} "
            f"platform={PLATFORM_NAMES.get(platform, f'未知({platform})')} "
            f"capabilities={caps:#06x} ({','.join(cap_names)})\n  {describe_logger_tlvs(payload, 5)}")


def describe_f407_reset(reason):
    # RCC_CSR 复位标志位号：.trellis/ref/cmsis/stm32f407xx.h:10320-10333
    # （BORRSTF=25 … LPWRRSTF=31）；平台上报的就是这些位的原始掩码
    names = {25: "BORRSTF", 26: "PINRSTF", 27: "PORRSTF", 28: "SFTRSTF",
             29: "IWDGRSTF", 30: "WWDGRSTF", 31: "LPWRRSTF"}
    hits = [name for bit, name in names.items() if reason & (1 << bit)]
    return f"RCC_CSR 原始值 {reason:#010x}" + (f"（{'|'.join(hits)}）" if hits else "（无标志位）")


def describe_s3_reset(reason):
    # ESP_RST_* 枚举（IDF v5.5.2 components/esp_system/include/esp_system.h:25-40）
    names = {0: "UNKNOWN", 1: "POWERON", 2: "EXT", 3: "SW", 4: "PANIC",
             5: "INT_WDT", 6: "TASK_WDT", 7: "WDT", 8: "DEEPSLEEP",
             9: "BROWNOUT", 10: "SDIO", 11: "USB", 12: "JTAG", 13: "EFUSE",
             14: "PWR_GLITCH", 15: "CPU_LOCKUP"}
    return f"esp_reset_reason={reason}（{names.get(reason, '未知值')}）"


def describe_status(payload, platform):
    if len(payload) < 25:
        return f"STATUS 负载 {len(payload)} 字节，不足 25"
    status, schema = payload[0], payload[1]
    uptime, reset = struct.unpack_from("<II", payload, 2)
    required, overdue, flags = payload[10], payload[11], payload[12]
    rx_ok, rx_error, tx_drop = struct.unpack_from("<III", payload, 13)
    flag_names = [name for bit, name in STATUS_FLAGS if flags & bit] or ["无"]
    reset_text = (describe_f407_reset(reset) if platform == 1 else
                  describe_s3_reset(reset) if platform == 2 else f"raw={reset}")
    return (f"status={STATUS_NAMES.get(status, status)} schema={schema} "
            f"uptime={uptime}ms\n  reset: {reset_text}\n"
            f"  required_mask={required:#04x} overdue_mask={overdue:#04x} "
            f"flags={flags:#04x} ({','.join(flag_names)})\n"
            f"  rx_ok={rx_ok} rx_error={rx_error} tx_drop={tx_drop}\n  {describe_logger_tlvs(payload, 25)}")


# ---------------------------------------------------------------- commands

def run_info(args):
    transport = device_session(args)
    try:
        frame = transport.request(TYPE_INFO, b"", args.timeout, retries=2)
        print(describe_info(frame["payload"]))
    finally:
        transport.close()
    return EXIT_OK


def run_status(args):
    transport = device_session(args)
    try:
        info = transport.request(TYPE_INFO, b"", args.timeout, retries=2)
        platform = info["payload"][2] if len(info["payload"]) >= 3 else None
        frame = transport.request(TYPE_STATUS, b"", args.timeout, retries=2)
        print(describe_info(info["payload"]))
        print(describe_status(frame["payload"], platform))
    finally:
        transport.close()
    return EXIT_OK


def run_command(args):
    payload = bytes.fromhex(args.payload) if args.payload else b""
    transport = device_session(args)
    try:
        frame = transport.request(args.type, payload, args.timeout, retries=0)
        status = frame["payload"][0] if frame["payload"] else None
        print(f"response status={STATUS_NAMES.get(status, status)} "
              f"payload={frame['payload'].hex()}")
        if status != STATUS_OK:
            return EXIT_REJECTED
    finally:
        transport.close()
    return EXIT_OK


def run_fault(args):
    payload = bytes([args.fault, args.task])
    transport = device_session(args)
    try:
        # TEST_FAULT 单次尝试：故障命令自动重试会造成双重故障注入
        frame = transport.request(TYPE_TEST_FAULT, payload, args.timeout, retries=0)
        status = frame["payload"][0] if frame["payload"] else None
        print(f"fault response status={STATUS_NAMES.get(status, status)}")
        if status != STATUS_OK:
            return EXIT_REJECTED
    finally:
        transport.close()
    return EXIT_OK


def run_log(args):
    transport = device_session(args)
    print(f"记录 {args.port} 的帧，Ctrl+C 结束；CSV -> {args.output or '未启用'}")
    try:
        while True:
            data = transport.ser.read(256)
            if data:
                transport.parser.feed(data)
                for frame, note in list(transport.received):
                    print(f"rx type={frame['type']:#04x} seq={frame['sequence']} "
                          f"len={frame['length']} note={note}")
                transport.received.clear()
    except KeyboardInterrupt:
        pass
    finally:
        transport.close()
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(description="双板串口协议主机工具（离线 codec 自测不依赖串口库）")
    parser.add_argument("--port", help="串口号（COM3 / /dev/ttyUSB0），必填于串口子命令")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=1.0, help="单次尝试期限（秒）")
    parser.add_argument("--output", help="CSV 帧日志路径")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("self-test").add_argument("--c-helper", help="codec-tool.exe 路径（交叉验证）")
    sub.add_parser("info")
    sub.add_parser("status")
    cmd = sub.add_parser("command")
    cmd.add_argument("--type", type=lambda x: int(x, 0), required=True)
    cmd.add_argument("--payload", help="hex 负载，如 01 00")
    fault = sub.add_parser("fault")
    fault.add_argument("--fault", type=lambda x: int(x, 0), required=True)
    fault.add_argument("--task", type=lambda x: int(x, 0), default=0)
    sub.add_parser("log")
    for name in ("start", "stop", "save"):
        sub.add_parser(name)
    configure = sub.add_parser("configure")
    configure.add_argument("--period", type=int, default=100)
    configure.add_argument("--filter-shift", type=int, default=2)
    record = sub.add_parser("record")
    record.add_argument("--seconds", type=float, default=10)

    # Accept common options before OR after the subcommand, as documented.
    for child in sub.choices.values():
        for flag, kind in [("--port", str), ("--baud", int), ("--timeout", float), ("--output", str)]:
            child.add_argument(flag, type=kind, default=argparse.SUPPRESS)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "self-test":
            return EXIT_OK if self_test(args.c_helper) else EXIT_SELFTEST
        if not args.port:
            print("串口子命令需要 --port（不做自动探测）", file=sys.stderr)
            return EXIT_SELFTEST
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise FrameError("timeout must be positive and finite")
        if args.command in ("start", "stop", "configure", "save"):
            return run_logger_control(args)
        if args.command == "record":
            return run_record(args)
        if args.command == "info":
            return run_info(args)
        if args.command == "status":
            return run_status(args)
        if args.command == "command":
            if not 1 <= args.type <= 0x7F:
                print("--type 必须在 1..0x7f", file=sys.stderr)
                return EXIT_SELFTEST
            return run_command(args)
        if args.command == "fault":
            return run_fault(args)
        if args.command == "log":
            return run_log(args)
    except (FrameError, ValueError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return EXIT_SELFTEST
    except TimeoutError as exc:
        print(f"超时：{exc}", file=sys.stderr)
        return EXIT_TIMEOUT
    except SerialError as exc:
        print(f"串口错误：{exc}", file=sys.stderr)
        return EXIT_SERIAL
    return EXIT_SELFTEST


if __name__ == "__main__":
    sys.exit(main())
