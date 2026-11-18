# 02-tim-pwm：TIM3 输出、独立 TIM2 捕获

配套现行章节：[ch12 定时器与PWM](../../../../docs/v1-drivers/12-timers-pwm.md)。完整步骤、接线、安全、波形方法、判据与待填记录见 [PWM取证协议](../../../../labs/timer-pwm/README.md)。

| 功能 | 当前main.c |
| --- | --- |
| PWM输出 | PA6/AF2/TIM3_CH1，COUNT_HZ=1MHz、ARR999、PSC按TIMclk计算 |
| 输入捕获 | PA0/AF1/TIM2_CH1，32位自由计数、IRQ28；接PA6→PA0 |
| 时钟对比 | system_clock()/timer_clock()按RCC推导；短暂切APB1=/2再恢复 |
| 动态占空比 | phase每20ms推进，CCR10–1000（1%–100%）、周期约4秒加开销 |
| 捕获逻辑 | common/behavior/capture.h；g_measured_hz/edges/overcapture |

目标启动文件为STM32F407ZGT6，LED按霸天虎PF6/PF8低亮；实际板型待核实。旧PA7、TIM3_CH2、CC2IF说明不适用，不是同一个TIM3自捕获。

冷复位HSI名义16MHz且APB1=/1时，理论TIMclk16MHz、PSC15、ARR999→1kHz；/2时PCLK1为8MHz，定时器×2仍16MHz。g_tim_clk_*是依据寄存器与名义时钟推导，**不是波形实测**；84MHz/PSC83仅属其他时钟条件，不套用。

初始CCR500很快被循环覆盖；当前程序不是固定50%模式。100%平台无上升沿，不能要求捕获和蓝灯所有相位始终稳定。固定CCR/改ARR实验需以后另行确认固件变更，本轮不实施。

## 后续构建烧录（本轮未执行）

保留common/behavior相对目录，在本目录和既有兼容Make环境运行：

```bash
make          # build/tim-pwm.elf/.bin/.hex/.map
make flash    # OpenOCD/ST-Link verify reset
```

工具链、单一供电、SWD、日志/哈希规则见取证协议。make debug/make gdb为既有调试目标，后者含load会写板。失败时先分PA6输出、PA0捕获、TIM2中断三层；TIM3没有MOE，不能按TIM1的MOE排错。

状态：`hardware_status: pending`，源码亦标Hardware measurements pending。当前只有静态公式与宿主逻辑的验证边界，尚缺真实身份、构建/verify、寄存器回读、PA6/PA0原始波形、仪器误差与静态CCR对账；不得宣称已经上板测出APB倍频规则。
