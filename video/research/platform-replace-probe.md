# 四平台换新能力探针（Phase 0）

- 任务：Task 1「四平台只读能力探针」
- 本次运行：2026-10-22T09:00:14.710Z（本机时区 +08:00，17:00）
- 探针：`video/publish/repost/probe-platforms.mjs`
- 运行命令：`node video/publish/repost/probe-platforms.mjs > .temp/v2-probe/report.txt 2>&1`
- 结果文件：`.temp/v2-probe/report.json`、`.temp/v2-probe/report.txt`
- 本次退出码：`3`（B站 `not-logged-in`；其余三平台 `yes`，脚本只在四平台全为 `yes|no` 时退出 0）
- 报告顶层：`blocked: false`，`blockedReason: null`
- CDP：`http://127.0.0.1:9223`，Chrome/153.0.8010.12，`/json/version` 可访问；连接时既有页面 1 个（小红书常驻页 `/new/home`），全程未关

## 0. 本次执行结论（先读）

常驻 Chromium 已由 `video/publish/xhs-daemon.mjs` 启动，CDP 可用。四平台真实状态：

| 平台 | status | 登录态 | 入口结论 | 证据 |
|---|---|---|---|---|
| B站 | `not-logged-in` | 未登录 | 无法判定（被重定向到登录页） | `finalUrl=https://passport.bilibili.com/login`，title `账号登录`，`entries=[]` |
| 抖音 | `yes` | 已登录 | 每条作品卡片直接显示「删除作品」 | `entries` 4 条，含 `BUTTON/DIV "删除作品"` |
| 知乎 | `yes` | 已登录 | 已发布视频行「更多」菜单内有「删除」；视频草稿为空 | `published.entries` 2 条，含 `BUTTON "删除"`；`draft.entries=[]`，页面「暂无内容」 |
| 小红书 | `yes` | 已登录 | 笔记卡片行内有垃圾桶图标，hover tooltip「删除」 | `noteCards=10; deleteControl=true count=10 cls="note-card__action-btn note-card__action-btn--del"` |

本次重跑修正了探针的两个盲点，否则会得到假阴性：

1. **知乎的「更多」按钮 innerText 前面带 U+200B**，旧的 `t === '更多'` 永远匹配不到，菜单不会展开，于是误判 `no`。现在扫描/展开前先剥掉 `\u200B-\u200D\uFEFF`，点开「更多」后才看到「删除」。
2. **小红书的删除是图标按钮**：`note-card__action-btn--del`，无文字、默认 `opacity: 0`，hover 卡片才显形，纯文本扫描永远看不到。现在额外统计该控件，并 hover 首张卡片后取证；**没有点删除按钮**。

08:58 的中间一轮曾把知乎/小红书记为 `no`，已被 09:00 的最终 `report.json` 覆盖；以上表为准。

登录态逐项：

- B站：未登录。打开目标页即 302 到 `https://passport.bilibili.com/login`，页面是扫码/密码登录页；按纪律没有尝试登录。
- 抖音：已登录，页面标题「抖音创作者中心」，作品列表可见。
- 知乎：已登录，页面标题「内容管理 - 创作中心 - 知乎」，共 84 条内容。
- 小红书：已登录，页面标题「小红书创作服务平台」，全部笔记 69。

---

## 1. B站

### 1.1 有/无入口与页面路径

- 目标页面：`https://member.bilibili.com/platform/upload-manager/article`。
- 最终落点：`https://passport.bilibili.com/login`，title `账号登录`。
- 页面是二维码 + 密码/短信登录页（截图 `.temp/v2-probe/bilibili.png`）。**没有打开稿件管理页，因此没有「更换视频/换源/删除/重新上传」的任何实时证据。**
- `entries: []`，`extra.replaceEntryVisible=false`，`extra.deleteEntryVisible=false`。这两个 false 只表示“没看到”，不表示“没有”。

### 1.2 判定证据（`report.json` 存档；网络 URL 已脱敏）

```json
"status": "not-logged-in",
"entries": [],
"evidence": "finalUrl=https://passport.bilibili.com/login; title=账号登录; entries=[]; expanded=[]; menuTexts=[]"
```

网络条目只有 passport 登录相关请求（以下为脱敏后的存档值）：

```text
https://passport.bilibili.com/x/passport-login/web/qrcode/generate
https://passport.bilibili.com/x/passport-login/captcha
https://passport.bilibili.com/x/passport-login/web/qrcode/poll
```

存档的 `report.json` 已脱敏：只保留 `scheme://host/path`，原始 query string（含 `qrcode_key`、`b_ret` 等参数）已就地剥离；探针代码此后记录 `networkEntries` 也用同样规则。另：旧存档的 `extra.editLinks` 里仍有一条登录页上的无关公开视频链接，当前代码已过滤为 `member.bilibili.com` 且路径含 `upload-manager` 的链接（未登录时为空）；该字段不参与判定。

没有任何 `replace|source|upload` 的稿件管理请求可分析。

### 1.3 历史旁证（不是本次证据，不计入判定）

`.temp/bili-web-run/f3-scheduler-one.log` 与 `c2-fill.log` 显示：**新投稿上传页在上传完成后有「更换视频」按钮**。那是提交页，不是已发布稿件的编辑页，不能证明已发布作品可换源，也不能证明换源后 cid 不变。本次未登录，无法把这条旁证升级为事实。

### 1.4 风险

- **删除重发**：BV 号变化，评论、弹幕、收藏、播放/点赞数据与外部链接全部丢失；合集归属要重挂；新稿重新过审、重新冷启动。
- **换源**：若平台重新转码，cid 会变化；B站弹幕按 cid/分P 归属，cid 变化会导致弹幕不可见或重置。稿件会重新进入审核态。
- 两种路径都要在动作前归档公开页数据（BV、cid、评论数、弹幕数、播放/点赞、合集），动作后逐项回读；只信页面/接口的公开态，不信 toast。

### 1.5 决议（待登录后重跑 + 用户点头）

**本次不能对 B站 做任何能力判定。** 需要先在同一个持久 profile 里由用户完成 B站 登录，再重跑探针。重跑后：

1. 若已发布稿件编辑页确有「更换视频/换源」：优先换源，不删重发；先做单集 canary（记录 BV/cid/评论/弹幕，动作后回读），cid 变化导致不可接受丢失时停止并回到用户面前。
2. 若已发布编辑页没有换源入口：才把「删除 + 重发」作为候选，逐集闸门 + 删除前归档 + 删除后回读。

**登录完成前，不实现 B站 删除/换源适配器。**

---

## 2. 抖音

### 2.1 有/无入口与页面路径

- 页面：`https://creator.douyin.com/creator-micro/content/manage`（作品管理）。
- 已登录。每条作品卡片右侧直接渲染四个动作：`编辑作品`、`设置权限`、`作品置顶`、`删除作品`。**「删除作品」是卡片上的直接按钮，不是藏在「更多」菜单里**（截图 `.temp/v2-probe/douyin.png` 可见每行红色删除按钮）。
- 这是本次四平台里最直接、最容易误触的删除入口。

### 2.2 判定证据（`report.json` 原文）

```json
"status": "yes",
"entries": [
  { "tag": "DIV",  "text": "编辑作品 设置权限 作品置顶 删除作品", "cls": "", "href": "" },
  { "tag": "DIV",  "text": "删除作品", "cls": "ghost-btn-hFvKoY op-btn-K0QzkN", "href": "" },
  { "tag": "SPAN", "text": "删除作品", "cls": "", "href": "" },
  { "tag": "DIV",  "text": "STM32下载报No target？九成不是芯片坏了 #STM32 #单片机 编辑作品 设置权限 作品置顶 删除作品", "cls": "", "href": "" }
],
"evidence": "finalUrl=https://creator.douyin.com/creator-micro/content/manage; title=抖音创作者中心; ..."
```

`extra.singleWorkMenuHasDelete: true`。历史 `.temp/dy-mstat.log`（2026-10-15）的菜单文案与本次一致，但本次已由实时页面独立证实。

### 2.3 风险

- 删除会清空该作品的评论、点赞、播放与互动数据，作品 ID 不可复用。
- 重发是全新作品：重新过审、重新冷启动；同一天多条会进低质池（既有台账口径：1 天 1 条，最多 2 条）。
- 「删除作品」是行内一级按钮，脚本若按坐标或模糊文本点击，容易点错行；适配器必须锁定“标题/作品 ID 精确匹配”的那一行。
- 删除前必须先把公开数据归档（作品 ID、标题、播放/点赞/评论、发布时间），否则删完无法对账。

### 2.4 决议（待用户点头）

实时探针确认“已登录 + 每条作品有删除作品”后，Task 16 才可以写抖音删除适配器。适配器必须：

1. 逐集闸门（`I_HAVE_USER_OK_DELETE_<ep>`），闸门内容来自对话原话，脚本不得自造。
2. 删除前归档公开数据到 `.temp/repost/<date>/<ep>/`。
3. 按标题 + 作品 ID 精确锁定目标行，禁止“列表第一行”式点击。
4. 删除后回读列表确认该条消失，再允许发布新稿。
5. 发布节奏沿用现有台账：1 天 1 条，最多 2 条。

**本次不实现、不执行。**

---

## 3. 知乎

### 3.1 有/无入口与页面路径

- 已发布页：`https://www.zhihu.com/creator/manage/creation/zvideo`。
- 草稿页：`https://www.zhihu.com/creator/manage/creation/draft?type=zvideo`（路由来自 `video/publish/zhihu-plan.md` 的实测）。
- 已发布页已登录，顶部「视频」tab，共 84 条内容；每行动作按钮是「编辑 / 数据 / 查看评论 / 更多」。
- 点开第一行的「更多」后，弹出菜单包含：`分享`、评论权限四项（`任何人都可以评论` / `仅显示我筛选后的评论` / `关注我的人能评论` / `我关注的人能评论` / `不允许评论`）以及 **`删除`**。本次只展开菜单读取文字，没有点「删除」。
- 草稿页已登录，选中「视频草稿」tab，页面正文为 **「暂无内容」**；`draft.entries=[]`，`draft.result=no`。

### 3.2 判定证据（`report.json` 原文）

已发布页：

```json
"entries": [
  { "tag": "DIV",    "text": "分享 任何人都可以评论 仅显示我筛选后的评论 关注我的人能评论 我关注的人能评论 不允许评论 删除", "cls": "Popover-content Popover-content--bottom Popover-content--arrowed undefined Popov", "href": "" },
  { "tag": "BUTTON", "text": "删除", "cls": "Button Menu-item css-cn5m5x Button--plain", "href": "" }
]
```

逐页结论：

```text
published.finalUrl=https://www.zhihu.com/creator/manage/creation/zvideo
published.entries=[... 上面 2 条 ...]
draft.finalUrl=https://www.zhihu.com/creator/manage/creation/draft?type=zvideo
draft.entries=[]
```

`extra.published.expansions` 记录本次只点了一次「更多」（`clicked: "更多"`）；`extra.draft.result = "no"`。

探针修正记录：知乎「更多」按钮的 `innerText` 是 `"\u200b 更多"`，旧扫描器用 `replace(/\s+/g,' ')` 去不掉 U+200B，导致 `t === '更多'` 失败、菜单没展开、误报 `no`。现在统一剥掉零宽字符，菜单能正常展开并命中「删除」。

### 3.3 风险

- 删除不可恢复；「删除」在「更多」下拉里，和评论权限设置同列，误点风险存在。
- 已发布页与草稿页是两个入口；本次视频草稿为「暂无内容」，但未来有草稿时误删会丢失续传素材与已填表单。
- 知乎视频重发受账号级频率窗口限制，`code=10000` 会在窗口内反复拒绝；被拒的尝试本身可能刷新窗口（既有台账口径）。
- 已发布侧的回读 API 不可靠：`creations/v2/zvideo` 返回的是 `type:"pin"`（每条视频旁同步发的那条想法），删除后的存在性核对要以创作者中心列表 UI 为准。

### 3.4 决议（待用户点头）

已发布视频删除入口已确认，Task 16 可以写知乎已发布删除适配器，但必须：

1. 逐集闸门 + 删除前归档标题/URL/发布时间/公开数据 + 删除后回列表核对消失。
2. 从「更多」菜单点「删除」是两级动作，适配器要在菜单展开后再次校验目标标题，禁止按坐标盲点。
3. 草稿删除单独闸门，默认不自动删；本次视频草稿为空，暂无草稿对象可操作。
4. 重发遵守频率窗口；`code=10000` 只停不重试。

**本次不实现、不执行。**

---

## 4. 小红书

### 4.1 有/无入口与页面路径

- 页面：`https://creator.xiaohongshu.com/new/note-manager`（笔记管理）。
- 已登录；「全部」tab 计数 69，当前渲染 10 张笔记卡片（翻页/滚动没有加载更多，仍是 10 张）。
- **每张卡片有行内图标动作，默认 `opacity: 0`，hover 卡片后 `note-card__actions--visible` 才显形：**
  - 铅笔图标：hover tooltip「编辑」；
  - 垃圾桶图标：`class="note-card__action-btn note-card__action-btn--del"`，hover tooltip「删除」。
- 本次 10 张已渲染卡片全部带删除图标（`deleteControlCount=10`），**10 张卡片的状态全部是「未通过」**；没有切换「已发布」tab，没有点任何图标。
- 「编辑」不是 `<a href>`：`a[href*="/publish/update"]` 数量为 0，`editLinkHasId=false`。笔记 ID 可从卡片 `data-impression` 里取到，例如 `6ad6165d000000002900e7a9`；历史 `video/publish/xhs-plan.md` 记录编辑会新开 `/publish/update?id=<noteId>`，本次未点击复核。

### 4.2 判定证据（`report.json` 结构证据 + 独立只读 hover 记录）

`report.json` 的 `entries` 是文本扫描结果，删除是图标，故为空；结构证据在 `extra`。**`report.json` 本身不含 tooltip 文案**，只有 `deleteControlCount`、`deleteControlClass`、`noteIds` 等结构字段；下面「编辑/删除」的 hover tooltip 来自 16:57 单独执行的只读 hover 复核 `inspect3.mjs`，不是最终 `report.json` 的内容。

```json
"entries": [],
"evidence": "...; noteCards=10; deleteControl=true count=10 cls=\"note-card__action-btn note-card__action-btn--del\"; editAnchors=0 editAnchorHasId=false; noteIds=[\"6ad6165d000000002900e7a9\", ...]",
"extra": {
  "editLinks": [],
  "editLinkHasId": false,
  "noteCardCount": 10,
  "noteIds": ["6ad6165d000000002900e7a9", "6ad601a5000000002f030b26", "6ad600f6000000002603049b", "6ad6004b000000000c00a6f4", "6ad5fbf9000000002f03288a"],
  "deleteControlCount": 10,
  "deleteControlPresent": true,
  "deleteControlClass": "note-card__action-btn note-card__action-btn--del",
  "editControlCount": 10,
  "deleteInlineAction": true
}
```

本摘录的字段名按当前契约（`deleteInlineAction`）展示；存档 `report.json` 生成于本次改名之前，键名仍是旧名，布尔值相同，不影响结论。

独立只读 hover 复核（`inspect3.mjs`，16:57；不点击、不出自 `report.json`）：

```text
edit tooltip: ["编辑"]
del tooltip: ["删除"]
```

DOM 摘录（删除按钮，默认透明，hover 卡片后可见）：

```html
<div class="note-card__actions note-card__actions--visible">
  <span class="note-card__action-btn"><svg ...>铅笔路径</svg></span>
  <span class="note-card__action-btn note-card__action-btn--del"><svg ...>垃圾桶路径</svg></span>
</div>
```

**这推翻了此前“网页端可能没有删除”的倾向性判断。** 历史 `xhs-plan.md` 只 hover 了行内图标、没有展开到删除层；本次确认删除图标就在行内，tooltip 明确为「删除」。

### 4.3 风险

- 删除不可恢复；原笔记的点赞、收藏、评论全部不迁移，重发笔记 ID 会变化，旧链接/外部引用失效。
- 删除图标是行内一级按钮，hover 即显形，误点风险高；适配器必须按 `noteId`/标题锁定卡片，禁止按坐标或“第一张卡片”点击。
- 本次 10 张已渲染卡片全部是「未通过」，不是公开笔记；如果目标集里有「已发布」笔记，需在 canary 时确认同一垃圾桶图标对已发布卡片同样可用（类名是行级通用控件，预期一致，但本次未逐张验证）。
- 小红书整条线不出现站外地址（既有口径）；编辑已发布笔记可能把笔记拉回审核，删除重发则必然重新审核。

### 4.4 决议（待用户点头）

网页端删除入口已确认，此前“无网页删除 → 只能 App 手动删或该平台不换视频”的二选一不再是被迫选项。建议：

1. **优先网页删除 + 重发**：逐集闸门（`I_HAVE_USER_OK_DELETE_<ep>`），删除前归档笔记 ID/标题/状态/互动数据，删除后回笔记管理核对消失，再走现有 `xhs-step.mjs` 发布 v2。
2. **先做单集 canary**：选一条「已发布」旧笔记，确认垃圾桶图标点下去是直接删除还是弹确认框、确认框文案是什么；canary 只记录，不批量。
3. **保留退路**：若用户不愿承担误删风险，仍可选 App 手动删或该平台不换视频；不允许“另发一条新笔记”冒充替换。
4. 适配器实现前必须拿到用户对该方案的点头。

**本次不实现、不执行。**

---

## 5. Task 16 的入口契约

`report.json` 顶层：

```json
{
  "at": "2026-10-22T09:00:14.710Z",
  "cdp": "http://127.0.0.1:9223",
  "blocked": false,
  "blockedReason": null,
  "platforms": { "bilibili": {}, "douyin": {}, "zhihu": {}, "xiaohongshu": {} }
}
```

每个平台对象至少包含：

```json
{ "status": "yes|no|not-logged-in", "entries": [], "evidence": "", "risk": "" }
```

`status` 语义（只允许这三值）：

- `yes`：已登录，页面渲染完成，允许的展开/悬停动作之后，确认存在删除、更换视频、换源或重新上传入口。抖音/知乎是可见文字命中；小红书是图标控件（`deleteControlPresent=true`）命中。
- `no`：已登录，页面渲染完成，允许的展开/悬停动作之后，没有命中上述入口。
- `not-logged-in`：登录墙/登录重定向，或 CDP 不可达导致页面无法观测。后者同时由顶层 `blocked:true` 标记。

本次 `blocked:false`，四平台 status 为 `not-logged-in / yes / yes / yes`。Task 16 消费时必须先看 `blocked`，再看各平台 `status`；B站 的 `not-logged-in` 不得当成 `no`。

脚本额外字段（用于后续适配器定位，不是放行依据）：

- B站：`extra.editLinks`（仅保留 `member.bilibili.com` 且路径含 `upload-manager` 的链接；未登录时为空）、`extra.replaceEntryVisible`、`extra.deleteEntryVisible`、`extra.networkEntries`（只记 `scheme://host/path`，query 已剥离）。
- 抖音：`extra.singleWorkMenuHasDelete`、`extra.menuTexts`。
- 知乎：`extra.published` / `extra.draft`（各自 `finalUrl`、`title`、`entries`、`result`；`result` 不叫 `status`，以保证顶层 `"status"` 恰好 4 条）。
- 小红书：`extra.editLinks`、`extra.editLinkHasId`、`extra.noteCardCount`、`extra.noteIds`、`extra.deleteControlCount`、`extra.deleteControlPresent`、`extra.deleteControlClass`、`extra.editControlCount`、`extra.deleteInlineAction`。

安全约束（脚本已内建，Task 16 沿用）：

- 只 `connectOverCDP`，不 `launch`；不 `browser.close()`。
- 每平台 `ctx.newPage()`，只 `page.close()` 自己开的页；小红书常驻页永不碰。
- 展开控件只允许可见文案精确等于「更多」或 `⋯/…/···/.../•••`；`aria-label`/`title` 仅在无可见文案时回退且只认「更多」。点击前 Node 侧再校验文案不含动作词。
- 点击中心点必须 `document.elementFromPoint(cx, cy) === 候选元素`；候选自身或任一后代含 `删除|确认|发布|提交|更换视频|重新上传` 即放弃。
- 小红书只 hover 卡片读取图标与 tooltip，不点删除。
- 不点删除、确认、发布、提交、更换视频、重新上传。

---

## 6. 用户确认门

本报告是 Phase 0 的产物，不是放行条。需要用户点头的事项：

1. **B站**：先在持久 profile 里完成登录，再重跑探针；拿到已发布编辑页的真实结果后再决定“优先换源”还是“删重发”。登录完成前 B站 无结论。
2. **小红书**：网页端删除已确认。是否按“网页删除 + 重发 + 单集 canary”执行；若不愿承担误删风险，选 App 手动删或该平台不换视频。
3. **抖音/知乎**：删除入口已确认。是否批准 Task 16 写“逐集闸门 + 删除前归档 + 删除后回读”的删除适配器。

在用户点头之前：

- 不进入 Task 16 的任何删除适配器实现；
- 不开始 Phase 4；
- 不删除、不替换任何线上作品。

---

## 7. 本次验证记录

```bash
$ test -s .temp/v2-probe/report.json && echo report.json OK
report.json OK

$ test -s .temp/v2-probe/report.txt && echo report.txt OK
report.txt OK

$ grep -c '"status"' .temp/v2-probe/report.json
4

$ node -e "const r=require('./.temp/v2-probe/report.json'); console.log(Object.values(r.platforms).map(v=>v.status).join(','))"
not-logged-in,yes,yes,yes

$ curl -s http://127.0.0.1:9223/json/list  # 只剩常驻页
page | 小红书创作服务平台 | https://creator.xiaohongshu.com/new/home
```

- `report.json` 非空；4 条平台 `status`，全部属于 `yes|no|not-logged-in`。
- 截图：`bilibili.png`（登录页）、`douyin.png`（作品列表含删除作品）、`zhihu-published.png`（84 条内容 + 更多）、`zhihu-draft.png`（视频草稿暂无内容）、`xiaohongshu.png`（笔记管理）、`zhihu-more-open.png`（更多菜单展开）、`xhs-manager-hover.png`、`xhs-del-hover.png`。
- 探针没有执行任何删除/确认/发布/提交/更换视频/重新上传点击；展开动作只有知乎第一行的「更多」；小红书只 hover 卡片和图标读取 tooltip；没有启动浏览器；没有调用 `browser.close()`；没有关闭小红书常驻页。
