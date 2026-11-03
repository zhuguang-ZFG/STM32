# AI 辅助开发内容加深 设计

## 结构

- 第十一部 id `pa`，目录 `docs/ai/`，章号 A0–A5 共 6 章；插于第十部（pj 双板综合项目）之后、附录之前。
- 章源文沿用全书惯例：frontmatter（title/status/difficulty/minutes）+ 🎯 定位引语 + 本章精髓三条 + 能理解/能用 + 先修 + 小节结构 + **记忆锚点 + `::: tip 一句话记住` 容器 + `✅ 下一站` achievement div**；A5 为全书正文末章，下一站指向附录区而非下一部。

## 章节与罗盘（chapter_guides 条目）

| 章 | 文件 | 内容 | 罗盘 question / deliverable / boundary |
|---|---|---|---|
| A0 | 00-pair-not-ghost.md | 定位与工具地图：结对工程师非代笔；学习/工作两阶段用法；2026 工具地图 | AI 都能写出能跑的代码了，我为什么还要学寄存器和 RTOS？/ 一张「模型能替你做与不能替你做」清单 + 工具地图 / 只立工作观，对账在 A2、提示词在 A1，不展开模型原理 |
| A1 | 01-prompt-patterns.md | 提示词模式：上下文（芯片/手册章节/板卡）+ 约束（资源/时序/风格）+ 验收（可编译/上板现象/对账动作）三段式 | 同样一个外设需求，为什么有人一句话搞定、有人贴五十行还被带偏？/ 三段式模板 + 弱强提示对照实录 / 工具配置在 A3，验收细则在 A2 |
| A2 | 02-manual-reconciliation.md | 手册对账闭环：生成 → RM0090 逐位对账 → 上板验证 → 回喂 | 模型给的 RCC 配置能过编译，烧进去没反应，错在哪一位？/ 以 S 篇已学外设为例的逐位对账流程 / 只讲验证流程，外设不重教 |
| A3 | 03-toolflow-mcp.md | MCP 与工具流：模型读手册/跑构建/看串口；agent 权限与安全边界 | 让模型自己看手册跑构建，和把错误粘给它差在哪？/ 工具流图 + 三场景 + 权限边界 / 消费侧为主，不教自建 MCP server |
| A4 | 04-hallucination-defense.md | 幻觉防御：假位定义/假库函数/假芯片特性类型学 + 验证决策树 | 模型编的寄存器名能有多像真的？/ 案例类型学 + 「什么必须查手册」决策树 / 案例以 STM32/ESP32 已知外设为主 |
| A5 | 05-this-book-pipeline.md | 压轴自证：本书 AI 生产线解剖——Trellis 工作流、13 门印前守卫、寡行守卫调试，file:line 引证 | 「把大模型当结对工程师」到底灵不灵？这本书就是实验 / 生产线解剖 + 证据引证 / 讲工作流证据，不讲工具安装 |

## 插图（13 枚）

- 部隔页题图：`art.py part_art("pa")` **显式新分支**（否则末尾 `return ""` 静默出空隔页，13 门与 art_guard 都不报）——主题：人机结对（对话气泡+芯片）；新增测试断言 manifest 每个 part id 的 part_art 非空。
- 6 枚章题花 `mcu-book/book/assets/chapter-art/ai-NN-*.svg`（装饰位）：320×88、≤6000B、纯矢量、无 filter/id/url、fill/stroke 只用 var(--cover-ink)、≥2 档笔压、纯 LF。
- 6 张内联机制图 `docs/public/anim/ai-*.svg`（生动形象的主力，无 320×88 限制）：ai-tool-map（A0）/ ai-prompt-anatomy（A1）/ ai-reconcile-loop（A2）/ ai-mcp-toolflow（A3）/ ai-hallucination-tree（A4）/ ai-book-pipeline（A5）；**必须过字体门**（SVG 文字不引系统字体/Type3，遵循 P2 净化口径）。
- 顺修 `build_html.py:790` 过时 docstring（hw-<章id> filter id 说法已被 :801 守卫否定）。

## manifest / 站点联动

- `manifest.json`：parts 插 pa（files: docs/ai/6 章）；chapter_guides +6（上表）；sources +外部官方文档条目（Copilot/Claude Code/Cursor/MCP 规范，含访问日期）→ 附录 E 来源卡自动收录。
- `docs/.vitepress/config.mts`：侧栏 +第十一部 6 章。
- 前言阅读图：双板项目之后加「AI 辅助开发」收尾支线说明。
- `mcu-book/tests/test_build.py:230/232/235` 硬编码 10 部/88 章/88 节——**改为从 manifest["parts"] 推导**（沿用 :237 附录处的既有做法），不是简单把 10→11。

## 写作与守卫流程

1. **研究**：外部事实采集（Copilot/Claude Code/Cursor/MCP 官方文档，当前事实 + URL + 访问日期）→ sources 清单 + 每章事实 token 候选；RM0090 对账案例页码。
2. **试点章 A2 先行**：成稿 + 插图 + 口癖门跑通后交用户评审（沿用 10-26 试点批规矩）；通过后才放行 A0/A1、A3/A4 两批各 2 章，A5 由主线亲自执笔（自证章需引仓库 file:line）。
3. **起草验收条件**（发子代理时随任务下发）：de-ai 风格指南 + 口癖阈值——`——` 散文面 ≤2/章（新部预算，全书均值 1/章）、散文本体「一句话」/「记住：」0（容器标签 `::: tip 一句话记住` 不计入）。
4. **机器门**：`mcu-book/tools/prose_guard.py` 加单文件模式（复用 MARKERS/prose_surface），新章逐章计数；事实 token 多重集断言复用 10-26-prose-polish 基建。
5. **重建 + 全套电池**（见下）。

## 验证电池

- 在线：VitePress 构建过（脚本名以 package.json 为准，实施时先核实）；侧栏与 anim 引用正确。
- 印前：`python mcu-book/build_print.py` → `python mcu-book/check_pdf.py mcu-book/dist/mcu-deep-book-print.pdf`（13 门）→ `.temp/widow_detect.py` 真寡行 0 → `.temp/orphan_head_check.py` 0 → U+2011 grep 0 → 全书 `get_drawings()` 空内联灰点 0 → 字体门 0 Type3。
- 测试：`pytest mcu-book/tests/`（含新增 part_art 覆盖与既有 67 项）+ `python mcu-book/tools/art_guard.py --dir mcu-book/book/assets/chapter-art`。
- 验收：用户过目插图生动度与文字详细度（对照附录 A/F 深度）。

## 风险与对策

- 工具 UI 时效性：来源卡 + 访问日期；正文口径「界面会变，方法论不变」；零截图，纯矢量示意。
- 篇幅膨胀：每章源文 400–600 行硬预算，超限砍例子不砍验证流程。
- 题图被对抗写回滤镜版：art_guard + test_print_vectors 已有门，新枚同受保护。
- A5 file:line 引证漂移：成稿时以当期仓库为准，印前复查一遍。
