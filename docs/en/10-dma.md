# 10 DMA
> 中文：[10 DMA](../10-DMA.md)

> DMA (direct memory access) moves data between a peripheral and memory on its own. The CPU does not have to touch every byte, so the cycles stay available for the actual computation.

<p align="center">
  <img src="../../assets/animations/dma-circular.svg" width="760" alt="DMA circular mode: the CPU and DMA move data in parallel">
  <br><sub>▲ Animation: DMA circular mode moving ADC data while the CPU does other work (vector animation drawn by the author, not a live recording)</sub>
</p>

<!-- video:ch10 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch10-dma.png">
    <source src="../../assets/video/ch10-dma.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.6 min). <a href="../../assets/video/ch10-dma.mp4">MP4</a> · <a href="../../assets/video/ch10-dma.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. DMA 是搬运工。外设来了新数据，或者内存里有一包要送出去，它可以自己搬，CPU 继续算别的。前提是你把源、目的和数量写对。
2. 剩余数量记在 NDTR 里。它减到 0，这一轮就搬完了。循环模式下，硬件会把数量装回去，指针也回到起点。你不用在中断里手动重置。
3. 半传输标志按元素个数算。如果每个元素是半字，两个字节，你要再乘 2 才是字节数。用字节去切半字数组，后半段会从奇数地址开始，读出来是错的。
4. 这一帧是仓库画的循环搬运。写指针走到头就绕回来，旧数据会被新数据盖住。你如果处理得比 DMA 慢，就会丢一圈。速度要算得过，不能只看灯还在闪。
5. 外设数据宽度、内存宽度、地址增不增加，三项要和真实的寄存器一致。ADC 结果是半字，你却按字节去增地址，内存里会插进一堆空隙。
6. 半满的时候可以处理前半段，全满的时候处理后半段。中断里只做这个切换和必要的计算，不要阻塞。一阻塞，下一圈 DMA 已经把你还没看的数据盖掉了。
7. F103 没有数据缓存，DMA 和 CPU 看的是同一份内存。到了带缓存的 H7，CPU 看到的数组可能和总线上的不一样。那一章会再提，这里先把 F1 的搬运做对。
8. 口诀：剩下的在 NDTR；半字的半传输按元素算，再乘 2 才是字节。调试时把 NDTR 打出来，比猜「DMA 是不是坏了」快得多。
9. 实验让 DMA 把一串数搬进数组，断点时后半段应该已经变了，NDTR 也在减小。数组纹丝不动，先查通道、方向和使能，别先改算法。
10. 合上书，三问。NDTR 里装的是地址还是剩余数量？循环模式谁把指针拨回去？半字传输的半满，怎样换成字节数？

</details>
<!-- /video:ch10 -->

## Learning goals

Before this chapter: finish chapter 04 (ISRs and the NVIC), chapter 05 (a timer's PSC, ARR, and TRGO), chapter 06 (USART1 and how to wire a USB-TTL module), and chapter 09 (ADC conversions and external triggers). You should know that the elements of an array sit one after another in memory, that a pointer holds an address, and how to turn an element count into a byte count (if not, read the "Zero-background primer" in chapter 00 first).

- [ ] Say what DMA saves the CPU: for the same 64 bytes out of a UART, how much work polling, interrupts, and DMA each give the CPU
- [ ] Say that the STM32F103C8T6 has only the 7 channels of DMA1, and look up in the request map which one ADC1, USART1_TX, and USART1_RX each use
- [ ] Set up a channel in the manual's six steps: peripheral address, memory address, count, priority, direction and width, and enable last
- [ ] Work out from a CNDTR reading how many items and bytes have been written: 8 half-words with CNDTR = 3 means 5 samples and 10 bytes
- [ ] Use circular mode with the half-transfer and transfer-complete interrupts so the CPU handles one half while DMA writes the other, and work out how much time each half leaves the CPU
- [ ] Send a line of text out of USART1 through DMA, and say why you must wait for the USART's TC, not just the DMA's TC
- [ ] Say why the F4's "stream plus channel" numbering and the H7's cache coherency do not carry over to this chip

## Core ideas

**In one sentence: DMA is the porter inside the chip. You tell it where to carry from, where to carry to, and how many items, and each time the peripheral asks, it carries one, with no help from the CPU. The STM32F103C8T6 has a single DMA1 with 7 channels, and each peripheral's request is wired to one fixed channel.**

### An analogy first

Think of DMA as a porter in a warehouse, and of the CPU as a manager sitting in the office.

- The **source address** is a shelf. ADC1's data register ADC1_DR is a shelf that holds one item at a time.
- The **destination address** is a row of slots. The array `adc_buf[8]` in memory has 8 slots.
- The **count** is the number of items on the work order. Carry one, cross one off; what is left on the order is CNDTR.
- A **request** is the bell on the shelf. Each time the ADC finishes a conversion, the bell rings once and the porter carries one item.
- A **channel** is one of the warehouse's 7 doors, each with a work order hanging on it. Each shelf's bell is wired behind just one of the doors; hang the work order on the wrong door and nobody answers the bell.
- An **interrupt** is the porter's phone call to the manager. You can arrange one call at the halfway mark (half transfer) and another when everything is done (transfer complete).

The analogy stops here. A real "item" can be 1, 2, or 4 bytes, and the work order counts items, not bytes (section 5). The porter and the manager use the same corridor, and when both head for the same place they take turns (section 10). Hang the work order on the wrong door and the porter never hears the bell, so the count never drops by a single item (section 3).

### 1. What DMA is: hardware that moves data for the CPU

**DMA** (direct memory access) is a circuit in the chip that does nothing but move data. It can move data from a peripheral to memory, from memory to a peripheral, or from memory to memory, without the CPU executing an instruction for it (RM0008 Rev 21 section 13.1, page 274).

Take the UART from chapter 06. Sending 64 bytes out of USART1 at 115200 baud, with 10 bits per character (start bit, 8 data bits, stop bit), takes `64 × 10 / 115200 ≈ 5.56 ms` on the wire. The three ways of writing it differ on the CPU side:

| Method | What the CPU does | CPU load for 64 bytes |
| --- | --- | --- |
| Polling | Keeps asking "is the transmit register empty?" and writes the next byte when it is | All 5.56 ms go here; everything else waits |
| Interrupts | Enters an interrupt each time the transmit register empties and writes the next byte | About 64 interrupts, each doing one small job |
| DMA | Sets up the addresses and count, starts it, then goes off to do other work | One interrupt when it finishes |

Read the third column. The time on the wire is 5.56 ms in all three. DMA saves CPU time, not transfer time.

A **request** is the signal a peripheral gives DMA, meaning "I'm ready, move one". The ADC finishing a conversion and the USART's transmit register emptying both raise a request. DMA moves one item and answers with an acknowledge, and the peripheral drops its request until next time (section 13.3.1, page 276). For each item moved, DMA does three things (same section, page 277):

1. Read one item from the source address.
2. Write it to the destination address.
3. Subtract 1 from the remaining count.

```text
ADC1 conversion done ──request──▶ DMA1 channel 1: read ADC1_DR ──▶ write adc_buf[i] ──▶ count − 1
     ▲                                                                                     │
     └───────────────────── acknowledge, wait for the next conversion ◀────────────────────┘
```

### 2. One DMA1 with 7 channels

**Conclusion: the STM32F103C8T6 has only DMA1, with 7 channels. The DMA2 in the manual belongs to high-density chips and is void on this part.**

A **channel** is one of 7 independent transfer setups inside DMA1. Each channel has its own set of registers that hold its source, destination, and count. All 7 can be active at once, each looking after one transfer; when several have a request at the same time, the arbiter inside DMA decides by priority which one to serve first.

RM0008 section 13.1 says "12 channels across the two controllers, 7 on DMA1 and 5 on DMA2", and the note on Figure 49 in the same chapter says DMA2 exists only on high-density and XL-density devices (pages 274 and 276). The STM32F103C8T6 is a medium-density device, and its datasheet lists only one 7-channel DMA (DS5319 Rev 20 section 2.3.13, page 17).

| Item | On the STM32F103C8T6 | Source |
| --- | --- | --- |
| Controller | DMA1 only | DS5319 Rev 20 section 2.3.13 |
| Channels | 7: channel 1 to channel 7 | Same; RM0008 Rev 21 section 13.1 |
| Registers per channel | CCR (configuration), CNDTR (count), CPAR (peripheral address), CMAR (memory address) | RM0008 Rev 21 section 13.4 |
| Priority | 4 software levels; on a tie the lower channel number goes first | Section 13.3.2 |
| Interrupts | One vector per channel: DMA1_Channel1 to DMA1_Channel7, vector table positions 11 to 17 | Table 63 |
| Clock | Bit 0 DMA1EN of RCC_AHBENR, off after reset | Section 7.3.6 |

The first two rows answer "what is there". The other four are what you touch when you write code: the registers, the priority, the interrupt function names, and the clock switch.

When two channels have a request at the same time, DMA first compares the software priority set by the PL bits in CCR: low, medium, high, or very high. On a tie the lower channel number goes first, for example channel 2 before channel 4 (section 13.3.2, page 277).

Each channel has three event flags: **HTIF** (half transfer), **TCIF** (transfer complete), and **TEIF** (transfer error). The three flags share the channel's one interrupt vector (section 13.2, and section 13.3.6 Table 77). You read the flags in DMA_ISR and clear them by writing 1 to the matching bit of DMA_IFCR (sections 13.4.1 and 13.4.2).

### 3. The request map: which peripheral uses which channel

**Conclusion: on F1 the requests are hard-wired. ADC1 can only use channel 1, USART1_TX only channel 4, and USART1_RX only channel 5. Look it up and fill it in; there is nothing to choose.**

The **request map** is the table of which peripheral's request is wired to which channel. The table below is all of RM0008 Rev 21 Table 78 (page 282):

| Channel | Requests wired to this channel |
| --- | --- |
| Channel 1 | ADC1, TIM2_CH3, TIM4_CH1 |
| Channel 2 | SPI1_RX, USART3_TX, TIM1_CH1, TIM2_UP, TIM3_CH3 |
| Channel 3 | SPI1_TX, USART3_RX, TIM3_CH4, TIM3_UP |
| Channel 4 | SPI2_RX, USART1_TX, I2C2_TX, TIM1_CH4, TIM1_TRIG, TIM1_COM, TIM4_CH2 |
| Channel 5 | SPI2_TX, USART1_RX, I2C2_RX, TIM1_UP, TIM2_CH1, TIM4_CH3 |
| Channel 6 | USART2_RX, I2C1_TX, TIM1_CH3, TIM3_CH1, TIM3_TRIG |
| Channel 7 | USART2_TX, I2C1_RX, TIM2_CH2, TIM2_CH4, TIM4_UP |

How to use it: find the request you need, and configure the channel of that row. The manual's table says SPI2/I2S2, but this part has no I2S, which is a peripheral of high-density chips (DS5319 Rev 20 section 2.2, page 13), so the table here says only SPI2. For the ADC there is only ADC1: ADC2 cannot issue DMA requests of its own (RM0008 Rev 21 section 11.12.3).

The requests in one row are simply ORed together before they reach DMA1, and DMA cannot tell which one is asking. So the manual requires that only one request on a channel be enabled at a time (section 13.3.7, page 281). For example, SPI2_RX and USART1_TX are both on channel 4, so the two cannot use DMA at the same time.

Setting up DMA alone is not enough. The peripheral also has its own switch for issuing DMA requests, in its own register:

| Peripheral | Switch | Position |
| --- | --- | --- |
| ADC1 | DMA in ADC_CR2 | Bit 8 (section 11.12.3) |
| USART1, 2, 3 | DMAT (transmit) and DMAR (receive) in USART_CR3 | Bits 7 and 6 (section 27.6.6) |
| SPI1, 2 | TXDMAEN and RXDMAEN in SPI_CR2 | Bits 1 and 0 (section 25.5.2) |
| I2C1, 2 | DMAEN in I2C_CR2 | Bit 11 (section 26.6.2) |
| TIM1 to TIM4 | UDE (update) and CC1DE to CC4DE (capture/compare) in TIMx_DIER | Bit 8 and bits 9 to 12 (sections 14.4.4 and 15.4.4) |

You need this table when you write the registers yourself. The HAL's `HAL_ADC_Start_DMA()` and `HAL_UART_Transmit_DMA()` set these bits for you (from the STM32CubeF1 HAL source). Miss this step and the DMA channel stays enabled but never gets a request, so CNDTR never drops.

### 4. Setting up a channel in six steps

**Conclusion: fill in the four registers in the manual's order: addresses and count first, then the configuration, and set EN only in the last step.**

The order from RM0008 Rev 21 section 13.3.3 (page 278):

| Step | Where | What | ADC1 example |
| --- | --- | --- | --- |
| 1 | CPAR | Address of the peripheral register | `&ADC1->DR` |
| 2 | CMAR | Memory address | Start address of the array `adc_buf` |
| 3 | CNDTR | Number of items to move | 8 |
| 4 | PL in CCR | Priority | High |
| 5 | The rest of CCR | Direction, circular, address increment, widths, interrupts | Peripheral to memory, 16-bit, memory address increments, HT and TC on |
| 6 | EN in CCR | Enable | Set to 1 |

The first three steps are the work order's "from where, to where, how many". Steps 4 and 5 say how to carry, and step 6 starts the job. CNDTR can only be written while EN = 0 (section 13.4.4), so to change the count, turn the channel off first.

The bits for step 5 are all in CCR (section 13.4.3, page 286; its offset is `0x08 + 20 × (channel number − 1)`, where 20 is decimal):

| Bit | Name | Meaning |
| --- | --- | --- |
| 14 | MEM2MEM | 1: memory to memory |
| 13:12 | PL | Priority: 00 low, 01 medium, 10 high, 11 very high |
| 11:10 | MSIZE | Width of each item on the memory side: 00 is 8-bit, 01 is 16-bit, 10 is 32-bit |
| 9:8 | PSIZE | Width on the peripheral side, coded the same as MSIZE |
| 7 | MINC | 1: after each item the memory address advances by one width |
| 6 | PINC | 1: after each item the peripheral address advances by one width |
| 5 | CIRC | 1: circular mode |
| 4 | DIR | 0: read from the peripheral, write to memory; 1: read from memory, write to the peripheral |
| 3 | TEIE | Transfer-error interrupt enable |
| 2 | HTIE | Half-transfer interrupt enable |
| 1 | TCIE | Transfer-complete interrupt enable |
| 0 | EN | Channel enable |

In the ADC example both sides are 16-bit, MINC = 1, PINC = 0, and DIR = 0. The peripheral address stays put because ADC1_DR is always the same address. The memory address has to advance, or all 8 results land in `adc_buf[0]`. Each field of the HAL's `hdma.Init` maps to a group of bits in this table; for example, `PeriphDataAlignment` is PSIZE and `MemInc` is MINC.

### 5. CNDTR: how much is left (NDTR on F4)

**Conclusion: CNDTR holds the number of items not yet moved. It is not a byte count, and it is not an address. Items written = total − CNDTR; bytes = items written × bytes per item.**

The low 16 bits of **CNDTR** (channel number of data register) are called NDT. You write the total before starting, and it drops by 1 for each item moved (section 13.3.1). The NDTR in the video narration is the name of the same counter on F4 (DMA_SxNDTR); on F1 the register is DMA_CNDTRx. The HAL's `__HAL_DMA_GET_COUNTER()` reads it.

With a buffer of 8 half-words (2 bytes each), CNDTR reads back 3:

```text
adc_buf: 8 half-words, 16 bytes
index    [0]   [1]   [2]   [3]   [4]   [5]   [6]   [7]
state    done  done  done  done  done  empty empty empty
                                        ▲
                               next write goes here: index 5

CNDTR = 3: 3 items still to write
written = 8 − 3 = 5 samples
bytes   = 5 × 2 = 10 bytes
```

One place where the manual can lead you astray: the register description in section 13.4.4 (page 287) calls the reading "remaining bytes". Section 13.3.1 of the same chapter says CNDTR holds the number of transfers still to be performed, and in the Table 76 example NDT = 4 at 16-bit width moves 4 half-words, 8 bytes. Only counting in items makes all three places agree.

A line to remember: **what is left is in CNDTR (NDTR in the narration); items written is the total minus the reading; for bytes, multiply by the bytes per item.**

NDT is 16 bits, so the maximum is 65535 (sections 13.3.3 and 13.4.4; section 13.2 writes 65536, but the 16-bit register settles it at 65535). When CNDTR is 0, the channel moves nothing even when enabled (section 13.4.4).

### 6. Data width: the two sides may differ, but F1 does not pack

**Conclusion: when PSIZE and MSIZE differ, F1 only pads each item with zeros or cuts off the high bits. It never joins two bytes into a half-word. The array's element type must be as wide as MSIZE.**

The table below is taken from RM0008 Rev 21 Table 76 (page 279). Source data is written B1B0, B3B2, and so on; each "B plus a digit" is one byte:

| Peripheral width PSIZE | Memory width MSIZE | How each item moves | What memory holds |
| --- | --- | --- | --- |
| 16-bit | 16-bit | Moved as is | B1B0, B3B2, …, 2 bytes each |
| 16-bit | 8-bit | Only the low byte is written | B0, B2, B4, …, high bytes dropped, 1 byte each |
| 16-bit | 32-bit | High 16 bits padded with 0 | 0000B1B0, 0000B3B2, …, 4 bytes each |
| 8-bit | 16-bit | High 8 bits padded with 0 | 00B0, 00B1, …, 2 bytes each |

Read the last column: one item in, one item out. The count stays the same; what changes is how many bytes each item takes in memory. An ADC result is 12 bits in a 16-bit data register (RM0008 Rev 21 section 11.1), so both sides are 16-bit and the array is `uint16_t`. Addresses must also be aligned to the width: a 16-bit address must be a multiple of 2 and a 32-bit address a multiple of 4 (section 13.2). A `uint16_t` array is naturally aligned to 2 bytes.

Item 5 of the video narration says that stepping the address in bytes "inserts a pile of gaps" in memory. According to Table 76, MSIZE at 8 bits drops the high bytes and lays the low bytes side by side with no gaps. Read back as `uint16_t`, each element is an odd number made of two low bytes, and the second half of the array is never written at all. The gaps come from MSIZE at 32 bits: each result takes 4 bytes, and read back as `uint16_t` you get "value, 0, value, 0". Both are width mistakes, and they look different.

F4 really does pack in FIFO mode, for example joining two bytes into one half-word on the way out (RM0090 Rev 22 section 10.3.10). F1 has nothing like it.

### 7. Normal mode and circular mode

**Conclusion: normal mode stops after CNDTR items. Circular mode reloads CNDTR and the addresses when it finishes and starts over, until you turn the channel off.**

**Normal mode** (CIRC = 0): once CNDTR reaches 0, the channel no longer answers requests, even though it is still enabled. For another round, clear EN, rewrite CNDTR, and set EN (section 13.3.3, page 278). Turning a channel off does not clear CCR, CPAR, or CMAR, so the old settings remain. Use it to send one packet or read a fixed batch.

**Circular mode** (CIRC = 1): when the last item has been moved, CNDTR reloads its initial value, the internal current addresses return to the start addresses in CPAR and CMAR, and requests keep being served (same section). Use it for an ADC that samples nonstop or a UART that receives all the time.

```text
Normal:   CNDTR  8 → 7 → … → 1 → 0              stops at 0, nothing more moves
Circular: CNDTR  8 → 7 → … → 1 → 8 → 7 → …      reloads 8 right after item 8
```

In circular mode, `length − CNDTR` is the next index to write in this lap, not how much has arrived in total. When CNDTR reloads 8, it starts from 0 again. To know which part is new, you have to remember where you last got to. The `HAL_UARTEx_ReceiveToIdle_DMA()` commonly used for UART receive gives you a `Size` in its callback, the first unwritten position in this lap, and comparing it with the previous position `old_pos` tells you which part is new (ST's STM32CubeF4 circular DMA example; Appendix A section 3).

**Memory to memory** (MEM2MEM = 1): it waits for no peripheral request, starts as soon as EN is set, and stops when CNDTR reaches 0. It cannot be combined with circular mode (section 13.3.3, page 279). Because it needs no request, any of the 7 channels can do it, so pick one your project is not using.

### 8. Half-transfer and transfer complete: one half at a time

**Conclusion: circular mode plus the HT and TC interrupts is a ping-pong buffer. Handle the first half when HT arrives and the second half when TC arrives. The time each half leaves the CPU is "items in half the buffer ÷ sample rate".**

HTIF is set when half has been moved and TCIF when all of it has, and each enters the interrupt if its enable bit is on (section 13.3.3, page 278). The manual's wording is that HTIF is set once "half of the bytes" are transferred; since every item has the same width, half the bytes is half the items. In a buffer of 8 half-words, HT arrives at sample 4, byte 8, not at 4 bytes.

A **ping-pong buffer** splits one buffer into two halves used in turn: DMA writes one half while the CPU reads the other, then they swap.

```text
            ┌──── first half [0]..[3] ───┬──── second half [4]..[7] ──┐
DMA writes  │ samples 1, 2, 3, 4         │ samples 5, 6, 7, 8         │  sample 9 goes to [0] again
            └────────────────────────────┴────────────────────────────┘
                                         ▲                            ▲
                          HT: CPU handles [0]..[3]     TC: CPU handles [4]..[7]

Deadline: after HT, finish the first half before DMA gets back to [0], which is 4 samples of time
```

The deadline for each half:

```text
deadline = (N / 2) ÷ sample rate
N = 8, 1 Hz trigger:     4 ÷ 1 = 4 s (Lab 3)
N = 64, 1 kHz sampling:  32 ÷ 1000 = 32 ms
```

In the interrupt, do only the swap and the necessary calculation, and do not block. If you fall behind DMA, the next lap overwrites data you have not handled yet. The LED keeps blinking, but the data is gone.

On a transfer error (for example, an address in the reserved space), the hardware clears the channel's EN and sets TEIF (section 13.3.5, page 280). The channel has stopped: check the address, then configure it again.

In the HAL, the ADC's HT and TC arrive in `HAL_ADC_ConvHalfCpltCallback()` and `HAL_ADC_ConvCpltCallback()`. For UART receive the counterparts are `HAL_UART_RxHalfCpltCallback()` and `HAL_UART_RxCpltCallback()`. `HAL_DMA_IRQHandler()` writes IFCR to clear the flags for you (from the STM32CubeF1 HAL source).

A DMA completion interrupt only says DMA has served all its requests. It does not say the application lost no data, and it does not say where a frame begins or ends.

### 9. F4 numbering: a stream first, then a channel

**Conclusion: F4 DMA adds a layer called a stream: two controllers with 8 streams each, and each stream selects one request out of 8 channels. The same peripheral request has completely different numbers on F4 and F1, so you cannot copy them across.**

The following comes from RM0090 Rev 22 chapter 10 (from page 304):

- The two controllers have 16 streams in total, 8 each. Each stream has up to 8 channels (requests), selected by the CHSEL bits of DMA_SxCR (sections 10.1 and 10.2).
- Each stream has a FIFO 4 words deep, each word 32 bits, and can work in FIFO mode or direct mode (section 10.2).
- Only DMA2 can do memory to memory (section 10.3.6, page 313).
- Packing and unpacking between different widths exist only in FIFO mode; direct mode needs equal widths (section 10.3.10, page 316). NDT also counts items: with a half-word PSIZE, the bytes to move are 2 × NDT (same section).
- There are two more error flags than on F1: FIFO error FEIF and direct mode error DMEIF. When the FIFO threshold and the burst length do not fit, FEIF is set as soon as the stream is enabled, and the stream turns itself off (section 10.3.12, Table 49, page 320).
- Double buffer mode: with DBM = 1 the two memory addresses M0AR and M1AR are used in turn, and the CT bit shows which one DMA is writing (section 10.3.9, page 315).

The table below puts a few common requests on the two families side by side (the F4 column is from RM0090 Rev 22 Table 44, page 310):

| Request | STM32F103C8T6 | STM32F4 |
| --- | --- | --- |
| ADC1 | DMA1 channel 1 | DMA2 Stream 0 or Stream 4, Channel 0 |
| USART1_TX | DMA1 channel 4 | DMA2 Stream 7, Channel 4 |
| USART1_RX | DMA1 channel 5 | DMA2 Stream 2 or Stream 5, Channel 4 |
| SPI1_RX | DMA1 channel 2 | DMA2 Stream 0 or Stream 2, Channel 3 |
| SPI1_TX | DMA1 channel 3 | DMA2 Stream 3 or Stream 5, Channel 3 |
| TIM1_CH1 | DMA1 channel 2 | DMA2 Stream 1 or Stream 3, Channel 6; or Stream 6, Channel 0 |

Each row is one request. The left cell holds only for this F103C8, and the right cell only for F4. On F4, the table gives you the stream first, then the channel.

### 10. Bus sharing and cache coherency

**Conclusion: DMA takes no CPU instructions, but it shares the bus with the CPU. On F1 the two take turns and the CPU gets at least half of the bandwidth. F1 has no data cache, so whatever DMA writes to memory the CPU can read at once. On F7 and H7 with a D-cache, you have to make sure separately that the CPU sees the new data.**

The **bus matrix** (BusMatrix) is the arbitration circuit that decides who uses SRAM, Flash, and the peripherals first. F1's DMA is a master on the AHB bus, which means it can start reads and writes on its own, and it reaches the bus matrix over the DMA bus (RM0008 Rev 21 section 3.1). Peripheral registers sit on the two peripheral buses APB1 and APB2, and DMA reaches them through bridges. When DMA and the CPU target the same destination (the same memory or the same peripheral), a DMA request may make the CPU wait for a few bus cycles. The bus matrix arbitrates in turn and guarantees the CPU at least half of the bandwidth (section 13.3, page 276).

F1's Cortex-M3 core has no data cache. The CPU and DMA reach the same SRAM through the bus matrix, so a number DMA has just written is there for the CPU's next read.

A **cache** is a small, fast store beside the core that holds copies of part of memory. The Cortex-M7 core of F7 and H7 has an L1 cache, managed in lines of 32 bytes ([AN4839 Rev 2](#source-an4839) section 2). **Cache coherency** asks whether the copy the CPU sees and the memory DMA sees are the same. DMA writes SRAM directly while the CPU may still be reading an old copy in the cache; and new data the CPU wrote may still sit in the cache, not yet in SRAM, so DMA reads the old value. AN4839 Rev 2 section 4 gives two kinds of fix:

- Put the DMA buffer in a region the MPU (memory protection unit) marks as non-cacheable.
- Keep the buffer in a cacheable region: do a clean before DMA sends (`SCB_CleanDCache_by_Addr()`, which writes new data in the cache back to SRAM), and an invalidate after DMA receives (`SCB_InvalidateDCache_by_Addr()`, which discards the old copy in the cache). Both work on 32-byte lines, so align the buffer to 32 bytes and make its length a multiple of 32, or you write back or discard other variables in the same line.

H7 has a separate problem too: some DMA controllers cannot reach certain memory at all, for example DTCM. With the buffer in the wrong place, no amount of cache care helps ([ST community article](#source-st-h7-dma)).

## Hardware and wiring

| Part | Connect to BluePill | Note |
| --- | --- | --- |
| USB-TTL module RXD | PA9 (USART1_TX, LQFP48 pin 30) | Labs 1 and 4: set the serial terminal on the PC to 115200-8-N-1 |
| USB-TTL module TXD | PA10 (USART1_RX, pin 31) | This chapter only sends; wired for later use |
| USB-TTL module GND | GND | A common ground is required |
| Potentiometer (10 kΩ, rule of thumb) wiper | PA0 (ADC12_IN0, pin 10) | Its two ends go to 3.3 V and GND; with no potentiometer, jumper PA0 to 3.3 V |
| On-board LED | PC13 | Lights on a low level; Labs 2 and 3 watch it toggle |
| ST-Link | SWDIO, SWCLK, GND, 3.3 V on the debug header | Watch CNDTR and the array in the debugger |

Wire these once and all four labs need no rewiring.

```text
USB-TTL module            BluePill (STM32F103C8T6)
  RXD  ◀────────────────  PA9   pin 30, USART1_TX
  TXD  ────────────────▶  PA10  pin 31, USART1_RX
  GND  ─────────────────  GND

3.3 V ──┐
     [pot]── wiper ─────▶ PA0   pin 10, ADC12_IN0
GND ────┘

On-board LED: PC13, lights on low
ST-Link: SWDIO, SWCLK, GND, 3.3 V on the debug header
```

Pin numbers are from DS5319 Rev 20 Table 5 and Figure 8. Keep the voltage on PA0 between 0 and 3.3 V. On the LQFP48 package the ADC reference VREF+ is tied inside to pin 9 VDDA (Table 47 note 3), so an input above it still reads only 4095. PA0 is not a 5 V tolerant pin (the I/O level column of Table 5 has no FT for it), the absolute maximum input voltage for such a pin is 4.0 V (Table 6, page 37), and 5 V exceeds it. Set the USB-TTL module's level jumper to 3.3 V.

## Code

The two listings below are complete: `uart_dma_tx.c` goes with Labs 1 and 4, and `adc_dma.c` with Labs 2 and 3. Both call the `SystemClock_Config()` written in chapter 02: HSE 8 MHz, PLL ×9 for 72 MHz, APB1 divided by 2, APB2 undivided, the same values as the clock-tree row of Appendix D.

```c
/* uart_dma_tx.c -- USART1 sends through DMA1 channel 4; the CPU counts while it waits */
#include "stm32f1xx_hal.h"
#include <stdio.h>

#define LINE_LEN  64                     /* 64 bytes per line, including the final \r\n */

UART_HandleTypeDef huart1;
DMA_HandleTypeDef  hdma_usart1_tx;

static char msg[LINE_LEN + 1];           /* 1 extra byte for snprintf's final '\0'; DMA sends only the first 64 */
static volatile uint8_t tx_done;         /* 1: the last line has fully left PA9 */
volatile uint32_t idle_last;             /* CPU idle loops during the last line; watch it in the debugger */

void SystemClock_Config(void);           /* Chapter 02: HSE 8 MHz, PLL x9 = 72 MHz */

static void uart1_dma_init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();         /* RCC_AHBENR bit 0: DMA1EN */

    GPIO_InitTypeDef io = {0};
    io.Pin   = GPIO_PIN_9;               /* PA9 = USART1_TX, alternate-function push-pull */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);
    io.Pin   = GPIO_PIN_10;              /* PA10 = USART1_RX, floating input */
    io.Mode  = GPIO_MODE_INPUT;
    io.Pull  = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = USART1;
    huart1.Init.BaudRate     = 115200;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart1);

    hdma_usart1_tx.Instance                 = DMA1_Channel4;          /* USART1_TX is wired to channel 4 only */
    hdma_usart1_tx.Init.Direction           = DMA_MEMORY_TO_PERIPH;   /* DIR = 1: read memory, write the peripheral */
    hdma_usart1_tx.Init.PeriphInc           = DMA_PINC_DISABLE;       /* The destination is always USART1->DR */
    hdma_usart1_tx.Init.MemInc              = DMA_MINC_ENABLE;        /* The source address adds 1 each time */
    hdma_usart1_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;    /* 8 bits on both sides */
    hdma_usart1_tx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_usart1_tx.Init.Mode                = DMA_NORMAL;             /* Stop after one line */
    hdma_usart1_tx.Init.Priority            = DMA_PRIORITY_LOW;
    HAL_DMA_Init(&hdma_usart1_tx);
    __HAL_LINKDMA(&huart1, hdmatx, hdma_usart1_tx);                   /* Hang the DMA handle on the UART handle */

    HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
    HAL_NVIC_SetPriority(USART1_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
}

void DMA1_Channel4_IRQHandler(void) { HAL_DMA_IRQHandler(&hdma_usart1_tx); }
void USART1_IRQHandler(void)        { HAL_UART_IRQHandler(&huart1); }

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)   /* The USART's TC: the last bit has left PA9 */
{
    if (huart->Instance == USART1) tx_done = 1;
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    uart1_dma_init();

    for (uint32_t n = 0; ; n++)
    {
        /* Build a line of exactly 64 bytes: 5 + 6 + 7 + 8 + 2 + 34 + 2 = 64 */
        snprintf(msg, sizeof msg, "line %06lu  idle %08lu  %-34s\r\n",
                 (unsigned long)(n % 1000000), (unsigned long)idle_last, "DMA1 channel 4 -> USART1 -> PA9");

        tx_done = 0;
        HAL_UART_Transmit_DMA(&huart1, (uint8_t *)msg, LINE_LEN);   /* Returns at once; DMA moves it in the background */

        uint32_t idle = 0;
        while (!tx_done) idle++;         /* The line takes about 5.56 ms on the wire; the idle CPU counts */
        idle_last = idle;

        HAL_Delay(500);
    }
}
```

Piece by piece:

- `__HAL_RCC_DMA1_CLK_ENABLE()`: DMA1 sits on AHB, and its clock switch is bit 0 DMA1EN of RCC_AHBENR (RM0008 Rev 21 section 7.3.6). It is off after reset. Without this line, writes to the DMA registers do nothing.
- `Instance = DMA1_Channel4`: from Table 78, USART1_TX is on channel 4. Any other channel gets no request (Lab 4).
- `DMA_MEMORY_TO_PERIPH`, `DMA_PINC_DISABLE`, `DMA_MINC_ENABLE`: read from `msg` and write to USART1_DR. The peripheral address stays put and the memory address advances by 1 per byte. Both widths are bytes because the USART sends and receives one 8-bit character at a time.
- `__HAL_LINKDMA()`: hangs the DMA handle on the UART handle's `hdmatx`, so `HAL_UART_Transmit_DMA()` knows which channel to start.
- Both interrupt functions are needed. When DMA has written the last byte it enters `DMA1_Channel4_IRQHandler()`, and there the HAL turns on the USART's TC interrupt. When the last bit leaves PA9 it enters `USART1_IRQHandler()`, and there the HAL sets the UART state back to idle and calls `HAL_UART_TxCpltCallback()`. Without the second one, the first line goes out, and every later call returns `HAL_BUSY` and sends nothing. This flow comes from the STM32CubeF1 HAL source; the rule that a send is finished only when the USART's TC is set after DMA writes the last item comes from RM0008 Rev 21 section 27.3.13 (page 813).
- `msg` is a `static` global array. It has to stay valid while DMA reads it in the background. As a local array in a function, its stack space goes to other variables when the function returns, and garbage gets sent. For the same reason the main loop rewrites `msg` only after `tx_done`: until DMA has finished reading it, the buffer belongs to DMA.
- The `snprintf()` line: the line number is taken modulo 1000000, so it always has 6 digits and the whole line is always 64 bytes.
- `while (!tx_done) idle++;` is only there to show the CPU has time to spare. A real program does other work here instead of spinning.
- At 115200 baud with 10 bits per character, 64 bytes take `64 × 10 / 115200 ≈ 5.56 ms`. `idle_last` records how many loops the CPU spun in that time.

```c
/* adc_dma.c -- TIM3 triggers ADC1 once a second; DMA1 channel 1 moves the results into adc_buf[8] */
#include "stm32f1xx_hal.h"

#define LAB_CIRCULAR  0                  /* 0: Lab 2, normal mode; 1: Lab 3, circular mode */
#define ADC_BUF_LEN   8                  /* 8 half-words = 16 bytes */

ADC_HandleTypeDef hadc1;
DMA_HandleTypeDef hdma_adc1;
TIM_HandleTypeDef htim3;

volatile uint16_t adc_buf[ADC_BUF_LEN];  /* DMA writes here */
volatile uint16_t left;                  /* CNDTR as read by the main loop; watch it in the debugger */

void SystemClock_Config(void);           /* Chapter 02: 72 MHz, APB2 = 72 MHz */

static void led_init(void)
{
    __HAL_RCC_GPIOC_CLK_ENABLE();
    GPIO_InitTypeDef io = {0};
    io.Pin   = GPIO_PIN_13;              /* On-board LED, lights on low */
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &io);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET);   /* Start with it off */
}

static void adc_dma_init(void)
{
    RCC_PeriphCLKInitTypeDef clk = {0};
    clk.PeriphClockSelection = RCC_PERIPHCLK_ADC;
    clk.AdcClockSelection    = RCC_ADCPCLK2_DIV6;              /* 72 MHz / 6 = 12 MHz */
    HAL_RCCEx_PeriphCLKConfig(&clk);

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_ADC1_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();

    GPIO_InitTypeDef io = {0};
    io.Pin  = GPIO_PIN_0;                                      /* PA0 = ADC12_IN0 */
    io.Mode = GPIO_MODE_ANALOG;
    HAL_GPIO_Init(GPIOA, &io);

    hdma_adc1.Instance                 = DMA1_Channel1;        /* ADC1 is wired to channel 1 only */
    hdma_adc1.Init.Direction           = DMA_PERIPH_TO_MEMORY; /* DIR = 0: read the peripheral */
    hdma_adc1.Init.PeriphInc           = DMA_PINC_DISABLE;     /* Always read ADC1->DR */
    hdma_adc1.Init.MemInc              = DMA_MINC_ENABLE;      /* Write the next element each time */
    hdma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;  /* PSIZE = 16 bits */
    hdma_adc1.Init.MemDataAlignment    = DMA_MDATAALIGN_HALFWORD;  /* MSIZE = 16 bits, as wide as uint16_t */
#if LAB_CIRCULAR
    hdma_adc1.Init.Mode                = DMA_CIRCULAR;         /* After 8 items, start over by itself */
#else
    hdma_adc1.Init.Mode                = DMA_NORMAL;           /* Stop after 8 items */
#endif
    hdma_adc1.Init.Priority            = DMA_PRIORITY_HIGH;
    HAL_DMA_Init(&hdma_adc1);
    __HAL_LINKDMA(&hadc1, DMA_Handle, hdma_adc1);

    hadc1.Instance                   = ADC1;
    hadc1.Init.ScanConvMode          = ADC_SCAN_DISABLE;       /* Convert one channel only */
    hadc1.Init.ContinuousConvMode    = DISABLE;                /* One conversion per trigger */
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv      = ADC_EXTERNALTRIGCONV_T3_TRGO;   /* Triggered by TIM3's TRGO */
    hadc1.Init.DataAlign             = ADC_DATAALIGN_RIGHT;
    hadc1.Init.NbrOfConversion       = 1;
    HAL_ADC_Init(&hadc1);

    ADC_ChannelConfTypeDef ch = {0};
    ch.Channel      = ADC_CHANNEL_0;
    ch.Rank         = ADC_REGULAR_RANK_1;
    ch.SamplingTime = ADC_SAMPLETIME_55CYCLES_5;               /* Example setting; chapter 09 covers the choice */
    HAL_ADC_ConfigChannel(&hadc1, &ch);

    HAL_ADCEx_Calibration_Start(&hadc1);                       /* Calibrate once after power-up */

    HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);
}

static void tim3_trgo_1hz_init(void)
{
    __HAL_RCC_TIM3_CLK_ENABLE();
    htim3.Instance           = TIM3;
    htim3.Init.Prescaler     = 7199;                           /* 72 MHz / 7200 = 10 kHz */
    htim3.Init.CounterMode   = TIM_COUNTERMODE_UP;
    htim3.Init.Period        = 9999;                           /* 10 kHz / 10000 = 1 Hz */
    htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_Base_Init(&htim3);

    TIM_MasterConfigTypeDef m = {0};
    m.MasterOutputTrigger = TIM_TRGO_UPDATE;                   /* MMS = 010: one TRGO beat per update */
    m.MasterSlaveMode     = TIM_MASTERSLAVEMODE_DISABLE;
    HAL_TIMEx_MasterConfigSynchronization(&htim3, &m);
}

void DMA1_Channel1_IRQHandler(void) { HAL_DMA_IRQHandler(&hdma_adc1); }

void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *hadc)    /* HT: adc_buf[0..3] are written */
{
    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc)        /* TC: adc_buf[4..7] are written too */
{
    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    led_init();
    adc_dma_init();
    tim3_trgo_1hz_init();

    HAL_ADC_Start_DMA(&hadc1, (uint32_t *)adc_buf, ADC_BUF_LEN);  /* The length is an item count: 8 half-words */
    HAL_TIM_Base_Start(&htim3);                                   /* The first beat comes 1 s later */

    while (1)
    {
        left = (uint16_t)__HAL_DMA_GET_COUNTER(&hdma_adc1);       /* Read CNDTR: how many are left to write */
    }
}
```

Piece by piece:

- `RCC_ADCPCLK2_DIV6`: the ADC clock is APB2's 72 MHz divided by 6, giving 12 MHz, within the manual's 14 MHz limit (RM0008 Rev 21 section 11.1, page 215).
- `Instance = DMA1_Channel1`: from Table 78, ADC1 is on channel 1.
- The two `HALFWORD` settings: ADC1_DR is 16 bits and the array is `uint16_t`, so PSIZE and MSIZE are both 16-bit (section 6).
- `ExternalTrigConv = ADC_EXTERNALTRIGCONV_T3_TRGO`: this sets EXTSEL in ADC_CR2 to 100, and each TIM3 TRGO starts one conversion (RM0008 Rev 21 section 11.12.3, page 240). `ContinuousConvMode = DISABLE` keeps it to one conversion per trigger. So DMA gets one request per second and CNDTR drops by 1 per second, slow enough to watch.
- The two TIM3 numbers: `72 MHz / (7199 + 1) / (9999 + 1) = 1 Hz`; chapter 05 has the method. `TIM_TRGO_UPDATE` is MMS = 010 in TIMx_CR2, which sends one TRGO beat at each update event.
- `HAL_ADC_Start_DMA(&hadc1, (uint32_t *)adc_buf, ADC_BUF_LEN)`: the third argument is the item count 8, which goes into CNDTR, not the byte count 16. The `uint32_t *` cast is what the HAL prototype requires; the actual writes follow MSIZE, 16 bits. The function also sets the DMA and EXTTRIG bits of ADC_CR2 and turns on DMA's HT and TC interrupts (from the STM32CubeF1 HAL source).
- ADC and DMA start before TIM3, so the receiving side is ready when the first beat arrives.
- Each callback toggles PC13: at HT, `adc_buf[0]` to `adc_buf[3]` are written; at TC, `adc_buf[4]` to `adc_buf[7]` are too. A real program handles the matching half here.
- `volatile` on `adc_buf`: this tells the compiler that DMA changes this memory behind the program's back, so it must read it again each time instead of reusing an old value from a register. The main loop here only reads CNDTR.

The same job in registers, laying out what the HAL does for you (bit names from RM0008 Rev 21 section 13.4). This covers only the DMA part, set up in circular mode with HT and TC on, matching Lab 3. The ADC and TIM3 setup is the same as above:

```c
static void adc_dma_regs_init(void)
{
    RCC->AHBENR |= RCC_AHBENR_DMA1EN;                    /* DMA1's clock */

    DMA1_Channel1->CCR   = 0;                            /* Make sure EN = 0: CNDTR cannot be written while EN is 1 */
    DMA1_Channel1->CPAR  = (uint32_t)&ADC1->DR;          /* Step 1: peripheral address, ADC1's data register */
    DMA1_Channel1->CMAR  = (uint32_t)adc_buf;            /* Step 2: memory address, start of the array */
    DMA1_Channel1->CNDTR = 8;                            /* Step 3: item count, not bytes */
    DMA1_Channel1->CCR   = DMA_CCR_PL_1                  /* Step 4: PL = 10, high priority */
                         | DMA_CCR_MSIZE_0               /* Step 5: MSIZE = 01, memory 16 bits */
                         | DMA_CCR_PSIZE_0               /*         PSIZE = 01, peripheral 16 bits */
                         | DMA_CCR_MINC                  /*         memory address increments; PINC = 0, DIR = 0 */
                         | DMA_CCR_CIRC                  /*         circular mode */
                         | DMA_CCR_HTIE | DMA_CCR_TCIE;  /*         half-transfer and transfer-complete interrupts */
    NVIC_EnableIRQ(DMA1_Channel1_IRQn);                  /* The interrupt has to reach the CPU */
    DMA1_Channel1->CCR  |= DMA_CCR_EN;                   /* Step 6: enable last */

    ADC1->CR2 |= ADC_CR2_DMA;                            /* Peripheral side: ADC1 raises a request after each conversion */
}

void DMA1_Channel1_IRQHandler(void)
{
    if (DMA1->ISR & DMA_ISR_HTIF1) {                 /* The first half is written */
        DMA1->IFCR = DMA_IFCR_CHTIF1;                /* Write 1 to clear the flag */
        /* Handle adc_buf[0..3] */
    }
    if (DMA1->ISR & DMA_ISR_TCIF1) {                 /* The second half is written */
        DMA1->IFCR = DMA_IFCR_CTCIF1;
        /* Handle adc_buf[4..7] */
    }
}
```

- `CCR = 0` comes first: CNDTR cannot be written while EN is 1, so make sure the channel is off.
- CCR is written twice: the configuration first and then EN on its own, matching step 6 of section 13.3.3.
- `ADC1->CR2 |= ADC_CR2_DMA` is the peripheral-side switch (the table in section 3). Without it the channel is on but never gets a request.
- The interrupt function checks which flag is set, then writes 1 to IFCR to clear it; reading ISR does not clear a flag (section 13.4.2). If the flag is not cleared, the interrupt fires again the moment it exits.

Memory to memory needs no peripheral request. The code below moves 16 words from `src` to `dst`. Channel 3 is an example setting; no other example in this chapter uses it:

```c
static uint32_t src[16], dst[16];

void dma_copy_words(void)
{
    RCC->AHBENR |= RCC_AHBENR_DMA1EN;
    DMA1_Channel3->CCR   = 0;
    DMA1_Channel3->CPAR  = (uint32_t)src;             /* With MEM2MEM the "peripheral" side is the source */
    DMA1_Channel3->CMAR  = (uint32_t)dst;
    DMA1_Channel3->CNDTR = 16;                        /* 16 words, 64 bytes */
    DMA1_Channel3->CCR   = DMA_CCR_MEM2MEM
                         | DMA_CCR_MSIZE_1 | DMA_CCR_PSIZE_1   /* 32 bits on both sides */
                         | DMA_CCR_MINC | DMA_CCR_PINC;        /* Both addresses must advance */
    DMA1_Channel3->CCR  |= DMA_CCR_EN;                /* Moving starts as soon as EN is set */
    while (!(DMA1->ISR & DMA_ISR_TCIF3)) { }          /* Wait until it is done */
    DMA1->IFCR = DMA_IFCR_CTCIF3;
    DMA1_Channel3->CCR = 0;                           /* Turn it off when done */
}
```

- With MEM2MEM, DIR = 0: the CPAR side is the source and the CMAR side the destination. Both addresses must advance, so PINC and MINC are both set.
- PL stays at 00, the lowest (example setting). Memory to memory moves items back to back once started, so a low priority lets peripheral channels' requests go first.
- It starts as soon as EN is set and stops when CNDTR reaches 0. CIRC cannot be set with it (section 13.3.3).

The full project is in [`examples/adc-dma/`](../../examples/adc-dma/): ADC1 scans three channels in continuous mode, with DMA1 channel 1 moving the results in circular mode. An example of receiving variable-length UART data through DMA is in [`examples/uart-dma-idle/`](../../examples/uart-dma-idle/), with USART1_RX on DMA1 channel 5.

## Hands-on labs

1. **Lab 1: UART DMA send, with the CPU counting while it waits.** Build and flash `uart_dma_tx.c`, open a serial terminal on the PC, and set it to 115200-8-N-1.
   - Expected: about every half second a line appears, like `line 000001  idle 000xxxxx  DMA1 channel 4 -> USART1 -> PA9`, 64 bytes each. The idle value on the first line is 0 because nothing has been measured yet. From the second line on it is a number in the tens of thousands (rule of thumb; it varies with the compiler's optimization level).
   - How to check: with a logic analyzer on PA9, measure one line from the first start bit to the last stop bit. It is about 5.56 ms, which matches `64 × 10 / 115200`. A nonzero idle means the CPU kept running its own code during those 5.56 ms; with the blocking `HAL_UART_Transmit()`, the 5.56 ms are all spent inside the function.
   - If it fails, check first: for nothing on the terminal, check that PA9 goes to the module's RXD, that the grounds are common, and the baud rate; then check that `Instance` is `DMA1_Channel4` and that `__HAL_RCC_DMA1_CLK_ENABLE()` is there. If only the first line appears, check the spelling of `USART1_IRQHandler` and `DMA1_Channel4_IRQHandler` and their `HAL_NVIC_EnableIRQ()` calls. For garbage on the terminal, check that `SystemClock_Config()` runs before `HAL_UART_Init()`.
2. **Lab 2: normal mode, watching CNDTR step down.** Keep `LAB_CIRCULAR` at 0, build and flash `adc_dma.c`, and connect PA0 to 3.3 V or the potentiometer. Watch `left` and `adc_buf` live in the debugger; if it has no live view, pause every second or two.
   - Expected: `left` starts at 8 and drops by 1 each second. `adc_buf` fills with readings from index 0 up, close to 4095 with PA0 at 3.3 V. PC13 turns on at 4 s (HT) and off at 8 s (TC). After that `left` stays at 0 and `adc_buf` no longer changes.
   - How to check: pause when `left` is 3. `adc_buf[0]` to `adc_buf[4]` hold readings and `adc_buf[5]` to `adc_buf[7]` are still 0: `8 − 3 = 5` samples written. Open a memory view at `adc_buf`: the first 10 bytes hold data and the last 6 are 00. 4095 is 0x0FFF, stored little-endian with the low byte first, so the memory view shows FF 0F (RM0008 Rev 21 section 3.2).
   - If it fails, check first: if `left` stays at 8, check that `HAL_TIM_Base_Start()` is called, that `MasterOutputTrigger` is `TIM_TRGO_UPDATE`, and that `ExternalTrigConv` is `ADC_EXTERNALTRIGCONV_T3_TRGO`; then check that `Instance` is `DMA1_Channel1`. If `left` jumps straight to 0 at the first second, `ContinuousConvMode` is set to `ENABLE`. If `left` stays at 7, the trigger is set to software start and only one conversion ran. If `left` moves but PC13 does not, check the spelling of `DMA1_Channel1_IRQHandler` and `HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn)`.
3. **Lab 3: circular mode, with HT and TC taking turns.** Change `LAB_CIRCULAR` to 1, then rebuild and flash.
   - Expected: PC13 toggles every 4 s and keeps going. `left` cycles from 8 down to 1 and reloads 8 the moment item 8 is written. `adc_buf` is overwritten lap after lap with new readings.
   - How to check: time PC13: 4 s on, 4 s off, which matches `(8 / 2) ÷ 1 Hz = 4 s`. Turn the potentiometer and new readings appear in `adc_buf` within seconds. The write position goes 0, 1, …, 7, 0, and the next index to write is always `8 − left`.
   - If it fails, check first: if PC13 toggles twice and stops, `Mode` is still `DMA_NORMAL`; make sure you rebuilt after changing `LAB_CIRCULAR`. If the interval is not 4 s, recompute `(ADC_BUF_LEN / 2) ÷ trigger rate`; if the trigger rate is wrong, go back to chapter 05 and check PSC and ARR.
4. **Lab 4: the wrong door on purpose.** In `uart_dma_tx.c`, change `hdma_usart1_tx.Instance` to `DMA1_Channel5`, leave the interrupt functions alone, and flash again.
   - Expected: nothing reaches the terminal. The program sits in `while (!tx_done)`, and `idle` keeps climbing.
   - How to check: pause and look at DMA1 channel 5 in the debugger's register view. Its CNDTR stays at 64, its EN is 1, and DMAT in USART1_CR3 is 1 too. The channel and the request are both on, but USART1_TX's request is wired to channel 4, so channel 5 never sees it (Table 78).
   - If it fails, check first: in this lab, success means nothing gets sent. If text still appears, the change was not flashed; rebuild and flash. Afterwards change `Instance` back to `DMA1_Channel4`.

## Self-test

1. A buffer of 16 half-words, normal mode, CNDTR reads back 6. How many samples and bytes have been written? Which index does the next value go to?
2. A project wants DMA for SPI2 receive and also for USART1 transmit. Can both run at once on the STM32F103C8T6?
3. An ADC samples at 1 kHz in circular mode with a buffer of 64 half-words. After HT arrives, at most how much time does the CPU have to handle the first half?
4. The ADC's PSIZE is 16-bit, MSIZE is set to 32-bit by mistake, the array is still `uint16_t adc_buf[8]`, and CNDTR is 4. What shows up in the array? What if CNDTR is 8?
5. Following an F4 example, you set up USART1_RX on a C8 as DMA2 Stream 5, Channel 4. What happens, and what should you change?

Answers:

1. `16 − 6 = 10` samples, `10 × 2 = 20` bytes. The next value goes to index 10, counting from 0.
2. No. In Table 78, SPI2_RX and USART1_TX are both on channel 4, and requests on one channel are ORed before they reach DMA1, so only one may be enabled at a time (RM0008 Rev 21 section 13.3.7). Use DMA for one and an interrupt or polling for the other, or use SPI1 instead, whose SPI1_RX is on channel 2.
3. Half is 32 samples, `32 ÷ 1000 = 32 ms`. Past 32 ms, DMA has started overwriting the first half.
4. Each result is written as 32 bits with the high 16 bits padded with 0, and the address advances by 4 (Table 76). The 4 results take 16 bytes and exactly fill `adc_buf[0]` to `adc_buf[7]`. Little-endian puts the low half-word first, so you see "result 1, 0, result 2, 0, …" alternating. With MSIZE at 32 bits, CMAR must also be a multiple of 4 (section 13.2), which a `uint16_t` array does not guarantee. With CNDTR at 8, DMA writes 32 bytes, running 16 bytes past the end of the array and trampling whatever comes next.
5. It fails at compile time: the F1 headers have no DMA2 streams, and the F1 HAL's `DMA_InitTypeDef` has no Channel field. Stream plus Channel numbering belongs to F4 (RM0090 Rev 22 Table 44). Even if you bypassed the compiler and wrote the addresses directly, the C8 has no DMA2 (DS5319 Rev 20 section 2.3.13 lists only one 7-channel DMA), so no counter would move. Change it to DMA1 channel 5 (Table 78).

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

**Part number.** The DMA conclusions in this chapter are pinned to order code STM32F103C8T6. It is a medium-density device with a single DMA1, 7 channels, and no DMA2. The sentence in RM0008 section 13.1, "12 channels across the two controllers, 5 of them on DMA2", belongs to high-density and XL-density chips and is void on the STM32F103C8T6. Sources: [DS5319 Rev 20 section 2.3.13](#source-ds5319-dma) (page 17), and RM0008 Rev 21 section 13.1 and the note on Figure 49 (pages 274 and 276). The channel numbers and the half-word arithmetic are the same as the DMA channel row of Appendix D.

**The three requests.** ADC1 = DMA1 channel 1, USART1_TX = DMA1 channel 4, USART1_RX = DMA1 channel 5, from Table 78 of [RM0008 Rev 21 chapter 13](#source-rm0008-dma) (page 282). Requests on one channel are ORed before they reach DMA1, and only one may be enabled at a time (section 13.3.7). The SPI2/I2S2 of Table 78 is just SPI2 on this part: I2S is a peripheral of high-density chips ([DS5319 Rev 20](#source-ds5319) section 2.2).

**The CNDTR arithmetic.** CNDTR counts data items, not bytes. With a buffer of 8 half-words and CNDTR reading 3, `8 − 3 = 5` samples have been written, and the byte count is `5 × 2 = 10`. Half-transfer is at 4 samples, which is 8 bytes, not 4 bytes. The evidence is section 13.3.1 (CNDTR holds the number of transfers still to be performed) and Table 76 (NDT = 4 at 16-bit width moves 4 half-words). Section 13.4.4 (page 287) calls the reading "remaining bytes"; read it as "remaining items", in line with the other two. The NDT maximum is 65535 (sections 13.3.3 and 13.4.4). The 65536 in section 13.2 does not fit a 16-bit register, so use 65535.

**Circular mode.** With CIRC = 1, when the last item has been moved, CNDTR reloads its initial value and the internal addresses return to the starting values in CPAR and CMAR (section 13.3.3, page 278). So `length − CNDTR` is only an index within this lap, not cumulative progress. For UART receive positions use `Size` from the callback and the previous `old_pos`, the same arithmetic as Appendix A section 3 ([STM32CubeF4 example](#source-stm32cube-f4)).

**Width.** When the two sides differ, F1 only pads with zeros or cuts off the high bits; it does not pack (Table 76, page 279). F4 packs only in FIFO mode, and that belongs to another manual (RM0090 Rev 22 section 10.3.10).

**The bus.** DMA1 is a master on AHB and reaches SRAM, Flash, and peripherals through the bus matrix; peripheral registers sit on APB1 and APB2 ([RM0008](#source-rm0008) section 3.1). When DMA and the CPU target the same destination they take turns, and the CPU gets at least half of the bandwidth (section 13.3, page 276). F1 has no data cache. H7 cache maintenance is covered only in section 10 of Core ideas, and the conclusions in this section do not involve it.

**F4 is another manual.** RM0090 Rev 22 chapter 10 (from page 304): 8 streams per controller; USART1_RX is on DMA2 Stream 5 (Stream 2 also works), Channel 4; each stream's FIFO is 4 32-bit words. See [RM0090](#source-rm0090). Write these numbers on a C8 and the counter does not move.

**The pins.** USART1_TX is still chapter 06's pin 30 PA9, and USART1_RX is pin 31 PA10 ([DS5319 Rev 20](#source-ds5319-usart) Table 5). The lab's PA0 is pin 10 ADC12_IN0, and pin 9 VDDA is the ADC reference ([DS5319 Rev 20](#source-ds5319-adc) Figure 8). ADC sampling time stays in chapter 09.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-10-dma-cndtr.svg" width="760" alt="Eight half-words with CNDTR at 3 means 5 samples and 10 bytes written; treating the remaining count as bytes cuts the buffer wrong">
  <br><sub>▲ Drawn for this book. STM32F103C8T6 has only DMA1. The figure draws USART1_TX's channel 4 together with a buffer of 8 half-words: with CNDTR = 3, 5 samples and 10 bytes have been written, and half-transfer is at sample 4, 8 bytes. The failure path treats that same reading as bytes. TX still leaves on pin 30 PA9. DMA2 Stream 5 has no counter on this C8. Sources: [RM0008 Rev 21 chapter 13](#source-rm0008-dma) and [DS5319 Rev 20 section 2.3.13](#source-ds5319-dma).</sub>
</p>

**How to read this figure.** The figure has three parts. The normal path: the first 5 of 8 slots are written, CNDTR = 3, and 10 bytes have been written; the tick beside slot 4 is half-transfer, 8 bytes. The failure path: "3 left" is taken as 3 bytes, so 5 bytes seem written, and the half-word array is cut after byte 5, right in the middle of sample 3. The side notes: ADC1 = channel 1 and USART1_RX = channel 5; memory to memory on channel 1 would fight ADC1 for the same channel. The figure pairs USART1_TX with half-word width only to show the counting rule. A real UART sends one character at a time, so the width is a byte (`uart_dma_tx.c` under Code). The counting rule stays the same: CNDTR counts items. The half-word labs in this chapter use ADC1 on channel 1 (Labs 2 and 3).

<p align="center">
  <img src="../../assets/gif/dma-cndtr.gif" width="640" alt="In an 8-half-word buffer CNDTR falls to 3: 5 samples and 10 bytes written">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the normal path: CNDTR falls to 3, marked as 5 samples and 10 bytes. Print uses the static figure. Treating the remaining count as bytes is not on this GIF.</sub>
</p>

The `dma-circular.svg` at the top of the chapter is an animation: ADC1 CH0 (PA0) goes through DMA1 channel 1 into `buf[8]` in circular mode, half-word, MINC = 1, the same setup as Lab 3. Two of its lines should be read through this chapter. 总线空闲时 DMA 自动抢占一个周期 ("DMA grabs a cycle automatically when the bus is idle") is inaccurate: DMA does not wait for an idle bus, and when it competes with the CPU for the same destination the bus matrix arbitrates in turn (section 10 of Core ideas). 缓冲区要 4 字节对齐 ("the buffer must be 4-byte aligned") is stricter than the manual: a half-word buffer only needs 2-byte alignment (RM0008 Rev 21 section 13.2). `dma-ring.gif` is only linked under Related resources.

## Timing and state

The table below splits Labs 2 and 3 by TIM3 trigger (8 half-words, one trigger per second). Every row can be recomputed with the rules in [RM0008 Rev 21 chapter 13](#source-rm0008-dma): items written = 8 − CNDTR, bytes = items written × 2.

| Trigger | Time | CNDTR | Samples written | Bytes written | Event |
| --- | --- | --- | --- | --- | --- |
| After start | 0 s | 8 | 0 | 0 | Waiting for the first trigger |
| 1 | 1 s | 7 | 1 | 2 | — |
| 4 | 4 s | 4 | 4 | 8 | HT: first half written, PC13 on. Not 4 bytes |
| 5 | 5 s | 3 | 5 | 10 | The figure's normal path; the next write is index 5 |
| 8 | 8 s | 0 | 8 | 16 | TC: PC13 off. Normal mode ends here |
| 8, circular | 8 s | 8 (reloaded) | 0 this lap | 0 this lap | Hardware reloads after TC; the next trigger writes `adc_buf[0]` again |
| 9, circular | 9 s | 7 | 1 this lap | 2 this lap | `8 − CNDTR` is this lap's index, not a running total |
| 12, circular | 12 s | 4 | 4 this lap | 8 this lap | HT again, PC13 on |

Two ways to work out the same reading:

| CNDTR | Arithmetic | Result |
| --- | --- | --- |
| 3, as items | `(8 − 3) × 2` | 5 samples, 10 bytes |
| 3, as bytes | `8 − 3` | 5 bytes seem written; the cut falls in the middle of sample 3 |

The two "completes" of a UART DMA send (Lab 1, 64 bytes):

| When | What happens | Flag |
| --- | --- | --- |
| `HAL_UART_Transmit_DMA()` is called | DMA1 channel 4 starts, CNDTR = 64 | — |
| Each TXE (transmit register empty) | DMA writes one byte to USART1_DR, CNDTR drops by 1 | — |
| CNDTR reaches 0 | Byte 64 has just been written to USART1_DR; byte 63 is still shifting out | DMA's TCIF4 |
| About two character times later | The last stop bit leaves PA9 (pin 30) | USART's TC |

Arithmetic: `64 × 10 / 115200 ≈ 5.56 ms`; one character is `10 / 115200 ≈ 86.8 µs`, two are about 0.17 ms. The order of the last two rows comes from RM0008 Rev 21 section 27.3.13 and Figure 297 (page 813); the 0.17 ms is worked out from that timing figure.

## Pitfalls and sources

The last column states only what the source can prove. The HAL's internal flow comes from the STM32CubeF1 source, not from these sources.

| What you see | Why | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| The second half of a half-word array looks like new data | Half-transfer was taken as 4 bytes | Treat half-transfer as 4 samples, 8 bytes | [RM0008 chapter 13](#source-rm0008-dma) | CNDTR counts data items. 5 of 8 half-words written is 10 bytes. Half-transfer is not 4 bytes |
| CNDTR reads 3 and the bytes do not add up | The remaining count was taken as bytes | Work out the items first, `8 − 3 = 5`, then multiply by 2 for 10 | [RM0008 chapter 13](#source-rm0008-dma) | 3 half-words left is not 3 bytes left |
| DMA2 Stream 5 is set up and nothing moves on the C8 | This part has no DMA2 | Use DMA1 channel 5 for USART1_RX | [DS5319 section 2.3.13](#source-ds5319-dma) | This medium-density part has a single 7-channel DMA1. DMA2 is void on the C8 |
| Numbers copied from an F4 example, and the board does nothing | F4 stream numbers were written on a C8 | Leave the F4 numbers on F4 | [RM0090](#source-rm0090) | On F4, USART1_RX is DMA2 Stream 5, Channel 4, and the FIFO is 4 32-bit words. This does not prove the C8 has DMA2 |
| Progress drifts in circular mode | `length − CNDTR` was used as a running total | Track progress with the callback's `Size` and `old_pos` | [RM0008 chapter 13](#source-rm0008-dma) | The count reloads in hardware after reaching zero |
| CNDTR stays at its initial 8 or 64 | The request never reaches this channel: wrong channel, or the peripheral's DMA bit is off | Fix the channel from Table 78; check the DMA bit of ADC_CR2 or DMAT of USART_CR3 | [RM0008 section 13.3.7](#source-rm0008) | Requests on a channel are ORed; each peripheral enables its request with the DMA bit in its own register |
| UART DMA sends only the first line | No `USART1_IRQHandler`, so the HAL never sees the USART's TC and stays busy | Add the interrupt function and enable USART1_IRQn | [RM0008 section 27.3.13](#source-rm0008) | After DMA writes the last byte, transmission is finished only when the USART's TC is set |
| A channel stops by itself, EN back to 0 | Transfer error: an address in the reserved space | Check the addresses in CPAR and CMAR, then configure it again | [RM0008 section 13.3.5](#source-rm0008) | On an error the hardware clears EN and sets TEIF |
| A `uint16_t` array shows "value, 0, value, 0" | MSIZE was set to 32 bits | Make MSIZE as wide as the array element | [RM0008 Table 76](#source-rm0008) | 16-bit to 32-bit pads the high 16 bits with 0, and the address advances by 4 |
| Writing CNDTR has no effect | The channel is still enabled | Clear EN, write CNDTR, then set EN | [RM0008 section 13.4.4](#source-rm0008) | CNDTR can only be written while EN = 0 |

## Related resources

- RM0008, *STM32F10xxx Reference Manual*, Chapter 13, DMA controller (including request-map tables 78 and 79).
- RM0090, *STM32F4 Reference Manual*, Chapter 9, DMA controller (stream / channel, FIFO, double buffer).
- Application note AN4031, *Using the STM32F2/F4 DMA controller*.
- Related chapters in this repo: [Chapter 09](09-adc-dac.md) ADC + DMA, and [Chapter 17](17-debug.md) DWT timing.
- Figures: `../../assets/animations/dma-circular.svg`, `../../assets/gif/dma-ring.gif` (both drawn by the author or program-generated).
