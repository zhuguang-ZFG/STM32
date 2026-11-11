# B7 批次报告：第四部分 FreeRTOS + 双 OS 对照（rtos/freertos 9 + compare 2，11 章）

日期：2026-10-26 · 机械层（主代理）+ 3 小单代理修复 · 主代理字节级对 HEAD 复验

## 计数表（vs HEAD，散文面）

| 章 | ——散文 | 门 |
|---|---|---|
| freertos/00-why-rtos | 36→1 | ✓ |
| freertos/01-task-tcb | 30→0 | ✓ |
| freertos/02-context-switch | 44→2 | ✓（围栏注释+表格 2 处代理违改，主代理从 HEAD 还原） |
| freertos/03-scheduler | 27→1 | ✓ |
| freertos/04-queue | 24→1 | ✓ |
| freertos/05-sem-mutex | 22→2 | ✓ |
| freertos/06-notify-event-timer | 33→2 | ✓ |
| freertos/07-heap | 25→0 | ✓ |
| freertos/08-port-f407 | 34→0 | ✓ |
| compare/00-side-by-side | 26→10→0+？| ✓（含机械层） |
| compare/01-choose | 21→1 | ✓ |

合计散文 —— 317→~13。

## 过程事件

1. **大单代理三连超时**（15min 上限）：A/C/D 原始分派全灭。改派 1-3 章小单（B7Fix1/2/3）全部完成——**单章级小单是可靠颗粒度**，固化为后续批次默认。
2. **02 围栏注释+表格违改**：Fix2 代理把围栏内注释与表格行的 `——` 也改了。主代理按"受保护行以 HEAD 为准"逐行还原（表格/标题/围栏行字节级取 HEAD），散文改动保留。此还原脚本可复用。
3. rtthread 8 章不在本批（B8 范围），HEAD 对照按目录过滤。

## 产物

docs/rtos/freertos/00-08 + compare/00-01 落盘。累计 70/94。
