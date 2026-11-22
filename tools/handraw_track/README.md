# handraw_track —— 知识轨手绘图（可复现生成）

本目录生成 `assets/illustrations/handraw/chNN-*.png` 知识轨插图（Handraw 视觉语法：
米色纸面、抖动墨线、普鲁士蓝 / 鼠尾草绿 / 砖红 / 那不勒斯黄，底部「原理示意 / 非实拍」徽章）。

与 ch00–ch12 已入库的 AI 生成图不同，这里的图由脚本确定性生成：
同一种子 → 字节一致的 SVG → Chromium 截图 → PNG。满足
`BOOK_REDESIGN_SPEC.md` §11「生成脚本能重建新增资源、不依赖随机数和网络」。

画法参考两个公开项目：[excalidraw/excalidraw](https://github.com/excalidraw/excalidraw)
的「抖动线 + 手写框 + 高亮条」视觉语法，以及
[rough-stuff/rough](https://github.com/rough-stuff/rough)
用随机种子生成确定草图线条的思路（两者均为 MIT）。这里按同样的思路用
纯 SVG 原语重写，不复制任何项目资产；图上的寄存器、地址与计数一律来自
对应章节正文，不用装饰性数字。

## 文件

| 文件 | 作用 |
| --- | --- |
| `hd.py` | 绘图原语库：抖动线 / 手绘框 / 手绘箭头 / 高亮条 / 页面骨架 |
| `fig_chNN.py` | 每章的图设计（真实寄存器、公式、版本号来自对应章节正文） |
| `fig_v0_v6.py` | 合并卷 v0 基础篇、v6 实验项目篇的图设计 |
| `fig_arch_*.py` | 各章静态知识板（DMA 期限、Flash 双槽、AI 防线、对账三关等），PNG 发布到 `docs/public/arch/` |
| `render.py` | Playwright + Chromium 把 SVG 截成 1152×864 PNG（并做确定性 256 色重写） |
| `fig_reading.py` | 合并书阅读补图：接线、构建依赖、中断抢占、完成时刻、缓冲区寿命、内存与排错等 22 张机制图 |
| `publish_staged.py` | 暂存族一条命令重建：跑 15 个模块 → 渲染 → 同步进 `docs/public/images/`；期望集合取自生成器输出，缺图算漂移，`--check` 有漂移即退出码 1 |
| `embed.py` | 把 `<p align="center">` 图块插到锚点图之后（zh+en 同步） |

## 重新生成某一章

```bash
cd tools/handraw_track
python fig_ch28.py                          # 写 SVG 到 assets/illustrations/handraw/
python render.py ../../assets/illustrations/handraw/ch28-*.svg
```

合并卷（v0 / v1 / v2 / b3 / onramp / learning / reading）的 86 张图走另一条链：模块把 SVG
写进 `assets/illustrations/staged/<组>/`（**在版本控制里**），PNG 发布到
`docs/public/images/`。整条链一条命令，别手工复制：

```bash
cd tools/handraw_track
python publish_staged.py            # 重建 + 渲染 + 同步
python publish_staged.py --check    # 只比对，有漂移则退出码 1
```

`--check` 会重渲 86 张并与已提交的 PNG 逐字节比对，用来防止"改了图忘了同步"。

期望集合取自**生成器的输出**（`assets/illustrations/staged/` 下每个 SVG 都该有一张
同名 PNG），不是取自 `docs/public/images/` 里现有的文件。所以删掉一张已发布图
不会被当成"本来就没有"：`--check` 会报 `missing` 并退出码 1，普通运行会把它补回来。
发布目录里没有 staged 源的老图只作 `note` 提示，不算漂移。

渲染依赖本机 Playwright Chromium（与 `tools/svg2gif.py` 依赖本机 Chrome 同理）；
PNG 已提交进 git，CI 与读者不需要这一步。

## 画质契约

- 画布固定 `1152×864`；纸面 `#FDF8EA`，墨色 `#2F2E2B`。
- 中文回退 `STKaiti` / `KaiTi`，拉丁仍用 `Segoe Print`；`text()` 的
  尺寸与 `text_w()` 估算要同时看，改字体后必须重渲染并抽查换行。
- `rect()` / `circle()` 的填充与抖动轮廓共用同一条 `<path>`；不要再加
  一层 `<rect>`/`<circle>` 填充，否则会露出「齐边底色 + 歪边线」的
  剪贴画感。
- 琥珀色描边用 `#8A6510`（米色纸上约 5:1）；`#A8801F` 只有 3.4:1，
  小字号标签不要再用。
- 钢笔双描：`stroke()` 对 `sw>=1.8`、非虚线、非动画、非半透明的实心线
  自动补第二次更松的细描（`amp*1.5+0.4`、`sw*0.7`、`opacity 0.30`）。
  `rect(double=False)` 是唯一关掉它的开关，留给药丸、小图标和标签框。
- 面板底色走两条路，别混：
  1. **暂存族（会发布，15 个模块）**：`fig_v0`、`fig_v1a`、`fig_v1b`、
     `fig_v1c`、`fig_v2a`、`fig_v2b`、`fig_v2c`、`fig_v2d`、`fig_v2e`、
     `fig_v4a`、`fig_v7a`、`fig_onramp`、`fig_merged_b3`、`fig_learning`、`fig_reading`
     直接把 `BLUE_FILL` / `GREEN_FILL` / `AMBER_PALE` / `RED_FILL` /
     `SHADOW` 传进 `card()` / `rect()`。它们写 SVG 到
     `assets/illustrations/staged/`，PNG 再落到 `docs/public/images/`——
     **改 `hd.py` 里的常量就会重涂这 86 张已发布图**。
     权威清单是 `publish_staged.py` 的 `MODULES`，别照这段文字抄：
     漏跑任一模块都会留下旧色的 SVG，`python publish_staged.py` 一次跑全，
     `--check` 会比对漂移。
  2. **chNN / app 族**：直接把 `"#FBEFD3"`、`"#F7DCD8"`、`"#E7EFE3"`
     这类字面量传进 `panel()` / `rect()`，常量碰不到它们；要改只能改
     `fig_*.py` 里的字面量。
  任一底色改完都要重算其上每种墨的对比度。现行取值只调**彩度**、不动亮度：
  `GREEN_FILL #E2F7E5`（彩度 9→21）、`BLUE_FILL #E4F0FD`（17→25），
  `AMBER_PALE #FBF0D2`、`RED_FILL #F8E6E1`、`SHADOW #E4DCC9` 保持原值。
  压暗淡底一定会压低深墨对比度（实测 GREEN 在 BLUE_FILL 上由 4.26 掉到 3.94），
  所以面板要"显出颜色"时加大饱和而不是压暗；改完实测最低墨为 4.25。 
- 高亮条走 `marker()`（歪头、歪尾、回笔），不再用对称 `blob()`：椭圆底衬
  会读成贴纸。`htext(hl=True)` 已默认改用 `marker()`。
- 标题：字号 50、压印偏移字 +3/+3（`INK` 0.16）双墨，下面一条重笔（4.2）
  加一条细骑线（1.5，`INK` 0.30）。

## 渲染与压缩

`render.py` 截图为 1152×864 后做一次确定性调色板重写：自适应 256 色、
无抖动、`optimize=True`。这些图只有平涂墨色与平涂底衬，没有渐变和照片，
量得 PSNR 42–45 dB（肉眼不可辨），而提交体积降到约 1/4。
重跑同一 SVG 必须得到同一字节；若改了 `render.py` 的量化参数，
所有 PNG 都要重渲染并在提交说明里写清。

## 新增一章的图

1. 读该章正文，选 4–6 个锚点（每张图回答一个正文问题，禁止装饰图）。
2. 仿照 `fig_ch28.py` 写 `fig_chNN.py`：固定 seed、真实数字、IG 图型登记写进提交说明。
3. `embed_chNN.py` 里写清 zh/en 的 alt 与图注（证明什么 / 不能证明什么 / 不是实拍）。
4. 渲染后先逐张看图再嵌入；嵌入后跑 `python tools/slop_lint.py` 与
   `python -m book.build_html --check`。
