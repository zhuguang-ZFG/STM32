# 讲解海报对齐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只修 `tools/gen_narrated.py` 里 `render_card` 的两处完整帧错误，再用 `python3 tools/gen_narrated.py --posters` 把 29 张 `assets/video/ch*.png` 全部重画，然后把整书标成 **1.2.9 · 2026-10-25**。本计划文件的 PR 不落地这些改动。

**Architecture:** 海报的像素合同是仓库里的 PNG 等于当时的 `render_poster()`。`render_poster()` 就是 `render_card(ch, ch["segments"][0], 1)`。先把要点循环的变量从 `line` 改成 `txt`，让参数 `line` 继续表示高亮序号；再让 `t >= 1` 时要点位移为 0。青条矩形和小芯调用保持原文。29 张在同一次 `--posters` 里写完，和这次的渲染器进同一个提交。不新开测试文件。Book CI 不安装 Pillow，海报合同仍由 `tools/check_assets.py` 的逐像素比对锁住。版本戳和版本断言放在后一个提交。

**Tech Stack:** Python 3、Pillow、文泉驿微米黑（默认 `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc`，`index=0`）、现有 `tools/gen_narrated.py`、`tools/narration.py`、`tools/check_assets.py`、`python3 -m unittest discover stm32-book/tests -v`、`python3 stm32-book/build_html.py --check`。不新增依赖，不改 `requirements.txt`。`stm32-book/requirements.txt` 里没有 Pillow。

`stm32-book/tests/` 不是 Python 包。单条测试写成 `python3 stm32-book/tests/test_build.py BookBuildContractTests.<方法名> -v`。不要写成 `python3 -m unittest stm32-book.tests...`。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。类名是 `BookBuildContractTests`。本刀不新增测试类。

设计规格：`docs/superpowers/specs/2026-10-25-book-posters-align-design.md`（PR #51，`53ef7b0`）。

写本计划时的尖端是 `53ef7b051a3c3d032b31735b534e41a4b1036bad`（`docs: 讲解海报对齐设计，按完整帧重画 (#51)`）。这一尖端的整书版本仍是 **1.2.8**，日期仍是 `2026-10-25`。`53ef7b0` 只新增了设计规格。它下面的 `6a9235e`（PR #50）才是刀 F 的实施。实施基线是本计划合入之后的 `main`，不是本计划的分支。本计划的 PR 只新增本文件。

下面的行号属于 `53ef7b0`。`tools/gen_narrated.py`、`stm32-book/tests/test_build.py`、两份 manifest、`revisions.json`、`stm32-book/README.md` 和 `6a9235e` 逐字节相同。实施时若行号被别的提交挪动，按函数名和引号里的原文定位。

`53ef7b0` 上，和规格一致：

- `builder.CSS` 的 SHA-256 是 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`。
- `stm32-book/styles/tokens.json` 是 `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd`。
- `stm32-book/styles/book.css` 是 `cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480`。
- `stm32-book/cover.svg` 是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。
- `assets/gif/` 40 张，按文件名排序、每行 `{文件名} {该文件字节的 SHA-256}\n` 再做 SHA-256，汇总是 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。`test_sample_svg_c_contract` 锁住这四串样式哈希和这串 GIF 清单哈希。
- `render_card` 在 `SCALE == 1` 时走默认路径。`SCALE != 1` 时转去 `_render_card_hd`。海报不设置 `NARRATED_SCALE`，所以进不了高清分支。
- 青条在 `render_card` 第 324–326 行：`bar_w = int(96 * min(1.0, t / 0.55))`，然后 `draw.rectangle((32, 100, 32 + bar_w, 103), fill=CYAN)`。`t=1` 时 `bar_w` 是 96。Pillow 的矩形两端都算进填充，所以是 x=32..128、y=100..103，共 388 个像素。`CYAN` 是 `(72, 214, 198)`。底色 `BG` 是 `(23, 26, 36)`。
- 无插图的卡在第 366–368 行调用 `_mascot(draw, W - 132, 248, mood, u)`。`W` 是 960，所以中心是 `(828, 248)`。29 张海报的第一拍标题都不含「口诀」「坑」「最常忘」「下一集」「合上书」「收尾」，`mood` 都是 `calm`。
- 要点循环在第 355–365 行。循环写成 `for i, line in enumerate(seg["lines"])`，盖住参数 `line`。`t=1` 且 `i=3` 时，现在的 `dx` 是 9。
- `render_poster()` 在第 456–457 行，就是 `render_card(ch, ch["segments"][0], 1)`。`write_posters()` 在第 512–519 行。`save_png()` 在第 460–466 行：字节已相同时不重写。
- `tools/narration.py` 的 `ch()` 只把章首 SVG 填进带 `svg=True` 的那一拍。29 章的 `segments[0]` 都没有这个标记。海报因此不调用 `_svg_png()`，也不开 Chrome。
- `assets/video/` 里有 29 张 `ch00`–`ch28` 的 PNG，另有 12 张 `chs01`–`chs12` 的 AI 海报。`check_assets.py` 只打开 `gen_narrated.CHAPTERS` 里的那 29 张。
- `validate_revisions()` 在 `stm32-book/build_html.py` 第 820 行。它要求 `revisions.json` 第一条的 `version` 等于 manifest 的 `version`。

设计规格「实施 PR」的 1–6 步在本计划里的位置：

| 规格里的顺序 | 本计划 |
| --- | --- |
| 1. 确认基线 | 开工条件。不产生提交 |
| 2. 渲染器 | Task 1。这一步还不写 PNG，也不提交 |
| 3. 海报 | Task 2。和 Task 1 的渲染器进同一个提交 |
| 4. 版本 | Task 3 |
| 5. 验证 | Task 4 |
| 6. 合入 | Task 4 的最后一步 |

渲染器和 29 张 PNG 必须在同一次提交里。先单独提交渲染器，那一次提交的仓库 PNG 就和 `render_poster()` 对不上。Task 1 只改源码并在内存里核对组甲的差集。Task 2 写 PNG，再把源码和 29 张一起提交。

## Global Constraints

- 本计划 PR 不实施海报对齐。不改 `tools/gen_narrated.py`，不改 `assets/video/`，不改 `stm32-book/`，不升版本，不打 tag，不创建 GitHub Release。CI 变绿不等于本 PR 可以自动合入。等人审完计划再合。
- 实施时可以改的只有：`tools/gen_narrated.py`（只限 `render_card` 的要点循环）、下面清单里的 29 张 `assets/video/ch*.png`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`、`stm32-book/tests/test_build.py`（只限版本断言）。
- 目标版本是 **1.2.9 · 2026-10-25**。预期路径上日期写死 `2026-10-25`。两份 manifest、`revisions.json` 和 README 写同一个版本、同一个日期。
- 实施开始时若 `stm32-book/manifest.json` 的 `version` 已经不是 `1.2.8`，停。先改本计划的版本目标，再动手。不要把 `1.2.9` 硬套到另一版上，也不要在实施分支里自己写下一条修订号。
- 实施 PR 在 Book CI（`.github/workflows/book.yml`，名称 `Book CI`）的 `book` 与 `book-en` 都变绿，并且实施者本机的 `python3 tools/check_assets.py` 退出码为 0 之后，仍由人决定是否 squash 合入 `main`。不在 CI 变绿后自动合。Book CI 不跑 `check_assets.py`，也不安装 Pillow。CI 变绿证明不了海报像素。不改 workflow。
- 不打 tag，不创建 GitHub Release。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 只改 `render_card` 里下面这一处循环。参数名 `line` 保持。高亮序号仍由调用方传入。海报不传，所以是 `None`。`_render_card_hd` 里同名的 `dx` 算式不动。那条算式写着 `sc(12)`，和第 362 行不是同一处。
- 青条矩形、`CYAN`、`_mascot` 的形和调用位置保持 `53ef7b0` 的原文。不删青条，不删小芯。
- 不新增单元测试。不改 `tools/check_assets.py` 的比较方式，不把 `tobytes()` 改成容差，不给任何一张海报留豁免。模块头「不需要任何第三方库」那一句保持原文。
- 29 张只由 `python3 tools/gen_narrated.py --posters` 写出。不附加章号。不附加 `--speak` 或 `--patch-docs`。不导出 `NARRATED_SCALE`、`NARRATED_FONT`、`NARRATED_MODULE`、`NARRATED_OUT`。不跑 `make videos`、`make assets`、`make verify`。`make assets` 会先重写样本 SVG 和 GIF。
- 不改 `tools/narration.py`。不改 29 个 MP4，不改 29 个 SRT。不跑配音。不碰 `assets/video/chs01-ai-basics.png` 到 `assets/video/chs12-ai-capstone.png` 这 12 张。
- 不改 `stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`load_css()`、`stm32-book/cover.svg`、`stm32-book/build_html.py`。刀 F 的七个令牌和 16 处空白保持。`.cover` 的 `92vh` 和 `.part-divider` 的 `52vh` 保持。
- 不改 53 张样本 SVG，不改 `tools/svgkit.py` 和各生成器，不重画 `assets/gif/`、`assets/photos/`、`assets/wechat/`。GIF 清单哈希保持 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。
- 不加厚 `docs/` 或 `docs/en/`。Batch5 不在这一刀。正文 diff 保持为空。
- 不改 `toc_html`、分类函数、罗盘 HTML、书签、章号。出版书签仍是 44 条。不删 `0x271`、`167 ns`、样本章和各批加厚的断言。`pageOverflow` 为 0 的 1200、840、390 三档不放宽。
- 四串样式哈希必须保持开工条件里的值。对不上时停。不要改 `test_sample_svg_c.py` 的期望哈希，不要改令牌或样式去凑。
- 修订说明只用设计里的四句。不写章节名，不写 Batch5。已有修订句子一字不改，包括 1.2.8 刀 F 的两句。
- `test_visual_polish_version_is_1_2_0` 的方法名不改。

上一句「Book CI 变绿后由人决定是否 squash」指海报的实施 PR。本计划文件的 PR 等人审阅，不在 CI 变绿后自动合入，也不在本 PR 里改 `tools/`、`assets/` 或版本。

## 开工条件

实施开始时先读实施分支所基于的 `main` 上的 `stm32-book/manifest.json`，只看 `version` 和 `date`。不要在本计划的分支上改渲染器、海报或版本。

- `version` 低于 `1.2.8`：停。刀 F 还没在这条历史上。不开实施分支。
- `version` 是 `1.2.8` 且 `date` 是 `2026-10-25`：实施版写成 `1.2.9`，日期写成 `2026-10-25`。下面任务里的字面量按这个走。这是预期路径。`53ef7b0` 就是这个状态。
- `version` 已经不是 `1.2.8`，或 `date` 已经不是 `2026-10-25`：停。不要把 `1.2.9` 和 `2026-10-25` 写到另一版书上。先对人说明，并先改本计划的版本目标。
- 四串样式哈希或 GIF 清单哈希已经不是下面的值：停。说明 `main` 上的样式或 GIF 已经离开这份设计所依据的字节。不要在分叉上重画海报，不要改测试期望，不要重算哈希后再继续。

在仓库根核对环境和哈希。环境变量要是空的。默认字体文件必须存在。不要设置 `NARRATED_FONT` 去换一份字体。字体不在默认路径上就停，先安装文泉驿微米黑，让这个路径出现，再重跑本节。

```bash
python3 - << 'PY'
import hashlib
import importlib.util
import os
from pathlib import Path

for name in ("NARRATED_SCALE", "NARRATED_FONT", "NARRATED_MODULE", "NARRATED_OUT"):
    if os.environ.get(name):
        raise SystemExit(f"{name} is set")
font = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
if not font.is_file():
    raise SystemExit(f"missing {font}")
from PIL import ImageFont
face = ImageFont.truetype(str(font), 26, index=0)
import PIL
print("pillow", PIL.__version__)
print("font", face.getname())

root = Path("stm32-book")
print("tokens", hashlib.sha256((root / "styles" / "tokens.json").read_bytes()).hexdigest())
print("book.css", hashlib.sha256((root / "styles" / "book.css").read_bytes()).hexdigest())
print("cover.svg", hashlib.sha256((root / "cover.svg").read_bytes()).hexdigest())
spec = importlib.util.spec_from_file_location("stm32_book_builder", root / "build_html.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print("CSS", hashlib.sha256(module.CSS.encode("utf-8")).hexdigest())

gif_dir = Path("assets/gif")
gifs = sorted(gif_dir.glob("*.gif"), key=lambda path: path.name)
listing = "".join(
    f"{path.name} {hashlib.sha256(path.read_bytes()).hexdigest()}\n" for path in gifs
)
print("gif", len(gifs), hashlib.sha256(listing.encode("utf-8")).hexdigest())
PY
```

`Markdown` 若还没装，先跑 `python3 -m pip install -q 'Markdown>=3.11,<4'`。Expected:

```text
pillow 13.0.0
font ('WenQuanYi Micro Hei', 'Regular')
tokens 9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd
book.css cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480
cover.svg 37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd
CSS aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf
gif 40 bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f
```

设计规格的像素测量是在 Pillow 13.0.0、`raqm` 可用、这份微米黑（字体版本 13107，`index=0`）上做的。Pillow 不是 `13.0.0`，或 `getname()` 不是 `('WenQuanYi Micro Hei', 'Regular')`：停。不要在另一套光栅器上写这 29 张。组甲的旧 PNG 只在这套光栅器上和修完的完整帧相差青条与小芯。换了 Pillow 或字体，要点字形也会变，Task 1 的差集会离开 388 和 7176。

`ffmpeg` 和 `ffprobe` 必须在 `PATH` 里。`check_videos()` 会探测 MP4 并抽前 20 秒看人声。缺了就停，不要改 `check_assets.py` 跳过这一段。

```bash
command -v ffmpeg
command -v ffprobe
```

Expected: 两行都是可执行文件的路径。

再确认循环还是旧的。已经有人改过就停，不要叠第二遍替换。

```bash
python3 - << 'PY'
from pathlib import Path
text = Path("tools/gen_narrated.py").read_text(encoding="utf-8")
old = '''        body_font = _font(26)
        for i, line in enumerate(seg["lines"]):
            shown = t >= 1.0 or t >= 0.22 + 0.24 * i
            wrapped = wrap_text(line, body_font, W - 80, 1, f"{ch['id']} 要点")
            if y + 34 > BAND_TOP - 16:
                raise ValueError(f"{ch['id']} 要点叠进字幕带：{line}")
            if shown:
                dx = int(12 * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))
                col = TEXT if (line is None or i == line) else MUTED
                draw.text((40 + dx, y), wrapped[0], font=body_font, fill=col)
            y += 40
'''
if text.count(old) != 1:
    raise SystemExit(f"old loop count {text.count(old)}")
if "def render_poster(ch):" not in text or "return render_card(ch, ch[\"segments\"][0], 1)" not in text:
    raise SystemExit("render_poster changed")
print("old loop once")
PY
```

Expected: 打印 `old loop once`，退出码 0。

## File map

| 路径 | 实施时的责任 |
| --- | --- |
| `docs/superpowers/plans/2026-10-25-book-posters-align.md` | 本计划。本 PR 只新增这一份 |
| `tools/gen_narrated.py` | Task 1 改 `render_card` 的要点循环。Task 2 和 29 张 PNG 同一提交。不改 `_render_card_hd`、青条、`_mascot`、`main()` |
| `assets/video/` 下表 29 张 PNG | Task 2。只由 `--posters` 写回。不手改像素 |
| `stm32-book/revisions.json` | Task 3：`entries` 最前插入 1.2.9。已有条目一字不改 |
| `stm32-book/manifest.json` | Task 3：`version` 改为 `1.2.9`。`date` 仍是 `2026-10-25` |
| `stm32-book/manifest-en.json` | 同上 |
| `stm32-book/README.md` | Task 3：当前版本句、发布节的版本句、tag 名，以及「也不要把 1.2.8 的产物标成 1.2.9」 |
| `stm32-book/tests/test_build.py` | Task 3：只改版本断言。方法名 `test_visual_polish_version_is_1_2_0` 不改 |

`tools/check_assets.py`、`tools/narration.py`、`stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`stm32-book/cover.svg`、`stm32-book/build_html.py`、`assets/gif/`、`assets/video/*.mp4`、`assets/video/*.srt`、`assets/video/chs*.png` 不在实施 diff 里。它们必须是空的。

## 29 张清单

路径都在 `assets/video/`。组甲是 `4e1306e` 的 25 张。组乙是后来写入的 4 张。两组都重画，没有豁免。第三列是改之前的字节数，验收不锁它。再生之后字节数会变。锁的是和 `render_poster()` 的 RGB 像素一致。

```text
ch00-learn.png 54559 甲
ch01-env.png 52066 甲
ch02-clock.png 48870 甲
ch03-gpio.png 52048 甲
ch04-nvic.png 49643 甲
ch05-tim.png 50514 甲
ch06-uart.png 45403 甲
ch07-i2c.png 46040 甲
ch08-spi.png 45216 甲
ch09-adc.png 50688 甲
ch10-dma.png 50548 甲
ch11-rtc.png 54150 甲
ch12-iap.png 50351 甲
ch13-can.png 57517 甲
ch14-usb.png 49916 甲
ch15-rtos.png 57103 甲
ch16-lp.png 57026 甲
ch17-debug.png 49698 甲
ch18-faq.png 49897 甲
ch19-projects.png 56497 甲
ch20-refs.png 54030 甲
ch21-boards.png 53789 甲
ch22-sim.png 56994 甲
ch23-g0-pins.png 49084 甲
ch24-l4-pins.png 46760 甲
ch25-h7-pins.png 47548 乙
ch26-spl.png 52573 乙
ch27-network.png 55582 乙
ch28-rtos-system.png 68574 乙
```

第一拍有四条要点、因而会踩到 `i=3` 位移的是这三章：

| 章 | 文件 | 第一拍标题 | 四条 |
| --- | --- | --- | --- |
| 01 | `ch01-env.png` | 一条二进制的旅程 | 编译、链接、烧录、复位运行 |
| 08 | `ch08-spi.png` | 四根线各管一件 | 时钟、主机出、主机入、片选 |
| 27 | `ch27-network.png` | 网络从铜线开始 | RJ45 和变压器、PHY、RMII、MAC 与 DMA |

第 00 章第一拍是三条：入门四周打底、进阶六周啃外设、实战八周做作品。章首 SVG 在后面的拍里，不在海报上。

---

### Task 1: 只改 `render_card` 的要点循环

**Files:**
- Modify: `tools/gen_narrated.py`（`render_card` 第 355–365 行那一段循环）
- Test: 这一任务不改 `stm32-book/tests/`。组甲差集用下面的内存脚本核对，脚本不进仓库

**Interfaces:**
- Consumes: `render_card(ch, seg, index, t=1.0, gprog=None, line=None, u=1.0)`。`TEXT` 是 `(236, 239, 244)`，`MUTED` 是 `(168, 178, 196)`，`CYAN` 是 `(72, 214, 198)`，`BG` 是 `(23, 26, 36)`。`wrap_text` 的签名不改。
- Produces: 循环变量名 `txt`。`t >= 1` 时 `dx` 是 0，否则仍是原来的错开算式。参数 `line` 仍是高亮序号。Task 2 依赖这一段已经落在磁盘上的 `render_card`，因为 `--posters` 调的就是它。这一任务不写 PNG，不提交。

不要改第 324–326 行的青条。不要改第 366–368 行的 `_mascot` 调用。不要改第 243–255 行 `_render_card_hd` 里的 `for i, txt in enumerate(lines)` 和 `dx = int(sc(12) * ...)`。高清分支已经用 `txt`，并已经用 `active = line is None or i == line`。默认路径要和它对齐，但不要把高清的面板、`sc()` 和 `k=1.4 * SCALE` 抄进 `render_card`。

- [ ] **Step 1: 整段换成设计规格里的循环**

把 `render_card` 里现在的：

```python
        body_font = _font(26)
        for i, line in enumerate(seg["lines"]):
            shown = t >= 1.0 or t >= 0.22 + 0.24 * i
            wrapped = wrap_text(line, body_font, W - 80, 1, f"{ch['id']} 要点")
            if y + 34 > BAND_TOP - 16:
                raise ValueError(f"{ch['id']} 要点叠进字幕带：{line}")
            if shown:
                dx = int(12 * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))
                col = TEXT if (line is None or i == line) else MUTED
                draw.text((40 + dx, y), wrapped[0], font=body_font, fill=col)
            y += 40
```

整段换成：

```python
        body_font = _font(26)
        for i, txt in enumerate(seg["lines"]):
            shown = t >= 1.0 or t >= 0.22 + 0.24 * i
            wrapped = wrap_text(txt, body_font, W - 80, 1, f"{ch['id']} 要点")
            if y + 34 > BAND_TOP - 16:
                raise ValueError(f"{ch['id']} 要点叠进字幕带：{txt}")
            if shown:
                dx = 0 if t >= 1.0 else int(12 * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))
                col = TEXT if (line is None or i == line) else MUTED
                draw.text((40 + dx, y), wrapped[0], font=body_font, fill=col)
            y += 40
```

`shown`、`y += 40`、颜色式里的参数名 `line` 保持。只把循环变量改成 `txt`，并在 `t >= 1.0` 时把 `dx` 收成 0。`t < 1` 的错开算式一个字符都不改。

不要用编辑器顺手重排 `render_card` 的其余行。字幕循环里的 `for line in sub_lines:` 是另一个 `line`，保持原文。

- [ ] **Step 2: 确认只有这一处变了，高清分支和青条还在**

```bash
python3 - << 'PY'
from pathlib import Path
text = Path("tools/gen_narrated.py").read_text(encoding="utf-8")
new = '''        body_font = _font(26)
        for i, txt in enumerate(seg["lines"]):
            shown = t >= 1.0 or t >= 0.22 + 0.24 * i
            wrapped = wrap_text(txt, body_font, W - 80, 1, f"{ch['id']} 要点")
            if y + 34 > BAND_TOP - 16:
                raise ValueError(f"{ch['id']} 要点叠进字幕带：{txt}")
            if shown:
                dx = 0 if t >= 1.0 else int(12 * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))
                col = TEXT if (line is None or i == line) else MUTED
                draw.text((40 + dx, y), wrapped[0], font=body_font, fill=col)
            y += 40
'''
if text.count(new) != 1:
    raise SystemExit("new loop missing")
if "for i, line in enumerate(seg[\"lines\"])" in text:
    raise SystemExit("old loop remains")
needles = (
    "bar_w = int(96 * min(1.0, t / 0.55))",
    "draw.rectangle((32, 100, 32 + bar_w, 103), fill=CYAN)",
    "_mascot(draw, W - 132, 248, mood, u)",
    "dx = int(sc(12) * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))",
    "active = line is None or i == line",
    "return render_card(ch, ch[\"segments\"][0], 1)",
    "CYAN = (72, 214, 198)",
)
for needle in needles:
    if text.count(needle) != 1:
        raise SystemExit(f"needle {needle!r} count {text.count(needle)}")
print("renderer loop only")
PY
git diff --stat -- tools/gen_narrated.py
git diff --stat -- assets stm32-book tools/check_assets.py tools/narration.py
```

Expected: 打印 `renderer loop only`。第一段 `git diff --stat` 只有 `tools/gen_narrated.py`。第二段无输出。`git diff -- tools/gen_narrated.py` 里只能看到这一段循环：循环变量、错误信息里的名字、以及 `dx = 0 if t >= 1.0 else` 这一行。

- [ ] **Step 3: 组甲在内存里只差青条和小芯，先不要写文件**

这一步读仓库里的旧 PNG，和修完之后的 `render_poster()` 比。不要调用 `save_png`，不要跑 `--posters`。组甲 25 张的差集必须是 388 个青条像素加 7176 个小芯像素。左半区（x < 700）除了青条矩形以外必须没有差集。组乙不参加这个计数，它们的字形本来就不是这套光栅器画的，留给 Task 2 同一条命令重画。

```bash
python3 - << 'PY'
import importlib.util
from pathlib import Path
from PIL import Image

spec = importlib.util.spec_from_file_location("gen_narrated", Path("tools/gen_narrated.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if module.SCALE != 1 or (module.W, module.H) != (960, 540):
    raise SystemExit(f"scale {module.SCALE} size {module.W, module.H}")
CYAN = (72, 214, 198)
BG = (23, 26, 36)
group_a = 0
for ch in module.CHAPTERS:
    seg = ch["segments"][0]
    if seg.get("svg"):
        raise SystemExit(f"{ch['id']} opening card has svg")
    name = module.chapter_name(ch) + ".png"
    old = Image.open(Path("assets/video") / name).convert("RGB")
    new = module.render_poster(ch)
    if old.size != (960, 540) or new.size != (960, 540):
        raise SystemExit(f"size {name}")
    if not ch["id"].isdigit() or int(ch["id"]) > 24:
        old.close()
        continue
    ob = old.tobytes()
    nb = new.tobytes()
    cyan = other = 0
    for i in range(0, len(ob), 3):
        if ob[i:i + 3] == nb[i:i + 3]:
            continue
        p = i // 3
        x, y = p % 960, p // 960
        if 32 <= x <= 128 and 100 <= y <= 103:
            if new.getpixel((x, y)) != CYAN or old.getpixel((x, y)) != BG:
                raise SystemExit(f"bar pixel {name} {x},{y}")
            cyan += 1
        elif x >= 700:
            other += 1
        else:
            raise SystemExit(f"left diff {name} {x},{y}")
    if cyan != 388 or other != 7176:
        raise SystemExit(f"count {name} cyan {cyan} other {other}")
    group_a += 1
    old.close()
if group_a != 25:
    raise SystemExit(f"group A {group_a}")
print("group A 25 x (388 cyan + 7176 mascot)")
PY
git diff --stat -- assets/video
```

Expected: 打印 `group A 25 x (388 cyan + 7176 mascot)`，退出码 0。`git diff --stat -- assets/video` 无输出。

计数不对就停。不要写 PNG，不要放宽 388 或 7176，不要改 `check_assets.py`。先把循环对回 Step 1 的原文。左半区还有差集，说明要点仍是灰的，或第四条仍停在右边 9 像素。

- [ ] **Step 4: 排版检查仍通过，工作区仍没有新的 PNG**

```bash
python3 tools/gen_narrated.py --check
```

Expected: 退出码 0。输出里没有 `[FAIL]`。这一命令会调用 `render_card`，但 `main()` 在 `--check` 时直接退出，不写海报。

```bash
git status --short -- assets/video
```

Expected: 无输出。

不要在这一步提交。`git diff -- tools/gen_narrated.py` 先留在工作区，等 Task 2 和 29 张 PNG 一起提交。

---

### Task 2: 同一次 `--posters` 重画 29 张，并和渲染器同一提交

**Files:**
- Modify: `assets/video/` 下清单里的 29 张 PNG，只通过 `python3 tools/gen_narrated.py --posters` 写回
- Modify: `tools/gen_narrated.py`（Task 1 已经改好的那一段，这一步不再改它）
- Test: `python3 tools/check_assets.py`

**Interfaces:**
- Consumes: Task 1 落在工作区里的 `render_card`。`write_posters()` 对 `selected()` 返回的每一章调用 `render_poster()`，再 `save_png()`。不传章号时 `selected()` 返回全部 `CHAPTERS`。同名 `.gif` 若存在会被删掉。这 29 个章名现在没有同名 GIF。
- Produces: 29 张 PNG，每张 `Image.open(...).convert("RGB").tobytes()` 等于同一次进程里 `render_poster(ch).tobytes()`，尺寸 `960×540`。这一提交同时含渲染器和这 29 张。

不要先提交渲染器。不要只重画对不上的那几张。不要给 `--posters` 加上 `00` 或 `ch00-learn` 这样的参数，那会少画其余章。

- [ ] **Step 1: 在干净环境里只跑海报命令**

确认 Task 1 的差集脚本已经通过，并且 `NARRATED_SCALE`、`NARRATED_FONT`、`NARRATED_MODULE`、`NARRATED_OUT` 都没有设置。然后在仓库根运行：

```bash
python3 tools/gen_narrated.py --posters
```

Expected: 退出码 0。按章序打印 29 行 `[poster] ch00-learn.png` 到 `[poster] ch28-rtos-system.png`。没有 `[poster] chs`。没有配音，没有 `[doc]`。

`write_posters()` 会删掉同名 `.gif`。跑完后这 29 个章名仍不该有同名 GIF。

- [ ] **Step 2: diff 只能是这 29 张 PNG**

```bash
git diff --name-only -- assets tools stm32-book
```

Expected: `tools/gen_narrated.py`，外加清单里的 29 张 `assets/video/ch*.png`。不多不少。不允许出现：

- `assets/video/chs01-ai-basics.png` 到 `assets/video/chs12-ai-capstone.png`
- 任何 `.mp4`、`.srt`、`.gif`
- `tools/narration.py`、`tools/check_assets.py`
- `assets/gif/`、`assets/animations/`、`assets/diagrams/`、`assets/boards/`
- `stm32-book/`

```bash
python3 - << 'PY'
from pathlib import Path
names = """
ch00-learn.png
ch01-env.png
ch02-clock.png
ch03-gpio.png
ch04-nvic.png
ch05-tim.png
ch06-uart.png
ch07-i2c.png
ch08-spi.png
ch09-adc.png
ch10-dma.png
ch11-rtc.png
ch12-iap.png
ch13-can.png
ch14-usb.png
ch15-rtos.png
ch16-lp.png
ch17-debug.png
ch18-faq.png
ch19-projects.png
ch20-refs.png
ch21-boards.png
ch22-sim.png
ch23-g0-pins.png
ch24-l4-pins.png
ch25-h7-pins.png
ch26-spl.png
ch27-network.png
ch28-rtos-system.png
""".split()
video = Path("assets/video")
for name in names:
    gif = video / name.replace(".png", ".gif")
    if gif.exists():
        raise SystemExit(f"gif appeared {gif.name}")
print("29 png, no chapter gif")
PY
```

Expected: 打印 `29 png, no chapter gif`，退出码 0。

29 张以外有 diff 就停。用 `git checkout -- <越界路径>` 撤回越界文件。不要为了消掉 SVG 或 GIF 的 diff 去提交它们。

- [ ] **Step 3: 在写出 PNG 的同一环境里跑素材自检**

```bash
python3 tools/check_assets.py
```

Expected: 退出码 0。输出含这一行：

```text
讲解视频检查完成：29 章 MP4 + SRT + 海报
```

结果行含 `全部通过`。不得出现 `与脚本画出的海报不一致`。不得出现 `[FAIL] …gif 仍在`。

SVG、引脚图、实拍、示例、仿真和链接仍通过。`assets/gif/` 里大于 500 KB 的 `*-zh.gif` 可以打印 `WARN`。`check_assets.py` 的 GIF 段只因此告警，不把总结果设成失败。不要压这些 GIF，不要改 `tools/check_assets.py`。

退出码不是 0 就停。不要改比较器，不要把第 25–28 章从循环里拿掉，不要只重画失败的那几张。若失败原因是字形，而 Pillow 或字体已经和 Task 1 开工时不同，先把 `assets/video/*.png` 和 `tools/gen_narrated.py` 还原，回到写出它们的那台机器重跑 Task 1 和 Task 2。

- [ ] **Step 4: 再跑一次 `--posters`，29 张不得再变**

```bash
python3 tools/gen_narrated.py --posters
git diff --stat -- assets/video
```

Expected: 命令退出码 0，仍是 29 行 `[poster]`。`git diff --stat -- assets/video` 相对 Step 2 没有新增输出。`save_png()` 发现字节相同，不重写。若又变了，先查是不是换了 Pillow、字体或 `NARRATED_SCALE`。不要提交一份和当前 `render_poster()` 对不上的 PNG。

- [ ] **Step 5: 渲染器和 29 张同一提交**

```bash
git add tools/gen_narrated.py assets/video/ch00-learn.png assets/video/ch01-env.png assets/video/ch02-clock.png assets/video/ch03-gpio.png assets/video/ch04-nvic.png assets/video/ch05-tim.png assets/video/ch06-uart.png assets/video/ch07-i2c.png assets/video/ch08-spi.png assets/video/ch09-adc.png assets/video/ch10-dma.png assets/video/ch11-rtc.png assets/video/ch12-iap.png assets/video/ch13-can.png assets/video/ch14-usb.png assets/video/ch15-rtos.png assets/video/ch16-lp.png assets/video/ch17-debug.png assets/video/ch18-faq.png assets/video/ch19-projects.png assets/video/ch20-refs.png assets/video/ch21-boards.png assets/video/ch22-sim.png assets/video/ch23-g0-pins.png assets/video/ch24-l4-pins.png assets/video/ch25-h7-pins.png assets/video/ch26-spl.png assets/video/ch27-network.png assets/video/ch28-rtos-system.png
git commit -m "book: 重画 29 张讲解海报，修好完整帧的要点色和位移"
```

`git show --stat --oneline HEAD` 必须是 30 个路径：1 个 `tools/gen_narrated.py` 和 29 张 PNG。不要加入 `chs*.png`、MP4、SRT、`narration.py`、`check_assets.py`。不要开实施 PR。版本仍是 1.2.8。

---

### Task 3: 把整书标成 1.2.9

**Files:**
- Modify: `stm32-book/revisions.json`（`entries` 最前插入一条）
- Modify: `stm32-book/manifest.json`（只改 `version`）
- Modify: `stm32-book/manifest-en.json`（只改 `version`）
- Modify: `stm32-book/README.md`（当前版本句、发布节的版本句、tag 名，再加一句误标）
- Modify: `stm32-book/tests/test_build.py`（只改版本断言）
- Test: `BookBuildContractTests.test_visual_polish_version_is_1_2_0`、`test_revision_file_lists_1_0_0_through_manifest_version`、`test_english_book_is_a_separate_offline_edition`、`assert_version_history_and_index`

**Interfaces:**
- Consumes: 开工条件定下的 `1.2.9` / `2026-10-25`。`validate_revisions()` 要求 `entries[0]["version"]` 等于两份 manifest 的 `version`。Task 2 的海报已经和 `render_poster()` 一致。`SampleSvgCTests` 不读版本号。
- Produces: 两份 manifest、`revisions.json` 第一条和 README 当前版本句都是 `1.2.9` / `2026-10-25`。1.2.8 的刀 F 两句改到 `entries[1]`，句子原文不改。

这一任务不改 `tools/gen_narrated.py`，不改 29 张 PNG，不改 `test_sample_svg_c.py`，不改样式哈希。已有修订句子一字不改。

`53ef7b0` 上，`test_visual_polish_version_is_1_2_0` 的绑定是：`density = entries[0]`（1.2.8），`entry = entries[1]`（1.2.7），`cover = entries[2]`，`tokens = entries[3]`，`typography = entries[4]`，`batch4 = entries[5]`，`batch3 = entries[6]`，`guide = entries[7]`，`previous = entries[8]`（1.2.0）。实施后各后移一位，新的 `entries[0]` 叫 `posters`。

- [ ] **Step 1: 在 `revisions.json` 最前插入 1.2.9**

`entries` 数组的第一项现在是 1.2.8。在它前面插入下面这一项，并给新项后面留一个逗号。1.2.8 那一项的原文不要动：

```json
    {
      "version": "1.2.9",
      "date": "2026-10-25",
      "zh": [
        "29 张讲解海报按当前完整帧重画：标题下有青条，无插图的卡有小芯，要点用正文色。",
        "样式令牌、封面、样本图和旁白成片不改。"
      ],
      "en": [
        "The 29 lecture posters are redrawn from the current finished frame: a cyan rule under the title, a mascot on cards without a figure, and bullet text in the body color.",
        "Style tokens, the cover, the sample drawings, and the narrated videos stay."
      ]
    },
```

四句必须与上面逐字相同。不要加第五句。不要改 1.2.8 刀 F 的「章距、段距、图距」那两句。

- [ ] **Step 2: 两份 manifest 只改 version**

`stm32-book/manifest.json` 和 `stm32-book/manifest-en.json` 各把这一行：

```json
  "version": "1.2.8",
```

改成：

```json
  "version": "1.2.9",
```

`"date": "2026-10-25"` 保持原文。不要改 `title`、`subtitle`、章号或罗盘。

- [ ] **Step 3: 改 README 的版本句，并追加一句误标**

`stm32-book/README.md` 第 17 行，只改版本号：

```markdown
当前版本：**v1.2.9 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

第 32 行关于 `tokens.json` 和 `book.css` 的那一句保持原文：

```markdown
样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。
```

发布节第 92 行，把开头的 `版本号已经是 1.2.8。` 改成 `版本号已经是 1.2.9。`。保留句末已有的「也不要把 1.2.7 的产物标成 1.2.8。」，并在这句后面紧接：

```text
也不要把 1.2.8 的产物标成 1.2.9。
```

第 98 行的 tag 名改成：

```markdown
3. 在该提交上打 tag `v1.2.9`，创建 GitHub Release，并附上这四份文件。
```

这一步仍不创建 tag，也不创建 Release。README 里的这句话是留给有权限的人以后做的，不是这一刀的实施步骤。

- [ ] **Step 4: 把版本断言后移一位，并锁住新的四句**

`assert_version_history_and_index` 约第 145 行，元组最前加上 `1.2.9`，并在现有 `>1.2.8<` 与 `>1.2.7<` 的比较之前加一行：

```python
        versions = ("1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.9<"), history.index(">1.2.8<"))
        self.assertLess(history.index(">1.2.8<"), history.index(">1.2.7<"))
```

后面从 `>1.2.7<` 到 `>1.0.0<` 的比较保持原文。

`test_revision_file_lists_1_0_0_through_manifest_version` 约第 186 行，列表最前加上 `1.2.9`，下一项仍是 `1.2.8`：

```python
            ["1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

两处 `<strong>v1.2.8</strong>` 改成 `<strong>v1.2.9</strong>`。一处在中文整书测试约第 280 行，一处在 `test_english_book_is_a_separate_offline_edition` 约第 437 行。同一英文测试约第 420 行：

```python
        self.assertEqual("1.2.9", manifest["version"])
```

`test_visual_polish_version_is_1_2_0` 约第 1626 行。删掉原来的九行绑定（`density = revisions["entries"][0]` 到 `previous = revisions["entries"][8]`）以及紧跟着的六行 `assertEqual`（manifest、英文 manifest、`density` 的 version 和 date，含两行 `density["date"]` 与 manifest 日期的比较）。用下面这一段代替。刀 F 的「章距、段距、图距」字符串列表不要删，它仍紧跟在这段最后两行之后，并仍属于现在的 `density`：

```python
        posters = revisions["entries"][0]
        density = revisions["entries"][1]
        entry = revisions["entries"][2]
        cover = revisions["entries"][3]
        tokens = revisions["entries"][4]
        typography = revisions["entries"][5]
        batch4 = revisions["entries"][6]
        batch3 = revisions["entries"][7]
        guide = revisions["entries"][8]
        previous = revisions["entries"][9]
        self.assertEqual("1.2.9", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.2.9", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.2.9", posters["version"])
        self.assertEqual("2026-10-25", posters["date"])
        self.assertEqual(posters["date"], self.manifest["date"])
        self.assertEqual(posters["date"], english["date"])
        self.assertEqual(
            [
                "29 张讲解海报按当前完整帧重画：标题下有青条，无插图的卡有小芯，要点用正文色。",
                "样式令牌、封面、样本图和旁白成片不改。",
            ],
            posters["zh"],
        )
        self.assertEqual(
            [
                "The 29 lecture posters are redrawn from the current finished frame: a cyan rule under the title, a mascot on cards without a figure, and bullet text in the body color.",
                "Style tokens, the cover, the sample drawings, and the narrated videos stay.",
            ],
            posters["en"],
        )
        self.assertEqual("1.2.8", density["version"])
        self.assertEqual("2026-10-25", density["date"])
```

最后两行就是原来的 `density` 版本断言，只是 `density` 现在指 `entries[1]`。它们后面继续是刀 F、刀 C、刀 D、刀 B、刀 E、1.2.3、1.2.2、1.2.1、1.2.0 那些已经写在方法里的 `assertEqual`。字符串列表不要重打。`entry` 现在是 1.2.7，紧跟着的 `self.assertEqual("1.2.7", entry["version"])` 保持原文。1.2.0 现在核对 `entries[9]`，因为 `previous` 已经指到那里。

同一方法末尾的 README 断言换成：

```python
        self.assertIn("当前版本：**v1.2.9 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.9。", readme)
        self.assertIn("样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2，", readme)
        self.assertIn("也不要把 1.2.2 的产物标成 1.2.3，", readme)
        self.assertIn("也不要把 1.2.3 的产物标成 1.2.4，", readme)
        self.assertIn("也不要把 1.2.4 的产物标成 1.2.5，", readme)
        self.assertIn("也不要把 1.2.5 的产物标成 1.2.6。", readme)
        self.assertIn("也不要把 1.2.6 的产物标成 1.2.7。", readme)
        self.assertIn("也不要把 1.2.7 的产物标成 1.2.8。", readme)
        self.assertIn("也不要把 1.2.8 的产物标成 1.2.9。", readme)
        self.assertIn("打 tag `v1.2.9`", readme)
        self.assertNotIn("当前版本：**v1.2.8", readme)
        self.assertNotIn("打 tag `v1.2.8`", readme)
```

不要删「也不要把 1.2.7 的产物标成 1.2.8。」。不要改 `test_css_token_extract_contract` 和 `test_sample_svg_c_contract` 里的哈希字符串。

- [ ] **Step 5: 跑版本测试和整套测试**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_revision_file_lists_1_0_0_through_manifest_version -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_english_book_is_a_separate_offline_edition -v
```

Expected: 三条都通过。

Run:

```bash
python3 -m unittest discover stm32-book/tests -v
```

Expected: 退出码 0，末尾是 `OK`。

只改了测试、还没改 `revisions.json` 和两份 manifest 时，这几条会失败。这是 `validate_revisions()` 的预期。把 Step 1 到 Step 4 放进同一个提交，不要把修订句子改短来迁就。

- [ ] **Step 6: 提交版本戳**

```bash
git add stm32-book/revisions.json stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 把整书标成 1.2.9"
```

这一步不要加入 `tools/gen_narrated.py`、`assets/video/`、`tokens.json`、`book.css`、`cover.svg`。它们在这一步没有新的改动。

---

### Task 4: 验收海报，并停在合入前

**Files:**
- Test: `python3 tools/check_assets.py`、整套 `stm32-book/tests`、中英文 `build_html.py --check`，以及再一次 `--posters` 确认 PNG 不再变化

**Interfaces:**
- Consumes: Task 2 的渲染器与 29 张 PNG，Task 3 的 `1.2.9`。没有新的函数。
- Produces: 下面五条命令退出码 0。实施 PR 的 diff 只含 File map 里 Task 1 到 Task 3 的路径。不产生新的提交，除非验收发现前面的替换漏了。

- [ ] **Step 1: 跑设计规格里的五条命令**

```bash
python3 tools/gen_narrated.py --posters
python3 tools/check_assets.py
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

Expected: 五条退出码都是 0。`--posters` 之后 `git status --short -- assets/video` 无输出。`check_assets.py` 含 `讲解视频检查完成：29 章 MP4 + SRT + 海报`，结果含 `全部通过`，不含 `与脚本画出的海报不一致`。`discover` 的末尾是 `OK`。两条 `--check` 都不打印 `revision history starts at`。

再核对四串样式哈希和 GIF 清单哈希仍是开工条件的输出。`cover.svg` 仍是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。

- [ ] **Step 2: 核对 diff 边界**

```bash
git diff --name-only origin/main
```

可以出现的路径只有：

- `tools/gen_narrated.py`
- 清单里的 29 张 `assets/video/ch*.png`
- `stm32-book/revisions.json`
- `stm32-book/manifest.json`
- `stm32-book/manifest-en.json`
- `stm32-book/README.md`
- `stm32-book/tests/test_build.py`

不允许出现 `docs/00`–`28`、`docs/en/`、`assets/gif/`、`assets/video/chs*.png`、`assets/video/*.mp4`、`assets/video/*.srt`、`tools/narration.py`、`tools/check_assets.py`、`tools/svgkit.py`、`stm32-book/styles/`、`stm32-book/cover.svg`、`stm32-book/build_html.py`、`.github/workflows/book.yml`。

```bash
git diff --stat origin/main -- docs assets/gif assets/video/chs01-ai-basics.png assets/video/chs12-ai-capstone.png stm32-book/styles stm32-book/cover.svg stm32-book/build_html.py tools/narration.py tools/check_assets.py tools/svgkit.py .github/workflows/book.yml
```

Expected: 空。`docs/superpowers/plans/2026-10-25-book-posters-align.md` 若还没在 `main` 上，它可以出现在实施分支里，但实施 PR 的最终 diff 不必再改它。上面这条命令不看 `docs/superpowers/plans/`。

```bash
git diff -U0 -- stm32-book/manifest.json stm32-book/manifest-en.json
git tag --points-at HEAD
```

Expected: 两份 manifest 只有 `version`。`git tag --points-at HEAD` 无输出。不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.9`。

确认这些断言还在：

```bash
grep -n -E '0x271|167 ns|len\(outline\)' stm32-book/tests/test_build.py
```

Expected: `0x271`、`167 ns` 和 `self.assertEqual(44, len(outline))` 仍有匹配。

- [ ] **Step 3: 看第 00 章和第 01 章的海报**

打开 `assets/video/ch00-learn.png` 和 `assets/video/ch01-env.png`。两张都是 960×540。标题下有一条青色短线。右侧有小芯。要点是浅色 `(236, 239, 244)` 那一档，不是灰的 `(168, 178, 196)`。第 01 章四条是「编译」「链接」「烧录」「复位运行」，第四条和上面三条左缘对齐。

不要求把 29 张逐张看完。第 08 章和第 27 章的第四条已由 Task 1 的左半区差集和 Task 2 的逐像素比对盖住。MP4 仍是原来的成片，第一帧可以还没有青条和小芯。海报不和 MP4 的帧对像素。

看不了图片时，在实施 PR 说明里写明已经由组甲的 388+7176 差集和 `check_assets.py` 的 `tobytes()` 比对覆盖，并注明人工抽看没有做。不要为了抽看去改测试、比较器或 PNG。

- [ ] **Step 4: 开实施 PR，并停在 squash 之前**

实施 PR 对着当时的 `main`。标题用中文，说明这是讲解海报对齐的实施，版本 **1.2.9**。正文写明：

- 只改了 `render_card` 的要点循环：循环变量改为 `txt`，`t >= 1` 时 `dx` 为 0。青条和小芯保持。
- 29 张全部由 `python3 tools/gen_narrated.py --posters` 写出，没有豁免。组甲相对旧 PNG 只多出青条和小芯。组乙同一条命令重画。
- 写出 PNG 的 Pillow 版本和字体路径写进说明。`check_assets.py` 在同一环境退出码 0。
- `book` 与 `book-en` 都变绿之后，由人决定是否 squash。CI 变绿不等于海报已经核对过。不打 tag，不创建 Release。

实施者自己不按合并按钮，不跑 `gh pr merge`。CI 还红时不合入。`check_assets.py` 还不是退出码 0 时也不合入。CI 变绿且本机自检通过后，由人决定是否 squash 合入。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。

最终 diff 必须同时有渲染器、29 张 PNG、版本断言和版本戳。不要把仍画着灰色要点的 PNG 留成 PR 的最终内容。

这一步在验收已经通过时没有新的提交。

## 风险

这些都是设计规格里的风险。实施时按这里停，不要在海报 PR 里顺手改样式、样本图或旁白成片。

- **若直接 `--posters` 而不改循环变量，29 张海报会把灰色要点锁进仓库。** Task 1 必须先把 `for i, line` 换成 `for i, txt`。颜色式继续读参数 `line`。
- **若只改颜色、不把 `t >= 1` 的位移收成 0，第 01 章和第 08 章的第四条会停在 x=49。** `dx = 0 if t >= 1.0 else ...` 必须在。海报左缘要和前三条一样，画在 x=40。
- **若把青条或小芯删掉来迁就 `4e1306e` 的 PNG，完整帧就退回去了。** 组甲相对旧 PNG 的差集就是那 388 加 7176。这两处保持。
- **若跑 `make assets` 或 `make verify`，53 张样本 SVG 和 GIF 会离开刀 C 的字节。** 只用 `python3 tools/gen_narrated.py --posters`。
- **若同时跑 `--speak`，会重配旁白并改 MP4。** 这一刀不配音。`main()` 在没有 `--speak` 时不会进 `speak()`。不要加这个参数。
- **若设置 `NARRATED_SCALE`，海报不再是 960×540，比对会失败，并且会走进没有改过的高清分支。** 保持默认 1。不要改 `_render_card_hd` 来迁就一份被放大的海报。
- **若在另一台机器上只重画第 25–28 章，组甲和组乙会来自两套光栅器。** 29 张同一次 `--posters` 写完。
- **若复审机器的 Pillow 和提交机器不同，`check_assets.py` 会再次在字形上失败。** 这不是豁免项。不要放宽 `tobytes()` 比较。回到写出 PNG 的环境重跑。
- **若顺手改 `tokens.json` 或样本 SVG，这一刀就做成了密度或刀 C。** 开工条件的四串哈希和 GIF 清单哈希保持。
- **若组甲差集不是 388+7176 仍去写 PNG，错误的字形会被提交。** Task 1 没过就不要进 Task 2。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 采用做法 3：修两处完整帧错误，青条和小芯不动，29 张全部 `--posters` | Global Constraints，Task 1，Task 2 |
| 循环变量改为 `txt`；参数 `line` 保持；`line is None` 时要点用 `TEXT` | Task 1 |
| `t >= 1` 时 `dx` 为 0；`t < 1` 的错开算式保持 | Task 1 |
| 不改 `_render_card_hd` 里写着 `sc(12)` 的那一处 `dx` | Task 1 Step 2 |
| 青条矩形 `(32, 100, 32 + bar_w, 103)` 与 `_mascot(draw, W - 132, 248, mood, u)` 保持 | Global Constraints，Task 1 |
| 组甲修完后相对旧 PNG 只剩青条 388 与小芯 7176，要点区差集为 0 | Task 1 Step 3 |
| 不给第 25–28 章豁免；29 张同一条命令、同一次提交 | Task 2 |
| 不设置 `NARRATED_SCALE`、`NARRATED_FONT`、`NARRATED_MODULE`；默认字体、`index=0`、`SCALE=1` | 开工条件，Task 2 |
| 不跑 `--speak`、`--patch-docs`、`make assets`、`make verify` | Global Constraints，Task 2 |
| `save_png()` 在字节相同时不重写；提交前再跑一次 `--posters` 工作区不再变化 | Task 2 Step 4，Task 4 Step 1 |
| 不新增单元测试；不改 `check_assets.py`；不把比较改成容差 | Global Constraints |
| `check_assets.py` 退出码 0，输出含 `讲解视频检查完成：29 章 MP4 + SRT + 海报` | Task 2，Task 4 |
| 四串样式哈希与 GIF 清单哈希保持 | 开工条件，Task 4 |
| 建议版本 1.2.9 · 2026-10-25；manifest 已不是 1.2.8 时停，先改本计划 | 开工条件，Task 3 |
| 修订四句；1.2.8 的刀 F 两句改到 `entries[1]` | Task 3 |
| README 保留「也不要把 1.2.7 的产物标成 1.2.8。」，再接 1.2.8 到 1.2.9；tag 名改为 `v1.2.9` | Task 3 |
| `test_visual_polish_version_is_1_2_0` 方法名不改；`versions` 最前加 `1.2.9` | Task 3 |
| 中英 `--check` 与 unittest 通过后，`book` 与 `book-en` 变绿，再由人决定是否 squash | Task 4 |
| 不改 workflow、不改正文、不改 `assets/gif/`、不改 MP4 与 SRT、不碰 `chs*.png`、不打 tag、不创建 Release | Global Constraints，Task 4 |
| 书签 44、`0x271`、`167 ns` | Task 4 Step 2 |
| 抽看第 00 章和第 01 章；第四条「复位运行」与上面三条左缘对齐 | Task 4 Step 3 |
| 设计 PR 不写实施计划；实施计划单独成 PR | 本文件。本计划 PR 只新增这一份 |

## 执行交接

本文件所在的 PR 只审阅计划，不实施海报。它不改 `tools/gen_narrated.py`，不改 `assets/video/`，不升版本。CI 变绿不等于可以自动合入。

实施要等本计划合入 `main`，并且 `stm32-book/manifest.json` 的 `version` 仍是 `1.2.8`、`date` 仍是 `2026-10-25`。然后从那个 `main` 另开分支，按任务顺序做。两种走法：

1. Subagent-Driven：每个任务一个新的执行者，任务之间再审一遍 diff。
2. Inline：同一会话里用 executing-plans，做完一个任务再进下一个。

Task 1 结束时渲染器已改，PNG 还是旧的，整套 `stm32-book` 测试仍按 1.2.8 通过，`check_assets.py` 的海报项仍会失败。这是预期。不要在这一步开实施 PR，也不要提交。Task 2 把渲染器和 29 张 PNG 放进同一个提交，`check_assets.py` 变为退出码 0，版本仍是 1.2.8。Task 3 把版本标成 1.2.9。实施 PR 要等到 Task 4 五条命令都退出码 0 再开。人在 `book` 与 `book-en` 都变绿、并且本机 `check_assets.py` 退出码为 0 之后，决定是否 squash 合入。不打 tag，不创建 Release。
