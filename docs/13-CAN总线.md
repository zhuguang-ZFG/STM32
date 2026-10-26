# 13 CAN 总线

> English: [CAN](en/13-can.md)

> CAN 用差分信号与无损仲裁实现多节点可靠通信，是汽车与工控领域最经典的总线之一。

<p align="center">
  <img src="../assets/animations/can-arbitration.svg" width="760" alt="CAN 非破坏性仲裁与位填充动画">
  <br><sub>▲ 动画：CAN 非破坏性仲裁与位填充（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch13 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch13-can.png">
    <source src="../assets/video/ch13-can.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解 2.8 分钟。配音是微软 Edge 在线神经语音「晓晓」（zh-CN-XiaoxiaoNeural），经 edge-tts 调用。edge-tts 大部分源码为 LGPLv3，srt_composer.py 为 MIT；声线模型是微软在线服务，不是开放模型。这里提交的是合成后的 MP4，离线可看。重新生成需要联网。画面由脚本和本仓库 SVG 生成，不是实拍。 视频：<a href="../assets/video/ch13-can.mp4">MP4</a> · 字幕：<a href="../assets/video/ch13-can.srt">SRT</a>。由 <code>python3 tools/gen_narrated.py --speak</code> 用 ffmpeg 合成。</sub>
</p>

**旁白（与字幕、配音同一份稿）**

1. CAN 发出去要有人应答。只有一个节点、又不是回环时，错误计数会一直涨。发送错误计数到 256，节点进入总线关闭，它就闭嘴了。这不是收发器坏了。
2. 先把控制器配成回环，自己发给自己。能收到，说明波特率和过滤器大体对了。再接到真正的总线。示例工程默认就是这条回环路。
3. F103 的 APB1 若是 36 兆，500 千比特要用预分频 9、位段 1 是 5、位段 2 是 2。一共 8 个时间份额，采样点在 75%。原先那组除不尽，实际只有 450 千比特。
4. 这一帧是仓库画的仲裁。线上是线与，显性位能盖过隐性位。标识更小的那一帧会留下来，输的那一方安静地改去接收。所以标识不是随便填的装饰。
5. 过滤器决定哪些标识能进接收邮箱。掩码模式里，掩码为 1 的位必须相同。标准标识在 32 位过滤器里要左移到正确的位置。放错一位，总线上有帧，你的邮箱仍是空的。
6. CAN1 默认在 PA11 和 PA12，和 USB 撞车。BluePill 上改到 PB8 接收、PB9 发送，用的是 CAN1 的第一种重映射。不要配成去 PD0、PD1 的那一种，C8 没有那两只脚。
7. 自动总线恢复可以让控制器自己试着回来。关掉它，就要在错误回调里停掉再重新启动。不管哪一种，总线上的接线、终端电阻和波特率得先改对，不然它还会再闭嘴。
8. 两块板子练习时，关掉回环，两边标识对调，总线两端各放 120 欧。收发器的电平要和模块匹配。单看回环全绿，不代表两块板子已经能对话。
9. 口诀：发送错误计数到 256 就闭嘴。单节点不要用正常模式考验自己。500 千比特在 36 兆上，记预分频 9 和一共 8 个时间份额。
10. 合上书，三问。为什么只有一个节点、又不是回环时会进总线关闭？36 兆下 500 千比特的预分频是多少？PB8 和 PB9 哪只是接收？
<!-- /video:ch13 -->

## 原理与边界

这一章的位时间和工作脚只钉在订货号 STM32F103C8T6 上。CAN1 的内核时钟是 APB1 的 36 MHz，跟第 02 章同一笔。工作点整格照抄罗盘：预分频 9，BS1 = 5，BS2 = 2，SJW = 1。见 [RM0008 Rev 21 bxCAN](#source-rm0008-can)。

时间份额 `Tq = 9 / 36e6 = 250` ns。同步段 1，加 BS1 的 5，加 BS2 的 2，一共 8。位时间 `8 × 250 ns = 2` µs，也就是 500 kbit/s。采样点 `(1 + 5) / 8 = 75%`，落在 1.5 µs。这是正常路径。

想要 10 个时间份额、采样点 70%（BS1 = 6，BS2 = 3）时，预分频是 7.2，不是整数。写成 8 时，`36e6 / (8 × 10) = 450` kbit/s。这是失败路径。1 Mbit/s 留在核心原理，不作为这一节的工作点。

BluePill 上用第一种重映射：第 45 脚 PB8 = CAN_RX，第 46 脚 PB9 = CAN_TX。复位默认是第 32 脚 PA11 = CAN_RX，第 33 脚 PA12 = CAN_TX。那一对是第 14 章 USB 的正常路径。见 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。

第 5 脚 PD0、第 6 脚 PD1 在 LQFP48 上有，它们是 HSE。重映射到这两只脚会停掉 8 MHz 晶振。见 [DS5319](#source-ds5319-clock)。RM0008 §9.3.3 写明，36、48 和 64 脚封装不能把 CAN 重映射到端口 D。第 45 脚和第 46 脚也是第 07 章的 I2C1 重映射。这一张主图不把 CAN 和 I2C 画成同时有效。见 [DS5319](#source-ds5319-i2c)。

总线两端各一只 120 Ω，接在 CANH 与 CANL 之间。MCU 的 PB8/PB9 进收发器的 RXD/TXD，收发器才出 CANH/CANL。两只 120 Ω 并联，直流负载是 60 Ω。60 Ω 不是电缆的特性阻抗。

只有一个节点、又不是回环时，没有应答，发送错误计数涨到 256，节点停止驱动总线。恢复是 128 次、每次 11 个连续隐性位。32 位掩码里，标准 ID 写入 `FilterIdHigh` 时左移 5 位。不左移时，总线上有帧，邮箱仍是空的。14 组过滤器和 2 个 FIFO 留在边界。见 [本仓库例程](#source-project-examples)。

中容量表印刷的向量名是 `USB_LP_CAN_RX0`，与第 14 章是同一条向量。互联型表才印 `USB_LP_CAN1_RX0`。两个例程不要编进同一个工程。见 [RM0008](#source-rm0008-usb)。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-13-can-bit.svg" width="760" alt="36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；写成预分频 8 和 10 个时间份额是 450 kbit/s；工作脚是第 45 脚和第 46 脚">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径是 8 个 250 ns 的时间份额，采样点 75%，2 µs，500 kbit/s，预分频 9，SJW = 1。120 Ω 接在 CANH 与 CANL 上。失败路径是预分频 8、10 个时间份额、450 kbit/s、采样点 70%。工作脚是第 45 脚 PB8 和第 46 脚 PB9。出处是 [RM0008 Rev 21 bxCAN](#source-rm0008-can) 和 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/can-500k.gif" width="640" alt="8 个时间份额走过 2 µs，采样点在 75%">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：8 个 250 ns 的时间份额，采样点 75%，500 kbit/s。印刷以静态主图为准。450 kbit/s 和晶振脚不在这条 GIF 上。</sub>
</p>

`can-arbitration.svg` 留作辅图。仲裁和位填充不进这张静态主图。

## 时序或状态

| 预分频 | BS1 | BS2 | 时间份额数 | 位时间 | 速率 | 采样点 |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | 5 | 2 | 8 | 2 µs | 500 kbit/s | 75%。时间份额 250 ns。正常 |
| 8 | 6 | 3 | 10 | 不是 2 µs | 450 kbit/s | 70%。失败 |
| 脚位 | PB8 收 | PB9 发 | 第 45 脚、第 46 脚 | — | — | PA11/PA12 与 USB 冲突 |
| 错误 | 计数到 256 | 总线关闭 | 128 次 | 每次 11 个隐性位 | — | 之后才可以再驱动 |
| 过滤器 | `FilterIdHigh` | 左移 5 | — | — | — | 不左移则邮箱仍空 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 示波器或分析仪上是 450 kbit/s | 预分频和段数配成了除不尽的那一档 | 预分频用 9，BS1 用 5，BS2 用 2 | [RM0008](#source-rm0008-can) | 8 个时间份额、预分频 9，在 36 MHz 下是 500 kbit/s。10 个时间份额配预分频 8 是 450 kbit/s |
| 单节点、正常模式，发几帧就闭嘴 | 没有应答，发送错误计数涨满 | 先用回环。上总线时要有应答节点 | [RM0008](#source-rm0008-can) | 发送错误计数到 256 进入总线关闭。恢复要 128 次、每次 11 个隐性位 |
| 总线上有帧，邮箱是空的 | 标准 ID 没有左移 | 写入 `FilterIdHigh` 时左移 5 | [本仓库例程](#source-project-examples) | `examples/can-bxcan` 用 `PEER_ID << 5` 填 `FilterIdHigh`。预分频宏是 9 |
| 两端都在报错 | 位时间不一致，或终端没接在总线两端 | 两端同一组位时间，CANH 与 CANL 之间两端各 120 Ω | [本仓库例程](#source-project-examples) | 例程要求两端各一只 120 Ω。这一行不规定电缆特性阻抗，也不规定收发器是 5 V 还是 3.3 V |
| 波形在 PA11/PA12，USB 也失效 | 还停在复位默认脚上 | 重映射到第 45 脚和第 46 脚 | [DS5319](#source-ds5319-usbcan) | 复位默认 CAN 在 PA11/PA12。PB8/PB9 是重映射。PA11/PA12 同时是 USB |
| 重映射到晶振脚之后时钟停了 | 那两只脚接着 HSE | 不要把 CAN 放到第 5 脚和第 6 脚 | [DS5319](#source-ds5319-clock) | LQFP48 第 5 脚是 PD0-OSC_IN，第 6 脚是 PD1-OSC_OUT。这两只脚存在 |
| 和 I2C 重映射抢同一对脚 | PB8/PB9 也是 I2C1 的重映射 | 这一对脚只选择 CAN 或 I2C 之一 | [DS5319](#source-ds5319-i2c) | 第 45 脚 PB8、第 46 脚 PB9 是 I2C1 的重映射。不改写第 07 章那张图 |

## 📌 学习目标

- [ ] 理解差分电平、显性/隐性、位填充、CRC、ACK 的作用。
- [ ] 分清数据帧/遥控帧/错误帧/过载帧，以及标准帧（11 位）与扩展帧（29 位）ID。
- [ ] 掌握非破坏性仲裁原理，理解「ID 越小优先级越高」。
- [ ] 会算波特率与采样点（BS1/BS2/SJW），并据此配置 `CAN_BTR`。
- [ ] 会配置过滤器与 F1 的双 FIFO 收发。

## 🧠 核心原理

### 1. 物理层：差分信号与显性/隐性

**结论**：CAN 用一对差分线 `CAN_H`/`CAN_L` 传输，**显性（Dominant）代表逻辑 0、隐性（Recessive）代表逻辑 1**；显性会覆盖隐性（线与逻辑），这是仲裁的基础。

| 逻辑值 | 总线状态 | CAN_H - CAN_L 差分 | 备注 |
| --- | --- | --- | --- |
| 0 | 显性 Dominant | 约 +2 V | 任一节点拉低即可产生，**优先级高** |
| 1 | 隐性 Recessive | 约 0 V | 只有所有节点都发隐性才是隐性 |

- 总线两端各接一只 **120 Ω**，接在 CANH 与 CANL 之间，不接在 MCU 脚上。两只 120 Ω 并联，直流负载是 60 Ω。60 Ω 不是电缆的特性阻抗。
- 收发器（TJA1050 / SN65HVD230 等）负责把单片机的 `CAN_TX`/`CAN_RX` TTL 电平转换成差分电平。**MCU 内部只有 CAN 控制器，不含收发器，必须外接。**
- 速率与长度经验：1 Mbps 时总线 ≤ 40 m；125 kbps 时可到约 500 m（速率越高距离越短）。

### 2. 位填充、CRC 与 ACK

| 机制 | 作用 | 规则 |
| --- | --- | --- |
| 位填充 Bit Stuffing | 保证有足够跳变，便于接收端再同步 | 连续 5 个相同电平后自动插入 1 个相反位（CRC 定界符前的固定填充除外） |
| CRC | 检错 | 15 位 CRC + 1 位界定符，发端计算、收端校验，错则发错误帧 |
| ACK | 确认送达 | 发端在 ACK 槽发隐性；**任一正确接收的节点拉显性**表示确认 |
| 错误计数 | 节点故障隔离 | TEC/REC 计数，超过阈值进入 error-passive/bus-off |

### 3. 帧类型与 ID

| 帧类型 | 用途 |
| --- | --- |
| 数据帧 Data Frame | 携带 0~8 字节数据 |
| 遥控帧 Remote Frame | 请求其他节点发送指定 ID 的数据 |
| 错误帧 Error Frame | 检测到错误时主动/被动发送 |
| 过载帧 Overload Frame | 接收方需要延迟下一帧 |

**数据帧结构**：`SOF(1)` + 仲裁场（11/29 位 ID + RTR）+ 控制场（IDE/r0/DLC）+ 数据场（0~8 B）+ CRC 场 + ACK 场 + EOF（7 位隐性）+ IFS。

- **标准帧**：11 位 ID（`IDE=0`），兼容性好、开销小。
- **扩展帧**：29 位 ID（`IDE=1`），由 11 位基础 ID + 18 位扩展 ID 组成。

### 4. 非破坏性仲裁

**结论**：多个节点同时发送时，**逐位仲裁**——谁发隐性却监测到显性，谁就立即退出转接收；赢得仲裁的报文**不会被破坏**，故称「非破坏性」。**ID 数值越小，优先级越高。**

| ID（标准帧） | 优先级 | 典型用途 |
| --- | --- | --- |
| `0x000` | 最高 | 紧急/控制 |
| `0x100` | 较高 | 实时控制 |
| `0x500` | 中 | 状态上报 |
| `0x7FF` | 最低 | 非关键/日志 |

> 仲裁在「仲裁场」进行；一旦某节点失去仲裁，它会自动转为接收状态，等总线空闲后重发，**不消耗重传次数、也不产生错误帧**。

### 5. 波特率与采样点

**结论**：一个位时间 `T_bit = 1/NBaud` 由 `SYNC_SEG(1 Tq)` + `BS1` + `BS2` 组成；采样点一般取在 **75%~87.5%**。

```
BaudRate = f_APB1 / (Prescaler × (1 + BS1 + BS2))
采样点位置 = (1 + BS1) / (1 + BS1 + BS2) × 100%
Tq = Prescaler / f_APB1
```

以 **F1（APB1=36 MHz）** 为例：

| 目标波特率 | Prescaler | BS1 | BS2 | 采样点 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 Mbps | 4 | 5 Tq | 3 Tq | 66.7% | 36 MHz / (4×9) = 1 MHz，短距离 |
| 500 kbps | 9 | 5 Tq | 2 Tq | 75% | 36 MHz / (9×8) = 500 kHz |
| 250 kbps | 18 | 5 Tq | 2 Tq | 75% | 分频再翻一倍 |
| 125 kbps | 36 | 5 Tq | 2 Tq | 75% | 长距离 |
| 100 kbps | 45 | 5 Tq | 2 Tq | 75% | 36 MHz / (45×8) = 100 kHz |

> 采样点想卡在 70%（BS1=6、BS2=3，一共 10 个 TQ）时，500 kbit/s 需要的预分频是 7.2，不是整数。上面改成能整除的 8 个 TQ、75% 采样点。示例 [`examples/can-bxcan`](../examples/can-bxcan/) 用的就是 500 kbit/s 这一行。1 Mbps 那一行的采样点是 66.7%。「采样点一般在 75% 到 87.5%」不覆盖这一行。四块的工作点只取 500 kbit/s。

> **SJW（再同步跳转宽度）** 用于吸收各节点时钟误差，一般取 1~2 Tq。采样点不一致是 CAN 通信偶发错误的首要原因，多节点必须统一。

### 6. 过滤器与双 FIFO（F1）

**结论**：F1 的 bxCAN 有 **14 个过滤器组** 和 **2 个接收 FIFO**；过滤器把「ID 匹配的报文」路由到 FIFO0 或 FIFO1，用中断/轮询取出。

| 模式 | 说明 | 关键寄存器 |
| --- | --- | --- |
| 掩码模式 Mask | ID + 掩码，掩码位=1 必须匹配、=0 不关心 | `CAN_FiR1`/`CAN_FiR2` |
| 列表模式 List | 多个 ID 精确匹配 | `CAN_FiR1`/`CAN_FiR2` |
| 位宽 | 32 位（标准+扩展）或 16 位（两个标准 ID） | `CAN_FS1R` |
| FIFO 分配 | 每组可关联 FIFO0 或 FIFO1 | `CAN_FFA1R` |

> F4 的 bxCAN 结构与之类似（也是 14 组过滤器 + 2 FIFO，见 RM0090 第 32 章 Controller area network），寄存器命名基本一致。

## 🛠️ 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill (F103) | CAN1 | PB8=CAN_RX、PB9=CAN_TX | 第一种重映射。第 45 脚收，第 46 脚发。PA11/PA12 是复位默认，和 USB 冲突，不走这条正常路径。外接 TJA1050/SN65HVD230 |
| BluePill | 收发器 | CANH/CANL | 两端各 120 Ω 终端电阻 |
| Nucleo-F411RE | CAN1 | PD0=CAN_RX、PD1=CAN_TX | 需外接收发器 |
| 任意 | 调试 | USART1 | 打印收发结果 |

接线：`CAN_TX → 收发器 TXD`，`CAN_RX → 收发器 RXD`，收发器 `CANH/CANL` 接总线；**收发器供电注意电平**（SN65HVD230 是 3.3 V，TJA1050 是 5 V）。

## 💻 代码实现

**① CAN 初始化（F1，500 kbps）**

```c
#include "stm32f1xx_hal.h"

CAN_HandleTypeDef hcan;

static void MX_CAN_Init(void)
{
    hcan.Instance                  = CAN1;
    hcan.Init.Prescaler            = 9;                 /* 36MHz/(9×(1+5+2))=500k */
    hcan.Init.Mode                 = CAN_MODE_NORMAL;
    hcan.Init.SyncJumpWidth        = CAN_SJW_1TQ;
    hcan.Init.TimeSeg1             = CAN_BS1_5TQ;
    hcan.Init.TimeSeg2             = CAN_BS2_2TQ;
    hcan.Init.TimeTriggeredMode    = DISABLE;
    hcan.Init.AutoBusOff           = ENABLE;
    hcan.Init.AutoWakeUp           = DISABLE;
    hcan.Init.AutoRetransmission   = ENABLE;
    hcan.Init.ReceiveFifoLocked    = DISABLE;
    hcan.Init.TransmitFifoPriority = DISABLE;
    HAL_CAN_Init(&hcan);
}
```

**② 过滤器：只收 0x123（掩码模式）**

```c
static void CAN_Filter_Init(void)
{
    CAN_FilterTypeDef f = {0};
    f.FilterBank           = 0;
    f.FilterMode           = CAN_FILTERMODE_IDMASK;
    f.FilterScale          = CAN_FILTERSCALE_32BIT;
    f.FilterIdHigh         = 0x123 << 5;   /* 标准帧 ID 左移 5 位 */
    f.FilterIdLow          = 0x0000;
    f.FilterMaskIdHigh     = 0x7FF << 5;   /* 11 位全部必须匹配 */
    f.FilterMaskIdLow      = 0x0000;
    f.FilterFIFOAssignment = CAN_RX_FIFO0;
    f.FilterActivation     = ENABLE;
    HAL_CAN_ConfigFilter(&hcan, &f);
    HAL_CAN_Start(&hcan);
    HAL_CAN_ActivateNotification(&hcan, CAN_IT_RX_FIFO0_MSG_PENDING);
}
```

**③ 发送与接收**

```c
void CAN_Send(uint16_t std_id, uint8_t *data, uint8_t len)
{
    CAN_TxHeaderTypeDef tx = {0};
    uint32_t mailbox;
    tx.StdId = std_id;
    tx.IDE   = CAN_ID_STD;
    tx.RTR   = CAN_RTR_DATA;
    tx.DLC   = len;
    HAL_CAN_AddTxMessage(&hcan, &tx, data, &mailbox);
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
    CAN_RxHeaderTypeDef rx;
    uint8_t data[8];
    HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rx, data);
    /* 处理 rx.StdId / data */
}
```

## 🧪 动手实验

1. **单节点自测（回环模式）**：把 CAN 配成 `CAN_MODE_LOOPBACK`，自发自收，串口打印收到的 ID 与数据。预期：能收到自己发出的帧，无需收发器和总线。
2. **双节点通信**：两块 BluePill + 收发器，A 发 B 收，总线两端各接 120 Ω。预期：B 稳定收到 A 的报文，串口打印一致。
3. **过滤器验证**：节点配「只收 0x123」，另一个节点分别发 0x123 与 0x456。预期：只打印 0x123 的帧，0x456 被过滤掉。
4. **（进阶）优先级观察**：两个节点同时发送不同 ID，用逻辑分析仪抓总线，验证 ID 小的先胜出。

### 7. 总线关闭之后怎么回来

**结论**：发送错误计数 TEC ≥ 256，节点进入 Bus-Off，不再驱动总线。恢复条件是总线上出现 **128 次、每次 11 个连续隐性位**。硬件可以自己等，这就是 ABOM。

```c
hcan.Init.AutoBusOff = ENABLE;   /* ABOM：数够 128×11 个隐性位后自动回到主动状态 */
```

没有别的节点应答时，发送方会一直报错直到 Bus-Off。单板调试先用环回模式，不要以为收发器坏了。

口诀：**TEC 到 256 就闭嘴；128 段 11 个隐性位才准再开口。**

自测：

1. 总线上只有一个节点，它为什么发几帧就进 Bus-Off？
2. `AutoBusOff` 打开之后，软件还要不要写“重新 Start”？
3. 标准帧 ID 0x100 仲裁时，最先和 0x200 比的是哪一位？

## 🔗 相关资源

- RM0008《STM32F10xxx 参考手册》第 21 章 Controller area network (bxCAN)（含 `CAN_BTR` 位定义、过滤器、双 FIFO）。
- RM0090《STM32F4 参考手册》第 32 章 Controller area network (bxCAN)。
- ISO 11898-1（CAN 数据链路层）与 ISO 11898-2（物理层）。
- 收发器数据手册：TJA1050、SN65HVD230。
- 配图：`../assets/animations/can-arbitration.svg`（作者自绘矢量图）。
- 可编译示例：[examples/can-bxcan](../examples/can-bxcan/)（环回、双节点、过滤器、ABOM 与软件恢复）。BluePill 上请重映射到 PB8/PB9，不要占用板载 USB 的 PA11/PA12。

- 📱 手机阅读版：[第 13 章 · CAN总线（公众号图文）](https://mp.weixin.qq.com/s/KvjVL15tp4MOqeR_5rxUbA)