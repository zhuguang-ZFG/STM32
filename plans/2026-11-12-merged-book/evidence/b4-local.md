# B4 本地验收证据

- 日期：2026-11-14
- 分支：worktree-merged-book-b2（B2→B3→B4 同工作树顺序推进）
- commit：`91e8b84e2ab787fdcfe24b0b0a7625a4bc5718cd`（Task 15 链接收口后验证 HEAD）
- 环境：Windows + Git Bash；Python 3.13.14；Node v24.14.0

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m book.manifest --check` | 0 | 无输出；manifest 与 toc.tsv 一致 |
| `python -m book.mapping --check` | 0 | 无输出；mapping 与源文件一致 |
| `python -m unittest discover book/tests -v` | 0 | 31 tests OK（含 motor 数值断言 5 条） |
| `python -m book.checks --check` | 0 | `checks passed` |
| `python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md docs/v4-platforms/*.md docs/v5-motion/*.md docs/v6-labs-projects/*.md docs/v7-delivery/*.md docs/appendix/*.md` | 0 | `干净：没有机械命中。`（九 glob） |
| `python -m book.build_html --check` | 0 | `built 52 pages, 0 planned chapters missing`（全书 46 章 + 6 附录齐备） |
| `node --test scripts/tests/legacy-redirects.test.mjs` | 0 | pass 2；fail 0 |

## B4 新增 13 个文件名

- `docs/v6-labs-projects/40-lab-method-instruments.md`
- `docs/v6-labs-projects/41-dual-board-logger-project.md`
- `docs/v6-labs-projects/42-project-delivery-acceptance.md`
- `docs/v7-delivery/43-ai-pair-programming.md`
- `docs/v7-delivery/44-manual-reconciliation-hallucination.md`
- `docs/v7-delivery/45-troubleshooting-handbook.md`
- `docs/v7-delivery/46-resources-roadmap-open-source.md`
- `docs/appendix/A-engineering-deep-read.md`
- `docs/appendix/B-project-index.md`
- `docs/appendix/C-exercises-answers.md`
- `docs/appendix/D-glossary.md`
- `docs/appendix/E-sources-version-license.md`
- `docs/appendix/F-open-source-community-map.md`

## 13 组测验 id

与 B3 收口一致（无新增 quiz；ch40–46 与附录无可用 JSON，沿 B2/B3 先例不新造）。

## 章节级验证与提交序列

- ch40：docs/21、docs/22 与 lab 八行（e01–e08 双目标 chNN;ch40）转 migrated；前向链接（ch42/46）延后。
- ch41：PRJ1/PRJ2 迁移；前向链接（ch42）延后；PRJ2 健康段「硬件 watchdog」照抄错误按 PRJ2:83 改写。
- ch42：D19 迁移；五处「待纠正草图」声明随代码同页保留。
- ch43：ai/00、01、03 迁移；「霸道者」→霸天虎；A0–A5 编号改章内引用；ch44/46/附录 E 链接延后。
- ch44：ai/02、04、05 迁移；AI05 数字漂移按重测修正（main:631、题花 101、动画 111、章数 94）；两套门禁按域分列。
- ch45：D18+mbF 迁移；补罗盘契约；失败分支聚合（18 章有节 204 条、两代格式）；mbF 站点问答与在线链接不搬。
- ch46+apC：docs/00、docs/20 与根书 apC 235 行重排迁移；29 节按 mapping 重排章号，一源多目标章双侧列号。
- apA：mcu 五契约骨架 + 根书 F103 双契约并入；寄存器名按平台分列。
- apB：双登记簿（examples 14+补登 motor-dc-speed；code/ 47 工程）；mapping 行修正（apB–F 曾误翻，已恢复 planned 再逐位翻转）。
- apD：统一 4 列（根书 ~130 词条 + mcu 独有词条与新组 ESP32/GD32/语言构建/项目仪器）；三张账原样保留；「原 emoji 图钉 图钉符号」改为「芯片相关」文字角标（emoji 由 mcu 源带入）。
- apE：双命名空间注册表说明（根 94 + mcu 75，ID 禁重号）；许可按域分节；「一笔数字怎样才算钉住」四格段保留。
- apF：mcu 30 仓表为底 + 根书「章」列；九知识点分两组；许可五族表；复刻清单并集；「学习路线收束」页按 mapping 收入末节。

## mapping 迁移摘要

- B4 收口：141 行中 `migrated` 全部完成可迁移项——lab 八行（chNN;ch40）、docs/21/22、PRJ×2、docs/19、ai×6、docs/18、mbF、docs/00、docs/20、附录 12 行全部 `migrated`；剩余 `planned` 均为无落位目标的淘汰/预留行（如 esp32/10/11/13 等映射到尚未规划目标或 B5 处理项，`docs/18–20` 类已在 B4 翻转的除外）。
- `partial` 行清零——所有 partial 的后半目标（ch40）已在本批落位。

## 其他收口动作

- Task 1：175 个资产目标迁移（18 已在库，157 新迁）。
- Task 15：ch40/41 引用式链接内联（10 处引用、7 条定义）；各章延后链接回填（约 18 处）；全文 `grep \]\[ch` 清零（v0 内部 [ch08] 引用式链接属 B1 自身范围，定义存在、checks 通过，不在本批清扫范围）。
- CI slop 扩到九 glob（新增 v6/v7/appendix）。

未验证：CI 远程运行结果；未执行任何远程推送或 Pages 切换；VitePress 站点切换仍归 B5（需发布指令）。

## 批次收口验证

- commit：`2893d087a13d84ebfa03560ca754e432560b1b55`（批次收口提交 HEAD）
- 上表 7 条命令在该 HEAD 重跑，退出码全部为 0：`checks passed`、`built 52 pages, 0 planned chapters missing`、slop 九 glob 无机械命中、31 tests OK、redirects pass 2 / fail 0；工作树干净（除 .qoder 工具目录）。
