#!/usr/bin/env python3
"""Checks for thickened chapters 12, 13, 14, and 15 and their static figures."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
IAP = DIAGRAMS / "sample-12-iap-map.svg"
CAN = DIAGRAMS / "sample-13-can-bit.svg"
USB = DIAGRAMS / "sample-14-usb-enum.svg"
RTOS = DIAGRAMS / "sample-15-rtos-prio.svg"


class Batch5FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                IAP,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "0x08000000",
                    "0x08004000",
                    "0x08004800",
                    "0x08004804",
                    "0x0800FC00",
                    "0x08010000",
                    "0xB800",
                    "0x45670123",
                    "0xCDEF89AB",
                    "0x0801FC00",
                    "LOCK",
                    "VTOR",
                    "MSP",
                    "Reset_Handler",
                    "1 KB",
                    "64 KB",
                    "medium-density",
                ),
            ),
            (
                CAN,
                (
                    "STM32F103C8T6",
                    "36 MHz",
                    "pin 45",
                    "PB8",
                    "pin 46",
                    "PB9",
                    "250 ns",
                    "2 us",
                    "500 kbit/s",
                    "75%",
                    "prescaler 9",
                    "450 kbit/s",
                    "70%",
                    "120",
                    "CANH",
                    "CANL",
                    "pin 32",
                    "PA11",
                    "pin 5",
                    "PD0",
                    "pin 6",
                    "PD1",
                ),
            ),
            (
                USB,
                (
                    "STM32F103C8T6",
                    "pin 32",
                    "PA11",
                    "DM",
                    "pin 33",
                    "PA12",
                    "DP",
                    "1.5",
                    "48 MHz",
                    "USBPRE = 0",
                    "USBPRE = 1",
                    "72 MHz",
                    "18",
                    "67",
                    "0x1209",
                    "0x0001",
                    "64",
                    "100 mA",
                    "1023",
                    "0x0483",
                ),
            ),
            (
                RTOS,
                (
                    "STM32F103C8T6",
                    "1 ms",
                    "TIM4",
                    "128 words",
                    "512 bytes",
                    "0x50",
                    "priority 2",
                    "priority 1",
                    "EXTI0",
                    "configASSERT",
                    "SysTick",
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
        iap = IAP.read_text(encoding="utf-8")
        self.assertNotIn("0x1FFFF000", iap)
        can = CAN.read_text(encoding="utf-8")
        self.assertNotIn("absent", can.lower())
        rtos = RTOS.read_text(encoding="utf-8")
        self.assertNotIn("167 ns", rtos)
        self.assertNotIn("17.2", rtos)


def _load_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch5GifTests(unittest.TestCase):
    def test_four_auxiliary_gifs_are_short_and_ascii(self) -> None:
        gifs = _load_gifs()
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
            "swd-fetch",
            "i2c-addr",
            "dma-cndtr",
            "iwdg-1s",
            "iap-jump",
            "can-500k",
            "usb-48m",
            "rtos-tick",
        ):
            self.assertIn(name, gifs.BUILDERS)
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        iap_src = source.split("def iap_jump", 1)[1].split("def can_500k", 1)[0]
        can_src = source.split("def can_500k", 1)[1].split("def usb_48m", 1)[0]
        usb_src = source.split("def usb_48m", 1)[1].split("def rtos_tick", 1)[0]
        rtos_src = source.split("def rtos_tick", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("0x45670123", iap_src)
        self.assertIn("0xCDEF89AB", iap_src)
        self.assertIn("MSP", iap_src)
        self.assertIn("Reset_Handler", iap_src)
        self.assertNotIn("0x0801FC00", iap_src)
        self.assertNotIn("LOCK", iap_src)
        self.assertIn("250 ns", can_src)
        self.assertIn("2 us", can_src)
        self.assertIn("75%", can_src)
        self.assertIn("500 kbit/s", can_src)
        self.assertNotIn("450", can_src)
        self.assertNotIn("PD0", can_src)
        self.assertIn("48 MHz", usb_src)
        self.assertIn("18 bytes", usb_src)
        self.assertIn("67 bytes", usb_src)
        self.assertIn("D+", usb_src)
        self.assertNotIn("72 MHz", usb_src)
        self.assertNotIn("1023", usb_src)
        self.assertIn("1 ms", rtos_src)
        self.assertIn("priority 2", rtos_src)
        self.assertIn("128 words", rtos_src)
        self.assertIn("512 bytes", rtos_src)
        self.assertNotIn("configASSERT", rtos_src)
        self.assertNotIn("167 ns", rtos_src)
        for name in ("iap-jump", "can-500k", "usb-48m", "rtos-tick"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)

class Batch5IapChapterTests(unittest.TestCase):
    def test_iap_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "12-Flash与IAP升级.md"
        en_path = ROOT / "docs" / "en" / "12-flash-iap.md"
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
        self.assertIn("/* F103C8 中容量 1KB/页 */", zh)
        self.assertIn("/* F103C8 medium-density, 1 KB per page */", en)
        self.assertNotIn("F103C8 小容量", zh)
        self.assertNotIn("small-capacity", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "0x08000000",
                "0x08004000",
                "0x08004800",
                "0x08004804",
                "0x0800FC00",
                "0x08010000",
                "0xB800",
                "0x45670123",
                "0xCDEF89AB",
                "0x0801FC00",
                "0xFFFF",
                "#source-rm0008-flash",
                "#source-pm0056-vector",
                "#source-project-examples",
                "#source-ds5319-swd",
                "#source-pm0075-rdp",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("0xAA", blocks)
            self.assertNotIn("0x1FFFF000", blocks)
            self.assertNotIn("20~40", blocks)
            self.assertNotIn("167 ns", blocks)
        self.assertIn("中容量", zh_blocks)
        self.assertIn("medium-density", en_blocks)
        self.assertIn("1 KB", zh_blocks)
        self.assertIn("1 KB", en_blocks)
        self.assertIn("../assets/diagrams/sample-12-iap-map.svg", zh)
        self.assertIn("../../assets/diagrams/sample-12-iap-map.svg", en)
        self.assertIn("../assets/gif/iap-jump.gif", zh)
        self.assertIn("../../assets/gif/iap-jump.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-12-iap-map.svg"), zh_key.index("iap-jump.gif"))
        self.assertLess(en_key.index("sample-12-iap-map.svg"), en_key.index("iap-jump.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        self.assertIn("flash-iap.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"{lock['baseline']}:{rel}"],
            ).decode("utf-8")
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch12 -->"
            end = "<!-- /video:ch12 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scope_zh = (
            "第 12 章的页、半字和两把钥匙。中容量按 1 KB 擦除。编程粒度是 16 位。"
            "擦除态是 0xFFFF。解锁先写 0x45670123，再写 0xCDEF89AB。大容量的 2 KB/页在 C8 上作废。"
            "按字节编程在这颗料上作废。不重写第 02 章的等待周期。不把 0xAA 写成无保护键。"
        )
        scope_en = (
            "Chapter file 12 pages, half-words, and the two keys. Medium-density parts erase 1 KB pages. "
            "Programming granularity is 16 bits. The erased state is 0xFFFF. Unlock writes 0x45670123 and then 0xCDEF89AB. "
            "The high-density 2 KB page is void on the C8. Byte programming is void on this part. "
            "Does not rewrite the chapter 02 wait states. Does not call 0xAA the unprotected key."
        )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "an2606",
            "an3965",
            "rm0090",
            "rm0008-flash",
            "pm0056-vector",
            "project-examples",
            "ds5319-swd",
            "pm0075-rdp",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["12-Flash与IAP升级.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["12-flash-iap.md"]["sources"])
        card_zh = zh_manifest["sources"]["rm0008-flash"]
        card_en = en_manifest["sources"]["rm0008-flash"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["rm0008-flash"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual("2026-10-25", card_zh["accessed"])
        self.assertEqual(card_zh["accessed"], card_en["accessed"])
        self.assertEqual(by_id["rm0008-flash"]["title_zh"], card_zh["title"])
        self.assertEqual(by_id["rm0008-flash"]["title_en"], card_en["title"])
        self.assertEqual(by_id["rm0008-flash"]["authority_zh"], card_zh["authority"])
        self.assertEqual(by_id["rm0008-flash"]["authority_en"], card_en["authority"])
        self.assertEqual(scope_zh, card_zh["scope"])
        self.assertEqual(scope_en, card_en["scope"])
        self.assertEqual(
            ["rm0008-flash"],
            list(zh_manifest["sources"])[-1:],
        )

if __name__ == "__main__":
    unittest.main()
