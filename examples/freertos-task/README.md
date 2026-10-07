# freertos-task —— FreeRTOS 三任务 + 队列 + 信号量 + FromISR

> 难度：★★★★　｜　涉及外设：GPIO/EXTI/USART + FreeRTOS　｜　对应章节：[15 FreeRTOS 入门](../../docs/15-FreeRTOS入门.md)

<p align="center">
  <img src="../../assets/animations/freertos-scheduler.svg" width="760" alt="FreeRTOS 任务状态迁移与抢占式调度">
  <br><sub>▲ 动画：FreeRTOS 任务状态迁移与抢占式调度（作者自绘矢量图）</sub>
</p>

## 一、功能说明

用 FreeRTOS 跑 **3 个任务**，演示 RTOS 最常用的三件套：

| 任务 | 优先级 | 职责 | 用到的 IPC |
| --- | --- | --- | --- |
| `vLedTask` | 1 | 每 500ms 翻转 LED | `vTaskDelay` |
| `vKeyTask` | 2 | 阻塞等待按键事件并打印 | `xQueueReceive` |
| `vUartTask` | 1 | 每 1s 打印心跳 | `xSemaphoreTake/Give` |

按键 **EXTI 中断**里用 `xQueueSendFromISR` 把事件送进队列（**FromISR API**），
串口发送用**互斥信号量**保护，避免多任务同时写串口导致输出互相穿插。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | 按键 | PA0 | 一端 PA0，另一端 GND | 下降沿中断 |
| BluePill | LED | PC13 | 板上已接 | LED 任务控制 |
| BluePill | USB-TTL | PA9/PA10 | 交叉连接 + 共地 | 115200 |

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| Middleware → FREERTOS → Interface | CMSIS_V1 | 使用原生 FreeRTOS API |
| FREERTOS → USE_PREEMPTION | Enabled | 抢占式调度 |
| FREERTOS → TICK_RATE_HZ | 1000 | 1ms 一个 tick |
| FREERTOS → TOTAL_HEAP_SIZE | ≥ 10240 | 三个任务栈 + 队列 |
| **SYS → Timebase Source** | **TIM4（不要用 SysTick）** | FreeRTOS 已占用 SysTick |
| NVIC → EXTI0 优先级 | 数值 ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY` | 否则 `FromISR` 会断言 |
| USART1 | 115200-8-N-1 | 日志输出 |

> ⚠️ **最关键的一条**：CubeMX 里把 HAL 时基源（Timebase Source）从 SysTick 改成 **TIMx**。
> 否则 HAL 和 FreeRTOS 都抢 SysTick，会出现 `HAL_Delay` 卡死或 tick 异常。

## 四、关键代码解读

**1) 中断里用 FromISR 版本 API**

```c
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
    if (GPIO_Pin == KEY_PIN) {
        uint8_t key_id = 1;
        BaseType_t woken = pdFALSE;
        xQueueSendFromISR(g_key_queue, &key_id, &woken);   /* 中断安全 */
        portYIELD_FROM_ISR(woken);                         /* 需要则立即切换 */
    }
}
```

**2) 任务阻塞等待队列（不占 CPU）**

```c
if (xQueueReceive(g_key_queue, &key_id, portMAX_DELAY) == pdTRUE) {
    /* 队列空时任务挂起，事件到来才被唤醒 */
}
```

**3) 互斥信号量保护共享资源（串口）**

```c
if (xSemaphoreTake(g_uart_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
    HAL_UART_Transmit(&huart1, s, len, 100);
    xSemaphoreGive(g_uart_mutex);      /* 用完必须归还，否则别人永远等不到 */
}
```

**4) 创建对象与启动调度器**

```c
g_key_queue  = xQueueCreate(8, sizeof(uint8_t));
g_uart_mutex = xSemaphoreCreateMutex();
xTaskCreate(vLedTask, "LED", 128, NULL, 1, NULL);
vTaskStartScheduler();                 /* 启动后不再返回 */
```

## 五、编译烧录步骤

1. CubeMX 生成 F103C8 工程，勾选 FreeRTOS（CMSIS_V1），**时基源改 TIM4**，覆盖 `Core/Src/main.c`。
2. 保留 CubeMX 生成的 `FreeRTOSConfig.h` 与 `Middlewares/Third_Party/FreeRTOS`。
3. 编译下载；串口助手 115200 观察输出。

## 六、预期现象

- 板载 LED 以 1Hz 稳定闪烁（`vLedTask`）；
- 串口每秒打印一行 `heartbeat N, tick=...`；
- 每按一次按键，串口打印一行 `KEY 1 pressed @... ms`；
- 多个任务同时输出时不会出现字符互相穿插（互斥量生效）。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 程序卡在调度器启动前 | HAL 时基与 RTOS 抢 SysTick | 时基源改 TIM4 |
| `configASSERT` 死循环 | 中断优先级数值太小 | 中断优先级 ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY` |
| 任务创建失败 | 堆空间不足 | 调大 `configTOTAL_HEAP_SIZE` |
| 串口输出乱 | 多任务同时发送 | 用互斥信号量保护 |
| 进入 HardFault | 栈太小溢出 | 加大任务栈，或用 `vApplicationStackOverflowHook` 定位 |
| 中断里调用普通 API 崩溃 | 用了非 FromISR 版本 | 中断内一律用 `xxxFromISR` |
| LED 不闪 | 优先级被高任务饿死 | 检查优先级；确保任务里有阻塞调用 |

## 八、相关资源

- FreeRTOS 官方文档（Task/Queue/Semaphore 章节）
- 参考手册 **RM0008**（EXTI、USART）
- 相关图：[`assets/animations/freertos-scheduler.svg`](../../assets/animations/freertos-scheduler.svg)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。
