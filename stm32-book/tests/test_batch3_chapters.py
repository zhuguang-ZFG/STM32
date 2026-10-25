#!/usr/bin/env python3
"""Checks for thickened chapters 02, 05, 08, and 09 and their static figures."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch3-02-05-08-09-lock.json"
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch3-02-05-08-09-source-list.json"
_BASELINE_MANIFESTS: dict[str, dict] | None = None


def baseline_manifests() -> tuple[dict, dict]:
    """Manifests at the lock file's baseline, before batch-3 sources exist."""
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
                f"batch-3 baseline {rev} is not in this checkout and could not be fetched"
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
CLOCK = DIAGRAMS / "sample-02-clock-tree.svg"
PWM = DIAGRAMS / "sample-05-pwm-1khz.svg"
SPI = DIAGRAMS / "sample-08-spi-jedec.svg"
ADC = DIAGRAMS / "sample-09-adc-sar.svg"


class Batch3FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                CLOCK,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 5 PD0",
                    "pin 6 PD1",
                    "pin 29 PA8",
                    "PLLMUL=0111",
                    "PLLSRC=1",
                    "PLLXTPRE=0",
                    "72 MHz",
                    "36 MHz",
                    "12 MHz",
                    "18 MHz",
                    "14 MHz",
                    "48 MHz",
                    "50 MHz",
                    "USBPRE=0",
                    "LATENCY=2",
                    "LATENCY=0",
                    "CSSC",
                    "HSI 8 MHz",
                    "7.3.2",
                ),
            ),
            (
                PWM,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 16",
                    "PA6",
                    "TIM3_CH1",
                    "PSC=71",
                    "ARR=999",
                    "CCR=500",
                    "1000 Hz",
                    "500 Hz",
                    "500 us",
                    "72 MHz",
                    "36 MHz",
                    "999999",
                    "16-bit",
                    "MOE",
                    "0x44",
                    "SPI1_MISO is not on this trace",
                ),
            ),
            (
                SPI,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 14 PA4",
                    "pin 15 PA5",
                    "pin 16 PA6",
                    "pin 17 PA7",
                    "CPOL=0",
                    "CPHA=0",
                    "BR=010",
                    "9 MHz",
                    "0x9F",
                    "0xEF",
                    "0x40",
                    "0x17",
                    "36 MHz",
                    "MOSI",
                    "MISO",
                    "swapped",
                ),
            ),
            (
                ADC,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 9 VDDA",
                    "pin 10 PA0",
                    "ADC12_IN0",
                    "12 MHz",
                    "21 us",
                    "239.5",
                    "12.5",
                    "4096",
                    "18 MHz",
                    "14 MHz",
                    "previous voltage",
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
        spi = SPI.read_text(encoding="utf-8")
        self.assertNotIn("0x40013000", spi)
        adc = ADC.read_text(encoding="utf-8")
        self.assertNotIn("270", adc)


def load_gen_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch3", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch3GifTests(unittest.TestCase):
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
            "clock-css",
            "pwm-1khz",
            "spi-jedec",
            "adc-sample",
        ):
            self.assertIn(name, gifs.BUILDERS)
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        clock_src = source.split("def clock_css", 1)[1].split("def pwm_1khz", 1)[0]
        pwm_src = source.split("def pwm_1khz", 1)[1].split("def spi_jedec", 1)[0]
        spi_src = source.split("def spi_jedec", 1)[1].split("def adc_sample", 1)[0]
        adc_src = source.split("def adc_sample", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("HSE 8 MHz", clock_src)
        self.assertIn("72 MHz", clock_src)
        self.assertIn("HSI 8 MHz", clock_src)
        self.assertNotIn("LATENCY", clock_src)
        self.assertIn("1000 Hz", pwm_src)
        self.assertIn("500 us", pwm_src)
        self.assertIn("CCR=500", pwm_src)
        self.assertNotIn("500 Hz", pwm_src)
        self.assertIn("0x9F", spi_src)
        self.assertIn("0xEF", spi_src)
        self.assertIn("9 MHz", spi_src)
        self.assertNotIn("36 MHz", spi_src)
        self.assertIn("12 MHz", adc_src)
        self.assertIn("MSB", adc_src)
        self.assertNotIn("18 MHz", adc_src)
        for name in ("clock-css", "pwm-1khz", "spi-jedec", "adc-sample"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)


class Batch3ClockChapterTests(unittest.TestCase):
    def test_clock_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "02-芯片选型与存储器时钟.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "02-part-and-clock.md").read_text(encoding="utf-8")
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
        self.assertNotIn("RM0008 第 8.3.2 节", zh)
        self.assertNotIn("RM0008 section 8.3.2", en)
        self.assertIn("7.3.2", zh)
        self.assertIn("7.3.2", en)
        for text in (zh, en):
            for token in (
                "STM32F103C8T6",
                "0111",
                "72 MHz",
                "36 MHz",
                "12 MHz",
                "18 MHz",
                "14 MHz",
                "48 MHz",
                "50 MHz",
                "8 MHz",
                "CSSC",
                "PD0",
                "PD1",
                "PA8",
                "USBPRE",
                "ADCPRE",
                "#source-rm0008-rcc",
                "#source-ds5319-clock",
            ):
                self.assertIn(token, text)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            self.assertNotIn("21 µs", blocks)
            self.assertNotIn("21 us", blocks)
            self.assertNotIn("21µs", blocks)
        self.assertIn("../assets/diagrams/sample-02-clock-tree.svg", zh)
        self.assertIn("../../assets/diagrams/sample-02-clock-tree.svg", en)
        self.assertIn("../assets/gif/clock-css.gif", zh)
        self.assertIn("../../assets/gif/clock-css.gif", en)
        self.assertIn("../assets/animations/clock-tree.svg", zh)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-02-clock-tree.svg"), zh_key.index("clock-css.gif"))
        self.assertLess(en_key.index("sample-02-clock-tree.svg"), en_key.index("clock-css.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        zh_cards = zh.split("## 坑与出处卡", 1)[1].split("## 📌 学习目标", 1)[0]
        en_cards = en.split("## Pitfalls and source cards", 1)[1].split("## 📌 Learning goals", 1)[0]
        for cards in (zh_cards, en_cards):
            self.assertGreaterEqual(cards.count("#source-rm0008-rcc"), 6)
        self.assertIn("不是数据手册", zh)
        self.assertIn("not numbers from DS5319", en)
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-rcc": (
                "第 02 章原理与边界、关键插图、时序或状态、坑与出处卡。只改写中密度 RCC_CFGR 第 7.3.2 节：HSE 8 MHz、PLLMUL=0111 得到 72 MHz、48–72 MHz 的 LATENCY 是 2、APB1 为 36 MHz 时定时器再 ×2、USBPRE=0 得到 48 MHz、ADCPRE=10 得到 12 MHz、ADCPRE=01 得到 18 MHz 并越过 14 MHz、CSS 回到 HSI 并要写 CSSC、送到 MCO 的时钟不得超过 50 MHz。第 8.3.2 节在 STM32F103C8T6 上作废。不把采样时间写进这一章。不改已有 rm0008。",
                "Chapter 02 principle, key figures, timing, and source cards. Restates medium-density RCC_CFGR section 7.3.2: HSE 8 MHz and PLLMUL=0111 give 72 MHz, LATENCY is 2 from 48 to 72 MHz, timers clock at twice PCLK when APB1 is 36 MHz, USBPRE=0 gives 48 MHz, ADCPRE=10 gives 12 MHz, ADCPRE=01 gives 18 MHz and crosses 14 MHz, CSS falls back to HSI and software writes CSSC, and the clock sent to MCO stays at or below 50 MHz. Section 8.3.2 is void on STM32F103C8T6. Does not put the sample time in this chapter. Does not change the existing rm0008 object.",
            ),
            "ds5319-clock": (
                "第 02 章关键插图。LQFP48 第 5 脚是 PD0-OSC_IN，第 6 脚是 PD1-OSC_OUT，第 29 脚 PA8 的复用含 MCO。不编负载电容的皮法。不改 ds5319-gpio。",
                "Chapter 02 key figure. LQFP48 pin 5 is PD0-OSC_IN, pin 6 is PD1-OSC_OUT, and pin 29 PA8 includes MCO in its alternate function. Does not invent a load-capacitor value. Does not change ds5319-gpio.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "ds5319", "rm0008-rcc", "ds5319-clock"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["02-芯片选型与存储器时钟.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["02-part-and-clock.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
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
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        baseline, baseline_en = baseline_manifests()
        for source_id, obj in baseline["sources"].items():
            self.assertEqual(obj, zh_manifest["sources"][source_id])
        for source_id, obj in baseline_en["sources"].items():
            self.assertEqual(obj, en_manifest["sources"][source_id])

class Batch3PwmChapterTests(unittest.TestCase):
    def test_pwm_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "05-定时器与PWM.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "05-timer-pwm.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertNotIn("16/32", zh)
        self.assertNotIn("16/32", en)
        self.assertNotIn("PWM_ARR / 2", zh)
        self.assertNotIn("PWM_ARR / 2", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        self.assertNotIn("0x10", zh_blocks)
        self.assertNotIn("0x10", en_blocks)
        for text in (zh, en):
            for token in (
                "PSC = 71",
                "ARR = 999",
                "CCR = 500",
                "1000 Hz",
                "500 Hz",
                "999999",
                "7199",
                "9999",
                "PA6",
                "MOE",
                "0x44",
                "0x0000",
                "#source-rm0008-tim",
                "#source-ds5319-tim",
            ):
                self.assertIn(token, text)
        self.assertIn("第 16 脚", zh)
        self.assertIn("pin 16", en)
        self.assertIn("../assets/diagrams/sample-05-pwm-1khz.svg", zh)
        self.assertIn("../../assets/diagrams/sample-05-pwm-1khz.svg", en)
        self.assertIn("../assets/gif/pwm-1khz.gif", zh)
        self.assertIn("../../assets/gif/pwm-1khz.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-05-pwm-1khz.svg"), zh_key.index("pwm-1khz.gif"))
        self.assertLess(en_key.index("sample-05-pwm-1khz.svg"), en_key.index("pwm-1khz.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertIn("另一组高分辨率", zh)
        self.assertIn("Not the Appendix D 1 kHz cell", en)
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-tim": (
                "第 05 章原理与边界、时序或状态、坑与出处卡。PSC = 71、ARR = 999、计数时钟 72 MHz 是 1000 Hz。同一组数用 36 MHz 得到 500 Hz。这颗料的 TIM2–TIM5 是 16 位，装不下 999999。能装下的 1 秒是 PSC = 7199、ARR = 9999。TIMx_BDTR 偏移 0x44，复位值 0x0000，位 15 是 MOE。不把 DeadTime 0x10 换成纳秒。不改附录 D 的 1 kHz 格子。",
                "Chapter 05 principle, timing, and source cards. PSC = 71 and ARR = 999 at a 72 MHz counter clock is 1000 Hz. The same numbers divided by 36 MHz are 500 Hz. TIM2–TIM5 on this part are 16-bit and cannot hold 999999. The 1 second that fits is PSC = 7199 and ARR = 9999. TIMx_BDTR is at offset 0x44, resets to 0x0000, and bit 15 is MOE. Does not turn DeadTime 0x10 into a nanosecond. Does not change the Appendix D 1 kHz cell.",
            ),
            "ds5319-tim": (
                "第 05 章关键插图和坑与出处卡。LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1。同一格也含 SPI1_MISO，这张图不把它画成同时有效。不把重映射到 PB4 或 PC6 画进正常路径。",
                "Chapter 05 key figure and source cards. LQFP48 pin 16 is PA6, and the default alternate function includes TIM3_CH1. The same cell also includes SPI1_MISO, and this figure does not draw both as active. Does not draw a remap onto PB4 or PC6 on the normal path.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "rm0008-tim", "ds5319-tim"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["05-定时器与PWM.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["05-timer-pwm.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
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
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        baseline, baseline_en = baseline_manifests()
        for source_id, obj in baseline["sources"].items():
            self.assertEqual(obj, zh_manifest["sources"][source_id])
        for source_id, obj in baseline_en["sources"].items():
            self.assertEqual(obj, en_manifest["sources"][source_id])

if __name__ == "__main__":
    unittest.main()
