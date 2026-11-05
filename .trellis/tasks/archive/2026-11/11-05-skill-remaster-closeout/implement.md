# 实施计划

## 规划审阅

- [x] 读原 spec、工作树基线及 docs-site 结构/质量契约。
- [x] 用户已授权规划并实现；采用原 spec 推荐的卡片 A 方案，保留主句和小注。
- [x] PRD/设计/实施计划已落盘；inline 主会话负责实施与检查。
- [x] `task.py start` 切换为 in_progress。

## 实施

1. [x] 保存本轮文字与文件基线；把卡片 HTML/CSS 与截图产线转入正式源码目录。
2. [x] 调整居中内容组，重渲 29 张竖版卡；保留横版封面并生成正式联系表。
3. [x] 生成同源精排导读，修正链接与附录口径，接入站点书籍入口。
4. [x] 复验 PPT 静态/备注校验器及模板同步；浏览器基本链路通过，扩展验证结果见 research/verification.md。
5. [x] 桌面/手机浏览器检查卡片、导读与入口，补 2 项正式浏览器回归；记录截图与报告。
6. [x] 更新旧 specs 的未决状态、代码规范与任务验收记录。

## 验证

- 卡片产线 `--check`：文字基线、主句来源、内容间距、文字边界、PNG 尺寸和联系表图片。
- 导读生成器 `--check`：源哈希、站点 base、入口与链接；浏览器 390px/1440px 验证。
- skill 的 `validate-presenter-mode.mjs`、`validate-swiss-deck.mjs`、`check-presenter-runtime-sync.mjs`。
- `npm run quality`（内含 docs:check/reading:check/docs:build/122 项单元测试等门禁）。
- `python -m pytest mcu-book/tests`；未改书稿排版与正文，不重复构建整本 PDF。
- `npx playwright test book-guide.spec.mjs`：2 项正式浏览器测试；本轮复用运行中的 preview，通过 `.temp/skill-closeout/playwright.config.mjs` 把 `reuseExistingServer` 设 true。
- 只提交本轮拥有的文件；既有卡片/旧 spec 的用户改动单独保留。

## 回滚点

正式资产生成前保存基线；生成器先验证再接受产物。任何失败修复后只复跑受影响门；旧路径不删除。

## 收口

- [x] 卡片/导读命令、测试和规范已交付；旧用户文件保留。
- [x] 最终质量门全绿；PPT 扩展验证包括冻结时暂停自动翻页、恢复后继续、排练记录及圈选/激光工具。
- [x] Phase 3.4 用户回复「继续下一步」确认提交计划，按三项分组提交；产线 `afd543f`、检查器 `08d0c3c`，规范和本任务为第三项。不并入会话开始前的卡片、旧 spec 历史差异或未跟踪 PPT。
- [x] 三项 work commit 已完成：`afd543f`、`08d0c3c`、`696c194`。本轮任务已归档至 `.trellis/tasks/archive/2026-11/11-05-skill-remaster-closeout/`，task.json 为 completed；归档与 journal 分别独立提交。
