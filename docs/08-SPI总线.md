# 08 SPI 总线

> English: [SPI](en/08-spi.md)

> SPI 的主机每发出一位，就同时收回一位，像两个人隔着桌子互换纸条。这一章用读 W25Q64 的 ID 0xEF4017 讲清楚这件事。

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

## 原理与适用范围

本章的数字都按 STM32F103C8T6 算。SPI1 挂在 APB2 上，时钟 72 MHz。工作点和附录 D 一致：Mode 0，`BR=010`，SCK = 9 MHz。如果用了重映射，下面的 PA5/PA6/PA7 要换成 PB3/PB4/PB5。

复位后 SPI1 在 LQFP48 的第 14～17 脚：第 14 脚 PA4 = SPI1_NSS，第 15 脚 PA5 = SPI1_SCK，第 16 脚 PA6 = SPI1_MISO，第 17 脚 PA7 = SPI1_MOSI。片选不用硬件 NSS，而是把 PA4 配成推挽输出，由软件拉低、拉高。I2C 那章用的是开漏，这里不是。第 16 脚也是第 05 章 TIM3_CH1 的输出脚，两个功能同一时间只能用一个。出处是 [DS5319 Rev 20 表 5](#source-ds5319-spi)。

Mode 0 是 CPOL = 0、CPHA = 0：空闲时 SCK 为低，在第一个边沿（上升沿）采样。对应的 HAL 配置是 `SPI_POLARITY_LOW`、`SPI_PHASE_1EDGE`、`SPI_NSS_SOFT`、`SPI_FIRSTBIT_MSB`、`SPI_BAUDRATEPRESCALER_8`。

`BR[2:0]` 只有 ÷2 到 ÷256 这八档，没有 ÷3。`010` 是 ÷8，`72 / 8 = 9` MHz；`001` 是 ÷4，18 MHz；`000` 是 ÷2，36 MHz。36 MHz 对杜邦线上的 W25Q64 太快，读回来的字节会乱。出处是 [RM0008 Rev 21 第 25.5.1 节](#source-rm0008-spi)。

读 ID 时主机发 `{0x9F, 0xFF, 0xFF, 0xFF}`。SPI 是全双工，发 `0x9F` 的那 8 个时钟里，MISO 上也移进了一个字节 `rx[0]`，它没有意义，不是厂商号。后面三个字节才是 ID：`rx[1]=0xEF`（Winbond），`rx[2]=0x40`（存储器类型，不是容量），`rx[3]=0x17`（容量，64 Mbit）。拼起来是 `rx[1] << 16 | rx[2] << 8 | rx[3]` = `0xEF4017`。W25Q64 一页 256 字节。[例程](#source-project-examples)把状态寄存器的位 0 当作忙标志来等。

读回的三个字节对不上 `0xEF 0x40 0x17`，最常见的原因是 MOSI 和 MISO 接反了。另外几种：片选一直不拉高，下一条命令会接在上一条后面；只调用 Transmit、不读 MISO，下一次读到的是上次留在接收寄存器里的字节；CPHA 配成第二沿，字节会错一位。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-08-spi-jedec.svg" width="760" alt="Mode 0、除以 8 得到 9 MHz；0x9F 之后的三字节是 0xEF、0x40、0x17；MOSI 和 MISO 对调之后对不上">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48。第 14 脚 PA4 = CS（推挽，事务期间为低），第 15 脚 PA5 = SCK，第 16 脚 PA6 = MISO，第 17 脚 PA7 = MOSI。CPOL = 0，CPHA = 0，BR=010，SCK = 9 MHz。正常路径 MOSI 先送 0x9F，随后三个 0xFF；rx[1] 到 rx[3] 是 0xEF、0x40、0x17。图下半部分是 PA6 与 PA7 接反时读到的错字节。右侧另标两种情况：PA4 一直为低时两条命令粘成一条；BR=000 时 SCK = 36 MHz。出处是 [RM0008 Rev 21 第 25.5.1 节](#source-rm0008-spi) 和 [DS5319 Rev 20 表 5](#source-ds5319-spi)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/spi-jedec.gif" width="640" alt="片选拉低后移出 0x9F，再移入 0xEF、0x40、0x17">
  <br><sub>▲ 动图版，只演示正常读 ID 的过程，SCK 为 9 MHz。印刷版只有上面的静态图。</sub>
</p>

## 时序与状态

| 行 | 字节序号 | MOSI | MISO | CS | SCK |
| --- | --- | --- | --- | --- | --- |
| 正常 | 1 | 0x9F | rx[0]，不是厂商号 | 低 | 上升沿采样 |
| 正常 | 2 | 0xFF | 0xEF | 低 | 上升沿采样 |
| 正常 | 3 | 0xFF | 0x40 | 低 | 上升沿采样 |
| 正常 | 4 | 0xFF | 0x17 | 低 | 上升沿采样 |
| 结束 | — | — | — | 回到高 | 空闲为低 |
| 模式 | — | — | — | — | CPOL = 0，CPHA = 0 |
| 速率 | — | — | — | — | BR=010 为 9 MHz，BR=001 为 18 MHz，BR=000 为 36 MHz |
| 失败 | 2 到 4 | — | 不是 0xEF 0x40 0x17 | 低 | PA6 与 PA7 对调 |

页大小 256 字节。出处是 [RM0008](#source-rm0008-spi) 与 [例程](#source-project-examples)。

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处里能查到什么 |
| --- | --- | --- | --- | --- |
| 读回的 ID 不是 0xEF4017 | PA7 不是 MOSI，或 PA6 不是 MISO，或模式不是 0 | 保持 Mode 0，并核对 PA7 是 MOSI、PA6 是 MISO | [DS5319](#source-ds5319-spi) | LQFP48 第 16 脚是 MISO，第 17 脚是 MOSI。三字节本身见下一行 |
| 把 rx[0] 当成厂商号 | 发命令的那 8 个 SCK 同时移进了 rx[0] | 厂商号在 rx[1]，类型在 rx[2]，容量在 rx[3] | [例程](#source-project-examples) | 命令是 0x9F。三字节是 0xEF、0x40、0x17。0x40 不是容量。页大小 256 字节 |
| SCK 跑到 36 MHz | BR 写成了 000 | BR 用 010，得到 9 MHz | [RM0008](#source-rm0008-spi) | 八档分频里 010 是 ÷8。000 是 ÷2 = 36 MHz。不支持 ÷3 |
| 两条命令粘在一起 | PA4 一直为低 | 每条事务结束把 PA4 拉高 | [DS5319](#source-ds5319-spi) | 第 14 脚是 SPI1_NSS。本章把它当推挽片选。它在 C8 上不是 DAC 输出 |
| ID 出现在 PB3/PB4/PB5 | 用了重映射，还当成复位默认 | 复位后的默认脚是 PA5/PA6/PA7 | [DS5319](#source-ds5319-spi) | 第 15 脚 SCK，第 16 脚 MISO，第 17 脚 MOSI |
| 状态字节的位 0 被当成协议里的忙 | 这是例程的做法 | 只按例程去等这一位 | [例程](#source-project-examples) | 例程把状态字节的位 0 当成忙 |

## 学习目标
- [ ] 理解 SPI 四线制与全双工移位原理
- [ ] 掌握 CPOL/CPHA 四种模式与常用器件模式
- [ ] 会算 SPI 速率与时钟分频（BR 位）
- [ ] 会比较软件模拟与硬件 SPI，了解 DMA 刷屏
- [ ] 会用 W25Q64 读 ID/读写页、ST7789 初始化

## 核心原理

SPI 是一主多从的总线。主机和从机各有一个移位寄存器，两个寄存器首尾相接成环，主机每移出一位，从机就同时移回一位。

### 1. 四根线与移位原理

SPI 像两个人隔着桌子换牌。主机手里 8 张，从机手里 8 张，主机每拍一下桌子（SCK 一个时钟），双方同时把最边上的一张推给对方。拍 8 下，两边的牌正好全换了一遍。所以 SPI 没有「只读」这回事：想读从机一个字节，主机也得推过去一个字节，通常推 0xFF 当填充。CS 拉低是告诉某一个从机「这局跟你玩」。

| 线 | 全称 | 方向 | 说明 |
| --- | --- | --- | --- |
| SCK | Serial Clock | 主→从 | 时钟 |
| MOSI | Master Out Slave In | 主→从 | 主机发 |
| MISO | Master In Slave Out | 从→主 | 从机发 |
| NSS/CS | Slave Select | 主→从 | 片选，低有效 |

移位原理：主从各有一个 8 位移位寄存器，构成环形。每个时钟沿双方各移出 1 位、移入 1 位，8 个时钟后完成一次字节交换。

### 2. CPOL/CPHA 四种模式

四种模式只是在约定两件事。CPOL 说桌子没拍的时候手放在上面还是下面，也就是时钟空闲是低还是高。CPHA 说是在拍下去的那一刻看牌，还是在抬起来的那一刻看牌，也就是第 1 个边沿还是第 2 个边沿采样。两边约定不一致，每一位都会差半拍，读回来的就是全 0、全 FF 或错位的数。

| 模式 | CPOL | CPHA | 空闲时钟 | 采样沿 | 常用器件 |
| --- | --- | --- | --- | --- | --- |
| Mode 0 | 0 | 0 | 低 | 第 1 沿（上升） | W25Q64、ST7789、多数器件 |
| Mode 1 | 0 | 1 | 低 | 第 2 沿（下降） | 部分传感器 |
| Mode 2 | 1 | 0 | 高 | 第 1 沿（下降） | 较少 |
| Mode 3 | 1 | 1 | 高 | 第 2 沿（上升） | W25Q64（也支持） |

> **先用 Mode 0 试；读 ID 全 0/全 FF 时优先怀疑模式不对。**

### 3. 速率与分频

SPI 的时钟由主机给，所以速度就是主机的总线时钟除以一个 2 的幂。分频只有 2 到 256 这八档，想要 10 MHz 是凑不出来的，只能在 9 MHz 和 18 MHz 之间选。速度上限多半不在芯片，而在线：杜邦线上跑 18 MHz 以上，波形已经圆得像正弦波了。

- SPI 时钟 = fPCLK / 分频系数（BR 位：2/4/8/16/32/64/128/256）。
- 例：APB2=72MHz，分频 8 → 9MHz。

| BR[2:0] | 分频 | 72MHz 下 SCK |
| --- | --- | --- |
| 000 | 2 | 36MHz |
| 001 | 4 | 18MHz |
| 010 | 8 | 9MHz |
| 011 | 16 | 4.5MHz |
| 100 | 32 | 2.25MHz |
| 101 | 64 | 1.125MHz |
| 110 | 128 | 0.5625MHz |
| 111 | 256 | 0.28125MHz |

### 4. NSS 管理与多从机

多个从机共用 SCK、MOSI、MISO 三根线，各自有一根 CS。主机想跟谁说话，就把谁的 CS 拉低，其他从机看到自己的 CS 是高，会把 MISO 放开不管。最省心的做法是把 CS 当普通 GPIO 自己控制，什么时候拉低、拉多久都看得见。

| 方式 | 说明 |
| --- | --- |
| 软件 NSS | 普通 GPIO 控制片选，最灵活（推荐） |
| 硬件 NSS | 由硬件管理，多主时用 |
| 多从机 | 每个从机独立 CS，共用 SCK/MOSI/MISO |

### 5. 软件模拟 vs 硬件 SPI

| 维度 | 软件模拟 | 硬件 SPI |
| --- | --- | --- |
| 速率 | 低（几十 kHz~几 MHz） | 高（几十 MHz） |
| CPU 占用 | 高 | 低 |
| 灵活性 | 高 | 低（固定引脚） |
| DMA | 无 | 支持（刷屏/读 Flash 快） |

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | W25Q64 | PA5=SCK, PA6=MISO, PA7=MOSI, PA4=CS | Mode 0/3 |
| BluePill | ST7789/ILI9341 | PA5=SCK, PA7=MOSI, PA4=CS, PA3=DC, PA2=RST | 只写，MISO 不用 |

## 代码实现

```c
/* spi_flash.c —— 硬件 SPI1 读 W25Q64 JEDEC ID（HAL） */
#include "stm32f1xx_hal.h"

SPI_HandleTypeDef hspi1;

#define FLASH_CS_LOW()   HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET)
#define FLASH_CS_HIGH()  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET)

#define CMD_JEDEC_ID     0x9F
#define CMD_READ_STATUS1 0x05
#define CMD_WRITE_ENABLE 0x06
#define CMD_PAGE_PROGRAM 0x02
#define CMD_READ_DATA    0x03

void SystemClock_Config(void);

static void spi_init(void)
{
    __HAL_RCC_SPI1_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA5/PA7 复用推挽，PA6 输入，PA4 普通输出做 CS */
    GPIO_InitTypeDef io = {0};
    io.Pin = GPIO_PIN_5 | GPIO_PIN_7; io.Mode = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH; HAL_GPIO_Init(GPIOA, &io);
    io.Pin = GPIO_PIN_6; io.Mode = GPIO_MODE_INPUT; io.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &io);
    io.Pin = GPIO_PIN_4; io.Mode = GPIO_MODE_OUTPUT_PP; io.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &io);
    FLASH_CS_HIGH();

    hspi1.Instance               = SPI1;
    hspi1.Init.Mode              = SPI_MODE_MASTER;
    hspi1.Init.Direction         = SPI_DIRECTION_2LINES;
    hspi1.Init.DataSize          = SPI_DATASIZE_8BIT;
    hspi1.Init.CLKPolarity       = SPI_POLARITY_LOW;   /* CPOL=0 */
    hspi1.Init.CLKPhase          = SPI_PHASE_1EDGE;    /* CPHA=0 → Mode 0 */
    hspi1.Init.NSS               = SPI_NSS_SOFT;
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_8;   /* 9MHz */
    hspi1.Init.FirstBit          = SPI_FIRSTBIT_MSB;
    HAL_SPI_Init(&hspi1);
}

/* 读 W25Q64 的 JEDEC ID：预期 0xEF4017 */
static uint32_t w25q_read_id(void)
{
    uint8_t tx[4] = {CMD_JEDEC_ID, 0xFF, 0xFF, 0xFF};
    uint8_t rx[4] = {0};

    FLASH_CS_LOW();
    HAL_SPI_TransmitReceive(&hspi1, tx, rx, 4, 100);
    FLASH_CS_HIGH();

    return ((uint32_t)rx[1] << 16) | ((uint32_t)rx[2] << 8) | rx[3];
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    spi_init();

    uint32_t id = w25q_read_id();   /* 预期 0xEF4017（Winbond 25Q64） */

    while (1) { (void)id; }
}
```

页写入（W25Q64 页大小 256 字节，写前必须写使能 + 等待忙）：

```c
static void w25q_write_enable(void)
{
    uint8_t cmd = CMD_WRITE_ENABLE;
    FLASH_CS_LOW();
    HAL_SPI_Transmit(&hspi1, &cmd, 1, 100);
    FLASH_CS_HIGH();
}

static void w25q_wait_busy(void)
{
    uint8_t cmd = CMD_READ_STATUS1, st = 0;
    do {
        FLASH_CS_LOW();
        HAL_SPI_Transmit(&hspi1, &cmd, 1, 100);
        HAL_SPI_Receive(&hspi1, &st, 1, 100);
        FLASH_CS_HIGH();
    } while (st & 0x01);   /* BUSY 位 */
}
```

DMA 刷屏思路：把整屏像素缓冲通过 `HAL_SPI_Transmit_DMA` 一次性发出，CPU 去准备下一帧，大幅提速。

完整工程见 [`examples/spi-flash/`](../examples/spi-flash/)。

## 动手实验

1. **实验一**：读 W25Q64 JEDEC ID，确认是 0xEF4017（对照 `spi-transfer.svg` 理解移位）。
2. **实验二**：向某页写 16 字节再读回，验证一致；故意不写使能观察失败。
3. **实验三**：ST7789 初始化并填充颜色，用 DMA 刷整屏，对比阻塞发送的帧率。

### 6. SPI 关键寄存器（F1）

| 寄存器 | 作用 |
| --- | --- |
| CR1 | 使能、主从、CPOL/CPHA、BR、NSS |
| CR2 | 中断/DMA 使能 |
| SR | 状态（TXE/RXNE/BSY） |
| DR | 数据 |

### 7. 软件模拟 SPI 核心片段

```c
/* 用 GPIO 模拟 SPI Mode 0（SCK=PA5, MOSI=PA7, MISO=PA6） */
static uint8_t spi_soft_xfer(uint8_t tx)
{
    uint8_t rx = 0;
    for (int i = 7; i >= 0; i--)
    {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_7, (tx >> i) & 1);  /* 准备数据 */
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);   /* 上升沿采样 */
        rx = (rx << 1) | HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_6);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
    }
    return rx;
}
```

### 8. ST7789 常用初始化命令

| 命令 | 值 | 作用 |
| --- | --- | --- |
| SWRESET | 0x01 | 软件复位 |
| SLPOUT | 0x11 | 退出睡眠 |
| COLMOD | 0x3A | 像素格式（0x55=16bit） |
| MADCTL | 0x36 | 扫描方向 |
| DISPON | 0x29 | 开显示 |

> 屏幕类器件通常「命令/数据」靠 DC 引脚区分，非 SPI 协议本身。

### 9. 全双工与只写器件

- 只写器件（如屏幕）可不接 MISO，用 `HAL_SPI_Transmit` 即可。
- 读器件（如 Flash）必须接 MISO，用 `HAL_SPI_TransmitReceive`。
- 全双工时发送的同时就在接收，收到的可能是上一次的残留数据。
- 只想读一个字节，也必须同时发出时钟。主机常发 dummy `0xFF`，从机才有机会把数据移出来。

### 10. SPI / I2C / UART 对比

| 维度 | SPI | I2C | UART |
| --- | --- | --- | --- |
| 线数 | 4 | 2 | 2（含 GND） |
| 速率 | 高 | 中 | 中 |
| 多设备 | 每设备一 CS | 地址寻址 | 点对点 |
| 全双工 | 是 | 半双工 | 是 |

## 相关资源

- 官方手册：**RM0008** 第 25 章（SPI）；W25Q64、ST7789 数据手册
- 上一篇：[07 I2C总线](07-I2C总线.md)
- 手机阅读版：[第 08 章 · SPI总线（公众号图文）](https://mp.weixin.qq.com/s/FOR_DIzh4qdzByi0qAI1Jg)
- 相关图：[`assets/animations/spi-transfer.svg`](../assets/animations/spi-transfer.svg)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。
