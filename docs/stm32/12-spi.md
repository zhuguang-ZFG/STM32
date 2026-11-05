---
title: S12 SPI：全双工的移位艺术
status: done
difficulty: 3
minutes: 45
---

# S12 SPI：四根线的全双工移位

> 🎯 SPI 是协议里的"直性子"：没有地址、没有 ACK、没有仲裁——片选一拉低，两个移位寄存器头尾相接成环，时钟每跳一下，两边各换一位。发和收是**同一个动作**的两面，这就是全双工的本质。

## 本章精髓

1. 移位环的真相：写 DR 发一个字节的同时必然收一个字节，所以"只想读"也要"假写"（发 0xFF/0x00），"只想写"也要"读走"收到的字节（否则溢出）。
2. CPOL/CPHA 四模式是"时钟相位"的排列组合：空闲电平（CPOL）× 第几沿采样（CPHA）：主从必须同款，模式错了数据错位还不报错（逻辑分析仪一眼识破）。
3. NSS 的管理哲学：硬件 NSS（SSM/SSOE）vs 软件 GPIO 拉片选：多从机/长帧场景软件片选更可控，大多数实战选软件。

- **能理解**：为什么"只想读一个字节"也必须写 DR；为什么 OVR（溢出）是"只写不读"的必然结局而不是偶发故障。
- **能用**：寄存器级把 W25Q 的 JEDEC ID 读出来、页写 256 字节再读回比对；分析仪上指认模式 0/3 的差异。

## 先修

- [S11 I2C](11-i2c.md)（抓包方法论）、[S3 复用](03-gpio.md)。

## 先跑起来（10 分钟 quick win）

SPI1（PA5/6/7，AF5，以 datasheet 为准）接 W25Q，发 `0x9F` 读三字节，串口打印出厂商/容量 ID，链路即通。

读回之前先押个交换：主机每移出去一位，手里是不是同时就收进一位？还是得等一个字节全部发完，才开始收自己的？押完往下读，答案就藏在移位环里：收发同拍到底是巧合还是必然。

## 动画：Mode 0 逐拍采样

一帧 8 拍：CS 拉低后，SCK 每个**上升沿**两根数据线各被采走 1 bit：主机发 0xA5 的同时收回 0x3C，收发同拍是移位环的必然，不是巧合。底部四宫格对照四种 CPOL/CPHA 模式，W25Q 系列 FLASH 支持 Mode 0/3。

![SPI 时序动画](/anim/spi-timing.svg)

## 板卡事实

- SPI1 引脚：SCK=PA5、MISO=PA6、MOSI=PA7，复用功能 **AF5**；片选没有专用引脚的硬性要求，本章用软件 GPIO（PA4，以 datasheet 与板卡规格书为准）。
- SPI1 挂 **APB2**（RCC_APB2ENR bit12 = `RCC_APB2ENR_SPI1EN_Msk` 0x1000，CMSIS 已核对）；霸天虎标准时钟树下 APB2 = 84MHz（[S2](02-rcc-clock.md)）→ 最高分频档 SCK = 42MHz。
- W25Q 系列（以你手上型号的 Winbond 手册为准）：JEDEC ID 命令 0x9F 回三字节（厂商 0xEF=Winbond、类型/容量两个字节）；状态寄存器命令 0x05，**BUSY = bit0**；页写 0x02（页 256 字节）、快读 0x03、写使能 0x06、扇区擦 0x20。
- 逻辑分析仪采样率 ≥ 4×SCK（抓 1MHz 的包至少 4MS/s；E02 的方法论直接复用）。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 移位环 | 主从移位寄存器成环；收发同拍的必然 | 库解析 |
| 四模式 | CPOL/CPHA 波形四宫格；器件手册怎么标 | 配置 |
| 最小收发 | 写 DR→等 TXE/RXNE→读 DR；BSY 收尾 | 代码分析 |
| W25Q 实战 | JEDEC ID/页写/读状态寄存器忙等 | 代码分析 |
| 片选策略 | 软 NSS vs 硬 NSS；多从机星型接线 | 引脚 |
| 提速与 DMA | 分频表、长帧 DMA（S8 复用） | 配置 |
| SPL 对照 | SPI_Init 八字段到 CR1/CR2 的落位 | 库解析 |

## 一、移位环：发即是收，收即是发

SPI 的硬件模型一张图说完：主机和从机各有一个 8 位移位寄存器，MOSI 把主机的"出"接到从机的"进"，MISO 把从机的"出"接回主机的"进"，**头尾相接，闭合成环**。时钟每来一拍，两边寄存器同步挪一位：主机移出去的是它 DR 里的新字节，移进来的是从机 DR 里的内容；8 拍之后，两个字节**完成对调**。

这个模型立刻推出三条在 I2C 里不成立的规矩：

1. **没有"只发"或"只收"**：8 拍一跑，两边都换了一个字节。想读 Flash 的状态寄存器？你也得**发**点什么（惯例 0xFF 或 0x00）去"顶"出从机的数据。
2. **发完必须收**：哪怕你根本不要从机回话，DR 里那个交换回来的字节也得读走；不读，下一个字节交换完成时 **OVR（overrun，SR bit6）** 置位，后续接收悄悄断线。
3. **没有地址阶段、没有 ACK**：选谁靠片选，收没收对靠应用层校验。SPI 的"简单"是把协议的活转嫁给了"片选+全双工"这两件事。

![SPI 全双工移位环：主机和从机各一个 8 位移位寄存器，MOSI 与 MISO 同时移出一位、移入一位](/figures/stm32-12-spi.svg)

## 二、四模式：CPOL/CPHA 的排列组合

SPI 帧只有两个自由度，全部写在 CR1 的最低两位（CMSIS 已核对：CPHA=bit0、CPOL=bit1）：

- **CPOL**：空闲时 SCK 停在什么电平（0=低、1=高）；
- **CPHA**：在第几个时钟沿采样（0=第一个沿、1=第二个沿）。

| 模式 | CPOL | CPHA | 空闲 SCK | 采样沿 | 数据何时变 |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 低 | 第 1 个沿（上升） | 每个下降沿 |
| 1 | 0 | 1 | 低 | 第 2 个沿（下降） | 每个上升沿 |
| 2 | 1 | 0 | 高 | 第 1 个沿（下降） | 每个上升沿 |
| 3 | 1 | 1 | 高 | 第 2 个沿（上升） | 每个下降沿 |

模式 0 与模式 3 是实战双主流：**采样沿同为"数据稳定后被抓"的安排**，区别只在空闲电平。W25Q 手册标"支持 Mode 0 与 Mode 3"，很多器件两档都能跑，但**主从必须同款**：模式错配不报错，症状是"MOSI 上的数据看起来对，从机读到的全错位一位"，分析仪上 MOSI 波形完全正常，破案只能靠把 SCK 空闲电平和采样沿对表。

器件手册的读法：一般写"CPOL=0/CPHA=0"或直接画时序图（图里标 CPOL/CPHA 或 TI 的"CKP/CKE"：TI 记法与 Motorola 记法还要换算，认波形别认缩写）。

## 三、最小收发：写 DR、等两个标志、一个 BSY 收尾

寄存器级一次字节交换（无项目依赖，可直接进任何工程）：

```c
#include "stm32f407.h"   /* CMSIS 设备头：SPI_TypeDef 与 SPI_SR_TXE/RXNE/BSY */

static uint8_t spi_xfer(SPI_TypeDef *spi, uint8_t b)
{
    while (!(spi->SR & SPI_SR_TXE)) { }        /* ① 等 TXE=1（bit1）：TX 缓冲空 */
    *((__IO uint8_t *)&spi->DR) = b;           /* ② 写 DR——8 位帧必须按字节访问（见下注） */
    while (!(spi->SR & SPI_SR_RXNE)) { }       /* ③ 等 RXNE=1（bit0）：交换回来的字节就位 */
    return *((__IO uint8_t *)&spi->DR);         /* ④ 读走它：RXNE 自动清，OVR 无机可乘 */
}
```

四步没有任何一步可以省：

- **① TXE**（SR bit1，CMSIS 已核对）：写 DR 前必须等它，上一字节还没搬进移位寄存器就写，等于覆盖；
- **② 按字节访问 DR**：F4 的 SPI 在 DFF=0（8 位帧）时规定 DR 按**单字节**访问（RM0090 data packing：按半字访问会一次塞进两个字节）；CMSIS 里 DR 是 32 位成员，所以要 `(__IO uint8_t*)&spi->DR` 这刀 cast；
- **③ RXNE**（SR bit0）：交换完成的证据：**等它就是等"对方的 8 拍全部走完"**；
- **④ 读走**：就算你不需要返回值也要读（丢弃返回值），这是"只写场景"必须履行的另一半合同。

**收尾第三件事：等 BSY=0 再放片选。** 一帧最后一个字节交换完，TXE 早就置位了，但移位寄存器可能还在蹦最后几拍，此刻拉高 CS，从机收到的就是被掐断的半个字节。法定顺序：

```c
static void spi_cs_high(void) { GPIOA->BSRR = (1u << 4) << 16; }   /* PA4 置高（BSRR 复位半区） */

/* 帧收尾 */
while (!(SPI1->SR & SPI_SR_TXE)) { }
while (SPI1->SR & SPI_SR_BSY) { }   /* BSY（bit7）=0：移位寄存器真正空闲 */
(void)*((__IO uint8_t *)&SPI1->DR);
spi_cs_high();
```

（[BSRR 复位半区](../c/07-ub-misra.md) 的 `1UL << (pin+16)` 掩码纪律在 C7 刚复习过。）

## 四、W25Q 实战：读 ID、页写、忙等

三个动作把 SPI 的典型工作流全覆盖。命令时序以 Winbond 手册为准，代码框架如下：

```c
/* 读 JEDEC ID：0x9F → 连收三字节。每收一字节都要"假写"顶出来 */
static void w25q_read_jedec(uint8_t id[3])
{
    spi_cs_low();
    (void)spi_xfer(SPI1, 0x9F);     /* 发命令，同时收回一个无所谓字节（读走） */
    id[0] = spi_xfer(SPI1, 0xFF);   /* 想读：发哑数据 0xFF 顶出对方字节 */
    id[1] = spi_xfer(SPI1, 0xFF);
    id[2] = spi_xfer(SPI1, 0xFF);
    spi_cs_high();                   /* 单字节帧，BSY 会在 spi_xfer 的 RXNE 等待里自然走完 */
}

/* 读状态寄存器：0x05 → 1 字节，BUSY=bit0 */
static uint8_t w25q_read_status(void)
{
    spi_cs_low();
    (void)spi_xfer(SPI1, 0x05);
    uint8_t s = spi_xfer(SPI1, 0xFF);
    spi_cs_high();
    return s;
}
```

读 JEDEC ID 是**链路自检**的标准第一步：0xEF 40 xx 三字节一出来，物理层、模式、片选、时序全部 OK，烧到板子后第一条要跑的就是它。**页写**多三样规矩：

```c
static void w25q_wait_idle(void)
{
    while (w25q_read_status() & 0x01) { }   /* BUSY 位轮询：写/擦期间必须等 */
}

static void w25q_page_program(uint32_t addr, const uint8_t *src, uint32_t len)
{
    /* 预防性断言：页 256 字节 + 页内不回绕（W25Q 页编程越界不会帮你换页） */
    if (len == 0 || len > 256 || (addr & 0xFF) + len > 256) { return; }

    spi_cs_low();
    (void)spi_xfer(SPI1, 0x06);        /* 写使能：每次编程/擦除前都要重发 */
    spi_cs_high();                      /* WE 是"一次性令牌"，靠 CS 边沿生效 */

    spi_cs_low();
    (void)spi_xfer(SPI1, 0x02);        /* Page Program */
    (void)spi_xfer(SPI1, (uint8_t)(addr >> 16));   /* 24 位地址，高字节先行 */
    (void)spi_xfer(SPI1, (uint8_t)(addr >> 8));
    (void)spi_xfer(SPI1, (uint8_t)addr);
    for (uint32_t i = 0; i < len; i++) {
        (void)spi_xfer(SPI1, src[i]);
    }
    spi_cs_high();
    w25q_wait_idle();                   /* tPP 期间 BUSY=1，轮询等它落地 */
}
```

三条 W25Q 的脾气（全部有对照物）：**写使能是一次性的**（CS 拉高即失效，下次操作前重发），对应 I2C 里 AT24C02 的页写回绕；**页内不回绕**（越界部分被丢弃/拒绝，按你的手册为准），对应 S11 的页对齐纪律；**编程/擦除期间 BUSY=1**（只能轮询状态寄存器，器件不 NACK 也不报错），对应 S11 的 tWR+ACK polling。**每个协议都要伺候"器件的擦写周期"，只是 SPI 里没有 ACK 帮你踩刹车，全靠应用层主动查。**

## 五、片选策略：软 NSS vs 硬 NSS

NSS 的两种管法：

- **软件片选**（本章默认）：NSS 相关位全不使能，CS 就是普通 GPIO：拉低开帧、BSY 清零后拉高收帧。优点：**片选时机 100% 由代码掌控**（能精确覆盖"命令+数据"整段）、多从机随便加（每个从机一根 CS）、可以控制"一个逻辑事务跨多帧"（比如 JEDEC 三字节必须同一次 CS 低电平）。
- **硬件 NSS**：CR1 的 SSM=bit9（CMSIS 已核对）=0 时 NSS 引脚接管片选，主模式配 CR2 的 SSOE=bit2 输出片选，每**一帧**自动起落。坑在于：SSOE 的片选是"字节级"的，多字节命令会被逐字节切断；而主模式忘配 SSOE、NSS 又被外部拉低，触发 **MODF**（模式错误，SR bit5）：SPE 被硬件清掉、MSTR 被降级成从机，一个静默的"我咋不发了"。
- **单主机的"防误伤"写法**：SSM=1 且 SSI=bit8 置 1：NSS 信号内部强制为高，外部引脚完全脱钩，MODF 从根上不可能。这是"软件片选+硬件免疫"的组合拳，主模式裸跑（不用 SSOE、CS 走 GPIO）时的标准姿势。

多从机接线：**星型**：SCK/MOSI/MISO 三线共享，每从机独享一根 CS；MISO 是"谁被选中谁开口"的总线，没人选中时其输出脚应呈高阻（模块一般用输出使能自动处理，自己拼电路时要看器件的 MISO 三态条件）。

## 六、提速与 DMA：分频表与"长帧交给 DMA"

波特率没有"位数"可填，只有**分频档**：CR1 的 BR=bits3-5（CMSIS：0x38），编码 000~111 对应 fpclk/2 ~/256。SPI1 挂 APB2=84MHz：

| BR 编码 | 分频 | SCK（SPI1@84MHz） |
|---|---|---|
| 000 | /2 | **42 MHz**（极限档，等长短线+回流地） |
| 001 | /4 | 21 MHz（短杜邦线可用） |
| 010 | /8 | 10.5 MHz |
| 011 | /16 | 5.25 MHz |
| … | … | … |
| 111 | /256 | 328 kHz（调通起步档） |

调通纪律：**先 /256 或 /16 把链路读对，再逐档提速**：分析仪采样率跟不上时，先修仪器再修速度；42MHz 档上杜邦线就是天线（骨架坑列表里那句"30cm 杜邦线还想 42MHz"的现实版）。

长帧（整页 256 字节、屏刷新缓冲）逐字节 `while` 等标志是浪费 CPU：移位环是全场最不用盯的员工，时钟一响必然换位，递料的活交给 DMA 就行。开 CR2 的 TXDMAEN=bit0 / RXDMAEN=bit1（CMSIS 已核对），收发两路 DMA 流按 [S8](08-dma.md) 的选型表配置，CPU 只管铺数据、配计数、等传输完成标志。注意 [S8](08-dma.md) 的旧坑直接适用：**SPI 的 DMA 请求不在 DMA1，F407 的 SPI1 在 DMA2**（S8 章内表的既有结论）；且 DMA 收发要**成对配置**：这就是第一节"发即是收"的 DMA 版：只发不配收流，OVR 照样等你。

## 七、SPL 对照：`SPI_Init` 八字段落位

SPL 的 `SPI_InitTypeDef` 八字段到寄存器的落位（对照 stm32f4xx_spi.c V1.8.0 的翻译逻辑，位号已经 CMSIS 核对）：

| 结构体字段 | 取值 → 寄存器落位 |
|---|---|
| `SPI_Direction` | 全双工不动位；`Direction_1Line_Tx/Rx`→ BIDIMODE/BIDIOE；`Direction_2Lines_RxOnly`→ RXONLY（CR1 bit15/bit14/bit10） |
| `SPI_Mode` | `Mode_Master` → **MSTR**（CR1 bit2）；从机则清 |
| `SPI_DataSize` | `DataSize_8b/16b` → **DFF**（CR1 bit11） |
| `SPI_CPOL` | → **CPOL**（CR1 bit1） |
| `SPI_CPHA` | → **CPHA**（CR1 bit0） |
| `SPI_NSS` | `NSS_Soft` → **SSM**（CR1 bit9）=1；`NSS_Hard`→SSM=0+CR2 **SSOE**（bit2）看主从 |
| `SPI_BaudRatePrescaler` | `_2.._256` → **BR**（CR1 bits3-5），编码即 0x00/0x08/0x10/…/0x38 |
| `SPI_FirstBit` | `FirstBit_MSB` 不动位；`_LSB` → **LSBFIRST**（CR1 bit7） |

`SPI_Cmd(SPIx, ENABLE)` 就是 SPE（CR1 bit6）置 1，**先 Init 后 Cmd**，SPE 置 1 前的配置都算"备机"，置 1 那一刻外设才咬合齿轮。读库姿势照旧（[S15](15-spl-anatomy.md) 的方法论）：拿到任何 SPL 工程先问"SPI_Init 把我的参数翻成了 CR1 的哪几位"，拿本节的表对答案，RM0090 永远是终审。

## 记忆锚点

::: tip 一句话记住
**片选拉低成环，发即是收收即是发；CPOL 定闲电平，CPHA 定哪沿采样；读 ID 先行，忙等看 BUSY。**
:::

**延伸**：多任务共享 SPI 总线需互斥锁（[F5](../rtos/freertos/05-sem-mutex.md)）；长帧传输用 DMA（[S8](08-dma.md)）释放 CPU。

## 实物实验

- 读 W25Q JEDEC ID + 页写 256 字节再读回比对；
- 分析仪对比模式 0/3 波形差异，导出双图存档。

## 常见坑

- **只写不读**：RXNE 溢出标志置位，通信悄悄断线，收发必须成对处理。
- **模式与器件不符**：W25Q 支持模式 0/3，换错模式读出的 ID 全错。
- **片选提前拉高**：BSY 还在忙就释放 NSS，最后字节报废，收尾等 BSY=0。
- **长走线跑高速**：杜邦线 30cm 还想 42MHz，先降到 1MHz 调通再提速。
- **8 位帧按 32 位写 DR**：违反 data packing：一次塞两个字节，波形"莫名"多一拍（第三节注）。
- **SPI 的 DMA 去找 DMA1**：F407 的 SPI1 请求在 DMA2（[S8](08-dma.md) 结论），配错流连"不工作"都算幸运。

## 短自测

1. 为什么"只读一个字节"也必须往 DR 写东西？发 0xFF 那一步在硬件上干了什么？
<details><summary>参考答案</summary>移位环两侧每拍同步交换：不写 DR，主机移位寄存器里就没有"料"推过去顶出从机的数据。发 0xFF（哑数据）就是用主机的移位输出把从机字节一拍一拍"顶"回 MISO，8 拍之后 DR 里躺着要读的字节。只想读 = 用假写驱动时钟，这是移位环的物理必然。</details>

2. OVR 什么时候置位？为什么说它是"设计错误"而不是"偶发故障"？
<details><summary>参考答案</summary>上一个交换完成的字节没被读走、新字节又收满时，SR 的 OVR（bit6）置位。它必然发生在"只写不读"的循环里，每写 DR 一次，硬件就同步收进一个字节，不读走就攒不下第二个。清 OVR 要读 SR 再读 DR（顺序见 RM0090），但根治是像 spi_xfer 那样收发成对。</details>

3. 模式 0 和模式 3 在分析仪上怎么一眼区分？它们为什么经常可以互换？
<details><summary>参考答案</summary>看 CS 拉低后、第一个数据变化前的 SCK 电平：低=模式 0，高=模式 3。两者的采样沿安排都能让数据在稳定期被采样（都是"一沿变、一沿采"的互补节奏），所以支持"第一沿采样"的器件常两档都兼容，但主从必须同款，错配的症状是数据整体错位一位而不报任何错。</details>

4. 为什么单主机的寄存器版代码常配 SSM=1、SSI=1，哪怕片选用的是 GPIO？
<details><summary>参考答案</summary>SSM=1 时 NSS 信号由 SSI 位内部提供（SSI=1 = 一直"高"=没人在选我当从机），外部 NSS 引脚彻底脱钩。这样即使 NSS 脚被外部干扰拉低、或复用成别的功能，MODF（模式错误）也无从触发，SPE 不会被硬件偷偷清掉。这是"软件片选+硬件免疫"的组合拳。</details>

5. 42MHz 需要什么条件？"先 /256 再提速"省的是什么？
<details><summary>参考答案</summary>等长或极短的走线、完整回流地、尽量少的过孔与转接（必要时上端接阻抗匹配）；杜邦线原型上请回到 5~10MHz 以内。先低分频调通省的是"分不清是协议错还是信号完整性错"的排查成本：把变量一个一个引入，是 E02 就立下的调试纪律。</details>

<QuizBank chapter="s12-spi" />

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| CR1/SR 位号（CPHA/CPOL/MSTR/BR/SPE/SSM/SSI/TXE/RXNE/OVR/BSY） | CMSIS `stm32f407xx.h`（本站 `.trellis/ref/cmsis/`，逐位核对） |
| 8 位帧按字节访问 DR | RM0090 SPI 章 data packing 说明；本章 `spi_xfer` 第 ② 步 |
| `SPI_Init` 八字段翻译 | SPL V1.8.0 `stm32f4xx_spi.c`（第七节落位表） |
| W25Q 命令集（0x9F/0x05/0x02/0x06/0x20） | Winbond W25Q 系列手册（以你的型号为准） |
| 波形逐拍对表 | 动画 [spi-timing.svg](/anim/spi-timing.svg) + [E02](../lab/e02-logic-uart.md) 抓包方法论 |
| 分频表与 84MHz 实算 | 本站 [S2 RCC](02-rcc-clock.md) 时钟树 + 第六节表 |
| DMA 选型（SPI1→DMA2） | [S8 DMA](08-dma.md) 请求映射表 |

## 你做到了

- 全双工移位从抽象变直觉；
- 拿下第一块 SPI 器件，抓包对表技能二次实战。

<div class="achievement">
✅ 下一站：<a href="13-flash-iap.html">S13 内部 Flash 与 IAP</a>：让固件学会给自己动手术。
</div>
