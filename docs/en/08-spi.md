# 08 The SPI Bus
> 中文：[SPI 总线](../08-SPI总线.md)

> SPI is a fast full-duplex link on four wires. Flash, displays, and sensors use it all the time.

<p align="center">
  <img src="../../assets/animations/spi-transfer.svg" width="760" alt="SPI full-duplex shift and CPOL/CPHA timing">
  <br><sub>▲ Animation: SPI full-duplex shifting, and the timing of the four CPOL/CPHA modes (vector drawing by the author)</sub>
</p>

<!-- video:ch08 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch08-spi.png">
    <source src="../../assets/video/ch08-spi.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.6 min). <a href="../../assets/video/ch08-spi.mp4">MP4</a> · <a href="../../assets/video/ch08-spi.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. SPI 通常是时钟、主机输出、主机输入、片选。名字要按方向记：主机出去的那根不能和进来的那根对调。对调之后，两边都在听，谁也不说话。
2. 模式由时钟空闲电平和在哪个沿采样决定。模式 0 是空闲为低，第一个有效沿就采样。主机和从机模式不一致时，数据会整字节错位，看起来像随机数。
3. 片选是一次事务的括号。拉低表示开始，拉高表示结束。有的从机只在片选上升沿才把数据收下。一直压着片选，下一包会粘在上一包后面。
4. 这一帧是仓库画的移位过程。时钟每走一拍，主机和从机同时移出一位。所以 SPI 没有应答位。你发出去的同时，也会收到一位，哪怕你并不关心它。
5. 全双工意味着你发送的时候，接收缓冲也在进数。只写不读，下一次读到的可能是上一包的剩菜。HAL 里能用收发一起的接口，把两边一次做完。
6. 时钟多快，从机手册说了才算。杜邦线很长时，沿会变钝，实验能过、产品会偶发。先把分频放到从机舒服的范围，再谈把速率拧高。
7. 多个从机可以共享时钟和两根数据线，但片选要各走各的。选中谁，谁才应该回应。两根片选同时为低，两个从机一起说话，线上就是冲突。
8. 口诀：模式 0 的空闲时钟是低；主机输出和主机输入不能接反。片选用上升沿结束一次事务。三句先背下来再接线。
9. 实验找一个带只读寄存器的器件，用正确的模式读回来。数值和手册复位值一致，这章才算过。读出全是 FF 或 00，先查模式和进出线。
10. 合上书，三问。模式 0 时空闲时钟是高还是低？主机输出和主机输入能不能接反？一次事务结束时片选应该怎样？

</details>
<!-- /video:ch08 -->

## Learning goals

Before this chapter: you need the APB2 clock from chapter 02 (PCLK2 = 72 MHz in this book's setup) and push-pull output and alternate functions from chapter 03. Chapter 07's I2C makes the best comparison, but you can follow this chapter without it. If binary, hex, and the shift operators (`<<`, `>>`) are new to you, read the "Zero-background primer" in chapter 00 first.

- [ ] Say who drives each of the four wires SCK, MOSI, MISO, and CS, and why MOSI and MISO must not be swapped
- [ ] Read the clock's idle level and sampling edge off a device's timing diagram, and turn them into CPOL/CPHA and HAL's `SPI_POLARITY_LOW` and `SPI_PHASE_1EDGE`
- [ ] Choose the BR field for PCLK2 = 72 MHz, work out SCK, and know that the datasheet limit for an SPI master is 18 MHz
- [ ] Read the W25Q64 JEDEC ID 0xEF4017 with a software chip select, and explain why rx[0] is not the manufacturer id
- [ ] Erase a sector, program a page, and read it back to compare, handling the 256-byte page boundary and the busy wait
- [ ] Fill an ST7789 screen with DMA, and size each transfer to fit in SRAM

## Core ideas

**In one sentence: SPI gives the master and the slave one shift register each and joins them into a ring; each clock the master produces moves one bit out of and one bit into each side, so 8 clocks swap one byte. SPI has no address and no acknowledge; the slave whose chip-select line is low takes part in the swap.**

### An analogy first

Two people sit across a table, each holding a stack of playing cards. A host beats a drum. On each beat both push their top card to the other, and each puts the card they receive at the bottom of their own stack. After 8 beats the two stacks have been swapped completely. Other people sit in the room too. The host taps the shoulder of whoever should swap next; anyone not tapped just watches.

The analogy stops here. In real SPI, "push a card" and "take a card" happen on two different clock edges, and two bits, CPOL and CPHA, decide which edge does which (section 2). The drum cannot beat arbitrarily fast either: both the slave and the STM32 have limits (section 3). And one thing the analogy hides: to read data the master still has to beat the drum, and on every beat it must push a card of its own, even one nobody wants (section 5).

### 1. Four wires and how the shift works

SPI (Serial Peripheral Interface) is a synchronous serial interface. "Synchronous" means a clock line travels next to the data, and the receiver samples by that clock, unlike chapter 06's UART, which relies on a baud rate both sides agreed on in advance.

| Wire | Full name | Driven by | Job |
| --- | --- | --- | --- |
| SCK | Serial Clock | The master | One bit moves per clock period |
| MOSI | Master Out Slave In | The master | Data from the master to the slave |
| MISO | Master In Slave Out | The selected slave | Data from the slave back to the master |
| CS | Chip Select; ST's manuals call it NSS | The master | Low selects one slave; high ends the exchange |

How to read the table: the "Driven by" column says who sets the level on that wire. MOSI and MISO are both named from the master's point of view, so the master's MOSI goes to the slave's MOSI and the master's MISO goes to the slave's MISO; they do not cross the way UART lines do. Slave modules often print MOSI as DI or SDI and MISO as DO or SDO (DI is data in and DO is data out, both from the slave's point of view). Swap the two and both sides "talk" at once and "listen" at once; what comes back is all 0xFF or garbage.

Each side has an 8-bit shift register (a register whose bits all move one place on every clock), and MOSI and MISO join the two into a ring:

```text
         master (STM32)                              slave (W25Q64)
   ┌─────────────────────┐      MOSI       ┌─────────────────────┐
   │ shift register b7…b0 │ ─────────────▶ │ shift register b7…b0 │
   │                     │ ◀───────────── │                     │
   └─────────────────────┘      MISO       └─────────────────────┘
              │                 SCK (produced by the master only)  ▲
              └────────────────────────────────────────────────────┘
```

The most significant bit goes first by default (MSB first; the LSBFIRST bit in CR1 changes it to LSB first, RM0008 Rev 21 section 25.3.1). On each clock the master pushes one bit out on MOSI and takes in, on MISO, the bit the slave pushes out; after 8 clocks the contents of the two registers have traded places. RM0008 Rev 21 section 25.3.5 puts it directly: the transfer starts the moment the master writes a byte into DR (the data register), and as each bit shifts out on MOSI, a bit shifts in on MISO at the same time.

So SPI is full duplex (sending and receiving happen together) by nature, and every byte is a swap. There is no sending without receiving and no receiving without sending; the only difference is whether you care about the byte that came back. This is also why SPI has no acknowledge bit like I2C (chapter 07). The master has no idea whether anyone is on the other end: with the wires wrong or the slave unpowered, it still produces the clocks and still "receives" a byte, usually 0xFF or 0x00. To confirm a device is there, read a register with a fixed value and compare, such as the W25Q64 JEDEC ID.

### 2. The four CPOL/CPHA modes

SPI devices differ on whether the clock idles high or low and on which edge they sample. The STM32 matches them with two bits in CR1 (SPI control register 1):

- CPOL (Clock Polarity): the level of SCK at idle. CPOL = 0 idles low; CPOL = 1 idles high.
- CPHA (Clock Phase): which edge samples. CPHA = 0 samples on the first edge; CPHA = 1 samples on the second edge. "The first edge" is the first time SCK leaves its idle level after chip select goes low.

The two bits give four modes, by convention Mode 0 to Mode 3:

| Mode | CPOL | CPHA | SCK at idle | Sampling edge | Edge that changes the next bit | HAL setting |
| --- | --- | --- | --- | --- | --- | --- |
| Mode 0 | 0 | 0 | Low | 1st edge, rising | Falling | `SPI_POLARITY_LOW` + `SPI_PHASE_1EDGE` |
| Mode 1 | 0 | 1 | Low | 2nd edge, falling | Rising | `SPI_POLARITY_LOW` + `SPI_PHASE_2EDGE` |
| Mode 2 | 1 | 0 | High | 1st edge, falling | Rising | `SPI_POLARITY_HIGH` + `SPI_PHASE_1EDGE` |
| Mode 3 | 1 | 1 | High | 2nd edge, rising | Falling | `SPI_POLARITY_HIGH` + `SPI_PHASE_2EDGE` |

How to read the table: in the device's timing diagram, first see whether SCK sits high or low before chip select falls; that fixes CPOL. Then see around which SCK edge the data line holds still (that is the sampling edge), and count whether it is the first or second edge after leaving idle; that fixes CPHA. Finally copy the two HAL macros from that row. Master and slave must use the same mode (RM0008 Rev 21 section 25.3.1). If the modes differ, every bit is sampled just as the other side changes it, and the bytes come back shifted by one bit or scrambled.

The W25Q64 supports Mode 0 and Mode 3 (Winbond's W25Q64 datasheet, which is not in this book's source list). Both sample on the rising edge; they differ only in the idle level. This chapter uses Mode 0 throughout. Clear SPE (the SPI enable bit) before changing CPOL or CPHA (RM0008 Rev 21 section 25.3.1).

### 3. Speed and the divider: the BR field and the 18 MHz limit

SPI1 sits on the APB2 bus (RM0008 Rev 21 section 7.3.7: bit 12 of RCC_APB2ENR is SPI1EN), and PCLK2 = 72 MHz in this book's setup. SCK is PCLK2 divided down; the three BR[2:0] bits in CR1 choose the divider, and there are only eight: 2, 4, 8, 16, 32, 64, 128, and 256. There is no ÷3 (RM0008 Rev 21 section 25.5.1):

```text
SCK = PCLK2 ÷ 2^(BR + 1)
BR = 010 (decimal 2): SCK = 72 MHz ÷ 2^3 = 72 MHz ÷ 8 = 9 MHz
```

| BR[2:0] | Divider | SCK at PCLK2 = 72 MHz | Time per bit | Usable? |
| --- | --- | --- | --- | --- |
| 000 | 2 | 36 MHz | About 28 ns | Above the 18 MHz datasheet limit; do not use |
| 001 | 4 | 18 MHz | About 56 ns | Right at the limit; only with short wires and a slave that allows it |
| 010 | 8 | 9 MHz | About 111 ns | This chapter's working point |
| 011 | 16 | 4.5 MHz | About 222 ns | Yes |
| 100 | 32 | 2.25 MHz | About 444 ns | Yes |
| 101 | 64 | 1.125 MHz | About 889 ns | Yes |
| 110 | 128 | 0.5625 MHz | About 1.78 µs | Yes |
| 111 | 256 | 0.28125 MHz | About 3.56 µs | Yes; try this one first when long jumper wires misbehave |

How to read the table: the first two columns are the BR encoding from RM0008 Rev 21 section 25.5.1; 72 divided by the divider gives the SCK in the third column, and "Time per bit" is the reciprocal of SCK. The last column rests on DS5319 Rev 20 Table 43: in master mode SCK is at most 18 MHz. The 36 MHz of `000` is a speed the register accepts and the chip does not guarantee.

Besides the chip's limit, two things cap the speed. One is the slave's own limit; check its datasheet. The other is the wiring: long jumper wires without a ground return next to them blunt the edges and ring, so 9 MHz may work on a breadboard and then drop a bit now and then with another set of wires (rule of thumb). Get it working at a slow setting first, then raise it one step at a time.

### 4. Chip select: NSS management and several slaves

One SPI bus can carry several slaves: they share SCK, MOSI, and MISO, and each slave gets its own chip-select line. The master pulls low the chip select of the slave it wants; slaves that are not selected keep their MISO in high impedance (let go, not driving), so they stay out of the way.

Chip select also brackets a transaction (one complete command plus its data): low marks the start and high marks the end. Many devices act on a command only at the rising edge of chip select; the W25Q64 does this for write enable, page program, and erase (Winbond datasheet). Keep chip select low and the next command is taken as data for the previous one.

The STM32's SPI peripheral has its own NSS pin; for SPI1 it is PA4 by default. The SSM and SSI bits in CR1 and the SSOE bit in CR2 decide how it is used (RM0008 Rev 21 section 25.3.1):

| Setting | What NSS does | Suits |
| --- | --- | --- |
| SSM = 1 (software management) | The NSS pin takes no part; the SSI bit stands in for the internal NSS level, and a master must set SSI to 1 | One master with a plain GPIO as chip select; this chapter uses it |
| SSM = 0, SSOE = 1 | The NSS pin is an output: driven low when the master starts communicating, and kept low until the SPI is disabled (SPE cleared) | A single slave that does not need chip select released between transactions |
| SSM = 0, SSOE = 0 | The NSS pin is an input: when something else pulls it low, the master reports a mode fault (MODF) at once and falls back to slave | Several masters sharing a bus |

How to read the table: the rows get rarer from top to bottom. The "hardware NSS" of the second row looks convenient, but it does not go high on its own after each command. A note in RM0008 Rev 21 section 25.3.3 says that when slaves must be deselected between transmissions, the NSS pin must be configured as a GPIO, or another GPIO must be toggled by software. Every W25Q64 command ends on a chip-select rising edge, so this chapter makes PA4 a push-pull output and drives it low and high in code; in HAL that is `SPI_NSS_SOFT`.

With a software chip select, SSI must be 1. HAL does it for you: the `SPI_MODE_MASTER` macro itself contains both the MSTR and SSI bits, and `SPI_NSS_SOFT` sets SSM (HAL source). If you write the registers yourself and leave out SSI, the internal NSS is low; RM0008 Rev 21 section 25.3.10 says this sets MODF and the hardware clears both SPE and MSTR, so the peripheral sends not a single clock.

Two more points for several slaves. First, drive every chip-select line high before the first SPI transfer. After reset the STM32's GPIOs are floating inputs (RM0008 Rev 21 section 9.1.1), and a floating chip-select pin before initialization may look like a selection to the slave; a 10 kΩ pull-up from each chip-select pin to 3.3 V makes this safer (rule of thumb). Second, at most one chip select may be low at any moment. With two low together, two slaves drive MISO at once, and the line is in contention.

### 5. Full duplex: reading a byte still takes clocks

A slave cannot produce a clock. To read, the master has to produce the clocks itself, and the only way to do that is to write a byte into DR. So on every read the master sends a "dummy byte" (often 0xFF) and takes in the byte the slave sends meanwhile.

Reading the W25Q64 JEDEC ID (command 0x9F) is a 4-byte transaction:

| Byte | Master sends on MOSI | Slave returns on MISO | Stored in |
| --- | --- | --- | --- |
| 1 | 0x9F (the command) | The slave is still taking in the command; nothing valid on MISO | rx[0], discarded |
| 2 | 0xFF (dummy) | 0xEF, the manufacturer id (Winbond) | rx[1] |
| 3 | 0xFF | 0x40, the memory type | rx[2] |
| 4 | 0xFF | 0x17, the capacity: 2^0x17 bytes | rx[3] |

How to read the table: the two bytes in one row are swapped during the same 8 clocks. During the 8 clocks of the command the slave is still receiving it, and whatever is on MISO means nothing, so rx[0] is not the manufacturer id. The three valid bytes start at rx[1], and together they are `rx[1] << 16 | rx[2] << 8 | rx[3]` = 0xEF4017. 0x17 is 23, and 2^23 bytes = 8 MiB, that is 64 Mbit, the 64 in the part number. The meaning of the three bytes comes from Winbond's datasheet, and this repository's spi-flash example also uses them to decide whether the chip is present.

The symmetry hides a trap: while you only send, the receive side keeps receiving. RM0008 Rev 21 section 25.3.5 states that when you only transmit and never read DR, OVR (the overrun flag) is set once the second byte arrives; section 25.3.10 says that after an overrun DR still holds the old byte nobody read, and everything that came after is lost. The next time you really read, the first thing out is "leftovers from the last packet".

The HAL functions each deal with this their own way (STM32CubeF1 HAL source, not in this book's source list):

- `HAL_SPI_TransmitReceive()` sends one byte and receives one, so nothing is left over. Use it to read the ID and the status.
- `HAL_SPI_Transmit()` in two-line mode clears OVR when it finishes, so "Transmit the command and address, then receive the data" works.
- `HAL_SPI_Receive()` in master two-line mode actually calls `HAL_SPI_TransmitReceive()` and sends the receive buffer's existing contents as the dummy bytes. If the buffer holds garbage, garbage goes out on MOSI. The W25Q64 ignores MOSI while it outputs read data, but some devices take it as a command, so this chapter fills the buffer with 0xFF before reading.

A device you only write to, such as a screen, can leave MISO unconnected and needs only `HAL_SPI_Transmit()`.

### 6. Displays and DMA: the ST7789

The ST7789 is a common colour display controller; small modules are usually 240×240 or 240×320. On SPI it only receives. Besides SCK, MOSI, and CS it needs a DC line (Data/Command select): with DC low the byte is a command; with DC high the byte is a parameter of the command or pixel data. DC is this kind of device's own convention and not part of SPI. Modules usually also have RES (reset) and BLK (backlight). Many modules print SCK and MOSI as SCL and SDA, which looks like I2C, but the interface is SPI.

Initialization and drawing use these commands (Sitronix's ST7789 datasheet, not in this book's source list):

| Command | Value | Parameters | Job |
| --- | --- | --- | --- |
| SWRESET | 0x01 | None | Software reset; wait 150 ms afterwards (rule of thumb) |
| SLPOUT | 0x11 | None | Leave sleep; wait 120 ms afterwards (rule of thumb) |
| COLMOD | 0x3A | 0x55 | Pixel format: 16 bits per pixel, RGB565 |
| MADCTL | 0x36 | 0x00 | Scan direction and red/blue order |
| INVON | 0x21 | None | Display inversion; most IPS modules need it for correct colours (rule of thumb) |
| CASET, RASET | 0x2A, 0x2B | Start and end, 2 bytes each | Set the column range and row range to write |
| RAMWR | 0x2C | Pixel data | Write pixels into the window just set |
| DISPON | 0x29 | None | Turn the display on |

How to read the table: for initialization send the rows top to bottom, skipping CASET, RASET, and RAMWR; after that, for each area you draw, send CASET, RASET, and RAMWR, followed by the pixel data.

How much data a full screen is: 240 × 240 pixels at 2 bytes each is 115 200 bytes, or 921 600 bits.

```text
SCK = 9 MHz:  921 600 ÷ 9 000 000  = 0.1024 s, about 102 ms per frame, at most about 9.8 frames per second
SCK = 18 MHz: 921 600 ÷ 18 000 000 = 0.0512 s, about 51 ms per frame, at most about 19.5 frames per second
```

That is the floor with the line never pausing; in practice it is only slower.

Sending that many bytes with the blocking `HAL_SPI_Transmit()` keeps the CPU waiting in place for those 100 ms. DMA (Direct Memory Access, covered in chapter 10) can move the data instead: each time the SPI empties its transmit buffer, TXE (transmit buffer empty) goes to 1 and the SPI asks the DMA for the next byte, which the DMA fetches from memory and writes into DR. SPI1's transmit request goes to DMA1 channel 3 and its receive request to channel 2 (RM0008 Rev 21 Table 78).

However fast the DMA is, the pixels need memory to sit in first. The STM32F103C8T6 has only 20 KB of SRAM in total (DS5319 Rev 20, front page), which cannot hold a 115 200-byte frame. The answer is to send it in pieces: allocate a 10-line buffer (240 × 2 × 10 = 4800 bytes), fill it with the colour, and send it 24 times; when drawing an image, the CPU can also fill the next piece while the DMA sends this one.

The DMA's "transfer complete" only says the last byte has been handed to the SPI; it may still be on its way out of the shift register. RM0008 Rev 21 section 25.3.9 requires waiting for BSY (the busy flag) to clear before disabling the SPI, and raising chip select should wait for that too. HAL waits for it before it calls the transmit-complete callback (STM32CubeF1 HAL source). A transmit-only DMA also sets OVR (section 25.3.9), and HAL clears it at the end as well.

### 7. Bit-banged SPI versus hardware SPI

Toggling SCK, writing MOSI, and reading MISO one bit at a time on plain GPIOs also gives you SPI; this is bit-banging. It works on any pins and any mode, but the CPU limits its speed, and the CPU can do nothing else while it toggles.

| Aspect | Bit-banged | Hardware SPI1 |
| --- | --- | --- |
| Speed | Limited by the CPU and the GPIOs; toggling with HAL calls gives roughly a few hundred kHz to 1 MHz (rule of thumb; measure with a logic analyzer) | Up to 18 MHz (DS5319 Rev 20 Table 43); this chapter uses 9 MHz |
| CPU load | Fully busy for the whole transfer | Blocking calls still wait; with DMA almost none |
| Pins | Any GPIO | PA5, PA6, PA7, or PB3, PB4, PB5 after the remap |
| DMA | Not possible | DMA1 channel 3 to send, channel 2 to receive |
| Changing mode | Edit the code | Change the CPOL and CPHA bits, clearing SPE first |

How to read the table: use bit-banging when pins clash, when a slave has unusual timing, and when speed does not matter; use the hardware SPI everywhere else.

### 8. SPI, I2C, and UART side by side

| Aspect | SPI | I2C (chapter 07) | UART (chapter 06) |
| --- | --- | --- | --- |
| Signal wires | SCK, MOSI, MISO, and one CS per slave | SCL, SDA | TX, RX |
| Clock line | Yes, from the master | Yes, from the master | No; both sides agree on a baud rate |
| Who is addressed | A chip-select line | An address byte | Point to point, nothing to select |
| Acknowledge | None | The 9th clock of every byte | None |
| Duplex | Full duplex | Half duplex | Full duplex |
| This book's working point | 9 MHz | 400 kHz | 115200 bit/s |

How to read the table: all three also need a shared GND, which the table leaves out. For speed with few devices use SPI; to save wires with many devices use I2C; to talk to a PC or another board use UART.

## Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill | SPI1_SCK | PA5 (LQFP48 pin 15) | Alternate-function push-pull output |
| BluePill | SPI1_MISO | PA6 (pin 16) | Floating input |
| BluePill | SPI1_MOSI | PA7 (pin 17) | Alternate-function push-pull output |
| BluePill | W25Q64 chip select | PA4 (pin 14) | Push-pull output, software controlled, idles high |
| W25Q64 module | CS, CLK, DO, DI | To PA4, PA5, PA6, PA7 in that order | VCC to 3.3 V; /WP and /HOLD to 3.3 V (many modules already tie them on the board) |
| ST7789 module | CS, DC, RES | PB0 (pin 18), PA3 (pin 13), PA2 (pin 12) | Example setting; BLK to 3.3 V |
| ST7789 module | SCL, SDA | PA5, PA7 | Really SCK and MOSI; write-only, MISO not connected |

The pin numbers come from DS5319 Rev 20 Table 5, and the GPIO configurations of SCK, MOSI, and MISO from RM0008 Rev 21 Table 25 (a full-duplex master's MISO is a floating input or an input with pull-up). Which pins the screen's CS, DC, and RES use is this book's example setting; any other free GPIO works.

```text
BluePill                    W25Q64 module         ST7789 module
PA4 (pin 14) ─────────────── CS
PB0 (pin 18) ──────────────────────────────────── CS
PA3 (pin 13) ──────────────────────────────────── DC
PA2 (pin 12) ──────────────────────────────────── RES
PA5 (pin 15) ── SCK ──────── CLK ──────────────── SCL
PA7 (pin 17) ── MOSI ─────── DI ───────────────── SDA
PA6 (pin 16) ── MISO ─────── DO
3.3V ─────────────────────── VCC, /WP, /HOLD ──── VCC, BLK
GND ──────────────────────── GND ──────────────── GND
```

When wiring, watch this: the two slaves need separate chip-select lines, with at most one low at any time; the W25Q64 module's DO goes to PA6 and DI to PA7, "slave out to master in", not crossed the way you would wire a UART.

## Code

The first program uses the hardware SPI1 to read the W25Q64 JEDEC ID, then erases one sector, writes 16 bytes, and reads them back to compare. There is no serial output; the results sit in global variables for the debugger.

```c
/* spi_flash.c: SPI1 Mode 0 at 9 MHz reads and writes a W25Q64 (HAL, STM32F103C8T6) */
#include <string.h>
#include "stm32f1xx_hal.h"

#define FLASH_CS_PORT       GPIOA
#define FLASH_CS_PIN        GPIO_PIN_4      /* pin 14, push-pull output as chip select */

#define CMD_WRITE_ENABLE    0x06U
#define CMD_READ_STATUS1    0x05U
#define CMD_PAGE_PROGRAM    0x02U
#define CMD_READ_DATA       0x03U
#define CMD_SECTOR_ERASE    0x20U           /* erase one 4 KB sector */
#define CMD_JEDEC_ID        0x9FU

#define STATUS_BUSY         0x01U           /* bit 0 of the W25Q64 status register 1 */
#define W25Q_PAGE_SIZE      256U
#define W25Q64_JEDEC_ID     0xEF4017UL

#define SPI_TIMEOUT_MS      100U
#define PROGRAM_TIMEOUT_MS  10U             /* page program takes at most about 3 ms; margin added */
#define ERASE_TIMEOUT_MS    1000U           /* sector erase takes at most about 400 ms; margin added */

#define TEST_ADDR           0x000000UL
#define TEST_LEN            16U

SPI_HandleTypeDef hspi1;

volatile uint32_t g_jedec_id;               /* in the debugger: should be 0xEF4017 */
volatile HAL_StatusTypeDef g_flash_status = HAL_ERROR;
volatile uint8_t g_verify_ok;               /* 1 means the read-back matches what was written */

static uint8_t s_tx[TEST_LEN];
static uint8_t s_rx[TEST_LEN];

void SystemClock_Config(void);
void error_handler(void);

static void cs_low(void)  { HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_RESET); }
static void cs_high(void) { HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_SET); }

void spi1_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_SPI1_CLK_ENABLE();

    /* Set the chip-select output high first, then make the pin an output,
       so the slave is never selected by the configuration itself */
    HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_SET);
    io.Pin   = FLASH_CS_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(FLASH_CS_PORT, &io);

    io.Pin  = GPIO_PIN_5 | GPIO_PIN_7;      /* SCK, MOSI: alternate-function push-pull */
    io.Mode = GPIO_MODE_AF_PP;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = GPIO_PIN_6;                   /* MISO: floating input */
    io.Mode = GPIO_MODE_INPUT;
    HAL_GPIO_Init(GPIOA, &io);

    hspi1.Instance               = SPI1;
    hspi1.Init.Mode              = SPI_MODE_MASTER;
    hspi1.Init.Direction         = SPI_DIRECTION_2LINES;     /* full duplex */
    hspi1.Init.DataSize          = SPI_DATASIZE_8BIT;
    hspi1.Init.CLKPolarity       = SPI_POLARITY_LOW;         /* CPOL = 0 */
    hspi1.Init.CLKPhase          = SPI_PHASE_1EDGE;          /* CPHA = 0, together Mode 0 */
    hspi1.Init.NSS               = SPI_NSS_SOFT;             /* chip select is PA4, driven in software */
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_8;  /* 72 MHz ÷ 8 = 9 MHz */
    hspi1.Init.FirstBit          = SPI_FIRSTBIT_MSB;
    hspi1.Init.TIMode            = SPI_TIMODE_DISABLE;
    hspi1.Init.CRCCalculation    = SPI_CRCCALCULATION_DISABLE;
    hspi1.Init.CRCPolynomial     = 7U;                       /* CRC unused; 7 is the CRCPR reset value */
    if (HAL_SPI_Init(&hspi1) != HAL_OK)
    {
        error_handler();
    }
}

uint32_t w25q_read_id(void)
{
    uint8_t tx[4] = {CMD_JEDEC_ID, 0xFF, 0xFF, 0xFF};
    uint8_t rx[4] = {0};
    HAL_StatusTypeDef st;

    cs_low();
    st = HAL_SPI_TransmitReceive(&hspi1, tx, rx, 4, SPI_TIMEOUT_MS);
    cs_high();
    if (st != HAL_OK)
    {
        return 0;
    }
    /* rx[0] shifted in while 0x9F shifted out; it is not the manufacturer id */
    return ((uint32_t)rx[1] << 16) | ((uint32_t)rx[2] << 8) | rx[3];
}

static HAL_StatusTypeDef w25q_write_enable(void)
{
    uint8_t cmd = CMD_WRITE_ENABLE;
    HAL_StatusTypeDef st;

    cs_low();
    st = HAL_SPI_Transmit(&hspi1, &cmd, 1, SPI_TIMEOUT_MS);
    cs_high();                              /* write enable takes effect on the chip-select rising edge */
    return st;
}

static HAL_StatusTypeDef w25q_wait_busy(uint32_t timeout_ms)
{
    uint8_t tx[2] = {CMD_READ_STATUS1, 0xFF};
    uint8_t rx[2];
    uint32_t start = HAL_GetTick();

    for (;;)
    {
        HAL_StatusTypeDef st;

        cs_low();
        st = HAL_SPI_TransmitReceive(&hspi1, tx, rx, 2, SPI_TIMEOUT_MS);
        cs_high();
        if (st != HAL_OK)
        {
            return st;
        }
        if ((rx[1] & STATUS_BUSY) == 0U)    /* rx[1] is the status byte */
        {
            return HAL_OK;
        }
        if ((HAL_GetTick() - start) > timeout_ms)
        {
            return HAL_TIMEOUT;
        }
    }
}

static void put_cmd_addr(uint8_t *buf, uint8_t cmd, uint32_t addr)
{
    buf[0] = cmd;
    buf[1] = (uint8_t)(addr >> 16);         /* 24-bit address, high byte first */
    buf[2] = (uint8_t)(addr >> 8);
    buf[3] = (uint8_t)addr;
}

HAL_StatusTypeDef w25q_erase_sector(uint32_t addr)
{
    uint8_t hdr[4];
    HAL_StatusTypeDef st = w25q_write_enable();

    if (st != HAL_OK)
    {
        return st;
    }
    put_cmd_addr(hdr, CMD_SECTOR_ERASE, addr);
    cs_low();
    st = HAL_SPI_Transmit(&hspi1, hdr, 4, SPI_TIMEOUT_MS);
    cs_high();                              /* chip-select rising edge starts the erase */
    if (st != HAL_OK)
    {
        return st;
    }
    return w25q_wait_busy(ERASE_TIMEOUT_MS);
}

HAL_StatusTypeDef w25q_write(uint32_t addr, const uint8_t *data, uint32_t len)
{
    while (len > 0U)
    {
        uint8_t hdr[4];
        uint32_t room = W25Q_PAGE_SIZE - (addr % W25Q_PAGE_SIZE);   /* bytes left in this page */
        uint32_t n = (len < room) ? len : room;
        HAL_StatusTypeDef st = w25q_write_enable();

        if (st != HAL_OK)
        {
            return st;
        }
        put_cmd_addr(hdr, CMD_PAGE_PROGRAM, addr);
        cs_low();
        st = HAL_SPI_Transmit(&hspi1, hdr, 4, SPI_TIMEOUT_MS);
        if (st == HAL_OK)
        {
            st = HAL_SPI_Transmit(&hspi1, (uint8_t *)data, (uint16_t)n, SPI_TIMEOUT_MS);
        }
        cs_high();                          /* chip-select rising edge starts programming */
        if (st != HAL_OK)
        {
            return st;
        }
        st = w25q_wait_busy(PROGRAM_TIMEOUT_MS);
        if (st != HAL_OK)
        {
            return st;
        }
        addr += n;
        data += n;
        len  -= n;
    }
    return HAL_OK;
}

HAL_StatusTypeDef w25q_read(uint32_t addr, uint8_t *data, uint16_t len)
{
    uint8_t hdr[4];
    HAL_StatusTypeDef st;

    put_cmd_addr(hdr, CMD_READ_DATA, addr);
    memset(data, 0xFF, len);                /* HAL_SPI_Receive sends the buffer's contents as dummy bytes */
    cs_low();
    st = HAL_SPI_Transmit(&hspi1, hdr, 4, SPI_TIMEOUT_MS);
    if (st == HAL_OK)
    {
        st = HAL_SPI_Receive(&hspi1, data, len, SPI_TIMEOUT_MS);
    }
    cs_high();
    return st;
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    spi1_init();

    g_jedec_id = w25q_read_id();
    if (g_jedec_id == W25Q64_JEDEC_ID)
    {
        for (uint32_t i = 0; i < TEST_LEN; i++)
        {
            s_tx[i] = (uint8_t)(0xA0U + i);
        }
        g_flash_status = w25q_erase_sector(TEST_ADDR);
        if (g_flash_status == HAL_OK)
        {
            g_flash_status = w25q_write(TEST_ADDR, s_tx, TEST_LEN);
        }
        if (g_flash_status == HAL_OK)
        {
            g_flash_status = w25q_read(TEST_ADDR, s_rx, TEST_LEN);
        }
        g_verify_ok = (g_flash_status == HAL_OK) && (memcmp(s_tx, s_rx, TEST_LEN) == 0);
    }

    while (1)
    {
    }
}

/* HSE 8 MHz × 9 = 72 MHz; APB2 is not divided, and SPI1 runs from it */
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();
    }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;   /* HCLK  = 72 MHz */
    clk.APB1CLKDivider = RCC_HCLK_DIV2;     /* PCLK1 = 36 MHz */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;     /* PCLK2 = 72 MHz: SPI1, GPIOA */
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();
    }
}

void error_handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}
```

Piece by piece:

- `spi1_init()` writes PA4 high before making it a push-pull output, so the chip select reads "not selected" from the first moment. SCK and MOSI are alternate-function push-pull and MISO is a floating input, which is the configuration RM0008 Rev 21 Table 25 gives for a full-duplex master.
- With `SPI_MODE_MASTER`, `SPI_NSS_SOFT`, and `SPI_BAUDRATEPRESCALER_8`, CR1 is 0x0314 after `HAL_SPI_Init()`: MSTR, SSI, and SSM set, BR = 010 (lab 3 checks this in the debugger). HAL has not set SPE yet; it enables the SPI on the first transfer (HAL source).
- `w25q_read_id()` sends 4 bytes and receives 4 in one call, and assembles the result starting at rx[1]. At 9 MHz the 32 clocks take about 3.6 µs.
- Write enable, sector erase, and page program all take effect at `cs_high()` (Winbond datasheet). The chip clears write enable by itself after each erase or program, so 0x06 goes out again before every erase or write.
- `w25q_wait_busy()` keeps sending 0x05 to read status register 1 until bit 0 (BUSY) is back to 0. That BUSY belongs to the W25Q64 and means the chip is still erasing or programming inside; BSY in the SPI peripheral's SR is bit 7 and only says the STM32 side is still shifting (RM0008 Rev 21 section 25.3.7). The two "busy" flags are different things.
- Flash bits can only be programmed from 1 to 0, and an erase returns a whole 4 KB sector to 0xFF (Winbond datasheet), so erase comes before write. The timeouts leave margin over the datasheet maximums: about 3 ms for a page program and about 400 ms for a sector erase.
- `w25q_write()` splits the data by page: `room` is the number of bytes left in the current page, and one command writes at most to the end of the page. When a page program runs past the end of the page, the extra bytes wrap to the start of the same page and overwrite what is there (Winbond datasheet).
- `w25q_read()` fills the buffer with 0xFF first, for the reason in section 5: `HAL_SPI_Receive()` sends it out unchanged as the dummy bytes.
- To read or write more data, change only `TEST_LEN` and the buffers; the length of `w25q_read()` is 16 bits, so at most 65 535 bytes per call.

The second piece of code fills an ST7789 screen with DMA. It goes in another file of the same project; it shares `hspi1`, SCK, and MOSI with the W25Q64, and each device has its own chip select.

```c
/* st7789_dma.c: SPI1 plus DMA1 channel 3 fill a 240×240 ST7789 screen (HAL)
 * Same project as spi_flash.c: in main(), call lcd_init() after spi1_init(),
 * then call lcd_fill_dma(). */
#include <stddef.h>
#include "stm32f1xx_hal.h"

#define LCD_CS_PORT     GPIOB
#define LCD_CS_PIN      GPIO_PIN_0              /* example setting, pin 18 */
#define LCD_DC_PORT     GPIOA
#define LCD_DC_PIN      GPIO_PIN_3              /* example setting, pin 13: low = command, high = data */
#define LCD_RST_PORT    GPIOA
#define LCD_RST_PIN     GPIO_PIN_2              /* example setting, pin 12 */

#define LCD_W           240U
#define LCD_H           240U
#define CHUNK_LINES     10U
#define CHUNK_BYTES     (LCD_W * 2U * CHUNK_LINES)   /* 4800 bytes */

extern SPI_HandleTypeDef hspi1;                 /* defined and initialized in spi_flash.c */
void error_handler(void);

DMA_HandleTypeDef hdma_spi1_tx;
volatile uint32_t g_idle_loops;                 /* how many loops the CPU spun while the DMA sent */

static uint8_t s_chunk[CHUNK_BYTES];
static volatile uint8_t s_dma_busy;
static volatile uint8_t s_dma_error;

/* Send a command and its parameters. The screen never answers, so a bad
   transfer cannot be read back; the return values are not checked here */
static void lcd_cmd(uint8_t cmd, const uint8_t *param, uint16_t n)
{
    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_RESET);       /* command */
    (void)HAL_SPI_Transmit(&hspi1, &cmd, 1, 100);
    if (n > 0U)
    {
        HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_SET);     /* parameters */
        (void)HAL_SPI_Transmit(&hspi1, (uint8_t *)param, n, 100);
    }
    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_SET);
}

void lcd_init(void)
{
    static const uint8_t colmod = 0x55;         /* 16 bits per pixel, RGB565 */
    static const uint8_t madctl = 0x00;
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();

    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_SET);         /* chip select high first */
    HAL_GPIO_WritePin(LCD_RST_PORT, LCD_RST_PIN, GPIO_PIN_SET);
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    io.Pin   = LCD_CS_PIN;
    HAL_GPIO_Init(LCD_CS_PORT, &io);
    io.Pin   = LCD_DC_PIN | LCD_RST_PIN;
    HAL_GPIO_Init(GPIOA, &io);

    /* SPI1_TX is on DMA1 channel 3 (RM0008 Table 78): memory to peripheral,
       memory address incrementing, one byte at a time */
    hdma_spi1_tx.Instance                 = DMA1_Channel3;
    hdma_spi1_tx.Init.Direction           = DMA_MEMORY_TO_PERIPH;
    hdma_spi1_tx.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_spi1_tx.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_spi1_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_spi1_tx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_spi1_tx.Init.Mode                = DMA_NORMAL;
    hdma_spi1_tx.Init.Priority            = DMA_PRIORITY_LOW;
    if (HAL_DMA_Init(&hdma_spi1_tx) != HAL_OK)
    {
        error_handler();
    }
    __HAL_LINKDMA(&hspi1, hdmatx, hdma_spi1_tx);
    HAL_NVIC_SetPriority(DMA1_Channel3_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel3_IRQn);

    HAL_GPIO_WritePin(LCD_RST_PORT, LCD_RST_PIN, GPIO_PIN_RESET);     /* hardware reset */
    HAL_Delay(10);
    HAL_GPIO_WritePin(LCD_RST_PORT, LCD_RST_PIN, GPIO_PIN_SET);
    HAL_Delay(120);

    lcd_cmd(0x01, NULL, 0);                     /* SWRESET */
    HAL_Delay(150);
    lcd_cmd(0x11, NULL, 0);                     /* SLPOUT */
    HAL_Delay(120);
    lcd_cmd(0x3A, &colmod, 1);                  /* COLMOD */
    lcd_cmd(0x36, &madctl, 1);                  /* MADCTL */
    lcd_cmd(0x21, NULL, 0);                     /* INVON: most IPS modules need it */
    lcd_cmd(0x29, NULL, 0);                     /* DISPON */
}

void DMA1_Channel3_IRQHandler(void)
{
    HAL_DMA_IRQHandler(&hdma_spi1_tx);
}

void HAL_SPI_TxCpltCallback(SPI_HandleTypeDef *hspi)
{
    if (hspi == &hspi1)
    {
        s_dma_busy = 0;                         /* HAL waited for BSY = 0 before calling us */
    }
}

void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi)
{
    if (hspi == &hspi1)
    {
        s_dma_error = 1;
        s_dma_busy = 0;
    }
}

HAL_StatusTypeDef lcd_fill_dma(uint16_t rgb565)
{
    uint8_t win[4] = {0, 0, (uint8_t)((LCD_W - 1U) >> 8), (uint8_t)(LCD_W - 1U)};
    uint8_t ramwr = 0x2C;
    HAL_StatusTypeDef st;

    for (uint32_t i = 0; i < CHUNK_BYTES; i += 2U)
    {
        s_chunk[i]      = (uint8_t)(rgb565 >> 8);   /* high byte first */
        s_chunk[i + 1U] = (uint8_t)rgb565;
    }

    lcd_cmd(0x2A, win, 4);                      /* CASET: columns 0 to 239 */
    win[2] = (uint8_t)((LCD_H - 1U) >> 8);
    win[3] = (uint8_t)(LCD_H - 1U);
    lcd_cmd(0x2B, win, 4);                      /* RASET: rows 0 to 239 */

    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_RESET);
    st = HAL_SPI_Transmit(&hspi1, &ramwr, 1, 100);                     /* RAMWR */
    HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_SET);         /* pixels from here on */

    s_dma_error = 0;
    for (uint32_t row = 0; (row < LCD_H) && (st == HAL_OK); row += CHUNK_LINES)
    {
        s_dma_busy = 1;
        st = HAL_SPI_Transmit_DMA(&hspi1, s_chunk, CHUNK_BYTES);
        while ((st == HAL_OK) && (s_dma_busy != 0U))
        {
            g_idle_loops++;                     /* the CPU is free to do other work here */
        }
        if (s_dma_error != 0U)
        {
            st = HAL_ERROR;
        }
    }
    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_SET);
    return st;
}
```

Piece by piece:

- The screen's chip select PB0 and the flash's chip select PA4 are separate; SCK and MOSI are shared. The first thing `lcd_init()` does is drive PB0 high, before any SPI transfer.
- When to change DC: `HAL_SPI_Transmit()` returns only after the last bit has shifted out and BSY has cleared (HAL source), so toggling DC between two calls is safe; DC stays high for the whole DMA transfer.
- The DMA uses channel 3 according to RM0008 Rev 21 Table 78. `__HAL_LINKDMA` attaches the DMA handle to `hspi1`, which is how `HAL_SPI_Transmit_DMA()` knows which channel to use. The handler name `DMA1_Channel3_IRQHandler` must match the startup file exactly; misspell it and the DMA-complete interrupt never arrives, and the program sticks in the wait loop.
- One piece is 4800 bytes, and 24 pieces make exactly 240 lines. While each piece's DMA runs, `g_idle_loops` keeps climbing, which shows the CPU is free; switch to a blocking send and the number stops growing.
- After RAMWR the chip select stays low; all 24 pieces of pixels count as data for that one command, and chip select goes high only when they are all sent.
- The delays and the INVON and MADCTL values are rules of thumb for common modules; when colours or orientation are wrong, the initialization sequence from the module's seller wins.

The third piece of code does the same Mode 0 with GPIOs. It uses the same pins as the hardware SPI1, so the two cannot run at the same time; to use both, move this one to a few free pins.

```c
/* soft_spi.c: an SPI master bit-banged on GPIOs, Mode 0, MSB first
 * SCK = PA5, MOSI = PA7, MISO = PA6, CS = PA4 */
#include "stm32f1xx_hal.h"

#define SSPI_PORT           GPIOA
#define SSPI_CS             GPIO_PIN_4
#define SSPI_SCK            GPIO_PIN_5
#define SSPI_MISO           GPIO_PIN_6
#define SSPI_MOSI           GPIO_PIN_7
#define SSPI_DELAY_LOOPS    5U              /* rule of thumb: sets the speed; measure with a logic analyzer */

static void sspi_delay(void)
{
    for (volatile uint32_t i = 0; i < SSPI_DELAY_LOOPS; i++)
    {
    }
}

void soft_spi_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    HAL_GPIO_WritePin(SSPI_PORT, SSPI_CS, GPIO_PIN_SET);      /* chip select idles high */
    HAL_GPIO_WritePin(SSPI_PORT, SSPI_SCK, GPIO_PIN_RESET);   /* Mode 0: SCK idles low */
    io.Pin   = SSPI_CS | SSPI_SCK | SSPI_MOSI;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(SSPI_PORT, &io);
    io.Pin  = SSPI_MISO;
    io.Mode = GPIO_MODE_INPUT;
    HAL_GPIO_Init(SSPI_PORT, &io);
}

uint8_t soft_spi_xfer(uint8_t tx)
{
    uint8_t rx = 0;

    for (int i = 7; i >= 0; i--)
    {
        /* put this bit in place while SCK is low */
        HAL_GPIO_WritePin(SSPI_PORT, SSPI_MOSI, ((tx >> i) & 1U) ? GPIO_PIN_SET : GPIO_PIN_RESET);
        sspi_delay();
        HAL_GPIO_WritePin(SSPI_PORT, SSPI_SCK, GPIO_PIN_SET);     /* rising edge: both sides sample */
        rx = (uint8_t)((rx << 1) | (HAL_GPIO_ReadPin(SSPI_PORT, SSPI_MISO) == GPIO_PIN_SET));
        sspi_delay();
        HAL_GPIO_WritePin(SSPI_PORT, SSPI_SCK, GPIO_PIN_RESET);   /* falling edge: the slave changes to the next bit */
    }
    return rx;
}

uint32_t soft_spi_read_id(void)
{
    uint32_t id;

    HAL_GPIO_WritePin(SSPI_PORT, SSPI_CS, GPIO_PIN_RESET);
    (void)soft_spi_xfer(0x9F);              /* the byte received meanwhile is thrown away */
    id  = (uint32_t)soft_spi_xfer(0xFF) << 16;
    id |= (uint32_t)soft_spi_xfer(0xFF) << 8;
    id |= soft_spi_xfer(0xFF);
    HAL_GPIO_WritePin(SSPI_PORT, SSPI_CS, GPIO_PIN_SET);
    return id;
}
```

Piece by piece:

- The Mode 0 rules become three steps in code: while SCK is low, put the bit on MOSI; raise SCK, both sides sample on this rising edge, and the master reads MISO right then; lower SCK, and the slave puts its next bit on MISO on this falling edge.
- After chip select falls and before the first rising edge, the slave already has its top bit on MISO, so the first bit is not lost.
- `SSPI_DELAY_LOOPS` sets the speed. One pass of the empty loop takes a few clock cycles and changes with the compiler's optimization level, so 5 is only a rule of thumb. When `soft_spi_read_id()` returns 0xEF4017 the timing is right, and you can compare it with the hardware SPI result.

Register version: the same SPI1, Mode 0, ÷8, to see which bits HAL wrote for you, and then a JEDEC ID read by hand.

```c
/* Register version: SPI1 Mode 0 at 9 MHz reads the JEDEC ID. For teaching; no timeouts */
static uint8_t spi1_xfer(uint8_t b)
{
    while ((SPI1->SR & SPI_SR_TXE) == 0U) { }      /* write only when the transmit buffer is empty */
    SPI1->DR = b;                                   /* writing DR starts the shifting */
    while ((SPI1->SR & SPI_SR_RXNE) == 0U) { }     /* after 8 clocks a whole byte has arrived */
    return (uint8_t)SPI1->DR;                       /* reading DR also clears RXNE */
}

uint32_t spi1_reg_read_id(void)
{
    uint32_t id;

    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_SPI1EN;
    GPIOA->BSRR = GPIO_BSRR_BS4;                    /* chip-select output high first */
    /* CRL has 4 bits per pin: PA4 = 0x3 push-pull output 50 MHz, PA5 = 0xB AF push-pull,
       PA6 = 0x4 floating input, PA7 = 0xB AF push-pull */
    GPIOA->CRL = (GPIOA->CRL & ~0xFFFF0000UL) | 0xB4B30000UL;

    SPI1->CR1 = SPI_CR1_MSTR | SPI_CR1_SSM | SPI_CR1_SSI | SPI_CR1_BR_1;  /* 0x0314: BR = 010, CPOL = CPHA = 0 */
    SPI1->CR1 |= SPI_CR1_SPE;                                              /* 0x0354 */

    GPIOA->BSRR = GPIO_BSRR_BR4;                    /* chip select low */
    (void)spi1_xfer(0x9F);
    id  = (uint32_t)spi1_xfer(0xFF) << 16;
    id |= (uint32_t)spi1_xfer(0xFF) << 8;
    id |= spi1_xfer(0xFF);
    while ((SPI1->SR & SPI_SR_BSY) != 0U) { }      /* the last bit has really shifted out */
    GPIOA->BSRR = GPIO_BSRR_BS4;                    /* chip select high */
    return id;
}
```

`CRL` covers PA0 to PA7 with 4 bits per pin (the two MODE bits low, the two CNF bits high); PA4 is bits 19:16 and PA7 is bits 31:28. The upper 16 bits are written as 0xB4B3, which from PA7 down to PA4 is 0xB, 0x4, 0xB, 0x3. The positions of the CR1 bits are in RM0008 Rev 21 section 25.5.1: CPHA is bit 0, CPOL bit 1, MSTR bit 2, BR bits 5:3, SPE bit 6, SSI bit 8, and SSM bit 9. Leave out `SPI_CR1_SSI` and the moment SPE is set you get MODF (section 4). The send-and-receive order follows section 25.3.5: wait for TXE, write DR, wait for RXNE, read DR; after the last byte is read, wait for BSY to clear (the closing step of section 25.3.5), and only then raise chip select. RM0008 Rev 21 section 25.3.7 also warns to judge each byte by TXE and RXNE and not to wait on BSY byte by byte.

The full project is in [`examples/spi-flash/`](../../examples/spi-flash/). It calls `HAL_SPI_TransmitReceive()` one byte at a time, writes 300 bytes in one go across a page boundary, and lights the LED on PC13 when the read-back matches. Inside `while (1)` it erases and rewrites sector 0 once a second; a W25Q64 sector is rated for 100 000 erase cycles (Winbond datasheet), so left running like this it reaches that in a little over a day. Power it off once you have seen the result, or change it to run once. It also configures MISO as alternate-function push-pull; RM0008 Rev 21 Table 25 recommends a floating input or an input with pull-up for a full-duplex master's MISO, and this chapter follows Table 25.

## Hands-on labs

1. **Lab 1: read the JEDEC ID.** Connect only the W25Q64 module, load the first program, and set a breakpoint on the line after `g_jedec_id = w25q_read_id();`.
   - Expected: in the debugger `g_jedec_id` is 0xEF4017.
   - How to check: put a logic analyzer on PA4, PA5, PA6, and PA7 with SPI Mode 0 decoding. While PA4 is low there are exactly 32 clocks; MOSI carries 9F FF FF FF, and bytes 2 to 4 on MISO are EF 40 17; one SCK period is about 111 ns, that is 9 MHz. The analyzer's sample rate should be at least 4 times SCK (rule of thumb), so at least 36 MHz to see 9 MHz; if yours is slower, set BR to a slow setting first.
   - If it fails, check first: 0xFFFFFF usually means MISO is not connected, the module has no power, or DO and DI are swapped (DO goes to PA6, DI to PA7); 0x000000, or a different value every time, means check that the two boards share ground and that /HOLD is tied to 3.3 V (with /HOLD low the chip pauses and does not drive DO, Winbond datasheet); a value that looks like the right one shifted by a bit means check that the mode is Mode 0.
2. **Lab 2: erase, write, read back.** Remove the breakpoint and let the program run to `while (1)`.
   - Expected: `g_flash_status` is `HAL_OK`, `g_verify_ok` is 1, and `s_rx` holds 0xA0 to 0xAF.
   - How to check: on the logic analyzer you see, in order, 06 (write enable), 20 00 00 00 (sector erase), a long run of 05 FF (the busy wait; bit 0 of the status byte stays 1 during the erase, typically for tens of milliseconds, rule of thumb), 06, 02 00 00 00 plus 16 bytes (page program), a few runs of 05 FF, and finally 03 00 00 00 plus 16 bytes (the read). In `w25q_write()`, replace `w25q_write_enable()` with `HAL_OK` and run again: the chip ignores the page program command, the read-back is all 0xFF, and `g_verify_ok` becomes 0.
   - If it fails, check first: if `g_flash_status` is `HAL_TIMEOUT`, see whether the status byte read by command 05 stays at 1; if the read-back differs from the written data in only a few bits, the sector was most likely written without an erase (programming can only turn 1 into 0).
3. **Lab 3: check BR and SCK, then light up the screen.** Set one breakpoint after `spi1_init()` and one after `w25q_read_id()`, and look at SPI1's CR1 in the debugger; then connect the ST7789 module and add `lcd_init();` and `lcd_fill_dma(0xF800);` after `spi1_init();` in `main()`.
   - Expected: CR1 is 0x0314 at the first breakpoint and 0x0354 at the second; the extra 0x0040 is SPE. Change `SPI_BAUDRATEPRESCALER_8` to `SPI_BAUDRATEPRESCALER_4`: the BR field of CR1 becomes 001, SCK becomes 18 MHz, and the ID still reads correctly. The whole screen turns red (0xF800 is red in RGB565).
   - How to check: measure SCK with the logic analyzer: about 111 ns per period at 9 MHz, about 56 ns at 18 MHz. The screen's PB0 is low for about 102 ms during the fill (9 MHz). Replace `HAL_SPI_Transmit_DMA()` in `lcd_fill_dma()` with the blocking `HAL_SPI_Transmit(&hspi1, s_chunk, CHUNK_BYTES, 1000)`: PB0 stays low for about as long, but `g_idle_loops` no longer grows. The line is just as fast; the difference is whether the CPU is free. Do not try `SPI_BAUDRATEPRESCALER_2`: the 36 MHz of BR = 000 is above the 18 MHz limit in DS5319 Rev 20 Table 43, and an occasional correct read proves nothing.
   - If it fails, check first: if SPE and MSTR in CR1 have both become 0, look at the MODF bit in SR (section 4); if the SCK period is not 111 ns, check first that PCLK2 is 72 MHz. If the screen stays black, check BLK and RES; if red shows as cyan, change 0x21 to 0x20 (INVOFF); if the program sticks in `lcd_fill_dma()`, check the name of `DMA1_Channel3_IRQHandler` and that its NVIC interrupt is enabled.

## Self-test

1. A sensor's datasheet says: SCK is high before chip select falls, and data is sampled on the falling edge of SCK. Which mode does it need? What go into HAL's `CLKPolarity` and `CLKPhase`?
2. A slave can run at 10 MHz at most. On SPI1 (PCLK2 = 72 MHz), what do you put in BR, and what is SCK? What about on SPI2 (on APB1, PCLK1 = 36 MHz)?
3. Reading the JEDEC ID returns rx[] = {0xFF, 0xEF, 0x40, 0x17}. Why does the first byte not count? What capacity does 0x17 stand for?
4. You want to write 16 bytes starting at address 0x0000F8. How many page program commands do you send, and at which address and with how many bytes does each start? What happens if you send all 16 bytes in one command?
5. For a 240×240 RGB565 screen at SCK = 18 MHz, what is the least time a full-screen refresh takes? Why can you not allocate a whole-frame buffer on an STM32F103C8T6 and send it with one DMA transfer?

Answers:

1. It idles high, so CPOL = 1; starting from high, the first edge is the falling edge, and sampling on the first edge means CPHA = 0. That is Mode 2: `SPI_POLARITY_HIGH` and `SPI_PHASE_1EDGE`.
2. SPI1: ÷4 gives 18 MHz, above 10 MHz; ÷8 gives 9 MHz, which is not. So BR = 010 (`SPI_BAUDRATEPRESCALER_8`) and SCK = 9 MHz. SPI2: 36 MHz ÷ 4 = 9 MHz, so BR = 001 (`SPI_BAUDRATEPRESCALER_4`). The same BR value gives SPI1 and SPI2 SCKs a factor of two apart because they sit on different buses (SPI2's clock enable is bit 14 of RCC_APB1ENR, RM0008 Rev 21 section 7.3.8).
3. During the 8 clocks that send 0x9F the slave is still receiving the command and puts nothing on MISO; that byte is whatever level the line happened to have (0xFF here). 0x17 = 23, so the capacity is 2^23 = 8 388 608 bytes, which is 8 MiB or 64 Mbit.
4. A page is 256 bytes, and 0xF8 = 248, so this page has 256 − 248 = 8 bytes left. Send two commands: 8 bytes starting at 0x0000F8, then the other 8 starting at 0x000100. Without the split, the 8 bytes past the end of the page wrap to the start of the same page and land in 0x000000 to 0x000007, damaging the data there (Winbond datasheet).
5. 240 × 240 × 2 = 115 200 bytes = 921 600 bits; 921 600 ÷ 18 000 000 = 0.0512 s, about 51 ms, at most about 19.5 frames per second. A whole frame needs 115 200 bytes, but the whole chip has only 20 KB (20 480 bytes) of SRAM, so it does not fit; it has to be sent in pieces of a few thousand bytes.

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

The SPI conclusions in this chapter are pinned to order code STM32F103C8T6.

**Clock.** SPI1 is on APB2, and in this book's setup its clock PCLK2 = 72 MHz. The working point is copied whole from Appendix D: Mode 0, `BR=010`, SCK = 9 MHz.

**Pins.** The reset-default pins are LQFP48 pin 15 PA5 = SPI1_SCK, pin 17 PA7 = SPI1_MOSI, pin 16 PA6 = SPI1_MISO, and pin 14 PA4 = SPI1_NSS ([DS5319 Rev 20 Table 5](#source-ds5319-spi)). This chapter does not use hardware NSS: PA4 is a push-pull GPIO, driven low and then high in software. That is not the open drain of chapter 07. On the C8, pin 14 is not a DAC output.

**Remap.** SPI1 can move as a group to PA15, PB3, PB4, and PB5 by setting the SPI1_REMAP bit in AFIO_MAPR (RM0008 Rev 21 Table 56). On the remapped pins, the PA5/PA6/PA7 above are void. The remap is not on the normal path: after reset PB3 and PB4 are the JTAG pins JTDO and NJTRST, and JTAG has to be switched off with SWJ_CFG in AFIO_MAPR before SPI1 can have them. Pin 16 is also TIM3_CH1 in chapter 05; this figure draws only MISO.

**Mode.** Mode 0 is CPOL = 0 and CPHA = 0: SCK idles low, and data is sampled on the first edge, which is the rising edge. The chapter code uses `SPI_POLARITY_LOW`, `SPI_PHASE_1EDGE`, `SPI_NSS_SOFT`, `SPI_FIRSTBIT_MSB`, and `SPI_BAUDRATEPRESCALER_8`.

**Divider.** `BR[2:0]` has only the eight dividers 2, 4, 8, 16, 32, 64, 128, and 256 ([RM0008 Rev 21 section 25.5.1](#source-rm0008-spi)). `010` is ÷8, and `72 / 8 = 9` MHz. `001` is ÷4, 18 MHz. `000` is ÷2, 36 MHz. 36 MHz is the too-fast failure next to the 9 MHz working point, with no separate ledger of its own; it is also above the 18 MHz that DS5319 Rev 20 Table 43 gives for master mode ([DS5319](#source-ds5319)). There is no ÷3. Do not invent an SPI base address.

**The three ID bytes.** The master sends `{0x9F, 0xFF, 0xFF, 0xFF}`. In full duplex, the eight SCK edges that shift out `0x9F` also shift `rx[0]` in, and that byte is not the manufacturer id. The next three bytes are `rx[1]=0xEF`, `rx[2]=0x40`, and `rx[3]=0x17`, assembled as `rx[1] << 16 | rx[2] << 8 | rx[3]`, which is `0xEF4017`. `0x40` is the memory type, not the capacity. The page is 256 bytes. These two sentences are checked against the [existing example](#source-project-examples) and Appendix D. The example treats bit 0 of the status byte as busy; that bit belongs to the W25Q64 and is not BSY in the SPI peripheral's SR. The four commands `0x05`, `0x06`, `0x02`, and `0x03` are in the Code section.

**Failure paths.** After MOSI and MISO are swapped, the three bytes do not match `0xEF 0x40 0x17`; that is the failure path on the key figure. While chip select stays low, the next command is glued to the previous one. A Transmit that never reads MISO lets the receive side overrun, and the next read gets a stale byte (RM0008 Rev 21 section 25.3.10). CPHA on the second edge shifts the bytes. The stuck chip select and `BR=000` at 36 MHz stay in the margin.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-08-spi-jedec.svg" width="760" alt="Mode 0 at divide-by-8 is 9 MHz; the three bytes after 0x9F are 0xEF, 0x40, and 0x17; swapping MOSI and MISO makes them miss">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48. Pin 14 PA4 = CS (push-pull, low during the transaction), pin 15 PA5 = SCK, pin 16 PA6 = MISO, pin 17 PA7 = MOSI. CPOL = 0, CPHA = 0, BR=010, SCK = 9 MHz. On the normal path MOSI sends 0x9F and then three 0xFF bytes; rx[1] through rx[3] are 0xEF, 0x40, and 0x17. The failure path swaps PA6 and PA7. In the margin, a PA4 that stays low glues two transactions, and BR=000 makes SCK = 36 MHz. Pin 14 is not drawn as DAC. Sources: [RM0008 Rev 21 section 25.5.1](#source-rm0008-spi) and [DS5319 Rev 20 Table 5](#source-ds5319-spi).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/spi-jedec.gif" width="640" alt="Chip select falls, 0x9F shifts out, then 0xEF, 0x40, and 0x17 shift in">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the normal path and marks 9 MHz. Print uses the static figure. The swapped wires and 36 MHz are not on this GIF.</sub>
</p>

The main figure shows the very transaction of lab 1, so you can hold a logic-analyzer capture next to it and compare byte by byte. Normal path: PA4 falls, MOSI sends 0x9F and three 0xFF bytes, and MISO answers 0xEF, 0x40, and 0x17 in the last three bytes. Failure path: PA6 and PA7 swapped, and the three bytes do not match. The margin shows two common mistakes: PA4 left low, gluing two transactions into one; and BR=000, which makes SCK 36 MHz. The opening `spi-transfer.svg` is an animated side figure with the timing of all four modes; in the PDF it does not move, so the pins, 9 MHz, and the three ID bytes follow this static figure.

## Timing and state

The table walks through lab 1's ID read in time order; the last three rows are the mode, the speed, and the failure path. At 9 MHz one byte of 8 clocks takes about 0.89 µs, and the 4 bytes, 32 clocks in all, take about 3.6 µs, not counting the overhead of the HAL functions themselves. The mode and the divider come from [RM0008 Rev 21 chapter 25](#source-rm0008-spi); the three ID bytes and the 256-byte page come from the [example](#source-project-examples).

| Row | Byte | MOSI | MISO | CS | SCK |
| --- | --- | --- | --- | --- | --- |
| Normal | 1 | 0x9F | rx[0], not the manufacturer id | low | sample on the rising edge |
| Normal | 2 | 0xFF | 0xEF | low | sample on the rising edge |
| Normal | 3 | 0xFF | 0x40 | low | sample on the rising edge |
| Normal | 4 | 0xFF | 0x17 | low | sample on the rising edge |
| End | — | — | — | back high once BSY clears | idle low |
| Mode | — | — | — | — | CPOL = 0, CPHA = 0 |
| Rate | — | — | — | — | BR=010 is 9 MHz, BR=001 is 18 MHz, BR=000 is 36 MHz (beyond the 18 MHz limit) |
| Failure | 2 through 4 | — | not 0xEF 0x40 0x17 | low | PA6 and PA7 swapped |

The page is 256 bytes: one page program command writes at most to the end of the page.

## Pitfalls and sources

| What you see | Why | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| The ID that comes back is not 0xEF4017 | PA7 is not MOSI, or PA6 is not MISO, or the mode is not 0 | Keep Mode 0, and check that PA7 is MOSI and PA6 is MISO | [DS5319](#source-ds5319-spi) | LQFP48 pin 16 is MISO and pin 17 is MOSI. The three bytes themselves are the next row |
| rx[0] was treated as the manufacturer id | The eight SCK edges of the command also shift rx[0] in | The manufacturer id is rx[1], the type is rx[2], and the capacity is rx[3] | [Example](#source-project-examples) | The command is 0x9F. The three bytes are 0xEF, 0x40, and 0x17. 0x40 is not the capacity. The page is 256 bytes |
| SCK runs at 36 MHz | BR was written as 000 | Use BR 010, which is 9 MHz | [RM0008](#source-rm0008-spi) | Among the eight dividers, 010 is ÷8. 000 is ÷2 = 36 MHz. There is no ÷3 |
| Occasional bad reads with BR 001 | 18 MHz is already the chip's limit, and long wires cannot keep up with the edges | Go back to 010, or shorten the wires | [DS5319](#source-ds5319) | Table 43: in master mode SCK is at most 18 MHz |
| Two commands are glued together | PA4 stayed low | Drive PA4 high at the end of each transaction | [DS5319](#source-ds5319-spi) | Pin 14 is SPI1_NSS. This chapter uses it as a push-pull chip select. On the C8 it is not a DAC output |
| The ID shows up on PB3/PB4/PB5 | A remap was treated as the reset default | The reset-default pins are PA5/PA6/PA7 | [DS5319](#source-ds5319-spi) | Pin 15 is SCK, pin 16 is MISO, and pin 17 is MOSI |
| After sending without receiving, the first read returns old data | The receive side overran, and DR still holds the unread old byte | Use `HAL_SPI_TransmitReceive()`; with your own register code, read DR and then SR to clear OVR | [RM0008](#source-rm0008) | Section 25.3.10: after an overrun DR keeps the old byte and later data is lost; reading DR and then SR clears OVR |
| The SPI stops as soon as it is enabled, and MSTR in CR1 is cleared | With software NSS management SSI was 0, which triggered MODF | Set SSM and SSI together | [RM0008](#source-rm0008) | Section 25.3.10: a master whose NSS is low (SSI at 0 under software management) sets MODF, and SPE and MSTR are cleared |
| Data read right after an erase or write is wrong | The wrong "busy" was awaited: BSY in the SPI peripheral's SR only says the STM32 has finished shifting, while the flash is still erasing or programming inside | Poll bit 0 of the status byte with 0x05 and continue once it is 0 | [Example](#source-project-examples) | The example treats bit 0 of the status byte as busy and polls it with a timeout |

The following items are not in the table because no source card in the list can back them: the W25Q64 commands (0x06, 0x05, 0x02, 0x03, 0x20), the BUSY bit of the status register, the wrap within a page, erase giving 0xFF, the erase and program times, and the 100 000-cycle erase endurance come from Winbond's W25Q64 datasheet; the ST7789 commands, the DC line, and the waits after reset come from Sitronix's ST7789 datasheet; `HAL_SPI_Receive()` sending the buffer as dummy bytes, `HAL_SPI_Transmit()` clearing OVR at the end, and waiting for BSY before the transmit-complete callback are how the STM32CubeF1 HAL source does it.

## Related resources

- Official manuals: **RM0008** chapter 25 (SPI); the W25Q64 and ST7789 datasheets
- Previous: [07 The I2C Bus](07-i2c.md)
- Figures: [`assets/animations/spi-transfer.svg`](../../assets/animations/spi-transfer.svg)
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.
