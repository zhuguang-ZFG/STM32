#!/usr/bin/env python3
"""Checks for thickened chapters 16, 17, 18, and 19 and their static figures."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _fetch_baseline(rev: str) -> None:
    """Shallow CI checkouts do not contain the lock baseline. Match batch 5.

    actions/checkout on Book CI uses the default depth of 1. A regression that
    runs ``git show <lock baseline>:<path>`` cannot see that commit until this
    function fetches it. Do not widen the workflow checkout instead.
    """
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    base = os.environ.get("GITHUB_BASE_REF", "main")
    commands = (
        ["git", "-C", str(ROOT), "fetch", "--depth=1", "origin", rev],
        [
            "git", "-C", str(ROOT), "fetch", "--depth=50", "origin",
            f"+refs/heads/{base}:refs/remotes/origin/{base}",
        ],
    )
    errors: list[str] = []
    for command in commands:
        if _git_show(rev, "stm32-book/manifest.json") is not None:
            return
        got = subprocess.run(command, capture_output=True, text=True, env=env)
        if got.returncode != 0:
            errors.append((got.stderr or got.stdout or command[-1]).strip())
    if _git_show(rev, "stm32-book/manifest.json") is None and errors:
        raise AssertionError("; ".join(errors))


def _git_show(rev: str, path: str) -> str | None:
    got = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{rev}:{path}"],
        capture_output=True,
    )
    if got.returncode != 0:
        return None
    return got.stdout.decode("utf-8")


def baseline_chapter(rev: str, path: str) -> str:
    blob = _git_show(rev, path)
    if blob is None:
        _fetch_baseline(rev)
        blob = _git_show(rev, path)
    if blob is None:
        raise AssertionError(
            f"batch-6 baseline {rev}:{path} is not in this checkout and could not be fetched"
        )
    return blob

DIAGRAMS = ROOT / "assets" / "diagrams"
STOP = DIAGRAMS / "sample-16-stop-wake.svg"
CFSR = DIAGRAMS / "sample-17-cfsr.svg"
BOOT = DIAGRAMS / "sample-18-boot-triage.svg"
FLASH = DIAGRAMS / "sample-19-flash-fit.svg"


class Batch6FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens, banned in (
            (
                STOP,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "14 uA",
                    "24 uA",
                    "5.4 us",
                    "8 MHz",
                    "72 MHz",
                    "0x271",
                    "12800",
                    "115200",
                    "SLEEPDEEP=1",
                    "PDDS=0",
                    "pin 10",
                    "PA0",
                    "自绘",
                ),
                ("14~20", "780", "8/16", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                CFSR,
                (
                    "STM32F103C8T6",
                    "0xE000ED28",
                    "0xE000ED2C",
                    "0xE000ED38",
                    "0xE000EDFC",
                    "0xE0001004",
                    "0x40000000",
                    "bit 15",
                    "bit 24",
                    "bit 30",
                    "1 us",
                    "72",
                    "6",
                    "pin 39",
                    "JTDO",
                    "自绘",
                ),
                ("167 ns", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                BOOT,
                (
                    "STM32F103C8T6",
                    "pin 34",
                    "PA13",
                    "pin 37",
                    "PA14",
                    "pin 7",
                    "0.1 uF",
                    "pin 44",
                    "BOOT0",
                    "0x08000000",
                    "0x1FFFF000",
                    "自绘",
                ),
                ("0x1FFFB000", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                FLASH,
                (
                    "STM32F103C8T6",
                    "0x08000000",
                    "0x08004000",
                    "0x08004800",
                    "0x08010000",
                    "0x0801B800",
                    "0xB800",
                    "110 KB",
                    "20480",
                    "65536",
                    "4096",
                    "自绘",
                ),
                ("0x5A5A0001", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            self.assertNotIn("Svg.footer", text)
            for token in tokens:
                self.assertIn(token, text, path.name)
            for token in banned:
                self.assertNotIn(token, text, path.name)


def _load_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch6", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch6GifTests(unittest.TestCase):
    def test_four_auxiliary_gifs_are_short_and_ascii(self) -> None:
        gifs = _load_gifs()
        names = (
            "led-blink",
            "pwm-breath",
            "uart-bits",
            "i2c-timing",
            "dma-ring",
            "sar-adc",
            "nvic-preempt",
            "uart-idle",
            "clock-css",
            "pwm-1khz",
            "spi-jedec",
            "adc-sample",
            "swd-fetch",
            "i2c-addr",
            "dma-cndtr",
            "iwdg-1s",
            "iap-jump",
            "can-500k",
            "usb-48m",
            "rtos-tick",
            "stop-wake",
            "cfsr-read",
            "boot0-low",
            "one-slot",
        )
        for name in names:
            self.assertIn(name, gifs.BUILDERS)
        self.assertEqual(list(gifs.BUILDERS)[-4:], ["stop-wake", "cfsr-read", "boot0-low", "one-slot"])
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        stop_src = source.split("def stop_wake_gif", 1)[1].split("def cfsr_read_gif", 1)[0]
        cfsr_src = source.split("def cfsr_read_gif", 1)[1].split("def boot0_low", 1)[0]
        boot_src = source.split("def boot0_low", 1)[1].split("def one_slot", 1)[0]
        slot_src = source.split("def one_slot", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("8 MHz", stop_src)
        self.assertIn("72 MHz", stop_src)
        self.assertIn("115200", stop_src)
        self.assertNotIn("12800", stop_src)
        self.assertNotIn("24 uA", stop_src)
        self.assertIn("CFSR", cfsr_src)
        self.assertIn("bit 15 = 1", cfsr_src)
        self.assertIn("1 us", cfsr_src)
        self.assertIn("72", cfsr_src)
        self.assertNotIn("bit 15 = 0", cfsr_src)
        self.assertNotIn("delta 0", cfsr_src)
        self.assertIn("pin 44", boot_src)
        self.assertIn("pin 34", boot_src)
        self.assertIn("pin 37", boot_src)
        self.assertIn("BOOT0 = 0", boot_src)
        self.assertNotIn("BOOT0 = 1", boot_src)
        self.assertNotIn("-O2", boot_src)
        self.assertIn("16 KB", slot_src)
        self.assertIn("2 KB", slot_src)
        self.assertIn("0xB800", slot_src)
        self.assertIn("0x08010000", slot_src)
        self.assertNotIn("0x0801B800", slot_src)
        self.assertNotIn("65536", slot_src)
        for name in ("stop-wake", "cfsr-read", "boot0-low", "one-slot"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)


class Batch6StopChapterTests(unittest.TestCase):
    def test_stop_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "16-低功耗设计.md"
        en_path = ROOT / "docs" / "en" / "16-low-power.md"
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in (
            "## Principle and boundary",
            "## Key figures",
            "## Timing or state",
            "## Pitfalls and source cards",
        ):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Learning goals", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core ideas", en)
        self.assertNotIn("HAL_RTCEx_SetWakeUpTimer_IT", zh)
        self.assertNotIn("HAL_RTCEx_SetWakeUpTimer_IT", en)
        self.assertNotIn("每秒唤醒一次", zh)
        self.assertNotIn("once a second", en)
        self.assertNotIn("14~20", zh)
        self.assertNotIn("14 to 20", en)
        self.assertNotIn("8/16", zh)
        self.assertNotIn("8 or 16 MHz", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "14 µA",
                "24 µA",
                "3.4 µA",
                "3.2 µA",
                "2 µA",
                "1.4 µA",
                "14.4 mA",
                "5.5 mA",
                "5.4 µs",
                "3.6 µs",
                "1.8 µs",
                "50 µs",
                "8 MHz",
                "72 MHz",
                "0x271",
                "12800",
                "115200",
                "1 ms",
                "PA0",
                "#source-ds5319-pwr",
                "#source-rm0008-usart",
                "#source-rm0008-rcc",
                "#source-project-examples",
                "#source-rm0008-rtc",
                "#source-rm0008-wdg",
                "#source-ds5319-adc",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("780", blocks)
            self.assertNotIn("14~20", blocks)
            self.assertNotIn("14 to 20", blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("21 µs", blocks)
            self.assertNotIn("17.2%", blocks)
        self.assertIn("第 10 脚", zh_blocks)
        self.assertIn("pin 10", en_blocks)
        self.assertIn("../assets/diagrams/sample-16-stop-wake.svg", zh)
        self.assertIn("../../assets/diagrams/sample-16-stop-wake.svg", en)
        self.assertIn("../assets/gif/stop-wake.gif", zh)
        self.assertIn("../../assets/gif/stop-wake.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-16-stop-wake.svg"), zh_key.index("stop-wake.gif"))
        self.assertLess(en_key.index("sample-16-stop-wake.svg"), en_key.index("stop-wake.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        self.assertIn("lowpower-wakeup.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch16 -->"
            end = "<!-- /video:ch16 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scope_zh = (
            "第 16 章的两格微安和唤醒微秒。3.3 V、25°C 下，低功耗稳压器、无独立看门狗是 14 µA，"
            "主稳压器那一格是 24 µA。Standby 按 LSI 和 IWDG 写成 3.4、3.2 或 2 µA。1.4 µA 是备份域。"
            "Sleep 是 14.4 mA 或 5.5 mA。醒来先是 8 MHz 的 HSI。不把 14~20 µA 写成表 16 的格子。"
        )
        scope_en = (
            "Chapter file 16 cells and wake-up times. At 3.3 V and 25°C, Stop with the low-power regulator "
            "and the independent watchdog off is 14 µA. The main-regulator cell is 24 µA. Standby is 3.4, 3.2, "
            "or 2 µA according to LSI and IWDG. 1.4 µA is the backup domain. Sleep is 14.4 mA or 5.5 mA. "
            "Wake-up starts on the 8 MHz HSI. Does not call 14 to 20 µA a Table 16 cell."
        )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "ds5319",
            "ds5319-pwr",
            "rm0008-pwr",
            "rm0008-rcc",
            "rm0008-usart",
            "ds5319-adc",
            "project-examples",
            "rm0008-rtc",
            "rm0008-wdg",
        ]
        guide = zh_manifest["chapter_guides"]["16-低功耗设计.md"]
        guide_en = en_manifest["chapter_guides"]["16-low-power.md"]
        self.assertEqual(compass, guide["sources"])
        self.assertEqual(compass, guide_en["sources"])
        self.assertEqual(
            "进入与退出 Sleep/Stop/Standby 时，哪些时钟、状态和唤醒源必须显式恢复？",
            guide["question"],
        )
        self.assertIn("14 µA", guide["boundary"])
        self.assertIn("24 µA", guide["boundary"])
        self.assertIn("8 MHz", guide["boundary"])
        self.assertNotIn("14~20", guide["boundary"])
        self.assertIn("14 µA", guide_en["boundary"])
        self.assertNotIn("14 to 20", guide_en["boundary"])
        for source_id, scope_pair in (
            ("ds5319-pwr", (scope_zh, scope_en)),
            (
                "rm0008-pwr",
                (
                    "第 16 章醒来先是 HSI，串口之前要重配时钟。PDDS=0 且 SLEEPDEEP=1 是 Stop。PDDS=1 且 SLEEPDEEP=1 是 Standby。不把 F4 的周期唤醒定时器写进来。",
                    "Chapter file 16 returns to HSI and must restore the clock before the next byte. PDDS=0 with SLEEPDEEP=1 is Stop. PDDS=1 with SLEEPDEEP=1 is Standby. Does not include the F4 periodic wake-up timer.",
                ),
            ),
        ):
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual("2026-10-25", card_zh["accessed"])
            self.assertEqual(card_zh["accessed"], card_en["accessed"])
            self.assertEqual(by_id[source_id]["title_zh"], card_zh["title"])
            self.assertEqual(by_id[source_id]["title_en"], card_en["title"])
            self.assertEqual(by_id[source_id]["authority_zh"], card_zh["authority"])
            self.assertEqual(by_id[source_id]["authority_en"], card_en["authority"])
            self.assertEqual(scope_pair[0], card_zh["scope"])
            self.assertEqual(scope_pair[1], card_en["scope"])
        self.assertEqual(["ds5319-pwr", "rm0008-pwr"], list(zh_manifest["sources"])[-2:])
        self.assertEqual(["ds5319-pwr", "rm0008-pwr"], list(en_manifest["sources"])[-2:])

class Batch6CfsrChapterTests(unittest.TestCase):
    def test_cfsr_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "17-调试与性能优化.md"
        en_path = ROOT / "docs" / "en" / "17-debug.md"
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in (
            "## Principle and boundary",
            "## Key figures",
            "## Timing or state",
            "## Pitfalls and source cards",
        ):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("CoreDebug_DEMCR_TRCENA_Msk", zh)
        self.assertIn("CoreDebug_DEMCR_TRCENA_Msk", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "0xE000ED28",
                "0xE000ED2C",
                "0xE000ED34",
                "0xE000ED38",
                "0xE000EDFC",
                "0xE0001004",
                "0x40000000",
                "bit 15",
                "bit 24",
                "bit 30",
                "1 µs",
                "PA13",
                "PA14",
                "PB3",
                "JTDO",
                "#source-pm0056",
                "#source-pm0056-dwt",
                "#source-ds5319-swd",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("10+", blocks)
            self.assertNotIn("2~4", blocks)
            self.assertNotIn("-mfpu", blocks)
        self.assertIn("6", zh_blocks)
        self.assertIn("6", en_blocks)
        self.assertIn("../assets/diagrams/sample-17-cfsr.svg", zh)
        self.assertIn("../../assets/diagrams/sample-17-cfsr.svg", en)
        self.assertIn("../assets/gif/cfsr-read.gif", zh)
        self.assertIn("../../assets/gif/cfsr-read.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-17-cfsr.svg"), zh_key.index("cfsr-read.gif"))
        self.assertLess(en_key.index("sample-17-cfsr.svg"), en_key.index("cfsr-read.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertIn("debug-swo.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch17 -->"
            end = "<!-- /video:ch17 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scope_zh = (
            "第 17 章的 DWT 使能顺序和硬件断点个数。先置 DEMCR 0xE000EDFC 的 bit 24，再读 DWT_CYCCNT 0xE0001004。"
            "72 MHz 下 72 个计数是 1 µs。没置 bit 24 时差值为 0。这颗 M3 是 6 个硬件断点。不重写 CFSR 的四个地址。不把 167 ns 写进来。"
        )
        scope_en = (
            "Chapter file 17 DWT enable order and hardware-breakpoint count. Set DEMCR 0xE000EDFC bit 24 before reading "
            "DWT_CYCCNT at 0xE0001004. At 72 MHz, 72 counts are 1 µs. A clear bit 24 reads a delta of 0. This M3 has 6 "
            "hardware breakpoints. Does not restate the four CFSR addresses. Does not include 167 ns."
        )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["pm0056", "pm0056-dwt", "ds5319-swd"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["17-调试与性能优化.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["17-debug.md"]["sources"])
        self.assertEqual(
            "面对崩溃或变慢，怎样从可重复现象走到故障寄存器、调用位置和周期证据？",
            zh_manifest["chapter_guides"]["17-调试与性能优化.md"]["question"],
        )
        card_zh = zh_manifest["sources"]["pm0056-dwt"]
        card_en = en_manifest["sources"]["pm0056-dwt"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["pm0056-dwt"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual("2026-10-25", card_zh["accessed"])
        self.assertEqual(scope_zh, card_zh["scope"])
        self.assertEqual(scope_en, card_en["scope"])
        self.assertEqual(by_id["pm0056-dwt"]["title_zh"], card_zh["title"])
        self.assertEqual(by_id["pm0056-dwt"]["title_en"], card_en["title"])
        self.assertEqual(["pm0056-dwt"], list(zh_manifest["sources"])[-1:])

if __name__ == "__main__":
    unittest.main()
