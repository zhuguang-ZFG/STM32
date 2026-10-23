# 26 STM32F10x Standard Peripheral Library (SPL)

> 中文：[26 STM32F10x 标准外设库（SPL）](../26-STM32F10x标准外设库SPL.md)

> SPL is not another spelling of HAL. It is an independent driver system from the STM32F1 era: no handles, no CubeMX generation flow, and no automatic timeout, state-machine, or callback management.

<!-- video:ch26 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch26-spl.png">
    <source src="../../assets/video/ch26-spl.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chinese voice-over, 2.9 min. Voice: Microsoft Edge neural voice zh-CN-XiaoxiaoNeural via edge-tts (library mostly LGPLv3; the voice model is an online Microsoft service, not an open model). Pictures are generated from this repo's SVGs, not photographs. Video: <a href="../../assets/video/ch26-spl.mp4">MP4</a> · subtitles: <a href="../../assets/video/ch26-spl.srt">SRT</a>. Rebuild with <code>python3 tools/gen_narrated.py --speak</code>.</sub>
</p>

**Narration script (Chinese, same text as the subtitles)**

1. 本章只认 STM32F10x SPL V3.5.0。F103C8、CB 使用中容量设备宏，启动文件和链接脚本也要匹配。只复制 main，工程不会一致。
2. SPL 工程至少包含 CMSIS、设备头、驱动、启动文件、SystemInit 和应用。缺 SystemInit，时钟假设不成立；缺启动文件，向量表和初始栈没有入口。
3. USE_STDPERIPH_DRIVER 载入标准库配置，STM32F10X_MD 选择中容量设备。两者必须进入真实编译命令，写在 IDE 截图里不会影响预处理。
4. 这一帧是仓库画的启动路径。复位后取栈顶，进入 Reset Handler，搬数据并清 BSS，调用 SystemInit，再到 main。SPL 不改变 Cortex-M 启动链。
5. SPL 常见顺序是先用 RCC 打开外设和 GPIO 时钟，再填初始化结构体，最后使能外设。时钟没开时，后面的寄存器写入不会形成你期待的硬件状态。这个规则和 HAL 工程完全相同。
6. USART SendData 只把一个数据写进数据寄存器。它不帮你发送整个缓冲，也不替你定义 TXE、TC 和超时。任何轮询等待都要有单调时钟截止点，超时后把原因交给上层策略。
7. 中断不来时按三张表排查：启动文件里的向量名字是否匹配，NVIC 是否使能且优先级合法，外设状态位和中断使能位是否同时成立。不要先把所有优先级都改成零。
8. SPL 和 HAL 会写同一组寄存器，却各自维护状态。双重初始化会覆盖波特率、DMA 和中断。迁移时一次只换一个外设，用同一波形对照。
9. 仓库示例在固定的 GNU Arm 工具链和冻结源码上编译。编译通过只证明接口和链接闭合；还要从 map 文件核对存储边界，再在真板上观察引脚、时钟和故障路径。
10. 合上书，三问。USE STDPERIPH DRIVER 和 STM32F10X MD 各管什么？USART SendData 到底保证什么？同一个串口为什么不能先用 SPL 初始化、再让 HAL 接管？
<!-- /video:ch26 -->
## 📌 Goals

- [ ] State the scope, directory layout, and two critical build macros of SPL V3.5.0.
- [ ] Recognize the common `RCC_*ClockCmd → *_StructInit → *_Init → *_Cmd` initialization sequence.
- [ ] Map the HAL entry points for GPIO, EXTI, timers, USART, I2C, SPI, ADC, DMA, Flash, and CAN to SPL V3.5.0.
- [ ] Understand that SPL has no HAL callback dispatcher: the IRQ handler must inspect and clear the real source.
- [ ] Decide whether an old SPL project should be maintained, migrated one peripheral at a time, or rebuilt on HAL/LL.

## 🧭 1. Freeze the version and boundary first

This chapter covers **STM32F10x Standard Peripheral Library V3.5.0 only**. ST's official product entry is **STSW-STM32054**. API names and layout were checked against the V3.5.0 source. The source mirror is frozen at commit `afa743577f2784e95be2d5003380fdb84a702519` for stable file locations; it is **not a new normative source**. Register behavior still comes from RM0008 and the exact device datasheet.

| Question | Boundary used here |
| --- | --- |
| Which parts does this SPL cover? | STM32F10x only. Do not copy `stm32f10x_*` files into G0, L4, or H7 projects |
| Should a new project start on SPL? | Usually no. Current families and CubeMX workflows use HAL/LL; SPL matters for reading, maintaining, and migrating old F1 code |
| Is SPL the same as CMSIS? | No. CMSIS supplies core and device register definitions; SPL builds peripheral structures and functions on top |
| Is SPL always “lower level” than HAL? | It is usually thinner, but still a function layer. Performance requires generated-code inspection and measurement |
| Can HAL and SPL own the same peripheral? | Both write the same registers, but their state assumptions are independent. Give each peripheral one owner |

The useful model has four layers:

1. `stm32f10x.h`: device selection, register addresses, and bit definitions.
2. Headers such as `stm32f10x_gpio.h`: structures, constants, and declarations.
3. Sources such as `stm32f10x_gpio.c`: structure fields translated into register writes.
4. Your project: clocks, pins, call order, interrupts, deadlines, and the product state machine.

## 🗂️ 2. Project skeleton

A missing source file can leave you with a declaration that compiles but no implementation to link:

```text
Libraries/
├── CMSIS/                              core, device, startup and system files
└── STM32F10x_StdPeriph_Driver/
    ├── inc/                            stm32f10x_gpio.h, usart.h, dma.h …
    └── src/                            matching .c driver files
Project/
├── STM32F10x_StdPeriph_Template/
│   ├── main.c
│   ├── stm32f10x_conf.h
│   ├── stm32f10x_it.c / .h
│   └── system_stm32f10x.c
└── STM32F10x_StdPeriph_Examples/       official examples grouped by peripheral
```

### Two macros that must be visible in the real compiler command

| Macro | Purpose | Typical failure when wrong |
| --- | --- | --- |
| `STM32F10X_MD` | Selects medium-density definitions for devices such as F103C8/CB | Interrupts, capabilities, startup object, or memory layout do not match the part |
| `USE_STDPERIPH_DRIVER` | Makes `stm32f10x.h` include `stm32f10x_conf.h` | `GPIO_InitTypeDef`, `RCC_APB2PeriphClockCmd`, and similar declarations disappear |

Do not keep `STM32F10X_MD` merely because a Blue Pill tutorial used it. Also verify:

- include paths contain CMSIS, the device headers, and `StdPeriph_Driver/inc`;
- required `StdPeriph_Driver/src/*.c` files are actually compiled;
- `stm32f10x_conf.h` includes the needed driver headers;
- startup file, linker script, density macro, and target part belong to the same memory class;
- the crystal assumption in `system_stm32f10x.c` matches the board.

### `assert_param` is not product error handling

With `USE_FULL_ASSERT`, invalid SPL arguments enter `assert_failed()` during development. Release builds normally remove those checks. They do not replace runtime handling for communication timeouts, missing sensors, DMA errors, or failed Flash programming.

## 🔁 3. The common model: clock, defaults, configuration, enable

```c
RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

GPIO_InitTypeDef io;
GPIO_StructInit(&io);                 /* obtain library-defined defaults */
io.GPIO_Pin   = GPIO_Pin_9;
io.GPIO_Mode  = GPIO_Mode_AF_PP;
io.GPIO_Speed = GPIO_Speed_50MHz;
GPIO_Init(GPIOA, &io);
```

The four boundaries are:

1. **Clock**: without it, peripheral writes do not establish the expected hardware state.
2. **Defaults**: an uninitialized local structure contains indeterminate fields.
3. **Overrides**: every selected field must match wiring, clocks, and protocol.
4. **Enable**: calls such as `USART_Cmd`, `SPI_Cmd`, `TIM_Cmd`, and `DMA_Cmd` normally come after configuration.

Not every peripheral has the same function names. Check the V3.5.0 header and RM0008 rather than inventing a missing `*_Cmd` because another peripheral has one.

## 💡 4. A buildable SPL blink loop

The example targets the common STM32F103C8 Blue Pill. PC13 is active low. The build defines `STM32F10X_MD` and `USE_STDPERIPH_DRIVER`; `stm32f10x_conf.h` includes at least RCC and GPIO. The V3.5.0 template already contains a non-weak empty `SysTick_Handler` in `stm32f10x_it.c`; **replace it rather than adding a duplicate handler in `main.c`**.

```c
#include "stm32f10x.h"

/* main.c: the time-base state has one definition. */
volatile uint32_t g_ms;

/* stm32f10x_it.c: replace the template implementation. */
extern volatile uint32_t g_ms;
void SysTick_Handler(void)
{
    g_ms++;
}

static void delay_ms(uint32_t delay)
{
    uint32_t start = g_ms;
    while ((uint32_t)(g_ms - start) < delay) {
        /* Product code may use an event or RTOS delay. */
    }
}

static void led_init(void)
{
    GPIO_InitTypeDef io;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    GPIO_StructInit(&io);
    io.GPIO_Pin   = GPIO_Pin_13;
    io.GPIO_Mode  = GPIO_Mode_Out_PP;
    io.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOC, &io);
    GPIO_SetBits(GPIOC, GPIO_Pin_13);       /* active low: start off */
}

int main(void)
{
    SystemCoreClockUpdate();
    if (SysTick_Config(SystemCoreClock / 1000U) != 0U) {
        while (1) { /* time-base setup failed */ }
    }

    led_init();
    while (1) {
        GPIO_ResetBits(GPIOC, GPIO_Pin_13);
        delay_ms(500);
        GPIO_SetBits(GPIOC, GPIO_Pin_13);
        delay_ms(500);
    }
}
```

The reproducible project is [`examples/spl-f1-blink/`](../../examples/spl-f1-blink/). It builds against the frozen source and shares one CMake truth across command line, CLion, and VS Code. The mirror stores `core_cm3.h` as `core_cm3.h.old`; the build only copies it when the proper filename is missing. With GNU Arm 10.3.1, the verified ELF had text 1976 B, data 20 B, bss 1028 B, and one `SysTick_Handler`. Those are build observations, not a hardware claim. Hardware acceptance still requires roughly 1 Hz on the LED and a `SystemCoreClock` that matches the actual clock.

## 🧩 5. HAL, SPL, and the final register boundary

This is not a mechanical replacement table. HAL often maintains handles and state; SPL usually writes peripheral registers directly.

| Goal | Typical HAL entry | SPL V3.5.0 | Hardware boundary |
| --- | --- | --- | --- |
| GPIO clock | `__HAL_RCC_GPIOA_CLK_ENABLE()` | `RCC_APB2PeriphClockCmd(...)` | `RCC_APB2ENR` |
| GPIO configuration | `HAL_GPIO_Init()` | `GPIO_Init()` | `GPIOx_CRL/CRH` |
| GPIO output | `HAL_GPIO_WritePin()` | `GPIO_SetBits/ResetBits/WriteBit` | `GPIOx_BSRR/BRR` |
| EXTI mapping | HAL GPIO EXTI setup | `GPIO_EXTILineConfig()` + `EXTI_Init()` | `AFIO_EXTICR`, EXTI |
| NVIC | `HAL_NVIC_SetPriority/EnableIRQ()` | `NVIC_Init()` in `misc.c` | NVIC ISER/IPR |
| Timer base | `HAL_TIM_Base_Init()` | `TIM_TimeBaseInit()` | PSC/ARR/CR1 |
| PWM channel | `HAL_TIM_PWM_ConfigChannel()` | `TIM_OC1Init()` etc. | CCMR/CCER/CCR |
| USART setup | `HAL_UART_Init()` | `USART_Init()` + `USART_Cmd()` | BRR/CR1/CR2/CR3 |
| USART I/O | `HAL_UART_Transmit/Receive()` | `USART_SendData/ReceiveData` + flags | SR/DR |
| I2C transaction | `HAL_I2C_Mem_Read/Write()` | START, address, event/flag, data calls | I2C state machine |
| SPI I/O | `HAL_SPI_TransmitReceive()` | `SPI_I2S_SendData/ReceiveData` + flags | SR/DR |
| ADC channel | `HAL_ADC_ConfigChannel()` | `ADC_RegularChannelConfig()` | SQR/SMPR |
| ADC calibration | HAL calibration entry | reset calibration, start, wait | CR2 |
| DMA | `HAL_DMA_Init()` | `DMA_Init()` + `DMA_Cmd()` | CCR/CNDTR/CPAR/CMAR |
| Flash | HAL erase/program | `FLASH_ErasePage/ProgramHalfWord` | controller state machine |
| CAN | HAL transmit/receive | `CAN_Transmit/CAN_Receive` | bxCAN mailbox/FIFO |

### Polling needs a deadline

`USART_SendData()` writes one data register. It does not provide a complete buffer operation or a HAL-style timeout:

```c
static int usart1_send_byte(uint8_t byte, uint32_t spin_limit)
{
    while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET) {
        if (spin_limit-- == 0U) return -1;
    }
    USART_SendData(USART1, byte);
    return 0;
}
```

`spin_limit` only demonstrates bounded waiting. Product code should use a deadline derived from a reliable monotonic clock and define recovery after timeout.

## ⚡ 6. Interrupts: no HAL callback dispatcher

```c
static volatile uint8_t g_key_event;

void EXTI0_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line0) != RESET) {
        EXTI_ClearITPendingBit(EXTI_Line0);
        g_key_event = 1U;                     /* hand off a minimal event */
    }
}
```

Check every boundary:

- `EXTI_Init()` configures the EXTI line; `GPIO_EXTILineConfig()` still maps the GPIO port.
- `NVIC_PriorityGroupConfig()` chooses grouping; `NVIC_Init()` enables the channel.
- Each handler checks the real source because vectors may be shared.
- Clear rules differ. USART ORE still requires reading SR then DR; do not substitute a similar-looking clear function.
- An ISR does not perform blocking output, a complete I2C transaction, Flash erase, or a long delay. Preserve minimal evidence and hand off work.

## 🚚 7. DMA: two drivers are not wired together automatically

USART1 TX needs at least:

1. DMA1 clock and DMA1 Channel 4 from the RM0008 request map.
2. `DMA_Init()` with addresses, direction, count, increments, and widths.
3. `USART_DMACmd()` to enable the USART request, then `DMA_Cmd()` to start the channel.

```c
DMA_InitTypeDef dma;
RCC_AHBPeriphClockCmd(RCC_AHBPeriph_DMA1, ENABLE);
DMA_DeInit(DMA1_Channel4);
DMA_StructInit(&dma);
dma.DMA_PeripheralBaseAddr = (uint32_t)&USART1->DR;
dma.DMA_MemoryBaseAddr     = (uint32_t)tx_buffer;
dma.DMA_DIR                = DMA_DIR_PeripheralDST;
dma.DMA_BufferSize         = tx_length;
dma.DMA_PeripheralInc      = DMA_PeripheralInc_Disable;
dma.DMA_MemoryInc          = DMA_MemoryInc_Enable;
dma.DMA_PeripheralDataSize = DMA_PeripheralDataSize_Byte;
dma.DMA_MemoryDataSize     = DMA_MemoryDataSize_Byte;
dma.DMA_Mode               = DMA_Mode_Normal;
dma.DMA_Priority           = DMA_Priority_Low;
dma.DMA_M2M                = DMA_M2M_Disable;
DMA_Init(DMA1_Channel4, &dma);
USART_DMACmd(USART1, USART_DMAReq_Tx, ENABLE);
DMA_Cmd(DMA1_Channel4, ENABLE);
```

The buffer must remain alive until completion. Width, direction, and increment rules must match the register. `DMA_GetCurrDataCounter()` returns remaining **items**, not newly received bytes. F1 has no D-cache; that does not make this code portable to H7.

## 🧰 8. Minimum peripheral chains

| Peripheral | Minimum SPL chain | Boundary most often missed |
| --- | --- | --- |
| GPIO | RCC → StructInit → Init → Set/ResetBits | AFIO clock for F1 remapping |
| EXTI | GPIO input → AFIO → map → EXTI → NVIC | uncleared pending bit repeats |
| Timer PWM | RCC/GPIO → TimeBase → OCx → Cmd | TIM1/TIM8 need `TIM_CtrlPWMOutputs` |
| USART | RCC/GPIO → Init → Cmd → flags + data | TXE and TC are different boundaries |
| I2C | clocks/open drain → Init → Cmd → START/address/events/data/STOP | transaction timeout and bus recovery |
| SPI | clocks/GPIO/CS → Init → Cmd → TXE/RXNE/BSY | every write also receives; wait for BSY clear |
| ADC | clock/analog pin → Init → channel → Cmd → calibration → conversion | F1 calibration order and sample time |
| DMA | clock → DeInit/StructInit/Init → request → Cmd | fixed request map and width-based count |
| Flash | unlock → clear → erase/program → status → lock | page/halfword alignment and power loss |
| CAN | clocks/GPIO → Init → filter → IRQ/NVIC → Tx/Rx | one normal-mode node receives no ACK |

## 🔀 9. Maintaining and migrating an old project

1. Freeze a reproducible baseline: exact part, V3.5.0, density macro, compiler, startup, crystal, linker script, and board revision.
2. Draw a peripheral ownership table: SPL, direct registers, or a third-party component.
3. Migrate one peripheral per change while keeping wiring, clocks, input, and instrument conditions fixed.
4. Compare visible results: GPIO voltage, PWM period, UART frame, DMA position, Flash checksum.
5. Remove old ownership after migration. Delete the SPL setup and IRQ path for a peripheral now owned by HAL.

Keep SPL when an F1 product is already in production, evidence and certification surround the frozen toolchain, and the team can keep that environment reproducible. Prefer HAL/LL when a new family has no SPL, CubeMX/current middleware is required, or the old project contains untraceable SPL copies.

## ⚠️ 10. Failure map

| Symptom | First boundary | Action |
| --- | --- | --- |
| `GPIO_InitTypeDef` undefined | driver macro/conf header | inspect compiler defines and `stm32f10x_conf.h` |
| compiles, then undefined reference | header present, source absent | compile the matching driver `.c` |
| IRQ name looks right but never runs | startup/density/NVIC mismatch | compare vector table, part, and NVIC setup |
| LED polarity reversed | PC13 LED is active low | use the schematic |
| final UART byte truncated | waited for TXE, not TC | wait for TC before disabling/changing direction |
| I2C loop never exits | event polling has no deadline | add one deadline and bus recovery |
| first ADC values wrong | F1 calibration order missing | reset calibration, wait, calibrate, wait |
| DMA immediately reports TE | map/address/clock/width mismatch | inspect RM0008, CPAR, CMAR, CNDTR |
| intermittent failure after adding HAL | double ownership | remove one setup and IRQ path |
| “same” API absent on H7 | SPL is not cross-generation | redesign for H7 HAL/LL, memory domains, and cache |

## 🧪 Labs

1. Build the SPL blink and record `SystemCoreClock`, measured period, and error.
2. Step through `GPIO_ResetBits` and record the final register write; compare chapter 3's HAL path.
3. Implement a deadline-based USART byte send and prove a clock fault returns an error instead of hanging.
4. Log `DMA_GetCurrDataCounter()` in circular receive and compute `(capacity - remaining)` with wrap.
5. Migrate one GPIO or USART peripheral to HAL, prove the waveform is unchanged, then remove old ownership.

Self-test:

1. What do `USE_STDPERIPH_DRIVER` and `STM32F10X_MD` each select?
2. Why is `USART_SendData()` not synonymous with `HAL_UART_Transmit()`?
3. Why should one USART not be initialized by both SPL and HAL?

## 🔗 Sources

- [STSW-STM32054](https://www.st.com/en/embedded-software/stsw-stm32054.html), the official STM32F10x SPL product entry.
- Frozen V3.5.0 source mirror: [commit `afa743577f2784e95be2d5003380fdb84a702519`](https://github.com/wajatimur/stm32f10x-stdperiph-lib/commit/afa743577f2784e95be2d5003380fdb84a702519). It locates source; ST and RM0008 remain authoritative.
- Related: [chapter 0](00-how-to-learn-stm32.md), [GPIO](03-gpio-and-led.md), [interrupts](04-interrupts-nvic.md), [UART](06-uart.md), and [DMA](10-dma.md).
