# 通往单片机之路（合并版全书源）

本目录是双书合并后的**唯一书稿与站点源**：46 章（卷 0–7）+ 6 附录，构建入口在仓库根 `book/` 包（`python -m book.build_html`）。

- 目录数据：`manifest.json`（由 `book/mapping.py --write` 从 `book/data/mapping.tsv` 生成，不手工编辑）。
- 章节文件：`v0-foundations/`（语言与构建）、`v1-drivers/`（裸机驱动）、`v2-reliability/`（可靠性与故障）、`v3-rtos/`（RTOS）、`v4-platforms/`（多平台与连接）、`v5-motion/`（运动控制）、`v6-labs-projects/`（实验与项目）、`v7-delivery/`（交付与资料）、`appendix/`（附录 A–F）。
- 测验数据：`.vitepress/data/quizzes/`（各章 `<QuizBank>` 引用）。
- 站点资产：`public/`（anim/figures/images/arch，挂载于 `/STM32/` 根）。
- 旧 `/mcu/**` 深链的跳转存根由 `scripts/legacy-redirects.mjs` 生成（覆盖率 100%，部署时进入 Pages staging 的 `mcu/` 子树）。
- 两书迁移的逐文件去向：`../plans/2026-11-12-merged-book/`（mapping.tsv 141 行 + 各批验收证据）。

写作与正文纪律：[CONTENT_GUIDE.md](CONTENT_GUIDE.md)。
