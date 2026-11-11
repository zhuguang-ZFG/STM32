# 设计：动画阅读体验修复

## 边界

改动只在**站点渲染层**（`docs/.vitepress/`）。不动 `docs/public/anim/*.svg` 源图、不动 `mcu-book/`（印前 PDF 链路）、不动 `docs/*.md` 正文。因此本书印前 1211 页的产出物不受影响。

## 已确认缺陷与修复

### D1 时长取错：`dur` 用了第一个 `dur=` 而不是主时间轴

**证据**（本机实测，非推断）：
- `docs/.vitepress/anim-decorate.mjs:89-92`：`raw.match(/dur="([\d.]+)s"/)` 取**首个**匹配；而 `scripts/anim-lint.mjs:78` 用 `Math.max(...durs)` 定义主时长。同一份图存在两个"时长"口径。
- 全库枚举：111 张动画，**30 张**首值≠主值，最大偏差 16 倍（`logger-queue-overflow` 0.75s vs 12s）。
- 浏览器实测 `/c/03-volatile`：SVG 内 `dur` 集合 `['1.5s','12s','1s']`，页面 `<figcaption>` 侧元信息显示 `1.5s 一轮`；`svg.getCurrentTime()` = **1.35**（= 1.5 × 0.9），落在 12s 时间轴的 **11%**，即第 ① 阶段。
- `AnimFigure.vue:72-78` 的注释明确要求静止帧停在**末尾**（"结论字幕都在，波形也已经整条画完"），实际停在第 ① 阶段的缺零件状态。截图已确认画面停在第 ① 阶段。

**影响链**：① 标签与进度条周期错；② 减少动效用户的静止帧回到第一阶段，与设计意图相反。

**修复**：`animDuration` 取 `Math.max`，与 `anim-lint` 对齐。规范 §3 已要求"连续动画的 dur 要能整除主 dur"，故最大值即主时长。

### D2 三页动画空舞台（站点）

**证据**：`/build/00-toolchain.html` 中 `.anim-figure` 属性仅 `['class','src']`，`svg=0`、`按钮=0`、`stageHTML` 长度 0。
**根因**：`docs/build/00-toolchain.md:59`、`docs/build/06-flash-debug.md:48`、`docs/c/00-c-in-mcu.md:43` 用 `<AnimFigure src="/anim/x.svg" />`。该形式只有 `mcu-book/build_html.py:63` 的 `ANIM_TAG` 认（渲染为静态 `<img class="anim">`）；站点侧 `config.mts` 只把独占一行的 `![…](/anim/x.svg)` 转成组件（`anim-figure-block` 规则），所以组件拿到空 `markup`。

**修复**：在 `config.mts` 里注册 `md.core.ruler.before('block', …)`，在 block 解析前把这一行改写成等价的 `![caption](/anim/x.svg)`，直接复用已经验证过的内联路径。**不改那三份 md** —— 书籍 `ANIM_TAG` 继续匹配，PDF 链路零改动，风险面最小。

> 实施记录：最初尝试在 `inline` 之后按 token 改写，未命中——markdown-it 把该行作为段落里的 `html_inline` 而非 `html_block`，且 token 形态随行内规则变化。改为源码级重写后一次通过。

### D3 手机端"放大"反而更小

**证据**：375px 视口下实测，行内 SVG 宽 **284px**，点"放大"后 lightbox 内 SVG 仅 **273.4px**（比值 **0.963**）；13px 标签的有效字号从 6.71px 掉到 6.46px。
**根因**：`custom.css:591-599` `.anim-lightbox__card { width: min(94vw,900px); padding: 16px 18px 12px }`，card 内宽 = 94vw − 36px − 边框，小于行内容器宽。

**修复**（两步，缺一不可）：
1. 窄屏放宽 card（`width:100%`、`padding:6px`），使放大视图严格大于行内：0.963 → **1.095**。
2. **光"更大"不够**。720 单位画布在 375px 屏上只能到 0.447×，11px 的规格下限字号实际只剩 **4.91px**，仍然读不了。
   故窄屏下给画布 `min-width: 680px` 并让舞台横向平移，字号回到 **10.39px**（0.944×）。
   验收标准因此改为"有效字号 ≥ 10px 且可横向平移"，而不是"比行内宽"。

### 与印前链路的已知分歧（记录，不在本次改动内）

`mcu-book/build_html.py:1366-1377` 的减少动效分支直接 `pauseAnimations()` 停**首帧**，注释却写"与在线站点 AnimFigure 同一口径"。
站点本次修好后停在 `0.9 × 主时长`（结论帧），两者分歧变大。改印前要动 1211 页产出物，需单独评审，故本次只记录不修改。

### D4 放大视图的可达性

**证据**：打开后 `document.activeElement` 仍是 `BODY`（焦点未进对话框）；`body` 的 `overflow: visible`（背景仍可滚动）。
**修复**：打开时记住并移入焦点、锁背景滚动，关闭时还原。

## 取舍

- **不改 SVG 源图**：`dur` 错在读取侧，改源图要把 30 张兄弟 dur 排序，风险与收益倒挂。
- **不改 md 正文**：D2 在渲染层兜住，避免触碰印前输出。
- **不追 F8**（减少动效下进度条恒 `animation:none`，按下播放也不走）：这更像有意的"减少动态"选择，且与 D1 修复后语义自洽；列为可选，不在本次范围。
- **不追 C4**：深色模式下 SMIL 动画 fill 未漏浅色——实测计算值取的是深色令牌（`rgb(241,245,249)`/`rgb(148,163,184)`），假说被否证。

## 回滚

逐条独立：D1 单函数、D2 单 rule、D3 单媒体查询、D4 单组件方法。任一回归可单独 revert，不牵动其他三条。
