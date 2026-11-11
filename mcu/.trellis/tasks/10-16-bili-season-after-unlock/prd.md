# B站合集解锁后建集并挂 17 条

## Goal

账号拿到「加入合集」权益后，用一次成型的通道把 17 条 B站稿件挂进一个合集，不再重复踩权限和字段坑。

## Blocked By（2026-10-16 实测，四条独立证据同向）

- 建集接口直接拒：`POST member.bilibili.com/x2/creative/web/season/add` → `code=20082 您创建的合集个数太多了`；但 `GET /seasons` 返回 `total=0`，一条存量都没有——这是权限位的伪装文案，不是额度满。
- 权限位读死：`GET member.bilibili.com/x/vupre/web/archive/white` → `season=false`、`new_season=false`（另有 `season_scope=2`、`season_add_multip=true`）。
- 投稿页那行控件是空的：`.temp/bili-web-run/c2-shape.log` 记录「加入合集 合集功能可用于收集整理系列性稿件 **开通合集功能需满足权益中心等级达 Lv2**，您可前往创作中心-权益中心查看相关数据」，`"控件": []`。
- 合集管理路由不存在：`/platform/content/season/manage`、`/platform/manager/season.html` 都被打回 `/platform/home`。

不要用 `x/member/web/exp` 的 `current_level` 判断这条门槛——那是用户经验等级（本账号 Lv4），和权益中心等级不是一套，《能不能建合集》那行推断是错的。

## Requirements

- 门槛只认 `white` 接口的 `season`/`new_season` 两位；任一为 true 才动手。
- 合集标题与简介必须和 `video/series.json` 的 `series` 字段同口径（现值 `"通往单片机之路 "` 带尾空格，别顺手改掉，改了要和站内实际标题核对）。
- 17 条一条不漏：以 `.temp/bili-web-run/<ep>.bvid` 为准（`c3b-volatile` 是 C3 的抖音 A/B 变体，标注 `variant: ab-test`、note 写明不上 B站，不算漏投）。
- 挂完必须复读 `x/web-interface/view?bvid=` 的 `ugc_season` 逐条确认，接口没回显就不算挂上。
- 这是平台可见的批量写操作：每条 `episodes/add` 之前要拿到用户在对话里的点头，脚本不自己放行。

## Acceptance Criteria

- [ ] `seasons` 列出新合集，`state=0`（正常），封面是线上 biliimg URL 而非本地路径。
- [ ] 17 条 aid/cid 全部进同一 section，逐条 `view.ugc_season` 回显合集 id。
- [ ] 合集简介里不出现 markdown 残留（2026-10-16 已实测 B站简介区按 `white-space: pre-line` 纯文本渲染，``` 围栏、行内反引号、`**` 会原样露出；投稿前用 `.temp/bili-desc-fix.mjs` 的 `clean()` 或 `.temp/bili-submit.mjs` 的 `plain()` 脱标记）。

## Notes（就绪即跑的三步）

1. 封面已生成并上传过一次：`video/out/season-cover-bili.png`（1920×1200，走 `buildCover(browser, ep, 'bili', …)` 产线，`.temp/bili-season-cover.mjs`），URL `https://archive.biliimg.com/bfs/archive/4ab3266e20a3609f8a8d5aa44680959f6552a82b.png`。若隔太久失效，重跑 `node .temp/bili-collection.mjs cover video/out/season-cover-bili.png`。
2. `node .temp/bili-collection.mjs create "<标题>" "<简介>" "<封面URL>"` → 写 `.temp/bili-season.json`，里面就是 `season_id`。
3. 逐条 `node .temp/bili-collection.mjs resolve <bvid>` 取 `aid`/`cid`，再 `node .temp/bili-collection.mjs join <section_id> "aid:cid:标题"`；`section_id` 从 `seasons` 返回的 `sections[]` 里读，别猜。

## 复测记录

- 2026-10-17 深夜：`node video/publish/bili-level.mjs` → `season=false new_season=false`（`season_scope=2`，`season_add_multip=true`）
  → **仍未解锁**，建集照旧会吃 `code=20082`（权限位伪装文案，不是额度）；等权益中心 Lv2 权限位翻上来再跑
  `bili-collection.mjs create` 建季并挂 17 条。
