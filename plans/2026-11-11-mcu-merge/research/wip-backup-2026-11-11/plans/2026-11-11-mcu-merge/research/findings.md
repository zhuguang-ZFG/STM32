# 合并规划调查记录

日期：2026-11-11。证据仅来自本地 Git 对象、工作区文件和 Trellis 只读上下文；本轮没有运行产品测试、安装依赖、构建书籍或访问线上服务。

## 1. 已确认基线

- 目标分支：`feat/mcu-subtree-merge`；HEAD：`92fc917ca6f0c93f0fc736bf3ea1eab3f8c0aec6`。
- 来源 HEAD：`cf161532c823446016a9deb60d31e5263397b7d7`；来源 tree：`8624f6bcceb90bf8f26d2cc04cbf8f2e30d429fa`。
- 目标 `HEAD:mcu` tree：`93e40d58340884f4d0da88475c382b8f5400fba8`。
- `9ff93300` 的提交消息包含 `git-subtree-dir: mcu` 和上述 source split SHA；来源祖先检查退出码为 0。
- 目标 remote 包含 `mcu-upstream = D:/Users/mcu/.git`；这是本地来源，不能把它当作已经同步的远程在线状态。
- 来源工作区状态只显示未跟踪 `.perch/`；这不代表被忽略的大文件不存在。
- 目标已有 9 个受跟踪修改、7 个未跟踪任务文件和未跟踪 `.qoder/`。本轮未修改它们；字节级保护快照见 [baseline.json](baseline.json)。

## 2. 已导入差异

`git diff --name-status cf161532 HEAD:mcu` 的已提交结果如下。4 个 workflow 移到目标根并带 `mcu-` 名称；其他变化是已做的部分路径适配。

| 状态 | 相对 MCU 项目根的路径 |
| --- | --- |
| D | `.github/workflows/book.yml` |
| D | `.github/workflows/deploy.yml` |
| D | `.github/workflows/links.yml` |
| D | `.github/workflows/quality.yml` |
| M | `README.md` |
| M | `docs/.vitepress/config.mts` |
| M | `scripts/docs-check.mjs` |
| M | `scripts/measure-site.mjs` |
| M | `scripts/search-check.mjs` |
| M | `scripts/seo-check.mjs` |

## 3. 收口问题

| ID | 静态观察 | 风险/处理阶段 |
| --- | --- | --- |
| F1 | VitePress config 与 seo/search 检查已使用 `/STM32/mcu/`；Playwright baseURL/webServer URL 仍为 `/mcu/` | 预览与浏览器测试入口不一致；P2 |
| F2 | `mcu/docs/public/robots.txt` 的 sitemap 仍指向旧 `/mcu/` | 站点身份不一致；P2 |
| F3 | pages/search/seo/docs-check 等测试仍包含旧默认 base 的预期 | 区分真实预期漂移和应保留的通用夹具/负例；P2。未运行，不能声称测试已失败 |
| F4 | `mcu-deploy.yml` 下载到 `mcu/site` 并直接上传该目录；未见创建上传根 `mcu/` 层级 | 与新公开 URL 存在静态结构不一致风险；P3 构建与挂载验证 |
| F5 | 主题 `McuFooter.vue`、`McuHero.vue`、CITATION repository-code 仍指向旧仓；docs-check 自链正则只识别旧仓 | 仓库身份及自链映射需整体收口；P2 |
| F6 | 根 `STRUCTURE.md` 未登记 `mcu/`；根未见 AGENTS，MCU AGENTS 与规范仍在子目录 | 维护入口及 spec 适用范围不足；P1 |
| F7 | MCU 工作流多以 `mcu/**` 触发；部署尚无共享 staging；根 release-fetch 仍固定四个 STM32 文件 | 需定义共享变更触发与独立产物发布；P3 |
| F8 | MCU Trellis 当前报告 single-repo、8 个 spec 层、23 个活动任务、无当前任务 | 不能直接把框架根搬到父目录或改写所有上下文路径；P1 |
| F9 | 既有 `historical-spec-closure` 工作区含新设计/证据及 CITATION URL 修复 | 必须保留已有工作，合并计划不能替代历史任务验收；P0/P4 |

## 4. 已读取的约束

- `mcu/AGENTS.md`、`mcu/.trellis/workflow.md`、`mcu/.trellis/spec/index.md`、guides、docs-site/book 索引及质量合同。
- 根 `README.md`、`STRUCTURE.md`、`Makefile`、`LICENSE`、`.gitignore` 和 `stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md` 的适用与裁定段落。
- 根 Book/MCU/Release workflows、MCU package scripts、站点配置、路径检查器、浏览器配置和受影响测试。
- 既有历史收口任务的上下文、基线漂移及 W1 证据用于识别已有工作边界，不把其中的旧结论当作本轮重新验证结果。

本次采用 `trellis-start` 读取上下文与规划约定。初次 Python 在沙箱内被拒绝，获准后运行三个只读上下文命令成功。文件扫描在部分根 `tools/sample_figs_quality*` 和缓存目录遇到访问限制；未将这些目录视为已完整审计。本次规划不依赖这些目录的内容结论。

## 5. 本次交付边界

计划作为跨仓库集成文档放在根 `plans/`，没有创建、启动或覆盖 MCU 的历史 Trellis 任务，没有修改当前任务指针。需求、设计、实施清单分别维护，便于实施时转成任务并按阶段验收。

远程主线/PR、真实 CI、部署设置、线上 URL、忽略资产完整性及产品构建状态均留待实施验证。任何“已完成合并”结论都必须补齐 PRD 的验收证据。
