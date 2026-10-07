# can-bxcan —— bxCAN 环回、双节点、过滤器、Bus-Off

> 难度：★★★★　｜　涉及外设：bxCAN + USART1　｜　对应章节：[13 CAN 总线](../../docs/13-CAN总线.md)

## 一、功能说明

一块 BluePill 就能做完前两步。第三步才需要第二块板和收发器。

| 步骤 | 宏 | 你该看到什么 |
| --- | --- | --- |
| 环回 + 过滤器 | `APP_CAN_LOOPBACK 1` | 先发 `0x456`，过滤器丢掉；再发 `PEER_ID`，串口打出 `loopback filter ok`，PC13 翻转 |
| 双节点 | 两块板都改成 `APP_CAN_LOOPBACK 0`，对调 `NODE_ID` / `PEER_ID` | 每块板只打印对方的 ID |
| 硬件恢复 | `APP_CAN_ABOM 1`（默认） | TEC 到 256 进入 Bus-Off 后，硬件数完 128 次 11 个隐性位，自己回到主动错误。软件不调用 `HAL_CAN_Stop` |
| 软件恢复 | `APP_CAN_ABOM 0` | 错误回调只置标志，主循环里 `HAL_CAN_Stop` 再 `HAL_CAN_Start` |

位时序按 RM0008 的公式，在 APB1 = 36 MHz 上正好是 500 kbit/s：

```text
波特率 = 36 MHz / (9 × (1 + 5 + 2)) = 500 kbit/s
采样点 = (1 + 5) / 8 = 75%
```

口诀：**ID 左移 5 位才进过滤器；PB8 收、PB9 发，别去抢 USB 的 PA11。**

## 二、硬件接线表

| 模式 | 引脚 | 接法 |
| --- | --- | --- |
| 环回 | 无 CAN 脚 | 不接收发器。PB8/PB9 可以悬空 |
| 正常 | PB8 = CAN_RX，PB9 = CAN_TX | 接到 SN65HVD230 的 RXD/TXD。收发器 3.3 V |
| 总线 | CANH / CANL | 两端各一只 120 Ω。只有一个节点时，发送方会一直报错直到 Bus-Off |
| 打印 | PA9 = USART1_TX，PA10 = USART1_RX | 115200 8N1，和 USB-TTL 共地 |
| 灯 | PC13 | 板载灯，低电平亮。每收到一帧翻转一次 |

`__HAL_AFIO_REMAP_CAN1_1()` 才是 PB8/PB9。`CAN1_2` 映射到 PD0/PD1，F103C8 的 48 脚封装没有。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| RCC HSE | 晶振 | 8 MHz × 9 = 72 MHz，APB1 = 36 MHz |
| CAN1 | 使能 | 生成 `stm32f1xx_hal_can.c`。引脚以本文件的重映射为准 |
| USART1 | 异步 115200 | PA9/PA10 |
| SYS Debug | Serial Wire | 留住 PA13/PA14 |
| NVIC | `USB_LP_CAN1_RX0`、`CAN1_SCE` | 接收和 Bus-Off 不在同一个 IRQ |

用本目录的 `main.c` 覆盖 `Core/Src/main.c`。如果 Cube 把 `HAL_CAN_MspInit` 生成在 `stm32f1xx_hal_msp.c` 里，删掉那一份，避免重复定义。

## 四、编译烧录

1. CubeIDE / Keil / PlatformIO 新建 STM32F103C8 工程，框架选 STM32Cube HAL（工程里要有 `stm32f1xx_hal_can.c`）。
2. 覆盖 `main.c`，编译下载。
3. 串口助手 115200。环回模式下应看到 `loopback filter ok`，随后每 500 ms 一行 `rx id=0x102`。

PlatformIO 可参考：`board = bluepill_f103c8`，`framework = stm32cube`，本文件放进 `src/`。

## 五、预期现象

- 环回：`0x456` 没有 `rx` 行；`0x102` 有，且 `d0=0xA5`。
- 双节点：A 的 `NODE_ID=0x101`、`PEER_ID=0x102`，B 对调。A 的串口只出现 `0x102`。
- Bus-Off：正常模式、总线上没有第二个应答节点时，发几帧后串口出现 `bus-off`。ABOM 打开时不必再看到 `software restart`。

自测：

1. 为什么环回里发出去的 `NODE_ID`（0x101）不会被自己收下来？
2. `FilterIdHigh = PEER_ID << 5` 的 5 是从哪一段位移来的？
3. ABOM 打开以后，软件还要不要 `HAL_CAN_Start` 第二次？

## 六、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 环回也收不到 | 过滤器 ID 没左移，或通知没开 | 对照 `can_filter_peer`，确认 `CAN_IT_RX_FIFO0_MSG_PENDING` |
| 正常模式立刻 Bus-Off | 总线上只有你一个节点，没人 ACK | 接第二块板，或先用环回 |
| 双节点全是错误帧 | 两端位时序不一致，或没接 120 Ω | 两边都用 Prescaler 9 / BS1 5 / BS2 2 |
| 下载后 SWD 消失 | 把 PA13/PA14 配成了别的复用 | 本示例不动这两只脚 |
| 和 USB 示例抢中断 | `USB_LP_CAN1_RX0` 是同一条 IRQ | CAN 和 USB 设备不要编进同一个工程 |

## 七、相关资源

- RM0008 第 21 章 bxCAN（`CAN_BTR`、过滤器、ABOM）。
- 配图：[`assets/animations/can-arbitration.svg`](../../assets/animations/can-arbitration.svg)（自绘矢量图，不是实拍）。
- 本示例没有在仿真器里跑过。Wokwi 的 BluePill 模型不含 bxCAN。
