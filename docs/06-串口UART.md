# 06 串口 UART

> English: [UART](en/06-uart.md)

> UART 是最常用的异步串行通信接口，用于打印日志、连接模块与上位机。

<p align="center">
  <img src="../assets/animations/uart-frame.svg" width="760" alt="UART 帧结构逐位时序">
  <br><sub>▲ 动画：UART 帧结构逐位时序（起始位/数据位/校验/停止位，作者自绘矢量图）</sub>
</p>

<!-- video:ch06 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch06-uart.png">
    <source src="../assets/video/ch06-uart.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.6 分钟）。<a href="../assets/video/ch06-uart.mp4">MP4</a> · <a href="../assets/video/ch06-uart.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. 115200 8N1 里的 8，是数据位，不是波特率的一部分。一帧通常是起始位、八位数据、没有校验、一位停止。位数说错，对方会一直解出错帧。
2. 波特率是双方约好的速度，由总线时钟分频得到。F103 上 APB 时钟不对，分频再准也会偏。一边 115200，另一边 9600，你只能看到乱码。
3. 溢出错误 ORE 表示你来不及把数据取走。清除时要先读状态寄存器，再读数据寄存器。顺序反了，标志清不掉，后面的字节会全部卡住。
4. 这一帧是仓库画的串口帧，一位一位排开。看图时对照你的初始化：数据位、停止位、校验，要和上位机软件里的设置逐项相同。差一项就乱码。
5. 不定长的一包数据，可以用 DMA 接着收，再用空闲线判断对方说完了。别在中断里一个字节一个字节地阻塞等待。Wokwi 里这套 DMA 目前对不上，接线可以看，收包要上真板。
6. RS485 要控制收发方向。最后一个字节离开移位寄存器，发送完成标志才会起来。标志没起来就转身去收，最后一个字节会被你自己截掉。
7. TX 接对方的 RX，RX 接对方的 TX，地必须连在一起。只接两根信号、不共地，电平没有参考，有时能蒙对，有时完全没字。先共地，再谈波特率。
8. 口诀：ORE 要先读状态再读数据；RS485 等发送完成再转身。这两句能省掉一半「串口偶发丢字」的下午。
9. 实验可以先把 TX 和 RX 短接，确认自己能收到自己发出的字，再接到电脑。短接都收不到，就先别怀疑 USB 转串口线。
10. 合上书，三问。8N1 的 8 是什么？清除溢出时先读哪个寄存器？RS485 为什么要等发送完成才能转换方向？

</details>
<!-- /video:ch06 -->

## 学习目标

读这一章之前：需要第 02 章的系统时钟和 APB1、APB2 两条总线的分频，第 03 章的复用推挽输出和输入上拉，第 04 章的中断。DMA 的细节在第 10 章，这一章只用到「外设自己把数据搬进内存」这一层意思。二进制、十六进制和位运算不熟的话，先读第 00 章的「零基础预备」。

- [ ] 画出 0x31 和 0xA5 在 8N1 下的一整帧：起始位、低位在前的 8 个数据位、停止位，共 10 位
- [ ] 用 USARTDIV = fPCLK / (16 × 波特率) 算出 USART1（72 MHz）和 USART2（36 MHz）跑 115200 时的 BRR 和误差
- [ ] 把 USB 转串口模块和 BluePill 交叉接好（TX 接 RX，RX 接 TX，地接地），跑通阻塞回显
- [ ] 把 printf 接到 USART1，说清 Keil 和 GCC 各要自己写哪个函数
- [ ] 用 DMA + IDLE 收一段长度不定的数据，并说清 IDLE 只表示「线空闲了一帧时间」
- [ ] 遇到 ORE、FE 时按「先读 SR、再读 DR」清标志，让接收不再卡死
- [ ] RS485 发完最后一个字节后，等 TC 置位再把方向脚切回接收

## 核心原理

**一句话结论：UART 不传时钟，收发两边各按约定的波特率自己计时。帧格式（数据位、校验、停止位）两边一致、波特率误差够小，字节就能对上。**

### 先打个比方

两个人隔着一条街用手电筒传暗号，事先约好三件事：

- 平时灯一直亮着，表示「没话说」。
- 要说一个字，先灭灯一拍，表示「开始了」。接下来 8 拍，亮是 1，灭是 0。
- 说完再亮一拍，表示「这个字结束」，然后可以接着说下一个字。

收的人一看到灯灭，就按约好的节奏数拍子，在每一拍的中间看一眼灯。约好的节奏就是波特率；开头灭灯的那一拍是起始位，结尾亮灯的那一拍是停止位。两人的表快慢不一样，数到后面几拍就会看错，这就是波特率误差。

比方到这里为止。真实的接收器不是每拍只看一眼：它把每一位切成 16 小份，在中间连取三次再按多数表决（第 4 节）。它每碰到一个起始位就重新对一次表，所以误差只在一帧（约 10 位）里累积，不会越传越偏。

### 1. UART 是什么：两根信号线，不传时钟

UART 是 Universal Asynchronous Receiver/Transmitter（通用异步收发器）的缩写。「异步」指线上没有时钟信号，收发两边靠各自的时钟和约好的速度对齐。STM32 里这个外设叫 USART，多出来的 S 是 Synchronous（同步），表示它还能另外输出一根时钟线。本章只用它的异步模式，所以照习惯叫 UART。

一条串口连接只要三根线：

| 线 | 全称 | 站在 STM32 这边看 |
| --- | --- | --- |
| TX | Transmit，发送 | 输出，接对方的 RX |
| RX | Receive，接收 | 输入，接对方的 TX |
| GND | 地 | 两边的电平都以它为参考，必须相连 |

这张表的读法：一边的「发」对着另一边的「收」，所以 TX、RX 要交叉接。两个方向各走各的线，可以同时收和发，这叫全双工。

STM32F103C8T6 有 3 个 USART（DS5319 Rev 20 表 2）。USART1 挂在 APB2 总线上，USART2、USART3 挂在 APB1 上。按第 02 章的 72 MHz 配置，APB2 是 72 MHz，APB1 是 36 MHz。同一个波特率在两条总线上算出的分频值不一样，第 3 节会算给你看。

引脚上是 3.3 V 逻辑电平：高电平是 1，低电平是 0，常被叫作「TTL 电平串口」。电脑上老式 9 针串口用的是 RS-232 电平，它用正负电压表示 0 和 1，而且高低相反，不能直接接 STM32 的引脚，中间要加 MAX3232 一类的电平转换芯片。现在最常见的做法是用一块 USB 转 TTL 串口模块（常见芯片有 CH340、CP2102），电脑把它认成一个 COM 口。

### 2. 帧格式详解

一帧就是一个字节在线上的完整样子。最常见的设置写作 8N1：8 个数据位，N 表示没有校验位（None），1 个停止位。

| 组成 | 取值 | 作用 |
| --- | --- | --- |
| 空闲 | 高电平 | 没有数据时线保持高 |
| 起始位 | 1 位，低电平 | 由高变低的下降沿告诉接收方「开始计时」 |
| 数据位 | 8 位或 9 位，低位在前（LSB first） | 字节本身 |
| 校验位 | 可选：无、奇、偶 | 简单检错：数一数 1 的个数是奇数还是偶数 |
| 停止位 | 1 位或 2 位，高电平 | 把线拉回高，给下一帧的下降沿留出位置 |

表里的行按时间先后排，从上往下就是线上从左到右的顺序。这些规定出自 RM0008 Rev 21 第 27.3.1、27.3.2 节。手册还列了 0.5 和 1.5 个停止位，那是给智能卡模式用的，普通串口用 1 位或 2 位。

拿字符「1」（0x31）走一遍。0x31 的二进制是 0011 0001。低位在前，所以 8 个数据位按 bit0 到 bit7 的顺序出去：1 0 0 0 1 1 0 0。加上前面的起始位和后面的停止位，线上一共 10 位：

```text
        空闲  起始  b0 b1 b2 b3 b4 b5 b6 b7  停止  空闲
0x31：   1     0    1  0  0  0  1  1  0  0    1     1
0xA5：   1     0    1  0  1  0  0  1  0  1    1     1
```

本书的插图用 0xA5（1010 0101）。它的 8 位正着读、倒着读都一样，图上看不出先发哪一头，正好用来专心看帧的结构；想练「低位在前」，用 0x31 这种不对称的字节。

<p align="center">
  <img src="../assets/gif/uart-bits.gif" width="640" alt="UART 逐位发送与波特率时间轴">
  <br><sub>▲ 动画：UART 逐位发送（含波特率时间轴，程序生成 GIF）</sub>
</p>

校验位在 F1 上有一条容易踩的规定：校验位占的是字长里的最高一位。USART_CR1 的 M 位选字长，0 是 8 位，1 是 9 位；打开校验（PCE = 1）后，硬件把校验位放在第 8 位（M = 0）或第 9 位（M = 1）上（RM0008 Rev 21 第 27.6.4 节）。所以「8 个数据位 + 偶校验 + 1 个停止位」（8E1）必须选 9 位字长，HAL 里是 `UART_WORDLENGTH_9B` 加 `UART_PARITY_EVEN`。选 8 位字长再开校验，只剩 7 个数据位。

### 3. 波特率与误差

波特率（baud rate）是每秒传多少位，单位 bit/s。UART 每次传一位，所以波特率就是位速率。一位的时间是波特率的倒数：

```text
一位时间 = 1 / 波特率              115200：1 / 115200 ≈ 8.68 µs
一帧时间 = 一帧的位数 × 一位时间    8N1 共 10 位：10 × 8.68 µs ≈ 86.8 µs
```

所以 115200 的 8N1 串口每秒最多传 115200 / 10 = 11520 个字节。

STM32 把外设时钟分频得到波特率。RM0008 Rev 21 第 27.3.4 节的公式是：

```text
波特率   = fCK / (16 × USARTDIV)
USARTDIV = fCK / (16 × 波特率)
fCK：USART1 用 PCLK2，其余 USART 用 PCLK1
```

公式里的 16 是过采样倍数：接收器每一位采 16 次（第 4 节）。USARTDIV 是带小数的数，写进 USART_BRR 寄存器：位 15:4 放整数部分（DIV_Mantissa），位 3:0 放小数部分乘 16 的结果（DIV_Fraction），见 RM0008 Rev 21 第 27.6.3 节。小数只有 4 位，所以只能精确到 1/16 = 0.0625。

以 USART1、72 MHz、115200 为例，一步一步算：

1. USARTDIV = 72 000 000 / (16 × 115200) = 39.0625
2. 整数部分 39 = 0x27；小数部分 0.0625 × 16 = 1 = 0x1
3. BRR = (0x27 << 4) | 0x1 = 0x271
4. 反算：72 000 000 / (16 × 39.0625) = 115200，误差为 0

误差的定义是（实际波特率 − 目标波特率）/ 目标波特率。下表是本书时钟配置下最常用的几格。读法：先看你用的是哪只 USART、挂在哪条总线上，再按目标波特率找 BRR。

| USART | 总线与时钟 | 目标波特率 | USARTDIV | BRR | 实际波特率 | 误差 |
| --- | --- | --- | --- | --- | --- | --- |
| USART1 | APB2，72 MHz | 9600 | 468.75 | 0x1D4C | 9600 | 0% |
| USART1 | APB2，72 MHz | 115200 | 39.0625 | 0x271 | 115200 | 0% |
| USART2 | APB1，36 MHz | 115200 | 19.53125，取 19.5 | 0x138 | 约 115384.6 | 约 0.16% |

USART2 那一格：19.53125 的小数部分是 0.53125 × 16 = 8.5，4 位小数装不下半格，取 8 得到 19.5，BRR = 0x138，实际波特率 36 000 000 / (16 × 19.5) ≈ 115384.6，快了约 0.16%。RM0008 Rev 21 表 192 列的就是这几格：72 MHz 下 115.2 kbps 写 39.0625、误差 0%；36 MHz 下写 19.5，误差一栏印的是 0.15%，按表注自己的定义算出来是 0.160%，本书写 0.16%。

误差多大才算大？接收器能容忍的总偏差由 RM0008 Rev 21 第 27.3.5 节的表 193、表 194 给出。总偏差是四样东西加在一起：发送方的误差、接收方 BRR 取整带来的误差、接收方自己时钟的偏差、线路和收发器造成的边沿不对称。

| M 位（字长） | BRR 的小数部分 | 把噪声标志 NE 当错误 | 不管 NE |
| --- | --- | --- | --- |
| 0（8 位） | 为 0 | 3.75% | 4.375% |
| 0（8 位） | 不为 0 | 3.33% | 3.88% |
| 1（9 位） | 为 0 | 3.41% | 3.97% |
| 1（9 位） | 不为 0 | 3.03% | 3.53% |

这张表这样用：先看字长和 BRR 有没有小数，再看程序是否把 NE 当成错误，查到的数就是总偏差的上限。0x271 和 0x138 的小数部分都不为 0，8 位字长时上限是 3.33%。两端的误差方向相反时会相加：电脑那边快 2%、板子这边慢 2%，总偏差就是 4%，已经超了。所以常见做法是让每一端各自不超过上限的一半左右（经验值）。

时钟源也算在误差里。BluePill 用 8 MHz 外部晶振（HSE）倍频到 72 MHz，晶振的误差通常只有百万分之几十（经验值），可以不管。改用片内 RC 振荡器 HSI 时，DS5319 Rev 20 表 24 给出的出厂校准精度在 25 °C 是 −1.1% 到 +1.8%，在 −40 到 105 °C 是 −2% 到 +2.5%，这一项就可能吃掉大半预算。

> [!NOTE]
> 这颗 STM32F103C8T6 的 USART_CR1 位 31:14 保留，没有 OVER8 位，只能 16 倍过采样（RM0008 Rev 21 第 27.6.4 节）。HAL 的 `UART_InitTypeDef` 里有 `OverSampling` 字段，F1 上只填 `UART_OVERSAMPLING_16`。8 倍过采样要换到 CR1 里有 OVER8 位的系列，例如 F4。

### 4. 接收器怎样判断 0 和 1

接收器内部用 16 倍波特率的采样时钟盯着 RX 线（RM0008 Rev 21 第 27.3.3 节）：

- 起始位：线由高变低后，硬件在第 3、5、7 次和第 8、9、10 次采样上再确认是低电平，确认了才算一帧开始。只是一个短毛刺，就放弃这次检测，回到空闲。
- 数据位：取每一位中间的第 8、9、10 次采样，按多数决定是 0 还是 1。三次不一致时按多数取值，同时置 NE（表 191）。
- 停止位：第 8、9、10 次采样应该是 1。采到 0 就是帧错误，置 FE。

误差预算就是从这里来的：两边时钟差一点，采样点就在每一位里慢慢挪动，到一帧末尾的停止位挪得最多。挪出了那三次采样的范围，就会采错。

### 5. 三种收发写法：阻塞、中断、DMA

- 阻塞（polling，轮询）：CPU 在循环里反复查标志，等到能收或能发为止。写法最简单，等的时候 CPU 别的什么也干不了。
- 中断（interrupt）：每收到一个字节，硬件打断 CPU，进中断服务函数把它取走。CPU 平时可以干别的。
- DMA（Direct Memory Access，直接存储器访问）：一块独立的硬件在外设和内存之间搬数据，搬完一批才通知 CPU。

| 对比 | 阻塞 | 中断 | DMA |
| --- | --- | --- | --- |
| 等数据时 CPU 在干什么 | 原地死等 | 干别的，每个字节被打断一次 | 干别的，一批搬完才被打断 |
| 115200 连续收时被打断的次数 | 不打断，但一直占着 CPU | 每秒约 11520 次 | 每批一次 |
| 代码量 | 最少 | 中等 | 最多，要配 DMA 通道 |
| 适合 | 调试、一次性的小数据 | 零散的短命令 | 大量数据、连续数据流、长度不定的包 |

读这张表时看第二行：115200 下一个字节占 86.8 µs，72 MHz 的 CPU 在这段时间里走 72 000 000 × 86.8 µs ≈ 6250 个时钟周期，所以中断方式在 115200 下负担不重。波特率升到 Mbit/s 级别，或者几路串口同时收，就该换 DMA 了。

### 6. 溢出错误、帧错误和其他状态标志

USART 的状态都在状态寄存器 USART_SR（偏移 0x00）里，一位一个标志。数据寄存器 USART_DR（偏移 0x04）读出来是收到的字节，写进去就是要发的字节。下表列出本章用到的位，出自 RM0008 Rev 21 第 27.6.1 节：

| 位 | 名字 | 置 1 表示 | 怎样清零 |
| --- | --- | --- | --- |
| 7 | TXE | 发送数据寄存器空了，可以写下一个字节 | 写 DR |
| 6 | TC | 发送完成：最后一帧连停止位都已离开引脚 | 先读 SR 再写 DR，或者软件写 0 |
| 5 | RXNE | 收到一个字节，可以读 DR | 读 DR |
| 4 | IDLE | 检测到空闲线：收完数据后线保持高电平满一帧时间 | 先读 SR 再读 DR |
| 3 | ORE | 溢出错误：上一个字节还没读走，下一个字节已经收完 | 先读 SR 再读 DR |
| 2 | NE | 噪声：某一位的三次采样不一致 | 先读 SR 再读 DR |
| 1 | FE | 帧错误：停止位上采到 0 | 先读 SR 再读 DR |
| 0 | PE | 校验错误 | 先读 SR 再读 DR |

读表时盯住最后一列，清除方法有三种：读 DR、写 DR、先读 SR 再读 DR。RXNE 读一次 DR 就清；IDLE 和四个错误标志必须两步都做，顺序不能反。

ORE 是怎么来的：接收器有两级，一级是正在一位一位收的移位寄存器，一级是收好的字节等你来读的 DR。DR 里的字节还没读走（RXNE 还是 1），移位寄存器又收完一个，就溢出了：DR 里的旧字节保留，新字节丢掉，ORE 置 1（RM0008 Rev 21 第 27.3.3 节）。115200 下留给你读 DR 的时间大约是一帧，86.8 µs；中断里做的事太多、或者关中断太久，就会溢出。

FE 通常说明两边波特率对不上，或者线上有干扰。出错的那个字节照样进 DR，读它之前先看 FE。同一个字节既帧错误又溢出时，只置 ORE。

HAL 的 `__HAL_UART_CLEAR_OREFLAG()`、`__HAL_UART_CLEAR_FEFLAG()` 在 F1 上做的就是「先读 SR 再读 DR」这一个动作，一次把这几个标志一起清掉。

### 7. RS485：等 TC 再转身

RS485 是一种用两根线（A、B）传差分信号的串口总线，同一时刻只能有一方发送，叫半双工。收发器芯片（例如 MAX485）有一只方向脚 DE（Driver Enable，驱动使能）：DE 为高时驱动总线，也就是发送；为低时放开总线，回到接收。很多模块把 DE 和 /RE 接在一起，用一只 GPIO 控制。

TXE 和 TC 的区别就在这里。TXE = 1 只说明 DR 里的字节已经搬进移位寄存器，这个字节还在一位一位往外走；TC = 1 才说明连停止位都出去了（RM0008 Rev 21 第 27.3.2 节）。TXE 一置位就切 DE，最后一个字节最多会被截掉一整帧，115200 下约 86.8 µs。手册还要求关 USART 或进低功耗模式之前也等 TC = 1。

口诀：**ORE 先读 SR 再读 DR；RS485 等 TC 再转身。**

### 8. DMA + IDLE：收长度不定的数据

很多设备（GPS 模块、AT 指令模块、上位机命令）一次发一串长度不定的字节，发完就停。IDLE 标志正好能发现「停」：收完数据后，RX 线保持高电平满一个帧时间（8N1、115200 时约 86.8 µs），硬件置 IDLE。IDLE 清掉之后，要等收到新字节才会再次置位，所以一串数据后面只来一次（RM0008 Rev 21 第 27.6.1 节）。

HAL 把这两件事打包成 `HAL_UARTEx_ReceiveToIdle_DMA()`：启动一次 DMA 接收，碰到下表任一事件就调用 `HAL_UARTEx_RxEventCallback(huart, Size)`。

| 事件 | 普通模式（DMA_NORMAL）下的 Size | 循环模式（DMA_CIRCULAR）下的 Size |
| --- | --- | --- |
| IDLE：线空闲了一帧时间 | 这一次收到的字节数，接收随即停止 | DMA 下一个要写的位置 |
| 半传输 HT：缓冲区写满一半 | 缓冲区长度的一半，接收继续 | 缓冲区长度的一半 |
| 传输完成 TC：缓冲区写满 | 缓冲区长度，接收停止 | 缓冲区长度，位置回到 0 |

这张表的用法：先确定 DMA 是普通模式还是循环模式，再看三种事件下 Size 的含义。普通模式最容易出错的是 HT 那一行：一包超过半个缓冲区时，回调会先来一次 Size = 一半，等到 IDLE 再来一次 Size = 总数，两次都从缓冲区开头算。两次都照单全收，前一半就处理了两遍。本章的代码在每次启动接收之后都关掉 HT 中断，只留 IDLE 和 TC。表里的 HAL 行为以所用 STM32CubeF1 版本的源码为准。

IDLE 不等于「对方的一包结束了」。对方发送中途停顿超过一帧时间，一包会被切成两次回调；两包挨得太紧，中间没有一帧的空闲，两包会并成一次回调。IDLE 只是线路状态，可靠的分包要靠协议里的长度字段或结束符，比如 AT 指令的 `\r\n`。

### 9. 把 printf 接到串口

printf 只负责把格式化好的字符交给 C 库的底层输出函数。自己写一个底层函数，让它从 USART1 发出去，printf 就打印到串口了。不同工具链的底层函数名字不同：

| 工具链 | 要自己写的函数 | 另外要注意 |
| --- | --- | --- |
| Keil MDK（Arm Compiler 5 或 6） | `fputc` | 勾选「Use MicroLIB」，或者自己关掉半主机 |
| arm-none-eabi-gcc（newlib） | `_write` | stdout 默认带缓冲，不带 `\n` 的字符串可能迟迟不出来 |

表的读法：按你用的编译器找一行，只写那一行的函数。半主机（semihosting）是让程序借调试器使用电脑输入输出的机制。Keil 用标准 C 库而不用 MicroLIB 时，printf 会走半主机，没接调试器时程序常常卡在里面，看起来像死机。

Arm Compiler 6 为了兼容 GCC 也定义了 `__GNUC__` 宏，所以用 `#ifdef __GNUC__` 区分 Keil 和 GCC 不可靠：Keil 也会编译出 `_write`，而它的库根本不调用这个函数，printf 什么也不打印。要先判断 Keil 才有的 `__ARMCC_VERSION`（Arm Compiler 5 和 6 都定义它）。这两个宏的含义出自 Arm Compiler 和 GCC 各自的文档，不在 ST 的手册里。

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | USART1_TX | PA9（LQFP48 第 30 脚） | 复用推挽输出，接 USB 转 TTL 模块的 RXD |
| BluePill | USART1_RX | PA10（第 31 脚） | 输入上拉，接模块的 TXD |
| BluePill | GND | GND | 和模块的 GND 相连 |
| BluePill | RS485 方向脚（可选） | PA8 | 例程设定，接 MAX485 的 DE 和 /RE |

脚号出自 DS5319 Rev 20 表 5。TX 用复用推挽、RX 用浮空或上拉输入，是 RM0008 Rev 21 表 24 给 USART 全双工规定的接法。

```text
BluePill                               USB 转 TTL 模块
PA9  (USART1_TX，第 30 脚) ──────────▶ RXD
PA10 (USART1_RX，第 31 脚) ◀────────── TXD
GND  ───────────────────────────────── GND
```

接线时注意：TX 接 RX、RX 接 TX，GND 一定要连；模块的电平跳线选 3.3 V；板子已经由 ST-Link 或 USB 供电时，不要再把模块的 5V 或 3V3 脚接到板子上，两路电源会互相顶。

电脑端的串口助手要和程序设得一样：

| 设置项 | 本章的值 |
| --- | --- |
| 波特率 | 115200 |
| 数据位 / 校验 / 停止位 | 8 / 无 / 1 |
| 流控 | 无 |
| 发送时加换行 | 按协议需要加 `\r\n` |

四项里错一项，收到的就是乱码或者干脆没有字。

## 代码实现

第一个程序：USART1 阻塞回显。上电先做一次自环自检，然后收到什么就发回什么。

```c
/* uart_echo.c —— USART1 115200 8N1 阻塞回显（HAL，STM32F103C8T6） */
#include "stm32f1xx_hal.h"

#define UART_BAUD        115200U
#define LOOPBACK_BYTE    0xA5U
#define LOOPBACK_MS      10U
#define ECHO_RX_MS       1000U
#define ECHO_TX_MS       100U

UART_HandleTypeDef huart1;
volatile uint8_t g_loopback = 0;            /* 自环实验看这个变量 */

void SystemClock_Config(void);
void error_handler(void);
static void uart1_init(void);

int main(void)
{
    uint8_t tx = LOOPBACK_BYTE;
    uint8_t rx = 0;
    uint8_t ch;

    HAL_Init();
    SystemClock_Config();                   /* BRR 0x271 的前提：PCLK2 = 72 MHz */
    uart1_init();

    /* 自环自检：PA9 和 PA10 短接时，发出的 0xA5 应该原样收回来 */
    HAL_UART_Transmit(&huart1, &tx, 1, LOOPBACK_MS);
    if (HAL_UART_Receive(&huart1, &rx, 1, LOOPBACK_MS) == HAL_OK)
    {
        g_loopback = rx;
    }

    while (1)
    {
        if (HAL_UART_Receive(&huart1, &ch, 1, ECHO_RX_MS) == HAL_OK)
        {
            HAL_UART_Transmit(&huart1, &ch, 1, ECHO_TX_MS);     /* 回显 */
        }
    }
}

static void uart1_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();

    io.Pin   = GPIO_PIN_9;                  /* PA9 = USART1_TX：复用推挽 */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = GPIO_PIN_10;                  /* PA10 = USART1_RX：输入上拉 */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = USART1;
    huart1.Init.BaudRate     = UART_BAUD;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;    /* F1 只有 16 倍 */
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        error_handler();
    }
}

/* HSE 8 MHz × 9 = 72 MHz；APB2 不分频，APB1 二分频 */
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
    clk.APB1CLKDivider = RCC_HCLK_DIV2;     /* PCLK1 = 36 MHz：USART2、USART3 */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;     /* PCLK2 = 72 MHz：USART1 */
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

逐段看：

- `SystemClock_Config()` 必须先跑。`HAL_UART_Init()` 按当时的 PCLK2 算 BRR；时钟还停在复位后的 8 MHz HSI 时，算出来的 BRR 不是 0x271。
- 时钟先开，再配引脚和串口。TX 是复用推挽，交给 USART1 驱动；RX 是输入，开上拉让线空闲时稳定在高电平，和「空闲为高」一致。
- 自环自检只在 PA9、PA10 短接时有意义。接电脑时这个 0xA5 会出现在串口助手里，显示成一个怪字符，接收那一步超时，`g_loopback` 保持 0。
- 回显用阻塞收发。一次粘贴一长串时可能丢字：发回显的那一帧时间里，后面的字节还在不停地来，这正是后面换成中断或 DMA 的原因。

第二段：把 printf 接到 USART1。和上面的程序放在同一个工程里，另建一个文件：

```c
/* retarget.c —— 把 printf 接到 USART1 */
#include <stdarg.h>
#include <stdio.h>
#include "stm32f1xx_hal.h"

#define LOG_BUF_SIZE  128U

extern UART_HandleTypeDef huart1;

#if defined(__ARMCC_VERSION)                /* Keil MDK：Arm Compiler 5 或 6 */
int fputc(int ch, FILE *f)
{
    uint8_t c = (uint8_t)ch;

    (void)f;
    HAL_UART_Transmit(&huart1, &c, 1, HAL_MAX_DELAY);
    return ch;
}
#elif defined(__GNUC__)                     /* arm-none-eabi-gcc + newlib */
int _write(int fd, char *ptr, int len)
{
    (void)fd;
    HAL_UART_Transmit(&huart1, (uint8_t *)ptr, (uint16_t)len, HAL_MAX_DELAY);
    return len;
}
#endif

/* 不依赖 C 库底层函数的写法：先格式化到缓冲区，再整段发出 */
void log_printf(const char *fmt, ...)
{
    char buf[LOG_BUF_SIZE];
    va_list ap;
    int n;

    va_start(ap, fmt);
    n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    if (n <= 0)
    {
        return;
    }
    if (n >= (int)sizeof(buf))              /* 截断时 n 是「本该有」的长度 */
    {
        n = (int)sizeof(buf) - 1;
    }
    HAL_UART_Transmit(&huart1, (uint8_t *)buf, (uint16_t)n, HAL_MAX_DELAY);
}
```

逐段看：

- 判断顺序是先 `__ARMCC_VERSION` 再 `__GNUC__`。反过来写，Arm Compiler 6 会走进 GCC 那一支（第 9 节）。
- `fputc` 里先把 `ch` 转成一个 `uint8_t` 再发，不拿 `int` 的地址冒充字节数组。
- `vsnprintf` 在字符串被截断时返回的是「完整字符串本该有的长度」，可能大于缓冲区。不夹到 `sizeof(buf) - 1`，`HAL_UART_Transmit` 会把缓冲区后面的栈内存也发出去。
- 用 GCC 时，在 `main()` 开头加一句 `setvbuf(stdout, NULL, _IONBF, 0);` 关掉 stdout 的缓冲，不带 `\n` 的字符串也会立刻出来。

第三个程序：DMA + IDLE 收长度不定的数据，收到的整包再用 DMA 发回去。`SystemClock_Config()` 和 `error_handler()` 与回显程序相同，这里不重复。

```c
/* uart_dma_idle.c —— USART1 DMA + IDLE 收不定长数据，DMA 整包回显（HAL，STM32F103C8T6） */
#include "stm32f1xx_hal.h"

#define UART_BAUD         115200U
#define DMA_RX_BUF_SIZE   64U       /* DMA 一次最多收 64 字节 */
#define RING_SIZE         512U      /* 环形缓冲区大小，必须是 2 的幂 */
#define TX_BUF_SIZE       64U

UART_HandleTypeDef huart1;
DMA_HandleTypeDef  hdma_usart1_rx;  /* USART1_RX：DMA1 通道 5 */
DMA_HandleTypeDef  hdma_usart1_tx;  /* USART1_TX：DMA1 通道 4 */

static uint8_t dma_rx_buf[DMA_RX_BUF_SIZE];
static uint8_t tx_buf[TX_BUF_SIZE]; /* DMA 发送期间不能改，单独一块 */

/* 环形缓冲区：回调（中断里）只改 head，主循环只改 tail */
static uint8_t ring[RING_SIZE];
static volatile uint16_t ring_head;
static volatile uint16_t ring_tail;
static volatile uint32_t ring_dropped;      /* 满了丢掉的字节数 */

void SystemClock_Config(void);
void error_handler(void);
static void uart1_dma_init(void);
static void uart_rx_start(void);

static void ring_push(const uint8_t *data, uint16_t len)
{
    for (uint16_t i = 0; i < len; i++)
    {
        uint16_t next = (uint16_t)((ring_head + 1U) & (RING_SIZE - 1U));
        if (next == ring_tail)              /* 留一个空位，用来区分满和空 */
        {
            ring_dropped += (uint32_t)(len - i);
            return;
        }
        ring[ring_head] = data[i];
        ring_head = next;
    }
}

static uint16_t ring_pop(uint8_t *out, uint16_t max)
{
    uint16_t n = 0;

    while ((n < max) && (ring_tail != ring_head))
    {
        out[n++] = ring[ring_tail];
        ring_tail = (uint16_t)((ring_tail + 1U) & (RING_SIZE - 1U));
    }
    return n;
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    uart1_dma_init();
    uart_rx_start();

    while (1)
    {
        /* 上一次 DMA 发送结束、状态回到 READY，才取下一批 */
        if (huart1.gState == HAL_UART_STATE_READY)
        {
            uint16_t n = ring_pop(tx_buf, TX_BUF_SIZE);
            if (n > 0U)
            {
                HAL_UART_Transmit_DMA(&huart1, tx_buf, n);
            }
        }
        /* 这里可以做别的事，接收不受影响 */
    }
}

/* 启动一次 DMA + IDLE 接收。启动函数会把 HT 中断重新打开，所以每次都要再关一次 */
static void uart_rx_start(void)
{
    if (HAL_UARTEx_ReceiveToIdle_DMA(&huart1, dma_rx_buf, DMA_RX_BUF_SIZE) == HAL_OK)
    {
        __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, DMA_IT_HT);
    }
}

/* IDLE 或缓冲区写满时调用。普通模式下 Size 就是这一次收到的字节数 */
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    if (huart->Instance == USART1)
    {
        ring_push(dma_rx_buf, Size);
        uart_rx_start();
    }
}

/* ORE、FE、NE 等错误：先读 SR 再读 DR 清标志，丢掉这一包，重新开始接收 */
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        __HAL_UART_CLEAR_OREFLAG(huart);
        uart_rx_start();
    }
}

static void uart1_dma_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();

    io.Pin   = GPIO_PIN_9;                  /* TX：复用推挽 */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);
    io.Pin  = GPIO_PIN_10;                  /* RX：输入上拉 */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = USART1;
    huart1.Init.BaudRate     = UART_BAUD;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        error_handler();
    }

    hdma_usart1_rx.Instance                 = DMA1_Channel5;
    hdma_usart1_rx.Init.Direction           = DMA_PERIPH_TO_MEMORY;
    hdma_usart1_rx.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_usart1_rx.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_usart1_rx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart1_rx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_usart1_rx.Init.Mode                = DMA_NORMAL;
    hdma_usart1_rx.Init.Priority            = DMA_PRIORITY_HIGH;
    if (HAL_DMA_Init(&hdma_usart1_rx) != HAL_OK)
    {
        error_handler();
    }
    __HAL_LINKDMA(&huart1, hdmarx, hdma_usart1_rx);

    hdma_usart1_tx.Instance                 = DMA1_Channel4;
    hdma_usart1_tx.Init.Direction           = DMA_MEMORY_TO_PERIPH;
    hdma_usart1_tx.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_usart1_tx.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_usart1_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart1_tx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_usart1_tx.Init.Mode                = DMA_NORMAL;
    hdma_usart1_tx.Init.Priority            = DMA_PRIORITY_LOW;
    if (HAL_DMA_Init(&hdma_usart1_tx) != HAL_OK)
    {
        error_handler();
    }
    __HAL_LINKDMA(&huart1, hdmatx, hdma_usart1_tx);

    /* 三个中断用同一个抢占优先级，回调之间不会互相打断 */
    HAL_NVIC_SetPriority(USART1_IRQn, 1, 0);            /* IDLE、发送完成 TC、错误 */
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_NVIC_SetPriority(DMA1_Channel5_IRQn, 1, 0);     /* 接收缓冲区写满 */
    HAL_NVIC_EnableIRQ(DMA1_Channel5_IRQn);
    HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 1, 0);     /* 发送搬运结束 */
    HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
}

void USART1_IRQHandler(void)
{
    HAL_UART_IRQHandler(&huart1);
}

void DMA1_Channel5_IRQHandler(void)
{
    HAL_DMA_IRQHandler(&hdma_usart1_rx);
}

void DMA1_Channel4_IRQHandler(void)
{
    HAL_DMA_IRQHandler(&hdma_usart1_tx);
}
```

逐段看：

- 通道是固定的：RM0008 Rev 21 表 78 规定 USART1_RX 在 DMA1 通道 5，USART1_TX 在通道 4。F1 的 DMA 请求不能随便改通道。
- `uart_rx_start()` 每次启动之后都关 HT。只在第一次启动时关、回调里重启时不关，一包超过 32 字节就会触发第 8 节说的「前一半处理两遍」。
- 回调在中断里运行，只做两件事：把数据推进环形缓冲区，重新启动接收。解析命令、打印这些慢活留给主循环。
- 环形缓冲区是一个首尾相接的数组。回调只改 `ring_head`，主循环只改 `ring_tail`，各管各的下标，不用关中断。留一个空位，是为了让「满」和「空」看起来不一样。
- DMA 发送期间硬件还在读 `tx_buf`，所以它必须是全局或静态数组，不能是函数里的局部数组，发送结束之前也不能改它。
- DMA 搬完最后一个字节时，最后一帧还在线上。F1 的 HAL 这时打开 TC 中断，等真正发完才把 `gState` 改回 READY、调用 `HAL_UART_TxCpltCallback()`，所以 `USART1_IRQn` 必须开着，只开 DMA 中断是不够的。这一条以所用 STM32CubeF1 版本的源码为准。

想把 DMA 改成循环模式，回调要换一种写法：循环模式下 Size 是位置，要和上一次的位置相减，还要处理绕回。

```c
/* 循环模式变体：hdma_usart1_rx.Init.Mode 改成 DMA_CIRCULAR，接收只启动一次，
   不关 HT，回调里也不重启。下面的回调替换上面同名的那个。
   出错重启接收时，要把 rx_old_pos 清零。 */
static uint16_t rx_old_pos;                 /* 上一次处理到的位置 */

void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    uint16_t pos = Size;                    /* 循环模式下 Size 是 DMA 下一个要写的位置 */

    if (huart->Instance != USART1)
    {
        return;
    }
    if (pos > rx_old_pos)
    {
        ring_push(&dma_rx_buf[rx_old_pos], (uint16_t)(pos - rx_old_pos));
    }
    else if (pos < rx_old_pos)              /* DMA 已经绕回开头：先取到末尾，再从头取到 pos */
    {
        ring_push(&dma_rx_buf[rx_old_pos], (uint16_t)(DMA_RX_BUF_SIZE - rx_old_pos));
        ring_push(&dma_rx_buf[0], pos);
    }
    rx_old_pos = (pos == DMA_RX_BUF_SIZE) ? 0U : pos;
}
```

循环模式里 HT 要留着：两次回调之间最多只来半个缓冲区的数据，DMA 不会在你处理之前把没读的数据覆盖掉。

第四段：RS485 方向脚，发完等 TC 再切回接收。接在回显程序里用：

```c
/* rs485.c —— PA8 控制 MAX485 的 DE 和 /RE（例程设定） */
#include "stm32f1xx_hal.h"

#define RS485_DE_PORT        GPIOA
#define RS485_DE_PIN         GPIO_PIN_8
#define RS485_TX_TIMEOUT_MS  100U
#define RS485_TC_TIMEOUT_MS  5U

extern UART_HandleTypeDef huart1;

void rs485_de_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    HAL_GPIO_WritePin(RS485_DE_PORT, RS485_DE_PIN, GPIO_PIN_RESET);   /* 默认接收 */
    io.Pin   = RS485_DE_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(RS485_DE_PORT, &io);
}

HAL_StatusTypeDef rs485_send(const uint8_t *buf, uint16_t len)
{
    HAL_StatusTypeDef st;
    uint32_t t0;

    HAL_GPIO_WritePin(RS485_DE_PORT, RS485_DE_PIN, GPIO_PIN_SET);     /* 占用总线 */
    st = HAL_UART_Transmit(&huart1, (uint8_t *)buf, len, RS485_TX_TIMEOUT_MS);

    t0 = HAL_GetTick();
    while (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_TC) == RESET)      /* 停止位出去了吗 */
    {
        if ((HAL_GetTick() - t0) > RS485_TC_TIMEOUT_MS)
        {
            st = HAL_TIMEOUT;
            break;
        }
    }
    HAL_GPIO_WritePin(RS485_DE_PORT, RS485_DE_PIN, GPIO_PIN_RESET);   /* 放开总线，回到接收 */
    return st;
}
```

逐段看：

- F1 的 `HAL_UART_Transmit()` 返回前本来就等 TC。这里再查一次，是把「等 TC 再转身」写在明处；它还带超时，`HAL_UART_Transmit()` 中途超时返回时，循环也不会一直等下去。
- 用中断或 DMA 发送时，在 `HAL_UART_TxCpltCallback()` 里拉低 DE。F1 的 HAL 在 TC 之后才调用它（以所用 STM32CubeF1 版本的源码为准）。
- 先写 DE 的电平再把引脚配成输出，上电那一刻就不会误占总线。

寄存器写法。同一个 USART1、115200 8N1，看清 HAL 背后写了哪几个寄存器：

```c
/* 寄存器写法：USART1，115200 8N1，PCLK2 = 72 MHz */
RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_USART1EN;

/* PA9：复用推挽 50 MHz（CNF = 10，MODE = 11 → 0xB）
   PA10：上拉输入（CNF = 10，MODE = 00 → 0x8），ODR10 = 1 选上拉 */
GPIOA->CRH  = (GPIOA->CRH & ~(0xFFUL << 4)) | (0xBUL << 4) | (0x8UL << 8);
GPIOA->BSRR = GPIO_BSRR_BS10;

USART1->BRR = 0x271;                                        /* 39.0625 */
USART1->CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE;   /* M = 0：8 位；PCE = 0：无校验 */

/* 发一个字节 */
while ((USART1->SR & USART_SR_TXE) == 0) { }
USART1->DR = 0xA5;
while ((USART1->SR & USART_SR_TC) == 0) { }                 /* 这一帧真正发完 */

/* 清 ORE、FE、NE：先读 SR，再读 DR */
(void)USART1->SR;
(void)USART1->DR;
```

`CRH` 管 PA8 到 PA15，每只脚 4 位，PA9 在位 7:4，PA10 在位 11:8；上拉还是下拉由 ODR 决定，这一点第 03 章讲过。置 TE 之后，硬件先发一个空闲帧（一整帧的高电平），再发第一个数据（RM0008 Rev 21 第 27.3.2 节）。

完整工程见 [`examples/uart-dma-idle/`](../examples/uart-dma-idle/)。那个例程按第 8 节的普通模式写，回调里重启接收，但没有关 HT，一包超过 32 字节时前一半会进两次环形缓冲区；照本节的 `uart_rx_start()` 改即可。

## 动手实验

1. **实验一：PA9 和 PA10 短接，自己收自己。** 拔掉 USB 转 TTL 模块，用一根杜邦线把 PA9 和 PA10 连起来，下载回显程序。
   - 预期现象：调试器的 Watch 窗口里，`g_loopback` 是 0xA5。
   - 怎么确认：逻辑分析仪接 PA9，按 115200、8N1 解码，看到一个 0xA5；从起始位的下降沿到停止位结束约 86.8 µs，每一位约 8.68 µs。
   - 没成功先查：杜邦线是否真的连上了 PA9 和 PA10；GPIOA 和 USART1 的时钟开了没有；PA9 是不是复用推挽。自环不检查波特率准不准，因为收发用的是同一个时钟，这一步只检查引脚和初始化。
2. **实验二：接电脑回显，再换成 printf。** 去掉短接线，按「硬件与接线」接好模块，串口助手设成 115200、8N1。回显正常后加入 `retarget.c`，在主循环里每秒打印一行 `printf("tick=%lu\r\n", (unsigned long)HAL_GetTick());`。
   - 预期现象：上电先收到一个怪字符（自检发出的 0xA5），之后输入什么回什么；换成 printf 后每秒一行，数字每行大约加 1000。
   - 怎么确认：把串口助手改成 9600 再发，收到的应该全是乱码，改回 115200 恢复，说明波特率两边都在起作用。用逻辑分析仪量一位的宽度，约 8.68 µs。
   - 没成功先查：TX、RX 是否交叉；GND 是否相连；串口助手的数据位、校验、停止位；Keil 有没有勾 MicroLIB；GCC 下字符串末尾有没有 `\n`。
3. **实验三：DMA + IDLE 整包回显。** 下载第三个程序，用串口助手一次发 5 个、40 个、100 个字符。
   - 预期现象：三串都原样发回，不重复、不缺字。
   - 怎么确认：40 个字符超过 64 字节缓冲区的一半，正好检验 HT 有没有关掉，回显里前 32 个字符不能出现两遍。100 个字符超过缓冲区，会分成 64 和 36 两次回调，回显仍然完整。在回调里给一个计数器加 1，用调试器看：发一串 40 个字符，计数只加 1。
   - 没成功先查：USART1_RX 是否用 DMA1 通道 5、USART1_TX 是否用通道 4；USART1 和 DMA1 通道 5、通道 4 的中断是否都开了；每次重启接收后有没有关 HT。

## 自测

1. USART2 挂在 36 MHz 的 APB1 上，要跑 9600，BRR 写多少？误差多少？
2. 9600、8N1 时，最后一个字节的停止位结束后，至少过多久 IDLE 才会置位？
3. 电脑那边的波特率快了 2%，板子这边慢了 2%，8 位数据、BRR 带小数，能稳定通信吗？
4. 字符「1」（0x31）在 8N1 下，线上 10 位依次是什么？
5. 示波器上 RS485 最后一个字节只发出了一部分，代码是在 TXE 置位时把 DE 拉低的。115200 下最多会被截掉多长时间？应该等哪个标志？

参考答案：

1. USARTDIV = 36 000 000 / (16 × 9600) = 234.375。整数 234 = 0xEA，小数 0.375 × 16 = 6，BRR = 0xEA6。反算 36 000 000 / (16 × 234.375) = 9600，误差 0%，和 RM0008 表 192 的 234.375、0% 一致。
2. 一帧的时间：10 / 9600 ≈ 1.04 ms。IDLE 要求线保持高电平满一帧时间。
3. 不能。两边方向相反，偏差相加是 2% + 2% = 4%。RM0008 表 194 给 8 位字长、BRR 带小数的上限是 3.33%（NE 当错误）或 3.88%（不管 NE），4% 都超了。
4. 0x31 = 0011 0001，低位在前是 1 0 0 0 1 1 0 0。加上起始位和停止位：0、1 0 0 0 1 1 0 0、1。
5. TXE 置位时，最后一个字节刚搬进移位寄存器，还有整整一帧没发：10 / 115200 ≈ 86.8 µs。应该等 TC，它在停止位离开引脚之后才置 1。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

前面讲的帧格式和采样规则对大多数 STM32 都成立。具体的脚号、时钟和寄存器位要落到一颗芯片上，本书用的是 STM32F103C8T6，封装 LQFP48，也就是 BluePill 上那颗。

**脚号。**[DS5319 Rev 20](#source-ds5319-usart) 的图 8 和表 5 显示，PA9 是第 30 脚，复位后的复用功能含 USART1_TX；PA10 是第 31 脚，含 USART1_RX。复位后 USART1 不在 PB6/PB7。要搬到 PB6/PB7，得先开 AFIO 时钟，再把 AFIO_MAPR 的 USART1_REMAP 置 1（[RM0008 Rev 21](#source-rm0008) 第 9.3.8 节表 54）。换封装，脚号就变，要重新查表。

**时钟。**USART1 挂在 APB2，用 PCLK2，最高 72 MHz；其余 USART 用 PCLK1，最高 36 MHz。这句话写在 RM0008 Rev 21 第 27.3.4 节的公式下面。本书的时钟配置正好把两条总线开到最高。

**采样。**这颗料的接收器用 16 倍波特率的时钟采样。起始位在第 3、5、7 点和第 8、9、10 点上确认；数据位和停止位都取第 8、9、10 点的多数，三点不一致置 NE（[RM0008 第 27.3.3 节](#source-rm0008-usart)，表 191）。

**BRR 这一格。**16 倍时 `USARTDIV = fPCLK / (16 × 波特率)`。72 MHz、115200：`72e6 / (16 × 115200) = 39.0625`，小数 `0.0625 × 16 = 1`，BRR = `0x271`，反算 `72e6 / (16 × 39.0625) = 115200`，分频误差是 0。`USART_BRR` 偏移 `0x08`，低 4 位是小数。约 0.16% 属于 36 MHz、BRR `0x138` 那一行，那是 APB1 上的 USART2，不是这只 USART1。丢掉小数、只用尾数 39，也会得到约 0.16%，但那不是写进 `0x271` 的结果。

**容差。**总偏差要小于 RM0008 Rev 21 第 27.3.5 节表 193、表 194 的上限。`0x271` 的小数不为 0，8 位字长时上限是 3.33%（NE 当错误）或 3.88%（不管 NE）。

**没有 8 倍过采样。**`USART_CR1` 偏移 `0x0C`，位 31:14 保留，没有 OVER8，F103 只有 16 倍。8 倍过采样要换到带 OVER8 的系列，例如 F4：[RM0090 Rev 22](#source-rm0090) 第 30.6.4 节把它放在 CR1 的位 15。本章不给 F103 算 8 倍的 BRR。

**IDLE。**115200、8N1 时一位约 8.68 µs，一帧 10 位约 86.8 µs。RM0008 里的空闲帧是一整帧的高电平。一次 IDLE 表示线已经空了一个帧时间，不表示对方协议里的一包到齐了。循环 DMA 的 `Size` 是写位置，不是这一次的增量。

**FE。**停止位在预期的采样点上不是高电平，硬件置 `USART_SR.FE`，无效数据照样进 `USART_DR`。清除是先读 SR 再读 DR，只读 DR 清不掉。单字节通信时 FE 自己不产生中断，它和 RXNE 同时置位，靠 RXNE 的中断进来；用 DMA 时要开 CR3 的 EIE 才有错误中断。所以不能说「FE 一定会进中断服务函数」。

**换系列时。**清标志的方法会变。G0 这类新一代 USART 有单独的 USART_ICR 寄存器，往 ORECF、FECF 这些位写 1 来清（RM0444 Rev 6）；「先读 SR 再读 DR」只适用于 F1、F4 这一代的 USART。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-06-uart-frame.svg" width="760" alt="停止位采到 0 就是帧错误，0x271 在 72 MHz、16 倍下误差是 0">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48 第 30 脚 PA9 = USART1_TX，第 31 脚 PA10 = USART1_RX。帧是 0xA5，低位在前。一位约 8.68 µs，10 位约 86.8 µs。BRR `0x271` = 39.0625，16 倍过采样，误差 0。寄存器偏移：USART_SR 0x00、USART_DR 0x04、USART_BRR 0x08、USART_CR1 0x0C。正常路径：停止位第 8、9、10 点为 1，FE 不置位。失败路径：这三点为 0，FE 置位，数据仍在 DR，先读 SR 再读 DR 才清除。这颗 F103 的 CR1 位 31:14 保留，没有 OVER8，图上不算 8 倍的 BRR。脚位来自 [DS5319 Rev 20 图 8](#source-ds5319-usart)；采样与 BRR 来自 [RM0008 Rev 21 第 27 章](#source-rm0008-usart)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/uart-idle.gif" width="640" alt="一帧结束后 RX 保持高，满一个帧时间后标出 IDLE 和 86.8 微秒">
  <br><sub>▲ 网页和公众号用的辅图，只标空闲线和 86.8 µs。印刷版以上面的静态图为准；帧错误的三点采样不在这条 GIF 上。</sub>
</p>

静态图从左到右是一帧 0xA5：起始位、8 个数据位、停止位，每一位下面标着第 8、9、10 个采样点。图的下半部分分成两条路：停止位采到 1，是正常收到一个字节；采到 0，就是帧错误，FE 置位，字节仍然进 DR。GIF 接在帧的后面，画的是线空闲满一个帧时间后 IDLE 才置位。章首的 `uart-frame.svg` 和帧格式一节的 `uart-bits.gif` 是会动的版本；PDF 不播放 GIF 时，起始位、停止位、第 8、9、10 个采样点和 FE 路径都能在静态图上找到。

## 时序与状态

下表从上往下是一帧在时间上的先后，最后两行是一帧收完之后可能进入的状态。时间都由 1/115200 推出，采样点和标志出自 [RM0008 第 27.3.3 节](#source-rm0008-usart)。

| 阶段 | RX 线 | 采样 | 标志 | 时间（115200） |
| --- | --- | --- | --- | --- |
| 空闲 | 高 | — | — | — |
| 起始位 | 低 | 第 3、5、7 点和第 8、9、10 点都确认是 0 | — | 约 8.68 µs |
| 数据位，0xA5，低位在前 | 1 0 1 0 0 1 0 1 | 每位取第 8、9、10 点的多数 | 三点不一致置 NE | 8 × 8.68 ≈ 69.4 µs |
| 停止位，正常 | 高 | 第 8、9、10 点为 1 | RXNE 置 1，FE 为 0 | 约 8.68 µs |
| 停止位，出错 | 低 | 第 8、9、10 点为 0 | RXNE 和 FE 同时置 1，数据仍进 DR | 约 8.68 µs |
| 一帧合计 | — | 10 位 | USART1，72 MHz，BRR `0x271`，误差 0% | 约 86.8 µs，USARTDIV 39.0625 |
| USART2 对照 | — | 10 位 | APB1，36 MHz，BRR `0x138`，约 0.16%，不是这只 USART1 | 约 86.7 µs |
| IDLE | 停止位之后一直为高 | — | 满一个帧时间置 IDLE，不是协议帧的结束 | 约 86.8 µs |
| ORE | DR 未读时下一帧又收完 | — | ORE 置 1，DR 里的旧字节保留，新字节丢掉 | 读 DR 的期限约一帧 |

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 有人说 USART1 的 `0x271` 已经偏了 | 丢了小数位只按尾数 39 算，或者抄了 USART2 那一行 | 72 MHz、16 倍、带上小数位，误差是 0% | [RM0008 BRR](#source-rm0008-usart) | `0x271` 对应 39.0625，分频结果正好 115200，这一格误差 0% |
| 停止位出错后仍读到一个字节，之后接收像卡住 | FE 置位时数据照样进 DR，只读 DR 不清标志 | 先读 SR 再读 DR | [RM0008 第 27.3.3 节](#source-rm0008-usart) | FE 置位时无效数据仍进 DR；只读 DR 清不掉 FE |
| 把 IDLE 当成对方一包已经结束 | IDLE 只说明线空闲了一帧时间 | 分包靠长度字段或结束符，不拿 86.8 µs 当包界 | [RM0008 USART](#source-rm0008-usart) | IDLE 是空闲线满一个帧时间 |
| 想在 F103 上打开 OVER8 修高波特率误码 | 这颗料的 CR1 没有这一位 | 先核对 72 MHz 和 `0x271`，误差是 0% | [RM0008 CR1](#source-rm0008-usart) | USART_CR1 位 31:14 保留 |
| 中断里处理太慢，ORE 置位后再也收不到 | 上一个字节没读走，下一个字节收完，新字节丢掉 | 中断里只搬数据，量大改用 DMA；清 ORE 先读 SR 再读 DR | [RM0008](#source-rm0008) | ORE 的成因，以及先读 SR 再读 DR 的清除顺序 |
| RS485 最后一个字节被截掉 | TXE 一置位就把 DE 拉低 | 等 TC 置位再切换方向 | [RM0008](#source-rm0008) | TXE 只表示数据进了移位寄存器，TC 表示整帧发完 |
| 循环 DMA 把 `Size` 当成这一次新增的字节数 | 循环模式下 `Size` 是写位置 | 保存上次的位置再相减，并处理绕回 | [STM32CubeF4 v1.28.3](#source-stm32cube-f4) | 只证明那个 F4 例程里 Size 是写位置，不证明 F103 的脚位 |
| 应用把 DMA 缓冲区当成一条完整的线性帧来读 | 循环缓冲区里的数据会绕回开头 | 只读到 DMA 写位置为止，绕回时分两段读 | [MaJerle USART DMA](#source-majerle-uart) | 环形位置和应用读取的边界，不涉及波特率和脚位 |
| 普通模式下一包的前一半被处理了两遍 | HT 和 IDLE 都会调用回调，Size 都从缓冲区开头算 | 每次启动接收后都关掉 HT | [ST 社区帖](#source-st-uart-idle) | 经验线索，未升格为规范：HT 与 IDLE 可能相邻触发，以所用 HAL 版本的源码为准 |

有两条坑没有放进表里，因为 manifest 里没有能证明它们的出处卡：Arm Compiler 6 也定义 `__GNUC__`，出自 Arm Compiler 的文档；8E1 必须选 9 位字长，出自 RM0008 第 27.6.4 节 PCE 位的说明，正文第 2 节已经写了，但 RM0008 USART 那张卡的范围不包括它。

## 相关资源

- 官方手册：**RM0008** 第 27 章（USART）；**DS5319** USART 引脚复用表
- 上一篇：[05 定时器与PWM](05-定时器与PWM.md)｜下一篇：[07 I2C总线](07-I2C总线.md)
- 手机阅读版：[第 06 章 · 串口UART（公众号图文）](https://mp.weixin.qq.com/s/_hR9mWbVJJp8_d05jBnA9w)
- 相关图：[`assets/animations/uart-frame.svg`](../assets/animations/uart-frame.svg)、[`assets/gif/uart-bits.gif`](../assets/gif/uart-bits.gif)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。
