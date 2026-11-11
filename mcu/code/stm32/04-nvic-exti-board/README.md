# S04 EXTI 外部中断演示

> 配套章节：[S4 NVIC 与 EXTI](../../docs/stm32/04-nvic-exti.md)

## 实验目标

按键 KEY1（PA0）触发外部中断，ISR 翻转红灯 PF6。

## 硬件需求

- **板卡**：野火 STM32F407 霸天虎
- **按键**：KEY1（PA0，按下接地，松开上拉）
- **LED**：板载 RGB 红灯 PF6
- **调试器**：ST-Link V2 + OpenOCD

## 核心概念

**EXTI 三层链路**：
1. **EXTI 控制器**：检测引脚边沿（上升/下降/双沿），置位挂起位
2. **NVIC 中断控制器**：优先级仲裁，压栈跳转
3. **CPU 内核**：执行 ISR，EXC_RETURN 返回

**配置流程**：
```
开时钟 → 配 GPIO → SYSCFG 映射 → EXTI 使能 → NVIC 使能 → ISR
```

## 构建与烧录

```bash
make            # 构建 build/exti.elf + .bin + .hex
make flash      # 烧录到板子
make debug      # 启动 OpenOCD GDB 服务（另开终端）
make gdb        # 连接调试
```

## 预期现象

- 上电后红灯灭
- 按下 KEY1 不触发（配置为上升沿）
- **松开 KEY1 时红灯翻转**（上升沿触发 EXTI0）
- 每次松开按键，红灯亮→灭→亮→灭...

## 关键代码解析

### SYSCFG 映射
```c
SYSCFG_EXTICR1 &= ~(0xFUL << (KEY1_PIN * 4));  /* 清零 */
SYSCFG_EXTICR1 |=  (0x0UL << (KEY1_PIN * 4));  /* 0000 = GPIOA */
```
PA0 映射到 EXTI0（EXTICR1 的低 4 位 = 0000 表示 GPIOA）。

### EXTI 配置
```c
EXTI_IMR |= (1UL << KEY1_PIN);      /* 使能中断 */
EXTI_RTSR |= (1UL << KEY1_PIN);     /* 上升沿触发 */
```

### ISR 清挂起
```c
EXTI_PR = (1UL << KEY1_PIN);        /* 写 1 清 0（W1C） */
```
**不清挂起位 = 进一次中断再也出不来**（这是新手第二大坑）。

## 延伸阅读

- [S4 NVIC 与 EXTI](../../docs/stm32/04-nvic-exti.md)：三层链路、优先级分组、向量表
- [S3 GPIO](../../docs/stm32/03-gpio.md)：GPIO 配置四件套
- [host-probe 工程](../04-nvic-exti/)：主机端 `_Static_assert` 验证寄存器地址
