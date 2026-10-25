# Batch 2 Chapters 04 and 06 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 只加厚第 04 章和第 06 章（中文和英文一起），写成和第 00、03 章相同的四块密度，每章一张可印刷的静态主图加一条短 GIF 辅图，把第 06 章 `0x271` 的误差改成和附录 D 同一笔账，合入时把整书升到 1.1.1，然后停下来等用户复审。

**Architecture:** 章号已经由设计锁死，不再打分重选。先只读 `04` 与 `06` 的中英四份，确认四块还不存在、旧坑标题还在，把结果写进新的锁定文件。然后写来源清单，再生成静态 SVG 和短 GIF，最后改四份正文。新出处只追加进 `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `sources`。附录 E 的卡片仍由 `stm32-book/build_html.py` 的 `source_registry_html()` 生成。主图走 `tools/svgkit.py` 的 `tools/gen_sample_figures.py`。短 GIF 走 `tools/gen_gifs.py` 的 `BUILDERS`。版本号同时写进两份 manifest、`stm32-book/revisions.json` 和 `stm32-book/README.md`。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 -m unittest`、`tools/svgkit.py`、`tools/gen_gifs.py`、`tools/minigfx.py`、`tools/check_assets.py`。不新增依赖，不改 `requirements.txt`。

单文件测试写成 `python3 stm32-book/tests/<file>.py -v`。`stm32-book/tests/` 不是 Python 包。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

## Global Constraints

- 只把第 04 章和第 06 章加厚到和第 00、03 章相同的四块密度。中文和英文一起写完。文件名仍是 `docs/04-中断与NVIC.md`、`docs/en/04-interrupts-nvic.md`、`docs/06-串口UART.md`、`docs/en/06-uart.md`。
- 四块标题必须原样出现，各一次：中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`；英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。标题不加表情符号。四块插在视频块之后、学习目标之前。
- 保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。保留 `## 🧠 核心原理` 与 `## 🧠 Core ideas`。`## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls and troubleshooting` 删掉，不留空标题。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上。生成脚本是 `tools/gen_sample_figures.py`，画布是 `tools/svgkit.py`。不调用 `Svg.footer()`。落款用已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。没有 `<animate`、`@keyframes`、`animation:`。图注写「自绘」，替代文本写结论。单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 另加一条短 GIF，只做网页和公众号辅图。GIF 不替换主图，也不是关键插图这一节唯一的图。必做的两条走 `tools/gen_gifs.py`，加入 `BUILDERS`。`minigfx.py` 只有 5×7 英文点阵，GIF 上的字用 ASCII。每条少于 500 KB。帧数不少于 3、不多于 12。`gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 改写吸收的许可顺序：先用 ST 公开 RM/DS/PM 的事实、用自己的话重写；然后才是 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。不吸收 CMSIS 正文。不把厂商手册、官方插图、社区原文或 MaJerle 的源码放进仓库。
- 在 STM32F103C8T6 上，`USART_CR1` 没有 OVER8。RM0008 Rev 21 里 `USART_CR1` 偏移 `0x0C`，位 31:14 保留。现有句子「F1/F4 支持 OVER8」改成：F103 只有 16 倍；8 倍要换到带 OVER8 的系列。这一批不追加 `rm0090-usart-over8`，不编一个 8 倍的 BRR。
- 第 06 章那张表把 39.0625、`0x271` 和 0.16% 写在同一行。这一批改掉：72 MHz 那一行的误差是 0%。大约 0.16% 留在 36 MHz、BRR `0x138` 那一行，并写明那是 APB1 上的 USART2，不是这只 USART1。这格从附录 D 照抄。不编辑附录 A 或附录 D。
- 实施合入时把整书从 1.1.0 升到 **1.1.1**。中英文整书共用这个版本号。日期用准备合并当天的 UTC 日期。不打 tag，不创建 GitHub Release。
- CI 变绿之后停下来等人复审。复审对象是构建出的中英 HTML 里的这两章。人接受之前不合入，也不开下一批章。
- 实施基线是 #22 合入之后的 `main` 尖端。写本计划时该尖端是 `7b4fedac429d8b756d27a1412a0ba1f60a079f85`（`docs: 第 04 与第 06 章大典加厚设计规格 (#22)`），其章节正文与 v1.1.0 `e8afafcfc0ed95a705915eef981dd6e609c84ab4` 相同，只多了设计规格。
- 不加厚除 04、06 以外的任何章，含 00、01、02、03、05 和 07–28。不改这几章的英文。不重选样本。不改 `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json`，不改 `2026-10-25-sample-source-list.json`，不改 `tools/scan_sample_chapters.py` 的打分规则。不改 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md`，不改样本实施计划，不改本批设计规格。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。章号显示仍是文件名前缀加 1：文件 `04` 在书里是第 5 章，文件 `06` 是第 7 章。源文件的一级标题继续带 `04` 和 `06`。不把标题改成「第 5 章」。
- 不改附录 A 的既有契约，不改附录 D 三套账的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。不删 `test_build.py` 里 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不放宽 `test_sample_chapters.py` 对 00 与 03 的断言。
- 不删除第 04、06 章已有的 `nvic-interrupt-flow.svg`、`gpio-input-interrupt.svg`、`interrupt-priority.svg`、`uart-frame.svg`、`uart-bits.gif`。不改第 01 章和第 02 章已有的图。不改已有 6 个 GIF `BUILDERS` 的像素。不重做 `*-zh.gif`。不把 `tools/svg2gif.py` 当成必经步骤。
- 新来源 id 只追加。已有 id 的对象一个字段都不改，含 `rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`majerle-uart`、`st-uart-idle`、`stm32cube-f4`、`pm0056`、`rm0090`。中英两份 manifest 的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。
- 代码继续按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。不新开可烧录工程。保留 `examples/exti-key/` 和 `examples/uart-dma-idle/`。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名，不改 `assets/video/`。
- 尾链的周期数不编。PM0056 DocID15491 Rev 6 第 2.3.7 节写了尾链的定义，没有印周期数。ARM DDI0337 里的 6 个周期不写进正文，也不补进附录 D。图上只画出「没有发生第二次嵌套入栈」。
- 第 04 章不写 `0x50`。`0x50` 留在第 15 章和附录 D。裸机优先级那一句只链已有的 `#source-freertos-priority`。
- 社区中断例程这一批不冻结。来源清单的 `community` 是空数组。不吸收 libopencm3，也不吸收未写许可的博客。
- 冻结的 STM32CubeF4 `v1.28.3` 例程 `UART_ReceptionToIdle_CircularDMA` 把 HT、TC、IDLE 写成三次分开的回调原因，22 字节的例子是 HT 的 Size=10、接着 TC 的 Size=20、再接着 IDLE 的 Size=2。它没有把「HT 与 IDLE 总会成对出现」写成行为。不追加那一行出处卡。论坛那一行仍保留，而且只作为「经验线索，未升格为规范」。

## File map

| 路径 | 责任 |
| --- | --- |
| `tools/scan_batch2_chapters.py` | 只读 04 与 06 的中英四份，确认四块缺失、旧坑标题还在 |
| `docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json` | 核对结果和运行时的 `git rev-parse HEAD` |
| `docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json` | 动笔前的来源清单；登记以 manifest 为准 |
| `tools/gen_sample_figures.py` | 在现有 `boot_state`、`gpio_led` 之外追加两张静态主图 |
| `assets/diagrams/sample-04-exception-stack.svg` | 第 04 章主图 |
| `assets/diagrams/sample-06-uart-frame.svg` | 第 06 章主图 |
| `tools/gen_gifs.py` | `BUILDERS` 追加 `nvic-preempt` 与 `uart-idle` |
| `assets/gif/nvic-preempt.gif` | 第 04 章辅图，只画抢占成功的那条 |
| `assets/gif/uart-idle.gif` | 第 06 章辅图，只画空闲线 |
| `assets/README.md` | 登记两张 SVG 和两条 GIF |
| `docs/04-中断与NVIC.md` 与 `docs/en/04-interrupts-nvic.md` | 第 04 章四块 |
| `docs/06-串口UART.md` 与 `docs/en/06-uart.md` | 第 06 章四块，并改 BRR 误差行 |
| `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` | 新 `sources`、两章罗盘、版本号 |
| `stm32-book/revisions.json` | 1.1.1 修订条目 |
| `stm32-book/README.md` | 当前版本句和发布一节的 tag 名 |
| `CREDITS.md` | 第六节下面增加 v1.1.1 小节；静态框图张数改为 10 |
| `stm32-book/tests/test_batch2_sources.py` | 来源清单的许可门 |
| `stm32-book/tests/test_batch2_chapters.py` | 四块、共享数字、主图、GIF、BRR 误差格 |
| `stm32-book/tests/test_build.py` | 只改当前版本断言；`0x271` 和书签条数保留 |

---

### Task 1: Gap scan and lock

**Files:**
- Create: `tools/scan_batch2_chapters.py`
- Create: `docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json`（由脚本写出）

**Interfaces:**
- Consumes: `docs/04-中断与NVIC.md`、`docs/en/04-interrupts-nvic.md`、`docs/06-串口UART.md`、`docs/en/06-uart.md`。不读别的章，不调用 `tools/scan_sample_chapters.py`。
- Produces: 锁定文件字段 `rubric`（字符串 `"2026-10-25-classic-encyclopedia-batch2-04-06"`）、`baseline`（40 位十六进制，等于运行时 `git rev-parse HEAD`）、`chapters`（`["04", "06"]`）、`four_blocks_absent`（`true`）、`old_pitfall_heading_present`（`true`）、`files`。`files` 的键是 `"04"` 和 `"06"`。每个值有 `zh`、`en`、`zh_four_blocks`、`en_four_blocks`、`zh_old_pitfall`、`en_old_pitfall`。后面的任务只改这两个前缀。

四块标题是中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`，英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。旧坑标题是中文 `## ⚠️ 常见坑与排查`，英文 `## ⚠️ Pitfalls and troubleshooting`。

在 `7b4fedac429d8b756d27a1412a0ba1f60a079f85` 上，这四份都还没有四块，旧坑标题都还在。若执行时任何一份已经有四块，脚本退出码 2，不写锁定文件，后面的任务停。不要在已有四块上再叠一套标题。

- [ ] **Step 1: 写入核对脚本**

把下面的程序保存为 `tools/scan_batch2_chapters.py`。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 04 and 06 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch2_chapters.py

Writes docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json and exits 0
when all four manuscripts lack the four headings and still have the old
pitfall heading. Exits 2 without writing the lock if a four-block heading
is already present, or if the old pitfall heading is already gone.
Does not score other chapters and does not touch the sample lock.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch2-04-06-lock.json"
FILES = {
    "04": (
        ROOT / "docs" / "04-中断与NVIC.md",
        ROOT / "docs" / "en" / "04-interrupts-nvic.md",
    ),
    "06": (
        ROOT / "docs" / "06-串口UART.md",
        ROOT / "docs" / "en" / "06-uart.md",
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
        "rubric": "2026-10-25-classic-encyclopedia-batch2-04-06",
        "baseline": baseline,
        "chapters": ["04", "06"],
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

Run: `python3 tools/scan_batch2_chapters.py`

Expected: 退出码 0，标准输出含

```text
04 four_blocks=no old_pitfall=yes
06 four_blocks=no old_pitfall=yes
baseline=
```

`baseline=` 后面是当时 `git rev-parse HEAD` 的 40 位哈希。并生成 `docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json`，其中 `chapters` 为 `["04", "06"]`，`four_blocks_absent` 为 `true`，`old_pitfall_heading_present` 为 `true`。

若退出码为 2：停止。不要改四块标题去凑退出码 0，也不要改 `tools/scan_sample_chapters.py`。

- [ ] **Step 3: 确认样本锁定和设计规格没被改写**

Run:

```bash
git diff --name-only -- docs/superpowers/plans/2026-10-25-sample-chapter-lock.json docs/superpowers/plans/2026-10-25-sample-source-list.json docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch2-04-06-design.md tools/scan_sample_chapters.py
```

Expected: 无输出。

- [ ] **Step 4: Commit**

```bash
git add tools/scan_batch2_chapters.py docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json
git commit -m "docs: 锁定第 04 与第 06 章尚未加厚"
```

这一笔提交里不要带 manifest 或章节正文。锁定文件里的 `baseline` 必须仍指向还没有新 `sources` 的那次提交。

### Task 2: Source list with the license gate

**Files:**
- Create: `docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json`
- Create: `stm32-book/tests/test_batch2_sources.py`
- Test: `stm32-book/tests/test_batch2_sources.py`

**Interfaces:**
- Consumes: Task 1 的 `chapters == ["04", "06"]`，以及 `four_blocks_absent == true`。
- Produces: 四个新 id，顺序固定为 `rm0008-exti`、`pm0056-nvic`、`rm0008-usart`、`ds5319-usart`。不产生 `rm0090-usart-over8`。`community` 是空数组。`reuse_existing` 的 id 是 `freertos-priority`、`majerle-uart`、`st-uart-idle`、`stm32cube-f4`，这四个不新建 manifest 对象。

2026-10-25 从公开目录核对过的事实，实施时打开同一批 URL。首页修订或节号变了就停，先改清单里的 `snapshot` 和 `section`，再画图、再写正文。数字本身不变：

- RM0008 Rev 21（February 2021）目录：`9.4.3` 到 `9.4.6` 是 `AFIO_EXTICR1` 到 `AFIO_EXTICR4`。`9.2.7` 不是 EXTICR，样本已经把它钉成 `GPIOx_LCKR`。`10.2.5` 是外部中断线映射。`10.3.6` 是 `EXTI_PR`。`27.3.3` 是接收。`27.6.3` 是 `USART_BRR`。`27.6.4` 是 `USART_CR1`。设计规格已写明这一版 `USART_CR1` 偏移 `0x0C`，位 31:14 保留。
- PM0056 DocID15491 Rev 6 目录：`2.3.6` 是优先级分组，`2.3.7` 是异常进入与返回。`2.3.7` 写 8 个字的栈帧（R0–R3、R12、返回地址、PSR、LR），并写尾链会跳过出栈再进入已挂起的异常。这一节没有印尾链周期数。PRIMASK 在 `2.1.3` 的 Table 7：置 1 时挡住可配置优先级的异常。`FAULTMASK` 挡住除 NMI 以外的异常。
- DS5319 Rev 20（July 2025）图 8 与表 5，和样本的 `ds5319-gpio` 是同一份 PDF。LQFP48 第 30 脚是 PA9，第 31 脚是 PA10。复位后的 USART1 默认脚不是 PB6/PB7。
- `majerle-uart` 的 commit `c242589d766eada3ad1d795630f2b1c2482a2af8` 已在 manifest 里，许可证按设计规格记为 MIT。对象一个字段都不改。
- `stm32cube-f4` 停在 tag `v1.28.3`，commit `94cae6e83f00e276a11957e7833c01ac3d0bd7af`。对象不改。读到的 `readme.txt` 把 `Size` 写成缓冲区里已经写到的下标。
- `st-uart-idle` 与 `freertos-priority` 仍是链接引用。对象不改。

打开这些 URL：

- `https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf`
- `https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf`
- `https://www.st.com/resource/en/datasheet/stm32f103c8.pdf`

PM0056 的这个 URL 打不开时，改用文档中心上真正打开同一份手册的 URL，两份 manifest 写同一个。节号以打开的那一版印出来的目录为准。打不开、或目录里没有 `2.3.7`，就停，不要换一份别的内核手册来补周期数。

- [ ] **Step 1: 写会失败的许可门测试**

保存为 `stm32-book/tests/test_batch2_sources.py`：

```python
#!/usr/bin/env python3
"""License gate for chapters 04 and 06. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch2-04-06-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch2-04-06-lock.json"
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


class Batch2SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_04_and_06(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["04", "06"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch2-04-06", lock["rubric"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["04", "06"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(
            ["rm0008-exti", "pm0056-nvic", "rm0008-usart", "ds5319-usart"],
            ids,
        )
        self.assertNotIn("rm0090-usart-over8", ids)
        for item in payload["absorb"]:
            self.assertIn(item["license_class"], ALLOWED)
            self.assertTrue(item["url"].startswith("https://"))
            self.assertNotIn("http://", item["url"])
            for banned in REJECTED:
                self.assertNotIn(banned, item["license"])
                self.assertNotIn(banned, item["license_class"])
            self.assertTrue(item["do_not_copy"])
            self.assertGreaterEqual(len(item["points"]), 1)
            self.assertNotIn(".pdf", item["repo_path"] if "repo_path" in item else "")
        by_id = {item["id"]: item for item in payload["absorb"]}
        self.assertEqual("9.4.3", by_id["rm0008-exti"]["section"])
        self.assertEqual("2.3.7", by_id["pm0056-nvic"]["section"])
        self.assertEqual("27.3.3", by_id["rm0008-usart"]["section"])
        self.assertEqual("Figure 8", by_id["ds5319-usart"]["section"])
        self.assertNotIn("cycle", by_id["pm0056-nvic"]["snapshot"].lower())
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(
            ["freertos-priority", "majerle-uart", "st-uart-idle", "stm32cube-f4"],
            reused,
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为清单不存在而失败**

Run: `python3 stm32-book/tests/test_batch2_sources.py Batch2SourceListTests.test_source_list_keeps_the_license_gate -v`

Expected: FAIL，`FileNotFoundError`，路径里含 `2026-10-25-batch2-04-06-source-list.json`。

锁定文件那一条此时应能通过。若它也失败，先回到 Task 1，不要改测试去迁就一份不存在的锁。

- [ ] **Step 3: 写入来源清单**

保存为 `docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json`：

```json
{
  "chapters": ["04", "06"],
  "community": [],
  "reuse_existing": [
    {
      "id": "freertos-priority",
      "claim": "A bare-metal priority setup does not automatically meet the chapter 15 FromISR constraint.",
      "do_not_copy": "Do not copy 0x50 into chapter 04. Leave that cell in chapter 15 and Appendix D."
    },
    {
      "id": "majerle-uart",
      "claim": "On a continuous DMA receive, the application reads up to the DMA write position. The buffer is not one flat frame.",
      "do_not_copy": "MIT commit c242589d766eada3ad1d795630f2b1c2482a2af8. Restate in our own words. Do not paste functions, and do not promote that repository's register values into a new norm."
    },
    {
      "id": "st-uart-idle",
      "claim": "Experience only, not promoted to a specification: someone reported HT and IDLE arriving close together.",
      "do_not_copy": "Link only. Do not copy sentences from the post. This row introduces no new register value and no new microsecond number."
    },
    {
      "id": "stm32cube-f4",
      "claim": "In the v1.28.3 circular DMA example, Size is the write position, not the increment of this transfer.",
      "do_not_copy": "BSD-3-Clause HAL. Stay inside tag v1.28.3 of the F446 example. Do not call its pins an F103 proof. Do not add a row that HT and IDLE always arrive as a pair."
    }
  ],
  "absorb": [
    {
      "id": "rm0008-exti",
      "chapters": ["04"],
      "title_zh": "RM0008 Rev 21 EXTI 与 AFIO_EXTICR",
      "title_en": "RM0008 Rev 21 EXTI and AFIO_EXTICR",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021, sections 9.4.3-9.4.6 AFIO_EXTICR1-4, section 10.2.5 line mapping, section 10.3.6 EXTI_PR",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "9.4.3",
      "do_not_copy": "Do not paste chapter 10 or the EXTICR registers. Do not call section 9.2.7 EXTICR. Do not trace the official line-mapping figure.",
      "points": [
        "PA0 and PB0 share EXTI0; one pin number keeps one port",
        "On F1, enable the AFIO clock before writing EXTICR",
        "EXTI_PR is cleared by writing 1 to the pending bit"
      ]
    },
    {
      "id": "pm0056-nvic",
      "chapters": ["04"],
      "title_zh": "PM0056 异常入栈、尾链与 PRIMASK",
      "title_en": "PM0056 exception stack, tail-chaining, and PRIMASK",
      "authority_zh": "ST 官方编程手册",
      "authority_en": "ST programming manual",
      "url": "https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf",
      "snapshot": "PM0056 DocID15491 Rev 6, section 2.3.6 priority grouping, section 2.3.7 exception entry and return, PRIMASK Table 7 in section 2.1.3. Section 2.3.7 does not print a tail-chain cycle count.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "2.3.7",
      "do_not_copy": "Do not paste section 2.3.7. Do not import a tail-chain cycle count from another manual. Do not change the existing pm0056 CFSR/HFSR object. Do not treat 167 ns as the ISR body budget.",
      "points": [
        "The stack frame is eight words: xPSR, return address, LR, R12, R3, R2, R1, R0, with SP at the lowest address",
        "Tail-chaining skips a stack pop and does not change who may preempt",
        "PRIMASK blocks configurable-priority exceptions and does not block NMI"
      ]
    },
    {
      "id": "rm0008-usart",
      "chapters": ["06"],
      "title_zh": "RM0008 Rev 21 USART 采样、BRR 与帧错误",
      "title_en": "RM0008 Rev 21 USART sampling, BRR, and framing error",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021, section 27.3.3 receiver, section 27.6.3 USART_BRR, section 27.6.4 USART_CR1 bits 31:14 reserved",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "27.3.3",
      "do_not_copy": "Do not paste section 27.3.3. Do not trace the official sampling figure. Do not invent an 8x BRR. OVER8 is not a bit on this F103.",
      "points": [
        "16x sampling; stop bit voted at samples 8, 9, and 10; start bit checked at samples 3, 5, 7 and 8, 9, 10",
        "USARTDIV = fPCLK / (16 x baud). At 72 MHz and 115200, USARTDIV is 39.0625, BRR is 0x271, divider error is 0",
        "FE is set when the stop samples are not high; the data byte still enters DR; clear by reading SR then DR",
        "USART_CR1 offset 0x0C, bits 31:14 reserved, so this part has no OVER8"
      ]
    },
    {
      "id": "ds5319-usart",
      "chapters": ["06"],
      "title_zh": "DS5319 Rev 20 LQFP48 的 USART1 脚",
      "title_en": "DS5319 Rev 20 LQFP48 USART1 pins",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
      "snapshot": "DS5319 Rev 20, July 2025, Figure 8 and Table 5, LQFP48 pins 30 and 31",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "Figure 8",
      "do_not_copy": "Do not trace Figure 8 or Table 5. Do not call PB6/PB7 the reset default.",
      "points": [
        "LQFP48 pin 30 is PA9 USART1_TX and pin 31 is PA10 USART1_RX",
        "Remap onto PB6/PB7 is not the reset default and needs AFIO"
      ]
    }
  ]
}
```

`accessed` 不写进这份清单。Task 5 写 manifest 时用当天 UTC 日期，中英相同。

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 stm32-book/tests/test_batch2_sources.py -v`

Expected: OK，两条测试都通过。

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json stm32-book/tests/test_batch2_sources.py
git commit -m "docs: 列上 04 与 06 的可吸收来源"
```

### Task 3: Static key figures

**Files:**
- Modify: `tools/gen_sample_figures.py`（只追加函数，并在 `main()` 里多保存两张；不改 `boot_state` 和 `gpio_led`）
- Create: `assets/diagrams/sample-04-exception-stack.svg`
- Create: `assets/diagrams/sample-06-uart-frame.svg`
- Modify: `assets/README.md`（开头的生成命令，以及第四节表的末尾）
- Create: `stm32-book/tests/test_batch2_chapters.py`
- Test: `stm32-book/tests/test_batch2_chapters.py`

**Interfaces:**
- Consumes: Task 2 清单里的订货号、脚位、寄存器名和 `0x271`。已有的 `_credit(canvas, note)`。
- Produces: `exception_stack() -> Svg` 与 `uart_frame() -> Svg`。两张 SVG 不含 `<animate`、`@keyframes`、`animation:`，不含「矢量动画」，含「自绘」。`sample-04-exception-stack.svg` 的文本含 `STM32F103C8T6`、`NVIC_PRIORITYGROUP_4`、`xPSR`、`PC`、`LR`、`R12`、`R3`、`R2`、`R1`、`R0`、`167 ns`、`PA0`、`EXTI0`、`EXTI_PR`、`EXTI0_IRQn`、`TIM2`、`PRIMASK`、`NMI`、`GROUP_4`。`sample-06-uart-frame.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`PA9`、`PA10`、`30`、`31`、`0xA5`、`0x271`、`39.0625`、`8.68`、`86.8`、`USART_SR`、`0x00`、`USART_DR`、`0x04`、`USART_BRR`、`0x08`、`USART_CR1`、`0x0C`、`FE`、`OVER8`。两张都小于 60 KB。

- [ ] **Step 1: 写会失败的主图测试**

保存为 `stm32-book/tests/test_batch2_chapters.py`：

```python
#!/usr/bin/env python3
"""Checks for thickened chapters 04 and 06 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为文件不存在而失败**

Run: `python3 stm32-book/tests/test_batch2_chapters.py -v`

Expected: FAIL，`sample-04-exception-stack.svg` 不存在（`FileNotFoundError`）。

- [ ] **Step 3: 追加两个生成函数并写出 SVG**

在 `tools/gen_sample_figures.py` 的 `gpio_led()` 之后、`main()` 之前插入下面两个函数。不要改 `boot_state`、`gpio_led`、`_credit`。

```python
def exception_stack() -> Svg:
    canvas = Svg(
        960,
        780,
        "抢占 1 可以打断抢占 2；抢占同为 1 时后来的请求不能嵌套",
        "STM32F103C8T6 · NVIC_PRIORITYGROUP_4 · PM0056 §2.3.7",
    )
    canvas.header(tag="04", tag_color=T.CYAN)
    canvas.text(40, 86, "正常路径  GROUP_4", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 100, 880, 250, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 128, "TIM2 抢占 2 正在执行", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 154, "EXTI0  PA0 下降沿  EXTI0_IRQn  抢占 1  子优先级 0", size=14, fill=T.GREEN)
    canvas.text(56, 180, "硬件入栈 8 个寄存器，从高地址到低地址：", size=14, fill=T.TEXT)
    canvas.text(56, 206, "xPSR   PC   LR   R12   R3   R2   R1   R0", size=16, fill=T.CYAN, weight="700")
    canvas.text(56, 232, "入栈后的 SP 指向 R0", size=14, fill=T.TEXT)
    canvas.text(56, 258, "大约 12 个 HCLK，72 MHz 时 12 / 72e6 ≈ 167 ns，不含 ISR 正文", size=14, fill=T.AMBER)
    canvas.text(56, 284, "然后取向量、执行 ISR、出栈返回。清标志写 EXTI_PR", size=14, fill=T.MUTED)
    canvas.text(56, 316, "NVIC_PRIORITYGROUP_4：4 位抢占，0 位子优先级。数值越小，逻辑优先级越高。", size=13, fill=T.MUTED)
    canvas.text(56, 338, "TIM2_IRQn 抢占 2 被 EXTI0_IRQn 抢占 1 打断", size=13, fill=T.GREEN)
    canvas.text(40, 376, "失败路径  优先级写错，更高的请求进不来", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 390, 880, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 418, "EXTI0 与 TIM2 的抢占都写成 1，子优先级仍写成 0 和 1", size=14, fill=T.TEXT, weight="700")
    canvas.text(56, 444, "子优先级不同也不嵌套。EXTI0 保持挂起，等正在执行的 ISR 退出", size=14, fill=T.AMBER)
    canvas.text(56, 470, "退出时可以尾链进去。没有发生第二次嵌套入栈", size=14, fill=T.RED)
    canvas.text(56, 496, "把 EXTI0 的抢占数值写成比 TIM2 更大，是出处卡的另一行，不在这张图上", size=13, fill=T.MUTED)
    canvas.text(56, 520, "STM32F103C8T6  ·  这一路径不是 NMI", size=13, fill=T.MUTED)
    canvas.rect(40, 560, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 590, "PRIMASK = 1 时 EXTI0 和 TIM2 都进不来", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 618, "NMI 仍然进入。不要把 NMI 画成被 NVIC 抢占字段挡住。", size=14, fill=T.TEXT)
    canvas.text(56, 646, "FAULTMASK 再挡住 HardFault，仍留 NMI。BASEPRI 只挡住数值大于等于阈值的那一截。", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。入栈与 167 ns 沿用附录 D；寄存器名来自 PM0056 第 2.3.7 节，EXTI 来自 RM0008 Rev 21。")
    return canvas


def uart_frame() -> Svg:
    canvas = Svg(
        960,
        820,
        "停止位采到 0 就是帧错误；0x271 在 72 MHz、16 倍下误差是 0",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 27 章",
    )
    canvas.header(tag="06", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  USART1  APB2  72 MHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "第 30 脚 PA9 = USART1_TX     第 31 脚 PA10 = USART1_RX     空闲为高", size=14, fill=T.CYAN)
    canvas.text(40, 138, "0xA5  LSB 先发：起始位 0，数据 1 0 1 0 0 1 0 1，停止位 1", size=14, fill=T.TEXT)
    canvas.text(40, 164, "一位约 8.68 µs，10 位约 86.8 µs。BRR 0x271，16 倍，39.0625，误差 0", size=14, fill=T.AMBER)
    canvas.text(40, 190, "USART_SR 0x00    USART_DR 0x04    USART_BRR 0x08    USART_CR1 0x0C", size=14, fill=T.MUTED)
    labels = ["ST", "b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "SP"]
    bits = ["0", "1", "0", "1", "0", "0", "1", "0", "1", "1"]
    for index, (label, bit) in enumerate(zip(labels, bits)):
        left = 40 + index * 90
        canvas.rect(left, 210, 80, 64, fill=T.PANEL, stroke=T.CYAN, rx=6)
        canvas.text(left + 8, 236, label, size=12, fill=T.MUTED)
        canvas.text(left + 8, 260, bit, size=18, fill=T.GREEN if bit == "1" else T.RED, weight="700")
    canvas.text(40, 300, "正常路径  停止位为高", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 314, 880, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 344, "停止位上的第 8、第 9、第 10 个采样点表决为 1", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 370, "FE 不置位。数据位用中间那三个点。", size=14, fill=T.GREEN)
    canvas.text(56, 396, "起始位的确认序列是第 3、5、7 点和第 8、9、10 点。RM0008 27.3.3", size=13, fill=T.MUTED)
    canvas.text(40, 460, "失败路径  停止位三点采到 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 474, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 504, "第 8、9、10 点为 0，FE 置位，数据仍在 USART_DR", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 530, "清除顺序：先读 USART_SR，再读 USART_DR。只读 DR 清不掉。", size=14, fill=T.RED)
    canvas.text(56, 556, "中断是否到来还要看 RXNE 或 CR3 的 EIE。FE 本身不是唯一的中断源。", size=13, fill=T.AMBER)
    canvas.text(56, 582, "不要写成「FE 一定进中断服务」", size=13, fill=T.MUTED)
    canvas.rect(40, 624, 880, 100, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 654, "旁注  OVER8 / 8 倍  不占帧错误那条路径", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 680, "这颗 F103 的 USART_CR1 位 31:14 保留，没有这个位。", size=14, fill=T.TEXT)
    canvas.text(56, 706, "不在这张图上算 8 倍的 BRR。重映射的 PB6/PB7 不在正常路径上。", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。脚位来自 DS5319 Rev 20 图 8；采样与 BRR 来自 RM0008 Rev 21 第 27 章。")
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
```

Run: `python3 tools/gen_sample_figures.py`

Expected: 退出码 0。两张新 SVG 出现在 `assets/diagrams/`。测试只要求小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。若 `sample-00-boot-state.svg` 或 `sample-03-gpio-led.svg` 出现内容 diff，说明 `boot_state` 或 `gpio_led` 被改过，先还原那两个函数再生成。不要把这两张旧图的改动提交进来。

在 `assets/README.md` 开头的生成命令里，把

```bash
python3 tools/gen_sample_figures.py   # 第 00、03 章的静态主图
```

换成

```bash
python3 tools/gen_sample_figures.py   # 第 00、03、04、06 章的静态主图
```

第四节表格末尾追加这两行，不要另起一列：

```markdown
| `sample-04-exception-stack.svg` | 第 04 章静态主图：GROUP_4 下抢占 1 打断抢占 2 的 8 寄存器入栈，以及同抢占不能嵌套。由 `tools/gen_sample_figures.py` 生成 |
| `sample-06-uart-frame.svg` | 第 06 章静态主图：PA9/PA10 上 0xA5 的 8N1 帧、停止位采样和 FE 清除顺序。由 `tools/gen_sample_figures.py` 生成 |
```

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch2_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_sample_figures.py assets/diagrams/sample-04-exception-stack.svg assets/diagrams/sample-06-uart-frame.svg assets/README.md stm32-book/tests/test_batch2_chapters.py
git commit -m "assets: 为 04 与 06 加上可印刷的静态主图"
```

提交前再看一眼 `git diff --stat -- assets/diagrams/sample-00-boot-state.svg assets/diagrams/sample-03-gpio-led.svg`。Expected: 无输出。

### Task 4: Short auxiliary GIFs

**Files:**
- Modify: `tools/gen_gifs.py`（在 `BUILDERS` 之前追加两个函数，并给字典加两个键。不改 `led_blink`、`pwm_breath`、`uart_bits`、`i2c_timing`、`dma_ring`、`sar_adc`）
- Create: `assets/gif/nvic-preempt.gif`
- Create: `assets/gif/uart-idle.gif`
- Modify: `assets/README.md`（第五节的表，以及「上面 6 张」那两句）
- Modify: `stm32-book/tests/test_batch2_chapters.py`
- Test: `stm32-book/tests/test_batch2_chapters.py`

**Interfaces:**
- Consumes: `tools/minigfx.py` 的 `Canvas`、`Gif`、`C`，以及 `chrome()`。
- Produces: `nvic_preempt()` 与 `uart_idle()`，各返回一帧数在 3 到 12 之间的 `Gif`。`BUILDERS` 的键在原有 6 个之后增加 `"nvic-preempt"` 和 `"uart-idle"`。`nvic_preempt` 的源码含 `TIM2` 与 `EXTI0`，不含同抢占失败那句。`uart_idle` 的源码含 `86.8 us` 与 `IDLE`，不含 `FE`。两条 GIF 文件都小于 500 KB。

- [ ] **Step 1: 把 GIF 断言加进测试**

在 `stm32-book/tests/test_batch2_chapters.py` 的文件头增加 `import importlib.util`，并在 `Batch2FigureTests` 之后追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch2_chapters.py Batch2GifTests -v`

Expected: FAIL，`BUILDERS` 里没有 `nvic-preempt`。

- [ ] **Step 3: 追加两个 BUILDERS 并生成 GIF**

在 `tools/gen_gifs.py` 里，`BUILDERS = {` 之前插入：

```python
def nvic_preempt():
    """TIM2 is running. EXTI0 at a higher preemption interrupts it, then returns.

    The equal-preemption failure stays on the static SVG. This GIF does not draw it.
    """
    g = Gif(W, H, delay=12)
    lines = (
        "TIM2 RUN  PREEMPT 2",
        "EXTI0 ARRIVES  PREEMPT 1",
        "STACK EIGHT REGS",
        "EXTI0 ISR RUNS",
        "UNSTACK AND RETURN",
        "TIM2 RESUMES",
    )
    for index, line in enumerate(lines):
        c = Canvas(W, H)
        chrome(c, "NVIC PREEMPT", "GROUP4", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 48, 448, 36, C.PANEL, C.STROKE)
        c.text("TIM2  PREEMPT 2", 28, 60, C.AMBER, 1)
        c.panel(16, 96, 448, 36, C.PANEL, C.CYAN if index else C.STROKE)
        c.text("EXTI0  PREEMPT 1", 28, 108, C.GREEN if index else C.DIM, 1)
        c.text(line, 28, 160, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 184, C.MUTED, 1)
        c.text("HIGHER PREEMPTION INTERRUPTS TIM2", 28, 214, C.GREEN, 1)
        c.text("THEN THE CORE RETURNS", 28, 232, C.MUTED, 1)
        c.text("PRINT THE FAILURE ON THE STATIC SVG", 28, 254, C.DIM, 1)
        g.add(c)
    return g


def uart_idle():
    """After one frame, RX stays high for one frame time, then IDLE is marked.

    Framing-error samples stay on the static SVG. This GIF does not replay 0xA5 bit by bit.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "FRAME END  STOP HIGH",
        "RX STAYS HIGH",
        "RX STAYS HIGH",
        "RX STAYS HIGH",
        "ONE FRAME OF IDLE",
        "IDLE  86.8 us",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "UART IDLE", "8N1", "AUX GIF  86.8 us IS ONE FRAME")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("RX LINE HIGH AFTER THE FRAME", 28, 58, C.MUTED, 1)
        c.hline(24, 120, 432, C.GREEN, 2)
        mark = 24 + int(432 * index / 5)
        c.vline(mark, 100, 40, C.AMBER, 1)
        c.text(note, 28, 160, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 184, C.MUTED, 1)
        c.text("IDLE IS THE LINE HIGH FOR 86.8 us", 28, 214, C.CYAN, 1)
        c.text("NOT A PROTOCOL LENGTH FIELD", 28, 232, C.AMBER, 1)
        c.text("FRAMING ERROR STAYS ON THE STATIC SVG", 28, 254, C.DIM, 1)
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
}
```

Run: `python3 tools/gen_gifs.py nvic-preempt uart-idle`

Expected: 退出码 0，两行 `[ok]`，帧数都是 6。不要为了这一步重跑另外 6 个名字。

在 `assets/README.md` 第五节表格末尾追加：

```markdown
| `nvic-preempt.gif` | NVIC 抢占的短循环：TIM2 正在执行，EXTI0 以更高抢占打断，然后返回 | 由 `tools/gen_gifs.py` 生成。辅图。同抢占失败只在静态主图上 |
| `uart-idle.gif` | 一帧结束后 RX 保持高，满一个帧时间后标出 IDLE 和 86.8 µs | 由 `tools/gen_gifs.py` 生成。辅图。帧错误的三点采样只在静态主图上 |
```

把「上面 6 张 GIF」换成「上面 8 张 GIF」。把「不是上面 6 张的中文翻译」换成「不是上面 8 张的中文翻译」。

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch2_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_gifs.py assets/gif/nvic-preempt.gif assets/gif/uart-idle.gif assets/README.md stm32-book/tests/test_batch2_chapters.py
git commit -m "assets: 为 04 与 06 加上短 GIF 辅图"
```

`git diff --name-only -- assets/gif/led-blink.gif assets/gif/pwm-breath.gif assets/gif/uart-bits.gif assets/gif/i2c-timing.gif assets/gif/dma-ring.gif assets/gif/sar-adc.gif` 应无输出。

### Task 5: Thicken chapter 04 in both languages

**Files:**
- Modify: `docs/04-中断与NVIC.md`
- Modify: `docs/en/04-interrupts-nvic.md`
- Modify: `stm32-book/manifest.json`（`sources` 末尾追加 `rm0008-exti`、`pm0056-nvic`；`04-中断与NVIC.md` 的 `sources` 改为 `["pm0056", "rm0008", "freertos-priority", "rm0008-exti", "pm0056-nvic"]`）
- Modify: `stm32-book/manifest-en.json`（同一组 id 与同一组 `url` / `snapshot` / `license` / `accessed`；英文 `title`、`authority`、`scope`；`04-interrupts-nvic.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_batch2_chapters.py`
- Test: `stm32-book/tests/test_batch2_chapters.py`

**Interfaces:**
- Consumes: `pm0056-nvic`、`rm0008-exti`、`freertos-priority`，以及 `assets/diagrams/sample-04-exception-stack.svg`、`assets/gif/nvic-preempt.gif`。
- Produces: 中文章在 `## 📌 学习目标` 之前出现四个新的二级标题；英文在 `## 📌 Learning goals` 之前出现四个英文标题。旧的 `## ⚠️ 常见坑与排查` 与 `## ⚠️ Pitfalls and troubleshooting` 删除。第 10 节尾链那一格改成「不改变谁有权抢占」。相关资源里「第 9.2.7 节（AFIO_EXTICR）」改成第 9.4.3 到 9.4.6 节，并写明第 9.2.7 节是 `GPIOx_LCKR`。正文不出现 `0x50`。不出现尾链周期数。

`accessed` 用准备当天的 UTC 日期，格式 `YYYY-MM-DD`。中英 manifest 写同一天。下面把它写成 `BATCH_DATE`，实施时换成 `date -u +%Y-%m-%d` 的输出。

`rm0008-exti` 的中文 `scope`：`第 04 章原理与边界、关键插图、坑与出处卡。只改写 EXTI 线按脚号共用、F1 上先开 AFIO 时钟再写 EXTICR，以及 EXTI_PR 要清。EXTICR 在 RM0008 Rev 21 第 9.4.3 到 9.4.6 节，不是第 9.2.7 节。不复制手册段落，不描官方图。`

`rm0008-exti` 的英文 `scope`：`Chapter 04 principle, key figures, and source cards. Restates that one EXTI line is shared by pin number, that F1 enables the AFIO clock before writing EXTICR, and that EXTI_PR must be cleared. EXTICR is RM0008 Rev 21 sections 9.4.3 through 9.4.6, not section 9.2.7. Does not copy manual prose and does not trace the official figure.`

`pm0056-nvic` 的中文 `scope`：`第 04 章原理与边界、时序或状态、坑与出处卡。只改写 8 个寄存器的入栈、尾链不改变抢占权，以及 PRIMASK 挡不住 NMI。不把 167 ns 写成 ISR 正文的预算，不把尾链周期数补进附录 D。不改已有 pm0056 的 CFSR/HFSR 范围。`

`pm0056-nvic` 的英文 `scope`：`Chapter 04 principle, timing, and source cards. Restates the eight-register stack, that tail-chaining does not change who may preempt, and that PRIMASK does not stop NMI. Does not treat 167 ns as the ISR body budget and does not add a tail-chain cycle count to Appendix D. Does not change the existing pm0056 CFSR/HFSR scope.`

两份 `license`、`url`、`snapshot` 都用清单里的字符串，中英相同。`title` 用清单的 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。

- [ ] **Step 1: 把章节断言和基线读取加进测试**

把 `stm32-book/tests/test_batch2_chapters.py` 的 import 区换成：

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
```

在文件末尾、`if __name__` 之前追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch2_chapters.py Batch2NvicChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`（`AssertionError`，`1 != 0`）。

- [ ] **Step 3: 改尾链那一格和错误的节号，并删掉旧坑表**

中文 `docs/04-中断与NVIC.md` 把这一格：

```markdown
| 尾链（Tail-chaining） | 连续中断省去出栈再入栈 |
```

换成：

```markdown
| 尾链（Tail-chaining） | 退出时可以省掉一部分出栈再入栈，不改变谁有权抢占。账在「时序或状态」 |
```

同一张表里「约 12 个时钟周期」那一格保持不动。

把相关资源这一条：

```markdown
- 官方手册：**RM0008** 第 10 章（中断与事件 EXTI）、第 9.2.7 节（AFIO_EXTICR）；《Cortex-M3 权威指南》（NVIC/异常处理）
```

换成：

```markdown
- 官方手册：**RM0008** 第 10 章（中断与事件 EXTI）、第 9.4.3 到 9.4.6 节（AFIO_EXTICR）。第 9.2.7 节是 GPIOx_LCKR，不是 EXTICR。入栈见 [PM0056 第 2.3.7 节](#source-pm0056-nvic)
```

英文 `docs/en/04-interrupts-nvic.md` 把这一格：

```markdown
| Tail-chaining | Back-to-back interrupts skip the unstack-then-stack |
```

换成：

```markdown
| Tail-chaining | On exit, hardware may skip part of the unstack and the next stack. It does not change who may preempt. The account is in Timing or state |
```

把相关资源这一条：

```markdown
- Official manuals: **RM0008** chapter 10 (interrupts and events, EXTI), section 9.2.7 (AFIO_EXTICR); *The Definitive Guide to the Cortex-M3* (NVIC / exception handling)
```

换成：

```markdown
- Official manuals: **RM0008** chapter 10 (interrupts and events, EXTI), sections 9.4.3 through 9.4.6 (AFIO_EXTICR). Section 9.2.7 is GPIOx_LCKR, not EXTICR. Stacking is [PM0056 section 2.3.7](#source-pm0056-nvic)
```

中文删除从 `## ⚠️ 常见坑与排查` 到下一节 `## 🧪 动手实验` 之前的整段（含表）。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。动手实验保留。机械抖动和 `volatile` 留在核心原理第 5 节和动手实验里，不写回出处卡。10 ms 到 20 ms 的消抖不进出处卡。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `## 📌 学习目标` 之前，紧挨视频块结束之后：

```markdown
## 原理与边界

这一章的抢占结论只钉在订货号 STM32F103C8T6 上。时钟沿用附录 D：SYSCLK = HCLK = 72 MHz。分组沿用罗盘和附录 D：HAL 默认 `NVIC_PRIORITYGROUP_4`，4 位抢占、0 位子优先级。数值越小，逻辑优先级越高。这三句整格照抄，不另算一个新的周期数。

抢占优先级更高（数值更小）的异常可以打断正在执行的、抢占更低的 ISR。子优先级只在多份请求已经同时挂起时决定谁先被响应，不能用来嵌套。`GROUP_4` 的子优先级位数是 0，`HAL_NVIC_SetPriority` 的子优先级参数在这个分组下不产生嵌套。要看见子优先级起作用，分组不能是 `GROUP_4`。分组一改，原来的数值不再表示同一级抢占。附录 D 已经把「改了分组还用旧的抢占级去比谁能嵌套」写成误读，这里沿用这句，不改附录。出处是 [PM0056 第 2.3.6 节](#source-pm0056-nvic)。

退出时若已有挂起异常，硬件可以省掉一部分出栈再入栈。尾链减少开销，不改变谁有权抢占。低优先级不会因为尾链插进高优先级的 ISR。「尾链打开后，低优先级也能插入高优先级」不是机制。PM0056 第 2.3.7 节没有印尾链的周期数，这里不编一个。图上只画出没有发生第二次嵌套入栈。不把周期数补进附录 D。

`PRIMASK` 关掉可配置优先级的中断，NMI 和 HardFault 仍能进入。`FAULTMASK` 再挡住 HardFault，仍留 NMI。`BASEPRI` 只挡住优先级数值大于等于阈值的那一截。NMI 不参加 EXTI0 和 TIM2 那种抢占比较。换屏蔽寄存器时，上一句的挡住范围作废，要按新的那把闸重读。第 02 章的 CSS 进 NMI 只作交叉引用，不在这一章重写时钟树。

裸机这套配置不自动满足第 15 章的 FromISR 约束。这句话链到 [已有的优先级说明](#source-freertos-priority)，不引入 `0x50`。

EXTI 线按脚号共用：PA0 和 PB0 都在 EXTI0 上，不能同时做外部中断。F1 上改端口要先开 AFIO 时钟，再写 `EXTICR`。这句只在 F1 上成立。换到用 SYSCFG 的系列时，AFIO 这一句作废。[RM0008 Rev 21](#source-rm0008-exti) 把 EXTICR 放在第 9.4.3 到 9.4.6 节。第 9.2.7 节是 `GPIOx_LCKR`，不要写成 EXTICR。`EXTI_PR` 要清，写 1 清掉对应的挂起位。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-04-exception-stack.svg" width="760" alt="抢占 1 可以打断抢占 2；抢占同为 1 时后来的请求不能嵌套">
  <br><sub>▲ 自绘。STM32F103C8T6，NVIC_PRIORITYGROUP_4。正常路径：TIM2 抢占 2 正在执行，EXTI0（PA0，EXTI0_IRQn）以抢占 1、子优先级 0 打断它。入栈 8 个寄存器，从高地址到低地址是 xPSR, PC, LR, R12, R3, R2, R1, R0，SP 指向 R0。大约 12 个 HCLK，72 MHz 时 167 ns，不含 ISR 正文。失败路径：两者抢占都写成 1，子优先级 0 和 1 仍然不能嵌套，退出后可以尾链，没有第二次嵌套入栈。PRIMASK = 1 时 EXTI0 和 TIM2 进不来，NMI 仍进入。出处是 [PM0056 第 2.3.7 节](#source-pm0056-nvic) 与 [RM0008 Rev 21 的 EXTICR](#source-rm0008-exti)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/nvic-preempt.gif" width="640" alt="TIM2 正在执行时，EXTI0 以更高抢占打断，然后返回">
  <br><sub>▲ 网页和公众号辅图。只播放抢占成功的那一条。印刷以静态主图为准。同抢占不能嵌套的失败不在这条 GIF 上。</sub>
</p>

章首的 `nvic-interrupt-flow.svg` 和简笔 `interrupt-priority.svg` 留作辅图。不播放它们，主图仍然能指出失败发生在「抢占被写成同一级」那一段。

## 时序或状态

| 阶段 | 分组 | EXTI0 抢占 | TIM2 抢占 | 状态 | 时间 |
| --- | --- | --- | --- | --- | --- |
| 正常：TIM2 正在执行 | GROUP_4 | — | 2 | TIM2 的 ISR 在跑 | — |
| 正常：EXTI0 到达 | GROUP_4 | 1 | 2 | 入栈 xPSR, PC, LR, R12, R3, R2, R1, R0 | 12 HCLK，约 167 ns |
| 正常：服务与返回 | GROUP_4 | 1 | 2 | 取向量、执行 ISR、出栈返回 | 167 ns 不含 ISR 正文 |
| 失败：抢占写成同一级 | GROUP_4 | 1 | 1 | EXTI0 保持挂起。尾链只发生在退出之后。没有第二次嵌套入栈 | 不另编周期数 |
| PRIMASK = 1 | GROUP_4 | 1 | 2 | 可配置中断不进入。NMI 仍进入 | — |

167 ns 与附录 D 同一笔，不改成别的纳秒数。出处是 [PM0056 第 2.3.7 节](#source-pm0056-nvic)。`EXTI_PR` 的清除见 [RM0008](#source-rm0008-exti)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 子优先级更小，却打断不了正在跑的 ISR | 同抢占不能嵌套 | 改抢占级，不要改子优先级来嵌套 | [PM0056](#source-pm0056-nvic) | 同抢占不能嵌套；GROUP_4 没有子优先级位 |
| 按键中断打不断定时器 | EXTI0 的抢占数值没有小于 TIM2 | 让 EXTI0 的抢占数值小于 TIM2 | [PM0056](#source-pm0056-nvic) | 数值越小越优先；写反了就嵌套失败 |
| 打开尾链之后低优先级插进了高优先级 | 这不是尾链的定义 | 检查抢占级 | [PM0056 第 2.3.7 节](#source-pm0056-nvic) | 尾链不改变谁有权抢占 |
| `__disable_irq()` 之后仍进了 NMI | PRIMASK 不管 NMI | 这是预期，不是 PRIMASK 失效 | [PM0056 Table 7](#source-pm0056-nvic) | PRIMASK 挡可配置优先级；NMI 除外 |
| PA0 已经占用 EXTI0，PB0 不再触发 | 同一编号的脚共用一条 EXTI 线 | 换一个脚号 | [RM0008 EXTICR](#source-rm0008-exti) | PA0 和 PB0 都在 EXTI0 上 |
| F1 上 EXTI 不进中断 | 没开 AFIO 时钟，或没写 EXTICR | 打开 AFIO 时钟再写 EXTICR，并清 EXTI_PR | [RM0008 第 9.4.3 节](#source-rm0008-exti) | 这句只在 F1 成立 |

```

英文插在 `## 📌 Learning goals` 之前。图的路径用 `../../assets/`。数字和寄存器名与中文相同：

```markdown
## Principle and boundary

The preemption conclusion of this chapter holds for orderable STM32F103C8T6. The clock is the Appendix D cell: SYSCLK = HCLK = 72 MHz. The grouping is the compass and Appendix D cell: HAL defaults to `NVIC_PRIORITYGROUP_4`, 4 preemption bits and 0 subpriority bits. A smaller number is a higher logical priority. Copy those three sentences whole. Do not invent another cycle count.

An exception with a higher preemption priority (a smaller number) may interrupt an ISR that is running at a lower preemption priority. Subpriority only chooses which already-pending request is taken first. It does not nest. Under `GROUP_4` the subpriority field has no bits, so the subpriority argument of `HAL_NVIC_SetPriority` does not create nesting. Seeing subpriority act means the grouping is not `GROUP_4`. After the grouping changes, the old numbers are not the same preemption level. Appendix D already calls "comparing the old preemption numbers after a grouping change" a misreading. This chapter keeps that sentence and does not edit the appendix. Source: [PM0056 section 2.3.6](#source-pm0056-nvic).

On exit, if an exception is already pending, hardware may skip part of the unstack and the next stack. Tail-chaining cuts overhead. It does not change who may preempt. A lower priority does not enter a higher-priority ISR because tail-chaining is on. "Tail-chaining lets a lower priority insert itself into a higher one" is not the mechanism. PM0056 section 2.3.7 does not print a tail-chain cycle count, so this chapter does not invent one. The figure only shows that a second nested stack did not happen. Do not add that count to Appendix D.

`PRIMASK` masks exceptions of configurable priority. NMI and HardFault still enter. `FAULTMASK` also masks HardFault and still leaves NMI. `BASEPRI` masks only the band whose priority number is greater than or equal to the threshold. NMI does not take part in the EXTI0 versus TIM2 preemption comparison. Changing the mask register voids the previous sentence; read the new gate again. The CSS-to-NMI note in chapter 02 is only a cross-reference. This chapter does not redraw the clock tree.

A bare-metal priority setup does not automatically meet the chapter 15 FromISR constraint. That sentence links the [existing priority note](#source-freertos-priority). It does not introduce `0x50`.

EXTI lines are shared by pin number: PA0 and PB0 are both EXTI0, so they cannot both be external interrupts. On F1, enabling a different port means enabling the AFIO clock and then writing `EXTICR`. That sentence holds only on F1. On a family that uses SYSCFG, the AFIO sentence is void. [RM0008 Rev 21](#source-rm0008-exti) places EXTICR in sections 9.4.3 through 9.4.6. Section 9.2.7 is `GPIOx_LCKR`, not EXTICR. `EXTI_PR` has to be cleared by writing 1 to the pending bit.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-04-exception-stack.svg" width="760" alt="Preemption 1 can interrupt preemption 2; a later request at the same preemption 1 cannot nest">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, NVIC_PRIORITYGROUP_4. Normal path: TIM2 at preemption 2 is running, and EXTI0 (PA0, EXTI0_IRQn) at preemption 1 and subpriority 0 interrupts it. Eight registers stack from high address to low address: xPSR, PC, LR, R12, R3, R2, R1, R0, and SP points at R0. About 12 HCLK, 167 ns at 72 MHz, not the ISR body. Failure path: both are written as preemption 1, subpriorities 0 and 1 still do not nest, tail-chaining can happen on exit, and there is no second nested stack. With PRIMASK = 1, EXTI0 and TIM2 stay out and NMI still enters. Sources: [PM0056 section 2.3.7](#source-pm0056-nvic) and [RM0008 Rev 21 EXTICR](#source-rm0008-exti).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/nvic-preempt.gif" width="640" alt="While TIM2 runs, EXTI0 at a higher preemption interrupts it and then returns">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the successful preemption. Print uses the static figure. The equal-preemption failure is not on this GIF.</sub>
</p>

The opening `nvic-interrupt-flow.svg` and the sketch `interrupt-priority.svg` stay side figures. Without playing them, the key figure still shows the failure where preemption was written as the same level.

## Timing or state

| Phase | Grouping | EXTI0 preemption | TIM2 preemption | State | Time |
| --- | --- | --- | --- | --- | --- |
| Normal: TIM2 is running | GROUP_4 | — | 2 | The TIM2 ISR is running | — |
| Normal: EXTI0 arrives | GROUP_4 | 1 | 2 | Stack xPSR, PC, LR, R12, R3, R2, R1, R0 | 12 HCLK, about 167 ns |
| Normal: handler and return | GROUP_4 | 1 | 2 | Vector fetch, ISR, unstack, return | 167 ns excludes the ISR body |
| Failure: preemption written equal | GROUP_4 | 1 | 1 | EXTI0 stays pending. Tail-chaining happens only after exit. No second nested stack | No invented cycle count |
| PRIMASK = 1 | GROUP_4 | 1 | 2 | Configurable interrupts do not enter. NMI still enters | — |

167 ns is the same Appendix D cell, not a different nanosecond figure. Source: [PM0056 section 2.3.7](#source-pm0056-nvic). Clearing `EXTI_PR` is [RM0008](#source-rm0008-exti).

## Pitfalls and source cards

| Symptom | Cause | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| A smaller subpriority still cannot interrupt the running ISR | Equal preemption does not nest | Change the preemption level, not the subpriority | [PM0056](#source-pm0056-nvic) | Equal preemption does not nest; GROUP_4 has no subpriority bits |
| The button interrupt cannot break into the timer | EXTI0's preemption number is not smaller than TIM2 | Give EXTI0 a smaller preemption number than TIM2 | [PM0056](#source-pm0056-nvic) | A smaller number wins; reversing them fails nesting |
| After tail-chaining is on, a lower priority enters a higher one | That is not what tail-chaining means | Check the preemption levels | [PM0056 section 2.3.7](#source-pm0056-nvic) | Tail-chaining does not change who may preempt |
| NMI still enters after `__disable_irq()` | PRIMASK does not cover NMI | This is expected, not a broken PRIMASK | [PM0056 Table 7](#source-pm0056-nvic) | PRIMASK masks configurable priority; NMI is outside it |
| PA0 already owns EXTI0, and PB0 never fires | One pin number shares one EXTI line | Use a different pin number | [RM0008 EXTICR](#source-rm0008-exti) | PA0 and PB0 are both EXTI0 |
| EXTI never fires on F1 | The AFIO clock is off, or EXTICR was not written | Enable the AFIO clock, write EXTICR, and clear EXTI_PR | [RM0008 section 9.4.3](#source-rm0008-exti) | This sentence holds only on F1 |
```

主图不放进 `<!-- video:` 块。视频块、旁白和章首动画留在原处。

- [ ] **Step 5: 把两个新 id 追加进两份 manifest**

取日期：

```bash
date -u +%Y-%m-%d
```

把打印出的日期记为 `BATCH_DATE`。Task 6 继续用同一个日期，不要各写一天。

在两份 manifest 的 `sources` 对象末尾追加 `rm0008-exti` 与 `pm0056-nvic`。不要改已有对象，包括 `pm0056`、`rm0008`、`freertos-priority`、`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`。

中文 `rm0008-exti`：

```json
"rm0008-exti": {
  "title": "RM0008 Rev 21 EXTI 与 AFIO_EXTICR",
  "authority": "ST 官方参考手册",
  "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
  "snapshot": "RM0008 Rev 21, February 2021, sections 9.4.3-9.4.6 AFIO_EXTICR1-4, section 10.2.5 line mapping, section 10.3.6 EXTI_PR",
  "accessed": "BATCH_DATE",
  "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
  "scope": "第 04 章原理与边界、关键插图、坑与出处卡。只改写 EXTI 线按脚号共用、F1 上先开 AFIO 时钟再写 EXTICR，以及 EXTI_PR 要清。EXTICR 在 RM0008 Rev 21 第 9.4.3 到 9.4.6 节，不是第 9.2.7 节。不复制手册段落，不描官方图。"
}
```

英文对象的 `url`、`snapshot`、`accessed`、`license` 与上面相同。`title` 用 `RM0008 Rev 21 EXTI and AFIO_EXTICR`，`authority` 用 `ST reference manual`，`scope` 用本任务的英文 scope。

中文 `pm0056-nvic`：

```json
"pm0056-nvic": {
  "title": "PM0056 异常入栈、尾链与 PRIMASK",
  "authority": "ST 官方编程手册",
  "url": "https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf",
  "snapshot": "PM0056 DocID15491 Rev 6, section 2.3.6 priority grouping, section 2.3.7 exception entry and return, PRIMASK Table 7 in section 2.1.3. Section 2.3.7 does not print a tail-chain cycle count.",
  "accessed": "BATCH_DATE",
  "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
  "scope": "第 04 章原理与边界、时序或状态、坑与出处卡。只改写 8 个寄存器的入栈、尾链不改变抢占权，以及 PRIMASK 挡不住 NMI。不把 167 ns 写成 ISR 正文的预算，不把尾链周期数补进附录 D。不改已有 pm0056 的 CFSR/HFSR 范围。"
}
```

英文 `title` 用 `PM0056 exception stack, tail-chaining, and PRIMASK`，`authority` 用 `ST programming manual`，`scope` 用本任务的英文 scope。其余四字段与中文相同。

`chapter_guides` 里中文键 `04-中断与NVIC.md` 与英文键 `04-interrupts-nvic.md` 的 `sources` 都改成：

```json
["pm0056", "rm0008", "freertos-priority", "rm0008-exti", "pm0056-nvic"]
```

不要在这一步追加 `rm0008-usart` 或 `ds5319-usart`。那是 Task 6。不要追加 `rm0090-usart-over8`。

- [ ] **Step 6: 运行测试和构建检查**

Run: `python3 stm32-book/tests/test_batch2_chapters.py -v && python3 stm32-book/tests/test_batch2_sources.py -v`

Expected: OK。

Run: `python3 stm32-book/build_html.py --check`

Expected: 退出码 0。

Run: `python3 stm32-book/build_html.py --lang en --check`

Expected: 退出码 0。

- [ ] **Step 7: Commit**

```bash
git add docs/04-中断与NVIC.md docs/en/04-interrupts-nvic.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch2_chapters.py
git commit -m "book: 加厚第 04 章的边界、主图、时序和出处"
```

### Task 6: Thicken chapter 06 in both languages, including the BRR fix

**Files:**
- Modify: `docs/06-串口UART.md`
- Modify: `docs/en/06-uart.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（追加 `rm0008-usart`、`ds5319-usart`；两个 `06-` 章的 `sources` 在原数组末尾追加这两个 id）
- Modify: `stm32-book/tests/test_batch2_chapters.py`
- Test: `stm32-book/tests/test_batch2_chapters.py`

**Interfaces:**
- Consumes: `rm0008-usart`、`ds5319-usart`、`majerle-uart`、`st-uart-idle`、`stm32cube-f4`，以及 `assets/diagrams/sample-06-uart-frame.svg`、`assets/gif/uart-idle.gif`。Task 5 的 `BATCH_DATE`。
- Produces: 四个中文标题和四个英文标题；旧坑表删除；`0x271` 所在的每一张表的误差格是 `0%`，不是 `0.16%`；`0x138` 那一行写明 USART2、APB1 和约 0.16%。正文含 `STM32F103C8T6`、`PA9`、`PA10`、`30`、`31`、`0xA5`、`0x271`、`39.0625`、`8.68`、`86.8`、`0x138`、采样点 8、9、10、`FE`。不出现 `F1/F4 支持 OVER8`，不出现 8 倍 BRR 的算式。不追加 HT 与 IDLE 成对的那一行。

`rm0008-usart` 的中文 `scope`：`第 06 章原理与边界、时序或状态、坑与出处卡。只改写 16 倍采样、BRR 0x271 在 72 MHz 下误差为 0、IDLE 是满一个帧时间、以及先读 SR 再读 DR 清 FE。F103 的 USART_CR1 位 31:14 保留，没有 OVER8。不复制 27.3.3，不描官方采样图，不编 8 倍的 BRR。`

`rm0008-usart` 的英文 `scope`：`Chapter 06 principle, timing, and source cards. Restates 16× sampling, BRR 0x271 with divider error 0 at 72 MHz, IDLE as one full frame of idle line, and clearing FE by reading SR then DR. On F103, USART_CR1 bits 31:14 are reserved, so there is no OVER8. Does not copy section 27.3.3, does not trace the official sampling figure, and does not invent an 8× BRR.`

`ds5319-usart` 的中文 `scope`：`第 06 章关键插图。只改写 LQFP48 第 30 脚 PA9 为 USART1_TX、第 31 脚 PA10 为 USART1_RX。复位后不是 PB6/PB7。不描图 8。`

`ds5319-usart` 的英文 `scope`：`Chapter 06 key figure. Restates LQFP48 pin 30 PA9 as USART1_TX and pin 31 PA10 as USART1_RX. The reset default is not PB6/PB7. Does not trace Figure 8.`

- [ ] **Step 1: 追加会失败的测试**

在 `stm32-book/tests/test_batch2_chapters.py` 里、`if __name__` 之前追加：

```python
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
            {"rm0008-exti", "pm0056-nvic", "rm0008-usart", "ds5319-usart"},
        )
        self.assertEqual(
            set(en_manifest["sources"]) - set(baseline_en["sources"]),
            {"rm0008-exti", "pm0056-nvic", "rm0008-usart", "ds5319-usart"},
        )
        for source_id in ("majerle-uart", "st-uart-idle", "stm32cube-f4", "pm0056", "rm0090"):
            self.assertEqual(baseline["sources"][source_id], zh_manifest["sources"][source_id])
            self.assertEqual(baseline_en["sources"][source_id], en_manifest["sources"][source_id])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch2_chapters.py Batch2UartChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 改 BRR 表、OVER8 那一句和 Size 注释，并删掉旧坑表**

中文 `docs/06-串口UART.md` 把学习目标这一条：

```markdown
- [ ] 会算波特率误差，理解 BRR 与 OVER8
```

换成：

```markdown
- [ ] 会算这颗 F103 上 16 倍过采样的 BRR。这颗料没有 OVER8
```

把核心原理里的波特率表和它下面那句换成：

```markdown
| USART | 目标波特率 | 总线 | PCLK | USARTDIV | BRR（十六进制） | 误差 |
| --- | --- | --- | --- | --- | --- | --- |
| USART1 | 9600 | APB2 | 72 MHz | 468.75 | 0x1D4C | 0% |
| USART1 | 115200 | APB2 | 72 MHz | 39.0625 | 0x271 | 0% |
| USART2 | 115200 | APB1 | 36 MHz | 19.531 | 0x138 | 约 0.16% |

> 这颗 STM32F103C8T6 的 USART_CR1 位 31:14 保留，没有 OVER8。8 倍过采样要换到带这个位的系列。F103 上不要为了高频误码去开 OVER8，先核对 72 MHz 和 BRR `0x271`。`HAL_UART_Init` 仍按 16 倍算 BRR。
```

把 DMA 注释这两处：

```c
/* 原理：DMA 循环接收填充缓冲区；总线空闲(IDLE)触发中断，
   用 Size 参数得到已收字节数，交给应用解析。 */
```

换成：

```c
/* 循环 DMA 时，回调里的 Size 是写位置，不是这一次新增的字节数。
   下面把接收重新启动。位置差写在「坑与出处卡」。 */
```

以及：

```c
        rx_len = Size;                                 /* Size = 已接收字节数 */
```

换成：

```c
        rx_len = Size;                                 /* 写位置。循环缓冲要和上次位置相减，并处理绕回 */
```

英文 `docs/en/06-uart.md` 把学习目标这一条：

```markdown
- [ ] Compute baud-rate error, and understand BRR and OVER8
```

换成：

```markdown
- [ ] Compute BRR for 16× oversampling on this F103. This part has no OVER8
```

把英文波特率表和它下面那句换成：

```markdown
| USART | Target baud | Bus | PCLK | USARTDIV | BRR (hex) | Error |
| --- | --- | --- | --- | --- | --- | --- |
| USART1 | 9600 | APB2 | 72 MHz | 468.75 | 0x1D4C | 0% |
| USART1 | 115200 | APB2 | 72 MHz | 39.0625 | 0x271 | 0% |
| USART2 | 115200 | APB1 | 36 MHz | 19.531 | 0x138 | about 0.16% |

> On this STM32F103C8T6, USART_CR1 bits 31:14 are reserved, so there is no OVER8. 8× oversampling means moving to a family that has that bit. On F103, do not switch OVER8 on to chase high-baud errors; check 72 MHz and BRR `0x271` first. `HAL_UART_Init` still computes BRR at 16×.
```

把英文注释：

```c
/* idea: DMA fills the buffer in a circle; bus idle (IDLE) raises the interrupt.
   The Size argument is how many bytes arrived, and the application parses them. */
```

换成：

```c
/* In circular DMA, Size in the callback is the write position, not this transfer's increment.
   The call below starts the reception again. The position difference is in the source cards. */
```

以及：

```c
        rx_len = Size;                                 /* Size = bytes received */
```

换成：

```c
        rx_len = Size;                                 /* write position; subtract the previous one and handle wrap */
```

中文删除从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整段。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。接线表里的 TX/RX 交叉和 3.3 V、代码节里的 printf 半主机都留下。不要把旧坑表整张贴回核心原理。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `## 📌 学习目标` 之前：

```markdown
## 原理与边界

这一章的帧只钉在订货号 STM32F103C8T6、封装 LQFP48 上。USART1 在 APB2。内核时钟 72 MHz 时 PCLK2 是 72 MHz，外设基址 `0x40013800`。默认脚是 PA9 = USART1_TX = 第 30 脚，PA10 = USART1_RX = 第 31 脚，来自 [DS5319 Rev 20 图 8](#source-ds5319-usart)。复位后不是 PB6/PB7。重映射要另开 AFIO，不把重映射脚写进正常路径。

这颗料的接收器用 16 倍波特率时钟采样。1 位停止位在第 8、第 9、第 10 个采样点上表决。起始位的确认序列是第 3、5、7 点和第 8、9、10 点，写在 [RM0008 27.3.3](#source-rm0008-usart)。数据位用中间那三个点。

16 倍时 `USARTDIV = fPCLK / (16 × 波特率)`。72 MHz、115200：`72e6 / (16 × 115200) = 39.0625`，小数 `0.0625 × 16 = 1`，BRR = `0x271`，`72e6 / (16 × 39.0625) = 115200`，分频误差是 0。`USART_BRR` 偏移 `0x08`，低 4 位是小数。这格从附录 D 照抄。72 MHz 那一行的误差是 0%。大约 0.16% 留在 36 MHz、BRR `0x138` 那一行，那是 APB1 上的 USART2，不是这只 USART1。丢掉小数、只用尾数 39，也会得到大约 0.16%，但那不是写进 `0x271` 的结果。不编辑附录 A 或附录 D。

8 倍过采样在这颗 F103 上作废。`USART_CR1` 偏移 `0x0C`，位 31:14 保留，没有 OVER8。F103 只有 16 倍；8 倍要换到带 OVER8 的系列。这里不编一个 8 倍的 BRR，也不追加 `rm0090-usart-over8`。

115200、8N1 时一位约 8.68 µs，一帧 10 位约 86.8 µs。RM0008 里空闲线是一整帧的高电平。一次 IDLE 表示线已经空了大约一个帧时间，不表示对方协议里的长度字段到了。循环 DMA 的 `Size` 仍是写位置，不是这一次的增量。

停止位在预期的采样点上不是高，硬件置 `USART_SR.FE`。无效数据仍然进 `USART_DR`。清除是先读 SR 再读 DR。只读 DR 清不掉。中断是否到来还要看 RXNE 或 CR3 的 EIE。单字节通信时 FE 本身不单独成为唯一的中断源。不要写成「FE 一定进中断服务」。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-06-uart-frame.svg" width="760" alt="停止位采到 0 就是帧错误，0x271 在 72 MHz、16 倍下误差是 0">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48 第 30 脚 PA9 = USART1_TX，第 31 脚 PA10 = USART1_RX。帧是 0xA5，LSB 先发。一位约 8.68 µs，10 位约 86.8 µs。BRR `0x271`，39.0625，16 倍，误差 0。寄存器偏移 USART_SR 0x00、USART_DR 0x04、USART_BRR 0x08、USART_CR1 0x0C。正常路径：停止位第 8、9、10 点为 1，FE 不置位。失败路径：这三点为 0，FE 置位，数据仍在 DR，清除是先读 SR 再读 DR。旁注：这颗 F103 的 CR1 位 31:14 保留，没有 OVER8，图上不算 8 倍 BRR。脚位来自 [DS5319 Rev 20 图 8](#source-ds5319-usart)。采样与 BRR 来自 [RM0008 Rev 21 第 27 章](#source-rm0008-usart)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/uart-idle.gif" width="640" alt="一帧结束后 RX 保持高，满一个帧时间后标出 IDLE 和 86.8 微秒">
  <br><sub>▲ 网页和公众号辅图。只标空闲线和 86.8 µs。印刷以静态主图为准。帧错误的三点采样不在这条 GIF 上。</sub>
</p>

`uart-frame.svg` 和 `uart-bits.gif` 留在原来的帧格式小节，标成辅图。PDF 不播放 GIF 时，起始位、停止位、第 8、9、10 个采样点和 FE 路径都在静态主图上。

## 时序或状态

| 阶段 | 线上电平 | 0xA5 的位 | 第 8、9、10 点 | FE | 时间 | BRR |
| --- | --- | --- | --- | --- | --- | --- |
| 空闲 | 高 | — | — | 0 | — | — |
| 起始位 | 0 | — | 起始位另用第 3、5、7 点确认 | 0 | 约 8.68 µs | — |
| 数据，LSB 先 | 1 0 1 0 0 1 0 1 | 0xA5 | 数据位用中间三点 | 0 | 8 位 | — |
| 正常停止位 | 1 | 停止位 | 表决为 1 | 0 | 约 8.68 µs | USART1，72 MHz，`0x271`，误差 0% |
| 失败停止位 | 0 | 停止位 | 三点为 0 | 1 | 约 8.68 µs | 清除是读 SR 再读 DR |
| 一帧合计 | — | 10 位 | — | — | 约 86.8 µs | 39.0625 |
| USART2 对照 | — | — | — | — | — | APB1，36 MHz，`0x138`，约 0.16%。不是这只 USART1 |
| IDLE | 停止位之后保持高 | — | — | 0 | 满一个帧时间，约 86.8 µs | 不是协议帧结束 |

不把 0.16% 放回 `0x271` 那一格。出处是 [RM0008 第 27.3.3 节](#source-rm0008-usart)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 表上 USART1 的 `0x271` 被说成已经偏了 0.16% | 那一格把小数位丢掉了，或者把 USART2 的行抄过来了 | 72 MHz、16 倍、带上小数位，误差是 0 | [RM0008 BRR](#source-rm0008-usart) | `0x271` 的分频结果是 115200。0.16% 不是这一格 |
| 停止位错了仍读到一个字节，接着卡死 | FE 置位时数据仍进 DR，只读 DR 不清标志 | 先读 SR 再读 DR 清 FE | [RM0008 27.3.3](#source-rm0008-usart) | FE 置位时数据仍进 DR；只读 DR 不清标志 |
| 把 IDLE 当成对方一包已经结束 | 空闲线只表示线路空闲 | 用长度或协议，不用 86.8 µs 当帧界 | [RM0008](#source-rm0008-usart) | IDLE 是线路空闲满一个帧时间 |
| F103 上打开 OVER8 来修高频误码 | 这颗料没有该位 | 先核对 72 MHz 和 `0x271` | [RM0008 CR1](#source-rm0008-usart) | CR1 位 31:14 保留 |
| 循环 DMA 把 `Size` 当成这一次新增的字节数 | `Size` 是写位置 | 自己保存上次位置再相减，注意绕回 | [STM32CubeF4 v1.28.3](#source-stm32cube-f4) | 只支持 v1.28.3 那个例程里 Size 是写位置。不是 F103 的引脚证明 |
| 应用一次把 DMA 缓冲区当完整线性帧读完 | 缓冲区不是一条拍平的帧 | 读到 DMA 写位置为止 | [MaJerle USART DMA](#source-majerle-uart) | 改写后的环位置边界。不支持新的波特率或脚位 |
| 半传输和 IDLE 好像总会成对出现 | 帖子里的时序没有升格成手册数字 | 不把帖子里的时序写成手册数字；空闲长度仍用 86.8 µs 那一格 | [ST 社区帖](#source-st-uart-idle) | 经验线索，未升格为规范。不支持新的寄存器值 |

```

英文插在 `## 📌 Learning goals` 之前：

```markdown
## Principle and boundary

The frame in this chapter holds for orderable STM32F103C8T6 in LQFP48. USART1 is on APB2. When the core clock is 72 MHz, PCLK2 is 72 MHz, and the peripheral base is `0x40013800`. The default pins are PA9 = USART1_TX = pin 30 and PA10 = USART1_RX = pin 31, from [DS5319 Rev 20 Figure 8](#source-ds5319-usart). After reset the pins are not PB6/PB7. A remap needs AFIO as well, and the remapped pins are not on the normal path.

The receiver on this part samples with a 16× baud clock. One stop bit is voted at samples 8, 9, and 10. The start bit is checked at samples 3, 5, and 7 and at samples 8, 9, and 10, as written in [RM0008 27.3.3](#source-rm0008-usart). Data bits use the middle three samples.

At 16×, `USARTDIV = fPCLK / (16 × baud)`. At 72 MHz and 115200, `72e6 / (16 × 115200) = 39.0625`, the fraction `0.0625 × 16 = 1`, BRR = `0x271`, `72e6 / (16 × 39.0625) = 115200`, and the divider error is 0. `USART_BRR` is at offset `0x08`, and the low 4 bits are the fraction. Copy this cell from Appendix D. The error on the 72 MHz row is 0%. About 0.16% stays on the 36 MHz row, BRR `0x138`, and that row is USART2 on APB1, not this USART1. Dropping the fraction and dividing by 39 also yields about 0.16%. That is not what writing `0x271` does. Do not edit Appendix A or Appendix D.

8× oversampling is void on this F103. `USART_CR1` is at offset `0x0C`, and bits 31:14 are reserved, so there is no OVER8. F103 has only 16×. 8× means a family that has OVER8. This chapter does not invent an 8× BRR and does not add `rm0090-usart-over8`.

At 115200 and 8N1, one bit is about 8.68 µs and a 10-bit frame is about 86.8 µs. In RM0008 an idle line is a whole frame of high. One IDLE means the line has been idle for about one frame time. It does not mean the length field of the other side's protocol has arrived. In circular DMA, `Size` is still the write position, not the increment of this transfer.

When the stop bit is not high at the expected samples, hardware sets `USART_SR.FE`. The invalid byte still enters `USART_DR`. Clearing it is a read of SR and then a read of DR. Reading only DR does not clear it. Whether an interrupt arrives still depends on RXNE or on EIE in CR3. In a one-byte exchange, FE itself is not the only interrupt source. Do not write "FE always enters the service routine."

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-06-uart-frame.svg" width="760" alt="A stop bit sampled as 0 is a framing error, and 0x271 has zero divider error at 72 MHz and 16×">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48 pin 30 PA9 = USART1_TX, pin 31 PA10 = USART1_RX. The frame is 0xA5, LSB first. One bit is about 8.68 µs and 10 bits are about 86.8 µs. BRR `0x271`, 39.0625, 16×, error 0. Offsets: USART_SR 0x00, USART_DR 0x04, USART_BRR 0x08, USART_CR1 0x0C. Normal path: stop-bit samples 8, 9, and 10 are 1, and FE stays clear. Failure path: those three samples are 0, FE is set, the byte remains in DR, and the clear order is SR then DR. Side note: on this F103, CR1 bits 31:14 are reserved, there is no OVER8, and the figure does not compute an 8× BRR. Pins are [DS5319 Rev 20 Figure 8](#source-ds5319-usart). Sampling and BRR are [RM0008 Rev 21 chapter 27](#source-rm0008-usart).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/uart-idle.gif" width="640" alt="After one frame, RX stays high, and IDLE plus 86.8 microseconds is marked after one frame time">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only marks the idle line and 86.8 µs. Print uses the static figure. The three framing-error samples are not on this GIF.</sub>
</p>

`uart-frame.svg` and `uart-bits.gif` stay in the frame section as side figures. When a PDF does not play the GIF, the start bit, the stop bit, samples 8, 9, and 10, and the FE path are all on the static figure.

## Timing or state

| Phase | Line | Bits of 0xA5 | Samples 8, 9, 10 | FE | Time | BRR |
| --- | --- | --- | --- | --- | --- | --- |
| Idle | High | — | — | 0 | — | — |
| Start bit | 0 | — | The start bit is also checked at samples 3, 5, and 7 | 0 | about 8.68 µs | — |
| Data, LSB first | 1 0 1 0 0 1 0 1 | 0xA5 | Data bits use the middle three samples | 0 | 8 bits | — |
| Normal stop | 1 | Stop | Voted as 1 | 0 | about 8.68 µs | USART1, 72 MHz, `0x271`, error 0% |
| Failed stop | 0 | Stop | The three samples are 0 | 1 | about 8.68 µs | Clear by reading SR, then DR |
| Whole frame | — | 10 bits | — | — | about 86.8 µs | 39.0625 |
| USART2 contrast | — | — | — | — | — | APB1, 36 MHz, `0x138`, about 0.16%. Not this USART1 |
| IDLE | Stays high after the stop bit | — | — | 0 | One full frame, about 86.8 µs | Not the end of a protocol frame |

Do not put 0.16% back into the `0x271` cell. Source: [RM0008 section 27.3.3](#source-rm0008-usart).

## Pitfalls and source cards

| Symptom | Cause | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The table says USART1 `0x271` is already 0.16% off | That cell dropped the fraction, or it copied the USART2 row | At 72 MHz and 16×, with the fraction kept, the error is 0 | [RM0008 BRR](#source-rm0008-usart) | The divider result of `0x271` is 115200. 0.16% is not this cell |
| A bad stop bit still yields a byte, and then reception sticks | FE is set and the byte is still in DR; reading only DR does not clear the flag | Read SR, then DR, to clear FE | [RM0008 27.3.3](#source-rm0008-usart) | When FE is set the byte still enters DR; reading only DR does not clear the flag |
| IDLE is treated as the end of the other side's packet | An idle line only means the wire is idle | Use a length or a protocol, not 86.8 µs as the frame boundary | [RM0008](#source-rm0008-usart) | IDLE is the line staying idle for one full frame time |
| OVER8 is turned on to fix high-baud errors on F103 | This part does not have that bit | Check 72 MHz and `0x271` first | [RM0008 CR1](#source-rm0008-usart) | CR1 bits 31:14 are reserved |
| Circular DMA treats `Size` as the new bytes of this transfer | `Size` is the write position | Save the previous position, subtract, and handle the wrap | [STM32CubeF4 v1.28.3](#source-stm32cube-f4) | Only that Size is the write position in the v1.28.3 example. Not an F103 pin proof |
| The application reads the DMA buffer once as one flat frame | The buffer is not one flat frame | Read only up to the DMA write position | [MaJerle USART DMA](#source-majerle-uart) | The restated ring-position boundary. Not a new baud rate or a new pin |
| Half-transfer and IDLE seem to arrive as a pair every time | The timing in the post was not promoted to a manual number | Do not write the post's timing as a manual number; the idle length stays the 86.8 µs cell | [ST community thread](#source-st-uart-idle) | Experience only, not promoted to a specification. No new register value |
```

主图不放进 `<!-- video:` 块。`uart-frame.svg` 与 `uart-bits.gif` 留在帧格式小节，不要删。

- [ ] **Step 5: 追加 `rm0008-usart` 与 `ds5319-usart`**

两份 manifest 的 `sources` 末尾追加这两个 id。`accessed` 用 Task 5 的 `BATCH_DATE`。`url`、`snapshot`、`license` 用清单里的字符串。`title`、`authority`、`scope` 用本任务的中英文本。

中文键 `06-串口UART.md` 与英文键 `06-uart.md` 的 `sources` 都改成：

```json
["rm0008", "stm32cube-f4", "st-uart-idle", "majerle-uart", "rm0008-usart", "ds5319-usart"]
```

不要改 `majerle-uart`、`st-uart-idle`、`stm32cube-f4`、`rm0008` 的旧对象。不要改第 04 章的罗盘数组。不要追加 `rm0090-usart-over8`。

- [ ] **Step 6: 运行测试和构建检查**

Run: `python3 stm32-book/tests/test_batch2_chapters.py -v && python3 stm32-book/tests/test_batch2_sources.py -v`

Expected: OK。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。

- [ ] **Step 7: Commit**

```bash
git add docs/06-串口UART.md docs/en/06-uart.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch2_chapters.py
git commit -m "book: 加厚第 06 章并把 0x271 的误差改成 0"
```

### Task 7: Register the batch, bump 1.1.1, keep the ledgers

**Files:**
- Modify: `CREDITS.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `version` 与 `date`
- Modify: `stm32-book/revisions.json`
- Modify: `stm32-book/README.md`
- Modify: `stm32-book/tests/test_build.py`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 5 和 Task 6 已经写进 manifest 的四个新 id，以及 `BATCH_DATE`。
- Produces: 两份 manifest 的 `version` 都是 `1.1.1`，`date` 都是 `BATCH_DATE`。`revisions.json` 的 `entries[0].version` 是 `1.1.1`。`test_build.py` 里当前版从 `1.1.0` 改为 `1.1.1`，历史列表仍含 `1.1.0` 以及 `1.0.8` 到 `1.0.0`。`0x271` 断言和出版书签长度 44 的断言还在。

- [ ] **Step 1: 先改版本断言，让测试失败**

在 `stm32-book/tests/test_build.py` 里只改当前版断言。不要删 `0x271`、`167 ns`、`会上手的几笔账`、`Numbers to reconcile before changing family`、`Channels, descriptors, and fault registers`，也不要改 `self.assertEqual(44, len(outline))`。

把

```python
versions = ("1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

改成

```python
versions = ("1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

在 `self.assertLess(history.index(">1.1.0<"), history.index(">1.0.8<"))` 之前加一行：

```python
self.assertLess(history.index(">1.1.1<"), history.index(">1.1.0<"))
```

把修订列表的期望从

```python
["1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

改成

```python
["1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

把 `self.assertEqual("1.1.0", manifest["version"])` 改成 `self.assertEqual("1.1.1", manifest["version"])`。

把两处 `self.assertIn("<strong>v1.1.0</strong>", html)` 改成 `self.assertIn("<strong>v1.1.1</strong>", html)`。

- [ ] **Step 2: 运行版本测试，确认失败**

Run: `python3 stm32-book/tests/test_build.py BookBuildTests.test_revision_file_lists_1_0_0_through_manifest_version -v`

Expected: FAIL，修订列表的首项仍是 `1.1.0`。

- [ ] **Step 3: 写 1.1.1**

`BATCH_DATE` 用 Task 5 已经取过的 UTC 日期。若那次会话没留下日期，再跑一次 `date -u +%Y-%m-%d`，中英写同一天。

两份 manifest 的 `version` 改为 `1.1.1`，`date` 改为 `BATCH_DATE`。不要改 `sources` 里已有对象的字段。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入：

```json
{
  "version": "1.1.1",
  "date": "BATCH_DATE",
  "zh": [
    "第 04 章写上 STM32F103C8T6 的抢占边界：GROUP_4 下抢占 1 可以打断抢占 2，同抢占不能嵌套，并加了一张不播放也能读的静态图。",
    "第 06 章把 USART1 在 72 MHz、16 倍下的 BRR 0x271 误差改成 0，并写上停止位采样和帧错误路径。"
  ],
  "en": [
    "Chapter file 04 records the STM32F103C8T6 preemption boundary: under GROUP_4, preemption 1 can interrupt preemption 2, equal preemption does not nest, plus a static figure that stays readable in print.",
    "Chapter file 06 changes the USART1 BRR 0x271 error at 72 MHz and 16× to 0, and records stop-bit sampling and the framing-error path."
  ]
}
```

把 `BATCH_DATE` 换成日期。修订说明只写第 04 章和第 06 章，用文件名前缀，不写尚未加厚的章，不把标题写成「第 5 章」。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.1.1 · BATCH_DATE**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后再打。
```

把「发布 GitHub Release」一节的第一段换成：

```markdown
版本号已经是 1.1.1。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1。
```

第三步的「在该提交上打 tag `v1.1.0`」改成「在该提交上打 tag `v1.1.1`」。这一步仍不创建 tag，也不创建 Release。前面的 artifact 名称和四份文件名保持不动。

- [ ] **Step 4: 在 CREDITS.md 增加 v1.1.1 小节，并改正静态框图的张数**

第一节表格里这一行：

```markdown
| 静态框图（8 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |
```

换成：

```markdown
| 静态框图（10 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |
```

第六节「样本章的改写吸收（v1.1.0）」的标题和那张表保留。在该节末尾追加：

```markdown
### 第 04 章与第 06 章（v1.1.1）

第 04 章和第 06 章用改写吸收补了同样的四块。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图、社区原文和 MaJerle 的函数不放进仓库。论坛帖只留链接。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| RM0008 Rev 21（2021-02），第 9.4.3 到 9.4.6 节、第 10.3.6 节，以及第 27.3.3 节、第 27.6.3 节、第 27.6.4 节 | ST 文档条款；只链接并改写事实，不转载手册 | 第 04 章 EXTI 与 EXTICR；第 06 章 16 倍采样、BRR `0x271` 误差 0、FE 的清除顺序 | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| PM0056 DocID15491 Rev 6，第 2.3.6 节、第 2.3.7 节，以及第 2.1.3 节 Table 7 | ST 文档条款；只链接并改写事实，不转载手册 | 第 04 章 8 寄存器入栈、尾链不改变抢占权、PRIMASK 挡不住 NMI | https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf |
| DS5319 Rev 20（2025-07），图 8 与表 5 | ST 文档条款；只链接并改写事实，不转载手册 | 第 06 章 LQFP48 第 30 脚 PA9、第 31 脚 PA10 | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
| MaJerle stm32-usart-uart-dma-rx-tx | MIT | 第 06 章坑卡：持续 DMA 接收时读到写位置为止，缓冲区不是一条拍平的帧 | https://github.com/MaJerle/stm32-usart-uart-dma-rx-tx/commit/c242589d766eada3ad1d795630f2b1c2482a2af8 |
| STM32CubeF4 v1.28.3 的 UART_ReceptionToIdle_CircularDMA | BSD-3-Clause | 第 06 章坑卡：循环 DMA 的 Size 是写位置。范围停在这个 F446 例程，不把它的引脚说成 F103 | https://github.com/STMicroelectronics/STM32CubeF4/tree/v1.28.3/Projects/STM32446E-Nucleo/Examples/UART/UART_ReceptionToIdle_CircularDMA |
```

- [ ] **Step 5: 运行整套测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。`test_sample_chapters.py` 对 00 与 03 的断言仍然通过。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。构建出的 HTML 里有 `v1.1.1`，并且 `id="source-rm0008-exti"`、`id="source-pm0056-nvic"`、`id="source-rm0008-usart"`、`id="source-ds5319-usart"` 都在。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0。

- [ ] **Step 6: Commit**

```bash
git add CREDITS.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 第 04 与第 06 章登记来源并把整书标成 1.1.1"
```

### Task 8: Scope gate, then stop

**Files:**
- 不新增文件。这一任务只核对 diff。核对失败时，只撤销越界改动，不顺手加厚别的章。

**Interfaces:**
- Consumes: Task 1 到 Task 7 的提交。
- Produces: 一份只含第 04 章和第 06 章加厚的 diff。用户复审之前，没有其余章节的加厚提交，没有 tag，没有 Release。

- [ ] **Step 1: 核对 diff 的路径**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只出现这些路径。顺序可以不同。

```text
CREDITS.md
assets/README.md
assets/diagrams/sample-04-exception-stack.svg
assets/diagrams/sample-06-uart-frame.svg
assets/gif/nvic-preempt.gif
assets/gif/uart-idle.gif
docs/04-中断与NVIC.md
docs/06-串口UART.md
docs/en/04-interrupts-nvic.md
docs/en/06-uart.md
docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json
docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json
docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch2-04-06.md
stm32-book/README.md
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_batch2_chapters.py
stm32-book/tests/test_batch2_sources.py
stm32-book/tests/test_build.py
tools/gen_gifs.py
tools/gen_sample_figures.py
tools/scan_batch2_chapters.py
```

`docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch2-04-06.md` 只在「先合并了本计划」的历史上出现。若实施分支从本计划提交切开，它会留在 diff 里，这是允许的。它不是章节正文。

`stm32-book/build_html.py`、`stm32-book/book/`、`stm32-book/subject-index.json`、`tools/scan_sample_chapters.py`、样本锁定文件、样本来源清单，以及其余 `docs/0`–`docs/28` 与 `docs/en/` 章节都不在这份列表里。

- [ ] **Step 2: 核对附录、构建脚本和第 01、02 章的图没有被卷进来**

Run:

```bash
git diff origin/main...HEAD -- stm32-book/build_html.py stm32-book/book/A-工程深读.md stm32-book/book/D-术语表.md stm32-book/book/en/A-uart-dma.md stm32-book/book/en/D-glossary.md
```

Expected: 无输出。

Run:

```bash
git diff --name-only origin/main...HEAD -- docs/00-如何学习STM32.md docs/01-开发环境搭建.md docs/02-芯片选型与存储器时钟.md docs/03-GPIO与LED.md docs/05-定时器与PWM.md docs/en/00-how-to-learn-stm32.md docs/en/01-dev-environment.md docs/en/02-part-and-clock.md docs/en/03-gpio-and-led.md docs/en/05-timer-pwm.md assets/animations/boot-sequence.svg assets/animations/clock-tree.svg assets/animations/memory-map.svg
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

不要运行 `gh release create`，不要 `git tag`，不要打 `v1.1.0` 或 `v1.1.1`。

- [ ] **Step 5: 停在用户复审**

实施 PR 的说明里写明：只加厚了文件 `04` 和 `06` 的中英四份；静态主图是 `sample-04-exception-stack.svg` 与 `sample-06-uart-frame.svg`；短 GIF 是辅图；第 06 章 `0x271` 那一格的误差是 0，约 0.16% 留在 USART2 的 `0x138`。请用户看构建出的中英 HTML 里的这两章：四块是否都在、关掉动画之后主图是否仍能指出失败、`#source-` 是否点得到附录 E 的卡片。

第 04 章要能指出的失败是「同抢占不能嵌套」。第 06 章要能指出的失败是「停止位第 8、9、10 点为 0，FE 置位」。

用户书面接受之前：

- 不为 `00`、`01`、`02`、`03`、`05`、`07`–`28` 开加厚 PR。
- 不加图目录或表目录。
- 不改 `stm32-book/build_html.py`，不改显示章号，不改 PDF 书签深度。
- 不打 `v1.1.1` 的 tag，不创建 GitHub Release。
- 不把 `rm0090-usart-over8` 补进这一批。要写 F4 的 OVER8 位号，先另开一版计划。

这一步没有新的提交。若 Step 1 到 Step 3 发现越界文件，撤销那些文件里的越界改动后再提交一次，提交说明写明撤回了哪一处，然后仍停在这里。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 只加厚 04 与 06，中英一起，四块标题各一次 | Task 5、Task 6、Task 8 |
| 静态主图，正常路径和失败路径，不用 `Svg.footer()`，小于 60 KB；放不下先拆图，仍超再写字节数，不降低画法，不改 60 KB 默认值 | Task 3 |
| 短 GIF 只是辅图，不替换主图，帧数 3 到 12 | Task 4、Task 5、Task 6 |
| 第 04 章 8 寄存器、167 ns、GROUP_4、PRIMASK、NMI、EXTI 共用线 | Task 5 |
| 尾链不改变抢占权，不编周期数，不写 `0x50` | Task 5，Global Constraints |
| 第 06 章 `0x271` 误差改为 0，0.16% 留在 USART2 的 `0x138` | Task 6 |
| F103 没有 OVER8，不编 8 倍 BRR，不追加 `rm0090-usart-over8` | Task 2、Task 6 |
| 新 id 只追加；`majerle-uart` 改写进坑卡；`st-uart-idle` 只留线索 | Task 2、Task 6、Task 7 |
| 社区中断列表为空；不追加 HT 与 IDLE 成对的那一行 | Task 2、Task 6 |
| 版本 1.1.1，不打 tag，不发 Release | Task 7、Task 8 |
| 不改附录 A、附录 D、`build_html.py`、样本锁定和其余章 | Task 8 |
| 书签仍是 44，`0x271` 断言仍在，样本测试不放宽 | Task 7 |
| CI 变绿后停下来等人复审 | Task 8 |
