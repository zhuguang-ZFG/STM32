# 讲解海报对齐设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.8**（`6a9235e`，PR #50，2026-10-25）  
上一份视觉设计：[2026-10-25-book-density-F-design.md](2026-10-25-book-density-F-design.md)。刀 F 已在 `6a9235e` 合入。刀 C 的实施是 PR #47，合入 `a481335`。  
本文件只记录讲解海报对齐的设计。它不改 `tools/gen_narrated.py`，不改 `assets/video/`，不改正文，不升版本号，不打 tag，不发布 Release，不新增 `docs/superpowers/plans/` 下的实施计划。

用户顺序是先修海报，再做 Batch5 加厚。这一刀只做 29 张讲解海报。Batch5 的章节范围不在本文件里。

## 背景

对照 `6a9235e` 核对过的事实。像素测量在 Pillow 13.0.0、`raqm` 可用、默认字体 `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc`（文泉驿微米黑，字体版本 13107，`index=0`）、`NARRATED_SCALE` 未设置（等于 1）的环境里完成。

1. **海报比对在 `tools/check_assets.py` 的 `check_videos()`。** 它 `import gen_narrated`，对 `gen_narrated.CHAPTERS` 每一章打开 `assets/video/<chapter_name>.png`，`Image.open(...).convert("RGB")`，再和 `render_poster(ch)` 比尺寸和 `tobytes()`。尺寸必须是 `960×540`。对不上时打印 `[FAIL] <name>.png 与脚本画出的海报不一致`。29 张都通过时，同一函数末尾打印 `讲解视频检查完成：29 章 MP4 + SRT + 海报`。比对的是 RGB 像素，不是 PNG 文件哈希。Book CI 的 `book` 与 `book-en` 不跑 `check_assets.py`，也不安装 Pillow。`stm32-book/requirements.txt` 里没有 Pillow。
2. **`render_poster()` 在 `tools/gen_narrated.py`。** 它就是 `render_card(ch, ch["segments"][0], 1)`。`t` 默认 1，`line` 默认 `None`，`u` 默认 1。文件头写明 `python3 tools/gen_narrated.py --posters` 写每章海报。`Makefile` 的 `videos` 目标就是这一条。`make assets` 会先跑动画、板卡、框图和 GIF 的生成器，再跑 `videos`。`check_assets.py` 的模块头仍写「不需要任何第三方库」；海报这一段实际要 Pillow。本刀不改这句说明。
3. **29 张的第一张卡都没有 SVG。** `tools/narration.py` 的 `ch()` 只把章首 SVG 填进带 `svg=True` 的那一拍。29 章的 `segments[0]` 都没有这个标记。`render_poster()` 因此不调用 `_svg_png()`，也不开 Chrome。刀 C 把 53 张样本 SVG 改成浅色纸底，进不了这 29 张海报。PR #47 已写明：`check_assets.py` 退出码 1，SVG 53/53 合法，29 张海报和 `render_poster()` 对不上；第 00 章第一张卡没有 SVG，对不上的点在青条像素，不是那批浅色图。`assets/video/` 和 `tools/gen_narrated.py` 在那次 PR 里的 diff 为空。
4. **第 00–24 章的 PNG 仍是 2026-10-08 的画面。** 这 25 张最后一次写入是 `4e1306e`。当时的 `render_card` 没有标题下青条，也没有小芯。在本机把 `4e1306e` 的 `render_poster()` 再跑一遍，这 25 张和仓库里的 PNG 逐像素相同。现在的 `render_poster()` 对不上，差集不是字体漂移。
5. **青条是 `4d48cb3` 加进完整帧的。** `6a9235e` 的 `render_card` 在 `t=1` 时执行 `bar_w = int(96 * min(1.0, t / 0.55))`，然后 `draw.rectangle((32, 100, 32 + bar_w, 103), fill=CYAN)`。`CYAN` 是 `(72, 214, 198)`。Pillow 的矩形两端都算进填充，所以是 x=32..128、y=100..103，共 97×4 = 388 像素。仓库 PNG 上这 388 像素是底色 `(23, 26, 36)`。标题滑入在 `t=1` 时位移为 0，青条宽度已经走满。
6. **小芯也是同一版完整帧的一部分。** 无插图的卡在要点之后调用 `_mascot(draw, W - 132, 248, mood, u)`。29 张海报的第一拍标题都不含「口诀」「坑」「最常忘」「下一集」「合上书」「收尾」，`mood` 都是 `calm`。把下面两处完整帧错误修掉之后，第 00–24 章相对仓库 PNG 的剩余差集每一张都相同：青条 388 像素，小芯 7176 像素，要点区 0 像素。小芯这 7176 像素相对底色的构成是芯片体 `(38, 44, 62)` 5530、`CYAN` 922、`LINE` `(58, 68, 88)` 312、`TEXT` `(236, 239, 244)` 258、`AMBER` `(255, 186, 92)` 97、`MUTED` `(168, 178, 196)` 57。
7. **`t=1` 的要点色被循环变量盖住了。** `render_card` 的参数 `line` 表示当前高亮的要点序号，`None` 表示不高亮。文档写「`t=1`、`line=None` 就是完整帧」。循环写成 `for i, line in enumerate(seg["lines"])`，把参数盖掉。颜色式 `TEXT if (line is None or i == line) else MUTED` 看到的 `line` 已经是字符串，于是每一条要点都用 `MUTED`。高清分支 `_render_card_hd` 用的是 `txt`，并用 `active = line is None or i == line`，没有这个覆盖。海报走 `SCALE == 1` 的 `render_card`，不走高清分支。第 00 章上，这把 1779 个正文色像素画成了灰色，加上抗锯齿边缘，落在青条以外的左半区。
8. **第四条要点在 `t=1` 时还没滑到位。** 位移是 `dx = int(12 * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))`。`i=3` 的起点是 0.94，滑完要到 1.24。`t=1` 时 `dx` 是 9。第一拍有四条要点的是第 01 章（编译、链接、烧录、复位运行）、第 08 章（时钟、主机出、主机入、片选）和第 27 章。前两章在修掉颜色覆盖之后，左半区仍有 1650 和 832 个像素对不上，包围盒都在第四条那一行（y=235..259）。把 `t >= 1` 的 `dx` 收成 0 之后，第 00–24 章的左半区差集为 0。任意一拍里要点最多 5 条；海报只用第一拍，第一拍最多 4 条。
9. **第 25–28 章是后来写的，青条已经在图上。** `ch25-h7-pins.png` 在 `70112eb`，`ch26-spl.png` 与 `ch27-network.png` 在 `0941da5`，`ch28-rtos-system.png` 在 `4b88d5e`。四张的 y=100..103 都已经有 97 个 `CYAN` 像素，和现在的青条矩形一致，青条矩形内的差集是 0。第一拍的 `head`、`lines`、`say` 从各自的写入提交到 `6a9235e` 没有改字。在本机上，它们对不上 `4e1306e` 的 `render_poster()`，也对不上 `70112eb` 和 `6a9235e` 的 `render_poster()`。第 25 章有 35823 个像素不同，其中 23525 个在 1 像素邻域里也找不到同色。这是另一台光栅器留下的字形和描边，不是浅色 SVG，也不是还缺一根青条。
10. **旁白成片不跟海报一起重画。** `ch00-learn.mp4` 到 `ch24-l4-pins.mp4` 仍是 `4e1306e`。第 25 章的 MP4 在 `70112eb`，第 26、27 章在 `0941da5`，第 28 章在 `4b88d5e`。`check_videos()` 核对编码、时长、字幕和人声，不把海报和 MP4 的帧做像素比对。`gen_narrated.py` 写明在线配音不是逐比特稳定的，所以海报可以单画。`assets/video/` 里这 29 个章名没有同名 `.gif`。另有 12 张 `chs01`–`chs12` 的 AI 海报，不在 `narration.CHAPTERS` 里，`check_assets.py` 不打开它们。
11. **版本字面量是 1.2.8。** `revisions.json` 第一条是刀 F 的两句，日期 `2026-10-25`。两份 manifest 的 `version` 是 `1.2.8`。`stm32-book/README.md` 当前版本句是 **v1.2.8 · 2026-10-25**。`builder.CSS` 的 SHA-256 是 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`。`tokens.json` 是 `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd`。`book.css` 是 `cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480`。`cover.svg` 是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。`test_sample_svg_c_contract` 锁住这四串，并锁住 `assets/gif/` 40 张文件名加 SHA-256 的清单哈希 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。

## 目标与非目标

### 目标

- `python3 tools/check_assets.py` 退出码 0。29 张海报都和当时的 `render_poster()` 逐像素相同。不给任何一张海报留豁免。`check_videos()` 里原有的 MP4、字幕、人声和章节引用检查仍通过。
- 实施时先改 `render_card` 里下面两处，再只跑 `python3 tools/gen_narrated.py --posters`，把 29 张 PNG 写成这次进程的输出。
- 青条和小芯留在完整帧上。要点在 `t=1` 且 `line is None` 时用 `TEXT`。四条要点在 `t=1` 时左缘都是 x=40。
- 实施时的版本目标是 **1.2.9 · 2026-10-25**。本设计 PR 不升版本。
- 设计 PR 与实施 PR 都等人审。CI 变绿之后不自动合。squash 由人决定。合入不打 tag，不创建 Release。

### 非目标

- 不改 `stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`load_css()` 和阅读面间距。刀 F 的七个令牌和 16 处空白保持。
- 不改 `stm32-book/cover.svg`，不改 `.cover` 的 `92vh`，不改 `.part-divider` 的 `52vh`。
- 不改 53 张样本 SVG，不改 `tools/svgkit.py` 和各生成器，不重画 `assets/gif/`、`assets/photos/`、`assets/wechat/`。
- 不加厚 `docs/` 或 `docs/en/`。不改旁白稿 `tools/narration.py`。不跑 `--speak`，不重写 29 个 MP4 和 SRT。不跑 `--patch-docs`。
- 不改 `tools/check_assets.py` 的比较方式，不把像素比对改成容差，不把第 25–28 章标成豁免。
- 不改 `_render_card_hd`。海报在默认 `SCALE == 1` 时进不了它。不改 `CYAN`、青条矩形、`_mascot` 的形和调用位置。
- 不碰 `assets/video/chs*.png`。不设置 `NARRATED_MODULE`、`NARRATED_SCALE`、`NARRATED_FONT`。
- 不跑 `make assets`，也不跑 `make verify`。这两条会重写样本 SVG 和 GIF。
- 不改 `.github/workflows/book.yml`。
- 不打 tag，不创建 GitHub Release。

## 方案

海报的像素合同是：仓库里的 PNG 等于当前 `render_poster()`。脚本是完整帧的来源。`4e1306e` 的 PNG 是来源被改写之前的存档。

做法 1 不改脚本，直接 `python3 tools/gen_narrated.py --posters`。29 张会和当前函数逐像素相同，`check_assets.py` 的海报项能过。写进仓库的画面会带上灰色要点，第 01、08、27 章的第四条还会停在右边 9 像素。这和「`t=1` 就是完整帧」相反。高清分支已经按参数 `line` 上色，默认海报路径却没有。

做法 2 把 `render_card` 退回 `4e1306e`：去掉青条和小芯，让第 00–24 章在本机直接和旧 PNG 相同，再只重画第 25–28 章。青条在 `t=1` 时已经画满，小芯是无插图卡的完整帧。第 25–28 章的文件里已经有这根青条。退回脚本是在改合同，不是在履行合同。

做法 3 只改默认路径上两处完整帧错误，青条和小芯不动，然后 29 张全部用 `--posters` 重画。颜色改完后，`line is None` 的要点用 `TEXT`。`t >= 1` 时要点位移为 0，入场过程里 `t < 1` 的错开保持。第 00–24 章相对旧 PNG 只多出那 388 像素青条和 7176 像素小芯。第 25–28 章用同一次进程重画，字形跟这次的 Pillow 和字体走。

采用做法 3。

## 渲染器

只改 `tools/gen_narrated.py` 里 `render_card` 的要点循环。`6a9235e` 上这段是：

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

参数名 `line` 保持。高亮序号仍由调用方传入。海报不传，所以是 `None`。`_render_card_hd` 里同名的 `dx` 算式不动；那条算式写着 `sc(12)`，和上面这一行不是同一处。

不新增单元测试。Book CI 不安装 Pillow，海报合同仍由 `check_assets.py` 的逐像素比对锁住。

## 再生

渲染器按上一节改完之后，在仓库根、同一次进程里跑：

```bash
python3 tools/gen_narrated.py --posters
```

不附加章号。不附加 `--speak` 或 `--patch-docs`。不导出 `NARRATED_SCALE`、`NARRATED_FONT`、`NARRATED_MODULE`。默认字体、`index=0`、`SCALE=1` 保持。需要本机有 Pillow 和文泉驿微米黑。这 29 张不栅格化 SVG，不需要 Chrome。

`write_posters()` 会删掉同名 `.gif`。这 29 个章名现在没有同名 GIF。跑完之后也不该出现。

然后在同一环境和同一次提交里跑 `python3 tools/check_assets.py`。海报像素由这一次的 `render_poster()` 产生，检查也调用同一次代码路径上的 `render_poster()`。另一台 Pillow 或另一份 FreeType 会让字形再次对不上。出现这种情况时停，不要改比较器，也不要只重画对不上的那几张。在写出 PNG 的那台机器上重跑 `--posters` 和 `check_assets.py`。

`save_png()` 在文件字节已相同时不重写。实施 PR 里对这 29 张再跑一次 `--posters`，工作区应不再变化。

## 29 张清单

路径都在 `assets/video/`。组甲是 `4e1306e` 的 25 张，本机旧渲染器可以逐像素复现。组乙是后来写入的 4 张，青条已经在图上，字形和本机 Pillow 13.0.0 不一致。

| 文件 | 字节 | 写入 | 组 |
| --- | --- | --- | --- |
| `ch00-learn.png` | 54559 | `4e1306e` | 甲 |
| `ch01-env.png` | 52066 | `4e1306e` | 甲 |
| `ch02-clock.png` | 48870 | `4e1306e` | 甲 |
| `ch03-gpio.png` | 52048 | `4e1306e` | 甲 |
| `ch04-nvic.png` | 49643 | `4e1306e` | 甲 |
| `ch05-tim.png` | 50514 | `4e1306e` | 甲 |
| `ch06-uart.png` | 45403 | `4e1306e` | 甲 |
| `ch07-i2c.png` | 46040 | `4e1306e` | 甲 |
| `ch08-spi.png` | 45216 | `4e1306e` | 甲 |
| `ch09-adc.png` | 50688 | `4e1306e` | 甲 |
| `ch10-dma.png` | 50548 | `4e1306e` | 甲 |
| `ch11-rtc.png` | 54150 | `4e1306e` | 甲 |
| `ch12-iap.png` | 50351 | `4e1306e` | 甲 |
| `ch13-can.png` | 57517 | `4e1306e` | 甲 |
| `ch14-usb.png` | 49916 | `4e1306e` | 甲 |
| `ch15-rtos.png` | 57103 | `4e1306e` | 甲 |
| `ch16-lp.png` | 57026 | `4e1306e` | 甲 |
| `ch17-debug.png` | 49698 | `4e1306e` | 甲 |
| `ch18-faq.png` | 49897 | `4e1306e` | 甲 |
| `ch19-projects.png` | 56497 | `4e1306e` | 甲 |
| `ch20-refs.png` | 54030 | `4e1306e` | 甲 |
| `ch21-boards.png` | 53789 | `4e1306e` | 甲 |
| `ch22-sim.png` | 56994 | `4e1306e` | 甲 |
| `ch23-g0-pins.png` | 49084 | `4e1306e` | 甲 |
| `ch24-l4-pins.png` | 46760 | `4e1306e` | 甲 |
| `ch25-h7-pins.png` | 47548 | `70112eb` | 乙 |
| `ch26-spl.png` | 52573 | `0941da5` | 乙 |
| `ch27-network.png` | 55582 | `0941da5` | 乙 |
| `ch28-rtos-system.png` | 68574 | `4b88d5e` | 乙 |

实施之后这 29 个字节数会变。验收不锁这些旧字节数，锁的是和 `render_poster()` 的像素一致。

## 版本

实施 PR 把整书标成 **1.2.9 · 2026-10-25**。本设计 PR 不动版本文件。

`revisions.json` 最前面插入一条，日期 `2026-10-25`：

- zh：`29 张讲解海报按当前完整帧重画：标题下有青条，无插图的卡有小芯，要点用正文色。`
- zh：`样式令牌、封面、样本图和旁白成片不改。`
- en：`The 29 lecture posters are redrawn from the current finished frame: a cyan rule under the title, a mascot on cards without a figure, and bullet text in the body color.`
- en：`Style tokens, the cover, the sample drawings, and the narrated videos stay.`

两份 manifest 的 `version` 改为 `1.2.9`，`date` 仍是 `2026-10-25`。

`stm32-book/README.md`：

- 当前版本句改为 **v1.2.9 · 2026-10-25**。
- 「版本号已经是 1.2.8。」改为「版本号已经是 1.2.9。」
- 在「也不要把 1.2.7 的产物标成 1.2.8。」之后接「也不要把 1.2.8 的产物标成 1.2.9。」
- 发布步骤里的 tag 从 `v1.2.8` 改为 `v1.2.9`。

`test_visual_polish_version_is_1_2_0` 的方法名不改。`entries[0]` 改为核对上面四句。现在由 `entries[0]` 核对的 1.2.8 密度两句改到 `entries[1]`，后面的下标顺延。`assert_version_history_and_index` 的 `versions` 最前加上 `1.2.9`，并断言 `>1.2.9<` 出现在 `>1.2.8<` 之前。README 相关断言改到 1.2.9，并保留「也不要把 1.2.7 的产物标成 1.2.8。」。不删更早版本的断言。

## 工作流与 PR 节奏

设计 PR 等人审阅后再合。实施 PR 在 `book` 与 `book-en` 变绿、并且实施者本机的 `check_assets.py` 退出码为 0 之后，仍等人决定是否 squash。两份 PR 都不在 CI 变绿后自动合。这一刀不改正文。

### 本 PR（设计）

只新增本文件。不改 `docs/` 章节、`docs/en/`、`stm32-book/`、`assets/`、`tools/`、`CREDITS.md`、`.github/`。不升版本，不打 tag，不发 Release。不新增实施计划。不再生海报。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **确认基线。** `builder.CSS`、`tokens.json`、`book.css`、`cover.svg` 的哈希仍是背景一节的四串。GIF 清单哈希仍是 `bd674b4a…`。`manifest.json` 的 `version` 仍是 `1.2.8`。若已经不是 1.2.8，停，先改本文件的版本目标再动手。
2. **渲染器。** 只做「渲染器」一节那一处替换。
3. **海报。** 跑「再生」一节那一条命令。diff 里的 `assets/video/` 只能是上表 29 张 PNG。
4. **版本。** 按「版本」一节改 `revisions.json`、两份 manifest、`stm32-book/README.md` 和 `stm32-book/tests/test_build.py`。
5. **验证。** 下面四条在同一环境通过之后，再请求合入。`check_assets.py` 的输出里要有 `讲解视频检查完成：29 章 MP4 + SRT + 海报`，并且结果行是全部通过。不得出现 `[FAIL] … 与脚本画出的海报不一致`。

```bash
python3 tools/gen_narrated.py --posters
python3 tools/check_assets.py
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

验证清单里的 `--posters` 是提交前的最后一次生成。它跑完后，这 29 张 PNG 不应再变。若又变了，先查是不是换了 Pillow 或字体。

6. **合入。** `book` 与 `book-en` 都变绿之后，由人决定是否 squash 合入 `main`。合入后在 `D:\Users\STM32` 拉取这次 `main`。不打 tag，不创建 Release。

实施 PR 的 diff 可以碰：`tools/gen_narrated.py`、上表 29 张 `assets/video/ch*.png`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`、`stm32-book/tests/test_build.py`。不碰 `tokens.json`、`book.css`、`cover.svg`、`build_html.py`、章节正文、`tools/narration.py`、`tools/check_assets.py`、`assets/gif/`、`assets/video/*.mp4`、`assets/video/*.srt`、`assets/video/chs*.png`、`.github/workflows/book.yml`。

## 风险

- **若直接 `--posters` 而不改循环变量，29 张海报会把灰色要点锁进仓库。** 先换掉 `for i, line`。
- **若只改颜色、不把 `t >= 1` 的位移收成 0，第 01 章和第 08 章的第四条会停在 x=49。** 海报左缘要和前三条一样，在 x=40。
- **若把青条或小芯删掉来迁就 `4e1306e` 的 PNG，完整帧就退回去了。** 这两处保持。
- **若跑 `make assets` 或 `make verify`，53 张样本 SVG 和 GIF 会离开刀 C 的字节。** 只用 `python3 tools/gen_narrated.py --posters`。
- **若同时跑 `--speak`，会重配旁白并改 MP4。** 这一刀不配音。
- **若设置 `NARRATED_SCALE`，海报不再是 960×540，比对会失败，并且会走进没有改过的高清分支。** 保持默认 1。
- **若在另一台机器上只重画第 25–28 章，组甲和组乙会来自两套光栅器。** 29 张同一次 `--posters` 写完。
- **若复审机器的 Pillow 和提交机器不同，`check_assets.py` 会再次在字形上失败。** 这不是豁免项。不要放宽 `tobytes()` 比较。回到写出 PNG 的环境重跑。
- **若顺手改 `tokens.json` 或样本 SVG，这一刀就做成了密度或刀 C。** 背景一节的四串哈希和 GIF 清单哈希保持。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-book-posters-align-design.md`。
- `stm32-book/`、`docs/` 章节、`docs/en/` 章节、资产、工具、workflow 和基线 `6a9235e` 相同。
- 版本号仍是 1.2.8。没有 tag，没有 Release。没有实施计划。没有新的海报 PNG。

### 实施 PR

- `python3 tools/check_assets.py` 退出码 0。输出含 `讲解视频检查完成：29 章 MP4 + SRT + 海报`，不含海报不一致的 `[FAIL]`。SVG、16 张 ASCII GIF、实拍、链接仍通过。没有新的豁免。
- `python3 -m unittest discover stm32-book/tests -v` 通过。中文与英文 `build_html.py --check` 通过。`book` 与 `book-en` 都绿。
- `builder.CSS`、`tokens.json`、`book.css`、`cover.svg` 的哈希仍是背景一节的四串。GIF 清单哈希仍是 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。
- `docs/` 与 `docs/en/` 的正文 diff 为空。`assets/video/` 的 diff 只有上表 29 张 PNG。
- 版本是 1.2.9 · 2026-10-25。没有 tag，没有 Release。

抽看第 00 章和第 01 章的海报即可：标题下有一条青色短线，右侧有小芯，要点是浅色而不是灰，第 01 章第四条「复位运行」和上面三条左缘对齐。不要求把 29 张逐张目视看完。MP4 仍是原来的成片，第一帧可以还没有青条和小芯；海报不和 MP4 帧对像素。

## 未决问题

没有会挡住海报实施的未决项。下面几项按此处的默认执行。复审规格时可以改口。改「还要不要留青条」或「还要不要改要点色」要在实施开始前定，并先改本文件。

1. **采用做法 3。** 修循环变量和 `t >= 1` 的位移，然后 29 张全部 `--posters`。不退回 `4e1306e` 的画面，也不带着灰色要点再生。
2. **青条矩形和小芯调用保持 `6a9235e` 的写法。** 不改颜色，不改坐标。
3. **不豁免第 25–28 章。** 它们和组甲同一条命令重画。
4. **不重配旁白，不改比较器，不跑 `make assets`。**
5. **版本。** 实施开始时若 `manifest.json` 仍是 `1.2.8`，实施 PR 写成 **1.2.9 · 2026-10-25**。本设计 PR 不升。两份 PR 都等人审，squash 由人决定。不打 tag，不创建 Release。
6. **Batch5 加厚不在这一刀。** 正文 diff 保持为空。

## 英文提要

Lecture-poster alignment only, on v1.2.8 (`6a9235e`, PR #50). `check_assets.py` fails all 29 posters against `render_poster()`. None of the 29 opening cards carries an SVG, so the light sample drawings from knife C are not the cause. Posters `ch00`–`ch24` were written at `4e1306e` and still match that revision's renderer pixel for pixel on Pillow 13.0.0 with WenQuanYi Micro Hei. The current finished frame adds a 388-pixel cyan rule at `(32,100)–(128,103)` and a 7176-pixel mascot. Two accidents in `render_card` must be fixed before regenerating: the loop variable `line` shadows the highlight index and paints every bullet `MUTED`, and bullet index 3 is still 9 pixels short of its rest position at `t=1`. Rename the loop variable to `txt` and force `dx = 0` when `t >= 1`. Keep the rule and the mascot. Then run `python3 tools/gen_narrated.py --posters` once for all 29 files, including `ch25`–`ch28`, whose PNGs already contain the rule but were rasterized on another Pillow. Do not change tokens, `book.css`, the cover, the 53 sample SVGs, GIFs, narration copy, MP4s, or SRTs. Do not run `make assets`. The poster check stays an exact RGB compare, with no exemptions. The provisional implementation version is 1.2.9 dated 2026-10-25. This design PR does not bump the version. Review before merge. A person decides whether to squash. Do not tag and do not create a Release. This design PR only adds this file.
