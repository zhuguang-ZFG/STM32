# dma-memcopy —— 4 KiB SRAM 内存搬运

> 难度：★★★☆　｜　涉及外设：DMA1 Channel1　｜　对应章节：[第14章 DMA](../../docs/v1-drivers/14-dma.md)

`hardware_status: pending`。本目录是 **BluePill / STM32F103C8T6 的完整 CMake 工程**：固定 STM32CubeF1 `v1.8.6`、HAL/CMSIS 子模块提交、启动文件、64 KiB Flash / 20 KiB RAM 链接脚本、SysTick 时基、DMA1 Channel1 中断入口和许可复制。固件构建、实际 ELF/BIN 向量/内存检查与宿主回归均通过；下载、DMA 板上行为、LED 观察与耗时仍未实测。

## 一、功能说明

DMA1 Channel1 以普通模式把两个 SRAM 数组之间搬运 **1024 个 32-bit 字，共 4096 字节**：

- 源数组运行时填入确定性 xorshift32 数据；目的数组预填 `0xA5A5A5A5`，避免“没搬也看起来成功”。
- `DMA_MEMORY_TO_MEMORY`，源/目的地址都递增，字/字宽度，普通模式，高优先级。
- `HAL_DMA_Start_IT()` 启动；TC 与 TE 中断回调分别记录完成和错误。
- 主循环用无符号 tick 差值等待，超时 1000 ms； tick 回绕不会延长等待。
- 完成后逐字节比较 4096 B，任何差异都判为失败。

PC13 板载 LED 低电平点亮：

| 结果 | LED |
| --- | --- |
| 成功 | 常亮 |
| 配置失败 | 1 次慢闪后长停，循环 |
| 启动失败 | 2 次慢闪后长停，循环 |
| DMA TE | 3 次慢闪后长停，循环 |
| 超时 | 4 次慢闪后长停，循环 |
| 内容不一致 | 5 次慢闪后长停，循环 |

慢闪为 120 ms 亮 / 120 ms 灭，组间停 800 ms。该时序是程序设计，不是实测值。

## 二、硬件接线

| 开发板 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- |
| BluePill | PC13 | 板载 LED | 低电平点亮；无需外部接线 |
| BluePill | PA13/PA14 | ST-Link SWDIO/SWCLK | 下载前保留 Serial Wire 调试 |
| BluePill | GND/3V3 | 按开发板正常供电 | 不要给 IO 直接供 5 V |

本例不需要 USB-TTL、示波器或外部存储器；也正因为没有额外仪器，板上结果只能先由 LED 模式区分，不能测出吞吐或延迟。

## 三、固定板型与 DMA 配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| MCU | STM32F103C8T6 | 20 KiB SRAM |
| DMA | DMA1 Channel1 | C8 只有 DMA1 |
| 方向 | `DMA_MEMORY_TO_MEMORY` | 源/目的都是 SRAM 数组 |
| 地址增量 | `DMA_PINC_ENABLE` + `DMA_MINC_ENABLE` | 两个数组都逐字前进 |
| 数据宽度 | `DMA_PDATAALIGN_WORD` + `DMA_MDATAALIGN_WORD` | 32 bit；地址 4 字节对齐 |
| 模式 | `DMA_NORMAL` | NDTR 到 0 后停止，不循环 |
| 优先级 | `DMA_PRIORITY_HIGH` | 与其他 DMA 通道仲裁时使用 |
| NVIC | DMA1 Channel1 global interrupt | TC/TE 回调入口 |
| 时钟 | HSE 8 MHz → PLL ×9 → 72 MHz | APB1=36 MHz，APB2=72 MHz |
| SYS → Debug | Serial Wire | 保留 PA13/PA14 |

F1 的内存到内存由 `CCR.MEM2MEM`（bit14）选择，不需要外设请求线。HAL 的 `DMA_MEMORY_TO_MEMORY` 会设置这一位；`PAR/CPAR` 在 HAL 眼里是源地址，`M0AR/CMAR` 是目的地址。

## 四、关键代码解读

**1) 配置并启动**

```c
hdma_memcopy.Instance = DMA1_Channel1;
hdma_memcopy.Init.Direction = DMA_MEMORY_TO_MEMORY;
hdma_memcopy.Init.PeriphInc = DMA_PINC_ENABLE;
hdma_memcopy.Init.MemInc = DMA_MINC_ENABLE;
hdma_memcopy.Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
hdma_memcopy.Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
hdma_memcopy.Init.Mode = DMA_NORMAL;
hdma_memcopy.Init.Priority = DMA_PRIORITY_HIGH;
HAL_DMA_Init(&hdma_memcopy);

HAL_DMA_Start_IT(&hdma_memcopy,
                 (uint32_t)(uintptr_t)g_dma_src,
                 (uint32_t)(uintptr_t)g_dma_dst,
                 1024U);  /* NDTR 是字数，不是 4096 字节 */
```

**2) 中断入口与回调**

```c
void DMA1_Channel1_IRQHandler(void)
{
    HAL_DMA_IRQHandler(&hdma_memcopy);
}

void HAL_DMA_XferCpltCallback(DMA_HandleTypeDef *hdma)
{
    if (hdma == &hdma_memcopy) { g_dma_done = 1U; }
}

void HAL_DMA_XferErrorCallback(DMA_HandleTypeDef *hdma)
{
    if (hdma == &hdma_memcopy) { g_dma_error = 1U; }
}
```

锁定版本的 `HAL_DMA_IRQHandler()` 在普通模式 TC 路径关闭 TC/TE 中断、清 TC 标志并把句柄状态置回 READY；TE 路径关闭中断、清标志、记录 `HAL_DMA_ERROR_TE` 并调用错误回调。代码不要自己再写一遍标志清除，避免与 HAL 重复。

**3) 回绕安全的等待**

```c
uint32_t start = HAL_GetTick();
while ((g_dma_done == 0U) && (g_dma_error == 0U))
{
    if ((uint32_t)(HAL_GetTick() - start) >= 1000U)
    {
        return DMA_MEMCOPY_TIMEOUT;
    }
}
```

直接写 `HAL_GetTick() > deadline` 在 tick 回绕时会误判；无符号减法保留模 `2^32` 的间隔。1000 ms 是软件等待上限，不是 DMA 搬运时间。

**4) 存储期**

两个数组是静态全局对象，存储期覆盖整个程序。DMA 结束前不修改源数组，也不读取正在写入的目的数组；TC 回调只说明硬件搬运完成，内容是否正确仍要比较。若把数组换成局部自动对象，必须保证函数返回前 DMA 已停止且软件消费结束。

## 五、编译、检查与烧录

需 Git、CMake ≥3.21、Ninja、GNU Arm 工具链（含 newlib）；下载另需 OpenOCD。本机验证版本为 GCC 10.3.1、CMake 3.30.2、Ninja 1.12.1。

以下从**仓库根目录**执行。已有相同提交的 CubeF1 可直接传路径：

```console
git clone --depth 1 --branch v1.8.6 https://github.com/STMicroelectronics/STM32CubeF1.git .temp/STM32CubeF1
git -C .temp/STM32CubeF1 submodule update --init Drivers/STM32F1xx_HAL_Driver Drivers/CMSIS/Device/ST/STM32F1xx
cd examples/dma-memcopy
cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"
cmake --build --preset bluepill
python tests/check_firmware.py build/bluepill/dma-memcopy.elf build/bluepill/dma-memcopy.bin
```

`build/bluepill/` 中应有 `dma-memcopy.elf/.hex/.bin/.map`。检查器读取真实二进制，核对栈顶、复位入口、SysTick、DMA1 Channel1 向量、两个 4096 B 缓冲的对齐/不重叠/SRAM 位置和至少 2 KiB 栈预留。提交不符或子模块未初始化时 CMake 直接失败。

2026-11-25 本机快照：

| 产物 | 结果 |
| --- | --- |
| BIN | 6508 B；SHA-256 `4b032d24de2941e03c1b15000076a175e11ee75acb33b246a21331c377979347` |
| ELF | SHA-256 `e2969dc929baf145d2d194be1ea732821ccfff9a8b7b40bdfc79bfed70527a5f` |
| Flash | 6508 B / 64 KiB |
| 静态 RAM | 8280 B / 20 KiB |
| 栈预留 | 2048 B；总计 10328 B / 20 KiB |

换工具链后以新日志和哈希为准。

宿主回归：

```console
cmake --preset host-tests
cmake --build --preset host-tests
ctest --preset host-tests
```

测试用受控 HAL 替身覆盖成功、内容不一致、TE、超时、启动失败、配置失败、tick 回绕超时和 LED 结果码；只证明生产控制流，不证明真实 HAL 时序或板上行为。

编译成功后，核对 BOOT0=0、PA13/PA14、GND 和目标供电，再执行下载：

```console
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program build/bluepill/dma-memcopy.elf verify reset exit"
```

保存含 `verify` 成功的完整日志，再记录 PC13 的实际表现。本轮未执行下载或上板观测。Wokwi 配置指向 `build/bluepill/dma-memcopy.elf`；Wokwi 是否完整模拟 DMA 不作为本示例的验收依据。

## 六、预期现象（理论与设计目标，未实测）

- 下载复位后，DMA1 Channel1 开始一次 4 KiB 搬运。
- 成功时 PC13 常亮。
- 1–5 次慢闪分别对应配置、启动、DMA 错误、超时、内容不一致。
- 若 LED 不亮或模式不稳定，先保存 OpenOCD 日志，再用调试器读取 `DMA1->ISR`、`DMA1_Channel1->CCR/CNDTR/CPAR/CMAR`、`g_dma_done/g_dma_error` 和两个缓冲地址；不要只凭 LED 猜原因。

## 七、常见问题

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 1 次慢闪 | DMA 配置/回调注册失败 | HAL 返回与 `hdma_memcopy.Init` | 修配置；不要在失败后继续启动 |
| 2 次慢闪 | `HAL_DMA_Start_IT()` 返回失败 | 句柄状态、源/目的地址、NDTR | 修启动参数或句柄状态 |
| 3 次慢闪 | DMA TE | `DMA1->ISR` 的 TEIF1、地址和 CCR | 检查地址可达性、对齐和配置 |
| 4 次慢闪 | 1000 ms 内未收到 TC/TE | CCR.EN、NDTR、ISR、NVIC 使能 | 先查时钟/向量/中断，再调整等待 |
| 5 次慢闪 | TC 后内容不同 | 首个不同字、源/目的地址与长度 | 检查宽度、增量、覆盖和比较逻辑 |
| LED 常亮但无仪器证据 | 只能说明程序走到成功分支 | 仍缺板上 DMA 轨迹与原始日志 | 补 SWD/逻辑分析仪记录后再宣称实测 |
| 构建提示提交不符 | CubeF1/HAL/CMSIS 版本不匹配 | CMake 打印的预期/实际提交 | 按锁定 tag 和子模块重新初始化 |

## 八、相关资源与参考边界

- **RM0008** 第 13 章：F1 DMA 通道、`MEM2MEM`、NDTR、TC/TE/HT 与标志清除语义。
- STM32CubeF1 `v1.8.6`，HAL `77fbb30b7a1d02533980400083e48c559aae5a4f`，CMSIS device `8a76309ed1250d817e9c888c4417171d2ba3ba63`。
- 官方 [DMA_FLASHToRAM 示例](https://github.com/STMicroelectronics/STM32CubeF1/blob/v1.8.6/Projects/STM3210E_EVAL/Examples/DMA/DMA_FLASHToRAM/Src/main.c)：用于核对 DMA1 Channel1、内存到内存、双增量、字宽、普通模式与 TC/TE 回调的配置形状；本示例改为 SRAM→SRAM 4 KiB，并增加超时、比较和 LED 结果码。
- 锁定 [HAL DMA 源码](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/77fbb30b7a1d02533980400083e48c559aae5a4f/Src/stm32f1xx_hal_dma.c)：以 `HAL_DMA_Start_IT()` 与 `HAL_DMA_IRQHandler()` 的实际行为为准。
- 《Mastering STM32》第二版物理第 237、269 页：CPU/DMA 路径与缓冲区存储期的解释顺序；只作教学参考，不复制插图。
- 野火《STM32 HAL 库开发实战指南》物理第 203、210 页：内存复制实验与“构建→下载→观察”的闭环安排；板型和接线不照搬。
- 本示例没有新增插图、照片或测量截图；构建与宿主测试都不代替真板证据。
