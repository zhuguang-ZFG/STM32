# 01 Setting Up the Development Environment
> 中文：[开发环境搭建](../01-开发环境搭建.md)

> From nothing, install a setup that can compile, flash, and single-step an STM32.

<p align="center">
  <img src="../../assets/animations/boot-sequence.svg" width="760" alt="Boot and vector fetch after power-on reset">
  <br><sub>▲ Animation: after power-on reset the CPU fetches the vector table and boots (vector drawing by the author)</sub>
</p>

<!-- video:ch01 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch01-env.png">
    <source src="../../assets/video/ch01-env.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chinese voice-over, 2.5 min. Voice: Microsoft Edge neural voice zh-CN-XiaoxiaoNeural via edge-tts (library mostly LGPLv3; the voice model is an online Microsoft service, not an open model). Pictures are generated from this repo's SVGs, not photographs. Video: <a href="../../assets/video/ch01-env.mp4">MP4</a> · subtitles: <a href="../../assets/video/ch01-env.srt">SRT</a>. Rebuild with <code>python3 tools/gen_narrated.py --speak</code>.</sub>
</p>

**Narration script (Chinese, same text as the subtitles)**

1. 环境这章只追一个问题：你写下的 C，怎样变成芯片里正在跑的程序。中间就是编译、链接、烧录、复位运行。工具可以换，这四步不会换。
2. Keil、CubeIDE、PlatformIO 都能走完这四步。差别只是谁帮你填启动文件和链接脚本。先选一个能单步的，不要三个一起装到怀疑人生。
3. 复位之后，内核先读向量表。第零个字是栈顶，第一个字才是复位入口。进 main 之前，启动文件还要配时钟、搬数据段、清 BSS。
4. 这一帧是仓库里的启动顺序动画，不是芯片照片。你只要记住：还没进 main，该做的家务启动文件已经做完一轮。单步时别以为第一行就是上电第一件事。
5. 下载靠 SWD。F103 上 PA13 是数据线，PA14 是时钟。把这两只脚让给别的功能，下次探针就连不上。救砖时先把 BOOT0 拉高，再重新接上。
6. Cube 生成的工程，用户代码写在它留的标记中间。时钟改了就重新生成，不要在启动文件里打补丁。临时文件和编译产物不要提交进版本库。
7. 第一次下载只做三件事：接上调试器，确认软件认出芯片型号，再下一个只点灯的空工程。连芯片都认不出，就先别查业务代码。
8. 口诀：先认出芯片，再谈业务。调试器连不上的时候，查线、查供电、查 BOOT，不要先重写 main。线都没通，改代码是在安慰自己。
9. 这章结束，你的文件夹里应该有一个能单步的工程。你要能说出向量表前两个字是什么，也要能指出 SWD 占用的两只脚。
10. 合上书，三问。向量表第零个字是什么？第一个字是什么？SWD 占哪两只脚？答不上来，就把启动文件再单步一遍。
<!-- /video:ch01 -->
## 📌 Learning goals
- [ ] See how Keil MDK, STM32CubeIDE, VS Code + PlatformIO, and CLion differ, and pick one
- [ ] Use STM32CubeMX to generate a project that compiles immediately (clock, SWD, code-generation options)
- [ ] Install the ST-Link driver, upgrade its firmware, and wire SWD from the table
- [ ] Track down "No target connected", "Flash Download failed", and a chip with read protection on your own

## 🧠 Core ideas

**Lead with the conclusion: whichever IDE you use, the toolchain underneath is the same path — compile → link → flash → reset and run.**

### 1. Toolchain data flow

```
source .c/.h
   │  compile (arm-none-eabi-gcc / ARMCC / ARMCLANG)
   ▼
object file .o
   │  link (ld / armlink) + linker script (.ld/.sct)
   ▼
executable .elf  ──► .hex / .bin
   │  flash (ST-Link / OpenOCD / pyOCD) over SWD
   ▼
Flash 0x08000000
   │  reset
   ▼
CPU fetches the vector table → Reset_Handler → main()
```

### 2. Power-on boot (the animation above)

| Step | What the hardware is doing | Notes |
| --- | --- | --- |
| 1 | After reset, read the **initial MSP** from `0x00000000` | Initial main stack pointer |
| 2 | Read the **Reset_Handler address** from `0x00000004` | Reset vector |
| 3 | Run `startup_stm32f1xx.s` | Set up the stack, call SystemInit |
| 4 | `SystemInit()` | Configure the clock and the vector-table offset |
| 5 | `__main` → `main()` | Enter your code |

### 3. Four development environments

| Dimension | Keil MDK-ARM | STM32CubeIDE | VS Code + PlatformIO | CLion + OpenOCD |
| --- | --- | --- | --- | --- |
| License | Community edition is free (a license is required past the code-size limit) | Completely free (ST official) | Free and open source | Paid (free for students) |
| Compiler | ARMCC / ARMCLANG | GCC (arm-none-eabi) | GCC | GCC |
| How hard to start | Low (lots of Chinese material) | Low (CubeMX is built in) | Medium (you have to fill in platformio.ini) | Medium to high |
| Debugger | Strong (registers, variables, breakpoints are complete) | Strong (debugger built in) | Medium (depends on Cortex-Debug) | Strong |
| Platforms | Windows only | Win / Linux / mac | All of them | All of them |
| Fits | Teaching, older company projects | What ST recommends, beginners | Tinkerers, CI automation | People who live in C/C++ |

**How to choose: beginners use STM32CubeIDE (free, and CubeMX is built in). If you already have a Keil license, use Keil. If you want the command line or CI, use PlatformIO.**

### 4. A normal project tree

```
Core/          Inc/  Src/          ← user code (main.c, interrupts, peripheral init)
Drivers/       CMSIS/  STM32F1xx_HAL_Driver/
Middlewares/   (optional, such as FreeRTOS or FatFs)
Startup/       startup_stm32f103xb.s
STM32F103C8TX_FLASH.ld           ← linker script (GCC)
<project>.ioc                    ← CubeMX project file
```

The tree is drawn in [`assets/diagrams/project-structure.svg`](../../assets/diagrams/project-structure.svg) (vector drawing by the author).

### 5. Generating a project in STM32CubeMX, end to end

| Step | What you do | The option that matters |
| --- | --- | --- |
| 1 | New Project, search, and select the part | Pick `STM32F103C8Tx` |
| 2 | Configure pins in the Pinout view | Example: set PC13 to `GPIO_Output` |
| 3 | System Core → RCC | Set HSE to `Crystal/Ceramic Resonator` |
| 4 | System Core → SYS | Set Debug to `Serial Wire` (otherwise reused SWD pins will not connect) |
| 5 | Clock Configuration | HSE 8 MHz → PLL ×9 → SYSCLK 72 MHz |
| 6 | Project Manager → Project | Name, path, Toolchain `STM32CubeIDE` or `MDK-ARM` |
| 7 | Code Generator | Check "Copy only necessary library files", and generate separate .c/.h files |
| 8 | GENERATE CODE | You can compile as soon as it finishes |

> ⚠️ SYS Debug must be **Serial Wire**. Otherwise CubeMX configures PA13/PA14 as ordinary GPIO, and after one flash you can never connect again (see Pitfalls).

### 6. Compile, flash, and debug

| Action | Keil | CubeIDE |
| --- | --- | --- |
| Compile | F7 / Build | Ctrl+B |
| Flash | F8 / Download | Run → Debug (downloads automatically) |
| Debug | Ctrl+F5 / Start Debug | F11 / Debug |
| Reset and run | Reset button | Run button |

## 🛠️ Hardware and wiring

### SWD wiring (ST-Link V2 ↔ BluePill)

| ST-Link pin | Board pin | Signal | Notes |
| --- | --- | --- | --- |
| 3.3V | 3V3 | Power | Optional (the board can also take USB power) |
| GND | GND | Ground | **Must be connected**, common ground |
| SWDIO | PA13 | Data | Bidirectional data |
| SWCLK | PA14 | Clock | Debug clock |
| RST | NRST | Reset | Worth connecting; flashing is more reliable |
| 5V | — | — | Usually unused |

> Clone ST-Link V2 boards often use a 10-pin header. Read the silkscreen. SWD needs only four wires (3V3/GND/SWDIO/SWCLK). NRST is optional.

### ST-Link driver and firmware

| Item | What to do |
| --- | --- |
| Install the driver | On Windows, install the ST-Link USB driver (Device Manager shows an STLink dongle) |
| Upgrade firmware | Run ST-Link Upgrade and click Upgrade (firmware that is too old reports DFU-related errors) |
| Check the link | In STM32CubeProgrammer, Connect. If you can read the Device ID, it is OK |
| Linux permissions | Add a udev rule so you do not sudo every time |

## 💻 Code

The skeleton of a CubeMX `main.c` (the part that matters). The full project is in [`examples/gpio-blink/`](../../examples/gpio-blink/).

```c
#include "main.h"

void SystemClock_Config(void);
static void MX_GPIO_Init(void);

int main(void)
{
    HAL_Init();                 /* reset all peripherals, init the Flash interface and SysTick */
    SystemClock_Config();       /* configure a 72MHz core clock */
    MX_GPIO_Init();             /* init PC13 */

    while (1)
    {
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
        HAL_Delay(500);
    }
}

static void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    __HAL_RCC_GPIOC_CLK_ENABLE();       /* the clock enable CubeMX inserts for you */

    GPIO_InitStruct.Pin   = GPIO_PIN_13;
    GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull  = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);
}
```

Compile and download from the command line (GCC + OpenOCD, which is what CI wants):

```bash
# 1) compile (a project generated by PlatformIO or a Makefile)
pio run

# 2) flash the .elf into Flash with OpenOCD
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c "program build/firmware.elf verify reset exit"
```

## ⚠️ Pitfalls and troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| No target connected | SWDIO and SWCLK are swapped, or there is no common ground | Check the four wires; power the board on its own; press NRST and connect again |
| Flash Download failed – "Cortex-M3" | The chip is read-protected, or the clock never started | Clear read protection in CubeProgrammer, then flash again |
| After one flash you can never connect | PA13/PA14 were set as ordinary GPIO (CubeMX was not set to Serial Wire) | Hold NRST, click Connect, and release to "connect under reset"; or set BOOT0=1, boot from SRAM, and erase |
| Compile says "No such file" | Include path or library was not added | Check Include Paths, and that the HAL sources are in the project |
| ST-Link says the firmware is old | The firmware version is too low | Upgrade it with ST-Link Upgrade |
| The program does not run | You forgot `HAL_Init()`, or clock setup failed | Single-step, and check `HAL_RCC_GetSysClockFreq()` |

### Clearing read protection (Read Protection)

1. STM32CubeProgrammer → choose ST-LINK, then Connect.
2. On the left, `Option bytes` → set Read Out Protection to `AA` (Level 0, no protection).
3. Click `Apply`. **Clearing read protection mass-erases the Flash.**
4. Download the program again.

The same thing from the command line (OpenOCD):

```bash
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c "init; reset halt; stm32f1x unlock 0; reset; shutdown"
```

## 🧪 Hands-on labs

1. **Lab 1 (the environment works):** Generate a project in CubeMX, compile it, and download it to a BluePill. The onboard LED blinks at 1 Hz.
2. **Lab 2 (single-step):** Break on `HAL_GPIO_TogglePin` and watch `GPIOC->ODR` change in the debug window.
3. **Lab 3 (reproduce the failure):** Set SYS Debug to Disable once, generate, and feel what "cannot connect" is like. Recover with connect-under-reset and a mass erase.

### 7. The project files that matter

| File | Role |
| --- | --- |
| `<project>.ioc` | CubeMX project settings; you can regenerate the code |
| `startup_stm32f103xb.s` | Startup assembly: vector table and reset entry |
| `STM32F103C8TX_FLASH.ld` | GCC linker script: Flash and RAM layout |
| `<project>.sct` | Keil scatter file |
| `system_stm32f1xx.c` | `SystemInit()`, clock init |
| `stm32f1xx_hal_conf.h` | HAL module switches (trim the size) |

### 8. Debug habits

| Habit | What you do |
| --- | --- |
| Breakpoint | Break on a suspicious line and look at variables and registers |
| Watch | Add globals and locals to the Watch window |
| Registers | Open Peripherals → GPIO and the other peripheral windows |
| SWO/ITM print | Print without using the UART; see the code below |
| Disassembly | Look at the assembly for the C, and see what the optimizer did |

```c
/* SWO/ITM print: only the SWO pin of SWD, does not take the UART */
int _write(int fd, char *ptr, int len)
{
    for (int i = 0; i < len; i++) ITM_SendChar(ptr[i]);
    return len;
}
```

### 9. More errors you will see

| Error | Cause | Fix |
| --- | --- | --- |
| `Flash Download failed` | Clock was not configured, or the algorithm was not selected | In Keil, pick the right Flash algorithm |
| `Cannot access target` | Target lost power or is in reset | Check power and NRST |
| `No STM32 target found` | Cable or driver | Try another USB port and reinstall the driver |
| `Core is locked up` | An illegal address was touched | Check pointers and stack overflow |

### 10. Flash download algorithms

| Part | Keil Flash algorithm | Notes |
| --- | --- | --- |
| F103C8 | STM32F10x Med-density | 64KB |
| F103RC | STM32F10x High-density | 256KB |
| F401 | STM32F4xx | — |

### 11. The startup file gets the house in order

**Conclusion:** after reset the CPU reads two words from `0x00000000`. The first is the MSP. The second is `Reset_Handler`. With BOOT0=0, that address is an alias of Flash at `0x08000000`, not a separate memory.

Current Cube startup order (trust the `startup_*.s` in your project; some older projects copy data first):

| Order | Who does it | Result |
| --- | --- | --- |
| 1 | Hardware | Read the MSP, then jump to Reset_Handler |
| 2 | `SystemInit` | Set up the clock, and point `SCB->VTOR` at the vector table |
| 3 | Startup file | Copy `.data` from Flash to RAM, and clear `.bss` |
| 4 | `__libc_init_array` | Run C++ global constructors and `libc` init |
| 5 | `main` | Your program |

A peripheral interrupt does not enter at `0x08000000 + 4×IRQn`. Sixteen system exceptions sit in front of the vector table, so the entry address is `VTOR + 4×(IRQn + 16)`.

### 12. The linker script stakes out the ground

**Conclusion:** F103C8 Flash is 64 KB, starting at `0x08000000`. SRAM is 20 KB, starting at `0x20000000`. The stack grows down from the top of RAM.

```ld
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
  RAM (xrw)   : ORIGIN = 0x20000000, LENGTH = 20K
}
_estack = ORIGIN(RAM) + LENGTH(RAM);
```

`.isr_vector` needs `KEEP`. Otherwise the linker throws away a vector table that C never references, and the chip flies off at power-up.

Motto: **item 0 is the stack, and item 1 is reset. Clock first, then copy .data, then clear .bss.**

Self-test:

1. With BOOT0=0, which physical memory does the CPU actually see when it reads `0x00000000`?
2. Does an uninitialized global live in `.bss` or `.data`? Who turns it into 0?
3. Why can't you take `IRQn`, multiply by 4, and add `0x08000000`?

## 🔗 Related resources

- Official manuals: **RM0008** chapter 2 (memory and buses), chapter 8 (RCC), chapter 9 (GPIO); **DS5319** (F103C8 datasheet)
- Previous: [00 How to Learn STM32](00-how-to-learn-stm32.md) | Next: [02 Choosing a Part, Memory, and Clocks](02-part-and-clock.md)
- Figures: [`assets/diagrams/project-structure.svg`](../../assets/diagrams/project-structure.svg), [`assets/animations/boot-sequence.svg`](../../assets/animations/boot-sequence.svg)
- Hardware and documents: the ST-Link, STM32CubeIDE, and STM32CubeProgrammer download pages on ST's website
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.
