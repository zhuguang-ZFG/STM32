# STM32 批次设计

## 事实基准

- 芯片：STM32F407ZGT6（Cortex-M4F）。寄存器事实以 ST 官方 CMSIS 头文件 `cmsis_device_f4` 的 `stm32f407xx.h` 为第一来源，位定义以 RM0090 为准，示例代码不用 SPL（现有 `00-blink` 即寄存器级裸机）。
- 板卡：霸天虎 F407ZGT6。已核实事实仅限规范中列出的 LED 接法（PF6/PF7/PF8 共阳，低电平点亮）。**HSE 晶振值未核实**——正文与工程都不得写死具体值作为“板上事实”。
- 工具链：`arm-none-eabi-gcc`（scoop `gcc-arm-none-eabi10.3`，10.3-2021.10）+ `mingw32-make` 4.4.1（winlibs，`D:\zhugu-home\mingw64\mingw64\bin`）。Makefile 沿用 `00-blink` 结构；Windows 下需保证 mingw64 的 `sh`/`mkdir`/`rm` 在 PATH，否则 `make clean` 等规则不可用——README 写明。
- 资料缓存放已忽略的 `.trellis/ref/`，正文引用稳定上游地址。

## 引脚决策

| 用途 | 引脚 | 复用 | 依据 | 备注 |
|---|---|---|---|---|
| MCO1 时钟输出 | PA8 | AF0 | RM0090 §8.4 GPIO 复用 | S2 实测入口 |
| TIM3_CH1 PWM 输出 | PA6 | AF2 | datasheet 复用表 | 不占用板载 LED |
| TIM3_CH2 输入捕获 | PA7 | AF2 | datasheet 复用表 | 与 PA6 之间需跳线 |
| USART1 TX/RX | PA9 / PA10 | AF7 | datasheet 复用表 | |
| 板载 RGB | PF6/PF7/PF8 | GPIO | 规范已核实 | 与 TIM3 复用冲突时以 LED 为准 |

正文必须写清：现有 S6 quick win 写“TIM3 CH1 输出到 PF6，若复用表无 TIM 通道则换脚”属于把核实工作推给读者；成稿改为 PA6，并单独用一段解释 PF6 在复用表中的归属与板载 LED 占用如何影响选脚策略。

## 三个工程

沿用 `00-blink` 的自包含结构（各自持有 `Makefile`、`startup_stm32f407xx.s`、`stm32f407xx.ld`、`main.c`、`README.md`），读者复制单目录即可构建，不引入跨工程共享头文件。

### 01-rcc-clock

- 编译期开关 `USE_HSE_PLL`（默认 0）：默认路径留在 HSI 16MHz，保证无 HSE 也能跑。
- HSE 路径：M/N/P/Q 由 `HSE_VALUE_HZ` 集中定义并在 README 提示“必须按你手上板子实测核对”；启动时读回 `RCC_CR`、`RCC_PLLCFGR`、`RCC_CFGR`，把实际生效的 `SYSCLK`/`HCLK`/`PCLK1`/`PCLK2` 算出来打印到串口或直接驱动 MCO1 频率。
- HSE 起振失败必须带超时回退 HSI（正文坑位之一）。
- `SystemCoreClock` 与串口重定向延迟保持一致；延时函数按实际 `HCLK` 计算循环数，不留“粗略延时”这种与时钟脱钩的写法。

### 02-tim-pwm

- TIM3：APB1 分频≠1 → 定时器时钟 84MHz；`PSC=83` → 计数 1MHz；`ARR=999` → 1kHz；`CCR1=500` → 50%。
- CH1（PA6）PWM 输出；CH2（PA7）输入捕获，测量周期并换算频率。
- 自测闭环：PA6 → PA7 跳线回环，捕获读数应与 1kHz 设定一致；README 写明跳线接法与不接跳线时的现象。
- 呼吸灯用 CCR 渐变；解析出的“改 CCR 只改占空比、不改频率”是本章主线。

### 03-uart-dma

- USART1 PA9/PA10，115200 8N1，默认 OVER8=0（16 倍过采样）。
- **波特率正确性前提**：`波特率 = f_PCLK / BRR`。HSI 16MHz 时 `BRR=139`，误差 −0.08%；1MHz 示例时钟下 `BRR=9`，误差 −3.549%，不可用。正文与工程注释都写明“1MHz 只是 PLL VCO 输入的示例分频结果，不能当成外设时钟”。
- RX：DMA1 循环模式接收固定长缓冲；用 USART 的 IDLE 标志判“一帧结束”，统计帧长与丢字节。
- TX：先轮询回显保证最小可跑通；DMA 发送作为同一工程的可选编译分支，映射关系（stream/channel）必须在 RM0090 核对后才写进代码与正文。
- 逐字节位序/起始停止位由 `uart-frame` 动画表达，工程里用 0x55 / 0x41 两个字节对照（S-F3）。

## 章节修复落点

| 编号 | 落点 |
|---|---|
| S-F1 | S2 正文：1MHz 标为“M/N 的设计目标值”，Flash 等待周期附电压/频率条件表，HSE 值留实测位 |
| S-F2 | S6 quick win 改为 PA6；新增“板上 LED 与复用冲突”一节 |
| S-F3 | S7 正文 + `e02-logic-uart.md`：0x41 统一；补 f_PCLK 前提 |
| S-F4 | S8 正文：`DIR` 位宽 2、位置 bit6 |
| S-F5 | S8 正文 + `dma-pingpong.svg`：处理期限与超期覆盖 |

## 动画

沿用父任务动画合同（独立 SVG+SMIL、viewBox 宽 720、四色、字号 ≥12px、`calcMode="discrete"` 阶段切换、title/desc）。六张新图各自表达一个可说清的结论；`dma-pingpong.svg` 修订时新增“当前所有者/截止点/覆盖”三元素，并保持原有教学结论。

每张图配正文里的逐阶段解说与一句结论；未播放时静态布局也要能读懂机制。

## 上板实测

霸天虎板可做：MCO1 测频核实 HSE 与 SYSCLK、PWM 占空比与频率测量、USART 回显实测波特率、DMA 环形接收计帧。实测结果以真实读数写入实验小节；未接仪器或无法连板的项目保留“待上板实测”，不得填推导值。