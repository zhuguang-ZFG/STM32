# 通往单片机之路（合并版全书源）

本目录是双书合并后的**唯一书稿与站点源**：47 章（上手卷 + 卷 0–7）+ 6 附录，构建入口在仓库根 `book/` 包（`python -m book.build_html`）。

- 目录数据：`manifest.json`（由 `python -m book.manifest --write` 从 `book/data/toc.tsv` 生成，不手工编辑；`python -m book.manifest --check` 校验是否过期）。
- 旧章到新章的逐文件映射：`book.mapping --write` 写出 `../plans/2026-11-12-merged-book/mapping.json`（源数据 `book/data/mapping.tsv`），与上面的 `manifest.json` 不是同一份产物。
- 章节文件：`onramp/`（上手 · 从开箱到点灯）、`v0-foundations/`（语言与构建）、`v1-drivers/`（裸机驱动）、`v2-reliability/`（可靠性与故障）、`v3-rtos/`（RTOS）、`v4-platforms/`（多平台与连接）、`v5-motion/`（运动控制）、`v6-labs-projects/`（实验与项目）、`v7-delivery/`（交付与资料）、`appendix/`（附录 A–F）。
- 测验数据：`.vitepress/data/quizzes/`（各章 `<QuizBank>` 引用）。
- 站点资产：`public/`（anim/figures/images/arch，挂载于 `/STM32/` 根）。
- 旧 `/mcu/**` 深链的跳转存根由 `scripts/legacy-redirects.mjs` 生成（覆盖率 100%，部署时进入 Pages staging 的 `mcu/` 子树）。
- 两书迁移的逐文件去向：`../plans/2026-11-12-merged-book/`（mapping.tsv 141 行 + 各批验收证据）。

写作与正文纪律：[CONTENT_GUIDE.md](CONTENT_GUIDE.md)。

学习入口：[第 46 章的五阶段能力目标与 47 章依赖索引](v7-delivery/46-resources-roadmap-open-source.md)（区分硬先修与推荐阅读，沿用 L0–L5）；动手取证：[实验目录](../labs/README.md)（含点灯/PWM/UART，均保留未实测状态）。
