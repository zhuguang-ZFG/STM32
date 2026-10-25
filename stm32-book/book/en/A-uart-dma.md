# A close reading: two valid contracts for UART + DMA + IDLE

The hard part of UART DMA is not calling one HAL function. It is choosing a **buffer-ownership contract** first. Two common shapes exist. Mixing the code from both is how you get duplicates, lost bytes, or a half frame overwritten.

## 1. Write the invariants first

Whichever shape you pick, write four invariants before the code:

1. The application does not write a region while DMA is writing it.
2. The callback's `Size` is the buffer position HAL reports. It equals "the length of this round" only under one contract: normal mode, re-armed after every event.
3. What you hand to the application is the **new slice**, not the whole array because it looks like a frame.
4. When the consumer falls behind, an overflow counter must move. Silent overwrite is not reliable reception.

ST's circular-DMA example lists HT, TC, and IDLE as callback sources and computes the new slice with `old_pos`. Community notes also point out that `Size` is the first unwritten position, possibly in `1..buffer_size`, not a fixed "length of this transfer." The snapshots are in [Appendix E](#appendix-references).

## 2. Contract A: normal DMA, re-armed after every event

This fits a command line, low or moderate throughput, and a wish for one contiguous block on each IDLE. The decision that matters: **turn the HT interrupt off, and turn it off again after every re-arm.** Otherwise a half-buffer event ends the round early and the next round overwrites the rest.

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

    /* Copy into the software queue first. If it is full, increment dropped_bytes. */
    ring_write(rx_dma, size);

    /* Re-arm. Do not disable HT only once at startup. */
    if (uart_rx_arm() != HAL_OK) {
        rx_rearm_errors++;
    }
}
```

There is a gap: a new byte can arrive, and raise ORE, while the callback is copying and re-arming. If the stream is fast, continuous, or must not have a gap, a larger buffer does not hide that. Use contract B.

## 3. Contract B: circular DMA, armed once, read by position

This fits a continuous stream. DMA does not stop. The application keeps the previous position. If `Size > old_pos`, the new slice is contiguous. If `Size < old_pos`, DMA wrapped, and you take the tail and then the head.

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

Do **not** call `HAL_UARTEx_ReceiveToIdle_DMA` again on every callback. Restarting resets the DMA position and makes `old_pos` meaningless. HT and IDLE can fire close together. The `pos == old_pos` check has to stay.

## 4. The boundary between the ISR and the application

`ring_write` may copy a bounded slice and count. It must not parse JSON, take a mutex, block on a transmit, or print a long log from the ISR. A single-producer, single-consumer ring you can audit exposes at least:

| State | Owner | What you can observe |
| --- | --- | --- |
| DMA write position | DMA / HAL | `Size`, or a position derived from NDTR |
| Software write position | ISR | Bytes successfully queued |
| Software read position | Main loop or task | Bytes consumed |
| Queue full | ISR | `dropped_bytes`; no silent overwrite |
| UART error | HAL error callback | ORE/FE/NE counts and the restart result |

If you use a FreeRTOS queue or stream buffer, the UART/DMA interrupt may call `...FromISR` only when its numeric priority satisfies `configMAX_SYSCALL_INTERRUPT_PRIORITY`. Priority 0 is the logically highest priority and must not call those APIs directly.

## 5. Two C edges that get missed

### The return value of `vsnprintf` is not the number of bytes stored

When the buffer is short, `vsnprintf` returns how many bytes it would have written, which can be larger than the array. Passing that value to the UART reads off the end. Clamp it to `sizeof(buf) - 1`:

```c
int n = vsnprintf(buf, sizeof(buf), fmt, ap);
if (n > 0) {
    size_t used = (size_t)n < sizeof(buf) ? (size_t)n : sizeof(buf) - 1U;
    HAL_UART_Transmit(&huart1, (uint8_t *)buf, (uint16_t)used, 100U);
}
```

### On H7, "DMA done" is not "the CPU sees the new bytes"

H7 still has two separate questions:

1. Can this DMA controller reach the memory region that holds the buffer? Some DMA cannot reach DTCM.
2. If the buffer is in a D-Cache region, do the CPU and DMA see the same bytes, through an MPU non-cacheable region or through clean/invalidate?

Changing only the linker script, or only adding a cache operation, can fix just one of the two. ST's H7 DMA article separates them. A migration should accept them separately.

## 6. A minimum check matrix

| Input | Expected | Evidence to record |
| --- | --- | --- |
| 1, 127, then 128 bytes, then a pause | The same bytes, no overrun of the buffer | Received length, CRC or a byte compare |
| A pause exactly at half the buffer | No duplicate, no early restart | Callback cause and the position sequence |
| A continuous stream past one lap | The tail and the head stay in order | The `old_pos → pos` trace |
| The application pauses until the queue is full | The overflow count rises; the system does not deadlock | `dropped_bytes` and the recovery |
| A forced ORE | The error is visible and reception can restart | Error flags and the restart status |
| H7 with cache on and off | Bytes match, or the failure is explicit | Memory section, cache operation, byte compare |

"The serial terminal showed something" is not the finish line. Each input should be explainable by length, position, error counts, and a byte compare.

## 7. Count the time in microseconds

A contract is not finished until you can say how long one event is. The first three numbers are pinned to an STM32F103C8T6, SYSCLK at 72 MHz, 115200, and 8N1. The last one belongs only to an H7 with a D-Cache. The steps and the BRR arithmetic are in the ledger at the end of [Appendix D](#appendix-glossary).

**One bit, and IDLE.** At 115200 bit/s one bit is about 8.68 µs. An 8N1 frame is 10 bits, about 86.8 µs. RM0008 sets IDLE when RX has been idle for one frame time, so one IDLE event means the line has been idle for about 86.8 µs. It does not mean a length field in the other side's protocol has arrived.

**NDTR is not a byte progress bar.** In normal mode, with a byte width and a buffer of 128, NDTR = 100 means `128 − 100 = 28` bytes have been written. Do not subtract like that in circular mode: NDTR reloads itself. Use `Size` and `old_pos` from the callback. If the width is a half-word, NDTR counts half-words, not bytes.

**The BRR fraction has to be in the division.** USART1 is on APB2, so its clock is 72 MHz, not APB1's 36 MHz. At 16× oversampling and 115200, `USARTDIV = 72e6 / (16 × 115200) = 39.0625`. The low 4 bits round to 1, BRR is `0x271`, and the divider lands on 115200 exactly. Drop that one fraction bit and the error becomes about 0.16%. The table in chapter 06 prints 39.0625 and 0.16% on the same row. The BRR `0x138` for USART2 at 36 MHz is the row that really is about 0.16% off. A note names which USART, and which 4 fraction bits, went into BRR.

**32 bytes on H7.** The D-Cache line is 32 bytes. Clean or invalidate a range aligned to that line, and align the buffer to 32 bytes. Invalidating only the few bytes just written drops or writes back the rest of the same line. Whether that memory can be reached by the DMA controller you chose is still a separate question.
