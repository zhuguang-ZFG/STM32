# 01-rcc-clock：把时钟树从图纸变成方波

配套章节：[S2 RCC 时钟树](../../docs/stm32/02-rcc-clock.md)

## 这个工程回答什么

芯片复位那一刻，只有内部 RC（HSI 16MHz）在供电：外部晶振没起振、Flash 还没提速、
主频锁在最低档。所以"跑起来"的第一件事永远是配时钟，顺序错了典型后果不是"跑得慢"，
而是**随机跑飞**。

本工程把这条顺序完整走一遍，并且把结果变成三种可以亲眼看到的东西：

1. **PA8 (MCO1)** 输出 ≈42MHz，用示波器/逻辑分析仪量；
2. **PF6 红灯**按 1Hz 闪——如果延时函数没跟着改时钟，它会快 10.5 倍（168/16）；
3. **GDB** 里直接读 `g_clock_tree[]`，看"程序认为自己是多少 Hz"。

## 硬件前提

| 项 | 说明 |
|---|---|
| 芯片 | STM32F407ZGT6（Cortex-M4F） |
| 板卡 | 霸天虎 F407ZGT6 |
| 晶振 | **必须自己核实**。工程默认 `HSE_VALUE_HZ=8000000`；改错它不会报错，只会算出完全错误的 SYSCLK |
| 外设 | 无。默认路径只用片内 RC 与 MCO1 |

## 构建

需要 PATH 上有：

- `arm-none-eabi-gcc`（本机：xPack GNU Arm Embedded GCC 15.2.1）
- `mingw32-make`（本机：GNU Make 4.4.1）
- Git 的 `usr\bin`（Makefile 用到 `mkdir -p` / `rm -rf`）

```bash
# 默认：留在 HSI 16MHz，不碰晶振，最稳
make

# 走 HSE + PLL 到 168MHz
make USE_HSE_PLL=1

# 你的板子晶振不是 8MHz 时必须显式传值
make USE_HSE_PLL=1 HSE_VALUE_HZ=25000000
```

烧录（需要 OpenOCD + ST-Link）：

```bash
make flash
```

## 代码结构（对照阅读）

| 位置 | 对应知识点 |
|---|---|
| `systick_init()` / `SysTick_Handler` | 延时必须跟着 HCLK 走，这是"改了时钟忘了改延时"的解药 |
| `flash_latency_ws_3v3()` | RM0090 Table 10：等待周期按 **VDD 电压范围**分列，3.3V 那列是 30/60/90/120/150/168 |
| `flash_config()` | VOS 只决定 HCLK 天花板（VOS=0 → ≤144MHz，VOS=1 → ≤168MHz） |
| `pll_params_from_hse()` | M/N/P/Q 的取值与约束（PLLM 2..63、VCO 输入 1..2MHz、PLLN 50..432、VCO 100..432MHz） |
| `clock_init()` | 电压档 → Flash → HSE（带超时）→ PLL → 切 SYSCLK → **回读 SWS** |
| `clock_tree_readback()` | 从 CFGR 反推真实时钟树，含"APB 分频≠1 时定时器时钟 ×2"的隐藏规则 |
| `mco1_init()` | 把内部时钟引到引脚上 |

## 预期观察

- 默认构建：红灯 1Hz 稳定闪烁；PA8 有 ≈4MHz 方波（16/4）。
- `USE_HSE_PLL=1`：PA8 ≈42MHz；红灯仍然是 1Hz（如果不仍是 1Hz，说明 SysTick 没重配）。
- GDB 读 `g_clock_tree[]`：`{168000000, 168000000, 42000000, 84000000, 84000000}`（TIM2CLK 为 PCLK1×2）。
- GDB 读 `g_clock_status`：0 = 走 PLL；1 = 回退 HSI（此时红灯连闪两下再停）。

## 失败排查

| 现象 | 多半是 |
|---|---|
| 灯完全不亮 / HardFault | `FLASH_ACR.LATENCY` 没配够，或忘了先切电压档 |
| 灯快得离谱 | SysTick 的 LOAD 没按新 HCLK 重算 |
| `g_clock_status==1` | 晶振没起振（虚焊/负载电容/你根本没焊晶振），代码已自动回退 HSI |
| 上电就死循环在 `clock_init` | HSE 起振等待没有超时（本工程已加超时）；若你的版本没有，说明改过这段 |