# B1 本地验收证据

- 日期：2026-11-13
- 分支：worktree-merged-book-b1
- commit：`35f057b233ba7a61ce3d889da6d4efddba353ca0`（验证时 HEAD）
- 环境：Windows + Git Bash；Python 3.13.14；Node v24.14.0

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m book.manifest --check` | 0 | 无输出；manifest 与 toc.tsv 一致 |
| `python -m book.mapping --check` | 0 | 无输出；mapping 与源文件一致 |
| `python -m unittest discover book/tests -v` | 0 | Ran 30 tests；OK |
| `python -m book.checks --check` | 0 | `checks passed` |
| `python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md` | 0 | `干净：没有机械命中。` |
| `python -m book.build_html --check` | 0 | `built 17 pages, 35 planned chapters missing` |
| `node --test scripts/tests/legacy-redirects.test.mjs` | 0 | tests 2；pass 2；fail 0 |

## 17 章文件名

- `docs/v0-foundations/01-c-memory-model.md`
- `docs/v0-foundations/02-c-volatile-ub.md`
- `docs/v0-foundations/03-struct-abi-registers.md`
- `docs/v0-foundations/04-function-pointer-state-machine.md`
- `docs/v0-foundations/05-toolchain-four-steps.md`
- `docs/v0-foundations/06-linker-startup-map.md`
- `docs/v0-foundations/07-build-systems-legacy.md`
- `docs/v1-drivers/08-architecture-memory-clock.md`
- `docs/v1-drivers/09-gpio.md`
- `docs/v1-drivers/10-interrupts-nvic-exti.md`
- `docs/v1-drivers/11-systick-timebase-rtc.md`
- `docs/v1-drivers/12-timers-pwm.md`
- `docs/v1-drivers/13-uart-framed-protocol.md`
- `docs/v1-drivers/14-dma.md`
- `docs/v1-drivers/15-adc-dac-sampling.md`
- `docs/v1-drivers/16-i2c-spi.md`
- `docs/v1-drivers/17-flash-iap-ota.md`

## 10 组测验 id

`c03-volatile`、`s02-rcc-clock`、`s03-gpio`、`s04-nvic`、`s06-tim`、`s07-usart`、`s08-dma`、`s09-adc`、`s11-i2c`、`s12-spi`

未验证：CI 远程运行结果；未执行任何远程推送或 Pages 切换。
