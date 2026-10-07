# 13 CAN 总线

> CAN 用差分信号与无损仲裁实现多节点可靠通信，是汽车与工控领域最经典的总线之一。

<p align="center">
  <img src="../assets/animations/can-arbitration.svg" width="760" alt="CAN 非破坏性仲裁与位填充动画">
  <br><sub>▲ 动画：CAN 非破坏性仲裁与位填充（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch13 -->
<p align="center">
  <img src="../assets/video/ch13-can.gif" width="640" alt="第 13 章讲解幻灯">
  <br><sub>▲ 本章讲解幻灯：程序生成的 GIF（tools/gen_videos.py，可复现，不是实拍）。旁白与五帧一一对应。</sub>
</p>

**旁白（跟着画面读，大约一分钟）**

1. CAN 用差分线。显性是逻辑 0，能压过隐性。所以 ID 越小越优先。
2. 仲裁是非破坏的。输的人立刻改听，赢的那帧一个位都没坏。
3. 连续五个同电平要插一位相反的填充位，好让对方还能同步。
4. MCU 里只有控制器。收发器和两端的 120 欧，得你自己接上。
5. 口诀：TEC 到 256 就闭嘴。自测：为什么单节点会进 Bus-Off？
<!-- /video:ch13 -->


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

- 总线两端各接一个 **120 Ω 终端电阻**，消除反射、保证差分阻抗约 60 Ω。
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
| 1 Mbps | 4 | 5 Tq | 3 Tq | 66.7% | 短距离 |
| 500 kbps | 8 | 6 Tq | 3 Tq | 70% | 常用 |
| 250 kbps | 16 | 6 Tq | 3 Tq | 70% | 工控常用 |
| 125 kbps | 32 | 6 Tq | 3 Tq | 70% | 长距离 |
| 100 kbps | 40 | 6 Tq | 3 Tq | 70% | — |

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
| BluePill (F103) | CAN1 | PA11=CAN_RX、PA12=CAN_TX | 外接 TJA1050/SN65HVD230 收发器 |
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
    hcan.Init.Prescaler            = 8;                 /* 36MHz/(8×(1+6+3))=500k */
    hcan.Init.Mode                 = CAN_MODE_NORMAL;
    hcan.Init.SyncJumpWidth        = CAN_SJW_1TQ;
    hcan.Init.TimeSeg1             = CAN_BS1_6TQ;
    hcan.Init.TimeSeg2             = CAN_BS2_3TQ;
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

## ⚠️ 常见坑与排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 完全通信不上 | 收发器未接 / 供电错 | 检查 TXD/RXD 与 3.3V/5V |
| 偶发错误、重传多 | 采样点不一致 / 无终端电阻 | 统一 BS1/BS2；两端加 120 Ω |
| 收不到指定 ID | 过滤器配置错（ID 未左移） | 标准帧 ID 左移 5 位 |
| 只能发不能收 | RXD 接错或过滤器未激活 | 核对引脚与 `FilterActivation` |
| 进入 Bus-Off | 短路 / 无其他节点 ACK | 检查总线，`AutoBusOff` 恢复 |
| 长距离丢帧 | 波特率过高 | 降速（≤125 kbps 可到 500 m） |
| 扩展帧 ID 错 | 未分基础/扩展 ID | `IDE=CAN_ID_EXT`，填 `ExtId` |

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