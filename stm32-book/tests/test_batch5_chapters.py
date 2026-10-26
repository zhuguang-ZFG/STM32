#!/usr/bin/env python3
"""Checks for thickened chapters 12, 13, 14, and 15 and their static figures."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"


def _fetch_baseline(rev: str) -> None:
    """Shallow CI checkouts do not contain the lock baseline. Match batch 4."""
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
            f"batch-5 baseline {rev}:{path} is not in this checkout and could not be fetched"
        )
    return blob
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
            baseline = baseline_chapter(lock["baseline"], rel)
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
        order = list(zh_manifest["sources"])
        self.assertIn("rm0008-flash", order)
        later = [
            name
            for name in ("rm0008-can", "ds5319-usbcan", "rm0008-usb", "freertos-syscall")
            if name in order
        ]
        if later:
            self.assertLess(order.index("rm0008-flash"), order.index(later[0]))
        else:
            self.assertEqual("rm0008-flash", order[-1])


class Batch5CanChapterTests(unittest.TestCase):
    def test_can_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "13-CAN总线.md"
        en_path = ROOT / "docs" / "en" / "13-can.md"
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
        self.assertNotIn("## ⚠️ Pitfalls\n", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Goals", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core idea", en)
        self.assertNotIn("## 📌 Learning goals", en)
        zh_video, zh_rest = _split_video(zh, "ch13")
        en_video, en_rest = _split_video(en, "ch13")
        self.assertIn("C8 没有那两只脚", zh_video)
        self.assertIn("C8 没有那两只脚", en_video)
        self.assertNotIn("C8 没有那两只脚", zh_rest)
        self.assertNotIn("C8 没有那两只脚", en_rest)
        self.assertNotIn("差分阻抗约 60", zh_rest)
        self.assertNotIn("differential impedance near 60", en_rest)
        self.assertIn("PB8=CAN_RX、PB9=CAN_TX", zh_rest)
        self.assertIn("PB8 = CAN_RX, PB9 = CAN_TX", en_rest)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "36",
                "250",
                "500",
                "450",
                "75",
                "70",
                "256",
                "128",
                "11",
                "120",
                "PB8",
                "PB9",
                "PA11",
                "PA12",
                "PD0",
                "PD1",
                "#source-rm0008-can",
                "#source-project-examples",
                "#source-ds5319-usbcan",
                "#source-ds5319-clock",
                "#source-ds5319-i2c",
                "#source-rm0008-usb",
            ):
                self.assertIn(token, blocks)
        self.assertIn("第 45 脚", zh_blocks)
        self.assertIn("第 46 脚", zh_blocks)
        self.assertIn("第 5 脚", zh_blocks)
        self.assertIn("第 6 脚", zh_blocks)
        self.assertIn("pin 45", en_blocks)
        self.assertIn("pin 46", en_blocks)
        self.assertIn("pin 5", en_blocks)
        self.assertIn("pin 6", en_blocks)
        self.assertIn("不是电缆", zh_blocks)
        self.assertIn("not the cable", en_blocks)
        self.assertIn("../assets/diagrams/sample-13-can-bit.svg", zh)
        self.assertIn("../../assets/diagrams/sample-13-can-bit.svg", en)
        self.assertIn("../assets/gif/can-500k.gif", zh)
        self.assertIn("../../assets/gif/can-500k.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-13-can-bit.svg"), zh_key.index("can-500k.gif"))
        self.assertLess(en_key.index("sample-13-can-bit.svg"), en_key.index("can-500k.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path, now in ((zh_path, zh), (en_path, en)):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            marker = "<!-- video:ch13 -->"
            end = "<!-- /video:ch13 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "rm0008-can",
            "ds5319-usbcan",
            "rm0008-usb",
            "project-examples",
            "ds5319-clock",
            "ds5319-i2c",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["13-CAN总线.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["13-can.md"]["sources"])
        order = list(zh_manifest["sources"])
        self.assertEqual(
            ["rm0008-flash", "rm0008-can", "ds5319-usbcan", "rm0008-usb"],
            order[-5:-1],
        )
        self.assertEqual(order[-5:], list(en_manifest["sources"])[-5:])
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-can": (
                "第 13 章的位时间、总线关闭和过滤器。36 MHz 下预分频 9、8 个时间份额是 500 kbit/s。预分频 8、10 个时间份额是 450 kbit/s。发送错误计数到 256 进入总线关闭。恢复是 128 次、每次 11 个隐性位。不编 CAN 基址。不把 450 kbit/s 写成工作点。",
                "Chapter file 13 bit time, bus-off, and filters. At 36 MHz, prescaler 9 and eight quanta is 500 kbit/s. Prescaler 8 and ten quanta is 450 kbit/s. A transmit error counter of 256 enters bus-off. Recovery is 128 times 11 recessive bits. Does not invent a CAN base address. Does not call 450 kbit/s the working point.",
            ),
            "ds5319-usbcan": (
                "第 13 章和第 14 章的脚。第 32 脚 PA11 的复用含 USB_DM 和 CAN_RX，第 33 脚 PA12 的复用含 USB_DP 和 CAN_TX。第 45 脚 PB8、第 46 脚 PB9 是 CAN 重映射。第 5 脚和第 6 脚存在。同一对 PA11/PA12 不能同时当 CAN 和 USB。",
                "Pins for chapter files 13 and 14. Pin 32 PA11 includes USB_DM and CAN_RX. Pin 33 PA12 includes USB_DP and CAN_TX. Pin 45 PB8 and pin 46 PB9 are the CAN remap. Pin 5 and pin 6 exist. PA11/PA12 cannot be CAN and USB at the same time.",
            ),
            "rm0008-usb": (
                "第 14 章的设备边界，以及第 13 章对同一条中断的交叉引用。F103 的 USB 是全速设备，不是主机。USB 时钟要 48 MHz。默认向量名是 USB_LP_CAN1_RX0。不把 480 Mbit/s 写进这颗料。",
                "The device boundary for chapter file 14, and the chapter file 13 cross-reference to the same interrupt. F103 USB is a full-speed device, not a host. The USB clock must be 48 MHz. The default vector name is USB_LP_CAN1_RX0. Does not write 480 Mbit/s onto this part.",
            ),
        }
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


class Batch5UsbChapterTests(unittest.TestCase):
    def test_usb_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "14-USB.md"
        en_path = ROOT / "docs" / "en" / "14-usb.md"
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
        self.assertNotIn("## ⚠️ Pitfalls\n", en)
        self.assertIn("## 📌 Goals", en)
        self.assertIn("## 🧠 Core idea", en)
        self.assertIn("0x1209/0x0001", zh)
        self.assertIn("0x1209/0x0001", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "USBPRE",
                "48",
                "72",
                "18",
                "67",
                "0x0043",
                "0x1209",
                "0x0001",
                "64",
                "0x32",
                "100",
                "1023",
                "1.5",
                "#source-rm0008-rcc",
                "#source-ds5319-usbcan",
                "#source-project-examples",
                "#source-rm0008-usb",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("10 ms", blocks)
            self.assertNotIn("90 Ω", blocks)
            self.assertNotIn("90 ohm", blocks.lower())
        self.assertIn("是设备", zh_blocks)
        self.assertIn("not a host", en_blocks)
        self.assertIn("不是这份", zh_blocks)
        self.assertIn("not this descriptor", en_blocks)
        self.assertIn("第 32 脚", zh_blocks)
        self.assertIn("第 33 脚", zh_blocks)
        self.assertIn("pin 32", en_blocks)
        self.assertIn("pin 33", en_blocks)
        self.assertIn("../assets/diagrams/sample-14-usb-enum.svg", zh)
        self.assertIn("../../assets/diagrams/sample-14-usb-enum.svg", en)
        self.assertIn("../assets/gif/usb-48m.gif", zh)
        self.assertIn("../../assets/gif/usb-48m.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-14-usb-enum.svg"), zh_key.index("usb-48m.gif"))
        self.assertLess(en_key.index("sample-14-usb-enum.svg"), en_key.index("usb-48m.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path, now in ((zh_path, zh), (en_path, en)):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            marker = "<!-- video:ch14 -->"
            end = "<!-- /video:ch14 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "usb20",
            "project-examples",
            "rm0008-rcc",
            "ds5319-usbcan",
            "rm0008-usb",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["14-USB.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["14-usb.md"]["sources"])
        self.assertNotIn("rm0008-rcc-pullup", zh_manifest["sources"])


class Batch5RtosChapterTests(unittest.TestCase):
    def test_rtos_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "15-FreeRTOS入门.md"
        en_path = ROOT / "docs" / "en" / "15-freertos.md"
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
        self.assertIn("## 📌 Learning goals", en)
        self.assertIn("## 🧠 Core ideas", en)
        self.assertIn("TIM4", zh)
        self.assertIn("TIM4", en)
        self.assertNotIn("改为 **TIMx**", zh)
        self.assertNotIn("改成 TIMx", zh)
        self.assertNotIn("改 TIMx", zh)
        self.assertNotIn("to **TIMx**", en)
        self.assertNotIn("to TIMx", en)
        self.assertIn("没有 FPU", zh)
        self.assertIn("no FPU", en)
        self.assertNotIn("选带 FPU 的移植（", zh)
        self.assertNotIn("Use the port that includes the FPU", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "1000",
                "0x50",
                "128",
                "512",
                "192",
                "768",
                "256",
                "1024",
                "TIM4",
                "13",
                "GROUP_4",
                "#source-project-examples",
                "#source-freertos-syscall",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("17.2", blocks)
        self.assertIn("大于等于 5", zh_blocks)
        self.assertIn("5 or a larger number", en_blocks)
        self.assertIn("../assets/diagrams/sample-15-rtos-prio.svg", zh)
        self.assertIn("../../assets/diagrams/sample-15-rtos-prio.svg", en)
        self.assertIn("../assets/gif/rtos-tick.gif", zh)
        self.assertIn("../../assets/gif/rtos-tick.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-15-rtos-prio.svg"), zh_key.index("rtos-tick.gif"))
        self.assertLess(en_key.index("sample-15-rtos-prio.svg"), en_key.index("rtos-tick.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path, now in ((zh_path, zh), (en_path, en)):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            marker = "<!-- video:ch15 -->"
            end = "<!-- /video:ch15 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "freertos-priority",
            "pm0056",
            "project-examples",
            "freertos-syscall",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["15-FreeRTOS入门.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["15-freertos.md"]["sources"])
        self.assertEqual(
            [
                "rm0008-flash",
                "rm0008-can",
                "ds5319-usbcan",
                "rm0008-usb",
                "freertos-syscall",
            ],
            list(zh_manifest["sources"])[-5:],
        )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        card_zh = zh_manifest["sources"]["freertos-syscall"]
        card_en = en_manifest["sources"]["freertos-syscall"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["freertos-syscall"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual("2026-10-25", card_zh["accessed"])
        self.assertEqual("MIT", card_zh["license"])
        self.assertEqual(by_id["freertos-syscall"]["title_zh"], card_zh["title"])
        self.assertEqual(by_id["freertos-syscall"]["title_en"], card_en["title"])
        self.assertEqual(
            "第 15 章的 0x50、字栈方向和互斥量。4 位优先级时 5 左移 4 位是 0x50。任务优先级数值更大的先跑。xTaskCreate 的深度单位是字。互斥量有优先级继承，二值信号量没有。不覆盖第 28 章。不把 17.2% 写进来。",
            card_zh["scope"],
        )
        self.assertEqual(
            "Chapter file 15 for 0x50, the word-stack direction, and mutexes. With 4 priority bits, 5 shifted left by 4 is 0x50. A numerically larger task priority runs first. The xTaskCreate depth is in words. A mutex has priority inheritance and a binary semaphore does not. Does not cover chapter file 28. Does not bring in 17.2 percent.",
            card_en["scope"],
        )


def _split_video(text: str, slug: str) -> tuple[str, str]:
    marker = f"<!-- video:{slug} -->"
    end = f"<!-- /video:{slug} -->"
    video = text.split(marker, 1)[1].split(end, 1)[0]
    rest = text.split(marker, 1)[0] + text.split(end, 1)[1]
    return video, rest


if __name__ == "__main__":
    unittest.main()
