# EXTI 按键示例补成完整工程

日期：2026-11-26。范围：`examples/exti-key` 的构建入口、宿主回归、ELF/BIN 检查、消抖标志清除时序与相关索引。`main.c` 只改 `key_process()` 内部顺序，函数边界不变，`tools/check_firmware_regressions.py` 的切片仍然有效。

## 目标与缺口

`examples/README.md` 与附录 B 都把 `exti-key` 列为待集成源码：只有 `main.c`，没有 HAL 依赖、启动文件、链接脚本与独立构建入口，也没有全固件编译。本轮按已合并的 `dma-memcopy` / `gpio-blink` 形状补齐，不改板型、时钟与接线。

## 变更

- 新增 `CMakeLists.txt`、`CMakePresets.json`、`cmake/arm-none-eabi.cmake`、`stm32f103c8.ld`、`dependencies.lock.json`、`include/stm32f1xx_hal_conf.h`、`stm32f1xx_it.c`：固定 CubeF1 `v1.8.6`（HAL `77fbb30b`、CMSIS device `8a76309e`），64 KiB Flash / 20 KiB RAM，2 KiB 栈预留，只启用 GPIO/RCC/CORTEX/FLASH 模块。
- 新增 `tests/stm32f1xx_hal.h`、`tests/exti_key_tests.c`：把生产 `main.c` 连同 `EXTI0_IRQHandler`、`HAL_GPIO_EXTI_Callback`、`key_process` 一起编译，用 HAL 替身驱动。
- 新增 `tests/check_firmware.py`：读真实 ELF/BIN，核对栈顶、复位入口、SysTick、EXTI0 向量、`g_key_event`/`g_key_count` 的 .bss 位置与栈预留。
- 新增 `.github/workflows/exti-key.yml`：路径过滤的宿主回归 + ARM 构建 + 向量检查。
- 修正 `key_process()` 的清除时序：原实现先清 `g_key_event` 再 `HAL_Delay(20)`，消抖窗口内到达的抖动边沿会重新置位，同一次按压在下一轮被当成第二次事件再翻转一次。现改为延时后清标志，窗口内边沿被吸收；代价是 20 ms 内开始的第二次真实按下被丢弃。README 的代码片段与现象描述同步改写。
- 更新 `examples/exti-key/README.md`（完整工程状态、构建/检查/烧录命令、本机快照、宿主测试覆盖、`error_handler` 终止语义）、`examples/README.md`、`docs/v1-drivers/10-interrupts-nvic-exti.md`、`docs/appendix/B-project-index.md`。

## 验证

- 宿主回归：`cmake --preset host-tests && cmake --build --preset host-tests && ctest --preset host-tests` → 1/1 通过。
- 反向验证：把 `key_process()` 的电平复核改成恒真后，`test_released_key_is_rejected` 失败；恢复后重新通过。测试确实约束消抖分支。
- 时序回归：`test_bounce_inside_debounce_window_is_absorbed` 让延时替身在窗口内再投递一次 `HAL_GPIO_EXTI_Callback(KEY_PIN)`。把清除挪回延时之前并隔离引导测试后，该用例在 `g_key_event == 0` 处失败；恢复后通过。原 burst 用例只在延时前连调回调，测不出这个缺陷。
- 固件：`cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"` + `cmake --build --preset bluepill` 通过；FLASH 4836 B、RAM 2072 B（含 2048 B 栈预留）。
- `python tests/check_firmware.py build/bluepill/exti-key.elf build/bluepill/exti-key.bin` → PASS（SP=0x20005000、EXTI0=0x8000127、`g_key_event`+1、`g_key_count`+4）。
- 本机快照：BIN 4836 B，SHA-256 `b5f9b6138f5c5f96d7472f5150087a552ec3849358348e919b76a0d3264ab681`；ELF SHA-256 `5c2b0a4633752d4cdbfe9fd83e89db1d4e268b31c795a199557b3028b885daef`。工具链 GCC 10.3.1 / CMake 3.30.2 / Ninja 1.12.1。
- 既有门：`tools/check_firmware_regressions.py` 14/14（含 `f103-key`）、`book.checks --check`、`book.build_html --check`（53 页 0 missing）、`tools/slop_lint.py`、`pytest book/tests` 124 项、`tools/check_assets.py`（583 项公共资产）、`npm run docs:build`、`npm run site:pages`（54 页对账）全部通过。

## 未完成

- 未下载、未上板：抖动波形、一次物理按压是否只产生一个事件、PC13 实际翻转均无证据。
- 未执行 Wokwi 仿真；`diagram.json` 只保证配置合法，不证明 EXTI/NVIC 模型行为。
- `error_handler()` 是终止路径，没有也不适合做宿主回归；测试里 HAL 时钟配置恒返回 `HAL_OK`。
- `task_verify`：仓库无 operator 配置的 Git baseline/checks，本轮未取得该证据。
