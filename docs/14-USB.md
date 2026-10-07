# 14 USB

> English: [USB](en/14-usb.md)

> USB 让 STM32 用一根线同时供电与通信，枚举成功后能变成虚拟串口(CDC)、键盘(HID)或 U 盘(MSC)。

<p align="center">
  <img src="../assets/animations/usb-enumeration.svg" width="760" alt="USB 设备枚举：复位 → 描述符 → 配置">
  <br><sub>▲ 动画：USB 设备枚举全过程（复位 → 取描述符 → 分配地址 → 配置）（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch14 -->
<p align="center">
  <img src="../assets/video/ch14-usb.gif" width="640" alt="第 14 章讲解幻灯">
  <br><sub>▲ 本章讲解幻灯：程序生成的 GIF（tools/gen_videos.py，可复现，不是实拍）。旁白与五帧一一对应。</sub>
</p>

**旁白（跟着画面读，大约一分钟）**

1. USB 主机说了算。设备只能等着被问。F103 是全速设备，不是主机。
2. 枚举就是：复位、读描述符、设地址、读配置、设配置。
3. 卡在描述符，多半是长度字段或 48 MHz 时钟不准。
4. CDC 是虚拟串口，走批量传输。HID 是键盘鼠标那类，走中断传输，常常免驱。
5. 自测：F103 的 DP/DM 在哪两只脚？CDC 和 HID 谁更依赖驱动？
<!-- /video:ch14 -->


## 📌 学习目标

- [ ] 分清 USB 2.0 低速(1.5 Mbps)/全速(12 Mbps)/高速(480 Mbps)，以及 STM32 各型号支持哪种。
- [ ] 掌握四种传输类型（控制/批量/中断/等时）的特点与适用场景。
- [ ] 读懂描述符层级：设备 → 配置 → 接口 → 端点，以及各字段含义。
- [ ] 背下枚举 7 步流程，能判断「设备管理器里不认」卡在哪一步。
- [ ] 说清 CDC 虚拟串口与 HID 的差异，并会在 CubeMX 里挂中间件。
- [ ] 会用 ST USB Device 库写一个 CDC 收发 + HID 自定义设备。

## 🧠 核心原理

### 1. USB 速率与 STM32 外设

**结论**：USB 主机发起一切通信，设备只能「被轮询」；STM32 最常见的是**全速(FS)设备**，只有带 `OTG_HS` 的型号才支持高速(HS)。

| 速率 | 标称 | 位速率 | STM32 支持情况 |
| --- | --- | --- | --- |
| 低速 Low Speed | USB 1.1 | 1.5 Mbps | 设备端（如 HID 鼠标），STM32 一般不做 |
| 全速 Full Speed | USB 1.1/2.0 | 12 Mbps | **F0/F1/F3/L4 的 USB 外设、F4/F7/H7 的 OTG_FS** |
| 高速 High Speed | USB 2.0 | 480 Mbps | 仅 **OTG_HS**（需外接 ULPI PHY 或内置 HS PHY 的型号） |

| 系列 | USB 外设 | 说明 | 参考手册章节 |
| --- | --- | --- | --- |
| STM32F1 | USB Device FS | 仅设备模式，12 Mbps，无 OTG 主机 | RM0008 第 23 章 USB device |
| STM32F4 | OTG_FS + OTG_HS | FS 内置 PHY；HS 需外接 ULPI PHY | RM0090 第 30 章 OTG_FS / 第 31 章 OTG_HS |
| STM32F7/H7 | OTG_FS + OTG_HS | 部分型号 HS 内置 PHY | 对应 RM 的 OTG 章节 |

> ⚠️ **F103 的 USB 是纯设备（Device only），不能做主机**；F411 的 `OTG_FS` 引脚是 **PA11(DM)/PA12(DP)**，与 CAN1 复用冲突，二选一。F1 的 USB 引脚同样是 PA11/PA12。

### 2. 四种传输类型

**结论**：按「实时性 vs 可靠性」取舍——**控制**用于枚举配置，**批量**用于大数据（可靠性优先），**中断**用于小数据低延迟，**等时**用于音频视频（实时优先，允许丢）。

| 类型 | 特点 | 典型用途 | 带宽保证 |
| --- | --- | --- | --- |
| 控制 Control | 端点 0 专用，可靠，每帧预留 | 枚举、配置、类请求 | 有 |
| 批量 Bulk | 可靠，无带宽保证，出错重传 | 虚拟串口 CDC、U 盘、打印机 | 无 |
| 中断 Interrupt | 可靠，有轮询间隔，延迟有界 | HID 键盘鼠标、小数据上报 | 有（小带宽） |
| 等时 Isochronous | 有带宽保证，**不重传、允许丢** | USB 音频、摄像头 | 有 |

### 3. 端点 Endpoint

**结论**：端点是主机与设备之间数据传输的「逻辑管道」，除端点 0 外**每个端点只支持一个方向**（IN 或 OUT）。

| 端点 | 方向 | 用途 |
| --- | --- | --- |
| EP0 | IN + OUT（双向） | 控制端点，枚举与标准请求 |
| EPn IN | 设备 → 主机 | 上报数据（如 CDC 的 TX） |
| EPn OUT | 主机 → 设备 | 接收数据（如 CDC 的 RX） |

F1 全速设备最多 **8 个双向端点（EP0~EP7）**；端点 FIFO 共享 **512 字节** 的 PMA（Packet Memory Area），需手工分配（见 RM0008 第 23 章 `USB_EPnR`、`BTABLE`）。

### 4. 描述符层级

**结论**：主机通过读取一串**描述符**来认识设备，层级为「设备 → 配置 → 接口 → 端点」，接口是功能的载体，一个配置可含多个接口。

```text
设备描述符 Device Descriptor          (VID / PID / 支持的配置数)
 └─ 配置描述符 Configuration Descriptor (供电方式 / 最大电流 / 接口数)
     ├─ 接口描述符 Interface Descriptor  (类/子类/协议，如 CDC / HID)
     │   ├─ 端点描述符 Endpoint Descriptor (地址/方向/类型/包长/间隔)
     │   └─ 端点描述符 Endpoint Descriptor
     └─ 接口描述符 Interface Descriptor
         └─ 端点描述符 Endpoint Descriptor
```

| 描述符 | 关键字段 | 说明 |
| --- | --- | --- |
| 设备 | `idVendor`/`idProduct` | VID/PID，ST 官方例程常用 0x0483/0x5740 |
| 设备 | `bNumConfigurations` | 配置数量，一般 1 |
| 配置 | `bMaxPower` | 最大电流，单位 2 mA（0x32 = 100 mA） |
| 接口 | `bInterfaceClass` | 0x02=CDC、0x03=HID、0x08=MSC、0xFF=厂商自定义 |
| 端点 | `bmAttributes` | 传输类型：0=控制 2=批量 3=中断 1=等时 |
| 端点 | `wMaxPacketSize` | FS 最大 64 字节（等时/中断可 1023） |

### 5. 枚举 7 步

**结论**：枚举是主机「复位设备 → 读描述符 → 分配地址 → 读配置 → 选择配置」的过程，**任何一步失败，设备管理器就报「未知设备 / 设备描述符请求失败」**。

| 步 | 动作 | 说明 |
| --- | --- | --- |
| 1 | 主机检测到设备（D+ 上拉） | 全速设备在 D+ 拉 1.5 kΩ 上拉，主机据此判断速率 |
| 2 | 复位总线 Reset | D+/D- 同时拉低 ≥ 10 ms |
| 3 | 默认地址 0 读设备描述符前 8 字节 | 拿到 `bMaxPacketSize0` |
| 4 | 再次复位后读完整设备描述符(18 字节) | 拿到 VID/PID |
| 5 | 设置地址 Set Address | 设备获得唯一地址（1~127） |
| 6 | 读配置描述符(9 字节) → 读完整配置集合 | 拿到接口/端点信息 |
| 7 | 选择配置 Set Configuration | 设备进入「已配置」状态，功能可用 |

> 调试口诀：**卡在第 3/4 步**多为描述符长度/字段错或时钟不准；**卡在第 6 步**多为配置描述符总长度 `wTotalLength` 算错；**卡在第 7 步**多为端点 FIFO/缓冲区没准备好。

### 6. CDC 虚拟串口 vs HID

**结论**：想「插上就变成串口」用 **CDC**（免驱、带宽高、适合传数据）；想「插上被识别成键盘/鼠标/自定义手柄」用 **HID**（免驱、系统原生支持、可被游戏/上位机直接读）。

| 维度 | CDC（通信设备类） | HID（人机接口设备） |
| --- | --- | --- |
| 用途 | 虚拟串口，收发任意字节流 | 键盘/鼠标/自定义报告 |
| 驱动 | Windows 10+ 免驱，老系统需 .inf | 全平台免驱 |
| 端点 | 通常 1 批量 IN + 1 批量 OUT + 1 中断 IN | 1 中断 IN（+ 可选 OUT） |
| 带宽 | 高（可跑满全速） | 低（每帧几十字节，受 `bInterval` 限） |
| 数据单位 | 字节流 | 固定格式「报告 Report」 |
| 典型场景 | 调试串口、数据采集卡 | 自定义手柄、宏键盘、扫码枪 |

### 7. CubeMX 中间件配置要点

| 配置项 | 位置 | 取值/说明 |
| --- | --- | --- |
| USB 外设 | Connectivity → USB / USB_OTG_FS | Device (FS)；F4 选 `Device_Only` 或 `OTG` |
| 类选择 | Middleware → USB_DEVICE → Class | `Communication Device Class (CDC)` 或 `HID` |
| 设备参数 | `USBD_DEVICE` 配置 | VID/PID、厂商/产品字符串 |
| CDC 参数 | `CDC` 子项 | 接口数、TX/RX 缓冲大小（默认 APP_TX/RX_DATA_SIZE=2048） |
| VBUS 检测 | `VBUS sensing` | 自供电板需接 VBUS 或关掉 sensing |
| 中断优先级 | NVIC → USB_LP / OTG_FS | 建议较高优先级 |
| 时钟 | RCC | FS 要求 USB 时钟 **48 MHz**（F1 由 PLL 分频；F4 由 PLL48CLK） |

> **48 MHz 时钟是硬性要求**：F1 全速 USB 需要 `USBCLK = 48 MHz`（PLL 72 MHz 时用 `USBPRE=1.5` 分频）；时钟不准会导致枚举失败或随机掉线。

## 🛠️ 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill (F103) | USB Device | PA11=USB_DM、PA12=USB_DP | 板载 micro-USB，D+ 已接 1.5 kΩ 上拉 |
| BluePill | 调试 | SWD PA13/PA14 | 保留，便于边调边看 |
| Nucleo-F411RE | OTG_FS | PA11=DM、PA12=DP | 板载 mini-USB 到 ST-Link 是虚拟串口，**非** OTG |
| F4-Discovery | OTG_FS | PA11/PA12 | 板载 micro-AB USB OTG 口 |
| BlackPill (F411) | USB | PA11/PA12 | 板载 Type-C 直连 MCU（DFU/自定义设备） |

接线要点：
- **USB 差分线尽量等长、靠近走线、90 Ω 差分阻抗**，别用杜邦线飞线，否则全速都可能枚举失败。
- 自绘裸板做 USB 时，**D+ 到 3.3 V 需接 1.5 kΩ 上拉**（全速设备标识），很多开发板已焊好。
- 供电：USB 口可取 5 V，板载 LDO 转 3.3 V；注意总线电流（未配置前 ≤ 100 mA）。
## 💻 代码实现

用 CubeMX 生成 USB CDC 工程后，真正要写代码的地方只有 **`USB_DEVICE/App/usbd_cdc_if.c`** 的回调。下面给出可用的收发实现。

**① CDC 初始化（`main.c`，CubeMX 生成）**

```c
#include "stm32f1xx_hal.h"
#include "usb_device.h"        /* CubeMX 生成：包含 MX_USB_DEVICE_Init 声明 */
#include "usbd_cdc_if.h"       /* CDC 收发接口 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();      /* 必须保证 USB 时钟 = 48 MHz */
    MX_GPIO_Init();
    MX_USB_DEVICE_Init();      /* 初始化 USB 设备栈并连接 */

    uint8_t msg[] = "STM32 CDC ready\r\n";

    while (1)
    {
        /* 非阻塞发送；返回 USBD_OK 表示已交给 USB 栈 */
        CDC_Transmit_FS(msg, sizeof(msg) - 1);
        HAL_Delay(1000);
    }
}
```

**② CDC 接收回调（`usbd_cdc_if.c`）**

```c
#include "usbd_cdc_if.h"

static int8_t CDC_Receive_FS(uint8_t *Buf, uint32_t *Len)
{
    /* Buf 指向内部接收缓冲，*Len 为本包长度 */
    /* 例：回显 —— 收到什么原样发回（注意不要在中断里长时间阻塞） */
    CDC_Transmit_FS(Buf, *Len);

    /* 关键：重新挂载接收，否则只能收到一包 */
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, &Buf[0]);
    USBD_CDC_ReceivePacket(&hUsbDeviceFS);
    return (USBD_OK);
}
```

**③ 发送函数原型（ST 库提供）**

```c
/* 由 ST 的 usbd_cdc_if.c 导出，应用层直接调用 */
uint8_t CDC_Transmit_FS(uint8_t *Buf, uint16_t Len);
```

> 发送是**异步**的：`CDC_Transmit_FS` 把数据交给 USB 栈后立即返回，真正上线由 USB 中断完成。若上一包未发完又调用，会返回 `USBD_BUSY`，需要重试或加标志。

**④ 自定义 HID 报告描述符片段（把设备做成「自定义手柄」）**

```c
/* 一个 4 字节输入报告：3 个按钮 + X/Y 相对坐标 */
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
    0x95, 0x03, 0x75, 0x01,   /* 3 个 1 位按钮            */
    0x81, 0x02,        /*     Input (Data,Var,Abs)       */
    0x95, 0x01, 0x75, 0x05,   /* 补齐 5 位                */
    0x81, 0x03,        /*     Input (Const)              */
    0x05, 0x01, 0x09, 0x30, 0x09, 0x31,  /* X, Y               */
    0x15, 0x81, 0x25, 0x7F,   /* Logical Min/Max -127..127 */
    0x75, 0x08, 0x95, 0x02,   /* 2 个 8 位字段            */
    0x81, 0x06,        /*     Input (Data,Var,Rel)       */
    0xC0, 0xC0         /* End Collection ×2              */
};
```

**⑤ 发送 HID 报告**

```c
/* 把 4 字节报告通过中断端点 IN 发出 */
USBD_HID_SendReport(&hUsbDeviceFS, report, sizeof(report));
```

## ⚠️ 常见坑与排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 设备管理器「未知 USB 设备（设备描述符请求失败）」 | 48 MHz 时钟不准 / 描述符错 | 核对 USB 时钟；检查设备描述符长度字段 |
| 完全不被识别 | D+ 无上拉 / 差分线接反 / 未连接 | 检查 1.5 kΩ 上拉；DM/DP 别接反 |
| 识别但报错码 43 | 枚举中途失败（多为配置描述符） | 核对 `wTotalLength` 与接口/端点数量 |
| 老 Windows 认不到 CDC | 缺 .inf 驱动 | 用 Win10+，或改 HID（免驱） |
| 只能收到第一包数据 | 未重新挂载接收 | 回调里 `USBD_CDC_ReceivePacket` |
| 发送返回 BUSY | 上一包未发完 | 判返回值重试，或加发送完成标志 |
| 运行一会儿掉线 | 中断优先级低 / 阻塞太久 | 别在 USB 中断里长时间操作；提高中断优先级 |
| F4 上 USB 和 CAN 冲突 | PA11/PA12 复用 | 二选一，或改用 CAN2/其他引脚 |
| VBUS sensing 报错 | 自供电未接 VBUS | CubeMX 关闭 VBUS sensing |
| DFU/自定义设备进不去 | BOOT 配置/描述符不符 | 用官方 DFU 描述符模板 |

## 🧪 动手实验

1. **CDC 回环（最易）**：CubeMX 生成 F103 的 CDC 工程，串口助手打开新出现的 COM 口，发什么回什么。预期：插上即多一个 COM 口，回显正常。
2. **CDC 定时上报**：每秒把 ADC 采到的电压（见第 09 章）通过 `CDC_Transmit_FS` 上报。预期：上位机收到连续数值。
3. **自定义 HID**：把设备改成 HID，用一个按键触发上报，用「Windows 游戏控制器」属性页查看。预期：按键时属性页里的坐标/按钮状态变化。
4. **（进阶）枚举抓包**：用 Wireshark + USBPcap（或硬件 USB 分析仪）抓取枚举过程，逐条对照第 5 节的 7 步。预期：能看到 GET_DESCRIPTOR / SET_ADDRESS / SET_CONFIGURATION 的完整交互。

仓库里的两个示例不附带 ST USB 中间件，直接用 HAL PCD 完成枚举：

- [examples/usb-cdc](../examples/usb-cdc/)：虚拟串口，回显，DTR 有效后每秒一行 `cdc tick`。
- [examples/usb-hid](../examples/usb-hid/)：启动式键盘，PA0 按下送一个字母 `a`。

两份都把 PLL 设成 72 MHz，USB 时钟选 PLL/1.5。F103 的 `USB_LP_CAN1_RX0` 与 bxCAN 接收是同一条中断，不要和 CAN 示例编进同一个工程。

## 🔗 相关资源

- RM0008《STM32F10xxx 参考手册》第 23 章 USB device（`USB_EPnR`、PMA、`BTABLE`）。
- RM0090《STM32F4 参考手册》第 30 章 USB OTG_FS、第 31 章 USB OTG_HS。
- USB 2.0 规范（usb.org）：第 9 章设备框架（描述符、枚举、标准请求）。
- 应用笔记 AN4879《USB hardware and PCB guidelines using STM32 MCUs》（差分走线/阻抗）。
- 数据手册 DS：USB 电气参数、PA11/PA12 复用。
- 配图：`../assets/animations/usb-enumeration.svg`（作者自绘矢量图）。

