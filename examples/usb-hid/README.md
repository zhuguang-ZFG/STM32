# usb-hid —— 全速 USB 键盘

> 难度：★★★★　｜　涉及外设：USB Device FS + GPIO　｜　对应章节：[14 USB](../../docs/14-USB.md)

## 一、功能说明

板子枚举成一台 **启动式键盘**。PA0 接到地的一瞬间，焦点窗口收到字母 `a`；松开发一个全 0 的报告，表示按键抬起。只在边沿发，不会按住连发。

报告一共 8 字节：第 1 字节是修饰键，第 2 字节保留，后面 6 字节是用法码。字母 a 的用法码是 `0x04`。描述符在 `usb_hid.c`，按 HID 1.11 的键盘集合来写，不链接 ST 中间件。

VID **0x1209**（pid.codes），PID **0x0002** 只是实验占位。

口诀：**先点文本框，再碰 PA0。这是真键盘，字母会打进当前窗口。**

## 二、硬件接线

| 信号 | 引脚 | 接法 |
| --- | --- | --- |
| USB_DM / USB_DP | PA11 / PA12 | 用板载 USB 座。D+ 需要 1.5 kΩ 上拉到 3.3 V |
| 按键 | PA0 | 内部上拉，按下接到 GND |
| 灯 | PC13 | 按下时点亮（低电平亮） |
| SWD | PA13 / PA14 | 保留 |

## 三、编译

和 [usb-cdc](../usb-cdc/README.md) 相同：PLL 72 MHz，USB 时钟 **PLL/1.5 = 48 MHz**。工程里加入 HAL 的 `stm32f1xx_hal_pcd.c`、`stm32f1xx_hal_pcd_ex.c`、`stm32f1xx_ll_usb.c`，再加入本目录三个源文件。不要同时编译 ST 的 `usbd_hid.c`，中断服务函数会重复定义。

Cube 若生成了另一份 `HAL_PCD_MspInit`，删掉生成的那份。

## 四、预期现象

主机把设备认成键盘，一般不需要驱动。用记事本获取焦点，把 PA0 碰一下地：出现一个 `a`，PC13 亮；松开灯灭。不会每秒刷屏。

自测：

1. 报告第 3 字节（下标 2）里的 `0x04` 表示什么？
2. 为什么松手还要再发一帧全 0？
3. `SET_IDLE`（请求号 0x0A）不应答的话，枚举会停在哪一类请求？

## 五、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 未知设备 | 48 MHz 不准，或报告描述符长度不是 63 | `cfg_desc` 里的 `0x3F` 必须等于 `sizeof report_desc` |
| 认成键盘但没有字母 | PA0 没接到地，或焦点不在文本框 | 上拉输入，按下为低 |
| 字母停在「一直按住」 | 抬起报告没发出去 | 看 `usb_hid_key(usage, 0)` 是否在松开时被调用 |
| 和 CDC 工程符号冲突 | 两套 `USB_LP_CAN1_RX0_IRQHandler` | 只把一个示例加进工程 |

## 六、相关资源

- RM0008 第 23 章 USB device。
- HID 1.11：报告描述符、`SET_IDLE`、`SET_PROTOCOL`、启动式键盘。
- 配图：[`assets/animations/usb-enumeration.svg`](../../assets/animations/usb-enumeration.svg)（自绘，不是实拍）。
