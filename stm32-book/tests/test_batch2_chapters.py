#!/usr/bin/env python3
"""Checks for thickened chapters 04 and 06 and their static figures."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch2-04-06-lock.json"
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch2-04-06-source-list.json"
_BASELINE_MANIFESTS: dict[str, dict] | None = None


def baseline_manifests() -> tuple[dict, dict]:
    """Manifests at the lock file's baseline, before batch-2 sources exist."""
    global _BASELINE_MANIFESTS
    if _BASELINE_MANIFESTS is not None:
        return _BASELINE_MANIFESTS["zh"], _BASELINE_MANIFESTS["en"]
    rev = json.loads(LOCK.read_text(encoding="utf-8"))["baseline"]
    paths = ("stm32-book/manifest.json", "stm32-book/manifest-en.json")
    blobs = [_git_show(rev, path) for path in paths]
    if any(blob is None for blob in blobs):
        _fetch_baseline(rev)
        blobs = [_git_show(rev, path) for path in paths]
        if any(blob is None for blob in blobs):
            raise AssertionError(
                f"batch-2 baseline {rev} is not in this checkout and could not be fetched"
            )
    _BASELINE_MANIFESTS = {
        "zh": json.loads(blobs[0]),
        "en": json.loads(blobs[1]),
    }
    return _BASELINE_MANIFESTS["zh"], _BASELINE_MANIFESTS["en"]


def _fetch_baseline(rev: str) -> None:
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


DIAGRAMS = ROOT / "assets" / "diagrams"
NVIC = DIAGRAMS / "sample-04-exception-stack.svg"
UART = DIAGRAMS / "sample-06-uart-frame.svg"


class Batch2FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                NVIC,
                (
                    "STM32F103C8T6",
                    "NVIC_PRIORITYGROUP_4",
                    "xPSR",
                    "PC",
                    "LR",
                    "R12",
                    "R3",
                    "R2",
                    "R1",
                    "R0",
                    "167 ns",
                    "PA0",
                    "EXTI0",
                    "EXTI_PR",
                    "EXTI0_IRQn",
                    "TIM2",
                    "PRIMASK",
                    "NMI",
                    "GROUP_4",
                ),
            ),
            (
                UART,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "PA9",
                    "PA10",
                    "30",
                    "31",
                    "0xA5",
                    "0x271",
                    "39.0625",
                    "8.68",
                    "86.8",
                    "USART_SR",
                    "0x00",
                    "USART_DR",
                    "0x04",
                    "USART_BRR",
                    "0x08",
                    "USART_CR1",
                    "0x0C",
                    "FE",
                    "OVER8",
                ),
            ),
        ):
            raw = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            for banned in ("<animate", "@keyframes", "animation:", "矢量动画", "实拍"):
                self.assertNotIn(banned, raw)
            for token in tokens:
                self.assertIn(token, raw)
            self.assertIn("自绘", raw)
            self.assertNotIn("Svg.footer", raw)


def load_gen_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch2", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch2GifTests(unittest.TestCase):
    def test_new_gifs_are_short_auxiliaries(self) -> None:
        gifs = load_gen_gifs()
        for name in (
            "led-blink",
            "pwm-breath",
            "uart-bits",
            "i2c-timing",
            "dma-ring",
            "sar-adc",
            "nvic-preempt",
            "uart-idle",
        ):
            self.assertIn(name, gifs.BUILDERS)
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        nvic_src = source.split("def nvic_preempt", 1)[1].split("def uart_idle", 1)[0]
        idle_src = source.split("def uart_idle", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("TIM2", nvic_src)
        self.assertIn("EXTI0", nvic_src)
        self.assertNotIn("SAME PREEMPT", nvic_src)
        self.assertIn("86.8 us", idle_src)
        self.assertIn("IDLE", idle_src)
        self.assertNotIn("FE", idle_src)
        for name in ("nvic-preempt", "uart-idle"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)


class Batch2NvicChapterTests(unittest.TestCase):
    def test_nvic_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "04-中断与NVIC.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "04-interrupts-nvic.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Learning goals", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core ideas", en)
        self.assertNotIn("0x50", zh)
        self.assertNotIn("0x50", en)
        self.assertNotIn("第 9.2.7 节（AFIO_EXTICR）", zh)
        self.assertNotIn("section 9.2.7 (AFIO_EXTICR)", en)
        for text in (zh, en):
            for token in (
                "STM32F103C8T6",
                "167 ns",
                "NVIC_PRIORITYGROUP_4",
                "xPSR, PC, LR, R12, R3, R2, R1, R0",
                "PRIMASK",
                "NMI",
                "EXTI0",
                "TIM2",
                "PA0",
                "GROUP_4",
                "#source-pm0056-nvic",
                "#source-rm0008-exti",
                "#source-freertos-priority",
            ):
                self.assertIn(token, text)
            self.assertNotIn("6 个周期", text)
            self.assertNotIn("6 cycles", text.lower())
        self.assertIn("../assets/diagrams/sample-04-exception-stack.svg", zh)
        self.assertIn("../../assets/diagrams/sample-04-exception-stack.svg", en)
        self.assertIn("../assets/gif/nvic-preempt.gif", zh)
        self.assertIn("../../assets/gif/nvic-preempt.gif", en)
        self.assertIn("../assets/animations/nvic-interrupt-flow.svg", zh)
        self.assertIn("../assets/diagrams/interrupt-priority.svg", zh)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-04-exception-stack.svg"), zh_key.index("nvic-preempt.gif"))
        self.assertLess(en_key.index("sample-04-exception-stack.svg"), en_key.index("nvic-preempt.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        zh_cards = zh.split("## 坑与出处卡", 1)[1].split("## 📌 学习目标", 1)[0]
        en_cards = en.split("## Pitfalls and source cards", 1)[1].split("## 📌 Learning goals", 1)[0]
        for cards in (zh_cards, en_cards):
            self.assertGreaterEqual(cards.count("#source-pm0056-nvic"), 4)
            self.assertGreaterEqual(cards.count("#source-rm0008-exti"), 2)
            self.assertNotIn("消抖", cards)
            self.assertNotIn("debounce", cards.lower())
            self.assertNotIn("10 ms", cards)
            self.assertNotIn("20 ms", cards)
        for start, end in (
            ("## 原理与边界", "## 关键插图"),
            ("## 关键插图", "## 时序或状态"),
            ("## 时序或状态", "## 坑与出处卡"),
            ("## 坑与出处卡", "## 📌 学习目标"),
        ):
            self.assertIn("#source-", zh.split(start, 1)[1].split(end, 1)[0])
        for start, end in (
            ("## Principle and boundary", "## Key figures"),
            ("## Key figures", "## Timing or state"),
            ("## Timing or state", "## Pitfalls and source cards"),
            ("## Pitfalls and source cards", "## 📌 Learning goals"),
        ):
            self.assertIn("#source-", en.split(start, 1)[1].split(end, 1)[0])
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-exti": (
                "第 04 章原理与边界、关键插图、坑与出处卡。只改写 EXTI 线按脚号共用、F1 上先开 AFIO 时钟再写 EXTICR，以及 EXTI_PR 要清。EXTICR 在 RM0008 Rev 21 第 9.4.3 到 9.4.6 节，不是第 9.2.7 节。不复制手册段落，不描官方图。",
                "Chapter 04 principle, key figures, and source cards. Restates that one EXTI line is shared by pin number, that F1 enables the AFIO clock before writing EXTICR, and that EXTI_PR must be cleared. EXTICR is RM0008 Rev 21 sections 9.4.3 through 9.4.6, not section 9.2.7. Does not copy manual prose and does not trace the official figure.",
            ),
            "pm0056-nvic": (
                "第 04 章原理与边界、时序或状态、坑与出处卡。只改写 8 个寄存器的入栈、尾链不改变抢占权，以及 PRIMASK 挡不住 NMI。不把 167 ns 写成 ISR 正文的预算，不把尾链周期数补进附录 D。不改已有 pm0056 的 CFSR/HFSR 范围。",
                "Chapter 04 principle, timing, and source cards. Restates the eight-register stack, that tail-chaining does not change who may preempt, and that PRIMASK does not stop NMI. Does not treat 167 ns as the ISR body budget and does not add a tail-chain cycle count to Appendix D. Does not change the existing pm0056 CFSR/HFSR scope.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["pm0056", "rm0008", "freertos-priority", "rm0008-exti", "pm0056-nvic"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["04-中断与NVIC.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["04-interrupts-nvic.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual(card_zh["accessed"], card_en["accessed"])
            self.assertRegex(card_zh["accessed"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertEqual(by_id[source_id]["title_zh"], card_zh["title"])
            self.assertEqual(by_id[source_id]["title_en"], card_en["title"])
            self.assertEqual(by_id[source_id]["authority_zh"], card_zh["authority"])
            self.assertEqual(by_id[source_id]["authority_en"], card_en["authority"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        baseline, baseline_en = baseline_manifests()
        for source_id, obj in baseline["sources"].items():
            self.assertEqual(obj, zh_manifest["sources"][source_id])
        for source_id, obj in baseline_en["sources"].items():
            self.assertEqual(obj, en_manifest["sources"][source_id])
        self.assertIn("rm0008-exti", zh_manifest["sources"])
        self.assertIn("pm0056-nvic", zh_manifest["sources"])
        self.assertNotIn("rm0090-usart-over8", zh_manifest["sources"])



class Batch2UartChapterTests(unittest.TestCase):
    def test_uart_chapters_fix_the_brr_cell_and_keep_four_blocks(self) -> None:
        zh = (ROOT / "docs" / "06-串口UART.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "06-uart.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertNotIn("F1/F4 支持 OVER8", zh)
        self.assertNotIn("F1 and F4 have the OVER8 bit", en)
        self.assertNotIn("8 × 115200", zh)
        self.assertNotIn("8 × 115200", en)
        self.assertNotIn("8 x 115200", zh)
        self.assertNotIn("8 x 115200", en)
        for text in (zh, en):
            for token in (
                "STM32F103C8T6",
                "PA9",
                "PA10",
                "30",
                "31",
                "0xA5",
                "0x271",
                "39.0625",
                "8.68",
                "86.8",
                "0x138",
                "FE",
                "#source-rm0008-usart",
                "#source-majerle-uart",
                "#source-st-uart-idle",
                "#source-stm32cube-f4",
                "#source-ds5319-usart",
            ):
                self.assertIn(token, text)
            rows_271 = [line for line in text.splitlines() if line.startswith("|") and "0x271" in line]
            self.assertGreaterEqual(len(rows_271), 1)
            for line in rows_271:
                self.assertIn("0%", line)
                self.assertNotIn("0.16%", line)
            rows_138 = [line for line in text.splitlines() if line.startswith("|") and "0x138" in line]
            self.assertGreaterEqual(len(rows_138), 1)
            for line in rows_138:
                self.assertIn("0.16%", line)
                self.assertIn("USART2", line)
        self.assertIn("位 31:14", zh)
        self.assertIn("bits 31:14", en)
        self.assertIn("那不是写进 `0x271` 的结果", zh)
        self.assertIn("That is not what writing `0x271` does.", en)
        self.assertIn("经验线索，未升格为规范", zh)
        self.assertIn("experience only", en.lower())
        self.assertIn("../assets/diagrams/sample-06-uart-frame.svg", zh)
        self.assertIn("../../assets/diagrams/sample-06-uart-frame.svg", en)
        self.assertIn("../assets/gif/uart-idle.gif", zh)
        self.assertIn("../../assets/gif/uart-idle.gif", en)
        self.assertIn("../assets/animations/uart-frame.svg", zh)
        self.assertIn("../assets/gif/uart-bits.gif", zh)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-06-uart-frame.svg"), zh_key.index("uart-idle.gif"))
        self.assertLess(en_key.index("sample-06-uart-frame.svg"), en_key.index("uart-idle.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        for needle in ("8", "9", "10"):
            self.assertIn(needle, zh_key)
            self.assertIn(needle, en_key)
        zh_cards = zh.split("## 坑与出处卡", 1)[1].split("## 📌 学习目标", 1)[0]
        en_cards = en.split("## Pitfalls and source cards", 1)[1].split("## 📌 Learning goals", 1)[0]
        for cards in (zh_cards, en_cards):
            self.assertGreaterEqual(cards.count("#source-rm0008-usart"), 4)
            self.assertEqual(1, cards.count("#source-stm32cube-f4"))
            self.assertEqual(1, cards.count("#source-st-uart-idle"))
            self.assertEqual(1, cards.count("#source-majerle-uart"))
        for start, end in (
            ("## 原理与边界", "## 关键插图"),
            ("## 关键插图", "## 时序或状态"),
            ("## 时序或状态", "## 坑与出处卡"),
            ("## 坑与出处卡", "## 📌 学习目标"),
        ):
            self.assertIn("#source-", zh.split(start, 1)[1].split(end, 1)[0])
        for start, end in (
            ("## Principle and boundary", "## Key figures"),
            ("## Key figures", "## Timing or state"),
            ("## Timing or state", "## Pitfalls and source cards"),
            ("## Pitfalls and source cards", "## 📌 Learning goals"),
        ):
            self.assertIn("#source-", en.split(start, 1)[1].split(end, 1)[0])
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-usart": (
                "第 06 章原理与边界、时序或状态、坑与出处卡。只改写 16 倍采样、BRR 0x271 在 72 MHz 下误差为 0、IDLE 是满一个帧时间、以及先读 SR 再读 DR 清 FE。F103 的 USART_CR1 位 31:14 保留，没有 OVER8。不复制 27.3.3，不描官方采样图，不编 8 倍的 BRR。",
                "Chapter 06 principle, timing, and source cards. Restates 16× sampling, BRR 0x271 with divider error 0 at 72 MHz, IDLE as one full frame of idle line, and clearing FE by reading SR then DR. On F103, USART_CR1 bits 31:14 are reserved, so there is no OVER8. Does not copy section 27.3.3, does not trace the official sampling figure, and does not invent an 8× BRR.",
            ),
            "ds5319-usart": (
                "第 06 章关键插图。只改写 LQFP48 第 30 脚 PA9 为 USART1_TX、第 31 脚 PA10 为 USART1_RX。复位后不是 PB6/PB7。不描图 8。",
                "Chapter 06 key figure. Restates LQFP48 pin 30 PA9 as USART1_TX and pin 31 PA10 as USART1_RX. The reset default is not PB6/PB7. Does not trace Figure 8.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "stm32cube-f4", "st-uart-idle", "majerle-uart", "rm0008-usart", "ds5319-usart"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["06-串口UART.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["06-uart.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual(card_zh["accessed"], card_en["accessed"])
            self.assertEqual(by_id[source_id]["title_zh"], card_zh["title"])
            self.assertEqual(by_id[source_id]["title_en"], card_en["title"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        baseline, baseline_en = baseline_manifests()
        self.assertEqual(
            set(zh_manifest["sources"]) - set(baseline["sources"]),
            {
                "rm0008-exti", "pm0056-nvic", "rm0008-usart", "ds5319-usart",
                "rm0008-rcc", "ds5319-clock", "rm0008-tim", "ds5319-tim",
                "rm0008-spi", "ds5319-spi", "rm0008-adc", "ds5319-adc",
                "ds5319-swd", "pm0075-rdp", "pm0056-vector",
                "ds5319-i2c", "rm0008-i2c", "rm0008-dma", "ds5319-dma",
                "rm0008-wdg", "rm0008-rtc", "ds5319-rtc",
                "rm0008-flash", "rm0008-can", "ds5319-usbcan", "rm0008-usb",
                "freertos-syscall",
                "ds5319-pwr", "rm0008-pwr", "pm0056-dwt", "ds5319-nrst", "ds5319-lse",
            },
        )
        self.assertEqual(
            set(en_manifest["sources"]) - set(baseline_en["sources"]),
            {
                "rm0008-exti", "pm0056-nvic", "rm0008-usart", "ds5319-usart",
                "rm0008-rcc", "ds5319-clock", "rm0008-tim", "ds5319-tim",
                "rm0008-spi", "ds5319-spi", "rm0008-adc", "ds5319-adc",
                "ds5319-swd", "pm0075-rdp", "pm0056-vector",
                "ds5319-i2c", "rm0008-i2c", "rm0008-dma", "ds5319-dma",
                "rm0008-wdg", "rm0008-rtc", "ds5319-rtc",
                "rm0008-flash", "rm0008-can", "ds5319-usbcan", "rm0008-usb",
                "freertos-syscall",
                "ds5319-pwr", "rm0008-pwr", "pm0056-dwt", "ds5319-nrst", "ds5319-lse",
            },
        )
        for source_id in ("majerle-uart", "st-uart-idle", "stm32cube-f4", "pm0056", "rm0090"):
            self.assertEqual(baseline["sources"][source_id], zh_manifest["sources"][source_id])
            self.assertEqual(baseline_en["sources"][source_id], en_manifest["sources"][source_id])

if __name__ == "__main__":
    unittest.main()
