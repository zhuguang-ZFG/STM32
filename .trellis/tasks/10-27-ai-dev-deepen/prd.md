# AI 辅助开发内容加深：把大模型当结对工程师写进书里

## Goal

为成书**新增第十一部「AI 辅助开发」**：教读者把大模型用作单片机开发的结对工程师——手册对账、寄存器级代码生成与验证、提示词模式、MCP 工具流、幻觉防御。插图生动形象、文字详细；案例主线为**混合式**：通用工具走查（读者可照做）为主 + 本书自身 AI 生产流水线压轴自证。落地后全书重建 + 印前全套复验。

## Background（仓库取证）

- 书结构：10 部 / 140 章 + 7 附录（A–G），`mcu-book/manifest.json:13-219`；正文章节源文在 `docs/`，附录源文在 `mcu-book/book/`；部隔页题图 `mcu-book/print/art.py`（94 枚无滤镜纯矢量，commit c6f133d）+ `mcu-book/tools/art_guard.py`；内联图惯例 `docs/public/anim/*.svg`。
- 现状：成品 PDF 全文扫描确认书中**没有**「AI 辅助开发」内容（仅小智语音线与 PLLM 假阳性）；本部为全新内容，不是既有内容改写。
- 章源文惯例：frontmatter（title/status/difficulty/minutes）+ 🎯 定位引语 + 本章精髓三条 + 能理解/能用 + 先修 + 先跑起来 + 小节结构 + 记忆锚点 + 自测（参照 `docs/esp32/12-audio-path.md`）；`manifest.json chapter_guides` 每章一条 {question, deliverable, boundary} 罗盘。
- 在线版联动：`docs/.vitepress/config.mts` 侧栏逐章登记（如 :275）。
- 印前验证管线：`mcu-book/build_print.py`（~350s）→ `check_pdf.py` 13 门 + `tests/`（67 passed）+ 寡行/孤儿/U+2011/灰点扫描电池（本轮建立）。
- 本书自身即 AI 辅助产物（Trellis 工作流、证据门、寡行守卫调试全程留痕）——压轴章素材，仓库内可引 file:line。
- 既有文字精修守卫基建在任务 `10-26-prose-polish`（事实 token 多重集断言），新章成稿后复用。

## Requirements

- R1 **新增第十一部**（用户拍板 2026-10-27）：插在第十部（双板综合项目）之后、附录之前。manifest.parts +1、部隔页 + 部题图、`docs/ai/` 新目录若干章、chapter_guides 补罗盘、config.mts 侧栏、前言阅读图联动。章节分解见 design.md。
- R2 内容主题（用户要求「文字要详细」）：
  - 定位与工具地图：大模型是结对工程师不是代笔；学习阶段 vs 工作阶段用法差异。
  - 提示词模式：嵌入式场景的上下文/约束/验收标准结构，弱提示 vs 强提示真实对比。
  - 手册对账方法论：AI 生成寄存器代码对着 RM0090/数据手册逐位验证（本书方法论的延伸）。
  - MCP 与工具流：让模型读手册、跑构建、看串口日志的工具化工作流。
  - 幻觉防御：假位定义/假库函数/假芯片特性的案例类型学与验证动作。
  - 压轴自证：本书自身的 AI 生产流水线（Trellis、13 门、寡行守卫故事），file:line 引证。
- R3 插图（用户要求「插图生动形象」）：新条目题图走 art.py 既有管线；内联 SVG 约 4 张（提示词解剖、对账工作流、幻觉防御决策树、MCP 工具流架构），风格与既有题图/anim 一致；**必须过字体门**（SVG 文字不得引入系统字体/Type3，遵循已收口的 P2 净化口径）。
- R4 外部素材登记：Copilot/Claude Code/Cursor/MCP 官方文档等来源进 `manifest.json sources`（含访问日期），正文引用走既有来源卡机制。
- R5 重建后全套复验：13 门、真寡行 0、孤儿标题 0、U+2011 0、全书空内联灰点 0、pytest、art_guard、大纲/目录/索引页码正确。

## Acceptance Criteria

- [ ] manifest（parts/chapter_guides/sources）与 config.mts 侧栏、前言阅读图均含第十一部；书签大纲层级正确（部 22→23 侧计数随构建器口径）。
- [ ] 印前 13 门全过；真寡行 0、孤儿标题 0、U+2011 0、空内联灰点 0（全书矢量扫描）。
- [ ] pytest 全过；art_guard 全过。
- [ ] 新 SVG/题图不引入系统字体（字体门 ✓）。
- [ ] 用户验收：插图生动、文字详细（与附录 A/F 同级深度）。

## Out of Scope

- 小智语音助手线（用户已排除）。
- 印前管线/守卫机制改动（已收口于 commit 4bf0308）。
- 新配套工程（各章引用既有板卡与工程作例）。

## Open Questions

（无——设计评审待用户确认后进入实施。）
