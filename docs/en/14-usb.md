# 14 USB

> 中文：[USB](../14-USB.md)

> “Unknown USB device” says only that enumeration failed somewhere. Reconcile the 48 MHz clock, D+ pull-up, standard requests, descriptor lengths, and endpoint buffers to locate the failed step.

<p align="center">
  <img src="../../assets/animations/usb-enumeration.svg" width="760" alt="USB enumeration: reset, descriptors, configuration">
  <br><sub>▲ Animation: USB enumeration (vector drawing, not a photograph)</sub>
</p>

<!-- video:ch14 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch14-usb.png">
    <source src="../../assets/video/ch14-usb.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.7 min). <a href="../../assets/video/ch14-usb.mp4">MP4</a> · <a href="../../assets/video/ch14-usb.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. F103 的 USB 全速要 48 兆时钟。常见做法是 PLL 先到 72 兆，再除以 1.5。时钟差一点，主机会在读描述符时失败，设备管理器里就是未知设备。
2. 全速设备用 D+ 上的 1.5 千欧上拉告诉主机：我是全速。BluePill 上这颗电阻常常已经在了。没有上拉，主机根本不知道你插上来了。
3. 枚举是主机在提问。它先在地址 0 要设备描述符的前 8 个字节，再给你分配地址，再要整份配置，最后选择配置。卡在哪一步，口诀在这一章的正文里。
4. 这一帧是仓库画的枚举过程，不是分析仪抓的真实波形。对照它看你的描述符长度。配置描述符的总长度算错，常常卡在选择配置之前。
5. CDC 插上像一个串口，适合传字节流。HID 插上像键盘或鼠标，系统自带驱动，但每次只能按报告格式送很少的字节。数据采集走 CDC，按键走 HID。
6. 在 F103 上，USB 的低优先级中断和 CAN 接收邮箱 0 共用一个入口。两套一起开的时候，服务函数里要分清是谁在叫。只复制一个空的中断函数，另一边就会丢。
7. 示例里 CDC 的配置描述符是 67 个字节。HID 的报告描述符也要自己数，别让总长度字段和真实字节数打架。设置地址要等这一次状态传输走完再生效。
8. 示例用的厂商号是 0x1209，产品号只是实验占位，并没有在 pid.codes 注册。可以在自己的电脑上认设备，不要把这组号印到准备送人的产品上。
9. 枚举卡在哪一步就查哪处：卡在读描述符，多半是 48 兆时钟或描述符字段；卡在读配置，多半是总长度；卡在最后一步，多半是端点没准备好。
10. 示例里的 0x1209 和产品号只是实验占位，没有在 pid.codes 注册。自己的电脑能认出设备就够了，别把这一组数字印到要送人的产品上。

</details>
<!-- /video:ch14 -->
## Principle and scope

The clock and the descriptors in this chapter are for the STM32F103C8T6. The USB clock comes from the 72 MHz PLL set up in chapter 02. With `USBPRE = 0` the PLL is divided by 1.5, which gives the 48 MHz full-speed USB needs. With `USBPRE = 1` there is no division, the USB clock is 72 MHz, and the host fails while reading the descriptors. See [RM0008](#source-rm0008-rcc).

Pin 32 PA11 = USB_DM and pin 33 PA12 = USB_DP. A full-speed device needs a 1.5 kΩ pull-up between D+ and 3.3 V, on the pin 33 side. The host tells the device speed from which line is pulled high: put the pull-up on pin 32, D−, and the host takes it for a low-speed device and never treats it as full speed. See [DS5319 Rev 20 Table 5](#source-ds5319-usbcan). The 1.5 kΩ value is printed in note 2 of DS5319 Table 45. RM0008 only says an external pull-up is needed and gives no value.

USB on the F103 is a full-speed device, not a host, so it cannot drive a USB stick or a keyboard. Full speed is 12 Mbit/s. Low speed, 1.5 Mbit/s, is not one of its modes. See [RM0008](#source-rm0008-usb).

In this repository's example the device descriptor is `0x12` long, 18 bytes, and `bMaxPacketSize0` is 64. VID is `0x1209` and PID is `0x0001`, a placeholder pair for test boards. The `0x0483/0x5740` seen in many ST examples is not what this descriptor holds. The configuration set's `wTotalLength` is `0x0043`, 67 bytes: the configuration, interface, and endpoint descriptors added together, not 18. `bMaxPower = 0x32` counts in 2 mA units, so it means 100 mA. See [examples in this repo](#source-project-examples).

At full speed, bulk and interrupt endpoints both top out at 64 bytes per packet. 1023 bytes applies only to full-speed isochronous endpoints. The example's notification endpoint is 8 bytes and its bulk endpoints are 64, both inside the limit.

PA11/PA12 are also CAN's reset-default pins, which is why chapter 13 remaps CAN to PB8/PB9. On a medium-density part the USB low-priority interrupt is named `USB_LP_CAN_RX0` in the vector table and is the same line as CAN receive. Only the connectivity-line table calls it `USB_LP_CAN1_RX0`. So do not build the USB and CAN examples into one project.

## Key figures


<p align="center">
  <img src="../../assets/animations/sample-14-usb-48m-flow.svg" width="720" alt="USB: D+ pull-up → 48 MHz → 18/67 bytes">
  <br><sub>▲ Hand-drawn CSS animation (FA-002). Pull-up→host sees FS→USBPRE→descriptors.</sub>
</p>


<p align="center">
  <img src="../../assets/diagrams/sample-14-usb-enum.svg" width="760" alt="Full speed needs 48 MHz. The D+ pull-up is on pin 33. This descriptor is an 18-byte device plus a 67-byte configuration set, VID/PID 0x1209/0x0001.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The working setup in the figure is USBPRE = 0, 48 MHz, 1.5 kΩ on D+ at pin 33, an 18-byte device descriptor, and a 67-byte configuration set. The broken setup is USBPRE = 1, which makes the USB clock 72 MHz. 0x0483/0x5740 is not what this descriptor holds. Sources: [RM0008](#source-rm0008-rcc), [DS5319](#source-ds5319-usbcan), and [usb-cdc](#source-project-examples).</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch14-usb-enum.png" width="760" alt="Handraw: USB enumeration and 48 MHz (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). USBPRE=0→48 MHz; D+ 1.5 kΩ; device 18 B + config 67 B; USBPRE=1 → 72 MHz fails; not a photo.</sub>
</p>

<p align="center">
  <img src="../../assets/gif/usb-48m.gif" width="640" alt="D+ is pulled up, the clock is 48 MHz, then 18 bytes and 67 bytes">
  <br><sub>▲ Animated version, showing only a normal enumeration: D+ pulled up, 48 MHz, 18 bytes, 67 bytes. The printed book has only the static figure above.</sub>
</p>

The full enumeration sequence is in `usb-enumeration.svg` at the top of the chapter.

## Timing and state

| Item | Value | Right or wrong |
| --- | --- | --- |
| `USBPRE = 0` | 48 MHz | Correct. 72 / 1.5 = 48 |
| `USBPRE = 1` | 72 MHz | Wrong; enumeration fails |
| Device descriptor | length 18, `bMaxPacketSize0` 64 | VID `0x1209`, PID `0x0001` |
| Configuration set | `wTotalLength` 67, which is `0x0043` | `bMaxPower` `0x32` = 100 mA |
| Packet length | bulk and interrupt ceiling 64 | 1023 is isochronous only. A notification endpoint of 8 is allowed |
| Pins | pin 32 is DM, pin 33 is DP | The pull-up goes on DP. On DM the host sees a low-speed device |

## Pitfalls and sources

| What you see | Why | What to do | Source | What the source shows |
| --- | --- | --- | --- | --- |
| Device Manager fails the descriptor request | The USB clock is not 48 MHz | Keep `USBPRE` at 0 | [RM0008](#source-rm0008-rcc) | `USBPRE=0` makes 72 MHz ÷ 1.5 = 48 MHz. `USBPRE=1` yields 72 MHz |
| The host does not see the device at all | The pull-up is not on D+ | Tie the pull-up to D+ on pin 33, not to DM. The resistance is 1.5 kΩ | [DS5319](#source-ds5319-usbcan) | Pin 32 PA11 includes USB_DM. Pin 33 PA12 includes USB_DP. Table 45 note 2 prints 1.5 kΩ on D+. Tied to DM, this is not the normal path |
| Enumeration shows someone else's VID | The ST example pair was copied | Use this repository's `0x1209/0x0001`. `0x0483/0x5740` is not this descriptor | [examples in this repo](#source-project-examples) | `examples/usb-cdc` has an 18-byte device descriptor. VID/PID is `0x1209/0x0001`. The PID is only a placeholder for the experiment board |
| The configuration length does not match the bytes | 18 was written as the total length | Write `wTotalLength` as 67 | [examples in this repo](#source-project-examples) | The total length in the configuration descriptor is `0x0043`. `bMaxPower` `0x32` is 100 mA |
| An interrupt or bulk endpoint is set to 1023 | That ceiling belongs to isochronous | The ceiling for those two classes at full speed is 64. 1023 is isochronous only | [examples in this repo](#source-project-examples) | The example bulk endpoint is 64 bytes and the notification endpoint is 8 bytes |
| Linked with the CAN example, the receive interrupt is shared | The two examples use one vector | Keep the examples apart. Do not leave CAN on PA11/PA12 | [RM0008](#source-rm0008-usb) | The printed medium-density name is `USB_LP_CAN_RX0`. The connectivity table prints `USB_LP_CAN1_RX0`. USB on this part is a device, not a host |

## Learning goals

- [ ] Separate USB 2.0 low-speed (1.5 Mbps), full-speed (12 Mbps), and high-speed (480 Mbps), and know which STM32 parts do which.
- [ ] Compare control, bulk, interrupt, and isochronous transfers.
- [ ] Read the descriptor tree: device, configuration, interface, endpoint.
- [ ] Recite the seven enumeration steps and guess where "unknown device" got stuck.
- [ ] Contrast CDC and HID, and know where CubeMX attaches the middleware.
- [ ] Use the ST USB Device library for a CDC echo and a custom HID — or the HAL PCD examples in this repo, which do not ship that middleware.

## Core ideas

Device Manager is not enough for USB debugging. Firmware state, PMA and endpoint registers, host traces, and D+/D− electrical waveforms prove different layers and cannot substitute for one another.

### 1. Speeds and which STM32 block you actually have


<p align="center">
  <img src="../../assets/diagrams/sample-14-usbpre-48.svg" width="760" alt="USBPRE=0 => 72/1.5=48 MHz; D+ pull-up marks full-speed">
  <br><sub>▲ Drawn for this book. FS needs 48 MHz; USBPRE=1 breaks enumeration.</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch14-usbpre-48.png" width="760" alt="Handraw: USBPRE and 48 MHz clock (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). PLL 72 MHz÷1.5=48 MHz; USBPRE=1 host rejects; check clock before blaming CDC; not a photo.</sub>
</p>


USB is a conversation chaired by the computer. The host calls on a device, and only then may the device answer; a device cannot seize the wire whenever it has data. The F103 has one 12 Mbps full-speed device block. It can be a keyboard or a virtual serial port, but it cannot host a flash drive. Reaching 480 Mbps takes both an `OTG_HS` block and the matching high-speed PHY.

**Takeaway:** The host starts every transfer. The device is polled. The common STM32 case is a **full-speed device**. Only parts with `OTG_HS` can do high-speed.

| Speed | Spec | Bit rate | On STM32 |
| --- | --- | --- | --- |
| Low | USB 1.1 | 1.5 Mbps | Device side (a HID mouse). STM32 usually does not do this |
| Full | USB 1.1/2.0 | 12 Mbps | **USB peripheral on F0/F1/F3/L4, OTG_FS on F4/F7/H7** |
| High | USB 2.0 | 480 Mbps | **OTG_HS only** (external ULPI PHY, or a part with an on-chip HS PHY) |

| Family | Block | Note | Manual |
| --- | --- | --- | --- |
| STM32F1 | USB Device FS | Device only, 12 Mbps, no OTG host | RM0008 chapter 23 |
| STM32F4 | OTG_FS + OTG_HS | FS PHY on chip; HS needs an external ULPI PHY | RM0090 chapter 30 / 31 |
| STM32F7/H7 | OTG_FS + OTG_HS | Some parts have an on-chip HS PHY | OTG chapter of that RM |

> **An F103 USB block is device-only. It cannot be a host.** F1 USB is on **PA11 (DM) / PA12 (DP)**. On the F103, USB and CAN share those two pins and the same 512-byte dedicated SRAM, so they cannot run at the same time and you pick one. The F411 `OTG_FS` is also on PA11/PA12, but the F411 has no CAN, so the conflict does not arise there.

### 2. Four transfer types

The four transfer types divide one bus in four different ways. Control introduces and configures the device. Bulk is freight: arriving late is acceptable, but a damaged packet is retried. Interrupt gives small messages such as key reports a regular chance to be polled. Isochronous reserves time for sound or video and never goes back for a missed packet, because late audio is no longer useful.

**Takeaway:** Trade latency against reliability. **Control** is for enumeration. **Bulk** moves bytes and retries. **Interrupt** is small and bounded. **Isochronous** keeps a time slot and is allowed to drop data.

| Type | Trait | Typical use | Bandwidth reserved |
| --- | --- | --- | --- |
| Control | Endpoint 0, reliable, reserved each frame | Enumeration, class requests | Yes |
| Bulk | Reliable, no reserved bandwidth, retries | CDC, disks, printers | No |
| Interrupt | Reliable, polling interval, bounded latency | HID keyboard/mouse, small reports | Yes, small |
| Isochronous | Reserved bandwidth, **no retry, drops allowed** | Audio, cameras | Yes |

### 3. Endpoints


<p align="center">
  <img src="../../assets/diagrams/sample-14-pma-map.svg" width="760" alt="F1 USB: eight endpoints share a 512-byte PMA">
  <br><sub>▲ Drawn for this book. IN/OUT are host-named; overlapping PMA corrupts packets.</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch14-pma-map.png" width="760" alt="Handraw: PMA and endpoint windows (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). 512-byte PMA shared by EP0..EP7; IN/OUT are host-named; overlap corrupts packets; not a photo.</sub>
</p>


Think of endpoints as numbered send and receive windows inside the device. The host puts data into an OUT window for the device to collect. The device fills an IN window and waits for the host to collect it. IN and OUT are named from the host's side, which is the easy part to read backwards. Each window also needs a transfer type, a maximum packet size, and buffer space in the 512-byte PMA.

**Takeaway:** An endpoint is a logical pipe. Except for endpoint 0, **each endpoint is one direction** (IN or OUT).

| Endpoint | Direction | Use |
| --- | --- | --- |
| EP0 | IN and OUT | Control, enumeration, standard requests |
| EPn IN | Device to host | Device transmits (CDC TX) |
| EPn OUT | Host to device | Device receives (CDC RX) |

An F1 full-speed device has up to **8 bidirectional endpoints (EP0–EP7)**. They share a **512-byte** packet memory (PMA). You assign that memory yourself (RM0008 chapter 23, `USB_EPnR`, `BTABLE`).

### 4. Descriptor tree

When a device is first plugged in, the computer sees the pull-up on D+ but has no idea what the device does. It asks from the outside in: who are you and how many configurations do you have; which functions are in this configuration; which endpoints belong to each function? The descriptors are the device's answers. One bad length, parent-child relation, or total count stops the host from reading the rest.

**Takeaway:** The host learns the device by reading descriptors: device, then configuration, then interface, then endpoint. The interface is the function. One configuration can hold several interfaces.

```text
Device Descriptor                         (VID / PID / how many configurations)
 └─ Configuration Descriptor              (power / max current / interface count)
     ├─ Interface Descriptor              (class / subclass / protocol, CDC or HID)
     │   ├─ Endpoint Descriptor           (address / direction / type / packet / interval)
     │   └─ Endpoint Descriptor
     └─ Interface Descriptor
         └─ Endpoint Descriptor
```

| Descriptor | Field | Meaning |
| --- | --- | --- |
| Device | `idVendor` / `idProduct` | ST examples often use 0x0483/0x5740. This repository's examples/usb-cdc does not. It uses 0x1209/0x0001 |
| Device | `bNumConfigurations` | Usually 1 |
| Configuration | `bMaxPower` | Unit is 2 mA (0x32 = 100 mA) |
| Interface | `bInterfaceClass` | 0x02 CDC, 0x03 HID, 0x08 MSC, 0xFF vendor |
| Endpoint | `bmAttributes` | 0 control, 1 isochronous, 2 bulk, 3 interrupt |
| Endpoint | `wMaxPacketSize` | 64 bytes maximum for full-speed bulk and interrupt; 1023 is full-speed isochronous only |

A full-speed interrupt endpoint's `wMaxPacketSize` tops out at 64 bytes. 1023 is the full-speed isochronous ceiling, not the interrupt ceiling. In this repository's `examples/usb-cdc`, the bulk endpoints are 64 bytes and the notification endpoint is 8 bytes.

<p align="center">
  <img src="../../assets/gif/usb-enumeration-zh.gif" width="720" alt="The USB host starts with bus reset, reads device and configuration descriptors, assigns an address, and selects a configuration">
  <br><sub>▲ Enumeration sequence: request order in the trace should match the state machine. The animation explains control-transfer order; it cannot prove 48 MHz accuracy, D+/D− signal quality, or descriptor-field correctness.</sub>
</p>

### 5. Seven enumeration steps

Every USB device comes out of reset at address 0. The host uses that temporary address to read just enough information, assigns a new address, and sends all later requests there. It then reads the complete configuration and selects one before the device is ready for normal traffic. In a trace, follow that order and stop at the first request that did not get the expected reply.

**Takeaway:** Reset, read descriptors, assign an address, read the configuration, select it. **Any failed step shows up as "unknown device" or "device descriptor request failed".**

| Step | Action | Note |
| --- | --- | --- |
| 1 | Host sees the device (pull-up on D+) | Full speed pulls D+ up with 1.5 kΩ. That is how the host picks the speed |
| 2 | Bus reset | D+ and D− low for at least 10 ms |
| 3 | At address 0, read the first 8 bytes of the device descriptor | Host learns `bMaxPacketSize0` |
| 4 | Reset again, then Set Address | Device gets an address from 1 to 127 |
| 5 | At the new address, read the full 18-byte device descriptor | VID/PID |
| 6 | Read 9 bytes of configuration, then the whole configuration set | Interfaces and endpoints |
| 7 | Set Configuration | The function is live |

> At steps 3 or 4, check device-descriptor length and 48 MHz first. At step 6, check `wTotalLength`. At step 7, check endpoint address, PMA, and whether the buffer is armed.


<p align="center">
  <img src="../../assets/diagrams/sample-14-descriptor-map.svg" width="760" alt="Device descriptor 18 bytes; configuration collection 67 bytes = 9+9+5+5+4+5+7+9+7+7; VID/PID 0x1209/0x0001; bulk endpoint 64 bytes, notification endpoint 8 bytes">
  <br><sub>▲ Drawn for this book. The descriptor tree: the device descriptor is 18 bytes; the configuration collection is 67 bytes = 9+9+5+5+4+5+7+9+7+7; VID/PID 0x1209/0x0001; the bulk endpoint is 64 bytes and the notification endpoint 8 — the two CDC endpoints hang off this tree, and the CDC-versus-HID differences in the next section all live inside the configuration collection. Sources: [RM0008 USB](#source-rm0008-usb) and the [usb-cdc example](#source-project-examples).</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch14-descriptor-map.png" width="760" alt="Handraw: descriptor tree 18+67 (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). Device 18 B; config set 67=0x0043; VID/PID 0x1209/0x0001; not a photo.</sub>
</p>

### 6. CDC versus HID

CDC delivers a stream of bytes, so the application decides where one message ends and the next begins. HID delivers fixed-format reports whose key bits, coordinates, and status fields are declared in advance. For logs and sampled data, CDC is usually simpler. Pick HID when the operating system should treat the board directly as a keyboard, mouse, or game controller.

**Takeaway:** CDC is "I am a serial port" (high bandwidth, byte stream). HID is "I am a keyboard, mouse, or custom gadget" (native support, fixed reports).

| | CDC | HID |
| --- | --- | --- |
| Job | Virtual COM, arbitrary bytes | Keyboard, mouse, custom report |
| Driver | Built in on Windows 10+. Older Windows wants an .inf | Driver-free on the usual desktops |
| Endpoints | Typically bulk IN, bulk OUT, and one interrupt IN | One interrupt IN (optional OUT) |
| Bandwidth | High, can fill full speed | Low, a few dozen bytes per frame, limited by `bInterval` |
| Unit | Byte stream | A fixed report |
| Typical | Debug log, data logger | Custom pad, macro keyboard, scanner |

### 7. CubeMX middleware

The CubeMX pages are assembling one device from three layers. RCC supplies the 48 MHz clock. The USB peripheral owns D+/D- and the interrupt. The middleware supplies descriptors, endpoints, and class handlers. Enumeration fails if any layer is missing. A common mistake is to keep changing the CDC code when the real fault is the 48 MHz clock or VBUS sensing.

| Item | Where | Value |
| --- | --- | --- |
| USB block | Connectivity → USB / USB_OTG_FS | Device (FS). On F4 pick `Device_Only` or `OTG` |
| Class | Middleware → USB_DEVICE → Class | CDC or HID |
| Identity | `USBD_DEVICE` | VID/PID, strings |
| CDC buffers | CDC page | Default `APP_TX/RX_DATA_SIZE` is 2048 |
| VBUS | VBUS sensing | A self-powered board must see VBUS, or you turn sensing off |
| IRQ | NVIC → USB_LP / OTG_FS | Keep it fairly high |
| Clock | RCC | Full speed wants a **48 MHz** USB clock (F1 divides the PLL; F4 uses PLL48CLK) |

> **48 MHz is not optional.** On F1, `USBCLK = 48 MHz`. With the PLL at 72 MHz, register bit `USBPRE = 0` means ÷1.5, so `72 / 1.5 = 48` MHz. A wrong clock fails enumeration or drops the link at random.

## Wiring

| Board | Peripheral | Pins | Note |
| --- | --- | --- | --- |
| BluePill (F103) | USB device | PA11 = DM, PA12 = DP | On-board micro-USB, D+ already has 1.5 kΩ |
| BluePill | Debug | SWD PA13/PA14 | Leave them alone |
| Nucleo-F411RE | OTG_FS | PA11 = DM, PA12 = DP | The ST-Link mini-USB is a virtual COM, **not** the OTG connector |
| F4-Discovery | OTG_FS | PA11/PA12 | On-board micro-AB |
| BlackPill (F411) | USB | PA11/PA12 | On-board Type-C wired to the MCU |

- Keep the pair short, matched, and near 90 Ω differential. Dupont wires often fail even at full speed.
- On a bare board, **D+ needs 1.5 kΩ to 3.3 V** so the host sees a full-speed device. Many dev boards already have it.
- The USB connector can feed 5 V into the on-board LDO. Before the device is configured, stay within 100 mA.

<p align="center">
  <img src="../../assets/boards/pinout-bluepill.svg" width="820" alt="BluePill pin map locating PA11 USB_DM, PA12 USB_DP, PA9, and PA10">
  <br><sub>▲ PA11/PA12 are the USB differential pair; PA9/PA10 are a separate UART debug path. The pin map locates signals but does not prove that a clone board's pull-up, resistors, or routing meet USB electrical requirements.</sub>
</p>

## Code

If CubeMX generated a CDC project, the file you actually edit is **`USB_DEVICE/App/usbd_cdc_if.c`**. The snippets below are that style.

**① Bring-up (`main.c`, generated)**

```c
#include "stm32f1xx_hal.h"
#include "usb_device.h"        /* CubeMX: declares MX_USB_DEVICE_Init */
#include "usbd_cdc_if.h"       /* CDC API */

int main(void)
{
    HAL_Init();
    SystemClock_Config();      /* USB clock must be 48 MHz */
    MX_GPIO_Init();
    MX_USB_DEVICE_Init();

    uint8_t msg[] = "STM32 CDC ready\r\n";

    while (1)
    {
        /* Non-blocking. USBD_OK means the stack accepted the buffer */
        CDC_Transmit_FS(msg, sizeof(msg) - 1);
        HAL_Delay(1000);
    }
}
```

**② Receive callback (`usbd_cdc_if.c`)**

```c
#include "usbd_cdc_if.h"

static int8_t CDC_Receive_FS(uint8_t *Buf, uint32_t *Len)
{
    /* Buf is the internal buffer, *Len is this packet */
    /* Echo. Do not block for long inside the USB interrupt */
    CDC_Transmit_FS(Buf, *Len);

    /* Arm the next OUT, or you only ever receive one packet */
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, &Buf[0]);
    USBD_CDC_ReceivePacket(&hUsbDeviceFS);
    return (USBD_OK);
}
```

**③ Transmit prototype (provided by the ST library)**

```c
/* Exported by ST's usbd_cdc_if.c */
uint8_t CDC_Transmit_FS(uint8_t *Buf, uint16_t Len);
```

> Transmit is **asynchronous**. `CDC_Transmit_FS` hands the buffer to the stack and returns. The USB interrupt finishes the packet. Calling it again too soon returns `USBD_BUSY`.

**④ A custom HID report (a small mouse)**

```c
/* 4-byte input report: 3 buttons plus relative X/Y */
__ALIGN_BEGIN static uint8_t HID_ReportDesc[] __ALIGN_END =
{
    0x05, 0x01,        /* Usage Page (Generic Desktop) */
    0x09, 0x02,        /* Usage (Mouse)                  */
    0xA1, 0x01,        /* Collection (Application)       */
    0x09, 0x01,        /*   Usage (Pointer)              */
    0xA1, 0x00,        /*   Collection (Physical)        */
    0x05, 0x09,        /*     Usage Page (Button)        */
    0x19, 0x01,        /*     Usage Minimum (1)          */
    0x29, 0x03,        /*     Usage Maximum (3)          */
    0x15, 0x00, 0x25, 0x01,   /* Logical Min/Max 0..1     */
    0x95, 0x03, 0x75, 0x01,   /* three 1-bit buttons      */
    0x81, 0x02,        /*     Input (Data,Var,Abs)       */
    0x95, 0x01, 0x75, 0x05,   /* pad to a byte            */
    0x81, 0x03,        /*     Input (Const)              */
    0x05, 0x01, 0x09, 0x30, 0x09, 0x31,  /* X, Y               */
    0x15, 0x81, 0x25, 0x7F,   /* Logical Min/Max -127..127 */
    0x75, 0x08, 0x95, 0x02,   /* two 8-bit fields         */
    0x81, 0x06,        /*     Input (Data,Var,Rel)       */
    0xC0, 0xC0         /* End Collection ×2              */
};
```

**⑤ Send a HID report**

```c
/* 4-byte report on the interrupt IN endpoint */
USBD_HID_SendReport(&hUsbDeviceFS, report, sizeof(report));
```

## Hands-on labs

1. **Enumeration evidence:** Save GET_DESCRIPTOR, SET_ADDRESS, and SET_CONFIGURATION traces and record USBCLK, the D+ pull-up, and `wTotalLength`. Break the total length once and confirm a repeatable failure step.
2. **CDC data loop:** Send lengths 1, 64, 65, and 256. Record `USBD_BUSY`, host length, and CRC. Do not overwrite the transmit buffer while the previous packet is pending.
3. **HID report loop:** Trigger a fixed four-byte report from a button and verify endpoint address, report length, and host state in the trace. UI movement is an observation; report bytes are the evidence.

<p align="center">
  <img src="../../assets/diagrams/instrument-evidence-ladder.svg" width="820" alt="USB evidence layers from build logs and registers through runtime logs, a logic analyzer, and an oscilloscope">
  <br><sub>▲ USB evidence is layer-specific: a host trace proves requests and descriptors, while a scope is needed for D+/D− electrical quality. A COM port appearing does not prove that CDC transfers of every length are correct (FA-002 · IG-010 · C-03/C-10/C-27/C-31).</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch14-evidence-ladder.png" width="760" alt="Handraw: USB evidence ladder (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). Log→registers→UART→logic analyzer→scope; a COM port does not prove every CDC length; not a photo.</sub>
</p>

This repo's two examples do not ship the ST USB middleware. They enumerate with HAL PCD:

- [examples/usb-cdc](../../examples/usb-cdc/): virtual COM, echo, and a `cdc tick` line once a second while DTR is set.
- [examples/usb-hid](../../examples/usb-hid/): a boot keyboard. PA0 to ground types the letter `a`.

Both run the PLL at 72 MHz and select USB = PLL/1.5. On F103, `USB_LP_CAN1_RX0` is the same IRQ as bxCAN receive. Do not link the CAN example into the same project.

Before leaving this chapter, keep the complete enumeration trace, the failure step from a bad `wTotalLength`, CRCs for the four CDC lengths, and one HID-report byte record.

## Related resources

- RM0008 chapter 23, USB device (`USB_EPnR`, PMA, `BTABLE`).
- RM0090 chapter 30, USB OTG_FS, and chapter 31, USB OTG_HS.
- USB 2.0 specification, chapter 9 (descriptors, enumeration, standard requests).
- AN4879, USB hardware and PCB guidelines using STM32 MCUs.
- The part datasheet for USB electrical limits and the PA11/PA12 alternate functions.
- Figure: `../../assets/animations/usb-enumeration.svg` (vector drawing).
