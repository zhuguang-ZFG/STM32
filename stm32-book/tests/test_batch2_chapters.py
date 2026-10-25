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


if __name__ == "__main__":
    unittest.main()
