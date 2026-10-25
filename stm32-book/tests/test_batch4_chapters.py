#!/usr/bin/env python3
"""Checks for thickened chapters 01, 07, 10, and 11 and their static figures."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-lock.json"
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-source-list.json"
_BASELINE_MANIFESTS: dict[str, dict] | None = None


def baseline_manifests() -> tuple[dict, dict]:
    """Manifests at the lock file's baseline, before batch-4 sources exist."""
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
                f"batch-4 baseline {rev} is not in this checkout and could not be fetched"
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
SWD = DIAGRAMS / "sample-01-swd-vectors.svg"
I2C = DIAGRAMS / "sample-07-i2c-addr.svg"
DMA = DIAGRAMS / "sample-10-dma-cndtr.svg"
IWDG = DIAGRAMS / "sample-11-iwdg-1s.svg"


class Batch4FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                SWD,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 34",
                    "PA13",
                    "SWDIO",
                    "pin 35",
                    "VSS_2",
                    "pin 36",
                    "VDD_2",
                    "pin 37",
                    "PA14",
                    "SWCLK",
                    "pin 44",
                    "BOOT0",
                    "0x08000000",
                    "0x00000000",
                    "MSP",
                    "Reset_Handler",
                    "GPIO",
                    "0x1FFFF000",
                    "0xA5",
                    "0xAA",
                    "64 KB",
                    "20 KB",
                ),
            ),
            (
                I2C,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 42",
                    "PB6",
                    "pin 43",
                    "PB7",
                    "4.7",
                    "0x78",
                    "0x3C",
                    "0x801E",
                    "400 kHz",
                    "ACK",
                    "NACK",
                    "36 MHz",
                    "0x00B4",
                ),
            ),
            (
                DMA,
                (
                    "STM32F103C8T6",
                    "DMA1",
                    "channel 4",
                    "CNDTR",
                    "5 samples",
                    "10 bytes",
                    "4 samples",
                    "8 bytes",
                    "DMA2",
                    "pin 30",
                    "PA9",
                ),
            ),
            (
                IWDG,
                (
                    "STM32F103C8T6",
                    "40 kHz",
                    "30 kHz",
                    "60 kHz",
                    "prescaler 64",
                    "625 Hz",
                    "Reload = 624",
                    "Reload = 625",
                    "pin 1",
                    "VBAT",
                    "pin 3",
                    "pin 4",
                    "32767",
                    "32768",
                    "0x50",
                    "58.25",
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
        dma = DMA.read_text(encoding="utf-8")
        self.assertNotIn("21 us", dma)
        self.assertNotIn("21 µs", dma)
        iwdg = IWDG.read_text(encoding="utf-8")
        self.assertNotIn("6 pF", iwdg)


def load_gen_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch4", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch4GifTests(unittest.TestCase):
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
            "swd-fetch",
            "i2c-addr",
            "dma-cndtr",
            "iwdg-1s",
        ):
            self.assertIn(name, gifs.BUILDERS)
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        swd_src = source.split("def swd_fetch", 1)[1].split("def i2c_addr", 1)[0]
        i2c_src = source.split("def i2c_addr", 1)[1].split("def dma_cndtr", 1)[0]
        dma_src = source.split("def dma_cndtr", 1)[1].split("def iwdg_1s", 1)[0]
        iwdg_src = source.split("def iwdg_1s", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("pin 34", swd_src)
        self.assertIn("pin 37", swd_src)
        self.assertIn("MSP", swd_src)
        self.assertIn("Reset_Handler", swd_src)
        self.assertNotIn("0xAA", swd_src)
        self.assertNotIn("GPIO", swd_src)
        self.assertIn("0x78", i2c_src)
        self.assertIn("0x801E", i2c_src)
        self.assertIn("4.7", i2c_src)
        self.assertIn("ACK", i2c_src)
        self.assertNotIn("0x3C", i2c_src)
        self.assertIn("CNDTR", dma_src)
        self.assertIn("5 samples", dma_src)
        self.assertIn("10 bytes", dma_src)
        self.assertNotIn("DMA2", dma_src)
        self.assertNotIn("3 bytes", dma_src)
        self.assertIn("Reload = 624", iwdg_src)
        self.assertIn("40 kHz", iwdg_src)
        self.assertIn("625 Hz", iwdg_src)
        self.assertNotIn("Reload = 625", iwdg_src)
        self.assertNotIn("0x50", iwdg_src)
        for name in ("swd-fetch", "i2c-addr", "dma-cndtr", "iwdg-1s"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)


class Batch4SwdChapterTests(unittest.TestCase):
    def test_swd_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "01-开发环境搭建.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "01-dev-environment.md").read_text(encoding="utf-8")
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
        self.assertIn("stm32f1x unlock 0", zh)
        self.assertIn("stm32f1x unlock 0", en)
        self.assertIn("LENGTH = 64K", zh)
        self.assertIn("LENGTH = 20K", zh)
        self.assertNotIn("从 SRAM 启动", zh)
        self.assertNotIn("boot from SRAM", en)
        self.assertNotIn("选 `AA`", zh)
        self.assertNotIn("set Read Out Protection to `AA`", en)
        for text in (zh, en):
            for token in (
                "STM32F103C8T6",
                "PA13",
                "PA14",
                "VSS_2",
                "VDD_2",
                "NRST",
                "BOOT0",
                "0x08000000",
                "0x00000000",
                "0x00000004",
                "0x1FFFF000",
                "0xA5",
                "64",
                "20",
                "#source-ds5319-swd",
                "#source-pm0075-rdp",
                "#source-pm0056-vector",
                "#source-rm0008-boot",
            ):
                self.assertIn(token, text)
        self.assertIn("第 34 脚", zh)
        self.assertIn("第 35 脚", zh)
        self.assertIn("第 37 脚", zh)
        self.assertIn("第 7 脚", zh)
        self.assertIn("第 44 脚", zh)
        self.assertIn("pin 34", en)
        self.assertIn("pin 35", en)
        self.assertIn("pin 37", en)
        self.assertIn("pin 7", en)
        self.assertIn("pin 44", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            self.assertIn("0xA5", blocks)
            self.assertIn("0xAA", blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("Level 2", blocks)
        self.assertIn("作废", zh_blocks)
        self.assertIn("void", en_blocks.lower())
        self.assertIn("../assets/diagrams/sample-01-swd-vectors.svg", zh)
        self.assertIn("../../assets/diagrams/sample-01-swd-vectors.svg", en)
        self.assertIn("../assets/gif/swd-fetch.gif", zh)
        self.assertIn("../../assets/gif/swd-fetch.gif", en)
        self.assertIn("../assets/animations/boot-sequence.svg", zh)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-01-swd-vectors.svg"), zh_key.index("swd-fetch.gif"))
        self.assertLess(en_key.index("sample-01-swd-vectors.svg"), en_key.index("swd-fetch.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        self.assertNotIn("矢量动画", zh_key)
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "ds5319-swd": (
                "第 01 章原理与边界、关键插图、时序或状态、坑与出处卡。只改写 LQFP48 第 34 脚 PA13 = JTMS/SWDIO、第 35 脚 VSS_2、第 36 脚 VDD_2、第 37 脚 PA14 = JTCK/SWCLK、第 7 脚 NRST、第 44 脚 BOOT0。STM32F103x8 闪存 64 KB、SRAM 20 KB。xB 的 128 KB 在 C8T6 上作废。第 39 脚 PB3 只写进边界，不进主图正常路径。不改 ds5319-gpio。",
                "Chapter 01 principle, key figures, timing, and source cards. Restates LQFP48 pin 34 PA13 = JTMS/SWDIO, pin 35 VSS_2, pin 36 VDD_2, pin 37 PA14 = JTCK/SWCLK, pin 7 NRST, and pin 44 BOOT0. STM32F103x8 Flash is 64 KB and SRAM is 20 KB. The xB 128 KB is void on C8T6. Pin 39 PB3 stays in the boundary and off the normal path. Does not change ds5319-gpio.",
            ),
            "pm0075-rdp": (
                "第 01 章读保护，以及第 11 章对 WDG_SW 的交叉引用。选项字节在 0x1FFFF800，低字节 RDP 的读允许键是 0xA5（手册印成 0x00A5）。编程回这个键会先整片擦除主闪存。USER 里 WDG_SW 为 0 是硬件看门狗，为 1 是软件看门狗。不把 0xAA 写成无保护键，不写 0xCC。不在第 01 章展开喂狗。",
                "Chapter 01 readout protection, and the chapter 11 cross-reference for WDG_SW. Option bytes sit at 0x1FFFF800. The readout-allowed RDP byte is 0xA5 (the manual prints 0x00A5). Programming that key back mass-erases main Flash first. WDG_SW = 0 is the hardware watchdog and WDG_SW = 1 is the software watchdog. Does not call 0xAA the unprotected key and does not write 0xCC. Does not expand watchdog feeding inside chapter 01.",
            ),
            "pm0056-vector": (
                "第 01 章的两字和 IRQ 入口。向量表第 0 项是 MSP 初值，第 1 项是 Reset。外设中断入口是 VTOR + 4×(IRQn + 16)。不改 pm0056 和 pm0056-nvic。不把 167 ns 写进这一章。",
                "Chapter 01's two words and the IRQ entry. Vector-table item 0 is the initial MSP and item 1 is Reset. A peripheral IRQ entry is VTOR + 4×(IRQn + 16). Does not change pm0056 or pm0056-nvic. Does not put 167 ns in this chapter.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "project-guide",
            "pm0056",
            "stm32cube-f4",
            "clion-embedded",
            "platformio-vscode",
            "ds5319-swd",
            "pm0075-rdp",
            "pm0056-vector",
            "rm0008-boot",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["01-开发环境搭建.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["01-dev-environment.md"]["sources"])
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


class Batch4I2cChapterTests(unittest.TestCase):
    def test_i2c_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "07-I2C总线.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "07-i2c.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core ideas", en)
        for text in (zh, en):
            for token in (
                "0x3C",
                "0x78",
                "0x79",
                "0x801E",
                "30",
                "0x00B4",
                "180",
                "400",
                "4.7",
                "36",
                "PB6",
                "PB7",
                "1000",
                "300",
                "#source-ds5319-i2c",
                "#source-rm0008-i2c",
                "#source-project-examples",
            ):
                self.assertIn(token, text)
        self.assertIn("第 42 脚", zh)
        self.assertIn("第 43 脚", zh)
        self.assertIn("pin 42", en)
        self.assertIn("pin 43", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            self.assertNotIn("300ns / Cb", blocks)
            self.assertNotIn("300 ns / Cb", blocks)
            self.assertIn("1 MHz", blocks)
        self.assertIn("作废", zh_blocks)
        self.assertIn("void", en_blocks.lower())
        self.assertNotIn("可达 400kHz/1MHz", zh_blocks)
        self.assertNotIn("Up to 400 kHz / 1 MHz", en_blocks)
        self.assertIn("../assets/diagrams/sample-07-i2c-addr.svg", zh)
        self.assertIn("../../assets/diagrams/sample-07-i2c-addr.svg", en)
        self.assertIn("../assets/gif/i2c-addr.gif", zh)
        self.assertIn("../../assets/gif/i2c-addr.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-07-i2c-addr.svg"), zh_key.index("i2c-addr.gif"))
        self.assertLess(en_key.index("sample-07-i2c-addr.svg"), en_key.index("i2c-addr.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "ds5319-i2c": (
                "第 07 章。第 42 脚 PB6 默认含 I2C1_SCL，第 43 脚 PB7 默认含 I2C1_SDA。表 42 在 36 MHz、3.3 V、4.7 kΩ 下把 400 kHz 印成 0x801E，100 kHz 印成 0x00B4。标准模式上升时间上限 1000 ns，快速模式 300 ns。1 MHz 在这颗料上作废。不吸收屏厂手册。",
                "Chapter 07. Pin 42 PB6 default alternate function includes I2C1_SCL and pin 43 PB7 includes I2C1_SDA. Table 42 at 36 MHz, 3.3 V, and 4.7 kΩ prints 400 kHz as 0x801E and 100 kHz as 0x00B4. The standard-mode rise-time limit is 1000 ns and the fast-mode limit is 300 ns. 1 MHz is void on this part. Does not absorb a display-vendor manual.",
            ),
            "rm0008-i2c": (
                "第 07 章。7 位地址加 1 位 R/W。线上写地址 0x78，读地址 0x79。第 9 个时钟 SDA 拉低是 ACK，保持高是 NACK。0x3C 原样送出变成 7 位地址 0x1E。不编 I2C 基址。",
                "Chapter 07. A 7-bit address plus one R/W bit. The write byte on the wire is 0x78 and the read byte is 0x79. SDA low on the 9th clock is ACK and SDA high is NACK. Sending 0x3C unchanged addresses 0x1E. Does not invent an I2C base address.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "ds5319-i2c", "rm0008-i2c", "project-examples"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["07-I2C总线.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["07-i2c.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual("2026-10-25", card_zh["accessed"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        self.assertEqual(
            baseline_manifests()[0]["sources"]["project-examples"],
            zh_manifest["sources"]["project-examples"],
        )
        self.assertEqual(
            baseline_manifests()[1]["sources"]["project-examples"],
            en_manifest["sources"]["project-examples"],
        )


class Batch4DmaChapterTests(unittest.TestCase):
    def test_dma_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "10-DMA.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "10-dma.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        for text in (zh, en):
            for token in (
                "DMA1",
                "CNDTR",
                "10",
                "#source-rm0008-dma",
                "#source-ds5319-dma",
                "#source-rm0090",
            ):
                self.assertIn(token, text)
        self.assertIn("通道 4", zh)
        self.assertIn("通道 5", zh)
        self.assertIn("通道 1", zh)
        self.assertIn("channel 4", en)
        self.assertIn("channel 5", en)
        self.assertIn("channel 1", en)
        self.assertIn("7", zh)
        self.assertIn("7", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            self.assertIn("DMA1", blocks)
            self.assertIn("CNDTR", blocks)
            self.assertIn("10", blocks)
            self.assertIn("8", blocks)
            self.assertNotIn("21 µs", blocks)
            self.assertNotIn("21 us", blocks)
        self.assertIn("没有 DMA2", zh_blocks)
        self.assertIn("no DMA2", en_blocks)
        self.assertIn("作废", zh)
        self.assertIn("../assets/diagrams/sample-10-dma-cndtr.svg", zh)
        self.assertIn("../../assets/diagrams/sample-10-dma-cndtr.svg", en)
        self.assertIn("../assets/gif/dma-cndtr.gif", zh)
        self.assertIn("../../assets/gif/dma-cndtr.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-10-dma-cndtr.svg"), zh_key.index("dma-cndtr.gif"))
        self.assertLess(en_key.index("sample-10-dma-cndtr.svg"), en_key.index("dma-cndtr.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-dma": (
                "第 10 章。CNDTR 数的是数据项。8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节。半传输是 4 个采样、8 字节。ADC1 通道 1，USART1_TX 通道 4，USART1_RX 通道 5。循环模式归零后重装。不把 21 µs 写进来。不改 rm0090。",
                "Chapter 10. CNDTR counts data items. Eight half-words with CNDTR = 3 means 5 samples and 10 bytes. Half-transfer is 4 samples, 8 bytes. ADC1 is channel 1, USART1_TX is channel 4, and USART1_RX is channel 5. Circular mode reloads at zero. Does not put 21 µs here. Does not change rm0090.",
            ),
            "ds5319-dma": (
                "第 10 章。中密度是一个 7 通道的 DMA1。DMA2 在 STM32F103C8T6 上作废。",
                "Chapter 10. Medium-density parts have one 7-channel DMA1. DMA2 is void on STM32F103C8T6.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "stm32cube-f4", "st-h7-dma", "majerle-uart", "rm0090", "rm0008-dma", "ds5319-dma"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["10-DMA.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["10-dma.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual("2026-10-25", card_zh["accessed"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        self.assertEqual(baseline_manifests()[0]["sources"]["rm0090"], zh_manifest["sources"]["rm0090"])


if __name__ == "__main__":
    unittest.main()
