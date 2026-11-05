# 成片版式合同：页头分节与纵向填充

改 `video/src/layout.mjs`、`video/src/spec.mjs` 的页头/版式，或给某一集写 `sections` 之前读这份。
判据全部来自 2026-10-17 的实测（`.trellis/tasks/archive/2026-10/10-16-video-layout-header-fill/research/baseline-20261017.md`），
不是原则陈述——每条都附了把它量出来的命令。

## 1. Scope / Trigger

- 触发：新增/修改常驻页头元素、改 `.lay-*` 的分布（justify-content / gap / padding-block）、给平台配置加分节信息。
- 不适用：动画本体（`docs/public/anim/*.svg` 与色表见 [docs-site/animation.md](../docs-site/animation.md)）、
  配音与时间轴（`video/src/tts.mjs` / `timeline.mjs`）。

## 2. Signatures

```js
// spec.mjs
export function sceneSections(scenes, sections)   // -> ({i,n,title}|null)[]，1-based；sections 缺省 => 全 null
export const SECTION_TITLE_MAX = 12               // 汉字数上限，loadEpisode 里硬校验
// layout.mjs / stage.mjs
pageHtml({ platform, size, safe, scenes, anims, kicker, badge, sections })
openStage(browser, { platform, size, safe, scenes, kicker, badge, sections })
```

```bash
npm run video:lint                # 当前 episode 集全量契约校验（含 sections 五条判据；2026-10 基线为 18 集）
npm run video:check -- [id…] [--platform p]   # 只跑舞台 + 排版审计，不渲帧、不写 video/out/
node .trellis/tasks/archive/2026-10/10-16-video-layout-header-fill/research/fill-probe.mjs <epId> [platform] [--sections f.json] [--out 前缀]
node .trellis/tasks/archive/2026-10/10-16-video-layout-header-fill/research/fill-sweep.mjs   # 2026-10 基线：18 集 × 双平台逐场填充分布
```

## 3. Contracts

- `ep.platforms[p].sections = [{ at: <该节第一场的 scene id>, title: <≤12 汉字> }]`，**按平台各自声明**
  （竖版 pick 是横版 scenes 的子集，同一份边界表在竖版命不中 id）。一节管到下一节开始为止。
- **兼容线**：没有 `sections` 的集，`.topbar` 的 outerHTML 必须与旧版逐字节相同。
  分叉点在"**要不要生成** `.secchip`/`.secbar`"，不是生成了再用 CSS 藏——
  藏起来仍然会进审计的相叠/越界名单，兼容线就只剩半条。
- **硬约束（继承 `drawTicks` 那条注释）**：页头 DOM 只随场次号 `i` 变，**绝不随帧时间 `t` 变**。
  一集上万帧，场内 DOM 变动会打穿逐帧去重。写入点只有一个：`MCU.setup(i)` 里 `drawTicks(i)` 同一处。
- 按场进度一根且只一根：**横版**底部 `.ticks` + 页头只给文字 chip；**竖版** `.ticks` 保持 `display:none`，
  页头下方 `.secbar` 是唯一进度载体（不放画面底部——抖音客户端的 @作者名/描述/音乐条压在那一段）。
- 集号在页头只出现一次：分节时左格按 `badge` 剥掉 `cover.kicker` 的 `· F5` 尾巴，右格给小节 chip。
- **首个真集实测（S5，2026-10-17）**：横版 6 节 / 竖版 5 节，40 场逐场 `MCU.setup(i)` 后读 DOM，
  `.secchip.textContent` 与 `sceneSections()` 算出的 `第 i/n 节 · title` **一字不差**（0 处不符）。
  横版最后一场读到「第 6/6 节 · Config 与优先级」、`.ticks` `display:flex` 且同屏 1 根进度杠；
  竖版 `.secbar` `display:flex`、`childElementCount` = 5 = 节数、`.cur` 下标跟着节走、`.ticks` `display:none`。
  片头没归进任何一节的场（S5 的 `hook-01/hook-02`）chip 必须是空串且不占宽——这是 `sceneSections()`
  「首节之前返回 null」那条的 DOM 侧对应物，光看 node 侧返回值不算证。

## 4. Validation & Error Matrix

| 输入 | 结果 |
|---|---|
| `sections[].at` 不是该平台真实 scene id | `loadEpisode` 报错（`video:check` 根本跑不起来） |
| 同一个 `at` 出现两次 | 报错「重复」+「不递增」两条（同一处笔误的两个面，不合并） |
| `at` 下标不严格递增 | 报错 |
| `title` 为空 / 超过 12 汉字 | 报错「超过页头宽度上限 12 字」 |
| `sections` 缺省 | 旧页头逐字节复现，审计输出与基线 diff 为空 |
| chip 实际被撑爆（实测 42 字） | 竖版逐场 `越出画布 span.secchip …`；横版 1920 装得下 ⇒ 由 12 字契约兜 |
| 同屏两根看得见的按场进度 | `同屏 2 根按场进度（secbar × ticks）` |
| 任何 `.fit` 字号 < 16px | `字号不可读`（`MIN_FONT` 地板，不许为过审调高它） |

12 字这个数是量出来的，不是拍的：chip 实测最宽 304px（横版 1920 的 15.8%）/ 505px（竖版 1080 的 46.8%），
47 场全部 `scrollWidth − clientWidth = 0`。

## 5. Good / Base / Bad Cases

- Good：`card` 场用「面板长满 + 内容框内居中」（`.lay-card{justify-content:stretch}` +
  `.cardpanel{flex:1 1 auto;justify-content:center}`）——横版 8 场 0.45→0.82，且框本身是可见物体，
  2026-10 测量：18 集 125 场横版 card 全部 82%（几何决定，与内容量无关）。竖版 card 不参与（它本来就有 0.85/0.67，
  套过去会变成"巨框里三行字"）。
- Base：`code`/`hook` 保持 `justify-content:center`，只把 `.lay` 的 gap 从 1.6u/2.4u 抬到横版 4u、竖版 2.4u。
  读数横版 code 0.64 / hook 0.59，是一组居中、间距均匀的内容。
- Bad：`space-between` + `padding-block:5u 9u`。填充读数涨到 0.74（竖版 0.90）"达标"，
  截图却是标题贴页头、代码贴下沿、中间空 250…470px（`research/lever-spacebetween-*.png`）。
  同一改动在竖版把长代码场挤给 `fitAll`：`f2-context-switch/name-map` 19.1→13.3px、
  `p4-iram/hook-01` 22.9→12.7px，三集 8 场撞 16px 地板。

## 6. Tests Required

- 改 CSS 前后各跑一次 `video:check`（**不带 `--platform`**，两平台一次收全）并 `diff`：
  旧集只允许通过行文案因新增判据而变化，逐场读数必须一字不变。
- 每条新判据都要**造一次故意的失败**并留下报错原文，否则它可能是死代码：
  ① 横版也渲染 `.secbar` → 必须报「进度杠重复」；② 页头 chip 塞 42 字 → 必须报「越出画布」。
- 版式改动必须**看截图**，不能只看分数：`fill-probe` 的 `fill` 能被"把内容拆开"刷高（见 §5 Bad）。
- 改完跑 `fill-sweep.mjs` 复核当时 18 集基线分布没有回退（当前集数从 `episodes/*/episode.json` 重算），跑 `md5sum -c research/out-md5-before.txt --quiet`
  证明没碰已发布产物（`video:check` 不写 `video/out/`；`video:build` 会，未发布集才允许跑）。
- **给某一集写了 `sections` 就不止跑审计**：审计只查几何（越界/相叠/进度杠唯一），不查页头**说的是不是真话**；
  而 `validateSections` 只查稿子自洽（`at` 命中该平台 `resolveScenes` 出来的真实 id、不重复、递增、title ≤12 字），
  它查不出「node 侧算对了、DOM 画错了」。所以要逐场把 DOM 与 `sceneSections()` 对账——chip 文案、
  竖版段数 = 节数、`.cur` 下标 = 当前节、`.ticks` 在两平台的可见性、同屏进度杠根数。
  范本 `.temp/s5-header-probe.mjs`（读 `video/out/<id>/…/timeline.json`，只开舞台不写产物）。


## 7. Wrong vs Correct

#### Wrong

```css
/* 用填充比当目标：把内容推到两端，数字涨了画面坏了 */
.lay-code,.lay-hook{justify-content:space-between;padding-block:5u 9u}
```
```js
// 数节点判"有没有两套进度"——竖版 .ticks 常驻 DOM 只是 display:none，12 场全部误报
document.querySelectorAll('.ticks,.secbar').length > 1
```

#### Correct

```css
/* 空隙只加 gap，分布保持居中；填充不够是这一场内容量不够，去写稿层解决 */
.lay-code,.lay-hook{justify-content:center;gap:calc(var(--u)*4)}
```
```js
// 判"看得见的"那几根，两平台同一口径，不加 platform 分支
[...document.querySelectorAll('.ticks,.secbar')]
  .filter((el) => getComputedStyle(el).display !== 'none' && rect(el).width && rect(el).height)
```

**指标纪律**：纵向填充比**既当不了审计闸，也不能当优化目标**。18 集 694 场实测，按 code/hook/card 设全局下限
的后果是 0.50→246 场红、0.70→377 场红（一行 `#define` 的 code 场填 12% 在版式上没错）。
审计只查几何（越界/裁切/压字幕/相叠/顶穿/孤字/字号地板/进度杠唯一），填充留档靠 `fill-probe`。
