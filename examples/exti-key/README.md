# exti-key —— EXTI 外部中断按键

> 难度：★★☆☆　｜　涉及外设：GPIO + EXTI + NVIC　｜　对应章节：[04 中断与 NVIC](../../docs/04-中断与NVIC.md)

<p align="center">
  <img src="../../assets/animations/gpio-input-interrupt.svg" width="760" alt="轮询 vs 中断 vs EXTI 对比">
  <br><sub>▲ 动画：轮询 vs 外部中断 vs EXTI 触发方式对比（作者自绘矢量图）</sub>
</p>

## 一、功能说明

用 PA0 按键的**下降沿中断**翻转板载 LED(PC13)，演示中断编程的标准范式：

- **两级结构**：ISR 只置 `volatile` 标志，耗时处理放主循环；
- **软件消抖**：主循环延时 20ms 后确认电平仍为低，才认为是有效按键；
- **回调写法**：用 HAL 的 `HAL_GPIO_EXTI_Callback`，而不是在 `EXTI0_IRQHandler` 里直接写逻辑；
- **NVIC 优先级**：`HAL_NVIC_SetPriority` 设置抢占/子优先级。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | 按键 | PA0 | 一端接 PA0，另一端接 GND | 内部上拉，**按下为低** |
| BluePill | LED | PC13 | 板上已接 | 低电平点亮 |

> 无外部按键时，可用杜邦线把 PA0 瞬时接到 GND 模拟一次按下。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| GPIO PA0 | GPIO_EXTI0 / **Pull-up** / External Interrupt Mode with Falling edge | 下降沿触发 |
| NVIC | EXTI line0 interrupt → Enabled | 抢占 1，子优先级 0 |
| NVIC Priority Group | 4 bits for pre-emption（默认） | HAL 默认分组 |
| RCC → HSE | Crystal/Ceramic Resonator | 8MHz 晶振 |
| SYS → Debug | Serial Wire | 保留 SWD |

> **F1 特有坑**：`HAL_GPIO_Init` 配置 EXTI 模式时会自动使能 AFIO 时钟，但若你手动写寄存器映射，务必 `__HAL_RCC_AFIO_CLK_ENABLE()`。

## 四、关键代码解读

**1) 把引脚配成「中断模式」**

```c
io.Pin  = KEY_PIN;
io.Mode = GPIO_MODE_IT_FALLING;   /* 下降沿中断；另有 _RISING / _RISING_FALLING */
io.Pull = GPIO_PULLUP;            /* 平时为高，按下接地为低 */
HAL_GPIO_Init(KEY_PORT, &io);
```

**2) NVIC 优先级设置**

```c
HAL_NVIC_SetPriority(EXTI0_IRQn, 1, 0);   /* 抢占=1，子优先级=0，数值越小越优先 */
HAL_NVIC_EnableIRQ(EXTI0_IRQn);           /* 使能该中断线，否则永远进不去 */
```

**3) 中断服务函数 + 回调（两级结构）**

```c
void EXTI0_IRQHandler(void)                 /* 向量：PA0 → EXTI0 */
{
    HAL_GPIO_EXTI_IRQHandler(KEY_PIN);      /* HAL 内部清标志并回调 */
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)   /* 运行在中断上下文 */
{
    if (GPIO_Pin == KEY_PIN) { g_key_event = 1; g_key_count++; }  /* 只置标志 */
}
```

**4) 主循环消抖处理（可安全用 HAL_Delay）**

```c
if (g_key_event) {
    __disable_irq(); g_key_event = 0; __enable_irq();   /* 临界区保护标志 */
    HAL_Delay(KEY_DEBOUNCE_MS);                          /* 等抖动过去 */
    if (HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN) == GPIO_PIN_RESET) {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);           /* 确认按下才翻转 */
    }
}
```

`volatile` 让编译器每次都从内存读 `g_key_event`，不会被优化成寄存器缓存。

## 五、编译烧录步骤

1. 用 CubeMX 生成 F103C8 工程，把本 `main.c` 覆盖 `Core/Src/main.c`（保留生成的 `stm32f1xx_it.c` 中 `SysTick_Handler`；若其中已有 `EXTI0_IRQHandler` 请删除以免重复定义）。
2. 编译（Keil：`F7`；CubeIDE：🔨）→ 下载（Keil：`F8`；CubeIDE：▶）。
3. PlatformIO：`pio run -t upload`。

## 六、预期现象

- 上电后 LED 熄灭；每按一次 PA0 按键，LED 亮/灭翻转一次；
- 快速连按不会出现「按一次翻多次」的抖动现象（消抖生效）；
- 在 ISR 里打断点，可看到每次按键进入一次中断。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 中断进不去 | 没使能 NVIC 或没配 EXTI | 补 `HAL_NVIC_EnableIRQ` + `GPIO_MODE_IT_xxx` |
| 一直反复进中断 | 忘记清标志 | `HAL_GPIO_EXTI_IRQHandler` 会清；自查是否绕过它 |
| 按一次触发多次 | 机械抖动 | 主循环消抖 10~20ms，或加 RC 滤波 |
| 主循环标志不更新 | 变量没加 `volatile` | 共享变量加 `volatile` |
| F4 能进、F1 不进 | F1 漏开 AFIO 时钟 | `__HAL_RCC_AFIO_CLK_ENABLE()` |
| 中断里程序卡死 | 调用了 `HAL_Delay`/`printf` | ISR 只置标志，耗时操作放主循环 |

## 八、相关资源

- 参考手册 **RM0008** 第 10 章（EXTI 中断与事件）、第 9.2.7 节（AFIO_EXTICR）
- 《Cortex-M3 权威指南》异常与 NVIC 章节
- 相关图：[`assets/animations/nvic-interrupt-flow.svg`](../../assets/animations/nvic-interrupt-flow.svg)、[`assets/diagrams/interrupt-priority.svg`](../../assets/diagrams/interrupt-priority.svg)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。
