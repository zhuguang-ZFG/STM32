# P5 发布留证（AC8）

日期：2026-11-11 · 目标：PR #106 合入 → CI 同 SHA 全绿 → 启用 Pages → 部署 → 线上回读关闭 AC8

## 部署前快照（发布门 §7 要求）

| 项 | 值 | 核查方式 |
|---|---|---|
| 目标仓 Pages 现状 | **无站**（`has_pages=false`） | `gh api repos/zhuguang-ZFG/STM32`（owner token，排除可见性歧义） |
| 目标仓默认分支 | main | 同上 |
| 分支保护 | 两分支均无 required checks | `gh api repos/.../branches/{main,feat/mcu-subtree-merge}/protection` → Branch not protected |
| 旧站线上状态 | **存活**，`https://zhuguang-zfg.github.io/mcu/` → HTTP 200（86,299 B） | curl（首次探测 000 为本地网络抖动，复测确认） |
| 旧仓状态 | `zhuguang-ZFG/mcu`：未归档、非 disabled、`has_pages=true`、`pushed_at=2026-11-11T06:59:36Z` | `gh api repos/zhuguang-ZFG/mcu` |
| 旧仓归档快照 tag | `mcu-pre-merge-archive` **存在** | `gh api repos/zhuguang-ZFG/mcu/tags` |
| 候选链 | `92fc917c`（基线）→ P1 `2e965db4` → P2 `27757966` → P3 `f6b039b6` → P4 `b6cddd64` → CI 修复 `f812a477`（PR HEAD） | git log |

## CI 首轮暴露并修复的真问题（f812a477）

| 失败 | 定性 | 处置 |
|---|---|---|
| Book CI book/book-en：slop 7 命中（p4-evidence 状态列的通过记号） | 真问题（自家文档） | 状态列改文字，slop 本地复跑干净 |
| mcu-quality lint：B905/B007 ×3 于 stm32-book | 真问题（预存配置 bug） | ruff-action 会把 src（默认仓库根）追加到命令行，args 写死 mcu 仍扫全仓 → 显式 `src: mcu` |
| 外链巡检 37 个 404 | 真问题（合并窗口必然 404） | `.lychee.toml` 放行三类：指向 main 的 blob/tree/workflows 引用 + 目标站首部署前；注明合入+首部署后删除 |
| arm-host / checks / mcu-book | runner DNS 抖动（`azure.archive.ubuntu.com` 解析失败，14:40–14:51 UTC） | 重跑自愈 |

## 同 SHA（701eb212，PR #106 候选）CI 证据 —— 全绿

| 工作流 | run | 结论 | 关键证据 |
|---|---|---|---|
| mcu 质量闸门 | 43065842663 | success | lint / checks（quality 15 段+浏览器+动画+整书+GNU 双口径）/ **arm-host** / **esp32 15 用例** |
| 外链巡检 | 43065842647 | success | 合并窗口放行后 0 失败 |
| MCU Book CI | 43065842654 | success | 整书 PDF 1211 页契约 + **Linux GNU sha256 权威口径** |
| Book CI（zh/en） | 43065842645 | success | SPL + **双语 PDF 构建 + audit_pdf_layout 版式审计** |

main 复验（§7 第 3 条：合入产生新 SHA 需核对）：`9b5a63e`（#106 合并）与 `0a613bf`（#105 合并）树均与 `701eb212` **完全相同**（tree `ee76fbdd…`，diff 空）→ 候选验证可转移。main 首跑 43069392578 quality 门再次全绿（含 esp32 15 用例），deploy 步暴露 mount-smoke 竞态（见下）修后 43072886915 **全绿含 deploy-pages**。

## 首部署抓到的真缺陷（已修）

mount-smoke.mjs 根入口断言：`page.goto` 读 meta-refresh 重定向页 body，浏览器即刻跳转导致 `response.text()` 抛 Protocol error（CI 必现、本地侥幸）。改 `page.request.get`（无导航竞态）。PR #107 合入后 43072886915 全绿。

## AC8 线上回读（2026-11-11 UTC 深夜 / 本地 11-12 凌晨）

| 项 | 结果 |
|---|---|
| 根入口 `/STM32/` | HTTP 200，内容含 `url=./mcu/` 重定向标记 |
| 首页 `/STM32/mcu/` | HTTP 200，含「通往单片机之路」 |
| 深链 `…/stm32/07-usart.html` | HTTP 200 |
| 导读 `…/guide/hardware.html` | HTTP 200 |
| 整书 `…/book/mcu-deep-book.html` | HTTP 200 |
| sitemap.xml | HTTP 200 |
| downloads 4 文件 | 全部下载，sha256 与线上 SHA256SUMS **ALL_MATCH**（html 10,803,795 B；pdf 33,355,667 B） |
| 旧站 `/mcu/` | HTTP 200 存活（处置决策项：归档壳仓重定向，README 已改为计划表述） |
| Pages 配置 | build_type=workflow，站点 `zhuguang-zfg.github.io/STM32/` |

**AC8 关闭。AC1–AC8 全部完成。**

## 收尾事项

- lychee 合并窗口三条放行已删除（本提交）；main 上外链门将全量复验这些 URL 200。
- `feat/mcu-merge-p1` 远端分支与本地 worktree 已删除（2026-11-12 收尾执行）。
- 旧仓 `zhuguang-ZFG/mcu`：已建归档壳仓——gh-pages 分支全部为跳转桩页（131 条路由含目录型 index），Pages 源切至 gh-pages，仓库已归档只读；整树历史与 tag `mcu-pre-merge-archive` 保留。

## 壳仓 v2：sitemap 之外的发布产物（advisory 指正后补齐，2026-11-12）

首轮壳仓只覆盖 sitemap 的 131 条页面路由，`/mcu/book/*` 与 `/mcu/downloads/*` 404。补齐口径：**PDF 保留可下载真字节**（从已部署新站原样取字节，sha256 与线上 SHA256SUMS 一致：主书 PDF `563cfd38…` 33,355,599 B、print PDF `9c8023ac…` 17,516,147 B），**HTML 入口与目录页用跳转桩**。实测：旧站 book pdf/print pdf → 200 + application/pdf + 字节哈希一致；book html/book 目录/downloads html → 跳转桩；SHA256SUMS.txt/book-downloads.json/downloads index 为真文件。

**壳仓 v3（2026-11-12 复核补正）**：v2 把 downloads/ 的两个 HTML 也做成桩，但 SHA256SUMS.txt 与 book-downloads.json 覆盖全部 4 文件——用户在旧站执行 `sha256sum -c` 必然失败。已改为：**downloads/ 整体为冻结的 v1.0.0 发布快照**（4 文件全真字节；二进制校验 sha256 全 OK，book-downloads.json 的 bytes/sha256 逐文件 ALL_MATCH）；book/ 的 HTML 仍为跳转桩（该目录无清单约束，PDF 为真字节）。注意环境坑：Git for Windows 的 sha256sum 以文本模式读文件，对 PDF 误报 FAILED（HTML 不受影响）——本仓 P4 阶段已记录同一现象；Windows 侧校验用 python/certutil 二进制读或 CI Linux 为准。旧仓已重新归档。表述纪律：壳仓覆盖 = 131 sitemap 路由（桩）+ book/（PDF 真字节、HTML 桩）+ downloads/（全真字节快照），非「旧站全部跳转」。
