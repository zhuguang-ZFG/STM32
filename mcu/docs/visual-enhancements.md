---
title: 视觉增强示例
description: 展示本站的视觉增强元素：Callout 盒子、代码块美化、链接动效等
---

# 视觉增强示例

> 🎨 本页展示本站的视觉增强元素，让学习成为一种享受。

## Callout 盒子

### 💡 Tip 盒子

::: tip
**提示**：这是一个提示盒子，用于展示有用的建议和技巧。

使用 `volatile` 关键字告诉编译器：这个变量可能会被硬件或中断改变，每次使用都必须真实访存。
:::

### ⚠️ Warning 盒子

::: warning
**警告**：这是一个警告盒子，用于提醒潜在的陷阱。

**常见错误**：把 `volatile int flag` 当锁用——volatile 只保证访存，不保证原子性和顺序！
:::

### ℹ️ Info 盒子

::: info
**信息**：这是一个信息盒子，用于补充背景知识。

Cortex-M4 的 SysTick 是 24 位递减计数器，最大单次延时 = (2^24 - 1) / 时钟频率。
:::

### 🚨 Danger 盒子

::: danger
**危险**：这是一个危险盒子，用于标记严重错误。

**铁律**：Flash 写操作前必须先擦除整个扇区！写入只能 1→0，擦除才能 0→1。
:::

## 代码块美化

```c
// 位带操作：原子翻转 PF6
#define GPIOF_ODR_BIT6_ALIAS \
    (*(volatile uint32_t *)(0x42000000 + ((0x40021414 - 0x40000000) << 5) + (6 << 2)))

int main(void) {
    // 配置 PF6 为输出
    GPIOF_MODER |= (1UL << 12);
    
    // 位带翻转
    while (1) {
        GPIOF_ODR_BIT6_ALIAS = 0;  // 亮
        delay(500);
        GPIOF_ODR_BIT6_ALIAS = 1;  // 灭
        delay(500);
    }
}
```

```python
# Python 示例：计算 SysTick LOAD 值
def calc_systick_load(clock_hz, period_ms):
    """
    计算 SysTick LOAD 寄存器值
    
    Args:
        clock_hz: 系统时钟频率（Hz）
        period_ms: 期望周期（毫秒）
    
    Returns:
        LOAD 寄存器值（24 位）
    """
    ticks = clock_hz * period_ms // 1000
    if ticks > 0x01000000:
        raise ValueError("超出 24 位范围")
    return ticks - 1

# 16MHz 时钟，1ms 周期
load = calc_systick_load(16_000_000, 1)
print(f"LOAD = {load} (0x{load:06X})")
```

## 表格美化

| 操作 | 寄存器 | 原子性 | 适用场景 |
|---|---|---|---|
| BSRR 置位 | `BSRR = (1 << N)` | ✅ 原子 | GPIO 专用，最常用 |
| BSRR 复位 | `BSRR = (1 << (N+16))` | ✅ 原子 | GPIO 专用 |
| ODR 读-改-写 | `ODR \|= (1 << N)` | ❌ 非原子 | 中断可能打断 |
| 位带操作 | `ALIAS = 1` | ✅ 原子 | 通用外设 |

## 引用块

> 🎯 同一段轮询，`-O0` 跑得好好的，`-O2` 一开就死等。编译器没坏——它只是不知道那个地址后面藏着一台会自己变状态的机器。

## 列表

### 有序列表

1. **开时钟**：RCC_AHB1ENR 的 GPIOFEN 位
2. **配模式**：MODER6=01(输出) / OTYPER6=0(推挽)
3. **控数据**：BSRR 低 16 位置位、高 16 位复位

### 无序列表

- **volatile**：保证每次使用都真实访存
- **原子操作**：不可被中断打断的操作
- **临界区**：关中断保护的代码段

## 链接动效

悬停查看链接下划线动效：

- [C3 volatile：跟编译器约法三章](/c/03-volatile)
- [S4 NVIC 与 EXTI](/stm32/04-nvic-exti)
- [F3 调度器](/rtos/freertos/03-scheduler)
- [交互式学习路径](/learning-path)

## 图片

![volatile 的访存合同](/anim/volatile-as-if.svg)

## 总结

本站的视觉增强元素：

✅ **Callout 盒子**：4 种类型（tip/warning/info/danger）  
✅ **代码块美化**：阴影、圆角、语言标签  
✅ **表格美化**：品牌表头、斑马纹、悬停高亮  
✅ **链接动效**：悬停下划线渐显  
✅ **图片阴影**：悬停上浮效果  
✅ **引用块**：渐变背景 + 装饰引号  
✅ **移动端优化**：响应式字号和间距  

这些元素让学习成为一种享受 🎉
