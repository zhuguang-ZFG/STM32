# 04 中断与 NVIC

> English: [Interrupts and the NVIC](en/04-interrupts-nvic.md)

> 中断让 CPU 不必死等外设，事件到来时自动跳转处理，是实时系统的核心机制。

<p align="center">
  <img src="../assets/animations/nvic-interrupt-flow.svg" width="760" alt="中断响应全流程">
  <br><sub>▲ 动画：中断响应全流程（入栈现场 → 取向量 → ISR → 出栈，作者自绘矢量图）</sub>
</p>

<!-- video:ch04 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch04-nvic.png">
    <source src="../assets/video/ch04-nvic.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解 2.5 分钟。配音是微软 Edge 在线神经语音「晓晓」（zh-CN-XiaoxiaoNeural），经 edge-tts 调用。edge-tts 大部分源码为 LGPLv3，srt_composer.py 为 MIT；声线模型是微软在线服务，不是开放模型。这里提交的是合成后的 MP4，离线可看。重新生成需要联网。画面用文泉驿微米黑绘制，插图是本仓库 SVG，不是实拍。 字幕：<a href="../assets/video/ch04-nvic.srt">SRT</a>。由 <code>python3 tools/gen_narrated.py --speak</code> 用 ffmpeg 合成。</sub>
</p>

**旁白（与字幕、配音同一份稿）**

1. 轮询是你不停去问，中断是事情来了敲你的门。主程序可以继续干别的。进了中断服务，办完要清标志，不然门会一直响。
2. NVIC 这道总闸可以分成三档来记：这路中断开了没有，优先级谁高，有没有挂起还没处理。三档看全，才不会觉得中断时灵时不灵。
3. EXTI 的编号就是引脚号。EXTI0 同时只能留给一个端口。PA0 和 PB0 不能一起拿这条线。要两只按键，就换不同的脚号。
4. 这一帧是仓库画的中断路径。引脚边沿先进 EXTI，再由 NVIC 决定要不要打断当前程序，最后才进你写的服务函数。路径上任何一扇门关着，回调都不会来。
5. 优先级不是数字越大越急。F1 上要先看优先级分组切成什么样，才知道哪些位是抢占、哪些是子优先级。抄例程时把分组改了，顺序会整个翻掉。
6. 中断服务要短。别在里面调用会阻塞的延时，也别做很重的打印。置一个标志，或者塞进缓冲区，把慢活交回主循环。服务函数一长，别的中断就饿着。
7. 主循环和中断一起碰的变量，编译器可能会缓存。单字节标志加 volatile。超过一个字的数据，读的时候还得短暂关中断，否则会撕成两半。
8. 口诀：总闸分三档；同一编号的脚，EXTI 只能留一个端口。记住这两句，按键中断的大多数玄学都会消失。
9. 实验用一只按键走下降沿，服务函数里只翻转 PC13。按下能亮、松开不连翻，说明边沿和清标志都做对了。连翻多半是没清，或者抖动没处理。
10. 合上书，三问。EXTI0 能同时留给 PA0 和 PB0 吗？服务函数里为什么别写阻塞延时？总闸那三档各管什么？
<!-- /video:ch04 -->
## 📌 学习目标
- [ ] 说清中断与轮询的差异及适用场景
- [ ] 掌握 NVIC 抢占优先级 / 子优先级分组规则
- [ ] 理解中断响应的硬件全流程（入栈 → 取向量 → ISR → 出栈）
- [ ] 会配置 EXTI 外部中断并注意 AFIO 时钟
- [ ] 会用 volatile、临界区，知道中断里为什么不能用 `HAL_Delay`

## 🧠 核心原理

**结论先行：中断把「CPU 反复查询」换成「外设主动通知」，代价是要正确处理优先级、共享变量和耗时。**

### 1. 中断 vs 轮询

| 维度 | 轮询（Polling） | 中断（Interrupt） |
| --- | --- | --- |
| CPU 占用 | 高（一直查） | 低（事件才响应） |
| 响应延迟 | 取决于轮询周期 | 通常几个时钟周期 ~ 微秒 |
| 代码复杂度 | 低 | 中（要处理优先级/共享变量） |
| 实时性 | 差（可能漏事件） | 好 |
| 适用场景 | 简单、事件稀少、要求确定性 | 事件异步、要求快速响应 |

### 2. NVIC 优先级机制

- 优先级**数值越小，优先级越高**。
- 优先级分「抢占优先级（preemption）」和「子优先级（subpriority）」。
- 抢占优先级高的可以打断抢占优先级低的 ISR；**同抢占优先级不能互相打断**（即使子优先级不同）。
- 子优先级只在多个中断**同时挂起**时决定谁先执行，不产生嵌套。
- 分组由 `HAL_NVIC_SetPriorityGrouping()` / `NVIC_PriorityGroupConfig()` 决定。

| 分组宏（HAL） | 抢占位 | 子优先级位 | 可表示的抢占级数 |
| --- | --- | --- | --- |
| `NVIC_PRIORITYGROUP_0` | 0 | 4 | 1（无抢占） |
| `NVIC_PRIORITYGROUP_1` | 1 | 3 | 2 |
| `NVIC_PRIORITYGROUP_2` | 2 | 2 | 4 |
| `NVIC_PRIORITYGROUP_3` | 3 | 1 | 8 |
| `NVIC_PRIORITYGROUP_4` | 4 | 0 | 16（HAL 默认） |

优先级仲裁示意图：

<p align="center">
  <img src="../assets/diagrams/interrupt-priority.svg" width="760" alt="抢占优先级与子优先级仲裁示意">
  <br><sub>▲ 图示：抢占优先级 vs 子优先级的仲裁示意（作者自绘矢量图）</sub>
</p>

### 3. 中断响应全流程

| 阶段 | 硬件动作 |
| --- | --- |
| 1 | 外设事件置位标志（如 `EXTI_PR` 对应位） |
| 2 | 外设把请求送到 NVIC，NVIC 置挂起位 |
| 3 | CPU 完成当前指令，比较优先级，决定是否响应 |
| 4 | 硬件自动入栈 8 个寄存器（xPSR, PC, LR, R12, R3, R2, R1, R0） |
| 5 | 从向量表取出 ISR 地址，跳转执行 |
| 6 | 执行用户 ISR，**清中断标志** |
| 7 | 出栈恢复现场，返回主程序 |

### 4. EXTI 外部中断

| 概念 | 说明 |
| --- | --- |
| EXTI 线 | 每条线对应一个（或一组）GPIO 引脚 |
| 触发方式 | 上升沿 / 下降沿 / 双边沿 |
| AFIO | F1 上配置 EXTI 引脚映射需使能 `__HAL_RCC_AFIO_CLK_ENABLE()`（**F1 特有坑**） |
| 映射 | `AFIO->EXTICR[x]` 选择 EXTI 线连到哪个端口（PAx/PBx/…） |

轮询 vs 中断 vs EXTI 对比动画：

<p align="center">
  <img src="../assets/animations/gpio-input-interrupt.svg" width="760" alt="轮询 vs 中断 vs EXTI">
  <br><sub>▲ 动画：轮询 vs 外部中断 vs EXTI 触发方式对比（作者自绘矢量图）</sub>
</p>

### 5. 关键 C 语义

| 概念 | 作用 |
| --- | --- |
| `volatile` | 告诉编译器变量可能在 ISR 中被改，禁止优化缓存 |
| 临界区 `__disable_irq()/__enable_irq()` | 关/开总中断，保护共享数据 |
| `__DSB()` | 数据同步屏障，保证内存访问完成 |
| 中断里禁用 `HAL_Delay` | 它依赖 SysTick 中断，若被同级/更高级屏蔽会死等 |

## 🛠️ 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | 按键（EXTI） | PA0 | 另一端接 GND，下降沿触发 |
| BluePill | LED | PC13 | 中断里翻转 |

## 💻 代码实现

```c
/* exti_key.c —— PA0 按键外部中断翻转 PC13（含标志位 + 主循环消抖） */
#include "stm32f1xx_hal.h"

#define LED_PIN   GPIO_PIN_13
#define LED_PORT  GPIOC
#define KEY_PIN   GPIO_PIN_0
#define KEY_PORT  GPIOA

static volatile uint8_t g_key_flag = 0;   /* ISR 与主循环共享，必须 volatile */

void SystemClock_Config(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();          /* F1 关键：EXTI 需要 AFIO 时钟 */

    GPIO_InitTypeDef io = {0};

    /* PC13 LED 输出 */
    io.Pin = LED_PIN; io.Mode = GPIO_MODE_OUTPUT_PP;
    io.Pull = GPIO_NOPULL; io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    /* PA0 按键，下降沿触发中断（按键接 GND，平时上拉为高） */
    io.Pin  = KEY_PIN;
    io.Mode = GPIO_MODE_IT_FALLING;       /* 下降沿中断 */
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);

    /* 配置 NVIC：抢占优先级 1，子优先级 0 */
    HAL_NVIC_SetPriority(EXTI0_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);

    while (1)
    {
        if (g_key_flag)
        {
            g_key_flag = 0;
            HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        }
    }
}

/* EXTI0 中断服务函数（PA0 映射到 EXTI0） */
void EXTI0_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(KEY_PIN) != RESET)
    {
        __HAL_GPIO_EXTI_CLEAR_IT(KEY_PIN);   /* 必须清标志，否则反复进中断 */
        g_key_flag = 1;                      /* 只置标志，不做耗时操作 */
    }
}
```

主循环侧软件消抖（避免机械抖动导致多次翻转）：

```c
if (g_key_flag)
{
    HAL_Delay(20);                          /* 主循环里延时是安全的 */
    if (HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN) == GPIO_PIN_RESET)  /* 仍为低 */
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
    }
    g_key_flag = 0;
}
```

临界区保护（主循环读多字节共享变量时）：

```c
uint32_t snapshot;
__disable_irq();          /* 关总中断 */
snapshot = g_shared_counter;
__enable_irq();           /* 开总中断 */
```

完整工程见 [`examples/exti-key/`](../examples/exti-key/)。

## ⚠️ 常见坑与排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 中断进不去 | 没使能 NVIC / 没配 EXTI / 没开 AFIO 时钟 | 补 `HAL_NVIC_EnableIRQ` + `__HAL_RCC_AFIO_CLK_ENABLE` |
| 一直反复进中断 | 忘记清中断标志 | ISR 里调 `__HAL_GPIO_EXTI_CLEAR_IT()` |
| 按一次触发多次 | 机械抖动 | 软件消抖或 RC 滤波 |
| 主循环读到的标志不更新 | 变量没加 volatile | 共享变量加 `volatile` |
| 中断里程序卡死 | 调用了 `HAL_Delay` | 中断里只置标志，耗时操作放主循环 |
| 高优先级中断丢事件 | 低优先级被长时间屏蔽 | 缩短 ISR，用「中断置标志 + 主循环处理」两级 |
| F4 上 EXTI 好使、F1 上不触发 | F1 忘开 AFIO 时钟 | 加 `__HAL_RCC_AFIO_CLK_ENABLE()` |

## 🧪 动手实验

1. **实验一**：PA0 按键下降沿中断翻转 PC13，按一次亮/灭一次。
2. **实验二**：去掉软件消抖，快速按键观察多次翻转；再加上消抖对比。
3. **实验三（优先级）**：增加第二个定时器中断，设不同抢占优先级，验证高抢占能打断低抢占 ISR。

### 6. NVIC 相关寄存器与函数

| 项目 | 说明 |
| --- | --- |
| ISER | 中断使能置位寄存器 |
| ICER | 中断使能清除寄存器 |
| ISPR/ICPR | 挂起/解挂 |
| IPR | 优先级寄存器（每 8 位一个） |
| `HAL_NVIC_SetPriority` | 设置抢占/子优先级 |
| `HAL_NVIC_EnableIRQ` | 使能中断 |
| `HAL_NVIC_SetPriorityGrouping` | 设置分组 |

### 7. SysTick 与 HAL 时基

- `HAL_Init()` 会把 SysTick 配置为 1ms 中断，`HAL_Delay()` 依赖它。
- SysTick 优先级通常设为最低（`TICK_INT_PRIORITY`），避免打断业务中断。
- 若在 ISR 中调用 `HAL_Delay()`，且该 ISR 优先级高于 SysTick，则计数不前进 → 死等。

### 8. 中断嵌套与优先级示例

```c
/* 高抢占（数值小）可打断低抢占；同抢占不可打断 */
HAL_NVIC_SetPriority(EXTI0_IRQn, 1, 0);   /* 抢占 1 */
HAL_NVIC_SetPriority(TIM2_IRQn, 2, 0);    /* 抢占 2，会被 EXTI0 打断 */
HAL_NVIC_EnableIRQ(EXTI0_IRQn);
HAL_NVIC_EnableIRQ(TIM2_IRQn);
```

### 9. 优先级分组选择建议

| 场景 | 建议分组 |
| --- | --- |
| 不用 RTOS | GROUP_4（全抢占） |
| 用 FreeRTOS | GROUP_4（RTOS 要求全抢占） |
| 需要子优先级仲裁 | GROUP_2 |

### 10. 中断响应开销与优化机制

| 机制 | 说明 |
| --- | --- |
| 硬件入栈 | 自动保存 8 个寄存器，约 12 个时钟周期 |
| 尾链（Tail-chaining） | 连续中断省去出栈再入栈 |
| 晚到（Late-arriving） | 入栈期间更高优先级抢占 |
| 优化建议 | ISR 尽量短，耗时操作交给主循环 |

### 11. 三把总闸，和共用的 EXTI 线

**结论**：`PRIMASK` 关掉除 NMI 和 HardFault 以外的全部中断；`FAULTMASK` 连 HardFault 也关，只留 NMI；`BASEPRI` 只挡住“优先级数值 ≥ 阈值”的那一截（数值越大，优先级越低）。

| 寄存器 | 挡住谁 | 常见写法 |
| --- | --- | --- |
| PRIMASK | 全部可屏蔽中断 | `__disable_irq()` / `__enable_irq()` |
| FAULTMASK | 再加 HardFault | `__disable_fault_irq()` |
| BASEPRI | 数值不够优先的那些 | `__set_BASEPRI(prio << (8 - __NVIC_PRIO_BITS))` |

EXTI 线是按**引脚号**共用的：PA0 和 PB0 都连在 EXTI0 上，不能同时做外部中断。要换端口，改 `AFIO->EXTICR`（F1）或 `SYSCFG->EXTICR`（F4），不是两条线并行。

口诀：**总闸分三档；同一编号的脚，EXTI 只能留一个端口。**

自测：

1. `__disable_irq()` 之后，HardFault 还能进来吗？
2. PA0 已经接了按键中断，PB0 还能再挂一个 EXTI 下降沿吗？
3. BASEPRI 的阈值是“数值更大更优先”还是相反？

## 🔗 相关资源

- 官方手册：**RM0008** 第 10 章（中断与事件 EXTI）、第 9.2.7 节（AFIO_EXTICR）；《Cortex-M3 权威指南》（NVIC/异常处理）
- 上一篇：[03 GPIO与LED](03-GPIO与LED.md)｜下一篇：[05 定时器与PWM](05-定时器与PWM.md)
- 相关图：[`assets/animations/nvic-interrupt-flow.svg`](../assets/animations/nvic-interrupt-flow.svg)、[`assets/animations/gpio-input-interrupt.svg`](../assets/animations/gpio-input-interrupt.svg)、[`assets/diagrams/interrupt-priority.svg`](../assets/diagrams/interrupt-priority.svg)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。

