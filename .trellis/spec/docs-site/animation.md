# 动画规范（docs/public/anim/*.svg）

一张动画 = 一个可独立打开的 `.svg` + 站点侧的统一包装（`AnimFigure`）。
文件本身保持"裸 SVG"：不带 CSS、不带脚本、颜色写成属性。站点在构建期把原文内联进页面 chunk，
再用 class 覆盖属性色，于是同一个文件既能独立查看（浅色），也能跟随站点深浅主题。

## 1. 画布与排版

| 项 | 约定 |
|---|---|
| viewBox | `0 0 720 <400–470>`，宽度一律 720，高度按内容 |
| 底色 | 首元素 `<rect width="720" height="<h>" fill="#f6f8fa"/>` |
| 主标题 | `x="24" y="30"` `font-size="17" font-weight="bold" fill="#3451b2"` |
| 副标题 | `x="24" y="50"` `font-size="12" fill="#666"`，一句话交代口径/参数 |
| 卡片 | `fill="#ffffff" stroke="#cbd5e1" rx="8"`；面板 `#f8fafc`/`#f1f5f9`；分隔线 `#e2e8f0` |
| 正文/代码 | `#333`，等宽写 `font-family="Consolas,monospace"` |
| 语义色 | 品牌 `#3451b2` · 成功/硬件 `#3eaf7c`（深 `#1a7f56`）· 警示 `#d97706`（深 `#92400e`）· 错误 `#dc2626` · 次要 `#666` · 弱化 `#888`/`#94a3b8` |
| 字号 | ≥11px；注释性文字 ≥12px |

**颜色只能从上表取。** 站点靠一张固定映射表把属性色换成主题 class
（`docs/.vitepress/anim-decorate.mjs` 的 `FILL_CLASS`/`STROKE_CLASS`）：新造一个十六进制值 = 深色模式下漏网。
半透明底纹同理——**不要写 `rgba(...)`**（映射表不认识），要么用表里的浅色 wash（`#dbe7ff`/`#d8f3e5`/`#fdf0d5`），
要么往映射表里加一项并在 `custom.css` 补 `html.dark` 的对应变量。

## 2. 元数据

`<svg>` 之后紧跟 `<title>` 与 `<desc>`：前者是图名，后者把整段动画的因果讲完一遍（读屏与"关掉动效"的人只看得到这两行）。
`<desc>` 不能是套话，要能独立承载结论。

## 3. 阶段时间轴

一轮 = `dur="8s…18s"`（复杂机制允许到 18s），阶段数 4–6，等分。约定：

- 每个阶段一组 `<g opacity>` + `<animate attributeName="opacity" calcMode="discrete" …>`；
- 阶段字幕：`<g font-size="13" font-weight="bold" fill="#3451b2">` 包 N 个 `<g>`，每段一行 `y` 相同；
- 阶段指示点：`<g transform="translate(<720-36-(N-1)*18>,<字幕 y+22>)" fill="#3451b2">`，N 个 `r="5"` 圆点。

**SMIL 的 discrete 语义**：第 i 个值生效区间是 `[keyTimes[i], keyTimes[i+1])`。
所以 N 个阶段要写 N+1 个 `keyTimes`（首 0 尾 1）与 N+1 个 `values`，末值只是回环瞬间的占位。
写成 `values="0;0;0;0;1"` 配 `keyTimes="0;0.25;0.5;0.75;1"` 的"最后一个 1"，最后一个阶段**永远看不见**——
正确写法是 `values="0;0;0;1;0"`（1 放在第 N 个槽位）。指示点则用 `1`/`0.2` 两档。

## 4. 动效：必须有"在跑"的东西

只有阶段切换 = 幻灯片，不算动画。每张图至少有一处**连续**运动，而且运动本身就是结论的一部分
（禁装饰性动画的老规矩不变）。三件够用且便宜的武器：

1. **爬线**——`<path>` 上写 `pathLength="1000"` + `stroke-dasharray="1000"`，再 `<animate attributeName="stroke-dashoffset" values="1000;0;0" keyTimes="0;0.5;1">`。
   波形/连线像被逻辑分析仪逐点抓出来。样板：`uart-frame.svg`。
2. **生长箭头**——`<line>` 的 `x2`（或 `y2`）从发端插到收端，箭头 marker 自然骑在尖端；比整条线突然浮现更能说明"报文在路上"。样板：`tcp-handshake.svg`。
3. **节拍脉冲**——给"重复发生"的事写一个短 `dur`（1s、0.7s）的 `repeatCount="indefinite"`，
   与主时间轴无关：左边 12s 一闪、右边每秒一闪，就是 volatile 的差别。样板：`volatile-as-if.svg`。

连续动画的 `dur` 要能整除主 `dur`，否则回环时肉眼可见地错位。

## 5. 站点侧会发生什么（改图前先知道）

- `config.mts` 的 `anim-figure-block` 规则把独占一行的 `![](/anim/x.svg)` 换成 `<AnimFigure>`，
  并把 SVG 原文转义后作为属性内联进该页 chunk（不进共享 chunk，避免每页都背 34 张图）。
  段落里塞 `<figure>` 会被 HTML 解析器挪走 → hydration mismatch，所以必须拆出 `<p>`。
- **两种作者写法都成立**：站点侧认 `![图注](/anim/x.svg)`；书籍正文的 `<AnimFigure src="/anim/x.svg" />`
  （`mcu-book/build_html.py:63` 的 `ANIM_TAG` 认它，印前渲染成静态 `<img class="anim">`）
  由 `config.mts` 的 `anim-figure-tag` 在 block 解析后、inline 解析前识别独占源码一行的顶层 `html_inline`，直接复用 `emit(name, caption)` 内联 SVG。
  三页 `build/00-toolchain.md`、`build/06-flash-debug.md`、`c/00-c-in-mcu.md` 用后者——
  **不要为了"统一"把它们改回图片语法**，那样会丢掉书籍侧的 `caption`/静态图语义。

  **边界**：不得在 block 前全局改写 `state.src`；那会污染围栏/注释并吞掉四空格代码缩进。
  `fence`/`code_block`、注释及与正文同行的标签保持原样；caption 不经图片 alt 二次解析。
  `tests/animation-markdown.test.mjs` 用真实 VitePress 配置覆盖代码保真、LF/CRLF、0–3 空格、图注转义与混排。
  主题以 `defineAsyncComponent(() => import('./AnimFigure.vue'))` 注册：无动画的首页不加载控件运行时，含动画页面仍由 SSR 输出图形并加载控件；保留 140KB 首屏预算，不靠放宽门限吸收增长。
- `decorateAnim()` 给每个 `id` 加 `af-<slug>-` 前缀（同页多图时 `url(#arr)` 会串到上一张图的箭头），
  并保留自闭合 `/`（少了它 `<rect/>` 会把后面的兄弟节点吞成子节点）。
- `AnimFigure.vue` 提供播放/暂停、进度条、`prefers-reduced-motion` 默认停在静止帧；
  暂停走 `svg.pauseAnimations()`，所以**页面上暂停不影响独立打开的文件**。
- **视口外自动停。** SMIL 跑在主线程，演示中心 69 张同时跑会把慢机器的帧率打到个位数（实测 12× CPU 节流下 3 fps，
  CI 上连 Playwright 靠 rAF 的等待都会饿死）。组件用 `IntersectionObserver`（200px 预载带）对视口外的图 `pauseAnimations()`，
  回到视口接着走；按钮只反映用户意图，自动停不改按钮文字，只加 `is-offscreen` class（进度条同步停）。
  SMIL 在 document `load` 就开跑、早于水合，所以 `config.mts` 的 `<head>` 还有一段内联脚本在 `DOMContentLoaded` 先按同一口径停一遍。
  同一页改成 55 fps——新增图不再需要担心"演示中心会不会卡"。
- 进度条只动 `transform: scaleX()`：动 `width` 每帧重排，69 条一起动就是 69 次主线程布局。
- 主题变量在 `custom.css` 的 `--mcu-anim-*`（`html.dark` 覆盖），class 规则挂在 `.anim-figure__stage svg` 下。

## 6. 自检

```bash
npm run anim:lint   # scripts/anim-lint.mjs：标签配对、色板漏网、keyTimes 槽位、指示点出界、dur 不整除
npm run docs:gen && npm run docs:build   # 死链门禁必须零错误
```

规范条款能被机器判定的都写进了 `anim-lint`（SMIL 的坑肉眼看不出来：末槽高亮永远不显示、
自造十六进制色在深色模式是白块、连续动画 dur 不整除主 dur 会在回环处跳帧）。
改完图先跑 lint，再在浏览器里确认：深色模式无白块、`svg.children.length` 没被吞、
阶段点与字幕同步、暂停后 `svg.getCurrentTime()` 不再前进。

## 7. 版式审计（出界 / 压字）——`npm run anim:audit`，CI 必跑

`anim-lint` 只看得到 SMIL 与色板，看不到"字被画到画布外"和"两行字叠在一起"。
这两类由 `scripts/anim-audit.mjs` 判定（Playwright 无头 Chromium，CI `checks` 作业在装完浏览器后跑）：
它扫 `docs/public/anim/` 全量内联，从所有 discrete 动画的 `keyTimes` 取每个阶段槽位的中点、
**再按 `--step`（默认 1s）等距加采样点**，`setCurrentTime(t)` 后用祖先链累乘 `opacity`
筛出"这一时刻真的看得见"的文字，再量两种违规：越过 viewBox、以及两行不同文字的墨水盒相交。

```bash
npm run anim:audit                        # 全量，非零退出即有问题
node scripts/anim-audit.mjs dual-os-compare --step 0.5   # 单图、更密采样
node scripts/anim-audit.mjs --font-scale 1.10            # 提交前必跑：模拟 CI 的 Linux 字体（见下）
```

**本地绿 ≠ CI 绿：字体不同。** 图里声明的是 `'Segoe UI','Microsoft YaHei'`，本地 Windows 真有这两套；
CI 的 ubuntu 上都没有，Chromium 退回 DejaVu Sans / Noto Sans CJK。实测同一行字在 CI 上宽
**2%（纯中文）～10%（等宽代码、寄存器名、十六进制）**——首次进 CI 时 69 张里 8 张出界/压字，本地全绿。
`--font-scale` 按倍率放大每个 `<text>` 的宽度（绕 `text-anchor` 锚点，竖向不动），
**`--font-scale 1.10` 本地全绿即可认为 CI 必绿**（1.10 是实测上限；它比 CI 严，所以多出来的报警也要修）。
反过来的经验规则：从 x=56 起笔的 13px 单行说明，本地右端别超过 **656**；等宽代码行更保守，断行优于缩号。

为什么要等距加采样：只取阶段中点时，`dual-os-compare` 的天平托盘标签随 4s 摆动周期
压进下方说明行（±4.5° × 160px 臂长 = 12.6px 下沉）在所有阶段中点都恰好不相交，
手动页跑了两轮都是 OK——加 1s 等距采样才抓到。**连续动画（animateTransform / 非 discrete）
造成的压字只有等距采样能看见。**

判定是文字对文字；**形状压文字**（填充矩形淡入时盖住虚线框、箭头穿过标签）不在覆盖范围内，
改图后仍要用 `scripts/anim-shot.html?fig=<名>&t=<秒>` 或 Playwright 截几帧亲眼看一遍。
`scripts/anim-audit.html` 保留为浏览器里逐条看表格的版本，判定逻辑与 CLI 同源，LIST 需手维护。

两个坑，都踩过：

- **`getBoundingClientRect()` 判压字会大量假阳性。** 它给 `<text>` 的是 em 盒（升部+降部），
  相邻两行baseline 相距 12px 时必然"相碰" 4~10px，而读者看不出任何重叠。
  竖向要改用 canvas `measureText()` 的 `actualBoundingBoxAscent/Descent` 折算墨水范围
  （`baseline = emTop + fontBoundingBoxAscent`，本套图无旋转无缩放，可直接套 em 盒比例）；
  横向 em 盒已经带 `text-anchor`，够用。阈值：横向 >3px **且** 竖向墨水重叠 >1px 才算压字。
- **后台标签页里 `requestAnimationFrame` 是冻结的**，靠 rAF 等布局会永远卡在第一张图。
  改成读一次 `getBoundingClientRect()` 强制刷新布局，`setCurrentTime()` 后立即量。

同一时刻两行 `textContent` 完全相同的文字不算压字——那是阶段字幕在遮罩上重画同一行，刻意的。

`scripts/anim-shot.html?fig=<名>&t=<秒>&z=<倍>` 用来定格复核：只画一张图并停在给定时刻。
截图需要可见的浏览器表面，量不到时用 `evaluate_script` 读坐标即可。
