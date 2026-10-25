# 工程深读：UART + DMA + IDLE 的两个正确契约

串口 DMA 的难点不是调用一个 HAL 函数，而是先选定**缓冲区所有权契约**。常见实现只有两类；把两类代码拼在一起，最容易造成重复、漏收或半帧覆盖。

## 1. 先写不变量

无论选哪一类，实现前都应写下四条不变量：

1. DMA 正在写的区域，应用不能同时改写。
2. 回调参数 `Size` 表示 HAL 报告的缓冲区位置；只有在“普通模式、每次事件后重新武装”这个特定契约中，它才等价于该轮长度。
3. 交给业务层的是**新增字节区间**，不是“看起来像一帧”的整个数组。
4. 软件消费者跟不上生产者时必须有可观察的溢出计数；静默覆盖不算可靠接收。

ST 的官方循环 DMA 例程明确列出 HT、TC、IDLE 三种回调来源，并用 `old_pos` 计算新增区间。社区经验帖也指出 `Size` 是首个未写位置，范围可能是 `1..buffer_size`，而不是固定意义的“本次长度”。来源快照见[附录 E](#appendix-references)。

## 2. 契约 A：Normal DMA，每次结束后重新武装

适合命令行、低到中等吞吐、希望每次 IDLE 都得到一块连续数据的场景。关键决定是：**关闭 HT 中断，并在每一次重新武装后再次关闭**。否则半缓冲事件会提前终止本轮，后半帧被下一轮覆盖。

```c
#define RX_DMA_CAP 128U
static uint8_t rx_dma[RX_DMA_CAP];

static HAL_StatusTypeDef uart_rx_arm(void)
{
    HAL_StatusTypeDef rc =
        HAL_UARTEx_ReceiveToIdle_DMA(&huart1, rx_dma, RX_DMA_CAP);
    if (rc == HAL_OK) {
        __HAL_DMA_DISABLE_IT(huart1.hdmarx, DMA_IT_HT);
    }
    return rc;
}

void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t size)
{
    if (huart->Instance != USART1) return;

    /* 先复制到软件队列；队列满时增加 dropped_bytes。 */
    ring_write(rx_dma, size);

    /* 再重新武装；不要只在启动时关闭一次 HT。 */
    if (uart_rx_arm() != HAL_OK) {
        rx_rearm_errors++;
    }
}
```

这个方案有一个明确空窗：回调复制与重新武装期间，新字节可能到达并触发 ORE。吞吐高、字节连续或不允许空窗时，不应靠“把缓冲区调大”掩盖，应改用契约 B。

## 3. 契约 B：Circular DMA，启动一次，按位置取增量

适合连续流。DMA 不停止，应用保存上一次位置。`Size > old_pos` 时新增区间连续；`Size < old_pos` 时说明 DMA 绕回数组开头，要处理尾段和头段。

```c
#define RX_DMA_CAP 128U
static uint8_t rx_dma[RX_DMA_CAP];
static uint16_t old_pos;

void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t pos)
{
    if (huart->Instance != USART1 || pos == old_pos) return;

    if (pos > old_pos) {
        ring_write(&rx_dma[old_pos], pos - old_pos);
    } else {
        ring_write(&rx_dma[old_pos], RX_DMA_CAP - old_pos);
        if (pos != 0U) ring_write(&rx_dma[0], pos);
    }
    old_pos = pos;
}
```

这里**不能**在每次回调重新调用 `HAL_UARTEx_ReceiveToIdle_DMA`。重新启动会重置 DMA 位置，破坏 `old_pos` 的意义。HT 与 IDLE 可能在相近时刻连续回调；`pos == old_pos` 的去重条件必须存在。

## 4. ISR 与业务层的边界

`ring_write` 只能做有界复制和计数，不能在 ISR 里解析 JSON、等待互斥量、阻塞发送或打印长日志。一个可审计的单生产者/单消费者环形队列至少暴露：

| 状态 | 责任 | 可观察量 |
| --- | --- | --- |
| DMA 写指针 | DMA/HAL | `Size` 或 NDTR 推导位置 |
| 软件写指针 | ISR | 成功入队字节数 |
| 软件读指针 | 主循环/任务 | 已消费字节数 |
| 队列满 | ISR | `dropped_bytes`，禁止静默覆盖 |
| UART 错误 | HAL 错误回调 | ORE/FE/NE 计数与重启结果 |

如果使用 FreeRTOS 队列或 stream buffer，UART/DMA 中断只有在数值优先级满足 `configMAX_SYSCALL_INTERRUPT_PRIORITY` 边界时才能调用 `...FromISR`。默认优先级 0 是逻辑最高优先级，不能直接调用这些 API。

## 5. 两个经常被忽略的 C 边界

### `vsnprintf` 的返回值不是已写入长度

缓冲区不足时，`vsnprintf` 返回“本来需要写多少字节”，可能大于数组容量。把该返回值直接交给 UART 会越界读取。应夹紧到 `sizeof(buf) - 1`：

```c
int n = vsnprintf(buf, sizeof(buf), fmt, ap);
if (n > 0) {
    size_t used = (size_t)n < sizeof(buf) ? (size_t)n : sizeof(buf) - 1U;
    HAL_UART_Transmit(&huart1, (uint8_t *)buf, (uint16_t)used, 100U);
}
```

### H7 的“DMA 完成”不等于“CPU 看见新数据”

H7 还要回答两个独立问题：

1. 所选 DMA 控制器能否访问缓冲区所在内存域；例如某些 DMA 不能访问 DTCM。
2. 缓冲区若处于 D-Cache 区，CPU 与 DMA 的可见副本是否通过 MPU 非缓存区或 clean/invalidate 保持一致。

只改链接脚本或只加 Cache 操作都可能只解决其中一半。ST 的 H7 DMA 文章把两类问题分开说明；迁移时也应分开验收。

## 6. 最小验证矩阵

| 输入 | 预期 | 要记录的证据 |
| --- | --- | --- |
| 1、127、128 字节后停顿 | 字节逐一相同，无越界 | 接收长度、CRC/逐字节比较 |
| 恰好半缓冲后停顿 | 不重复，不提前重启 | 回调原因与位置序列 |
| 超过一圈的连续流 | 跨尾/头连续 | `old_pos → pos` 轨迹 |
| 业务暂停直到队列满 | 溢出计数增加，系统不死锁 | `dropped_bytes` 与恢复结果 |
| 人为制造 ORE | 错误可见，接收可恢复 | 错误标志、重启返回值 |
| H7 Cache 开/关对照 | 数据一致或明确失败 | 内存段、Cache 操作、字节对比 |

完成标准不是“串口助手里看起来收到了”，而是每一条输入都能用长度、位置、错误计数和字节比较解释。

## 7. 把时间算到微秒

契约写完，还要能回答这一下有多长。前三笔钉在 STM32F103C8T6、SYSCLK 72 MHz、115200、8N1 上。最后一笔只属于带 D-Cache 的 H7。分档和 BRR 的算式在[附录 D](#appendix-glossary)文末的账里。

**一位和 IDLE。** 115200 bit/s 时一位约 8.68 µs。8N1 一帧是 10 位，约 86.8 µs。RM0008 里 IDLE 置位的条件是 RX 保持空闲满一个帧时间，所以一次 IDLE 表示线上已经空了大约 86.8 µs，不表示对方协议里的长度字段已经到了。

**NDTR 不是字节进度条。** 普通模式、字节宽度、缓冲区 128 时，若读到 NDTR = 100，已经写入 `128 − 100 = 28` 个字节。循环模式不要用这一减：NDTR 会自己重装，位置用回调里的 `Size` 和 `old_pos`。宽度若是半字，NDTR 的单位是半字，不是字节。

**BRR 的小数位要算进去。** USART1 在 APB2，时钟是 72 MHz，不是 APB1 的 36 MHz。16 倍过采样、115200：`USARTDIV = 72e6 / (16 × 115200) = 39.0625`。低 4 位收成 1，BRR = `0x271`，分频结果正好 115200。丢掉这 1 个小数位，才会得到大约 0.16%。第 06 章的表把 39.0625 和 0.16% 写在同一行；USART2 在 36 MHz 下的 BRR `0x138` 才真有大约 0.16%。记账时写清是哪一个 USART、BRR 的哪 4 位。

**H7 的 32 字节。** D-Cache 的行长是 32 字节。清洁或作废按对齐到行的区间做，缓冲区按 32 字节对齐。只对刚才写入的那几个字节做 invalidate，同一行里的其余字节会一起被丢掉或写回。这块内存能不能被所选 DMA 访问，仍是另一件事。

## 8. 请求先落到哪条通道

契约 B 的 `Size` 只有在请求真的进了这条 DMA 时才有意义。STM32F103C8 是中容量，只有 DMA1，7 条通道，没有 DMA2。把大容量的 DMA2 通道号抄到 C8 上，计数器不会动。

| 请求 | F103C8（RM0008，只有 DMA1） | F4（RM0090） |
| --- | --- | --- |
| USART1_TX | Channel 4 | DMA2 Stream 7，Channel 4 |
| USART1_RX | Channel 5 | DMA2 Stream 5，Channel 4 |
| ADC1 | Channel 1 | DMA2 Stream 0 或 Stream 4，Channel 0 |

F4 先选 Stream，再用 `CHSEL` 选 Channel。同一外设的 TX 和 RX 常常是不同的 Stream、同一个 Channel。FIFO 是 4 个 32 位字。F1 没有这级 FIFO，宽度不对时不会在 FIFO 里打包。

半字不要用字节去减。缓冲区长度 8、宽度是半字、`CNDTR` 读回 3：已经写入 `8 − 3 = 5` 个采样，字节数是 `5 × 2 = 10`。这个缓冲区的半传输发生在 4 个采样，也就是 8 个字节。按「每 4 字节处理一次」去切，会把后一半当成新数据。循环模式下不要用 `长度 − CNDTR` 当累计进度：计数归零后硬件会重装，位置仍用回调里的 `Size` 和 `old_pos`。

F1 的 DMA 控制器是 AHB 上的主机。它访问的外设寄存器在 APB，中间经过桥。外设时钟门没开时，请求不会出现，这和通道号选错是两件不同的事。
