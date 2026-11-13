# B2 本地验收证据

- 日期：2026-11-14
- 分支：worktree-merged-book-b2
- commit：`401bf3ddc6e2df5719d7e96c4358e8d64064b740`（验证时 HEAD，含 Task 12 链接清扫）
- 环境：Windows + Git Bash；Python 3.13.14；Node v24.14.0

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m book.manifest --check` | 0 | 无输出；manifest 与 toc.tsv 一致 |
| `python -m book.mapping --check` | 0 | 无输出；mapping 与源文件一致 |
| `python -m unittest discover book/tests -v` | 0 | Ran 30 tests；OK |
| `python -m book.checks --check` | 0 | `checks passed` |
| `python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md` | 0 | `干净：没有机械命中。`（四个 glob） |
| `python -m book.build_html --check` | 0 | `built 27 pages, 25 planned chapters missing` |
| `node --test scripts/tests/legacy-redirects.test.mjs` | 0 | pass 2；fail 0 |

## B2 新增 10 章文件名

- `docs/v2-reliability/18-low-power.md`
- `docs/v2-reliability/19-watchdog-reset-hardfault.md`
- `docs/v2-reliability/20-debug-performance.md`
- `docs/v3-rtos/21-why-rtos.md`
- `docs/v3-rtos/22-tasks-tcb-scheduler.md`
- `docs/v3-rtos/23-context-switch-porting.md`
- `docs/v3-rtos/24-queue-semaphore-notification.md`
- `docs/v3-rtos/25-memory-management.md`
- `docs/v3-rtos/26-device-framework-shell.md`
- `docs/v3-rtos/27-rtos-comparison-selection.md`

## 13 组测验 id

B1 的 10 组：`c03-volatile`、`s02-rcc-clock`、`s03-gpio`、`s04-nvic`、`s06-tim`、`s07-usart`、`s08-dma`、`s09-adc`、`s11-i2c`、`s12-spi`
B2 新增 3 组：`s14-pwr`（含勘误）、`f4-queue`（Q5 阻断性勘误）、`f7-heap`（Q2/Q4 措辞微调）

## 章节级验证与评审轮

每章走「feat 提交 → 评审修复轮 → fix 提交」：

| 章 | feat | fix 轮要点 |
| --- | --- | --- |
| ch18 | 0a1b051a | probe count、链接与读数（276dc5cb） |
| ch19 | 67b427df | 看门狗窗口与复位标志（3ec1ccf8） |
| ch20 | 1d879026 | 来源、插图与断点预算（f88d08e4） |
| ch21 | 8fc53a90 | 阻塞成因与来源行号（c9bd45ca） |
| ch22 | aaea417d | yield 宏、位图与 RT-Thread 字段（051d2bea） |
| ch23 | 2afd17b9 | 无独立 fix 轮（随 feat 提交复审通过） |
| ch24 | 67ac208d | 速度断言与队列摘录（19eb04fe） |
| ch25 | 4be84405 | 表格渲染、heap_2/heap_5/slab 措辞（602535d2）；Mallock 拼写、手绘板题注、RT-Thread stats 行（8bfac459） |
| ch26 | 921bb284 | 引脚组号表述、V2 回调上下文、finsh_syscall 字段、list_thread 原型、Q18 实验口径（55b73796） |
| ch27 | 844d915f | 删「以人月计」、ch18 口径引用、实时性表述（5c0e4139） |

## mapping 迁移摘要

- B2 收口时 `migrated`：B1 各章（root `docs/01–17`）、B2 涉及的根书章（`docs/11`、`docs/15`、`docs/16`、`docs/17`、`docs/28`）、RTOS 深潜源（`mcu/docs/rtos/freertos/00–08`、`rtthread/00–06`、`compare/00–01`）。
- 保持 `partial`：`mcu/docs/lab/e04-priority-inversion.md`、`e06-lowpower-current.md`（等 B4 的 ch40）；其余 lab 各章同样 `partial`。
- `docs/18–20`（FAQ/项目实战/资源）映射到 ch45/ch42/ch46（B4 目标），仍 `planned`。

## 其他收口动作

- Task 12：B1 前向引用清扫完成——20 条 `[chNN]` 定义删除、35 处引用改为 inline（401bf3dd）；`ch10/ch28–31/ch34/ch40` 等 B3/B4 目标的残留定义按计划保留。
- `.github/workflows/merge-check.yml` 的 slop 行扩到四个 glob（随本批 CI 提交）。
- 插图手绘回访（8eae93e3）：ch18 加 `ch16-battery-budget`、ch19 加 `ch18-hardfault-ladder`、ch24 加 `ch15-prio-inherit` 三块手绘知识板（PNG 入 `docs/public/images/`）；加上 ch25/26/27 各自的手绘板，B2 十章每章至少一块手绘图，已在 `book/dist/site` 抽查渲染。

未验证：CI 远程运行结果；未执行任何远程推送或 Pages 切换；VitePress 站点切换仍归 B5。

## 批次收口验证

- commit：`09b9d2c66cf78157ce7e85b4f3b6d56af3c5a649`（Task 13 收口提交 HEAD）
- 上表 7 条命令在该 HEAD 重跑，退出码全部为 0：`checks passed`、`built 27 pages, 25 planned chapters missing`、slop 四 glob 无机械命中、30 tests OK、redirects pass 2 / fail 0。
