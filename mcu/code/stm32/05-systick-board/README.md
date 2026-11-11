# S05 SysTick 延时演示

> 配套章节：[S5 SysTick：内核的心跳](../../docs/stm32/05-systick.md)

## 实验目标

用 SysTick 实现精确 1ms 节拍，`delay_ms(500)` 翻转红灯，逻辑分析仪验证周期。

## 硬件需求

- **板卡**：野火 STM32F407 霸天虎
- **LED**：板载 RGB 红灯 PF6
- **测量工具**：逻辑分析仪（测 PF6 翻转周期）
- **调试器**：ST-Link V2 + OpenOCD

## 核心概念

**SysTick** 是 Cortex-M4 内核自带的 24 位递减计数器：
- 4 个寄存器：CTRL、LOAD、VAL、CALIB（地址 0xE000E010 ~ 0xE000E01C）
- 从 LOAD 倒数到 0，触发中断后自动重装
- **周期 = (LOAD + 1) / 时钟频率**

**1ms 节拍计算**（16MHz HSI）：
```
LOAD = 16000000 / 1000 - 1 = 15999
```

## 构建与烧录

```bash
make            # 构建 build/systick.elf + .bin + .hex
make flash      # 烧录到板子
make debug      # 启动 OpenOCD GDB 服务（另开终端）
make gdb        # 连接调试
```

## 预期现象

- 红灯以 **1Hz** 频率闪烁（500ms 亮 + 500ms 灭）
- 逻辑分析仪测 PF6：高电平 500ms，低电平 500ms，周期 1000ms
- **精度**：误差 < 0.1%（SysTick 时钟精度 = 系统时钟精度）

## 关键代码解析

### SysTick 初始化
```c
SYSTICK_RVR = ticks_per_ms - 1;  /* LOAD = 周期 - 1 */
SYSTICK_CVR = 0;                  /* 清当前值 */
SYSTICK_CSR = ENABLE | TICKINT | CLKSOURCE;
```

**为什么 LOAD = 周期 - 1？**
- 计数器从 LOAD 倒数到 0，共 LOAD+1 个 tick
- 1ms = 16000 tick → LOAD = 15999

### 中断服务函数
```c
void SysTick_Handler(void) {
    g_ms_ticks++;
}
```

**中断号 -1**：SysTick 是 Cortex-M4 内核异常，不是外设中断。

### 阻塞延时
```c
static void delay_ms(uint32_t ms) {
    uint32_t start = g_ms_ticks;
    while ((g_ms_ticks - start) < ms) {}
}
```

**为什么用减法？**
- `g_ms_ticks` 会在 49.7 天后溢出回绕
- `(now - start)` 在溢出时仍能得到正确差值（无符号整数模运算）

## 对比软件延时

| 方式 | 精度 | CPU 占用 | 适用场景 |
|---|---|---|---|
| `for` 循环 | ❌ 差（受编译优化、时钟频率影响） | 100% | 简单演示，不要求精度 |
| SysTick 中断 | ✅ 高（依赖系统时钟） | 低（中断处理） | 需要精确延时 |
| DMA + TIM | ✅ 极高 | 0%（硬件自动） | 高精度、低功耗 |

## 24 位限制

SysTick 是 24 位计数器，最大 LOAD = 0xFFFFFF = 16777215。

**16MHz 下最大单次延时**：
```
16777216 / 16000000 = 1.048 秒
```

超过 1 秒的延时需要软件计数器累加（本工程的 `g_ms_ticks` 就是 32 位，可计 49.7 天）。

## 延伸阅读

- [S5 SysTick](../../docs/stm32/05-systick.md)：24 位限制、溢出处理、SysTick_Config 源码解析
- [S2 RCC 时钟树](../../docs/stm32/02-rcc-clock.md)：系统时钟配置（HSI/HSE/PLL）
- [host-probe 工程](../05-systick/)：主机端 `_Static_assert` 验证寄存器地址
