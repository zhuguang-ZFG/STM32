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
  <br><sub>▲ 本章讲解视频（2.8 分钟）。<a href="../assets/video/ch13-can.mp4">MP4</a> · <a href="../assets/video/ch13-can.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

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

</details>
<!-- /video:ch13 -->

## 学习目标

读这一章之前：会按第 02 章把主频配到 72 MHz，知道这时 APB1 是 36 MHz；知道第 04 章讲的中断和 NVIC；会用第 03 章的方法控制 PC13 的灯；还要认得二进制、十六进制和左移（不熟的话先读第 00 章的「零基础预备」）。

- [ ] 说清显性和隐性是什么，为什么标识（ID）数值越小越优先，输掉仲裁为什么不算出错
- [ ] 数出一帧 8 字节标准数据帧有多少位，算出它在 500 kbit/s 下占多久
- [ ] 用 36 MHz 的 APB1 算出 500 kbit/s 的预分频、BS1、BS2 和采样点，写出 `CAN_BTR = 0x00140008`
- [ ] 把 CAN1 重映射到 BluePill 的 PB8/PB9，配一个只收标准数据帧 `0x123` 的过滤器
- [ ] 先用回环模式单板跑通收发，再接收发器和第二块板组成真正的总线
- [ ] 读懂 `CAN_ESR`，说出单节点时 TEC 为什么停在 128，什么情况下才会进总线关闭

## 核心原理

**一句话结论：CAN（Controller Area Network，控制器局域网）是几个节点共用一对差分线的广播总线，谁都可以发，几个节点同时发时按标识逐位比较、数小的留下，每一帧都要有别的节点应答，出错多的节点按计数一步步退出总线；STM32F103 片内只有 CAN 控制器 bxCAN，要外接一颗收发器才能接上总线。**

### 先打个比方

把 CAN 总线想成一间没有主持人的会议室。

- 想发言先听：屋里安静（总线空闲）才能开口。谁都可以开口，说的话所有人都听得到。
- 两个人同时开口，就一个字一个字地比。规矩是「出声」压过「不出声」：同一时刻只要有人出声，全屋听到的就是出声。谁本想不出声、却听见有人出声，就知道自己输了，马上闭嘴改听，等这句说完再试。每个人开口先报编号，编号小的前面几位出声早，所以总能赢。
- 每说完一句，至少要有一个听众当场「嗯」一声。说完没人「嗯」，讲的人就给自己记一笔错。
- 错记多了，先降成只许小声说（错误被动）；再多就被请出会议室（总线关闭），要等屋里安静好一阵子才准回来。

比方到这里为止。真实的「出声」是显性位，「编号」是 11 位标识，「嗯」一声是别的节点在固定的 ACK 位上拉显性，「安静好一阵子」是 128 次、每次 11 个连续隐性位。还有一处和比方不一样：没人应答的讲者记错到一定程度会停在「小声说」，不会被请出去，第 7 节细说。

### 1. 物理层：差分信号与显性/隐性

**结论：CAN 用 CANH、CANL 两根线传一个差分信号。两线拉开约 2 V 是显性，代表 0；两线几乎一样高是隐性，代表 1。只要有一个节点发显性，整条总线就是显性，这叫「线与」，仲裁和应答都靠它。**

| 逻辑值 | 名字 | CANH − CANL（典型值） | 谁说了算 |
| --- | --- | --- | --- |
| 0 | 显性（dominant） | 约 2 V | 任何一个节点发 0，总线就是 0 |
| 1 | 隐性（recessive） | 约 0 V | 所有节点都发 1，总线才是 1 |

表里的电压是 ISO 11898-2 规定的高速 CAN 典型值，收发器的数据手册里都能查到；ST 的参考手册不管这一层。

单片机和总线之间隔着一颗收发器（transceiver）：

- STM32F103 片内只有 CAN 控制器 bxCAN，引出来的是 CAN_TX、CAN_RX 两只普通逻辑电平的脚。收发器把 CAN_TX 上的 0/1 变成 CANH/CANL 上的显性/隐性，再把总线的状态送回 CAN_RX。所以控制器发出去的每一位都会从 CAN_RX 读回来，它靠这一点知道自己有没有输掉仲裁、有没有人应答。
- 常见的收发器有 SN65HVD230（3.3 V 供电）和 TJA1050（5 V 供电）。
- 总线两端各接一只 120 Ω 电阻，跨在 CANH 和 CANL 之间，吸收信号走到线缆末端时的反射。中间的节点不接。
- 速率越高，线能拉得越短。经验值是 1 Mbit/s 时约 40 m，125 kbit/s 时约 500 m：信号要在采样点之前从最远的节点走个来回，仲裁和应答才来得及。

### 2. 一帧数据：标识、位填充、CRC 与 ACK

**结论：一帧标准数据帧由固定的几段拼成，带 N 个字节数据时，不算填充位共 44 + 8N 位。CRC 用来查错，ACK 位要由别的节点改成显性，位填充保证线上不会长时间没有跳变。**

下表从上到下是一帧标准数据帧在线上的顺序。位数和规则出自 Bosch 的 CAN 2.0 规范（ISO 11898-1 的前身）：

| 段 | 位数 | 作用 |
| --- | --- | --- |
| 帧起始 SOF | 1 | 一个显性位，所有节点据此对齐 |
| 标识 ID | 11 | 这帧装的是什么数据，也是仲裁时比的优先级 |
| RTR | 1 | 显性是数据帧，隐性是遥控帧 |
| IDE、r0 | 2 | IDE 为显性表示 11 位标识的标准帧，隐性表示 29 位的扩展帧 |
| DLC | 4 | 数据字节数，0 到 8 |
| 数据 | 8N | N 个字节 |
| CRC | 15 + 1 | 15 位校验码，加 1 位隐性的定界符 |
| ACK | 1 + 1 | 发送方在 ACK 槽发隐性，任何一个正确收到的节点把它改成显性；后面跟 1 位定界符 |
| 帧结束 EOF | 7 | 7 个隐性位 |

把位数加起来：1 + 11 + 1 + 2 + 4 + 16 + 2 + 7 = 44，再加数据的 8N。8 个字节时是 108 位，500 kbit/s 下一位 2 µs，一帧占 216 µs。两帧之间还要隔 3 个隐性位。

另外三种帧：遥控帧（RTR 为隐性，没有数据段，用来请求别的节点发某个标识的数据）、错误帧（节点发现错误时发出，作废当前这一帧）、过载帧（接收方要求推迟下一帧，很少用到）。扩展帧把标识加长到 29 位，本章只用标准帧。

一帧可信，靠的是下面三条：

- **位填充。** 从帧起始到 CRC 这一段，发送方每发完 5 个同值的位，就自动插一个相反的位，接收方再把它删掉。这样线上至少每 6 位有一次跳变，接收方能跟着跳变校准自己的时钟。CRC 定界符、ACK 和帧结束是固定格式，不填充。填充会让帧变长：8 字节的帧最坏多出 24 位，算法在自测第 3 题。
- **CRC。** 发送方按帧的内容算出 15 位校验码放进帧里，每个接收方自己再算一遍，对不上就发错误帧，这一帧作废，发送方重发。
- **ACK。** 只要有一个节点正确收到，ACK 槽就是显性。发送方在 ACK 槽读回隐性，就知道没有任何节点正确收到，给自己记一次 ACK 错误。总线上只有一个节点时，每一帧都是这个结果，第 7 节会用到。

### 3. 非破坏性仲裁：标识越小越优先

**结论：几个节点同时开始发，就从标识的最高位起逐位比较。发隐性却读回显性的节点立刻停发、改成接收；留下来的那一帧一位都没被破坏，所以叫非破坏性仲裁。标识数值越小，越早出现显性的 0，优先级越高。**

举 `0x100` 和 `0x200` 同时发送的例子。11 位标识从第 10 位（最高位）写到第 0 位：

```text
位号     10  9  8  7  6  5  4  3  2  1  0
0x100     0  0  1  0  0  0  0  0  0  0  0
0x200     0  1  0  0  0  0  0  0  0  0  0
线上      0  0
             ^ 第 9 位：0x200 发隐性 1，读回显性 0，退出
```

第 10 位两边都是 0，打平；第 9 位上 `0x100` 发显性 0，`0x200` 发隐性 1 却读回 0，于是 `0x200` 退出、转为接收，等总线空闲再重发。`0x100` 那一帧照常发完，所有节点（包括 `0x200`）都收到完整的一帧。

两点常被问到：

- 输掉仲裁不是错误，不发错误帧，也不动错误计数。
- 标识相同的数据帧和遥控帧撞在一起，数据帧赢，因为它的 RTR 位是显性。两个节点用同一个标识发不同的数据，仲裁分不出胜负，会在数据段撞出位错误，所以一个标识只给一个节点发。

### 4. 波特率与采样点：一位切成几个时间份额

**结论：bxCAN 把一位切成若干个时间份额（time quantum，记作 tq）：开头 1 个同步段，后面是位段 1（BS1）和位段 2（BS2），在 BS1 结束的那一刻采样。速率 = APB1 时钟 ÷（预分频 × 份额数）。**

公式出自 RM0008 Rev 21 第 24.7.7 节：

```text
tq      = 预分频 ÷ f_APB1                  寄存器里写 BRP = 预分频 − 1
一位    = (1 + BS1 + BS2) × tq
速率    = f_APB1 ÷ (预分频 × (1 + BS1 + BS2))
采样点  = (1 + BS1) ÷ (1 + BS1 + BS2)
```

APB1 = 36 MHz 时，常用的几档如下。每一行都能用上面的式子算回去；500 kbit/s 那一行是本章例程设定的工作点：

| 速率 | 预分频 | BS1 | BS2 | 份额数 | 采样点 | 验算 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 Mbit/s | 3 | 8 | 3 | 12 | 75% | 36 MHz ÷ (3 × 12) = 1 MHz |
| 500 kbit/s | 9 | 5 | 2 | 8 | 75% | 36 MHz ÷ (9 × 8) = 500 kHz |
| 250 kbit/s | 18 | 5 | 2 | 8 | 75% | 36 MHz ÷ (18 × 8) = 250 kHz |
| 125 kbit/s | 36 | 5 | 2 | 8 | 75% | 36 MHz ÷ (36 × 8) = 125 kHz |
| 100 kbit/s | 45 | 5 | 2 | 8 | 75% | 36 MHz ÷ (45 × 8) = 100 kHz |

选参数时注意三点：

- **预分频必须是整数。** 想要 10 个份额、采样点 70%（BS1 = 6、BS2 = 3）时，500 kbit/s 要的预分频是 36 MHz ÷ (500 kHz × 10) = 7.2，填不进寄存器。写成 8，速率就变成 36 MHz ÷ (8 × 10) = 450 kbit/s，和别的节点对不上。
- **各段有范围。** `CAN_BTR` 里 BS1 能填 1–16 个份额，BS2 能填 1–8 个，SJW 能填 1–4 个，预分频是 1–1024，由 RM0008 Rev 21 第 24.9.2 节各字段的位宽决定。
- **采样点各节点要接近。** 经验值是放在 75% 到 87.5% 之间。SJW（重同步跳转宽度）是节点每遇到一次跳变，最多能把位段拉长或缩短几个份额，用来跟上别的节点的时钟，例程设定是 1。各节点的时钟都要来自晶振，不要用片内 RC 振荡器跑 CAN（经验值）。

### 5. 过滤器与两个接收 FIFO

**结论：bxCAN 收下的每一帧先过过滤器，被某一组过滤器放行才进接收 FIFO，没有一组放行就丢掉。STM32F103 有 14 组过滤器和 2 个接收 FIFO，每个 FIFO 存 3 帧（RM0008 Rev 21 第 24.2 节）；复位后所有过滤器都没有激活（`CAN_FA1R` 复位值为 0），不配过滤器就一帧也收不到。**

每组过滤器有三项要选：

| 设置 | 选项 | 意思 |
| --- | --- | --- |
| 模式 | 掩码模式（IDMASK） | 一个标识加一个掩码：掩码为 1 的位必须和标识相同，为 0 的位不管 |
| 模式 | 列表模式（IDLIST） | 两个寄存器都放标识，帧的标识必须等于其中一个 |
| 位宽 | 32 位 | 一组过滤器管一对 32 位的标识和掩码，标准帧、扩展帧都能比 |
| 位宽 | 16 位 | 一组拆成两对 16 位的，只适合标准帧 |
| 去向 | FIFO0 或 FIFO1 | 这一组放行的帧进哪个 FIFO |

32 位掩码模式下，寄存器的每一位对着帧里的哪一位，见 RM0008 Rev 21 第 24.7.4 节的图 230：

```text
位号    31 ...... 21 | 20 ........ 3 |  2  |  1  |  0
内容    STID[10:0]   | EXID[17:0]    | IDE | RTR |  0
HAL     FilterIdHigh = 第 31-16 位      FilterIdLow = 第 15-0 位
```

11 位的标准标识占第 31–21 位，落在高 16 位 `FilterIdHigh` 的第 15–5 位上，所以写进去之前要左移 5 位。本章的过滤器这样填：

| 字段 | 值 | 意思 |
| --- | --- | --- |
| `FilterIdHigh` | `0x123 << 5 = 0x2460` | 期望的标识 |
| `FilterIdLow` | `0x0000` | 期望 IDE = 0（标准帧）、RTR = 0（数据帧） |
| `FilterMaskIdHigh` | `0x7FF << 5 = 0xFFE0` | 11 位标识每一位都要相同 |
| `FilterMaskIdLow` | `0x0006` | IDE、RTR 两位也要相同 |

这样只收 `0x123` 的标准数据帧；高 11 位同样是 `0x123` 的扩展帧、`0x123` 的遥控帧都进不来。掩码的低 16 位写成 0 的话，这两种帧也会被放行。

### 6. 工作模式：先回环，再上总线

**结论：bxCAN 复位后在睡眠模式，配置要在初始化模式里做，配完切到正常模式才收发。调试时先用回环模式：控制器在内部把发送接到接收，不看 CAN_RX 脚，也不要求应答，一块板、不接收发器就能自发自收。**

下表的进入方法出自 RM0008 Rev 21 第 24.4 节和第 24.5 节：

| 模式 | 怎么进 | 收发 | 用途 |
| --- | --- | --- | --- |
| 睡眠 | 复位后默认 | 不收不发 | 省电 |
| 初始化 | `CAN_MCR` 的 INRQ 置 1 | 不收不发 | 写位时间、选模式，`CAN_BTR` 只能在这时写 |
| 正常 | INRQ 清 0，再在 CAN_RX 上等到 11 个连续隐性位 | 收发 | 接真正的总线 |
| 回环 | `CAN_BTR` 的 LBKM 置 1 | 发出的帧自己收下，CAN_TX 脚上照样有波形 | 单板自测 |
| 静默 | `CAN_BTR` 的 SILM 置 1 | 只收不发，连 ACK 也不发 | 接到别人的总线上旁听 |

`HAL_CAN_Start()` 就是「INRQ 清 0，再等硬件确认」这一步。正常模式下 CAN_RX 一直是显性，比如收发器没供电、RX 接错了脚，它等不到那 11 个隐性位，会超时返回错误。

推荐的顺序是先回环、后总线。回环能收到，说明位时间、过滤器和中断都对；它证明不了的是收发器、接线、终端和对方的位时间，这些要到两块板对发时才见分晓。

### 7. 错误状态：总线关闭之后怎么回来

**结论：每个节点有发送错误计数 TEC 和接收错误计数 REC。任一个超过 127，节点进入错误被动；TEC 超过 255，进入总线关闭，不再收发；要回到总线上，必须先在 CAN_RX 上数够 128 次、每次 11 个连续隐性位。**

三种状态的门槛出自 RM0008 Rev 21 第 24.7.6 节的图 233，出错时发什么出自 CAN 2.0 规范：

| 状态 | 条件 | 出错时 | 能否收发 |
| --- | --- | --- | --- |
| 错误主动 | TEC、REC 都不超过 127 | 发 6 个显性位的主动错误标志，当场作废这一帧 | 能 |
| 错误被动 | TEC 或 REC 超过 127 | 只发 6 个隐性位的被动错误标志，破坏不了别的节点正在发的帧 | 能 |
| 总线关闭 | TEC 超过 255 | 不发 | 不能 |

计数的规矩出自 CAN 2.0 规范第 8 节。简单说：发送方每出一次错 TEC 加 8，每成功发出一帧减 1；接收方出错时 REC 一般加 1，每成功收到一帧减 1。

总线上只有一个节点、又不在回环模式时，结果取决于有没有收发器：

- **接着收发器，只是没有别的节点。** 每一帧都没人应答，TEC 每次加 8，第 16 次到 128，进入错误被动。CAN 2.0 规范第 8 节对这种情况有一条例外：错误被动的发送方因为没人应答而出的 ACK 错误，不再加 TEC。于是 TEC 停在 128，控制器一遍遍重发，不会进总线关闭。
- **没接收发器。** PB9 发出的显性位回不到 PB8，PB8 只靠上拉读到隐性，每一帧在第一位就是位错误。位错误没有那条例外，TEC 一路涨过 255，进入总线关闭。

从总线关闭回来有两种办法：

- **ABOM = 1**（HAL 里写 `AutoBusOff = ENABLE`）：控制器一进总线关闭，就自己开始数那 128 次 11 个隐性位，数够了回到错误主动。
- **ABOM = 0**：软件要让控制器进、出一次初始化模式，HAL 里就是 `HAL_CAN_Stop()` 再 `HAL_CAN_Start()`。初始化模式里控制器不看 CAN_RX，所以离开初始化模式以后，仍然要在正常模式里数够这 128 次（RM0008 Rev 21 第 24.7.6 节）。

两种办法都至少要等 128 × 11 = 1408 个位时间，500 kbit/s 下是 1408 × 2 µs ≈ 2.8 ms。接线、终端或位时间不改对，节点回来以后还会再关掉。

口诀：**TEC 过 255 就闭嘴，128 段 11 个隐性位才准再开口；没人应答只会停在 128。**

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill（STM32F103C8T6） | CAN1 | PB8=CAN_RX、PB9=CAN_TX | 第 45、46 脚。要用重映射 `CAN_REMAP = 10`，HAL 宏是 `__HAL_AFIO_REMAP_CAN1_2()` |
| 收发器模块 | SN65HVD230 或 TJA1050 | TXD、RXD、CANH、CANL | SN65HVD230 接 3.3 V，TJA1050 接 5 V。PB8、PB9 在 DS5319 Rev 20 表 5 里是 FT 脚，能承受 5 V |
| 总线 | 双绞线 | CANH、CANL | 两端各一只 120 Ω。很多模块板上已经焊了一只，先看模块的原理图 |
| BluePill | 板载灯 | PC13 | 低电平亮，每收到一帧翻转一次 |
| BluePill | SWD | PA13、PA14 | 烧录，在调试器里看计数 |

实验一只要一块 BluePill，不接收发器。实验二和实验三按下图接两套：

```text
BluePill A              收发器 A                                    收发器 B         BluePill B
PB9 CAN_TX ───────────▶ TXD                                         TXD ◀─────────── CAN_TX PB9
PB8 CAN_RX ◀─────────── RXD                                         RXD ───────────▶ CAN_RX PB8
3V3 ─────────────────── VCC                                         VCC ─────────────────── 3V3
GND ─────────────────── GND ─────────────────────────────────────── GND ─────────────────── GND
                        CANH ──┬───────────────────────────────┬── CANH
                               │                               │
                             120 Ω                           120 Ω
                               │                               │
                        CANL ──┴───────────────────────────────┴── CANL
收发器用 SN65HVD230 时 VCC 接 3V3；用 TJA1050 时改接 BluePill 的 5V 脚。
```

接线只有一处和第 06 章的串口相反：CAN 是同名相接，PB9（CAN_TX）接收发器的 TXD，PB8（CAN_RX）接 RXD，不交叉；两块板还要共地，图里经两只收发器的 GND 连在一起。

> [!WARNING]
> STM32F103 的 CAN 和 USB 不能同时用：两者共用一块 512 字节的 SRAM（RM0008 Rev 21 第 24.2 节），复位默认的 CAN 脚 PA11/PA12 又正好是 USB 的 D− 和 D+。BluePill 的 USB 口接在 PA11/PA12 上，所以本章把 CAN 移到 PB8/PB9。PB8/PB9 同时是 I2C1 的重映射脚，这一对脚同一时刻只能给其中一个用。

## 代码实现

下面是一份完整的 `main.c`：时钟、CAN 初始化、引脚和中断、过滤器、发送和接收回调都在里面。

CubeMX 里只做三件事：RCC 的 HSE 选晶振，SYS 的 Debug 选 Serial Wire，Connectivity 里勾上 CAN（这样工程里才有 `stm32f1xx_hal_can.c`，`HAL_CAN_MODULE_ENABLED` 也会打开）。CAN 的参数不用填，NVIC 里不要勾 CAN 的中断。生成代码以后，用下面的文件替换 `Core/Src/main.c`，再删掉 `stm32f1xx_hal_msp.c` 里生成的 `HAL_CAN_MspInit()` 和 `HAL_CAN_MspDeInit()`，免得和这里重复定义。仓库里的 [`examples/can-bxcan/`](../examples/can-bxcan/) 多了串口打印和软件恢复的开关，但它的重映射有一行要改，见「逐段看」。

```c
/* main.c —— BluePill 上的 bxCAN：500 kbit/s，回环自测或两板对发（STM32F103C8T6，HAL） */
#include "stm32f1xx_hal.h"

#define USE_LOOPBACK    1U        /* 1 = 回环，单板自测；0 = 正常模式，接收发器上总线 */
#define CAN_PRESCALER   9U        /* 36 MHz / (9 × 8) = 500 kbit/s（例程设定） */
#define TX_ID           0x123U    /* 本板发送的标准标识 */
#define RX_ID           0x123U    /* 过滤器只放行这个标识；两板对发时改成对方的 TX_ID */
#define SEND_PERIOD_MS  500U
#define LED_PORT        GPIOC
#define LED_PIN         GPIO_PIN_13

CAN_HandleTypeDef hcan;
volatile uint32_t g_rx_count;     /* 收到的帧数，在调试器里看 */
volatile uint8_t  g_rx_data[8];   /* 最近一帧的数据 */
volatile uint32_t g_esr;          /* CAN_ESR 的快照，实验三用 */

void SystemClock_Config(void);
void Error_Handler(void);
static void LED_Init(void);
static void MX_CAN_Init(void);
static void CAN_Filter_Init(void);
static void CAN_Send(uint32_t std_id, const uint8_t *data, uint8_t len);

int main(void)
{
    uint8_t payload[8] = {0, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77};

    HAL_Init();
    SystemClock_Config();
    LED_Init();
    MX_CAN_Init();
    CAN_Filter_Init();
    if (HAL_CAN_Start(&hcan) != HAL_OK) {                 /* 离开初始化模式 */
        Error_Handler();
    }
    if (HAL_CAN_ActivateNotification(&hcan, CAN_IT_RX_FIFO0_MSG_PENDING) != HAL_OK) {
        Error_Handler();
    }

    for (;;) {
        payload[0]++;                                     /* 第 0 字节当序号 */
        CAN_Send(TX_ID, payload, 8U);
        g_esr = hcan.Instance->ESR;                       /* 读错误计数和状态位 */
        HAL_Delay(SEND_PERIOD_MS);
    }
}

static void MX_CAN_Init(void)
{
    hcan.Instance                  = CAN1;
    hcan.Init.Prescaler            = CAN_PRESCALER;
    hcan.Init.Mode                 = USE_LOOPBACK ? CAN_MODE_LOOPBACK : CAN_MODE_NORMAL;
    hcan.Init.SyncJumpWidth        = CAN_SJW_1TQ;
    hcan.Init.TimeSeg1             = CAN_BS1_5TQ;
    hcan.Init.TimeSeg2             = CAN_BS2_2TQ;
    hcan.Init.TimeTriggeredMode    = DISABLE;
    hcan.Init.AutoBusOff           = ENABLE;          /* ABOM：总线关闭后硬件自己恢复 */
    hcan.Init.AutoWakeUp           = DISABLE;
    hcan.Init.AutoRetransmission   = ENABLE;          /* 没发成功就自动重发 */
    hcan.Init.ReceiveFifoLocked    = DISABLE;
    hcan.Init.TransmitFifoPriority = DISABLE;
    if (HAL_CAN_Init(&hcan) != HAL_OK) {              /* 里面会调用 HAL_CAN_MspInit() */
        Error_Handler();
    }
}

void HAL_CAN_MspInit(CAN_HandleTypeDef *h)
{
    GPIO_InitTypeDef io = {0};

    if (h->Instance != CAN1) {
        return;
    }
    __HAL_RCC_CAN1_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();
    __HAL_AFIO_REMAP_CAN1_2();                        /* CAN_REMAP = 10：PB8 收，PB9 发 */

    io.Pin  = GPIO_PIN_8;                             /* PB8 = CAN_RX */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;                            /* 什么都没接时读到隐性 */
    HAL_GPIO_Init(GPIOB, &io);

    io.Pin   = GPIO_PIN_9;                            /* PB9 = CAN_TX */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &io);

    HAL_NVIC_SetPriority(USB_LP_CAN1_RX0_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(USB_LP_CAN1_RX0_IRQn);
}

static void CAN_Filter_Init(void)
{
    CAN_FilterTypeDef f = {0};

    f.FilterBank           = 0;
    f.FilterMode           = CAN_FILTERMODE_IDMASK;
    f.FilterScale          = CAN_FILTERSCALE_32BIT;
    f.FilterIdHigh         = RX_ID << 5;              /* 标准标识在第 31–21 位 */
    f.FilterIdLow          = 0x0000U;                 /* IDE = 0 标准帧，RTR = 0 数据帧 */
    f.FilterMaskIdHigh     = 0x7FFU << 5;             /* 11 位标识全部要相同 */
    f.FilterMaskIdLow      = 0x0006U;                 /* IDE、RTR 也要相同 */
    f.FilterFIFOAssignment = CAN_FILTER_FIFO0;
    f.FilterActivation     = ENABLE;
    f.SlaveStartFilterBank = 14;                      /* 只有带 CAN2 的料才用这一项 */
    if (HAL_CAN_ConfigFilter(&hcan, &f) != HAL_OK) {
        Error_Handler();
    }
}

static void CAN_Send(uint32_t std_id, const uint8_t *data, uint8_t len)
{
    CAN_TxHeaderTypeDef tx = {0};
    uint32_t mailbox;

    if (HAL_CAN_GetTxMailboxesFreeLevel(&hcan) == 0U) {
        return;                                       /* 3 个发送邮箱都在排队：这一帧不发 */
    }
    tx.StdId              = std_id;
    tx.IDE                = CAN_ID_STD;
    tx.RTR                = CAN_RTR_DATA;
    tx.DLC                = len;
    tx.TransmitGlobalTime = DISABLE;
    (void)HAL_CAN_AddTxMessage(&hcan, &tx, (uint8_t *)data, &mailbox);
}

void USB_LP_CAN1_RX0_IRQHandler(void)                 /* 和 USB 低优先级中断共用这一个入口 */
{
    HAL_CAN_IRQHandler(&hcan);
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *h)
{
    CAN_RxHeaderTypeDef rx;
    uint8_t data[8];

    if (HAL_CAN_GetRxMessage(h, CAN_RX_FIFO0, &rx, data) != HAL_OK) {
        return;
    }
    for (uint32_t i = 0; i < rx.DLC && i < 8U; i++) {
        g_rx_data[i] = data[i];
    }
    g_rx_count++;
    HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
}

static void LED_Init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);   /* 先灭 */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
}

void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;                  /* 8 MHz 晶振 */
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;                /* 8 MHz × 9 = 72 MHz */
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        Error_Handler();
    }
    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;               /* APB1 = 36 MHz，bxCAN 用它 */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK) {
        Error_Handler();
    }
}

void Error_Handler(void)
{
    __disable_irq();
    for (;;) {
    }
}
```

逐段看：

- `CAN_PRESCALER` 的 9 加上 `CAN_BS1_5TQ`、`CAN_BS2_2TQ`，就是第 4 节表里 500 kbit/s 那一行：一个份额 250 ns，一位 8 个份额、2 µs，采样点 75%。两块板要用同一组。
- `USE_LOOPBACK` 为 1 时，HAL 置 `CAN_BTR` 的 LBKM 位。回环模式里控制器忽略 ACK 错误，也不看 CAN_RX 脚（RM0008 Rev 21 第 24.5.2 节），所以实验一不接收发器也能收到自己发的帧。
- `AutoBusOff = ENABLE` 就是第 7 节的 ABOM = 1。`AutoRetransmission = ENABLE` 表示没发成功就一直重发：单节点时同一帧会一直重发下去，3 个发送邮箱很快占满。`CAN_Send()` 先查有没有空邮箱，满了就跳过，免得 `HAL_CAN_AddTxMessage()` 报错。
- `__HAL_AFIO_REMAP_CAN1_2()` 把 `AFIO_MAPR` 的 CAN_REMAP 写成 `10`，CAN 才走 PB8/PB9（RM0008 Rev 21 第 9.4.2 节）。HAL 的三个宏按顺序编号：`_1` 是复位默认的 PA11/PA12，`_2` 是 PB8/PB9，`_3` 是 PD0/PD1，48 脚的 C8 用不了。编号容易记反：`_1` 不是「第一种重映射」，而是不重映射。
- PB8 配成上拉输入：什么都没接时读到隐性，正常模式下 `HAL_CAN_Start()` 才等得到 11 个连续隐性位。PB9 配成复用推挽输出。
- 过滤器就是第 5 节那张表：标识左移 5 位，掩码低 16 位的 `0x0006` 让 IDE、RTR 参与比较。`SlaveStartFilterBank` 只在有 CAN2 的料上起作用，F103 上 HAL 不看它。
- 中断入口的名字要和启动文件一字不差：`USB_LP_CAN1_RX0_IRQHandler`。名字写错，链接器不报错，第一帧进来时 CPU 跳进启动文件里的默认处理函数，在那里死循环。CubeMX 里勾了 CAN 的中断，`stm32f1xx_it.c` 里会再生成一个同名函数，链接时报重复定义。
- `g_esr` 每 500 ms 读一次 `CAN_ESR`，实验三把它按位拆开看。

同样的位时间和模式，用寄存器写是下面这样。它只换掉 `MX_CAN_Init()`，引脚、重映射和中断仍用上面的 `HAL_CAN_MspInit()`：

```c
/* 寄存器写法：在初始化模式里写位时间，再回正常模式（RM0008 Rev 21 第 24.4、24.9.2 节） */
#include "stm32f1xx_hal.h"

#define BTR_SJW(n)    ((uint32_t)((n) - 1U) << 24)    /* SJW[1:0]，第 25:24 位 */
#define BTR_TS2(n)    ((uint32_t)((n) - 1U) << 20)    /* TS2[2:0]，第 22:20 位 */
#define BTR_TS1(n)    ((uint32_t)((n) - 1U) << 16)    /* TS1[3:0]，第 19:16 位 */
#define BTR_BRP(n)    ((uint32_t)((n) - 1U))          /* BRP[9:0]，第 9:0 位 */
#define CAN_BTR_500K  (BTR_SJW(1U) | BTR_TS2(2U) | BTR_TS1(5U) | BTR_BRP(9U))   /* 0x00140008 */
#define WAIT_LIMIT    1000000UL

int CAN1_Init_Reg(int loopback)
{
    uint32_t t;

    __HAL_RCC_CAN1_CLK_ENABLE();
    CAN1->MCR &= ~CAN_MCR_SLEEP;                          /* 复位后在睡眠模式，先出来 */
    CAN1->MCR |= CAN_MCR_INRQ;                            /* 请求进初始化模式 */
    for (t = 0; (CAN1->MSR & CAN_MSR_INAK) == 0U; t++) {
        if (t > WAIT_LIMIT) return -1;
    }
    CAN1->MCR |= CAN_MCR_ABOM;                            /* 相当于 AutoBusOff = ENABLE */
    CAN1->MCR &= ~CAN_MCR_NART;                           /* 相当于 AutoRetransmission = ENABLE */
    CAN1->BTR = CAN_BTR_500K | (loopback ? CAN_BTR_LBKM : 0U);   /* 回环时是 0x40140008 */
    CAN1->MCR &= ~CAN_MCR_INRQ;                           /* 请求离开初始化模式 */
    for (t = 0; (CAN1->MSR & CAN_MSR_INAK) != 0U; t++) {
        if (t > WAIT_LIMIT) return -1;                    /* CAN_RX 上一直等不到 11 个隐性位 */
    }
    return 0;
}
```

`CAN_BTR` 只能在初始化模式里写（RM0008 Rev 21 第 24.9.2 节），所以写位时间一定夹在 INRQ 置 1 和清 0 之间。各段写进寄存器时都要减 1：预分频 9 写成 BRP = 8，BS1 的 5 写成 TS1 = 4，BS2 的 2 写成 TS2 = 1，SJW 的 1 写成 0，拼起来就是 `0x00140008`。

## 动手实验

1. **实验一：单板回环，自己发给自己。** 保持 `USE_LOOPBACK` 为 1，`TX_ID` 和 `RX_ID` 都是 `0x123`，只用一块 BluePill，不接收发器。
   - 预期现象：PC13 的灯每 500 ms 翻转一次，也就是 1 Hz 闪烁。
   - 怎么确认：在调试器里看 `g_rx_count` 每秒加 2，`g_rx_data[0]` 跟着发送序号走；用逻辑分析仪接 PB9，能看到一帧帧的波形，最窄的脉冲宽 2 µs。
   - 没成功先查：编译时报 `CAN_HandleTypeDef` 没定义，是 CubeMX 里没勾 CAN；`TX_ID` 和 `RX_ID` 是否相同；中断函数名是否一字不差；链接时报重复定义，是 CubeMX 也生成了 `HAL_CAN_MspInit()` 或 CAN 的中断函数；程序停在 `Error_Handler()` 时，在调试器的调用栈里看是哪一步返回了错误。
2. **实验二：两块板接上收发器，组成真正的总线。** 两块板都把 `USE_LOOPBACK` 改成 0；A 板 `TX_ID = 0x123`、`RX_ID = 0x124`，B 板 `TX_ID = 0x124`、`RX_ID = 0x123`。按「硬件与接线」的图接线，总线两端各一只 120 Ω。
   - 预期现象：两块板的灯都以 1 Hz 闪烁，各自收到的是对方的帧。断开其中一块的 CANH、CANL，另一块的灯停住不闪。
   - 怎么确认：断电后用万用表量 CANH 与 CANL 之间，两只 120 Ω 并联应读到约 60 Ω；通电后在调试器里看 `g_esr`，TEC、REC 都是 0。
   - 没成功先查：TXD、RXD 是不是同名相接；两块板的 `RX_ID` 是否都是对方的 `TX_ID`；收发器的供电对不对；如果用的是 `examples/can-bxcan`，重映射宏改成 `_2` 没有；用 5 V 的 TJA1050 不通时，先换一块 3.3 V 的 SN65HVD230 排除电平问题。
3. **实验三：看错误计数怎么涨。** 在实验二的基础上，拔掉 B 板到总线的 CANH、CANL，只留 A 板，看 `g_esr`；再把 A 板 PB8、PB9 到收发器的两根线也拔掉，看第二次。
   - 预期现象：只剩 A 板和它的收发器时，`g_esr` 停在 `0x00800033`：TEC 是 128，进入错误被动，不进总线关闭。连收发器也拔掉以后，多读几次 `g_esr`，能看到第 2 位 BOFF 置 1。把 B 板接回去，A 板每成功发出一帧 TEC 减 1，慢慢回到 0。
   - 怎么确认：把 `g_esr` 按 RM0008 Rev 21 第 24.9.2 节的 `CAN_ESR` 拆开：第 31–24 位是 REC，第 23–16 位是 TEC，第 6–4 位是 LEC（`011` 是 ACK 错误，`100`、`101` 是位错误），第 2 位 BOFF，第 1 位 EPVF（错误被动），第 0 位 EWGF（任一计数到 96）。`0x00800033` 就是 REC = 0、TEC = 0x80、LEC = 011、EPVF = 1、EWGF = 1。
   - 没成功先查：`AutoRetransmission` 是否为 `ENABLE`，关掉重发就只会出错一次；`USE_LOOPBACK` 是否已经改成 0；进了总线关闭以后，TEC 字段只是 9 位计数器的低 8 位，读数没有意义，要看 BOFF 位。

## 自测

1. APB1 是 36 MHz，预分频 9、BS1 = 5、BS2 = 2：一个时间份额多长？一位多长？在一位开始后多久采样？
2. 标准标识 `0x100` 和 `0x200` 同时开始发送，在哪一位分出胜负？输的一方要不要给自己记错？
3. 一帧 8 字节的标准数据帧，不算填充是多少位？500 kbit/s 下占多久？最坏情况下填充位再多几个？
4. 总线上只有一块板，接着收发器，用正常模式发送，TEC 最后是多少？会不会进总线关闭？把收发器也拔掉呢？
5. 500 kbit/s 下进了总线关闭，ABOM 打开时最少多久能回到总线？ABOM 关掉时软件要做什么？

参考答案：

1. tq = 9 ÷ 36 MHz = 250 ns；一位 = (1 + 5 + 2) × 250 ns = 2 µs，即 500 kbit/s；采样点在 (1 + 5) × 250 ns = 1.5 µs 处，1.5 ÷ 2 = 75%。
2. `0x100` 是 `001 0000 0000`，`0x200` 是 `010 0000 0000`。第 10 位两边都是 0，打平；第 9 位 `0x100` 是显性 0、`0x200` 是隐性 1，`0x200` 读回 0，在这一位退出。输掉仲裁不是错误，不记错，等总线空闲再发。
3. 44 + 8 × 8 = 108 位；108 × 2 µs = 216 µs。填充只发生在帧起始到 CRC 这 34 + 64 = 98 位里，最坏是第一次连续 5 位就插一位，之后每 4 位插一位，共 ⌊(98 − 1) ÷ 4⌋ = 24 位，整帧最长 132 位、264 µs。
4. 每次没人应答 TEC 加 8，16 × 8 = 128，第 16 次后进入错误被动；之后按 CAN 2.0 规范第 8 节的例外，错误被动发送方的 ACK 错误不再加分，TEC 停在 128，不进总线关闭。拔掉收发器后，PB9 的显性位回不到 PB8，每一帧都是位错误，没有例外，TEC 涨过 255，进入总线关闭。
5. 128 × 11 = 1408 个位时间，1408 × 2 µs = 2.816 ms。ABOM 关掉时，软件要让控制器进、出一次初始化模式（`HAL_CAN_Stop()` 再 `HAL_CAN_Start()`），之后同样要在正常模式里等够这 1408 个隐性位。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

**订货号与时钟。** 这一章的位时间、工作脚和错误状态只钉在订货号 STM32F103C8T6（LQFP48，中容量）上。bxCAN 的时钟是 APB1，本书按第 02 章配成 36 MHz。预分频 9、BS1 = 5、BS2 = 2、SJW = 1 是例程设定的工作点，见 [RM0008 Rev 21 bxCAN](#source-rm0008-can)。

**位时间。** `tq = 9 / 36 MHz = 250 ns`。同步段 1，加 BS1 的 5、BS2 的 2，一共 8 个时间份额，一位 `8 × 250 ns = 2 µs`，即 500 kbit/s。采样点 `(1 + 5) / 8 = 75%`，落在 1.5 µs。写进 `CAN_BTR` 的是各段减 1：BRP = 8、TS1 = 4、TS2 = 1、SJW = 0，合起来是 `0x00140008`；回环再加第 30 位 LBKM，是 `0x40140008`。公式和位域出自 RM0008 Rev 21 第 24.7.7 节和第 24.9.2 节。

**失败的那一档。** 想要 10 个时间份额、采样点 70%（BS1 = 6、BS2 = 3）时，500 kbit/s 要的预分频是 `36e6 / (500e3 × 10) = 7.2`，不是整数。写成 8，得到 `36e6 / (8 × 10) = 450 kbit/s`，一位 2.22 µs，比 500 kbit/s 慢 10%，和别的节点对不上。450 kbit/s 不是工作点。

**工作脚。** BluePill 用 `CAN_REMAP = 10`：第 45 脚 PB8 = CAN_RX，第 46 脚 PB9 = CAN_TX，见 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。复位默认的 `00` 是第 32 脚 PA11 = CAN_RX、第 33 脚 PA12 = CAN_TX，这一对同时是 USB 的 D− 和 D+。编码出自 RM0008 Rev 21 第 9.4.2 节 `AFIO_MAPR` 的第 14:13 位，[RM0008 bxCAN 卡](#source-rm0008-can) 也记了 `10` 和 `11` 两种。HAL 的宏按顺序编号：`__HAL_AFIO_REMAP_CAN1_1()` 是 `00`，`_2()` 是 `10`，`_3()` 是 `11`，出自 STM32CubeF1 的 `stm32f1xx_hal_gpio_ex.h`。

**晶振脚。** LQFP48 的第 5 脚是 PD0-OSC_IN，第 6 脚是 PD1-OSC_OUT，两只脚都在，见 [DS5319](#source-ds5319-clock)。它们平时接 8 MHz 晶振，只有不用 HSE 时，才能用 `AFIO_MAPR` 的 PD01_REMAP 把它们当 PD0、PD1 用（RM0008 Rev 21 第 9.4.2 节）。CAN 的 `11` 编码在这颗料上用不了：[RM0008 第 9.3.3 节](#source-rm0008-can) 写明 36、48、64 脚封装不能把 CAN 重映射到端口 D，表 34 的脚注说这一档只在 100 脚和 144 脚封装上有。旁白文字稿第 6 条说的「没有那两只脚」，准确的说法是：两只脚都在，只是 CAN 去不了。

**和 I2C 共用。** 第 45 脚和第 46 脚也是 I2C1 的重映射（SCL、SDA），见 [DS5319](#source-ds5319-i2c)。这对脚同一时刻只给 CAN 或 I2C1 之一；第 07 章的 I2C1 用默认的 PB6/PB7，不冲突。

**终端。** 两只 120 Ω 各在总线一端，跨在 CANH 与 CANL 之间，不接在 PB8、PB9 上；PB8/PB9 进收发器的 RXD/TXD，CANH/CANL 只由收发器驱动。两只 120 Ω 并联，断电时量 CANH 与 CANL 之间是 60 Ω。60 Ω 是直流负载，不是电缆的特性阻抗。

**错误状态。** TEC 大于 255，即计到 256，进入总线关闭；恢复要在 CANRX 上看到 128 次、每次 11 个连续隐性位，500 kbit/s 下至少 `128 × 11 × 2 µs = 2.816 ms`，见 [RM0008](#source-rm0008-can)。ABOM 为 1 时硬件自己开始恢复；为 0 时软件要进、出一次初始化模式，而初始化模式里控制器不看 CANRX，恢复只能在正常模式下数完（RM0008 Rev 21 第 24.7.6 节）。单节点会不会走到 256，要看有没有收发器：接着收发器、只是没人应答，TEC 到 128 进入错误被动以后就停住，因为 CAN 2.0 规范第 8 节规定错误被动发送方的这种 ACK 错误不再加分；没接收发器，PB9 的显性位回不到 PB8，是位错误，没有这条例外，才会走到 256。另外，`CAN_ESR` 的 TEC 字段只是 9 位计数器的低 8 位（RM0008 Rev 21 第 24.9.2 节），256 要看 BOFF 位。

**过滤器。** 这颗料有 14 组过滤器和 2 个接收 FIFO，见 [RM0008](#source-rm0008-can)。32 位掩码里，标准标识写进 `FilterIdHigh` 要左移 5 位，`0x123 << 5 = 0x2460`；不左移，总线上有帧，邮箱仍是空的。`examples/can-bxcan` 用的就是 `PEER_ID << 5`，见 [本仓库例程](#source-project-examples)。本章再把 `FilterMaskIdLow` 设成 `0x0006`，让 IDE、RTR 两位也参与比较，只收标准数据帧；例程写的是 `0x0000`，高 11 位相同的扩展帧和遥控帧也会进来。

**例程的出入。** `examples/can-bxcan` 的 README 说单节点会进总线关闭，按上面那段，接着收发器时它会停在错误被动，见 [本仓库例程](#source-project-examples)。

**共用的中断和存储。** 中容量的向量表（RM0008 Rev 21 表 63）在第 20 号位置印的是 `USB_LP_CAN_RX0`，CAN 的 FIFO0 接收和 USB 的低优先级中断共用这一条，见 [RM0008](#source-rm0008-usb)。CMSIS 头文件和启动文件里，它叫 `USB_LP_CAN1_RX0_IRQn` 和 `USB_LP_CAN1_RX0_IRQHandler`；互联型的表 61 在同一位置印的是 `CAN1_RX0`。USB 和 CAN 还共用一块 512 字节的 SRAM，同一时刻只能用一个（RM0008 Rev 21 第 24.2 节）。第 13 章和第 14 章的例程不要编进同一个工程。

**换系列时。** STM32F405/F407 有 CAN1、CAN2 两个控制器，共用 28 组过滤器（RM0090 Rev 22 第 32.2 节），HAL 的 `SlaveStartFilterBank` 在那里才起作用；STM32F401、F411 没有 bxCAN。换到别的系列，脚位、时钟和向量名都要按那颗料的手册重查。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-13-can-bit.svg" width="760" alt="36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；写成预分频 8 和 10 个时间份额是 450 kbit/s；工作脚是第 45 脚和第 46 脚">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径是 8 个 250 ns 的时间份额，采样点 75%，2 µs，500 kbit/s，预分频 9，SJW = 1。120 Ω 接在 CANH 与 CANL 上。失败路径是预分频 8、10 个时间份额、450 kbit/s、采样点 70%。工作脚是第 45 脚 PB8 和第 46 脚 PB9。出处是 [RM0008 Rev 21 bxCAN](#source-rm0008-can) 和 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/can-500k.gif" width="640" alt="8 个时间份额走过 2 µs，采样点在 75%">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：8 个 250 ns 的时间份额，采样点 75%，500 kbit/s。印刷以静态主图为准。450 kbit/s 和晶振脚不在这条 GIF 上。</sub>
</p>

图分三块。正常路径画 8 个 250 ns 的份额、1.5 µs 处的采样点和第 45、46 脚，并注明 120 Ω 跨在 CANH 与 CANL 上，不接 PB8 或 PB9。失败路径画预分频 8、10 个份额的 450 kbit/s。旁注写 PA11/PA12 留给 USB，第 45、46 脚不同时画成 I2C，总线关闭的 256 和 128 × 11 只进表格。旁注里有一句要改正：图上写「把 CAN 重映射到第 5 脚、第 6 脚会停掉 HSE」，可这条路在 48 脚封装上根本不存在，RM0008 Rev 21 第 9.3.3 节规定这种封装不能把 CAN 映射到端口 D。第 5、6 脚真正的限制是：只有不用 HSE 时，才能当 PD0、PD1 用。

`can-arbitration.svg` 留作辅图。仲裁和位填充不进这张静态主图。这两件事在核心原理第 2、3 节。

## 时序与状态

下表把位时间、帧长和恢复时间放在一起，每一行都能用第 4 节的式子或第 2 节的位数算回去。帧长按 CAN 2.0 规范的帧格式数：

| 项目 | 份额或位数 | 一位或一段 | 结果 |
| --- | --- | --- | --- |
| 预分频 9，BS1 5，BS2 2 | 1 + 5 + 2 = 8 个份额 | 8 × 250 ns = 2 µs | 500 kbit/s，采样点 75%，在 1.5 µs。工作点 |
| 预分频 8，BS1 6，BS2 3 | 1 + 6 + 3 = 10 个份额 | 10 × 222 ns ≈ 2.22 µs | 450 kbit/s，采样点 70%。失败 |
| 8 字节标准数据帧 | 44 + 64 = 108 位 | 108 × 2 µs | 216 µs，不算填充 |
| 最坏情况的填充 | ⌊(98 − 1) / 4⌋ = 24 位 | 24 × 2 µs | 48 µs，整帧最长 264 µs |
| 总线关闭后的恢复 | 128 × 11 = 1408 位 | 1408 × 2 µs | 至少 2.816 ms |

错误状态的迁移如下。门槛出自 [RM0008 Rev 21 第 24.7.6 节](#source-rm0008-can) 的图 233，单节点那一行按 CAN 2.0 规范第 8 节的计数规则推出：

| 状态 | 进入条件 | 出错时发什么 | 去哪 |
| --- | --- | --- | --- |
| 错误主动 | 复位后；或 TEC、REC 都回到 128 以下 | 6 个显性位 | TEC 或 REC 大于 127 时去错误被动 |
| 错误被动 | TEC 或 REC 大于 127 | 6 个隐性位 | 都小于 128 时回错误主动；TEC 大于 255 时去总线关闭 |
| 总线关闭 | TEC 大于 255，即 256 | 不发 | 数够 128 次 11 个隐性位，回错误主动（ABOM = 1 自动；= 0 要软件进出初始化模式） |
| 单节点，接收发器 | 每帧一次 ACK 错误，TEC 加 8 | 进入错误被动以后是 6 个隐性位 | 停在错误被动，TEC = 128，`CAN_ESR = 0x00800033` |
| 单节点，没有收发器 | 每帧在第一位出位错误 | — | TEC 涨过 255，去总线关闭 |

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 示波器或分析仪上是 450 kbit/s | 预分频 8 配了 10 个时间份额 | 预分频 9，BS1 5，BS2 2 | [RM0008](#source-rm0008-can) | 36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；预分频 8、10 个时间份额是 450 kbit/s |
| 回环能收到，上总线以后对方收不到，PB9 上没有波形 | 重映射宏写成了 `__HAL_AFIO_REMAP_CAN1_1()`，那是 PA11/PA12 | 换成 `__HAL_AFIO_REMAP_CAN1_2()` | [RM0008](#source-rm0008-can) | `AFIO_MAPR` 编码 10 把 CAN 放到 PB8/PB9。HAL 宏的编号出自 STM32CubeF1 源码，不在这张卡里 |
| 单节点用正常模式，TEC 停在 128，没有总线关闭 | 没人应答；错误被动发送方的 ACK 错误不再加分 | 接第二个节点，或先用回环 | [RM0008](#source-rm0008-can) | TEC 到 256 才进总线关闭，恢复要 128 次、每次 11 个隐性位。停在 128 出自 CAN 2.0 规范第 8 节，不在这张卡里 |
| 总线上有帧，邮箱是空的 | 标准标识没左移 5 位 | `FilterIdHigh = RX_ID << 5` | [本仓库例程](#source-project-examples) | `examples/can-bxcan` 用 `PEER_ID << 5` 填 `FilterIdHigh`，预分频写的是 9 |
| `HAL_CAN_Start()` 超时返回错误 | CANRX 上等不到 11 个连续隐性位：RX 接错脚，或收发器没供电 | 查 PB8 到收发器 RXD 的线和收发器的电源；先用回环排除 | [RM0008](#source-rm0008) | RM0008 Rev 21 第 24.4.2 节：进正常模式要先看到 11 个连续隐性位 |
| 两块板都在报错 | 位时间不一致，或终端没接在总线两端 | 两边同一组位时间；两端各一只 120 Ω，断电量 CANH-CANL 约 60 Ω | [本仓库例程](#source-project-examples) | 例程要求两端各一只 120 Ω。这一行不规定电缆的特性阻抗，也不规定收发器是 5 V 还是 3.3 V |
| 波形在 PA11/PA12，USB 也失效 | CAN 还在复位默认脚上 | 重映射到第 45 脚和第 46 脚 | [DS5319](#source-ds5319-usbcan) | PA11/PA12 的复用同时含 CAN 和 USB；第 45 脚 PB8、第 46 脚 PB9 是 CAN 的重映射 |
| 想把 CAN 放到第 5、6 脚 | 那是晶振脚，48 脚封装不能把 CAN 映射到端口 D | 用 PB8/PB9 | [DS5319](#source-ds5319-clock) | LQFP48 第 5 脚是 PD0-OSC_IN，第 6 脚是 PD1-OSC_OUT，两只脚存在。端口 D 不能重映射出自 RM0008 第 9.3.3 节 |
| I2C1 的重映射和 CAN 抢同一对脚 | PB8/PB9 也是 I2C1 的重映射 | 这一对脚只选 CAN 或 I2C1 之一 | [DS5319](#source-ds5319-i2c) | 第 45 脚 PB8、第 46 脚 PB9 是 I2C1 的重映射。不改写第 07 章那张图 |
| 收到第一帧就卡死，或和 USB 例程编在一起两边都乱 | 中断入口名字写错；或 CAN 和 USB 共用一条向量 | 入口写 `USB_LP_CAN1_RX0_IRQHandler`；CAN 和 USB 分成两个工程 | [RM0008](#source-rm0008-usb) | 中容量向量表印的是 `USB_LP_CAN_RX0`，CAN 接收和 USB 共用。CMSIS 的名字出自启动文件，共用 SRAM 出自 RM0008 第 24.2 节 |

F4 的 28 组过滤器、ISO 11898-2 的电平和 CAN 2.0 规范的计数细则没有单独成行：它们不是这颗 C8 的手册数字。

## 相关资源

- RM0008《STM32F10xxx 参考手册》第 21 章 Controller area network (bxCAN)（含 `CAN_BTR` 位定义、过滤器、双 FIFO）。
- RM0090《STM32F4 参考手册》第 32 章 Controller area network (bxCAN)。
- ISO 11898-1（CAN 数据链路层）与 ISO 11898-2（物理层）。
- 收发器数据手册：TJA1050、SN65HVD230。
- 配图：`../assets/animations/can-arbitration.svg`（作者自绘矢量图）。
- 可编译示例：[examples/can-bxcan](../examples/can-bxcan/)（环回、双节点、过滤器、ABOM 与软件恢复）。BluePill 上请重映射到 PB8/PB9，不要占用板载 USB 的 PA11/PA12。

- 手机阅读版：[第 13 章 · CAN总线（公众号图文）](https://mp.weixin.qq.com/s/KvjVL15tp4MOqeR_5rxUbA)
