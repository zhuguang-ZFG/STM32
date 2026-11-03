# ai4fw 四平台发布文案与交付清单

> 事实口径：全部数字出自 `research/source-snapshot-369-repos.md`（GitHub API 快照，2026-10-27）。
> 成片：竖版母版 `jobs/ai4fw/outputs/film.mp4`（64.09s，1080×1920，30fps，H.264，总码率 954 kbps）；
> 横版母版 `jobs/ai4fw-16x9/outputs/film.mp4`（同长同旁白，1920×1080，总码率 845 kbps）。
> 水印/品牌：通往单片机之路。评论/置顶统一带快照口径。

## 交付文件（video/out/ai4fw/）

| 文件 | 用途 | 规格 |
|---|---|---|
| douyin.mp4 | 抖音（xhs-step 复用同名文件） | 1080×1920 H.264，954 kbps ✅抖音约束 |
| wx.mp4 | 视频号 | 同竖版母版；总码率 954 kbps ≤10 Mbps ✅实测（ffprobe format.bit_rate） |
| bilibili.mp4 | B站 | 1920×1080 H.264，845 kbps |
| douyin-cover.png | 抖音竖封面 / 小红书封面 / 视频号封面 | 1080×1920（管线 finalize 导出） |
| douyin-cover-1440x1080.png | 抖音横封面 | 1440×1080，16:9 封面等比+模糊补边（无内容裁切） |
| bilibili-cover.png | B站封面 | 1920×1080 |

## B站（横版，tid 231）

- 标题（30 字）：不用视频大模型：369 个 AI 视频工具仓库里最能打的四个
- 简介：见 `out/ai4fw/bili-submit.yaml` desc（426 字，纯文本无 markdown，四框架+星数+快照口径+选型表）
- 标签：AI视频,AI工具,开源项目,编程,效率工具
- 封面：bilibili-cover.png
- 置顶评论（发布后）：四仓库+星数+快照口径（同抖音 pinned）

## 抖音（竖版，不进「通往单片机之路」mix——内容轨不同）

- 标题（22 字 ≤30 ✅）：369 个 AI 视频工具仓库，这四个最能打
- 描述（caption）：不用视频大模型，一段代码直接出片 / 四框架一行 / 选型一句 / #AI #AI视频 #开源 #编程
- 自主声明：内容为个人观点或见解（沿用 5 集既有惯例）
- 封面：竖 douyin-cover.png + 横 douyin-cover-1440x1080.png（双封面走模态流，防「竖封面变第 0 帧」旧坑）
- 置顶评论（pinned，275 字）：四仓库+星数+快照口径+「要全量版评论区吱声」

## 小红书（竖版，复用 douyin.mp4/douyin-cover.png）

- 标题（15 字 ≤20 ✅）：369 个仓库里，这四个最能打
- 正文（347 字 ≤1000 ✅）：见 episode.json publish.xiaohongshu.body
- 话题：AI / 编程 / 效率工具 / 开源

## 视频号（竖版 wx.mp4）

- 短标题（≤16 字力荐）：369 个仓库，这四个最能打（13 字）
- 描述：不用视频大模型，一段代码直接出片。369 个 AI 视频工具仓库里最能打的四个：lemo-opuscar / huashu-art-motion / huashu-motion / sweety-handdraw-video（星数口径见评论）
- 四项必改（wx-plan.md §4 实测）：位置→不显示位置；视频标注→无需标注（沿用 c3 口径）；合集→不挂；声明原创→保持默认勾选
- 封面：douyin-cover.png（大字 369 钩子在 204px 卡片可读；如糊再走 wx-cover-final 两步量宽法另做）

## 发布顺序与闸门

1. B站（bili-web.mjs --ep=ai4fw：open→feed→fill→cover→more→publish）
2. 抖音（douyin-step.mjs 步骤编排，无 seasonpick）
3. 小红书（xhs-step.mjs --ep=ai4fw，无 collection）
4. 视频号（.temp/wx-run 9225 常驻浏览器）
- 全部共用闸门 `.temp/*/I_HAVE_USER_OK=ai4fw`，来自用户 2026-10-28「要搞定啊」对话授权。
