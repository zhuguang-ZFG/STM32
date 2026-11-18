# PWM：把时钟、PSC/ARR/CCR 与波形对上

状态：`hardware_status: pending`。本轮仅源码/文档核对，未构建、烧录或测量。沿用 [ch12 E03](../../docs/v1-drivers/12-timers-pwm.md) 的方法，先会ch08/ch09的时钟与复用，取证前读 [共同安全与记录](../README.md)。

## 现有工程与参数

主样板：[mcu/code/stm32/02-tim-pwm](../../mcu/code/stm32/02-tim-pwm/README.md)。启动目标STM32F407ZGT6/霸天虎口径，实际板卡/芯片待核实；依据main.c与 [capture.h](../../mcu/code/common/behavior/capture.h)：

| 项 | 当前源码事实 | 边界 |
| --- | --- | --- |
| 输出 | PA6/AF2/TIM3_CH1，PWM mode1、正极性 | 不是板载PF6，也不是F103的复用配置 |
| 捕获 | **PA0/AF1/TIM2_CH1**，TIM2 32位自由计数、IRQ28 | 跳线PA6→PA0，不是旧PA7/TIM3_CH2 |
| 时钟 | 回读SWS/PLL/AHB/APB，短暂设APB1=/2比较再恢复 | g_tim_clk_*是公式推导，不是仪器实测 |
| 计数 | COUNT_HZ=1000000，PSC=TIMclk/COUNT_HZ−1，ARR=999 | 非整除会保护停留；不是固定PSC71 |
| 占空比 | 初始CCR1=500，主循环立即按phase改写，每20ms一步 | 不是固定50%；循环CCR最小10、最大1000，即1%–100% |
| 观测 | g_pwm_hz/g_measured_hz/g_capture_edges/g_overcapture | TIM2同源捕获不能独立证明绝对频率准确 |

冷复位HSI名义16MHz、APB1=/1条件下（**理论，待回读确认**）：TIMclk=16MHz、PSC15，`f=16e6/((15+1)×(999+1))=1000Hz`，周期1ms。短暂/2时PCLK1=8MHz、TIMclk仍16MHz，随后恢复。实际条件不同就重算，不套章内84MHz或F103的72MHz。

## 接线、构建与烧录（后续执行）

1. 完成共同身份/供电清单，断电接 **PA6→PA0**；探头尖端接PA6，地夹接板GND。照片可辨针名，先确认PA0被配置为输入捕获，禁止两输出硬连。
2. 不接电机或功率负载，测波形不需要LED；要接LED先核限流与负载。SWD按实际针序，单一合规电源，禁止带电换线。
3. 从仓库根进入现有Makefile目录，**本轮未执行**：

   ```powershell
   Set-Location mcu/code/stm32/02-tim-pwm
   make
   make flash
   ```

   目标为`build/tim-pwm.elf/.bin/.hex/.map`；先构建成功保留日志/哈希，后续获准写板才verify reset。debug/gdb含写板行为的边界见共同说明。

## 预期、测量与判据（全部非实测）

1. 写押注和理论输入，保存RCC、PSC/ARR/CCR1/CCMR1/CCER/CR1回读；另记g_hclk、g_pclk1_before/after、g_tim_clk_before/after、g_pwm_hz。读数全部待测，不能抄默认数填表。
2. 探头倍率与通道一致，PA6上升沿触发，约0.2ms/div起步，采样率至少10MSa/s，登记实际设置；另存约4秒长记录看包络，不用长时基低采样计算短脉宽。
3. 在**当前动态程序**上选非端点脉冲，保存连续周期与高电平宽度，`D=tH/T`。1MHz计数下CCR250/500/750分别对应理论250/500/750µs，仅为计算样例，不是实测。相隔很久的GDB回读不能冒充同一脉冲CCR。
4. phase循环会经过100%平台，平台期间无上升沿，不能要求蓝灯和g_measured_hz全相位恒定有效。在稳定非端点窗口核对g_capture_edges增长、g_overcapture不新增，和波形交叉对账；跨100%平台的间隔单列。捕获频率来自同一板时钟，只作辅助证据。
5. **功能通过**：构建/verify/冷复位证据齐，PA6有PWM，跳线后PA0有相同边沿；非端点窗口捕获增长且无新增过捕获，周期与PSC/ARR一致。**精度通过**：测前依据实际时钟规格与仪器/量化误差定限，计算频差/占空比差并比较；误差限未知则精度待判。
6. 静态CCR对账应先固定占空比再测，但**当前代码没有固定模式**。本轮不改程序，不用暂停断点冒充稳定PWM；调试冻结/继续会改变条件。固定25%/50%/75%和ARR翻倍仍是ch12原实验设计，需后续确认最小固件变更后执行，这部分现在阻塞/待测。

理论呼吸周期约`200×20ms≈4s`加开销，最小并非0%；不是F103对照的约2秒。

| 失败信号 | 区分证据 | 下一动作 |
| --- | --- | --- |
| PA6无波形 | GPIOA AFRL6=AF2、TIM3 CC1E/CEN、RCC与保护循环位置 | 逐层查使能/复用；TIM3没有MOE，不用TIM1的办法修它 |
| PWM正常但捕获不增 | PA6→PA0电平、PA0 AF1、TIM2 CC1E/CC1IF/IRQ28 | 先查跳线，再查TIM2，不走旧PA7/CC2路径 |
| 频率成倍错误 | RCC/PSC/ARR实际回读、两处+1 | 区分PCLK和APB定时器×2，回ch08/ch12 |
| 短暂频率跳变/为0 | 是否100%平台、过捕获/超时与原始边沿 | 分无边沿平台与丢捕获，别一律归因GPIO速度 |

## 独立练习与证据缺口

不改代码计算ARR499且计数时钟不变时的2kHz及不同CCR的高电平宽度；解释为何同源捕获1000不能证明HSI无误差。改ARR/固定CCR属于以后独立代码实验，本轮不实施。

共同表补：`PSC/ARR/CCR=待回读`、`T/tH/f/D=待测`、`捕获/过捕获增量=待测`、`误差预算/复测=待测`。实际身份、构建/verify、波形、寄存器和固定占空比证据仍缺，不得宣布已硬件复现。

F103对照：[examples/timer-pwm](../../examples/timer-pwm/README.md) 为BluePill/HAL，HSE8MHz×9，APB1=36MHz/TIM3=72MHz，PSC71/ARR999、PA6。只有待集成main.c；初始ARR/2=499（49.9%），动态步长10会到CCR1000再回落，并非精确0–999。不可混用两条工程的时钟/复用/构建入口。
