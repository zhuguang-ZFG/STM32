# 设计：常驻页头 + 纵向填充

前提读数全部来自 `research/baseline-20261017.md`，不是按 PRD 的行号推的。
三处与 PRD 诊断不同，本设计按实测走：padding 不是填充问题、竖版没那条「中间一条」、
`.ticks` 分段进度已经存在。

## 1. 边界

改动只碰三个文件：`video/src/spec.mjs`（数据契约与校验）、`video/src/layout.mjs`（CSS + payload + MCU）、
`video/src/cli.mjs`（排版审计的元素清单）。
`stage.mjs` / `render.mjs` / `timeline.mjs` / `mux.mjs` / `package.mjs` 不动——它们只按场次号取帧，
版式改完仍然「同一场内 DOM 一字不变」，逐帧去重与 seek 标定都不受影响
（`calib.mjs` 量的是 seek 门限，与字号无关，**不需要重跑标定**）。

## 2. 数据契约：新增 `sections`，不复用 `kicker`

实测否掉了 PRD 里「把 `scenes[].kicker` 带到页头」这条路（覆盖率 6%，语义是卡片小标题，
且已被审计选择器占用）。改成在平台配置里声明分节边界：

```jsonc
"platforms": {
  "bilibili": {
    "size": [1920, 1080], "targetSec": [480, 720],
    "sections": [
      { "at": "hook-01", "title": "开场" },
      { "at": "code-01", "title": "寄存器版图" }
    ],
    "scenes": [ … ]
  }
}
```

- `at` 是该节**第一场**的 scene id；一节管到下一节开始为止。
- `spec.mjs` 新增纯函数 `sceneSections(scenes, sections)` → 每场一个 `{ i, n, title }`（1-based 显示）。
- `validateEpisode` 补四条判据（都算 error，不算 warning）：`at` 必须命中该平台真实存在的 scene id；
  各 `at` 在 scenes 里的下标必须严格递增；`title` 非空；`sections` 里不许出现同一个 `at` 两次。
  id 不存在或顺序乱是**写错稿**，静默退回旧页头会把错误一路带到成片里。
- **兼容线**：`sections` 缺省 → 页头文本必须与今天逐字相同（旧 episode.json 都没有这个字段，
  误跑 `video:check` 时旧集的审计结果要能一字不差地复现，这是回归口径）。

## 3. 页头渲染

`.topbar` 是页面级静态 DOM（`layout.mjs:186`、`:317`），今天印的是 `F5` + `通往单片机之路 · F5`
——集号重复了两遍。改成左右两格各司其职：

- 左：`badge` + 系列名（去掉 `cover.kicker` 里那个 `· F5` 尾巴，集号只留一份）；
- 右：新增 `.secchip`，内容 = 「第 i/n 节 · title」。

分段进度**不再造第二套按场的条**：`.ticks` 已经在按场分（横版实测可见），页头再放一根按场的就是同屏两根。
分工按平台定死，并写进 AC：

- 横版：底部 `.ticks` 继续当按场进度，页头**只给文字**「第 i/n 节 · title」，不放杠；
- 竖版：`.ticks` 本就 `display:none`（`:291`，注释理由是右下角 `03 / 09` 已说清同一件事），
  所以页头那根 `.secbar` 是竖版唯一的按节进度载体，位置放在 topbar 下方一条，
  不放到画面底部——抖音客户端的 @作者名/描述/音乐条压在下面那一段。

DOM 写入点只有一个：`MCU.setup(i)`（`:391`）里跟着 `drawTicks(i)` 同一处更新。
硬约束继承 `:409` 那条注释：**只随场次号变，绝不随帧时间 t 变**，否则上万帧的逐帧去重被打穿。

## 4. 纵向填充：分两条杠杆，按 kind 分派

实测内容中心 y=488 与内带（97…879）中心 488 完全重合，说明「中间一条」是**居中放置 + 自然高度**的结果，
不是 padding 挤的。所以有两条杠杆，各自的风险完全不同：

**(a) 分布空隙**（多子元素场次）：`.lay-code` / `.lay-hook` 从 `justify-content:center` 改成
`space-between` + 显式的上下留白带（`padding-block`），让内容上下界**被定义成目标区间**，
而不是指望字号刚好长到那儿。横版目标带取 y≈150…780（PRD 的口径），换算成
`.body` 内带 97…879 之上的 padding：上 ≈5u、下 ≈9u（实现时以实测边界定值，不拍数）。
这条杠杆**不改变任何元素的自然尺寸**，只分配空隙 → 不可能新增 fitAll 收缩、不可能引入裁切，
这是它优先于 (b) 的理由。

> **Phase 2 实测回写（2026-10-17，`research/lever-spacebetween-*.png`）**：上面这句是错的，两条都错了。
> `space-between` 把多子元素场次**拆到带的两端**——横版 code 实测 0.74、竖版 0.90，数字全达标，
> 截图却是标题贴页头、代码贴下沿、中间一条空洞（`lever-spacebetween-bilibili-code.png` 那帧最清楚：
> 标题与 `semphr.h 原文行号` 之间空了 250px）。**填充比是被"挖洞"刷上去的，不是被内容填满的。**
> 另一半也不成立：padding 确实会引入新的失败——竖版 `padding-block:3u 6u` 把
> `f2-context-switch/name-map` 从 19.1px 压到 13.3px、`p4-iram/hook-01` 从 22.9px 压到 12.7px，
> 三集 8 场全部撞 `MIN_FONT` 地板（`video:check` 实测红，改前同一命令全绿）。
> 落地的走法换成**只加大 `.lay` 的 gap、保持居中**：横版 code 1.6u→4u、hook 2.4u→4u，
> 竖版 code 1.6u→2.4u。读数横版 code 0.64（最差场 0.38）、hook 0.59、竖版 code 0.54、hook 0.75，
> 都比 space-between 低，但截图是一组居中、间距均匀的内容（`after-bilibili-code.png`），
> 18 集 × 双平台 694 场审计全绿。
> **结论写死**：code/hook 的填充由**每场内容量**决定，CSS 分布杠杆只能决定"洞摆在哪"。
> 要真填进去，得在写稿时把一场拆成两场或补足行——那是 spec 层的事，本任务不假装 CSS 能解决。

**(b) 放大内部尺度**（单子元素场次）：`lay-card` 只有一个 `.cardpanel`，`space-between` 对单子元素
等于把它顶到带上沿，视觉更坏。卡片只能靠长面板自己：`.cardpanel` 的 padding 与 `.bullets`/`.title` 字号
按 `150…780` 目标实测反推（当前 card 内容 470px，要到 630px 是 ×1.34 量级）。
这条杠杆有真实风险：字号上去后横向放不下时 `fitAll` 会把它压回来，
压到 `MIN_FONT`（`cli.mjs` 的 16px 地板）就会被审计判失败——
所以 (b) 必须和审计一起跑，改一档量一次，不许连改几档再看。

> **Phase 2 实测回写（2026-10-17，`research/after-f5-sem-mutex.json`）**：上面这条 (b) 的走法被否了。
> 面板 padding 4.2u→6.5u、内部 gap 2.2u→3.4u、`.bullets` 字号 2.15u/1.35u 三档连加，横版 card 只到
> **0.66（最差场 0.56）**，同一套把竖版 card 从 0.85 顶到 0.95——把字吹大并不等于把空白变成排版。
> 落地的走法换成**让面板本身长满、内容在框内居中**：`.lay-card{justify-content:stretch}`
> + `.cardpanel{flex:1 1 auto;justify-content:center}`（`.cardpanel` 是有底色/描边/投影的**可见盒子**，
> 拉伸它回答的是「中间一条横幅」这件事，而不是把字放大去凑面积）。
> 实测横版 card 8 场全部 0.82（改前 0.55/0.45）；竖版 card 实测本来就 0.85/0.67、不缺填充，
> 所以在 douyin 块里退回旧的居中摆法（`justify-content:center` + `flex:0 1 auto`）——
> 给它套横版那条会把短卡变成框里只有三行字的巨框。`.cols{flex:0 1 auto}` 那条护栏原样没动。

**明确不动的**：
- `.cols{flex:0 1 auto}`（`:210`）保留。`:208` 那段注释立着护栏：改成 `flex:1` 就是
  「8 行代码配 800px 的框，下半屏全是空的」——用拉伸换填充是把问题换成另一种难看。
- `lay-anim` 实测 92%，不碰（动画有固定 viewBox，硬撑会走样）。
- `lay-outro` 实测 23%（标题 + 一枚 URL 药丸），不参与填充指标。
- **竖版 padding 一律不动**（`:288` 的 10u/22u/8u + `.caps` 16u）。
  `safe` 字段虽然传进了 CSS 层，但 `PLATFORM_DEFAULTS.douyin.safe.bottom=300` 与今天正文下界
  22u≈422px 不是一回事：那个 22u 是把文字停在抖音描述区之上的，换成 safe 值会把内容推进客户端文字里。
  所以 `safe` 的「单一来源」这件事本次**不做**，只在竖版对 `lay-code`（实测 52%）加 (a) 杠杆。

## 5. 审计口径要跟着扩

`cli.mjs` 两处元素清单必须带上新的页头元素，否则页头溢出/相叠一个都不查：
- `:226` 压字幕带选择器：加 `.secchip`、`.secbar`；
- `:239` 兄弟相叠 marks：同上（topbar 在 `.lay` 外，与 `.title` 是否相叠正是这次要防的）。

新增一条判据：**横版不许出现两根按场进度**（`.ticks` 与页头按场杠互斥），用 DOM 计数断言，不靠目测。

> **Phase 2 实测回写**：判据落地成两条口径修正。
> ① 数的是**看得见的**杠（`getComputedStyle().display !== 'none'` 且宽高非 0），不是节点数：
>    竖版 `.ticks` 一直挂在 DOM 里只是 `display:none`，按节点数判 12 场全部误报。
> ② 判据对两平台一视同仁（写成「同屏只许一根」），不加 `platform` 分支——
>    误报来自口径，不来自平台，加分支就是把判据改成跟着实现走。
>    故意造的反例（横版也渲染 `.secbar`）确实报出 `同屏 2 根按场进度（secbar × ticks）`。
>
> **没有加的那条**：纵向填充下限。18 集 × 双平台 694 场实测（`research/baseline-20261017.md` §七）
> 说明它当不了闸：短内容场 legitimately 填得少——横版 code 最低 12%（`c4-struct-abi/gpiof-macro` 只有一行宏）、
> 竖版 card 最低 31%、横版 hook 最低 24%。任何 ≤0.70 的全局阈值都会把 **246–377 个已发布场次**判成失败，
> 而把阈值定到能放行它们的那个数字，这条判据就抓不到任何东西了。
> 更糟的是这个数**能刷**：`space-between` 把内容拆到带的两端，读数立刻 0.55→0.74，画面却多了一条空洞
> （`research/lever-spacebetween-bilibili-code.png`）。能被挖洞刷上去的指标不配当闸。
> 填充的证据因此留在 `fill-probe`/`fill-sweep`（`after-*.json`），不写进审计。

## 6. 只对未发布新集生效

版式是 CSS，不看 episode 身份——旧集一旦被重新渲染就会换成新版式，这是本次唯一的真实危险。
三层拦法（第 1 层是纪律，2、3 层是可跑的检查）：

1. 本任务**禁止对既有 18 个 id 跑 `video:build`**；`video:check` 允许（它不写 `video/out/`）。
2. 开工前生成 `video/out` 的 md5 清单存进 research，收工重算比对，逐字节相同才算过。
3. 改造只在 S5（第一个带 `sections` 的新集）上量边界、出截图留档；S5 尚未渲帧，不存在回炉问题。

回滚点：改动集中在三个文件的一个 commit，`git revert` 即可；
`sections` 字段是纯增量（旧稿没有该字段 → 页头走旧路径），不存在需要迁回的数据。

## 7. 待定项（1.4 复核时要用户点头的两件事）

1. 横版页头是否去掉 `· F5` 那个重复集号（观众侧视觉变化，虽然与「旧集不回炉」不冲突，
   但它改的是 17 集以来的品牌位文本口径）。
2. `sections[].title` 的长度上限。页头字号 1.7u≈18.4px，竖版可用宽度约 860px，
   先按 12 个汉字设硬校验，实现时以实测宽度为准调数——不是先拍了再说。
