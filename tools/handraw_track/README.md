# handraw_track —— 知识轨手绘图（可复现生成）

本目录生成 `assets/illustrations/handraw/chNN-*.png` 知识轨插图（Handraw 视觉语法：
米色纸面、抖动墨线、普鲁士蓝 / 鼠尾草绿 / 砖红 / 那不勒斯黄，底部「原理示意 / 非实拍」徽章）。

与 ch00–ch12 已入库的 AI 生成图不同，这里的图由脚本确定性生成：
同一种子 → 字节一致的 SVG → Chromium 截图 → PNG。满足
`BOOK_REDESIGN_SPEC.md` §11「生成脚本能重建新增资源、不依赖随机数和网络」。

## 文件

| 文件 | 作用 |
| --- | --- |
| `hd.py` | 绘图原语库：抖动线 / 手绘框 / 手绘箭头 / 高亮条 / 页面骨架 |
| `fig_chNN.py` | 每章的图设计（真实寄存器、公式、版本号来自对应章节正文） |
| `render.py` | Playwright + Chromium 把 SVG 截成 1152×864 PNG |
| `embed.py` | 把 `<p align="center">` 图块插到锚点图之后（zh+en 同步） |

## 重新生成某一章

```bash
cd tools/handraw_track
python fig_ch28.py                          # 写 SVG 到 assets/illustrations/handraw/
python render.py ../../assets/illustrations/handraw/ch28-*.svg
```

渲染依赖本机 Playwright Chromium（与 `tools/svg2gif.py` 依赖本机 Chrome 同理）；
PNG 已提交进 git，CI 与读者不需要这一步。

## 新增一章的图

1. 读该章正文，选 4–6 个锚点（每张图回答一个正文问题，禁止装饰图）。
2. 仿照 `fig_ch28.py` 写 `fig_chNN.py`：固定 seed、真实数字、IG 图型登记写进提交说明。
3. `embed_chNN.py` 里写清 zh/en 的 alt 与图注（证明什么 / 不能证明什么 / 不是实拍）。
4. 渲染后先逐张看图再嵌入；嵌入后跑 `python tools/slop_lint.py` 与
   `python stm32-book/build_html.py --check`。
