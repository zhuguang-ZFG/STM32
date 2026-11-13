# B3 本地验收证据

- 日期：2026-11-14
- 分支：worktree-merged-book-b2（B3 与 B2 同工作树顺序推进）
- commit：`ffa988616a315cf46a2a9c995fc5441bd4ad1dfb`（Task 16 链接清扫后验证 HEAD）
- 环境：Windows + Git Bash；Python 3.13.14；Node v24.14.0

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m book.manifest --check` | 0 | 无输出；manifest 与 toc.tsv 一致 |
| `python -m book.mapping --check` | 0 | 无输出；mapping 与源文件一致 |
| `python -m unittest discover book/tests -v` | 0 | 31 tests OK（30 基线 + test_motor_numbers 5 条：位置钉、PWM 算术/锚点/负向哨兵、带宽算术/锚点/负向哨兵） |
| `python -m book.checks --check` | 0 | `checks passed` |
| `python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md docs/v4-platforms/*.md docs/v5-motion/*.md` | 0 | `干净：没有机械命中。`（六个 glob） |
| `python -m book.build_html --check` | 0 | `built 39 pages, 13 planned chapters missing` |
| `node --test scripts/tests/legacy-redirects.test.mjs` | 0 | pass 2；fail 0 |

旧书套件（`python -m unittest discover stm32-book/tests`）在删除 `test_motor_draft_numbers.py` 后重跑 OK（含旧书 29 章 HTML 构建）——守卫对象已迁至 `book/tests/test_motor_numbers.py`，先加后删时序完成。

## B3 新增 12 章文件名

- `docs/v4-platforms/28-chip-migration-differences.md`
- `docs/v4-platforms/29-gd32-arm-riscv.md`
- `docs/v4-platforms/30-esp32s3-architecture-boot.md`
- `docs/v4-platforms/31-esp32-drivers-audio.md`
- `docs/v4-platforms/32-esp32-wifi-ble-espnow.md`
- `docs/v4-platforms/33-network-protocol-stack.md`
- `docs/v4-platforms/34-multicore-cache.md`
- `docs/v4-platforms/35-can-usb-fieldbus.md`
- `docs/v5-motion/36-motor-driver-power.md`
- `docs/v5-motion/37-dc-motor-openloop.md`
- `docs/v5-motion/38-encoder-speed-measurement.md`
- `docs/v5-motion/39-speed-closed-loop-pi.md`

## 13 组测验 id

与 B2 收口一致（c03-volatile、s02–s12 十组、s14-pwr、f4-queue、f7-heap）；B3 无新增 quiz（ch28–39 无可用 JSON，沿 B2 ch26/27 先例不新造）。

## 章节级验证与提交序列

12 章均走「feat 提交 → 门禁（checks/slop/build/mapping）→ 必要时 fix 提交」；B3 批内即时修复记录：

- ch28：docs/25 双目标行转 `partial`；前向链接（ch34/ch29）延后。
- ch30：ch31/ch32 前向链接延后。
- ch31：ch40（B4 目标）前向链接延后。
- ch33：ch34 前向链接延后（3 处，含一次 checks 未过即提交的纠正）。
- ch36：ch37/38/39 前向链接延后；ch28 相对路径层级修正。
- ch37：前向链接延后；负向哨兵自触发修正（第 7 节不再逐字引用禁用文案）；加入 `book/tests/test_motor_numbers.py`（31 tests OK）。
- ch38：ch39 前向链接延后。
- 手绘板补迁：ch28-h745-contracts/boundaries PNG（ch34 引用）。

## mapping 迁移摘要

- B3 收口时 `migrated` 新增：`docs/23`、`docs/24`、`docs/25`（ch28;ch34 双目标）、`docs/27`、`docs/13`、`docs/14`、GD32 `00/01/02/03/04/05/06/07/08/09`、ESP32 `00/01/02/03/05/06/07/08/09/12`、`esp32/04`（ch10;ch34 双目标）、motor 草稿 `29/30/31/32`。
- 保持 `partial`：`e04`、`e06`、`e08`（三者后半目标都是 B4 的 ch40）及 lab 其余各行。
- 仍 `planned`：B4 目标（`docs/18–20`→ch42/45/46、esp32/10/11/13 等）。

## 其他收口动作

- Task 1：148 处图片引用 → 145 个文件迁入 `docs/public/`（3 个已在库）；motor 分支 15 块手绘板按文件取件（`git show feat/motor-ch29-32-placement:…`，未合并该分支）。
- Task 2：`tools/handraw_track/fig_merged_b3.py` 生成 4 块新板（mc29-gd32-contrast / mc30-s3-boot-chain / mc31-matrix-audio / mc32-wifi-espnow），playwright 渲染 PNG 入 `docs/public/images/`；B3 十二章每章至少 1 块手绘知识板。
- Task 15：`stm32-book/tests/test_motor_draft_numbers.py` 删除（设计规格 §5 显式授权的唯一旧树改动）；`book/tests/test_motor_numbers.py` 先行加入（ch37 提交）。
- Task 16：54 处 `[chNN]` 引用内联、36 条定义删除（13 个 B1 文件）；残留 id（ch40 等 B4 目标）按计划保留。
- `.github/workflows/merge-check.yml` slop 行扩到六个 glob。

未验证：CI 远程运行结果；未执行任何远程推送或 Pages 切换；VitePress 站点切换仍归 B5。
