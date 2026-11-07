# Journal - zhuguang-ZFG (Part 1)

> AI development session journal
> Started: 2026-10-06

---

## 2026-10-06 站点奠基（任务 10-06-01 + 00）

**决策**：VitePress 站点；STM32 寄存器主线（霸天虎 F407ZGT6）；ESP-IDF v5.5（立创实战派 S3）；FreeRTOS+RT-Thread 双精讲；四件套+风格契约+动画实物。

**产出**：84 个 md 页面（七板块+金样例）；双路线第 0 章成稿；code/stm32/00-blink 四文件全套；code/esp32/00-hello；动画×3（SVG+SMIL）；实验模板+E01+接线 SVG；README/CONTRIBUTING；.trellis/spec 按真实结构重写。

**验证**：docs:build 零错误（ignoreDeadLinks=false，含 FPU 修复后复验）；占位 grep 干净；浏览器实测首页+C6+动画加载；寄存器事实经 ST 官方 CMSIS 头文件核对全对；task_verify=unverified（无配置检查）。

**审查修复**：启动文件漏使能 FPU（CPACR）——硬浮点编译下第一条 FPU 指令即 UsageFault(NOCP)，已补并使 B4/spec/README 三处同步为"启动四工序"。评审另一项"栈帧顺序"质疑经核对为误报（xPSR 居最高地址、sp 指向 R0，SVG 画法正确）。

**教训**：①子代理 15 分钟硬时限，25 页/人+读大文档=全部超杀零产出——切片≤5 页且上下文内联；②rtos 子目录跨板块链接需 `../../`；③模板示例图片路径须放代码块防 Vite import 解析；④连续 hashline 编辑必须先回读再落刀（本轮三次行号猜测失误）。



## Session 1: 项目质量修复：本地验收完成

**Date**: 2026-10-06
**Task**: 项目质量修复：本地验收完成
**Branch**: `main`

### Summary

完成场景构建隔离、三个实验工程、S3 目标保护、工程清单与严格元数据、实验状态、CI 门禁、高亮与搜索优化。25 单元 + 3 浏览器测试通过，19 工程构建/取证通过。保留原 B3 工作；集成提交、远端 CI、上板实测待执行，见当前任务 research/validation.md。

### Main Changes

- 新增 E05/E07/E08 工程；修复 GD32 Thumb 复位向量、GPIO 占用脚输出与 FreeRTOS 场景产物复用。
- CI 复用完整质量检查，实验状态与源码/实测证据分开；详见任务验收记录。

### Git Commits

未提交：这是实施与本地验收会话；保留 B3 并行工作，等待集成。

### Testing

- npm run quality、firmware:check、test:browser 通过；性能测量完成。远端 CI 与硬件实测未执行。

### Status

本地实现和验收完成，任务仍为 **in_progress**，未将集成/硬件验收标为完成。

### Next Steps

- 集成 B3 原工作及本任务改动，运行远端 CI；有目标板与仪器后补充实测。


## Session 2: 提交质量修复并通过远端 CI

**Date**: 2026-10-07
**Task**: 提交质量修复并通过远端 CI
**Branch**: `main`

### Summary

已提交推送 main；远端文档、浏览器、ARM/host、六项 ESP32-S3 构建及 Pages 全部成功。完成当前任务归档，硬件实测仍独立待执行。

### Main Changes

- B3 原有章节与链接器取证作为独立提交 50d6e5e 集成，质量修复提交 286d692；已推送 main。
- GitHub Actions run 37492733587 的 9 个 jobs 全部成功，包括 ARM/host、文档与浏览器回归、六个 ESP32-S3 工程和 Pages 部署。
- 任务已归档至 .trellis/tasks/archive/2026-10/10-06-project-quality-reproducibility，保存远端状态 JSON 与验收记录。
- 硬件仍待实际测量，不以 CI 代替上板证据；旧开发依赖告警按原方案记录为后续事项。


### Git Commits

| Hash | Message |
|------|---------|
| `50d6e5e` | (see git log) |
| `286d692` | (see git log) |

### Testing

- GitHub Actions run 37492733587 全部 9 个 jobs 为 success（25 单元测试、3 浏览器回归、全工程构建/取证、Pages）；记录在归档任务 research/ci-first-success.json。

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 3: 抖音投放收口：s2-rcc 封面去母题过审、导流评论落库

**Date**: 2026-10-16
**Task**: 抖音投放收口：s2-rcc 封面去母题过审、导流评论落库
**Branch**: `main`

### Summary

第 9 集 s2-rcc 完成抖音投稿，16 集在抖音全部投齐（作品 41→42，平台侧回读 2026年10月16日 11:44 已发布）。抖音判「请勿使用截屏当封面」的单一变量是横封面上的 wave 母题，去母题后预发布快速检测转「封面效果检测通过」，改法落进 platforms.douyin.cover 并重生成做像素核对。导流评论已发并逐字回读（cid=7697135842757772041，128 字与发布文案一致），置顶经实测仍需 App 长按。投放驱动的固定等待被 6.8~10.2 秒的上行全部打穿，改为复用标签页加轮询。

### Main Changes

- **封面判定的单一变量找到了**：抖音那句「请勿使用截屏当封面」和 s2 横封面上的 `wave` 母题有关——f3/s4 的横封面没有母题就过。去掉母题后，预发布快速检测当场翻成「封面效果检测通过」。修法走 `platforms.douyin.cover` 整块替换（`package.mjs:278` 的既有口径），B站/知乎仍读 base `cover`，所以两边封面不受影响；改完重生成并做像素核对，与平台实测过的图一致（横 0%、竖 0.831% 仅抗锯齿，对照 29.166%）。
- **`aweme_id` 取不到不是脚本的错**：内容管理页的 DOM 里压根不放 id（已发布也一样，`dy-id-one.mjs` 因此空手）。要抓它自己的列表接口 `creator/janus/douyin/creator/pc/work_list`，按标题定位取号，并用 `duration` 对一遍（65640 ↔ 65.600s）。
- **评论「没发出去」是链路假象**：回车提交是有效的，但这条上行上请求过了约 2.5 分钟才落库。中间窗口里同时能看到「编辑框还有字」和「暂无评论」，按 DOM 判失败就会重发成两条。最终平台侧只有一条：`cid=7697135842757772041`，128 字与 `发布-douyin.md`「## ②」逐字一致，作者带 作者 标。
- **置顶仍然只有 App 能做**：2026-10-16 实测，自己那条评论的 `⋯` 菜单里只有「删除评论」，没有置顶项。web 端做不到不是脚本没写对。
- **慢链路打穿了所有固定等待**：daemon 的 30 秒 `goto` 直接把常驻浏览器带崩（进程一退窗口就关，登录态白搭）；评论脚本固定等 12 秒必然赶不上评论区水合。统一改成「复用已开着的标签页 + 轮询到元素真出现」，导航预算放到 240 秒。
- 顺带把 `.temp` 投放驱动补了几道硬保护：发前清空编辑框并确认清空、这条文案已在列表里就停（防重发刷屏）、提交只认评论行内最右侧图标且排除 danmaku 容器。其中**图标提交那条路径未经实战**——重复保护在它真发之前就停了。


### Git Commits

| Hash | Message |
|------|---------|
| `395accc` | (see git log) |
| `327d136` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 4: F5 片单补录 + 三平台投放（抖音/B站成，知乎撞频控）

**Date**: 2026-10-16
**Task**: F5 片单补录 + 三平台投放（抖音/B站成，知乎撞频控）
**Branch**: `main`

### Summary

F5《信号量和互斥量》收进片单（no:17、next 清空），断行修复与 B站简介压字（2177→1982，publish.bilibili.intro 1310→1115）都已提交推送。投放：抖音在线（aweme_id 7697231677763931428，66977ms 与成片一致，导流评论 cid=7697253575721992960 逐字校验，置顶仍需 App 手动）；B站 BV1JsJt6bEFH（9 项回读全过）。知乎三次被拒，响应体 code=10000「近期发布频率过高，请24小时后重试~」——账号 10-15 15:43 批量 8 条 + 当晚并发投 STM32 系列，是账号级滚动频控，草稿完整无需重传，窗口过后 node .temp/f5-zh-publish.mjs 续传。平台实测事实落 .temp/zhihu-plan.md：成功只认「发布成功」弹窗、失败只认 /api/v4/content/publish 响应体、内容管理列表返回的是 pin 不能当回读、CDP 里 browser.close() 会杀常驻浏览器。顺手补了两处会复发的坑：f5-zh-publish.mjs 原先成功也不写 published.txt 留痕（下轮会误判成没投）且不删闸门，现在留痕+删闸门+有留痕即拒跑。遗留观察：抖音合集把 F5 排成第16集，与片单 no:17 不同源——合集序号由平台按入集合顺序自己排，B站分P才用我们的编号。

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

| Hash | Message |
|------|---------|
| `49b9250` | (see git log) |
| `f9d00a2` | (see git log) |
| `8c14cfd` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 5: F5 投放收尾 + 与 STM32 项目逐帧对比，开出两条后续任务

**Date**: 2026-10-16
**Task**: F5 投放收尾 + 与 STM32 项目逐帧对比，开出两条后续任务
**Branch**: `main`

### Summary

抖音腿补齐：导流评论 cid=7697253575721992960 逐字校验通过并写进 .temp/douyin-submitted.txt（置顶仍须 App 长按）。知乎三次被拒后确认是账号级滚动频控（code=10000），草稿完整无需重传；顺手把 f5-zh-publish.mjs 补成「成功才落 published.txt 留痕 + 用掉即删闸门 + 有留痕就拒跑」，这三处缺的语义正是今晚「弹窗没抓到却无从证伪」的同一种瞎。知乎这条线跑了 16 条一直没有 runbook，补 .temp/zhihu-plan.md（与 douyin-plan/wx-plan/yt-plan 同规格）：成功只认「发布成功」弹窗、失败只认 /api/v4/content/publish 响应体、creations/v2/zvideo 返回的是 pin 不能当回读、续传前必须逐字比对草稿标题前 60 字（今天横幅上挂的是别的会话的稿）、CDP 里 browser.close() 会杀常驻 9223 浏览器。与 D:/Users/STM32/final-videos 逐帧对比（同物种：1080p30/配音+SRT/11–14 分钟）：差距两处——常驻页头不答「第几章哪一节」、内容块纵向只用了 y≈300–700 中间一条；不抄的两处也记了数（他们单条 1 GB/10 Mbps vs 我们 539 kbps；选择题卡片+吉祥物会稀释「屏上每个数都能 probe.sh 复现」这条卖点）。据此开两条 Trellis 任务：10-16-e04-board-measurement（填 docs/lab/e04-priority-inversion.md:101 那张至今全空的四行表，硬约束=模型值 6000/2500 永不作为实测填入）、10-16-video-layout-header-fill（版式两处改造，只对未发布新集生效，依赖下一集立项，因 series.json 的 next/backlog 现在都是空）。

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

| Hash | Message |
|------|---------|
| `797a228` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 6: B站 17 条简介脱 markdown 残留 + 合集门槛取证

**Date**: 2026-10-16
**Task**: B站 17 条简介脱 markdown 残留 + 合集门槛取证
**Branch**: `main`

### Summary

实测 B站简介区按纯文本渲染（pre/code 数 0），17 条线上稿件的 ``` 围栏/行内反引号/** 全部原样露出；逐字核验只删标记后全量回传，公开页复读 17/17 干净，生成端加 plain() 断源。合集建集被 code=20082 挡，真因是 season=false（权益中心 Lv2 门槛），判据与就绪三步记进新任务 PRD。

### Main Changes

**做了什么**

用户指令两条：先建 B站合集挂 17 条，再补简介去反引号。第二条做完，第一条撞平台门槛，证据已入账（`.trellis/tasks/10-16-bili-season-after-unlock/`，commit `0cc07d6`）。

**关键发现**

1. B站简介区是 `white-space: pre-line` 的纯文本——实测视频页 `pre`/`code` 元素数为 0，`span.desc-info-text` 里 ``` 围栏、`行内代码`、`**粗体**` 全部原样露给观众。发布稿本身是 markdown，围栏是给 md 用的，问题只在跨到平台这一发没脱标记。
2. 合集那条 `code=20082 您创建的合集个数太多了` 是伪装文案：`seasons` 返回 `total=0`，账号一条都没有。真门槛在投稿页那行「开通合集功能需满足权益中心等级达 Lv2」，`white` 接口 `season=false`/`new_season=false` 读死，两个合集管理路由都打回 `/platform/home`。
3. `x/member/web/exp` 的 `current_level`（本账号 Lv4）是用户经验等级，不是权益中心等级，`.temp/bili-level.mjs` 里那句「能否建合集=level>=2」推断是错的，已在 PRD 写明别再拿它当判据。

**改了哪些**

- `.temp/bili-desc-fix.mjs`（新）：dry 逐条算脱标记差异并留改前原文 `.temp/desc-live/`，post 一发一条走全量回传，发完立刻复读核对。`vupre` 连打会 `-702` 限频，加了 1.5s 间隔 + 退避重打。
- `.temp/bili-cover-edit.mjs`：`k=v` 的 v 支持 `@文件` 写法——简介上千字带换行，走命令行必然被 shell 掰断。
- `.temp/bili-submit.mjs`：desc 组装加 `plain()`，新集投稿前就脱标记，2000 字上限按脱完的长度拦。
- `.temp/bili-season-page.mjs`、`.temp/bili-upower.mjs`、`.temp/bili-right-center.mjs`（新，只读探针，只 `page.close()`）。

**验证**

- 脱标记前后逐字核验：去掉 ` * 空白` 后 17/17 与原文完全一致、顺序不变，只删了 2 行围栏 + 成对反引号 + 成对星号（F5 另有 9 对行内反引号、2 对粗体）。
- 17 条 `edit` 全 `code=0`，复读编辑框与公开 `view` 接口：简介长度逐条等于目标、残留归零、`state=0`。作者侧 `state=-6` 只是改动复核标记，公开页不受影响。
- 观众侧页面复扫：`命中反引号节点数 0`。
- 生成端 `--dry` 的 17 条简介长度与线上逐条相等，两条通道口径一致。

**待办**

- 知乎 F5 仍被账号级 24h 频控挡着，草稿完整，闸门文件 `.temp/zh-run/I_HAVE_USER_OK=f5-sem-mutex` 留在原地，窗口过了跑 `node .temp/f5-zh-publish.mjs`。
- 抖音 F5 那条评论需用户在 App 里长按置顶（web 端无置顶入口，`stick_position=0` 已留痕）。


### Git Commits

| Hash | Message |
|------|---------|
| `0cc07d6` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 7: 视频版式改版落地：页头小节 chip + 纵向分布，填充率判据被实测否掉

**Date**: 2026-10-17
**Task**: 视频版式改版落地：页头小节 chip + 纵向分布，填充率判据被实测否掉
**Branch**: `main`

### Summary

常驻页头补 sections 契约与「第 i/n 节 · title」chip（竖版另给一根 .secbar），code/hook 改成只加 gap、横版 card 让面板长满；694 场逐场实测证明纵向填充比既当不了审计闸也不能当优化目标——space-between 把读数刷到 0.74/0.90 却留 250–470px 空洞被截图否掉，竖版 padding 把 8 场压穿 16px 地板是真回退已退回。审计扩到第八项「同屏两根按场进度」，18 集 × 双平台 exit 0、无 sections 的旧集页头逐字节不变、video/out/ md5 未动。S5 第 18 集出口条件解除。

### Main Changes

**做了什么**

会话前半先把第 18 集选题定档 S5 SysTick、backlog 补四条候选（`1fa7d1d`）、给 S5 立项 PRD 与实跑留档（`69fd32a`）、把版式任务补到可 start（`78e67f6`）；1.4 复核通过后从步骤 0 一路跑到步骤 8：常驻页头加「当前小节」，两类版式的纵向分布改掉，排版审计扩到第八项。落地分成两个 commit——`83a292a`（sections 契约 + 页头渲染）与 `ce08dc7`（纵向分布 + 审计扩容）。

**关键发现**

1. 纵向填充比既当不了审计闸，也不能当优化目标。18 集 × 双平台 694 场逐场实测：任何 ≤0.70 的全局阈值都判红 246–377 个已发布场次。而 `justify-content:space-between` 能把 code/hook 读数从 0.55 刷到 0.74（竖版 0.90），截图却是标题贴页头、代码贴下沿、中间空 250–470px。CSS 分布只能决定「洞摆在哪」，code/hook 的填充由每场内容量决定。
2. `padding-block` 是实伤不是观感：竖版加 3u/6u 把长代码场挤给 fitAll，19.1px 压到 13.3px，f2/p4/s16 三集 8 场撞审计的 16px 地板（`video:check` exit 1）。控制变量用 `git checkout HEAD -- video/src/layout.mjs` 复跑，证明改前是绿的——这是真回退，不是既有欠账。
3. 唯一能被 CSS 钉死的 kind 是 card：横版让面板长满（`justify-content:stretch` + `flex:1 1 auto`）125 场全部到 0.82；竖版原样不动，它改版前实测就有 0.85，「长满」只会把三行字的短卡吹成巨框。
4. 进度杠判据必须数**看得见的**那几根：竖版 `.ticks` 一直挂在 DOM 里只是 `display:none`，按节点数判 12 场全部误报。
5. 页头标题超长由两层各抓一半：竖版靠几何（42 字塞进 `.secchip` → 12 场 `越出画布`），横版靠契约（1920 装得下，`loadEpisode` 的 `SECTION_TITLE_MAX=12` 先拦）。原 design 写的「审计抓到」是只想到了一层。

**改了哪些**

- `video/src/spec.mjs`：`sceneSections()` 纯函数 + `SECTION_TITLE_MAX=12` + `validateSections()` 接进 `validateEpisode`（`at` 命中/严格递增/`title` 非空/`at` 不重复，四条都算 error）。
- `video/src/layout.mjs`：页头左格收成 badge + 系列名（去掉重复的 `· F5` 尾巴），右格新增 `.secchip`「第 i/n 节 · title」，竖版另给一根 `.secbar`（它 `.ticks` 本就关掉，这是唯一按节进度载体）；`.lay-code/.lay-hook` 只加 gap（横 4u / 竖 2.4u，字号地板是竖版只抬到 2.4u 的理由）；横版 `.lay-card` 面板长满、竖版留旧摆法。页头 DOM 唯一写入点是 `MCU.setup(i)`，只随场次号变、绝不随帧时间 t 变。
- `video/src/cli.mjs`：`hit`/`marks` 两个选择器补 `.secchip,.secbar`；新增第八项「同屏 N 根按场进度」。
- `.trellis/spec/video/`（新层：`index.md` + `layout-contract.md` 七段契约）、`spec/index.md` 补第四层表行、`spec/guides/index.md` 补「改成片版式时」四条 checklist。
- `research/`：`fill-probe.mjs` 扩 chip/杠读数 + 双平台截图 + 最差场列；新 `fill-sweep.mjs` 全量扫描器；`baseline-20261017.md` 补 §六–§八。`after-*`/`after-sec-*` 与 `baseline-*` 成对，被否的走法留 `lever-spacebetween-*.png` 两张反例。

**验证**

- 兼容性口径：无 `sections` 的旧集页头 DOM 一字不变；用 fixture 注入后 `video:check` 输出与不注入**逐位相同**，与改前基线只差两条 verdict 行。
- `npm run video:lint` 18 条全绿；`npm run video:check`（无参数，18 集 × 双平台 694 场）exit 0——CSS 注释定稿后又单独复跑一遍 `check-all18-shipped.txt`，仍 exit 0。
- `md5sum -c research/out-md5-before.txt --quiet` exit 0：`video/out/` 一字节未动，全程没对既有 18 个 id 跑 `video:build`。
- 两个故意失败证明新判据不是死代码（bilibili 也渲染 `.secbar` → `同屏 2 根按场进度`；42 字 chip → 竖版越界 + `loadEpisode` 契约拦截）。
- PRD 的 AC 按实测分档改写（card 达标、code/hook 的 0.70 换成「不许靠拆开内容换填充」、anim/outro 豁免、两平台分开），走 Phase 1 修订口径而非就地放宽。
- 归档之后补的一刀：`task.py archive` 把 `research/` 往下挪三层，spec 指过去的命令、`layout.mjs` 注释里的反例截图路径、两个探针脚本自己的相对 import 一起失效，改指 `archive/2026-10/` 并把相对深度从 4 层补到 6 层（每个 specifier 用 existsSync 验过落地）。

**待办**

- 本任务出口条件解除：`10-17-s5-systick-episode` 可以进 Phase 2 渲帧——S5 是第一个真正带 `sections` 的集，新页头的第一个观众就是它。
- 知乎 F5 频控窗口（10-17 21:07 之后）跑 `node .temp/f5-zh-publish.mjs`，闸门文件 `.temp/zh-run/I_HAVE_USER_OK=f5-sem-mutex` 留在原地。
- 抖音 F5 置顶需用户在 App 内长按；E04 上板要真板（COM4/COM5 是蓝牙虚拟口）；B站合集等权益中心 Lv2。


### Git Commits

| Hash | Message |
|------|---------|
| `1fa7d1d` | (see git log) |
| `69fd32a` | (see git log) |
| `78e67f6` | (see git log) |
| `83a292a` | (see git log) |
| `ce08dc7` | (see git log) |
| `29def0a` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 8: 开小红书第四条投放线，F5 竖版笔记已发布

**Date**: 2026-10-17
**Task**: 开小红书第四条投放线，F5 竖版笔记已发布
**Branch**: `main`

### Summary

常驻浏览器 + 分步驱动 + 台账三件套落地：字段上限、话题 chip、封面三层入口全是实测量出来的；站外地址与超限拦在 fill 里，发布那一步仍归人点。F5 2026-10-17 15:32 已发布并回笔记管理核到。

### Main Changes

### 会话目标

新开第四条投放线：小红书竖版笔记，把 F5《信号量和互斥量》投上去。用户口径三条——只发 F5 一条试水、AI 起有头浏览器探入口、标题/正文/评论一律不出现站外地址与 GitHub 字样。

### 关键决定与实测

- **没有 API 通道，沿用常驻浏览器那套**：本机无任何小红书开放平台凭证，创作者后台发布接口未验过；入口实测在 `creator.xiaohongshu.com/publish/publish?target=video`，是个 SPA 表单。于是 `xhs-daemon.mjs`（复用 `.temp/douyin-profile` 与 9223 那个窗口，同一 user-data-dir 起第二个实例会被挡）+ `xhs-probe.mjs`（只读）+ `xhs-step.mjs`（分步驱动，十个 verb）。
- **上限只能自己量**：标题 20 字、正文 1000 字，且**都不在 DOM 强制**——喂 39 字进标题框，`input.value` 仍是 39，页面只把计数器印成「39 / 20」，拦的是提交。所以断言写进 `fill`：按码点断长度，任何字段命中 `https?://` 或 `github` 直接退出码 2。
- **话题必须是 chip**：正文里直接打 `#名字` 是黑字，不成话题；只有 `#名字` 之后弹出来的那条候选被接住才生成 `a.tiptap-topic`（带 `data-topic` 的 id 与 `xhsdiscover://topic/v2/...`）。接法用回车——上一版用 `locator('text=/^#FreeRTOS/')` 点候选，先匹配到的正是刚打进正文的那串黑字，三次"clicked"拼出「#优先 级反转斥锁RTOS」这种交错垃圾。
- **封面入口藏三层**：点默认封面缩略图（「设置封面」那四个字只是标题，点了没反应）→「编辑封面」→ 才有 `accept="image/png, image/jpeg, image/*"` 的 file input → 裁剪/模版/贴纸/文字/滤镜/标记 → 点「完成」才落定。应用后平台自己回「封面效果评估通过，未发现封面质量问题」。
- **发布成功的判据**：笔记管理 `/new/note-manager` 的「已发布」标签里有这条，且「审核中」「未通过」都是空的。发布后表单 URL 变 `?source=&published=true`、草稿箱归零，但那是事后信号不是回执。观众侧详情页从笔记管理点标题打不开（只选中、弹出页不导航），所以"有没有漏地址"的核对必须留在**发布前**：15:31 对编辑器正文与 `episode.json` 逐字比过，只差空行，两个外链正则双双「无」。

### 改动的文件

- 新增 `video/publish/xhs-daemon.mjs`、`xhs-probe.mjs`、`xhs-step.mjs`、`xhs-plan.md`（台账：实测事实表、与抖音四处口径差、闸门与工具布局、F5 已发布状态与证据）。
- `video/episodes/f5-sem-mutex/episode.json` 补 `publish.xiaohongshu`（title/body/topics/pinned/repro/noLink）；正文那句「（6000 / 2500）」改成「6000 与 2500」，因为它会被全页正则当成计数器。
- `.agents/skills/video-release/SKILL.md` 从三条线改成四条线：§2 新增小红书小节（入口命令 + 判据）、§3 四条失败信号、§4 导流口径、§5 运行态表行、§6 三个坑（常驻页不许关 / 全页正则读计数器 / SPA 要 settle）。

### 验证

- F5 那条 **2026-10-17 15:32 已发布**：笔记管理「已发布」有它（01:06，截图 `manager-已发布.png`），「审核中」「未通过」两标签空；创作者中心首页「最新笔记」也换成这条。发布键是人点的——`publish` 步查完闸门仍抛错，这一步至今没自动化，留痕 `.temp/xhs-run/f5-sem-mutex-published.txt`。
- 计数器读法改版后做过判别验证：合成一页「正文含（6000 / 2500）+ 两个真计数器」，旧的全页正则吐三条、新的只吐 `539 /1000` 与 `18 /20`（`.temp/xhs-counter-check.mjs`）；顺带量到一条事实——没传视频时空表单上一个计数器都没有。
- `xhs-probe.mjs` 真跑一遍：6.7 秒 exit 0。之前它收尾没有 `process.exit`，CDP 那条 websocket 挂着导致进程永不退出（上一版靠 timeout 掐掉）；探针默认 URL 也从已失效的 `/creator/home`（实测回「你访问的页面不见了」）换成活着的 `/new/home`。
- 三个脚本 `node --check` 全过；`episode.json` JSON 解析过；新增文件里除 `noLink` 那条自述外无 http/github 字样，cookie 只报条数不报值。

### 待办

- 置顶导流评论：用户选「先写工具我来发」，但探完的结论是**网页侧没有入口**——创作者中心十项导航里没有任何评论项，笔记行的「置顶」图标置顶的是笔记本身，公网 `explore/<noteId>` 直连回 `error_code=300031`（要 `xsec_token`），而这个 profile 只登录了创作者中心。出路两条：同一窗口再登录一次网页版后我量评论区写 `comment` 步，或手机 App 内发+长按置顶。证据与 noteId 在 `xhs-plan.md`。
- 合集：用户定「这轮先不建」——挂合集要走「编辑」，改已发布笔记可能重新进审核（B站有 `state=-6` 先例），等第二条上小红书再定名。内容类型声明与原创声明仍未选。
- 标题体例：账号既有条目是「STM32零基础自学N｜…」，F5 这条走的是「xSemaphore 一个函数都没有」，要不要统一得定。
- 知乎 F5 频控窗口 10-17 21:07 之后重跑 `node .temp/f5-zh-publish.mjs`；抖音 F5 置顶需用户在 App 内长按；E04 上板要真板；B站合集等 Lv2。


### Git Commits

| Hash | Message |
|------|---------|
| `018c542` | (see git log) |
| `7d6e750` | (see git log) |
| `758eaef` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 9: 小红书置顶评论已发出、置顶入口实测不存在；合集挂载做到「选中」待人提交

**Date**: 2026-10-17
**Task**: 小红书置顶评论已发出、置顶入口实测不存在；合集挂载做到「选中」待人提交
**Branch**: `main`

### Summary

comment 步补 --go（闸门另起一张 I_HAVE_USER_OK_COMMENT）并真发出 138 字置顶评论；量到网页版评论菜单只有「删除评论」，据此不写 pin 步。合集名进 episode.json，新写 collection 步：认 tooltip「编辑」进 /publish/update、弹层按整段文本全等选中「STM32 零基础自学」，冷跑两次验到选中不落盘、提交那颗是 closed shadow 的 <xhs-publish-btn>，所以停在未提交等人点。

### Main Changes

### 做了什么

接上一轮小红书那条线的两个尾巴，都按"先实测再写代码"走完。

1. **置顶评论发出去了，并量到"置顶"在网页版做不到**
   - 用户点头「发送这条置顶评论」→ 给 `xhs-step.mjs comment` 补 `--go` 分支，闸门用**另一个文件**
     `.temp/xhs-run/I_HAVE_USER_OK_COMMENT=f5-sem-mutex`（不复用发布那张 `I_HAVE_USER_OK=<ep>`，两种授权混一起，以后谁看见它就以为发布也批过了）。
   - 实跑：138 字回填一致 → 点「发送」→ 评论框剩 0 字、列表按前 18 字找回这条 = 是。留痕 `f5-sem-mutex-comment-sent.png`。
   - 再按用户要求量置顶入口，结论是**否定的**：自家评论的「…」菜单里只有「删除评论」，整页扫不到「置顶」二字
     （`.temp/xhs-pin-probe4.mjs` + `comment-menu-open.png`）。据此**不写 `pin` 步**，与抖音同口径：置顶只能 App 内长按。
2. **合集：建好了，挂载做到"选中"为止**
   - 用户改口「可以创建合集了，另一个已经创建ok了」→ 合集名 `STM32 零基础自学` 进事实源
     `episode.json` 的 `publish.xiaohongshu.collection`（含一个半角空格，是弹层里 `div.item` 的逐字文本）。
   - 新写 `xhs-step.mjs collection`：笔记管理里 hover 图标认 tooltip「编辑」→ 新标签落 `/publish/update`（noteId 不抄进代码）
     → 点 `.collection-plugin-button` → `.d-popover .item` 按整段文本全等认领 → 回读整行文本 + 截图。**不点提交。**
   - 冷跑两次（中间关掉编辑页）量到两件事：选中**不落盘**（重开又回落「选择合集」）；判据只能读
     `.collection-plugin-wrapper` 整行文本，因为选中后 `.collection-plugin-button` 那个类会消失。
   - 提交那颗是 `<xhs-publish-btn submit-text=发布 save-text=暂存离开 is-publish=true is-save-draft=false>`，
     rect `220,740 680x90`，**closed shadow root**：全页 `getByText('发布',{exact:true})` 命中 0，x=240→880 每 40px 做
     `elementFromPoint` 全部命中宿主自身（坐标也点不准）；实例上只有 `_onPublish`/`_onSave`，那是绕过前端校验硬触发，不做。
     顺带一个撞名坑：左上角导航 `div.publish-video > .btn-wrapper` 文案是「发布笔记」。
   - 所以编辑页现在停在"已选中合集、未提交"，等人点那一下（`is-publish=true` 时点了等于把公开笔记重新提交，大概率再走审核）。

### 改了哪些文件

- `video/publish/xhs-step.mjs`：`comment` 补 `--go` + 独立闸门；新增 `collection` 步；`WEB_ONLY` 改 `NO_WORK_PAGE`（collection 走 `/publish/update`，不能被 `/publish/publish` 工作页认领抢走）。
- `video/episodes/f5-sem-mutex/episode.json`：`publish.xiaohongshu.collection` + `collectionNote`。
- `video/publish/xhs-plan.md`：置顶评论四条证据 → 已发出；新增「置顶这件事在网页版做不了」一节（四条证据 + 据此不写 pin）；「合集这轮不建」改成实测到的挂载链路与 `<xhs-publish-btn>` 契约。
- `.agents/skills/video-release/SKILL.md`：命令块加 `collection` 与 `comment --go`；判据三条（评论闸门另起一张、置顶做不到、合集挂载只到选中）；§3 加"选完重开又变回选择合集"一行。
- `.temp/xhs-run/f5-sem-mutex-published.txt`：评论已发（16:21）与合集选中未提交两条留痕。

### 验证

- `node --check video/publish/xhs-step.mjs` 过；`episode.json` JSON 解析过。
- `collection` 步冷跑两次全绿：`弹层里的可选项（1）：「STM32 零基础自学」` → `这一行显示合集名：是` → 打印 `<xhs-publish-btn>` 属性契约 → 明确停手没点提交。
- 探针全程只读：只 `page.close()`，没碰 `browser.close()`，常驻页与登录态没动。

### 待办

- 合集最后那一下提交归人点（编辑页就开着，选中状态在）；点完重开编辑页应仍显示合集名才算挂上。
- 内容类型声明与原创声明仍未选（属人工决定）。
- 知乎 F5 频控窗口 10-17 21:07 之后重跑 `node .temp/f5-zh-publish.mjs`；抖音 F5 置顶需用户在 App 内长按；E04 上板要真板；B站合集等 Lv2。
- 标题体例：账号既有条目是「STM32零基础自学N｜…」，F5 这条是「xSemaphore 一个函数都没有」，要不要统一得定。


### Git Commits

(No commits - planning session)

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 10: 小红书合集线收口（建「通往单片机之路」、F5/S5 换集落盘）+ 视频系列 17 条批量上传全发

**Date**: 2026-10-17
**Task**: 小红书合集线收口（建「通往单片机之路」、F5/S5 换集落盘）+ 视频系列 17 条批量上传全发
**Branch**: `main`

### Summary

视频系列自建合集「通往单片机之路」建成、F5/S5 换集落盘（坐标点击+重开回读；S5 复审约 3-4 分钟后回稳）；用户「视频都要上传啊」后 17 条文案块从各集抖音稿派生（不新编）、xhs-batch.sh 逐集发布 17/17 零失败，「已发布」整列 43 张卡片对账逐条在列（=24 章+F5/S5+17 新）、3 条抽样合集行全中；发布点击改为 CDP 穿透量内部「发布」盒。

### Main Changes

### Summary

视频系列自建合集「通往单片机之路」建成、F5/S5 换集落盘（坐标点击+重开回读；S5 被复审拉到「审核中」约 3-4 分钟后回稳）；
用户「视频都要上传啊」后 17 条文案块从各集抖音稿派生（不新编一字），`xhs-batch.sh` 逐集发布，**17/17 零失败**，
「已发布」整列 43 张卡片对账逐条在列、3 条抽样合集归属全中；发布点击改用 CDP 穿透量内部「发布」盒。

### 做了什么

1. **状态核实（不抄前一条会话的说法）**：S5 已发布且已挂章节合集「STM32 零基础自学」
   （重开浏览器后经笔记管理「编辑」新开的页回读）；F5 未挂任何合集；账号弹层里只有 1 个合集；
   抖音那条线的视频合集叫「通往单片机之路」（mix，c3b 排第 5 集）。
2. **拍板（对话问答）**：新建「通往单片机之路」（给视频系列）＋提交那一下由我点（坐标点击+回读验证）＋立一个新任务。
3. **建合集**：`collectioncreate --ep=f5-sem-mutex --desc=屏上每个数都是本机跑的`——
   编辑页 → 加入合集 → footer「创建合集」→ 名称/简介 →「创建并加入」，回显「共1篇 成功创建」；
   闸门 `I_HAVE_USER_OK_COLLECTION=通往单片机之路`。中途两个坑都修进驱动：认领编辑页要按标题框逐字
   （F5 那步曾复用 S5 留下的页、把别人的合集行当自己的读）；「创建并加入」后立刻 reload 会撞 SPA 原生
   confirm（ProtocolError: No dialog is showing）——统一挂 dialog 监听。
4. **换集并提交**：`collection --ep=f5-sem-mutex --go` / `--ep=s5-systick --go`——真实点击 (560,789) →
   F5 回读「更新成功」、S5 toast 偶发没读到 → 两条**重开编辑页回读那一行=「通往单片机之路」（落盘）**；
   笔记管理里两条都在「已发布」；**S5 被拉回「审核中」约 3-4 分钟后转回「已发布」**（播放数 51 不变），
   F5 同批没有——`is-publish=true` 的提交何时引复审平台不保证。
5. **17 条批量上传**（用户「视频都要上传啊」→ 选「今晚 17 条连跑全发」）：
   - 文案块派生：标题=抖音候选里最短 ≤20 字（f0/p4 两条人工指定；p4 三条候选全超 20）、
     正文=抖音 `intro` 去掉含 站内/全篇/全文/免费/仓库/通往单片机之路 的句子 + 尾巴「复现：<repro>」、
     置顶=抖音 `pinned` 同规则删句、话题=tags 前三个、合集=通往单片机之路。
     插入按**花括号配平定位 publish 对象**（根键顺序不定：c4 的文件尾是 platforms 的收尾，
     按尾锚会把块插进 platforms——被「除新块外一切不变」的守卫拦下）；文件是 CRLF，逐文件取 EOL。
   - `video/publish/xhs-batch.sh`：逐集 `open→upload→fill→topics→coverset→coverapply→attach→publish --go`，
     任一步非零即停；逐集闸门 `I_HAVE_USER_OK=<ep>`（内容=用户原话+该集 id）。
   - `attach` 在**发布表单**上把合集选好（发出去一并落盘，省掉发完回编辑页补一遍）；
     `publish --go` 的点击用 **CDP `DOM.getDocument(pierce:true)` + `DOM.getBoxModel`** 量内部「发布」盒
     （573..693 × 769..809 → 点 (633,789)）——宿主 rect 221..901 的正中 (561,789) 落在
     「暂存离开 429..549｜发布 573..693」之间的**空隙**上，点它什么都不发生（第一次白点过一次）。
   - 结果：**17/17 发布成功、零失败**（c3-volatile 单跑 + 16 条批跑 1608s）；笔记管理「已发布」
     整列 **43 张卡片**收齐（= 24 章 + F5/S5 + 17 新），新 17 条 22:22–22:49 逐条在列。
6. **核对工具的两个坑**（写进 xhs-plan）：笔记管理**搜索框会偶发返回空结果**（同一前缀换个时刻能命中）——
   别当唯一判据；该列表是**虚拟列表、只渲染可视区约 10 条**，`PageDown`/滚轮/scrollTop 单用都不动，
   要 **Ctrl+Minus 缩小 + 三种滚动齐上**才收得全 43 条。
7. **抽 3 条核合集归属**：f0-why-rtos / c3-volatile / f6-timers 编辑页回读那一行全部=「通往单片机之路」✓。

### 改了哪些文件

- `video/publish/xhs-step.mjs`：+`collectioncreate` / `attach` / `publish --go`、`collection --go`；
  `claimEditPage`（按标题框认领）、`findPublishButtonBox`（CDP 穿透）、dialog 监听、
  `openCollectionPicker`（入口两态回退）。
- `video/publish/xhs-batch.sh`（新）：逐集跑批。
- `video/episodes/<17 集>/episode.json`：+`publish.xiaohongshu` 块（派生稿）；`f5/s5` 的 `collection`
  改「通往单片机之路」并更新 `collectionNote`。
- `video/publish/xhs-plan.md`：合集一节重写、批量一节新增（含结果与核对坑）、四处旧口径改写。
- `.agents/skills/video-release/SKILL.md`：命令块加 collectioncreate/--go、attach、publish --go、xhs-batch.sh；
  发布/合集两条判据重写；§3/§6 补今天的三个坑。
- `.trellis/tasks/10-17-xhs-series-collection/`（收口，AC 全勾+执行记录）、
  `.trellis/tasks/10-17-xhs-series-upload/`（新建：PRD+AC 全勾）。

### 验证

- S5/F5 落盘：重开编辑页回读（含浏览器重启后新开页）；点击坐标与 toast 回读记录在案。
- 批量：16 个「完成」标记 + 17 条 `published=true`；「已发布」整列对账；3 条抽样合集行回读。
- `node --check video/publish/xhs-step.mjs` 过；17 份 episode.json 的深比对守卫（除新块外一切不变）全过。
- 期间浏览器窗口无预警掉了三次（第三次由定时任务占用同一共享 profile 的嫌疑最大）——每次重启 daemon 后继续，
  产物均在服务端，未影响结果。

### 待办

- S5 置顶评论未填未发（发送需 `I_HAVE_USER_OK_COMMENT=s5-systick` 的对话点头）；17 条新笔记的评论区置顶
  只能在 App 内长按做。
- 内容类型声明 / 原创声明：F5、S5 两集都没选（属人工决定）。
- 笔记管理虚拟列表的核对方式已写进 xhs-plan，下次别再用"搜索一次没命中"下结论。


### Git Commits

| Hash | Message |
|------|---------|
| `e09345e` | feat(publish): 小红书视频系列 17 条上传全发，合集「通往单片机之路」建成收口 |
| `0212cf3` | docs(publish): 批次核对口径修正——43=24 章+F5/S5+17 新、抽样 3/3、核验记为整列对账 |
| `cfbe246` | chore: record journal |

### Testing

- `node --check video/publish/xhs-step.mjs`：过（当晚批跑与两次发布点击都由这一版驱动完成）。
- 17 份 episode.json 的生成守卫：按花括号配平插入 + 写回后 JSON.parse 深比对「除新块外一切不变」，全过。
- 发布：17/17 每条日志都有 `URL 已 published=true`；批日志 16 个「完成」标记、零错误行。
- 权威核对：笔记管理「已发布」整列 43 张卡片收齐（=24 章+F5/S5+17 新）逐条对；截图 `xhs-manager-scrolled2.png`（标签 active 已复核）。
- 合集归属：f0/c3-volatile/f6-timers 编辑页回读合集行 3/3 =「通往单片机之路」。
- 落盘回读：F5/S5 换集后重开编辑页那一行=合集名（含浏览器重启后新开页）。

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 11: xhs 驱动改进：虚拟列表扫卡、只读 collectioncheck、xhs-verify 整列对账与台账对齐

**Date**: 2026-10-18
**Task**: xhs 驱动改进：虚拟列表扫卡、只读 collectioncheck、xhs-verify 整列对账与台账对齐
**Branch**: `main`

### Summary

把当晚靠临时探针硬啃的手法固化进驱动并清掉 6 处旧口径；最难用例与 19/19 复核全过

### Main Changes

- `xhs-step.mjs`：`claimEditPage` 换成**虚拟列表扫卡**——Ctrl+Minus 缩小 ×4，再用 PageDown / 滚轮 / scrollTop 三种滚动轮着来（上限 25 轮），
  认领到编辑页后 Ctrl+0 还原缩放。背景：笔记管理是虚拟列表、只渲染可视区约 10 条，旧逻辑在"目标卡不在首屏"时直接报「没有卡片」。
- `xhs-step.mjs`：新增只读 `collectioncheck --ep=<ep>`——认领编辑页 → **重载读服务端** → 回读合集那一行，PASS/FAIL、退出码 0/4、
  截图 `<ep>-collectioncheck.png`；并把它并进 `NO_WORK_PAGE`（原来会顺手认领/新开一张 /publish/publish 发布页，纯只读核对不该有副作用）。
- `xhs-step.mjs`：`comment` 步在 profile 主页找卡加**有界滚动兜底**（6 轮 × 3 种滚动），评论流不再只认第一屏。
- 新增 `video/publish/xhs-verify.mjs`：**整列对账**替代搜索式核验——默认核所有带 `publish.xiaohongshu` 的集（可 `--eps=a,b,c`），
  收全「已发布」列表按标题对账，落标签容器 `tab-item--active` 类名做证据，列表头总数只作动态记录、不当完整性基准，退出码 0/1/2，
  用完还原缩放再关自己的页（缩放是 origin 级，别带进常驻页）。
- 台账收口（6 处旧口径与实装对齐）：xhs-plan 发布步说明、comment 头注（「不给 --go」→ 默认只填/`--go` 可代发）、`NO_WORK_PAGE` 集合、
  S5 评论状态（未填未发 → 已发）、评论一节标题、xhs-verify 条目去掉已废的「⚠」说法；SKILL 命令块与判据同步。
- **现场事实**：核对时列表头 43→44→45 边跑边涨，是 **ops 线并发补发它审计出的 ch24/ch25**（用它自己 CDP 量的按钮坐标发的）；
  那晚 23:3x 的账 45 = 26 章 + 19 条视频，是快照不是最终数——这也是把「总数」降级为动态记录的直接原因。


### Git Commits

| Hash | Message |
|------|---------|
| `22cfba3` | feat(publish): xhs 驱动——合集只读复核 collectioncheck + 虚拟列表扫卡（缩小+三种滚动） |
| `61942e7` | feat(publish): 小红书发布核对常设化——xhs-verify.mjs（整列对账替代搜索式核验） |
| `bb293bf` | fix(publish): 三处自相矛盾——collectioncheck 并入 NO_WORK_PAGE、comment 头注对齐 --go、S5 评论状态改实录 |
| `60f048c` | docs(publish): 台账三处收口——评论线标题改实际行为、核对工具条目去掉已废的⚠口径、并发数注明为当晚快照 |

### Testing

- `collectioncheck --ep=c3-volatile`：44 条列表里扫到第 17 位那张卡（最难用例），重载回读合集行 =「通往单片机之路」、归属 是（72.9s）。
- `collectioncheck --ep=s14-pwr`：通过（57.4s），顺带验到「别的笔记的编辑页不碰」分支；并入 `NO_WORK_PAGE` 后复跑仍过。
- `xhs-verify.mjs`：两跑 **19/19 全中**（含 F5/S5 回归）；标签 `tab-item--active` 类名逐跑落证；总数只作动态记录、不参与判定。
- `node --check video/publish/xhs-step.mjs` 与 `video/publish/xhs-verify.mjs`：全过。

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 12: BMS-Z 对齐：验证纵深（门禁脚本/文档对账/PDF 契约/下载打包/dist 对账）

**Date**: 2026-10-25
**Task**: BMS-Z 对齐：验证纵深（门禁脚本/文档对账/PDF 契约/下载打包/dist 对账）
**Branch**: `feat/video-v2-remaster`

### Summary

对照姊妹项目 BMS-Z 补齐验证纵深：新增 local-gates(.ps1/.sh)、docs-check、pages-check、search-check、check_pdf、publish_downloads、links.yml+.lychee.toml、ruff.toml+lint job；runner 钉 ubuntu-24.04；补 CITATION/SECURITY/CoC/根 CHANGELOG。全量本地门禁 24 pass/0 fail/0 skip。

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

| Hash | Message |
|------|---------|
| `d87f513` | (see git log) |
| `ca9b756` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete

## Session 13: AI 章有趣度增量 + 印前字体子集双坑修复

**Date**: 2026-10-27
**Task**: 10-27-ai-dev-deepen 验收面内继续（用户明示不新建任务）
**Branch**: `feat/video-v2-remaster`

### Summary

干区外科润色 5 处（A0 选型段、A3 配置/拓扑/四问/收尾），事实 token 多重集零漂移、口癖预算内、零新字符。印前重建连破两坑：其他任务未提交改动致 庭/胆/讯 缺子集（SimSun 回退）→ 子集 2144→2147 字；provenance 漂移致 Cascadia Mono 未钉轴（源文件实为可变字体）→ 全书代码嵌成无名 Type3 → 重钉 wght=400/700。最终 13 门 + 印前电池 + 回归三件套全绿。

### Main Changes

- docs/ai/00-pair-not-ghost.md:313、docs/ai/03-toolflow-mcp.md:128/130/306/324（仅散文框定段，不可动清单零触碰）
- docs/ai/03-toolflow-mcp.md:328 「第六章」→「第六节」（跨模型评审采纳；修后全链复验）
- mcu-book/print/fonts/ 九支 woff2 重建（mono 钉 wght=400/700；覆盖 2147 字；provenance.json 同步）
- 详见 .trellis/tasks/10-27-ai-dev-deepen/implement.md「实施实录（2026-10-27 有趣度增量）」

### Git Commits

无（工作区改动，与既有 368 处未提交改动共存）

### Testing

- prose_guard compare ×2「不可动清单：全部一致」；single 口癖预算内；新字符零缺（含 :328 修复后复跑）
- `npm run docs:build` ✓
- check_pdf 13 门「全部通过」；widow 0 / orphan 0 / U+2011 0 / 灰点 0
- pytest 72 passed；anim-lint 109/109；art_guard 100 枚 0 违规

### Status

[OK] **Completed**

### Next Steps

- 用户过目 A0/A3 润色段（任务 Phase 7 验收面）
- `.temp/interest-orig/` 为 docs/ai 唯一 pre-polish 基线，保留勿清

## Session 14: AI 章第二轮有趣度增量（A1/A4）

**Date**: 2026-10-27
**Task**: 10-27-ai-dev-deepen（续，不新建）
**Branch**: feat/video-v2-remaster

### Summary

六章全量复扫定位剩余干点：A0/A2/A5 与 A1/A4 节级意象已饱和（强行加喻有负收益），仅三处扁平连接句值得动。

### Main Changes

- docs/ai/01-prompt-patterns.md:224 「措辞是天气，你要看的是地形」
- docs/ai/04-hallucination-defense.md:230 窗口意象 + 「先问在不在，再问对不对」；:260 「越往下越贵」
- docs/ai/04-hallucination-defense.md:178-183 删 §二三条「工作推论」复读块（180/181 分别复述 :172/:155，评审 advisory 属实；保留 :48 埋点与 :172 收束，常见坑坑体复盘不动）

### Git Commits

无（工作区改动，与既有未提交改动共存）

### Testing

- prose_guard compare ×2「不可动清单：全部一致」；single 预算内（A1 ×1 / A4 ×1）；零新字符
- `npm run docs:build` ✓；check_pdf 13 门「全部通过」；widow 0 / orphan 0 / U+2011 0 / 灰点 0；三句新文确认进 PDF
- pytest 72 passed；anim-lint 109/109；art_guard 100 枚 0 违规
- 删脂后复验：compare 一致、预算内、零新字符；重排 13 门全过、电池全 0、回归三件套绿；PDF 确认块无残留且 :48/:172 原句在

### Status

[OK] **Completed**

### Next Steps

- 用户过目 A1/A4 三处润色句与 A4 §二删脂（并入 Phase 7 验收面）
- `.temp/interest-orig/` 内 A1/A4 快照为本轮基线，保留勿清

## Session 15: AI 章第四轮（复读扫描 + A0 句式去叠）

**Date**: 2026-10-27
**Task**: 10-27-ai-dev-deepen（续，不新建）
**Branch**: feat/video-v2-remaster

### Summary

针对 gates 盲区（复述/句式疲劳）做机械扫描后外科处置：六章句级近重复与「不是X，是Y」密度全量判读，命中均为合法重复类；唯一动刀点为 A0:315 双叠转折句。

### Main Changes

- docs/ai/00-pair-not-ghost.md:315 删填充转折「这不是行业默契的修辞，是三个独立来源可以互相印证的事实陈述」→「三个来源互相印证，这本身就是本章工作观的外部证据」（保留章旨级强转「不是本书的口味，是工具提供者自己写下的边界」）
- 工具：.temp/fat_scan.py（句级 LCS + 句式计数，可复跑）

### Git Commits

无（工作区改动，与既有未提交改动共存）

### Testing

- prose_guard compare「不可动清单：全部一致」；single 预算内（——×2）；零新字符
- `npm run docs:build` ✓；check_pdf 13 门「全部通过」；widow 0 / orphan 0；PDF 四断言 PASS
- pytest 72 passed；anim-lint 109/109；art_guard 100 枚 0 违规
- task_verify：unverified（project-or-git-baseline-unavailable，docs/ai 未入 git）

### Status

[OK] **Completed**

### Next Steps

- 用户过目 A0:315（并入 Phase 7 验收面，累计 11 点）
- 六章文字面判定为维护水位：再要求继续时方向是逐字句微调或事实/结构层，无批量目标
- `.temp/fat-orig/` 为 R4 基线；`.temp/interest-orig/` 各轮基线均保留勿清

## Session 16: R5 插图生动化（AI 部题花重绘）

**Date**: 2026-10-27
**Task**: 10-27-ai-dev-deepen（续，不新建）
**Branch**: feat/video-v2-remaster

### Summary

用户指令转向插图生动度。题花密度对照全书范本判四枚扁平（A0/A1/A2/A5），按各章母题重绘；A3/A4 语义完备不动。文字面复扫零干区、零改动。

### Main Changes

- `mcu-book/book/assets/chapter-art/ai-00/01/02/05-*.svg` 重绘（890/1080/1024/1157B → 1602/2029/2273/2069B，入全书范本带）：A0 分布+采样→草稿→放大镜→终审印章；A1 夹板工单→齿轮机头模型→带勾草稿；A2 手册↔断开箭头+三问+放大镜对账→带表笔板卡（实测作丝印）；A5 传送带源文→双闸门→成书
- A2 视觉复核修正：双向箭头原穿镜片与对勾交叉 → 断成两段短箭头让镜头坐缺口

### Git Commits

无（工作区改动，与既有未提交改动共存）

### Testing

- 视觉核验：白底 3 倍临时副本光栅（`:img` 黑布坑绕过），视觉模型逐要素确认四枚无重叠/穿字/越界
- art_guard 100 枚 0 违规；anim-lint 109/109（未动复跑）
- `npm run docs:build` ✓；build_print 1168 页字体全 Type0 具名；check_pdf 13 门「全部通过」
- PDF 断言 v3 PASS：get_toc 定位章页 + 题花字号带 5.9pt（e06 对照 7.6pt 校准）六章标签全命中；pytest 72 passed
- 新标签字符 ⊆ 字体子集域 2260 字；文本零改动（prose_guard 不适用）

### Status

[OK] **Completed**

### Next Steps

- 用户过目四枚重绘题花（并入 Phase 7 验收面）
- `.temp/art-orig/` 为本轮 pre-redraw 基线，保留勿清；`.temp/view-*.svg` 为视觉核验临时件

## Session 17: R5b 几何对位复审（bbox 算术抓 R5 残留缺陷 + A3/A4 补判重绘）

### What Happened

- Advisory 以 bbox 算术证 R5 有实缺陷（视觉模型「布局已核」不构成几何证据）：A0 放大镜与终审章双悬空（镜片距纸 11u、章距纸缘 59u）；A5 全图零曲线（100 枚中唯一）；另 A0/A2 共用放大镜母题（2/6 重复）
- R5b 四处修：A0 删镜（归 A2）+ 章加大压纸角 + 纸右缘在章覆盖段留缺口（视觉复核揪出缘线穿「终/审」二字之间）；A5 弯带+柱沉+物件齐落带面+signature 波；A3 撤「语义完备」判定整体重绘（回环齿轮模型+三管线接手册叠/构建终端/方波三具体站点，原版底波穿串口日志框）；A4 撤判定重绘（真落差决策树+四异叶子：摊开书/交叠纸/采样线探针/播放钮；「抽样信」经正文 6 处用例证为章内术语，非截断）
- 流程事故：A3 首写文件名调换（ai-03-mcp-toolflow ≠ 章节 slug ai-03-toolflow-mcp）成孤儿，构建未读到、art_guard 100→101 暴露；归位复 100
- 六枚 720×440 主插画盘点（advisory 优先级主张）：各章核心时刻/生态图各司其职，判不动

### Testing

- bbox 断言 19 项 PASS；白底黑描边 3 倍光栅视觉复核：A0 缺口干净、A3 三管线零穿越、A4 下垂成立无穿入
- art_guard 100 枚 0 违规；anim-lint 109；docs:build ✓；重排 1168 页 185.3×260.3mm 字体 5 支 Type0 具名；check_pdf 13 门全过；pytest 72 passed
- PDF 断言 v4：TOC 二级定章页（level-1 是部不是章）+ 5.9pt 字号带，六章标签全命中（A0 p985…A5 p1073）
- 题花 45 用字对 sans-regular woff2 cmap 直查零缺字；prose_guard --single 六章预算全绿（零文本改动）

### Status

[OK] **Completed**

### Next Steps

- 用户过目 R5b 后的六枚题花（Phase 7 验收面：文字 11 点 + 全套重绘题花）
- 教训入档：bbox 断言须含线段×矩形/文字相交类；题花文件名必须匹配章节 slug；多文件误传 prose_guard 会触发成对比较假红

## Session 18: 书级趣味性批 1（C 篇抽象基础 8 章）

### What Happened

- 续用任务 `10-27-book-interest-polish`（书级语义，非 AI 面 deepen）。三槽位全书扫描：回扣 grep 恰中六试点=已闭环（P2 实质早由先前润色轮完成，仅复选框未勾）；`> 🎯` 钩子覆 117 文件；非试点收尾（S6/C1 抽查）止于成就清单无回扣 → H1 成立（约 88 章缺槽 2+3）
- 批 1 = C0/C1/C3–C8（PRD 批次序「抽象基础」居首，8≤10）：每章「先跑起来」插押注句、「你做到了」插「回到开场」回扣段，纯散文，不改标题/围栏/行内码/事实 token
- 基线：`.temp/cbatch-orig/` 8 枚（pre-batch）；`.temp/pilot-orig/` 6 枚为会话起点态（pre-pilot 基线早于本会话、不可从 git 重建——P3 报告以槽位位置清单服务抽评）
- 方法论收敛（prose_guard compare 假红教训的推广）：插入文本自带 **0 反引号 span、0 阿拉伯数字 token**（裸中文数词/裸标识符安全，C8 全净为证），守卫即零违规；C4/C6 fence 后双空行一并修正

### Testing

- prose_guard --single ×8：口癖预算全绿（——·散文 1–2、一句话 0、记住：0、下一站 1）
- prose_guard compare ×8 vs `.temp/cbatch-orig/`：不可动清单全部一致（零事实 token 漂移）
- 净增字数：+0.9%～+3.1%（上限 12%）；docs:gen 86/86；reading:check 78 篇 ±40% 内；docs:build ✓；pytest 72 passed
- 印前重排（build_print/check_pdf/PDF 断言）按 PRD 推延至试点文本定稿验收，本轮文本级全绿

### Status

[OK] **Completed**（P4 批 1）

### Next Steps

- 用户抽评 ≥2 章（试点 + 批 1）后开批 2；候选：B 篇构建工具或 S 篇外设
- implement.md P3 第四项（用户抽评）与 P5 待验收后勾选
- 保留勿清：`.temp/pilot-orig/`、`.temp/cbatch-orig/`

## Session 19: 书级趣味性批 2（B 篇构建工具 7 章，整篇槽位闭环）

### What Happened

- 用户「继续改进优化」授权批 2。全书缺口扫描（83 章有先跑起来+你做到了双锚，回扣 grep）：缺槽分布 S17/E12/rt-thread8/freertos8/G9/B7/AI6；AI 篇属 deepen 验收面不动
- 批 2 = B0–B6（B7 已是试点），补完后 B 篇 8 章槽 2+3 全覆盖；含两枚长章 02-elf、03-linker-script
- 槽 2 押注逐章对准本地判分锚点（B1 三行关键数字、B2 入口地址差一、B3 两份 bin 尺寸、B4 单步计数、B5 队尾大户、B0 目录清单、B6 停机才可写）；槽 3 回扣开场框架逐章换结构（那句/那笔/那位/那本/那对），落实批 1 记下的反模板约束
- 插入延续零 token 方法论（零反引号 span、零阿拉伯数字、零破折号），守卫首跑即全绿零返工

### Testing

- prose_guard --single ×7 口癖全绿；compare ×7 vs `.temp/bbatch-orig/` 不可动清单全部一致
- 净增 +0.9%～+2.7%（上限 12%）；docs:build ✓；pytest 72 passed；reading:check 78 篇；links:check 157 链接
- 印前重排仍按 PRD 推延至文本定稿验收

### Status

[OK] **Completed**（P4 批 2）

### Next Steps

- 剩余缺口：S 篇 16、E 篇 12、rtos 两支 16、G 篇 9、AI 篇 6（AI 篇待 deepen 验收后再议）；批 2 选批时已按全路径核对、AI 篇明确排除在 deepen 验收面之外
- 批 3 候选：S 篇（章数最多，含两枚超长章 14-pwr、16-debug-hardfault）
- 保留勿清：`.temp/bbatch-orig/`（批 2 基线）

## Session 20: 书级趣味性批 3（S 篇外设开段 S1–S9）

### What Happened

- 用户「同意继续」授权批 3，按建议走 S 篇；S10-dac 已是试点，本批取连续 9 章 S1–S9（≤10 上限），S11–S17 留批 4
- 槽 2 押注全部本地可判分或上板即时可判：S1 三住户谁住外设街（CPUID）、S2 默认版跑哪个钟（内部钟）、S3 共阳写低才亮、S4 门牌落在五到十之间（六）、S5 LOAD 减一、S6 动 CCR 频率不动、S7 波特率错一格出乱码、S8 计数器减到零跳回、S9 十二刀半格以内；B4 教训落实：每章菜单先核正文答案锚再落笔（S1 特意先 grep PPB/口诀行）
- 槽 3 回扣开场继续换框架（那一口你押谁/那一口替你判了/那一口就是第一课/门牌是六/押减一的那口/动 CCR 的那一口/乱码那一口的账/跳回去那一口/半格以内的那一口），零模板复制
- 顺手修一处存量口癖：S3 :33「BSRR 一句话发令」→「一声令下」（快照原件即报预算超 1，compare 2→2 证明非本轮引入；修后 2→1）

### Testing

- prose_guard --single ×9 口癖全绿；compare ×9 vs `.temp/sbatch-orig/` 不可动清单全部一致（零事实 token 漂移）
- 净增 +1.4%～+1.9%（上限 12%）；docs:build ✓（46.62s）；pytest 72 passed；reading:check 78 篇；links:check 157 链接
- 印前重排仍按 PRD 推延至文本定稿验收

### Status

[OK] **Completed**（P4 批 3）

### Next Steps

- 批 4 候选：S 篇尾段 S11–S17（7 章，含超长章 14-pwr、16-debug-hardfault）；之后 E 篇 12、rtos 两支 16、G 篇 9
- 保留勿清：`.temp/sbatch-orig/`（批 3 基线，9 枚合计 91000 字符）

## Session 21: 批 3 去模板化 + 书级美感诊断

### What Happened

- advisory 指出 S 批 17 处同框架（先押一口 ×9 + 那一口 ×8）；用户同步反馈「还是不够好看美观优秀」。先修模板：18 处开头重写为 9 个零重复框架（押个名字/押个数/押一题/先猜一把/出个选择题/三个答案押一个/押个结局/押个现场/押个精度），回扣起句全部脱离「那一口」句式（S4 原本非模板未动）
- 零 token 纪律全程保持（菜单仍含正确答案、零阿拉伯数字/反引号/破折号）
- 干区抽查 S2/S4/S5 中段：S4 链路节有角色拟人与归属故事、S2 六步每步带死法后果、S5 有「阴险」「第 50 天前后必爆」——中段非干区，无需补刀；文字面美感短板确认为开头模板（已修）
- 美感下一杠杆定位：题花丰富度。100 枚 chapter-art 尺寸分布 min 475 / p25 1301 / 中位 1562 / p75 1790 / max 2585（初记 101 枚 max 156769 为 wc total 行伪影，Session 22 修正）；对照 R5 范本带 1900–2600B，章题花低于 1200B 的有 10 枚（gd32-08、c-07、build-02-elf、build-03-linker-script、rtos-freertos-06/07、esp32-00-env、stm32-17-watchdog-reset、lab-e01-blink、stm32-06-tim）；附录类题花薄属正常，不计

### Testing

- prose_guard --single ×9 全绿；compare ×9 vs `.temp/sbatch-orig/` 不可动清单全部一致；「先押一口/那一口」全书 S 批零残留；净增回落至 +0～+1%
- docs:build ✓（36.97s）；pytest/reading/links 同批复跑（Session 21 交付时引用结果）

### Status

[OK] **Completed**（批 3 修正轮 + 诊断）

### Next Steps

- 美感主建议：题花重绘批（10 枚薄弱章题花，复用 R5 管线：SVG 重绘入 1900–2600B 范本带 → 白底光栅 :img 视觉核验 → art_guard/anim-lint → 印前断言），或先批 4（S11–S17 文字槽位）
- 保留勿清：`.temp/sbatch-orig/`（批 3 基线）

## Session 22: 章首题花接入网页版（advisory 验证 + 实现）

### What Happened

- advisory（concern）证实闭环：docs/ 全站题花此前零渲染（唯一 grep 命中是 ai/05 命令表格文字提及）。实现走 anim 同款构建期内联：config.mts md 规则按 env 相对路径 slug（stm32/06-tim.md → stm32-06-tim）读 mcu-book/book/assets/chapter-art/<slug>.svg，存在即以 html_block 注入 H1 之后（镜像印前「标题 → 题花」相邻关系），缺失静默跳过，feTurbulence/<filter 硬门与 build_html.py chapter_art_html 同口径；无组件、无 public 拷贝、单一事实源
- custom.css 加 .chapter-art（max-width 460px 居中、margin -0.25rem auto 0.6rem）+ --cover-ink 双主题令牌（浅 #123b33 / 暗 #a3c4b9）；资产 SVG 本就写 stroke/fill="var(--cover-ink, #123b33)"，内联进 DOM 后变量穿透，深浅两套自动适配（<img> 引用穿不过 CSS 变量边界，故必须内联）
- 覆盖率：94 书文件 94 枚题花全命中（A–F 附录图不映射 web URL，仅印前用）；dist 94 页含 chapter-art、各 index 页零残留、位置紧随 </h1>
- perf 预算第四次上调（有据）：反事实构建（临时关注入）实测题花对搜索索引贡献仅 +7.0KB raw / +1.9KB br（94 枚 SVG 共 1479 字符文本以二元组令牌入索引，整串不入正文）；无题花索引 4090.9KB raw / 710.5KB br 本已双超 10-13 校准限（4050/690）——超限为 10-13 以来正文增写累积，非题花引入。largestChunkBr 690→760、searchIndexRaw 4050→4400，注释注明实测与归因

### Testing

- docs:build ✓（94 页注入）；perf 全绿（shell 139.7/140、largest 712.3/760、index raw 4096.5/4400）；search 2113 标题 / a11y 131 页 / reading 78 章 / links 157 / pytest 72 全过
- 浏览器受控核验（重启后 preview）：浅/暗墨令牌翻转 rgb(18,59,51) ↔ rgb(163,196,185)、H1 下间距 16.2px、460px 居中（centerOff 0）、375px 移动端宽 295px 无横向溢出

### Status

[OK] **Completed**（网页版题花从零渲染到 94 章全覆盖）

### Next Steps

- 二选一待用户定向：A）题花重绘批（10 枚薄弱章题花入 1900–2600B 范本带，复用 R5 管线）；B）批 4 文字槽位 S11–S17（7 章，含 14-pwr 21.2k、16-debug-hardfault 18.7k）
- 未动 docs/ai/05-this-book-pipeline.md（deepen 验收面禁止混入）；保留勿清：`.temp/sbatch-orig/`
- 工具教训 ×2：①wc -c 输出的 total 行会混进统计（count+1、max=总量），分位数须先剔除再算；②vitepress preview 的 sirv 静态索引不随 dist 重建刷新，重建后必须重启 preview，否则新哈希 CSS 404、页面全裸——曾误判为 CSS 编译失败，curl 直打服务端 404 后定位

### 追记：advisory 复核——搜索索引污染修复（同日）

- 采纳一条（concern 属实）：题花 `<text>` 标签经 renderSearch 进了索引正文——tim 首节 token 表抓到 ccrcnt（CCR/CNT 剥标签后熔接成伪 token）、数越/过阈/→ 等题花独有 token；违反 search-render.mjs 头部「不索引 SVG 序列化数据」的自有契约。修复：renderSearch 在剥 `<pre>` 旁增剥 `<div class="chapter-art">…</div>`（资产零 foreignObject，非贪婪截断安全）
- 验证：剥后 ccrcnt 全索引消失、数越/过阈只剩 esp32 散文合法命中、tim 首节 57→48 token 全为正文词；索引原文 4098.1 → 4091.1 KB（≈关题花反事实 4090.9，题花贡献归零）；94 页注入不回归；search:check 2113 标题 ✓；perf 全绿（711.5/760、4091.1/4400）；perf-budget 注释同步修正并补摊比核算（索引字节/正文字节 2.14 → 2.13 不升反降，超限确为正文增长 1,740,970 → 1,964,854 B）
- 排查方法记档：MiniSearch 序列化索引是 `[token, {field:{docId:…}}]` 对数组（dist chunks/@localSearchIndexroot.*.js 内 `const t='…'` 包装），可 node 解析做章节级 token 归因；ASCII 探针要防熔接（ccrcnt）、CJK 探针用题花独有二元组（数越/过阈，全 docs 散文 grep 反证）
- 其余 advisory 判定：陈旧 preview/构建期内联/TEMP 守卫恢复/917 实测值/工具用法五条均已于前轮闭环或经本轮复核不成立（守卫行在位、917 已是实测值、transformPageData 方案与已交付内联同效），无动作

## Session 23: 题花重绘批闭环（10 枚薄弱章题花入范本带 + 字体子集陈旧性修复）

### What Happened

- 三波重绘 10 枚薄弱题花（原 1020–1193B、共 11209B）入 1900–2600B 范本带：波 1 stm32-06-tim 2395 / c-07-ub-misra 2273 / build-03-linker-script 2187；波 2 build-02-elf 1974 / esp32-00-env 2414 / lab-e01-blink 2183；波 3 gd32-08-mtime-delay 1984 / rtos-freertos-06-notify-event-timer 2213 / rtos-freertos-07-heap 2252 / stm32-17-watchdog-reset 2067。每枚保原标签语义（mtime/mtimecmp/MTIP、任务通知/TCB 邮箱、heap_4、喂狗/迟到即复位……），叙事升维：TIM 军刀三刃、ELF 解剖台+readelf 放大镜、idf.py→USB→小板首次对话、BSRR 位卡点灯+1Hz 方波、电表跨限 MTIP 小旗、纸飞机直投邮箱+大叉划掉排队信封（不排队不拷贝）、内存条墙溶解合并+malloc 大件入位、喂狗环+迟到时钟→复位键
- 每波验证链：art_check 标签 ⊆ sans cmap（新入域 $ idf.py/你好/红/任务A/IWDG/malloc/空闲/释放 全 NONE）→ art_guard 100-0 → mkview 白底光栅（:img 对透明底线稿画黑布，工具坑沿用）→ 视觉模型逐要素核验。波 1 揪出 CNT 与小闪电仅 4px 间距，CNT x 66→58 修复后复核通过；heap 首稿 1463B 未入带，补邻格空闲标注+墙溶解碎屑+malloc 收尾后 2252B
- A4 印前门暴露字体子集陈旧性：check_pdf 字体门新挂 IAAAAA+SimSun（首见 p197）。归因：全书仅 2 处 10pt 正文（'窥' build/06-flash-debug.md:171、'喘' stm32/06-tim.md:277，均为批 1–3 押注/回扣句），subset woff2 生成早于该批散文落字（域 2147）。修复＝按 provenance 原规格重跑 subset_fonts.py（9 支、2147→2153），重建 PDF 后门复绿——非管线改动，纯数据滞后
- PDF 题花断言 v5（.temp/art_pdf_assert_rbatch.py）：get_toc 定位章页（章号前缀 S/C/B/P/V/F + 实验 E01）+ 字号带 5.0–8.6pt 判据，10 章标签全命中（5.9–6.8pt），承 v3/v4 拒空洞证据教训

### Testing

- art_guard 100 枚 0 违规 / anim-lint 109 全过 / docs:build ✓ / docs:check ✓（137 md、244ms）
- build_print：1171 页（+3 为重绘后回流）、185.3×260.3mm、5 支字体全 Type0 具名；check_pdf 13 门「印前契约：全部通过」（含字体门复绿）
- pytest 72 passed（字体重生成后复跑）；PDF 断言 v5 10/10 PASS

### Status

[OK] **Completed**（A 题花重绘批全绿闭环；波批快照 `.temp/rbatch-orig/` 保留勿清）

### Next Steps

- 批 4 文字槽位 S11–S17（7 章，含 14-pwr 21.2k、16-debug-hardfault 18.7k）——等用户过目 A 面后进入
- 工具教训：①todo `done` 传 items[] 会静默整表标完（已报 xd://report_issue，workaround＝rm 后重建，done 只用单数 task）；②glob 200 条结果上限会藏住根级 package.json/anim-lint.mjs，根目录发现用 ls/find；③print/fonts/ 在 mcu-book/print/ 下而非 mcu-book/fonts/（glob 缩进层级易误读）

### 追记：跨模型 advisory 批量复核（同日，A 批收尾后）

- 11 条迟到回执逐条对照，9 条系已闭环事项的重复通知（SimSun 归因链/子集九条配方含 Cascadia 轴向钉死/断言章前缀实测/glob 截断改 ls/todo items[] bug 已上报），无增量动作
- 1 条现场验证：重绘是否保留 `role="img"`+`aria-label`（art_guard 不查、a11y-check 只管 `<img alt>`，grep 是唯一判据）——10/10 双属性在位，aria-label 语义完整非空壳（如 stm32-17「喂狗循环箭头围着小狗和骨头转；若迟到时钟走过点…」），读屏输出无回归
- 1 条采纳为后续实践：视觉核验提问避免逐项念出预期画面（模型顺向确认偏差）；波 1 CNT×闪电 4px 险撞系提示式提问下仍命中的实例，下次题花批至少一枚改零提示提问

## Session 24: 批 4 文字槽位缩编落地（S11/S12 两章精准手术，五章 no-op）

### What Happened

- B0 盘点+advisory 复核推翻原案七章插花：五王已湿（S13 直性子/顶出/三道防呆、S14 押注回扣书挡 14 条、S15 单向门、S16 法医体系、S17 反例自带「狗永远不叫」落点），全批插花=增重不增趣。终版缩编：主刀 S11 L205–280（总线卡死恢复+DMA，七章唯一整段干区）+副刀 S12 L188–204（分频+DMA 节）；S13–S17 no-op。快照 `.temp/b4-orig/`
- S11 四拍（17891→18386 字节，+1.0%）：①总线卡死开篇茶话会拍（主持人中场晕倒、客人半字悬嘴边）②九脉冲拍 ③DMA 拍（主人亲自递话 vs 帮手端整盘字节按节拍往 DR 放）④TC 括注（帮手放空盘子≠最后一个字已出口）。S12 一拍（18981 字节 +0.2%）：移位环=全场最不用盯的员工，时钟一响必然换位，递料交 DMA
- prose_guard compare 抓到真问题：S11 首稿合并句掉事实 token `9个`×1（原句「9 个时钟」「9 个脉冲」两处，改写只留前者）→ 原句 verbatim 保留+比喻句追加其后，复绿。fact_tokens 多重集全等判据有效防 token 漂移
- 工具坑：edit 的 `PUT 208.<:` 语法无效（正确 `PUT <208:`），流式预览失败连带中止同批并行 edit；同文件插入行与上一段间需手动补空行否则粘连成段

### Testing

- prose_guard --single：S11 ——散文 2/2、S12 1/2，一句话/记住 散文 0 ✓；compare ×2 不可动清单全部一致 ✓
- 字符域：新增字（S11 专于倒刚嘴客宣布帮悬敲晕杯然爬盘端补请递 / S12 响盯递）全 ⊆ serif cmap NONE missing → 子集无需重跑
- docs:check 137 md ✓ / docs:build 33.21s ✓ / pytest 72 passed
- build_print+check_pdf：1171 页、185.3×260.3mm、印前 13 门「全部通过」、体量 ×1.05

### Status

[OK] **Completed**（B 批 4 缩编全绿闭环；快照 `.temp/b4-orig/` 保留勿清）

### Next Steps

- 10-27-book-interest-polish 任务收口候选：批 1–4 全闭环，等用户验收后可归档
- 教训：todo `done` 按注册文本匹配——门序随缩编收窄不改 todo 挂名文案，按原文案勾毕

## Session 25: 批 5 文字槽位落地（E 篇 esp32 13 章押注/回扣闭环）

### What Happened

- C0 干区定位：书级散文抛光剩余 E/G/F/R/lab 五片；按 Session 21 排队批 5 = E 篇。E 篇 14 章中仅 02-gpio-matrix 已有押注/回扣书挡（押结果/开场锚），其余 13 章（00/01/03–13）全 0/0 → 整篇槽位闭环。基线快照 `.temp/ebatch-orig/`
- 13 章 × 2 拍：押注落「先跑起来」quick win 段后（00 无该节、落「第一步」节头后），回扣落「你做到了」清单后 `<div class="achievement">` 前。押注框架 13 式全新互不重复（押出身/押一棒/押方向/认内鬼/押一层/押分家人/押闲差/押趟车大站/押没省掉的/押一笔/押份遗产/押数量级/押盲区），避开 S 篇 9 式与 02「押结果」；回扣起句 13 式零重复（出身揭晓/你押的那一棒/方向押完翻底牌/内鬼就是/字节睡在/分家人是/闲差押中了/大站点完名/没省掉的是/断电判分的结果/遗产清点/带宽对完账/不叫的原因）
- 判分锚点全部取自各章 quick win 可观测量：rst:0x1 ROM 第一棒、sdkconfig/sdkconfig.h 双形态、helper 半截链、ring buffer 中层、DC 分家人、硬件 fade 闲差、六状态大站、add_peer 登记、NVS 断电计数、RTC 遗产、精髓带宽算式、TWDT 出勤≠产出
- 零阿拉伯数字（防 fact_tokens 多重集漂移）+ 零破折号 + 零行内代码三条纪律。compare 首跑抓到 08/09 插入散文带反引号（行内代码 41→43 / 64→65 段违规）→ 去反引号改裸词（init/add_peer）复绿；事实 token 13 章零漂移。净增 +1.2%～+5.4%/章，均 ≪12%
- 字符域：6 字全书首见（乖勤卒谜跪鬼＝乖乖/出勤/小卒/猜谜/第一个跪/内鬼）出 serif cmap → 按 provenance 九支完整口径重跑 subset_fonts.py（2153→2159）。工具坑两枚：①CLI 静态字体轴向须留空 `Family|source||output`，provenance 记录的 "static" 是输出格式不是输入格式；②脚本 docstring 示例只列 2 支 serif，全量口径以 provenance.json 的 fonts/charsFrom 为准（部分重跑会因 emoji/符号并集缺字退码 1）

### Testing

- prose_guard --single ×13：——散文 0–2/2、一句话/记住 散文 0，全部预算内 ✓；compare ×13（vs `.temp/ebatch-orig/`）不可动清单全部一致 ✓（08/09 行内代码修复后复跑）
- subset 九支重跑：2159 字、乖勤卒谜跪鬼 union NONE missing、provenance.json 已登记
- docs:check 137 md / 331ms ✓；docs:build 39.48s ✓；pytest 72 passed（28.76s）
- build_print+check_pdf：1173 页（+2 回流）、185.3×260.3mm、5 支可嵌入轮廓字体、印前 13 门「全部通过」、体量 ×1.05（509s）

### Status

[OK] **Completed**（E 批 5 全绿闭环；快照 `.temp/ebatch-orig/` 保留勿清）

### Next Steps

- 批 6 候选（Session 21 排队）：rtos 两支（F 篇 freertos / R 篇 rtthread）→ G 篇 gd32 → lab；等用户验收 E 批后推进
- 10-27-book-interest-polish 批 1–5 全闭环，归档与否待用户拍板

### 评审轮追记（外部模型反馈处置）

- 采纳修复 ×2：01/04 押注拍原落点横在冒号引导句与其表格/console 之间（「这是本章最实用的调试入口：」「下面是本机实测：」）→ 纯移位至冒号段之前（01 押注 L43→L41、04 L47→L45），文本零改动；双章 --single + compare 复跑绿（零 token 漂移、不可动清单一致）
- 采纳认知：prose_guard 有 `--additions`（compare_additive，tools/prose_guard.py:180/226）＝纯插入轮专用门，只拒原文全文未见的新 fact token、允许复用章内数字与新增行内代码；本批已按更严的 compare 多重集全等收官不回改，批 6 起纯插入轮应改用之
- 拒绝 ×1：「恢复 10/12/13 被剥数字」——16MB（10 你做到了 bullet）、500ms+2000ms（13 bullet）就在回扣上方一行，12 算式由押注指向精髓行，写回＝与相邻 bullet 冗余，且须把已全绿的严格门降级为 additions 门
- 后验 ×2：全书押注框架 grep 清单（B/C/S 篇各 7 式 vs 本批 13 式）零碰撞；「那一口/回到开场」回扣起句在 13 章零命中（既有 11 处全在 C 篇×8、esp32/02、gd32/01、stm32/10）
- 过期 ×4：subset 九支全量口径（已按此执行且全绿）；批 5=E 篇结构槽位方案（与实际一致）；fat_scan 密度 pass；docs/rtos 21 md 递归计数——后两条记为批 6 候选研判依据
- 移位后重建 docs:check/build + build_print/check_pdf，保持源与产物一致

## Session 26: 批 6 文字槽位落地（rtos 两支 16 章押注/回扣闭环）

### What Happened

- C0 盘点：rtos 两支 17 章中 F03-scheduler 已有嵌入式书挡（押下一次亮灯属于谁 + 回到那帧被冻结的 tick）跳过，16 章 × 2 拍 = 32 处；基线快照 `.temp/rtos-orig/`（17 文件 4540 行）
- 事实核验先行：F01 首行日志=high（main.c 先建 low 后 high、vTaskStartScheduler 才启动）；F00/F05/F07 剧透规避三案（F00 押注前移至首个 c 块栅栏后、F05 弃押真凶改押解药机制、F07 弃押邻居改押空闲链表合并接头）；R 篇押注主打双 OS 对照角（嫁妆/平线/翻译官/名册/落点/乡音）与 F 篇单内核观察角区分
- 押注 16 式全新（死活/头一行/响不响/睡法/解药/首付/接头/房东/辈分/嫁妆/骨架数/平不平/翻译官/名册/落点/乡音）+ 回扣起句 16 式零重复；全部锚定 quick win 可观测量、判分依托本章精髓、零新事实
- C2 抓到 F00/F02「一句话」散文口癖 3 处——orig 快照同样失败证实为原文本既有（非本批引入），按全书口癖纪律保义改写：一句话判据→判据只有一条、配置文档里的一句话→只写在配置文档里、核心动作一句话→核心动作只有一步；行内代码/链接/加粗逐字保留，--additions 复跑绿
- 字符域：4 新字（乡炮羊衔）九支首见 → 按 provenance 完整口径重跑 subset_fonts.py（2159→2163）
- 工具坑：自写字符检查首版 int/str 类型错配假报 1299 字全缺（t.cmap 键是 int，与 str 字符集合相减恒空）——改 ord() 码点比较后真相为 4 字真缺；教训：对账脚本先小样本对拍再信结果

### Testing

- prose_guard --single ×16 预算内（——散文 0–2/2、一句话/记住 散文 0）+ --additions ×16 vs `.temp/rtos-orig/` 不可动清单一致 ✓；净增 +0.8%～+2.5%/章 ≪12%
- 框架后验：32 短语全书唯一（F05 实际句式「解药先押下」），F03 既有书挡保持 1 不受扰
- subset 九支重跑：2163 字、union 2273→2277、乡炮羊衔 missing NONE、provenance.json 已登记
- docs:check 137 md/315ms ✓；docs:build 39.85s ✓；pytest 72 passed（31.15s）
- build_print：1173 页、185.3×260.3mm、5 支可嵌入轮廓字体、大纲 802 条；check_pdf 印前 13 门「全部通过」、体量 源文 849,411 / PDF 894,002 字（×1.05）

### Status

[OK] **Completed**（批 6 rtos 16 章全绿闭环；快照 `.temp/rtos-orig/` 保留勿清）

### Next Steps

- 批 7 候选（Session 21 排队）：G 篇 gd32 → lab；等用户验收批 6 后推进
- 10-27-book-interest-polish 批 1–6 全闭环，归档与否待用户拍板

## Session 27: 批 7 三面改进闭环（G 篇文字修复 + 题花全量验证 + 动画审计修复）

### What Happened

- 文字：G 篇 9 章 --additions 复核抓 2 处事实值违规——G00 版本号「15.2.1」（印前不可核验的浮值）删除改「行李是零」工具链复用叙述、G06「各最多 16 级」（NVIC 记忆惯性串到 CLIC）删除改 level/priority 两维拆解 + 0x5FA 钥匙句；两章 compare_additive 复跑「不可动清单：全部一致」
- 插图：题花线收口——100 枚 chapter-art 全量 art_guard（御舆模式）0 违规；AI 三张（00/01/02）生产件确认已含评审终态（02 的双向箭头分左右两段+中间镜片对勾、「实测」为板内丝印），art_check 标签缺字 NONE；rbatch 10 枚重建后 PDF 断言 10/10 PASS
- 动画：按规范跑提交前必查 `--font-scale 1.10`（CI Linux 字体模拟）抓到 struct-alignment ④ 页脚行出界（x=36 起本地宽 ~650，×1.1 右缘 751>720）——删冗余从句「；位域只在工具链固定时用」（阶段面板正文 L89 已有同义句「工具链不固定就别拿它罩硬件」），纯删字符零新字；基线 + 1.10 复跑双绿
- --dots 34 张压字明细逐项判级（审计明言不计失败）：gpio-config 绿灌色/值格子均画在字后（desc 明言设计意图）、rtt-finsh-dispatch 终端块光标压命令行（有意光标画法）、esp32-driver-layers 飞行块 z 序修复注释在案（字画块后）——均非缺陷；esp32-ota-rollback 投票区 10×6px×2 时刻擦边不足半字，记录跳过
- 工具坑：todo 工具 done op 误标（传单项却标 5 项、随后 start 报 Missing task content）已上报 xd://report_issue，init 重建后续用

### Testing

- G 篇：--single 9/9 预算内、--additions 9/9 vs `.temp/gbatch-orig/` 不可动清单一致、18 押注/回扣短语全书唯一、新字符 ⊆ 2277 并集（本批纯删零新字）
- 动画：anim:lint 109 ✓、anim:audit 基线 109 ✓、--font-scale 1.10 109 ✓（修复前 1 张失败）
- 全量：docs:check 137 md ✓、docs:gen 86/86 章 + 109 动画、docs:build 44.74s ✓、pytest 72 passed（35.63s）
- 印前：book:pdf 1173 页 185.3×260.3mm、5 支可嵌入轮廓字体、大纲 802 条（478.5s）；check_pdf 印前 13 门「全部通过」；体量 源文 850,999 / PDF 895,461 字（×1.05）
- art_pdf_assert_rbatch：10/10 PASS（S6/C7/B3/B2/P0/V3/F6/F7/S17/E01，标签字号 5.9–6.8pt 在 5.0–8.6pt 带内）

### Status

[OK] **Completed**（批 7 G 篇 + 插图 + 动画三面全绿闭环；`.temp/gbatch-orig/` 与 `.temp/rbatch-orig/` 保留勿清）

### Next Steps

- 批 7 三栏汇报用户验收；后续候选 G 篇 → lab 线（Session 21 排队）
- 10-27-book-interest-polish 批 1–7 全闭环，归档与否待用户拍板

## Session 28: 押注泄题修复轮（advisory 审计 + 5 章押注/回扣重写）

### What Happened

- 外部 advisory 疑点：G 篇章头押注（预测问句）被紧邻脚手架（结构表行/动画标题/引导段）直接作答 = 泄题。逐章判级 9 章：G00（表行一「编译旗逐字相同」作答行李问）、G03（表行一/二「0 起编号」「CTL0/1/2」逐字作答）、G05（表行三/四「没有 CPACR」「没有硬件两读」断言半问）、G06（动画节 ECLIC 两维 + 表行二「16 level + 16 priority」作答拆维问）、G07（动画节泄露 4MHz/绕 PLL1/×27/108M 路线数）→ 5 处坐实必修
- 拒修/保留判定：G08 advisory 证据不成立；G02（动画标题「AF 复用的 16 选 1 选择器」）、G09（「RISC-V 点灯闭环」）中性不泄；G04 表行「TRNG 等独有」泄枚举半问但「等」留活口、SDIO 分频器半问未泄 → 保留不修（半修比多修更差的反向同理：全修同类坐实项，误报不凑数）
- 修复策略：表格属不可动清单（--additions 保护）→ 只改押注散文不改表；泄题判据 = 断言直接答案，只列主题（「中断号地图｜总线归属」式）不算。每章换到未泄半问，且 qw 前文同步复查（G00 qw L38「同一组编译旗」只答旧注不碰新注）
- 5 组新押注/回扣（bet 换问 + 回扣同步换「对答案」锚）：G00 开箱单（三件套谁管向量表/谁拉 200MHz/谁划地盘）↔ 开箱对上；G03 排门牌（8 对 6 独有三名字、八路总线归属）↔ 门牌对上（USART5/UART6/UART7，USART0 与 USART5 挂 APB2 其余 APB1）；G05 工序单（搬 .data/清 .bss/调 SystemInit/进 main 的指令拼写）↔ 工序单对上（ldr/str → la/lw/sw）；G06 两扇门（shv 置 1/置 0 各进哪扇、0x5FA 认不认）↔ 两扇门对答案（硬件直跳/公共入口 mcause 分发/钥匙不认）；G07 算盘（25 的什么性质卡死直分、绕 PLL1 每步凑哪个数）↔ 算盘对上（25 是 5 的倍数 4 不是，÷ PREDV1_DIV5、×8、再 ÷ PREDV0_DIV10）
- 审计中抓到 G07 表行一「0x04 陷阱与消失的 PLL 寄存器」会泄候选押注（0x04 偏移住户/四位域）→ 弃 0x04/PLL 半问换 25-性质问；新 fact token 逐词核基线计数（USART6 在 G03 原文 0 次 → 全文不出现；裸 40/10 不安全 → 用 ÷ PREDV1_DIV5 原形）；唯一域外字符「岔」→ 改「两扇门」

### Testing

- 泄题复查（本轮验收核心）：5 章新押注 vs 全部前置脚手架（qw/动画节/结构表）逐行核对——G00 表行三只列三件套名单不派分工、G03 表行三只标「总线归属」主题、G05 表行二只承诺对照表、G06 行二「向量/非向量」行五「shv 模式」均主题级、G07 表行三只承诺「推导」不给 5 的倍数论证；0x5FA/三个独有名/门派分配/5 的倍数在全部脚手架零断言
- prose：--single 5/5 预算内（——散文 ≤2、一句话/记住 0）、--additions 5/5 vs `.temp/gbatch-orig/`「不可动清单：全部一致」+ 事实 token ⊆ 章原文
- 唯一性与字符域：10 新短语（开箱单/排门牌/工序单/两扇门/算盘 + 五个「对上」起句）全书各 1 次；G 篇九式开场互不重复；5 文件全文字符 ⊆ 2277 并集
- 全链：docs:check 137 md ✓、docs:gen 86/86 + 109 动画 + 47 工程、docs:build 42.70s、pytest 72 passed
- 印前：book:pdf 1173 页 185.3×260.3mm、5 支可嵌入轮廓字体、大纲 802 条（450.8s）；check_pdf 印前 13 门「全部通过」；体量 源文 851,390 / PDF 896,024 字（×1.05）
- art_pdf_assert_rbatch：10/10 PASS（TOC 动态定位章首页，页移免疫；实测页码未动，S6 p281…E01 p933 原位）

### Status

[OK] **Completed**（5 章押注泄题修复全绿闭环；G01/G02/G04/G08/G09 未动；快照 `.temp/gbatch-orig/`、`.temp/rbatch-orig/` 保留勿清）

### Next Steps

- 连同批 7 一并汇报用户验收；归档 vs 批 8（G 篇 → lab 线）待拍板

## Session 29: 批 8 E 篇「先猜」装置落地（lab 线 8 章 + 预存违规修复）

### What Happened

- 审计：E 篇 8 章章头引语/收尾段已生动（E04 火星探路者剧本、E06 偷电贼算账在），表格功能性强；缺口是 8 章零「先猜」预测时刻。S4（nvic-exti L42「敲回车之前，先猜一把…丢了直觉才丢分」）与 P2（gpio-matrix L92）已有单点惯例，E 篇应复用此心理装置而非发明新体系
- 设计：每章「原理一句话」节尾加一段押注（约 50 字），问句全部瞄准**留在读者板子上的答案**（数量级/误差/听感/两 OS 谁离理论近），预期现象/理论时间线/步骤只给定性或理论值——泄题在结构上不可能，无需逐章回扣段；答案锚即各章「实测记录」表。index.md 使用规则补第 2 条信条「上板前先猜一把」引用 S4 收句作全系列座右铭
- 8 组起句各异（改参数前先猜/抓包前先估/上探头前先猜/烧录前先押一注/换挡前先猜/上电前先押一记/动手前先猜/开播前先押耳朵），答案落点各异（秒表/光标/探头读数/串口日志/波形/万用表/串口/喇叭）
- 抓到并修复 e04 预存口癖违规：思考题 2「查资料补一句话」触发「一句话·散文 1 处 > 预算 0」（快照复跑坐实为存量、非本批引入），改「查资料补一行」
- 字符域预检抓到「咔哒」域外（2277 并集）→ E08 弃拟声词改「周期性的还是随机的」；token 预检：25%/6000/2500/10kΩ/1kΩ/1g 全部在章原文（1g 靠 L47 image alt）

### Testing

- 泄题复查：8 注 vs 各章章头引语/预期现象/步骤逐条核对——E01 无倍率、E02 无帧宽、E03 明文不预填误差、E04 理论值≠实测值+OS 对比未断言、E05 无陡度比、E06 只说「明显下降」、E07 预期现象只覆盖加速度计、E08 明文不宣称缓冲临界值 → 全部留给板子
- prose：--single 9/9（e04 修复后）；--additions 9/9 vs `.temp/ebatch-orig/`「不可动清单：全部一致」+ 事实 token 合规
- 唯一性与字符域：9 新起句 grep 全书各恰 1 次；9 文件全文字符 ⊆ 2277 并集
- 全链：docs:check 137 md ✓、docs:gen 86/86+109+47、docs:build 44.24s、pytest 72 passed
- 印前：book:pdf 1173 页 185.3×260.3mm、5 支可嵌入轮廓字体（454.4s）；check_pdf 印前 13 门「全部通过」；体量 源文 851,787 / PDF 896,305 字（×1.05）；art_pdf_assert_rbatch 10/10 PASS（E01 p933 原位，E 篇增量吸收在页余量内）

### Status

[OK] **Completed**（批 8 E 篇先猜装置全绿闭环；`.temp/gbatch-orig/`、`.temp/rbatch-orig/` 保留勿清；`.temp/ebatch-orig/` 为本批基线，内含早前会话的 esp32 件勿动）

### Next Steps

- 批 8 汇报用户验收；10-27-book-interest-polish 批 1–8 闭环，归档与否待拍板

### 修复轮追记（同 session，advisory 复审触发）

- 外部审计抓到真缺陷：8 条押注与原理句之间漏空行，Markdown 懒延续会并成一段，与 G 篇「押注独立成段」惯例不一致 → 8 章各补 1 个空行
- 验证途中踩检查器 bug：段落判据 `endswith('</p>')` 的 40 字符回看窗口把押注自身的开标签 `<p>` 也吞进去，对一切独立段恒 False；bg_78 repr 定案分隔符实为 `</p>\r\n<p>`（text 模式读取归一成 \n 后修正判据 `("</p>\n<p>"+b) in html` 即过）——中途两次 ✗ 均为假阴性，磁盘内容早已正确；「陈旧落盘/僵尸管线」假设均被 mtime 与 md5 证伪
- 终验：print HTML 8/8 独立段；站点 HTML（docs/.vitepress/dist/lab/，此前误判为「无 lab 页」——只搜了 mcu-book/dist/，advisory 指正后补验）8/8 独立段；PDF 文本块层 8/8 独立块（p934/939/944/948/955/961/965/969，前块尾均为原理句收束）；prose --single/--additions 8/8 复跑；docs:check 137、docs:gen 86+109+47、docs:build 34.1s、pytest 72 passed；book:pdf 1173 页（518.9s）；印前 13 门全部通过（PDF 896,448 字 ×1.05）；art_pdf_assert_rbatch 10/10 exit=0（E01 p933 原位）
- advisory 其余两条核销：docs-check.mjs 实在仓库根 scripts/（npm 从 mcu-book 跑解析无碍）；E 篇 integrity 复核 8 注零未实测断言（6000/2500 明标「理论账」、25% 引步骤 2 手算值）——无需改动

## Session 30: 批 9 S 篇后半「先猜」装置落地（stm32 11–17 七章）

### What Happened

- 审计升级：批 8 后用户令「继续找下一面」。装置覆盖盘点发现此前的 grep pattern 漏检多种形态——单字「押|先猜|赌一把」漏「押个数」（S02）与「下注」（S10 L29 已有）；扩到「预测|遮住」又发现 B07 L27「先预测再执行」、G01 L25「先遮住下文结论…算完再往下读」也已有装置。真缺口收敛为 S 篇后半 7 章：11-i2c / 12-spi / 13-flash-iap / 14-pwr / 15-spl-anatomy / 16-debug-hardfault / 17-watchdog-reset
- 全书覆盖图景（正文成稿章，剔 index/报告/模板）：C 9/9、P 14/14、F 17/17、B 7/8→8/8（B07 误判修正）、G 9/10→10/10（G01 误判修正）、S 9/17→16/17（S00-env 环境章除外全满）。剩 ai 5、projects 2、rtos compare 2、S00 留批 10 候选
- 设计（S 篇「押定再读」型，答案留在章节后文）：每章 quick win 节末加独立押注段，半问瞄准该章最有反直觉张力的事实，全部避开章头精髓/板卡事实/动画节此前已断言的角度——S11 页边界绕回、S12 移位环收发同拍、S13 先解锁先擦除、S14 Standby 后主/备份 SRAM 谁记得、S15 库 vs 手写体积、S16 addr2line 报行是真凶还是邻居、S17 WWDG 喂早同样复位
- 起句家族扩容 7 个新 lead（落点后改归宿/交换/顺序/失忆/体积/真凶/喂养），与既有 40+「押个X」成员全书唯一

### Testing

- 预检抓两起撞车：「先押个落点」已存在于 R6 L38 → S11 改「先押个归宿」；字符域「熬」「勤」不在 2260 字子集 → S14 改「撑过长夜」、S17 改「越频繁越稳」
- prose：--single 7/7、--additions vs `.temp/ibatch-orig/`（本批基线）7/7「不可动清单：全部一致」；7 注零裸数字、fact token ⊆ 章原文、口癖零
- 四层独立段：md 层空行隔离 7/7；站点 HTML（docs/.vitepress/dist/stm32/）7/7；print HTML（`("</p>\n<p>"+bet)` 判据）7/7；PDF 文本块 7/7（p345/358/372/385/405/417/434 均以押注句起头）
- 全链：docs:check 137 ✓、docs:build 39.4s（含 gen）、pytest 72 passed；book:pdf 1173 页 469s、5 支可嵌入轮廓字体；check_pdf 印前 13 门全部通过（源文 852,369 / PDF 897,245 字 ×1.05）；art_pdf_assert_rbatch 10/10 exit=0（S17 p433 题花原位）

### Status

[OK] **Completed**（批 9 S 篇后半 7 章先猜装置全绿闭环；`.temp/ibatch-orig/` 为本批基线保留勿清）

### Next Steps

- 批 9 汇报用户验收；批 10 候选：ai 5 章、projects 2 章、rtos compare 2 章、S00-env；装置形态盘点法（多 pattern 防漏检）已沉淀本 session


## Session 31: B站合集搬运 18 条 + 抖音台账收口（10-16 解锁后续）

### What Happened

- 用户令「继续上传抖音b站建合集」。先跑 bili-health 归属表：18 条视频系列已全部在「STM32」合集（9411799/小节 10536952，第 46–67/67 位，10-25 前后另一条线挂入）——10-16 PRD 的前提（站内无归属）已过时。新建空合集「通往单片机之路」9435811（小节 10566117，封面/简介已挂）后向用户拍板，用户选「搬进新合集」（与抖音 mix、小红书合集同名同口径；STM32 回归纯章节品，其简介本就写「几十秒短讲不收在这里」）
- 契约踩坑三连（均有独立证据）：① episodes/add body 必须 camelCase（sectionId + episodes[{aid,cid,title,charging_pay}]，csrf 走 query）——snake_case 会被静默忽略仍返回 code=0（biliup season.rs / DanmakuRender / hnucjx technical.md 三源一致）；② 稿件已属他季时 add 返回 code=20080 拒绝 → 不支持直搬，必须先 del 再 add；③ del 走 form id=<episode_id>&csrf，episode_id 是小节条目 id 非 aid，从 GET season/section?id= 的 episodes[].id 拿。bili-API-collect 仓库 2026-01 因律师函清空，契约只能靠生产实现源码
- 执行：c3-volatile 单条试点（del→add→member 端验证）通过后批量 17 条（逐条 del + 一次 add 保序）。批量后校验全挂经查是校验脚本自身 off-by-one（c3 试点占 l2[0]，17 条应从 l2[1] 起对位），非服务端伪象——权威端复读顺序严格系列顺序（episode_id 230360723→230360837 递增），脚本已修正；s5 抖音评论与计划源全文 diff 仅「49 天 vs 49.7 天」一处（224/226 字），台账按实措辞不写「逐字一致」
- 抖音收口：s5 评论核实已发（cid=7698991097133728562 at=2026-10-21T05:42Z stick_position=0），补登台账；f5+s5 并入待置顶清单（现 19 条全部未置顶，置顶只能 App 长按）

### Testing

- member 端：新小节 10566117 恰 18 条顺序=series.json；旧小节 10536952 剩 49
- 公共端（PRD 验收门 bili-health.mjs）：18/18 逐条回显「通往单片机之路 第k/18条」k=1..18 顺序正确；view.ugc_season 是公共缓存，写后验收必须用 member 端 season/section，公共端只作最终传播确认
- video/publish/bili-collection.mjs join 子命令已修为 camelCase 契约并注释防再踩

### Status

[OK] **Completed**（10-16-bili-season-after-unlock 验收闭环：合集建成+18 条挂载+逐条回显；抖音 19 条台账/评论全核清，仅剩 App 手工置顶）

### Next Steps

- 用户 App 手工置顶 19 条（清单 .temp/douyin-run/待置顶清单.md）
- ai4fw 视频（10-28 任务）未渲染未发布，不在本轮范围


## Session 32: 批 10 收口（rtos compare 2 + S00-env 押注）+ 印前终验

### What Happened

- 批 10 补齐最后 3 章「先押再读」装置：rtos/compare/00-side-by-side（对表之前先押个左右舵）、compare/01-choose（走树之前先押个站位）、stm32/00-env（动手之前先押个分工）。AI 5 章与 projects 2 章经审计已有装置，不动。
- 三注均为独立段、零阿拉伯数字、零反引号、零「——」；新字符全部落在书稿字符并集内（「岔」不在域，01-choose 改「顺着树往下走」）；起句全书唯一（避开既有「先押个方向」「先押个落点」「押个数」「下注」家族）。
- 手法：延续「半问 + 答案在后文」——compare 两章分别押「优先级方向换不换边」与「四样全占的树落点」，S00 押「谁翻译、谁送进芯片」，答案分别在总览对照表、场景树与记忆锚点节。

### Testing

- prose：--single 3/3 预算内（破折号 ≤2、一句话 0、记住 0）；--additions vs `.temp/jbatch-orig/` 3/3「不可动清单：全部一致」且无新增 fact token。
- 站点链：docs:check 137 md ✓、pytest 72 passed、reading:check 78 章 ✓、docs:build 43.80s ✓；站点 HTML 三注均独立 <p>。
- 印前链（本轮重建）：book:pdf 1174 页（paged 267.5s，源文 853,183 / PDF 897,973 字 ×1.05）；寡行守卫检查 326 断点回移 43（整块 5）；check_pdf 13 门全部通过；art_pdf_assert_rbatch 10/10 PASS。
- PDF 文本块层：PyMuPDF 定位三注 3/3 独立块（p211 / p642 / p649，均为正文段落块，非并入上下段）。

### Status

[OK] **Completed**（10-27-book-interest-polish 批 1–10 全部闭环；`.temp/jbatch-orig/` 为本批基线保留）

### Next Steps

- 用户验收批 10；任务归档待拍板。
- 视频侧转入 10-22-video-v2-remaster Wave C（s14/s16/s2/s4/s7），首集 s2-rcc。


## Session 33: Skill spec 收口提交与归档：卡片产线、导读入口及 PPT 复验

**Date**: 2026-11-05
**Task**: Skill spec 收口提交与归档：卡片产线、导读入口及 PPT 复验
**Branch**: `feat/video-v2-remaster`

### Summary

完成推荐 A 卡片布局、30 张正式素材、同源导读与过期门、锚点误报修复及 13 页 PPT 复验；质量门通过，按确认计划提交并归档，既有工作区修改保留。

### Main Changes

### Changes

- 正式化 29 张竖版金句卡与 1 张横版封面：源码/共享 CSS/渲染与检查命令归入 scripts/social-cards，正式 PNG/摘要/联系表放 video/assets/social-cards/book；主句与小注保持接收基线，内容组间距 36px，横版封面字节不变。
- 精排导读从 docs/reference/book.md 同源生成，接入站点书籍入口；源文/生成器/HTML 摘要由 docs:build 前置检查。修复 VitePress 对独立 HTML 的路由拦截、hero 标题配色继承与旧附录笔误。
- pages-check 屏蔽 script/style 里的伪 href，保留真实错误行号；新增回归测试。传播资产可执行契约与复盘已落 .trellis/spec/docs-site/presentation-assets.md。
- 旧 PPT 13 页复验通过，含观众屏同步/宫格/备注/计时/遮屏/重连/排练/标注/自动翻页；2 条既有版式警告保留解释。

### Validation

- npm run quality 全绿：122 项单元测试、47 工程、111 动画、138 Markdown、132 构建页、2616 锚点链接、2116 可检索标题。
- Python 72 passed；导读 390px/1440px 两项浏览器回归通过；29 卡文字/来源/边界/间距与 30 图摘要/尺寸通过。
- 本轮提交不改变被验收的代码或素材字节，未重复跑整本 PDF。

### Completion

- 用户回复「继续下一步」确认提交计划，三项 work commit：afd543f、08d0c3c、696c194。
- 任务已归档至 .trellis/tasks/archive/2026-11/11-05-skill-remaster-closeout（归档提交 eae36b1）。
- 旧任务 13 张 PNG、未跟踪 PPT、旧 spec 与联系表混合修改保持工作区，未并入本轮提交；未推送远端。
- 用户审美终验、平台投稿、guizang-voice 旧文样本仍独立延期。其他 Trellis 任务未作状态变更。


### Git Commits

| Hash | Message |
|------|---------|
| `afd543f` | (see git log) |
| `08d0c3c` | (see git log) |
| `696c194` | (see git log) |

### Testing

- 已完成 quality（122 项单元测试）、72 项 Python 测试、2 项导读浏览器回归、30 图资产与 PPT 全链路验证，详见本节 Validation 与归档任务 research/verification.md。

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 34: ai4fw 视频号发布

**Date**: 2026-11-05
**Task**: ai4fw 视频号发布
**Branch**: `feat/video-v2-remaster`

### Summary

视频号 ai4fw 已发表；短标题空格修正、声明原创弹窗确认、视频 ID 与台账落盘；小红书账号异常，用户指示停止上传/评论，置顶评论未发送且不再重试。

### Main Changes

- 视频号 ai4fw 发表完成：`wx.mp4` 上传，描述/短标题/封面/位置/标注/声明原创按用户确认落表；列表状态「原创审核中」，视频 ID `export/UzFfBgAAxLiJNGsvWCOPk8zT4DCaHweWiuhuxnNDBuHhb1nJ_g`。
- 新增 `.temp/ai4fw-wx.mjs`：隐藏 file input 直塞、`insertText` 描述、浮层 Esc、标注读 `.select-display`、封面直塞隐藏 image input、`--go` + `.temp/wx-run/I_HAVE_USER_OK=ai4fw` 闸门、发表后台账。
- 修正 `video/publish/copy-ai4fw.md`：短标题中文逗号被平台判特殊字符，改为空格；声明原创需在「原创权益」弹窗勾协议再点「声明原创」。
- 任务 `10-28-social-video-ai-tools` notes 记录发表状态与小红书账号异常停止指令；台账 `wx-ledger.jsonl` / `ai4fw-published.txt` / `wx-posted.txt` 已写。

### Validation

- `node .temp/ai4fw-wx.mjs --resume` 三次：描述/短标题/位置/标注/封面/声明原创全部读回，短标题无红字校验错误。
- `node .temp/ai4fw-wx.mjs --go --resume` 退出 0，点发表后跳转 `post/list`。
- 列表页第一张 ai4fw 卡片：369 描述、原创审核中、2026-11-05 20:59；视频 ID 由「复制视频ID」读回。
- 封面预览截图为 `douyin-cover.png` 的 369 画面；位置=不显示位置、合集未选、链接未选、活动不参与、不定时、标注=无需标注。

### Completion

- 四平台发布链：B站、抖音、小红书早前已发；视频号本轮已发。
- 小红书账号异常，用户 2026-11-05 指示停止上传/评论；置顶评论只填了 264 字未发送，已删除 ai4fw 的 xhs 发布/评论闸门，不再重试。视频号原创审核状态需稍后复查；本轮记录随任务提交，未推送 git。

### Next Steps

- 稍后刷新视频号列表，确认原创审核状态。
- 小红书不再执行上传/评论/合集/编辑动作；保留已发布内容，不删除/不改。


## Session 35: B3/B4 第三批提交与发布交接

**Date**: 2026-11-07
**Task**: B3/B4 第三批提交与发布交接
**Branch**: `docs/language-b3-b4-release`

### Summary

用户确认按计划提交并发布；755ff3f仅含B3五行、B4三行与配套日志。两章strict prose_guard、78章prose、78篇reading、138文件docs及task context本轮实际通过；源码等于此前已构建版本，八个验证输入SHA不变。task_verify仍unverified/project-or-git-baseline-unavailable。仅归档本批任务，11-02用户工作42文件已固定哈希。独立分支PR门禁全绿后再锁定head合并并核实部署，远端结果尚待。

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

| Hash | Message |
|------|---------|
| `755ff3f` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete
