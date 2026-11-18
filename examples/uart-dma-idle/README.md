# uart-dma-idle —— UART + DMA + IDLE 不定长接收

> 难度：★★★☆　｜　涉及外设：USART + DMA + 环形缓冲　｜　对应章节：[第13章UART](../../docs/v1-drivers/13-uart-framed-protocol.md) / [第14章DMA](../../docs/v1-drivers/14-dma.md)

<p align="center">
  <img src="../../assets/animations/uart-frame.svg" width="760" alt="UART 帧结构逐位时序">
  <br><sub>▲ 动画：UART 帧结构逐位时序（起始位/数据位/校验/停止位，作者自绘矢量图）</sub>
</p>

> hardware_status: pending。仅提供F103C8 HAL示例main.c，缺完整HAL/启动/链接工程，本轮未全固件编译。生产回调的宿主受控HAL测试覆盖HT→IDLE/TC前缀重复与重装失败；未连接串口/写板/测吞吐。集成HAL必须真实提供ReceiveToIdle及GetRxEventType。

## 一、功能说明

用 USART1 的 **DMA + IDLE 空闲中断**实现不定长接收，收到的数据进入**软件环形缓冲区**，
主循环异步取出并做**命令行解析**（AT 指令风格）。相比「`HAL_UART_Receive` 定长接收」，
DMA搬到64字节接收区，ISR再复制到软件环；不是零拷贝。IDLE只是线路空闲交付事件，不是应用帧边界，命令行仍靠CR/LF组帧。

支持的命令：

| 指令 | 作用 | 返回 |
| --- | --- | --- |
| `AT` | 握手 | `OK` |
| `AT+LED=0/1` | 设置板载 LED（0 点亮） | `OK` |
| `AT+LED?` | 查询 LED 状态 | `+LED:<0/1>` |
| `AT+ECHO=0/1` | 开/关回显 | `OK` |
| `AT+INFO` | 固件信息 | 版本串 |
| `AT+RESET` | 软件复位 | `OK` |

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | USB-TTL 模块 | PA9 (TX) → 模块 RX | 交叉连接 | USART1_TX |
| BluePill | USB-TTL 模块 | PA10 (RX) ← 模块 TX | 交叉连接 | USART1_RX |
| BluePill | 共地 | GND ↔ GND | **必须共地** | 否则乱码 |
| BluePill | LED | PC13 | 板上已接 | 低电平点亮 |

> USB-TTL 模块选 3.3V 电平（如 CH340/CP2102 的 3V3 档），避免 5V 直连 IO。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| USART1 → Mode | Asynchronous | 异步串口 |
| USART1 → Baud Rate | 115200 | 8-N-1 |
| USART1 → DMA | USART1_RX → DMA1 Channel5, Normal | RX 用 DMA |
| NVIC | USART1 global interrupt = ✔ | IDLE 中断靠它 |
| NVIC | DMA1 channel5 global interrupt = ✔ | 传输完成/错误 |

> F1 的 DMA 请求映射固定：**USART1_RX = DMA1_CH5，USART1_TX = DMA1_CH4**（见 RM0008 表 78）。

## 四、关键代码解读

**1) 启动「DMA + 空闲」接收**

```c
/* DMA_NORMAL；首次与后续重装都检查返回值。 */
if (HAL_UARTEx_ReceiveToIdle_DMA(&huart1, g_dma_rx_buf, DMA_RX_BUF_SIZE) != HAL_OK) {
    error_handler();
}
```

**2) 接收事件回调（IDLE / 半满 / 满都会进这里）**

```c
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    if (huart->Instance == UART_INSTANCE)
    {
        /* DMA_NORMAL: HT只报进度，接收仍活动；等IDLE/TC后复制整个前缀一次。
         * 官方F1 HAL_UARTEx_GetRxEventType说明普通模式HT不终止接收。 */
        if (HAL_UARTEx_GetRxEventType(huart) == HAL_UART_RXEVENT_HT)
        {
            return;
        }
        rb_push(&g_rb, g_dma_rx_buf, Size);
        /* 重新武装：下一次不定长接收 */
        if (HAL_UARTEx_ReceiveToIdle_DMA(huart, g_dma_rx_buf, DMA_RX_BUF_SIZE) != HAL_OK)
        {
            error_handler(); /* 明确停机；不把重装失败当作已恢复接收。 */
        }
    }
}
```

DMA_NORMAL中HT的Size=32只是进度，不消费/重装；IDLE或TC终止时再复制当前传输的Size字节一次。Size不等于协议一帧，64字节TC也可能只是长命令的一段。重装HAL_ERROR/HAL_BUSY会进入既有error_handler明确停机，不是已保证恢复；错误回调也检查重装返回。

**3) 环形缓冲区（生产者=ISR，消费者=主循环）**

```c
static void rb_push(ring_buf_t *rb, const uint8_t *d, uint16_t len) {
    for (uint16_t i = 0; i < len; i++) {
        uint16_t next = (rb->head + 1) & (RING_BUF_SIZE - 1);
        if (next == rb->tail) break;      /* 满则丢 */
        rb->buf[rb->head] = d[i];
        rb->head = next;
    }
}
```

用 2 的幂大小 + 位与取模，`head/tail` 都是 `volatile`，天然适配「单生产者单消费者」无锁模型。

**4) 命令行解析（逐字节组帧，遇到 \r/\n 执行）**

```c
static void cmd_process_char(char c) {
    if (c == '\r' || c == '\n') {
        if (g_line_len) { g_line[g_line_len] = '\0'; cmd_execute(g_line); g_line_len = 0; }
        return;
    }
    if (g_line_len < CMD_LINE_MAX - 1) g_line[g_line_len++] = c;
}
```

## 五、编译烧录步骤

1. CubeMX 生成 F103C8 工程，按上表配 USART1 + DMA1_CH5，覆盖 `Core/Src/main.c`
   （若生成代码里已有 `USART1_IRQHandler` / `DMA1_Channel5_IRQHandler`，删除以免重复定义）。
2. 编译下载后，用串口助手（115200，勾选「发送新行」）输入 `AT` 回车。
3. 可复用本文件uart_dma_init，但仍依赖完整HAL、启动/链接配置及实际SysTick/IRQ入口；本仓库没有独立可构建F103工程，不能称其不依赖工程支持。

## 六、预期现象

- 上电串口打印 `[BOOT] uart-dma-idle ready. type 'AT' for help`；
- 输入 `AT` → 回显 `> AT` + `OK`；
- 输入 `AT+LED=0` → 板载 LED 点亮；`AT+LED?` → 返回 `+LED:0`；
- 连续发送仍可能在普通模式重装窗口或软件环满时丢字节；需原始序列与计数实测，不能由环形缓冲存在就保证不丢。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 收到乱码 | 波特率/时钟不符或未共地 | 统一 115200，接 GND |
| 只收到一次就停 | 未重装或重装返回失败 | 查HAL返回与error_handler；不要在普通模式HT事件重启活动DMA |
| 一帧被拆成多帧 | 发送端字符间有空闲 | 缩短发送间隔，或按协议头尾组帧 |
| 丢数据 | 环形缓冲太小/溢出 | 增大 `RING_BUF_SIZE`，或加溢出计数 |
| 中断进不去 | 没使能 USART1/DMA NVIC | `HAL_NVIC_EnableIRQ` 两处都要开 |
| 长命令截断/丢字节 | 重装窗口、软件环满或CMD_LINE_MAX边界 | 分别核DMA交付段与CR/LF组帧、长度及丢失，不能只加大DMA数组就保证无损 |
| 溢出错误后停机 | ORE或DMA重装失败 | 读取实际错误与重装返回；当前失败即明确停机，后续恢复策略需另行设计 |

## 八、相关资源

- 参考手册 **RM0008** 第 27 章（USART）、第 10 章（DMA 请求映射表 78）
- 应用笔记 AN4031《Using the STM32F2/F4 DMA controller》
- 相关图：[`assets/animations/uart-frame.svg`](../../assets/animations/uart-frame.svg)、[`assets/gif/uart-bits.gif`](../../assets/gif/uart-bits.gif)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。
