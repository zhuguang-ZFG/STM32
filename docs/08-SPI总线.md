# 08 SPI 总线

> English: [SPI](en/08-spi.md)

> SPI 用四根线实现高速全双工通信，常用于 Flash、屏幕、传感器。

<p align="center">
  <img src="../assets/animations/spi-transfer.svg" width="760" alt="SPI 全双工移位与 CPOL/CPHA 时序">
  <br><sub>▲ 动画：SPI 全双工移位与 CPOL/CPHA 四种模式时序（作者自绘矢量图）</sub>
</p>

<!-- video:ch08 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch08-spi.png">
    <source src="../assets/video/ch08-spi.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.6 分钟）。<a href="../assets/video/ch08-spi.mp4">MP4</a> · <a href="../assets/video/ch08-spi.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. SPI 通常是时钟、主机输出、主机输入、片选。名字要按方向记：主机出去的那根不能和进来的那根对调。对调之后，两边都在听，谁也不说话。
2. 模式由时钟空闲电平和在哪个沿采样决定。模式 0 是空闲为低，第一个有效沿就采样。主机和从机模式不一致时，数据会整字节错位，看起来像随机数。
3. 片选是一次事务的括号。拉低表示开始，拉高表示结束。有的从机只在片选上升沿才把数据收下。一直压着片选，下一包会粘在上一包后面。
4. 这一帧是仓库画的移位过程。时钟每走一拍，主机和从机同时移出一位。所以 SPI 没有应答位。你发出去的同时，也会收到一位，哪怕你并不关心它。
5. 全双工意味着你发送的时候，接收缓冲也在进数。只写不读，下一次读到的可能是上一包的剩菜。HAL 里能用收发一起的接口，把两边一次做完。
6. 时钟多快，从机手册说了才算。杜邦线很长时，沿会变钝，实验能过、产品会偶发。先把分频放到从机舒服的范围，再谈把速率拧高。
7. 多个从机可以共享时钟和两根数据线，但片选要各走各的。选中谁，谁才应该回应。两根片选同时为低，两个从机一起说话，线上就是冲突。
8. 口诀：模式 0 的空闲时钟是低；主机输出和主机输入不能接反。片选用上升沿结束一次事务。三句先背下来再接线。
9. 实验找一个带只读寄存器的器件，用正确的模式读回来。数值和手册复位值一致，这章才算过。读出全是 FF 或 00，先查模式和进出线。
10. 合上书，三问。模式 0 时空闲时钟是高还是低？主机输出和主机输入能不能接反？一次事务结束时片选应该怎样？

</details>
<!-- /video:ch08 -->

## 学习目标

读这一章之前：需要第 02 章的 APB2 时钟（本书的配置下 PCLK2 = 72 MHz），第 03 章的推挽输出和复用功能；第 07 章的 I2C 拿来对比最方便，没读也能看懂。二进制、十六进制和移位运算（`<<`、`>>`）不熟，先读第 00 章的「零基础预备」。

- [ ] 说出 SCK、MOSI、MISO、CS 四根线各由谁驱动，以及 MOSI 和 MISO 为什么不能对调
- [ ] 从器件手册的时序图读出 SCK 的空闲电平和采样沿，换算成 CPOL/CPHA 和 HAL 的 `SPI_POLARITY_LOW`、`SPI_PHASE_1EDGE`
- [ ] 在 PCLK2 = 72 MHz 下选 BR 位、算出 SCK，并知道数据手册给 SPI 主机的上限是 18 MHz
- [ ] 用软件片选读出 W25Q64 的 JEDEC ID 0xEF4017，说清 rx[0] 为什么不是厂商号
- [ ] 完成一次扇区擦除、页编程和读回比对，处理好 256 字节的页边界和忙等待
- [ ] 用 DMA 给 ST7789 屏幕填色，按 SRAM 的大小决定一次发多少字节

## 核心原理

**一句话结论：SPI 让主机和从机各拿一个移位寄存器，首尾相接连成一个环；主机每打一个时钟，双方各移出一位、移进一位，8 个时钟交换一个字节。SPI 没有地址，也没有应答，片选线被拉低的那个从机参与交换。**

### 先打个比方

两个人隔着桌子换扑克牌，每人手里一摞。主持人敲一下鼓，两人同时把最上面一张推给对方，再把对方推过来的那张放到自己这摞的最下面。敲 8 下，两摞牌整个换了一遍。屋里还坐着别人，主持人想跟谁换，就先拍拍谁的肩膀；没被拍到的人只看不动。

比方到这里为止。真的 SPI 里，「推牌」和「接牌」发生在时钟的两个不同边沿上，哪个边沿推、哪个边沿接，由 CPOL 和 CPHA 两个位决定（第 2 节）。鼓也不能敲得太快，从机和 STM32 都有上限（第 3 节）。还有一点比方里看不出来：主机想读数据也得敲鼓，敲鼓的同时它自己也必须推一张牌出去，哪怕那张牌没人要（第 5 节）。

### 1. 四根线与移位原理

SPI（Serial Peripheral Interface，串行外设接口）是一种同步串行接口。「同步」的意思是数据线旁边跟着一根时钟线，接收方看着时钟采样，不像第 06 章的 UART 那样靠双方事先约好的波特率。

| 线 | 全称 | 由谁驱动 | 作用 |
| --- | --- | --- | --- |
| SCK | Serial Clock，串行时钟 | 主机 | 每个时钟周期移一位 |
| MOSI | Master Out Slave In，主出从入 | 主机 | 主机送给从机的数据 |
| MISO | Master In Slave Out，主入从出 | 被选中的从机 | 从机送回主机的数据 |
| CS | Chip Select，片选；ST 的手册叫 NSS | 主机 | 拉低选中一个从机，拉高结束这次通信 |

表的读法：「由谁驱动」那一列说的是这根线上的电平由谁决定。MOSI 和 MISO 都是从主机的角度起的名字，所以主机的 MOSI 接从机的 MOSI，主机的 MISO 接从机的 MISO，不像 UART 那样交叉接。从机模块上常把 MOSI 印成 DI 或 SDI，把 MISO 印成 DO 或 SDO（DI 是数据进，DO 是数据出，都是从从机的角度说的）。两根线对调以后，两边同时在「说」、同时在「听」，读回来的是全 0xFF 或一串乱码。

两边各有一个 8 位的移位寄存器（每来一个时钟，里面的位整体挪动一格的寄存器），用 MOSI 和 MISO 连成一个环：

```text
         主机（STM32）                               从机（W25Q64）
   ┌─────────────────────┐      MOSI       ┌─────────────────────┐
   │ 移位寄存器  b7 … b0  │ ─────────────▶ │ 移位寄存器  b7 … b0  │
   │                     │ ◀───────────── │                     │
   └─────────────────────┘      MISO       └─────────────────────┘
              │                 SCK（只由主机产生）       ▲
              └───────────────────────────────────────────┘
```

默认高位先出（MSB first，CR1 的 LSBFIRST 位可以改成低位先出，RM0008 Rev 21 第 25.3.1 节）。主机每产生一个时钟，就从 MOSI 推出一位，同时从 MISO 收进从机推出的一位；8 个时钟以后，两个寄存器里的内容正好对换。RM0008 Rev 21 第 25.3.5 节写得很直接：主机把一个字节写进 DR（数据寄存器）的那一刻开始发送，MOSI 上每移出一位，MISO 上同时移进一位。

所以 SPI 天生是全双工（发和收同时进行）的，而且每个字节都是一次交换：不存在只发不收，也不存在只收不发，区别只在你理不理会收到的那个字节。这也是 SPI 没有 I2C 那种应答位（第 07 章）的原因。主机根本不知道对面有没有人：线接错了、从机没上电，主机照样打出时钟，照样「收到」一个字节，通常是 0xFF 或 0x00。要确认器件在线，得读一个有固定值的寄存器来对账，比如 W25Q64 的 JEDEC ID。

### 2. CPOL/CPHA 四种模式

不同的 SPI 器件，对「时钟空闲时是高还是低」「在哪个边沿采样」要求不一样。STM32 用 CR1（SPI 控制寄存器 1）里的两个位来对齐：

- CPOL（Clock Polarity，时钟极性）：空闲时 SCK 的电平。CPOL = 0 空闲为低，CPOL = 1 空闲为高。
- CPHA（Clock Phase，时钟相位）：在第几个边沿采样。CPHA = 0 在第 1 个边沿采样，CPHA = 1 在第 2 个边沿采样。「第 1 个边沿」指片选拉低以后，SCK 第一次离开空闲电平的那一下。

两个位组合出四种模式，习惯上叫 Mode 0 到 Mode 3：

| 模式 | CPOL | CPHA | 空闲时 SCK | 采样沿 | 换下一位的边沿 | HAL 写法 |
| --- | --- | --- | --- | --- | --- | --- |
| Mode 0 | 0 | 0 | 低 | 第 1 沿，上升沿 | 下降沿 | `SPI_POLARITY_LOW` + `SPI_PHASE_1EDGE` |
| Mode 1 | 0 | 1 | 低 | 第 2 沿，下降沿 | 上升沿 | `SPI_POLARITY_LOW` + `SPI_PHASE_2EDGE` |
| Mode 2 | 1 | 0 | 高 | 第 1 沿，下降沿 | 上升沿 | `SPI_POLARITY_HIGH` + `SPI_PHASE_1EDGE` |
| Mode 3 | 1 | 1 | 高 | 第 2 沿，上升沿 | 下降沿 | `SPI_POLARITY_HIGH` + `SPI_PHASE_2EDGE` |

表的读法：先在器件手册的时序图里看片选拉低之前 SCK 停在高还是低，定下 CPOL；再看数据线在 SCK 的哪个边沿附近保持不变（那就是采样沿），数一数它是离开空闲以后的第 1 个还是第 2 个边沿，定下 CPHA；最后按这一行抄 HAL 的两个宏。主机和从机必须用同一种模式（RM0008 Rev 21 第 25.3.1 节）。模式对不上时，每一位都在对方换数据的那一刻被采样，读回的字节整体错开一位，或者干脆是乱的。

W25Q64 支持 Mode 0 和 Mode 3（Winbond 的 W25Q64 数据手册，不在本书的出处清单里）。这两种模式都在上升沿采样，区别只在空闲电平。本章全用 Mode 0。改 CPOL、CPHA 之前要先把 SPE（SPI 使能位）清零（RM0008 Rev 21 第 25.3.1 节）。

### 3. 速率与分频：BR 位和 18 MHz 上限

SPI1 挂在 APB2 总线上（RM0008 Rev 21 第 7.3.7 节，RCC_APB2ENR 的位 12 是 SPI1EN），本书的配置下 PCLK2 = 72 MHz。SCK 由 PCLK2 分频得到，分频系数由 CR1 的 BR[2:0] 三个位决定，只有 2、4、8、16、32、64、128、256 八档，没有 ÷3 这样的档位（RM0008 Rev 21 第 25.5.1 节）：

```text
SCK = PCLK2 ÷ 2^(BR + 1)
BR = 010（十进制 2）：SCK = 72 MHz ÷ 2^3 = 72 MHz ÷ 8 = 9 MHz
```

| BR[2:0] | 分频 | PCLK2 = 72 MHz 时的 SCK | 一位的时间 | 能不能用 |
| --- | --- | --- | --- | --- |
| 000 | 2 | 36 MHz | 约 28 ns | 超过数据手册的 18 MHz 上限，不用 |
| 001 | 4 | 18 MHz | 约 56 ns | 正好在上限上，线短、从机也允许时才用 |
| 010 | 8 | 9 MHz | 约 111 ns | 本章的工作点 |
| 011 | 16 | 4.5 MHz | 约 222 ns | 可以 |
| 100 | 32 | 2.25 MHz | 约 444 ns | 可以 |
| 101 | 64 | 1.125 MHz | 约 889 ns | 可以 |
| 110 | 128 | 0.5625 MHz | 约 1.78 µs | 可以 |
| 111 | 256 | 0.28125 MHz | 约 3.56 µs | 可以；杜邦线很长时先用这一档排查 |

表的读法：前两列是 RM0008 Rev 21 第 25.5.1 节的 BR 编码，72 除以分频就是第三列的 SCK，「一位的时间」是 SCK 的倒数。最后一列的依据是 DS5319 Rev 20 表 43：主机模式下 SCK 最高 18 MHz。`000` 的 36 MHz 是寄存器里写得进去、芯片却不保证的速度。

除了芯片的上限，速率还受两样东西限制。一是从机自己的上限，查从机的手册。二是走线：杜邦线又长又没有地线陪着，边沿会变钝、会振铃，9 MHz 在面包板上能跑，换一组线可能就偶尔错一位（经验值）。先用慢档跑通，再一档一档往上加。

### 4. 片选：NSS 管理与多从机

一条 SPI 总线上可以挂好几个从机：SCK、MOSI、MISO 大家共用，每个从机单独占一根片选线。主机想和谁通信，就把谁的片选拉低；没被选中的从机让自己的 MISO 处于高阻（松手，不驱动），不干扰别人。

片选同时是一次事务（一条完整的命令加上它的数据）的括号：拉低表示开始，拉高表示结束。很多器件在片选上升沿才真正执行命令，W25Q64 的写使能、页编程、擦除都是这样（Winbond 数据手册）。片选一直压着不放，下一条命令会被当成上一条命令的数据。

STM32 的 SPI 外设自带一只 NSS 脚，SPI1 默认在 PA4。CR1 的 SSM、SSI 和 CR2 的 SSOE 三个位决定它怎么用（RM0008 Rev 21 第 25.3.1 节）：

| 配置 | NSS 的行为 | 适合 |
| --- | --- | --- |
| SSM = 1（软件管理） | NSS 脚不参与，内部的 NSS 电平由 SSI 位代替；主机要把 SSI 置 1 | 单个主机、片选用普通 GPIO，本章用这种 |
| SSM = 0，SSOE = 1 | NSS 脚当输出：主机开始通信时被拉低，一直保持到 SPI 被关掉（SPE 清零） | 只有一个从机，而且它不要求两次事务之间松开片选 |
| SSM = 0，SSOE = 0 | NSS 脚当输入：被别人拉低时主机立即报主模式故障（MODF），自动退回从机 | 多个主机共用总线 |

表的读法：从上往下越来越少见。第二行的「硬件 NSS」看着省事，但它不会在每条命令之后自动拉高。RM0008 Rev 21 第 25.3.3 节的注释说：从机需要在两次传输之间被释放时，NSS 脚要配成 GPIO，或者另用一个 GPIO 由软件翻转。W25Q64 的每条命令都要片选上升沿收尾，所以本章把 PA4 配成推挽输出，代码里自己拉低、拉高，HAL 里对应的是 `SPI_NSS_SOFT`。

用软件片选时，SSI 那一位一定要是 1。HAL 已经替你做了：`SPI_MODE_MASTER` 这个宏本身就含 MSTR 和 SSI 两个位，`SPI_NSS_SOFT` 再把 SSM 置 1（HAL 源码）。自己写寄存器时漏了 SSI，内部的 NSS 就是低电平，RM0008 Rev 21 第 25.3.10 节说这时会置 MODF，硬件把 SPE 和 MSTR 都清零，表现为外设一个时钟也不发。

多从机时还有两件事。第一，所有片选线要在第一次 SPI 传输之前就拉高。STM32 复位后 GPIO 是浮空输入（RM0008 Rev 21 第 9.1.1 节），初始化之前片选脚悬空，从机可能把它当成选中；给片选脚接一只 10 kΩ 上拉电阻到 3.3 V 更稳妥（经验值）。第二，任何时刻最多只有一根片选为低。两根同时为低，两个从机一起往 MISO 上送数据，线上就是冲突。

### 5. 全双工：读一个字节也要发时钟

从机自己不会产生时钟。主机想读，必须自己打出时钟，而打时钟的唯一办法是往 DR 里写一个字节。所以每次读，主机都要发一个「无用字节」（dummy byte，常用 0xFF），同时收进从机送出的字节。

读 W25Q64 的 JEDEC ID（命令 0x9F）是一次 4 字节的事务：

| 第几个字节 | 主机在 MOSI 上发 | 从机在 MISO 上回 | 收在哪里 |
| --- | --- | --- | --- |
| 1 | 0x9F（命令） | 从机还在收命令，MISO 上没有有效数据 | rx[0]，丢掉 |
| 2 | 0xFF（无用字节） | 0xEF，厂商号（Winbond） | rx[1] |
| 3 | 0xFF | 0x40，存储器类型 | rx[2] |
| 4 | 0xFF | 0x17，容量：2^0x17 字节 | rx[3] |

表的读法：同一行的两个字节是在同样 8 个时钟里交换的。发命令的那 8 个时钟里，从机还在接收命令，MISO 上的东西没有意义，所以 rx[0] 不是厂商号；三个有效字节从 rx[1] 开始，拼起来是 `rx[1] << 16 | rx[2] << 8 | rx[3]` = 0xEF4017。0x17 是 23，2^23 字节 = 8 MiB，也就是 64 Mbit，正是型号里的 64。三个字节的含义出自 Winbond 的数据手册，本仓库的 spi-flash 例程也靠这三个字节判断芯片在位。

收发对称还带来一个坑：只发不收的时候，接收这一侧照样在收。RM0008 Rev 21 第 25.3.5 节写明，只发送、不读 DR 时，收到第二个字节就会置 OVR（溢出）标志；第 25.3.10 节说，溢出以后 DR 里留着的是没读走的那个旧字节，后面来的都丢了。下一次真要读的时候，最先读出来的是「上一包的剩菜」。

HAL 的几个函数各自这样处理（STM32CubeF1 的 HAL 源码，不在本书的出处清单里）：

- `HAL_SPI_TransmitReceive()` 发一个收一个，从根上不留残留。读 ID、读状态都用它。
- `HAL_SPI_Transmit()` 在双线模式下结束时会顺手清掉 OVR，所以「先 Transmit 命令和地址，再收数据」这种写法没问题。
- `HAL_SPI_Receive()` 在主机双线模式下其实调用的是 `HAL_SPI_TransmitReceive()`，把接收缓冲区里原有的内容当无用字节发出去。缓冲区里是垃圾，MOSI 上发的就是垃圾。W25Q64 读数据时不理会 MOSI，有的器件却会把它当命令，所以本章在读之前先把缓冲区填成 0xFF。

只写不读的器件，比如屏幕，可以不接 MISO，只用 `HAL_SPI_Transmit()`。

### 6. 屏幕和 DMA：ST7789

ST7789 是常见的彩色屏控制芯片，小模块多是 240×240 或 240×320。它在 SPI 上只收不发。除了 SCK、MOSI、CS，它还要一根 DC 线（Data/Command，数据/命令选择）：DC 为低，这个字节是命令；DC 为高，这个字节是命令的参数或像素数据。DC 是这类器件自己的约定，不属于 SPI。模块上一般还有一根 RES（复位）和一根 BLK（背光）。很多模块把 SCK、MOSI 印成 SCL、SDA，看着像 I2C，其实是 SPI。

初始化和画图常用这几条命令（Sitronix 的 ST7789 数据手册，不在本书的出处清单里）：

| 命令 | 值 | 参数 | 作用 |
| --- | --- | --- | --- |
| SWRESET | 0x01 | 无 | 软件复位；之后等 150 ms（经验值） |
| SLPOUT | 0x11 | 无 | 退出睡眠；之后等 120 ms（经验值） |
| COLMOD | 0x3A | 0x55 | 像素格式：每个像素 16 位，RGB565 |
| MADCTL | 0x36 | 0x00 | 扫描方向和红蓝顺序 |
| INVON | 0x21 | 无 | 颜色反显；多数 IPS 模块要发它颜色才正（经验值） |
| CASET、RASET | 0x2A、0x2B | 起点、终点各 2 字节 | 设定要写的列范围、行范围 |
| RAMWR | 0x2C | 像素数据 | 往刚设定的窗口里写像素 |
| DISPON | 0x29 | 无 | 打开显示 |

表的读法：初始化时从上往下发，跳过 CASET、RASET、RAMWR；之后每画一块区域，就发一遍 CASET、RASET、RAMWR，再跟上像素数据。

整屏有多少数据：240 × 240 个像素，每个 2 字节，一共 115 200 字节，合 921 600 位。

```text
SCK = 9 MHz： 921 600 ÷ 9 000 000  = 0.1024 s，约 102 ms 一帧，每秒最多约 9.8 帧
SCK = 18 MHz：921 600 ÷ 18 000 000 = 0.0512 s，约 51 ms 一帧，每秒最多约 19.5 帧
```

这是线上一刻不停时的下限，实际只会更慢。

用阻塞的 `HAL_SPI_Transmit()` 发这么多字节，CPU 在这 100 ms 里一直原地等。DMA（Direct Memory Access，直接存储器访问，第 10 章细讲）可以替 CPU 搬：SPI 每腾空一次发送缓冲，TXE（发送缓冲空）置 1，就向 DMA 要下一个字节，DMA 从内存取来写进 DR。SPI1 的发送请求接在 DMA1 的通道 3，接收请求接在通道 2（RM0008 Rev 21 表 78）。

DMA 搬得再快，也得先有一块内存放像素。STM32F103C8T6 一共只有 20 KB SRAM（DS5319 Rev 20 首页），装不下 115 200 字节的整帧。办法是分块：开一块 10 行的缓冲区（240 × 2 × 10 = 4800 字节），填好颜色后连发 24 次；画图片时也可以 DMA 发这一块的同时，让 CPU 填下一块。

DMA 的「传输完成」只说明最后一个字节已经交给了 SPI，它可能还在移位寄存器里往外走。RM0008 Rev 21 第 25.3.9 节要求再等 BSY（忙标志）清零，才能关掉 SPI；拉高片选也要等到这时。HAL 在调用发送完成回调之前已经替你等过（STM32CubeF1 HAL 源码）。只发不收的 DMA 同样会让 OVR 置 1（第 25.3.9 节），HAL 在结束时也会把它清掉。

### 7. 软件模拟 SPI 和硬件 SPI

用普通 GPIO 一位一位地翻转 SCK、写 MOSI、读 MISO，也能做出 SPI，叫软件模拟（bit-banging）。它不挑引脚，模式随便改，但速度受 CPU 限制，翻转期间 CPU 干不了别的。

| 比较项 | 软件模拟 | 硬件 SPI1 |
| --- | --- | --- |
| 速度 | 受 CPU 和 GPIO 限制；用 HAL 函数翻转时大约几百 kHz 到 1 MHz（经验值，以逻辑分析仪实测为准） | 最高 18 MHz（DS5319 Rev 20 表 43），本章用 9 MHz |
| CPU 占用 | 整个传输期间被占满 | 阻塞写法也要等；配合 DMA 时几乎不占 |
| 引脚 | 任意 GPIO | PA5、PA6、PA7，或重映射后的 PB3、PB4、PB5 |
| DMA | 不能用 | DMA1 通道 3 发，通道 2 收 |
| 换模式 | 改代码 | 改 CPOL、CPHA 两个位，改之前先清 SPE |

表的读法：引脚冲突、从机的时序特殊、速度要求又不高时用软件模拟；其余场合用硬件 SPI。

### 8. SPI、I2C、UART 放在一起看

| 比较项 | SPI | I2C（第 07 章） | UART（第 06 章） |
| --- | --- | --- | --- |
| 信号线 | SCK、MOSI、MISO，每个从机一根 CS | SCL、SDA | TX、RX |
| 时钟线 | 有，主机产生 | 有，主机产生 | 没有，双方约定波特率 |
| 选中谁 | 片选线 | 地址字节 | 点对点，不用选 |
| 应答 | 没有 | 每个字节的第 9 个时钟 | 没有 |
| 双工 | 全双工 | 半双工 | 全双工 |
| 本书的工作点 | 9 MHz | 400 kHz | 115200 bit/s |

表的读法：三种接口都还要一根共用的 GND，表里没写。要速度、器件不多，用 SPI；要省线、器件多，用 I2C；和电脑或另一块板子通信，用 UART。

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | SPI1_SCK | PA5（LQFP48 第 15 脚） | 复用推挽输出 |
| BluePill | SPI1_MISO | PA6（第 16 脚） | 浮空输入 |
| BluePill | SPI1_MOSI | PA7（第 17 脚） | 复用推挽输出 |
| BluePill | W25Q64 的片选 | PA4（第 14 脚） | 推挽输出，软件控制，空闲为高 |
| W25Q64 模块 | CS、CLK、DO、DI | 依次接 PA4、PA5、PA6、PA7 | VCC 接 3.3 V；/WP、/HOLD 接 3.3 V（很多模块板上已经接好） |
| ST7789 模块 | CS、DC、RES | PB0（第 18 脚）、PA3（第 13 脚）、PA2（第 12 脚） | 例程设定；BLK 接 3.3 V |
| ST7789 模块 | SCL、SDA | PA5、PA7 | 其实是 SCK、MOSI；只写，不接 MISO |

脚号来自 DS5319 Rev 20 表 5，SCK、MOSI、MISO 的 GPIO 配置来自 RM0008 Rev 21 表 25（全双工主机的 MISO 用浮空输入或上拉输入）。屏幕的 CS、DC、RES 接哪只脚是本书的例程设定，换别的空闲 GPIO 也可以。

```text
BluePill                    W25Q64 模块          ST7789 模块
PA4 (第14脚) ─────────────── CS
PB0 (第18脚) ──────────────────────────────────── CS
PA3 (第13脚) ──────────────────────────────────── DC
PA2 (第12脚) ──────────────────────────────────── RES
PA5 (第15脚) ── SCK ──────── CLK ──────────────── SCL
PA7 (第17脚) ── MOSI ─────── DI ───────────────── SDA
PA6 (第16脚) ── MISO ─────── DO
3.3V ─────────────────────── VCC、/WP、/HOLD ──── VCC、BLK
GND ──────────────────────── GND ──────────────── GND
```

接线时注意：两个从机的片选必须各走各的线，任何时刻最多一根为低；W25Q64 模块的 DO 接 PA6、DI 接 PA7，按「从机出、主机进」去接，别照着 UART 的习惯交叉。

## 代码实现

第一个程序：用硬件 SPI1 读出 W25Q64 的 JEDEC ID，再擦除一个扇区、写 16 个字节、读回比对。不用串口，结果放在全局变量里，用调试器看。

```c
/* spi_flash.c —— SPI1 Mode 0、9 MHz 读写 W25Q64（HAL，STM32F103C8T6） */
#include <string.h>
#include "stm32f1xx_hal.h"

#define FLASH_CS_PORT       GPIOA
#define FLASH_CS_PIN        GPIO_PIN_4      /* 第 14 脚，推挽输出当片选 */

#define CMD_WRITE_ENABLE    0x06U
#define CMD_READ_STATUS1    0x05U
#define CMD_PAGE_PROGRAM    0x02U
#define CMD_READ_DATA       0x03U
#define CMD_SECTOR_ERASE    0x20U           /* 擦除一个 4 KB 扇区 */
#define CMD_JEDEC_ID        0x9FU

#define STATUS_BUSY         0x01U           /* W25Q64 状态寄存器 1 的位 0 */
#define W25Q_PAGE_SIZE      256U
#define W25Q64_JEDEC_ID     0xEF4017UL

#define SPI_TIMEOUT_MS      100U
#define PROGRAM_TIMEOUT_MS  10U             /* 页编程最长约 3 ms，留了余量 */
#define ERASE_TIMEOUT_MS    1000U           /* 扇区擦除最长约 400 ms，留了余量 */

#define TEST_ADDR           0x000000UL
#define TEST_LEN            16U

SPI_HandleTypeDef hspi1;

volatile uint32_t g_jedec_id;               /* 调试器里看：应为 0xEF4017 */
volatile HAL_StatusTypeDef g_flash_status = HAL_ERROR;
volatile uint8_t g_verify_ok;               /* 1 表示读回与写入一致 */

static uint8_t s_tx[TEST_LEN];
static uint8_t s_rx[TEST_LEN];

void SystemClock_Config(void);
void error_handler(void);

static void cs_low(void)  { HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_RESET); }
static void cs_high(void) { HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_SET); }

void spi1_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_SPI1_CLK_ENABLE();

    /* 先让片选输出高电平，再把脚配成输出，避免一配置就选中从机 */
    HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_SET);
    io.Pin   = FLASH_CS_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(FLASH_CS_PORT, &io);

    io.Pin  = GPIO_PIN_5 | GPIO_PIN_7;      /* SCK、MOSI：复用推挽 */
    io.Mode = GPIO_MODE_AF_PP;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = GPIO_PIN_6;                   /* MISO：浮空输入 */
    io.Mode = GPIO_MODE_INPUT;
    HAL_GPIO_Init(GPIOA, &io);

    hspi1.Instance               = SPI1;
    hspi1.Init.Mode              = SPI_MODE_MASTER;
    hspi1.Init.Direction         = SPI_DIRECTION_2LINES;     /* 全双工 */
    hspi1.Init.DataSize          = SPI_DATASIZE_8BIT;
    hspi1.Init.CLKPolarity       = SPI_POLARITY_LOW;         /* CPOL = 0 */
    hspi1.Init.CLKPhase          = SPI_PHASE_1EDGE;          /* CPHA = 0，合起来是 Mode 0 */
    hspi1.Init.NSS               = SPI_NSS_SOFT;             /* 片选由 PA4 软件控制 */
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_8;  /* 72 MHz ÷ 8 = 9 MHz */
    hspi1.Init.FirstBit          = SPI_FIRSTBIT_MSB;
    hspi1.Init.TIMode            = SPI_TIMODE_DISABLE;
    hspi1.Init.CRCCalculation    = SPI_CRCCALCULATION_DISABLE;
    hspi1.Init.CRCPolynomial     = 7U;                       /* 不用 CRC；7 是 CRCPR 的复位值 */
    if (HAL_SPI_Init(&hspi1) != HAL_OK)
    {
        error_handler();
    }
}

uint32_t w25q_read_id(void)
{
    uint8_t tx[4] = {CMD_JEDEC_ID, 0xFF, 0xFF, 0xFF};
    uint8_t rx[4] = {0};
    HAL_StatusTypeDef st;

    cs_low();
    st = HAL_SPI_TransmitReceive(&hspi1, tx, rx, 4, SPI_TIMEOUT_MS);
    cs_high();
    if (st != HAL_OK)
    {
        return 0;
    }
    /* rx[0] 是发 0x9F 时同时移进来的，不是厂商号 */
    return ((uint32_t)rx[1] << 16) | ((uint32_t)rx[2] << 8) | rx[3];
}

static HAL_StatusTypeDef w25q_write_enable(void)
{
    uint8_t cmd = CMD_WRITE_ENABLE;
    HAL_StatusTypeDef st;

    cs_low();
    st = HAL_SPI_Transmit(&hspi1, &cmd, 1, SPI_TIMEOUT_MS);
    cs_high();                              /* 片选上升沿，写使能才生效 */
    return st;
}

static HAL_StatusTypeDef w25q_wait_busy(uint32_t timeout_ms)
{
    uint8_t tx[2] = {CMD_READ_STATUS1, 0xFF};
    uint8_t rx[2];
    uint32_t start = HAL_GetTick();

    for (;;)
    {
        HAL_StatusTypeDef st;

        cs_low();
        st = HAL_SPI_TransmitReceive(&hspi1, tx, rx, 2, SPI_TIMEOUT_MS);
        cs_high();
        if (st != HAL_OK)
        {
            return st;
        }
        if ((rx[1] & STATUS_BUSY) == 0U)    /* rx[1] 才是状态字节 */
        {
            return HAL_OK;
        }
        if ((HAL_GetTick() - start) > timeout_ms)
        {
            return HAL_TIMEOUT;
        }
    }
}

static void put_cmd_addr(uint8_t *buf, uint8_t cmd, uint32_t addr)
{
    buf[0] = cmd;
    buf[1] = (uint8_t)(addr >> 16);         /* 24 位地址，高字节先发 */
    buf[2] = (uint8_t)(addr >> 8);
    buf[3] = (uint8_t)addr;
}

HAL_StatusTypeDef w25q_erase_sector(uint32_t addr)
{
    uint8_t hdr[4];
    HAL_StatusTypeDef st = w25q_write_enable();

    if (st != HAL_OK)
    {
        return st;
    }
    put_cmd_addr(hdr, CMD_SECTOR_ERASE, addr);
    cs_low();
    st = HAL_SPI_Transmit(&hspi1, hdr, 4, SPI_TIMEOUT_MS);
    cs_high();                              /* 片选上升沿，开始擦除 */
    if (st != HAL_OK)
    {
        return st;
    }
    return w25q_wait_busy(ERASE_TIMEOUT_MS);
}

HAL_StatusTypeDef w25q_write(uint32_t addr, const uint8_t *data, uint32_t len)
{
    while (len > 0U)
    {
        uint8_t hdr[4];
        uint32_t room = W25Q_PAGE_SIZE - (addr % W25Q_PAGE_SIZE);   /* 这一页还剩几个字节 */
        uint32_t n = (len < room) ? len : room;
        HAL_StatusTypeDef st = w25q_write_enable();

        if (st != HAL_OK)
        {
            return st;
        }
        put_cmd_addr(hdr, CMD_PAGE_PROGRAM, addr);
        cs_low();
        st = HAL_SPI_Transmit(&hspi1, hdr, 4, SPI_TIMEOUT_MS);
        if (st == HAL_OK)
        {
            st = HAL_SPI_Transmit(&hspi1, (uint8_t *)data, (uint16_t)n, SPI_TIMEOUT_MS);
        }
        cs_high();                          /* 片选上升沿，开始编程 */
        if (st != HAL_OK)
        {
            return st;
        }
        st = w25q_wait_busy(PROGRAM_TIMEOUT_MS);
        if (st != HAL_OK)
        {
            return st;
        }
        addr += n;
        data += n;
        len  -= n;
    }
    return HAL_OK;
}

HAL_StatusTypeDef w25q_read(uint32_t addr, uint8_t *data, uint16_t len)
{
    uint8_t hdr[4];
    HAL_StatusTypeDef st;

    put_cmd_addr(hdr, CMD_READ_DATA, addr);
    memset(data, 0xFF, len);                /* HAL_SPI_Receive 会把缓冲区原有的内容当无用字节发出去 */
    cs_low();
    st = HAL_SPI_Transmit(&hspi1, hdr, 4, SPI_TIMEOUT_MS);
    if (st == HAL_OK)
    {
        st = HAL_SPI_Receive(&hspi1, data, len, SPI_TIMEOUT_MS);
    }
    cs_high();
    return st;
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    spi1_init();

    g_jedec_id = w25q_read_id();
    if (g_jedec_id == W25Q64_JEDEC_ID)
    {
        for (uint32_t i = 0; i < TEST_LEN; i++)
        {
            s_tx[i] = (uint8_t)(0xA0U + i);
        }
        g_flash_status = w25q_erase_sector(TEST_ADDR);
        if (g_flash_status == HAL_OK)
        {
            g_flash_status = w25q_write(TEST_ADDR, s_tx, TEST_LEN);
        }
        if (g_flash_status == HAL_OK)
        {
            g_flash_status = w25q_read(TEST_ADDR, s_rx, TEST_LEN);
        }
        g_verify_ok = (g_flash_status == HAL_OK) && (memcmp(s_tx, s_rx, TEST_LEN) == 0);
    }

    while (1)
    {
    }
}

/* HSE 8 MHz × 9 = 72 MHz；APB2 不分频，SPI1 用它 */
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
    clk.APB1CLKDivider = RCC_HCLK_DIV2;     /* PCLK1 = 36 MHz */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;     /* PCLK2 = 72 MHz：SPI1、GPIOA */
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

- `spi1_init()` 先把 PA4 写成高电平再配成推挽输出，片选从第一刻起就是「不选中」。SCK、MOSI 是复用推挽，MISO 是浮空输入，这是 RM0008 Rev 21 表 25 给全双工主机的配置。
- `SPI_MODE_MASTER`、`SPI_NSS_SOFT`、`SPI_BAUDRATEPRESCALER_8` 合起来，`HAL_SPI_Init()` 之后 CR1 是 0x0314：MSTR、SSI、SSM 三个位置 1，BR = 010（实验三会在调试器里核对）。HAL 这时还没置 SPE，第一次传输时才使能 SPI（HAL 源码）。
- `w25q_read_id()` 一次发 4 个字节、收 4 个字节，结果从 rx[1] 开始拼。在 9 MHz 下这 32 个时钟约 3.6 µs。
- 写使能、扇区擦除、页编程都在 `cs_high()` 那一刻才生效（Winbond 数据手册）。芯片做完一次擦除或编程就自动清掉写使能，所以每次擦写之前都要重发 0x06。
- `w25q_wait_busy()` 反复发 0x05 读状态寄存器 1，等位 0（BUSY）变回 0。这个 BUSY 是 W25Q64 自己的，表示芯片内部还在擦写；SPI 外设 SR 里的 BSY 是位 7，只说明 STM32 这一侧还在移位（RM0008 Rev 21 第 25.3.7 节）。两个「忙」不是一回事。
- 闪存的位只能由 1 编程成 0，擦除把整个 4 KB 扇区变回 0xFF（Winbond 数据手册），所以先擦后写。超时值按数据手册的最长时间留了余量：页编程约 3 ms，扇区擦除约 400 ms。
- `w25q_write()` 按页拆开写：`room` 是这一页剩下的字节数，一次最多写到页尾。一条页编程命令越过页尾时，多出的字节会绕回这一页的开头，覆盖那里的数据（Winbond 数据手册）。
- `w25q_read()` 先把缓冲区填成 0xFF，原因见第 5 节：`HAL_SPI_Receive()` 会把它原样当无用字节发出去。
- 要读写更多数据，只改 `TEST_LEN` 和缓冲区；`w25q_read()` 的长度是 16 位的，一次最多 65 535 字节。

第二段代码：ST7789 屏幕用 DMA 整屏填色。它放在同一个工程的另一个文件里，和 W25Q64 共用 `hspi1` 和 SCK、MOSI，片选各用各的。

```c
/* st7789_dma.c —— SPI1 加 DMA1 通道 3，给 240×240 的 ST7789 整屏填色（HAL）
 * 和 spi_flash.c 在同一个工程里：main() 里在 spi1_init() 之后调用 lcd_init()，
 * 再调用 lcd_fill_dma()。 */
#include <stddef.h>
#include "stm32f1xx_hal.h"

#define LCD_CS_PORT     GPIOB
#define LCD_CS_PIN      GPIO_PIN_0              /* 例程设定，第 18 脚 */
#define LCD_DC_PORT     GPIOA
#define LCD_DC_PIN      GPIO_PIN_3              /* 例程设定，第 13 脚：低 = 命令，高 = 数据 */
#define LCD_RST_PORT    GPIOA
#define LCD_RST_PIN     GPIO_PIN_2              /* 例程设定，第 12 脚 */

#define LCD_W           240U
#define LCD_H           240U
#define CHUNK_LINES     10U
#define CHUNK_BYTES     (LCD_W * 2U * CHUNK_LINES)   /* 4800 字节 */

extern SPI_HandleTypeDef hspi1;                 /* 在 spi_flash.c 里定义并初始化 */
void error_handler(void);

DMA_HandleTypeDef hdma_spi1_tx;
volatile uint32_t g_idle_loops;                 /* DMA 发送期间 CPU 空转了多少圈 */

static uint8_t s_chunk[CHUNK_BYTES];
static volatile uint8_t s_dma_busy;
static volatile uint8_t s_dma_error;

/* 发一条命令和它的参数。屏幕不回话，发错了也读不出来，所以这里不查返回值 */
static void lcd_cmd(uint8_t cmd, const uint8_t *param, uint16_t n)
{
    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_RESET);       /* 命令 */
    (void)HAL_SPI_Transmit(&hspi1, &cmd, 1, 100);
    if (n > 0U)
    {
        HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_SET);     /* 参数 */
        (void)HAL_SPI_Transmit(&hspi1, (uint8_t *)param, n, 100);
    }
    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_SET);
}

void lcd_init(void)
{
    static const uint8_t colmod = 0x55;         /* 每个像素 16 位，RGB565 */
    static const uint8_t madctl = 0x00;
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();

    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_SET);         /* 先让片选为高 */
    HAL_GPIO_WritePin(LCD_RST_PORT, LCD_RST_PIN, GPIO_PIN_SET);
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    io.Pin   = LCD_CS_PIN;
    HAL_GPIO_Init(LCD_CS_PORT, &io);
    io.Pin   = LCD_DC_PIN | LCD_RST_PIN;
    HAL_GPIO_Init(GPIOA, &io);

    /* SPI1_TX 在 DMA1 通道 3（RM0008 表 78）：内存到外设，内存地址递增，按字节搬 */
    hdma_spi1_tx.Instance                 = DMA1_Channel3;
    hdma_spi1_tx.Init.Direction           = DMA_MEMORY_TO_PERIPH;
    hdma_spi1_tx.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_spi1_tx.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_spi1_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_spi1_tx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_spi1_tx.Init.Mode                = DMA_NORMAL;
    hdma_spi1_tx.Init.Priority            = DMA_PRIORITY_LOW;
    if (HAL_DMA_Init(&hdma_spi1_tx) != HAL_OK)
    {
        error_handler();
    }
    __HAL_LINKDMA(&hspi1, hdmatx, hdma_spi1_tx);
    HAL_NVIC_SetPriority(DMA1_Channel3_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel3_IRQn);

    HAL_GPIO_WritePin(LCD_RST_PORT, LCD_RST_PIN, GPIO_PIN_RESET);     /* 硬件复位 */
    HAL_Delay(10);
    HAL_GPIO_WritePin(LCD_RST_PORT, LCD_RST_PIN, GPIO_PIN_SET);
    HAL_Delay(120);

    lcd_cmd(0x01, NULL, 0);                     /* SWRESET */
    HAL_Delay(150);
    lcd_cmd(0x11, NULL, 0);                     /* SLPOUT */
    HAL_Delay(120);
    lcd_cmd(0x3A, &colmod, 1);                  /* COLMOD */
    lcd_cmd(0x36, &madctl, 1);                  /* MADCTL */
    lcd_cmd(0x21, NULL, 0);                     /* INVON：多数 IPS 模块要它 */
    lcd_cmd(0x29, NULL, 0);                     /* DISPON */
}

void DMA1_Channel3_IRQHandler(void)
{
    HAL_DMA_IRQHandler(&hdma_spi1_tx);
}

void HAL_SPI_TxCpltCallback(SPI_HandleTypeDef *hspi)
{
    if (hspi == &hspi1)
    {
        s_dma_busy = 0;                         /* HAL 进回调之前已经等到 BSY = 0 */
    }
}

void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi)
{
    if (hspi == &hspi1)
    {
        s_dma_error = 1;
        s_dma_busy = 0;
    }
}

HAL_StatusTypeDef lcd_fill_dma(uint16_t rgb565)
{
    uint8_t win[4] = {0, 0, (uint8_t)((LCD_W - 1U) >> 8), (uint8_t)(LCD_W - 1U)};
    uint8_t ramwr = 0x2C;
    HAL_StatusTypeDef st;

    for (uint32_t i = 0; i < CHUNK_BYTES; i += 2U)
    {
        s_chunk[i]      = (uint8_t)(rgb565 >> 8);   /* 高字节先发 */
        s_chunk[i + 1U] = (uint8_t)rgb565;
    }

    lcd_cmd(0x2A, win, 4);                      /* CASET：列 0 到 239 */
    win[2] = (uint8_t)((LCD_H - 1U) >> 8);
    win[3] = (uint8_t)(LCD_H - 1U);
    lcd_cmd(0x2B, win, 4);                      /* RASET：行 0 到 239 */

    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_RESET);
    st = HAL_SPI_Transmit(&hspi1, &ramwr, 1, 100);                     /* RAMWR */
    HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, GPIO_PIN_SET);         /* 后面全是像素 */

    s_dma_error = 0;
    for (uint32_t row = 0; (row < LCD_H) && (st == HAL_OK); row += CHUNK_LINES)
    {
        s_dma_busy = 1;
        st = HAL_SPI_Transmit_DMA(&hspi1, s_chunk, CHUNK_BYTES);
        while ((st == HAL_OK) && (s_dma_busy != 0U))
        {
            g_idle_loops++;                     /* CPU 这时可以去干别的 */
        }
        if (s_dma_error != 0U)
        {
            st = HAL_ERROR;
        }
    }
    HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, GPIO_PIN_SET);
    return st;
}
```

逐段看：

- 屏幕的片选 PB0 和 Flash 的片选 PA4 各管各的，SCK、MOSI 共用。`lcd_init()` 第一件事就是把 PB0 拉高，然后才有 SPI 传输。
- 改 DC 的时机：`HAL_SPI_Transmit()` 要等最后一位移完、BSY 清零才返回（HAL 源码），所以两次调用之间翻转 DC 是安全的；DMA 发送期间 DC 一直保持为高。
- DMA 的配置按 RM0008 Rev 21 表 78 选通道 3。`__HAL_LINKDMA` 把 DMA 句柄挂到 `hspi1` 上，`HAL_SPI_Transmit_DMA()` 才知道用哪个通道。中断函数名 `DMA1_Channel3_IRQHandler` 必须和启动文件里的一字不差，写错了 DMA 完成中断进不来，程序卡在等待循环里。
- 一块 4800 字节，发 24 块正好 240 行。每块的 DMA 在跑的时候，`g_idle_loops` 一直在涨，说明 CPU 是空着的；换成阻塞发送，这个数就不涨了。
- RAMWR 之后片选一直保持为低，24 块像素都算这一条命令的数据，全发完才拉高。
- 等待时间、INVON 和 MADCTL 的值都是常见模块的经验值；颜色、方向不对时，以模块卖家给的初始化序列为准。

第三段代码：同样的 Mode 0，用 GPIO 模拟。它和硬件 SPI1 用同一组脚，二者不能同时用；要同时用就换几只空闲的脚。

```c
/* soft_spi.c —— 用 GPIO 模拟 SPI 主机，Mode 0，高位先出
 * SCK = PA5，MOSI = PA7，MISO = PA6，CS = PA4 */
#include "stm32f1xx_hal.h"

#define SSPI_PORT           GPIOA
#define SSPI_CS             GPIO_PIN_4
#define SSPI_SCK            GPIO_PIN_5
#define SSPI_MISO           GPIO_PIN_6
#define SSPI_MOSI           GPIO_PIN_7
#define SSPI_DELAY_LOOPS    5U              /* 经验值：决定速率，用逻辑分析仪量 */

static void sspi_delay(void)
{
    for (volatile uint32_t i = 0; i < SSPI_DELAY_LOOPS; i++)
    {
    }
}

void soft_spi_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    HAL_GPIO_WritePin(SSPI_PORT, SSPI_CS, GPIO_PIN_SET);      /* 片选空闲为高 */
    HAL_GPIO_WritePin(SSPI_PORT, SSPI_SCK, GPIO_PIN_RESET);   /* Mode 0：SCK 空闲为低 */
    io.Pin   = SSPI_CS | SSPI_SCK | SSPI_MOSI;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(SSPI_PORT, &io);
    io.Pin  = SSPI_MISO;
    io.Mode = GPIO_MODE_INPUT;
    HAL_GPIO_Init(SSPI_PORT, &io);
}

uint8_t soft_spi_xfer(uint8_t tx)
{
    uint8_t rx = 0;

    for (int i = 7; i >= 0; i--)
    {
        /* SCK 为低时先放好这一位 */
        HAL_GPIO_WritePin(SSPI_PORT, SSPI_MOSI, ((tx >> i) & 1U) ? GPIO_PIN_SET : GPIO_PIN_RESET);
        sspi_delay();
        HAL_GPIO_WritePin(SSPI_PORT, SSPI_SCK, GPIO_PIN_SET);     /* 上升沿：双方采样 */
        rx = (uint8_t)((rx << 1) | (HAL_GPIO_ReadPin(SSPI_PORT, SSPI_MISO) == GPIO_PIN_SET));
        sspi_delay();
        HAL_GPIO_WritePin(SSPI_PORT, SSPI_SCK, GPIO_PIN_RESET);   /* 下降沿：从机换下一位 */
    }
    return rx;
}

uint32_t soft_spi_read_id(void)
{
    uint32_t id;

    HAL_GPIO_WritePin(SSPI_PORT, SSPI_CS, GPIO_PIN_RESET);
    (void)soft_spi_xfer(0x9F);              /* 这一字节同时收到的不要 */
    id  = (uint32_t)soft_spi_xfer(0xFF) << 16;
    id |= (uint32_t)soft_spi_xfer(0xFF) << 8;
    id |= soft_spi_xfer(0xFF);
    HAL_GPIO_WritePin(SSPI_PORT, SSPI_CS, GPIO_PIN_SET);
    return id;
}
```

逐段看：

- Mode 0 的规矩落到代码上就是三步：SCK 为低时把位放到 MOSI 上；拉高 SCK，双方在这个上升沿采样，主机顺手读 MISO；拉低 SCK，从机在下降沿把下一位放到 MISO 上。
- 片选拉低以后、第一个上升沿之前，从机就已经把最高位放到 MISO 上了，所以第一位不会丢。
- `SSPI_DELAY_LOOPS` 决定速率，空循环一圈要几个时钟周期，随编译器优化级别变，所以 5 只是经验值。`soft_spi_read_id()` 读到 0xEF4017，就说明时序对了，可以拿它和硬件 SPI 的结果对照。

寄存器版：同样的 SPI1、Mode 0、÷8，看清 HAL 替你写了哪些位，再手动读一次 JEDEC ID。

```c
/* 寄存器版：SPI1 Mode 0、9 MHz 读 JEDEC ID。教学用，没有超时 */
static uint8_t spi1_xfer(uint8_t b)
{
    while ((SPI1->SR & SPI_SR_TXE) == 0U) { }      /* 发送缓冲空了才能写 */
    SPI1->DR = b;                                   /* 一写 DR 就开始移位 */
    while ((SPI1->SR & SPI_SR_RXNE) == 0U) { }     /* 8 个时钟后收满一个字节 */
    return (uint8_t)SPI1->DR;                       /* 读 DR 同时清掉 RXNE */
}

uint32_t spi1_reg_read_id(void)
{
    uint32_t id;

    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_SPI1EN;
    GPIOA->BSRR = GPIO_BSRR_BS4;                    /* 先让片选输出为高 */
    /* CRL 每只脚 4 位：PA4 = 0x3 推挽输出 50 MHz，PA5 = 0xB 复用推挽，
       PA6 = 0x4 浮空输入，PA7 = 0xB 复用推挽 */
    GPIOA->CRL = (GPIOA->CRL & ~0xFFFF0000UL) | 0xB4B30000UL;

    SPI1->CR1 = SPI_CR1_MSTR | SPI_CR1_SSM | SPI_CR1_SSI | SPI_CR1_BR_1;  /* 0x0314：BR = 010，CPOL = CPHA = 0 */
    SPI1->CR1 |= SPI_CR1_SPE;                                              /* 0x0354 */

    GPIOA->BSRR = GPIO_BSRR_BR4;                    /* 片选拉低 */
    (void)spi1_xfer(0x9F);
    id  = (uint32_t)spi1_xfer(0xFF) << 16;
    id |= (uint32_t)spi1_xfer(0xFF) << 8;
    id |= spi1_xfer(0xFF);
    while ((SPI1->SR & SPI_SR_BSY) != 0U) { }      /* 最后一位真正移完 */
    GPIOA->BSRR = GPIO_BSRR_BS4;                    /* 片选拉高 */
    return id;
}
```

`CRL` 管 PA0 到 PA7，每只脚 4 位（MODE 两位在低、CNF 两位在高），PA4 是位 19:16，PA7 是位 31:28；高 16 位写成 0xB4B3，从 PA7 往 PA4 依次是 0xB、0x4、0xB、0x3。CR1 里各个位的位置见 RM0008 Rev 21 第 25.5.1 节：CPHA 是位 0，CPOL 是位 1，MSTR 是位 2，BR 是位 5:3，SPE 是位 6，SSI 是位 8，SSM 是位 9。少写 `SPI_CR1_SSI`，SPE 一置 1 就进 MODF（第 4 节）。收发的顺序照第 25.3.5 节：等 TXE、写 DR、等 RXNE、读 DR；最后一个字节读完，再等 BSY 清零（第 25.3.5 节的收尾步骤），然后才拉高片选。RM0008 Rev 21 第 25.3.7 节也提醒，每个字节用 TXE 和 RXNE 判断，不要拿 BSY 来逐字节等。

完整工程见 [`examples/spi-flash/`](../examples/spi-flash/)。它逐字节调用 `HAL_SPI_TransmitReceive()`，一次写 300 个字节、跨过页边界，读回一致就点亮 PC13 的 LED。它在 `while (1)` 里每秒把 0 号扇区擦写一遍；W25Q64 每个扇区的擦写寿命是 10 万次（Winbond 数据手册），这样一直跑，一天多就到了，看完结果就断电，或者改成只跑一次。那里还把 MISO 配成了复用推挽；RM0008 Rev 21 表 25 给全双工主机 MISO 的推荐是浮空输入或上拉输入，本章按表 25 写。

## 动手实验

1. **实验一：读 JEDEC ID。** 只接 W25Q64 模块，下载第一个程序，在 `g_jedec_id = w25q_read_id();` 的下一行打断点。
   - 预期现象：调试器里 `g_jedec_id` 是 0xEF4017。
   - 怎么确认：逻辑分析仪接 PA4、PA5、PA6、PA7，按 SPI Mode 0 解码。PA4 为低期间正好 32 个时钟；MOSI 上是 9F FF FF FF，MISO 上第 2 到第 4 个字节是 EF 40 17；一个 SCK 周期约 111 ns，也就是 9 MHz。逻辑分析仪的采样率至少要 SCK 的 4 倍（经验值），看 9 MHz 至少要 36 MHz 采样；不够就先把 BR 改成慢档再看。
   - 没成功先查：读到 0xFFFFFF，多半是 MISO 没接通、模块没上电，或者 DO 和 DI 接反了（DO 接 PA6，DI 接 PA7）；读到 0x000000 或每次都不一样，查两块板是否共地、/HOLD 是否接了 3.3 V（/HOLD 为低时芯片暂停、不驱动 DO，Winbond 数据手册）；读到的值像正确值错开了一位，查模式是不是 Mode 0。
2. **实验二：擦除、写入、读回。** 去掉断点，让程序跑到 `while (1)`。
   - 预期现象：`g_flash_status` 是 `HAL_OK`，`g_verify_ok` 是 1，`s_rx` 里是 0xA0 到 0xAF。
   - 怎么确认：逻辑分析仪上依次看到 06（写使能），20 00 00 00（扇区擦除），一长串 05 FF（等忙；擦除期间状态字节的位 0 是 1，一般持续几十毫秒，经验值），06，02 00 00 00 加 16 个字节（页编程），几串 05 FF，最后 03 00 00 00 加 16 个字节（读）。把 `w25q_write()` 里的 `w25q_write_enable()` 换成 `HAL_OK` 重跑：芯片不理页编程命令，读回全是 0xFF，`g_verify_ok` 变成 0。
   - 没成功先查：`g_flash_status` 是 `HAL_TIMEOUT` 时，看 05 命令读回的状态字节是不是一直为 1；读回的数据和写入的只差几个位，多半是没擦就写（编程只能把 1 变成 0）。
3. **实验三：核对 BR 和 SCK，再让屏幕亮起来。** 在 `spi1_init()` 之后、`w25q_read_id()` 之后各打一个断点，在调试器里看 SPI1 的 CR1；然后接上 ST7789 模块，在 `main()` 的 `spi1_init();` 之后加上 `lcd_init();` 和 `lcd_fill_dma(0xF800);`。
   - 预期现象：第一个断点处 CR1 是 0x0314，第二个断点处是 0x0354，多出来的 0x0040 是 SPE。把 `SPI_BAUDRATEPRESCALER_8` 改成 `SPI_BAUDRATEPRESCALER_4`，CR1 的 BR 字段变成 001，SCK 变成 18 MHz，ID 仍然读得对。屏幕整屏变红（RGB565 的 0xF800 是红色）。
   - 怎么确认：逻辑分析仪量 SCK：9 MHz 时周期约 111 ns，18 MHz 时约 56 ns。屏幕的 PB0 在填屏期间为低约 102 ms（9 MHz）。把 `lcd_fill_dma()` 里的 `HAL_SPI_Transmit_DMA()` 换成阻塞的 `HAL_SPI_Transmit(&hspi1, s_chunk, CHUNK_BYTES, 1000)`，PB0 为低的时间差不多，`g_idle_loops` 却不再增长：线上一样快，区别在于 CPU 有没有空。不要试 `SPI_BAUDRATEPRESCALER_2`：BR = 000 的 36 MHz 超过 DS5319 Rev 20 表 43 的 18 MHz 上限，偶尔读对也不说明可靠。
   - 没成功先查：CR1 的 SPE 和 MSTR 都变成了 0，看 SR 的 MODF 位（第 4 节）；SCK 周期不是 111 ns，先查 PCLK2 是不是 72 MHz。屏幕全黑先查 BLK 和 RES；红色显示成青色，把 0x21 换成 0x20（INVOFF）；程序卡在 `lcd_fill_dma()` 里，查 `DMA1_Channel3_IRQHandler` 的名字和 NVIC 使能。

## 自测

1. 某个传感器的手册写着：片选拉低之前 SCK 为高，数据在 SCK 的下降沿采样。它要哪种模式？HAL 的 `CLKPolarity` 和 `CLKPhase` 各填什么？
2. 一个从机最高只能跑 10 MHz。接在 SPI1（PCLK2 = 72 MHz）上，BR 填多少、SCK 是多少？换到 SPI2（挂在 APB1，PCLK1 = 36 MHz）上呢？
3. 读 JEDEC ID 时收到的 rx[] 是 {0xFF, 0xEF, 0x40, 0x17}。为什么第一个字节不算？0x17 表示多大的容量？
4. 要从地址 0x0000F8 开始写 16 个字节。页编程命令要发几次，每次从哪个地址开始、写几个字节？不拆开、一次发 16 个字节会怎样？
5. 240×240、RGB565 的屏幕，SCK = 18 MHz 时整屏刷一次至少要多久？为什么不能在 STM32F103C8T6 上开一块整帧缓冲区，再一次 DMA 发出去？

参考答案：

1. 空闲为高，CPOL = 1；从高电平出发，第 1 个边沿就是下降沿，在第 1 个边沿采样，CPHA = 0。这是 Mode 2，填 `SPI_POLARITY_HIGH` 和 `SPI_PHASE_1EDGE`。
2. SPI1：÷4 是 18 MHz，超过 10 MHz；÷8 是 9 MHz，不超。所以 BR = 010（`SPI_BAUDRATEPRESCALER_8`），SCK = 9 MHz。SPI2：36 MHz ÷ 4 = 9 MHz，BR = 001（`SPI_BAUDRATEPRESCALER_4`）。同一个 BR 值，SPI1 和 SPI2 的 SCK 差一倍，因为它们挂在不同的总线上（SPI2 的时钟使能在 RCC_APB1ENR 的位 14，RM0008 Rev 21 第 7.3.8 节）。
3. 发 0x9F 的那 8 个时钟里，从机还在接收命令，没往 MISO 上送数据，这个字节是线上碰巧的电平（这里是 0xFF）。0x17 = 23，容量是 2^23 = 8 388 608 字节，也就是 8 MiB、64 Mbit。
4. 一页 256 字节，0xF8 = 248，这一页还剩 256 − 248 = 8 个字节。所以发两次：从 0x0000F8 写 8 个，再从 0x000100 写剩下的 8 个。不拆的话，超出页尾的 8 个字节会绕回这一页的开头，写进 0x000000 到 0x000007，把那里的数据弄坏（Winbond 数据手册）。
5. 240 × 240 × 2 = 115 200 字节 = 921 600 位；921 600 ÷ 18 000 000 = 0.0512 s，约 51 ms，每秒最多约 19.5 帧。整帧要 115 200 字节，可整颗芯片只有 20 KB（20 480 字节）SRAM，装不下；只能分块发，每块几千字节。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

这一章的 SPI 结论只钉在订货号 STM32F103C8T6 上。

**时钟。** SPI1 在 APB2 上，本书的配置下它的时钟 PCLK2 = 72 MHz。工作点整格照抄附录 D：Mode 0，`BR=010`，SCK = 9 MHz。

**脚号。** 复位后的默认脚是 LQFP48 第 15 脚 PA5 = SPI1_SCK，第 17 脚 PA7 = SPI1_MOSI，第 16 脚 PA6 = SPI1_MISO，第 14 脚 PA4 = SPI1_NSS（[DS5319 Rev 20 表 5](#source-ds5319-spi)）。本章片选不用硬件 NSS：PA4 配成推挽 GPIO，软件拉低再拉高。这不是第 07 章的开漏。第 14 脚在 C8 上不是 DAC 输出。

**重映射。** SPI1 可以整组搬到 PA15、PB3、PB4、PB5，那要置 AFIO_MAPR 的 SPI1_REMAP 位（RM0008 Rev 21 表 56）。换到重映射脚时，上面的 PA5/PA6/PA7 作废。重映射不画进正常路径：PB3、PB4 复位后是 JTAG 的 JTDO 和 NJTRST，要先用 AFIO_MAPR 的 SWJ_CFG 关掉 JTAG 才能让给 SPI1。第 16 脚同时是第 05 章的 TIM3_CH1；本图只画 MISO。

**模式。** Mode 0 是 CPOL = 0、CPHA = 0：空闲时 SCK 为低，数据在第一个边沿（上升沿）采样。章内代码写的是 `SPI_POLARITY_LOW`、`SPI_PHASE_1EDGE`、`SPI_NSS_SOFT`、`SPI_FIRSTBIT_MSB`、`SPI_BAUDRATEPRESCALER_8`。

**分频。** `BR[2:0]` 只有 2、4、8、16、32、64、128、256 这八档（[RM0008 Rev 21 第 25.5.1 节](#source-rm0008-spi)）。`010` 是 ÷8，`72 / 8 = 9` MHz。`001` 是 ÷4，18 MHz。`000` 是 ÷2，36 MHz。36 MHz 是相对 9 MHz 工作点的过快失败，不另开一套账；它也超过了 DS5319 Rev 20 表 43 给主机模式的 18 MHz 上限（[DS5319](#source-ds5319)）。不支持 ÷3。不编 SPI 基址。

**ID 三字节。** 主机发出 `{0x9F, 0xFF, 0xFF, 0xFF}`。全双工下，发 `0x9F` 的那 8 个 SCK 同时移进 `rx[0]`，这一字节不是厂商号。接下来三字节是 `rx[1]=0xEF`、`rx[2]=0x40`、`rx[3]=0x17`，拼法是 `rx[1] << 16 | rx[2] << 8 | rx[3]`，也就是 `0xEF4017`。`0x40` 是存储器类型，不是容量。页大小 256 字节。这两句对照的是 [已有例程](#source-project-examples) 和附录 D。例程把状态字节的位 0 当成忙，那是 W25Q64 自己的位，不是 SPI 外设 SR 里的 BSY。`0x05`、`0x06`、`0x02`、`0x03` 四条命令在代码实现一节。

**失败路径。** MOSI 和 MISO 对调之后，三字节对不上 `0xEF 0x40 0x17`，这是主图的失败路径。片选一直为低时，下一条命令接在上一条后面。只调用 Transmit、不读 MISO 时，接收一侧会溢出，下一次读到的是残留（RM0008 Rev 21 第 25.3.10 节）。CPHA 配成第二沿时，字节会错位。片选不释放和 `BR=000` 的 36 MHz 放在旁注。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-08-spi-jedec.svg" width="760" alt="Mode 0、除以 8 得到 9 MHz；0x9F 之后的三字节是 0xEF、0x40、0x17；MOSI 和 MISO 对调之后对不上">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48。第 14 脚 PA4 = CS（推挽，事务期间为低），第 15 脚 PA5 = SCK，第 16 脚 PA6 = MISO，第 17 脚 PA7 = MOSI。CPOL = 0，CPHA = 0，BR=010，SCK = 9 MHz。正常路径 MOSI 先送 0x9F，随后三个 0xFF；rx[1] 到 rx[3] 是 0xEF、0x40、0x17。失败路径是 PA6 与 PA7 对调。旁注：PA4 一直为低时两条事务粘成一条；BR=000 时 SCK = 36 MHz。不把第 14 脚画成 DAC。出处是 [RM0008 Rev 21 第 25.5.1 节](#source-rm0008-spi) 和 [DS5319 Rev 20 表 5](#source-ds5319-spi)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/spi-jedec.gif" width="640" alt="片选拉低后移出 0x9F，再移入 0xEF、0x40、0x17">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径，并标出 9 MHz。印刷以静态主图为准。对调线和 36 MHz 不在这条 GIF 上。</sub>
</p>

主图画的就是实验一的那次事务，可以拿逻辑分析仪的截图逐字节对照。正常路径：PA4 拉低，MOSI 依次送出 0x9F 和三个 0xFF，MISO 在后三个字节回 0xEF、0x40、0x17。失败路径：PA6 和 PA7 对调，三个字节对不上。旁注是两种常见错误：PA4 一直为低，两条事务粘成一条；BR=000，SCK 变成 36 MHz。章首的 `spi-transfer.svg` 是会动的辅图，四种模式的时序画在那张图上；PDF 里它不会动，脚位、9 MHz 和 ID 三字节以这张静态主图为准。

## 时序与状态

下表按时间顺序走一遍实验一的读 ID 事务，最后三行是模式、速率和失败路径。按 9 MHz 算，一个字节 8 个时钟约 0.89 µs，4 个字节共 32 个时钟约 3.6 µs，HAL 函数本身的开销不算在内。模式和分频出自 [RM0008 Rev 21 第 25 章](#source-rm0008-spi)，三个 ID 字节和 256 字节的页大小出自 [例程](#source-project-examples)。

| 行 | 字节序号 | MOSI | MISO | CS | SCK |
| --- | --- | --- | --- | --- | --- |
| 正常 | 1 | 0x9F | rx[0]，不是厂商号 | 低 | 上升沿采样 |
| 正常 | 2 | 0xFF | 0xEF | 低 | 上升沿采样 |
| 正常 | 3 | 0xFF | 0x40 | 低 | 上升沿采样 |
| 正常 | 4 | 0xFF | 0x17 | 低 | 上升沿采样 |
| 结束 | — | — | — | 等 BSY 清零后回到高 | 空闲为低 |
| 模式 | — | — | — | — | CPOL = 0，CPHA = 0 |
| 速率 | — | — | — | — | BR=010 为 9 MHz，BR=001 为 18 MHz，BR=000 为 36 MHz（超出 18 MHz 上限） |
| 失败 | 2 到 4 | — | 不是 0xEF 0x40 0x17 | 低 | PA6 与 PA7 对调 |

页大小 256 字节：一条页编程命令最多写到页尾。

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 读回的 ID 不是 0xEF4017 | PA7 不是 MOSI，或 PA6 不是 MISO，或模式不是 0 | 保持 Mode 0，并核对 PA7 是 MOSI、PA6 是 MISO | [DS5319](#source-ds5319-spi) | LQFP48 第 16 脚是 MISO，第 17 脚是 MOSI。三字节本身见下一行 |
| 把 rx[0] 当成厂商号 | 发命令的那 8 个 SCK 同时移进了 rx[0] | 厂商号在 rx[1]，类型在 rx[2]，容量在 rx[3] | [例程](#source-project-examples) | 命令是 0x9F。三字节是 0xEF、0x40、0x17。0x40 不是容量。页大小 256 字节 |
| SCK 跑到 36 MHz | BR 写成了 000 | BR 用 010，得到 9 MHz | [RM0008](#source-rm0008-spi) | 八档分频里 010 是 ÷8。000 是 ÷2 = 36 MHz。不支持 ÷3 |
| BR 用 001 时偶尔读错 | 18 MHz 已经到了芯片的上限，线长时边沿跟不上 | 退回 010，或者缩短连线 | [DS5319](#source-ds5319) | 表 43：主机模式下 SCK 最高 18 MHz |
| 两条命令粘在一起 | PA4 一直为低 | 每条事务结束把 PA4 拉高 | [DS5319](#source-ds5319-spi) | 第 14 脚是 SPI1_NSS。本章把它当推挽片选。它在 C8 上不是 DAC 输出 |
| ID 出现在 PB3/PB4/PB5 | 用了重映射，还当成复位默认 | 复位后的默认脚是 PA5/PA6/PA7 | [DS5319](#source-ds5319-spi) | 第 15 脚 SCK，第 16 脚 MISO，第 17 脚 MOSI |
| 只发不收之后，第一次读到的是旧数据 | 接收一侧溢出，DR 里留着没读走的旧字节 | 用 `HAL_SPI_TransmitReceive()`；自己写寄存器时先读 DR、再读 SR，清掉 OVR | [RM0008](#source-rm0008) | 第 25.3.10 节：溢出后 DR 保留旧字节，之后的数据丢失；先读 DR 再读 SR 清除 OVR |
| SPI 一使能就停，CR1 的 MSTR 被清零 | 软件管理 NSS 时 SSI 是 0，触发了 MODF | SSM 和 SSI 一起置 1 | [RM0008](#source-rm0008) | 第 25.3.10 节：主机的 NSS 为低（软件管理时是 SSI 为 0）会置 MODF，SPE 和 MSTR 被清零 |
| 擦写之后马上读，数据不对 | 等错了「忙」：SPI 外设 SR 的 BSY 只说明 STM32 这边移完了，Flash 内部还在擦写 | 发 0x05 轮询状态字节的位 0，变成 0 再继续 | [例程](#source-project-examples) | 例程把状态字节的位 0 当成忙，并带超时轮询 |

下面几条没有放进表里，因为清单里没有能证明它们的出处卡：W25Q64 的命令（0x06、0x05、0x02、0x03、0x20）、状态寄存器的 BUSY 位、页内绕回、擦除得到 0xFF、擦写时间和 10 万次的擦写寿命，出自 Winbond 的 W25Q64 数据手册；ST7789 的命令、DC 线和复位后的等待时间，出自 Sitronix 的 ST7789 数据手册；`HAL_SPI_Receive()` 把缓冲区当无用字节发出去、`HAL_SPI_Transmit()` 结束时清 OVR、发送完成回调之前先等 BSY，是 STM32CubeF1 HAL 源码里的写法。

## 相关资源

- 官方手册：**RM0008** 第 25 章（SPI）；W25Q64、ST7789 数据手册
- 上一篇：[07 I2C总线](07-I2C总线.md)
- 手机阅读版：[第 08 章 · SPI总线（公众号图文）](https://mp.weixin.qq.com/s/FOR_DIzh4qdzByi0qAI1Jg)
- 相关图：[`assets/animations/spi-transfer.svg`](../assets/animations/spi-transfer.svg)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。
