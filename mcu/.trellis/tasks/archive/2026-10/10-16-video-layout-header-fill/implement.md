# 执行计划：常驻页头 + 纵向填充

顺序是硬的：先立护栏，再改数据契约，再改渲染，最后才动字号。
每步的验证命令直接可跑；标 ⛔ 的是**不过就不许往下走**的闸。

## 0. 护栏先立（改代码之前）

- [x] 生成既有产物清单：`find video/out -type f | sort | xargs md5sum > research/out-md5-before.txt`
      —— 实际覆盖 **1220 个文件 / 5.3 GB**（比原计划的 `-name '*.mp4' -o -name '发布*.md'` 更严：
      封面 PNG、SRT、`bili-submit.yaml` 一起算）。
- [x] 存一份改前的审计输出：`npm run video:check -- f5-sem-mutex > research/check-before-f5.txt 2>&1`
      —— 不带 `--platform`，两平台一次收全（35 + 12 场）。
- [x] 这条参照可复现，先证明再拿来当闸门：同一命令连跑两遍 `diff` 空。见 `research/baseline-20261017.md` §五。
- [x] 改前基线边界（`research/baseline-f5-sem-mutex.json`）本轮不覆盖。

⛔ 本任务全程禁止对既有 18 个 id 跑 `video:build`（会按新版式重渲已发布的集）。`video:check` 允许，它不写 `video/out/`。

## 1. 数据契约（spec.mjs）

- [x] `sceneSections(scenes, sections)`：返回每场 `{ i, n, title }`（1-based 显示）；`sections` 缺省返回全 `null`；
      首节之前的场次也是 `null`，页头保持旧文案。
- [x] `validateEpisode` 补判据（都算 error）：`at` 命中真实 scene id、下标严格递增、`title` 非空、`at` 不重复，
      外加 `SECTION_TITLE_MAX = 12` 的长度硬校验（1.4 复核已点头）。
- [x] 验证：`npm run video:lint` 全绿（18 个旧集都没有 `sections`，一条错不报）；
      正向/反向用一次性脚本在内存里造 sections（`.temp/sections-selftest.mjs`，不写 `video/episodes/`）：
      缺省⇒全 null、合法⇒零报错、五种写错稿各报一条，6/6 符合预期。
      `at` 重复那一例同时报「重复」与「不递增」两条，是同一处笔误的两个面，不合并——
      合并就要在下标判断里加 `if (!seen)` 的特例，反而更难读。

## 2. 页头渲染（layout.mjs）

- [x] `pageHtml` 收 `sections`，`payload` 每项带 `sec`；新增 `.secchip`（横版只有文字）与 `.secbar`（只竖版）。
      **分叉点在"要不要生成这两个元素"**：没有 `sections` 就不生成，而不是生成了再用 CSS 藏——
      藏起来仍然会进审计的相叠/越界名单，兼容线也就只剩半条。
- [x] `MCU.setup(i)` 内在 `drawTicks(i)` 同一处更新页头（`drawHeader(item.sec)`），**只随 i 变**；
      `setup` 的 `if (i === current) return` 天然保证同一场内页头 DOM 一个字不变。
- [x] 左格去掉 `cover.kicker` 的 `· F5` 尾巴（按 `badge` 匹配剥，不写死集号）——`sections` 缺省时走旧字符串。
- [x] 验证（两层，都不靠目测）：
      ① `npm run video:check -- f5-sem-mutex` 与 `research/check-before-f5.txt` **逐字节相同**（diff 空）。
      ② DOM 层面：老集 `.topbar` outerHTML 仍是 `<div class="topbar"><span class="badge">F5</span><span class="brand2">通往单片机之路 · F5</span></div>`，
      `#secchip`/`#secbar` 都是 `null`；注入夹具后横版 chip 随场次推进到「第 6/6 节」，
      竖版 `secbar` 段数 = n 且 `cur` 跟着节号走，`.ticks` 仍 `display:none`。
- [x] 与设计的一处出入照记：`stage.mjs` 的 `openStage` 多了 `sections` 一个透传参数。
      design §1 说它不动，但不改签名就送不进 `pageHtml`；用模块级全局注入（照 `setAnimSourceReader` 那套）
      会把上一集的分节漏给下一集——`video:build` 是遍历多集的。seek/渲帧语义没动，标定仍不需要重跑。

## 3. 测量夹具（不动仓库里的已发布稿）

- [x] `research/fill-probe.mjs` 加 `--sections <file>` 与 `--out <前缀>`。
      `--out` 不在原计划里，但没有它就危险：默认前缀是 `baseline`，改完 CSS 再跑一次会把
      「改之前长什么样」的唯一凭据（`baseline-f5-sem-mutex.json` + 五张 png）就地覆盖。改后读数一律 `--out after`。
- [x] 夹具 `research/f5-sections.json`：横版 6 节、竖版 5 节，按现有 narration 的语义段落划。
      **形状是按平台分组的** `{bilibili:[…], douyin:[…]}`——竖版 `pick` 是横版 35 场里的 12 场子集，
      同一份边界表在竖版命不中 scene id，整集页头会全空。
      这只是测量夹具，不构成「F5 该补 sections」：F5 已发布，不回炉。
- [x] 12 字上限由实测背书，不是拍的：chip 实测最宽 横版 304px / 竖版 505px，
      `scrollWidth − clientWidth = 0`，35 + 12 场无一溢出。
- [x] 一条判据差点是假的，已纠：「同屏不许两根按场进度」最初按 `querySelectorAll('.ticks, .secbar').length` 判，
      竖版 12 场**全**误报——`.ticks` 一直在 DOM 里，只是 `display:none`。
      改成只数看得见的（computed display ≠ none）后竖版回到 1 根。
      **步骤 7 写进 `cli.mjs` 的那条断言必须用可见性口径**，否则审计会红一整集。

## 4. 纵向填充 · 杠杆 (a)：分布空隙

- [x] `lay-code` / `lay-hook` 横版：先按 design 试 `space-between` + `padding-block:5u 9u`，
      实测填充 0.74 达标——**但截图否掉了它**：标题贴页头、代码贴下沿、中间空 250px
      （`research/lever-spacebetween-bilibili-code.png`）。填充比是靠把内容拆开刷上去的。
- [x] 落地的走法换成**保持 `justify-content:center`、只把 `.lay` 的 gap 从 1.6u/2.4u 加到 4u**。
      实测横版 code 0.64（最差场 0.38）、hook 0.59（最差 0.51）——比 `space-between` 低，
      但那是一组居中、间距均匀的内容（`research/after-bilibili-code.png`）。
- [x] 验证：`npm run video:check -- f5-sem-mutex` 与 18 集全量（694 场）全 0；
      逐场读数与改前**只差通过行那一项文案**（见步骤 7）。

## 5. 纵向填充 · 杠杆 (b)：卡片内部尺度

- [x] 字号/padding 三档连加（4.2u→6.5u、gap→3.4u、`.bullets` 2.35u/1.5u）实测只到 **0.66（最差 0.56）**，
      同时把竖版 card 顶到 0.95——三档全部退回。design §4 的这条走法被否。
- [x] 换成**面板长满、内容框内居中**：`.lay-card{justify-content:stretch}` + `.cardpanel{flex:1 1 auto;justify-content:center}`。
      横版 card 8 场 **0.82**（改前 0.55/0.45），18 集 125 场横版 card 全部 82%（几何钉死，与内容量无关）。
- [x] ⛔ 全程零 `tooSmall`：`MIN_FONT` 没动、没加特例；`anim`（92%）与 `outro`（23%）一个字没改。
- [x] `.cols{flex:0 1 auto}` 那条护栏原样保留（design §4「明确不动的」）。

## 6. 竖版

- [x] `.frame` 的 10u/22u/8u 与 `.caps` 16u **一律没动**。
- [x] 竖版 `padding-block:3u 6u` 试过，**已退回**：它把长代码场的字压穿地板——
      `f2-context-switch/name-map` 19.1→13.3px、`p4-iram/hook-01` 22.9→12.7px、`s16-hardfault` 四场 14.7px，
      `video:check` 三集红（同一命令改前 exit 0）。竖版改成只加 gap 2.4u：code 0.54、hook 0.75，三集回到全绿。
- [x] 页头 `.secbar` 放在 topbar 下方一条（不放底部：抖音客户端的 @作者名/描述/音乐条压在那一段）。
- [x] 竖版 `card` 不参与"面板长满"：实测它本来就有 0.85/0.67，套横版那条会变成"框里三行字"，
      在 douyin 块里显式退回旧的 `justify-content:center` + `flex:0 1 auto`。
- [x] 验证：`video:check` 竖版 18 集全 0 + fill-probe 出竖版三 kind 边界表；
      `.ticks` 在竖版仍 `display:none`，页头杠是唯一进度（47 场实测每场只有一根看得见的）。

## 7. 审计扩容（cli.mjs）

- [x] `:226` 压字幕选择器与 `:239` 相叠 marks 各加 `.secchip`、`.secbar`。
- [x] 新增断言：同屏只许一根**看得见的**按场进度（`display !== 'none'` 且宽高非 0），
      两平台同一口径。故意反例（横版也渲染 `.secbar`）→ 逐场报
      `同屏 2 根按场进度（secbar × ticks）`；正常态 694 场 0 命中。
- [x] 故意失败测试：42 字标题塞进 `.secchip` → 竖版 12 场全部 `越出画布 span.secchip 155,228,1490,272`
      （横版 1920 装得下，不报）。另一层：`video:check` 根本进不去——`loadEpisode` 里的
      `SECTION_TITLE_MAX=12` 先拦（`bilibili.sections[3]: title 42 字，超过页头宽度上限 12 字`）。
      原计划写的"审计抓到"实际是**两层各抓一半**，竖版靠几何、横版靠契约。
- [x] **没有加**纵向填充判据：18 集实测（§七）任何 ≤0.70 的全局阈值都判红 246–377 个已发布场次，
      而 `space-between` 证明这个数能靠挖洞刷上去。它当不了闸。

## 8. 收尾核对

- [x] `npm run video:lint` 全绿（18 条，无一条 `sections` 报错）；`video:check` f5 两平台全绿。
- [x] `npm run video:check`（无参数，18 条 × 双平台 694 场）exit 0。
- [x] md5 比对：`md5sum -c research/out-md5-before.txt --quiet` → exit 0，`video/out/` 一字节未动。
- [x] `research/` 更新：`after-*` / `after-sec-*`（双平台逐 kind 截图 + 两份 json）与 `baseline-*` 成对；
      被否的走法留 `lever-spacebetween-*.png` 两张反例；全量扫描器 `fill-sweep.mjs` 一起留档。
- [x] PRD 的 AC 按实测分档改写（card 达标、code/hook 的 0.70 换成"不许用拆开内容换填充"、
      `anim`/`outro` 豁免、两平台分开、页头那条补实测数），走 Phase 1 修订口径而不是就地放宽。

## 回滚点

- 每步都是独立可 revert 的改动；最稳的两个回滚位是「只加契约、没动 CSS」（步骤 2 之后）
  与「分布完成、字号未动」（步骤 4 之后）。
- 步骤 5（字号放大）是唯一会引入裁切/字号地板失败的地方，出问题就单独退回它，
  不要连步骤 4 一起退。
- 全部改动集中在 `video/src/{spec,layout,cli}.mjs`，一个 commit 可整体 `git revert`；
  `sections` 是纯增量字段，旧稿不含它就走旧渲染，不存在数据迁回。

## 出口条件

版式改造落地后，`10-17-s5-systick-episode` 才允许进 Phase 2 渲帧——S5 是第一个带 `sections` 的集，
也是这次新页头的第一个观众。顺序反过来第 18 集就白做一版。
