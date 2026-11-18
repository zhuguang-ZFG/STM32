# 01-rcc-clock：把时钟树从图纸变成方波

配套章节：[第8章：架构、存储器地图与时钟树](../../../../docs/v1-drivers/08-architecture-memory-clock.md)

> hardware_status: pending。已修复MCO源/AF配置和冷复位升频的PWR/Flash/APB先后次序，PLL停机/锁定等待有界退出；实际生产C宿主回归与现有HSI、HSE8/25MHz构建通过。没有写板或测量，不能据编译推断真实晶振/频率/接线正确。仅支持从复位HSI16进入，不作任意运行时重配指南。

## 这个工程回答什么

芯片复位那一刻，只有内部 RC（HSI 16MHz）在供电：外部晶振没起振、Flash 还没提速、
主频锁在最低档。所以"跑起来"的第一件事永远是配时钟，顺序错了典型后果不是"跑得慢"，
而是**随机跑飞**。

本工程的教学目标是用三种手段对账；下面是待硬件验收的设计目标，不是已采集读数：

1. **PA8 (MCO1)** 默认HSI理论16MHz，PLL168路径/4理论42MHz，用仪器量；
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

- `arm-none-eabi-gcc`（本轮实际使用GNU Arm Embedded 10.3.1 20210824）
- `mingw32-make`（本机：GNU Make 4.4.1）
- Git 的 `usr\bin`（Makefile 用到 `mkdir -p` / `rm -rf`）

```bash
# 默认：留在 HSI 16MHz，不碰晶振，最稳
make

# 以下是现有纯构建参数；上板仍需确认晶振/供电/接线与单独授权
# 冷复位HSI16 → HSE + PLL目标168MHz（硬件过渡仍未测）
make USE_HSE_PLL=1

# 你的板子晶振不是 8MHz 时必须显式传值
make USE_HSE_PLL=1 HSE_VALUE_HZ=25000000
```

以下是既有烧录入口（OpenOCD + ST-Link）；本轮未执行。先核对板型、晶振值、供电/接线并另获硬件授权：

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
| `clock_init()` | PWR门/电压档 → Flash/回读 → HSE/PLL有界等待 → 安全APB分频 → SW/SWS |
| `clock_tree_readback()` | 从 CFGR 反推真实时钟树，含"APB 分频≠1 时定时器时钟 ×2"的隐藏规则 |
| mco1_init() | PA8=AF0推挽/Very High，按SWS选HSI/HSE/PLL并配分频；实际频率待测 |

## 预期观察

- 默认构建不启动PLL，名义HSI16MHz，SysTick目标1ms、红灯约1Hz；MCO1选HSI且/1，PA8理论16MHz，均待实测，不是4MHz。
- USE_HSE_PLL=1且晶振参数/供电正确的目标为SYSCLK168MHz、APB1=42MHz/APB2=84MHz，MCO1选PLL/4理论42MHz。已作纯编译与函数回归，未量过真实时钟/过渡。
- GDB 读 `g_clock_tree[]`：`{168000000, 168000000, 42000000, 84000000, 84000000}`（TIM2CLK 为 PCLK1×2）。
- g_clock_status=0仅表示未记录错误，默认HSI路径也为0，不证明走PLL；实际源看CFGR.SWS。1为Flash回读/就绪等待/切源失败、2为参数助手拒绝；按具体路径核SWS，不能只凭一个状态值证明已安全回退。

## 失败排查

| 现象 | 多半是 |
|---|---|
| 灯完全不亮 / HardFault | `FLASH_ACR.LATENCY` 没配够，或忘了先切电压档 |
| 灯快得离谱 | SysTick 的 LOAD 没按新 HCLK 重算 |
| g_clock_status==1 | 可能是Flash回读、HSE/PLL就绪或SWS失败；查CR/CFGR与时钟回读，不等同于已回退HSI |
| clock_init返回失败/红灯错误节奏 | HSE、PLL停止/锁定与SWS均有有界等待；核状态和实际时钟回读，超时计数不是已校准毫秒 |