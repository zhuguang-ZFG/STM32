# Phase 3.4 提交计划（已获一次性确认）

2026-11-05 用户在提交计划与归档确认问题后回复「继续下一步」，本轮按该计划执行。产线提交 `afd543f`、检查器提交 `08d0c3c`；第三项规范/任务提交随后完成，最终提交号记入 journal。

## 1. feat(content): 收口金句卡产线与精排导读入口

- `scripts/social-cards/`：29 张卡源、共享 CSS、横版封面源、生成/检查命令和说明。
- `video/assets/social-cards/book/`：30 张正式 PNG、manifest 与联系表。
- `scripts/book-guide/`、`docs/public/book-guide/`：导读生成器、契约、CSS、说明与正式 HTML/manifest。
- `docs/reference/book.md`、`package.json`：读者入口、附录笔误和四条产线命令/构建前置门。
- `tests/book-guide.test.mjs`、`tests/browser/book-guide.spec.mjs`：过期、篡改和 2 种视口入口回归。

## 2. fix(checks): 忽略内联脚本和样式中的伪锚点

- `scripts/pages-check.mjs`
- `tests/pages-check.test.mjs`

## 3. docs(trellis): 登记传播资产契约与实现验收

- `.trellis/spec/docs-site/index.md`
- `.trellis/spec/docs-site/quality-contract.md`
- `.trellis/spec/docs-site/presentation-assets.md`
- `.trellis/tasks/11-05-skill-remaster-closeout/`（规划、任务状态、复验脚本/报告与复盘）

## 排除并保留工作区的既有文件

- 旧任务 `.trellis/tasks/11-02-skill-remaster/deliverables/` 的 13 张已修改 PNG。
- 旧任务未跟踪的 `deliverables/ppt/`（本轮验证，未改动）。
- 旧任务 `specs.md`、`deliverables/review-sheet.html`：包含会话前说明修订与本轮收口记录，暂不把整文件混入本轮提交。当前更新全部保留。

确认以上三个 work commit 后，再按 finish-work 归档**本轮任务**并记录 journal；不清理或归档其他任务，不推送远端。
