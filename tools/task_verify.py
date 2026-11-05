#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task_verify —— 分列验证工具（passed / failed / unverified，unverified 不冒充通过）。

背景：`BOOK_CLASSIC_CONVERGE_SPECS.md` §10.2 要求 task_verify 的分列报告；
本环境原本没有该工具，此前以手写等价记录落盘。本脚本按开源 verify 工具的
通用模式（checks 清单 → 逐项执行 → 机器可读报告）实现等价工具本体：
命令清单来自 checks JSON，每项要么作为命令执行（exit 0 = passed，否则 failed
并附输出尾部），要么显式声明为 manual/deferred（= unverified，必须写 reason）。

用法：
    python tools/task_verify.py --checks stm32-book/tests/fixtures/task-verify-checks.json \
        --out stm32-book/audits/task-verify-report.json

退出码：无 failed 项 → 0（存在 unverified 也返回 0，报告内如实分列）；
存在 failed 项 → 1。
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
VALID_STATUS = {"passed", "failed", "unverified"}


def run_one(check: dict, timeout: int) -> dict:
    cid = check["id"]
    kind = check.get("kind", "command")
    if kind in ("manual", "deferred"):
        return {
            "id": cid,
            "kind": kind,
            "status": "unverified",
            "reason": check.get("reason", "manual check without executable command"),
        }
    cmd = check["cmd"]
    cwd = str(ROOT)
    started = time.monotonic()
    try:
        got = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return {
            "id": cid, "kind": kind, "cmd": cmd, "status": "failed",
            "exit_code": None, "duration_s": round(time.monotonic() - started, 1),
            "tail": f"timeout after {timeout}s",
        }
    tail_lines = (got.stdout or b"").decode("utf-8", "replace").strip().splitlines()[-6:]
    status = "passed" if got.returncode == 0 else "failed"
    return {
        "id": cid,
        "kind": kind,
        "cmd": cmd,
        "status": status,
        "exit_code": got.returncode,
        "duration_s": round(time.monotonic() - started, 1),
        "tail": tail_lines,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=3600)
    args = ap.parse_args()

    manifest = json.loads(Path(args.checks).read_text(encoding="utf-8"))
    results = []
    for check in manifest["checks"]:
        print(f"[run] {check['id']}", flush=True)
        results.append(run_one(check, args.timeout))

    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    unverified = sum(1 for r in results if r["status"] == "unverified")
    if failed:
        overall = "failed"
    elif unverified:
        overall = "passed_with_unverified"  # unverified 不冒充通过，也不拖垮整体
    else:
        overall = "passed"
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "checks_manifest": str(Path(args.checks)),
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "unverified": unverified,
            "overall": overall,
        },
        "results": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"[done] overall={overall} passed={passed} failed={failed} "
          f"unverified={unverified} -> {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
