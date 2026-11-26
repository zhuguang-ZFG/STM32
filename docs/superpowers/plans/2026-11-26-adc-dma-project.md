# ADC/DMA 示例补成完整工程

日期：2026-11-26。范围：`examples/adc-dma` 的构建入口、宿主回归、ELF/BIN 检查与相关索引。`main.c` 未改动：生产逻辑保持原样，函数边界不变。

## 目标与缺口

`examples/README.md` 把 `adc-dma` 列为待集成源码：只有 `main.c`、`diagram.json` 与 `wokwi.toml`，没有 HAL 依赖、启动文件、链接脚本与独立构建入口，也没有全固件编译。本轮按已合并的 `dma-memcopy` / `gpio-blink` 与 `exti-key` 的形状补齐，不改板型、时钟与接线。

## 变更

- 新增 `CMakeLists.txt`、`CMakePresets.json`、`cmake/arm-none-eabi.cmake`、`stm32f103c8.ld`、`dependencies.lock.json`、`include/stm32f1xx_hal_conf.h`、`stm32f1xx_it.c`：固定 CubeF1 `v1.8.6`（HAL `77fbb30b`、CMSIS device `8a76309e`），64 KiB Flash / 20 KiB RAM，2 KiB 栈预留，启用 GPIO/RCC/RCC_EX/CORTEX/FLASH/DMA/ADC 模块。
- 新增 `tests/stm32f1xx_hal.h`、`tests/adc_dma_tests.c`：把生产 `main.c` 连同 `adc_dma_init`、`adc_channel_avg`、`adc_to_volt`、`moving_average` 与主循环一起编译，用 HAL 替身驱动。
- 新增 `tests/check_firmware.py`：读真实 ELF/BIN，核对栈顶、复位入口、SysTick 向量、`hadc1`/`hdma_adc1` 的存储、`g_adc_buf`（96 B，半字对齐）与 `g_ma_buf`（96 B）的 .bss 位置、`g_ma_idx`/`g_ma_filled` 的字节宽度与栈预留。
- 新增 `.github/workflows/adc-dma.yml`：路径过滤的宿主回归 + ARM 构建 + 向量/内存检查。
- 修正 `examples/adc-dma/README.md` 的两处失效章节链接（`docs/09-ADC与DAC.md`、`docs/10-DMA.md` 已在合并书中不存在），改指 `docs/v1-drivers/15-adc-dac-sampling.md` 与 `docs/v1-drivers/14-dma.md`。
- 修正 `examples/adc-dma/wokwi.toml`：原指向不存在的 `build/firmware.elf`，改为本工程产物 `build/bluepill/adc-dma.elf`，并注明 Wokwi 的 ADC 模型不覆盖真实模拟前端。
- 更新 `examples/adc-dma/README.md`（完整工程状态、构建/检查/烧录命令、本机快照、宿主测试覆盖、块平均非原子快照的局限、`error_handler` 终止语义）、`examples/README.md`、`docs/v1-drivers/15-adc-dac-sampling.md`。

## 验证

- 宿主回归：`cmake --preset host-tests && cmake --build --preset host-tests && ctest --preset host-tests` → 1/1 通过。
- 反向验证一（去交错）：把 `g_adc_buf[s * ADC_NUM_CH + ch_index]` 改成 `g_adc_buf[s + ch_index]` 后，`test_channel_average_deinterleaves_ranks` 在常量填充的 `adc_channel_avg(ADC_CH0_INDEX) == 100` 处失败；恢复后通过。
- 反向验证二（窗口推进）：把 `if (ch_index == (ADC_NUM_CH - 1U))` 改成恒真后，`test_moving_average_window` 在 `g_ma_idx == 1 && g_ma_filled == 0` 处失败；恢复后通过。
- 反向验证三（心跳边界）：把 `>= SAMPLE_PERIOD_MS` 改成 `> SAMPLE_PERIOD_MS` 后，`test_led_heartbeat_period` 在 100 ms 用例的 `toggle_count == 1` 处失败；恢复后通过。
- 反向验证四（DMA 循环模式）：把 `hdma_adc1.Init.Mode = DMA_CIRCULAR` 改成 `0U` 后，`test_boot_configures_sampling_chain` 在 `captured_dma.Init.Mode == DMA_CIRCULAR`（`tests/adc_dma_tests.c:295`）失败；恢复后通过。
- 反向验证五（ADC 时钟分频）：把 `pclk.AdcClockSelection = RCC_ADCPCLK2_DIV6` 改成 `RCC_HCLK_DIV2` 后，同一测试在 `captured_pclk.AdcClockSelection == RCC_ADCPCLK2_DIV6`（`tests/adc_dma_tests.c:276`）失败；恢复后通过。这两项只证明宿主断言咬得住配置写入，真实 HAL 里的寄存器语义仍靠 ARM 构建与手册核对。
- 固件：`cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"` + `cmake --build --preset bluepill` 通过；FLASH 9980 B、RAM 2376 B（含 2048 B 栈预留；`data` 12 B + `bss` 2364 B）。
- `python tests/check_firmware.py build/bluepill/adc-dma.elf build/bluepill/adc-dma.bin` → PASS（SP=0x20005000、SysTick=0x8000575、`g_adc_buf`=0x20000080+96、`g_ma_buf`=0x200000e0+96、`_ebss`-基址 328 B）。
- 本机快照：BIN 9980 B，SHA-256 `4290ca392d965bfac3aa009b95dfd909d0cdbe7b2e1af4b670dea832706d97c6`；ELF SHA-256 `3ef7fcb58f0e3d60f0da9eacd9060d51d7ed20fc55683b72ee15fff669a44bd9`。工具链 GCC 10.3.1 / CMake 3.30.2 / Ninja 1.12.1。CI（Ubuntu 仓库版 GCC）同一源码为 10132 B Flash、RAM 2376 B，复位入口 `0x8000591`、SysTick `0x8000577`；故检查器只比对结构属性，不比对绝对地址与哈希。
- 既有门：`tools/check_firmware_regressions.py` 14/14、`book.checks --check`、`book.build_html --check`（53 页 0 missing）、`tools/slop_lint.py`、`python -m unittest discover book/tests`（124 项通过；本机 `pytest book/tests` 会在 `C:\Documents and Settings`、`C:\Users\zhugu\BMS-Z-videos` 两个联接点上收集失败，加 `--rootdir . -c NUL` 也不解决，故仓库门用 unittest）、`tools/check_assets.py`、`npm run docs:build`、`npm run site:pages` 全部通过。

## 未完成

- 未下载、未上板：ADC 实际码值、VDDA 实测、DMA 传输轨迹与滑动平均的板上效果均无证据。
- 未执行 Wokwi 仿真；`diagram.json` 只保证配置合法，Wokwi 的 ADC 模型不覆盖真实模拟前端。
- 块平均在 DMA 仍写同一缓冲区时读取，不是原子快照（一个缓冲区周期约 48 × 68 / 12 MHz ≈ 272 µs）。本轮只在 README 与本章正文写明局限，未改成双缓冲或半传输/传输完成回调：那会改变生产逻辑，需要单独的时序证据才能宣称抗撕裂。
- `error_handler()` 是终止路径，宿主回归只验证「失败时不进入 `HAL_ADC_Start_DMA`」与 `__disable_irq` 被调用一次，不验证原地停留。
- `task_verify`：仓库无 operator 配置的 Git baseline/checks，本轮未取得该证据。
