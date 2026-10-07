# usb-cdc —— 全速 USB 虚拟串口

> 难度：★★★★　｜　涉及外设：USB Device FS　｜　对应章节：[14 USB](../../docs/14-USB.md)

## 一、功能说明

BluePill 插上板载 USB 线，主机会枚举出一个 CDC 串口。这个工程**不包含** ST USB Device 中间件，描述符和类请求写在 `usb_cdc.c` 里，底层用 HAL 的 PCD。

| 现象 | 条件 |
| --- | --- |
| 设备名 `CDC virtual COM` | 枚举走完 SET_CONFIGURATION |
| 打开串口后每秒一行 `cdc tick` | 主机把 DTR 拉高（`SET_CONTROL_LINE_STATE`） |
| 你发什么，它回什么 | 批量端点 0x02 OUT / 0x82 IN，主循环里回显 |
| PC13 跟着 tick 翻转 | 板载灯，低电平亮 |

VID 用 pid.codes 的 **0x1209**，PID **0x0001** 只是实验占位，没有在 pid.codes 注册。量产前换成你自己的号码。

口诀：**72 MHz 的 PLL 要再除 1.5，USB 才是 48 MHz。时钟歪了，描述符要不到。**

## 二、硬件接线

| 信号 | 引脚 | 备注 |
| --- | --- | --- |
| USB_DM | PA11 | 板载 micro-USB 已经接好 |
| USB_DP | PA12 | 全速设备需要 D+ 对 3.3 V 的 1.5 kΩ。多数 BluePill 已经焊上 |
| 板载灯 | PC13 | 低电平点亮 |
| SWD | PA13 / PA14 | 本示例不占用 |

不要用杜邦线飞 USB 差分线。BluePill 的座子就是走线。

## 三、把 HAL PCD 放进工程

CubeMX 新建 F103C8 时，如果勾选 USB Device 中间件，会再生成一套 `usbd_*.c`。那些文件和本示例的中断服务函数会撞名，而且中间件源码不在本仓库里。

做法：

1. 时钟：HSE 8 MHz，PLL ×9，SYSCLK 72 MHz，USB 时钟选 **PLL / 1.5**。
2. 把 Cube 固件包里的这三个文件加进工程（只加 HAL，不加 USB Device 库）：
   - `stm32f1xx_hal_pcd.c`
   - `stm32f1xx_hal_pcd_ex.c`
   - `stm32f1xx_ll_usb.c`
3. 用本目录的 `main.c`、`usb_cdc.c`、`usb_cdc.h` 加入工程。`main.c` 覆盖 `Core/Src/main.c`。
4. 若 `stm32f1xx_hal_msp.c` 里已有 `HAL_PCD_MspInit`，删掉，避免和 `usb_cdc.c` 重复定义。
5. 编译下载。`USB_LP_CAN1_RX0_IRQHandler` 只留本示例这一份。

PlatformIO：`board = bluepill_f103c8`，`framework = stm32cube`。需要在 `build_flags` 里确认 PCD 源文件被编译进来（Cube 框架默认不一定包含 USB）。缺符号时把上面三个 HAL 文件放进 `src/`。

## 四、预期现象

Windows 10 及以后的系统自带 `usbser.sys`，CDC ACM 一般不用自己装 inf。设备管理器里多一个 COM 口。

串口助手任意波特率都能打开（线速率是 USB 批量传输，`SET_LINE_CODING` 只是把 115200 8N1 存下来）。打开后看到 `cdc tick`，输入 `hi` 会回 `hi`。

自测：

1. 为什么 SYSCLK 已经是 72 MHz，还要单独配 USB 预分频？
2. 回显只成功一次，第二次没了，回调里漏了哪一步？
3. 这条 USB 中断和 bxCAN 的哪一个 IRQ 是同一个？

## 五、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 未知设备，描述符失败 | USB 不是 48 MHz，或 D+ 没有 1.5 kΩ | 核对 `RCC_USBCLKSOURCE_PLL_DIV1_5`；看板上拉 |
| 完全没有设备 | PA11/PA12 被配成普通 GPIO，或线只能充电 | 用本文件的输入模式；换一根数据线 |
| 有 COM 口但没有 tick | 助手没拉 DTR | 换一个会设 DTR 的串口工具，或看回显 |
| 链接报 `HAL_PCD_Init` 未定义 | 工程没编进 PCD | 加上面三个 HAL 文件 |
| 和 CAN 示例一起编 | 共用 `USB_LP_CAN1_RX0_IRQHandler` | 分成两个工程 |

## 六、相关资源

- RM0008 第 23 章 USB device（端点寄存器、PMA、48 MHz）。
- USB 2.0 第 9 章；CDC PSTN 子类的 `SET_LINE_CODING`（0x20）和 `SET_CONTROL_LINE_STATE`（0x22）。
- 配图：[`assets/animations/usb-enumeration.svg`](../../assets/animations/usb-enumeration.svg)（自绘，不是实拍）。
- 本示例没有在 Wokwi 上跑过：当前 BluePill 模型的说明里没有把 USB 设备枚举列成可用项。
