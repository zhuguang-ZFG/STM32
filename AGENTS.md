# AGENTS（仓库根路由）

本文件是 **Git 仓库根** 的路由入口，不复制各域规则正文。按改动域读取权威文档后再动手。

## 三个根与工作目录

| 身份 | 路径 | 说明 |
| --- | --- | --- |
| Git 仓库根 | 本文件所在目录（如 `D:\Users\STM32` / 收口 worktree `D:\Users\STM32-mcu-merge-p1`） | 根域 STM32 书、`plans/` 合并证据、跨域入口 |
| MCU 项目根 | `<Git根>/mcu` | MCU 子树独立上下文：VitePress/脚本/固件/书籍门、Trellis 任务与 spec |
| 对外站点根 | `/STM32/mcu/` | MCU 站点挂载前缀；旧 `/mcu/` 仅迁移负例（P2/P3 收口中） |

命令、Trellis 脚本与路径解析须在对应根执行/解释，不可混用。

## 路由

### 1) STM32 知识库（根域：`docs/`、`examples/`、`stm32-book/`、`cheatsheets/`、`assets/`、`tools/`、`labs/`、`sim/` 等）

- 写作与正文纪律：[`docs/CONTENT_GUIDE.md`](docs/CONTENT_GUIDE.md)
- 目录与边界地图：[`STRUCTURE.md`](STRUCTURE.md)、[`README.md`](README.md)
- 整书/长课/收口规格（权威正文在各自文件中）：
  - [`stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md`](stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md)
  - [`stm32-book/BOOK_REDESIGN_SPEC.md`](stm32-book/BOOK_REDESIGN_SPEC.md)
  - [`stm32-book/BOOK_VIDEO_CLASSIC_SPECS.md`](stm32-book/BOOK_VIDEO_CLASSIC_SPECS.md)
- 超级能力/设计规格索引：[`docs/superpowers/specs/`](docs/superpowers/specs/)（按需读取具体 spec）

### 2) MCU 姊妹书子树（`mcu/`）

- 项目级代理与工作流指引（含 Trellis 管理块，勿在此复制）：[`mcu/AGENTS.md`](mcu/AGENTS.md)
- MCU 规范索引与分层质量门：[`mcu/.trellis/spec/index.md`](mcu/.trellis/spec/index.md)、[`mcu/.trellis/workflow.md`](mcu/.trellis/workflow.md)
- 内容边界与读者入口：[`mcu/README.md`](mcu/README.md)、[`mcu/docs/index.md`](mcu/docs/index.md)
- 任务与历史记录：[`mcu/.trellis/tasks/`](mcu/.trellis/tasks/)（历史状态/证据不因路径迁移自动改写；AC6）

### 3) subtree 合并收口计划（跨域）

- [`plans/2026-11-11-mcu-merge/prd.md`](plans/2026-11-11-mcu-merge/prd.md) — 目标、非目标、R1–R8、AC1–AC8
- [`plans/2026-11-11-mcu-merge/design.md`](plans/2026-11-11-mcu-merge/design.md) — 架构与组件设计
- [`plans/2026-11-11-mcu-merge/implement.md`](plans/2026-11-11-mcu-merge/implement.md) — P0–P5 实施与放行
- [`plans/2026-11-11-mcu-merge/research/findings.md`](plans/2026-11-11-mcu-merge/research/findings.md)、[`research/baseline.json`](plans/2026-11-11-mcu-merge/research/baseline.json) — 调研与基线证据

## 纪律（路由级）

- **分域维护**：根域与 `mcu/` 域分开改动；同名文件不覆盖式合并，跨书改交叉链接。
- **不复制规则正文**：以目标域权威文件为准；本文件仅指路。
- **门禁不降级**：STM32 与 MCU 既有验证门完整保留；通过/失败/未验证分开报告。
- **历史保真**：不因 subtree/路径调整自动归档任务或将历史状态改为通过。
- **发布受控**：本收口未合并/未发布；P5 需明确指令与 AC1–AC8 证据。
