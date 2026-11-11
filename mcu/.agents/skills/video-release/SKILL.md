---
name: video-release
description: 把 video/out/<ep>/ 的成片投到 B站（横版）、抖音（竖版）、知乎（横版视频）、小红书（竖版笔记）四条线，并处理补字段、改简介改封面、查状态、置顶评论这些平台侧动作。用户说"投稿/发布/上线某集"、"补 B站分区标签封面"、"简介里露出反引号"、"抖音七项核对没过"、"知乎一直回 10000"、"小红书草稿停在哪一步"、"先填表等我点发布"时使用。这套线的难点不是接口而是判断：哪一步不可逆、放行凭什么、失败信号读哪个。工具全在 video/publish/，本文件只讲判据与入口，细节以各平台台账为准。
argument-hint: <episode-id>
---

# 视频投放：B站 / 抖音 / 知乎 / 小红书

## 0. 动手前先确认的四件事

1. **这一集在账上是什么状态**——`node video/publish/bili-ledger.mjs`（B站）；抖音看 `.temp/douyin-run/<ep>-published.txt`；知乎看 `.temp/zh-run/<ep>-published.txt`；小红书看 `.temp/xhs-run/<ep>-published.txt`（草稿留痕在同一个目录，但**草稿不等于已发布**）。**没有留痕就当没投过，有留痕就当投过了**，判错的代价都是重复稿。
2. **闸门文件只能来自对话里对这一条的点头**。各平台都认 `.temp/<平台>-run/I_HAVE_USER_OK=<ep>`，内容是人类那句原话。脚本不许自己造，也不许"用户上次同意过批量发"就推断这次也算。
3. **公开批量投稿每次都要单独授权**。一集一次授权；同一条重跑不等于第二次授权。
4. **台账先读**。`video/publish/douyin-plan.md`、`video/publish/zhihu-plan.md`、`video/publish/xhs-plan.md` 里是实测结论（含"哪个入口已经不可用"、"这条草稿停在哪一步"这类会过期的事实），本文件只讲不会过期的判断。

## 1. 五条红线（踩过才写下的，别绕）

- **不可逆动作前那道闸不许跳。** 抖音的 `verify`、B站的 check、知乎的表单状态栏，都只读页面不写字。历史上 f3 连两次在发布前 0 秒崩，就是因为把 `verify` 做成了可跳过的一步。小红书那条线连发布本身都还没自动化——别把"顺手补上"当成收尾，得先有用户点头和实测证据。
- **`FORCE_RESUBMIT=1` / `FREE_RESUBMIT=1` 只在用户明说之后用。** 不加就直接跑，重复稿会真发出去。
- **一集的字只从 `video/episodes/<ep>/episode.json` 和 `video/out/<ep>/` 来**，脚本里不写字面量。缺字段就停手——抖音的 `publish.douyin.declare`（自主声明）没填就是必填项没满足，不替这一集猜。
- **绝不在 CDP 连接上调 `browser.close()`。** 四条线共用 `D:/Users/mcu/.temp/douyin-profile` 起的那个有头浏览器（9223），close 会把浏览器一起带走，登录态要重新验。临时探针只 `page.close()`，靠进程退出断开——**但小红书那个常驻页本身就是登录现场，探针一律自己开新页，谁都不许关它**（关掉的后果见 §6）。
- **凭证不进 stdout，不进仓库。** B站工具统一丢弃含 `SESSDATA|bili_jct|access_token|refresh_token` 的响应；cookie 文件在 `C:/Users/zhugu/tools/biliup-rs/` 下，仓库外。`.env`、credentials 一类永不提交。

## 2. 一集走完全程

### B站横版

```sh
sh video/publish/bili-one.sh <ep>
```

填表 → 点「立即投稿」→ 用 API 补字段，退出码不参与判定：**看 `.temp/bili-web-run/<ep>.bvid` 有没有落**。落了就只补字段绝不重投（`add/v3` 曾 code=0 之后被代理掐断，脚本非零但稿已出去）。

- API 通道投稿撞 **21566**，浏览器是唯一发得出去的路，所以点按钮也交给脚本。
- 只想补字段：`node video/publish/bili-cover-edit.mjs repair <BV> video/out/<ep>/bili-submit.yaml`
- 只填不发（人工点最后一键）：`sh video/publish/bili-prepare.sh <ep>`，步骤 `open→feed→wait→fill→tagsync→cover→setmore→check→descdiff`。
- 投稿参数生成：`node video/publish/bili-submit.mjs [--desc=full|short] [--title-style=punchy|series] [--dry]`。

### 抖音竖版

```sh
node video/publish/dy-post-one.mjs <ep>            # 全流程，核对不过就停在发布前
node video/publish/dy-post-one.mjs <ep> --from=publish   # 断点续走，绝不重传片源
```

七项核对（标题 / 描述首句 / 双封面 v+h / 合集 / 两项检测 / 可见性=公开 / 自主声明）全过才去看闸门文件；核对没过退出码 2，闸门缺失退出码 3——**这两种都不许改成"跳过"**。单步排查用 `node video/publish/douyin-step.mjs <verb> --ep <ep>`（`--ep x` 与 `--ep=x` 都认；缺 `--ep` 直接报错，不回落默认集）。

置顶导流评论：`node video/publish/douyin-pin.mjs --ep <ep>` 默认只探，带 `--go` 才真置顶；判据只看评论列表里出现「置顶」且挂在自家那条上。

### 知乎

```sh
node video/publish/zh-one.mjs --ep <ep>            # 只填不发，打核对
node video/publish/zh-one.mjs --ep <ep> --publish  # 仍要闸门文件
```

- **成功只认弹窗「发布成功 / 感谢你的第 N 篇创作」**，页面 URL 不变，别拿跳转判成败。
- **失败的权威信号是 `POST /api/v4/content/publish` 的响应体**（`.code` + `.toast_message`）。HTTP 200 也可能带着 error；只看状态码会把"服务端拒了"读成"前端拦住了"。
- 点完一个非 GET 请求都没发出去 = 前端拦下，去读表单状态栏。
- **回读状态这条路不可用**：`creations/v2/zvideo` 返回的是 `type:"pin"`（每条视频旁同步发的那条想法），不是视频本身。

### 小红书竖版笔记

```sh
node video/publish/xhs-daemon.mjs                      # 起常驻有头窗口，登录在这里发生
node video/publish/xhs-step.mjs status --ep=<ep>       # 只读：这一集现在走到哪一步
node video/publish/xhs-step.mjs open --ep=<ep>         # 打开 publish 表单（竖版视频那条）
node video/publish/xhs-step.mjs upload --ep=<ep>       # 喂 video/out/<ep>/douyin.mp4，内部等 30 秒
node video/publish/xhs-step.mjs fill --ep=<ep>         # 填标题正文（超限或有站外地址 → 退出码 2）
node video/publish/xhs-step.mjs topics --ep=<ep>       # 打话题再接弹层，成 chip 才算数
node video/publish/xhs-step.mjs cover --ep=<ep>        # 只读：把封面面板的结构和文案量下来
node video/publish/xhs-step.mjs coverset --ep=<ep>     # 喂自定义封面，停在裁剪页不点应用
node video/publish/xhs-step.mjs coverapply --ep=<ep>   # 点「完成」，封面才落定
node video/publish/xhs-step.mjs comment --ep=<ep>      # 网页版自家笔记页：把置顶评论填进评论框，不发
node video/publish/xhs-step.mjs comment --ep=<ep> --go # 加 --go 且写好 I_HAVE_USER_OK_COMMENT=<ep> 才真发这条评论
node video/publish/xhs-step.mjs collection --ep=<ep>   # 编辑页选合集，到"选中"为止，不点提交
node video/publish/xhs-step.mjs collectioncheck --ep=<ep>   # 只读：认领编辑页→重载→核验那一行=合集名（批后抽样用这个，别用一次性探针）
node video/publish/xhs-step.mjs collectioncreate --ep=<ep> --desc=<简介>   # 建合集并加入（闸门 I_HAVE_USER_OK_COLLECTION=<合集名>）
node video/publish/xhs-step.mjs collection --ep=<ep> --go   # 换/挂合集并点提交（闸门 I_HAVE_USER_OK_SUBMIT=<ep>；坐标点击+回读落盘）
node video/publish/xhs-step.mjs attach --ep=<ep>       # 发布表单上把合集选好——发出去时一并挂上（不点提交，不要闸门）
node video/publish/xhs-step.mjs publish --ep=<ep> --go # 点发布（闸门 I_HAVE_USER_OK=<ep>；判据 URL published=true，权威核对在笔记管理）
sh video/publish/xhs-batch.sh <ep> [<ep> ...]          # 逐集跑完七步表单+挂集+发布，任一步非零即停，闸门逐集检查
```

`measure` 是量字段上限用的探针步——**别在正经稿件上跑，它会把测试字写进标题和正文**。

- **发布动作已自动化，但始终逐集放行**：`publish` 要闸门 `I_HAVE_USER_OK=<ep>`（内容=对话里对这一条的点头原话）**且**加 `--go` 才点；默认（没 `--go`）只回显闸门然后退出码 3。判据是点完 URL 变 `?source=&published=true`；权威信号仍是笔记管理「已发布」——批量上传时批后统一跑一遍核对。
- **点那颗按钮的姿势**：`<xhs-publish-btn>` 是 closed shadow 自定义元素（文本扫不到、`getByText` 点不中、`elementFromPoint` 只回宿主），但**真实鼠标在宿主 rect 内坐标点能命中内部按钮**（2026-10-17 章节批与 F5/S5 换集各验一次：rect `220,744 680x90` → 点 `(560,789)` → 回读「更新成功」）。别用 `_onPublish` 硬触发（绕过前端校验）。
- **平台不替我们拦超限**：标题 39 字喂进去 `input.value` 还是 39，计数器只印成「39 / 20」，拦的是提交。所以断言写在本机侧——`fill` 先按码点断 标题 ≤20、正文 ≤1000，任何字段出现 `http(s)://` 或 `github` 字样就退出码 2 停手（口径见 §4）。
- **成功只认笔记管理 `/new/note-manager` 的「已发布」标签里有这条**（「审核中」「未通过」两个标签同时应当是空的——落在审核里不等于发出去了）。发布后表单 URL 会变成 `?source=&published=true`、草稿箱归零，但那是**事后信号不是回执**，别拿它写判据。本机侧的账是 `.temp/xhs-run/<ep>-published.txt`；草稿留痕也在同一个目录，**草稿不等于已发布**。
- **回读观众侧文案这条路暂时不可用**：笔记管理里点标题只会选中，弹出的标签页不导航到详情页。所以"有没有漏地址"要在**发布前**用编辑器正文逐字比（`.temp` 下的一次性脚本即可，别把判据留到发出去之后）。
- **评论只在网页版发得出去，创作者中心没有评论区**（十项导航里没有任何评论项，数据看板只报「评论数」；笔记行上那个「置顶」图标置顶的是**笔记本身**不是评论）。链路是 `/explore` 顶栏的 `a[href^="/user/profile/"]` → 主页按标题找到带 `xsec_token` 的卡片 → 笔记页，**token 每次现取别抄存**；未登录 `www` 域时直连笔记页会吃 `error_code=300031`。`comment` 步默认只填不发，`--go` 走的是**另一个闸门** `I_HAVE_USER_OK_COMMENT=<ep>`——别拿发布那张闸来放评论。
- **「置顶这条评论」在网页版做不到**：自家评论的「…」菜单里只有「删除评论」，整页扫不到「置顶」二字（2026-10-17 量完四条证据见 `xhs-plan.md`）。所以这一条线**没有 `pin` 步**，跟抖音同口径——置顶只能在 App 里长按。以后谁想补，先量到入口再写代码。
- **合集：选中不落盘，落盘要提交**。`collection` 步从笔记管理认 tooltip「编辑」进 `/publish/update`（**认领按标题框逐字**——开着的编辑页不一定是这一条的，实测踩过；笔记管理是虚拟列表，`claimEditPage` 会先缩小再三种滚动扫卡，2026-10-17 加）；选中后重开页面会回落「选择合集」，要落盘得点那颗 `<xhs-publish-btn>`（`collection --go`，闸门 `I_HAVE_USER_OK_SUBMIT=<ep>`）。落盘判据=**重开编辑页那一行仍显示合集名**，不认 toast（toast 偶发读不到）；随时复查用只读的 `collectioncheck --ep=<ep>`。两个实测坑：入口分两态（没挂时 `.collection-plugin-button`、已挂时它消失、换 `.collection-plugin-choose`）；`is-publish=true` 的提交可能把笔记拉回审核（S5 被拉回、几分钟后回「已发布」；F5 没有——平台不保证，提交前要预期）。**新发的稿子在发布表单上就有「加入合集」**（`attach` 步），选好再发比发完回编辑页补一遍省事。

## 3. 平台的"没做成"分别长什么样

| 信号 | 真实含义 | 该做的 |
|---|---|---|
| B站 `21566` | API 投稿风控，不是内容问题 | 走浏览器 `bili-one.sh` |
| B站 `21011 / 21015 / 21001` | 覆写式 `web/edit` 缺 `videos[]` / 缺 `filename` / 写成 `tags` | 从 `bili-editbox.mjs` 的 view 回读重建 payload |
| B站 `-702` | `vupre` 连打的限频，不是权限 | 隔 1.5s、退避重打（已有 5 次） |
| B站 `20082`「合集个数太多」 | **权益中心 Lv2 权限位没开**，文案是伪装；`seasons total=0` 就是证据 | 别刷额度；用 `bili-level.mjs` 读 `archive/white` 的 `season/new_season` |
| B站 编辑后 `state=-6` | 只是改动复审，观众侧 `view` 仍 `state=0` | 用 `bili-public-check.mjs <BV>` 复核（吃 BV 号，不吃集号） |
| B站 `desc_format_id=9999` | 回读值，不是异常 | 忽略 |
| 抖音 点发布后页面原地不动 | 十有八九是自主声明没选 | 补 `episode.json` 的 `publish.douyin.declare` |
| 抖音 `流量减少`＋`批量发布违规或低质内容` | 一天多条进低质池 | 1 天 1 条，最多 2 条 |
| 知乎 `code=10000` 频率过高 | **账号级滚动窗口**，从账号最后一次成功发布起算，"24小时"是低估 | 窗口没过别再点——被拒的尝试本身可能刷新窗口 |
| 小红书 计数器印成「39 / 20」但字都还在 | 平台**不在 DOM 上限高**，超限只标红，真正拦在提交那一步 | 别信"看起来通过了"；`fill` 的前置断言没过就是没过，改稿件不改断言 |
| 小红书 正文里的 `#词` 显示成黑字 | 纯文本 `#` 不是话题，只有输入 `#名字` 后弹出来的那条候选被接住才成 chip | `topics` 步用回车接弹层；**不许用 locator 点候选**——先匹配到的正是刚打进正文的那串黑字 |
| 小红书 封面点了没反应 | 「设置封面」那四个字只是标题，入口是默认封面缩略图本身（三层才到 file input） | 先 `cover` 量结构，再 `coverset` 喂图、`coverapply` 点完成 |
| 小红书 点评论框报 `intercepts pointer events` | 「评论」那条占位与 `p.content-input` 是同 rect 的兄弟，占位盖在上面 | 先点 `.engage-bar .inner-when-not-active` 换到输入态，再敲字（`comment` 步已这么写） |
| 小红书 合集选完、重开页面又变回「选择合集」 | 选中只是表单状态，不提交不落盘；且选中后 `.collection-plugin-button` 那个类会消失（换 `.collection-plugin-choose`） | 判据读 `.collection-plugin-wrapper` 整行文本；落盘用 `collection --go`（闸门+坐标点击+重开核对）；新发的稿子在发布表单上直接 `attach` 再发 |
| 小红书 点发布页底栏中心没反应 | 底栏是「暂存离开 429..549｜发布 573..693」两颗按钮（flex 居中、gap 24），宿主 `<xhs-publish-btn>`（rect 221..901）的正中心 (561) 正好落在**两颗中间的空隙**上 | 用 CDP `DOM.getDocument(pierce:true)` + `DOM.getBoxModel` 量内部「发布」那颗的真实盒（驱动里的 `findPublishButtonBox`），别点宿主中心 |
| 小红书 上一步的弹层还挂着，下一步点击超时 | 一次实验遗留的 `d-modal-mask` 在拦 pointer events | 驱动已把 `coverset` 做成幂等（见到 file input 直接喂）；手工救援前先看有没有遮罩，别急着 reload |

## 4. 字怎么出去（简介与文案）

- **B站简介按 `white-space:pre-line` 纯文本渲染**（实测页面 `pre`/`code` 元素数为 0）。```` ``` ````围栏、`` ` ` ``行内码、`**粗体**`都会原样露给观众。发布稿本身仍是 markdown，脱标记发生在平台边界：生成期 `bili-submit.mjs` 的 `plain()`，历史稿件用 `node video/publish/bili-desc-fix.mjs`（默认 dry，`post <ep>` 才发；只许脱标记——把标记以外的任何差异当异常，宁可不发）。
- **抖音描述里不提站外**，导流只放置顶评论（2026-10-14 定的口径）。
- **小红书整条线都不出现站外地址**（2026-10-17 用户口径）：标题、正文、置顶评论里连 `http(s)://` 和 `github` 字样都不许有——我们自己站点上那个 github.io 地址，从小红书这边看同样算站外。导流只说「全网同名：通往单片机之路」，复现命令用 `sh code/...` 这种纯文本形式。断言写在 `fill` 里，不靠人记。
- 长正文只走文件不走命令行：`bili-cover-edit.mjs` 的取值支持 `desc=@路径`。

## 5. 运行态与产物分别在哪

| 种类 | 位置 | 注意 |
|---|---|---|
| 集序与字段 | `video/series.json`、`video/episodes/<ep>/episode.json` | 唯一事实源 |
| 成片与素材 | `video/out/<ep>/`（gitignored） | 重跑产线可再生 |
| 闸门 + 留痕 | `.temp/bili-web-run/`、`.temp/douyin-run/`、`.temp/zh-run/`、`.temp/xhs-run/` | **在 gitignored 目录里**：清 `.temp` 前先备份，否则重复稿防线和"这条发过没"的账一起没了 |
| 常驻浏览器 | `.temp/douyin-profile`（持久 profile） | 由 `video/publish/douyin-daemon.mjs` / `bili-daemon.mjs` / `xhs-daemon.mjs` 起，9223；**小红书那一页是登录现场，任何脚本都不许关它** |
| 平台台账 | `video/publish/{douyin,zhihu,xhs,wx,yt}-plan.md` | `douyin-plan.md` 已改成只追加不重生成；投稿表在 `douyin-plan.generated.md`；`xhs-plan.md` 记的是实测字段上限、封面入口层级、发布成功的判据，以及这条线走到哪一步了 |
| 合集（B站） | `bili-collection.mjs <seasons\|cover\|create\|join\|resolve>` | Lv2 未解锁，见 `.trellis/tasks/10-16-bili-season-after-unlock/` |

## 6. 已知的坑，别重新踩

- **`bili-submit.mjs` 没有单集模式，且默认 `tid=171` 是错的**：跑一次写**全部** `video/out/*／bili-submit.yaml`（18 份），
  而这个系列 18 条线上实际分区全是 **231**（2026-10-17 逐条 GET `vupre/web/archive/view` 对过）。
  所以任何时候跑它都得带 `--tid=231`；不带就把已发布稿件的投稿配置刷成分区错的，将来谁拿它跑 `repair` 就把视频挪了分区。
  平台侧不会因此改动（生成器只写本地文件），所以这个错**只有本地 md5 基线和 view 回读能发现**——
  2026-10-17 就是这么踩的：为看简介长度跑了一次 `--dry` 之外的全量，17 份 yaml 被覆写，靠 `--tid=231` 重生成 + 逐条回读才收干净。
- **知乎「继续发布」横幅可能挂着别的会话的草稿**，点之前逐字比对标题前 60 字。
- **入口 URL 不许拼**，只从页面 `<a>` 里找。知乎 `/upload-video` 一类入口会失效，重跑第一步是把入口重新点出来。
- **共享浏览器上的标签页会被人关掉**。多集连投必须按集认领标签页身份（`douyin-step.mjs` 用 sessionStorage 盖章，B站用 `__biliEp`），别按"第一个平台页"选页——那等于给上一条稿件填下一条的字。
  小红书编辑页同理但更土：`/publish/update` 开着的不一定是这一条（实测 F5 那步复用了 S5 留下的页、把别人的合集行当自己的读），所以 `claimEditPage` 按**标题框的值逐字**认领，不是同一个标题就另开。
- **发布页底栏是两颗按钮，点中心无效**：`<xhs-publish-btn>` 宿主 rect 221..901 的正中心落在「暂存离开」（429..549）与「发布」（573..693）中间的空隙上——2026-10-17 首次点发布就这么白点了一次。正路是 CDP `DOM.getDocument(pierce:true)` 穿透 closed shadow、`DOM.getBoxModel` 量内部「发布」那颗的四边形（`xhs-step.mjs` 的 `findPublishButtonBox`）。
- **SPA 带未保存改动导航会弹原生 confirm**，不接住就撞 playwright 的竞态自动处理（`ProtocolError: No dialog is showing`，2026-10-17 两次）。xhs 的编辑页与探针统一挂 `dialog` 监听、一律接受。
- 抖音竖版/横版两张封面都得走模态流上传；`slot` 那条喂的 `input[type=file]` 左边那个是「生成参考图」，直接喂会让封面退回视频第 0 帧。
- **常驻页一关，登录就白扫**：小红书第一版探针用 `find(p => p.url().includes('xiaohongshu'))` 选页，拿到的正是 daemon 唯一那一页，收尾 `page.close()` 把常驻页带走，node 因 unsettled top-level await 以 13 退出、窗口消失。现在的规矩：脚本自己 `ctx.newPage()`，工作页永不 close，daemon 用 `setInterval` 挂住进程。
- **别用全页正则读计数器**：`document.body.innerText.match(/\d+\s*\/\s*\d+/)` 会把稿件正文里那句「（6000 / 2500）」当计数器读进日志——读数看着对，其实是稿件自己的字。F5 稿件已改成「6000 与 2500」，判据也只认贴着输入框那一条。
- **小红书是 SPA，`domcontentloaded` 时字段一个都还没渲染**，探针 dump 出 0 个输入框不代表页面坏了；先轮询到 `input[type=file]` / `[contenteditable]` / `textarea` 出现再读。
- 改产线脚本后**真跑一遍**才算改完：把工具从 `.temp` 挪进 `video/publish/` 那轮，靠运行才逮到三处相对 import 断裂。
