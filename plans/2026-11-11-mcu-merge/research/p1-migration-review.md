# P1 迁移差异与规范取舍审查

日期：2026-11-11
范围：只读复核 `cf161532...`（来源 HEAD）→ `HEAD:mcu` 的 10 路径已提交差异，对照 `research/baseline.json`、`research/findings.md`、`design.md`、`prd.md`。本文件不改变 `mcu/` 历史，不修改历史任务状态。

## 1. 10 路径差异复核（与 baseline 一致）

| 状态 | 路径 | 审查结论 |
|---|---|---|
| D | `mcu/.github/workflows/book.yml` | 有意迁移：MCU 书籍 workflow 已在目标根以 `mcu-book.yml` / 根路径适配形式承载（P3 仍需核实触发与汇总）；子树内删除避免双维护。 |
| D | `mcu/.github/workflows/deploy.yml` | 有意迁移：部署职责迁至根 `mcu-deploy.yml`/Pages staging 组装链路（P3 收口）。子树内旧部署入口删除是预期定制。 |
| D | `mcu/.github/workflows/links.yml` | 有意迁移：外链/检查职责由根 MCU workflow 承接；删除子树副本避免并行失效。 |
| D | `mcu/.github/workflows/quality.yml` | 有意迁移：质量门迁至根 `mcu-quality.yml`；保留完整门槛属 P4/AC5 约束。 |
| M | `mcu/README.md` | 有意定制：增加迁移注记、指向 `zhuguang-ZFG/STM32` 与 `/STM32/mcu/` 新入口；保留 Apache-2.0 与 MCU 内容边界声明。后续 P2 需继续核对仓库/站点身份一致性（F5 类）。 |
| M | `mcu/docs/.vitepress/config.mts` | 有意定制：站点 base/身份向 `/STM32/mcu/` 对齐（findings F1/F2/F3 表明仍有非 config 消费者待 P2 统一）。 |
| M | `mcu/scripts/docs-check.mjs` | 有意定制：文档检查适配新子树/路径上下文；P2 需与共享 site-config 和旧路径负例策略协同。 |
| M | `mcu/scripts/measure-site.mjs` | 有意定制：测量脚本适配新 base/挂载前提；P3 浏览器/挂载冒烟需以实际 staging 为准。 |
| M | `mcu/scripts/search-check.mjs` | 有意定制：搜索检查适配新路径；P2/P3 保留旧 base 负例与新 base 正例。 |
| M | `mcu/scripts/seo-check.mjs` | 有意定制：SEO/robots/sitemap 检查向新身份收敛；findings F2 记录 `docs/public/robots.txt` 等仍需 P2 审查。 |

## 2. 设计取舍确认

- **subtree 增量整合（已执行）**：来源 SHA 为祖先，差异仅 10 路径，符合“保留来源历史、避免重复导入”。
- **单仓双书、分域维护**：根 STM32 体系（`docs/`, `examples/`, `stm32-book/`）与 MCU 体系（`mcu/docs/`, `mcu/code/`, `mcu/mcu-book/`）并存；本 P1 只补入口/路由，不做内容重编或章节合并。
- **删除子树 workflow、保留根承接**：策略正确，但 P3 需证明触发矩阵、artifact 结构、Pages 挂载与根 release 不互相破坏。
- **路径/身份已部分收口但未完成**：config 与部分脚本已改，Playwright/robots/主题/CITATION/测试预期等仍是 P2 风险（findings F1–F5、F7）。

## 3. 风险与后续门

- P2：统一 `mcu/scripts/site-config.mjs`（或等价单一来源）消费链，补新 base 正例/旧 base 负例，禁止字面量漂移。
- P3：staging 根含 `mcu/`、`mcu/index.html`、资源与深链在 `/STM32/` 挂载下可用；触发矩阵与汇总规则可解释。
- P4：两套验证门完整保留并留证；本轮 P1 不运行构建/测试门（避免无关耗时与环境误判），仅做规范与证据落盘。

## 4. 结论

10 路径迁移差异**可解释、与 subtree 收口目标一致**；不存在已发现的内容丢失证据。后续以 P2/P3/P4 验证闭环替代“字符串已改即完成”的判断。
