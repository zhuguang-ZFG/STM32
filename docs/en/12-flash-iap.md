# 12 Flash and IAP Updates
> 中文：[12 Flash 与 IAP 升级](../12-Flash与IAP升级.md)

> Receiving an image and jumping to it does not prove an update succeeded. The bootloader must validate length, range, CRC, and vectors, and the application must report a version heartbeat or the system should stay on the old image or roll back.

<p align="center">
  <img src="../../assets/animations/flash-iap.svg" width="760" alt="IAP update: bootloader plus app, two regions, and the jump">
  <br><sub>▲ Animation: an IAP update, with the bootloader and the app in two regions and a jump between them (vector animation drawn by the author, not a live recording)</sub>
</p>

<!-- video:ch12 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch12-iap.png">
    <source src="../../assets/video/ch12-iap.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.6 min). <a href="../../assets/video/ch12-iap.mp4">MP4</a> · <a href="../../assets/video/ch12-iap.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. 闪存不能当内存随便改一个字节。通常要先擦，再写。擦写之前必须解锁。写到一半掉电，这一页可能是半新半旧，启动时要能认出来。
2. F103 的读保护里，选项字节 0xA5 表示不保护。改成别的值之前，先想清楚你还能不能再读出来。改保护之前，先把现有程序备份下来。
3. 到了 F4，0xCC 这一档是不可逆的读保护。手滑写进去，这颗芯片的调试口就回不来了。实验这种操作，不要放在你唯一的那块板子上。
4. 这一帧是仓库画的升级路径。正在执行的程序不要擦掉自己的脚下。新固件写到另一块区域，校验通过，再跳过去。校验失败就留在旧程序里，设备还活着。
5. 程序如果不是从默认的闪存起始跑，中断向量表的偏移也要改。只改链接脚本、不改向量表偏移，平时能跑，一进中断就飞到旧地址。
6. 跳转之前至少核对长度和校验。有条件再看版本号。没有校验就跳，等于允许任意一包噪声变成你的新程序。失败了要留在还能通信的旧程序里。
7. 擦除不是调用一下就结束。要等忙标志落下，再去读。写保护如果开着，解锁只解了闪存控制器还不够。手册里的顺序不要跳步。
8. 口诀：0xA5 是 F1 的开门钥匙，0xCC 是 F4 的单程票；改保护先备份。擦之前为什么必须解锁？因为锁着的闪存会拒绝你，或者你以为写进去了其实没有。
9. 实验选一页确定不会踩到当前程序的闪存，擦掉、写几个字、再读回来。和程序区叠在一起的实验，做完这章你就没有调试器可以后悔了。
10. 合上书，三问。擦除之前为什么必须解锁？F103 的 0xA5 表示保护还是不保护？F4 写进 0xCC 之后还能不能恢复调试？

</details>
<!-- /video:ch12 -->

## Principle and scope

Page size, half-word programming, and the jump in this chapter are all for the STM32F103C8T6. It is medium-density: 64 KB of Flash from `0x08000000` up to but not including `0x08010000`, in 1 KB pages, 64 pages numbered 0 to 63. Page 63 starts at `0x0800FC00`. `0x0801FC00` is the last page of a 128 KB part and lies outside the C8's 64 KB. High-density parts use 2 KB pages, so page addresses must be recomputed on those. See [RM0008 Rev 21 chapter 3](#source-rm0008-flash).

Program addresses must be 2-byte aligned, and each write is 16 bits. An erased half-word reads back `0xFFFF`. Flash can only turn 1s into 0s; a bit that is already 0 returns to 1 only when the whole page is erased. The F103 cannot program single bytes (the F4 can), so a 32-bit value takes two half-word writes.

To unlock, write the two keys to `FLASH_KEYR` in order: `0x45670123`, then `0xCDEF89AB`. Only then does `CR.LOCK` clear. In the reverse order the lock stays set and the erase returns an error. Lock again when the write is done.

The layout below is the one used by this book and by `examples/iap-bootloader`; the manual does not require it. Bootloader: from `0x08000000`, 16 KB, 16 pages, ending before `0x08004000`. Parameters: from `0x08004000`, 2 KB, 2 pages, ending before `0x08004800`. Application: from `0x08004800`, 46 KB, 46 pages, length `0xB800`, ending before `0x08010000`. The three add up to exactly 64 KB. The application's link-script origin and `SCB->VTOR` must both be `0x08004800`. Change only one and the application's interrupts still land in the bootloader's vector table.

Word 0 of the application region is the initial MSP. Word 1, at `0x08004804`, is the address of `Reset_Handler`. Before the jump, read both words, set the MSP, write `VTOR`, then branch to the reset address. With `VTOR` still 0, interrupts still go to the bootloader. These two words mean the same as in the startup sequence of chapter 01. See [PM0056](#source-pm0056-vector).

The "no protection" value for readout protection is `0xA5`. Setting it back to `0xA5` makes the hardware mass-erase main Flash first. See [PM0075](#source-pm0075-rdp). This chapter's bootloader lives in user Flash, not in the factory system memory. The UART it receives firmware on is still pin 30 PA9 and pin 31 PA10 from chapter 06.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-12-iap-map.svg" width="760" alt="Medium-density Flash uses 1 KB pages. The application starts at 0x08004800 and is 0xB800 bytes long. The jump loads word 0 and word 1.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, medium-density, 64 KB, 1 KB pages. In order, the figure writes 0x45670123, then 0xCDEF89AB, programs a half-word into the application, loads the MSP from 0x08004800 and the reset address from 0x08004804, and sets VTOR to 0x08004800. It also marks three faults: the keys reversed, the last page taken as 0x0801FC00, and VTOR left at 0. Sources: [RM0008 Rev 21 chapter 3](#source-rm0008-flash) and [PM0056](#source-pm0056-vector).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/iap-jump.gif" width="640" alt="The two keys are written in order, then the CPU reads the MSP and the reset word">
  <br><sub>▲ Animated version: 0x45670123, then 0xCDEF89AB, one half-word into the application, then the MSP and the reset address are read. The printed book has only the static figure above.</sub>
</p>

The opening animation `flash-iap.svg` shows the whole update flow. For page boundaries, the two keys, and the two jump words, go by the static figure above.

## Timing and state

| Region | Start | Length | Pages | Ends at |
| --- | --- | --- | --- | --- |
| Bootloader | `0x08000000` | 16 KB | 16 | `0x08004000` |
| Parameters | `0x08004000` | 2 KB | 2 | `0x08004800` |
| Application | `0x08004800` | 46 KB, `0xB800` | 46 | `0x08010000` |
| Last page | `0x0800FC00` | 1 KB | page 63 | inside the application |
| Failure address | `0x0801FC00` | — | — | not in this 64 KB |
| Keys | `0x45670123` first | `0xCDEF89AB` second | — | the reverse order leaves LOCK set |
| Half-word | address aligned to 2 bytes | 16 bits | erased state `0xFFFF` | the C8 cannot program single bytes |
| Jump | word at `0x08004800` is the MSP | word at `0x08004804` is reset | `VTOR = 0x08004800` | `VTOR` left at 0 still enters the bootloader |

## Pitfalls and sources

| What you see | Why | What to do | Source | What the source shows |
| --- | --- | --- | --- | --- |
| The comment says low density, but the page size is right | The density name is wrong | Call this part medium-density. The page stays 1 KB, 64 pages | [RM0008](#source-rm0008-flash) | Medium-density parts erase 1 KB pages. 2 KB pages are on high-density parts |
| The erase returns an error | The keys are reversed, or the address is not on a page boundary | Write KEY1, then KEY2. Keep the address on a page boundary | [RM0008](#source-rm0008-flash) | The order is `0x45670123` then `0xCDEF89AB`. The reverse order does not clear LOCK |
| A written byte reads back wrong | The program was not a half-word, or a 0 was asked to become 1 | Write half-words on even addresses. Erase the page before turning a 0 back into a 1 | [RM0008](#source-rm0008-flash) | Programming granularity is 16 bits. The erased state is `0xFFFF`. The F103 has no byte programming |
| The jump dies, or interrupts return to the bootloader | The two words were not loaded, or VTOR is still 0 | Load the MSP and the reset word from `0x08004800`, and write `VTOR` | [PM0056](#source-pm0056-vector) | Word 0 is the initial stack. Word 1 is the reset address |
| The application length does not match the link script | The length is not 46 KB | Origin `0x08004800`, length `0xB800` | [examples in this repo](#source-project-examples) | `examples/iap-bootloader` sizes the application at 46 KB, which is `0xB800` |
| The experiment writes `0x0801FC00` | That is the last page of a 128 KB part | The last page on this C8 is `0x0800FC00` | [DS5319](#source-ds5319-swd) | STM32F103x8 Flash is 64 KB. `0x0801FC00` is the last page of a 128 KB part |
| Readout protection is cleared with another family's unprotected key | The F103 key values differ from other families | The unprotected value is `0xA5`. Clearing it mass-erases main Flash | [PM0075](#source-pm0075-rdp) | RDP `0xA5` allows readout. Programming `0xA5` back mass-erases first |

## Learning goals

- [ ] Know the F1 "page" and F4 "sector" Flash layout, the erase/write endurance, and the programming granularity.
- [ ] Walk the full sequence: unlock (KEY1 / KEY2) → erase → program → lock.
- [ ] Understand how IAP works, and be able to draw the bootloader-plus-app memory map.
- [ ] Know the critical steps before jumping to the app: disable interrupts, reset the peripherals, set MSP, and set `SCB->VTOR`.
- [ ] Know the basic flow of a YMODEM / UART update protocol.

## Core ideas

Split the update into receive, program, verify, jump, and application confirmation. Every stage needs a failure exit; an unvalidated address must never become MSP or PC.

### 1. How Flash is organized

Flash is like a notebook you write in pencil and can only erase a whole page at a time. Erased cells are all 1. Writing can only turn a 1 into a 0, and the only way to turn a 0 back into a 1 is to erase the whole page. So to change one byte, you read the page out, erase it, and write it back with the changed byte. Each page survives only so many erases, so a log that writes often has to rotate through pages.

F1 erases by **1 KB or 2 KB pages** and programs a **half-word (16 bits)**. F4 erases by **16 to 128 KB sectors** and can program a **byte, half-word, word, or double word**.

| Item | STM32F1 (RM0008, Chapter 3, FLASH) | STM32F4 (RM0090, Chapter 3, FLASH) |
| --- | --- | --- |
| Erase granularity | Page: 1 KB on low- and medium-density, 2 KB on high-density | Sector: S0–S3 = 16 KB, S4 = 64 KB, S5–S7 = 128 KB (F407VG) |
| Program granularity | Half-word (16-bit) | Byte / half-word / word (32-bit) / double word (64-bit) |
| Programming voltage | Generated internally (the internal pump provides VPP) | Generated internally |
| Endurance | ≥ 10k cycles (guaranteed by the datasheet) | ≥ 10k cycles |
| Data retention | 20 years at 85°C | 20 years at 85°C |
| Erase time | Page erase ~20 to 40 ms | Sector erase ~0.4 to 4 s (larger is slower) |

> [!WARNING]
> Flash **can only be erased a whole page or a whole sector at a time**. You cannot change it byte by byte. Changing one byte still means erasing the whole page first. If you log frequently, do wear leveling and spread the writes across different pages.

### 2. Unlock and the programming sequence

Flash is normally locked, so a runaway program cannot scribble on it. To unlock it, you write two fixed values to the key register in order. If the order or a value is wrong, Flash stays locked until the next reset. After unlocking you erase, then write, and wait for the busy flag to clear before each next step. Lock it again at the end.

**The F1 sequence (RM0008, Chapter 3):**

1. **Unlock**: write `0x45670123` and then `0xCDEF89AB` (KEY1, KEY2) to `FLASH_KEYR`. That clears `CR.LOCK`.
2. **Erase**: set `CR.PER=1`, write the target page address to `FLASH_AR`, set `CR.STRT=1`, and poll `SR.BSY` until it is 0. Then check `SR.EOP`.
3. **Program**: set `CR.PG=1`, write a **half-word** to the target address, and poll `SR.BSY`.
4. **Lock**: set `CR.LOCK=1`.

**What is different on F4**: erase by setting the `SER` bit in `FLASH_CR` and selecting the sector number with `SNB[3:0]`. Programming uses `PSIZE` to choose the width. Watch the F4 Flash voltage range (`VPP`) and the "programming parallelism" setting.

The HAL wraps that sequence as:

```c
HAL_FLASH_Unlock();                                  /* unlock */
HAL_FLASHEx_Erase(&erase, &sectorError);             /* erase (page or sector) */
HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD, addr, data);  /* F1 half-word */
/* F4 can use FLASH_TYPEPROGRAM_WORD / FLASH_TYPEPROGRAM_DOUBLEWORD */
HAL_FLASH_Lock();                                    /* lock */
```

### 3. How IAP works, and how you split the memory

IAP lets the chip replace its own program. Flash is split into regions. At the front is a small bootloader that is never overwritten. Next is a parameter region that holds the update flag. After that is the real application. At every power-up the bootloader runs first and checks the parameter region. If an update is due, it receives the new program over UART and writes it into the application region. If not, it jumps straight to the application.

IAP splits Flash into a **bootloader region, a parameter region, and an app region**. At power-up the bootloader runs first, decides whether to update or to jump, and then jumps to the app.

**Example map (STM32F103C8T6, 64 KB Flash):**

| Region | Start address | Size | Contents |
| --- | --- | --- | --- |
| Bootloader | `0x0800 0000` | 16 KB | Boot, UART update, and the jump |
| Parameters | `0x0800 4000` | 2 KB | Update flag, app size, CRC |
| App | `0x0800 4800` | 46 KB | The user application (the linker script origin becomes 0x08004800) |

**Example map (STM32F411CE, 512 KB Flash):**

| Region | Start address | Size |
| --- | --- | --- |
| Bootloader | `0x0800 0000` | 32 KB |
| Parameters | `0x0800 8000` | Sector 2 on its own (16 KB), of which 2 KB is used. Sector 3 is left empty |
| App | `0x0801 0000` | 448 KB (sectors 4–7, up to `0x0808 0000`) |

> F4 erases by sector. If the parameter region shares a sector with the bootloader, they are erased together, so the parameter region has to **own a sector by itself**.

<p align="center">
  <img src="../../assets/diagrams/iap-acceptance-gates.svg" width="820" alt="An IAP image passes length and CRC, slot range, vector, jump, and application-heartbeat gates">
  <br><sub>▲ Update gates: any failed check stays in the bootloader and preserves the last valid image. Reaching the app proves only that control left the bootloader; the version heartbeat proves that the new image completed startup (FA-002 · IG-010 · C-03/C-10/C-27/C-31).</sub>
</p>

### 4. What you must do before jumping to the app

Jumping from the bootloader to the application is a shift change, and the bootloader has to tidy up. Interrupts, timers, and peripherals it turned on have to be switched off, or the application receives an interrupt it does not expect the moment it starts. The CPU also has to be told two things: where the new stack starts, and where the vector table now lives. Skip any of these and the application may run back into the bootloader on its first interrupt.

Before the jump you must disable interrupts, reset the peripherals, set MSP, and set the vector-table offset. Otherwise an interrupt inside the app jumps back into the bootloader's vector table and the chip hangs.

```c
typedef void (*pFunction)(void);
#define APP_ADDR  0x08004800UL

void JumpToApp(void)
{
    uint32_t app_stack = *(volatile uint32_t *)APP_ADDR;         /* vector table [0] = MSP */
    uint32_t app_entry = *(volatile uint32_t *)(APP_ADDR + 4);   /* vector table [1] = Reset_Handler */

    /* 1) Disable global interrupts and stop SysTick, so an interrupt cannot cut in during the jump */
    __disable_irq();
    SysTick->CTRL = 0;
    SysTick->LOAD = 0;
    SysTick->VAL  = 0;

    /* 2) Reset every peripheral (put the ones the bootloader used back to their defaults) */
    HAL_RCC_DeInit();
    HAL_DeInit();

    /* 3) Set the main stack pointer MSP and the vector-table offset */
    __set_MSP(app_stack);
    SCB->VTOR = APP_ADDR;

    /* 4) Enable interrupts again and jump to the app entry */
    __enable_irq();
    ((pFunction)app_entry)();
}
```

**On the app side**, move the vector-table base to the app's own start address as well (usually at the top of `SystemInit()` or `main()`):

```c
SCB->VTOR = 0x08004800UL;   /* must match what the bootloader agreed */
```

### 5. YMODEM / UART update flow

YMODEM is a reliable file-transfer protocol with a CRC check. Paired with a UART, it is a general-purpose IAP path.

1. The device (the bootloader) enters receive mode and periodically sends the character `'C'` to request data.
2. The host (SecureCRT, Xshell, or a tool you write) sends the first packet: file name and size.
3. The device picks the app address, erases the matching pages, and receives **128-byte or 1024-byte** packets. After the CRC16 checks out, it writes Flash and replies `ACK`.
4. When the transfer ends (an empty packet), it checks the CRC of the whole image, sets the "app is valid" flag, and resets or jumps.

## Hardware and wiring

| Board | Use | Pin | Notes |
| --- | --- | --- | --- |
| BluePill (F103) | UART IAP | PA9 / PA10 → USB-TTL | Receive the update image on UART1 |
| Nucleo-F411RE | UART IAP | USART2 (ST-Link virtual COM port) | No extra USB-TTL adapter |
| Any | Watch it while debugging | SWD (SWDIO / SWCLK) | You can still connect after it falls into the bootloader |

> IAP needs no extra hardware. You only need a serial tool that can send a file (SecureCRT, Xshell, or a host program you write).

## Code

**① Erase and program Flash (F1, by page)**

```c
#include "stm32f1xx_hal.h"

#define APP_ADDR     0x08004800UL
#define FLASH_PAGE   1024U        /* F103C8 medium-density, 1 KB per page */

/* Erase the pages covering [addr, addr+len) */
int Flash_EraseRange(uint32_t addr, uint32_t len)
{
    FLASH_EraseInitTypeDef er = {0};
    uint32_t page_err = 0;

    HAL_FLASH_Unlock();
    er.TypeErase   = FLASH_TYPEERASE_PAGES;
    er.PageAddress = addr;
    er.NbPages     = (len + FLASH_PAGE - 1) / FLASH_PAGE;
    if (HAL_FLASHEx_Erase(&er, &page_err) != HAL_OK) {
        HAL_FLASH_Lock();
        return -1;
    }
    HAL_FLASH_Lock();
    return 0;
}

/* Write the buffer as half-words */
int Flash_WriteBuf(uint32_t addr, const uint16_t *data, uint32_t halfwords)
{
    HAL_FLASH_Unlock();
    for (uint32_t i = 0; i < halfwords; i++) {
        if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD,
                              addr + i * 2, data[i]) != HAL_OK) {
            HAL_FLASH_Lock();
            return -1;
        }
    }
    HAL_FLASH_Lock();
    return 0;
}
```

**② Jump to the app**

```c
typedef void (*pFunction)(void);

void JumpToApp(uint32_t app_addr)
{
    uint32_t sp    = *(volatile uint32_t *)app_addr;
    uint32_t entry = *(volatile uint32_t *)(app_addr + 4);

    __disable_irq();
    SysTick->CTRL = 0; SysTick->LOAD = 0; SysTick->VAL = 0;
    HAL_RCC_DeInit();
    HAL_DeInit();

    __set_MSP(sp);
    SCB->VTOR = app_addr;
    __enable_irq();
    ((pFunction)entry)();
}
```

**③ Bootloader main flow (the skeleton)**

```c
int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_USART1_UART_Init();

    /* If a 'U' command arrives within 500 ms of power-up, enter the update; otherwise jump to the app */
    if (Uart_WaitForUpgrade(500)) {
        Ymodem_Receive(APP_ADDR);        /* receive packets, check them, write Flash */
    }
    JumpToApp(APP_ADDR);
    for (;;) { }                         /* never reaches here */
}
```

> The app project has to change the linker script: Flash origin `0x08004800`, and the length reduced to match. At the top of `main()`, set `SCB->VTOR = 0x08004800;`.

## Hands-on labs

1. **Page-write evidence:** Write a known 256-byte pattern only to a test page explicitly reserved by the linker script. After reset, compare every byte and the CRC. Refuse the test if the address falls inside the app or bootloader region.
2. **Reject bad images:** Create three images: wrong CRC, MSP outside SRAM, and Reset_Handler outside the app slot. The bootloader prints a stable error code and remains in update mode without jumping.
3. **Valid update and rollback:** For a valid image, record length, CRC, vector[0], vector[1], and the app_version heartbeat. With A/B slots, interrupt one transfer and confirm that the old slot still boots.

### 6. Option bytes: readout protection, write protection, and the hardware watchdog

Option bytes do not live in an ordinary Flash page. Changing readout protection erases the whole user Flash. Back up first, then touch it.

| Byte | F1 | F4 |
| --- | --- | --- |
| RDP | `0xA5` means no protection; any other value is readout protection. There is no Level 2 | `0xAA` is Level 0; any other value that is not `0xCC` is Level 1; `0xCC` is Level 2, and it is irreversible |
| USER | `nRST_STOP`, `nRST_STDBY`, `WDG_SW` | The same bits cover reset-on-stop and the hardware watchdog |
| WRP | Write protection by page | Write protection by sector |

The F4 levels `0xAA` and `0xCC` do not exist on the STM32F103C8T6. The F103 no-protection value is `0xA5`, and clearing readout protection mass-erases main Flash.

When `WDG_SW = 0`, the hardware IWDG starts at power-up and software cannot stop it. On F4, if the parameter region is squeezed into the same sector as the bootloader, erasing the parameters erases the bootloader with them, so the parameter region has to own a sector of its own.

Reading the current configuration is safe:

```c
HAL_FLASH_OB_Unlock();
FLASH_OBProgramInitTypeDef ob = {0};
HAL_FLASHEx_OBGetConfig(&ob);   /* inspect RDPLevel / WRP; do not write yet */
```

The call that writes RDP is not shown here. It erases the whole chip. Copying it into a sample project is an easy way to lock the board into readout protection.

Before leaving this chapter, keep one page-write CRC, stable error codes for the three bad images, and a version heartbeat from a valid image. An A/B design also needs proof that the old version boots after an interrupted update.

Self-test:

1. On an F103, if you change RDP from 0xA5 to some other value, is the program in Flash still there?
2. After you write 0xCC on an F4, can an ST-Link still recover the part?
3. Why can't a 2 KB parameter region on F4 just sit at the tail of the bootloader's sector?

## Related resources

- RM0008, *STM32F10xxx Reference Manual*, Chapter 3, Embedded Flash memory (page layout, KEY, programming sequence).
- RM0090, *STM32F4 Reference Manual*, Chapter 3, FLASH (sector layout, SER / SNB, programming width).
- Datasheet DS: endurance, data retention, and program / erase times.
- Application note AN2557, *STM32F10xxx in-application programming using the USART*.
- The Definitive Guide to the ARM Cortex-M3 and Cortex-M4: the vector table, `SCB->VTOR`, and the exception model.
- Figure: `../../assets/animations/flash-iap.svg` (vector drawing by the author).
