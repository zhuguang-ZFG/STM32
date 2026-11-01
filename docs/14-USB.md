# 14 USB

> English: [USB](en/14-usb.md)

> USB 让 STM32 用一根线同时供电与通信，枚举成功后能变成虚拟串口(CDC)、键盘(HID)或 U 盘(MSC)。

<p align="center">
  <img src="../assets/animations/usb-enumeration.svg" width="760" alt="USB 设备枚举：复位 → 描述符 → 配置">
  <br><sub>▲ 动画：USB 设备枚举全过程（复位 → 取描述符 → 分配地址 → 配置）（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch14 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch14-usb.png">
    <source src="../assets/video/ch14-usb.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.6 分钟）。<a href="../assets/video/ch14-usb.mp4">MP4</a> · <a href="../assets/video/ch14-usb.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. F103 的 USB 全速要 48 兆时钟。常见做法是 PLL 先到 72 兆，再除以 1.5。时钟差一点，主机会在读描述符时失败，设备管理器里就是未知设备。
2. 全速设备用 D+ 上的 1.5 千欧上拉告诉主机：我是全速。BluePill 上这颗电阻常常已经在了。没有上拉，主机根本不知道你插上来了。
3. 枚举是主机在提问。它先在地址 0 要设备描述符的前 8 个字节，再给你分配地址，再要整份配置，最后选择配置。卡在哪一步，口诀在这一章的正文里。
4. 这一帧是仓库画的枚举过程，不是分析仪抓的真实波形。对照它看你的描述符长度。配置描述符的总长度算错，常常卡在选择配置之前。
5. CDC 插上像一个串口，适合传字节流。HID 插上像键盘或鼠标，系统自带驱动，但每次只能按报告格式送很少的字节。数据采集走 CDC，按键走 HID。
6. 在 F103 上，USB 的低优先级中断和 CAN 接收邮箱 0 共用一个入口。两套一起开的时候，服务函数里要分清是谁在叫。只复制一个空的中断函数，另一边就会丢。
7. 示例里 CDC 的配置描述符是 67 个字节。HID 的报告描述符也要自己数，别让总长度字段和真实字节数打架。设置地址要等这一次状态传输走完再生效。
8. 示例用的厂商号是 0x1209，产品号只是实验占位，并没有在 pid.codes 注册。可以在自己的电脑上认设备，不要把这组号印到准备送人的产品上。
9. 口诀：卡在读描述符，多半是时钟或描述符字段；卡在读配置，多半是总长度；卡在最后一步，多半是端点还没准备好。
10. 合上书，三问。F103 的 D+ 和 D- 在哪两只脚？48 兆时钟从 72 兆怎样得到？CDC 和 HID，谁更像一个串口？

</details>
<!-- /video:ch14 -->

## 学习目标

读这一章之前：需要第 02 章的时钟树（PLL 怎样倍频到 72 MHz），第 03 章的复用功能，第 04 章的 NVIC；第 06 章的串口收发和第 10 章的 DMA 用到时会再提。二进制、十六进制和「字节」不熟，先读第 00 章的「零基础预备」。

- [ ] 说出 USB 的三档速率，以及 STM32F103C8T6 的 USB 外设是哪一档、能不能做主机
- [ ] 说出四种传输类型各适合什么数据，以及全速下批量和中断端点的包长上限 64 字节
- [ ] 把设备描述符、配置描述符、接口描述符和端点描述符画成一棵树，算出例程配置集合的总长 67 字节
- [ ] 按顺序说出枚举的七步，看到「设备描述符请求失败」时判断卡在哪一步
- [ ] 在 72 MHz 的 PLL 下配出 48 MHz 的 USB 时钟，说清 `USBPRE` 写 0 和写 1 的区别
- [ ] 用 CubeMX 的 USB_DEVICE 中间件做出一个 CDC 虚拟串口，回显时检查 `USBD_BUSY`

## 核心原理

**一句话结论：USB 的一切通信都由主机发起，设备只回答。插上以后，主机先用一串固定的问题（枚举）读清设备是什么，之后才按描述符里写的端点收发数据；F103 上这一切的前提，是一个准确的 48 MHz USB 时钟和 D+ 上的上拉电阻。**

### 先打个比方

把 USB 主机想成酒店前台，设备是刚进门的客人。客人不能自己去找房间，只能等前台问：

- 客人站到门口，按一下铃（D+ 上拉），前台才知道来了人。
- 前台先给一个临时号牌 0，问一句最要紧的：「你一次能接几样东西？」（设备描述符的前 8 字节）。
- 然后发正式房号（设置地址），再把登记表整份要来：你是谁、要几个房间、每个房间干什么（设备描述符、配置描述符和下面的接口、端点）。
- 登记完，前台说「入住」（设置配置），客人才能开始用房间。

比方到这里为止。真的前台不会忘记问过什么，USB 主机也不会；可客人的登记表要是写错一个长度，前台就会在那一步停下，设备管理器里只剩一个「未知设备」。主机问得很快，每一步都有超时，所以设备的时钟必须准。

### 1. USB 速率与 STM32 外设

USB 2.0 有三档速率。设备在 D+ 或 D− 上接一只上拉电阻，主机看是哪根线被拉高，就知道它是低速还是全速；高速设备先以全速连接，再和主机握手升上去（[USB 2.0 规范](#source-usb20) 第 7 章）。

| 速率 | 位速率 | 在 STM32 上 |
| --- | --- | --- |
| 低速 Low Speed | 1.5 Mbit/s | 鼠标、键盘一类的老设备用；本书用到的 STM32 外设不工作在这一档 |
| 全速 Full Speed | 12 Mbit/s | F0/F1/F3/L4 的 USB 设备外设，F4/F7/H7 的 OTG_FS |
| 高速 High Speed | 480 Mbit/s | 只有 OTG_HS，要外接 ULPI 接口的 PHY 芯片，或者用自带高速 PHY 的型号 |

| 系列 | USB 外设 | 能做什么 | 手册 |
| --- | --- | --- | --- |
| STM32F103 | USB 全速设备接口 | 只能做设备，不能做主机；端点可配 1 到 8 个 | RM0008 Rev 21 第 23 章 |
| STM32F405/F407 | OTG_FS 和 OTG_HS | 设备、主机和 OTG；OTG_FS 自带全速 PHY，OTG_HS 要高速时外接 ULPI PHY | RM0090 Rev 22 第 34、35 章 |

> [!WARNING]
> F103 的 USB 和 CAN 共用一块 512 字节的 SRAM，同一时刻只能用其中一个（RM0008 Rev 21 第 23.2 节）。BluePill 的板载 USB 口接在 PA11/PA12，复位后 CAN 的默认脚也在这两只脚上，第 13 章已经把 CAN 移到 PB8/PB9。

### 2. 四种传输类型

USB 按数据的性质分四种传输。下表最后一列是全速下一个包最多多少字节（[USB 2.0 规范](#source-usb20) 第 5 章）：

| 类型 | 特点 | 典型用途 | 全速包长上限 |
| --- | --- | --- | --- |
| 控制 Control | 每个设备都有，走端点 0；出错重传 | 枚举、配置、类请求 | 8、16、32 或 64 字节 |
| 批量 Bulk | 出错重传，不保证带宽，总线空闲时多发 | 虚拟串口 CDC、U 盘、打印机 | 64 字节 |
| 中断 Interrupt | 出错重传，主机按固定间隔来问，延迟有上限 | 键盘、鼠标、少量状态上报 | 64 字节 |
| 等时 Isochronous | 保证带宽，出错不重传，丢就丢了 | 音频、摄像头 | 1023 字节 |

「中断传输」和 MCU 的中断不是一回事：它也是主机来问，只是按描述符里的 `bInterval` 定期问，最短 1 ms 一次。所以全速下一个中断端点每秒最多带 64 × 1000 = 64 000 字节。批量没有间隔限制，全速下一帧（1 ms）最多 19 个 64 字节的包，规范上的上限约 1.2 MB/s；实际能跑到多少，看主机和固件。

### 3. 端点 Endpoint

端点是设备里一块收发缓冲，主机按「地址 + 端点号 + 方向」找到它。端点 0 是双向的控制端点，每个设备都必须有；其余端点每个只走一个方向。方向按主机来叫：IN 是设备发给主机，OUT 是主机发给设备。

| 端点 | 方向 | 用途 |
| --- | --- | --- |
| EP0 | IN 和 OUT | 控制端点，枚举和标准请求 |
| EPn IN | 设备 → 主机 | 上报数据，比如 CDC 的发送 |
| EPn OUT | 主机 → 设备 | 收数据，比如 CDC 的接收 |

F103 的 USB 外设可以配 1 到 8 个端点，所有端点的缓冲都放在一块 512 字节的包缓冲区（PMA）里，由缓冲描述表 `BTABLE` 分配（RM0008 Rev 21 第 23.2、23.3 节）。CubeMX 生成的工程替你分好了；自己加端点时，要算清它们加起来放不放得下。

### 4. 描述符：一棵树

主机靠读描述符认识设备。描述符是一串字节，开头两个字节固定是「本描述符的长度」和「类型」。它们排成一棵树：

```text
设备描述符           VID、PID、端点 0 的包长、有几个配置
 └─ 配置描述符       供电方式、最大电流、有几个接口、整个集合的总长
     ├─ 接口描述符   类、子类、协议，比如 CDC 或 HID
     │   ├─ 端点描述符   地址、方向、类型、包长、间隔
     │   └─ 端点描述符
     └─ 接口描述符
         └─ 端点描述符
```

主机要配置描述符时，设备一次把它和下面所有的接口、端点描述符连在一起送出去，这一串叫配置集合。配置描述符里的 `wTotalLength` 就是这一串的总长。下表是最常查的几个字段（[USB 2.0 规范](#source-usb20) 第 9.6 节）：

| 描述符 | 字段 | 含义 |
| --- | --- | --- |
| 设备 | `bLength` | 设备描述符固定 18 字节，即 `0x12` |
| 设备 | `idVendor` / `idProduct` | 厂商号和产品号。ST 官方例程常用 `0x0483/0x5740`；本仓库 `examples/usb-cdc` 用的是 `0x1209/0x0001` |
| 设备 | `bMaxPacketSize0` | 端点 0 的包长，全速可以是 8、16、32 或 64 |
| 配置 | `wTotalLength` | 整个配置集合的字节数，例程是 67，即 `0x0043` |
| 配置 | `bMaxPower` | 最大电流，单位 2 mA：`0x32` 是 100 mA |
| 接口 | `bInterfaceClass` | `0x02` 是 CDC 的通信接口，`0x0A` 是 CDC 的数据接口，`0x03` 是 HID，`0x08` 是 U 盘，`0xFF` 是厂商自定义 |
| 端点 | `bmAttributes` | 低 2 位是传输类型：0 控制、1 等时、2 批量、3 中断 |
| 端点 | `wMaxPacketSize` | 全速批量和中断最多 64；1023 只属于全速等时 |

`0x1209` 是 pid.codes 给开源项目用的厂商号，`0x0001` 只是本仓库的实验占位，没有在 pid.codes 注册。在自己电脑上做实验可以，不要印到准备送人的产品上。

### 5. 枚举的七步

插上以后，主机按下面的顺序问（[USB 2.0 规范](#source-usb20) 第 9.1 节）。任何一步设备没答对，设备管理器里就是「未知设备」或「设备描述符请求失败」：

| 步 | 主机做什么 | 设备要答出什么 |
| --- | --- | --- |
| 1 | 看到 D+ 被拉高，知道来了一个全速设备 | D+ 上的 1.5 kΩ 上拉 |
| 2 | 复位总线：D+ 和 D− 一起拉低至少 10 ms | 复位后回到默认状态，地址是 0 |
| 3 | 在地址 0 上要设备描述符，只读前 8 字节 | `bMaxPacketSize0` |
| 4 | 设置地址 | 等这次传输的状态阶段走完，再换成新地址 |
| 5 | 在新地址上读完整的设备描述符，18 字节 | VID、PID、配置数 |
| 6 | 先读配置描述符的前 9 字节拿到总长，再按总长读整个配置集合 | `wTotalLength` 和后面的接口、端点描述符 |
| 7 | 设置配置 | 打开描述符里的端点，进入「已配置」状态 |

有的主机在第 3 步之后会再复位一次，不影响后面的顺序。

第 4 步有一个细节：设备收到「设置地址」后，要等这次控制传输的状态阶段完成，才能真的换地址。马上换的话，主机发来的应答包对不上地址，枚举停在这里。CubeMX 的中间件和 HAL 已经按这个顺序处理。

口诀：**卡在第 3 步，查时钟和设备描述符；卡在第 6 步，查 `wTotalLength`；卡在第 7 步，查端点和缓冲区。**

### 6. CDC 和 HID 选哪个

| 比较项 | CDC（通信设备类） | HID（人机接口设备） |
| --- | --- | --- |
| 插上像什么 | 一个串口 | 键盘、鼠标或自定义设备 |
| 驱动 | Windows 10 起自带；更早的 Windows 要装 `.inf` | 各平台都自带 |
| 端点 | 一个中断 IN 做通知，一对批量 IN/OUT 传数据 | 一个中断 IN，可选一个中断 OUT |
| 带宽 | 走批量，全速上限约 1.2 MB/s | 走中断，一个端点全速最多 64 000 字节每秒 |
| 数据的样子 | 任意字节流 | 报告描述符定好格式的「报告」 |
| 适合 | 调试打印、数据采集 | 按键、扫码枪、少量控制量 |

传数据选 CDC；要插上就被系统当成键盘或鼠标、不想让用户装任何东西，选 HID。

### 7. CubeMX 里的 USB 设置

| 设置 | 位置 | 怎么填 |
| --- | --- | --- |
| USB 外设 | Connectivity → USB | 勾上 Device (FS)；F4 上是 USB_OTG_FS，选 Device_Only |
| 设备类 | Middleware → USB_DEVICE → Class For FS IP | Communication Device Class (CDC) 或 Human Interface Device Class (HID) |
| 设备参数 | USB_DEVICE → Device Descriptor | VID、PID、厂商和产品字符串 |
| 收发缓冲 | USB_DEVICE → Parameter Settings | CDC 的 `APP_RX_DATA_SIZE` 和 `APP_TX_DATA_SIZE` |
| 时钟 | Clock Configuration | USB 时钟必须是 48 MHz |
| 中断 | NVIC | F1 上是 `USB_LP_CAN1_RX0`，勾上使能 |

F1 的 48 MHz 怎样来：PLL 先倍频到 72 MHz，再经 `USBPRE` 位决定的分频送给 USB。`USBPRE = 0` 是除以 1.5，`72 / 1.5 = 48` MHz；`USBPRE = 1` 是不分频，USB 拿到 72 MHz，主机在读描述符时就会失败（RM0008 Rev 21 第 7.3.2 节）。HAL 里对应的写法是 `RCC_USBCLKSOURCE_PLL_DIV1_5`。CubeMX 的时钟页里 USB 那一格显示 48 MHz 才算配对。

F4 的 OTG_FS 有一个 F1 没有的设置：VBUS 检测。它通过 PA9 看主机有没有供电。板子没有把 VBUS 接到 PA9 时，要在 CubeMX 里把 VBUS sensing 关掉，否则设备一直以为没插上。

## 硬件与接线

| 开发板 | 外设 | 引脚 | 说明 |
| --- | --- | --- | --- |
| BluePill（F103C8T6） | USB 全速设备 | 第 32 脚 PA11 = USB_DM，第 33 脚 PA12 = USB_DP | 板载 micro-USB 已经接好；D+ 上拉电阻在板上 |
| BluePill | 调试 | PA13 / PA14 | SWD，留着边调边看 |
| NUCLEO-F411RE | OTG_FS | PA11 = DM，PA12 = DP | 板上的 USB 口接的是 ST-LINK，不是 F411 的 OTG；要用 OTG_FS，从排针引出 PA11/PA12 自己接 |
| STM32F4-Discovery | OTG_FS | PA11 / PA12 | 板上有一个接 F407 的 micro-AB USB 口 |
| BlackPill（F411CE） | OTG_FS | PA11 / PA12 | 板载 Type-C 直接接 MCU |

接线要注意三件事：

- **上拉电阻**。全速设备要在 D+ 和 3.3 V 之间接一只 1.5 kΩ（[USB 2.0 规范](#source-usb20) 第 7.1.5 节），F103 片内没有这只电阻。BluePill 板上已经焊了，但不少板子上焊的阻值不是 1.5 kΩ（经验）。大多数电脑照样能认；某台电脑认不出、换一台能认时，量一下 PA12 到 3.3 V 的电阻。自己画板时按 1.5 kΩ 焊。
- **差分线**。D+ 和 D− 是一对差分线，USB 2.0 规范要求 90 Ω 差分阻抗。用开发板的座子就行，不要用杜邦线飞线，那样全速也可能枚举失败。
- **电流**。设备在被配置之前，从 USB 取的电流不能超过 100 mA；配置以后按 `bMaxPower` 声明的值取（[USB 2.0 规范](#source-usb20) 第 7.2.1 节）。例程声明的是 100 mA。

## 代码实现

用 CubeMX 生成带 USB_DEVICE 中间件的 CDC 工程以后，要自己写的地方只有两处：`main.c` 的主循环，以及 `USB_DEVICE/App/usbd_cdc_if.c` 里的接收回调。下面这份代码做回显：电脑发来什么，就原样发回去。

```c
/* USB_DEVICE/App/usbd_cdc_if.c。CubeMX 已经生成了 CDC_Receive_FS 的空壳，
   把它的函数体换成下面这样；其余几行放进文件顶部的 USER CODE 区 */
#include <string.h>

#define ECHO_BUF_SIZE 256U

static uint8_t           s_echo[ECHO_BUF_SIZE];   /* 收到、还没发回去的字节 */
static volatile uint32_t s_echo_len = 0;          /* 非 0 表示有数据待发 */

static int8_t CDC_Receive_FS(uint8_t *Buf, uint32_t *Len)
{
    /* 这个回调在 USB 中断里运行，只拷贝，不发送 */
    if (s_echo_len == 0U) {
        uint32_t n = (*Len < ECHO_BUF_SIZE) ? *Len : ECHO_BUF_SIZE;
        memcpy(s_echo, Buf, n);
        s_echo_len = n;
    }
    /* 上一包还没发完时，这一包丢掉。不重新挂接收，就只能收到一包 */
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, &Buf[0]);
    USBD_CDC_ReceivePacket(&hUsbDeviceFS);
    return USBD_OK;
}

/* 主循环调用：有数据就发；USB 还在发上一包时返回 0，下次再试 */
uint8_t CDC_EchoPoll(void)
{
    if (s_echo_len == 0U) {
        return 1U;
    }
    if (hUsbDeviceFS.dev_state != USBD_STATE_CONFIGURED) {
        return 0U;
    }
    if (CDC_Transmit_FS(s_echo, (uint16_t)s_echo_len) != USBD_OK) {
        return 0U;                                /* USBD_BUSY：上一包还在路上 */
    }
    s_echo_len = 0U;
    return 1U;
}
```

```c
/* main.c */
#include "main.h"
#include "usb_device.h"
#include "usbd_cdc_if.h"

uint8_t CDC_EchoPoll(void);   /* 定义在 usbd_cdc_if.c，也可以声明到 usbd_cdc_if.h 里 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();      /* PLL 72 MHz，USB 时钟 RCC_USBCLKSOURCE_PLL_DIV1_5 = 48 MHz */
    MX_GPIO_Init();
    MX_USB_DEVICE_Init();      /* 初始化 USB 设备栈并接上总线 */

    while (1)
    {
        (void)CDC_EchoPoll();
    }
}
```

逐段看：

- `CDC_Receive_FS()` 在 USB 中断里被调用，`Buf` 指向中间件自己的接收缓冲，`*Len` 是这一包的长度，全速批量最多 64 字节。回调里只把数据拷进 `s_echo`，不在这里发：这时上一次发送可能还没完成，`CDC_Transmit_FS()` 会返回 `USBD_BUSY`，数据就丢了。
- `USBD_CDC_SetRxBuffer()` 加 `USBD_CDC_ReceivePacket()` 重新挂上接收。少了这两行，设备只收第一包，之后电脑发什么都没反应。
- `s_echo_len` 当作「有数据待发」的标志。中断里写、主循环里清，所以加 `volatile`。这是单缓冲的最简写法：主循环还没把上一包发出去时，新来的一包会被丢掉。要不丢，换成第 06 章那种环形缓冲。
- `CDC_EchoPoll()` 先看设备是不是已经被配置：枚举还没走到第 7 步时，CDC 类的数据还没建立，不能发。`CDC_Transmit_FS()` 是异步的，返回 `USBD_OK` 只表示交给了 USB 栈，真正发出去靠 USB 中断。所以 `s_echo` 在发完之前不能改；这份代码在 `s_echo_len` 清零之前不会往里写，正好满足。
- `SystemClock_Config()` 是 CubeMX 生成的。打开它核对一行：`PeriphClkInit.UsbClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5`。

再看 HID。CubeMX 选 HID 类时，中间件自带一份鼠标的报告描述符，报告是 4 字节：按键、X、Y、滚轮。下面这一段把鼠标往右挪一下：

```c
#include "usbd_hid.h"

extern USBD_HandleTypeDef hUsbDeviceFS;

void Mouse_NudgeRight(void)
{
    uint8_t report[4] = { 0x00, 10, 0, 0 };   /* 按键全松开，X 加 10，Y 和滚轮不动 */
    if (hUsbDeviceFS.dev_state == USBD_STATE_CONFIGURED) {
        (void)USBD_HID_SendReport(&hUsbDeviceFS, report, sizeof(report));
    }
}
```

- 报告的四个字节由报告描述符规定，顺序和含义要和它一致。自己改了报告描述符，`HID_MOUSE_REPORT_DESC_SIZE` 和报告长度要一起改，否则主机解析出来的数会错位。
- X 和 Y 是相对值，范围 −127 到 127。鼠标报告每发一次就挪一次；不像键盘，不需要再发一份「抬起」。
- `USBD_HID_SendReport()` 也是异步的，上一份还没被主机取走时返回 `USBD_BUSY`。主机按 `bInterval` 来取，比这更快的调用都会拿到 `USBD_BUSY`。

仓库里另有两个例程，不链接 ST 的中间件，直接用 HAL 的 PCD 层完成枚举，描述符写在自己的源文件里，适合对照第 4、5 节逐字节看：

- [examples/usb-cdc](../examples/usb-cdc/)：虚拟串口，回显；电脑打开串口（DTR 有效）以后每秒发一行 `cdc tick`。
- [examples/usb-hid](../examples/usb-hid/)：启动式键盘，PA0 按下时发一个字母 `a`。

两个例程都把 PLL 设成 72 MHz、USB 时钟选 PLL/1.5。F103 上 USB 的低优先级中断和 CAN 接收共用 `USB_LP_CAN1_RX0` 这一条，不要和 CAN 例程编进同一个工程。

## 动手实验

1. **CDC 回显。** 用 CubeMX 生成 F103 的 CDC 工程，按上面的代码改 `usbd_cdc_if.c` 和 `main.c`，插上板载 USB。
   - 预期现象：电脑上多出一个串口（Windows 的设备管理器里在「端口」下面）。用串口助手打开它，波特率随便填，发什么就收回什么。
   - 怎么确认：拔掉再插，那个串口消失又出现。逐个字符慢慢发，每个都原样回来。一次粘贴几百字节，回来的可能少一些：单缓冲在主循环还没发完时会丢包，这是代码的取舍，不是故障。
   - 没成功先查：设备管理器里是「未知设备」，按第 5 节的口诀查：先看 `UsbClockSelection` 是不是 `RCC_USBCLKSOURCE_PLL_DIV1_5`、HSE 是不是 8 MHz 晶振；能出现串口但只回显第一包，查回调里有没有重新挂接收；什么都不出现，量 PA12 到 3.3 V 之间有没有上拉。
2. **改一个描述符字段，看枚举停在哪。** 在实验一的工程里，把配置描述符的 `wTotalLength` 故意改小 1，重新下载。它在中间件的 `usbd_cdc.c` 里，配置描述符数组的第 3、4 个字节，写作 `LOBYTE(USB_CDC_CONFIG_DESC_SIZ)` 和 `HIBYTE(...)`；改这两个字节，不要改 `USB_CDC_CONFIG_DESC_SIZ` 这个宏本身，它同时决定数组长度，改了编译不过。
   - 预期现象：串口不再出现，或者出现一个带感叹号的设备；改回去以后恢复。
   - 怎么确认：Windows 上用 USBPcap 加 Wireshark，或者 Linux 上 `dmesg`，看主机读配置集合那一步拿到的长度和设备给出的字节数对不上。
   - 没成功先查：改了没效果，先确认改的是全速那一份：有的中间件版本里全速和高速各有一份配置描述符，F103 用全速的。
3. **HID 鼠标。** 新建一个工程，USB_DEVICE 选 HID 类，把 `Mouse_NudgeRight()` 加进去，PA0 接一个按键，配成内部上拉，按下接到地（和 `examples/usb-hid` 一样），每按一次调用一次。
   - 预期现象：插上以后不装驱动，电脑认出一只鼠标；每按一次键，指针往右挪一小段。
   - 怎么确认：按住不放时指针不应该一直走，因为代码只在按下的那一下发报告；如果一直走，是按键没有按边沿判断，或者没有消抖。
   - 没成功先查：认成了鼠标但指针不动，看 `USBD_HID_SendReport()` 的返回值，`USBD_BUSY` 表示发得太快；报告长度和描述符不一致时，指针会乱跳或往错的方向走。
4. **（进阶）抓一次枚举。** Windows 装 USBPcap 和 Wireshark（或者用硬件 USB 分析仪），拔插实验一的板子，把枚举过程抓下来。
   - 预期现象：能按顺序找到第 5 节表里的请求：`GET_DESCRIPTOR`（设备，8 字节）、`SET_ADDRESS`、`GET_DESCRIPTOR`（设备，18 字节）、`GET_DESCRIPTOR`（配置，9 字节，再按总长读一次）、`SET_CONFIGURATION`。
   - 怎么确认：抓到的设备描述符第 9、10 字节（`idVendor`，低字节在前）和你在 CubeMX 里填的 VID 一致。
   - 没成功先查：USBPcap 要选对板子所在的那个根集线器；抓不到最前面几步，是因为开始抓之前设备已经插上了，先开始抓再插。

## 自测

1. F103 的 PLL 是 72 MHz。`USBPRE` 写 0 和写 1，USB 时钟各是多少？哪一种能枚举？
2. 一个全速中断端点的 `bInterval` 是 1。它每秒最多能送多少字节？想更快，该换成哪种传输？
3. 例程的配置集合是 67 字节。设备描述符是 18 字节。主机在枚举的第 6 步先读几个字节、为什么？
4. 电脑上显示「设备描述符请求失败」。按第 5 节，最可能卡在哪一步，先查哪两样？
5. CDC 回显的接收回调里直接调用 `CDC_Transmit_FS()`，粘贴一大段文字时会丢字。为什么？

参考答案：

1. `USBPRE = 0` 是除以 1.5，72 / 1.5 = 48 MHz，能枚举；`USBPRE = 1` 不分频，USB 拿到 72 MHz，主机读描述符时失败。全速 USB 要求 48 MHz（RM0008 Rev 21 第 7.3.2 节）。
2. 全速中断端点一个包最多 64 字节，`bInterval = 1` 是每 1 ms 问一次，所以每秒最多 64 × 1000 = 64 000 字节。要更快，换成批量传输：全速下一帧最多 19 个 64 字节的包，规范上限约 1.2 MB/s。
3. 先读 9 字节，正好是配置描述符本身。主机这时还不知道整个配置集合有多长，要先从这 9 字节里读出 `wTotalLength`（这里是 67），再按这个长度把配置描述符连同接口、端点描述符整串读一遍。
4. 卡在第 3 步：主机在地址 0 上要设备描述符，没拿到正确的回答。先查 USB 时钟是不是 48 MHz（`RCC_USBCLKSOURCE_PLL_DIV1_5`、HSE 是不是 8 MHz），再查设备描述符的长度和 `bMaxPacketSize0`。
5. 回调在 USB 中断里运行。上一包还在发的时候，`CDC_Transmit_FS()` 返回 `USBD_BUSY`，这一包没交出去；回调又没有检查返回值，数据就丢了。正确的做法是回调里只拷贝、重新挂接收，在主循环里发，并检查返回值。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

这一章的时钟和描述符只钉在订货号 STM32F103C8T6 上。USB 时钟整格照抄第 02 章和罗盘。PLL 是 72 MHz。`USBPRE = 0` 再除以 1.5，USB 时钟是 48 MHz。`USBPRE = 1` 不除，USB 时钟是 72 MHz，主机在读描述符时失败。见 [RM0008](#source-rm0008-rcc)。不重画时钟树。

第 32 脚 PA11 = USB_DM，第 33 脚 PA12 = USB_DP。全速的 1.5 kΩ 上拉接在 D+ 和 3.3 V 之间，也就是第 33 脚这一侧。接到第 32 脚上，主机不会按这颗全速设备来认。见 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。表 45 注 2 印出 D+ 上这只 1.5 kΩ。RM0008 只提到外接上拉，不印欧姆。图上的 1.5 kΩ 与表 45 注 2 和罗盘是同一笔。

这颗料的 USB 是全速设备，不是主机。12 Mbit/s 是它的全速档。低速 1.5 Mbit/s 不是它的工作模式。见 [RM0008](#source-rm0008-usb)。

设备描述符长度 `0x12`，共 18 字节。`bMaxPacketSize0` 是 64。VID 是 `0x1209`，PID 是 `0x0001`。这是本仓库实验号。`0x0483/0x5740` 不是这份描述符。配置集合的 `wTotalLength` 是 `0x0043`，即 67，不是 18。`bMaxPower = 0x32`，单位 2 mA，所以是 100 mA。见 [本仓库例程](#source-project-examples)。

全速批量和中断的上限都是 64 字节。1023 只属于全速等时。例程的通知端点是 8 字节，批量端点是 64 字节。8 没有超出 64 的上限。

PA11/PA12 的 CAN 默认功能在第 13 章已经移走。本图只画 USB。中容量表印刷的向量名是 `USB_LP_CAN_RX0`，与 CAN 接收是同一条中断。互联型表才印 `USB_LP_CAN1_RX0`。两个例程不要编在一起。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-14-usb-enum.svg" width="760" alt="全速要 48 MHz；D+ 上拉在第 33 脚；这份描述符是 18 字节设备加 67 字节配置集合，VID/PID 是 0x1209/0x0001">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径是 USBPRE = 0、48 MHz、第 33 脚 D+ 上的 1.5 kΩ、18 字节和 67 字节。失败路径是 USBPRE = 1，时钟变成 72 MHz。0x0483/0x5740 不是这份描述符。出处是 [RM0008](#source-rm0008-rcc)、[DS5319](#source-ds5319-usbcan) 和 [usb-cdc](#source-project-examples)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/usb-48m.gif" width="640" alt="D+ 被拉高，时钟是 48 MHz，随后是 18 字节和 67 字节">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：D+ 上拉、48 MHz、18 字节、67 字节。印刷以静态主图为准。72 MHz 和接错的上拉不在这条 GIF 上。</sub>
</p>

`usb-enumeration.svg` 留作辅图。

## 时序与状态

| 项目 | 值 | 对错 |
| --- | --- | --- |
| `USBPRE = 0` | 48 MHz | 正常。72 / 1.5 = 48 |
| `USBPRE = 1` | 72 MHz | 失败 |
| 设备描述符 | 长度 18，`bMaxPacketSize0` 64 | VID `0x1209`，PID `0x0001` |
| 配置集合 | `wTotalLength` 67，即 `0x0043` | `bMaxPower` `0x32` = 100 mA |
| 包长 | 批量和中断上限 64 | 1023 只属于等时。通知端点 8 是允许的 |
| 脚位 | 第 32 脚 DM，第 33 脚 DP | 上拉在 DP。接到 DM 不是这条正常路径 |

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 设备管理器里描述符请求失败 | USB 时钟不是 48 MHz | `USBPRE` 保持 0 | [RM0008](#source-rm0008-rcc) | `USBPRE=0` 时 72 MHz ÷1.5 = 48 MHz。`USBPRE=1` 得到 72 MHz |
| 主机完全看不到设备 | 上拉不在 D+ | 上拉接在第 33 脚 D+，不要接到 DM。阻值是 1.5 kΩ | [DS5319](#source-ds5319-usbcan) | 第 32 脚 PA11 的复用含 USB_DM，第 33 脚 PA12 的复用含 USB_DP。表 45 注 2 印出 D+ 上的 1.5 kΩ。接到 DM 不是这条正常路径 |
| 枚举到的是别人的 VID | 抄了 ST 例程那一对 | 用本仓库的 `0x1209/0x0001`。`0x0483/0x5740` 不是这份描述符 | [本仓库例程](#source-project-examples) | `examples/usb-cdc` 的设备描述符是 18 字节。VID/PID 是 `0x1209/0x0001`。PID 只给实验板占位 |
| 配置集合长度和字节数对不上 | 把 18 写成了总长 | `wTotalLength` 写成 67 | [本仓库例程](#source-project-examples) | 配置描述符里的总长是 `0x0043`。`bMaxPower` 的 `0x32` 是 100 mA |
| 中断或批量端点写成 1023 | 用了等时的上限 | 全速这两类的上限是 64。1023 只给等时 | [本仓库例程](#source-project-examples) | 例程批量端点是 64 字节，通知端点是 8 字节 |
| 和 CAN 例程链在一起，接收中断串了 | 两条例程共用一条向量 | 两个例程分开。CAN 不要留在 PA11/PA12 | [RM0008](#source-rm0008-usb) | 向量名以印刷为准。中容量表印 `USB_LP_CAN_RX0`。互联型表印 `USB_LP_CAN1_RX0`。这颗料的 USB 是设备，不是主机 |

## 相关资源

- RM0008《STM32F10xxx 参考手册》第 23 章 USB device（`USB_EPnR`、PMA、`BTABLE`）。
- RM0090《STM32F4 参考手册》第 30 章 USB OTG_FS、第 31 章 USB OTG_HS。
- USB 2.0 规范（usb.org）：第 9 章设备框架（描述符、枚举、标准请求）。
- 应用笔记 AN4879《USB hardware and PCB guidelines using STM32 MCUs》（差分走线/阻抗）。
- 数据手册 DS：USB 电气参数、PA11/PA12 复用。
- 配图：`../assets/animations/usb-enumeration.svg`（作者自绘矢量图）。



- 手机阅读版：[第 14 章 · USB（公众号图文）](https://mp.weixin.qq.com/s/iSVv3wSvz9Rl4LOVxeOfdg)
