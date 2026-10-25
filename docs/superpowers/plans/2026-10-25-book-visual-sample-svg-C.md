# 整书样本图 C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 让仓库根 `assets/` 里的 53 张 SVG 改由生成器写成浅色纸底、三档描边和三档圆角，语义色对齐整书亮色里过得了 4.5 的强调色和提示色，然后把整书标成 **1.2.7 · 2026-10-25**。本计划文件的 PR 不落地这些改动。

**Architecture:** 图仍然只从 `tools/svgkit.py` 的 `T` 字面量和各生成器的 `sw` / `rx` 实参来。生成器把成品写回 `assets/`。不读 `stm32-book/styles/tokens.json`，不写 `var(--*)`。三波都进同一次实施 PR：先 18 张静态图，再 25 张动画，再 10 张板卡和引脚图。53 张都再生完才提交 `test_sample_svg_c.py`。版本戳和版本断言放在最后一次提交。不新开第二套暗色 SVG，不升 token schema。

**Tech Stack:** Python 3 标准库、现有 `tools/svgkit.py` 与 `tools/gen_*.py`、`python3 -m unittest discover stm32-book/tests -v`、`python3 stm32-book/build_html.py --check`。不新增依赖，不改 `requirements.txt`。

`stm32-book/tests/` 不是 Python 包。单条测试写成 `python3 stm32-book/tests/test_sample_svg_c.py SampleSvgCTests.<方法名> -v`。不要写成 `python3 -m unittest stm32-book.tests...`。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。已有类名是 `BookBuildContractTests`。刀 C 的新类名是 `SampleSvgCTests`，放在新文件里。

设计规格：`docs/superpowers/specs/2026-10-25-book-visual-sample-svg-C-design.md`（PR #45，`ed82805`）。

写本计划时的尖端是 `ed828053584c453092034f131483f534fd00fc31`（`docs: 整书视觉刀 C 设计，统一样本 SVG 画法 (#45)`）。这一尖端的整书版本仍是 **1.2.6**，日期仍是 `2026-10-25`。它只新增了设计规格。它下面的 `10a01ec`（PR #44）才是刀 D 的实施。实施基线是本计划合入之后的 `main`，不是本计划的分支。本计划的 PR 只新增本文件。

在 `ed82805` 上复核过，和规格一致：

- 拼好的 `builder.CSS` SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。`book.css` 源文件 19838 字节，SHA-256 是 `7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5`。`tokens.json` 的 SHA-256 是 `c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b`。`cover.svg` 是 3880 字节，SHA-256 是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。
- `assets/` 下恰好 53 张 SVG，路径、宽高、改前字节数和文本哈希与规格里的表一致，0 张对不上。文本哈希的算法是：按文档顺序取出每个 `<text…>…</text>` 的原始内部文本（不反转义），用 `\n` 连接，再做 UTF-8 的 SHA-256。正则是 `<text\b[^>]*>(.*?)</text>`，`re.DOTALL`。
- 按下面五个命令把 53 张写回原路径之后，`git diff -- assets` 为空。成品和生成器在这条历史上仍是逐字节相同。
- `assets/gif/*.gif` 恰好 40 个。按文件名排序、每行 `{文件名} {该文件字节的 SHA-256}\n` 再做 SHA-256，汇总是 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。其中 16 张不是 `*-zh.gif`，24 张是。17 张 `*-zh.gif` 已经大于 500 KB。
- H743 引脚图现在是 75786 字节。除它以外每张都小于 60 KB。

下面生成器的行号属于 `ed82805`。实施时若行号被别的提交挪动，按函数名和引号里的原文定位。

设计规格「实施 PR」的 1–9 步在本计划里的位置：

| 规格里的顺序 | 本计划 |
| --- | --- |
| 1. 确认基线 | 开工条件。不产生提交 |
| 2. 波次 1，18 张静态图 | Task 1 |
| 3. 波次 2，25 张动画 | Task 2 |
| 4. 波次 3，10 张板卡和引脚图 | Task 3 |
| 5. `assets/README.md` 那一句 | Task 4 |
| 6. `test_sample_svg_c.py` | Task 5。版本断言不在这一任务 |
| 7. 版本 | Task 6 |
| 8. 验证 | Task 7 |
| 9. 合入 | Task 7 的最后一步 |

最终测试要等 53 张都再生完才提交。波次 1 若提交它，动画和板卡还是旧色，整套 `discover` 会红，而且规格写明不要在那一步提交这份测试。每一波自己的检查是仓库根的一段 `python3 -`，先在旧图上失败，再生后再通过。

## Global Constraints

- 本计划 PR 不实施刀 C。不改 `assets/`，不改 `tools/`，不改 `stm32-book/`，不升版本，不打 tag，不创建 GitHub Release。CI 变绿不等于本 PR 可以自动合入。等人审完计划再合。
- 实施时可以改的只有：`tools/svgkit.py`、`tools/gen_sample_figures.py`、`tools/gen_diagrams.py`、`tools/anim_basics.py`、`tools/anim_gpio.py`、`tools/anim_comm.py`、`tools/anim_sys.py`、`tools/gen_boards.py`、`tools/gen_pinouts.py`、下面这 53 张 SVG、`assets/README.md` 的那一句、`stm32-book/tests/test_sample_svg_c.py`、`stm32-book/tests/test_build.py` 里的版本断言、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。
- 目标版本是 **1.2.7 · 2026-10-25**。日期写死 `2026-10-25`。设计规格里「日期用实施当天」那一句，按本计划改成这个冻住的日期。两份 manifest、`revisions.json` 和 README 写同一个日期。
- 三波是同一次实施 PR 里的顺序，不是三个版本。三波都进 1.2.7。前一波的检查没过，就不开始下一波。不要在波次 1 或波次 2 之后就开实施 PR。
- 实施 PR 在 Book CI（`.github/workflows/book.yml`，名称 `Book CI`）的 `book` 与 `book-en` 都变绿之后 squash 合入 `main`。不改 workflow。不改正文，不设第二次章节 HTML 人审。Book CI 不跑 `tools/check_assets.py`。`check_assets.py` 由实施者在 Task 7 本地跑。
- 不打 tag，不创建 GitHub Release。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 53 张 SVG 只许由生成器写回。不手改成品，不用编辑器改一个 `fill`。不把 SVG 挪进 `stm32-book/styles/` 或 `stm32-book/assets/`。
- 浅色纸底。`T` 只改规格调色表里的那些赋值，并删除 `WHITE`。`FONT` 与 `MONO` 两行保持原文，仍含 `PingFang SC` 和 `Hiragino Sans GB`。不把 `--font-sans` 抄进 `<text>`。不加 `@font-face`，不写 `url(`。
- `#c4552a` 不进入 `T`，也不进入这 53 张。`#9a3d1c` 同样不进入。失败色是 `#8f2d2d`，注意色是 `#7a4e00`。这两个只写在 `T` 里，不写进 `tokens.json`。
- 描边只留 `1`、`1.5`、`2`。圆角只留 `2`、`4`、`8`。`rx=0` 或省略 `rx` 保持。圆没有 `rx`。映射表：

| 现在的描边 | 改成 |
| --- | --- |
| `1` | `1` |
| `1.2` | `1` |
| `1.4`、`1.5`、`1.6` | `1.5` |
| `1.8`、`2`、`2.2`、`2.4`、`2.6`、`3` | `2` |

| 现在的圆角 | 改成 |
| --- | --- |
| `1`、`1.5`、`2`、`2.5`、`3` | `2` |
| `4`、`5`、`6`、`7` | `4` |
| `8`、`9`、`10`、`11`、`12`、`14`、`16` | `8` |

- 零件色不收进这三档语义色。`PCB`、`SILK`、`GOLD`、`PAD` 和芯片体的 `#1b1f28`、`#dfe6f0`、`#8b98b0` 保持。`led()` 里的 `#ffffff` 高光和 `#00000066` 描边保持原文。不新增零件色。
- 不改 `book.css`、`tokens.json`、`load_css()`、`schema`。拼好的 CSS 哈希保持 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。对不上时停，不要改这个哈希，也不要改样式来凑。
- 不改 `stm32-book/cover.svg`。不重画 `assets/gif/`、`assets/photos/`、`assets/video/`、`assets/wechat/`。不改 `tools/gen_gifs.py`、`tools/minigfx.py`、`tools/svg2gif.py`、`tools/gen_tietu.py`、`tools/gen_narrated.py`、`tools/gen_videos.py`、`tools/gen_mp_covers.py`、`tools/check_assets.py`、`tools/gen_animations.py`。
- 不改坐标、宽高、`viewBox`、字号、句子、引脚顺序、`pitch`、`label_room`。不改动画时长、类名和 `@keyframes` 正文。不给 `i2c-transaction.svg` 补 `<style>` 或 `<animate`。
- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、两份 `CONTENT_GUIDE.md`、罗盘文案、`revisions.json` 里已有句子、章节里的图路径和图注。不改 `toc_html`、分类函数、罗盘 HTML、书签、章号。出版书签仍是 44 条。
- 除 `assets/boards/pinout-stm32h743zi-lqfp144.svg` 以外，每张 SVG 的 UTF-8 长度必须小于 `60 * 1024`。H743 这张小于 `80 * 1024`，可以大于 60 KB。不拆图，不把仓库默认的 60 KB 改成 80 KB。样本章和三份 batch 测试继续用 60 KB 锁十二张 `sample-*.svg`。
- `assets/gif/` 的 40 个文件一个字节都不改。汇总哈希保持 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。不把已经超过 500 KB 的 `*-zh.gif` 收进新的失败条件，也不把它们重新压小。
- 四个既有视觉方法和封面两个方法的函数体一个断言都不改：`test_visual_polish_css_contract`、`test_typography_e_css_contract`、`test_visual_polish_contrast_clears_4_5`、`test_code_glossary_and_print_css_keep_reading_units_movable`、`test_cover_svg_stays_self_contained`、`test_cover_imprint_d_contract`。`test_css_token_extract_contract` 里的哈希字符串也不改。
- 不删 `0x271`、`167 ns`、出版书签长度为 44、样本章和各批加厚的断言。`pageOverflow` 为 0 的 1200、840、390 三档不放宽。
- 修订说明只用设计里的四句。不写下一刀，也不写章节名。已有修订句子一字不改。
- `assets/README.md` 只加规格里那一句。不改第 124 行「这 5 张 SVG 还没有对应动图」。

上一句「Book CI 变绿后 squash 合入」指刀 C 的实施 PR。本计划文件的 PR 等人审阅，不在 CI 变绿后自动合入，也不在本 PR 里改 `assets/`、`tools/` 或版本。

## 开工条件

实施开始时先读实施分支所基于的 `main` 上的 `stm32-book/manifest.json`，只看 `version` 和 `date`。不要在本计划的分支上改生成器、SVG 或版本。

- `version` 低于 `1.2.6`：停。刀 D 还没在这条历史上。不开实施分支。
- `version` 是 `1.2.6` 且 `date` 是 `2026-10-25`：实施版写成 `1.2.7`，日期写成 `2026-10-25`。下面任务里的字面量按这个走。这是预期路径。`ed82805` 就是这个状态。
- `version` 已经高于 `1.2.6`（仍是 `1.2.x`，且补丁号大于 6）：实施版写成下一条修订号。不把 `1.2.7` 硬套上去。日期仍是 `2026-10-25`。Task 6 里每一处 `1.2.7` 换成这个新号，每一处当作「上一版」的 `1.2.6` 换成当时 manifest 的 `version`。修订四句不变。已有修订句子保持原文，只把索引后移一位。
- `date` 已经不是 `2026-10-25`：停。不要把本计划里冻住的日期写到另一天的书上。先对人说明。

接着核对样式。在仓库根运行：

```bash
python3 - << 'PY'
import hashlib
import importlib.util
from pathlib import Path
path = Path("stm32-book/build_html.py")
spec = importlib.util.spec_from_file_location("stm32_book_builder", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(hashlib.sha256(module.CSS.encode("utf-8")).hexdigest())
for rel in (
    "stm32-book/styles/book.css",
    "stm32-book/styles/tokens.json",
    "stm32-book/cover.svg",
):
    print(rel, hashlib.sha256(Path(rel).read_bytes()).hexdigest())
PY
```

Expected:

```text
a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4
stm32-book/styles/book.css 7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5
stm32-book/styles/tokens.json c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b
stm32-book/cover.svg 37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd
```

不是这些值就停。本刀不改样式，也不重新计算样式哈希。

然后在还没改生成器的时候，于仓库根按这个顺序跑一遍：

```bash
python3 tools/gen_sample_figures.py
python3 tools/gen_diagrams.py
python3 tools/gen_animations.py
python3 tools/gen_boards.py
python3 tools/gen_pinouts.py
git diff --stat -- assets
```

Expected: `git diff --stat -- assets` 无输出。`gen_sample_figures.py` 不打印 `[ok]`。`gen_diagrams.py` 打印 6 行 `[ok]`。`gen_animations.py` 的最后一行是 `共生成 25 个动画`。`gen_boards.py` 打印 7 行 `[ok]`。`gen_pinouts.py` 打印 3 行 `pins ok`。

若 `assets/` 的 diff 不为空，停。说明 `main` 上的 SVG 已经和生成器分叉。不要在分叉上套这套调色，也不要提交这次再生。用 `git checkout -- assets` 把成品还原后再停。

`validate_revisions()` 在 `build_html.py` 第 820 行。它要求 `revisions.json` 第一条的 `version` 等于 manifest 的 `version`。Task 6 必须同一提交改测试、两份 manifest、`revisions.json` 和 README。

## 收档脚本

Task 1、Task 2、Task 3 用同一段脚本收 `sw=` 和 `rx=` 的数字实参。不要把脚本存进仓库。不要对 `tools/gen_tietu.py`、`tools/minigfx.py`、`tools/svg2gif.py`、`tools/gen_gifs.py`、`tools/check_assets.py` 运行它。

脚本只替换完整的 `sw=<数字>` 和 `rx=<数字>`。`rx=10` 不会被 `rx=1` 的规则切成 `rx=20`。`rx=r - 4` 不是数字实参，保持原文。圆的半径 `r=13` 不是圆角，保持原文。`board()` 的 `r=14` 不归这段脚本，Task 3 单独改成 `r=8`。

未出现在映射表里的数字必须让脚本以退出码 1 结束，并且不写文件。不要临时加一档。

`ed82805` 上，脚本会改掉的实参个数是：

| 文件 | 改掉的实参 |
| --- | --- |
| `tools/svgkit.py` | 6 |
| `tools/gen_sample_figures.py` | 7 |
| `tools/gen_diagrams.py` | 44 |
| `tools/anim_basics.py` | 20 |
| `tools/anim_gpio.py` | 30 |
| `tools/anim_comm.py` | 25 |
| `tools/anim_sys.py` | 62 |
| `tools/gen_boards.py` | 42 |
| `tools/gen_pinouts.py` | 3 |

这 6 处 `svgkit.py` 就是 `panel()` 的 `rx=12`、`box()` 的 `rx=10`、`waveform()` 的 `sw=2.4`、`axis()` 的两处 `sw=1.4`、`legend()` 的 `rx=3`。矩形、线、路径、圆、多边形的默认 `sw=1.5` 不在这 6 处里。`arrow()` 的 `sw=2`、`chip()` 的 `rx=8`、`grid()` 和页眉页脚的 `sw=1`、`led()` 的 `sw=1` 也不在里。

个数对不上就停。先确认开工条件的再生 diff 仍为空。不要为了凑个数去改句子或坐标。

脚本正文：

```python
import re
from pathlib import Path

SW = {
    "1": "1",
    "1.2": "1",
    "1.4": "1.5",
    "1.5": "1.5",
    "1.6": "1.5",
    "1.8": "2",
    "2": "2",
    "2.2": "2",
    "2.4": "2",
    "2.6": "2",
    "3": "2",
}
RX = {
    "0": "0",
    "1": "2",
    "1.5": "2",
    "2": "2",
    "2.5": "2",
    "3": "2",
    "4": "4",
    "5": "4",
    "6": "4",
    "7": "4",
    "8": "8",
    "9": "8",
    "10": "8",
    "11": "8",
    "12": "8",
    "14": "8",
    "16": "8",
}
PAT = re.compile(r"\b(sw|rx)=(\d+(?:\.\d+)?)")


def remap(text: str) -> tuple[str, int]:
    changed = 0

    def sub(match: re.Match) -> str:
        nonlocal changed
        kind, raw = match.group(1), match.group(2)
        table = SW if kind == "sw" else RX
        if raw not in table:
            raise SystemExit(f"unmapped {kind}={raw}")
        new = table[raw]
        if new != raw:
            changed += 1
        return f"{kind}={new}"

    return PAT.sub(sub, text), changed


for path_text in (
    "tools/svgkit.py",
    "tools/gen_sample_figures.py",
    "tools/gen_diagrams.py",
):
    path = Path(path_text)
    new, changed = remap(path.read_text(encoding="utf-8"))
    path.write_text(new, encoding="utf-8")
    print(f"{path} {changed}")
```

上面这份就是 Task 1 的文件列表。Task 2 和 Task 3 的命令已经把列表换成自己的文件。不要改成 `sys.argv`，以免把 `gen_tietu.py` 收进去。期望的个数印在该任务的 Step 里。

## File map

| 路径 | 实施时的责任 |
| --- | --- |
| `docs/superpowers/plans/2026-10-25-book-visual-sample-svg-C.md` | 本计划。本 PR 只新增这一份 |
| `tools/svgkit.py` | Task 1。改 `T` 的颜色，删除 `WHITE`，再用收档脚本改 6 个默认 `rx` / `sw`。不改 `render()`、`led()`、`FONT`、`MONO`、动画助手，也不改模块文档字符串里的「深色卡片」 |
| `tools/gen_sample_figures.py` | Task 1。收档脚本把 `gpio_led()` 的 4 处 `rx=10` 和 2 处 `rx=6`、`uart_frame()` 的 1 处 `rx=6` 收进档。不改句子和坐标 |
| `tools/gen_diagrams.py` | Task 1。收档脚本收 `sw` / `rx`。另外只改优先级色条和 `l4_idd_bench()` 里点名的填充与描边 |
| `tools/anim_basics.py`、`anim_gpio.py`、`anim_comm.py`、`anim_sys.py` | Task 2。先改点名的 `#0b1220` 和 `T.WHITE`，再收档。不改类名和 `@keyframes` 正文 |
| `tools/gen_boards.py` | Task 3。`board()` 的 `r=14` 改为 `8`，`header()` 的脚名改为 `fill=T.TEXT`，再收档。`SILK` 常量保持 |
| `tools/gen_pinouts.py` | Task 3。只收档。`_color()` 仍返回 `T` 的成员。芯片体三色保持 |
| `assets/diagrams/*.svg` 这 18 张 | Task 1 只再生 |
| `assets/animations/*.svg` 这 25 张 | Task 2 只再生 |
| `assets/boards/*.svg` 这 10 张 | Task 3 只再生 |
| `assets/README.md` | Task 4。在生成命令代码块下面加一句 |
| `stm32-book/tests/test_sample_svg_c.py` | Task 5 新建 |
| `stm32-book/tests/test_build.py` | Task 6 只改版本断言 |
| `stm32-book/manifest.json`、`manifest-en.json` | Task 6：`version` 改为 `1.2.7`，`date` 保持 `2026-10-25` |
| `stm32-book/revisions.json` | Task 6：`entries` 最前插入 1.2.7。已有条目一字不改 |
| `stm32-book/README.md` | Task 6：当前版本句、发布节的版本句、tag 名，以及新的误标句 |

`stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`stm32-book/cover.svg`、`assets/gif/` 不在实施 diff 里。它们必须是空的。

## 画布与文本哈希

第三列是改之前的 UTF-8 字节数。测试不断言这一列相等。再生之后字节数会变。断言的是宽、高和第四列的文本哈希。H743 的 75786 只是基线，不是上限。上限是 `80 * 1024`。

```text
animations/adc-sar.svg 900x620 19409 ebd3127f7efde5d3c25f5a82dea6ae36eaff2a4c3a87c698f95f0d329a0ca807
animations/boot-sequence.svg 900x620 14058 d6d1baa08f2d9763ef5971f4701775db3905d34a7d6998310b127dd21beaddfc
animations/can-arbitration.svg 900x620 23362 6a68426929c8ad0f4046b091ae4be6db894eba2e4125f1e03c41c695167a3176
animations/clock-tree.svg 900x620 10921 c0e07c5c01bffae9769331541bdf87dcfc4ea61e3b4081b6f72834b476fbed08
animations/debug-swo.svg 900x620 12545 e44f13c22225782401c9b3d44f376781297c0103040118786626621476a6ffdd
animations/dma-circular.svg 900x620 16488 7deb7de9dc81e1a01c1c2e01827c131661f5b6d45bb5c2fb1d0473e126041fd1
animations/flash-iap.svg 900x620 12795 55ad4b20f25654a8bb6a705303a99d5fb513f5b125b70a4545278f84d63ad0cb
animations/freertos-scheduler.svg 900x620 15775 fe1bebd106b7c825a5d815edc67842821a8298e6e98036153641ca928c098bb3
animations/g0-boot-swd.svg 900x620 12398 e9121dfb6e5290afd5d192048fa7d7409a821c7651538c80bde3237df535155f
animations/gpio-blink.svg 900x620 14249 811377a9c3b65dd99cbeb8a1ff720b0e4e6410bc852726ac98f9aa20619175ea
animations/gpio-input-interrupt.svg 900x620 13740 4b97aeb339eb046f0091312b6caf918b1acdc176cc72e4295cc7c116792c6697
animations/i2c-transaction.svg 900x620 17483 e5c5b2aca2aae67cc607e3eb929cc0f20c184deceb8815f32a9d4e96f4bef55a
animations/iwdg-window.svg 900x620 10675 324f8c83215265a9e4b9c256552019165c14adb914c3fc9189f054f264751444
animations/l4-stop2-evidence.svg 900x620 13976 ae6b68a3a26ee3995d72dc29bcfcb2bab733a2e54637e4d9a6a8581b9f577e28
animations/lowpower-wakeup.svg 900x620 10766 7a5fe86d6e1a29c7f8e00d177f0ec928c85f7405e8427e8f27209720cc0a22b6
animations/memory-map.svg 900x620 7846 82e9be18ac7ecbe388e478b995ef9bcf8e876a2373406565469fda41e911b11f
animations/network-packet-journey.svg 900x620 18648 0081c4c6270e94527deba9ea9365811c22de28130ee343d8df68797eb36f1016
animations/nvic-interrupt-flow.svg 900x620 12972 07a38a7e7d4b430809683b2beb00f98b3cac0a17fc45bb1a5d066d20c22c9dc4
animations/rtos-system-layers.svg 900x620 13996 1a44f6f16dcc08a20467d946a35a22ef968582f37faf99b5b74f5107deaf31e9
animations/spi-transfer.svg 900x620 18861 579ddd86d159809dc4c667a0bf1faf652c1c0538d4d155f6f7187896df7a3968
animations/timer-modes.svg 900x620 11712 c8a1e34469293d5f4a02a5703271bcf62fc4e9f2f1e89429dbcaa02b56ebeabf
animations/timer-pwm.svg 900x620 10046 54833bf0841b1569cb993934699473b2ee4d2f0ed56b858a4fb9b5855bb8532f
animations/toolchain-flow.svg 900x620 15176 e131ad994e16c099c15d4d941c0e7aade4865c53c912248a73590e939645e0bd
animations/uart-frame.svg 900x620 18533 a696fc8932d337f1b22dacef54ecfe01dd37aa963b41d67111c584122f6b3400
animations/usb-enumeration.svg 900x620 10874 b531c1c1278ee8560a2a4297dd4f36e8dfb5934fc09f7df494faf9d5e455e20d
boards/blackpill-stm32f411ce.svg 900x620 32264 511d86c80d8862e78be2a0c7e6ca7e24e1db11d30ea66d47b3b2f1e8cdec0494
boards/bluepill-stm32f103c8t6.svg 900x620 35647 272634dc07da80d8c5d7e6471d9778310292318aace55acbecfcd92a8d9d4c25
boards/f103zet6-dev.svg 900x620 26509 8d52a625b72cef5f53be80091fc870d3bcf9537b0c178c5aa4ebfcb810ded612
boards/f4-discovery.svg 900x620 26524 d0d4d756b30de2d1a11a43bd78abd0f733dcf2696cc88f708de8cde63cfe659f
boards/nucleo-f411re.svg 900x620 21385 434fa875affbab6a0d987df16919de7b6cfaf88c3703da29593bef68b5006c8b
boards/peripheral-wiring.svg 900x620 13970 a5517214a0d7efcb8721fa41c8fee6224a7deca98f193bf39147ccc3f36fd166
boards/pinout-bluepill.svg 900x620 35176 4de478b58c8d278166311b99311183121ccf1ecb38a50c99450b35e60893cabd
boards/pinout-stm32g071rb-lqfp64.svg 620x750 34523 7ccc8b702e15d0473bfc1d4c956397dfbb5bd50363d4e762bd100c794d1d2193
boards/pinout-stm32h743zi-lqfp144.svg 840x970 75786 4d71ec5cab732513073bac6721ae4c688a36f18ab11fcae4b5e6e927433b7a96
boards/pinout-stm32l476rg-lqfp64.svg 620x750 34508 a5a8468d7b087956a4635ac7c88412f1e7920570c53e388e0a10a44fbe5f8adf
diagrams/interrupt-priority.svg 900x560 11877 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8673 32e1a5b195562947e04d2da8efc2f0c89dd97aed9f7cacbb3c5914ce52f8ec96
diagrams/layers-hal-ll-reg.svg 900x560 10401 60098b25b368c2f6acefb4e9a3152f816506cae44e68b2fb8ffbf0878c049f78
diagrams/network-debug-ladder.svg 900x560 11278 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14071 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13014 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/sample-00-boot-state.svg 960x620 7103 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-01-swd-vectors.svg 960x980 7328 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-clock-tree.svg 960x860 7402 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-03-gpio-led.svg 960x660 8221 932244c2053d317d50bf5106192a79fbf9d1546f16dd00bcf99110b7bd11a8ad
diagrams/sample-04-exception-stack.svg 960x780 7528 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-05-pwm-1khz.svg 960x820 6845 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-06-uart-frame.svg 960x820 12448 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6620 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-08-spi-jedec.svg 960x860 6850 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-09-adc-sar.svg 960x860 6656 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-10-dma-cndtr.svg 960x900 6552 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-11-iwdg-1s.svg 960x980 7169 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
```

---

### Task 1: 波次 1，浅色样本图和静态框图

**Files:**
- Modify: `tools/svgkit.py`（`class T` 第 24–52 行；默认值在第 113、198、262、289、290、323 行，由收档脚本改）
- Modify: `tools/gen_sample_figures.py`（`gpio_led()` 第 65、67、69、74、81、87 行；`uart_frame()` 第 149 行）
- Modify: `tools/gen_diagrams.py`（`interrupt_priority()` 第 223–224 行；`l4_idd_bench()` 第 283–293 行；其余 `sw` / `rx` 由收档脚本改）
- Modify: `assets/diagrams/` 下上表 18 张 SVG，只通过生成器写回
- Test: 这一任务不新增 `stm32-book/tests/test_sample_svg_c.py`

**Interfaces:**
- Consumes: `Svg.rect` 的 `rx` 与 `sw`，`T.BG` 到 `T.PINK` 的现有名字。`gen_sample_figures.py` 和 `gen_diagrams.py` 不引用 `T.WHITE`。
- Produces: `T.BG == "#fbfaf7"`，`T.CYAN == "#075e84"`，`T` 上不再有 `WHITE`。18 张框图不再含 `#0b1220`。动画和板卡这一任务结束时仍是旧字节。Task 2 才能 `import` 已经删除 `WHITE` 的 `svgkit`；在 Task 2 改完三处 `T.WHITE` 之前，不要运行 `gen_animations.py`，否则 `memory_map()` 和 `iwdg_window()` 会在 `T.WHITE` 上抛 `AttributeError`。

`gen_sample_figures.py` 只写 12 张 `sample-*.svg`。`gen_diagrams.py` 只写 6 张非样本框图。两个脚本都写到 `assets/diagrams/`，文件名不重叠。不要在这一任务运行 `gen_animations.py`、`gen_boards.py`、`gen_pinouts.py`。

- [ ] **Step 1: 先确认这 18 张还是旧底**

在仓库根运行。`ROWS` 用上面「画布与文本哈希」里 18 行 `diagrams/` 开头的记录，一行不差。

```bash
python3 - << 'PY'
import hashlib, re
from pathlib import Path
ROWS = """
diagrams/interrupt-priority.svg 900x560 11877 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8673 32e1a5b195562947e04d2da8efc2f0c89dd97aed9f7cacbb3c5914ce52f8ec96
diagrams/layers-hal-ll-reg.svg 900x560 10401 60098b25b368c2f6acefb4e9a3152f816506cae44e68b2fb8ffbf0878c049f78
diagrams/network-debug-ladder.svg 900x560 11278 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14071 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13014 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/sample-00-boot-state.svg 960x620 7103 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-01-swd-vectors.svg 960x980 7328 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-clock-tree.svg 960x860 7402 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-03-gpio-led.svg 960x660 8221 932244c2053d317d50bf5106192a79fbf9d1546f16dd00bcf99110b7bd11a8ad
diagrams/sample-04-exception-stack.svg 960x780 7528 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-05-pwm-1khz.svg 960x820 6845 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-06-uart-frame.svg 960x820 12448 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6620 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-08-spi-jedec.svg 960x860 6850 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-09-adc-sar.svg 960x860 6656 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-10-dma-cndtr.svg 960x900 6552 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-11-iwdg-1s.svg 960x980 7169 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
""".strip().splitlines()
failed = False
for line in ROWS:
    rel, wh, _size, digest = line.split()
    text = Path("assets", rel).read_text(encoding="utf-8")
    if "#0b1220" not in text:
        failed = True
        print("already light", rel)
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", text, flags=re.DOTALL)
    got = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    if got != digest:
        failed = True
        print("text hash", rel, got)
print("FAIL" if failed else "OLD-AND-STABLE")
raise SystemExit(1 if failed else 0)
PY
```

Expected: 退出码 1，输出里有 `FAIL`，并且 18 行都不会打印 `text hash`。打印 `already light` 才是异常，那说明这 18 张已经被动过，停。退出码 0 且输出 `OLD-AND-STABLE` 也停：说明 `#0b1220` 已经不在，基线和规格不一致。

这一步的失败是预期。不要提交。

- [ ] **Step 2: 改 `T`，并改框图里点名的填充**

把 `tools/svgkit.py` 的 `class T` 整段换成：

```python
class T:
    """配色 / 尺寸常量。"""

    BG = "#fbfaf7"
    BG2 = "#f1f5f7"
    PANEL = "#f1f5f7"
    PANEL2 = "#e5f3f8"
    STROKE = "#5e6872"
    GRID = "#d7dce1"

    TEXT = "#17202a"
    MUTED = "#5e6872"
    DIM = "#5e6872"

    CYAN = "#075e84"
    BLUE = "#1e4d63"
    GREEN = "#1b5c45"
    AMBER = "#7a4e00"
    ORANGE = "#9a3412"
    RED = "#8f2d2d"
    VIOLET = "#5b3a8c"
    PINK = "#8e2f5b"

    FONT = ("'PingFang SC','Hiragino Sans GB','Microsoft YaHei',system-ui,"
            "-apple-system,'Segoe UI',sans-serif")
    MONO = ("ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,"
            "'Courier New',monospace")
```

`WHITE = "#f8fafc"` 这一行删掉，不要留空行代替它。`FONT` 和 `MONO` 的引号和断行保持上面这样。不要改文件开头的模块文档字符串。不要改 `led()`。

在 `tools/gen_diagrams.py` 的 `interrupt_priority()` 里，把：

```python
        s.text(80 + x + w / 2, 151 + row * 50, label, size=10.5,
               anchor="middle", fill="#0b1220", weight="700")
```

换成：

```python
        s.text(80 + x + w / 2, 151 + row * 50, label, size=10.5,
               anchor="middle", fill="#fbfaf7", weight="700")
```

在 `l4_idd_bench()` 里只改这七处，句子不改：

```python
    s.rect(500, 108, 346, 68, fill="#0d2b22", stroke="#8b98b0", rx=10)
    s.text(673, 134, "ST-LINK 区", size=13, anchor="middle", fill="#dfe6f0", weight="700")
    s.text(673, 158, "功能调试可接；功耗测量需排查回灌", size=9.5,
           anchor="middle", fill="#e2b23c")
    s.rect(500, 190, 346, 122, fill="#123057", stroke="#7aa2ff", rx=10)
    s.text(673, 216, "目标 MCU 供电域", size=13, anchor="middle", fill="#dfe6f0",
           weight="700")
    s.text(673, 260, "STM32L476RG", size=10.5, anchor="middle", mono=True,
           fill="#dfe6f0", weight="700")
    s.text(673, 279, "VDD / VSS", size=9, anchor="middle", mono=True, fill="#8b98b0")
```

这七处里的 `rx=10` 先留着，下一步收档脚本会收成 `rx=8`。外框 `fill="#123a2e"` 和芯片体 `fill="#151922"` 不改。不要把 `T.TEXT` 用到这块深绿板上。

- [ ] **Step 3: 收这三份源码的描边和圆角**

把收档脚本存成一次性的标准输入，文件列表用这三份。在仓库根运行：

```bash
python3 - << 'PY'
import re
import sys
from pathlib import Path

SW = {
    "1": "1", "1.2": "1", "1.4": "1.5", "1.5": "1.5", "1.6": "1.5",
    "1.8": "2", "2": "2", "2.2": "2", "2.4": "2", "2.6": "2", "3": "2",
}
RX = {
    "0": "0", "1": "2", "1.5": "2", "2": "2", "2.5": "2", "3": "2",
    "4": "4", "5": "4", "6": "4", "7": "4", "8": "8", "9": "8",
    "10": "8", "11": "8", "12": "8", "14": "8", "16": "8",
}
PAT = re.compile(r"\b(sw|rx)=(\d+(?:\.\d+)?)")

def remap(text: str) -> tuple[str, int]:
    changed = 0
    def sub(match: re.Match) -> str:
        nonlocal changed
        kind, raw = match.group(1), match.group(2)
        table = SW if kind == "sw" else RX
        if raw not in table:
            raise SystemExit(f"unmapped {kind}={raw}")
        new = table[raw]
        if new != raw:
            changed += 1
        return f"{kind}={new}"
    return PAT.sub(sub, text), changed

for path_text in (
    "tools/svgkit.py",
    "tools/gen_sample_figures.py",
    "tools/gen_diagrams.py",
):
    path = Path(path_text)
    new, changed = remap(path.read_text(encoding="utf-8"))
    path.write_text(new, encoding="utf-8")
    print(f"{path} {changed}")
PY
```

Expected:

```text
tools/svgkit.py 6
tools/gen_sample_figures.py 7
tools/gen_diagrams.py 44
```

然后核对默认值已经落在档内：

```bash
python3 - << 'PY'
from pathlib import Path
text = Path("tools/svgkit.py").read_text(encoding="utf-8")
for needle in (
    "def panel(self, x, y, w, h, rx=8, fill=T.PANEL, stroke=T.STROKE)",
    "color=T.TEXT, rx=8, size=15, cls=None, mono=False,",
    "def waveform(self, x, y, w, h, bits, color=T.GREEN, sw=2, cls=None,",
    "self.line(x, y, x, y + h, stroke=color, sw=1.5)",
    "self.line(x, y + h, x + w, y + h, stroke=color, sw=1.5)",
    "self.rect(x + i * dx, y - 10, 12, 12, fill=c, rx=2)",
    'BG = "#fbfaf7"',
    'CYAN = "#075e84"',
):
    if needle not in text:
        raise SystemExit(needle)
if "WHITE" in text or "#0b1220" in text or "#22d3ee" in text:
    raise SystemExit("old token still in svgkit")
sample = Path("tools/gen_sample_figures.py").read_text(encoding="utf-8")
if "rx=10" in sample or "rx=6" in sample:
    raise SystemExit("sample radius")
print("ok")
PY
```

Expected: `ok`。`chip()` 的 `rx=8` 和 `arrow()` 的 `sw=2` 仍在。`header()` 里宽度为 4 的色条仍是 `self.rect(0, 0, 4, 58, fill=tag_color)`，那是矩形宽度，不是描边。

- [ ] **Step 4: 只再生这 18 张**

```bash
python3 tools/gen_sample_figures.py
python3 tools/gen_diagrams.py
```

Expected: `gen_diagrams.py` 打印这 6 行，`gen_sample_figures.py` 无输出，两个命令的退出码都是 0。

```text
[ok] layers-hal-ll-reg.svg
[ok] project-structure.svg
[ok] peripheral-bus.svg
[ok] interrupt-priority.svg
[ok] l4-idd-bench.svg
[ok] network-debug-ladder.svg
```

- [ ] **Step 5: 核对 18 张，并确认动画、板卡、GIF 没被写到**

```bash
python3 - << 'PY'
import hashlib, re
from pathlib import Path
ROWS = """
diagrams/interrupt-priority.svg 900x560 11877 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8673 32e1a5b195562947e04d2da8efc2f0c89dd97aed9f7cacbb3c5914ce52f8ec96
diagrams/layers-hal-ll-reg.svg 900x560 10401 60098b25b368c2f6acefb4e9a3152f816506cae44e68b2fb8ffbf0878c049f78
diagrams/network-debug-ladder.svg 900x560 11278 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14071 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13014 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/sample-00-boot-state.svg 960x620 7103 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-01-swd-vectors.svg 960x980 7328 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-clock-tree.svg 960x860 7402 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-03-gpio-led.svg 960x660 8221 932244c2053d317d50bf5106192a79fbf9d1546f16dd00bcf99110b7bd11a8ad
diagrams/sample-04-exception-stack.svg 960x780 7528 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-05-pwm-1khz.svg 960x820 6845 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-06-uart-frame.svg 960x820 12448 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6620 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-08-spi-jedec.svg 960x860 6850 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-09-adc-sar.svg 960x860 6656 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-10-dma-cndtr.svg 960x900 6552 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-11-iwdg-1s.svg 960x980 7169 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
""".strip().splitlines()
ALLOWED = {
    "#fbfaf7", "#f1f5f7", "#e5f3f8", "#5e6872", "#d7dce1", "#17202a",
    "#075e84", "#1e4d63", "#1b5c45", "#7a4e00", "#9a3412", "#8f2d2d",
    "#5b3a8c", "#8e2f5b", "#ffffff",
    "#00000055", "#00000066", "#00000088", "#08214a", "#08224a", "#0a0d13",
    "#0a1f5e", "#0a2a52", "#0b2c4c", "#0c0f16", "#0c2242", "#0d2b22",
    "#0e3b6e", "#0f2f8a", "#0f3f6b", "#123057", "#123a2e", "#141821",
    "#151922", "#153a9e", "#1b1f28", "#1d4ed8", "#2a3242", "#2b3038",
    "#39424f", "#4a5260", "#59606c", "#5b6472", "#5d6470", "#7aa2ff",
    "#7fd4ff", "#808a9a", "#8b98b0", "#8d7420", "#8d949e", "#9aa4b2",
    "#9db8ff", "#bcd8ff", "#c4b5fd", "#c9ced6", "#cfe0ff", "#d8b23a",
    "#dbeafe", "#dfe6f0", "#e2b23c", "#e7ebf0", "#e8f1ff", "#ffffff22",
}
BANNED = {
    "#0b1220", "#0e1626", "#111c31", "#16233c", "#243354", "#1a2742",
    "#e6edf3", "#93a4c0", "#64748b", "#22d3ee", "#60a5fa", "#34d399",
    "#fbbf24", "#fb923c", "#f87171", "#a78bfa", "#f472b6", "#f8fafc",
    "#c4552a", "#9a3d1c",
}
for line in ROWS:
    rel, wh, _size, digest = line.split()
    width, height = wh.split("x")
    path = Path("assets", rel)
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    if len(raw) >= 60 * 1024:
        raise SystemExit(f"size {rel} {len(raw)}")
    attrs = re.search(r"<svg\b([^>]*)>", text).group(1)
    if re.search(r'\bwidth="(\d+)"', attrs).group(1) != width:
        raise SystemExit(f"width {rel}")
    if re.search(r'\bheight="(\d+)"', attrs).group(1) != height:
        raise SystemExit(f"height {rel}")
    if f'viewBox="0 0 {width} {height}"' not in text:
        raise SystemExit(f"viewBox {rel}")
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", text, flags=re.DOTALL)
    got = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    if got != digest:
        raise SystemExit(f"text {rel} {got}")
    colors = {
        item.lower()
        for item in re.findall(r"#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})(?![0-9A-Fa-f])", text)
    }
    bad = colors - ALLOWED
    if bad or colors & BANNED:
        raise SystemExit(f"color {rel} {sorted(bad or colors & BANNED)}")
    strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
    if not strokes <= {"1", "1.5", "2"}:
        raise SystemExit(f"sw {rel} {strokes}")
    radii = set(re.findall(r'\brx="([^"]+)"', text))
    if not radii <= {"2", "4", "8"}:
        raise SystemExit(f"rx {rel} {radii}")
    if "stroke-width:" in text:
        raise SystemExit(f"css stroke {rel}")
    if rel.startswith("diagrams/sample-"):
        for banned in ("<animate", "@keyframes", "animation:", "矢量动画"):
            if banned in text:
                raise SystemExit(f"{banned} {rel}")
        if "自绘" not in text:
            raise SystemExit(f"credit {rel}")
    elif "自绘矢量动画" not in text:
        raise SystemExit(f"footer {rel}")
print("18 ok")
PY
git diff --stat -- assets/animations assets/boards assets/gif stm32-book/cover.svg stm32-book/styles
```

Expected: 第一段打印 `18 ok`，退出码 0。第二段无输出。

再跑已有的样本章测试。它们锁句子和 60 KB，不锁颜色：

```bash
python3 -m unittest discover stm32-book/tests -v
```

Expected: 退出码 0。这一任务还没加 `test_sample_svg_c.py`，所以 `discover` 不会去要 53 张一起变浅。若这里失败，修生成器，不要改已有测试的句子断言。

- [ ] **Step 6: 提交波次 1**

```bash
git add tools/svgkit.py tools/gen_sample_figures.py tools/gen_diagrams.py assets/diagrams
git commit -m "book: 刀 C 波次 1，浅色样本图与静态框图"
```

不要把 `assets/animations/`、`assets/boards/`、`assets/gif/` 加进这次提交。不要开实施 PR。

---

### Task 2: 波次 2，浅色动画

**Files:**
- Modify: `tools/anim_basics.py`（`memory_map()` 第 187 行的 `fill=T.WHITE`）
- Modify: `tools/anim_gpio.py`（第 139 行「命中」、第 157 行「ISR」）
- Modify: `tools/anim_comm.py`（只收 `sw` / `rx`）
- Modify: `tools/anim_sys.py`（第 45 行「CNT」；`iwdg_window()` 第 317–318 行的 `T.WHITE`）
- Modify: `assets/animations/*.svg` 这 25 张，只通过 `python3 tools/gen_animations.py` 写回
- Test: 仍不新增 `test_sample_svg_c.py`

**Interfaces:**
- Consumes: Task 1 已经删除的 `T.WHITE`，以及 `T.TEXT == "#17202a"`、`T.BG == "#fbfaf7"`。`gen_animations.py` 只导入四个 `anim_*.py` 的 `ALL` 和 `NAMES`，本任务不改那个文件。
- Produces: 25 张动画不再含 `#0b1220` 和 `#22d3ee`。`i2c-transaction.svg` 仍没有 `<style` 和 `<animate`。板卡这一任务结束时仍是旧字节。

25 张和四个模块的对应是：

| 模块 | 成品 |
| --- | --- |
| `anim_basics.py` | `toolchain-flow.svg`、`boot-sequence.svg`、`memory-map.svg`、`clock-tree.svg` |
| `anim_gpio.py` | `gpio-blink.svg`、`gpio-input-interrupt.svg`、`nvic-interrupt-flow.svg`、`debug-swo.svg` |
| `anim_comm.py` | `uart-frame.svg`、`i2c-transaction.svg`、`spi-transfer.svg`、`can-arbitration.svg`、`usb-enumeration.svg`、`network-packet-journey.svg` |
| `anim_sys.py` | `timer-pwm.svg`、`timer-modes.svg`、`adc-sar.svg`、`dma-circular.svg`、`iwdg-window.svg`、`flash-iap.svg`、`freertos-scheduler.svg`、`lowpower-wakeup.svg`、`l4-stop2-evidence.svg`、`rtos-system-layers.svg`、`g0-boot-swd.svg` |

- [ ] **Step 1: 先改三处旧字色，再收档**

`tools/anim_gpio.py`：

```python
    s.text(88 + 6 * 56, y + 10, "命中", size=11, anchor="middle", fill="#fbfaf7",
           weight="700")
```

```python
    s.text(394, y2 + 10, "ISR", size=11, anchor="middle", fill="#fbfaf7",
           weight="700")
```

`tools/anim_sys.py`：

```python
    s.text(54, 132, "CNT", size=9, anchor="middle", fill="#fbfaf7", weight="700")
```

```python
    s.text(48, 132, "0xFFF", size=10, fill=T.TEXT, mono=True)
    s.text(820, 132, "0", size=10, fill=T.TEXT, anchor="end", mono=True)
```

`tools/anim_basics.py`：

```python
    s.circle(872, 131, 7, fill=T.TEXT, opacity=0.85, cls="ptr")
```

`cls="ptr"`、`cls="hit"`、`cls="isr"`、`cls="cnt"`、`cls="dec"` 都留下。不要改 `add_style(...)` 的字符串。

然后对这四个文件跑收档脚本。在仓库根运行：

```bash
python3 - << 'PY'
import re
from pathlib import Path

SW = {
    "1": "1", "1.2": "1", "1.4": "1.5", "1.5": "1.5", "1.6": "1.5",
    "1.8": "2", "2": "2", "2.2": "2", "2.4": "2", "2.6": "2", "3": "2",
}
RX = {
    "0": "0", "1": "2", "1.5": "2", "2": "2", "2.5": "2", "3": "2",
    "4": "4", "5": "4", "6": "4", "7": "4", "8": "8", "9": "8",
    "10": "8", "11": "8", "12": "8", "14": "8", "16": "8",
}
PAT = re.compile(r"\b(sw|rx)=(\d+(?:\.\d+)?)")

def remap(text: str) -> tuple[str, int]:
    changed = 0
    def sub(match: re.Match) -> str:
        nonlocal changed
        kind, raw = match.group(1), match.group(2)
        table = SW if kind == "sw" else RX
        if raw not in table:
            raise SystemExit(f"unmapped {kind}={raw}")
        new = table[raw]
        if new != raw:
            changed += 1
        return f"{kind}={new}"
    return PAT.sub(sub, text), changed

for path_text in (
    "tools/anim_basics.py",
    "tools/anim_gpio.py",
    "tools/anim_comm.py",
    "tools/anim_sys.py",
):
    path = Path(path_text)
    new, changed = remap(path.read_text(encoding="utf-8"))
    path.write_text(new, encoding="utf-8")
    print(f"{path} {changed}")
PY
```

Expected:

```text
tools/anim_basics.py 20
tools/anim_gpio.py 30
tools/anim_comm.py 25
tools/anim_sys.py 62
```

```bash
grep -n 'T\.WHITE\|fill="#0b1220"' tools/anim_basics.py tools/anim_gpio.py tools/anim_comm.py tools/anim_sys.py tools/svgkit.py tools/gen_diagrams.py
```

Expected: 无输出，退出码 1。`grep` 没找到时退出码就是 1。

- [ ] **Step 2: 只再生 25 张动画**

```bash
python3 tools/gen_animations.py
```

Expected: 退出码 0，最后一行是 `共生成 25 个动画`。不要运行 `tools/svg2gif.py`。不要运行 `tools/gen_gifs.py`。

- [ ] **Step 3: 核对 25 张，并确认板卡和 GIF 没被写到**

```bash
python3 - << 'PY'
import hashlib, re
from pathlib import Path
ROWS = """
animations/adc-sar.svg 900x620 19409 ebd3127f7efde5d3c25f5a82dea6ae36eaff2a4c3a87c698f95f0d329a0ca807
animations/boot-sequence.svg 900x620 14058 d6d1baa08f2d9763ef5971f4701775db3905d34a7d6998310b127dd21beaddfc
animations/can-arbitration.svg 900x620 23362 6a68426929c8ad0f4046b091ae4be6db894eba2e4125f1e03c41c695167a3176
animations/clock-tree.svg 900x620 10921 c0e07c5c01bffae9769331541bdf87dcfc4ea61e3b4081b6f72834b476fbed08
animations/debug-swo.svg 900x620 12545 e44f13c22225782401c9b3d44f376781297c0103040118786626621476a6ffdd
animations/dma-circular.svg 900x620 16488 7deb7de9dc81e1a01c1c2e01827c131661f5b6d45bb5c2fb1d0473e126041fd1
animations/flash-iap.svg 900x620 12795 55ad4b20f25654a8bb6a705303a99d5fb513f5b125b70a4545278f84d63ad0cb
animations/freertos-scheduler.svg 900x620 15775 fe1bebd106b7c825a5d815edc67842821a8298e6e98036153641ca928c098bb3
animations/g0-boot-swd.svg 900x620 12398 e9121dfb6e5290afd5d192048fa7d7409a821c7651538c80bde3237df535155f
animations/gpio-blink.svg 900x620 14249 811377a9c3b65dd99cbeb8a1ff720b0e4e6410bc852726ac98f9aa20619175ea
animations/gpio-input-interrupt.svg 900x620 13740 4b97aeb339eb046f0091312b6caf918b1acdc176cc72e4295cc7c116792c6697
animations/i2c-transaction.svg 900x620 17483 e5c5b2aca2aae67cc607e3eb929cc0f20c184deceb8815f32a9d4e96f4bef55a
animations/iwdg-window.svg 900x620 10675 324f8c83215265a9e4b9c256552019165c14adb914c3fc9189f054f264751444
animations/l4-stop2-evidence.svg 900x620 13976 ae6b68a3a26ee3995d72dc29bcfcb2bab733a2e54637e4d9a6a8581b9f577e28
animations/lowpower-wakeup.svg 900x620 10766 7a5fe86d6e1a29c7f8e00d177f0ec928c85f7405e8427e8f27209720cc0a22b6
animations/memory-map.svg 900x620 7846 82e9be18ac7ecbe388e478b995ef9bcf8e876a2373406565469fda41e911b11f
animations/network-packet-journey.svg 900x620 18648 0081c4c6270e94527deba9ea9365811c22de28130ee343d8df68797eb36f1016
animations/nvic-interrupt-flow.svg 900x620 12972 07a38a7e7d4b430809683b2beb00f98b3cac0a17fc45bb1a5d066d20c22c9dc4
animations/rtos-system-layers.svg 900x620 13996 1a44f6f16dcc08a20467d946a35a22ef968582f37faf99b5b74f5107deaf31e9
animations/spi-transfer.svg 900x620 18861 579ddd86d159809dc4c667a0bf1faf652c1c0538d4d155f6f7187896df7a3968
animations/timer-modes.svg 900x620 11712 c8a1e34469293d5f4a02a5703271bcf62fc4e9f2f1e89429dbcaa02b56ebeabf
animations/timer-pwm.svg 900x620 10046 54833bf0841b1569cb993934699473b2ee4d2f0ed56b858a4fb9b5855bb8532f
animations/toolchain-flow.svg 900x620 15176 e131ad994e16c099c15d4d941c0e7aade4865c53c912248a73590e939645e0bd
animations/uart-frame.svg 900x620 18533 a696fc8932d337f1b22dacef54ecfe01dd37aa963b41d67111c584122f6b3400
animations/usb-enumeration.svg 900x620 10874 b531c1c1278ee8560a2a4297dd4f36e8dfb5934fc09f7df494faf9d5e455e20d
""".strip().splitlines()
ALLOWED = {
    "#fbfaf7", "#f1f5f7", "#e5f3f8", "#5e6872", "#d7dce1", "#17202a",
    "#075e84", "#1e4d63", "#1b5c45", "#7a4e00", "#9a3412", "#8f2d2d",
    "#5b3a8c", "#8e2f5b", "#ffffff",
    "#00000055", "#00000066", "#00000088", "#08214a", "#08224a", "#0a0d13",
    "#0a1f5e", "#0a2a52", "#0b2c4c", "#0c0f16", "#0c2242", "#0d2b22",
    "#0e3b6e", "#0f2f8a", "#0f3f6b", "#123057", "#123a2e", "#141821",
    "#151922", "#153a9e", "#1b1f28", "#1d4ed8", "#2a3242", "#2b3038",
    "#39424f", "#4a5260", "#59606c", "#5b6472", "#5d6470", "#7aa2ff",
    "#7fd4ff", "#808a9a", "#8b98b0", "#8d7420", "#8d949e", "#9aa4b2",
    "#9db8ff", "#bcd8ff", "#c4b5fd", "#c9ced6", "#cfe0ff", "#d8b23a",
    "#dbeafe", "#dfe6f0", "#e2b23c", "#e7ebf0", "#e8f1ff", "#ffffff22",
}
BANNED = {
    "#0b1220", "#0e1626", "#111c31", "#16233c", "#243354", "#1a2742",
    "#e6edf3", "#93a4c0", "#64748b", "#22d3ee", "#60a5fa", "#34d399",
    "#fbbf24", "#fb923c", "#f87171", "#a78bfa", "#f472b6", "#f8fafc",
    "#c4552a", "#9a3d1c",
}
for line in ROWS:
    rel, wh, _size, digest = line.split()
    width, height = wh.split("x")
    path = Path("assets", rel)
    raw = path.read_bytes()
    svg = raw.decode("utf-8")
    limit = 80 * 1024 if rel.endswith("pinout-stm32h743zi-lqfp144.svg") else 60 * 1024
    if len(raw) >= limit:
        raise SystemExit(f"size {rel} {len(raw)}")
    attrs = re.search(r"<svg\b([^>]*)>", svg).group(1)
    if re.search(r'\bwidth="(\d+)"', attrs).group(1) != width:
        raise SystemExit(f"width {rel}")
    if re.search(r'\bheight="(\d+)"', attrs).group(1) != height:
        raise SystemExit(f"height {rel}")
    if f'viewBox="0 0 {width} {height}"' not in svg:
        raise SystemExit(f"viewBox {rel}")
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.DOTALL)
    got = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    if got != digest:
        raise SystemExit(f"text {rel} {got}")
    colors = {
        item.lower()
        for item in re.findall(r"#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})(?![0-9A-Fa-f])", svg)
    }
    bad = colors - ALLOWED
    if bad or colors & BANNED:
        raise SystemExit(f"color {rel} {sorted(bad or colors & BANNED)}")
    strokes = set(re.findall(r'stroke-width="([^"]+)"', svg))
    if not strokes <= {"1", "1.5", "2"}:
        raise SystemExit(f"sw {rel} {strokes}")
    radii = set(re.findall(r'\brx="([^"]+)"', svg))
    if not radii <= {"2", "4", "8"}:
        raise SystemExit(f"rx {rel} {radii}")
    if "stroke-width:" in svg:
        raise SystemExit(f"css stroke {rel}")
    if "自绘矢量动画" not in svg:
        raise SystemExit(f"footer {rel}")
i2c = Path("assets/animations/i2c-transaction.svg").read_text(encoding="utf-8")
if "<style" in i2c or "<animate" in i2c:
    raise SystemExit("i2c gained motion")
print("25 ok")

PY
```

Expected: 打印 `25 ok`，退出码 0。然后：

```bash
git diff --stat -- assets/boards assets/gif assets/diagrams stm32-book/cover.svg stm32-book/styles
```

Expected: 无输出。`assets/diagrams` 在这一步没有新的未提交改动；波次 1 的改动已经在上一次提交里。

- [ ] **Step 4: 提交波次 2**

```bash
git add tools/anim_basics.py tools/anim_gpio.py tools/anim_comm.py tools/anim_sys.py assets/animations
git commit -m "book: 刀 C 波次 2，浅色动画"
```

不要开实施 PR。不要把 `*-zh.gif` 加进来。

---

### Task 3: 波次 3，浅色板卡和引脚图

**Files:**
- Modify: `tools/gen_boards.py`（`board()` 第 31 行的 `r=14`；`header()` 第 57–58 行的脚名）
- Modify: `tools/gen_pinouts.py`（只收 `sw` / `rx`：芯片体 `rx=6`，两条引脚短线 `sw=1.6`）
- Modify: `assets/boards/*.svg` 这 10 张
- Test: 仍不新增 `test_sample_svg_c.py`

**Interfaces:**
- Consumes: Task 1 的 `T.TEXT`。`gen_boards.header()` 现在把脚名画成 `fill=SILK`。`board()` 的内框用 `rx=r - 4`。五个调用都不传 `r`。
- Produces: `board()` 的默认 `r` 是 `8`，因此内框圆角是 `4`。纸上的排针脚名是 `T.TEXT`。`SILK` 仍是 `#e8f1ff`。`_color()` 的函数体不改。H743 引脚图的字节数要记到实施 PR 说明里。

`gen_boards.py` 写这 7 张：`bluepill-stm32f103c8t6.svg`、`blackpill-stm32f411ce.svg`、`nucleo-f411re.svg`、`f4-discovery.svg`、`f103zet6-dev.svg`、`pinout-bluepill.svg`、`peripheral-wiring.svg`。`gen_pinouts.py` 写另外 3 张 LQFP。两个脚本都写到 `assets/boards/`，文件名不重叠。先改源码再跑命令。不要先跑命令。

- [ ] **Step 1: 改板轮廓和纸上的脚名**

`board()` 的签名改成：

```python
def board(s, x, y, w, h, fill=PCB, dark=PCB_DARK, r=8, holes=True):
```

函数体里的 `rx=r` 和 `rx=r - 4` 保持。不要把 `rx=r - 4` 收成字面量。`holes` 里的 `sw=1.6` 留给收档脚本，它会变成 `sw=1.5`。

`header()` 里只有脚名这一处从 `SILK` 改成 `T.TEXT`：

```python
            s.text(px + (pitch - 3) / 2, y + dy, labels[i], size=label_size,
                   anchor="middle", fill=T.TEXT)
```

改之前 `fill=SILK` 有 11 处。改之后剩 10 处。这 10 处是板上的丝印，保持 `SILK`。`SILK = "#e8f1ff"` 这一行不改。`PCB`、`GOLD`、`PAD` 不改。

`tools/gen_pinouts.py` 的 `_color()` 整段不改。芯片体这三行不改：`fill="#1b1f28"`、`fill="#dfe6f0"`、`fill="#8b98b0"`。`pitch = 20 if n <= 16 else 15` 和 `label_room = 150` 不改。

- [ ] **Step 2: 收这两份源码的描边和圆角**

在仓库根运行：

```bash
python3 - << 'PY'
import re
from pathlib import Path

SW = {
    "1": "1", "1.2": "1", "1.4": "1.5", "1.5": "1.5", "1.6": "1.5",
    "1.8": "2", "2": "2", "2.2": "2", "2.4": "2", "2.6": "2", "3": "2",
}
RX = {
    "0": "0", "1": "2", "1.5": "2", "2": "2", "2.5": "2", "3": "2",
    "4": "4", "5": "4", "6": "4", "7": "4", "8": "8", "9": "8",
    "10": "8", "11": "8", "12": "8", "14": "8", "16": "8",
}
PAT = re.compile(r"\b(sw|rx)=(\d+(?:\.\d+)?)")

def remap(text: str) -> tuple[str, int]:
    changed = 0
    def sub(match: re.Match) -> str:
        nonlocal changed
        kind, raw = match.group(1), match.group(2)
        table = SW if kind == "sw" else RX
        if raw not in table:
            raise SystemExit(f"unmapped {kind}={raw}")
        new = table[raw]
        if new != raw:
            changed += 1
        return f"{kind}={new}"
    return PAT.sub(sub, text), changed

for path_text in (
    "tools/gen_boards.py",
    "tools/gen_pinouts.py",
):
    path = Path(path_text)
    new, changed = remap(path.read_text(encoding="utf-8"))
    path.write_text(new, encoding="utf-8")
    print(f"{path} {changed}")
PY
```

Expected:

```text
tools/gen_boards.py 42
tools/gen_pinouts.py 3
```

这 42 不含 `r=14`。`r=14` 已经在 Step 1 改成 `r=8`，脚本看不到它。若脚本打印的个数不是 42，停。不要把 `button()` 的 `r=13` 收成圆角。

```bash
grep -n 'r=14\|fill=SILK' tools/gen_boards.py
```

Expected: 没有 `r=14`。`fill=SILK` 仍有 10 行。`header()` 的那一处是 `fill=T.TEXT`。

- [ ] **Step 3: 再生 10 张板卡**

```bash
python3 tools/gen_boards.py
python3 tools/gen_pinouts.py
```

Expected: 退出码 0。板卡 7 行 `[ok]`，引脚图 3 行 `pins ok`。不要运行 `gen_animations.py`。

- [ ] **Step 4: 核对 10 张，并记下 H743 的字节数**

H743 用 `80 * 1024`，其余 9 张用 `60 * 1024`。75786 不作为相等断言。脚本先打印再生后的字节数，再打印 `10 ok`。把那个整数写进实施 PR 的说明。不要为了把它压进 60 KB 去改 `T.MONO`。

```bash
python3 - << 'PY'
import hashlib, re
from pathlib import Path
ROWS = """
boards/blackpill-stm32f411ce.svg 900x620 32264 511d86c80d8862e78be2a0c7e6ca7e24e1db11d30ea66d47b3b2f1e8cdec0494
boards/bluepill-stm32f103c8t6.svg 900x620 35647 272634dc07da80d8c5d7e6471d9778310292318aace55acbecfcd92a8d9d4c25
boards/f103zet6-dev.svg 900x620 26509 8d52a625b72cef5f53be80091fc870d3bcf9537b0c178c5aa4ebfcb810ded612
boards/f4-discovery.svg 900x620 26524 d0d4d756b30de2d1a11a43bd78abd0f733dcf2696cc88f708de8cde63cfe659f
boards/nucleo-f411re.svg 900x620 21385 434fa875affbab6a0d987df16919de7b6cfaf88c3703da29593bef68b5006c8b
boards/peripheral-wiring.svg 900x620 13970 a5517214a0d7efcb8721fa41c8fee6224a7deca98f193bf39147ccc3f36fd166
boards/pinout-bluepill.svg 900x620 35176 4de478b58c8d278166311b99311183121ccf1ecb38a50c99450b35e60893cabd
boards/pinout-stm32g071rb-lqfp64.svg 620x750 34523 7ccc8b702e15d0473bfc1d4c956397dfbb5bd50363d4e762bd100c794d1d2193
boards/pinout-stm32h743zi-lqfp144.svg 840x970 75786 4d71ec5cab732513073bac6721ae4c688a36f18ab11fcae4b5e6e927433b7a96
boards/pinout-stm32l476rg-lqfp64.svg 620x750 34508 a5a8468d7b087956a4635ac7c88412f1e7920570c53e388e0a10a44fbe5f8adf
""".strip().splitlines()
ALLOWED = {
    "#fbfaf7", "#f1f5f7", "#e5f3f8", "#5e6872", "#d7dce1", "#17202a",
    "#075e84", "#1e4d63", "#1b5c45", "#7a4e00", "#9a3412", "#8f2d2d",
    "#5b3a8c", "#8e2f5b", "#ffffff",
    "#00000055", "#00000066", "#00000088", "#08214a", "#08224a", "#0a0d13",
    "#0a1f5e", "#0a2a52", "#0b2c4c", "#0c0f16", "#0c2242", "#0d2b22",
    "#0e3b6e", "#0f2f8a", "#0f3f6b", "#123057", "#123a2e", "#141821",
    "#151922", "#153a9e", "#1b1f28", "#1d4ed8", "#2a3242", "#2b3038",
    "#39424f", "#4a5260", "#59606c", "#5b6472", "#5d6470", "#7aa2ff",
    "#7fd4ff", "#808a9a", "#8b98b0", "#8d7420", "#8d949e", "#9aa4b2",
    "#9db8ff", "#bcd8ff", "#c4b5fd", "#c9ced6", "#cfe0ff", "#d8b23a",
    "#dbeafe", "#dfe6f0", "#e2b23c", "#e7ebf0", "#e8f1ff", "#ffffff22",
}
BANNED = {
    "#0b1220", "#0e1626", "#111c31", "#16233c", "#243354", "#1a2742",
    "#e6edf3", "#93a4c0", "#64748b", "#22d3ee", "#60a5fa", "#34d399",
    "#fbbf24", "#fb923c", "#f87171", "#a78bfa", "#f472b6", "#f8fafc",
    "#c4552a", "#9a3d1c",
}
for line in ROWS:
    rel, wh, _size, digest = line.split()
    width, height = wh.split("x")
    path = Path("assets", rel)
    raw = path.read_bytes()
    svg = raw.decode("utf-8")
    limit = 80 * 1024 if rel.endswith("pinout-stm32h743zi-lqfp144.svg") else 60 * 1024
    if len(raw) >= limit:
        raise SystemExit(f"size {rel} {len(raw)}")
    attrs = re.search(r"<svg\b([^>]*)>", svg).group(1)
    if re.search(r'\bwidth="(\d+)"', attrs).group(1) != width:
        raise SystemExit(f"width {rel}")
    if re.search(r'\bheight="(\d+)"', attrs).group(1) != height:
        raise SystemExit(f"height {rel}")
    if f'viewBox="0 0 {width} {height}"' not in svg:
        raise SystemExit(f"viewBox {rel}")
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.DOTALL)
    got = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    if got != digest:
        raise SystemExit(f"text {rel} {got}")
    colors = {
        item.lower()
        for item in re.findall(r"#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})(?![0-9A-Fa-f])", svg)
    }
    bad = colors - ALLOWED
    if bad or colors & BANNED:
        raise SystemExit(f"color {rel} {sorted(bad or colors & BANNED)}")
    strokes = set(re.findall(r'stroke-width="([^"]+)"', svg))
    if not strokes <= {"1", "1.5", "2"}:
        raise SystemExit(f"sw {rel} {strokes}")
    radii = set(re.findall(r'\brx="([^"]+)"', svg))
    if not radii <= {"2", "4", "8"}:
        raise SystemExit(f"rx {rel} {radii}")
    if "stroke-width:" in svg:
        raise SystemExit(f"css stroke {rel}")
    if "自绘矢量动画" not in svg:
        raise SystemExit(f"footer {rel}")
h743 = Path("assets/boards/pinout-stm32h743zi-lqfp144.svg")
size = h743.stat().st_size
print(size)
if not 60 * 1024 < size < 80 * 1024:
    raise SystemExit("H743 left the expected window")
blue = Path("assets/boards/bluepill-stm32f103c8t6.svg").read_text(encoding="utf-8")
black = Path("assets/boards/blackpill-stm32f411ce.svg").read_text(encoding="utf-8")
if "#123057" not in blue:
    raise SystemExit("blue pill lost its soldermask")
if "#141821" not in black:
    raise SystemExit("black pill lost its soldermask")
print("10 ok")

PY
```

Expected: 先打印一个整数，再打印 `10 ok`。整数严格大于 61440，严格小于 81920。退出码 0。然后：

```bash
git diff --stat -- assets/gif assets/animations assets/diagrams stm32-book/cover.svg stm32-book/styles
```

Expected: 无输出。

- [ ] **Step 5: 提交波次 3**

```bash
git add tools/gen_boards.py tools/gen_pinouts.py assets/boards
git commit -m "book: 刀 C 波次 3，浅色板卡与引脚图"
```

这次提交之后，53 张都已经是浅色。版本号仍是 1.2.6。不要开实施 PR，测试文件还没写。

---

### Task 4: 给资产清单加一句颜色说明

**Files:**
- Modify: `assets/README.md`（生成命令那一块代码围栏的下面，`## 一、动画演示` 的上面）
- Test: 仍不新增测试文件。这一句由下面的 `grep` 锁定

**Interfaces:**
- Consumes: 无。
- Produces: 文件里恰好一次出现下面这句。第 124 行那句过时的「5 张 SVG 还没有对应动图」保持原文。

- [ ] **Step 1: 只插入这一句**

代码围栏现在结束在 `python3 tools/gen_gifs.py` 那一行之后。在围栏结束和 `## 一、动画演示` 之间加上这句，前后各留一个空行：

```markdown
图内纸色、墨色和语义色写在 tools/svgkit.py 的字面量里，数值与整书亮色令牌相同，生成时不读 stm32-book/styles/tokens.json。
```

不要改围栏里的命令。不要把 `gen_sample_figures.py` 从清单里删掉或改写。不要改「这 5 张 SVG 还没有对应动图」。

- [ ] **Step 2: 确认只有一句，而且 GIF 字节没动**

```bash
python3 - << 'PY'
from pathlib import Path
text = Path("assets/README.md").read_text(encoding="utf-8")
sentence = "图内纸色、墨色和语义色写在 tools/svgkit.py 的字面量里，数值与整书亮色令牌相同，生成时不读 stm32-book/styles/tokens.json。"
if text.count(sentence) != 1:
    raise SystemExit(text.count(sentence))
if "这 5 张 SVG 还没有对应动图" not in text:
    raise SystemExit("inventory sentence removed")
print("readme ok")
PY
git diff --stat -- assets/gif
```

Expected: `readme ok`，并且 GIF 的 diff 无输出。

- [ ] **Step 3: 提交这一句**

```bash
git add assets/README.md
git commit -m "docs: 刀 C 说明样本图颜色写在 svgkit 字面量里"
```

---

### Task 5: 写下 53 张的画法契约

**Files:**
- Create: `stm32-book/tests/test_sample_svg_c.py`
- Test: `stm32-book/tests/test_sample_svg_c.py`

**Interfaces:**
- Consumes: Task 1 到 Task 4 的成品和源码。`load_builder()` 的写法和 `stm32-book/tests/test_build.py` 相同。`BOOK_DIR` 是 `stm32-book/`，仓库根是它的父目录。
- Produces: `SampleSvgCTests.test_sample_svg_c_contract`。Task 6 不改这个方法。这一任务不改 `test_build.py`，所以版本断言仍是 1.2.6。

这一任务开始时 53 张已经再生完。测试写入后应当直接通过。若失败，回到对应的生成器修，不要改下面的哈希、允许色或 60 KB。不要把色表抄进 `test_build.py`。

- [ ] **Step 1: 新建测试文件**

`ROWS` 用「画布与文本哈希」的全部 53 行，包括第三列字节数。测试读第三列，但不和它比相等。

```python
from __future__ import annotations

import hashlib
import importlib.util
import re
import unittest
from pathlib import Path


BOOK_DIR = Path(__file__).resolve().parents[1]
REPO = BOOK_DIR.parent
BUILD_PATH = BOOK_DIR / "build_html.py"

ROWS = """
animations/adc-sar.svg 900x620 19409 ebd3127f7efde5d3c25f5a82dea6ae36eaff2a4c3a87c698f95f0d329a0ca807
animations/boot-sequence.svg 900x620 14058 d6d1baa08f2d9763ef5971f4701775db3905d34a7d6998310b127dd21beaddfc
animations/can-arbitration.svg 900x620 23362 6a68426929c8ad0f4046b091ae4be6db894eba2e4125f1e03c41c695167a3176
animations/clock-tree.svg 900x620 10921 c0e07c5c01bffae9769331541bdf87dcfc4ea61e3b4081b6f72834b476fbed08
animations/debug-swo.svg 900x620 12545 e44f13c22225782401c9b3d44f376781297c0103040118786626621476a6ffdd
animations/dma-circular.svg 900x620 16488 7deb7de9dc81e1a01c1c2e01827c131661f5b6d45bb5c2fb1d0473e126041fd1
animations/flash-iap.svg 900x620 12795 55ad4b20f25654a8bb6a705303a99d5fb513f5b125b70a4545278f84d63ad0cb
animations/freertos-scheduler.svg 900x620 15775 fe1bebd106b7c825a5d815edc67842821a8298e6e98036153641ca928c098bb3
animations/g0-boot-swd.svg 900x620 12398 e9121dfb6e5290afd5d192048fa7d7409a821c7651538c80bde3237df535155f
animations/gpio-blink.svg 900x620 14249 811377a9c3b65dd99cbeb8a1ff720b0e4e6410bc852726ac98f9aa20619175ea
animations/gpio-input-interrupt.svg 900x620 13740 4b97aeb339eb046f0091312b6caf918b1acdc176cc72e4295cc7c116792c6697
animations/i2c-transaction.svg 900x620 17483 e5c5b2aca2aae67cc607e3eb929cc0f20c184deceb8815f32a9d4e96f4bef55a
animations/iwdg-window.svg 900x620 10675 324f8c83215265a9e4b9c256552019165c14adb914c3fc9189f054f264751444
animations/l4-stop2-evidence.svg 900x620 13976 ae6b68a3a26ee3995d72dc29bcfcb2bab733a2e54637e4d9a6a8581b9f577e28
animations/lowpower-wakeup.svg 900x620 10766 7a5fe86d6e1a29c7f8e00d177f0ec928c85f7405e8427e8f27209720cc0a22b6
animations/memory-map.svg 900x620 7846 82e9be18ac7ecbe388e478b995ef9bcf8e876a2373406565469fda41e911b11f
animations/network-packet-journey.svg 900x620 18648 0081c4c6270e94527deba9ea9365811c22de28130ee343d8df68797eb36f1016
animations/nvic-interrupt-flow.svg 900x620 12972 07a38a7e7d4b430809683b2beb00f98b3cac0a17fc45bb1a5d066d20c22c9dc4
animations/rtos-system-layers.svg 900x620 13996 1a44f6f16dcc08a20467d946a35a22ef968582f37faf99b5b74f5107deaf31e9
animations/spi-transfer.svg 900x620 18861 579ddd86d159809dc4c667a0bf1faf652c1c0538d4d155f6f7187896df7a3968
animations/timer-modes.svg 900x620 11712 c8a1e34469293d5f4a02a5703271bcf62fc4e9f2f1e89429dbcaa02b56ebeabf
animations/timer-pwm.svg 900x620 10046 54833bf0841b1569cb993934699473b2ee4d2f0ed56b858a4fb9b5855bb8532f
animations/toolchain-flow.svg 900x620 15176 e131ad994e16c099c15d4d941c0e7aade4865c53c912248a73590e939645e0bd
animations/uart-frame.svg 900x620 18533 a696fc8932d337f1b22dacef54ecfe01dd37aa963b41d67111c584122f6b3400
animations/usb-enumeration.svg 900x620 10874 b531c1c1278ee8560a2a4297dd4f36e8dfb5934fc09f7df494faf9d5e455e20d
boards/blackpill-stm32f411ce.svg 900x620 32264 511d86c80d8862e78be2a0c7e6ca7e24e1db11d30ea66d47b3b2f1e8cdec0494
boards/bluepill-stm32f103c8t6.svg 900x620 35647 272634dc07da80d8c5d7e6471d9778310292318aace55acbecfcd92a8d9d4c25
boards/f103zet6-dev.svg 900x620 26509 8d52a625b72cef5f53be80091fc870d3bcf9537b0c178c5aa4ebfcb810ded612
boards/f4-discovery.svg 900x620 26524 d0d4d756b30de2d1a11a43bd78abd0f733dcf2696cc88f708de8cde63cfe659f
boards/nucleo-f411re.svg 900x620 21385 434fa875affbab6a0d987df16919de7b6cfaf88c3703da29593bef68b5006c8b
boards/peripheral-wiring.svg 900x620 13970 a5517214a0d7efcb8721fa41c8fee6224a7deca98f193bf39147ccc3f36fd166
boards/pinout-bluepill.svg 900x620 35176 4de478b58c8d278166311b99311183121ccf1ecb38a50c99450b35e60893cabd
boards/pinout-stm32g071rb-lqfp64.svg 620x750 34523 7ccc8b702e15d0473bfc1d4c956397dfbb5bd50363d4e762bd100c794d1d2193
boards/pinout-stm32h743zi-lqfp144.svg 840x970 75786 4d71ec5cab732513073bac6721ae4c688a36f18ab11fcae4b5e6e927433b7a96
boards/pinout-stm32l476rg-lqfp64.svg 620x750 34508 a5a8468d7b087956a4635ac7c88412f1e7920570c53e388e0a10a44fbe5f8adf
diagrams/interrupt-priority.svg 900x560 11877 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8673 32e1a5b195562947e04d2da8efc2f0c89dd97aed9f7cacbb3c5914ce52f8ec96
diagrams/layers-hal-ll-reg.svg 900x560 10401 60098b25b368c2f6acefb4e9a3152f816506cae44e68b2fb8ffbf0878c049f78
diagrams/network-debug-ladder.svg 900x560 11278 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14071 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13014 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/sample-00-boot-state.svg 960x620 7103 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-01-swd-vectors.svg 960x980 7328 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-clock-tree.svg 960x860 7402 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-03-gpio-led.svg 960x660 8221 932244c2053d317d50bf5106192a79fbf9d1546f16dd00bcf99110b7bd11a8ad
diagrams/sample-04-exception-stack.svg 960x780 7528 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-05-pwm-1khz.svg 960x820 6845 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-06-uart-frame.svg 960x820 12448 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6620 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-08-spi-jedec.svg 960x860 6850 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-09-adc-sar.svg 960x860 6656 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-10-dma-cndtr.svg 960x900 6552 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-11-iwdg-1s.svg 960x980 7169 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
""".strip().splitlines()

SEMANTIC = {
    "#fbfaf7",
    "#f1f5f7",
    "#e5f3f8",
    "#5e6872",
    "#d7dce1",
    "#17202a",
    "#075e84",
    "#1e4d63",
    "#1b5c45",
    "#7a4e00",
    "#9a3412",
    "#8f2d2d",
    "#5b3a8c",
    "#8e2f5b",
}
PARTS = {
    "#00000055",
    "#00000066",
    "#00000088",
    "#08214a",
    "#08224a",
    "#0a0d13",
    "#0a1f5e",
    "#0a2a52",
    "#0b2c4c",
    "#0c0f16",
    "#0c2242",
    "#0d2b22",
    "#0e3b6e",
    "#0f2f8a",
    "#0f3f6b",
    "#123057",
    "#123a2e",
    "#141821",
    "#151922",
    "#153a9e",
    "#1b1f28",
    "#1d4ed8",
    "#2a3242",
    "#2b3038",
    "#39424f",
    "#4a5260",
    "#59606c",
    "#5b6472",
    "#5d6470",
    "#7aa2ff",
    "#7fd4ff",
    "#808a9a",
    "#8b98b0",
    "#8d7420",
    "#8d949e",
    "#9aa4b2",
    "#9db8ff",
    "#bcd8ff",
    "#c4b5fd",
    "#c9ced6",
    "#cfe0ff",
    "#d8b23a",
    "#dbeafe",
    "#dfe6f0",
    "#e2b23c",
    "#e7ebf0",
    "#e8f1ff",
    "#ffffff22",
}
ALLOWED = SEMANTIC | PARTS | {"#ffffff"}
BANNED = {
    "#0b1220",
    "#0e1626",
    "#111c31",
    "#16233c",
    "#243354",
    "#1a2742",
    "#e6edf3",
    "#93a4c0",
    "#64748b",
    "#22d3ee",
    "#60a5fa",
    "#34d399",
    "#fbbf24",
    "#fb923c",
    "#f87171",
    "#a78bfa",
    "#f472b6",
    "#f8fafc",
    "#c4552a",
    "#9a3d1c",
}
SOURCE_FILES = (
    "tools/svgkit.py",
    "tools/gen_sample_figures.py",
    "tools/gen_diagrams.py",
    "tools/anim_basics.py",
    "tools/anim_gpio.py",
    "tools/anim_comm.py",
    "tools/anim_sys.py",
    "tools/gen_boards.py",
    "tools/gen_pinouts.py",
)


def load_builder():
    spec = importlib.util.spec_from_file_location("stm32_book_builder", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder: {BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text_hash(svg: str) -> str:
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.DOTALL)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


class SampleSvgCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()

    def test_sample_svg_c_contract(self) -> None:
        self.assertEqual(
            "a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4",
            hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            "c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b",
            hashlib.sha256((BOOK_DIR / "styles" / "tokens.json").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5",
            hashlib.sha256((BOOK_DIR / "styles" / "book.css").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd",
            hashlib.sha256((BOOK_DIR / "cover.svg").read_bytes()).hexdigest(),
        )

        found = sorted(
            path.relative_to(REPO / "assets").as_posix()
            for path in (REPO / "assets").rglob("*.svg")
        )
        expected = []
        for line in ROWS:
            rel, wh, _old_size, digest = line.split()
            width, height = (int(part) for part in wh.split("x"))
            expected.append(rel)
            path = REPO / "assets" / rel
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            limit = 80 * 1024 if rel.endswith("pinout-stm32h743zi-lqfp144.svg") else 60 * 1024
            self.assertLess(len(raw), limit, rel)
            attrs = re.search(r"<svg\b([^>]*)>", text)
            self.assertIsNotNone(attrs, rel)
            self.assertEqual(str(width), re.search(r'\bwidth="(\d+)"', attrs.group(1)).group(1), rel)
            self.assertEqual(str(height), re.search(r'\bheight="(\d+)"', attrs.group(1)).group(1), rel)
            self.assertIn(f'viewBox="0 0 {width} {height}"', text, rel)
            self.assertEqual(digest, text_hash(text), rel)
            colors = {
                item.lower()
                for item in re.findall(
                    r"#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})(?![0-9A-Fa-f])",
                    text,
                )
            }
            self.assertFalse(colors - ALLOWED, (rel, sorted(colors - ALLOWED)))
            self.assertFalse(colors & BANNED, rel)
            strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
            self.assertTrue(strokes <= {"1", "1.5", "2"}, (rel, strokes))
            self.assertFalse("stroke-width:" in text, rel)
            radii = set(re.findall(r'\brx="([^"]+)"', text))
            self.assertTrue(radii <= {"2", "4", "8"}, (rel, radii))
            if Path(rel).name.startswith("sample-"):
                self.assertNotIn("<animate", text, rel)
                self.assertNotIn("@keyframes", text, rel)
                self.assertNotIn("animation:", text, rel)
                self.assertNotIn("矢量动画", text, rel)
                self.assertIn("自绘", text, rel)
            else:
                self.assertIn("自绘矢量动画", text, rel)
        self.assertEqual(expected, found)
        self.assertEqual(53, len(found))

        i2c = (REPO / "assets" / "animations" / "i2c-transaction.svg").read_text(encoding="utf-8")
        self.assertNotIn("<style", i2c)
        self.assertNotIn("<animate", i2c)

        gifs = sorted((REPO / "assets" / "gif").glob("*.gif"), key=lambda path: path.name)
        self.assertEqual(40, len(gifs))
        listing = "".join(
            f"{path.name} {hashlib.sha256(path.read_bytes()).hexdigest()}\n"
            for path in gifs
        )
        self.assertEqual(
            "bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f",
            hashlib.sha256(listing.encode("utf-8")).hexdigest(),
        )

        svgkit = (REPO / "tools" / "svgkit.py").read_text(encoding="utf-8")
        self.assertIn('BG = "#fbfaf7"', svgkit)
        self.assertIn('CYAN = "#075e84"', svgkit)
        self.assertNotIn("WHITE", svgkit)
        self.assertNotIn("#0b1220", svgkit)
        self.assertNotIn("#22d3ee", svgkit)
        self.assertIn("PingFang SC", svgkit)
        self.assertIn("Hiragino Sans GB", svgkit)

        for rel in SOURCE_FILES:
            source = (REPO / rel).read_text(encoding="utf-8")
            self.assertNotIn('fill="#0b1220"', source, rel)
            self.assertNotIn("T.WHITE", source, rel)
        sample_src = (REPO / "tools" / "gen_sample_figures.py").read_text(encoding="utf-8")
        self.assertNotIn("rx=10", sample_src)
        self.assertNotIn("rx=6", sample_src)


if __name__ == "__main__":
    unittest.main()
```

`PARTS` 恰好 48 个。`SEMANTIC` 恰好 14 个。8 位色只有 `PARTS` 里那四个。

- [ ] **Step 2: 跑这条新测试**

```bash
python3 stm32-book/tests/test_sample_svg_c.py SampleSvgCTests.test_sample_svg_c_contract -v
```

Expected: `ok`。失败时看断言带出来的文件名。修生成器后只重跑写那张图的那一个命令，再跑这条测试。不要改 `ROWS` 里的文本哈希。不要把 H743 的门槛放宽到 `80 * 1024` 以上。

- [ ] **Step 3: 整套测试仍按 1.2.6 通过**

```bash
python3 -m unittest discover stm32-book/tests -v
```

Expected: 退出码 0。版本断言还是 1.2.6。这一任务不改 `test_build.py`。

- [ ] **Step 4: 提交测试**

```bash
git add stm32-book/tests/test_sample_svg_c.py
git commit -m "test: 锁住刀 C 的 53 张样本图画法"
```

---

### Task 6: 把整书标成 1.2.7

**Files:**
- Modify: `stm32-book/tests/test_build.py`（`assert_version_history_and_index` 第 145–148 行；`test_revision_file_lists_1_0_0_through_manifest_version` 第 184 行；`test_build_produces_one_complete_offline_book` 第 278 行的 `<strong>v1.2.6</strong>`；`test_english_book_is_a_separate_offline_edition` 第 418 行和第 435 行；`test_visual_polish_version_is_1_2_0` 第 1619 行起）
- Modify: `stm32-book/manifest.json`（只改 `version`）
- Modify: `stm32-book/manifest-en.json`（只改 `version`）
- Modify: `stm32-book/revisions.json`（`entries` 最前插入一条）
- Modify: `stm32-book/README.md`（第 17 行、第 92 行、第 98 行）
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: `validate_revisions()` 要求 `entries[0]["version"]` 等于两份 manifest 的 `version`。Task 5 的 `SampleSvgCTests` 不读版本号。
- Produces: manifest、英文 manifest、`revisions.json` 第一条和 README 当前版本句都是 `1.2.7` 与 `2026-10-25`。已有 1.2.6 的刀 D 两句改去 `entries[1]`，句子原文不改。

开工条件若已经把实施版换成高于 `1.2.7` 的号，这一任务里每一处 `1.2.7` 用那个号，每一处拿来当上一版的 `1.2.6` 用当时 manifest 的旧号。日期仍写 `2026-10-25`。

- [ ] **Step 1: 先改版本断言，确认它会失败**

在 `assert_version_history_and_index` 里，把元组的开头改成 `"1.2.7", "1.2.6",`，并在现有的 `self.assertLess(history.index(">1.2.6<"), history.index(">1.2.5<"))` 上面加：

```python
        self.assertLess(history.index(">1.2.7<"), history.index(">1.2.6<"))
```

`test_revision_file_lists_1_0_0_through_manifest_version` 的列表以 `"1.2.7"` 起头，下一项仍是 `"1.2.6"`。

两处 `"<strong>v1.2.6</strong>"` 改成 `"<strong>v1.2.7</strong>"`。英文 manifest 的 `self.assertEqual("1.2.6", manifest["version"])` 改成 `"1.2.7"`。

`test_visual_polish_version_is_1_2_0` 的变量改成：

```python
        entry = revisions["entries"][0]
        cover = revisions["entries"][1]
        tokens = revisions["entries"][2]
        typography = revisions["entries"][3]
        batch4 = revisions["entries"][4]
        batch3 = revisions["entries"][5]
        guide = revisions["entries"][6]
        previous = revisions["entries"][7]
```

新的 `entry` 断言是：

```python
        self.assertEqual("1.2.7", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.2.7", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.2.7", entry["version"])
        self.assertEqual("2026-10-25", entry["date"])
        self.assertEqual(
            [
                "仓库里的样本图、框图、动画和板卡图改成浅色纸底，语义色与正文的强调色、提示色对齐。描边只留 1、1.5 和 2，圆角只留 2、4 和 8。",
                "封面、样式令牌和章节正文不改。光栅 GIF 仍是原来的深色，不随这批矢量图重画。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "The sample drawings, diagrams, animations, and board drawings in the repository now use light paper. Their semantic colors line up with the text accent and tip. Strokes are only 1, 1.5, and 2. Corners are only 2, 4, and 8.",
                "The cover, the style tokens, and the chapter text stay as they are. The raster GIFs keep the previous dark palette and are not redrawn with these vectors.",
            ],
            entry["en"],
        )
```

原来的 `entry` 改名为 `cover`。1.2.6 的版本号、日期和中英两句保持现在文件里的原文，只是断言对象从 `entry` 换成 `cover`。后面的 `tokens`、`typography`、`batch4`、`batch3`、`guide`、`previous` 只改索引，句子一字不改。

README 断言改成：

```python
        self.assertIn("当前版本：**v1.2.7 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.7。", readme)
        self.assertIn("也不要把 1.2.5 的产物标成 1.2.6。", readme)
        self.assertIn("也不要把 1.2.6 的产物标成 1.2.7。", readme)
        self.assertIn("打 tag `v1.2.7`", readme)
        self.assertNotIn("当前版本：**v1.2.6", readme)
        self.assertNotIn("打 tag `v1.2.6`", readme)
```

`样式来自 tokens.json 和 book.css` 那一句，以及更早的误标句，保持原断言。

先只提交测试会红。这一步先跑，确认失败点在版本，不在刀 C 的画法：

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
```

Expected: FAIL，因为 manifest 仍是 `1.2.6`。不要在这一步停住不改 manifest。同一个提交里做完 Step 2。

- [ ] **Step 2: 同一提交改四份版本文件**

`stm32-book/manifest.json` 和 `stm32-book/manifest-en.json` 只把 `"version": "1.2.6"` 改成 `"version": "1.2.7"`。`"date": "2026-10-25"` 不改。其他字段不改。

`stm32-book/revisions.json` 的 `entries` 最前面插入。已有的 1.2.6 对象整个留下：

```json
    {
      "version": "1.2.7",
      "date": "2026-10-25",
      "zh": [
        "仓库里的样本图、框图、动画和板卡图改成浅色纸底，语义色与正文的强调色、提示色对齐。描边只留 1、1.5 和 2，圆角只留 2、4 和 8。",
        "封面、样式令牌和章节正文不改。光栅 GIF 仍是原来的深色，不随这批矢量图重画。"
      ],
      "en": [
        "The sample drawings, diagrams, animations, and board drawings in the repository now use light paper. Their semantic colors line up with the text accent and tip. Strokes are only 1, 1.5, and 2. Corners are only 2, 4, and 8.",
        "The cover, the style tokens, and the chapter text stay as they are. The raster GIFs keep the previous dark palette and are not redrawn with these vectors."
      ]
    },
```

`stm32-book/README.md`：

- 第 17 行的 `当前版本：**v1.2.6 · 2026-10-25**` 改为 `当前版本：**v1.2.7 · 2026-10-25**`。后面「中文整书和英文整书共用这一版号」不改。
- 第 92 行开头的 `版本号已经是 1.2.6。` 改为 `版本号已经是 1.2.7。`。句末保持 `也不要把 1.2.5 的产物标成 1.2.6。`，紧接着再加一句 `也不要把 1.2.6 的产物标成 1.2.7。`
- 第 98 行的 ``打 tag `v1.2.6` `` 改为 ``打 tag `v1.2.7` ``。
- 第 32 行关于 `tokens.json` 和 `book.css` 的那一句不改。

- [ ] **Step 3: 版本测试和画法测试一起通过**

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
python3 stm32-book/tests/test_sample_svg_c.py SampleSvgCTests.test_sample_svg_c_contract -v
python3 -m unittest discover stm32-book/tests -v
```

Expected: 三条都是退出码 0。

- [ ] **Step 4: 提交版本戳**

```bash
git add stm32-book/tests/test_build.py stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md
git commit -m "book: 刀 C 把整书标成 1.2.7"
```

这次提交不改 `tokens.json`、`book.css`、`cover.svg`。

---

### Task 7: 验证并开实施 PR

**Files:**
- Modify: 无。验收通过时这一任务没有新的提交
- Test: 已有的 `stm32-book/tests/` 与 `tools/check_assets.py`

**Interfaces:**
- Consumes: Task 6 的 `1.2.7` 和 Task 5 的契约。
- Produces: 实施 PR。不产生 tag，不产生 Release。

- [ ] **Step 1: 四条命令**

在仓库根运行：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
python3 tools/check_assets.py
```

Expected: 前三条退出码 0。第四条在 SVG、16 张 ASCII GIF 的逐像素比对、引脚图、实拍、示例、仿真和链接都通过时退出码 0。

`check_assets.py` 对大于 500 KB 的 GIF 只打印 `WARN`，不因此把 `ok` 设成假。17 张 `*-zh.gif` 打印 `WARN` 是预期，不要压它们，也不要改 `check_assets.py`。

`check_videos()` 会 `import PIL` 并调用 `ffmpeg`。若失败只是 `ModuleNotFoundError: PIL` 或找不到 `ffmpeg`，在实施 PR 说明里贴上这段追溯，不要改 `assets/video/`，不要改 `tools/gen_narrated.py`。其余检查已经通过时，这个环境缺口不挡住刀 C。若海报字节和 `render_poster()` 对不上，停。那不是这一刀该修的，说明有人改了海报生成器或视频文件。

GIF 像素比对失败也停。那说明 `minigfx.py` 或 16 张 ASCII GIF 被碰到了。不要改它们来迁就浅色 SVG。

- [ ] **Step 2: 最终 diff 的边界**

```bash
git diff --stat origin/main
python3 - << 'PY'
import hashlib
from pathlib import Path
gifs = sorted(Path("assets/gif").glob("*.gif"), key=lambda path: path.name)
listing = "".join(
    f"{path.name} {hashlib.sha256(path.read_bytes()).hexdigest()}\n" for path in gifs
)
got = hashlib.sha256(listing.encode()).hexdigest()
if got != "bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f":
    raise SystemExit(got)
print("gif ok", len(gifs))
PY
git diff --stat -- stm32-book/styles stm32-book/cover.svg docs docs/en assets/gif assets/photos assets/video
grep -n '0x271\|167 ns\|len(outline)' stm32-book/tests/test_build.py
```

Expected: `gif ok 40`。样式、封面、`docs/`、`docs/en/`、GIF、实拍和视频的 diff 无输出。`grep` 仍能看到 `0x271`、`167 ns` 和 `self.assertEqual(44, len(outline))`。

`git diff --stat origin/main` 里可以出现的路径只有 File map 里 Task 1 到 Task 6 那些。不允许出现 `tools/gen_tietu.py`、`tools/minigfx.py`、`tools/svg2gif.py`、`tools/check_assets.py`、`tools/gen_animations.py`、`.github/workflows/book.yml`。

53 张 SVG 的最终内容里不得再有 `#0b1220`。浅色 `T`、53 张再生的 SVG 和 `1.2.7` 必须在同一个 PR 里。

- [ ] **Step 3: 打开构建出的 HTML**

中文文件是 `stm32-book/dist/stm32-practical-book.html`。看这几处：

- 第 00 章主图 `sample-00-boot-state.svg`：浅纸上能读出 BOOT0=0 和系统存储器。正常路径是深绿 `#1b5c45`，失败路径是暗红 `#8f2d2d`。图里没有深色满版底。句子仍是现在的手册句。
- 第 03 章主图：PA0 与 PC13 仍是两块。卡片圆角是 8 或 4，不再有 10 和 6。
- `gpio-blink.svg`：浅底上灯仍会闪，类名还在。页脚仍有「自绘矢量动画」。
- Blue Pill 结构图：板身仍是 `#123057`，排针脚名在纸上是 `#17202a`，板上的丝印仍是 `#e8f1ff`。
- 暗色：页面变暗时，这张图仍是浅纸。封面仍是深色铜版，图里仍有 `#c4552a`，样本图里没有。
- 印刷预览：任选一张样本图，纸面上是浅底线框。

英文书看同一张样本图即可。图与中文相同。不要求把 29 章逐页看完。

看不了浏览器时，在实施 PR 说明里写明已经由 `test_sample_svg_c_contract`、样本章测试和 `build_html.py --check` 覆盖了哈希、宽高、文本、描边、圆角、禁色和 60 KB，并注明人工抽看没有做。不要为了抽看去改测试或再手改 SVG。

- [ ] **Step 4: 开实施 PR 并停住**

实施 PR 从本计划已经合入的 `main` 另开分支。标题写明这是样本图 C 的实施，不是本计划。说明里写上：

- 53 张 SVG 由生成器再生。浅色纸底，描边只有 1、1.5、2，圆角只有 2、4、8。`#c4552a` 不在这 53 张里。
- H743 引脚图的再生后字节数是 Task 3 打印的那个整数，小于 80 KB，可以大于 60 KB。
- `tokens.json`、`book.css`、`cover.svg` 的 diff 为空。拼好的 CSS SHA-256 仍是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。
- GIF 汇总哈希不变。16 张 ASCII GIF 仍是深色。24 张 `*-zh.gif` 没有重采样。
- 版本是 1.2.7 · 2026-10-25。前三条本地命令通过。`check_assets.py` 的结果按 Step 1 写明。`book` 与 `book-en` 都变绿之后 squash 合入 `main`。
- 合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 不打 tag，不创建 GitHub Release。

实施者自己不按合并按钮，不跑 `gh pr merge`。CI 还红时不合入。CI 变绿后由协调员 squash 合入。

这一步在验收已经通过时没有新的提交。

## 风险

这些都是设计规格里的风险。实施时按这里停，不要在样本图 PR 里顺手改样式或 GIF。

- **若手改 SVG 而不改生成器，下一次生成会把浅色盖回深色。** 53 张只许由五个生成命令写出。Task 1 到 Task 3 的提交里不要出现没有对应源码 diff 的 SVG。
- **若把 `T.TEXT` 用在 `#123a2e` 那块板岛上，字会沉进阻焊。** 板上的字只用已经在零件色清单里的 `#dfe6f0`、`#8b98b0`、`#e2b23c`。Task 1 的七处替换就是这些。
- **若脚名继续用 `SILK`，浅纸上会看不见。** 只有 `header()` 的脚名改成 `T.TEXT`。板上丝印仍用 `SILK`。改完后 `fill=SILK` 还有 10 处。
- **若把 `#c4552a` 拿来写注意，对比大约 4.3。** 注意用 `T.AMBER`，也就是 `#7a4e00`。书脊色留在封面和扉页。
- **若把整书等宽栈写进每个 `<text>`，H743 引脚图会再长大约 19 KB。** `FONT` 和 `MONO` 保持原文。
- **若重跑 `svg2gif.py`，公众号动图会换掉，而且 17 张仍然过不了 500 KB。** 不运行它。动画 SVG 与 `*-zh.gif` 的暂时不一致是这一刀接受的结果。
- **若顺手改 `minigfx.C`，`check_assets.py` 的逐像素比对会失败。** `C` 保持深色。`C.WHITE` 不是 `T.WHITE`，不要删。
- **若改 `book.css` 来让图和框同色，刀 D 的哈希会失效。** 框保持原样。图用自己的 `#fbfaf7`。
- **若给 `gen_tietu.py` 一起收圆角，就超出了这 53 张。** 不改、不运行。它以后若被拿去出贴图，会继承浅色 `T`。那不是 1.2.7 的验收面。
- **若在 Task 1 就跑 `gen_animations.py`，会在 `T.WHITE` 上崩溃，或者把还没收档的动画写成半套浅色。** 动画命令只在 Task 2 的源码改完之后跑。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 53 张由生成器再生，不手改成品 | Global Constraints，Task 1–3 |
| 浅色纸底；语义色对齐过得了 4.5 的强调色和提示色；`#c4552a` 与 `#9a3d1c` 不进图 | Task 1 的 `T`，Task 5 的 `BANNED` |
| 描边只留 1、1.5、2；圆角只留 2、4、8 | 收档脚本，Task 5 |
| 零件色 48 个加 `#ffffff` 留下；阻焊不收成提示色 | Task 5 的 `PARTS`，Task 3 不改 `PCB` |
| 色条上的 `#0b1220` 改成 `#fbfaf7`；`T.WHITE` 改成 `T.TEXT` 后删除 | Task 1 的优先级色条，Task 2 的三处动画 |
| 板岛上的字和两处描边改成清单里的零件色 | Task 1 的七处 |
| 纸上的脚名改成墨色，`SILK` 常量不改 | Task 3 |
| `board()` 的 `r=14` 改为 `8` | Task 3 |
| 不改句子、坐标、`viewBox`、字体族、动画类名 | 开工条件的文本哈希，Task 5 的宽高和 `viewBox` |
| 不改 `cover.svg`、`tokens.json`、`book.css`；CSS 哈希保持 `a4ccd140…` | 开工条件，Task 5，Task 7 |
| 不重画 GIF；汇总哈希保持 `bd674b4a…` | Global Constraints，Task 7 |
| H743 可以大于 60 KB，必须小于 80 KB；不改 60 KB 这条默认 | Task 3 Step 4，Task 5 |
| 三波同一次 1.2.7，不拆版本 | Global Constraints，Task 7 |
| `assets/README.md` 只加那一句，不改「5 张还没有动图」 | Task 4 |
| 新测试文件，不把色表塞进 `test_build.py` | Task 5 |
| 版本断言后移；修订四句；日期在本计划里冻成 2026-10-25 | 开工条件，Task 6 |
| `book` 与 `book-en` 变绿后 squash；不打 tag | Task 7 |
| 人工看第 00 章、第 03 章、一帧动画、Blue Pill、暗色和印刷 | Task 7 Step 3 |
| 本设计之后的实施计划单独成 PR | 本文件。本计划 PR 只新增这一份 |

## 执行交接

本文件所在的 PR 只审阅计划，不实施样本图。它不改 `assets/`，不改 `tools/`，不升版本，不改 `cover.svg`，不改 `book.css`。CI 变绿不等于可以自动合入。

实施要等本计划合入 `main`，并且 `stm32-book/manifest.json` 的 `version` 仍是 `1.2.6`、`date` 仍是 `2026-10-25`（或按开工条件已经更高）。然后从那个 `main` 另开分支，按任务顺序做。两种走法：

1. Subagent-Driven：每个任务一个新的执行者，任务之间再审一遍 diff。
2. Inline：同一会话里用 executing-plans，做完一个任务再进下一个。

Task 1 结束时 18 张框图是浅色，动画和板卡仍是深色，整套测试应当仍绿。Task 3 结束时 53 张都是浅色，版本仍是 1.2.6。Task 5 把画法契约加上，版本仍是 1.2.6。Task 6 才把版本改成 1.2.7。实施 PR 要等到 Task 7 的前三条命令都退出码 0 再开。协调员在 `book` 与 `book-en` 都变绿后 squash 合入。不设章节人审停点。不打 tag，不创建 Release。
