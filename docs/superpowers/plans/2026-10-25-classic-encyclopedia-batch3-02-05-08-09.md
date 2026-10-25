# Batch 3 Chapters 02, 05, 08, and 09 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只加厚第 02、05、08、09 章（中文和英文一起），写成和第 00、03、04、06 章相同的四块密度，每章一张可印刷的静态主图加一条短 GIF 辅图，把时钟、1 kHz、SPI 和 ADC 的数字改成和附录 D 同一笔账，合入时把整书升到 1.2.2 · 2026-10-25，然后停下来等人复审。人接受之前不合入。

**Architecture:** 章号已经由设计锁死，不再打分重选，也不拆成四份计划。四章共用一次版本号、一次来源追加和一次人审。先只读这四章的中英八份，确认四块还不存在、旧坑标题还在。来源清单和锁定文件已经随本计划提交。然后生成静态 SVG 和短 GIF，再改八份正文。新出处只追加进 `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `sources`。附录 E 的卡片仍由 `stm32-book/build_html.py` 的 `source_registry_html()` 生成。主图走 `tools/svgkit.py` 的 `tools/gen_sample_figures.py`。短 GIF 走 `tools/gen_gifs.py` 的 `BUILDERS`。版本号同时写进两份 manifest、`stm32-book/revisions.json` 和 `stm32-book/README.md`。日期写死 `2026-10-25`，不取实施当天的日期。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 -m unittest`、`tools/svgkit.py`、`tools/gen_gifs.py`、`tools/minigfx.py`、`tools/check_assets.py`。不新增依赖，不改 `requirements.txt`。

单文件测试写成 `python3 stm32-book/tests/<file>.py -v`。`stm32-book/tests/` 不是 Python 包。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

本计划不拆成四个子计划。设计规格把这四章锁成同一批，版本只升一次到 1.2.2。拆开会把一次人审拆成四次，或者让 1.2.2 先带着不完整的四章合入。

## Global Constraints

- 只把第 02、05、08、09 章加厚到和第 00、03、04、06 章相同的四块密度。中文和英文一起写完。文件名仍是 `docs/02-芯片选型与存储器时钟.md`、`docs/en/02-part-and-clock.md`、`docs/05-定时器与PWM.md`、`docs/en/05-timer-pwm.md`、`docs/08-SPI总线.md`、`docs/en/08-spi.md`、`docs/09-ADC与DAC.md`、`docs/en/09-adc-dac.md`。
- 四块标题必须原样出现，各一次：中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`；英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。标题不加表情符号。四块插在 `<!-- /video: -->` 之后、学习目标之前。
- 保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。保留 `## 🧠 核心原理` 与 `## 🧠 Core ideas`。`## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls and troubleshooting` 删掉，不留空标题。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上。生成脚本是 `tools/gen_sample_figures.py`，画布是 `tools/svgkit.py`。不调用 `Svg.footer()`。落款用已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。没有 `<animate`、`@keyframes`、`animation:`。图注写「自绘」，英文图注写 `Drawn for this book`。替代文本写结论。单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 另加一条短 GIF，只做网页和公众号辅图。GIF 不替换主图，也不是关键插图这一节唯一的图。四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`。`minigfx.py` 只有 5×7 英文点阵，GIF 上的字用 ASCII。每条少于 500 KB。帧数不少于 3、不多于 12。`gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 改写吸收的许可顺序：先用 ST 公开 RM/DS 的事实、用自己的话重写；然后才是 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。不把厂商手册、官方插图或社区原文放进仓库。W25Q64 和 ST7789 的厂商手册不吸收。不吸收 libopencm3。
- 订货号是 STM32F103C8T6，LQFP48。读者看到的章号仍是文件名前缀加 1。源文件的一级标题继续带 `02`、`05`、`08`、`09`。这一批不改这个加 1。
- 第 02 章把「RM0008 第 8.3.2 节」改成中密度第 7.3.2 节。`PLLMUL=0111` 是 ×9，`8 × 9 = 72` MHz。PCLK1 = 36 MHz，PCLK2 = 72 MHz。TIM2–TIM7 的计数时钟是 72 MHz。`ADCPRE=10` 得到 12 MHz，`ADCPRE=01` 得到 18 MHz，上限 14 MHz。`USBPRE=0` 得到 48 MHz。LATENCY 在 48–72 MHz、2.7–3.6 V 是 2。CSS 回到 HSI 8 MHz，NMI 里要写 CSSC。MCO 正常路径是 PA8 上的 36 MHz，不得超过 50 MHz。第 02 章四块里不出现 `21 µs`。
- 第 05 章的 1 kHz 整格照抄附录 D：PSC = 71，ARR = 999，计数时钟 72 MHz，`72e6 / (72 × 1000) = 1000` Hz。同一组数用 36 MHz 去除得到 500 Hz。CCR = 500 是 50%。这颗料的 TIM2–TIM5 是 16 位。PSC = 71、ARR = 999999 装不下。能装下的 1 秒是 PSC = 7199、ARR = 9999。`TIMx_BDTR` 偏移 `0x44`，复位值 `0x0000`，位 15 是 MOE。不把 `DeadTime = 0x10` 换算成纳秒，也不把它写进出处卡。不改 `examples/timer-pwm/`。
- 第 08 章的工作点整格照抄附录 D：Mode 0，`BR=010`，SCK = 9 MHz。`BR=001` 是 18 MHz，`BR=000` 是 36 MHz。分频只有 2、4、8、16、32、64、128、256。命令 `0x9F` 之后的三字节是 `0xEF`、`0x40`、`0x17`，`rx[1]` 才是厂商号。页大小 256 字节。片选是推挽 GPIO，不是第 07 章的开漏。不编 SPI 基址。不把 `0x78` 或 4.7 kΩ 写进这一章。
- 第 09 章的采样时钟是 12 MHz。`239.5 + 12.5 = 252`，`252 / 12e6 = 21 µs`。换算分母是 4096。码 2048 在名义 3.3 V 下是 1.65 V。C8 有 ADC1 和 ADC2，没有 ADC3，没有 DAC。温度通道是 ADC1_IN16，推荐采样 17.1 µs。不把 F4 的 `TS_CAL1` / `VREFINT_CAL` 写进来。不重画第 03 章的 LED 图。不把半字、`CNDTR` 和「已写 5 个采样」搬进这一章。
- 第 16 脚 PA6：第 05 章主图只主张 TIM3_CH1，第 08 章主图只主张 SPI1_MISO。两张图都不把两种功能画成同时有效。
- 实施合入时把整书从 1.2.1 升到 **1.2.2**。中英文整书共用这个版本号。日期写死 **2026-10-25**。`accessed` 也写死 `2026-10-25`。不打 tag，不创建 GitHub Release。
- Book CI 变绿之后停下来等人复审。复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。CI 变绿不等于可以自动 squash 合入。
- 实施基线是 #30 合入之后的 `main` 尖端。写本计划时该尖端是 `d08235d54e1f4632b4c2133cb0c334e030c10119`（`docs: classic encyclopedia Batch3 02/05/08/09 design (#30)`）。其章节正文与 v1.2.1 `b2a4f267f58ba42bd9749e94d9f8c2bac7cac118` 相同，只多了设计规格。
- 不加厚除 02、05、08、09 以外的任何章，含 00、01、03、04、06、07 和 10–28。不改这几章的英文。不重选样本。不改 `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json`，不改 `2026-10-25-sample-source-list.json`，不改 `2026-10-25-batch2-04-06-lock.json`，不改 `2026-10-25-batch2-04-06-source-list.json`，不改 `tools/scan_sample_chapters.py`。不改总纲、Batch2 规格、观感规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。不改本批设计规格。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约，不改附录 D 三套账的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。不删 `test_build.py` 里 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不放宽 `test_sample_chapters.py` 或 `test_batch2_chapters.py`。不新增读取 `CONTENT_GUIDE.md` 的测试。
- 不删除、不重画已有图。第 02 章留下 `clock-tree.svg`、`memory-map.svg`、`peripheral-bus.svg`。第 05 章留下 `timer-pwm.svg`、`timer-modes.svg`、`pwm-breath.gif`。第 08 章留下 `spi-transfer.svg`。第 09 章留下 `adc-sar.svg` 和 `sar-adc.gif`。不改 `sar-adc.gif` 的像素。不改已有 8 个 GIF `BUILDERS` 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`。不把 `tools/svg2gif.py` 当成必经步骤。不改 `assets/video/`。
- 新来源 id 只追加，顺序固定为 `rm0008-rcc`、`ds5319-clock`、`rm0008-tim`、`ds5319-tim`、`rm0008-spi`、`ds5319-spi`、`rm0008-adc`、`ds5319-adc`。没有第九个 id。已有 id 的对象一个字段都不改，含 `rm0008`、`ds5319`、`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`project-examples`、`pm0056`。中英两份 manifest 的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。
- 代码继续按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。不新开可烧录工程。不改 `examples/timer-pwm/`、`examples/spi-flash/`、`examples/adc-dma/`。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不预选文件 `01` 或 `07` 作为下一批。
- 系列对比表里的人民币价格留在第 02 章核心原理，标明不是数据手册的数。不进四块，不进新来源的 scope。
- `rm0008-adc` 的 snapshot 只有在 RM0008 Rev 21 第 11 章印出 R_ADC 和 C_ADC 时才加上这两个常数。没印出来，就不写皮法和千欧。源阻抗表留在核心原理，标成估算，不进出处卡。和 21 µs 写在同一格里的时间都按 ADCCLK = 12 MHz。
- SPI 的 BR 编码默认沿用附录 D 和章内表。第 25.5.1 节印出的字段不同时，用印出的编码，9 MHz 仍是 ÷8，18 MHz 仍是 ÷4，并在实施 PR 说明里写明差异。

## File map

| 路径 | 责任 |
| --- | --- |
| `tools/scan_batch3_chapters.py` | 只读 02、05、08、09 的中英八份，确认四块缺失、旧坑标题还在 |
| `docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json` | 核对结果。本计划提交时 `baseline` 是 `d08235d54e1f4632b4c2133cb0c334e030c10119`。实施开始时脚本把它改成当时的 `git rev-parse HEAD` |
| `docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json` | 动笔前的来源清单。八个 absorb id，社区列表为空。登记以 manifest 为准 |
| `tools/gen_sample_figures.py` | 在现有四张静态主图之外追加四张。不改 `boot_state`、`gpio_led`、`exception_stack`、`uart_frame` |
| `assets/diagrams/sample-02-clock-tree.svg` | 第 02 章主图 |
| `assets/diagrams/sample-05-pwm-1khz.svg` | 第 05 章主图 |
| `assets/diagrams/sample-08-spi-jedec.svg` | 第 08 章主图 |
| `assets/diagrams/sample-09-adc-sar.svg` | 第 09 章主图 |
| `tools/gen_gifs.py` | `BUILDERS` 追加 `clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample` |
| `assets/gif/clock-css.gif` | 第 02 章辅图。只画 CSS 回到 HSI |
| `assets/gif/pwm-1khz.gif` | 第 05 章辅图。只画 1000 Hz |
| `assets/gif/spi-jedec.gif` | 第 08 章辅图。只画正常路径的三字节 |
| `assets/gif/adc-sample.gif` | 第 09 章辅图。只画一次成功的采样和 MSB |
| `assets/README.md` | 登记四张 SVG 和四条 GIF |
| 八份章节 Markdown | 四块，以及和附录 D 冲突的那几格 |
| `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` | 八个新 `sources`、四章罗盘、版本号 |
| `stm32-book/revisions.json` | 1.2.2 修订条目，插在数组最前 |
| `stm32-book/README.md` | 当前版本句，以及「也不要把 1.2.1 的产物标成 1.2.2」 |
| `CREDITS.md` | 第六节下面增加 v1.2.2 小节。静态框图张数改为 14。光栅动画个数改为 12 |
| `stm32-book/tests/test_batch3_sources.py` | 来源清单的许可门 |
| `stm32-book/tests/test_batch3_chapters.py` | 四块、共享数字、主图、GIF |
| `stm32-book/tests/test_build.py` | 只改当前版本断言。`0x271` 和书签条数保留 |

---

### Task 1: Gap scan and lock

**Files:**
- Create: `tools/scan_batch3_chapters.py`
- Modify: `docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json`（脚本用运行时 HEAD 重写 `baseline`。章号和布尔值保持不变）

**Interfaces:**
- Consumes: 八份原稿。不读别的章，不调用 `tools/scan_sample_chapters.py`，不调用 `tools/scan_batch2_chapters.py`。
- Produces: 锁定文件字段 `rubric`（字符串 `"2026-10-25-classic-encyclopedia-batch3-02-05-08-09"`）、`baseline`（40 位十六进制，等于运行时 `git rev-parse HEAD`）、`chapters`（`["02", "05", "08", "09"]`）、`four_blocks_absent`（`true`）、`old_pitfall_heading_present`（`true`）、`files`。`files` 的键是 `"02"`、`"05"`、`"08"`、`"09"`。每个值有 `zh`、`en`、`zh_four_blocks`、`en_four_blocks`、`zh_old_pitfall`、`en_old_pitfall`。后面的任务只改这四个前缀。

四块标题是中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`，英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。旧坑标题是中文 `## ⚠️ 常见坑与排查`，英文 `## ⚠️ Pitfalls and troubleshooting`。

在 `d08235d54e1f4632b4c2133cb0c334e030c10119` 上，这八份都还没有四块，旧坑标题都还在。本计划提交里的锁定文件已经记下这个结果。若执行时任何一份已经有四块，脚本退出码 2，不改写锁定文件，后面的任务停。不要在已有四块上再叠一套标题。

- [ ] **Step 1: 写入核对脚本**

把下面的程序保存为 `tools/scan_batch3_chapters.py`。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 02, 05, 08, and 09 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch3_chapters.py

Rewrites docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json and
exits 0 when all eight manuscripts lack the four headings and still have the
old pitfall heading. Exits 2 without writing the lock if a four-block heading
is already present, or if the old pitfall heading is already gone.
Does not score other chapters and does not touch the sample lock or the
batch-2 lock.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch3-02-05-08-09-lock.json"
FILES = {
    "02": (
        ROOT / "docs" / "02-芯片选型与存储器时钟.md",
        ROOT / "docs" / "en" / "02-part-and-clock.md",
    ),
    "05": (
        ROOT / "docs" / "05-定时器与PWM.md",
        ROOT / "docs" / "en" / "05-timer-pwm.md",
    ),
    "08": (
        ROOT / "docs" / "08-SPI总线.md",
        ROOT / "docs" / "en" / "08-spi.md",
    ),
    "09": (
        ROOT / "docs" / "09-ADC与DAC.md",
        ROOT / "docs" / "en" / "09-adc-dac.md",
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
        "rubric": "2026-10-25-classic-encyclopedia-batch3-02-05-08-09",
        "baseline": baseline,
        "chapters": ["02", "05", "08", "09"],
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

Run: `python3 tools/scan_batch3_chapters.py`

Expected: 退出码 0，标准输出含

```text
02 four_blocks=no old_pitfall=yes
05 four_blocks=no old_pitfall=yes
08 four_blocks=no old_pitfall=yes
09 four_blocks=no old_pitfall=yes
baseline=
```

`baseline=` 后面是当时 `git rev-parse HEAD` 的 40 位哈希。锁定文件里 `chapters` 仍为 `["02", "05", "08", "09"]`，`four_blocks_absent` 仍为 `true`，`old_pitfall_heading_present` 仍为 `true`。`baseline` 被改成这次运行的 HEAD。这个 HEAD 必须还没有新的 `sources`，也还没有四块。

若退出码为 2：停止。不要改四块标题去凑退出码 0，也不要改 `tools/scan_sample_chapters.py`。

- [ ] **Step 3: 确认样本锁定、Batch2 锁定和设计规格没被改写**

Run:

```bash
git diff --name-only -- docs/superpowers/plans/2026-10-25-sample-chapter-lock.json docs/superpowers/plans/2026-10-25-sample-source-list.json docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch2-04-06-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch3-02-05-08-09-design.md tools/scan_sample_chapters.py
```

Expected: 无输出。

- [ ] **Step 4: Commit**

```bash
git add tools/scan_batch3_chapters.py docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json
git commit -m "docs: 锁定第 02、05、08、09 章尚未加厚"
```

这一笔提交里不要带 manifest 或章节正文。锁定文件里的 `baseline` 必须仍指向还没有新 `sources` 的那次提交。

### Task 2: Source list with the license gate

**Files:**
- Modify: `docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json`（只在第 11 章印出了 R_ADC 与 C_ADC，或第 25.5.1 节的 BR 编码和附录 D 不同时才改 snapshot。默认不改）
- Create: `stm32-book/tests/test_batch3_sources.py`
- Test: `stm32-book/tests/test_batch3_sources.py`

**Interfaces:**
- Consumes: Task 1 的 `chapters == ["02", "05", "08", "09"]`，以及 `four_blocks_absent == true`。已提交的来源清单。
- Produces: 八个新 id，顺序固定为 `rm0008-rcc`、`ds5319-clock`、`rm0008-tim`、`ds5319-tim`、`rm0008-spi`、`ds5319-spi`、`rm0008-adc`、`ds5319-adc`。不产生第九个 id。`community` 是空数组。`reuse_existing` 只有 `project-examples`。这个 id 不新建 manifest 对象。

来源清单已经随本计划提交。实施时不要另写一份。许可门测试去读这份文件。

2026-10-25 设计规格冻结的事实，实施时打开同一批 URL。首页修订或节号变了就停，先改清单里的 `snapshot` 和 `section`，再画图、再写正文。数字本身不变：

- RM0008 Rev 21（February 2021）：中密度 `RCC_CFGR` 在第 7.3.2 节。第 8.3.2 节是互联型。CSS 在第 7.2.7 节。通用定时器时基在第 15 章。`SPI_CR1` 在第 25.5.1 节。ADC 的校准在第 11.4 节。PDF 与已有 `rm0008-boot` 相同，不另找一份修订。
- DS5319 Rev 20（July 2025）图 8 与表 5，和 `ds5319-gpio` 是同一份 PDF。LQFP48 第 5 脚 PD0、第 6 脚 PD1、第 9 脚 VDDA、第 10 脚 PA0、第 14 脚 PA4、第 15 脚 PA5、第 16 脚 PA6、第 17 脚 PA7、第 29 脚 PA8。
- `project-examples` 已在 manifest 里。对象一个字段都不改。

打开这些 URL：

- `https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf`
- `https://www.st.com/resource/en/datasheet/stm32f103c8.pdf`

两份都打不开就停。不要换一份别的手册来补皮法或基址。

社区例程这一批不冻结。来源清单的 `community` 是空数组。不吸收未写许可的博客，不吸收 GPL 的 libopencm3，不吸收 Winbond 或显示屏厂商手册。

- [ ] **Step 1: 写许可门测试**

保存为 `stm32-book/tests/test_batch3_sources.py`：

```python
#!/usr/bin/env python3
"""License gate for chapters 02, 05, 08, and 09. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch3-02-05-08-09-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch3-02-05-08-09-lock.json"
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
    "rm0008-rcc",
    "ds5319-clock",
    "rm0008-tim",
    "ds5319-tim",
    "rm0008-spi",
    "ds5319-spi",
    "rm0008-adc",
    "ds5319-adc",
]


class Batch3SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_02_05_08_09(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["02", "05", "08", "09"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch3-02-05-08-09", lock["rubric"])
        for prefix, zh_name, en_name in (
            ("02", "docs/02-芯片选型与存储器时钟.md", "docs/en/02-part-and-clock.md"),
            ("05", "docs/05-定时器与PWM.md", "docs/en/05-timer-pwm.md"),
            ("08", "docs/08-SPI总线.md", "docs/en/08-spi.md"),
            ("09", "docs/09-ADC与DAC.md", "docs/en/09-adc-dac.md"),
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
        self.assertEqual(["02", "05", "08", "09"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(ABSORB, ids)
        self.assertEqual(8, len(ids))
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
        self.assertEqual("7.3.2", by_id["rm0008-rcc"]["section"])
        self.assertEqual("Figure 8", by_id["ds5319-clock"]["section"])
        self.assertEqual("15", by_id["rm0008-tim"]["section"])
        self.assertEqual("Table 5", by_id["ds5319-tim"]["section"])
        self.assertEqual("25.5.1", by_id["rm0008-spi"]["section"])
        self.assertEqual("Table 5", by_id["ds5319-spi"]["section"])
        self.assertEqual("11.4", by_id["rm0008-adc"]["section"])
        self.assertEqual("Figure 8", by_id["ds5319-adc"]["section"])
        adc_snap = by_id["rm0008-adc"]["snapshot"]
        self.assertNotIn("pF", adc_snap)
        self.assertNotIn("kΩ", adc_snap)
        self.assertNotIn("kilohm", adc_snap.lower())
        spi_snap = by_id["rm0008-spi"]["snapshot"]
        self.assertIn("9 MHz", spi_snap)
        self.assertIn("18 MHz", spi_snap)
        self.assertIn("36 MHz", spi_snap)
        self.assertNotIn("0x40013", spi_snap)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(["project-examples"], reused)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试**

Run: `python3 stm32-book/tests/test_batch3_sources.py -v`

Expected: OK，两条测试都通过。清单已经在本计划提交里，所以这一步不是 `FileNotFoundError`。若失败，改清单去满足上面的断言，不要放宽 `ABSORB`，也不要删掉测试来制造一次红色。不要追加第九个 id。

锁定文件那一条若失败，先回到 Task 1。不要改测试去迁就一份章号不对的锁。

- [ ] **Step 3: 打开两份 PDF，只核对会改 snapshot 的两处**

打开 Task 2 开头的两个 URL。

BR：读 RM0008 Rev 21 第 25.5.1 节印出的 `BR[2:0]`。附录 D 和章内表现在是 `000` = ÷2 = 36 MHz，`001` = ÷4 = 18 MHz，`010` = ÷8 = 9 MHz。印出的编码相同，清单不动。印出的编码不同，把 `rm0008-spi` 的 `snapshot` 改成印出的编码，9 MHz 仍写 ÷8，18 MHz 仍写 ÷4，并在实施 PR 说明里写明差异。不编 SPI 基址。

采样电容：在 RM0008 Rev 21 第 11 章里找 R_ADC 和 C_ADC。两个常数都印出来，才把印出的数写进 `rm0008-adc` 的 `snapshot`，并在 Task 8 用印出的公式重算源阻抗表。两个里缺一个，snapshot 保持现在这句 `This snapshot does not include R_ADC or C_ADC.`，不写皮法，不写千欧。正文里已有的 1 kΩ、8 pF 继续标成估算，不升格。

无论哪一处，都不要改 `license_class`，不要改 URL，不要改另外六个 id 的 `points`。

- [ ] **Step 4: 再跑测试并提交**

Run: `python3 stm32-book/tests/test_batch3_sources.py -v`

Expected: OK。

```bash
git add stm32-book/tests/test_batch3_sources.py docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json
git commit -m "docs: 钉上 02、05、08、09 的许可门"
```

若清单相对本计划提交没有差异，`git add` 里带上它也没有关系，提交内容里可以只有测试文件。不要在这一笔里改章节正文。

### Task 3: Static key figures

**Files:**
- Modify: `tools/gen_sample_figures.py`（只追加函数，并在 `main()` 里多保存四张。不改 `boot_state`、`gpio_led`、`exception_stack`、`uart_frame`、`_credit`）
- Create: `assets/diagrams/sample-02-clock-tree.svg`
- Create: `assets/diagrams/sample-05-pwm-1khz.svg`
- Create: `assets/diagrams/sample-08-spi-jedec.svg`
- Create: `assets/diagrams/sample-09-adc-sar.svg`
- Modify: `assets/README.md`（开头的生成命令，以及第四节表的末尾）
- Create: `stm32-book/tests/test_batch3_chapters.py`
- Test: `stm32-book/tests/test_batch3_chapters.py`

**Interfaces:**
- Consumes: Task 2 清单里的订货号、脚位和寄存器名。已有的 `_credit(canvas, note)`。
- Produces: `clock_tree() -> Svg`、`pwm_1khz() -> Svg`、`spi_jedec() -> Svg`、`adc_sample() -> Svg`。四张 SVG 不含 `<animate`、`@keyframes`、`animation:`，不含「矢量动画」，不含「实拍」，含「自绘」。每张都小于 60 KB。

`sample-02-clock-tree.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`pin 5 PD0`、`pin 6 PD1`、`pin 29 PA8`、`PLLMUL=0111`、`PLLSRC=1`、`PLLXTPRE=0`、`72 MHz`、`36 MHz`、`12 MHz`、`18 MHz`、`14 MHz`、`48 MHz`、`50 MHz`、`USBPRE=0`、`LATENCY=2`、`LATENCY=0`、`CSSC`、`HSI 8 MHz`、`7.3.2`。

`sample-05-pwm-1khz.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`pin 16`、`PA6`、`TIM3_CH1`、`PSC=71`、`ARR=999`、`CCR=500`、`1000 Hz`、`500 Hz`、`500 us`、`72 MHz`、`36 MHz`、`999999`、`16-bit`、`MOE`、`0x44`、`SPI1_MISO is not on this trace`。

`sample-08-spi-jedec.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`pin 14 PA4`、`pin 15 PA5`、`pin 16 PA6`、`pin 17 PA7`、`CPOL=0`、`CPHA=0`、`BR=010`、`9 MHz`、`0x9F`、`0xEF`、`0x40`、`0x17`、`36 MHz`、`MOSI`、`MISO`、`swapped`。不含 `0x40013000`。

`sample-09-adc-sar.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`pin 9 VDDA`、`pin 10 PA0`、`ADC12_IN0`、`12 MHz`、`21 us`、`239.5`、`12.5`、`4096`、`18 MHz`、`14 MHz`、`previous voltage`。不含 `270`。

- [ ] **Step 1: 写会失败的主图测试**

保存为 `stm32-book/tests/test_batch3_chapters.py`：

```python
#!/usr/bin/env python3
"""Checks for thickened chapters 02, 05, 08, and 09 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为文件不存在而失败**

Run: `python3 stm32-book/tests/test_batch3_chapters.py -v`

Expected: FAIL，`sample-02-clock-tree.svg` 不存在（`FileNotFoundError`）。

- [ ] **Step 3: 追加四个生成函数并写出 SVG**

在 `tools/gen_sample_figures.py` 的 `uart_frame()` 之后、`main()` 之前插入下面四个函数。不要改 `boot_state`、`gpio_led`、`exception_stack`、`uart_frame`、`_credit`。

```python
def clock_tree() -> Svg:
    canvas = Svg(
        960,
        860,
        "72 MHz 要 2 个 Flash 等待；HSE 停振后系统时钟回到 HSI 8 MHz",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 7.3.2 节",
    )
    canvas.header(tag="02", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  中密度", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 5 PD0  pin 6 PD1  HSE 8 MHz", size=14, fill=T.CYAN)
    canvas.text(40, 138, "PLLXTPRE=0  PLLSRC=1  PLLMUL=0111  8 x 9 = 72 MHz", size=14, fill=T.TEXT)
    canvas.text(40, 164, "SYSCLK = HCLK = 72 MHz    PCLK1 = 36 MHz    PCLK2 = 72 MHz", size=14, fill=T.AMBER)
    canvas.text(40, 190, "TIM2-TIM7 = 72 MHz    ADCCLK = 12 MHz    USBPRE=0  USBCLK = 48 MHz", size=14, fill=T.TEXT)
    canvas.text(40, 216, "正常路径  LATENCY=2    CSS 未触发    pin 29 PA8  MCO = PLL/2 = 36 MHz", size=15, fill=T.GREEN, weight="700")
    canvas.rect(40, 230, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 258, "48 MHz 到 72 MHz 这一档 LATENCY=2", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 284, "0 到 24 MHz 是 0，24 到 48 MHz 是 1。电压档 2.7-3.6 V", size=14, fill=T.GREEN)
    canvas.text(56, 310, "MCO=111 送出 36 MHz，低于 50 MHz", size=14, fill=T.TEXT)
    canvas.text(56, 336, "RM0008 Rev 21 第 7.3.2 节。第 8.3.2 节在这颗料上作废", size=13, fill=T.MUTED)
    canvas.text(56, 360, "旁注：ADCPRE=01 得到 18 MHz，越过 14 MHz。MCO 直接送 72 MHz 也越过 50 MHz", size=13, fill=T.AMBER)
    canvas.text(40, 406, "失败路径  同一棵 x9 的树，LATENCY=0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 420, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 450, "只把 PLL 改成 x9，LATENCY=0，取指失败", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 476, "HSE 停振：SYSCLK 回到 HSI 8 MHz，PLL 关掉", size=14, fill=T.RED)
    canvas.text(56, 502, "NMI 一直进来，直到软件写 CSSC", size=14, fill=T.AMBER)
    canvas.text(56, 528, "不把 18 MHz 和 72 MHz 的 MCO 再画成第三条完整的树", size=13, fill=T.MUTED)
    canvas.rect(40, 570, 880, 90, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 600, "旁注  互联型第 8.3.2 节在 STM32F103C8T6 上作废", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 626, "OTGFSPRE、PLLMUL 的 000x 保留、以及 x6.5，不写进这颗 C8", size=14, fill=T.TEXT)
    canvas.text(56, 650, "0111 仍是 x9，0000 仍是 x2。无源晶振不开 bypass", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。树来自 RM0008 Rev 21 第 7.3.2 节与第 7.2.7 节；脚位来自 DS5319 Rev 20 图 8。")
    return canvas


def pwm_1khz() -> Svg:
    canvas = Svg(
        960,
        820,
        "72 MHz 计数时钟下这组 PSC/ARR 是 1 kHz；改用 36 MHz 去除得到 500 Hz",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 15 章",
    )
    canvas.header(tag="05", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  pin 16 PA6 = TIM3_CH1", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "计数时钟 72 MHz    PSC=71    ARR=999    CCR=500", size=14, fill=T.CYAN)
    canvas.text(40, 138, "72e6 / ((71+1) x (999+1)) = 1000 Hz    高电平 500 us", size=14, fill=T.AMBER)
    canvas.text(40, 164, "SPI1_MISO is not on this trace", size=14, fill=T.MUTED)
    canvas.text(40, 196, "正常路径  CNT 0 到 499 为高，500 到 999 为低", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 210, 880, 140, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 240, "周期 1000 us，频率 1000 Hz，占空比 50%", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 266, "PWM 模式 1：CNT < CCR 时输出为高", size=14, fill=T.GREEN)
    canvas.text(56, 292, "计数时钟先被分成 1 MHz，再数 1000 下", size=14, fill=T.TEXT)
    canvas.text(56, 318, "TIM3_REMAP=00。PB4 和 PC6 不在这条路径上", size=13, fill=T.MUTED)
    canvas.text(40, 376, "失败路径  同一组 PSC/ARR/CCR，去除时用了 36 MHz", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 390, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 420, "周期变成 2000 us，频率 500 Hz", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 446, "多出来的那一倍来自把 PCLK1 当成了定时器时钟", size=14, fill=T.RED)
    canvas.text(56, 472, "TIM3 在 APB1。预分频不是 1，计数时钟仍是 72 MHz", size=14, fill=T.AMBER)
    canvas.text(56, 498, "不要用 36 MHz 去除这组 PSC=71、ARR=999", size=13, fill=T.MUTED)
    canvas.rect(40, 540, 880, 110, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 570, "旁注  16-bit 装不下 ARR=999999", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 596, "能装下的 1 秒是 PSC=7199、ARR=9999", size=14, fill=T.TEXT)
    canvas.text(56, 622, "TIM1 的 MOE 在 TIMx_BDTR 偏移 0x44，复位值 0x0000，位 15 为 0。那是另一只定时器，不占 PA6", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。时基来自 RM0008 Rev 21 第 15 章；脚位来自 DS5319 Rev 20 表 5。")
    return canvas


def spi_jedec() -> Svg:
    canvas = Svg(
        960,
        860,
        "Mode 0、除以 8 得到 9 MHz；0x9F 之后的三字节是 0xEF、0x40、0x17",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 25.5.1 节",
    )
    canvas.header(tag="08", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  SPI1  APB2  72 MHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 14 PA4 = CS    pin 15 PA5 = SCK    pin 16 PA6 = MISO    pin 17 PA7 = MOSI", size=14, fill=T.CYAN)
    canvas.text(40, 138, "CPOL=0  CPHA=0  空闲 SCK 为低，上升沿采样    BR=010  SCK = 9 MHz", size=14, fill=T.AMBER)
    canvas.text(40, 164, "正常路径  MOSI 先送 0x9F，随后三个 0xFF", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 178, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 208, "rx[0] 是命令期间移入的字节，不是厂商号", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 234, "rx[1]=0xEF  rx[2]=0x40  rx[3]=0x17", size=14, fill=T.GREEN)
    canvas.text(56, 260, "拼起来是 0xEF4017。0x40 是存储器类型，不是容量", size=14, fill=T.TEXT)
    canvas.text(56, 286, "事务结束时 PA4 回到高。片选是推挽 GPIO", size=14, fill=T.AMBER)
    canvas.text(56, 312, "页大小 256 字节。不把第 14 脚画成 DAC", size=13, fill=T.MUTED)
    canvas.text(40, 364, "失败路径  PA6 与 PA7 swapped", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 378, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 408, "MISO 上读不到 0xEF 0x40 0x17", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 434, "MOSI 和 MISO 对调之后，三字节对不上", size=14, fill=T.RED)
    canvas.text(56, 460, "CPHA 配成第二沿时字节会错位。那一行不占这张失败路径", size=14, fill=T.AMBER)
    canvas.text(56, 486, "PB3/PB4/PB5 不在正常路径上", size=13, fill=T.MUTED)
    canvas.rect(40, 528, 880, 110, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 558, "旁注  PA4 一直为低时两条事务粘成一条", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 584, "BR=000 时 SCK = 36 MHz，相对这条 9 MHz 的工作点过快", size=14, fill=T.TEXT)
    canvas.text(56, 610, "不编 SPI 基址。TIM3_CH1 不画进这条 MISO 波形", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。BR 来自 RM0008 Rev 21 第 25.5.1 节；脚位来自 DS5319 Rev 20 表 5。")
    return canvas


def adc_sample() -> Svg:
    canvas = Svg(
        960,
        860,
        "这颗料的 ADC 时钟是 12 MHz，最长转换 21 us；采样太短时电容上仍是上一次的电压",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 11 章",
    )
    canvas.header(tag="09", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  pin 10 PA0 = ADC12_IN0", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 9 VDDA 是参考    ADCCLK = 12 MHz    分母 4096", size=14, fill=T.CYAN)
    canvas.text(40, 138, "正常路径  采样开关闭合，然后断开保持，比较器做 MSB", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 152, 880, 170, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 182, "R_AIN 给采样电容充电。开关断开后电压被保持", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 208, "MSB 那一次与 Vref/2 比较", size=14, fill=T.GREEN)
    canvas.text(56, 234, "最长一档 239.5 + 12.5 = 252 周期 = 21 us", size=14, fill=T.AMBER)
    canvas.text(56, 260, "码值 x VDDA / 4096。码 2048 在名义 3.3 V 下是 1.65 V", size=14, fill=T.TEXT)
    canvas.text(56, 286, "1.5 周期 = 125 ns。不把 LED 电阻画进这张图", size=13, fill=T.MUTED)
    canvas.text(40, 348, "失败路径  采样太短，电容上仍是 previous voltage", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 362, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 392, "这一次的码不是现在的输入", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 418, "高阻时用 239.5 周期", size=14, fill=T.RED)
    canvas.text(56, 444, "71.5 周期是 5.958 us，盖不住温度通道的 17.1 us", size=14, fill=T.AMBER)
    canvas.rect(40, 502, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 532, "旁注  除以 4 得到 18 MHz，越过 14 MHz", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 558, "1 us 那个例子是 14 MHz 上的，不是这颗料的工作点", size=14, fill=T.TEXT)
    canvas.text(56, 584, "第 14 脚画成 DAC 时，C8 上没有这只脚的 DAC。C8 有 ADC1 和 ADC2", size=13, fill=T.MUTED)
    canvas.text(56, 608, "不把第 03 章的 LED 电阻画进来", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。Tconv 与 17.1 us 来自 RM0008 Rev 21 第 11 章；脚位来自 DS5319 Rev 20 图 8。")
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
```

Run: `python3 tools/gen_sample_figures.py`

Expected: 退出码 0。四张新 SVG 出现在 `assets/diagrams/`。测试只要求小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。若 `sample-00-boot-state.svg`、`sample-03-gpio-led.svg`、`sample-04-exception-stack.svg` 或 `sample-06-uart-frame.svg` 出现内容 diff，说明旧函数被改过，先还原那四个函数再生成。不要把这四张旧图的改动提交进来。

在 `assets/README.md` 开头的生成命令里，把

```bash
python3 tools/gen_sample_figures.py   # 第 00、03、04、06 章的静态主图
```

换成

```bash
python3 tools/gen_sample_figures.py   # 第 00、02、03、04、05、06、08、09 章的静态主图
```

第四节表格末尾追加这四行，不要另起一列：

```markdown
| `sample-02-clock-tree.svg` | 第 02 章静态主图：中密度 72 MHz 树、LATENCY=2，以及 LATENCY=0 的取指失败和 CSS 回到 HSI。由 `tools/gen_sample_figures.py` 生成 |
| `sample-05-pwm-1khz.svg` | 第 05 章静态主图：PA6 上 TIM3_CH1 的 1 kHz，以及用 36 MHz 去除得到的 500 Hz。由 `tools/gen_sample_figures.py` 生成 |
| `sample-08-spi-jedec.svg` | 第 08 章静态主图：LQFP48 第 14–17 脚、Mode 0、9 MHz，以及 MOSI/MISO 对调后读不到 0xEF 0x40 0x17。由 `tools/gen_sample_figures.py` 生成 |
| `sample-09-adc-sar.svg` | 第 09 章静态主图：12 MHz 下一次采样和 MSB 比较，最长转换 21 µs，采样太短时电容上仍是上一次的电压。由 `tools/gen_sample_figures.py` 生成 |
```

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch3_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_sample_figures.py assets/diagrams/sample-02-clock-tree.svg assets/diagrams/sample-05-pwm-1khz.svg assets/diagrams/sample-08-spi-jedec.svg assets/diagrams/sample-09-adc-sar.svg assets/README.md stm32-book/tests/test_batch3_chapters.py
git commit -m "assets: 为 02、05、08、09 加上可印刷的静态主图"
```

提交前再看一眼：

```bash
git diff --stat -- assets/diagrams/sample-00-boot-state.svg assets/diagrams/sample-03-gpio-led.svg assets/diagrams/sample-04-exception-stack.svg assets/diagrams/sample-06-uart-frame.svg
```

Expected: 无输出。

### Task 4: Short auxiliary GIFs

**Files:**
- Modify: `tools/gen_gifs.py`（在 `BUILDERS` 之前追加四个函数，并给字典加四个键。不改已有八个函数）
- Create: `assets/gif/clock-css.gif`
- Create: `assets/gif/pwm-1khz.gif`
- Create: `assets/gif/spi-jedec.gif`
- Create: `assets/gif/adc-sample.gif`
- Modify: `assets/README.md`（第五节的表，以及「上面 8 张」那两句）
- Modify: `stm32-book/tests/test_batch3_chapters.py`
- Test: `stm32-book/tests/test_batch3_chapters.py`

**Interfaces:**
- Consumes: `tools/minigfx.py` 的 `Canvas`、`Gif`、`C`，以及 `chrome()`。
- Produces: `clock_css()`、`pwm_1khz()`、`spi_jedec()`、`adc_sample()`，各返回一帧数在 3 到 12 之间的 `Gif`。`BUILDERS` 的键在原有 8 个之后增加 `"clock-css"`、`"pwm-1khz"`、`"spi-jedec"`、`"adc-sample"`。`clock_css` 的源码含 `HSE 8 MHz`、`72 MHz`、`HSI 8 MHz`，不含 `LATENCY`。`pwm_1khz` 的源码含 `1000 Hz`、`500 us`、`CCR=500`，不含 `500 Hz`。`spi_jedec` 的源码含 `0x9F`、`0xEF`、`9 MHz`，不含 `36 MHz`。`adc_sample` 的源码含 `12 MHz`、`MSB`，不含 `18 MHz`。四条 GIF 文件都小于 500 KB。

- [ ] **Step 1: 把 GIF 断言加进测试**

在 `stm32-book/tests/test_batch3_chapters.py` 的文件头增加 `import importlib.util`，并在 `Batch3FigureTests` 之后追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3GifTests -v`

Expected: FAIL，`BUILDERS` 里没有 `clock-css`。

- [ ] **Step 3: 追加四个 BUILDERS 并生成 GIF**

在 `tools/gen_gifs.py` 里，`BUILDERS = {` 之前插入。四个函数按 `clock_css`、`pwm_1khz`、`spi_jedec`、`adc_sample` 的顺序紧挨着，中间不要插入别的 `def`。

```python
def clock_css():
    """HSE enters the PLL, SYSCLK sits at 72 MHz, then HSE vanishes and SYSCLK returns to HSI.

    The fetch failure stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    lines = (
        "HSE 8 MHz INTO PLL",
        "PLL x9 LOCKS",
        "SYSCLK 72 MHz",
        "HSE GONE",
        "PLL OFF",
        "SYSCLK IS HSI 8 MHz",
    )
    for index, line in enumerate(lines):
        c = Canvas(W, H)
        chrome(c, "CLOCK CSS", "HSE", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 48, 448, 36, C.PANEL, C.STROKE)
        c.text("HSE 8 MHz", 28, 60, C.CYAN, 1)
        c.panel(16, 96, 448, 36, C.PANEL, C.GREEN if index >= 2 else C.STROKE)
        c.text("72 MHz" if index < 4 else "HSI 8 MHz", 28, 108, C.AMBER, 1)
        c.text(line, 28, 160, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 184, C.MUTED, 1)
        c.text("CSS RETURNS SYSCLK TO HSI", 28, 214, C.GREEN, 1)
        c.text("PRINT THE FETCH FAILURE ON THE SVG", 28, 232, C.DIM, 1)
        g.add(c)
    return g


def pwm_1khz():
    """CNT walks to ARR and the level flips at CCR=500.

    The slow path stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "CNT 0  HIGH",
        "CNT 250  HIGH",
        "CCR=500  EDGE",
        "CNT 750  LOW",
        "CNT 999  LOW",
        "1000 Hz  500 us HIGH",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "PWM 1 KHZ", "TIM3", "AUX GIF  1000 Hz")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("PSC=71 ARR=999 CCR=500", 28, 58, C.MUTED, 1)
        level = C.GREEN if index < 2 else C.AMBER
        c.hline(24, 120, 200 if index < 2 else 432, level, 2)
        c.text(note, 28, 160, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 184, C.MUTED, 1)
        c.text("1000 Hz FROM A 72 MHz CLOCK", 28, 214, C.CYAN, 1)
        c.text("500 us HIGH THEN LOW", 28, 232, C.GREEN, 1)
        c.text("PRINT THE SLOW PATH ON THE STATIC SVG", 28, 254, C.DIM, 1)
        g.add(c)
    return g


def spi_jedec():
    """CS falls, MOSI shifts 0x9F, then MISO returns 0xEF 0x40 0x17 at 9 MHz.

    The swapped-wire failure stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "CS LOW",
        "MOSI 0x9F",
        "MISO 0xEF",
        "MISO 0x40",
        "MISO 0x17",
        "CS HIGH  9 MHz",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "SPI JEDEC", "MODE 0", "AUX GIF  9 MHz")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("PA5 SCK  PA7 MOSI  PA6 MISO", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("0x9F THEN 0xEF 0x40 0x17", 28, 200, C.GREEN, 1)
        c.text("9 MHz  BR=010", 28, 222, C.CYAN, 1)
        c.text("PRINT THE SWAP ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def adc_sample():
    """One successful sample, then the MSB compare, at 12 MHz.

    The short-sample failure stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "SWITCH CLOSED",
        "CAP CHARGES",
        "SWITCH OPENS",
        "HOLD",
        "MSB COMPARE",
        "ADCCLK 12 MHz",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "ADC SAMPLE", "12 MHZ", "AUX GIF  ONE CONVERSION")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("PA0  ADC12_IN0  VDDA", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("12 MHz SAMPLE THEN MSB", 28, 200, C.GREEN, 1)
        c.text("PRINT THE SHORT SAMPLE ON THE SVG", 28, 222, C.DIM, 1)
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
}
```

Run: `python3 tools/gen_gifs.py clock-css pwm-1khz spi-jedec adc-sample`

Expected: 退出码 0，四行 `[ok]`，帧数都是 6。不要为了这一步重跑另外 8 个名字。

在 `assets/README.md` 第五节表格末尾追加：

```markdown
| `clock-css.gif` | HSE 8 MHz 进 PLL，系统时钟停在 72 MHz，然后 HSE 消失，系统时钟回到 HSI 8 MHz | 由 `tools/gen_gifs.py` 生成。辅图。LATENCY=0 的取指失败只在静态主图上 |
| `pwm-1khz.gif` | CNT 从 0 走到 ARR，CCR=500 处电平翻转，标出 1000 Hz 和 500 µs | 由 `tools/gen_gifs.py` 生成。辅图。500 Hz 的失败只在静态主图上 |
| `spi-jedec.gif` | CS 拉低，MOSI 移出 0x9F，MISO 随后移入 0xEF、0x40、0x17，标出 9 MHz | 由 `tools/gen_gifs.py` 生成。辅图。对调线和 36 MHz 只在静态主图上 |
| `adc-sample.gif` | 一次成功的采样，接着 MSB 那一次比较，标出 ADCCLK = 12 MHz | 由 `tools/gen_gifs.py` 生成。辅图。采样过短和 18 MHz 只在静态主图上 |
```

把「上面 8 张 GIF」换成「上面 12 张 GIF」。把「不是上面 8 张的中文翻译」换成「不是上面 12 张的中文翻译」。

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch3_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_gifs.py assets/gif/clock-css.gif assets/gif/pwm-1khz.gif assets/gif/spi-jedec.gif assets/gif/adc-sample.gif assets/README.md stm32-book/tests/test_batch3_chapters.py
git commit -m "assets: 为 02、05、08、09 加上短 GIF 辅图"
```

`git diff --name-only -- assets/gif/led-blink.gif assets/gif/pwm-breath.gif assets/gif/uart-bits.gif assets/gif/i2c-timing.gif assets/gif/dma-ring.gif assets/gif/sar-adc.gif assets/gif/nvic-preempt.gif assets/gif/uart-idle.gif` 应无输出。

### Task 5: Thicken chapter 02 in both languages

**Files:**
- Modify: `docs/02-芯片选型与存储器时钟.md`
- Modify: `docs/en/02-part-and-clock.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `rm0008-rcc`、`ds5319-clock`；`02-芯片选型与存储器时钟.md` 的 `sources` 改为 `["rm0008", "ds5319", "rm0008-rcc", "ds5319-clock"]`）
- Modify: `stm32-book/manifest-en.json`（同一组 id 与同一组 `url` / `snapshot` / `license` / `accessed`；英文 `title`、`authority`、`scope`；`02-part-and-clock.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch3_chapters.py`
- Test: `stm32-book/tests/test_batch3_chapters.py`

**Interfaces:**
- Consumes: `rm0008-rcc`、`ds5319-clock`，以及 `assets/diagrams/sample-02-clock-tree.svg`、`assets/gif/clock-css.gif`。
- Produces: `baseline_manifests() -> tuple[dict, dict]`、`_fetch_baseline(rev: str) -> None`、`_git_show(rev: str, path: str) -> str | None`。中文章在 `## 📌 学习目标` 之前出现四个新的二级标题；英文在 `## 📌 Learning goals` 之前出现四个英文标题。旧的 `## ⚠️ 常见坑与排查` 与 `## ⚠️ Pitfalls and troubleshooting` 从这两份里删除。正文不再出现 `RM0008 第 8.3.2 节` 或 `RM0008 section 8.3.2`。四块里不出现 `21 µs`。修订号 Rev 21 留在出处链接里。

`accessed` 写死 `2026-10-25`。中英 manifest 写同一天。

- [ ] **Step 1: 把章节断言和基线读取加进测试**

把 `stm32-book/tests/test_batch3_chapters.py` 的 import 区换成：

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
```

在文件末尾、`if __name__` 之前追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3ClockChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`（`AssertionError`，`1 != 0`）。

- [ ] **Step 3: 改节号，标上价格不是手册数字，并删掉旧坑表**

中文 `docs/02-芯片选型与存储器时钟.md` 把这一行：

```markdown
**RCC_CFGR 关键位（RM0008 第 8.3.2 节）：**
```

换成：

```markdown
**RCC_CFGR 关键位（RM0008 Rev 21 中密度第 7.3.2 节。第 8.3.2 节是互联型，在 STM32F103C8T6 上作废）：**
```

在系列对比表和 `### 3. 内核特性对比（Cortex-M）` 之间插入：

```markdown
> 价格是选型口吻，不是 DS5319 或 RM0008 里的数。不进四块，也不进新来源的 scope。
```

在 `### 10. 先开时钟，再谈 CSS 和 MCO` 那一节的口诀之前插入：

```markdown
换系列时外设基址不同，用 CMSIS 头文件里的宏，不把地址写死。这句没有新的寄存器值，不进出处卡。
```

英文 `docs/en/02-part-and-clock.md` 把这一行：

```markdown
**Important RCC_CFGR bits (RM0008 section 8.3.2):**
```

换成：

```markdown
**Important RCC_CFGR bits (RM0008 Rev 21 medium-density section 7.3.2. Section 8.3.2 is the connectivity line and is void on STM32F103C8T6):**
```

在系列对比表和 `### 3. Core features (Cortex-M)` 之间插入：

```markdown
> The prices are a selection sketch. They are not numbers from DS5319 or RM0008. They stay out of the four blocks and out of the new sources' scope.
```

在 `### 10. Turn the clock on before you talk about CSS and MCO` 那一节的 motto 之前插入：

```markdown
When the family changes, peripheral base addresses change. Use the CMSIS macros and do not hard-code them. This sentence adds no new register value and does not enter a source card.
```

中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段（含表）。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。动手实验保留。「回退 HSI 再查焊点」已经在第 10 节，不写回出处卡。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch02 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的时钟结论只钉在订货号 STM32F103C8T6、封装 LQFP48 上。时钟账整格照抄附录 D，不另算一套大约的主频。换到互联型时，下面第 7.3.2 节那一句作废，要改读第 8.3.2 节。换电压档时，等待周期那一档作废，要按附录 D 的电压格重读。

HSE 从第 5 脚 PD0-OSC_IN、第 6 脚 PD1-OSC_OUT 进来，8 MHz。`PLLXTPRE=0`（HSE 不预分频），`PLLSRC=1`（PLL 入口是 HSE），`PLLMUL=0111`（×9）。`8 × 9 = 72` MHz。`SW=10` 时 SYSCLK 用 PLL。HPRE 取不分频，HCLK = 72 MHz。PPRE1 = `100`（÷2），PCLK1 = 36 MHz，不得超过 36 MHz。PPRE2 取不分频，PCLK2 = 72 MHz。APB 预分频不是 1 时，挂在那条总线上的定时器时钟再 ×2，所以 TIM2–TIM7 仍是 72 MHz。TIM1 在 APB2，预分频为 1，不再 ×2。出处是 [RM0008 Rev 21 第 7.3.2 节](#source-rm0008-rcc)。

`FLASH_ACR` 基址 `0x40022000`，偏移 `0x00`。LATENCY 在 48 MHz 到 72 MHz 这一档是 `010`，也就是 2。0–24 MHz 是 0，24–48 MHz 是 1。电压档整格照抄附录 D：2.7–3.6 V。只把 PLL 改成 ×9、LATENCY 还留在 0，取指会错。这句是主图的失败路径。

`USBPRE=0` 时 72 MHz 的 PLL 再 ÷1.5，得到 48 MHz。`USBPRE=1` 是不除，得到 72 MHz，不是 48 MHz。`ADCPRE=10` 是 PCLK2÷6，`72 / 6 = 12` MHz。`ADCPRE=01` 是 ÷4，得到 18 MHz，越过 RM0008 的 14 MHz 上限。采样时间和逐次逼近留在第 09 章，这一章不写。

HSE 停振且 CSS 已开时，若 HSE 直接或经 PLL 当系统时钟，硬件改用 HSI，并关掉 HSE；HSE 若是 PLL 入口，PLL 也关掉。CSS 中断接在 NMI 上。NMI 里要写 `RCC_CIR` 的 CSSC，否则 NMI 会一直进来。同一事件还送到 TIM1 和 TIM8 的刹车输入。上电默认系统时钟是 HSI 8 MHz，不是 Cube 里填的 72 MHz。第 04 章只交叉引用「CSS 进 NMI」，不在这一章重画抢占。

第 29 脚 PA8 的复用含 MCO。脚位见 [DS5319 Rev 20 图 8](#source-ds5319-clock)。`MCO=111` 送出 PLL÷2，也就是 36 MHz，低于手册写的 50 MHz I/O 上限。`MCO=100` 把 SYSCLK 送出去时，72 MHz 越过这句 50 MHz。正常路径是 36 MHz。HSE bypass 只用于外部时钟，无源晶振不开 bypass。

第 8.3.2 节的 `OTGFSPRE`、`PLLMUL` 的 `000x` 保留、以及 ×6.5，在 STM32F103C8T6 上作废。这颗 C8 的 `RCC_CFGR` 用第 7.3.2 节。`0111` 仍是 ×9，`0000` 是 ×2。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-02-clock-tree.svg" width="760" alt="72 MHz 要 2 个 Flash 等待；HSE 停振后系统时钟回到 HSI 8 MHz">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48。第 5 脚 PD0、第 6 脚 PD1 进来的 8 MHz，PLLMUL=0111、PLLSRC=1、PLLXTPRE=0，得到 72 MHz。PCLK1 = 36 MHz，PCLK2 = 72 MHz，TIM2–TIM7 = 72 MHz，ADCCLK = 12 MHz，USBPRE=0 得到 48 MHz。正常路径 LATENCY = 2，第 29 脚 PA8 上的 MCO 是 36 MHz。失败路径是同一棵树 LATENCY 仍为 0。HSE 停振后 SYSCLK 回到 HSI 8 MHz，NMI 里要写 CSSC。18 MHz 越过 14 MHz，72 MHz 直接送 MCO 越过 50 MHz，这两句只在旁注。出处是 [RM0008 Rev 21 第 7.3.2 节与第 7.2.7 节](#source-rm0008-rcc) 和 [DS5319 Rev 20 图 8](#source-ds5319-clock)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/clock-css.gif" width="640" alt="HSE 消失后系统时钟从 72 MHz 回到 HSI 8 MHz">
  <br><sub>▲ 网页和公众号辅图。只播放 CSS 回到 HSI 的那一条。印刷以静态主图为准。LATENCY 仍为 0 的取指失败不在这条 GIF 上。</sub>
</p>

章首的 `clock-tree.svg` 留作辅图。不播放它，72 MHz、LATENCY 和 CSS 回 HSI 都在静态主图上。

## 时序或状态

| 阶段 | SWS / 开关 | 时钟 | 状态 |
| --- | --- | --- | --- |
| 复位 | SWS 指向 HSI | HSI 8 MHz | 系统时钟还不是 Cube 里填的 72 MHz |
| HSE 就绪 | HSE 从第 5 脚、第 6 脚进来 | 8 MHz | PLL 还没切 |
| PLL 锁定 | PLLMUL=0111，PLLSRC=1，PLLXTPRE=0 | 72 MHz | 先写 LATENCY，再切 SW |
| 写等待 | LATENCY = 2 | 72 MHz | 48 MHz 到 72 MHz 这一档 |
| 切到 PLL | SW=10，SWS 读回 PLL | SYSCLK = HCLK = 72 MHz | PCLK1 = 36 MHz，PCLK2 = 72 MHz，USBPRE=0 得到 48 MHz |
| 失败：等待还是 0 | LATENCY = 0 | 72 MHz | 取指失败 |
| CSS | HSE 失败 | SYSCLK 回到 HSI 8 MHz | PLL 关闭。NMI 挂起，直到软件写 CSSC |
| ADC | ADCPRE=10 | 12 MHz | ADCPRE=01 得到 18 MHz，越过 14 MHz |

这张表不写采样时间。出处是 [RM0008 Rev 21 第 7.3.2 节](#source-rm0008-rcc)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 只改 PLL ×9，一跑就停住 | LATENCY 还是 0 | 先把 LATENCY 写成 2，再切 SYSCLK | [RM0008](#source-rm0008-rcc) | 48–72 MHz 这一档是 2 个等待。电压档沿用附录 D 的 2.7–3.6 V |
| PWM 频率差一倍 | 用 PCLK1 的 36 MHz 去除 | 定时器时钟用 72 MHz | [RM0008](#source-rm0008-rcc) | APB 预分频不是 1 时定时器时钟再 ×2。TIM1 在 APB2 且预分频为 1 时不再 ×2 |
| 晶振没起振，系统停在外面 | HSE 停了，CSS 没把 NMI 清掉 | 打开 CSS 之后时钟回到 HSI，并在 NMI 里写 CSSC | [RM0008](#source-rm0008-rcc) | HSE 作为 PLL 入口时，失败会关掉 PLL，SYSCLK 改用 HSI |
| 按第 8.3.2 节去填 PLLMUL | 那一节是互联型 | 这颗 C8 用第 7.3.2 节。0111 仍是 ×9，0000 是 ×2 | [RM0008](#source-rm0008-rcc) | 互联型的 000x 保留和 OTGFSPRE 在 STM32F103C8T6 上作废 |
| MCO 送出的波形超出脚的速度 | 把 72 MHz 的 SYSCLK 直接送上 PA8 | 送 PLL÷2 的 36 MHz | [RM0008](#source-rm0008-rcc) | 送到 MCO 脚的时钟不得超过 50 MHz |
| ADC 为了更快选了 ÷4 | ADCPRE=01 得到 18 MHz | 改回 ÷6，得到 12 MHz | [RM0008](#source-rm0008-rcc) | 14 MHz 是上限。÷4 得到 18 MHz。采样时间留在第 09 章 |

```

英文插在 `<!-- /video:ch02 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The clock conclusion in this chapter is pinned to order code STM32F103C8T6 in LQFP48. The clock ledger is copied whole from Appendix D. On a connectivity-line part, the section 7.3.2 sentence below is void and you read section 8.3.2 instead. When the voltage range changes, the wait-state step is void and you re-read the voltage cell in Appendix D.

HSE enters on pin 5 PD0-OSC_IN and pin 6 PD1-OSC_OUT at 8 MHz. `PLLXTPRE=0` (HSE is not prescaled), `PLLSRC=1` (the PLL input is HSE), `PLLMUL=0111` (×9). `8 × 9 = 72` MHz. With `SW=10`, SYSCLK uses the PLL. HPRE divides by 1, so HCLK = 72 MHz. PPRE1 = `100` (÷2), so PCLK1 = 36 MHz and must not exceed 36 MHz. PPRE2 divides by 1, so PCLK2 = 72 MHz. When an APB prescaler is not 1, timers on that bus clock at twice PCLK, so TIM2–TIM7 are still 72 MHz. TIM1 is on APB2 with a prescaler of 1, so it is not doubled again. Source: [RM0008 Rev 21 section 7.3.2](#source-rm0008-rcc).

`FLASH_ACR` is at base `0x40022000`, offset `0x00`. LATENCY for 48 MHz to 72 MHz is `010`, which is 2. From 0 to 24 MHz it is 0. From 24 to 48 MHz it is 1. The voltage cell is copied whole from Appendix D: 2.7–3.6 V. Setting the PLL to ×9 and leaving LATENCY at 0 makes instruction fetch fail. That is the failure path on the key figure.

With `USBPRE=0`, the 72 MHz PLL is divided by 1.5 and the result is 48 MHz. `USBPRE=1` does not divide, so the result is 72 MHz, which is not 48 MHz. `ADCPRE=10` is PCLK2÷6, and `72 / 6 = 12` MHz. `ADCPRE=01` is ÷4, which is 18 MHz and crosses the RM0008 ceiling of 14 MHz. Sample time and successive approximation stay in chapter file 09. This chapter does not write them.

When HSE stops and CSS is on, if HSE is the system clock directly or through the PLL, hardware switches to HSI and turns HSE off. If HSE was the PLL input, the PLL turns off too. The CSS interrupt is NMI. The NMI handler writes CSSC in `RCC_CIR`, or NMI keeps returning. The same event also reaches the TIM1 and TIM8 break inputs. After reset the system clock is HSI at 8 MHz, not the 72 MHz filled in by Cube. Chapter file 04 only cross-references “CSS enters NMI”. This chapter does not redraw preemption.

Pin 29 PA8 includes MCO in its alternate function. The pin is in [DS5319 Rev 20 Figure 8](#source-ds5319-clock). `MCO=111` drives PLL÷2, which is 36 MHz, under the 50 MHz I/O limit written in the manual. `MCO=100` drives SYSCLK out, and 72 MHz crosses that 50 MHz sentence. The normal path is 36 MHz. HSE bypass is only for an external clock. A crystal does not enable bypass.

Section 8.3.2 `OTGFSPRE`, the reserved `PLLMUL` encoding `000x`, and ×6.5 are void on STM32F103C8T6. This C8 uses section 7.3.2 for `RCC_CFGR`. `0111` is still ×9. `0000` is still ×2.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-02-clock-tree.svg" width="760" alt="72 MHz needs two Flash wait states; after HSE stops, the system clock returns to HSI at 8 MHz">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48. Pin 5 PD0 and pin 6 PD1 bring in 8 MHz. PLLMUL=0111, PLLSRC=1, and PLLXTPRE=0 produce 72 MHz. PCLK1 = 36 MHz, PCLK2 = 72 MHz, TIM2–TIM7 = 72 MHz, ADCCLK = 12 MHz, and USBPRE=0 produces 48 MHz. The normal path has LATENCY = 2, and MCO on pin 29 PA8 is 36 MHz. The failure path is the same tree with LATENCY still 0. After HSE stops, SYSCLK returns to HSI at 8 MHz and the NMI handler writes CSSC. 18 MHz crosses 14 MHz, and driving 72 MHz straight out of MCO crosses 50 MHz. Those two sentences stay in the margin. Sources: [RM0008 Rev 21 sections 7.3.2 and 7.2.7](#source-rm0008-rcc) and [DS5319 Rev 20 Figure 8](#source-ds5319-clock).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/clock-css.gif" width="640" alt="After HSE disappears, the system clock falls from 72 MHz back to HSI at 8 MHz">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the CSS return to HSI. Print uses the static figure. The fetch failure with LATENCY still 0 is not on this GIF.</sub>
</p>

The opening `clock-tree.svg` stays a side figure. Without playing it, 72 MHz, LATENCY, and the CSS return to HSI are all on the static figure.

## Timing or state

| Phase | SWS / switch | Clock | State |
| --- | --- | --- | --- |
| Reset | SWS points at HSI | HSI 8 MHz | The system clock is not the 72 MHz filled in by Cube |
| HSE ready | HSE enters on pin 5 and pin 6 | 8 MHz | The PLL is not selected yet |
| PLL locks | PLLMUL=0111, PLLSRC=1, PLLXTPRE=0 | 72 MHz | Write LATENCY before switching SW |
| Write the wait | LATENCY = 2 | 72 MHz | The 48 MHz to 72 MHz step |
| Switch to the PLL | SW=10, SWS reads back PLL | SYSCLK = HCLK = 72 MHz | PCLK1 = 36 MHz, PCLK2 = 72 MHz, USBPRE=0 produces 48 MHz |
| Failure: wait still 0 | LATENCY = 0 | 72 MHz | Instruction fetch fails |
| CSS | HSE fails | SYSCLK returns to HSI 8 MHz | The PLL is off. NMI stays pending until software writes CSSC |
| ADC | ADCPRE=10 | 12 MHz | ADCPRE=01 produces 18 MHz and crosses 14 MHz |

This table does not include the sample time. Source: [RM0008 Rev 21 section 7.3.2](#source-rm0008-rcc).

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The core stops as soon as the PLL is set to ×9 | LATENCY is still 0 | Write LATENCY = 2 before switching SYSCLK | [RM0008](#source-rm0008-rcc) | The 48–72 MHz step is two wait states. The voltage cell is Appendix D, 2.7–3.6 V |
| PWM frequency is off by 2× | The division used PCLK1 at 36 MHz | Use the 72 MHz timer clock | [RM0008](#source-rm0008-rcc) | When the APB prescaler is not 1, the timer clock is doubled. TIM1 on APB2 with prescaler 1 is not doubled again |
| The crystal never starts and the core sits outside | HSE stopped and CSS left NMI pending | After CSS is on, the clock returns to HSI, and the NMI handler writes CSSC | [RM0008](#source-rm0008-rcc) | When HSE is the PLL input, the failure turns the PLL off and SYSCLK uses HSI |
| PLLMUL was filled from section 8.3.2 | That section is the connectivity line | This C8 uses section 7.3.2. 0111 is still ×9 and 0000 is still ×2 | [RM0008](#source-rm0008-rcc) | The connectivity-line 000x reserved encoding and OTGFSPRE are void on STM32F103C8T6 |
| The waveform on MCO is too fast for the pin | SYSCLK at 72 MHz was driven straight onto PA8 | Drive PLL÷2, which is 36 MHz | [RM0008](#source-rm0008-rcc) | The clock sent to the MCO pin must not exceed 50 MHz |
| ADC was set to ÷4 to go faster | ADCPRE=01 produces 18 MHz | Change it back to ÷6, which is 12 MHz | [RM0008](#source-rm0008-rcc) | 14 MHz is the ceiling. ÷4 produces 18 MHz. Sample time stays in chapter file 09 |

```

四块里不要写入 `21 µs` 或 `21 us`。采样时间只说「留在第 09 章」。修订号 Rev 21 留在出处链接里。

- [ ] **Step 5: 追加两个来源对象**

`url`、`snapshot`、`license` 从清单原样复制。`title` 用 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。`accessed` 是 `2026-10-25`。`scope` 用本任务测试里 `scopes` 字典的那两句。中文对象追加在 `stm32-book/manifest.json` 的 `sources` 末尾，英文对象追加在 `stm32-book/manifest-en.json` 的 `sources` 末尾。不要改已有 id 的任何字段。两章罗盘的 `sources` 改成测试里的 `compass`，不删除 `rm0008` 和 `ds5319`。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3ClockChapterTests -v`

Expected: OK。

```bash
git add docs/02-芯片选型与存储器时钟.md docs/en/02-part-and-clock.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch3_chapters.py
git commit -m "book: 加厚第 02 章并把 CFGR 改回第 7.3.2 节"
```

### Task 6: Thicken chapter 05 in both languages

**Files:**
- Modify: `docs/05-定时器与PWM.md`
- Modify: `docs/en/05-timer-pwm.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `rm0008-tim`、`ds5319-tim`；`05-定时器与PWM.md` 的 `sources` 改为 `["rm0008", "rm0008-tim", "ds5319-tim"]`）
- Modify: `stm32-book/manifest-en.json`（同一组字段规则；`05-timer-pwm.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch3_chapters.py`
- Test: `stm32-book/tests/test_batch3_chapters.py`

**Interfaces:**
- Consumes: `rm0008-tim`、`ds5319-tim`，以及 `assets/diagrams/sample-05-pwm-1khz.svg`、`assets/gif/pwm-1khz.gif`。Task 5 的 `baseline_manifests()`。不要再定义一遍。
- Produces: 四块各一次。分类表不再有 `16/32`。片段里的比较值是 `500`，不再有 `PWM_ARR / 2`。四块里不出现 `0x10`。`examples/timer-pwm/` 的 diff 为空。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch3_chapters.py` 末尾、`if __name__` 之前追加。不要再贴 `baseline_manifests`。

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3PwmChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 改正位宽、1 秒那一行、比较值和分辨率注记**

中文 `docs/05-定时器与PWM.md`：

把

```markdown
| 通用 | TIM2~TIM5 | 16/32 位 | 4 通道，PWM/捕获/编码器 | 通用定时/PWM |
```

换成

```markdown
| 通用 | TIM2~TIM5 | 16 位 | 4 通道，PWM/捕获/编码器 | 这颗 STM32F103C8T6 上是 16 位。32 位的 TIM2/TIM5 是别的系列，换到那一系列时这一句作废 |
```

把

```markdown
| 1s（大 ARR） | 71 | 999999 | 1.000s | 需 32 位定时器 |
```

换成

```markdown
| 1s（大 ARR） | 71 | 999999 | 装不下 | 这颗料的 TIM2–TIM5 是 16 位，装不下 999999。能装下的 1 秒是上一行 PSC = 7199、ARR = 9999 |
```

把

```markdown
| 1kHz | 72000 | 1/72000 | 高分辨率，适合调光 |
```

换成

```markdown
| 1kHz | 72000 | 1/72000 | 另一组高分辨率参数（PSC = 0 时 ARR+1 = 72000）。不是附录 D 的 1 kHz 格子（PSC = 71，ARR = 999） |
```

把

```markdown
    oc.Pulse      = PWM_ARR / 2;                     /* 初始 50% 占空比 = CCR */
```

换成

```markdown
    oc.Pulse      = 500;                             /* CCR = 500。500 / (ARR + 1) = 50%，高电平 500 µs */
```

英文 `docs/en/05-timer-pwm.md`：

把

```markdown
| General-purpose | TIM2–TIM5 | 16/32-bit | 4 channels, PWM / capture / encoder | General timing and PWM |
```

换成

```markdown
| General-purpose | TIM2–TIM5 | 16-bit | 4 channels, PWM / capture / encoder | On this STM32F103C8T6 they are 16-bit. 32-bit TIM2/TIM5 is a sentence about another family, and it is void if you move to that family |
```

把

```markdown
| 1 s (large ARR) | 71 | 999999 | 1.000 s | Needs a 32-bit timer |
```

换成

```markdown
| 1 s (large ARR) | 71 | 999999 | does not fit | TIM2–TIM5 on this part are 16-bit and cannot hold 999999. The 1 s that fits is the row above, PSC = 7199 and ARR = 9999 |
```

把

```markdown
| 1 kHz | 72000 | 1/72000 | High resolution, good for dimming |
```

换成

```markdown
| 1 kHz | 72000 | 1/72000 | A different high-resolution set (PSC = 0 makes ARR+1 = 72000). Not the Appendix D 1 kHz cell (PSC = 71, ARR = 999) |
```

把

```markdown
    oc.Pulse      = PWM_ARR / 2;                     /* initial 50% duty = CCR */
```

换成

```markdown
    oc.Pulse      = 500;                             /* CCR = 500. 500 / (ARR + 1) = 50%, high for 500 µs */
```

`bd.DeadTime = 0x10` 留在核心原理，不换算成纳秒，不写进四块。中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。预装载、更新标志和呼吸灯撕裂已经在核心原理里，不写回出处卡。不改 `examples/timer-pwm/`。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch05 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的波形结论只钉在订货号 STM32F103C8T6 上。计数时钟用附录 D 的 72 MHz，不用 36 MHz。换到 32 位定时器的系列时，「这颗料是 16 位」那一句作废。

TIM3 在 APB1。PCLK1 = 36 MHz，预分频不是 1，所以 TIM3 的计数时钟是 72 MHz。PSC = 71，ARR = 999。`72e6 / ((71+1) × (999+1)) = 1000` Hz。计数时钟先被分成 1 MHz，再数 1000 下，周期 1 ms。同一组 PSC、ARR 用 36 MHz 去除，得到 500 Hz。这是主图的失败路径。出处是 [RM0008 Rev 21 第 15 章](#source-rm0008-tim)。

PWM 模式 1：CNT < CCR 时输出有效电平。CCR = 500 时，`500 / (999+1) = 50%`，高电平 500 µs。

这颗料的 TIM2–TIM5 是 16 位。PSC = 71、ARR = 999999 装不下。能装下的 1 秒是 PSC = 7199、ARR = 9999，`72e6 / (7200 × 10000) = 1` Hz。32 位的 TIM2/TIM5 是别的系列上的句子。

默认不重映射时 TIM3_CH1 在 PA6。DS5319 Rev 20 表 5：LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1，同一格也含 SPI1_MISO。本图只画定时器。SPI 对这只脚的用法在第 08 章，两章的主图不把两种功能画成同时有效。重映射到 PB4 或 PC6 要另写 `TIM3_REMAP`，不画进正常路径。出处是 [DS5319 Rev 20 表 5](#source-ds5319-tim)。

TIM1/TIM8 的 `TIMx_BDTR` 偏移 `0x44`，复位值 `0x0000`，位 15 MOE 为 0 时主输出关着。`HAL_TIM_PWM_Start` 会置 MOE。通用定时器 TIM3 没有这一位。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-05-pwm-1khz.svg" width="760" alt="72 MHz 计数时钟下这组 PSC/ARR 是 1 kHz；改用 36 MHz 去除得到 500 Hz">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48 第 16 脚 PA6 = TIM3_CH1。计数时钟 72 MHz，PSC = 71，ARR = 999，CCR = 500。正常路径周期 1 ms，高电平 500 µs，频率 1000 Hz。失败路径用 36 MHz 去除，周期 2 ms，频率 500 Hz。ARR = 999999 在 16 位计数器里装不下。TIM1 的 MOE 在偏移 0x44，复位值 0x0000，不占这条波形。SPI1_MISO 不画进这条波形。出处是 [RM0008 Rev 21 第 15 章](#source-rm0008-tim) 和 [DS5319 Rev 20 表 5](#source-ds5319-tim)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/pwm-1khz.gif" width="640" alt="CNT 走到 CCR = 500 时电平翻转，频率 1000 Hz">
  <br><sub>▲ 网页和公众号辅图。只播放 1000 Hz 和 500 µs 的正常路径。印刷以静态主图为准。500 Hz 的失败不在这条 GIF 上。</sub>
</p>

章首的 `timer-pwm.svg` 和 `pwm-breath.gif` 留在原节，标成辅图。不播放它们，1 kHz 和 500 Hz 都在静态主图上。

## 时序或状态

| 行 | 计数时钟 | PSC | ARR | CCR | CNT | 输出 | 时间 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 正常，高 | 72 MHz | 71 | 999 | 500 | 0 到 499 | 高 | 500 µs |
| 正常，低 | 72 MHz | 71 | 999 | 500 | 500 到 999 | 低 | 再 500 µs，周期 1000 µs，1000 Hz |
| 失败 | 36 MHz | 71 | 999 | 500 | 0 到 999 | 同一比较 | 周期 2000 µs，500 Hz |
| 装不下 | 72 MHz | 71 | 999999 | — | — | 不作为 1 秒 | 16 位截断，不算成 1 秒 |
| 1 秒 | 72 MHz | 7199 | 9999 | — | 0 到 9999 | — | 1 Hz |

出处是 [RM0008 Rev 21 第 15 章](#source-rm0008-tim)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 示波器上是 500 Hz | 用 36 MHz 去除了 | 用 72 MHz 去除，PSC = 71，ARR = 999 | [RM0008](#source-rm0008-tim) | 这组数在 72 MHz 下是 1000 Hz。36 MHz 去除得到 500 Hz |
| 想要 1 秒，ARR 写成 999999 | 16 位装不下 | 改成 PSC = 7199、ARR = 9999 | [RM0008](#source-rm0008-tim) | 这颗料的通用定时器是 16 位，装不下 999999 |
| TIM1 完全没有波形 | BDTR 位 15 的 MOE 还是 0 | 置上 MOE | [RM0008](#source-rm0008-tim) | 复位值 0x0000，MOE 为 0 时主输出关闭。偏移 0x44。TIM3 没有这一位 |
| PWM 出现在别的脚上 | TIM3_REMAP 不是 00 | 保持 TIM3_REMAP=00，用 PA6 | [DS5319](#source-ds5319-tim) | LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1 |

```

英文插在 `<!-- /video:ch05 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The waveform conclusion in this chapter is pinned to order code STM32F103C8T6. The counter clock is the 72 MHz from Appendix D, not 36 MHz. On a family whose TIM2 or TIM5 is 32-bit, the sentence “this part is 16-bit” is void.

TIM3 is on APB1. PCLK1 = 36 MHz and the prescaler is not 1, so the TIM3 counter clock is 72 MHz. PSC = 71 and ARR = 999. `72e6 / ((71+1) × (999+1)) = 1000` Hz. The counter clock is first divided to 1 MHz, then counts 1000 steps, and the period is 1 ms. The same PSC and ARR divided by 36 MHz produce 500 Hz. That is the failure path on the key figure. Source: [RM0008 Rev 21 chapter 15](#source-rm0008-tim).

PWM mode 1 drives the active level while CNT < CCR. With CCR = 500, `500 / (999+1) = 50%`, and the high time is 500 µs.

TIM2–TIM5 on this part are 16-bit. PSC = 71 and ARR = 999999 do not fit. The 1 second that fits is PSC = 7199 and ARR = 9999, `72e6 / (7200 × 10000) = 1` Hz. A 32-bit TIM2 or TIM5 is a sentence about another family.

With no remap, TIM3_CH1 is on PA6. DS5319 Rev 20 Table 5: LQFP48 pin 16 is PA6, the default alternate function includes TIM3_CH1, and the same cell also includes SPI1_MISO. This figure draws only the timer. Chapter file 08 draws SPI on this pin. The two key figures do not draw both functions as active together. A remap onto PB4 or PC6 writes `TIM3_REMAP` and is not on the normal path. Source: [DS5319 Rev 20 Table 5](#source-ds5319-tim).

On TIM1/TIM8, `TIMx_BDTR` is at offset `0x44`, the reset value is `0x0000`, and bit 15 MOE at 0 holds the main output off. `HAL_TIM_PWM_Start` sets MOE. General-purpose TIM3 has no such bit.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-05-pwm-1khz.svg" width="760" alt="At a 72 MHz counter clock this PSC/ARR pair is 1 kHz; dividing by 36 MHz produces 500 Hz">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48 pin 16 PA6 = TIM3_CH1. Counter clock 72 MHz, PSC = 71, ARR = 999, CCR = 500. The normal path has a 1 ms period, 500 µs high, and 1000 Hz. The failure path divides by 36 MHz, so the period is 2 ms and the frequency is 500 Hz. ARR = 999999 does not fit in a 16-bit counter. TIM1 MOE is at offset 0x44 with reset value 0x0000, and it is not this waveform. SPI1_MISO is not drawn on this waveform. Sources: [RM0008 Rev 21 chapter 15](#source-rm0008-tim) and [DS5319 Rev 20 Table 5](#source-ds5319-tim).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/pwm-1khz.gif" width="640" alt="The level flips when CNT reaches CCR = 500, at 1000 Hz">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the 1000 Hz path and the 500 µs high time. Print uses the static figure. The 500 Hz failure is not on this GIF.</sub>
</p>

The opening `timer-pwm.svg` and `pwm-breath.gif` stay in their original section and are marked as side figures. Without playing them, both 1 kHz and 500 Hz are on the static figure.

## Timing or state

| Row | Counter clock | PSC | ARR | CCR | CNT | Output | Time |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Normal, high | 72 MHz | 71 | 999 | 500 | 0 through 499 | high | 500 µs |
| Normal, low | 72 MHz | 71 | 999 | 500 | 500 through 999 | low | another 500 µs, period 1000 µs, 1000 Hz |
| Failure | 36 MHz | 71 | 999 | 500 | 0 through 999 | same compare | period 2000 µs, 500 Hz |
| Does not fit | 72 MHz | 71 | 999999 | — | — | not a 1 s pulse | truncated at 16 bits, not counted as 1 s |
| 1 second | 72 MHz | 7199 | 9999 | — | 0 through 9999 | — | 1 Hz |

Source: [RM0008 Rev 21 chapter 15](#source-rm0008-tim).

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The scope shows 500 Hz | The division used 36 MHz | Divide by 72 MHz, with PSC = 71 and ARR = 999 | [RM0008](#source-rm0008-tim) | This set is 1000 Hz at 72 MHz. Dividing by 36 MHz produces 500 Hz |
| ARR was written as 999999 for a 1 s period | A 16-bit counter cannot hold it | Use PSC = 7199 and ARR = 9999 | [RM0008](#source-rm0008-tim) | The general-purpose timers on this part are 16-bit and cannot hold 999999 |
| TIM1 has no waveform at all | BDTR bit 15 MOE is still 0 | Set MOE | [RM0008](#source-rm0008-tim) | The reset value is 0x0000. With MOE at 0 the main output stays off. The offset is 0x44. TIM3 has no such bit |
| PWM appears on some other pin | TIM3_REMAP is not 00 | Keep TIM3_REMAP=00 and use PA6 | [DS5319](#source-ds5319-tim) | LQFP48 pin 16 is PA6, and the default alternate function includes TIM3_CH1 |

```

四块里不要写入 `0x10`。死区留在核心原理。

- [ ] **Step 5: 追加两个来源对象**

规则与 Task 5 的 Step 5 相同。`scope` 用本任务测试里的 `scopes`。罗盘改成 `["rm0008", "rm0008-tim", "ds5319-tim"]`。不要改 Task 5 已经追加的 `rm0008-rcc` 和 `ds5319-clock`。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3PwmChapterTests -v`

Expected: OK。

```bash
git diff --name-only -- examples/timer-pwm
```

Expected: 无输出。

```bash
git add docs/05-定时器与PWM.md docs/en/05-timer-pwm.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch3_chapters.py
git commit -m "book: 加厚第 05 章并把 1 kHz 与 500 Hz 写成同一笔账"
```

### Task 7: Thicken chapter 08 in both languages

**Files:**
- Modify: `docs/08-SPI总线.md`
- Modify: `docs/en/08-spi.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `rm0008-spi`、`ds5319-spi`；`08-SPI总线.md` 的 `sources` 改为 `["rm0008", "project-examples", "rm0008-spi", "ds5319-spi"]`）
- Modify: `stm32-book/manifest-en.json`（`08-spi.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch3_chapters.py`
- Test: `stm32-book/tests/test_batch3_chapters.py`

**Interfaces:**
- Consumes: `rm0008-spi`、`ds5319-spi`、已有的 `project-examples`，以及 `assets/diagrams/sample-08-spi-jedec.svg`、`assets/gif/spi-jedec.gif`。Task 5 的 `baseline_manifests()`。
- Produces: 四块各一次。分频表补全到 `111` = ÷256。四块里不出现 `0x3A`、`4.7`、`0x40013000`。`project-examples` 对象与基线逐字段相同。不改 `examples/spi-flash/`。

- [ ] **Step 1: 把章节断言加进测试**

```python
class Batch3SpiChapterTests(unittest.TestCase):
    def test_spi_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "08-SPI总线.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "08-spi.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        for text in (zh, en):
            for token in (
                "010",
                "9 MHz",
                "001",
                "18 MHz",
                "000",
                "36 MHz",
                "0x9F",
                "0xEF",
                "0x40",
                "0x17",
                "256",
                "PA4",
                "PA5",
                "PA6",
                "PA7",
                "CPOL",
                "CPHA",
                "rx[1]",
                "SPI_POLARITY_LOW",
                "SPI_PHASE_1EDGE",
                "SPI_BAUDRATEPRESCALER_8",
                "#source-rm0008-spi",
                "#source-ds5319-spi",
                "#source-project-examples",
            ):
                self.assertIn(token, text)
            self.assertIn("111", text)
        self.assertIn("第 14 脚", zh)
        self.assertIn("第 17 脚", zh)
        self.assertIn("pin 14", en)
        self.assertIn("pin 17", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            self.assertNotIn("0x3A", blocks)
            self.assertNotIn("4.7", blocks)
            self.assertNotIn("0x40013000", blocks)
        self.assertIn("../assets/diagrams/sample-08-spi-jedec.svg", zh)
        self.assertIn("../../assets/diagrams/sample-08-spi-jedec.svg", en)
        self.assertIn("../assets/gif/spi-jedec.gif", zh)
        self.assertIn("../../assets/gif/spi-jedec.gif", en)
        self.assertIn("../assets/animations/spi-transfer.svg", zh)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-08-spi-jedec.svg"), zh_key.index("spi-jedec.gif"))
        self.assertLess(en_key.index("sample-08-spi-jedec.svg"), en_key.index("spi-jedec.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-spi": (
                "第 08 章原理与边界、时序或状态、坑与出处卡。全双工在每个 SCK 上同时移出和移入。八档分频只有 2、4、8、16、32、64、128、256。BR 010 是 ÷8 = 9 MHz，001 是 ÷4 = 18 MHz，000 是 ÷2 = 36 MHz。Mode 0 是 CPOL = 0、CPHA = 0。发 0x9F 的那一字节同时移入的不是厂商号。不编 SPI 基址。",
                "Chapter 08 principle, timing, and source cards. Full duplex shifts out and in on each SCK. The only dividers are 2, 4, 8, 16, 32, 64, 128, and 256. BR 010 is ÷8 = 9 MHz, 001 is ÷4 = 18 MHz, and 000 is ÷2 = 36 MHz. Mode 0 is CPOL = 0 and CPHA = 0. The byte shifted in while 0x9F shifts out is not the manufacturer id. Does not invent an SPI base address.",
            ),
            "ds5319-spi": (
                "第 08 章关键插图和坑与出处卡。LQFP48 第 14 脚 PA4 是 SPI1_NSS，第 15 脚 PA5 是 SPI1_SCK，第 16 脚 PA6 是 SPI1_MISO，第 17 脚 PA7 是 SPI1_MOSI。不把重映射画成复位后的默认脚。不把第 14 脚画成 DAC。不把 TIM3_CH1 画成与 MISO 同时有效。",
                "Chapter 08 key figure and source cards. LQFP48 pin 14 PA4 is SPI1_NSS, pin 15 PA5 is SPI1_SCK, pin 16 PA6 is SPI1_MISO, and pin 17 PA7 is SPI1_MOSI. Does not draw the remap as the reset default. Does not draw pin 14 as DAC. Does not draw TIM3_CH1 as active together with MISO.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "project-examples", "rm0008-spi", "ds5319-spi"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["08-SPI总线.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["08-spi.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual("2026-10-25", card_zh["accessed"])
            self.assertEqual(by_id[source_id]["title_zh"], card_zh["title"])
            self.assertEqual(by_id[source_id]["title_en"], card_en["title"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        baseline, baseline_en = baseline_manifests()
        self.assertEqual(baseline["sources"]["project-examples"], zh_manifest["sources"]["project-examples"])
        self.assertEqual(baseline_en["sources"]["project-examples"], en_manifest["sources"]["project-examples"])
        for source_id, obj in baseline["sources"].items():
            self.assertEqual(obj, zh_manifest["sources"][source_id])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3SpiChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 把分频表补全八档，并删掉旧坑表**

若 Task 2 读到的第 25.5.1 节编码和下面这张表不同，表里的 `BR[2:0]` 改成印出的编码，9 MHz 仍对着 ÷8，18 MHz 仍对着 ÷4，36 MHz 仍对着 ÷2。编码相同就用下面这三行。

中文在 `| 100 | 32 | 2.25MHz |` 之后追加：

```markdown
| 101 | 64 | 1.125MHz |
| 110 | 128 | 0.5625MHz |
| 111 | 256 | 0.28125MHz |
```

英文在 `| 100 | 32 | 2.25 MHz |` 之后追加：

```markdown
| 101 | 64 | 1.125 MHz |
| 110 | 128 | 0.5625 MHz |
| 111 | 256 | 0.28125 MHz |
```

中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。ST7789 的 `0x01`、`0x11`、`0x3A`、`0x36`、`0x29` 留在核心原理第 8 节，不进四块。写使能和忙位留在核心原理；忙位若要写进出处卡，只用下面四块里那一行，链接 `project-examples`。不新开 Winbond id。不改 `examples/spi-flash/`。不编 SPI 基址。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch08 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的 SPI 结论只钉在订货号 STM32F103C8T6 上。SPI1 在 APB2，内核时钟 72 MHz。工作点整格照抄附录 D：Mode 0，`BR=010`，SCK = 9 MHz。换到重映射脚时，下面的 PA5/PA6/PA7 作废。

复位后的默认脚是 LQFP48 第 15 脚 PA5 = SPI1_SCK，第 17 脚 PA7 = SPI1_MOSI，第 16 脚 PA6 = SPI1_MISO，第 14 脚 PA4 = SPI1_NSS。本章片选不用硬件 NSS，PA4 配成推挽 GPIO，软件拉低再拉高。这不是第 07 章的开漏。重映射到 PB3/PB4/PB5 不画进正常路径。第 16 脚同时是第 05 章的 TIM3_CH1；本图只画 MISO。出处是 [DS5319 Rev 20 表 5](#source-ds5319-spi)。

Mode 0 是 CPOL = 0、CPHA = 0。空闲时 SCK 为低，数据在第一个边沿（上升沿）采样。章内代码是 `SPI_POLARITY_LOW`、`SPI_PHASE_1EDGE`、`SPI_NSS_SOFT`、`SPI_FIRSTBIT_MSB`、`SPI_BAUDRATEPRESCALER_8`。

`BR[2:0]` 只有 2、4、8、16、32、64、128、256 这八档。`010` 是 ÷8，`72 / 8 = 9` MHz。`001` 是 ÷4，18 MHz。`000` 是 ÷2，36 MHz。36 MHz 是相对 9 MHz 工作点的过快失败，不另开一套账。不支持 ÷3。不编 SPI 基址。出处是 [RM0008 Rev 21 第 25.5.1 节](#source-rm0008-spi)。

主机发出 `{0x9F, 0xFF, 0xFF, 0xFF}`。全双工下，发 `0x9F` 的那 8 个 SCK 同时移进 `rx[0]`，这一字节不是厂商号。接下来三字节是 `rx[1]=0xEF`、`rx[2]=0x40`、`rx[3]=0x17`。拼法是 `rx[1] << 16 | rx[2] << 8 | rx[3]`，也就是 `0xEF4017`。`0x40` 是存储器类型，不是容量。页大小 256 字节。这两句链接 [已有例程](#source-project-examples) 和附录 D。状态字节的位 0 在例程里当成忙。`0x05`、`0x06`、`0x02`、`0x03` 留在核心原理。

MOSI 和 MISO 对调之后，三字节对不上 `0xEF 0x40 0x17`。这是主图的失败路径。片选一直为低时，下一条命令接在上一条后面。只调用 Transmit、不读 MISO 时，下一次读到的是残留。CPHA 配成第二沿时，字节会错位。片选不释放和 `BR=000` 的 36 MHz 放在旁注。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-08-spi-jedec.svg" width="760" alt="Mode 0、除以 8 得到 9 MHz；0x9F 之后的三字节是 0xEF、0x40、0x17；MOSI 和 MISO 对调之后对不上">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48。第 14 脚 PA4 = CS（推挽，事务期间为低），第 15 脚 PA5 = SCK，第 16 脚 PA6 = MISO，第 17 脚 PA7 = MOSI。CPOL = 0，CPHA = 0，BR=010，SCK = 9 MHz。正常路径 MOSI 先送 0x9F，随后三个 0xFF；rx[1] 到 rx[3] 是 0xEF、0x40、0x17。失败路径是 PA6 与 PA7 对调。旁注：PA4 一直为低时两条事务粘成一条；BR=000 时 SCK = 36 MHz。不把第 14 脚画成 DAC。出处是 [RM0008 Rev 21 第 25.5.1 节](#source-rm0008-spi) 和 [DS5319 Rev 20 表 5](#source-ds5319-spi)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/spi-jedec.gif" width="640" alt="片选拉低后移出 0x9F，再移入 0xEF、0x40、0x17">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径，并标出 9 MHz。印刷以静态主图为准。对调线和 36 MHz 不在这条 GIF 上。</sub>
</p>

章首的 `spi-transfer.svg` 留作辅图。不播放它，脚位、9 MHz 和 ID 三字节都在静态主图上。

## 时序或状态

| 行 | 字节序号 | MOSI | MISO | CS | SCK |
| --- | --- | --- | --- | --- | --- |
| 正常 | 1 | 0x9F | rx[0]，不是厂商号 | 低 | 上升沿采样 |
| 正常 | 2 | 0xFF | 0xEF | 低 | 上升沿采样 |
| 正常 | 3 | 0xFF | 0x40 | 低 | 上升沿采样 |
| 正常 | 4 | 0xFF | 0x17 | 低 | 上升沿采样 |
| 结束 | — | — | — | 回到高 | 空闲为低 |
| 模式 | — | — | — | — | CPOL = 0，CPHA = 0 |
| 速率 | — | — | — | — | BR=010 为 9 MHz，BR=001 为 18 MHz，BR=000 为 36 MHz |
| 失败 | 2 到 4 | — | 不是 0xEF 0x40 0x17 | 低 | PA6 与 PA7 对调 |

页大小 256 字节。出处是 [RM0008](#source-rm0008-spi) 与 [例程](#source-project-examples)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 读回的 ID 不是 0xEF4017 | PA7 不是 MOSI，或 PA6 不是 MISO，或模式不是 0 | 保持 Mode 0，并核对 PA7 是 MOSI、PA6 是 MISO | [DS5319](#source-ds5319-spi) | LQFP48 第 16 脚是 MISO，第 17 脚是 MOSI。三字节本身见下一行 |
| 把 rx[0] 当成厂商号 | 发命令的那 8 个 SCK 同时移进了 rx[0] | 厂商号在 rx[1]，类型在 rx[2]，容量在 rx[3] | [例程](#source-project-examples) | 命令是 0x9F。三字节是 0xEF、0x40、0x17。0x40 不是容量。页大小 256 字节 |
| SCK 跑到 36 MHz | BR 写成了 000 | BR 用 010，得到 9 MHz | [RM0008](#source-rm0008-spi) | 八档分频里 010 是 ÷8。000 是 ÷2 = 36 MHz。不支持 ÷3 |
| 两条命令粘在一起 | PA4 一直为低 | 每条事务结束把 PA4 拉高 | [DS5319](#source-ds5319-spi) | 第 14 脚是 SPI1_NSS。本章把它当推挽片选。它在 C8 上不是 DAC 输出 |
| ID 出现在 PB3/PB4/PB5 | 用了重映射，还当成复位默认 | 复位后的默认脚是 PA5/PA6/PA7 | [DS5319](#source-ds5319-spi) | 第 15 脚 SCK，第 16 脚 MISO，第 17 脚 MOSI |
| 状态字节的位 0 被当成协议里的忙 | 这是例程的做法 | 只按例程去等这一位 | [例程](#source-project-examples) | 例程把状态字节的位 0 当成忙 |

```

英文插在 `<!-- /video:ch08 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The SPI conclusion in this chapter is pinned to order code STM32F103C8T6. SPI1 is on APB2 and the kernel clock is 72 MHz. The working point is copied whole from Appendix D: Mode 0, `BR=010`, SCK = 9 MHz. On the remapped pins, the PA5/PA6/PA7 sentence below is void.

The reset-default pins are LQFP48 pin 15 PA5 = SPI1_SCK, pin 17 PA7 = SPI1_MOSI, pin 16 PA6 = SPI1_MISO, and pin 14 PA4 = SPI1_NSS. This chapter does not use hardware NSS. PA4 is a push-pull GPIO, driven low and then high in software. That is not the open-drain of chapter file 07. The remap onto PB3/PB4/PB5 is not on the normal path. Pin 16 is also TIM3_CH1 in chapter file 05. This figure draws only MISO. Source: [DS5319 Rev 20 Table 5](#source-ds5319-spi).

Mode 0 is CPOL = 0 and CPHA = 0. SCK idles low, and the data is sampled on the first edge, which is the rising edge. The chapter code uses `SPI_POLARITY_LOW`, `SPI_PHASE_1EDGE`, `SPI_NSS_SOFT`, `SPI_FIRSTBIT_MSB`, and `SPI_BAUDRATEPRESCALER_8`.

`BR[2:0]` has only the eight dividers 2, 4, 8, 16, 32, 64, 128, and 256. `010` is ÷8, and `72 / 8 = 9` MHz. `001` is ÷4, 18 MHz. `000` is ÷2, 36 MHz. 36 MHz is the too-fast failure next to the 9 MHz working point. There is no second ledger. There is no ÷3. Do not invent an SPI base address. Source: [RM0008 Rev 21 section 25.5.1](#source-rm0008-spi).

The master sends `{0x9F, 0xFF, 0xFF, 0xFF}`. In full duplex, the eight SCK edges that shift out `0x9F` also shift `rx[0]` in, and that byte is not the manufacturer id. The next three bytes are `rx[1]=0xEF`, `rx[2]=0x40`, and `rx[3]=0x17`. The assembly is `rx[1] << 16 | rx[2] << 8 | rx[3]`, which is `0xEF4017`. `0x40` is the memory type, not the capacity. The page is 256 bytes. Those two sentences link the [existing example](#source-project-examples) and Appendix D. The example treats bit 0 of the status byte as busy. `0x05`, `0x06`, `0x02`, and `0x03` stay in the core ideas.

After MOSI and MISO are swapped, the three bytes do not match `0xEF 0x40 0x17`. That is the failure path on the key figure. While chip select stays low, the next command is glued to the previous one. A Transmit that never reads MISO leaves a stale byte for the next read. CPHA on the second edge shifts the byte. The stuck chip select and `BR=000` at 36 MHz stay in the margin.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-08-spi-jedec.svg" width="760" alt="Mode 0 at divide-by-8 is 9 MHz; the three bytes after 0x9F are 0xEF, 0x40, and 0x17; swapping MOSI and MISO makes them miss">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48. Pin 14 PA4 = CS (push-pull, low during the transaction), pin 15 PA5 = SCK, pin 16 PA6 = MISO, pin 17 PA7 = MOSI. CPOL = 0, CPHA = 0, BR=010, SCK = 9 MHz. On the normal path MOSI sends 0x9F and then three 0xFF bytes; rx[1] through rx[3] are 0xEF, 0x40, and 0x17. The failure path swaps PA6 and PA7. In the margin, a PA4 that stays low glues two transactions, and BR=000 makes SCK = 36 MHz. Pin 14 is not drawn as DAC. Sources: [RM0008 Rev 21 section 25.5.1](#source-rm0008-spi) and [DS5319 Rev 20 Table 5](#source-ds5319-spi).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/spi-jedec.gif" width="640" alt="Chip select falls, 0x9F shifts out, then 0xEF, 0x40, and 0x17 shift in">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the normal path and marks 9 MHz. Print uses the static figure. The swapped wires and 36 MHz are not on this GIF.</sub>
</p>

The opening `spi-transfer.svg` stays a side figure. Without playing it, the pins, 9 MHz, and the three ID bytes are all on the static figure.

## Timing or state

| Row | Byte | MOSI | MISO | CS | SCK |
| --- | --- | --- | --- | --- | --- |
| Normal | 1 | 0x9F | rx[0], not the manufacturer id | low | sample on the rising edge |
| Normal | 2 | 0xFF | 0xEF | low | sample on the rising edge |
| Normal | 3 | 0xFF | 0x40 | low | sample on the rising edge |
| Normal | 4 | 0xFF | 0x17 | low | sample on the rising edge |
| End | — | — | — | returns high | idle low |
| Mode | — | — | — | — | CPOL = 0, CPHA = 0 |
| Rate | — | — | — | — | BR=010 is 9 MHz, BR=001 is 18 MHz, BR=000 is 36 MHz |
| Failure | 2 through 4 | — | not 0xEF 0x40 0x17 | low | PA6 and PA7 swapped |

The page is 256 bytes. Sources: [RM0008](#source-rm0008-spi) and the [example](#source-project-examples).

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The ID that comes back is not 0xEF4017 | PA7 is not MOSI, or PA6 is not MISO, or the mode is not 0 | Keep Mode 0, and check that PA7 is MOSI and PA6 is MISO | [DS5319](#source-ds5319-spi) | LQFP48 pin 16 is MISO and pin 17 is MOSI. The three bytes themselves are the next row |
| rx[0] was treated as the manufacturer id | The eight SCK edges of the command also shift rx[0] in | The manufacturer id is rx[1], the type is rx[2], and the capacity is rx[3] | [example](#source-project-examples) | The command is 0x9F. The three bytes are 0xEF, 0x40, and 0x17. 0x40 is not the capacity. The page is 256 bytes |
| SCK runs at 36 MHz | BR was written as 000 | Use BR 010, which is 9 MHz | [RM0008](#source-rm0008-spi) | Among the eight dividers, 010 is ÷8. 000 is ÷2 = 36 MHz. There is no ÷3 |
| Two commands are glued together | PA4 stayed low | Drive PA4 high at the end of each transaction | [DS5319](#source-ds5319-spi) | Pin 14 is SPI1_NSS. This chapter uses it as a push-pull chip select. On the C8 it is not a DAC output |
| The ID shows up on PB3/PB4/PB5 | A remap was treated as the reset default | The reset-default pins are PA5/PA6/PA7 | [DS5319](#source-ds5319-spi) | Pin 15 is SCK, pin 16 is MISO, and pin 17 is MOSI |
| Bit 0 of the status byte is treated as a protocol busy flag | That is what the example does | Wait on that bit only as the example does | [example](#source-project-examples) | The example treats bit 0 of the status byte as busy |

```

四块里不要写 `0x3A`，不要写 4.7 kΩ，不要写 SPI 基址。

- [ ] **Step 5: 追加两个来源对象**

规则与 Task 5 的 Step 5 相同。`scope` 用本任务测试里的 `scopes`。罗盘改成 `["rm0008", "project-examples", "rm0008-spi", "ds5319-spi"]`。不要改 `project-examples` 的任何字段。若 Task 2 改过 `rm0008-spi` 的 snapshot，manifest 的 snapshot 跟清单走，并在实施 PR 说明里写明 BR 差异。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3SpiChapterTests -v`

Expected: OK。

```bash
git diff --name-only -- examples/spi-flash
```

Expected: 无输出。

```bash
git add docs/08-SPI总线.md docs/en/08-spi.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch3_chapters.py
git commit -m "book: 加厚第 08 章并写上 9 MHz 与 0xEF4017"
```

### Task 8: Thicken chapter 09 in both languages

**Files:**
- Modify: `docs/09-ADC与DAC.md`
- Modify: `docs/en/09-adc-dac.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `rm0008-adc`、`ds5319-adc`；`09-ADC与DAC.md` 的 `sources` 改为 `["rm0008", "ds5319", "rm0008-adc", "ds5319-adc"]`）
- Modify: `stm32-book/manifest-en.json`（`09-adc-dac.md` 的 `sources` 与中文数组相同）
- Modify: `docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json`（只有第 11 章印出了 R_ADC 和 C_ADC 才改 `rm0008-adc` 的 snapshot）
- Modify: `stm32-book/tests/test_batch3_chapters.py`
- Modify: `stm32-book/tests/test_batch3_sources.py`（只有 snapshot 写进了印出的常数，才把「不含 pF」改成「含印出的数」）
- Test: `stm32-book/tests/test_batch3_chapters.py`

**Interfaces:**
- Consumes: `rm0008-adc`、`ds5319-adc`，以及 `assets/diagrams/sample-09-adc-sar.svg`、`assets/gif/adc-sample.gif`。Task 5 的 `baseline_manifests()`。Task 2 对第 11 章的核对结果。
- Produces: 四块各一次。正文不再有 `F1 只有 1 个 ADC` 或 `only one ADC`。不再有 `about VREF/2` 或 `约 VREF/2`。四块里不出现 `CNDTR`。`examples/adc-dma/` 的 diff 为空。`sar-adc.gif` 的像素与基线相同。

- [ ] **Step 1: 把章节断言加进测试**

```python
class Batch3AdcChapterTests(unittest.TestCase):
    def test_adc_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "09-ADC与DAC.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "09-adc-dac.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertNotIn("F1 只有 1 个 ADC", zh)
        self.assertNotIn("only one ADC", en)
        self.assertNotIn("约 VREF/2", zh)
        self.assertNotIn("about VREF/2", en)
        for text in (zh, en):
            for token in (
                "12 MHz",
                "14 MHz",
                "18 MHz",
                "21 µs",
                "4096",
                "239.5",
                "12.5",
                "252",
                "17.1",
                "125 ns",
                "2048",
                "1.65",
                "VDDA",
                "PA0",
                "ADC1",
                "ADC2",
                "205.2",
                "5.958",
                "#source-rm0008-adc",
                "#source-ds5319-adc",
            ):
                self.assertIn(token, text)
        self.assertIn("没有 DAC", zh)
        self.assertIn("no DAC", en)
        self.assertIn("第 9 脚", zh)
        self.assertIn("第 10 脚", zh)
        self.assertIn("pin 9", en)
        self.assertIn("pin 10", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        self.assertNotIn("CNDTR", zh_blocks)
        self.assertNotIn("CNDTR", en_blocks)
        self.assertIn("../assets/diagrams/sample-09-adc-sar.svg", zh)
        self.assertIn("../../assets/diagrams/sample-09-adc-sar.svg", en)
        self.assertIn("../assets/gif/adc-sample.gif", zh)
        self.assertIn("../../assets/gif/adc-sample.gif", en)
        self.assertIn("../assets/animations/adc-sar.svg", zh)
        self.assertIn("../assets/gif/sar-adc.gif", zh)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-09-adc-sar.svg"), zh_key.index("adc-sample.gif"))
        self.assertLess(en_key.index("sample-09-adc-sar.svg"), en_key.index("adc-sample.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        listed = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-adc": (
                "第 09 章原理与边界、时序或状态、坑与出处卡。转换时间 = 采样 + 12.5。12 MHz 下 252 周期是 21 µs，1.5 周期是 125 ns。17.1 µs 在 12 MHz 上是 205.2 个周期，通道是 ADC1 输入 16。VREFINT 是 ADC1 输入 17。双 ADC 器件上 TSVREFE 只在 ADC1。ADC2 的 16 和 17 接到 VSS。第 11.4 节：CAL 之前 ADON 已为 1 至少两个 ADC 时钟。1 µs 那个例子是 14 MHz 上的。不写 F4 的 TS_CAL1 或 VREFINT_CAL。",
                "Chapter 09 principle, timing, and source cards. Conversion time is the sample time plus 12.5 cycles. At 12 MHz, 252 cycles is 21 µs and 1.5 cycles is 125 ns. 17.1 µs is 205.2 cycles at 12 MHz, on ADC1 input 16. VREFINT is ADC1 input 17. On a dual-ADC device TSVREFE is only in ADC1. ADC2 inputs 16 and 17 are tied to VSS. Section 11.4: ADON has been 1 for at least two ADC clocks before CAL. The 1 µs example is at 14 MHz. Does not import F4 TS_CAL1 or VREFINT_CAL.",
            ),
            "ds5319-adc": (
                "第 09 章原理与边界和坑与出处卡。中密度有两个 12 位 ADC。STM32F103C8 有 ADC1 和 ADC2，没有 ADC3，没有 DAC。LQFP48 第 10 脚 PA0 是 ADC12_IN0，第 9 脚 VDDA 是参考。第 14 脚不是 DAC_OUT1。不改 ds5319-gpio，也不改第 03 章的 LED 图。",
                "Chapter 09 principle and source cards. Medium-density devices have two 12-bit ADCs. STM32F103C8 has ADC1 and ADC2, and it has no ADC3 and no DAC. LQFP48 pin 10 PA0 is ADC12_IN0, and pin 9 VDDA is the reference. Pin 14 is not DAC_OUT1. Does not change ds5319-gpio and does not change the chapter 03 LED figure.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["rm0008", "ds5319", "rm0008-adc", "ds5319-adc"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["09-ADC与DAC.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["09-adc-dac.md"]["sources"])
        for source_id, (scope_zh, scope_en) in scopes.items():
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual("2026-10-25", card_zh["accessed"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        baseline, _baseline_en = baseline_manifests()
        for source_id, obj in baseline["sources"].items():
            self.assertEqual(obj, zh_manifest["sources"][source_id])
        self.assertIn("rm0008-adc", zh_manifest["sources"])
        self.assertIn("ds5319-adc", zh_manifest["sources"])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch3_chapters.py Batch3AdcChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 改 ADC 个数、换算注释，并把 14 MHz 的采样档改成 12 MHz**

中文把

```markdown
- F1 只有 1 个 ADC（大容量型号才有 ADC3），ADC1/2 共享 DMA1 通道 1。
```

换成

```markdown
- STM32F103C8 有 ADC1 和 ADC2，没有 ADC3，也没有 DAC。这颗料只有 DMA1，ADC1 是通道 1。半字和 CNDTR 的算术留在第 10 章。
```

英文把

```markdown
- An F1 has only one ADC (only high-density parts have ADC3). ADC1 and ADC2 share DMA1 channel 1.
```

换成

```markdown
- An STM32F103C8 has ADC1 and ADC2. It has no ADC3 and no DAC. This part has only DMA1, and ADC1 is channel 1. Half-word and CNDTR arithmetic stays in chapter file 10.
```

中文把

```markdown
HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 2048); /* 约 VREF/2 */
```

换成

```markdown
HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 2048); /* 2048 / 4096 = 1/2，名义 3.3 V 下是 1.65 V */
```

英文把

```markdown
HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 2048); /* about VREF/2 */
```

换成

```markdown
HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 2048); /* 2048 / 4096 = 1/2, which is 1.65 V at a nominal 3.3 V */
```

默认走这一支：第 11 章没有同时印出 R_ADC 和 C_ADC。中文把源阻抗那张表整张换成：

```markdown
| 信号源阻抗 R_AIN | 最小采样时间 t_s（估算，不进出处卡） | 这颗料 ADCCLK = 12 MHz 的采样档 | 说明 |
| --- | --- | --- | --- |
| ≤ 1 kΩ | ≈ 78 ns | `000` = 1.5 周期（125 ns） | 运放直驱 / 分压电阻取小 |
| ≈ 10 kΩ | ≈ 0.78 µs | `010` = 13.5 周期（1.125 µs） | 常见电位器 |
| ≈ 50 kΩ | ≈ 3.9 µs | `101` = 55.5 周期（4.625 µs） | 高阻传感器 |
| ≈ 100 kΩ | ≈ 7.8 µs | `111` = 239.5 周期（19.958 µs） | 高阻时用这一档 |
| ≥ 1 MΩ | ≥ 78 µs | 239.5 周期仍不够 | **必须加电压跟随器缓冲** |
```

表下加一句：

```markdown
RM0008 在 14 MHz、采样 1.5 周期处写出的 1 µs 是上限上的例子。71.5 周期在 12 MHz 上是 5.958 µs，盖不住温度通道的 17.1 µs。和 21 µs 同一格的时间只按 12 MHz。右列对比表里 F4 的「t_s + 12 周期」在这颗料上作废。
```

英文把那张表整张换成：

```markdown
| Source impedance R_AIN | Minimum sample time t_s (an estimate, not a source card) | Sample step on this part at ADCCLK = 12 MHz | Notes |
| --- | --- | --- | --- |
| ≤ 1 kΩ | ≈ 78 ns | `000` = 1.5 cycles (125 ns) | Op-amp drive, or a small divider |
| ≈ 10 kΩ | ≈ 0.78 µs | `010` = 13.5 cycles (1.125 µs) | A typical potentiometer |
| ≈ 50 kΩ | ≈ 3.9 µs | `101` = 55.5 cycles (4.625 µs) | A high-impedance sensor |
| ≈ 100 kΩ | ≈ 7.8 µs | `111` = 239.5 cycles (19.958 µs) | Use this step for a high impedance |
| ≥ 1 MΩ | ≥ 78 µs | 239.5 cycles is still not enough | **You must add a voltage-follower buffer** |
```

表下加一句：

```markdown
The 1 µs that RM0008 prints at 14 MHz and 1.5 cycles is an example at the ceiling. 71.5 cycles is 5.958 µs at 12 MHz and does not cover the temperature channel's 17.1 µs. Times that share a cell with 21 µs use 12 MHz only. The F4 column “t_s + 12 cycles” in the comparison table is void on this part.
```

扫描时的串扰留在这张表下面，一句话，不进出处卡：

中文：`扫描时前一通道还没放完电，高阻通道会串扰。加长采样，或在序列里插入间隔。这句不进出处卡。`

英文：`During a scan, a high-impedance channel can pick up the previous channel if that capacitor has not finished discharging. Lengthen the sample, or insert a gap in the sequence. This sentence does not enter a source card.`

另一支，只有两个常数都印在第 11 章时才走：用印出的 R_ADC 和 C_ADC 代入正文已有的公式 `ts ≈ (R_AIN + R_ADC) × C_ADC × ln(2^(N+2))`，N = 12。把算出来的五格写进上表的 t_s 列，去掉「估算」二字，并在 `rm0008-adc` 的 snapshot 末尾加上印出的两个数。许可门测试里 `assertNotIn("pF", adc_snap)` 和 `assertNotIn("kΩ", adc_snap)` 改成 `assertIn` 印出的那两个数。出处卡再加一行，主张只写印出的常数和重算后的 1 kΩ 那一格。印出的数若正好是 1 kΩ 和 8 pF，1 kΩ 源阻抗那一格写成 155 ns，不是 78 ns。没印出来就不要走这一支，也不要为了凑 155 ns 去改 snapshot。

中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。不改 `examples/adc-dma/`。不改 `assets/gif/sar-adc.gif`。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch09 -->` 与 `## 📌 学习目标` 之间：

```markdown
## 原理与边界

这一章的采样结论只钉在订货号 STM32F103C8T6 上。采样时钟用附录 D 的 12 MHz。换算分母用 4096。换到有 DAC 的型号时，「这颗料没有 DAC」那一句作废。换到 F4 时，「采样再加 12.5」和上电校准那两句作废。

PCLK2 = 72 MHz，`ADCPRE=10`（÷6）得到 ADCCLK = 12 MHz。÷4 得到 18 MHz，越过 14 MHz。分频位的句子交叉引用第 02 章，这一章不重画时钟树。RM0008 在 14 MHz、采样 1.5 周期处给出 `Tconv = 1 µs`。那是上限上的例子。这颗料的工作点是 12 MHz。四块里不把 1 µs 和 21 µs 写进同一格。出处是 [RM0008 Rev 21 第 11 章](#source-rm0008-adc)。

采样开关合上时，输入经源阻抗给采样电容充电。开关断开后电容上的电压被保持。然后从 MSB 开始比较 12 次。转换时间是采样周期再加上 12.5 个 ADCCLK。最长采样档 239.5 再加 12.5 等于 252 个周期，`252 / 12e6 = 21 µs`。在 12 MHz 上：1.5 周期 = 125 ns，13.5 周期 = 1.125 µs，55.5 周期 = 4.625 µs，71.5 周期 = 5.958 µs，239.5 周期 = 19.958 µs。F4 的「采样再加 12 个周期」在这颗料上作废。

温度传感器的推荐采样时间是 17.1 µs。`17.1e-6 × 12e6 = 205.2` 个周期，所以 239.5 周期盖得住，71.5 周期盖不住。通道是 ADC1 的输入 16。VREFINT 是 ADC1 的输入 17，正文保持「约 1.20 V」，不编一块板子上的实测 VDDA。TSVREFE 在 `ADC_CR2`，双 ADC 器件上这一位只在 ADC1。ADC2 的通道 16 和 17 接到 VSS。温度公式是 `(V25 − VSENSE) / Avg_Slope + 25`。V25 ≈ 1.43 V、斜率 ≈ 4.3 mV/°C 标成电气特性里的典型值，不是保证的校准。F4 的 `TS_CAL1`、`TS_CAL2`、`VREFINT_CAL` 在 F103C8 上作废。

DS5319 写明中密度器件都有两个 12 位 ADC。C8 有 ADC1 和 ADC2，没有 ADC3，没有 DAC。`HAL_DAC_Start` 在这颗料上落空。高密度 F103 和 F4 才有 DAC。DAC 的缓冲器、噪声和三角波留在核心原理，并写明换到有 DAC 的型号才成立。出处是 [DS5319 Rev 20](#source-ds5319-adc)。

LQFP48 第 10 脚 PA0 = ADC12_IN0，第 9 脚 VDDA 就是参考。这一封装没有单独的 VREF+。100 脚及以上才有单独的 VREF+ / VREF−，C8 用不到。第 10 脚在第 03 章是 LED 的电流脚；本图把它画成模拟输入时，点灯那条「写 1 输出电流」同时作废。不重画 `sample-03-gpio-led.svg`。第 14 脚 PA4 在 C8 上是 ADC12_IN4 / SPI1_NSS，不是 DAC_OUT1。把 DAC 画在第 14 脚上是失败旁注。

电压 = 码 × VDDA / 4096。名义 3.3 V 时 1 LSB = `3.3 / 4096 ≈ 0.806` mV，和章内 806 µV 那一格同一笔。码 2048 是 `2048 / 4096 = 1/2`，名义 3.3 V 下正好 1.65 V。分母用 4095 会偏一个 LSB。

RM0008 第 11.4 节：上电后做一次校准。置 `ADC_CR2` 的 CAL 之前，ADON 已经为 1 至少两个 ADC 时钟。HAL 侧是 `HAL_ADCEx_Calibration_Start`，放在 Start 之前。F4 没有这一步，那句在换系列时作废。

DMA 只交叉引用第 10 章和附录 D：这颗料只有 DMA1，ADC1 是通道 1。不把半字和「已写 5 个采样」的算术搬进这一章。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-09-adc-sar.svg" width="760" alt="这颗料的 ADC 时钟是 12 MHz，最长转换 21 µs；采样太短时电容上仍是上一次的电压">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48 第 10 脚 PA0 = ADC12_IN0，第 9 脚 VDDA 为参考。ADCCLK = 12 MHz。正常路径采样开关闭合再断开，比较器做 MSB 那一次，最长一档 239.5 + 12.5 = 21 µs，码值乘 VDDA / 4096。失败路径是采样太短，电容上仍是上一次的电压。旁注：÷4 得到 18 MHz，越过 14 MHz；第 14 脚被画成 DAC 时，C8 上没有这只脚的 DAC。不把第 03 章的 LED 电阻画进来。出处是 [RM0008 Rev 21 第 11 章](#source-rm0008-adc) 和 [DS5319 Rev 20 图 8](#source-ds5319-adc)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/adc-sample.gif" width="640" alt="一次采样之后做 MSB 比较，ADCCLK 是 12 MHz">
  <br><sub>▲ 网页和公众号辅图。只播放一次成功的采样和 MSB。印刷以静态主图为准。采样过短和 18 MHz 不在这条 GIF 上。</sub>
</p>

章首的 `adc-sar.svg` 留作辅图。`sar-adc.gif` 留在原节，不替换像素。

## 时序或状态

| 行 | 采样周期数 | 采样时间 | 加 12.5 之后 |
| --- | --- | --- | --- |
| 最短 | 1.5 | 125 ns | 14 / 12e6 |
| 最长 | 239.5 | 19.958 µs | 252 / 12e6 = 21 µs |
| 温度 | 239.5，不用 71.5 | 17.1 µs 需要 205.2 个周期 | 71.5 周期只有 5.958 µs，盖不住 |
| 失败 | — | — | ADCCLK = 18 MHz，越过 14 MHz。这一行不再除出另一套微秒去和 21 µs 并列 |
| 换算 | — | — | 码 2048 在名义 3.3 V 下是 1.65 V，分母 4096 |

时钟是 12 MHz。出处是 [RM0008 Rev 21 第 11 章](#source-rm0008-adc)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 读数还停在上一次的电压附近 | 采样时间按错了时钟 | 按 12 MHz 加长采样。高阻时用 239.5 周期 | [RM0008](#source-rm0008-adc) | 转换时间 = 采样 + 12.5。12 MHz 下最长 252 周期是 21 µs |
| 为了更快把 ADC 设成 ÷4 | ADCPRE 选成了 ÷4 | 改回 ÷6，12 MHz | [RM0008](#source-rm0008-adc) | 14 MHz 是上限。18 MHz 越过它。1 µs 那个例子是 14 MHz 上的，不是这颗料的工作点 |
| 温度通道噪声大、读数飘 | 采样盖不住 17.1 µs，或通道开错了 | 采样至少覆盖 17.1 µs，用 ADC1 通道 16，并置 TSVREFE | [RM0008](#source-rm0008-adc) | 17.1 µs 在 12 MHz 上是 205.2 个周期。VREFINT 是 ADC1 通道 17。ADC2 的 16/17 接到 VSS |
| 上电第一次整体偏移 | 没校准 | Start 之前做校准 | [RM0008](#source-rm0008-adc) | 第 11.4 节：CAL 之前 ADON 已为 1 至少两个 ADC 时钟 |
| 换算比万用表高一截 | 分母用了 4095 | 分母用 4096 | [RM0008](#source-rm0008-adc) | 12 位满量程是 4096 步。码 2048 是半满量程。参考是第 9 脚 VDDA |
| 蓝药丸上调用了 HAL_DAC_Start，PA4 没有模拟电压 | 这颗 C8 没有 DAC | 要模拟电压用 PWM 加 RC，或换有 DAC 的型号 | [DS5319](#source-ds5319-adc) | 中密度有两个 12 位 ADC。没有 ADC3，没有 DAC。第 14 脚不是 DAC_OUT1 |
| 第 10 脚点过灯，采样却像在读推挽 | 脚还停在输出 | 采样时这只脚是模拟输入，不再按第 03 章输出电流 | [DS5319](#source-ds5319-adc) | LQFP48 第 10 脚 PA0 是 ADC12_IN0。不改写第 03 章那张 LED 图 |

```

英文插在 `<!-- /video:ch09 -->` 与 `## 📌 Learning goals` 之间：

```markdown
## Principle and boundary

The sampling conclusion in this chapter is pinned to order code STM32F103C8T6. The sample clock is the 12 MHz from Appendix D. The conversion divisor is 4096. On a part that has a DAC, the sentence “this part has no DAC” is void. On an F4, the sentences “sample plus 12.5” and “calibrate after power-up” are void.

PCLK2 = 72 MHz, and `ADCPRE=10` (÷6) gives ADCCLK = 12 MHz. ÷4 gives 18 MHz and crosses 14 MHz. The prescaler sentence cross-references chapter file 02. This chapter does not redraw the clock tree. RM0008 prints `Tconv = 1 µs` at 14 MHz and 1.5 cycles. That is an example at the ceiling. This part's working point is 12 MHz. The four blocks do not put 1 µs and 21 µs in the same cell. Source: [RM0008 Rev 21 chapter 11](#source-rm0008-adc).

While the sample switch is closed, the input charges the sample capacitor through the source impedance. After the switch opens, the voltage on the capacitor is held. The converter then compares 12 times, starting at the MSB. Conversion time is the sample cycles plus 12.5 ADCCLK cycles. The longest sample step, 239.5 plus 12.5, is 252 cycles, and `252 / 12e6 = 21 µs`. At 12 MHz: 1.5 cycles = 125 ns, 13.5 cycles = 1.125 µs, 55.5 cycles = 4.625 µs, 71.5 cycles = 5.958 µs, and 239.5 cycles = 19.958 µs. The F4 sentence “sample plus 12 cycles” is void on this part.

The recommended sample time for the temperature sensor is 17.1 µs. `17.1e-6 × 12e6 = 205.2` cycles, so 239.5 cycles covers it and 71.5 cycles does not. The channel is ADC1 input 16. VREFINT is ADC1 input 17. The prose keeps “about 1.20 V” and does not invent a measured VDDA for one board. TSVREFE is in `ADC_CR2`. On a dual-ADC device that bit is only in ADC1. ADC2 channels 16 and 17 are tied to VSS. The temperature formula is `(V25 − VSENSE) / Avg_Slope + 25`. V25 ≈ 1.43 V and the slope ≈ 4.3 mV/°C are typical values from the electrical characteristics, not a guaranteed calibration. F4 `TS_CAL1`, `TS_CAL2`, and `VREFINT_CAL` are void on F103C8.

DS5319 says every medium-density device has two 12-bit ADCs. The C8 has ADC1 and ADC2. It has no ADC3 and no DAC. `HAL_DAC_Start` does nothing useful on this part. A DAC exists on high-density F103 parts and on F4. The DAC buffer, noise, and triangle wave stay in the core ideas, and they hold only after you change to a part that has a DAC. Source: [DS5319 Rev 20](#source-ds5319-adc).

LQFP48 pin 10 PA0 = ADC12_IN0, and pin 9 VDDA is the reference. This package has no separate VREF+. Packages with 100 pins and up have separate VREF+ / VREF−, and the C8 does not use that sentence. Pin 10 is the LED current pin in chapter file 03. When this figure draws it as an analog input, the chapter 03 sentence “write 1 to source current” is void at the same time. Do not redraw `sample-03-gpio-led.svg`. Pin 14 PA4 on the C8 is ADC12_IN4 / SPI1_NSS, not DAC_OUT1. Drawing a DAC on pin 14 is a failure note in the margin.

Voltage = code × VDDA / 4096. At a nominal 3.3 V, 1 LSB = `3.3 / 4096 ≈ 0.806` mV, the same cell as the 806 µV already in the chapter. Code 2048 is `2048 / 4096 = 1/2`, which is exactly 1.65 V at a nominal 3.3 V. A divisor of 4095 is off by one LSB.

RM0008 section 11.4: calibrate once after power-up. Before setting CAL in `ADC_CR2`, ADON has already been 1 for at least two ADC clocks. On the HAL side that is `HAL_ADCEx_Calibration_Start`, placed before Start. An F4 does not have this step, and that sentence is void when the family changes.

DMA is only a cross-reference to chapter file 10 and Appendix D: this part has only DMA1, and ADC1 is channel 1. Do not move the half-word or the “5 samples already written” arithmetic into this chapter.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-09-adc-sar.svg" width="760" alt="On this part the ADC clock is 12 MHz and the longest conversion is 21 µs; a sample that is too short leaves the previous voltage on the capacitor">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48 pin 10 PA0 = ADC12_IN0, pin 9 VDDA is the reference. ADCCLK = 12 MHz. The normal path closes the sample switch and then opens it, and the comparator takes the MSB step. The longest step is 239.5 + 12.5 = 21 µs, and the code is multiplied by VDDA / 4096. The failure path is a sample so short that the capacitor still holds the previous voltage. In the margin, ÷4 produces 18 MHz and crosses 14 MHz; a DAC drawn on pin 14 does not exist on the C8. The chapter 03 LED resistor is not on this figure. Sources: [RM0008 Rev 21 chapter 11](#source-rm0008-adc) and [DS5319 Rev 20 Figure 8](#source-ds5319-adc).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/adc-sample.gif" width="640" alt="One sample, then the MSB compare, with ADCCLK at 12 MHz">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays one successful sample and the MSB. Print uses the static figure. The short sample and 18 MHz are not on this GIF.</sub>
</p>

The opening `adc-sar.svg` stays a side figure. `sar-adc.gif` stays in its original section. Its pixels are not replaced.

## Timing or state

| Row | Sample cycles | Sample time | After adding 12.5 |
| --- | --- | --- | --- |
| Shortest | 1.5 | 125 ns | 14 / 12e6 |
| Longest | 239.5 | 19.958 µs | 252 / 12e6 = 21 µs |
| Temperature | 239.5, not 71.5 | 17.1 µs needs 205.2 cycles | 71.5 cycles is only 5.958 µs and does not cover it |
| Failure | — | — | ADCCLK = 18 MHz, which crosses 14 MHz. This row is not divided again into a second set of microseconds beside 21 µs |
| Conversion | — | — | Code 2048 is 1.65 V at a nominal 3.3 V, divisor 4096 |

The clock is 12 MHz. Source: [RM0008 Rev 21 chapter 11](#source-rm0008-adc).

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The reading is still near the previous voltage | The sample time used the wrong clock | Lengthen the sample at 12 MHz. Use 239.5 cycles for a high impedance | [RM0008](#source-rm0008-adc) | Conversion time = sample + 12.5. At 12 MHz the longest 252 cycles is 21 µs |
| ADC was set to ÷4 to go faster | ADCPRE selected ÷4 | Change it back to ÷6, 12 MHz | [RM0008](#source-rm0008-adc) | 14 MHz is the ceiling. 18 MHz crosses it. The 1 µs example is at 14 MHz, not this part's working point |
| The temperature channel is noisy and the reading wanders | The sample does not cover 17.1 µs, or the channel is wrong | Cover at least 17.1 µs, use ADC1 channel 16, and set TSVREFE | [RM0008](#source-rm0008-adc) | 17.1 µs is 205.2 cycles at 12 MHz. VREFINT is ADC1 channel 17. ADC2 inputs 16 and 17 are tied to VSS |
| The first reading after power-up is shifted as a whole | There was no calibration | Calibrate before Start | [RM0008](#source-rm0008-adc) | Section 11.4: ADON has been 1 for at least two ADC clocks before CAL |
| The converted voltage reads higher than the meter | The divisor was 4095 | Use 4096 | [RM0008](#source-rm0008-adc) | A 12-bit full scale is 4096 steps. Code 2048 is half of full scale. The reference is pin 9 VDDA |
| HAL_DAC_Start on a Blue Pill leaves no analog voltage on PA4 | This C8 has no DAC | For an analog voltage use PWM plus an RC, or change to a part that has a DAC | [DS5319](#source-ds5319-adc) | Medium-density devices have two 12-bit ADCs. There is no ADC3 and no DAC. Pin 14 is not DAC_OUT1 |
| Pin 10 used to light an LED, and the sample looks like a push-pull read | The pin is still an output | While sampling, this pin is an analog input and no longer sources the chapter 03 current | [DS5319](#source-ds5319-adc) | LQFP48 pin 10 PA0 is ADC12_IN0. Do not rewrite the chapter 03 LED figure |

```

1 kΩ 和 8 pF 只有在 snapshot 写进了印出的常数之后，才在这张表下面再加一行阻抗主张。没写进 snapshot，就不加这一行。四块里不要写 `CNDTR`。

- [ ] **Step 5: 追加两个来源对象**

规则与 Task 5 的 Step 5 相同。`scope` 用本任务测试里的 `scopes`。罗盘改成 `["rm0008", "ds5319", "rm0008-adc", "ds5319-adc"]`。`snapshot` 跟清单走。若走了印出常数那一支，清单、manifest 和许可门测试在同一笔提交里一起改。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch3_chapters.py -v`

Expected: OK。`Batch3FigureTests`、`Batch3GifTests` 和三个已经加厚的章节测试仍然通过。

Run: `python3 stm32-book/tests/test_batch3_sources.py -v`

Expected: OK。

```bash
git diff --name-only -- examples/adc-dma assets/gif/sar-adc.gif
```

Expected: 无输出。

```bash
git add docs/09-ADC与DAC.md docs/en/09-adc-dac.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch3_chapters.py stm32-book/tests/test_batch3_sources.py docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json
git commit -m "book: 加厚第 09 章并改成 12 MHz 下的 21 µs"
```

清单没有差异时，提交里可以不带它。不要把 `sar-adc.gif` 加进来。

### Task 9: Register the batch, bump 1.2.2, keep the ledgers

**Files:**
- Modify: `CREDITS.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `version` 与 `date`
- Modify: `stm32-book/revisions.json`
- Modify: `stm32-book/README.md`
- Modify: `stm32-book/tests/test_build.py`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 5 到 Task 8 已经写进 manifest 的八个新 id。日期是 `2026-10-25`，不另取。
- Produces: 两份 manifest 的 `version` 都是 `1.2.2`，`date` 都是 `2026-10-25`。`revisions.json` 的 `entries[0].version` 是 `1.2.2`，`entries[1]` 仍是现在的 1.2.1 指南说明。`test_build.py` 里当前版从 `1.2.1` 改为 `1.2.2`。`0x271` 断言、`167 ns` 断言和出版书签长度 44 的断言还在。

- [ ] **Step 1: 先改版本断言，让测试失败**

在 `stm32-book/tests/test_build.py` 里只改当前版断言。不要删 `0x271`、`167 ns`、`会上手的几笔账`、`Numbers to reconcile before changing family`、`Channels, descriptors, and fault registers`，也不要改 `self.assertEqual(44, len(outline))`。

把

```python
versions = ("1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

改成

```python
versions = ("1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

在 `self.assertLess(history.index(">1.2.1<"), history.index(">1.2.0<"))` 之前加一行：

```python
self.assertLess(history.index(">1.2.2<"), history.index(">1.2.1<"))
```

把修订列表的期望从

```python
["1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

改成

```python
["1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

把 `self.assertEqual("1.2.1", manifest["version"])` 改成 `self.assertEqual("1.2.2", manifest["version"])`。

把两处 `self.assertIn("<strong>v1.2.1</strong>", html)` 改成 `self.assertIn("<strong>v1.2.2</strong>", html)`。

`test_visual_polish_version_is_1_2_0` 改成核对当前条目是 1.2.2。把函数体里取条目的三行换成：

```python
        entry = revisions["entries"][0]
        guide = revisions["entries"][1]
        previous = revisions["entries"][2]
```

把 `self.assertEqual("1.2.1", self.manifest["version"])` 改成 `self.assertEqual("1.2.2", self.manifest["version"])`。英文 manifest 和 `entry["version"]` 同样改成 `1.2.2`。`entry["date"]` 仍是 `2026-10-25`。

现在对 `entry["zh"]` 和 `entry["en"]` 的两句指南说明，改去核对 `guide`：

```python
        self.assertEqual("1.2.1", guide["version"])
        self.assertEqual(
            [
                "贡献指南把大典四块写成每章必选，放在视频块之后、学习目标之前。",
                "旧的常见坑与排查迁入坑与出处卡，并用 `#source-` 链到附录 E。这一版不改正文章。",
            ],
            guide["zh"],
        )
        self.assertEqual(
            [
                "The contributor guide requires the four compendium sections after the video block and before the learning goals.",
                "The old pitfalls section moves into Pitfalls and source cards, with `#source-` links to Appendix E. This edition does not rewrite chapter prose.",
            ],
            guide["en"],
        )
```

`entry` 的中英改成：

```python
        self.assertEqual(
            [
                "第 02 章把 CFGR 改回第 7.3.2 节，并写上 72 MHz 要 2 个等待、CSS 回到 HSI。第 05 章写上 1 kHz 和 500 Hz 两条路径。",
                "第 08 章写上 Mode 0、9 MHz，以及 0x9F 之后的 0xEF、0x40、0x17。第 09 章写上 12 MHz 下的 21 µs、除以 4096，以及 C8 有 ADC1/ADC2、没有 DAC。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 02 moves CFGR back to section 7.3.2, with two Flash wait states at 72 MHz and CSS falling back to HSI. Chapter file 05 records both the 1 kHz path and the 500 Hz path.",
                "Chapter file 08 records Mode 0 at 9 MHz and, after 0x9F, the bytes 0xEF, 0x40, and 0x17. Chapter file 09 records 21 µs at 12 MHz, division by 4096, and that the C8 has ADC1 and ADC2 and no DAC.",
            ],
            entry["en"],
        )
```

`previous` 仍核对 1.2.0 的那两句观感说明，断言原文不动，只是对象从 `entries[1]` 换成 `entries[2]`。

README 断言改成：

```python
        self.assertIn("当前版本：**v1.2.2 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.2。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2。", readme)
        self.assertIn("打 tag `v1.2.2`", readme)
        self.assertNotIn("当前版本：**v1.2.1", readme)
        self.assertNotIn("打 tag `v1.2.1`", readme)
```

- [ ] **Step 2: 运行版本测试，确认失败**

Run: `python3 stm32-book/tests/test_build.py BookBuildTests.test_revision_file_lists_1_0_0_through_manifest_version -v`

Expected: FAIL，修订列表的首项仍是 `1.2.1`。

- [ ] **Step 3: 写 1.2.2**

两份 manifest 的 `version` 改为 `1.2.2`，`date` 改为 `2026-10-25`。不要改 `sources` 里已有对象的字段。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入：

```json
{
  "version": "1.2.2",
  "date": "2026-10-25",
  "zh": [
    "第 02 章把 CFGR 改回第 7.3.2 节，并写上 72 MHz 要 2 个等待、CSS 回到 HSI。第 05 章写上 1 kHz 和 500 Hz 两条路径。",
    "第 08 章写上 Mode 0、9 MHz，以及 0x9F 之后的 0xEF、0x40、0x17。第 09 章写上 12 MHz 下的 21 µs、除以 4096，以及 C8 有 ADC1/ADC2、没有 DAC。"
  ],
  "en": [
    "Chapter file 02 moves CFGR back to section 7.3.2, with two Flash wait states at 72 MHz and CSS falling back to HSI. Chapter file 05 records both the 1 kHz path and the 500 Hz path.",
    "Chapter file 08 records Mode 0 at 9 MHz and, after 0x9F, the bytes 0xEF, 0x40, and 0x17. Chapter file 09 records 21 µs at 12 MHz, division by 4096, and that the C8 has ADC1 and ADC2 and no DAC."
  ]
}
```

修订说明只写这四章，用文件名前缀，不写尚未加厚的章，不把标题写成「第 3 章」。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.2.2 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

把「发布 GitHub Release」一节里这一句：

```markdown
版本号已经是 1.2.1。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0，也不要把 1.2.0 的产物标成 1.2.1。
```

换成：

```markdown
版本号已经是 1.2.2。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0，也不要把 1.2.0 的产物标成 1.2.1，也不要把 1.2.1 的产物标成 1.2.2。
```

第三步的「在该提交上打 tag `v1.2.1`」改成「在该提交上打 tag `v1.2.2`」。这一步仍不创建 tag，也不创建 Release。前面的 artifact 名称和四份文件名保持不动。

- [ ] **Step 4: 在 CREDITS.md 增加 v1.2.2 小节，并改正张数**

第一节表格里这一行：

```markdown
| 静态框图（10 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |
```

换成：

```markdown
| 静态框图（14 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |
```

这一行现在写着 6 个 GIF，数的是 Batch2 之前的生成器。`BUILDERS` 在本任务之前已经有 8 个键，本批再加 4 个，一共 12 个。把

```markdown
| 光栅动画（6 个 GIF） | `assets/gif/` | **本仓库作者用纯 Python 渲染并手写 GIF 编码器生成**，脚本见 `tools/minigfx.py`、`tools/gen_gifs.py` |
```

换成：

```markdown
| 光栅动画（12 个 GIF） | `assets/gif/` | **本仓库作者用纯 Python 渲染并手写 GIF 编码器生成**，脚本见 `tools/minigfx.py`、`tools/gen_gifs.py` |
```

不要重跑已有 8 个 GIF。12 是 `BUILDERS` 的键数，不是 `*-zh.gif` 的张数。

第六节「样本章的改写吸收（v1.1.0）」和「第 04 章与第 06 章（v1.1.1）」的标题和表都保留。在该节末尾追加：

```markdown
### 第 02、05、08、09 章（v1.2.2）

第 02、05、08、09 章用改写吸收补了同样的四块。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图和厂商数据手册不放进仓库。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| RM0008 Rev 21（2021-02），中密度第 7.2 节、第 7.2.7 节、第 7.3.2 节，第 15 章，第 25.5.1 节，第 11 章与第 11.4 节 | ST 文档条款；只链接并改写事实，不转载手册 | 第 02 章 72 MHz、2 个等待和 CSS；第 05 章 1 kHz 与 MOE；第 08 章 Mode 0 与 9 MHz；第 09 章 12 MHz 下的 21 µs 和校准 | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| DS5319 Rev 20（2025-07），图 8 与表 5 | ST 文档条款；只链接并改写事实，不转载手册 | 第 02 章第 5、6、29 脚；第 05 章第 16 脚 PA6；第 08 章第 14–17 脚；第 09 章第 9 脚 VDDA、第 10 脚 PA0，以及 C8 有两只 ADC、没有 DAC | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
| 本仓库 `examples/spi-flash` | MIT | 第 08 章坑卡：0x9F 之后的三字节是 0xEF、0x40、0x17，页 256 字节，状态字节位 0 在例程里当成忙 | https://github.com/zhuguang-ZFG/STM32/tree/main/examples |
```

- [ ] **Step 5: 运行整套测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。`test_sample_chapters.py` 对 00 与 03 的断言仍然通过。`test_batch2_chapters.py` 仍然通过。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。构建出的 HTML 里有 `v1.2.2`，并且 `id="source-rm0008-rcc"`、`id="source-ds5319-clock"`、`id="source-rm0008-tim"`、`id="source-ds5319-tim"`、`id="source-rm0008-spi"`、`id="source-ds5319-spi"`、`id="source-rm0008-adc"`、`id="source-ds5319-adc"` 都在。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0。

- [ ] **Step 6: Commit**

```bash
git add CREDITS.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 第 02、05、08、09 章登记来源并把整书标成 1.2.2"
```

### Task 10: Scope gate, then stop

**Files:**
- 不新增文件。这一任务只核对 diff。核对失败时，只撤销越界改动，不顺手加厚别的章。

**Interfaces:**
- Consumes: Task 1 到 Task 9 的提交。
- Produces: 一份只含第 02、05、08、09 章加厚的 diff。用户复审之前，实施 PR 保持打开。没有 tag，没有 Release。Book CI 变绿不等于可以 squash 合入。

- [ ] **Step 1: 核对 diff 的路径**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只出现这些路径。顺序可以不同。多出来的路径若是本计划自己的三份文件，也允许，它们不是章节正文。

```text
CREDITS.md
assets/README.md
assets/diagrams/sample-02-clock-tree.svg
assets/diagrams/sample-05-pwm-1khz.svg
assets/diagrams/sample-08-spi-jedec.svg
assets/diagrams/sample-09-adc-sar.svg
assets/gif/adc-sample.gif
assets/gif/clock-css.gif
assets/gif/pwm-1khz.gif
assets/gif/spi-jedec.gif
docs/02-芯片选型与存储器时钟.md
docs/05-定时器与PWM.md
docs/08-SPI总线.md
docs/09-ADC与DAC.md
docs/en/02-part-and-clock.md
docs/en/05-timer-pwm.md
docs/en/08-spi.md
docs/en/09-adc-dac.md
docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json
docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json
docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch3-02-05-08-09.md
stm32-book/README.md
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_batch3_chapters.py
stm32-book/tests/test_batch3_sources.py
stm32-book/tests/test_build.py
tools/gen_gifs.py
tools/gen_sample_figures.py
tools/scan_batch3_chapters.py
```

`docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch3-02-05-08-09.md` 只在「先合并了本计划」的历史上出现。若实施分支从本计划提交切开，它会留在 diff 里，这是允许的。它不是章节正文。

`stm32-book/build_html.py`、`stm32-book/book/`、`docs/CONTENT_GUIDE.md`、`docs/en/CONTENT_GUIDE.md`、样本锁定、Batch2 锁定，以及其余章节都不在这份列表里。

- [ ] **Step 2: 核对附录、构建脚本、第 01 章和第 07 章没有被卷进来**

Run:

```bash
git diff origin/main...HEAD -- stm32-book/build_html.py stm32-book/book/A-工程深读.md stm32-book/book/D-术语表.md stm32-book/book/en/A-uart-dma.md stm32-book/book/en/D-glossary.md docs/01-开发环境搭建.md docs/07-I2C总线.md docs/en/01-dev-environment.md docs/en/07-i2c.md
```

Expected: 无输出。

Run:

```bash
git diff --name-only origin/main...HEAD -- docs/00-如何学习STM32.md docs/03-GPIO与LED.md docs/04-中断与NVIC.md docs/06-串口UART.md docs/en/00-how-to-learn-stm32.md docs/en/03-gpio-and-led.md docs/en/04-interrupts-nvic.md docs/en/06-uart.md assets/gif/sar-adc.gif assets/diagrams/sample-03-gpio-led.svg
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

Expected: 四条命令都退出码 0。

- [ ] **Step 4: 确认没有 tag 和 Release**

Run: `git tag --points-at HEAD`

Expected: 无输出。

不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.1` 或 `v1.2.2`。

- [ ] **Step 5: 停在用户复审**

实施 PR 的说明里写明：只加厚了文件 `02`、`05`、`08`、`09` 的中英八份；静态主图是 `sample-02-clock-tree.svg`、`sample-05-pwm-1khz.svg`、`sample-08-spi-jedec.svg`、`sample-09-adc-sar.svg`；短 GIF 是辅图。第 02 章的 CFGR 是第 7.3.2 节。第 05 章 72 MHz 下是 1000 Hz，36 MHz 去除是 500 Hz。第 08 章 Mode 0、9 MHz，`0x9F` 之后是 `0xEF`、`0x40`、`0x17`。第 09 章 12 MHz 下最长 21 µs，分母 4096，C8 有 ADC1 和 ADC2、没有 DAC。若第 25.5.1 节的 BR 编码或第 11 章的 R_ADC / C_ADC 和清单不同，说明里写明差异。

请用户看构建出的中英 HTML 里的这四章：四块是否都在、关掉动画之后主图是否仍能指出失败、`#source-` 是否点得到附录 E 的卡片。

第 02 章要能指出的失败是「72 MHz 时 LATENCY 仍为 0」。第 05 章要能指出的失败是「用 36 MHz 去除，1 kHz 变成 500 Hz」。第 08 章要能指出的失败是「PA6 与 PA7 对调，读不到 0xEF 0x40 0x17」。第 09 章要能指出的失败是「采样太短，电容上仍是上一次的电压」。

用户书面接受之前：

- 不为 `00`、`01`、`03`、`04`、`06`、`07`、`10`–`28` 开加厚 PR。
- 不加图目录或表目录。
- 不改 `stm32-book/build_html.py`，不改显示章号，不改 PDF 书签深度。
- 不打 `v1.2.2` 的 tag，不创建 GitHub Release。
- 不把 Book CI 变绿当成可以自动 squash 合入。人接受之前，实施 PR 保持打开。
- 不预选文件 `01` 或 `07` 作为下一批。下一批仍是 4 章，到下一次设计再锁。

这一步没有新的提交。若 Step 1 到 Step 3 发现越界文件，撤销那些文件里的越界改动后再提交一次，提交说明写明撤回了哪一处，然后仍停在这里。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 只加厚 02、05、08、09，中英一起，四块标题各一次 | Task 5、Task 6、Task 7、Task 8、Task 10 |
| 静态主图，正常路径和失败路径，不用 `Svg.footer()`，小于 60 KB | Task 3 |
| 短 GIF 只是辅图，帧数 3 到 12，不改已有 8 个 BUILDERS 的像素 | Task 4 |
| 第 02 章第 7.3.2 节、72 MHz、LATENCY = 2、CSS 回 HSI、四块里不写 21 µs | Task 5 |
| 第 05 章 1 kHz 与 500 Hz、CCR = 500、16 位装不下 999999、第 16 脚只画 TIM3_CH1 | Task 6 |
| 第 08 章 Mode 0、9 MHz、0x9F 之后的 0xEF 0x40 0x17、对调线、不编基址 | Task 7 |
| 第 09 章 12 MHz 下 21 µs、除以 4096、两只 ADC、没有 DAC、不重画 LED | Task 8 |
| R_ADC / C_ADC 只有印出来才进 snapshot；BR 编码以第 25.5.1 节为准 | Task 2、Task 7、Task 8 |
| 新 id 只追加八个；`project-examples` 不改对象 | Task 2、Task 7 |
| 版本 1.2.2 · 2026-10-25，不打 tag，不发 Release | Task 9、Task 10 |
| 不改附录 A、附录 D、`build_html.py`、样本锁定、Batch2 锁定和其余章 | Task 10 |
| 书签仍是 44，`0x271` 与 `167 ns` 断言仍在，样本测试和 Batch2 测试不放宽 | Task 9 |
| CI 变绿后停下来等人复审，不自动合入 | Task 10 |

## 执行交接

计划写在 `docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch3-02-05-08-09.md`。实施时二选一：

1. Subagent-Driven（推荐）：每个任务一个新的子代理，任务之间复核。必用 superpowers:subagent-driven-development。
2. Inline Execution：在同一个会话里按 superpowers:executing-plans 分批做，每批停下来复核。

无论哪一种，Task 10 都停在人复审。人接受之前不合入。
