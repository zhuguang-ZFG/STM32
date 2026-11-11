# YouTube 投稿这条线（2026-10-14 起）

素材用户已定：**两版都发**——长版用 B站那 16 条 16:9 母带，Shorts 用抖音那 16 条 9:16 母带。
账号：用户已有 Google 账号与频道；登录只在他自己那台窗口里做，凭证不进对话、不进仓库。

## 为什么是浏览器驱动而不是 API

本机没有 `yt-dlp` / `googleapis` / `client_secret*.json`，也没有任何 Google OAuth 凭证。
要走 Data API v3 得先在 Google Cloud 建 OAuth 客户端并把 secret 落到本机——那是另一件事，今天不做。
直连可达性实测：`youtube.com/generate_204 → 204`、`google.com/generate_204 → 204`，无代理环境变量。
所以沿用抖音那套：常驻有头 chromium + 专用持久 profile + 分步驱动 + 发布前放行标记。

- 常驻进程：`.temp/yt-daemon.mjs`，profile 目录 `.temp/yt-profile`，CDP 端口 **9224**（抖音是 9223，互不干扰）
- 绝不指向个人 Chrome 的 `User Data`
- 驱动：`.temp/yt-step.mjs <id> <step>`，步骤 `status open drop progress title desc audience vis thumb next save publish`
- 放行：`publish` 之前必须有 `.temp/yt-run/I_HAVE_USER_OK=<id>`，这个标记只能来自对话里的点头

## 已产出的东西

- `.temp/yt-pack.mjs` → `.temp/yt-run/<id>.md`，16 集两版文案各一节（标题 fenced + 描述 fenced）
  - 标题最长 56 字（s14-pwr 长版），全部 < 100 字上限
  - 描述 255–315 字，全部 < 5000 字上限
  - 事实源：`video/series.json` 的 `no` 与 `source` + `episode.json` 的 `publish.bilibili` / `publish.douyin`
- `.temp/yt-cover169.mjs` → `video/out/<id>/youtube-thumb.png`，16 张 1920×1080，198–256 KB（上限 2 MB）
  - 为什么不直接拿 B站封面：产线出的是 **1920×1200（16:10）**，油管按 16:9 裁，右上角那张证据卡会被切掉一角
  - 不改产线：`buildCover` 先查 `ep.cover.sizes[platform]`，喂临时键 `y169` 就出 16:9 画布；`coverU` 取短边，1080 那档不变，所以字号尺度与竖版一致

## 与抖音那条线的三处口径差

1. **导流**：YouTube 描述区可以直挂站外链接，所以站内全文地址（`https://zhuguang-zfg.github.io/mcu/<章节>.html`）与复现命令都写进描述，不再靠置顶评论兜——抖音那条「描述不提、全进评论」的限制是平台特有的。
2. **标题**：抖音作品标题框实测 30 字且**静默截尾**（`video/src/cli.mjs` 已加 lint 护栏）；YouTube 上限 100 字，所以长版可以直接用 B站那条长标题，不用砍。
3. **合集**：YouTube 侧对应物是播放列表，名字同样 16 条共用（`通往单片机之路`），第一条发布时建。

## 两个先说清楚的风险

- **BGM 出处不可证 → Content ID**。`video/src/mux.mjs:5` 用的 `video/assets/ambient-pad.m4a` 是 `4ce4043` 一次性提交进来的，元数据被剥（无任何 tag），当初的源 `docs/video/ambient-pad.wav` 既没进过版本管理、现在磁盘上也没了，所以本机无法证明它是自研还是取自某个素材包。B站没有自动比对所以一直没声；YouTube 有 Content ID，命中就是收益归他人或静音/下架。**处置：第一条先发 unlisted，等版权/Content ID 面板出结论再转公开**，别一上来 16 条全公开。
- **自定义封面要手机验证**。未验证电话号码的 Google 账号在 YouTube 不能上传自定义封面（也不能发 >15 分钟视频）。长版 9–12 分钟，所以这条会直接卡住第一条——登录之后第一件事就是验这个，卡住的话需要用户在账号里完成手机验证。

## 频道现状（2026-10-14 实测）

- 账号已在本窗口登录，channelId `UCC-17pZvrJyC1if8_VW7RyA`，显示名 **Barbar Honma**，订阅 0。
- 原有 2 条与系列无关的旧视频已按用户点名全部删除：`U-VzQHokFyE`（安装视频 5:10，2026-03-18）、`qA2IUCNVOpA`（第1课 How to start a conversation 老外教你说英语 37:17，2023-04-10）。
  删完复查 videos / shorts / 播放列表三个 tab 可见行均为 **0**，频道是干净的。
  （`.temp/yt-delete.mjs` 默认 probe-only、带 `--go` 才点，且每次重数可见行按下标定位——第一条刚被用户手动删掉时它报"不在可见列表里，跳过"而没有误点别的行，这个护栏算验过了。）
- 显示名「Barbar Honma」和系列无关，是否要改成与抖音「本机实跑」同口径，等第一条发出去再定。

## 硬拦路石：未通过一次性验证的账号有【每日上传上限】

2026-10-14 跑到第 8 条时撞墙。现象是**整批停在 `step=DETAILS`、`#next-button` 点了不推进**，看上去完全像脚本时序 bug，实际 Studio 在对话框里（shadow root 内）写的是：
「已达到每日上传数上限。完成一次性验证即可每天上传更多视频，或者你也可以等待 24 小时。」

- 撞上限时上传**不会报错**，而是永远挂在「正在上传…」，稿件进不了 UU——所以前面几轮的 c4 三笔残稿、以及"救草稿时「继续」死灰"，根因都是这一条，不是页面交互。
- 当日实际投出去 7 条（含 2 条 Shorts 与 1 条长版的补投），第 8 条起全被拒。
- 已加护栏：`yt-go.mjs` 塞片后与等上传的每一步都递归 `textContent` 找这句，命中就抛 `QUOTA:…`；`yt-batch.mjs` 看到 `QUOTA:` 立刻整批停手（`quotaHalt`），因为继续投只会攒废稿。
- **取进度文案必须用 `textContent` 递归走 `shadowRoot`**：`innerText` 在 `ShadowRoot`（它是 DocumentFragment）上是 `undefined`，早先用它判"上传已完"永远读成空串，第一秒就误判完成、抢跑点「继续」，白刷 16 次。这是那一批 `step=DETAILS` 空转的第二个根因（第一个是配额）。
- 这一条和「描述里的外链不可点」是**同一个闸门**：Google 一次性验证。用户做完验证，两个限制一起解；不做，就只能按 24 小时节奏分批投。

## 探针顺序（第一条）

1. 用户在 `.temp/yt-profile` 那个窗口里登录 → `node .temp/yt-step.mjs c3-volatile status` 读回 `signedIn`
2. `open` → `drop --file=D:\Users\mcu\video\out\c3-volatile\bilibili.mp4` → `progress`
3. `title` `desc` `audience` `vis=UNLISTED` → `save`
4. 详情页看三件事：能不能传自定义封面（手机验证）、版权面板有没有 Content ID 声明、时长/分辨率识别对不对
5. 结论回来再决定 Shorts 那条怎么发、以及 16 条的批次节奏

## Studio 上传框实测（c3 两条发完之后补记）

这一节全是踩出来的，脚本头部注释也各有一份，这里汇总：

- **四步框的步序不能靠点步条跳**。`#step-badge-0..3`（详细信息 / 视频元素 / 检查 / 公开范围）点上去 `workflow-step` 不变，只有 `#next-button`（文案「继续」）会推进。所以判"到没到可见性"要用**对话框内单选文案本身**，不要用步数——「检查」那一步耗时不定，步数会飘。
- **详情表单在上传到 7% 就已经渲染出来了**，这时候连点「继续」永远走不到公开范围。必须先等 `ytcp-uploads-dialog` 的 innerText 里不再有 `上传中|处理中|\d%`，再开始走步骤。
- **同一页面可能有两套 `#title-textarea` 和两套受众单选**（背景元数据编辑页 + 前景对话框）。所有查询一律以 `ytcp-uploads-dialog` 为作用域，否则写进背景那套，对话框一直报「你需要回答此问题」，「继续」死灰。
- **`ytcp-social-suggestions-textbox` 是 contenteditable**：`keyboard.type` 进不去（读回来还是旧值），必须 `box.focus()` + `document.execCommand('selectAll')` + `execCommand('insertText')`。
- **`tp-yt-paper-radio-button` 不吃合成点击**：`el.click()` 选不中，要 `scrollIntoView({block:'center'})` 后 `page.mouse.click(x+12, y+h/2)`，点完读 `aria-checked` 确认真的选中了。
- **「继续」会在刚答完必填后短暂 disabled**（Studio 自查/自动保存），得等到解禁，最多 30 s；等不到就停手报 `workflow-step`，不硬闯。
- **可见性那一步（`workflow-step="REVIEW"`）的提交按钮是 `#done-button`，文案就是「保存」**（实测可见 60×36）。同一步里 `id="save"` 那个「保存」是 **disabled** 的，而 **`#save-button` 在这一步压根不存在**——早先"隐藏的 #done-button 点不动、只能点 #save-button"那句结论是反的，作废。
  按文案兜底 `/保存|发布|完成/` 会抓到那个灰的 `#save`：一点，对话框关掉、标题说明因为自动保存留下了、**可见性没提交**，稿件停在「草稿」（`oembed` 403，内容列表那行带「— 草稿」）。
  c5 长版 `brE9TNVOrwQ` 第一次就是这么落成草稿的；用 `yt-draft.mjs`（走「编辑草稿」重新回到 REVIEW）点 `#done-button` 后转成不公开列出，`oembed` 回 200。**所以「已保存」这句文案不是证据，那一行还有没有「草稿」二字才是**——两个脚本都在这一步后面加了行核对。
- **`document.querySelector` 不穿透 open shadow root，Playwright 的 CSS 引擎穿透**。探针量不到某个按钮时，先分清是"真没有"还是"在 shadow 里"：要量 shadow 就得递归走 `el.shadowRoot`（`yt-savebtn2.mjs` 是这么把 `#done-button` 量出来的）。
- **`REVIEW` 步页脚那句「检查完毕。未发现任何问题。」就是 Content ID 的结论**，不用另开版权面板。
- **上传中断会自动落成草稿**，oembed 回 **403 = 私享/草稿**（200 = 公开/不公开列出，404 = 已删）。草稿的右侧栏 `ytcp-video-metadata-editor-sidepanel` 里**没有可见性控件**（只有 `ytcp-video-info` / `shorts-content-links-picker` / 字幕 / 结束屏 / 信息卡片），可见性只存在于四步框里。
  「编辑草稿」重新打开的那个框**是能救活的**——之前报「继续」死灰，病根就是上面那条"两套控件没作用域"，不是草稿态本身。`yt-draft.mjs` 走 `视频链接` 页 →「编辑草稿」→ 作用域填表 → 真坐标点单选 → `#done-button`，c5 实测由草稿转成不公开列出成功。
  但**上传中断的那条**（`上传已中断`，行里给「继续上传 / 删除视频」两个按钮）不一样：点「继续上传」是从 0% 重传、不复用已传的字节，所以那种情况直接重跑 `yt-go.mjs` 更省事。c4 的 `KsruyTUrD40` 就停在这里，标题被我早前一次没作用域的写入污染成了 `TEST-A 标题`，删除不可逆、要用户自己在 Studio 点。
- **拿 video id 的稳定路子不是点 Studio 的行**（处理中的行不渲染 `href`、行节点点不动），而是读频道自己的 uploads 播放列表 `UU…`（= 频道 id 的 `UC` 换成 `UU`），递归走 `window.ytInitialData` 取 `n.videoId`；自己登录态下「不公开列出」的稿件同样在里面。投稿前后各取一次快照，差集就是这次的 id；差集 >1 直接报错，不猜。
- **Shorts 必须给 9:16 封面**（1080×1920，`yt-cover916.mjs` 走 `ep.cover.sizes.s916` 那个临时键）。喂 16:9 会被判比例不合规。
- `page.setViewportSize()` 对 `connectOverCDP` 拿到的页面无效，截图宽度仍是窗口宽，别指望它做尺寸断言。
- **一条一进程**：Studio 的上传框会在网络抖动时自己消失，批量排在一个进程里 = 后面全部白跑；一条一边界，中断只丢当前这条。

## 播放列表（合集）加队实测

- 真 id 是 **`PLAN0DrrdpGds`**（`PLAN` 前缀，不是常规 `PL`）。之前按 `PL0DrrdpGds` 查公网页查到 0 条，是 id 抄漏了两位，不是列表空。id 从 Studio「内容 → 播放列表」那一行的链接里量：`https://studio.youtube.com/playlist/<id>/edit`。播放列表本身是**公开**范围。
- **走不通的路（先记下，别再试第二遍）**：视频编辑页的播放列表下拉。形状是
  `ytcp-video-metadata-playlists [role=button]`（贴底，必须 scrollIntoView）→ 浮层 `ytcp-checkbox-group#playlists-list > … > div#items > ytcp-ve`，
  勾选态**不在 `ytcp-ve` 身上、在它 shadow 里的 `role=checkbox`**（只读包装元素会永远读到未勾）。
  但**勾选能翻、点完浮层里的 `ytcp-button.done-button`「完成」之后不持久**——公网对账三遍都停在 1 条；
  同层的 `save-button`「保存」在未改动时 disabled 且不可见，我也没能让它变成可点。这条路废掉。
- **走得通的路是 www 观看页的「保存」**（`.temp/yt-save-pl.mjs`，7 条全过，公网对账 `仍缺：（无）`）：
  观看页动作条**没有独立「保存」**，它收在「其他操作」菜单里（宣传/保存/不喜欢/举报）；
  点开后的选择器里每一行是 `button.ytButtonOrAnchorHost`，**选中态写在 aria-label**：`通往单片机之路, 公开, 未选中` / `已选中`——
  点一下就直接落库（www 这条发的是 `append_playlist`，没有"再点某个提交按钮"这个会骗人的环节）。
- 两个必须记住的坐标坑：
  - `[aria-label="其他操作"]` **一个页面上有十几个**（右侧相关视频每行一个），`.first()` 会挑错人；
    认动作条那一个的办法是**取和「分享」y 相差 10 px 内的那个**。
  - Shorts 版式动作条贴在视口底（实测 y≈847，窗口只有 ~911 高），菜单朝下开整块掉到屏幕外——
    **坐标量得到、点不到**。`scrollIntoViewIfNeeded` 不算它出界所以不管用；
    要 `page.mouse.wheel(0, y-320)` 把动作条滚到画面中部再量再点（YouTube 的滚动容器不是 window，`window.scrollBy` 也别指望）。
  - 反过来，**菜单项本身绝不能再滚**：一滚菜单自己关掉，之后点的就是失效坐标。
- 公网播放列表页 **`playlistVideoRenderer` 已经 0 命中**：新版把每条放进了 `lockupViewModel` / `"contentId":"…"`。核对成员两种都认（`.temp/yt-plcheck.mjs`）。
- 加队脚本 **每条一个独立 page、跑完即关**，收尾不信 Studio 的复核、直接拿公网播放列表页对账。
  上一版复用 `ctx.pages()[0]`，浏览器一崩整批就 "Target page, context or browser has been closed"。
  另：常驻 Chromium 这一小时崩过两次（exit 13 / exit 1），脚本里 `page.close()` 前要先确认不是最后一个标签。

## 仍卡在账号侧（不是脚本能解的）

- 描述里的站内地址是**纯文本不可点**：Studio 报「如需提供可点击的外部链接，请先完成一次性验证。」要用户在 Google 账号里完成验证（一般是手机）。
- 自定义封面能传（c3 两条都已上），说明手机验证这一项已过；卡的是外链那一项。
