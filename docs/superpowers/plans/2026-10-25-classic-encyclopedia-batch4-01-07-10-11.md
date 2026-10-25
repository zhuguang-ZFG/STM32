# Batch 4 Chapters 01, 07, 10, and 11 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只加厚第 01、07、10、11 章（中文和英文一起），写成和第 00、02、03、04、05、06、08、09 章相同的四块密度，每章一张可印刷的静态主图加一条短 GIF 辅图，把 SWD 脚位、`0xA5`、I2C 地址、DMA 半字和看门狗的 1 秒改成和已冻结手册以及附录 D 同一笔账，合入时把整书升到 1.2.3 · 2026-10-25，然后停下来等人复审。人接受之前不合入。

**Architecture:** 章号已经由设计锁死，不再打分重选，也不拆成四份计划。四章共用一次版本号、一次来源追加和一次人审。先只读这四章的中英八份，确认四块还不存在、旧坑标题还在。来源清单和锁定文件已经随本计划提交。然后生成静态 SVG 和短 GIF，再改八份正文。新出处只追加进 `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `sources`。附录 E 的卡片仍由 `stm32-book/build_html.py` 的 `source_registry_html()` 生成。主图走 `tools/svgkit.py` 的 `tools/gen_sample_figures.py`。短 GIF 走 `tools/gen_gifs.py` 的 `BUILDERS`。版本号同时写进两份 manifest、`stm32-book/revisions.json` 和 `stm32-book/README.md`。日期写死 `2026-10-25`，不取实施当天的日期。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 -m unittest`、`tools/svgkit.py`、`tools/gen_gifs.py`、`tools/minigfx.py`、`tools/check_assets.py`。不新增依赖，不改 `requirements.txt`。

单文件测试写成 `python3 stm32-book/tests/<file>.py -v`。`stm32-book/tests/` 不是 Python 包。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

本计划不拆成四个子计划。设计规格把这四章锁成同一批，版本只升一次到 1.2.3。拆开会把一次人审拆成四次，或者让 1.2.3 先带着不完整的四章合入。

## Global Constraints

- 只把第 01、07、10、11 章加厚到和第 00、02、03、04、05、06、08、09 章相同的四块密度。中文和英文一起写完。文件名仍是 `docs/01-开发环境搭建.md`、`docs/en/01-dev-environment.md`、`docs/07-I2C总线.md`、`docs/en/07-i2c.md`、`docs/10-DMA.md`、`docs/en/10-dma.md`、`docs/11-RTC与看门狗.md`、`docs/en/11-rtc-watchdog.md`。
- 四块标题必须原样出现，各一次：中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`；英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。标题不加表情符号。四块插在 `<!-- /video: -->` 之后、学习目标之前。
- 保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。保留 `## 🧠 核心原理` 与 `## 🧠 Core ideas`。`## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls and troubleshooting` 删掉，不留空标题。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上。生成脚本是 `tools/gen_sample_figures.py`，画布是 `tools/svgkit.py`。不调用 `Svg.footer()`。落款用已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。没有 `<animate`、`@keyframes`、`animation:`。图注写「自绘」，英文图注写 `Drawn for this book`。替代文本写结论。单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。第 11 章的第二张只允许叫 `assets/diagrams/sample-11-rtc-prescaler.svg`。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 另加一条短 GIF，只做网页和公众号辅图。GIF 不替换主图，也不是关键插图这一节唯一的图。四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`。`minigfx.py` 只有 5×7 英文点阵，GIF 上的字用 ASCII。每条少于 500 KB。帧数不少于 3、不多于 12。`gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 改写吸收的许可顺序：先用 ST 公开 RM/DS/PM 的事实、用自己的话重写；然后才是 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。不把厂商手册、官方插图或社区原文放进仓库。SSD1306、AT24C02、MPU6050 的厂商手册和 UM10204 不吸收。不吸收 libopencm3。
- 订货号是 STM32F103C8T6，LQFP48。读者看到的章号仍是文件名前缀加 1。源文件的一级标题继续带 `01`、`07`、`10`、`11`。这一批不改这个加 1。文件 `01` 在书里是第 2 章，`07` 是第 8 章，`10` 是第 11 章，`11` 是第 12 章。
- 第 01 章：复位后 SWDIO 是第 34 脚 PA13，SWCLK 是第 37 脚 PA14。第 35 脚是 VSS_2，第 36 脚是 VDD_2。第 7 脚是 NRST，第 44 脚是 BOOT0。BOOT0=0 时 `0x00000000` 别名闪存 `0x08000000`。第 0 字是 MSP，第 1 字在 `0x00000004`，是 `Reset_Handler`。IRQ 入口是 `VTOR + 4×(IRQn + 16)`。BOOT1=0 且 BOOT0=1 取到系统存储器 `0x1FFFF000`，不是 SRAM。SRAM 要 BOOT1=1 且 BOOT0=1。无保护字节是 `0xA5`。PM0075 把这只键印成 `0x00A5`，低字节仍是 `0xA5`。`0xAA` 和 `0xCC` 在这颗料上作废。C8 是 64 KB 闪存、20 KB SRAM。xB 的 128 KB 作废。链接脚本里已有的 `LENGTH = 64K` 和 `LENGTH = 20K` 保持不动。
- 第 07 章：I2C1 在 APB1，PCLK1 = 36 MHz。复位默认是第 42 脚 PB6 = I2C1_SCL，第 43 脚 PB7 = I2C1_SDA，开漏，外接 4.7 kΩ 到 3.3 V。7 位 `0x3C` 的写地址是 `0x78`，读地址是 `0x79`。表 42 在 36 MHz、3.3 V、4.7 kΩ 下把 400 kHz 印成 `I2C_CCR = 0x801E`，100 kHz 印成 `0x00B4`。`0x801E` 的低 12 位是 30。达成速率留 ±2%，不把 400 kHz 写成保证的边沿。1 MHz 在这颗料上作废。`300ns / Cb` 留在核心原理当估算，不进四块。不把第 08 章的推挽片选写进来。
- 第 10 章：这颗中密度只有 DMA1，7 条通道，没有 DMA2。ADC1 = 通道 1，USART1_TX = 通道 4，USART1_RX = 通道 5。8 个半字且 `CNDTR = 3`：已写 5 个采样、10 字节。半传输是 4 个采样、8 字节。F4 的 USART1_RX 是 DMA2 Stream 5、Channel 4，FIFO 是 4 个 32 位字，这句在 C8 上作废。21 µs 不进这一章的四块。不改附录 A。
- 第 11 章：`T = 64 / 40000 × (624 + 1) = 1` s。Reload 625 多一个计数。LSI 是 30 / 40 / 60 kHz，40 kHz 是典型值，这一秒不是保证值。IWDG 只在减到 0 时复位，喂早不复位。WWDG 在 PCLK1 = 36 MHz、预分频 8、初值 `0x7F` 时超时 58.25 ms；计数器大于 `0x50` 时喂狗会复位。LSE 32.768 kHz，PRL = 32767 才是 1 Hz。备份寄存器是 10 个 16 位，共 20 字节。42 个在 C8 上作废。四块不写 6 pF，也不写 ±20 ppm 和 ±50%。代码里 Reload = 4095 的超时写成 `(4095 + 1) / 625 = 6.5536` s。不重画 `iwdg-window.svg`。
- 实施合入时把整书从 1.2.2 升到 **1.2.3**。中英文整书共用这个版本号。日期写死 **2026-10-25**。`accessed` 也写死 `2026-10-25`。不打 tag，不创建 GitHub Release。
- Book CI 变绿之后停下来等人复审。复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。CI 变绿不等于可以自动 squash 合入。
- 实施基线是 #33 合入之后的 `main` 尖端。写本计划时该尖端是 `ea11ce7b2dd02cec4e46a6abcb701a0286faef4a`（`docs: classic encyclopedia Batch4 01/07/10/11 design (#33)`）。其章节正文与 v1.2.2 `205fba7ba10000facbafece55a31f8372e4a541e` 相同，只多了设计规格。
- 不加厚除 01、07、10、11 以外的任何章，含 00、02、03、04、05、06、08、09 和 12–28。不重选样本。不改 `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json`，不改 `2026-10-25-sample-source-list.json`，不改 `2026-10-25-batch2-04-06-lock.json`，不改 `2026-10-25-batch2-04-06-source-list.json`，不改 `2026-10-25-batch3-02-05-08-09-lock.json`，不改 `2026-10-25-batch3-02-05-08-09-source-list.json`，不改 `tools/scan_sample_chapters.py`，不改 `tools/scan_batch2_chapters.py`，不改 `tools/scan_batch3_chapters.py`。不改总纲、Batch2 规格、Batch3 规格、观感规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。不改本批设计规格。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约，不改附录 D 三套账的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。不删 `test_build.py` 里 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py` 或 `test_batch3_chapters.py`。不新增读取 `CONTENT_GUIDE.md` 的测试。
- 不删除、不重画已有图。第 01 章留下 `boot-sequence.svg`、`project-structure.svg`。第 07 章留下 `i2c-transaction.svg`、`i2c-timing.gif`。第 10 章留下 `dma-circular.svg`、`dma-ring.gif`。第 11 章留下 `iwdg-window.svg`。不改这 12 条已有 GIF 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`。不重画 `sample-00-boot-state.svg`、`sample-02-clock-tree.svg`、`sample-03-gpio-led.svg`、`sample-04-exception-stack.svg`、`sample-05-pwm-1khz.svg`、`sample-06-uart-frame.svg`、`sample-08-spi-jedec.svg`、`sample-09-adc-sar.svg`。不把 `tools/svg2gif.py` 当成必经步骤。不改 `assets/video/`，不重写 `<!-- video: -->` 旁白。
- 新来源 id 只追加，顺序固定为 `ds5319-swd`、`pm0075-rdp`、`pm0056-vector`、`ds5319-i2c`、`rm0008-i2c`、`rm0008-dma`、`ds5319-dma`、`rm0008-wdg`、`rm0008-rtc`、`ds5319-rtc`。没有第十一个 id。已有 id 的对象一个字段都不改，含 `rm0008`、`ds5319`、`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`pm0056`、`pm0056-nvic`、`project-examples`、`rm0090`。中英两份 manifest 的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。
- 代码继续按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。不新开可烧录工程。不改 `examples/gpio-blink/`、`examples/spl-f1-blink/`、`examples/i2c-oled/`、`examples/adc-dma/`。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不改仓库根 `README.md` 里「6 个教学光栅动画」那一句。不预选文件 `12` 作为下一批。
- Keil、CubeIDE、PlatformIO、CLion 的授权和菜单路径留在第 01 章核心原理，不进四块，不进新来源的 scope。OpenOCD 的 `unlock` 命令行留在核心原理。AT24C02 的 `0x50`、MPU6050 的 `0x68` 和魔法值 `0xA5A5` 留在核心原理，不进出处卡。总线上补 9 个时钟的恢复留在核心原理，不进出处卡。
- PM0075 的 URL 用文件名含 `pm0075` 的那一份：`https://www.st.com/resource/en/programming_manual/pm0075-stm32f10xxx-flash-memory-microcontrollers-stmicroelectronics.pdf`。2026-10-25 这次下载的 PDF 是 31 页，页眉印 Doc ID 17863 Rev 2，修订史是 27-Aug-2012。读允许键印成 `0x00A5`。若实施时同一 URL 改道到文件名含 `CD00283419` 的 `https://` 地址，把清单和 manifest 的 `url` 改成返回这份 PDF 的地址，主张仍是 `0xA5` 和整片擦除。PDF 里同时找不到 `0xA5` 和 `0x00A5` 时停下来，不另编一个键。
- 向量表节号默认是 PM0056 Rev 7 第 2.3.4 节。这一节的标题若不是向量表，snapshot 的 `section` 改成印出「第 0 项是 MSP、第 1 项是 Reset」的那一节，主张不变。
- I2C 的 CCR 位默认是快速模式、DUTY = 0、字段值 30，与表 42 的 `0x801E` 一致。第 26 章印出的位不同时，用印出的位，表 42 的寄存器值仍是 `0x801E`，并在实施 PR 说明里写明差异。不编基址。
- 调试冻住的位名默认不写进四块，只写「可以冻住」，链接 `ds5319-rtc`。RM0008 第 17 章印出位名时，把名字补进 `rm0008-wdg` 的 snapshot，并在对应坑卡的主张里加上这个名字。不新开 id，也不编一个没印出来的位号。

## File map

| 路径 | 责任 |
| --- | --- |
| `tools/scan_batch4_chapters.py` | 只读 01、07、10、11 的中英八份，确认四块缺失、旧坑标题还在 |
| `docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json` | 核对结果。本计划提交时 `baseline` 是 `ea11ce7b2dd02cec4e46a6abcb701a0286faef4a`。实施开始时脚本把它改成当时的 `git rev-parse HEAD` |
| `docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-source-list.json` | 动笔前的来源清单。十个 absorb id，社区列表为空。登记以 manifest 为准 |
| `tools/gen_sample_figures.py` | 在现有八张静态主图之外追加四张。不改已有八个函数 |
| `assets/diagrams/sample-01-swd-vectors.svg` | 第 01 章主图 |
| `assets/diagrams/sample-07-i2c-addr.svg` | 第 07 章主图 |
| `assets/diagrams/sample-10-dma-cndtr.svg` | 第 10 章主图 |
| `assets/diagrams/sample-11-iwdg-1s.svg` | 第 11 章主图。超过 60 KB 时才另存 `sample-11-rtc-prescaler.svg` |
| `tools/gen_gifs.py` | `BUILDERS` 追加 `swd-fetch`、`i2c-addr`、`dma-cndtr`、`iwdg-1s` |
| `assets/gif/swd-fetch.gif` | 第 01 章辅图。只画取指的正常路径 |
| `assets/gif/i2c-addr.gif` | 第 07 章辅图。只画 `0x78` 和 ACK |
| `assets/gif/dma-cndtr.gif` | 第 10 章辅图。只画 5 个采样、10 字节 |
| `assets/gif/iwdg-1s.gif` | 第 11 章辅图。只画 Reload 624 的那一秒 |
| `assets/README.md` | 登记四张 SVG 和四条 GIF，并改 `iwdg-window.svg` 的说明 |
| 八份章节 Markdown | 四块，以及和附录 D、手册冲突的那几格 |
| `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` | 十个新 `sources`、四章罗盘、版本号 |
| `stm32-book/revisions.json` | 1.2.3 修订条目，插在数组最前 |
| `stm32-book/README.md` | 当前版本句，以及「也不要把 1.2.2 的产物标成 1.2.3」 |
| `CREDITS.md` | 第六节下面增加 v1.2.3 小节。静态框图张数改为 18。若拆出第二张第 11 章 SVG，改为 19。光栅动画个数改为 16 |
| `stm32-book/tests/test_batch4_sources.py` | 来源清单的许可门 |
| `stm32-book/tests/test_batch4_chapters.py` | 四块、共享数字、主图、GIF |
| `stm32-book/tests/test_build.py` | 只改当前版本断言。`0x271` 和书签条数保留 |

---

### Task 1: Gap scan and lock

**Files:**
- Create: `tools/scan_batch4_chapters.py`
- Modify: `docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json`（脚本用运行时 HEAD 重写 `baseline`。章号和布尔值保持不变）

**Interfaces:**
- Consumes: 八份原稿。不读别的章，不调用 `tools/scan_sample_chapters.py`，不调用 `tools/scan_batch2_chapters.py`，不调用 `tools/scan_batch3_chapters.py`。
- Produces: 锁定文件字段 `rubric`（字符串 `"2026-10-25-classic-encyclopedia-batch4-01-07-10-11"`）、`baseline`（40 位十六进制，等于运行时 `git rev-parse HEAD`）、`chapters`（`["01", "07", "10", "11"]`）、`four_blocks_absent`（`true`）、`old_pitfall_heading_present`（`true`）、`files`。`files` 的键是 `"01"`、`"07"`、`"10"`、`"11"`。每个值有 `zh`、`en`、`zh_four_blocks`、`en_four_blocks`、`zh_old_pitfall`、`en_old_pitfall`。后面的任务只改这四个前缀。

四块标题是中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`，英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。旧坑标题是中文 `## ⚠️ 常见坑与排查`，英文 `## ⚠️ Pitfalls and troubleshooting`。

在 `ea11ce7b2dd02cec4e46a6abcb701a0286faef4a` 上，这八份都还没有四块，旧坑标题都还在。本计划提交里的锁定文件已经记下这个结果。若执行时任何一份已经有四块，脚本退出码 2，不改写锁定文件，后面的任务停。不要在已有四块上再叠一套标题。

- [ ] **Step 1: 写入核对脚本**

把下面的程序保存为 `tools/scan_batch4_chapters.py`。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 01, 07, 10, and 11 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch4_chapters.py

Rewrites docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json and
exits 0 when all eight manuscripts lack the four headings and still have the
old pitfall heading. Exits 2 without writing the lock if a four-block heading
is already present, or if the old pitfall heading is already gone.
Does not score other chapters and does not touch the sample lock, the
batch-2 lock, or the batch-3 lock.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-lock.json"
FILES = {
    "01": (
        ROOT / "docs" / "01-开发环境搭建.md",
        ROOT / "docs" / "en" / "01-dev-environment.md",
    ),
    "07": (
        ROOT / "docs" / "07-I2C总线.md",
        ROOT / "docs" / "en" / "07-i2c.md",
    ),
    "10": (
        ROOT / "docs" / "10-DMA.md",
        ROOT / "docs" / "en" / "10-dma.md",
    ),
    "11": (
        ROOT / "docs" / "11-RTC与看门狗.md",
        ROOT / "docs" / "en" / "11-rtc-watchdog.md",
    ),
}
ZH_BLOCKS = ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡")
EN_BLOCKS = (
    "## Principle and boundary",
    "## Key figures",
    "## Timing or state",
    "## Pitfalls and source cards",
)
ZH_OLD = "## ⚠️ 常见坑与排查"
EN_OLD = "## ⚠️ Pitfalls and troubleshooting"


def four_blocks(text: str, headings: tuple[str, ...]) -> bool:
    return any(heading in text for heading in headings)


def main() -> int:
    payload_files: dict[str, dict] = {}
    blocked = False
    for prefix, (zh_path, en_path) in FILES.items():
        if not zh_path.is_file() or not en_path.is_file():
            print(f"missing manuscript for {prefix}", file=sys.stderr)
            return 2
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        row = {
            "zh": zh_path.relative_to(ROOT).as_posix(),
            "en": en_path.relative_to(ROOT).as_posix(),
            "zh_four_blocks": four_blocks(zh, ZH_BLOCKS),
            "en_four_blocks": four_blocks(en, EN_BLOCKS),
            "zh_old_pitfall": ZH_OLD in zh,
            "en_old_pitfall": EN_OLD in en,
        }
        payload_files[prefix] = row
        if row["zh_four_blocks"] or row["en_four_blocks"]:
            print(f"{prefix} already has a four-block heading; stop", file=sys.stderr)
            blocked = True
        if not row["zh_old_pitfall"] or not row["en_old_pitfall"]:
            print(f"{prefix} is missing the old pitfall heading; stop", file=sys.stderr)
            blocked = True
        print(
            f"{prefix} four_blocks={'yes' if row['zh_four_blocks'] or row['en_four_blocks'] else 'no'} "
            f"old_pitfall={'yes' if row['zh_old_pitfall'] and row['en_old_pitfall'] else 'no'}"
        )
    if blocked:
        return 2
    baseline = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    payload = {
        "rubric": "2026-10-25-classic-encyclopedia-batch4-01-07-10-11",
        "baseline": baseline,
        "chapters": ["01", "07", "10", "11"],
        "four_blocks_absent": True,
        "old_pitfall_heading_present": True,
        "files": payload_files,
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"baseline={baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 在改任何章节之前运行核对**

Run: `python3 tools/scan_batch4_chapters.py`

Expected: 退出码 0，标准输出含

```text
01 four_blocks=no old_pitfall=yes
07 four_blocks=no old_pitfall=yes
10 four_blocks=no old_pitfall=yes
11 four_blocks=no old_pitfall=yes
baseline=
```

`baseline=` 后面是当时 `git rev-parse HEAD` 的 40 位哈希。锁定文件里 `chapters` 仍为 `["01", "07", "10", "11"]`，`four_blocks_absent` 仍为 `true`，`old_pitfall_heading_present` 仍为 `true`。`baseline` 被改成这次运行的 HEAD。这个 HEAD 必须还没有新的 `sources`，也还没有四块。

若退出码为 2：停止。不要改四块标题去凑退出码 0，也不要改 `tools/scan_sample_chapters.py`。

- [ ] **Step 3: 确认样本锁定、Batch2 锁定、Batch3 锁定和设计规格没被改写**

Run:

```bash
git diff --name-only -- docs/superpowers/plans/2026-10-25-sample-chapter-lock.json docs/superpowers/plans/2026-10-25-sample-source-list.json docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch2-04-06-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch3-02-05-08-09-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md tools/scan_sample_chapters.py tools/scan_batch2_chapters.py tools/scan_batch3_chapters.py
```

Expected: 无输出。

- [ ] **Step 4: Commit**

```bash
git add tools/scan_batch4_chapters.py docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json
git commit -m "docs: 锁定第 01、07、10、11 章尚未加厚"
```

这一笔提交里不要带 manifest 或章节正文。锁定文件里的 `baseline` 必须仍指向还没有新 `sources` 的那次提交。

### Task 2: Source list with the license gate

**Files:**
- Modify: `docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-source-list.json`（只在下面三处核对印出的文字和清单不同时才改 snapshot 或 url。默认不改）
- Create: `stm32-book/tests/test_batch4_sources.py`
- Test: `stm32-book/tests/test_batch4_sources.py`

**Interfaces:**
- Consumes: Task 1 的 `chapters == ["01", "07", "10", "11"]`，以及 `four_blocks_absent == true`。已提交的来源清单。
- Produces: 十个新 id，顺序固定为 `ds5319-swd`、`pm0075-rdp`、`pm0056-vector`、`ds5319-i2c`、`rm0008-i2c`、`rm0008-dma`、`ds5319-dma`、`rm0008-wdg`、`rm0008-rtc`、`ds5319-rtc`。不产生第十一个 id。`community` 是空数组。`reuse_existing` 的 id 顺序是 `rm0008-boot`、`project-examples`、`rm0090`。这三个 id 不新建 manifest 对象。

来源清单已经随本计划提交。实施时不要另写一份。许可门测试去读这份文件。

2026-10-25 设计规格冻结的事实，实施时打开同一批 URL。首页修订或节号变了就停，先改清单里的 `snapshot` 和 `section`，再画图、再写正文。数字本身不变：

- DS5319 Rev 20（July 2025）表 5、表 25、表 41、表 42，第 2.3.13、2.3.14、2.3.15 节，和 `ds5319-gpio` 是同一份 PDF。
- RM0008 Rev 21（February 2021）第 10、16、17、18、26 章，以及 PWR 章里的 `PWR_CR` DBP。PDF 与已有 `rm0008-boot` 相同。
- PM0056 Rev 7（December 2024）与已有 `pm0056-nvic` 是同一份 PDF。默认节号 2.3.4。
- PM0075 Doc ID 17863 Rev 2（August 2012，修订史 27 August 2012）。`0x1FFFF800` 的低字节是 RDP。手册印出的读允许键是 `0x00A5`。编程回这个键会先整片擦除主闪存。`WDG_SW` 为 0 是硬件看门狗，为 1 是软件看门狗。

打开这些 URL：

- `https://www.st.com/resource/en/datasheet/stm32f103c8.pdf`
- `https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf`
- `https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf`
- `https://www.st.com/resource/en/programming_manual/pm0075-stm32f10xxx-flash-memory-microcontrollers-stmicroelectronics.pdf`

四份里有打不开的就停。不要换一份别的手册来补皮法、基址或另一个读保护键。

社区例程这一批不冻结。来源清单的 `community` 是空数组。不吸收未写许可的博客，不吸收 GPL 的 libopencm3，不吸收屏厂、EEPROM 厂或传感器厂的手册，不吸收 UM10204 的句子。

- [ ] **Step 1: 写许可门测试**

保存为 `stm32-book/tests/test_batch4_sources.py`：

```python
#!/usr/bin/env python3
"""License gate for chapters 01, 07, 10, and 11. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-lock.json"
ALLOWED = {
    "ST-facts-restated",
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "CC BY 4.0",
    "CC BY 3.0",
    "CC0",
}
REJECTED = ("GPL", "LGPL", "CC BY-NC", "CC BY-ND", "All rights reserved", "Apache-2.0")
ABSORB = [
    "ds5319-swd",
    "pm0075-rdp",
    "pm0056-vector",
    "ds5319-i2c",
    "rm0008-i2c",
    "rm0008-dma",
    "ds5319-dma",
    "rm0008-wdg",
    "rm0008-rtc",
    "ds5319-rtc",
]


class Batch4SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_01_07_10_11(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["01", "07", "10", "11"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch4-01-07-10-11", lock["rubric"])
        for prefix, zh_name, en_name in (
            ("01", "docs/01-开发环境搭建.md", "docs/en/01-dev-environment.md"),
            ("07", "docs/07-I2C总线.md", "docs/en/07-i2c.md"),
            ("10", "docs/10-DMA.md", "docs/en/10-dma.md"),
            ("11", "docs/11-RTC与看门狗.md", "docs/en/11-rtc-watchdog.md"),
        ):
            row = lock["files"][prefix]
            self.assertEqual(zh_name, row["zh"])
            self.assertEqual(en_name, row["en"])
            self.assertFalse(row["zh_four_blocks"])
            self.assertFalse(row["en_four_blocks"])
            self.assertTrue(row["zh_old_pitfall"])
            self.assertTrue(row["en_old_pitfall"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["01", "07", "10", "11"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(ABSORB, ids)
        self.assertEqual(10, len(ids))
        for item in payload["absorb"]:
            self.assertIn(item["license_class"], ALLOWED)
            self.assertTrue(item["url"].startswith("https://"))
            self.assertNotIn("http://", item["url"])
            for banned in REJECTED:
                self.assertNotIn(banned, item["license"])
                self.assertNotIn(banned, item["license_class"])
            self.assertTrue(item["do_not_copy"])
            self.assertGreaterEqual(len(item["points"]), 1)
        by_id = {item["id"]: item for item in payload["absorb"]}
        self.assertEqual("Table 5", by_id["ds5319-swd"]["section"])
        self.assertEqual("2.4.1", by_id["pm0075-rdp"]["section"])
        self.assertEqual("2.3.4", by_id["pm0056-vector"]["section"])
        self.assertEqual("Table 42", by_id["ds5319-i2c"]["section"])
        self.assertEqual("26", by_id["rm0008-i2c"]["section"])
        self.assertEqual("10", by_id["rm0008-dma"]["section"])
        self.assertEqual("2.3.13", by_id["ds5319-dma"]["section"])
        self.assertEqual("17", by_id["rm0008-wdg"]["section"])
        self.assertEqual("16", by_id["rm0008-rtc"]["section"])
        self.assertEqual("Table 25", by_id["ds5319-rtc"]["section"])
        rdp = by_id["pm0075-rdp"]["snapshot"]
        self.assertIn("0x00A5", rdp)
        self.assertIn("mass erase", rdp)
        self.assertNotIn("0xCC", rdp)
        rtc = by_id["ds5319-rtc"]["snapshot"]
        self.assertNotIn("pF", rtc)
        self.assertNotIn("ppm", rtc)
        self.assertNotIn("50%", rtc)
        i2c = by_id["rm0008-i2c"]["snapshot"]
        self.assertNotIn("0x40005400", i2c)
        dma = by_id["rm0008-dma"]["snapshot"]
        self.assertNotIn("21 µs", dma)
        self.assertNotIn("21 us", dma)
        vector = by_id["pm0056-vector"]["snapshot"]
        self.assertNotIn("167 ns", vector)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(["rm0008-boot", "project-examples", "rm0090"], reused)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试**

Run: `python3 stm32-book/tests/test_batch4_sources.py -v`

Expected: OK，两条测试都通过。清单已经在本计划提交里，所以这一步不是 `FileNotFoundError`。若失败，改清单去满足上面的断言，不要放宽 `ABSORB`，也不要删掉测试来制造一次红色。不要追加第十一个 id。

锁定文件那一条若失败，先回到 Task 1。不要改测试去迁就一份章号不对的锁。

- [ ] **Step 3: 打开四份 PDF，只核对会改 snapshot 的三处**

打开 Task 2 开头的四个 URL。

RDP：在 PM0075 里找读允许键和整片擦除。写本计划时，Doc ID 17863 Rev 2 把键印成 `0x00A5`，并写明编程回这个键会先对主闪存做 Mass Erase。`WDG_SW` 为 0 是硬件看门狗，为 1 是软件看门狗。印出的句子还在，清单不动。同一 URL 若改道到文件名含 `CD00283419` 的地址，把 `pm0075-rdp` 的 `url` 改成返回这份 PDF 的 `https://` 地址。PDF 里同时找不到 `0xA5` 和 `0x00A5`，或者找不到整片擦除这句，就停下来，不另编一个键。

向量表：读 PM0056 Rev 7 第 2.3.4 节的标题。标题就是向量表，并且第 0 项是 MSP、第 1 项是 Reset，清单的 `section` 保持 `2.3.4`。标题不是向量表，把 `section` 和 snapshot 里的节号改成印出这两项的那一节。主张不变。不要把 167 ns 写进 snapshot。

CCR 位：读 RM0008 Rev 21 第 26 章印出的快速模式 CCR。默认 `0x801E` 是快速模式、DUTY = 0、低 12 位为 30。印出的位相同，清单不动。印出的位不同，把 `rm0008-i2c` 的 snapshot 改成印出的位，400 kHz 那一行仍写表 42 的 `0x801E`，并在实施 PR 说明里写明差异。不编 I2C 基址。

调试冻住：在 RM0008 Rev 21 第 17 章找独立看门狗在调试时冻住计数器的位名。没印出来，`rm0008-wdg` 的 snapshot 保持现在这句 `A debug-freeze bit name is added here only if chapter 17 prints it.`，四块只写「可以冻住」。印出来了，把印出的名字补进这个 snapshot，不新开 id，也不编一个没印出来的位号。

无论哪一处，都不要改 `license_class`，不要改另外七个 id 的 `points`。

- [ ] **Step 4: 再跑测试并提交**

Run: `python3 stm32-book/tests/test_batch4_sources.py -v`

Expected: OK。

```bash
git add stm32-book/tests/test_batch4_sources.py docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-source-list.json
git commit -m "docs: 钉上 01、07、10、11 的许可门"
```

若清单相对本计划提交没有差异，`git add` 里带上它也没有关系，提交内容里可以只有测试文件。不要在这一笔里改章节正文。

### Task 3: Static key figures

**Files:**
- Modify: `tools/gen_sample_figures.py`（只追加函数，并在 `main()` 里多保存四张。不改 `boot_state`、`gpio_led`、`exception_stack`、`uart_frame`、`clock_tree`、`pwm_1khz`、`spi_jedec`、`adc_sample`、`_credit`）
- Create: `assets/diagrams/sample-01-swd-vectors.svg`
- Create: `assets/diagrams/sample-07-i2c-addr.svg`
- Create: `assets/diagrams/sample-10-dma-cndtr.svg`
- Create: `assets/diagrams/sample-11-iwdg-1s.svg`
- Modify: `assets/README.md`（开头的生成命令，第四节表的末尾，以及第一节里 `iwdg-window.svg` 那一行）
- Create: `stm32-book/tests/test_batch4_chapters.py`
- Test: `stm32-book/tests/test_batch4_chapters.py`

**Interfaces:**
- Consumes: Task 2 清单里的订货号、脚位和寄存器名。已有的 `_credit(canvas, note)`。
- Produces: `swd_vectors() -> Svg`、`i2c_addr() -> Svg`、`dma_cndtr() -> Svg`、`iwdg_1s() -> Svg`。四张 SVG 不含 `<animate`、`@keyframes`、`animation:`，不含「矢量动画」，不含「实拍」，含「自绘」。每张都小于 60 KB。默认不产生 `sample-11-rtc-prescaler.svg`。

`sample-01-swd-vectors.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`pin 34`、`PA13`、`SWDIO`、`pin 35`、`VSS_2`、`pin 36`、`VDD_2`、`pin 37`、`PA14`、`SWCLK`、`pin 44`、`BOOT0`、`0x08000000`、`0x00000000`、`MSP`、`Reset_Handler`、`GPIO`、`0x1FFFF000`、`0xA5`、`0xAA`、`64 KB`、`20 KB`。

`sample-07-i2c-addr.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`pin 42`、`PB6`、`pin 43`、`PB7`、`4.7`、`0x78`、`0x3C`、`0x801E`、`400 kHz`、`ACK`、`NACK`、`36 MHz`、`0x00B4`。

`sample-10-dma-cndtr.svg` 的文本含 `STM32F103C8T6`、`DMA1`、`channel 4`、`CNDTR`、`8`、`3`、`5 samples`、`10 bytes`、`4 samples`、`8 bytes`、`DMA2`、`pin 30`、`PA9`。不含 `21 us`。

`sample-11-iwdg-1s.svg` 的文本含 `STM32F103C8T6`、`40 kHz`、`30 kHz`、`60 kHz`、`prescaler 64`、`625 Hz`、`Reload = 624`、`Reload = 625`、`pin 1`、`VBAT`、`pin 3`、`pin 4`、`32767`、`32768`、`0x50`、`58.25`。不含 `6 pF`。

- [ ] **Step 1: 写会失败的主图测试**

保存为 `stm32-book/tests/test_batch4_chapters.py`：

```python
#!/usr/bin/env python3
"""Checks for thickened chapters 01, 07, 10, and 11 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为文件不存在而失败**

Run: `python3 stm32-book/tests/test_batch4_chapters.py -v`

Expected: FAIL，`sample-01-swd-vectors.svg` 不存在（`FileNotFoundError`）。

- [ ] **Step 3: 追加四个生成函数并写出 SVG**

在 `tools/gen_sample_figures.py` 的 `adc_sample()` 之后、`main()` 之前插入下面四个函数。不要改已有八个函数，也不要改 `_credit`。

```python
def swd_vectors() -> Svg:
    canvas = Svg(
        960,
        980,
        "SWCLK 在第 37 脚；BOOT0=0 时第 0 字是栈、第 1 字是复位；无保护字节是 0xA5",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 表 5",
    )
    canvas.header(tag="01", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 34 PA13 = SWDIO    pin 37 PA14 = SWCLK", size=14, fill=T.CYAN)
    canvas.text(40, 138, "pin 35 VSS_2    pin 36 VDD_2    pin 44 BOOT0 = 0", size=14, fill=T.AMBER)
    canvas.text(40, 164, "程序写入 0x08000000。0x00000000 别名到这块闪存", size=14, fill=T.TEXT)
    canvas.text(40, 196, "正常路径  第 0 字 MSP，第 1 字 Reset_Handler，然后才到 main", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 210, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 240, "读 0x00000000 得到 MSP", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 266, "读 0x00000004 得到 Reset_Handler", size=14, fill=T.GREEN)
    canvas.text(56, 292, "物理存储器是 0x08000000 起的 64 KB。SRAM 是 20 KB，从 0x20000000 起", size=14, fill=T.TEXT)
    canvas.text(56, 318, "无保护字节是 0xA5。RDP 编程回 0xA5 会先整片擦除主闪存", size=14, fill=T.AMBER)
    canvas.text(56, 344, "IRQ 入口是 VTOR + 4×(IRQn + 16)", size=13, fill=T.MUTED)
    canvas.text(40, 386, "失败路径  同一对 PA13/PA14 被配成 GPIO", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 400, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 430, "Debug 关掉之后，下一次探针在这两只脚上连不上", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 456, "pin 34 和 pin 37 不再是 SWDIO / SWCLK", size=14, fill=T.RED)
    canvas.text(56, 482, "SYS Debug 要留在 Serial Wire", size=14, fill=T.AMBER)
    canvas.rect(40, 540, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 570, "旁注  pin 35 被当成 SWCLK 会接空", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 596, "BOOT1=0 且 BOOT0=1 时取到 0x1FFFF000，不是 SRAM", size=14, fill=T.TEXT)
    canvas.text(56, 622, "0xAA 不是这颗料的无保护。128 KB 在 C8T6 上作废", size=14, fill=T.AMBER)
    canvas.text(56, 648, "第 39 脚 PB3 默认是 JTDO。SWO 不在正常路径上", size=13, fill=T.MUTED)
    canvas.text(56, 672, "不把第 00 章的整张启动表再画一遍", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。脚位来自 DS5319 Rev 20 表 5；两字来自 PM0056；0xA5 来自 PM0075。")
    return canvas


def i2c_addr() -> Svg:
    canvas = Svg(
        960,
        920,
        "HAL 送出的写地址是 0x78；0x801E 是 36 MHz 下表 42 的 400 kHz 行；0x3C 原样送出时第 9 个时钟没有 ACK",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 表 42",
    )
    canvas.header(tag="07", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  I2C1  APB1", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 42 PB6 = SCL    pin 43 PB7 = SDA", size=14, fill=T.CYAN)
    canvas.text(40, 138, "两只 4.7 kΩ 接到 3.3 V    PCLK1 = 36 MHz    I2C_CCR = 0x801E", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  START 之后线上第一字节是 0x78", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "第 9 个时钟 SDA 为低，ACK", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "目标速率 400 kHz，旁边是表 42 的 ±2%，不是保证值", size=14, fill=T.GREEN)
    canvas.text(56, 266, "0x801E：快速模式，DUTY = 0，CCR 字段 = 30", size=14, fill=T.TEXT)
    canvas.text(56, 292, "3 × 30 / 36e6 = 2.5 µs", size=14, fill=T.AMBER)
    canvas.text(56, 316, "100 kHz 那一行是 0x00B4。PB8/PB9 不在这条路径上", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  DevAddress 填了 0x3C", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "线上第一字节是 0x3C，7 位地址变成 0x1E", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "第 9 个时钟 SDA 仍为高，NACK", size=14, fill=T.RED)
    canvas.text(56, 456, "读方向的线上字节是 0x79，不占这条失败路径", size=14, fill=T.AMBER)
    canvas.rect(40, 514, 880, 110, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 544, "旁注  只有片内上拉时，不把这张图画成 400 kHz", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 570, "1 MHz 不在表 41、表 42 里", size=14, fill=T.TEXT)
    canvas.text(56, 596, "USART1 的重映射不是复位默认。不画推挽片选", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。CCR 与脚位来自 DS5319 Rev 20 表 42 和表 5；地址字节来自 RM0008 Rev 21 第 26 章。")
    return canvas


def dma_cndtr() -> Svg:
    canvas = Svg(
        960,
        900,
        "8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节；把剩余计数当成字节会切错",
        "STM32F103C8T6 · RM0008 Rev 21 第 10 章",
    )
    canvas.header(tag="10", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  只有 DMA1，7 条通道", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "USART1_TX 走 channel 4。宽度是半字。缓冲区长度 8", size=14, fill=T.CYAN)
    canvas.text(40, 138, "TX 仍从 pin 30 PA9 出去。不重画 8N1 帧", size=14, fill=T.MUTED)
    canvas.text(40, 170, "正常路径  CNDTR = 3", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "已写 5 samples，10 bytes", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "8 − 3 = 5，再乘 2 才是字节", size=14, fill=T.GREEN)
    canvas.text(56, 266, "半传输刻度在第 4 samples，8 bytes，不是 4 字节", size=14, fill=T.AMBER)
    canvas.text(56, 292, "ADC1 = channel 1。USART1_RX = channel 5", size=14, fill=T.TEXT)
    canvas.text(56, 316, "归零后硬件重装 CNDTR。长度减 CNDTR 不是累计", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  同一读数被当成字节", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "还剩 3 字节、已写 5 字节。后一半从错误的边界切开", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "CNDTR 数的是数据项，不是字节", size=14, fill=T.RED)
    canvas.text(56, 456, "半字数组会从奇数边界切开", size=14, fill=T.AMBER)
    canvas.rect(40, 504, 880, 100, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 534, "旁注  DMA2 Stream 5 在这颗 C8 上没有计数器", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 560, "F4 的那一组号留在 F4。不画采样电容", size=14, fill=T.TEXT)
    canvas.text(56, 584, "内存到内存若占用通道 1，它和 ADC1 抢同一条通道", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。CNDTR 来自 RM0008 Rev 21 第 10 章；只有 DMA1 来自 DS5319 Rev 20 第 2.3.13 节。")
    return canvas


def iwdg_1s() -> Svg:
    canvas = Svg(
        960,
        980,
        "Reload 624 在 40 kHz 典型值下是 1 秒；减到 0 才复位；LSE 要 PRL = 32767 才是 1 Hz",
        "STM32F103C8T6 · DS5319 Rev 20 表 25",
    )
    canvas.header(tag="11", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  IWDG  典型 40 kHz，范围 30 kHz 到 60 kHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "prescaler 64    计数频率 625 Hz    Reload = 624", size=14, fill=T.CYAN)
    canvas.text(40, 138, "64 / 40000 × (624 + 1) = 1 s。这是典型值，不是保证值", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  计数器还大于 0 时喂狗，不复位", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 130, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "这一次喂狗发生在超时之前", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "喂早对 IWDG 不是复位条件", size=14, fill=T.GREEN)
    canvas.text(56, 266, "30 kHz 时同一套数是 4/3 s。60 kHz 时是 2/3 s", size=14, fill=T.TEXT)
    canvas.text(56, 292, "Stop 和 Standby 里计数不停。调试时可以冻住", size=13, fill=T.MUTED)
    canvas.text(40, 340, "失败路径  同一条计数减到 0，没有喂狗，复位", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 354, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 384, "Reload = 625 会多一个计数", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 410, "(625 + 1) / 625 比 1 秒多一拍", size=14, fill=T.RED)
    canvas.text(56, 436, "不把 6.55 s 画成第二套规范", size=14, fill=T.AMBER)
    canvas.rect(40, 484, 880, 160, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 514, "备份域  pin 1 VBAT    pin 3 PC14    pin 4 PC15", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 540, "32.768 kHz，PRL = 32767，10 个 16 位寄存器，20 字节", size=14, fill=T.TEXT)
    canvas.text(56, 566, "PRL = 32768 不是 1 Hz。42 个备份寄存器在这颗料上作废", size=14, fill=T.AMBER)
    canvas.text(56, 592, "窗口看门狗：计数器大于 0x50 时喂狗会复位", size=14, fill=T.TEXT)
    canvas.text(56, 618, "超时尺度是 58.25 ms，不和 IWDG 的 1 秒画成同一种狗", size=13, fill=T.MUTED)
    canvas.text(56, 642, "不画负载电容的皮法，也不画 PC13 的 LED", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。LSI 与备份寄存器来自 DS5319 Rev 20 表 25、第 2.3.14 节和第 2.3.15 节；1 秒来自 RM0008 Rev 21 第 17 章。")
    return canvas
```

把 `main()` 换成：

```python
def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    boot_state().save(os.path.join(out_dir, "sample-00-boot-state.svg"))
    gpio_led().save(os.path.join(out_dir, "sample-03-gpio-led.svg"))
    exception_stack().save(os.path.join(out_dir, "sample-04-exception-stack.svg"))
    uart_frame().save(os.path.join(out_dir, "sample-06-uart-frame.svg"))
    clock_tree().save(os.path.join(out_dir, "sample-02-clock-tree.svg"))
    pwm_1khz().save(os.path.join(out_dir, "sample-05-pwm-1khz.svg"))
    spi_jedec().save(os.path.join(out_dir, "sample-08-spi-jedec.svg"))
    adc_sample().save(os.path.join(out_dir, "sample-09-adc-sar.svg"))
    swd_vectors().save(os.path.join(out_dir, "sample-01-swd-vectors.svg"))
    i2c_addr().save(os.path.join(out_dir, "sample-07-i2c-addr.svg"))
    dma_cndtr().save(os.path.join(out_dir, "sample-10-dma-cndtr.svg"))
    iwdg_1s().save(os.path.join(out_dir, "sample-11-iwdg-1s.svg"))
```

Run: `python3 tools/gen_sample_figures.py`

Expected: 退出码 0。四张新 SVG 出现在 `assets/diagrams/`。测试只要求小于 60 KB。`sample-11-iwdg-1s.svg` 小于 60 KB 时，不要另写 `sample-11-rtc-prescaler.svg`。它达到或超过 60 KB 时，把备份域那一块拆进 `rtc_prescaler() -> Svg`，文件名 `sample-11-rtc-prescaler.svg`，两张都用 `_credit()`，都不调用 `Svg.footer()`，`main()` 多保存这一张。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。若已有八张 `sample-00` 到 `sample-09` 出现内容 diff，说明旧函数被改过，先还原那八个函数再生成。不要把这八张旧图的改动提交进来。

在 `assets/README.md` 开头的生成命令里，把

```bash
python3 tools/gen_sample_figures.py   # 第 00、02、03、04、05、06、08、09 章的静态主图
```

换成

```bash
python3 tools/gen_sample_figures.py   # 第 00、01、02、03、04、05、06、07、08、09、10、11 章的静态主图
```

第一节表格里这一行：

```markdown
| `iwdg-window.svg` | 独立看门狗计数与喂狗窗口（过早/过晚都复位） | 11 |
```

换成：

```markdown
| `iwdg-window.svg` | 辅图：独立看门狗只惩罚喂晚，喂早也复位的是窗口看门狗。文件不重画 | 11 |
```

第四节表格末尾追加这四行，不要另起一列。只有拆出第二张时才加第五行：

```markdown
| `sample-01-swd-vectors.svg` | 第 01 章静态主图：第 34 脚 PA13 与第 37 脚 PA14 上的取指，以及这两只脚被配成 GPIO、第 35 脚被当成 SWCLK。由 `tools/gen_sample_figures.py` 生成 |
| `sample-07-i2c-addr.svg` | 第 07 章静态主图：第 42、43 脚上的写地址 0x78 与 ACK，以及 DevAddress 填 0x3C 时的 NACK。由 `tools/gen_sample_figures.py` 生成 |
| `sample-10-dma-cndtr.svg` | 第 10 章静态主图：8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节，以及把剩余计数当成字节。由 `tools/gen_sample_figures.py` 生成 |
| `sample-11-iwdg-1s.svg` | 第 11 章静态主图：预分频 64、Reload 624 在 40 kHz 典型值下的 1 秒，以及减到 0 才复位。由 `tools/gen_sample_figures.py` 生成 |
```

拆图时追加的那一行是：

```markdown
| `sample-11-rtc-prescaler.svg` | 第 11 章静态局部：LSE、PRL = 32767 与 10 个备份寄存器。主图放不下 60 KB 时才拆出。由 `tools/gen_sample_figures.py` 生成 |
```

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch4_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_sample_figures.py assets/diagrams/sample-01-swd-vectors.svg assets/diagrams/sample-07-i2c-addr.svg assets/diagrams/sample-10-dma-cndtr.svg assets/diagrams/sample-11-iwdg-1s.svg assets/README.md stm32-book/tests/test_batch4_chapters.py
git commit -m "assets: 为 01、07、10、11 加上可印刷的静态主图"
```

若拆出了 `sample-11-rtc-prescaler.svg`，把它一并 `git add`。提交前再看一眼：

```bash
git diff --stat -- assets/diagrams/sample-00-boot-state.svg assets/diagrams/sample-02-clock-tree.svg assets/diagrams/sample-03-gpio-led.svg assets/diagrams/sample-04-exception-stack.svg assets/diagrams/sample-05-pwm-1khz.svg assets/diagrams/sample-06-uart-frame.svg assets/diagrams/sample-08-spi-jedec.svg assets/diagrams/sample-09-adc-sar.svg assets/diagrams/iwdg-window.svg
```

Expected: 无输出。`iwdg-window.svg` 的字节与基线相同。改的是 `assets/README.md` 里的说明，不是这张 SVG。

### Task 4: Short auxiliary GIFs

**Files:**
- Modify: `tools/gen_gifs.py`（在 `BUILDERS` 之前追加四个函数，并给字典加四个键。不改已有十二个函数）
- Create: `assets/gif/swd-fetch.gif`
- Create: `assets/gif/i2c-addr.gif`
- Create: `assets/gif/dma-cndtr.gif`
- Create: `assets/gif/iwdg-1s.gif`
- Modify: `assets/README.md`（第五节的表，以及「上面 12 张」那两句）
- Modify: `stm32-book/tests/test_batch4_chapters.py`
- Test: `stm32-book/tests/test_batch4_chapters.py`

**Interfaces:**
- Consumes: `tools/minigfx.py` 的 `Canvas`、`Gif`、`C`，以及 `chrome()`。
- Produces: `swd_fetch()`、`i2c_addr()`、`dma_cndtr()`、`iwdg_1s()`，各返回一帧数在 3 到 12 之间的 `Gif`。`BUILDERS` 的键在原有 12 个之后增加 `"swd-fetch"`、`"i2c-addr"`、`"dma-cndtr"`、`"iwdg-1s"`。`swd_fetch` 的源码含 `pin 34`、`pin 37`、`MSP`、`Reset_Handler`，不含 `0xAA`，不含 `GPIO`。`i2c_addr` 的源码含 `0x78`、`0x801E`、`4.7`、`ACK`，不含 `0x3C`。`dma_cndtr` 的源码含 `CNDTR`、`5 samples`、`10 bytes`，不含 `DMA2`，不含 `3 bytes`。`iwdg_1s` 的源码含 `Reload = 624`、`40 kHz`、`625 Hz`，不含 `Reload = 625`，不含 `0x50`。四条 GIF 文件都小于 500 KB。

- [ ] **Step 1: 把 GIF 断言加进测试**

在 `stm32-book/tests/test_batch4_chapters.py` 的文件头增加 `import importlib.util`，并在 `Batch4FigureTests` 之后追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4GifTests -v`

Expected: FAIL，`BUILDERS` 里没有 `swd-fetch`。

- [ ] **Step 3: 追加四个 BUILDERS 并生成 GIF**

在 `tools/gen_gifs.py` 里，`BUILDERS = {` 之前插入。四个函数按 `swd_fetch`、`i2c_addr`、`dma_cndtr`、`iwdg_1s` 的顺序紧挨着，中间不要插入别的 `def`。

```python
def swd_fetch():
    """SWD writes Flash, then the CPU reads MSP and Reset_Handler.

    GPIO reuse and 0xAA stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    lines = (
        "WRITE 0x08000000",
        "pin 34 SWDIO",
        "pin 37 SWCLK",
        "READ MSP",
        "READ Reset_Handler",
        "BOOT0 = 0",
    )
    for index, line in enumerate(lines):
        c = Canvas(W, H)
        chrome(c, "SWD FETCH", "BOOT0=0", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 48, 448, 36, C.PANEL, C.STROKE)
        c.text("pin 34  pin 37", 28, 60, C.CYAN, 1)
        c.text(line, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("MSP THEN Reset_Handler", 28, 200, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 222, C.DIM, 1)
        g.add(c)
    return g


def i2c_addr():
    """START, shift 0x78, then ACK on the 9th clock.

    A raw 0x3C and a missing pull-up stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "START",
        "SHIFT 0x78",
        "BIT 7 TO BIT 0",
        "9TH CLOCK",
        "SDA LOW  ACK",
        "0x801E  4.7 k",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "I2C ADDR", "0x78", "AUX GIF  ACK")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("PB6 SCL  PB7 SDA", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("0x78 THEN ACK", 28, 200, C.GREEN, 1)
        c.text("0x801E AND 4.7 k", 28, 222, C.CYAN, 1)
        c.text("PRINT THE NACK ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def dma_cndtr():
    """Eight half-words, CNDTR falls to 3: 5 samples, 10 bytes.

    Treating the remainder as bytes stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "8 HALF-WORDS",
        "CNDTR 8",
        "CNDTR 6",
        "CNDTR 4",
        "CNDTR 3",
        "5 samples  10 bytes",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "DMA CNDTR", "DMA1", "AUX GIF  HALF-WORDS")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("channel 4  HALF-WORD", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("5 samples IS 10 bytes", 28, 200, C.GREEN, 1)
        c.text("PRINT THE BYTE CUT ON THE SVG", 28, 222, C.DIM, 1)
        g.add(c)
    return g


def iwdg_1s():
    """A 625 Hz count is fed before it reaches 0.

    Reload = 625 and the window watchdog stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "40 kHz TYPICAL",
        "prescaler 64",
        "625 Hz",
        "COUNT DOWN",
        "FEED BEFORE ZERO",
        "Reload = 624",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "IWDG 1S", "624", "AUX GIF  TYPICAL 40 kHz")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("NOT A GUARANTEE", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("Reload = 624", 28, 200, C.GREEN, 1)
        c.text("625 Hz UNTIL THE FEED", 28, 222, C.CYAN, 1)
        c.text("PRINT ZERO AND THE WINDOW ON THE SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g
```

把 `BUILDERS` 换成：

```python
BUILDERS = {
    "led-blink": led_blink,
    "pwm-breath": pwm_breath,
    "uart-bits": uart_bits,
    "i2c-timing": i2c_timing,
    "dma-ring": dma_ring,
    "sar-adc": sar_adc,
    "nvic-preempt": nvic_preempt,
    "uart-idle": uart_idle,
    "clock-css": clock_css,
    "pwm-1khz": pwm_1khz,
    "spi-jedec": spi_jedec,
    "adc-sample": adc_sample,
    "swd-fetch": swd_fetch,
    "i2c-addr": i2c_addr,
    "dma-cndtr": dma_cndtr,
    "iwdg-1s": iwdg_1s,
}
```

Run: `python3 tools/gen_gifs.py swd-fetch i2c-addr dma-cndtr iwdg-1s`

Expected: 退出码 0，四行 `[ok]`，帧数都是 6。不要为了这一步重跑另外 12 个名字。

在 `assets/README.md` 第五节表格末尾追加：

```markdown
| `swd-fetch.gif` | SWD 写完闪存，CPU 读出 MSP 和 Reset_Handler，标出第 34 脚和第 37 脚 | 由 `tools/gen_gifs.py` 生成。辅图。GPIO 复用和 0xAA 只在静态主图上 |
| `i2c-addr.gif` | START 之后移出 0x78，第 9 个时钟 ACK，标出 0x801E 和 4.7 kΩ | 由 `tools/gen_gifs.py` 生成。辅图。0x3C 被原样送出和缺上拉只在静态主图上 |
| `dma-cndtr.gif` | 8 个半字的缓冲区里 CNDTR 减到 3，标出已写 5 个采样、10 字节 | 由 `tools/gen_gifs.py` 生成。辅图。把剩余计数当成字节只在静态主图上 |
| `iwdg-1s.gif` | 625 Hz 的计数在减到 0 之前被喂狗，标出 Reload = 624 和 40 kHz 典型值 | 由 `tools/gen_gifs.py` 生成。辅图。减到 0、Reload = 625 和窗口看门狗的早喂只在静态主图上 |
```

把「上面 12 张 GIF」换成「上面 16 张 GIF」。把「不是上面 12 张的中文翻译」换成「不是上面 16 张的中文翻译」。

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch4_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_gifs.py assets/gif/swd-fetch.gif assets/gif/i2c-addr.gif assets/gif/dma-cndtr.gif assets/gif/iwdg-1s.gif assets/README.md stm32-book/tests/test_batch4_chapters.py
git commit -m "assets: 为 01、07、10、11 加上短 GIF 辅图"
```

`git diff --name-only -- assets/gif/led-blink.gif assets/gif/pwm-breath.gif assets/gif/uart-bits.gif assets/gif/i2c-timing.gif assets/gif/dma-ring.gif assets/gif/sar-adc.gif assets/gif/nvic-preempt.gif assets/gif/uart-idle.gif assets/gif/clock-css.gif assets/gif/pwm-1khz.gif assets/gif/spi-jedec.gif assets/gif/adc-sample.gif` 应无输出。

### Task 5: Thicken chapter 01 in both languages

**Files:**
- Modify: `docs/01-开发环境搭建.md`
- Modify: `docs/en/01-dev-environment.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `ds5319-swd`、`pm0075-rdp`、`pm0056-vector`；`01-开发环境搭建.md` 的 `sources` 改为 `["project-guide", "pm0056", "stm32cube-f4", "clion-embedded", "platformio-vscode", "ds5319-swd", "pm0075-rdp", "pm0056-vector", "rm0008-boot"]`）
- Modify: `stm32-book/manifest-en.json`（同一组 id 与同一组 `url` / `snapshot` / `license` / `accessed`；英文 `title`、`authority`、`scope`；`01-dev-environment.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch4_chapters.py`
- Test: `stm32-book/tests/test_batch4_chapters.py`

**Interfaces:**
- Consumes: `ds5319-swd`、`pm0075-rdp`、`pm0056-vector`、已有的 `rm0008-boot`，以及 `assets/diagrams/sample-01-swd-vectors.svg`、`assets/gif/swd-fetch.gif`。
- Produces: `baseline_manifests() -> tuple[dict, dict]`、`_fetch_baseline(rev: str) -> None`、`_git_show(rev: str, path: str) -> str | None`。中文章在 `## 📌 学习目标` 之前出现四个新的二级标题；英文在 `## 📌 Learning goals` 之前出现四个英文标题。旧的 `## ⚠️ 常见坑与排查` 与 `## ⚠️ Pitfalls and troubleshooting` 从这两份里删除。OpenOCD 的 `stm32f1x unlock 0` 留在核心原理。链接脚本里的 `LENGTH = 64K` 和 `LENGTH = 20K` 不改。四块里不再把无保护写成选 `AA`，也不再把「BOOT0=1」单独说成 SRAM 启动。

`accessed` 写死 `2026-10-25`。中英 manifest 写同一天。不改已有 `pm0056`、`pm0056-nvic`、`rm0008-boot` 的任何字段。167 ns 不进这一章。

- [ ] **Step 1: 把章节断言和基线读取加进测试**

把 `stm32-book/tests/test_batch4_chapters.py` 的 import 区换成：

```python
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path
```

在 `ROOT = ...` 之后增加：

```python
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
```

在文件末尾、`if __name__` 之前追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4SwdChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`（`AssertionError`，`1 != 0`）。

- [ ] **Step 3: 把解锁步骤留在核心原理，并删掉旧坑表**

中文 `docs/01-开发环境搭建.md`：在 `## 🧠 核心原理` 这一节的末尾、`## 🛠️ 硬件与接线` 之前，插入下面这一段。不要把它放进四块。

````markdown
### 芯片被读保护时怎么解锁

工具链菜单留在这里，不进四块。无保护字节是 `0xA5`，不是 `0xAA`。`0xAA` 在 STM32F103C8T6 上作废。解除保护会整片擦除主闪存。

1. STM32CubeProgrammer → 选择 ST-LINK 连接方式，Connect。
2. 左侧 `Option bytes` → Read Out Protection 写成 `0xA5`。界面若只显示 Level 0，旁边仍写明写入的字节是 `0xA5`。
3. 点击 `Apply`。**注意：解除读保护会全片擦除主闪存。**
4. 重新下载程序。

命令行等价（OpenOCD）：

```bash
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c "init; reset halt; stm32f1x unlock 0; reset; shutdown"
```
````

然后删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段（含原来的 `AA` 步骤和旧坑表）。动手实验保留。`LENGTH = 64K` 和 `LENGTH = 20K` 那两行不要改。

英文 `docs/en/01-dev-environment.md`：在 `## 🧠 Core ideas` 这一节的末尾、`## 🛠️ Hardware and wiring` 之前，插入：

````markdown
### Clearing readout protection

Toolchain menus stay here and do not enter the four blocks. The unprotected byte is `0xA5`, not `0xAA`. `0xAA` is void on STM32F103C8T6. Clearing protection mass-erases main Flash.

1. STM32CubeProgrammer → choose ST-LINK, then Connect.
2. On the left, `Option bytes` → write Read Out Protection as `0xA5`. If the UI only shows Level 0, still write that the byte is `0xA5`.
3. Click `Apply`. **Clearing readout protection mass-erases main Flash.**
4. Download the program again.

The same thing from the command line (OpenOCD):

```bash
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c "init; reset halt; stm32f1x unlock 0; reset; shutdown"
```
````

然后删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。动手实验保留。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch01 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的调试和启动结论只钉在订货号 STM32F103C8T6、封装 LQFP48 上。闪存和 SRAM 跟第 02 章同一笔：64 KB 从 `0x08000000` 起，20 KB 从 `0x20000000` 起。启动别名跟第 00 章同一笔，不另画一套 BOOT 表。

复位后的调试口是第 34 脚 PA13 = SWDIO，第 37 脚 PA14 = SWCLK。中间隔着第 35 脚 VSS_2 和第 36 脚 VDD_2。把第 35 脚当成 SWCLK 是主图的失败路径。第 7 脚 NRST 建议接，它不是第三根 SWD 信号。第 44 脚是 BOOT0。信号名 PA13/PA14 与第 03 章一致；封装脚号只在这一章展开。SYS Debug 选 Serial Wire。把它关掉之后，这两只脚变成普通 GPIO，下一次 SWD 连接失败。脚位见 [DS5319 Rev 20 表 5](#source-ds5319-swd)。

BOOT0=0 时，CPU 从 `0x00000000` 读到的是闪存 `0x08000000` 的别名。第 0 个字是 MSP 初值，第 1 个字在 `0x00000004`，是 `Reset_Handler`。外设中断入口不是 `0x08000000 + 4×IRQn`，而是 `VTOR + 4×(IRQn + 16)`。`.isr_vector` 要用 `KEEP` 这件事留在核心原理。两字见 [PM0056 的向量表](#source-pm0056-vector)。

BOOT1=0 且 BOOT0=1：CPU 仍读 `0x00000000`，取到的是系统存储器 `0x1FFFF000`，闪存里的程序还在，只是没有被取指。BOOT1=1 且 BOOT0=1 才从 SRAM `0x20000000` 启动。「BOOT0=1 从 SRAM 启动」这句话作废，改成这两行。不重画第 00 章那张图。启动别名见 [RM0008 Rev 21 表 9](#source-rm0008-boot)。

无保护是 RDP = `0xA5`，不是 `0xAA`。手册把这只键印成 `0x00A5`，低字节仍是 `0xA5`。解除保护会整片擦除主闪存。`0xAA` 和 `0xCC` 在这颗料上作废。选项字节界面若只显示 Level 0，旁边仍写明写入的字节是 `0xA5`。见 [PM0075](#source-pm0075-rdp)。

这颗 C8 是 64 KB 闪存、20 KB SRAM。xB 的 128 KB 作废。链接脚本里的 `LENGTH = 64K` 和 `LENGTH = 20K` 跟这两句同一笔。

跟踪脚是第 39 脚 PB3，默认功能是 JTDO，重映射里才有 TRACESWO。它不是 PA13，也不是 PA14。ITM 打印留在核心原理，不进主图的正常路径。第 17 章的 `debug-swo.svg` 不重画。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-01-swd-vectors.svg" width="760" alt="SWCLK 在第 37 脚；BOOT0=0 时第 0 字是栈、第 1 字是复位；无保护字节是 0xA5">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48。第 34 脚 PA13 = SWDIO，第 37 脚 PA14 = SWCLK。第 35 脚是 VSS_2，第 36 脚是 VDD_2。第 44 脚 BOOT0 = 0 时，0x00000000 别名到 0x08000000。第 0 字是 MSP，第 1 字是 Reset_Handler。失败路径是这两只脚被配成 GPIO，或把第 35 脚当成 SWCLK。BOOT1=0 且 BOOT0=1 时取到 0x1FFFF000，不是 SRAM。无保护字节是 0xA5，0xAA 作废。出处是 [DS5319 Rev 20 表 5](#source-ds5319-swd)、[PM0056 的向量表](#source-pm0056-vector) 和 [PM0075 的 0xA5](#source-pm0075-rdp)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/swd-fetch.gif" width="640" alt="SWD 写完闪存后，CPU 读出 MSP 和 Reset_Handler">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：SWD 写完闪存，CPU 读出 MSP 和 Reset_Handler，标出第 34 脚和第 37 脚。印刷以静态主图为准。GPIO 复用和 0xAA 不在这条 GIF 上。</sub>
</p>

`boot-sequence.svg` 留作辅图。不播放它，脚号、两字和连不上的失败都在静态主图上。

## 时序或状态

| 阶段 | BOOT / Debug | 读到的地址 | 状态 |
| --- | --- | --- | --- |
| 复位，BOOT0=0 | 第 44 脚 BOOT0 = 0 | `0x00000000` 别名 `0x08000000` | 物理存储器是 64 KB 闪存 |
| 第 0 字 | 向量表第 0 项 | `0x00000000` | MSP 初值 |
| 第 1 字 | 向量表第 1 项 | `0x00000004` | `Reset_Handler`，然后才到 `main` |
| 失败：Debug 关掉 | 第 34 脚和第 37 脚变成 GPIO | PA13 / PA14 不再是 SWD | SWD 连接失败 |
| 失败：系统存储器 | BOOT1=0 且 BOOT0=1 | `0x1FFFF000` | 不是 SRAM。闪存里的程序还在，只是没有被取指 |
| SRAM | BOOT1=1 且 BOOT0=1 | `0x20000000` | 两只 BOOT 都为 1 才从 SRAM 启动 |
| IRQ | 外设中断 | `VTOR + 4×(IRQn + 16)` | 不是 `0x08000000 + 4×IRQn` |
| 容量 | C8 | 64 KB 闪存，20 KB SRAM | 128 KB 在这颗料上作废 |

这张表不写工具链菜单。第 35 脚是 VSS_2，第 36 脚是 VDD_2，第 7 脚是 NRST。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 烧录一次后再也连不上 | PA13/PA14 被配成 GPIO | 把 Debug 留在 Serial Wire，SWD 留在第 34 脚和第 37 脚 | [DS5319](#source-ds5319-swd) | LQFP48 第 34 脚是 PA13/SWDIO，第 37 脚是 PA14/SWCLK。第 35 脚是 VSS_2 |
| 探针接在 PA13 旁边那只脚上，时钟没有 | 第 35 脚被当成了 SWCLK | 空开第 35、36 脚，时钟接到第 37 脚 | [DS5319](#source-ds5319-swd) | 第 35 脚是 VSS_2，第 36 脚是 VDD_2，第 37 脚才是 SWCLK |
| BOOT0 拉高之后跑的不是闪存里的程序，也不是 SRAM | BOOT1 仍是 0 | BOOT1=0 时这是系统存储器。要进 SRAM，两只 BOOT 都拉高 | [RM0008](#source-rm0008-boot) | BOOT1=0 且 BOOT0=1 时别名到 `0x1FFFF000`。SRAM 启动还要 BOOT1=1 |
| 按 `AA` 解除读保护，片子仍保护着或擦除结果对不上 | 无保护键不是 `0xAA` | 无保护键写成 `0xA5`。解除时主闪存会被整片擦掉 | [PM0075](#source-pm0075-rdp) | RDP 为 `0xA5` 才允许读出。编程回 `0xA5` 会先整片擦除。`0xAA` 在这颗料上作废 |
| 向量表第 0 字被当成复位入口 | 第 0 字是栈 | 第 0 字是 MSP，第 1 字才是 `Reset_Handler` | [PM0056](#source-pm0056-vector) | 向量表第 0 项是栈初值，第 1 项是复位。IRQ 入口要先加上 16 个系统异常 |

```

英文插在 `<!-- /video:ch01 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The debug and boot conclusion in this chapter is pinned to order code STM32F103C8T6 in LQFP48. Flash and SRAM are the same ledger as chapter file 02: 64 KB from `0x08000000`, 20 KB from `0x20000000`. The boot alias is the same ledger as chapter file 00. This chapter does not draw another BOOT table.

After reset the debug port is pin 34 PA13 = SWDIO and pin 37 PA14 = SWCLK. Pin 35 VSS_2 and pin 36 VDD_2 sit between them. Counting pin 35 as SWCLK is the failure path on the key figure. Pin 7 NRST is worth connecting. It is not a third SWD signal. Pin 44 is BOOT0. The signal names PA13/PA14 match chapter file 03. The package pin numbers are expanded only here. Leave SYS Debug on Serial Wire. After it is turned off, those two pins become ordinary GPIO and the next SWD connection fails. Pins: [DS5319 Rev 20 Table 5](#source-ds5319-swd).

With BOOT0=0, what the CPU reads at `0x00000000` is an alias of Flash at `0x08000000`. Word 0 is the initial MSP. Word 1, at `0x00000004`, is `Reset_Handler`. A peripheral IRQ entry is not `0x08000000 + 4×IRQn`. It is `VTOR + 4×(IRQn + 16)`. Keeping `.isr_vector` with `KEEP` stays in the core ideas. The two words: [PM0056 vector table](#source-pm0056-vector).

BOOT1=0 and BOOT0=1: the CPU still reads `0x00000000` and gets system memory at `0x1FFFF000`. The program in Flash is still there. It is just not being fetched. SRAM boot needs BOOT1=1 and BOOT0=1, from `0x20000000`. The sentence "BOOT0=1 boots from SRAM" is void. Replace it with these two lines. Do not redraw the chapter 00 figure. Alias: [RM0008 Rev 21 Table 9](#source-rm0008-boot).

Unprotected readout is RDP = `0xA5`, not `0xAA`. The manual prints that key as `0x00A5`. The low byte is still `0xA5`. Clearing protection mass-erases main Flash. `0xAA` and `0xCC` are void on this part. If the option-byte screen only shows Level 0, still write that the byte is `0xA5`. See [PM0075](#source-pm0075-rdp).

This C8 is 64 KB of Flash and 20 KB of SRAM. The xB 128 KB is void. `LENGTH = 64K` and `LENGTH = 20K` in the linker script are the same ledger.

The trace pin is pin 39 PB3. Its default function is JTDO. TRACESWO appears only in the remap column. It is not PA13 and it is not PA14. ITM printing stays in the core ideas and off the normal path of the key figure. Do not redraw chapter 17's `debug-swo.svg`.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-01-swd-vectors.svg" width="760" alt="SWCLK is on pin 37; with BOOT0=0 word 0 is the stack and word 1 is reset; the unprotected byte is 0xA5">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48. Pin 34 PA13 = SWDIO and pin 37 PA14 = SWCLK. Pin 35 is VSS_2 and pin 36 is VDD_2. With pin 44 BOOT0 = 0, 0x00000000 aliases 0x08000000. Word 0 is the MSP and word 1 is Reset_Handler. The failure is those two pins reused as GPIO, or pin 35 counted as SWCLK. BOOT1=0 and BOOT0=1 fetches 0x1FFFF000, not SRAM. The unprotected byte is 0xA5. 0xAA is void. Sources: [DS5319 Rev 20 Table 5](#source-ds5319-swd), [the PM0056 vector table](#source-pm0056-vector), and [PM0075's 0xA5](#source-pm0075-rdp).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/swd-fetch.gif" width="640" alt="After SWD writes Flash, the CPU reads the MSP and Reset_Handler">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the normal path: SWD finishes writing Flash, the CPU reads the MSP and Reset_Handler, and pins 34 and 37 are marked. Print uses the static figure. GPIO reuse and 0xAA are not on this GIF.</sub>
</p>

`boot-sequence.svg` stays a side figure. Without playing it, the pin numbers, the two words, and the failed connection are all on the static figure.

## Timing or state

| Phase | BOOT / Debug | Address read | State |
| --- | --- | --- | --- |
| Reset, BOOT0=0 | Pin 44 BOOT0 = 0 | `0x00000000` aliases `0x08000000` | The physical memory is 64 KB of Flash |
| Word 0 | Vector item 0 | `0x00000000` | Initial MSP |
| Word 1 | Vector item 1 | `0x00000004` | `Reset_Handler`, then `main` |
| Failure: Debug off | Pins 34 and 37 become GPIO | PA13 / PA14 are no longer SWD | The SWD connection fails |
| Failure: system memory | BOOT1=0 and BOOT0=1 | `0x1FFFF000` | Not SRAM. The program in Flash is still there and is not fetched |
| SRAM | BOOT1=1 and BOOT0=1 | `0x20000000` | Both BOOT pins must be 1 |
| IRQ | Peripheral interrupt | `VTOR + 4×(IRQn + 16)` | Not `0x08000000 + 4×IRQn` |
| Size | C8 | 64 KB Flash, 20 KB SRAM | 128 KB is void on this part |

This table does not include toolchain menus. Pin 35 is VSS_2, pin 36 is VDD_2, and pin 7 is NRST.

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| After one flash you can never connect | PA13/PA14 were set as GPIO | Leave Debug on Serial Wire, on pin 34 and pin 37 | [DS5319](#source-ds5319-swd) | LQFP48 pin 34 is PA13/SWDIO and pin 37 is PA14/SWCLK. Pin 35 is VSS_2 |
| The probe is on the pin next to PA13 and there is no clock | Pin 35 was counted as SWCLK | Leave pins 35 and 36 open and put the clock on pin 37 | [DS5319](#source-ds5319-swd) | Pin 35 is VSS_2, pin 36 is VDD_2, and pin 37 is SWCLK |
| BOOT0 high runs neither the Flash program nor SRAM | BOOT1 is still 0 | That is system memory while BOOT1=0. SRAM needs both BOOT pins high | [RM0008](#source-rm0008-boot) | BOOT1=0 and BOOT0=1 aliases `0x1FFFF000`. SRAM boot also needs BOOT1=1 |
| Choosing `AA` leaves the part protected, or the erase does not match | The unprotected key is not `0xAA` | Write the unprotected key as `0xA5`. Clearing it mass-erases main Flash | [PM0075](#source-pm0075-rdp) | RDP `0xA5` is what allows readout. Programming it back mass-erases first. `0xAA` is void on this part |
| Word 0 of the vector table was treated as the reset entry | Word 0 is the stack | Word 0 is the MSP. Word 1 is `Reset_Handler` | [PM0056](#source-pm0056-vector) | Item 0 is the initial stack. Item 1 is reset. An IRQ entry adds the 16 system exceptions first |

```

四块里不要把无保护写成选 `AA`。`0xAA` 只作为作废出现。不要写入 167 ns。不要把第 00 章的启动图重画进这一章。

- [ ] **Step 5: 追加三个来源对象**

`url`、`snapshot`、`license` 从清单原样复制。`title` 用 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。`accessed` 是 `2026-10-25`。`scope` 用本任务测试里 `scopes` 字典的那三句。中文对象按 `ds5319-swd`、`pm0075-rdp`、`pm0056-vector` 的顺序追加在 `stm32-book/manifest.json` 的 `sources` 末尾，英文对象按同样顺序追加在 `stm32-book/manifest-en.json` 的 `sources` 末尾。不要改已有 id 的任何字段。`rm0008-boot` 只出现在罗盘里，不新建对象。两章罗盘的 `sources` 改成测试里的 `compass`，不删除原来的五个 id。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4SwdChapterTests -v`

Expected: OK。

```bash
git add docs/01-开发环境搭建.md docs/en/01-dev-environment.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch4_chapters.py
git commit -m "book: 加厚第 01 章并把无保护键改成 0xA5"
```

### Task 6: Thicken chapter 07 in both languages

**Files:**
- Modify: `docs/07-I2C总线.md`
- Modify: `docs/en/07-i2c.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `ds5319-i2c`、`rm0008-i2c`；`07-I2C总线.md` 的 `sources` 改为 `["rm0008", "ds5319-i2c", "rm0008-i2c", "project-examples"]`）
- Modify: `stm32-book/manifest-en.json`（同一组字段规则；`07-i2c.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch4_chapters.py`
- Test: `stm32-book/tests/test_batch4_chapters.py`

**Interfaces:**
- Consumes: `ds5319-i2c`、`rm0008-i2c`、已有的 `project-examples`，以及 `assets/diagrams/sample-07-i2c-addr.svg`、`assets/gif/i2c-addr.gif`。Task 5 的 `baseline_manifests()`。不要再定义一遍。
- Produces: 四块各一次。四块可以写「1 MHz 在这颗料上作废」，不能把 1 MHz 列成工作点。四块不出现 `300ns / Cb`。`examples/i2c-oled/` 的 diff 为空。不新建 `project-examples` 对象。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch4_chapters.py` 末尾、`if __name__` 之前追加。不要再贴 `baseline_manifests`。

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4I2cChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 把 1 MHz 标成作废，把上升时间估算留在核心原理，并删掉旧坑表**

中文 `docs/07-I2C总线.md` 把这一行：

```markdown
| 快速+ | 1MHz | 1k~2.2kΩ | 需注意灌电流 |
```

换成：

```markdown
| 快速+ | 1 MHz | — | 在 STM32F103C8T6 上作废，不进四块的工作点 |
```

把这一行：

```markdown
> 经验：`Rp(max) ≈ 300ns / Cb`（标准模式上升时间限制）；电容越大，上拉要越小。
```

换成：

```markdown
> 估算，不是 DS5319 的标准模式上限：`Rp(max) ≈ 300ns / Cb`。电容越大，上拉要越小。标准模式上升时间上限是 1000 ns，快速模式是 300 ns，那两句在四块里。
```

把这一行：

```markdown
| 速率 | 较低 | 可达 400kHz/1MHz |
```

换成：

```markdown
| 速率 | 较低 | 快速模式目标 400 kHz。1 MHz 在 STM32F103C8T6 上作废 |
```

英文 `docs/en/07-i2c.md` 把这一行：

```markdown
| Fast+ | 1 MHz | 1 kΩ to 2.2 kΩ | Watch the sink current |
```

换成：

```markdown
| Fast+ | 1 MHz | — | Void on STM32F103C8T6. Not a working point in the four blocks |
```

把这一行：

```markdown
> Rule of thumb: `Rp(max) ≈ 300ns / Cb` (the standard-mode rise-time limit). More capacitance means a smaller pull-up.
```

换成：

```markdown
> An estimate, not the DS5319 standard-mode limit: `Rp(max) ≈ 300ns / Cb`. More capacitance means a smaller pull-up. The standard-mode rise-time limit is 1000 ns and the fast-mode limit is 300 ns. Those two sentences are in the four blocks.
```

把这一行：

```markdown
| Speed | Lower | Up to 400 kHz / 1 MHz |
```

换成：

```markdown
| Speed | Lower | Fast mode targets 400 kHz. 1 MHz is void on STM32F103C8T6 |
```

中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。动手实验保留。`examples/i2c-oled/` 不要改。AT24C02 的 `0x50` 和 MPU6050 的 `0x68` 留在核心原理。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch07 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的 I2C 结论只钉在订货号 STM32F103C8T6 上。I2C1 在 APB1，PCLK1 = 36 MHz，跟附录 D 的 APB1 格子同一笔。工作点整格照抄 DS5319 表 42：Rp = 4.7 kΩ，目标 400 kHz，`I2C_CCR = 0x801E`。地址整格照抄附录 D：7 位 `0x3C`，HAL 填 `0x78`。

复位后的默认脚是第 42 脚 PB6 = I2C1_SCL，第 43 脚 PB7 = I2C1_SDA。两只脚都配成复用开漏，外面各接 4.7 kΩ 到 3.3 V。这不是第 08 章的推挽片选。重映射到第 45 脚 PB8、第 46 脚 PB9 不画进正常路径。表 5 的重映射列把 USART1_TX / USART1_RX 放在 PB6/PB7 上；那不是复位默认，和第 06 章同一笔。本图只画 I2C。两只脚不能同时充当 USART1。脚位见 [DS5319 Rev 20 表 5 与表 42](#source-ds5319-i2c)。

7 位 `0x3C` 的位型是 `0111100`。写方向的线上第一字节是 `0x3C << 1`，也就是 `0x78`。读方向是 `0x79`。HAL 的 DevAddress 填 `0x78`，不填 `0x3C`。把扫描器看到的 `0x3C` 原样送进 `HAL_I2C_Master_Transmit`，线上出去的是 `0x3C`，7 位地址变成 `0x1E`。这是主图的失败路径。例程里的宏已经是 `0x78`，见 [examples/i2c-oled](#source-project-examples)。地址字节见 [RM0008 Rev 21 第 26 章](#source-rm0008-i2c)。

接收方拉低 SDA 是 ACK。SDA 保持高是 NACK。地址不对时看到的是 NACK，不是「高电平表示答应了」。

`HAL_I2C_Mem_Read` 的顺序是 START、器件地址+写、寄存器地址、重复起始、器件地址+读、数据、STOP。先 `Master_Transmit` 再 `Master_Receive` 会在中间插入 STOP。

`0x801E`：快速模式位置位，DUTY = 0，CCR 字段 = 30。PCLK1 = 36 MHz 时，一个 SCL 周期是 `3 × 30 / 36e6 = 2.5` µs，目标 400 kHz。100 kHz 那一行是 `0x00B4`，CCR 字段 = 180，标准模式，`36e6 / (2 × 180) = 100` kHz。36 MHz 不是 10 MHz 的整数倍，所以表 41 说这样到不了「400 kHz 上限」的那句条件；表 42 仍把 400 kHz 和 `0x801E` 印在 36 MHz 这一列。达成速率按表 42 注 2 留 ±2% 的容差，不把 400 kHz 写成保证的边沿。1 MHz 不在表 41、表 42 里，在 STM32F103C8T6 上作废。

表 42 这一行的外部上拉是 4.7 kΩ。片内大约 30–50 kΩ 沿用附录 D 和第 03 章，不能代替这只电阻去跑 400 kHz。标准模式上升时间上限是 1000 ns，快速模式是 300 ns。`300ns / Cb` 那条估算不进四块。Cb 上限 400 pF 可以写在这里，不把它换成另一张皮法表。

配成开漏时，连到 VDD 的 PMOS 被关掉，管子还在。外部上拉仍然要有。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-07-i2c-addr.svg" width="760" alt="HAL 送出的写地址是 0x78；0x801E 是 36 MHz 下表 42 的 400 kHz 行；把 0x3C 原样送上总线时第 9 个时钟没有 ACK">
  <br><sub>▲ 自绘。STM32F103C8T6。第 42 脚 PB6 = SCL，第 43 脚 PB7 = SDA，两只 4.7 kΩ 接到 3.3 V。PCLK1 = 36 MHz，I2C_CCR = 0x801E，目标 400 kHz，容差 ±2%。正常路径的第一字节是 0x78，第 9 个时钟 ACK。失败路径是 DevAddress 填了 0x3C，第 9 个时钟 SDA 仍为高。出处是 [DS5319 Rev 20 表 42 和表 5](#source-ds5319-i2c) 与 [RM0008 Rev 21 第 26 章](#source-rm0008-i2c)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/i2c-addr.gif" width="640" alt="START 之后移出 0x78，第 9 个时钟 ACK">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：START，线上移出 0x78，第 9 个时钟 ACK，标出 0x801E 和 4.7 kΩ。印刷以静态主图为准。0x3C 被原样送出和缺上拉不在这条 GIF 上。</sub>
</p>

`i2c-transaction.svg` 和 `i2c-timing.gif` 留在原节，标成辅图。

## 时序或状态

| 段 | SCL | SDA | 线上的字节 |
| --- | --- | --- | --- |
| START | 高 | 由高到低 | 还没有地址字节 |
| 正常：写地址 | 8 个时钟 | 逐位移出 | `0x78` |
| 正常：第 9 个时钟 | 第 9 个时钟 | 低 | ACK |
| 失败：写地址 | 8 个时钟 | 逐位移出 | `0x3C`，7 位地址变成 `0x1E` |
| 失败：第 9 个时钟 | 第 9 个时钟 | 高 | NACK |
| 读方向 | 重复起始之后 | 地址字节 | `0x79`，中间没有 STOP |
| 速率 | `0x801E` 目标 400 kHz | `0x00B4` 是 100 kHz | 容差 ±2%。CCR 字段 30 与 180 |
| 上拉 | 外部 4.7 kΩ 到 3.3 V | 36 MHz、3.3 V | 只有片内上拉时不跑这一行 400 kHz |

上升时间：标准模式 1000 ns，快速模式 300 ns。1 MHz 在这颗料上作废，不列成工作点。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 扫描器看到 `0x3C`，HAL 却没有 ACK | DevAddress 填了 7 位地址 | DevAddress 填 `0x78`。读方向的线上字节是 `0x79` | [RM0008](#source-rm0008-i2c) | 7 位地址左移 1 位再加读写位。`0x3C` 原样送出会变成 7 位地址 `0x1E` |
| 例程和手册对不上地址写法 | 7 位和 8 位混在一处 | 例程的宏已经是 `0x78` | [例程](#source-project-examples) | `examples/i2c-oled` 的器件地址是 `0x78`，由 `0x3C << 1` 得到 |
| 总线上拉只有片内电阻，400 kHz 超时 | 片内大约 30–50 kΩ 不够 | 按表 42 外接 4.7 kΩ 到 3.3 V | [DS5319](#source-ds5319-i2c) | 36 MHz、3.3 V 下 400 kHz 那一行的 Rp 是 4.7 kΩ。片内上下拉的千欧数沿用附录 D，不由这条来源重新规定 |
| SCL 比 400 kHz 偏一截 | CCR 不是表 42 那一行 | 核对 `I2C_CCR` 是 `0x801E`，并留下 ±2% | [DS5319](#source-ds5319-i2c) | 表 42 在 36 MHz 下把 400 kHz 印成 `0x801E`。36 MHz 不是 10 MHz 的整数倍，达成速率不是保证的 400 kHz 整 |
| 波形出现在 PB8/PB9，或和串口抢 PB6 | 用了重映射，或和 USART1 抢脚 | 复位默认是第 42 脚和第 43 脚，只开 I2C1 | [DS5319](#source-ds5319-i2c) | 第 42 脚默认含 I2C1_SCL，第 43 脚默认含 I2C1_SDA。USART1 的重映射不是复位默认 |

```

英文插在 `<!-- /video:ch07 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The I2C conclusion in this chapter is pinned to order code STM32F103C8T6. I2C1 is on APB1 and PCLK1 = 36 MHz, the same Appendix D cell. The working point is copied whole from DS5319 Table 42: Rp = 4.7 kΩ, a 400 kHz target, and `I2C_CCR = 0x801E`. The address is copied whole from Appendix D: 7-bit `0x3C`, and HAL writes `0x78`.

The reset-default pins are pin 42 PB6 = I2C1_SCL and pin 43 PB7 = I2C1_SDA. Both pins are alternate-function open-drain, each with 4.7 kΩ to 3.3 V. This is not the push-pull chip select from chapter file 08. The remap onto pin 45 PB8 and pin 46 PB9 is not on the normal path. Table 5's remap column places USART1_TX / USART1_RX on PB6/PB7. That is not the reset default, the same ledger as chapter file 06. This figure draws only I2C. The two pins cannot be USART1 at the same time. Pins: [DS5319 Rev 20 Tables 5 and 42](#source-ds5319-i2c).

The bit pattern of 7-bit `0x3C` is `0111100`. The first byte on the wire for a write is `0x3C << 1`, which is `0x78`. The read byte is `0x79`. HAL's DevAddress is `0x78`, not `0x3C`. Passing the scanner's `0x3C` straight into `HAL_I2C_Master_Transmit` puts `0x3C` on the wire, and the 7-bit address becomes `0x1E`. That is the failure path. The example macro is already `0x78`. See [examples/i2c-oled](#source-project-examples). The address byte: [RM0008 Rev 21 chapter 26](#source-rm0008-i2c).

The receiver pulling SDA low is ACK. SDA staying high is NACK. A wrong address shows NACK. A high level is not "yes".

`HAL_I2C_Mem_Read` is START, address plus write, register address, repeated START, address plus read, data, STOP. `Master_Transmit` followed by `Master_Receive` inserts a STOP in the middle.

`0x801E`: the fast-mode bit is set, DUTY = 0, and the CCR field is 30. At PCLK1 = 36 MHz one SCL period is `3 × 30 / 36e6 = 2.5` µs, a 400 kHz target. The 100 kHz row is `0x00B4`, CCR field 180, standard mode, `36e6 / (2 × 180) = 100` kHz. 36 MHz is not an integer multiple of 10 MHz, so Table 41's condition for the "400 kHz ceiling" is not met. Table 42 still prints 400 kHz and `0x801E` in the 36 MHz column. Keep the ±2% tolerance from Table 42 note 2. Do not call 400 kHz a guaranteed edge. 1 MHz is not in Table 41 or Table 42. It is void on STM32F103C8T6.

The external pull-up on this Table 42 row is 4.7 kΩ. The on-chip 30–50 kΩ is Appendix D and chapter file 03. It does not replace this resistor at 400 kHz. The standard-mode rise-time limit is 1000 ns and the fast-mode limit is 300 ns. The `300ns / Cb` estimate does not enter the four blocks. The 400 pF Cb ceiling can be written here. Do not turn it into another picofarad table.

In open-drain the PMOS that would connect to VDD is off. The transistor is still there. The external pull-up is still required.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-07-i2c-addr.svg" width="760" alt="HAL's write address is 0x78; 0x801E is Table 42's 400 kHz row at 36 MHz; sending 0x3C unchanged leaves no ACK on the 9th clock">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. Pin 42 PB6 = SCL and pin 43 PB7 = SDA, each with 4.7 kΩ to 3.3 V. PCLK1 = 36 MHz and I2C_CCR = 0x801E, a 400 kHz target with ±2% tolerance. The normal path's first byte is 0x78 and the 9th clock is ACK. The failure is DevAddress set to 0x3C, with SDA still high on the 9th clock. Sources: [DS5319 Rev 20 Tables 42 and 5](#source-ds5319-i2c) and [RM0008 Rev 21 chapter 26](#source-rm0008-i2c).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/i2c-addr.gif" width="640" alt="After START the wire shifts 0x78 and the 9th clock is ACK">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the normal path: START, 0x78 on the wire, ACK on the 9th clock, with 0x801E and 4.7 kΩ marked. Print uses the static figure. A raw 0x3C and a missing pull-up are not on this GIF.</sub>
</p>

`i2c-transaction.svg` and `i2c-timing.gif` stay in their original section and are marked as side figures.

## Timing or state

| Segment | SCL | SDA | Byte on the wire |
| --- | --- | --- | --- |
| START | High | High to low | No address byte yet |
| Normal: write address | 8 clocks | Shifted out | `0x78` |
| Normal: 9th clock | 9th clock | Low | ACK |
| Failure: write address | 8 clocks | Shifted out | `0x3C`, which addresses `0x1E` |
| Failure: 9th clock | 9th clock | High | NACK |
| Read direction | After repeated START | Address byte | `0x79`, with no STOP in between |
| Rate | `0x801E` targets 400 kHz | `0x00B4` is 100 kHz | Tolerance ±2%. CCR fields 30 and 180 |
| Pull-up | External 4.7 kΩ to 3.3 V | 36 MHz, 3.3 V | On-chip pull-ups alone do not run this 400 kHz row |

Rise time: 1000 ns in standard mode, 300 ns in fast mode. 1 MHz is void on this part and is not a working point.

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| A scanner shows `0x3C` and HAL gets no ACK | DevAddress was the 7-bit value | Write DevAddress as `0x78`. The read byte on the wire is `0x79` | [RM0008](#source-rm0008-i2c) | Shift the 7-bit address left by 1 and add the R/W bit. Sending `0x3C` unchanged addresses `0x1E` |
| The example and the manual disagree on the address form | 7-bit and 8-bit were mixed | The example macro is already `0x78` | [Examples](#source-project-examples) | `examples/i2c-oled` uses device address `0x78`, from `0x3C << 1` |
| The only pull-up is on-chip and 400 kHz times out | About 30–50 kΩ is not enough | Add the Table 42 4.7 kΩ to 3.3 V | [DS5319](#source-ds5319-i2c) | At 36 MHz and 3.3 V the 400 kHz row uses Rp = 4.7 kΩ. The on-chip kilohms stay with Appendix D and are not restated by this source |
| SCL is off from 400 kHz | CCR is not the Table 42 row | Check that `I2C_CCR` is `0x801E`, and keep ±2% | [DS5319](#source-ds5319-i2c) | Table 42 at 36 MHz prints 400 kHz as `0x801E`. 36 MHz is not an integer multiple of 10 MHz, so the achieved rate is not a guaranteed 400 kHz |
| The waveform is on PB8/PB9, or the UART takes PB6 | A remap is on, or USART1 shares the pin | The reset default is pin 42 and pin 43, with only I2C1 enabled | [DS5319](#source-ds5319-i2c) | Pin 42's default includes I2C1_SCL and pin 43's default includes I2C1_SDA. The USART1 remap is not the reset default |

```

四块里不要出现 `300ns / Cb`。1 MHz 只和「作废」写在一起，不列成工作点。

- [ ] **Step 5: 追加两个来源对象**

按 Task 5 的字段规则，把 `ds5319-i2c`、`rm0008-i2c` 追加到两份 manifest 的 `sources` 末尾。`scope` 用本任务测试里的两句。不要改 `project-examples`。罗盘改成测试里的 `compass`。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4I2cChapterTests -v`

Expected: OK。

```bash
git add docs/07-I2C总线.md docs/en/07-i2c.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch4_chapters.py
git commit -m "book: 加厚第 07 章并把 400 kHz 钉在 0x801E"
```

`git diff --name-only -- examples/i2c-oled` 应无输出。

### Task 7: Thicken chapter 10 in both languages

**Files:**
- Modify: `docs/10-DMA.md`
- Modify: `docs/en/10-dma.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `rm0008-dma`、`ds5319-dma`；`10-DMA.md` 的 `sources` 改为 `["rm0008", "stm32cube-f4", "st-h7-dma", "majerle-uart", "rm0090", "rm0008-dma", "ds5319-dma"]`）
- Modify: `stm32-book/manifest-en.json`（同一组字段规则；`10-dma.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch4_chapters.py`
- Test: `stm32-book/tests/test_batch4_chapters.py`

**Interfaces:**
- Consumes: `rm0008-dma`、`ds5319-dma`、已有的 `rm0090`，以及 `assets/diagrams/sample-10-dma-cndtr.svg`、`assets/gif/dma-cndtr.gif`。Task 5 的 `baseline_manifests()`。
- Produces: 四块各一次。四块写明 C8 没有 DMA2。21 µs 不出现在这一章的四块里。不改 `rm0090` 对象。不改附录 A。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch4_chapters.py` 末尾、`if __name__` 之前追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4DmaChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 把分类表里的 DMA2 标成作废，并删掉旧坑表**

中文把这一格：

```markdown
| 控制器 | DMA1（7 通道）、DMA2（5 通道，大容量） | DMA1/DMA2 各 8 个 Stream |
```

换成：

```markdown
| 控制器 | DMA1（7 通道）。DMA2（5 通道）是大容量的句子，在 STM32F103C8T6 上作废 | DMA1/DMA2 各 8 个 Stream |
```

在 `**② 内存→内存搬运（MEM2MEM）**` 那一段的代码块后面加一句：

```markdown
这条示例占用 DMA1 通道 1，和 ADC1 的请求抢同一条通道。它不是 USART1_TX 的正常路径。
```

英文把这一格：

```markdown
| Controllers | DMA1 (7 channels), DMA2 (5 channels, high-density) | DMA1 and DMA2, 8 streams each |
```

换成：

```markdown
| Controllers | DMA1 (7 channels). "DMA2 (5 channels)" is the high-density sentence and is void on STM32F103C8T6 | DMA1 and DMA2, 8 streams each |
```

在英文内存到内存那段代码块后面加一句：

```markdown
This example takes DMA1 channel 1 and contends with ADC1's request. It is not the USART1_TX normal path.
```

打开 RM0008 Rev 21 第 10 章的请求表，对照章内「F1 DMA1 请求映射」那张节选。和印出的表对不上的格子，按印出的表改，不新编通道号。对得上就保持节选。四块只主张附录 D 的三行：ADC1 = 通道 1，USART1_TX = 通道 4，USART1_RX = 通道 5。

中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。动手实验里已有的「8 个半字、CNDTR 读回 3、5 个采样、半传输 4 个采样也就是 8 字节」保留，不另写一套数字。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch10 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的 DMA 结论只钉在订货号 STM32F103C8T6 上。通道号和半字账整格照抄附录 D。不把第 09 章的 21 µs 搬进来。

这颗中密度有一个 DMA，7 条通道。分类表里「DMA2（5 通道，大容量）」在 STM32F103C8T6 上作废。见 [DS5319 Rev 20 第 2.3.13 节](#source-ds5319-dma)。F4 的 Stream 和 Channel 是另一本手册：USART1_RX 在 DMA2 Stream 5、Channel 4，FIFO 是 4 个 32 位字。把这组号写进 C8，计数器不动。见 [RM0090](#source-rm0090)。不改那条已有对象。

ADC1 = DMA1 通道 1。USART1_TX = DMA1 通道 4。USART1_RX = DMA1 通道 5。四块只主张附录 D 这三行。见 [RM0008 Rev 21 第 10 章](#source-rm0008-dma)。

缓冲区 8 个半字，`CNDTR` 读回 3：已经写入 `8 − 3 = 5` 个采样，字节数是 `5 × 2 = 10`。半传输发生在 4 个采样，也就是 8 字节，不是 4 字节。把 `CNDTR` 当成剩余字节，会把「还剩 3」读成 3 字节。这是主图的失败路径。

计数归零后硬件重装 `CNDTR`。`长度 − CNDTR` 不是累计进度。位置仍用回调里的 `Size` 和 `old_pos`，这句与附录 A 同一笔，不改附录 A。

F1 的 DMA 控制器是 AHB 主机，外设寄存器在 APB。F1 没有 D-Cache。H7 的 Cache 维护留在核心原理，不进这颗料的四块规范主张。

USART1_TX 仍是第 06 章的第 30 脚 PA9。本图只旁注通道号，不重画那一帧。ADC 的采样时间留在第 09 章。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-10-dma-cndtr.svg" width="760" alt="8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节；把剩余计数当成字节会切错">
  <br><sub>▲ 自绘。STM32F103C8T6，只有 DMA1。USART1_TX 走通道 4，宽度是半字，缓冲区长度 8。CNDTR = 3 时已写 5 个采样、10 字节。半传输在第 4 个采样、8 字节。失败路径把同一读数当成字节。TX 仍从第 30 脚 PA9 出去。DMA2 Stream 5 在这颗 C8 上没有计数器。出处是 [RM0008 Rev 21 第 10 章](#source-rm0008-dma) 和 [DS5319 Rev 20 第 2.3.13 节](#source-ds5319-dma)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/dma-cndtr.gif" width="640" alt="8 个半字的缓冲区里 CNDTR 减到 3，已写 5 个采样、10 字节">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：CNDTR 减到 3，标出已写 5 个采样、10 字节。印刷以静态主图为准。把剩余计数当成字节不在这条 GIF 上。</sub>
</p>

`dma-circular.svg` 和 `dma-ring.gif` 留在原节，标成辅图。

## 时序或状态

| 长度 | 宽度 | CNDTR | 已写采样 | 已写字节 |
| --- | --- | --- | --- | --- |
| 8 | 半字 | 3 | 5 | 10 |
| 8 | 半字 | 半传输 | 4 | 8，不是 4 字节 |
| 8 | 被当成字节 | 3 | 错切 | 还剩 3 被读成 3 字节 |
| USART1_TX | DMA1 通道 4 | — | — | 第 30 脚 PA9 |
| USART1_RX | DMA1 通道 5 | — | — | 不是 DMA2 Stream 5 |
| ADC1 | DMA1 通道 1 | — | — | 和内存到内存示例抢这一条通道 |
| 作废 | DMA2 Stream 5 | 这颗料上没有计数器 | — | F4 的 FIFO 是 4 个 32 位字，不证明 C8 有 DMA2 |
| 循环 | 归零后重装 | 重装后的 CNDTR | 不是累计 | `长度 − CNDTR` 不是进度 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 半字数组后一半看起来像新数据 | 半传输被当成 4 字节 | 半传输按 4 个采样、8 字节处理 | [RM0008](#source-rm0008-dma) | `CNDTR` 数的是数据项。8 个半字里已写 5 个是 10 字节。半传输不是 4 字节 |
| `CNDTR` 读回 3，字节数却对不上 | 剩余计数被当成字节 | 先减采样个数，再乘 2 | [RM0008](#source-rm0008-dma) | 剩余 3 个半字不是剩余 3 字节 |
| 配了 DMA2 Stream 5，C8 上不动 | 这颗料没有 DMA2 | USART1_RX 改用 DMA1 通道 5 | [DS5319](#source-ds5319-dma) | 这颗中密度只有一个 7 通道的 DMA1。DMA2 在 C8 上作废 |
| 对照 F4 例程时通道号能对上，板上不对 | F4 的编号被写进了 C8 | F4 那一组号留在 F4 | [RM0090](#source-rm0090) | F4 的 USART1_RX 是 DMA2 Stream 5、Channel 4。FIFO 是 4 个 32 位字。这条不证明 C8 有 DMA2 |
| 循环模式下进度越算越大 | 用了 `长度 − CNDTR` 当累计 | 进度用回调里的写位置 | [RM0008](#source-rm0008-dma) | 计数归零后硬件重装。进度用回调里的写位置 |

```

英文插在 `<!-- /video:ch10 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The DMA conclusion in this chapter is pinned to order code STM32F103C8T6. The channel numbers and the half-word ledger are copied whole from Appendix D. Do not import the 21 µs from chapter file 09.

This medium-density part has one DMA and 7 channels. The classification cell "DMA2 (5 channels, high-density)" is void on STM32F103C8T6. See [DS5319 Rev 20 section 2.3.13](#source-ds5319-dma). F4 streams and channels are another manual: USART1_RX is DMA2 Stream 5, Channel 4, and the FIFO is four 32-bit words. Writing that set onto a C8 leaves the counter still. See [RM0090](#source-rm0090). Do not edit that existing object.

ADC1 = DMA1 channel 1. USART1_TX = DMA1 channel 4. USART1_RX = DMA1 channel 5. The four blocks claim only these three Appendix D rows. See [RM0008 Rev 21 chapter 10](#source-rm0008-dma).

Eight half-words with `CNDTR` reading 3: `8 − 3 = 5` samples have been written, and the byte count is `5 × 2 = 10`. Half-transfer is at 4 samples, which is 8 bytes, not 4 bytes. Treating `CNDTR` as remaining bytes reads "3 left" as 3 bytes. That is the failure path.

When the count reaches zero, hardware reloads `CNDTR`. `length − CNDTR` is not cumulative progress. The position still comes from `Size` and `old_pos` in the callback, the same ledger as Appendix A. Do not edit Appendix A.

The F1 DMA controller is an AHB master. Peripheral registers sit on APB. F1 has no D-Cache. H7 cache maintenance stays in the core ideas and out of this part's four-block claims.

USART1_TX is still pin 30 PA9 from chapter file 06. This figure only notes the channel number. It does not redraw that frame. ADC sample time stays in chapter file 09.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-10-dma-cndtr.svg" width="760" alt="Eight half-words with CNDTR at 3 means 5 samples and 10 bytes written; treating the remaining count as bytes cuts the buffer wrong">
  <br><sub>▲ Drawn for this book. STM32F103C8T6 has only DMA1. USART1_TX uses channel 4, the width is a half-word, and the buffer length is 8. With CNDTR = 3, 5 samples and 10 bytes have been written. Half-transfer is at sample 4, 8 bytes. The failure treats that same reading as bytes. TX still leaves on pin 30 PA9. DMA2 Stream 5 has no counter on this C8. Sources: [RM0008 Rev 21 chapter 10](#source-rm0008-dma) and [DS5319 Rev 20 section 2.3.13](#source-ds5319-dma).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/dma-cndtr.gif" width="640" alt="In an 8-half-word buffer CNDTR falls to 3: 5 samples and 10 bytes written">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the normal path: CNDTR falls to 3, marked as 5 samples and 10 bytes. Print uses the static figure. Treating the remaining count as bytes is not on this GIF.</sub>
</p>

`dma-circular.svg` and `dma-ring.gif` stay in their original section and are marked as side figures.

## Timing or state

| Length | Width | CNDTR | Samples written | Bytes written |
| --- | --- | --- | --- | --- |
| 8 | half-word | 3 | 5 | 10 |
| 8 | half-word | half-transfer | 4 | 8, not 4 bytes |
| 8 | treated as bytes | 3 | cut wrong | "3 left" was read as 3 bytes |
| USART1_TX | DMA1 channel 4 | — | — | Pin 30 PA9 |
| USART1_RX | DMA1 channel 5 | — | — | Not DMA2 Stream 5 |
| ADC1 | DMA1 channel 1 | — | — | The memory-to-memory example contends for this channel |
| Void | DMA2 Stream 5 | no counter on this part | — | The F4 FIFO is four 32-bit words and does not prove the C8 has DMA2 |
| Circular | reload at zero | the reloaded CNDTR | not a cumulative total | `length − CNDTR` is not progress |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The second half of a half-word array looks like new data | Half-transfer was treated as 4 bytes | Handle half-transfer as 4 samples, 8 bytes | [RM0008](#source-rm0008-dma) | `CNDTR` counts data items. 5 of 8 half-words is 10 bytes. Half-transfer is not 4 bytes |
| `CNDTR` reads 3 and the byte count does not match | The remaining count was treated as bytes | Subtract samples first, then multiply by 2 | [RM0008](#source-rm0008-dma) | 3 half-words left is not 3 bytes left |
| DMA2 Stream 5 was configured and the C8 does not move | This part has no DMA2 | Use DMA1 channel 5 for USART1_RX | [DS5319](#source-ds5319-dma) | This medium-density part has one 7-channel DMA1. DMA2 is void on the C8 |
| An F4 example's channel numbers match the text and not the board | The F4 numbers were written onto the C8 | Leave that set of numbers on F4 | [RM0090](#source-rm0090) | F4 USART1_RX is DMA2 Stream 5, Channel 4. The FIFO is four 32-bit words. This does not prove the C8 has DMA2 |
| Progress in circular mode keeps growing | `length − CNDTR` was used as a cumulative total | Use the write position from the callback | [RM0008](#source-rm0008-dma) | Hardware reloads the count at zero. Progress uses the write position in the callback |

```

Cache、FIFO 阈值和局部变量缓冲区留在核心原理。局部变量那一行不引入新的通道号。

- [ ] **Step 5: 追加两个来源对象**

按 Task 5 的字段规则，把 `rm0008-dma`、`ds5319-dma` 追加到两份 manifest 的 `sources` 末尾。不要改 `rm0090`。罗盘改成测试里的 `compass`。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4DmaChapterTests -v`

Expected: OK。

```bash
git add docs/10-DMA.md docs/en/10-dma.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch4_chapters.py
git commit -m "book: 加厚第 10 章并把半字账钉在 5 个采样"
```

### Task 8: Thicken chapter 11 in both languages

**Files:**
- Modify: `docs/11-RTC与看门狗.md`
- Modify: `docs/en/11-rtc-watchdog.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `rm0008-wdg`、`rm0008-rtc`、`ds5319-rtc`；`11-RTC与看门狗.md` 的 `sources` 改为 `["rm0008", "ds5319", "rm0008-wdg", "rm0008-rtc", "ds5319-rtc", "pm0075-rdp"]`）
- Modify: `stm32-book/manifest-en.json`（同一组字段规则；`11-rtc-watchdog.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch4_chapters.py`
- Test: `stm32-book/tests/test_batch4_chapters.py`

**Interfaces:**
- Consumes: `rm0008-wdg`、`rm0008-rtc`、`ds5319-rtc`、Task 5 已经追加的 `pm0075-rdp`，以及 `assets/diagrams/sample-11-iwdg-1s.svg`、`assets/gif/iwdg-1s.gif`。若 Task 3 拆出了 `sample-11-rtc-prescaler.svg`，关键插图在主图之后再引用它。
- Produces: 四块各一次。四块写明 IWDG 喂早不复位，42 个备份寄存器在 C8 上作废，并且不出现 `6 pF`。不重画 `iwdg-window.svg`。不新建 `pm0075-rdp`。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch4_chapters.py` 末尾、`if __name__` 之前追加：

```python
class Batch4WatchdogChapterTests(unittest.TestCase):
    def test_watchdog_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "11-RTC与看门狗.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "11-rtc-watchdog.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertNotIn("6 pF", zh)
        self.assertNotIn("6 pF", en)
        self.assertNotIn("过早/过晚都触发复位", zh)
        self.assertNotIn("too early and too late both reset", en)
        self.assertIn("6.5536", zh)
        self.assertIn("6.5536", en)
        self.assertNotIn("4095/625", zh)
        self.assertNotIn("4095/625", en)
        for text in (zh, en):
            for token in (
                "624",
                "625",
                "32767",
                "32768",
                "58.25",
                "0x7F",
                "0x50",
                "40",
                "30",
                "60",
                "#source-rm0008-wdg",
                "#source-rm0008-rtc",
                "#source-ds5319-rtc",
                "#source-pm0075-rdp",
            ):
                self.assertIn(token, text)
        self.assertIn("第 1 脚", zh)
        self.assertIn("第 3 脚", zh)
        self.assertIn("第 4 脚", zh)
        self.assertIn("pin 1", en)
        self.assertIn("pin 3", en)
        self.assertIn("pin 4", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            self.assertNotIn("6 pF", blocks)
            self.assertNotIn("±20 ppm", blocks)
            self.assertNotIn("±50%", blocks)
            self.assertNotIn("0xA5A5", blocks)
        self.assertIn("喂早不复位", zh_blocks)
        self.assertIn("does not reset", en_blocks)
        self.assertIn("作废", zh_blocks)
        self.assertIn("void", en_blocks.lower())
        self.assertIn("../assets/diagrams/sample-11-iwdg-1s.svg", zh)
        self.assertIn("../../assets/diagrams/sample-11-iwdg-1s.svg", en)
        self.assertIn("../assets/gif/iwdg-1s.gif", zh)
        self.assertIn("../../assets/gif/iwdg-1s.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        self.assertLess(zh_key.index("sample-11-iwdg-1s.svg"), zh_key.index("iwdg-1s.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0])
        self.assertNotIn("示意图", zh_key)
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-wdg": (
                "第 11 章的 1 秒和窗口。预分频 64、f_LSI 按 40 kHz 时计数频率 625 Hz。Reload 624 是 1 秒，Reload 625 多一个计数。IWDG 减到 0 才复位。WWDG 在 36 MHz、预分频 8、初值 0x7F 时超时 58.25 ms；计数器大于窗口值时喂狗会复位。不把 40 kHz 的秒数写成保证值。不改附录 D。",
                "Chapter 11's one second and the window. Prescaler 64 at 40 kHz counts at 625 Hz. Reload 624 is 1 second and Reload 625 is one extra count. The IWDG resets only at 0. The WWDG at 36 MHz, prescaler 8, and 0x7F times out in 58.25 ms, and feeding while the counter is above the window resets it. Does not treat the 40 kHz second as a guarantee. Does not change Appendix D.",
            ),
            "rm0008-rtc": (
                "第 11 章的 1 Hz 时基。RTC 时钟除以 (PRL + 1)。32.768 kHz 配 PRL = 32767 得到 1 Hz。PRL = 32768 不是 1 Hz。写备份域之前置 PWR_CR 的 DBP。不把 F4 的 0xCA、0x53 或 TR/DR 写进来。",
                "Chapter 11's 1 Hz time base. The RTC clock is divided by (PRL + 1). 32.768 kHz with PRL = 32767 is 1 Hz. PRL = 32768 is not 1 Hz. Set DBP in PWR_CR before writing the backup domain. Does not import F4 keys 0xCA and 0x53 or call TR/DR the calendar on this part.",
            ),
            "ds5319-rtc": (
                "第 11 章主图的晶振脚、10 个备份寄存器和 LSI 范围。表 25 的 fLSI 是 30 / 40 / 60 kHz。备份寄存器 10 个 16 位，共 20 字节。第 1 脚 VBAT，第 3 脚 PC14-OSC32_IN，第 4 脚 PC15-OSC32_OUT。调试时可以冻住独立看门狗。不编负载电容的皮法。不把 ±20 ppm 或 ±50% 写进 snapshot。",
                "Chapter 11's crystal pins, ten backup registers, and the LSI range. Table 25 prints fLSI as 30 / 40 / 60 kHz. Ten 16-bit backup registers are 20 bytes. Pin 1 is VBAT, pin 3 is PC14-OSC32_IN, and pin 4 is PC15-OSC32_OUT. The independent watchdog can be frozen while debugging. Does not invent a load-capacitor picofarad. Does not put ±20 ppm or ±50% in the snapshot.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "ds5319", "rm0008-wdg", "rm0008-rtc", "ds5319-rtc", "pm0075-rdp"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["11-RTC与看门狗.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["11-rtc-watchdog.md"]["sources"])
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
            zh_manifest["sources"]["pm0075-rdp"],
            zh_manifest["sources"]["pm0075-rdp"],
        )
        baseline_zh, _baseline_en = baseline_manifests()
        self.assertNotIn("pm0075-rdp", baseline_zh["sources"])
        self.assertEqual(
            baseline_zh["sources"]["ds5319"],
            zh_manifest["sources"]["ds5319"],
        )
```

若 Task 2 把调试冻住的位名写进了 `rm0008-wdg` 的 snapshot，坑卡「断点停住以后自己复位」那一行的主张里加上印出的名字，并让测试里的 `rm0008-wdg` scope 仍是上面这句。位名留在 snapshot，不改 scope 的句子，除非印出的名字必须出现在主张里。主张里加上名字时，中英四块那一行一起加，测试对 scope 的相等断言保持上面的句子。

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4WatchdogChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 改正图注、LSI、备份寄存器、皮法和 4095，并删掉旧坑表**

中文 `docs/11-RTC与看门狗.md` 把章首这一行：

```markdown
  <br><sub>▲ 动画：独立看门狗计数与喂狗窗口（过早/过晚都触发复位）（作者自绘矢量动画，非实拍）</sub>
```

换成：

```markdown
  <br><sub>▲ 辅图。独立看门狗只惩罚喂晚。喂早也复位的是窗口看门狗。不播放这张图时，1 秒和减到 0 才复位都在静态主图上。（作者自绘矢量动画，非实拍）</sub>
```

把 LSE 这一行的精度格从 `高（±20 ppm）` 换成 `由晶振决定。±20 ppm 不进四块`。

把 LSI 这一行：

```markdown
| LSI（内部 RC） | ≈ 32~40 kHz | 低（±50% 起振误差、温漂大） | 无 | 省引脚/仅做唤醒 |
```

换成：

```markdown
| LSI（内部 RC） | 最小 30 kHz，典型 40 kHz，最大 60 kHz | 表 25 的范围，不是 ±50% | 无 | 省引脚/仅做唤醒 |
```

把备份寄存器这一行：

```markdown
| STM32F1 | `BKP_DR1`~`BKP_DR10`（42 个，大容量） | 16 位 |
```

换成：

```markdown
| STM32F103C8T6 | `BKP_DR1`~`BKP_DR10`，10 个 16 位，共 20 字节。42 个是大容量，在这颗料上作废 | 16 位 |
```

在 IWDG 与 WWDG 对比表后面加一句：

```markdown
独立看门狗喂早不复位。喂早也复位的是窗口看门狗。
```

硬件表里 LSE 那一格：

```markdown
| BluePill (F103) | LSE 晶振 | PC14=OSC32_IN、PC15=OSC32_OUT | 焊 32.768 kHz 晶振 + 2×负载电容（~6 pF） |
```

换成：

```markdown
| BluePill (F103) | LSE 晶振 | PC14=OSC32_IN、PC15=OSC32_OUT | 焊 32.768 kHz 晶振，负载电容按晶振手册选择 |
```

把这一段：

```markdown
> ⚠️ 负载电容要按晶振手册选（常见 6 pF / 12.5 pF），**电容过大 LSE 不起振**，是「RTC 不走时」的头号原因。
```

换成：

```markdown
> ⚠️ 负载电容按晶振手册选择。DS5319 这一节没有印成 6 pF，四块不写皮法。电容过大时 LSE 可以不起振。
```

把这一行：

```c
    hiwdg.Init.Reload    = 4095;                /* 超时 ≈ 4095/625 ≈ 6.55 s */
```

换成：

```c
    hiwdg.Init.Reload    = 4095;                /* 超时 (4095 + 1) / 625 = 6.5536 s。四块的主账仍是 Reload 624 的 1 秒 */
```

英文做同样的六处替换。章首图注换成：

```markdown
  <br><sub>▲ Side figure. The independent watchdog only punishes a late feed. An early feed that also resets is the window watchdog. Without playing this figure, the 1 second and the reset-at-zero are both on the static figure. (vector animation drawn by the author, not a live recording)</sub>
```

英文 LSI 行换成最小 30 kHz、典型 40 kHz、最大 60 kHz，并写明不是 ±50%。英文 LSE 精度格写成 `Set by the crystal. ±20 ppm stays out of the four blocks`。英文备份寄存器行写成 10 个 16 位、20 字节，42 个在 C8 上作废。英文对比表后加 `An early feed does not reset the IWDG. An early feed that resets is the window watchdog.` 英文硬件备注改成 `Solder a 32.768 kHz crystal. Choose the load capacitors from the crystal manual.` 英文 6 pF 警告改成 `Choose the load capacitors from the crystal manual. DS5319 does not print 6 pF in this section, and the four blocks do not write a picofarad. Too much capacitance can keep the LSE from starting.` 英文 `4095/625 ≈ 6.55 s` 改成 `(4095 + 1) / 625 = 6.5536 s`，并写明四块的主账仍是 Reload 624。

中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。动手实验里的「约 6.5 s」可以留下。魔法值 `0xA5A5` 留在代码里，不进出处卡。不重画 `iwdg-window.svg`，也不重画第 03 章的 LED 图。PC13 若还当心跳灯，沿用第 03 章：只能灌电流，写 0 才亮。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch11 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的看门狗和 RTC 结论只钉在订货号 STM32F103C8T6 上。1 秒整格照抄附录 D：预分频 64，Reload = 624，LSI 按典型 40 kHz 得到 625 Hz。LSI 的范围用表 25 的 30 / 40 / 60 kHz，不把 40 kHz 写成保证值。

`T = 64 / 40000 × (624 + 1) = 1` s。Reload 写成 625 时，`(625 + 1) / 625` 多一个计数。同一套预分频和重载：LSI = 30 kHz 时 `64 / 30000 × 625 = 4/3` s；LSI = 60 kHz 时 `64 / 60000 × 625 = 2/3` s，正是 30 kHz 那一档的一半。附录 D 写「大约一半」，因为 30 kHz 和 60 kHz 是手册范围的两端，不是每颗料的实测。最长一档大约 26 s 这句沿用附录 D，不另编一个保证的最大值。独立看门狗只在减到 0 时复位。喂早不复位。见 [RM0008 Rev 21 第 17 章](#source-rm0008-wdg) 和 [DS5319 Rev 20 表 25](#source-ds5319-rtc)。

窗口看门狗喂早和喂晚都会复位。PCLK1 = 36 MHz，预分频 8，计数初值 `0x7F`：超时 `(1/36e6) × 4096 × 8 × 64 = 58.25` ms。窗口值 `0x50` 时，计数器还大于 `0x50` 就喂狗，会立刻复位。这是旁注，不是 IWDG 的主波形。

若片段留下 Reload = 4095，超时写成 `(4095 + 1) / 625 = 6.5536` s，不写成 `4095/625`。动手实验里的「约 6.5 s」可以留下，不进四块的主账。主图只画 624 这一秒。

LSE 是 32.768 kHz，从第 3 脚 PC14-OSC32_IN 和第 4 脚 PC15-OSC32_OUT 进来。PRL = 32767 时 `(32767 + 1)` 把 32768 Hz 分成 1 Hz。PRL = 32768 不是 1 Hz。这是 RTC 的失败路径。LSI 典型 40 kHz，用整数 PRL 得不到跨 30–60 kHz 仍成立的 1 Hz。备份域由第 1 脚 VBAT 在主电源消失后续电。写之前打开 PWR 与 BKP 时钟，并置 `PWR_CR` 的 DBP。见 [RM0008 Rev 21 第 16 章](#source-rm0008-rtc)。

这颗中密度是 10 个 16 位备份数据寄存器，共 20 字节。42 个是大容量的句子，在 C8 上作废。F4 的 20 个 32 位备份寄存器和 BCD 的 `TR`/`DR` 在这颗料上作废。日历由软件从 32 位秒计数换算。这句由「这颗料是 32 位计数器、10 个 16 位寄存器」支持，不新开 F4 RTC 的 id。

IWDG 在 Stop 和 Standby 里继续计数。调试时可以冻住计数器，沿用章内的 `__HAL_DBGMCU_FREEZE_IWDG()`。位名只有 RM0008 印出来才写进主张。没印出来，这里只写「调试时可以冻住」，不编位号。`WDG_SW = 0` 时上电就由硬件看门狗接管，软件关不掉；为 1 时是软件看门狗。这句链接 [PM0075](#source-pm0075-rdp)，不在第 01 章展开。

四块不写 6 pF，也不写 ±20 ppm 和 ±50%。LSE 用着第 3 脚和第 4 脚时，这两只脚不再当 GPIO。PC13 若还当心跳灯，沿用第 03 章：只能灌电流，写 0 才亮，不重画那张 LED 图。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-11-iwdg-1s.svg" width="760" alt="Reload 624 在 40 kHz 典型值下是 1 秒；减到 0 才复位；LSE 要 PRL = 32767 才是 1 Hz">
  <br><sub>▲ 自绘。STM32F103C8T6。LSI 典型 40 kHz，范围 30–60 kHz。预分频 64，计数频率 625 Hz，Reload = 624，在减到 0 之前喂狗是 1 秒的典型账，不是保证值。失败路径是减到 0，或把 Reload 写成 625。备份域是第 1 脚 VBAT、第 3 脚 PC14、第 4 脚 PC15，32.768 kHz，PRL = 32767，10 个 16 位寄存器。PRL = 32768 不是 1 Hz。窗口看门狗在计数器大于 0x50 时喂狗会复位，超时 58.25 ms。出处是 [DS5319 Rev 20 表 25、第 2.3.14 节和第 2.3.15 节](#source-ds5319-rtc) 以及 [RM0008 Rev 21 第 17 章](#source-rm0008-wdg)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/iwdg-1s.gif" width="640" alt="625 Hz 的计数在减到 0 之前被喂狗，Reload = 624">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：625 Hz 的计数在减到 0 之前被喂狗，标出 Reload = 624 和 40 kHz 典型值。印刷以静态主图为准。减到 0、Reload = 625 和窗口看门狗的早喂不在这条 GIF 上。</sub>
</p>

`iwdg-window.svg` 留作辅图。不播放它。喂早也复位的那一条属于窗口看门狗，已经改在章首图注里，不在这张静态主图上冒充 IWDG。

## 时序或状态

| 预分频 | f_LSI | Reload | (Reload + 1) | 时间 | 复位与否 |
| --- | --- | --- | --- | --- | --- |
| 64 | 40 kHz | 624 | 625 | 1 s | 减到 0 才复位。喂早不复位 |
| 64 | 40 kHz | 625 | 626 | 多一个计数 | 不是 1 秒整 |
| 64 | 30 kHz | 624 | 625 | 4/3 s | 不是保证值 |
| 64 | 60 kHz | 624 | 625 | 2/3 s | 大约是 30 kHz 那一档的一半 |
| RTC | 32768 Hz | PRL = 32767 | 32768 | 1 Hz | 分频比是 (PRL + 1) |
| RTC 失败 | 32768 Hz | PRL = 32768 | 32769 | 不是 1 Hz | 改成 32767 |
| 备份寄存器 | — | 10 个 16 位 | 20 字节 | 第 1 脚 VBAT 续电 | 42 个在 C8 上作废 |
| WWDG | PCLK1 = 36 MHz | 预分频 8，初值 `0x7F` | — | 58.25 ms | 计数器大于 `0x50` 时喂狗复位 |
| 对照 | 64 | 4095 | 4096 | 6.5536 s | 不取代 Reload 624 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 按 40 kHz 算的 1 秒，板上偏短或偏长 | 40 kHz 只是典型值 | Reload 用 624，并按 30–60 kHz 留余量 | [DS5319](#source-ds5319-rtc) | 表 25 的 fLSI 是 30 / 40 / 60 kHz。40 kHz 是典型值。这一秒不是保证值 |
| Reload 写成 625，超时比 1 秒多一拍 | 少算了一次 +1 的位置 | 改成 624 | [RM0008](#source-rm0008-wdg) | 预分频 64、40 kHz 时计数频率 625 Hz。时间用 `(Reload + 1)`。625 多一个计数 |
| 独立看门狗一喂就复位，像有窗口 | 把它当成了窗口看门狗 | 喂早对 IWDG 是允许的。要窗口用 WWDG | [RM0008](#source-rm0008-wdg) | IWDG 减到 0 才复位。WWDG 在计数器大于窗口值时喂狗也会复位。36 MHz 下 `0x7F` 与预分频 8 的超时是 58.25 ms |
| 主电源掉了日历归零 | 备份域没有续电，或 PRL 不对 | 接上第 1 脚 VBAT，LSE 用第 3 脚和第 4 脚，PRL 写 32767 | [DS5319](#source-ds5319-rtc) | 10 个 16 位备份寄存器由 VBAT 续电。默认 1 秒时基来自 32.768 kHz。42 个在这颗料上作废 |
| 预分频写成 32768，秒脉冲偏慢 | 分频比是 (PRL + 1) | 改成 32767 | [RM0008](#source-rm0008-rtc) | 分频比是 `(PRL + 1)`。32768 Hz 要写成 32767 才是 1 Hz |
| 断点停住以后自己复位 | 调试时计数器还在减 | 调试时冻住 IWDG | [DS5319](#source-ds5319-rtc) | 第 2.3.15 节：调试时可以冻住独立看门狗的计数器。位名不在这条主张里，除非 `rm0008-wdg` 的 snapshot 已经写上印出的名字 |
| 选项字节把看门狗改成上电就跑，软件关不掉 | `WDG_SW` 为 0 | `WDG_SW` 为 0 是硬件看门狗，为 1 才是软件看门狗 | [PM0075](#source-pm0075-rdp) | USER 字节的这一位：0 表示硬件看门狗，1 表示软件看门狗 |

```

若 Task 3 拆出了 `sample-11-rtc-prescaler.svg`，在中文关键插图的 GIF 之前再插一张，路径 `../assets/diagrams/sample-11-rtc-prescaler.svg`，图注写「自绘」，替代文本写出 PRL = 32767 才是 1 Hz。英文用 `../../assets/diagrams/sample-11-rtc-prescaler.svg`。第一张图仍是 `sample-11-iwdg-1s.svg`。

英文插在 `<!-- /video:ch11 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The watchdog and RTC conclusion in this chapter is pinned to order code STM32F103C8T6. The 1 second is copied whole from Appendix D: prescaler 64, Reload = 624, and LSI taken as a typical 40 kHz gives 625 Hz. The LSI range is Table 25's 30 / 40 / 60 kHz. Do not call 40 kHz a guarantee.

`T = 64 / 40000 × (624 + 1) = 1` s. Reload written as 625 makes `(625 + 1) / 625` one extra count. The same prescaler and reload: at LSI = 30 kHz, `64 / 30000 × 625 = 4/3` s; at LSI = 60 kHz, `64 / 60000 × 625 = 2/3` s, half of the 30 kHz case. Appendix D says "about half" because 30 kHz and 60 kHz are the ends of the manual range, not a measurement of every part. The "about 26 s" longest step stays with Appendix D. Do not invent a guaranteed maximum. The independent watchdog resets only when the counter reaches 0. An early feed does not reset it. See [RM0008 Rev 21 chapter 17](#source-rm0008-wdg) and [DS5319 Rev 20 Table 25](#source-ds5319-rtc).

The window watchdog resets on both an early feed and a late feed. PCLK1 = 36 MHz, prescaler 8, counter `0x7F`: the timeout is `(1/36e6) × 4096 × 8 × 64 = 58.25` ms. With window `0x50`, feeding while the counter is still above `0x50` resets immediately. That is a margin note, not the IWDG waveform.

If a fragment keeps Reload = 4095, write the timeout as `(4095 + 1) / 625 = 6.5536` s, not `4095/625`. The hands-on "about 6.5 s" may stay. It does not enter the four blocks' main ledger. The key figure draws only the 624 second.

LSE is 32.768 kHz, entering on pin 3 PC14-OSC32_IN and pin 4 PC15-OSC32_OUT. PRL = 32767 makes `(32767 + 1)` divide 32768 Hz into 1 Hz. PRL = 32768 is not 1 Hz. That is the RTC failure path. A typical 40 kHz LSI has no integer PRL that stays 1 Hz across 30–60 kHz. The backup domain is kept by pin 1 VBAT after the main supply disappears. Before a write, enable the PWR and BKP clocks and set DBP in `PWR_CR`. See [RM0008 Rev 21 chapter 16](#source-rm0008-rtc).

This medium-density part has ten 16-bit backup data registers, 20 bytes. Forty-two is the high-density sentence and is void on the C8. F4's twenty 32-bit backup registers and the BCD `TR`/`DR` are void on this part. Software turns the 32-bit second counter into a calendar. That sentence is supported by "this part is a 32-bit counter and ten 16-bit registers". Do not open an F4 RTC id.

The IWDG keeps counting in Stop and Standby. It can be frozen while debugging, using the chapter's `__HAL_DBGMCU_FREEZE_IWDG()`. A bit name is written into the claim only when RM0008 prints it. Otherwise write only "it can be frozen while debugging" and do not invent a bit number. `WDG_SW = 0` means the hardware watchdog takes over at power-up and software cannot turn it off. `WDG_SW = 1` is the software watchdog. That sentence links [PM0075](#source-pm0075-rdp) and is not expanded in chapter 01.

The four blocks do not write 6 pF, ±20 ppm, or ±50%. While LSE uses pin 3 and pin 4, those pins are not GPIO. If PC13 is still the heartbeat LED, keep chapter 03's rule: it can only sink, and writing 0 turns it on. Do not redraw that LED figure.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-11-iwdg-1s.svg" width="760" alt="Reload 624 is 1 second at a typical 40 kHz; reset happens only at 0; LSE needs PRL = 32767 for 1 Hz">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. LSI is typically 40 kHz and spans 30–60 kHz. Prescaler 64, a 625 Hz count, and Reload = 624 are a 1 second ledger at the typical value, not a guarantee, when the dog is fed before zero. The failure is reaching 0, or writing Reload as 625. The backup strip is pin 1 VBAT, pin 3 PC14, pin 4 PC15, 32.768 kHz, PRL = 32767, and ten 16-bit registers. PRL = 32768 is not 1 Hz. The window watchdog resets if fed while the counter is above 0x50, on a 58.25 ms scale. Sources: [DS5319 Rev 20 Table 25 and sections 2.3.14 and 2.3.15](#source-ds5319-rtc) and [RM0008 Rev 21 chapter 17](#source-rm0008-wdg).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/iwdg-1s.gif" width="640" alt="A 625 Hz count is fed before it reaches 0, with Reload = 624">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the normal path: a 625 Hz count is fed before zero, marked with Reload = 624 and a typical 40 kHz. Print uses the static figure. Reaching zero, Reload = 625, and an early window-watchdog feed are not on this GIF.</sub>
</p>

`iwdg-window.svg` stays a side figure. Do not play it for the IWDG claim. The early-feed reset belongs to the window watchdog. That sentence is in the opening caption. It does not pretend to be the IWDG on this static figure.

## Timing or state

| Prescaler | f_LSI | Reload | (Reload + 1) | Time | Reset? |
| --- | --- | --- | --- | --- | --- |
| 64 | 40 kHz | 624 | 625 | 1 s | Resets only at 0. An early feed does not reset |
| 64 | 40 kHz | 625 | 626 | one extra count | Not exactly 1 second |
| 64 | 30 kHz | 624 | 625 | 4/3 s | Not a guarantee |
| 64 | 60 kHz | 624 | 625 | 2/3 s | About half of the 30 kHz case |
| RTC | 32768 Hz | PRL = 32767 | 32768 | 1 Hz | The divider is (PRL + 1) |
| RTC failure | 32768 Hz | PRL = 32768 | 32769 | not 1 Hz | Change it to 32767 |
| Backup registers | — | ten 16-bit | 20 bytes | Pin 1 VBAT keeps them | 42 is void on the C8 |
| WWDG | PCLK1 = 36 MHz | prescaler 8, counter `0x7F` | — | 58.25 ms | Feeding above `0x50` resets |
| Comparison | 64 | 4095 | 4096 | 6.5536 s | Does not replace Reload 624 |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| A 1 second computed at 40 kHz runs short or long on the board | 40 kHz is only typical | Use Reload 624 and leave margin for 30–60 kHz | [DS5319](#source-ds5319-rtc) | Table 25 prints fLSI as 30 / 40 / 60 kHz. 40 kHz is typical. That second is not a guarantee |
| Reload written as 625 times out one count past 1 second | The +1 was applied to the wrong side | Change it to 624 | [RM0008](#source-rm0008-wdg) | Prescaler 64 at 40 kHz counts at 625 Hz. Time uses `(Reload + 1)`. 625 is one extra count |
| The independent watchdog resets as soon as it is fed, as if it had a window | It was treated as the window watchdog | An early feed is allowed for the IWDG. Use the WWDG for a window | [RM0008](#source-rm0008-wdg) | The IWDG resets only at 0. The WWDG also resets when fed while the counter is above the window. At 36 MHz, `0x7F` and prescaler 8 time out in 58.25 ms |
| The calendar returns to zero when the main supply drops | The backup domain was not kept, or PRL is wrong | Connect pin 1 VBAT, use pins 3 and 4 for LSE, and write PRL 32767 | [DS5319](#source-ds5319-rtc) | Ten 16-bit backup registers are kept by VBAT. The default 1 second comes from 32.768 kHz. 42 is void on this part |
| A prescaler of 32768 makes the second pulse slow | The divider is (PRL + 1) | Change it to 32767 | [RM0008](#source-rm0008-rtc) | The divider is `(PRL + 1)`. 32768 Hz is 1 Hz only when written as 32767 |
| The part resets by itself after a breakpoint | The counter kept running in debug | Freeze the IWDG while debugging | [DS5319](#source-ds5319-rtc) | Section 2.3.15: the independent watchdog counter can be frozen while debugging. The bit name is not in this claim unless the `rm0008-wdg` snapshot already records the printed name |
| Option bytes make the watchdog run from power-up and software cannot stop it | `WDG_SW` is 0 | 0 is the hardware watchdog and 1 is the software watchdog | [PM0075](#source-pm0075-rdp) | That bit in the USER byte: 0 means the hardware watchdog and 1 means the software watchdog |

```

- [ ] **Step 5: 追加三个来源对象**

按 Task 5 的字段规则，把 `rm0008-wdg`、`rm0008-rtc`、`ds5319-rtc` 追加到两份 manifest 的 `sources` 末尾。不要新建 `pm0075-rdp`，它已经在 Task 5 里。罗盘改成测试里的 `compass`，把 `pm0075-rdp` 放在数组最后。若 Task 2 改过 `rm0008-wdg` 的 snapshot，manifest 的 snapshot 用改过的那一串，中英相同。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch4_chapters.py Batch4WatchdogChapterTests -v`

Expected: OK。

```bash
git add docs/11-RTC与看门狗.md docs/en/11-rtc-watchdog.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch4_chapters.py
git commit -m "book: 加厚第 11 章并把 1 秒钉在 Reload 624"
```

`git diff --stat -- assets/diagrams/iwdg-window.svg` 应无输出。

### Task 9: Register the batch, bump 1.2.3, keep the ledgers

**Files:**
- Modify: `CREDITS.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `version` 与 `date`
- Modify: `stm32-book/revisions.json`
- Modify: `stm32-book/README.md`
- Modify: `stm32-book/tests/test_build.py`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 5 到 Task 8 已经写进 manifest 的十个新 id。日期是 `2026-10-25`，不另取。
- Produces: 两份 manifest 的 `version` 都是 `1.2.3`，`date` 都是 `2026-10-25`。`revisions.json` 的 `entries[0].version` 是 `1.2.3`，`entries[1]` 仍是现在的 1.2.2 四章说明，`entries[2]` 仍是 1.2.1 指南说明，`entries[3]` 仍是 1.2.0 观感说明。`test_build.py` 里当前版从 `1.2.2` 改为 `1.2.3`。`0x271` 断言、`167 ns` 断言和出版书签长度 44 的断言还在。

- [ ] **Step 1: 先改版本断言，让测试失败**

在 `stm32-book/tests/test_build.py` 里只改当前版断言。不要删 `0x271`、`167 ns`、`会上手的几笔账`、`Numbers to reconcile before changing family`、`Channels, descriptors, and fault registers`，也不要改 `self.assertEqual(44, len(outline))`。

把

```python
versions = ("1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

改成

```python
versions = ("1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

在 `self.assertLess(history.index(">1.2.2<"), history.index(">1.2.1<"))` 之前加一行：

```python
self.assertLess(history.index(">1.2.3<"), history.index(">1.2.2<"))
```

把修订列表的期望从

```python
["1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

改成

```python
["1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

把 `self.assertEqual("1.2.2", manifest["version"])` 改成 `self.assertEqual("1.2.3", manifest["version"])`。

把两处 `self.assertIn("<strong>v1.2.2</strong>", html)` 改成 `self.assertIn("<strong>v1.2.3</strong>", html)`。

`test_visual_polish_version_is_1_2_0` 改成核对当前条目是 1.2.3。把函数体里取条目的三行换成：

```python
        entry = revisions["entries"][0]
        batch3 = revisions["entries"][1]
        guide = revisions["entries"][2]
        previous = revisions["entries"][3]
```

把 `self.assertEqual("1.2.2", self.manifest["version"])` 改成 `self.assertEqual("1.2.3", self.manifest["version"])`。英文 manifest 和 `entry["version"]` 同样改成 `1.2.3`。`entry["date"]` 和两份 manifest 的 `date` 仍是 `2026-10-25`。

现在对 `entry["zh"]` 和 `entry["en"]` 的 1.2.2 两句，改去核对 `batch3`，原文不动：

```python
        self.assertEqual("1.2.2", batch3["version"])
        self.assertEqual(
            [
                "第 02 章把 CFGR 改回第 7.3.2 节，并写上 72 MHz 要 2 个等待、CSS 回到 HSI。第 05 章写上 1 kHz 和 500 Hz 两条路径。",
                "第 08 章写上 Mode 0、9 MHz，以及 0x9F 之后的 0xEF、0x40、0x17。第 09 章写上 12 MHz 下的 21 µs、除以 4096，以及 C8 有 ADC1/ADC2、没有 DAC。",
            ],
            batch3["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 02 moves CFGR back to section 7.3.2, with two Flash wait states at 72 MHz and CSS falling back to HSI. Chapter file 05 records both the 1 kHz path and the 500 Hz path.",
                "Chapter file 08 records Mode 0 at 9 MHz and, after 0x9F, the bytes 0xEF, 0x40, and 0x17. Chapter file 09 records 21 µs at 12 MHz, division by 4096, and that the C8 has ADC1 and ADC2 and no DAC.",
            ],
            batch3["en"],
        )
```

现在对 `guide` 的 1.2.1 两句保持原文，只是对象从 `entries[1]` 换成 `entries[2]`。现在对 `previous` 的 1.2.0 两句保持原文，只是对象从 `entries[2]` 换成 `entries[3]`。

`entry` 的中英改成：

```python
        self.assertEqual(
            [
                "第 01 章写上 SWD 在第 34 脚 PA13 和第 37 脚 PA14，读保护解除写 0xA5，BOOT0=1 且 BOOT1=0 进的是系统存储器。第 07 章写上 0x3C 在 HAL 里是 0x78，表 42 的 400 kHz 行是 0x801E 和 4.7 kΩ。",
                "第 10 章写上只有 DMA1，8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节。第 11 章写上预分频 64、Reload 624 在 40 kHz 典型值下是 1 秒，LSI 是 30–60 kHz，备份寄存器是 10 个。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 01 records SWD on pin 34 PA13 and pin 37 PA14, readout protection level 0 as 0xA5, and BOOT0=1 with BOOT1=0 entering system memory. Chapter file 07 records that 0x3C is 0x78 in HAL, and that Table 42's 400 kHz row is 0x801E with 4.7 kΩ.",
                "Chapter file 10 records DMA1 only, and that eight half-words with CNDTR 3 means 5 samples and 10 bytes written. Chapter file 11 records prescaler 64 and Reload 624 as 1 second at a typical 40 kHz, LSI as 30–60 kHz, and ten backup registers.",
            ],
            entry["en"],
        )
```

README 断言改成：

```python
        self.assertIn("当前版本：**v1.2.3 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.3。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2，", readme)
        self.assertIn("也不要把 1.2.2 的产物标成 1.2.3。", readme)
        self.assertIn("打 tag `v1.2.3`", readme)
        self.assertNotIn("当前版本：**v1.2.2", readme)
        self.assertNotIn("打 tag `v1.2.2`", readme)
```

- [ ] **Step 2: 运行版本测试，确认失败**

Run: `python3 stm32-book/tests/test_build.py BookBuildTests.test_revision_file_lists_1_0_0_through_manifest_version -v`

Expected: FAIL，修订列表的首项仍是 `1.2.2`。

- [ ] **Step 3: 写 1.2.3**

两份 manifest 的 `version` 改为 `1.2.3`，`date` 改为 `2026-10-25`。不要改 `sources` 里已有对象的字段。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入：

```json
{
  "version": "1.2.3",
  "date": "2026-10-25",
  "zh": [
    "第 01 章写上 SWD 在第 34 脚 PA13 和第 37 脚 PA14，读保护解除写 0xA5，BOOT0=1 且 BOOT1=0 进的是系统存储器。第 07 章写上 0x3C 在 HAL 里是 0x78，表 42 的 400 kHz 行是 0x801E 和 4.7 kΩ。",
    "第 10 章写上只有 DMA1，8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节。第 11 章写上预分频 64、Reload 624 在 40 kHz 典型值下是 1 秒，LSI 是 30–60 kHz，备份寄存器是 10 个。"
  ],
  "en": [
    "Chapter file 01 records SWD on pin 34 PA13 and pin 37 PA14, readout protection level 0 as 0xA5, and BOOT0=1 with BOOT1=0 entering system memory. Chapter file 07 records that 0x3C is 0x78 in HAL, and that Table 42's 400 kHz row is 0x801E with 4.7 kΩ.",
    "Chapter file 10 records DMA1 only, and that eight half-words with CNDTR 3 means 5 samples and 10 bytes written. Chapter file 11 records prescaler 64 and Reload 624 as 1 second at a typical 40 kHz, LSI as 30–60 kHz, and ten backup registers."
  ]
}
```

修订说明只写这四章，用文件名前缀，不写尚未加厚的章，不把标题写成「第 2 章」。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.2.3 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

把「发布 GitHub Release」一节里这一句的末尾，在现有「也不要把 1.2.1 的产物标成 1.2.2。」之后加上「也不要把 1.2.2 的产物标成 1.2.3。」，并把开头的「版本号已经是 1.2.2。」改成「版本号已经是 1.2.3。」。整句是：

```markdown
版本号已经是 1.2.3。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0，也不要把 1.2.0 的产物标成 1.2.1，也不要把 1.2.1 的产物标成 1.2.2，也不要把 1.2.2 的产物标成 1.2.3。
```

第三步的「在该提交上打 tag `v1.2.2`」改成「在该提交上打 tag `v1.2.3`」。这一步仍不创建 tag，也不创建 Release。前面的 artifact 名称和四份文件名保持不动。

- [ ] **Step 4: 在 CREDITS.md 增加 v1.2.3 小节，并改正张数**

第一节表格里这一行：

```markdown
| 静态框图（14 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |
```

换成 18 张。只有 `assets/diagrams/sample-11-rtc-prescaler.svg` 真的存在时才写成 19 张，并在实施 PR 说明里写明拆图原因。

```markdown
| 静态框图（18 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |
```

把

```markdown
| 光栅动画（12 个 GIF） | `assets/gif/` | **本仓库作者用纯 Python 渲染并手写 GIF 编码器生成**，脚本见 `tools/minigfx.py`、`tools/gen_gifs.py` |
```

换成：

```markdown
| 光栅动画（16 个 GIF） | `assets/gif/` | **本仓库作者用纯 Python 渲染并手写 GIF 编码器生成**，脚本见 `tools/minigfx.py`、`tools/gen_gifs.py` |
```

不要重跑已有 12 个 GIF。16 是 `BUILDERS` 的键数，不是 `*-zh.gif` 的张数。

第六节已有的「样本章的改写吸收（v1.1.0）」「第 04 章与第 06 章（v1.1.1）」「第 02、05、08、09 章（v1.2.2）」三个小节的标题和表都保留。在该节末尾追加：

```markdown
### 第 01、07、10、11 章（v1.2.3）

第 01、07、10、11 章用改写吸收补了同样的四块。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图和厂商数据手册不放进仓库。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| DS5319 Rev 20（2025-07），表 5、表 25、表 41、表 42，第 2.3.13、2.3.14、2.3.15 节 | ST 文档条款；只链接并改写事实，不转载手册 | 第 01 章第 34 脚和第 37 脚；第 07 章第 42、43 脚与 0x801E；第 10 章只有 DMA1；第 11 章 LSI 30/40/60 kHz、第 1/3/4 脚和 10 个备份寄存器 | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
| RM0008 Rev 21（2021-02），第 10、16、17、18、26 章 | ST 文档条款；只链接并改写事实，不转载手册 | 第 07 章地址字节与 ACK；第 10 章 CNDTR；第 11 章 1 秒、窗口和 PRL | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| PM0075，Doc ID 17863 Rev 2（2012-08） | ST 文档条款；只链接并改写事实，不转载手册 | 第 01 章读保护键 0xA5 与整片擦除；第 11 章 WDG_SW | https://www.st.com/resource/en/programming_manual/pm0075-stm32f10xxx-flash-memory-microcontrollers-stmicroelectronics.pdf |
| PM0056 Rev 7（2024-12），向量表 | ST 文档条款；只链接并改写事实，不转载手册 | 第 01 章第 0 字是 MSP，第 1 字是复位 | https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf |
| 本仓库 `examples/i2c-oled` | MIT | 第 07 章坑卡：器件地址宏是 0x78 | https://github.com/zhuguang-ZFG/STM32/tree/main/examples |
```

若 `pm0075-rdp` 的 URL 在 Task 2 改成了 `CD00283419` 那一地址，这一表的 PM0075 链接用改过的 URL。

- [ ] **Step 5: 运行整套测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。`test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py` 仍然通过。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。构建出的 HTML 里有 `v1.2.3`，并且 `id="source-ds5319-swd"`、`id="source-pm0075-rdp"`、`id="source-pm0056-vector"`、`id="source-ds5319-i2c"`、`id="source-rm0008-i2c"`、`id="source-rm0008-dma"`、`id="source-ds5319-dma"`、`id="source-rm0008-wdg"`、`id="source-rm0008-rtc"`、`id="source-ds5319-rtc"` 都在。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 6: Commit**

```bash
git add CREDITS.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 第 01、07、10、11 章登记来源并把整书标成 1.2.3"
```

### Task 10: Scope gate, then stop

**Files:**
- 不新增文件。这一任务只核对 diff。核对失败时，只撤销越界改动，不顺手加厚别的章。

**Interfaces:**
- Consumes: Task 1 到 Task 9 的提交。
- Produces: 一份只含第 01、07、10、11 章加厚的 diff。用户复审之前，实施 PR 保持打开。没有 tag，没有 Release。Book CI 变绿不等于可以 squash 合入。

- [ ] **Step 1: 核对 diff 的路径**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只出现这些路径。顺序可以不同。多出来的路径若是本计划自己的三份文件，也允许，它们不是章节正文。`sample-11-rtc-prescaler.svg` 只有在 Task 3 真的拆图时才允许出现。

```text
CREDITS.md
assets/README.md
assets/diagrams/sample-01-swd-vectors.svg
assets/diagrams/sample-07-i2c-addr.svg
assets/diagrams/sample-10-dma-cndtr.svg
assets/diagrams/sample-11-iwdg-1s.svg
assets/gif/dma-cndtr.gif
assets/gif/i2c-addr.gif
assets/gif/iwdg-1s.gif
assets/gif/swd-fetch.gif
docs/01-开发环境搭建.md
docs/07-I2C总线.md
docs/10-DMA.md
docs/11-RTC与看门狗.md
docs/en/01-dev-environment.md
docs/en/07-i2c.md
docs/en/10-dma.md
docs/en/11-rtc-watchdog.md
docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json
docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-source-list.json
docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch4-01-07-10-11.md
stm32-book/README.md
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_batch4_chapters.py
stm32-book/tests/test_batch4_sources.py
stm32-book/tests/test_build.py
tools/gen_gifs.py
tools/gen_sample_figures.py
tools/scan_batch4_chapters.py
```

`docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch4-01-07-10-11.md` 只在「先合并了本计划」的历史上出现。若实施分支从本计划提交切开，它会留在 diff 里，这是允许的。它不是章节正文。

`stm32-book/build_html.py`、`stm32-book/book/`、`docs/CONTENT_GUIDE.md`、`docs/en/CONTENT_GUIDE.md`、样本锁定、Batch2 锁定、Batch3 锁定，以及其余章节都不在这份列表里。

- [ ] **Step 2: 核对附录、构建脚本和已经加厚的章没有被卷进来**

Run:

```bash
git diff origin/main...HEAD -- stm32-book/build_html.py stm32-book/book/A-工程深读.md stm32-book/book/D-术语表.md stm32-book/book/en/A-uart-dma.md stm32-book/book/en/D-glossary.md docs/00-如何学习STM32.md docs/02-芯片选型与存储器时钟.md docs/03-GPIO与LED.md docs/08-SPI总线.md docs/09-ADC与DAC.md
```

Expected: 无输出。

Run:

```bash
git diff --name-only origin/main...HEAD -- docs/04-中断与NVIC.md docs/05-定时器与PWM.md docs/06-串口UART.md docs/en/04-interrupts-nvic.md docs/en/05-timer-pwm.md docs/en/06-uart.md assets/gif/i2c-timing.gif assets/gif/dma-ring.gif assets/diagrams/iwdg-window.svg assets/diagrams/sample-00-boot-state.svg assets/diagrams/sample-09-adc-sar.svg examples/i2c-oled examples/adc-dma
```

Expected: 无输出。

在 `stm32-book/build_html.py` 里确认 `display_chapter_number` 仍是文件名前缀加 1。本批 diff 必须为空，所以这一条只是读，不改。

- [ ] **Step 3: 再跑一遍验收命令**

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
python3 tools/check_assets.py
```

Expected: 四条命令都退出码 0。`check_assets.py` 的输出含 `全部通过`。

- [ ] **Step 4: 确认没有 tag 和 Release**

Run: `git tag --points-at HEAD`

Expected: 无输出。

不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.2` 或 `v1.2.3`。

- [ ] **Step 5: 停在用户复审**

实施 PR 的说明里写明：只加厚了文件 `01`、`07`、`10`、`11` 的中英八份；静态主图是 `sample-01-swd-vectors.svg`、`sample-07-i2c-addr.svg`、`sample-10-dma-cndtr.svg`、`sample-11-iwdg-1s.svg`；短 GIF 是辅图。第 01 章的 SWD 在第 34 脚 PA13 和第 37 脚 PA14，读保护解除写 `0xA5`，BOOT0=1 且 BOOT1=0 进的是系统存储器。第 07 章的 `0x3C` 在 HAL 里是 `0x78`，表 42 的 400 kHz 行是 `0x801E` 和 4.7 kΩ。第 10 章只有 DMA1，8 个半字且 `CNDTR` 为 3 时已写 5 个采样、10 字节。第 11 章预分频 64、Reload 624 在 40 kHz 典型值下是 1 秒，LSI 是 30–60 kHz，备份寄存器是 10 个。若向量表节号、CCR 位、调试冻住的位名、PM0075 的 URL，或第 11 章拆图和清单不同，说明里写明差异。

请用户看构建出的中英 HTML 里的这四章：四块是否都在、关掉动画之后主图是否仍能指出失败、`#source-` 是否点得到附录 E 的卡片。

第 01 章要能指出的失败是「第 35 脚被当成 SWCLK，或 PA13/PA14 被配成 GPIO」。第 07 章要能指出的失败是「DevAddress 填了 `0x3C`，第 9 个时钟没有 ACK」。第 10 章要能指出的失败是「半字的 `CNDTR` 被当成字节」。第 11 章要能指出的失败是「Reload 写成 625，或多等一个计数才复位；IWDG 喂早不复位」。

用户书面接受之前：

- 不为 `00`、`02`、`03`、`04`、`05`、`06`、`08`、`09`、`12`–`28` 开加厚 PR。
- 不加图目录或表目录。
- 不改 `stm32-book/build_html.py`，不改显示章号，不改 PDF 书签深度。
- 不打 `v1.2.3` 的 tag，不创建 GitHub Release。
- 不把 Book CI 变绿当成可以自动 squash 合入。人接受之前，实施 PR 保持打开。
- 不预选文件 `12` 作为下一批。下一批仍是 4 章，到下一次设计再锁。

这一步没有新的提交。若 Step 1 到 Step 3 发现越界文件，撤销那些文件里的越界改动后再提交一次，提交说明写明撤回了哪一处，然后仍停在这里。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 只加厚 01、07、10、11，中英一起，四块标题各一次 | Task 5、Task 6、Task 7、Task 8、Task 10 |
| 静态主图，正常路径和失败路径，不用 `Svg.footer()`，小于 60 KB | Task 3 |
| 短 GIF 只是辅图，帧数 3 到 12，不改已有 12 个 BUILDERS 的像素 | Task 4 |
| 第 01 章第 34/37 脚、`0xA5`、系统存储器 `0x1FFFF000`、64 KB 与 20 KB | Task 5 |
| 第 07 章 `0x78`、`0x801E`、4.7 kΩ、1 MHz 作废、`300ns / Cb` 不进四块 | Task 6 |
| 第 10 章只有 DMA1，5 个采样、10 字节，半传输 8 字节，不写 21 µs | Task 7 |
| 第 11 章 Reload 624、30–60 kHz、PRL 32767、10 个寄存器、喂早不复位、不写 6 pF | Task 8 |
| 向量表节号、CCR 位、调试冻住位名、PM0075 URL 按印出的文字改 snapshot | Task 2 |
| 新 id 只追加十个；`rm0008-boot`、`project-examples`、`rm0090` 不改对象 | Task 2、Task 5、Task 6、Task 7 |
| 版本 1.2.3 · 2026-10-25，不打 tag，不发 Release | Task 9、Task 10 |
| 不改附录 A、附录 D、`build_html.py`、样本锁定、Batch2 锁定、Batch3 锁定和其余章 | Task 10 |
| 书签仍是 44，`0x271` 与 `167 ns` 断言仍在，样本测试、Batch2 测试和 Batch3 测试不放宽 | Task 9 |
| CI 变绿后停下来等人复审，不自动合入 | Task 10 |
| 第 11 章超过 60 KB 才拆 `sample-11-rtc-prescaler.svg`，静态框图改为 19 张 | Task 3、Task 9 |

## 执行交接

计划写在 `docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch4-01-07-10-11.md`。实施时二选一：

1. Subagent-Driven（推荐）：每个任务一个新的子代理，任务之间复核。必用 superpowers:subagent-driven-development。
2. Inline Execution：在同一个会话里按 superpowers:executing-plans 分批做，每批停下来复核。

无论哪一种，Task 10 都停在人复审。人接受之前不合入。
