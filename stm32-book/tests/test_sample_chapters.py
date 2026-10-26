#!/usr/bin/env python3
"""Checks for the two thickened sample chapters and their static figures."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
BOOT = DIAGRAMS / "sample-00-boot-state.svg"
GPIO = DIAGRAMS / "sample-03-gpio-led.svg"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-chapter-lock.json"
_BASELINE_MANIFESTS: dict[str, dict] | None = None


def baseline_manifests() -> tuple[dict, dict]:
    """Pre-sample manifests.

    PR checkouts on Actions are shallow and do not have ``origin/main``.
    The lock file records the commit the sample was cut from. Use that
    object when it is already local; otherwise fetch that one commit.
    """
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
                f"pre-sample baseline {rev} is not in this checkout and could not be fetched"
            )
    _BASELINE_MANIFESTS = {
        "zh": json.loads(blobs[0]),
        "en": json.loads(blobs[1]),
    }
    return _BASELINE_MANIFESTS["zh"], _BASELINE_MANIFESTS["en"]


def _fetch_baseline(rev: str) -> None:
    """Bring the pinned pre-sample commit into a shallow checkout.

    Actions does not advertise ``origin/main``. Fetch that commit directly,
    then the base branch deeply enough that the same commit is still present
    after this pull request lands on main.
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


class SampleFigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (BOOT, ("STM32F103C8T6", "BOOT0", "BOOT1", "SWDIO", "SWCLK", "0x08000000", "0x00000000", "0x1FFFF000", "SYSCLK")),
            (GPIO, ("STM32F103C8T6", "LQFP48", "PA0", "PC13", "270", "260", "3.3", "3 mA", "2 MHz", "30 pF", "LCKR", "0x18")),
        ):
            raw = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            for banned in ("<animate", "@keyframes", "animation:"):
                self.assertNotIn(banned, raw)
            for token in tokens:
                self.assertIn(token, raw)
            self.assertIn("自绘", raw)
            self.assertNotIn("实拍", raw)
            self.assertNotIn("矢量动画", raw)


class SampleGpioChapterTests(unittest.TestCase):
    def test_gpio_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "03-GPIO与LED.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "03-gpio-and-led.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Learning goals", en)
        for text in (zh, en):
            for token in ("STM32F103C8T6", "LQFP48", "PA0", "PC13", "270", "260", "3.3", "3 mA", "2 MHz", "30 pF", "GPIOx_LCKR", "0x18", "PA13", "PA14", "#source-ds5319-gpio", "#source-rm0008-gpio", "#source-project-examples"):
                self.assertIn(token, text)
            self.assertIn("../assets/diagrams/sample-03-gpio-led.svg" if text is zh else "../../assets/diagrams/sample-03-gpio-led.svg", text)
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
        core = zh.split("## 🧠 核心原理", 1)[1].split("## 🛠️ 硬件与接线", 1)[0]
        core_en = en.split("## 🧠 Core ideas", 1)[1].split("## 🛠️ Hardware and wiring", 1)[0]
        for block in (core, core_en):
            self.assertNotIn("260", block)
            self.assertNotIn("270", block)
            self.assertNotIn("3 mA", block)
            self.assertNotIn("3mA", block)
        self.assertNotIn("示意图", zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0])
        self.assertNotIn("schematic", en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0].lower())
        self.assertIn("自绘", zh)
        self.assertIn("Drawn for this book", en)
        listed = json.loads((ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-source-list.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-gpio": (
                "第 03 章原理与边界、时序或状态、坑与出处卡。只改写 GPIOx_LCKR 偏移 0x18 的锁定序列，以及 SWDIO=PA13、SWCLK=PA14。不复制手册段落，不覆盖 F4 的 AFR。",
                "Chapter 03 principle, timing, and source cards. Restates the GPIOx_LCKR lock at offset 0x18 and SWDIO=PA13, SWCLK=PA14. Does not copy manual prose and does not cover F4 AFR.",
            ),
            "ds5319-gpio": (
                "第 03 章原理与边界、关键插图、坑与出处卡。只改写 LQFP48 第 10 脚 PA0、第 2 脚 PC13，以及注 5 的 3 mA、2 MHz、30 pF。不复制注 5 原文，不描图 8。",
                "Chapter 03 principle, key figures, and source cards. Restates LQFP48 pin 10 PA0, pin 2 PC13, and note 5: 3 mA, 2 MHz, 30 pF. Does not copy note 5 and does not trace Figure 8.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        self.assertEqual(
            ["rm0008", "ds5319", "rm0008-gpio", "ds5319-gpio", "project-examples"],
            zh_manifest["chapter_guides"]["03-GPIO与LED.md"]["sources"],
        )
        self.assertEqual(
            ["rm0008", "ds5319", "rm0008-gpio", "ds5319-gpio", "project-examples"],
            en_manifest["chapter_guides"]["03-gpio-and-led.md"]["sources"],
        )
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


class SampleFoundationChapterTests(unittest.TestCase):
    def test_foundation_chapters_have_four_blocks_and_the_same_addresses(self) -> None:
        zh = (ROOT / "docs" / "00-如何学习STM32.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "00-how-to-learn-stm32.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core ideas", en)
        for text in (zh, en):
            for token in ("STM32F103C8T6", "0x08000000", "0x00000000", "0x00000004", "0x1FFFF000", "0x1FFFB000", "0x08080000", "BOOT0", "BOOT1", "SYSCLK", "#source-rm0008-boot"):
                self.assertIn(token, text)
        self.assertIn("../assets/diagrams/sample-00-boot-state.svg", zh)
        self.assertIn("../../assets/diagrams/sample-00-boot-state.svg", en)
        self.assertIn("自绘", zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0])
        self.assertIn("Drawn for this book", en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0])
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
        listed = json.loads((ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-source-list.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        self.assertEqual(
            ["project-guide", "rm0008", "ds5319", "rm0008-boot"],
            zh_manifest["chapter_guides"]["00-如何学习STM32.md"]["sources"],
        )
        self.assertEqual(
            ["project-guide", "rm0008", "ds5319", "rm0008-boot"],
            en_manifest["chapter_guides"]["00-how-to-learn-stm32.md"]["sources"],
        )
        card_zh = zh_manifest["sources"]["rm0008-boot"]
        card_en = en_manifest["sources"]["rm0008-boot"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["rm0008-boot"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual(card_zh["accessed"], card_en["accessed"])
        self.assertEqual(
            "第 00 章的启动状态与失败路径。只改写 RM0008 Rev 21 第 3.4 节表 9；互联型地址和 XL 密度 Bank2 在这颗 STM32F103C8T6 上作废。不复制该节原文。",
            card_zh["scope"],
        )
        self.assertEqual(
            "Chapter 00 boot states and the failure path. Restates RM0008 Rev 21 section 3.4 Table 9. The connectivity-line address and the XL-density Bank2 row are void on STM32F103C8T6. Does not copy that section.",
            card_en["scope"],
        )
        baseline, baseline_en = baseline_manifests()
        self.assertEqual(
            set(zh_manifest["sources"]) - set(baseline["sources"]),
            {
                "rm0008-boot", "rm0008-gpio", "ds5319-gpio",
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
                "rm0008-boot", "rm0008-gpio", "ds5319-gpio",
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


if __name__ == "__main__":
    unittest.main()
