---
title: "Flash、IAP 与 OTA"
platforms: [f407, f103, esp32]
---

# Flash、IAP 与 OTA

> Flash 是这本书里唯一一块“断电还记得”的地方，也是唯一一块“写错就把自己脚下挖空”的地方。它只能把 1 写成 0，想把 0 变回 1 就得整页或整扇区擦掉；擦写之前要先解锁，写完还要等 BSY 落下。IAP 让固件在运行时给自己换程序，OTA 把这件事做成可回滚的双槽提交。本章把 F407 的扇区表、F103C8 的页表、两把钥匙、PSIZE 与电压的对应、IAP 跳转的向量表与 MSP、双槽切换的记录格式摆在一起；三个来源都没有留下上板读数，正文把手册规则、算术推导、来源说法与待做实验分开写。

## 本章罗盘

- **问题**：F407 的 1 MB 为什么要切成 12 个大小不等的扇区，扇区 11 从哪个地址开始，参数区为什么不能塞进代码扇区的空隙？F103C8 的 64 KB 为什么是 1 KB 一页、共 64 页，末页地址怎么算，换成大容量型号后 2 KB 一页会改掉哪几个数？两把钥匙 `0x45670123` 与 `0xCDEF89AB` 为什么必须按顺序写，写反了为什么只能等复位？F4 的 PSIZE 为什么不能超过供电电压允许的最高档、又必须和写入宽度配对，F407 上为什么不能选 x64，F103 又为什么只认半字？擦写寿命的 1 万次与 20 年是谁的承诺，参数区怎样做才能在擦到一半断电时仍然读得回旧值？IAP 跳转前为什么要关中断、设 MSP、改 VTOR，跳复位入口而不是 `main` 的理由是什么，App 一侧为什么还要再写一次 VTOR？单槽升级为什么没有回头路，双槽的 A/B 记录、CRC 校验、原子切换与回滚各自管哪一段？ESP32 的分区表、NVS 与 OTA 状态机在来源里是怎么写的，哪些只是来源说法？三个来源里哪些数字是手册规则、哪些是本章的算术、哪些还没有人上板量过？
- **交付**：能按 1 MB 总和复算 F407 的 12 个扇区，按 64 页复算 F103C8 的页边界；能说出两把钥匙的顺序、F4 的 PSIZE 三档与电压、F1 的半字粒度；能写出 F4 的解锁→扇区擦除→字写入→等 BSY→清 EOP→上锁序列，也能写出 F1 的解锁→页擦除→半字写入序列；能设计一个带魔数、版本、CRC 与默认回退的参数快照，并说清 A/B 两份为什么必须落在不同的擦除单位；能写出 IAP 跳转函数，按向量表第 0 字设 MSP、第 1 字跳复位入口，把 VTOR 指向 App 基址，并解释 PRIMASK 由谁打开；能按 F407 的 480 KB 槽与 F103C8 的 22 KB 槽各画一张双槽表，写出“先写备槽、校验、追加记录、下次启动确认”的切换顺序；能按现象把 LOCK、PSIZE、对齐、WRP、VTOR、MSP、PRIMASK、看门狗与半擦状态分到不同的检查动作；能读懂 ESP32 的分区表字段、NVS 追加写与 OTA 状态表，并指出它们只是 P10 的来源事实。
- **边界**：两平台 STM32 章加 ESP32 对照。F407 的扇区表、PSIZE、CR/SR 位号、参数区与 IAP 双固件布局来自 S13《S13 内部 Flash 与 IAP》；F103C8 的 1 KB 页、64 页、16 KB Bootloader + 2 KB 参数区 + 46 KB APP 布局、半字编程、两把钥匙与 RDP `0xA5` 来自根书第 12 章；ESP32 的分区表、NVS、OTA 五步与回滚状态机只转写 P10《P10 Flash、分区表、NVS 与 OTA》，不往 STM32 上外推。三个来源都没有本章的上板读数：S13 没有独立工程，根书第 12 章的动手实验是待做清单，P10 的 boot_count 1→5 与回滚日志是 P10 的实物实验自述（声称日志存档，本仓库未见原始日志文件）。S13 正文写“11 个扇区”，同节表格却列出扇区 0–11 共 12 行，本章按 1 MB 总和复算后采用 12 个；根书表把 F4 的编程粒度写成“字节/半字/字/双字”，双字 x64 只在 F42x/F43x 上成立，F407 只有 x8/x16/x32；S13 说擦 128 KB 扇区“最坏几百毫秒”，根书表写 0.4–4 s，两处都未核数据手册原表；F1 的 CR/SR 位号两个来源都没有逐位列出，本章按 RM0008 语义标注为待复核；STM32 的双槽布局与记录格式是本章按扇区/页尺寸做的设计，不是来源里现成的实现；ESP32 的小节只写来源事实，没有核 IDF 原文。GD32 不在本章平台列表，只在跨平台边界里指一句。F407 的 512 KB 型号只用到扇区 7，扇区 8–11 是 1 MB 型号的版图，换芯片先查数据手册。
- **依据锚点**：S13（`mcu/docs/stm32/13-flash-iap.md`）、根书第 12 章（`docs/12-Flash与IAP升级.md`）、P10（`mcu/docs/esp32/10-flash-nvs-ota.md`）；[第 6 章](../v0-foundations/06-linker-startup-map.md)的链接脚本与启动、[第 8 章](./08-architecture-memory-clock.md)的存储器地图与时钟、[第 16 章](./16-i2c-spi.md)的 W25Q 外部 Flash、[第 19 章][ch19]的看门狗与复位、[第 18 章][ch18]的低功耗。RM0008 第 3 章、RM0090 第 3 章、DS5319、PM0056 与 ESP-IDF 文档均转引自上述来源；本章没有取到这些手册与文档的原件，逐处标注“来源说法”或“待复核”。

## 先做出来

不接板子也能完成最小胜利：把两个平台的擦除边界和参数区各算一行。

```text
F407：4 × 16 KB + 1 × 64 KB + 7 × 128 KB = 64 + 64 + 896 = 1024 KB = 1 MB
      扇区 11 起始 = 0x080E0000，长度 128 KB，结束于 0x08100000
F103C8：64 KB ÷ 1 KB = 64 页，页号 0–63
      页 63 起始 = 0x08000000 + 63 × 0x400 = 0x0800FC00
      页 63 结束 = 0x08010000
```

| 平台 | 擦除单位 | Bootloader | 参数或元数据 | App 起点 | 备注 |
| --- | --- | --- | --- | --- | --- |
| F407VG（1 MB） | 扇区 16/64/128 KB | 扇区 0，`0x08000000`，16 KB | 单槽放扇区 11，`0x080E0000`，128 KB | `0x08004000`（单槽） | 双槽布局见机制第六节 |
| F103C8（64 KB） | 页 1 KB | 16 KB，`0x08000000`–`0x08004000` | 2 KB，`0x08004000`–`0x08004800` | `0x08004800` | 本书布局，RM 没有规定这样分 |

押一题再往下读：F407 的 App 如果长到把扇区 11 也用掉了，参数区还能放哪？答案不在“代码扇区的空隙”里——擦参数会连带擦代码。可选的路只有三条：把 App 压回扇区 11 之前、换更大 Flash 的型号、把参数挪到外部 Flash（W25Q 的 SPI 读写在[第 16 章](./16-i2c-spi.md)）。本章第六节的双槽布局会把元数据放到扇区 1，正是为了不让参数和代码共用擦除单位。

有板的人先做 F407 的最小闭环：确认 App 不占扇区 11，擦 `0x080E0000`，写入 `0xA5A50001`，断电重启后读回，串口打印 `read=0xA5A50001 PASS`。这一步的预期现象是按手册规则推的，不是本章量到的读数；记录表在“测量与证据”里留空。

## 机制

### 一、擦除单位：F4 的扇区与 F1 的页

F407VG 的 1 MB 主 Flash 从 `0x08000000` 起，按扇区擦除，扇区大小并不相等。S13 的表把它列全，本章按总和复算一遍：

| 扇区 | 起始 | 大小 | 结束 | 单槽用途建议 |
| --- | --- | --- | --- | --- |
| 0 | `0x08000000` | 16 KB | `0x08004000` | Bootloader |
| 1 | `0x08004000` | 16 KB | `0x08008000` | 单槽 App 起点；双槽时做元数据 |
| 2 | `0x08008000` | 16 KB | `0x0800C000` | App |
| 3 | `0x0800C000` | 16 KB | `0x08010000` | App |
| 4 | `0x08010000` | 64 KB | `0x08020000` | App |
| 5 | `0x08020000` | 128 KB | `0x08040000` | App |
| 6 | `0x08040000` | 128 KB | `0x08060000` | App |
| 7 | `0x08060000` | 128 KB | `0x08080000` | App |
| 8 | `0x08080000` | 128 KB | `0x080A0000` | App |
| 9 | `0x080A0000` | 128 KB | `0x080C0000` | App |
| 10 | `0x080C0000` | 128 KB | `0x080E0000` | App |
| 11 | `0x080E0000` | 128 KB | `0x08100000` | 单槽参数区首选 |

S13 正文写“11 个扇区”，表里却是 0–11 共 12 行。把大小相加：4×16 + 64 + 7×128 = 1024 KB，正好 1 MB，12 个才对。这个计数笔误不影响地址，但提醒一件事：读来源要先对表，再信正文里的数。

![Flash 扇区与 IAP：Bootloader 在 0x08000000，App 从 0x08004000 起，参数区独占一扇；擦除按扇区，写入按字](/figures/stm32-13-flash-iap.svg)

F103C8 是 64 KB、中容量、1 KB 一页、64 页，页 0 从 `0x08000000` 起，页 63 从 `0x0800FC00` 起，到 `0x08010000` 结束。高密度型号是 2 KB 一页，页号与地址的乘法要换成 `n × 0x800`；把中容量的 1 KB 表直接套过去，擦除地址会落到页中间，硬件按页边界对齐的要求不满足，轻则报错，重则擦错页。

参数区的选址只有两条硬规则：

1. **参数区与代码区不共用擦除单位**。F4 擦一个扇区就是整块 16/64/128 KB，F1 擦一页就是整块 1/2 KB；参数和代码落在同一个擦除单位里，擦参数等于擦代码。F407 单槽选扇区 11，是因为它最大、最靠后，App 不用满 1 MB 时天然隔离。
2. **参数区要能被 Bootloader 和 App 同时读到**。放在主 Flash 的任何位置都满足；放在外部 Flash 也能读，但要在 Bootloader 里先初始化 SPI，启动链多一层依赖。

### 二、解锁：两把钥匙、PSIZE 与电压

Flash 上锁时，CR 里的 PG、SER、PER、STRT 等位会被硬件忽略，防的是程序跑飞时乱写。解锁是把两个固定常数按顺序写进 `FLASH_KEYR`：

```text
KEY1 = 0x45670123
KEY2 = 0xCDEF89AB
先 KEY1，后 KEY2；顺序或数值不对，Flash 保持锁定到下次复位
```

两把钥匙不是 CMSIS 宏，是 RM0008 与 RM0090 里的手册常数。F1 与 F4 的钥匙相同，寄存器名都叫 `FLASH_KEYR`；写完第二把钥匙，CR 的 LOCK 位清零。上锁则反过来：向 CR 的 LOCK 位写 1。F4 的 LOCK 在 CR bit31，F1 在 CR bit7。

```c
/* F407：解锁与上锁；F103 的 KEYR 序列相同，LOCK 位换成 CR bit7 */
static void flash_unlock(void)
{
    if (FLASH->CR & FLASH_CR_LOCK) {          /* 已解锁就不要重复写钥匙 */
        FLASH->KEYR = 0x45670123u;            /* KEY1 */
        FLASH->KEYR = 0xCDEF89ABu;            /* KEY2 */
    }
}

static void flash_lock(void)
{
    FLASH->CR |= FLASH_CR_LOCK;               /* 写 1 重新上锁 */
}
```

解锁只打开 Flash 控制器，不解写保护（WRP）和读保护（RDP）。WRP 开着的扇区或页，解锁后照样擦不动、写不进，SR 会置 WRPERR；RDP 管的是调试器能不能读，和擦写使能是两套闸。

F4 擦写前还要设并行度 PSIZE（CR bits8–9）。它有两层约束：不能超过当前供电允许的最高档，而且必须与每次写访问的宽度一致。下表列的是每个电压区间允许的最高并行度；低一档在高电压下仍然可用（3.3 V 选 x16 是合法的），高一档不能用在低电压：

| 供电 VDD | 最高 PSIZE | 该档写宽度 | 说明 |
| --- | --- | --- | --- |
| 2.7–3.6 V | `10`（x32） | 32 位 | 3.3 V 板子的常用档；x8/x16 也可用 |
| 2.1–2.7 V | `01`（x16） | 16 位 | 2.7 V 以上同样可用 |
| 1.8–2.1 V | `00`（x8） | 8 位 | 最低压档 |
| — | `11`（x64） | 64 位 | 仅 F42x/F43x；F407 不选 |

PSIZE 必须在置 STRT 或 PG 之前设好，并且要和写入宽度配对：PSIZE 设 x16 却按 32 位字写，控制器会置 PGPERR（并行度错误）或 PGSERR（编程序列错误），这一次编程不生效；3.3 V 系统选 x16 并按 16 位写则是合法的，只是并行度低、速度慢。真正会“不报错却写坏数据”的是反方向：PSIZE 选得比供电允许的最高档还高（例如 2.5 V 系统选 x32）。根书表把 F4 的编程粒度笼统写成“字节/半字/字/双字”，双字那一档只属于 F42x/F43x；F407 的可用档就是上表前三行。

F103 没有 PSIZE 这一档可选，中容量与高容量型号的编程粒度都是半字（16 位），地址要 2 字节对齐；一个 32 位值分两次半字写。F1 的擦除粒度是页，F4 是扇区，这是两家 Flash 控制器最根本的差别。

### 三、擦除与写入：序列、BSY 与 EOP

F4 的扇区擦除序列是：解锁 → 设 PSIZE → 清 SNB 再写扇区号 → 置 SER → 置 STRT → 等 BSY → 清 EOP → 清 SER → 上锁。S13 的例程以擦扇区 11 为例，下面把错误检查补上：

```c
/* F407：擦一个扇区。snb = 0..11；PSIZE = x32，对应 2.7–3.6 V */
static int flash_erase_sector(uint8_t snb)
{
    flash_unlock();
    FLASH->CR &= ~FLASH_CR_PSIZE_Msk;
    FLASH->CR |= (0x2u << FLASH_CR_PSIZE_Pos);      /* x32 */
    FLASH->CR &= ~FLASH_CR_SNB_Msk;                  /* SNB = CR bits3–6 */
    FLASH->CR |= ((uint32_t)snb << FLASH_CR_SNB_Pos);
    FLASH->CR |= FLASH_CR_SER;                       /* SER = CR bit1 */
    FLASH->CR |= FLASH_CR_STRT;                      /* STRT = CR bit16，硬件自清 */
    while (FLASH->SR & FLASH_SR_BSY) { }             /* BSY = SR bit16 */
    if (FLASH->SR & (FLASH_SR_WRPERR | FLASH_SR_OPERR |
                     FLASH_SR_PGAERR | FLASH_SR_PGPERR | FLASH_SR_PGSERR)) {
        FLASH->SR = FLASH_SR_WRPERR | FLASH_SR_OPERR |
                    FLASH_SR_PGAERR | FLASH_SR_PGPERR |
                    FLASH_SR_PGSERR;                 /* 写 1 清，重试前不能留旧错误 */
        FLASH->CR &= ~FLASH_CR_SER;
        flash_lock();
        return -1;                                   /* 写保护、操作或对齐错误 */
    }
    FLASH->SR = FLASH_SR_EOP;                        /* EOP = SR bit0，写 1 清 */
    FLASH->CR &= ~FLASH_CR_SER;
    flash_lock();
    return 0;
}
```

F4 的字写入是：解锁 → 设 PSIZE 与 PG → 直接往目标 Flash 地址写 32 位 → 等 BSY → 清 EOP → 清 PG → 上锁。先擦后写这条规则对两家都成立：F1 往未擦除的半字再写会置 PGERR（SR bit2）；F4 的 PGAERR 则是编程对齐错误（地址没有按 PSIZE 的宽度对齐），不是“未擦除”错误，往未擦除单元再写在 F4 上会走 OPERR/PGSERR 一侧的报错路径还是只表现为读回不等于目标值，来源没有逐条写明，这句标待复核。可靠的做法仍是先把目标擦成 `0xFFFFFFFF`，写完读回比对。

```c
/* F407：写一个 32 位字。addr 必须 4 字节对齐，且该字已擦除 */
static int flash_write_word(uint32_t addr, uint32_t data)
{
    flash_unlock();
    FLASH->CR &= ~FLASH_CR_PSIZE_Msk;
    FLASH->CR |= (0x2u << FLASH_CR_PSIZE_Pos) | FLASH_CR_PG;  /* PG = CR bit0 */
    *(volatile uint32_t *)addr = data;               /* 写地址即触发编程 */
    while (FLASH->SR & FLASH_SR_BSY) { }
    if (FLASH->SR & (FLASH_SR_WRPERR | FLASH_SR_OPERR |
                     FLASH_SR_PGAERR | FLASH_SR_PGPERR | FLASH_SR_PGSERR)) {
        FLASH->SR = FLASH_SR_WRPERR | FLASH_SR_OPERR |
                    FLASH_SR_PGAERR | FLASH_SR_PGPERR |
                    FLASH_SR_PGSERR;                 /* 写 1 清，失败后不留错误位 */
        FLASH->CR &= ~FLASH_CR_PG;
        flash_lock();
        return -1;
    }
    FLASH->SR = FLASH_SR_EOP;
    FLASH->CR &= ~FLASH_CR_PG;
    flash_lock();
    return 0;
}
```

F103 的页擦除与半字写入是另一套寄存器序：擦除要把页地址写进 `FLASH_AR`，置 PER 与 STRT，等 BSY；写入要置 PG，往目标地址写半字，等 BSY。F1 没有 SNB，也没有 PSIZE，SR 的位号与 F4 不同。

```c
/* F103：擦一页；page_addr 必须是 1 KB（中容量）或 2 KB（高容量）页边界 */
static int f1_flash_erase_page(uint32_t page_addr)
{
    flash_unlock();
    FLASH->CR |= FLASH_CR_PER;                       /* PER = CR bit1 */
    FLASH->AR = page_addr;                           /* 页地址进 AR */
    FLASH->CR |= FLASH_CR_STRT;                      /* STRT = CR bit6 */
    while (FLASH->SR & FLASH_SR_BSY) { }             /* BSY = SR bit0 */
    if (FLASH->SR & (FLASH_SR_PGERR | FLASH_SR_WRPRTERR)) {
        FLASH->SR = FLASH_SR_PGERR | FLASH_SR_WRPRTERR;  /* 写 1 清 */
        FLASH->CR &= ~FLASH_CR_PER;
        flash_lock();
        return -1;
    }
    FLASH->SR = FLASH_SR_EOP;                        /* EOP = SR bit5，写 1 清 */
    FLASH->CR &= ~FLASH_CR_PER;
    flash_lock();
    return 0;
}

/* F103：写一个半字；addr 必须 2 字节对齐，且该半字已擦除 */
static int f1_flash_write_halfword(uint32_t addr, uint16_t data)
{
    flash_unlock();
    FLASH->CR |= FLASH_CR_PG;                        /* PG = CR bit0 */
    *(volatile uint16_t *)addr = data;
    while (FLASH->SR & FLASH_SR_BSY) { }
    if (FLASH->SR & (FLASH_SR_PGERR | FLASH_SR_WRPRTERR)) {
        FLASH->SR = FLASH_SR_PGERR | FLASH_SR_WRPRTERR;  /* 写 1 清 */
        FLASH->CR &= ~FLASH_CR_PG;
        flash_lock();
        return -1;
    }
    FLASH->SR = FLASH_SR_EOP;
    FLASH->CR &= ~FLASH_CR_PG;
    flash_lock();
    return 0;
}
```

两家的位号放在一张表里，换平台时逐位对，不要只改头文件名：

| 位 | F4 CR | F1 CR | F4 SR | F1 SR |
| --- | --- | --- | --- | --- |
| 0 | PG | PG | EOP | BSY |
| 1 | SER | PER | OPERR | — |
| 2 | MER | MER | — | PGERR |
| 3–6 | SNB[3:0] | — | — | — |
| 4 | — | — | WRPERR | WRPRTERR |
| 5 | — | — | PGAERR | EOP |
| 6 | — | STRT | PGPERR | — |
| 7 | — | LOCK | PGSERR | — |
| 8–9 | PSIZE[1:0] | — | — | — |
| 16 | STRT | — | BSY | — |
| 31 | LOCK | — | — | — |

F4 的 PG/SER/MER/SNB/PSIZE/STRT/LOCK 与 SR 的 EOP/BSY/WRPERR 由 S13 列出，本章与它的代码注释对过；OPERR/PGAERR/PGPERR/PGSERR 的位号按 RM0090 第 3 章的寄存器语义补，标为待复核。F1 的位号两个来源都没有逐位写，本章按 RM0008 第 3 章的寄存器语义填，同样标为待复核。F1 的 EOP 在 bit5、BSY 在 bit0，和 F4 的 EOP=0、BSY=16 正好错开，这是从 F4 迁到 F1 时最容易抄错的一处。

![Flash 擦除与编程序列：解锁 → SER/SNB → STRT → 等 BSY；编程 PG=1 写 32 位字再等 BSY](/figures/stm32-13-flash-seq.svg)

三条等待纪律：

1. **擦写期间不要从 Flash 取指**。F4 在擦写时对主 Flash 的取指会被总线阻塞；如果中断处理函数也在 Flash 里，擦一个 128 KB 扇区的毫秒到秒级时间里，CPU 和中断都可能在等同一块 Flash。把关键路径放进 RAM 执行是稳妥做法：函数加 `__attribute__((section(".ramfunc")))`，链接脚本给 `.ramfunc` 分配 RAM 的 VMA 和 Flash 的 LMA，启动代码负责搬运。
2. **BSY 必须等到底**。F4 擦扇区、F1 擦页都是毫秒到秒级，轮询期间要给看门狗喂狗；把超时写成固定循环次数时，先按最坏擦除时间算够。
3. **EOP 写 1 清，错误位逐个查**。F4 的 EOP 在 SR bit0，F1 在 bit5；写完只清 EOP 不看 WRPERR/OPERR/PGAERR 等错误位，失败会被当成成功，下一行代码继续往坏数据上跑。失败返回前要把错误位写 1 清掉，否则下一次调用拿旧错误误判。

```c
/* 擦写关键路径放 RAM：函数属性 + 链接脚本 + 启动搬运 */
__attribute__((section(".ramfunc"))) static int flash_erase_sector(uint8_t snb);
```

```text
.ramfunc : { *(.ramfunc) } >RAM AT>FLASH
```

### 四、寿命与参数区：魔数、CRC 与 A/B

根书表给的两组寿命数是“擦写 ≥ 1 万次、数据保持 20 年 @ 85 °C”，并说出处是数据手册；S13 没有重复这两组数。本章把它们当来源说法，不当成本章实测：具体型号的保证值要看对应的 DS 表，温度、擦写次数与保持时间三者要一起看，不能把“1 万次”当成无限写入的许可。

参数区不是把结构体往 Flash 一拷就完事。擦除单位大于结构体，改一个字段也要整页/整扇区重写；擦到一半断电，读回来可能是半新半旧。最小的防呆是三层：魔数、CRC、默认回退。

```c
#include <stddef.h>
#include <stdint.h>

#define PARAM_MAGIC 0x50415241u   /* 'PARA' */

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t seq;                 /* A/B 两份时用于选新 */
    uint32_t baud;
    uint32_t sample_rate;
    uint32_t crc;                 /* 覆盖 crc 之前的字节 */
} params_t;

static uint32_t crc32_simple(const uint8_t *p, uint32_t n)
{
    uint32_t c = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < n; i++) {
        c ^= p[i];
        for (int b = 0; b < 8; b++) {
            c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
        }
    }
    return ~c;
}
```

读取时先看魔数，再算 CRC，再比版本；任何一步不对就回退默认值，不把半擦数据当合法快照。`0xFFFFFFFF` 是擦除态，不等于合法魔数；这正是魔数存在的理由。

A/B 双备份的关键不是“写两份”，而是“两份落在不同的擦除单位”：

- F103C8 的 2 KB 参数区正好两页：A 放页 16，B 放页 17。擦 A 时 B 完好，擦 B 时 A 完好。
- F407 单槽只有一个扇区 11 时，A/B 两份都在同一个 128 KB 扇区里，擦除时一起没；要做真正的 A/B，得再拿一个扇区（例如扇区 1 与扇区 11，或扇区 1 与扇区 2），代价是 App 可用空间减少。
- 写入顺序是“擦备份 → 写备份 → 校验备份 → 更新序号/提交”；读取时选序号最大且 CRC 通过的那份。擦到一半断电，备份坏了，主份还在；提交前断电，新份没生效，旧份仍然是最后有效值。

参数区还要考虑寿命：同一个扇区反复擦写，寿命按那个扇区单点消耗。更新频率高的参数先放 RAM、定期落盘，或者用外部 FRAM/EEPROM；W25Q 的页编程与扇区擦除在[第 16 章](./16-i2c-spi.md)有另一套规则。

### 五、IAP：双固件、跳转与 VTOR

IAP 的双固件布局是：Bootloader 从 `0x08000000` 起，占扇区 0（F407，16 KB）或前 16 页（F103C8，16 KB）；App 从 `0x08004000`（F407 单槽）或 `0x08004800`（F103C8）起。两块各有自己的向量表，表的第一字是初始 MSP，第二字是复位入口 `Reset_Handler`。跳转不是函数调用：App 有自己的栈、自己的中断表、自己的 `.data/.bss` 初始化与时钟配置，跳过去等于让 App 走一次软上电。

![IAP 跳转接力：关中断、复位 SysTick、设 VTOR 与 MSP、跳 App 复位入口](/anim/iap-handoff.svg)

跳转前先把 App 镜像验一遍，别把任意一包噪声当程序：

```c
#define SRAM_START 0x20000000u
#define SRAM_END   0x20020000u   /* F407 主 SRAM 128 KB；F103C8 改成 0x20005000 */

/* 只查向量表两个字：MSP 是否落在主 SRAM，复位入口是否落在槽内且 Thumb 位为 1 */
static int app_vector_ok(uint32_t base, uint32_t slot_end)
{
    uint32_t msp = *(volatile uint32_t *)base;
    uint32_t rst = *(volatile uint32_t *)(base + 4u);

    if (msp < SRAM_START || msp > SRAM_END) return 0;
    if ((rst & ~1u) < base || (rst & ~1u) >= slot_end) return 0;
    if ((rst & 1u) == 0) return 0;
    return 1;
}
```

长度与 CRC 的校验在 Bootloader 收完固件时做，向量表检查放在跳转前；两道都过才允许换槽。根书第 12 章的验收门写的是“范围、CRC、向量、跳转、心跳”五道，本章把范围与 CRC 归到写槽阶段，向量与 MSP 归到跳转前，心跳归到 App 启动后。

跳转函数本身只有五步：

```c
typedef void (*reset_handler_t)(void);
#define APP_ADDR 0x08004000u   /* F407 单槽；F103C8 用 0x08004800 */

static void jump_to_app(void)
{
    __disable_irq();                            /* PRIMASK = 1，焊住切换窗口 */

    /* 清 NVIC 使能与挂起：F407 用 ICER[0..2]/ICPR[0..2]，F103 用 [0..1]。
       多写的那个寄存器在 F103 上是保留位，写入被忽略，所以这里统一循环 3 次 */
    for (uint32_t i = 0; i < 3U; i++) {
        NVIC->ICER[i] = 0xFFFFFFFFu;
        NVIC->ICPR[i] = 0xFFFFFFFFu;
    }
    SysTick->CTRL = 0;
    SysTick->LOAD = 0;
    SysTick->VAL  = 0;
    SCB->ICSR = SCB_ICSR_PENDSTCLR_Msk;

    SCB->VTOR = APP_ADDR;                       /* 向量表归位 App */
    __DSB();                                    /* 等 VTOR 写入生效 */
    __ISB();
    __set_MSP(*(volatile uint32_t *)APP_ADDR);  /* 第 0 字 = App 栈顶 */
    __DSB();                                    /* 等 MSP 切换完成再取指 */
    __ISB();

    reset_handler_t handler =
        (reset_handler_t)(*(volatile uint32_t *)(APP_ADDR + 4u));
    handler();                                  /* 第 1 字 = 复位入口 */

    for (;;) { }                                /* 跳过去就回不来 */
}
```

五步里最容易被省略的是最后一步的“回不来”和第一段的“关中断”：

- **关中断优先**：VTOR 切换前后，任何可屏蔽中断都会按当时的 VTOR 取入口；如果向量表正在换、栈还没换，取到的入口和栈可能分属两套固件。PRIMASK 置 1 把这段窗口焊死。
- **VTOR 与 MSP 都要在跳转前就位**：`__set_MSP(*(uint32_t *)APP_ADDR)` 是从 App 基址显式读第 0 字，不经过 VTOR；动画里“VTOR 必须在 MSP 之前，否则 MSP 从旧表读”的说法比实际机制更强。真正不能省的是：跳转前两者都已设好，且中断全程关着。本章仍按 VTOR→MSP 写，与动画顺序一致，也让此后任何隐式取向量都走 App 的表。
- **跳复位入口，不跳 `main`**：App 的 `Reset_Handler` 先做 `.data` 拷贝、`.bss` 清零、`SystemInit` 时钟配置，再进 `main`；直接跳 `main` 会跳过这些初始化，全局变量和时钟都停在 Bootloader 的状态。[第 6 章](../v0-foundations/06-linker-startup-map.md)把这段启动序列拆过一遍。
- **PRIMASK 由谁打开**：S13 的跳转函数把中断关掉后不再打开；根书第 12 章在清空 NVIC 后先 `__enable_irq()` 再跳。两种做法都能工作，但不能两边都不做：如果 Bootloader 不开、App 的启动代码也不开，App 能跑，所有可屏蔽中断却永远不会来。本章的选择是 App 在启动早期自己 `__enable_irq()`，Bootloader 保持关中断到跳转；这样中断第一次进来时，App 的 `.data/.bss` 与时钟已经就位。根书那种“跳转前最后一条开中断”的写法，前提是 NVIC 的使能与挂起都已清空，且外设不再产生新请求。
- **外设复位是设计选择**：根书在跳转前调 `HAL_RCC_DeInit()` 与 `HAL_DeInit()`，把 Bootloader 用过的外设恢复默认；S13 则把“复不复位”留给 App 决定。两种都可以，关键是 App 不能假设外设处于复位值——串口、定时器、DMA 都要重新初始化。

App 一侧要做的两件事：

1. **链接脚本的起始地址与 Bootloader 约定一致**。F407 单槽 App 的 `ORIGIN = 0x08004000`，F103C8 是 `0x08004800`；链接到 `0x08000000` 的 App 即使被写进槽里，代码里的绝对地址也全错。
2. **VTOR 指向自己**。Bootloader 跳转前已经设过一次，但 App 的 `SystemInit()` 可能把它写回 Flash 基址：STM32F4/F1 HAL 的 `SystemInit()` 默认执行 `SCB->VTOR = FLASH_BASE | VECT_TAB_OFFSET`，`VECT_TAB_OFFSET` 默认为 0，等于把 VTOR 改回 `0x08000000`。App 要么把 `VECT_TAB_OFFSET` 改成槽偏移，要么在 `main` 开头再写一次 `SCB->VTOR = APP_ADDR`。只在 Bootloader 里设一次，是 IAP 最常见的坑。

Cortex-M3/M4 的 VTOR 在 `SCB` 里，F1 的编程手册是 PM0056，F4 是 PM0214；根书只引了 PM0056，本章没有取 PM0214 原件。VTOR 的低位有对齐要求，`0x08004000` 与 `0x08004800` 都满足；换到更小的槽时，链接脚本的起始地址要按芯片要求对齐。

### 六、OTA 双槽与回滚：把换程序做成一次可撤销的提交

单槽 IAP 的流程是“Bootloader 收固件 → 擦 App 区 → 写 App 区 → 跳 App”。它在擦掉旧 App 的那一刻就没有回头路了：传输失败、CRC 不过、写到一半断电，旧程序已经不在，设备只能留在 Bootloader 等重传。根书第 12 章把这条写得很直白：单槽没有旧镜像可回退，回滚需要完好的备份和可恢复的切换记录。

双槽把“运行中的槽”和“接收新固件的槽”分开：新固件永远写另一个槽，写坏了大不了重来，当前槽不动；只有新槽通过校验并完成一次“提交记录”后，下次启动才换过去。下面两套布局是按扇区/页尺寸算的，不是来源里现成的工程；根书只把“A/B 回滚、旧槽仍能启动”列为动手实验的第 3 项。

F407VG 的 1 MB 双槽布局：

| 区域 | 扇区 | 地址 | 大小 | 说明 |
| --- | --- | --- | --- | --- |
| Bootloader | 0 | `0x08000000` | 16 KB | 不参与升级 |
| 元数据 | 1 | `0x08004000` | 16 KB | 追加记录，见下 |
| Slot A | 2–7 | `0x08008000` | 480 KB（`0x78000`） | 16+16+64+128+128+128 |
| Slot B | 8–11 | `0x08080000` | 512 KB，实用 480 KB | 末尾 32 KB 留空 |
| 合计 | 0–11 | `0x08000000`–`0x08100000` | 1024 KB | 两槽等大 480 KB |

Slot B 的 512 KB 里只划 480 KB 给镜像，最后 32 KB 不用；两个槽的可用大小必须相等，否则“新固件只装得进大槽”的隐患从第一天就埋下。

F103C8 的 64 KB 双槽布局：

| 区域 | 页 | 地址 | 大小 | 说明 |
| --- | --- | --- | --- | --- |
| Bootloader | 0–15 | `0x08000000` | 16 KB | 不参与升级 |
| 元数据 | 16–17 | `0x08004000` | 2 KB | 两页追加记录 |
| Slot A | 18–39 | `0x08004800` | 22 KB（`0x5800`） | 22 页 |
| Slot B | 40–61 | `0x0800A000` | 22 KB（`0x5800`） | 22 页 |
| 备用 | 62–63 | `0x0800F800` | 2 KB | 可做元数据整理或第二参数区 |
| 合计 | 0–63 | `0x08000000`–`0x08010000` | 64 KB | 两槽等大 22 KB |

单槽时 App 有 46 KB（`0x08004800`–`0x08010000`）；双槽把 46 KB 切成 22+22+2，代价是每个槽只剩 22 KB。这是双槽的真实成本：换来的是任意一次升级失败都能回旧槽。

切换的记录格式可以小到一条结构体：

```c
#define OTA_MAGIC 0x4F544152u   /* 'OTAR' */

typedef struct {
    uint32_t magic;
    uint32_t seq;        /* 单调递增，选最大且校验通过的一条 */
    uint32_t active;     /* 0 = Slot A，1 = Slot B */
    uint32_t state;      /* 0 = 待确认，1 = 有效，2 = 无效 */
    uint32_t length;     /* 镜像字节数，必须 <= 槽大小 */
    uint32_t crc;        /* 镜像 CRC32 */
    uint32_t version;    /* 版本号，便于心跳与防降级 */
    uint32_t meta_crc;   /* 覆盖 meta_crc 之前的字节 */
} ota_record_t;
```

元数据区按追加日志写：每条记录写在下一个空位，`meta_crc` 最后写；启动时从头扫一遍，选 `seq` 最大且 `meta_crc` 通过的那条。写新记录不需要擦旧记录，所以“换槽”这个动作只依赖一条记录的完整性；记录写到一半断电，`meta_crc` 不过，上一条记录仍然有效。元数据页写满后再整理：把最新有效记录搬到新页，擦旧页，序号继续递增。如果改成两份独立快照而不是追加日志，两份必须落在不同的扇区/页，理由和参数区的 A/B 一样。

一次完整的双槽升级：

1. **写备槽**。当前 `active` 指向 A，就把新镜像写进 B；只擦 B 的扇区/页，A 不动。
2. **校验**。长度不超过槽大小、CRC32 对得上、向量表第 0 字在主 SRAM、第 1 字在 B 槽内且 Thumb 位为 1；任何一项不过，删掉 B 的记录，A 继续运行。
3. **提交**。追加一条记录：`active = B`、`state = 待确认`、`seq = 上一条 + 1`。这条记录写完并通过 `meta_crc`，才算换槽成功；此前断电，启动时仍选 A。
4. **首次启动**。Bootloader 读到 B 是“待确认”，跳 B；B 在 `main` 里做自检（点灯、串口、外设应答、联网，任选），通过就追加 `state = 有效` 的记录，失败就追加 `state = 无效` 并复位。
5. **回退**。如果 B 在“待确认”状态下一次启动前没有转成“有效”（崩溃、看门狗、断电），Bootloader 把 B 标成无效，追加一条 `active = A` 的记录，回旧槽。回退永远发生在下一次启动，不在运行中；这一点和 ESP32 的 PENDING_VERIFY→ABORTED 是同一个思路，只是记录格式由本章设计。

这套设计的关键不是“有两个槽”，而是“换槽是一次带 CRC 的小记录提交”：镜像写入是长事务，记录提交是短事务；长事务失败不影响旧槽，短事务失败有上一条记录兜底。根书第 12 章的实验 3 要求“中断一次传输，确认旧槽仍能启动”，验的就是长事务失败时旧槽不动；本章再补上短事务的记录格式与回滚路径。

### 七、ESP32 对照：分区表、NVS 与 OTA

这一节只写 P10 的来源事实，不往 STM32 上外推，也没有核 ESP-IDF 原文。P10 的板卡是 16 MB Flash 的 ESP32-S3 模组，实际分区以 `idf.py partition-table` 读出的为准。

ESP32 的 Flash 版图不写在链接脚本里，而写在一张 CSV 分区表里。分区表本身放在 `0x8000`，长度 `0xC00`，最多 95 条，结尾跟一个 MD5 校验，正好占满一个 `0x1000` 扇区；所以 CSV 的第一个分区必须从 `0x9000` 或更靠后起步。P10 给的教学示例表：

```csv
# Name,   Type, SubType,  Offset,  Size,     Flags
nvs,      data, nvs,      0x9000,  0x5000,
otadata,  data, ota,      0xE000,  0x2000,
phy_init, data, phy,      0x10000, 0x1000,
ota_0,    app,  ota_0,    0x20000, 0x300000,
ota_1,    app,  ota_1,    0x320000,0x300000,
spiffs,   data, spiffs,   0x620000,0x9E0000,
```

16 MB 是 `0x1000000`；两个 3 MB 的 ota 槽加约 9.8 MB 文件系统，首尾相接正好铺满。P10 的立创实战派默认布局多为 factory + 大存储区，往往没有 ota 槽；要玩 OTA，第一件事就是换一张双槽表。

![ESP32 分区表、NVS 与 OTA 双槽：otadata 记账，Slot A 当前运行，新固件写入 Slot B，自检失败回滚](/arch/ota-slots.png)

CSV 的六个字段与对齐约束（P10 写明这是工具链的硬性检查，写错构建期直接报错）：

| 字段 | 作用 | 来源里的约束 |
| --- | --- | --- |
| name | 分区名，`esp_partition_find_first` 按名查 | 最长 16 字节（含结尾空字符，即 15 字符） |
| type | app / data 两大类 | bootloader 只认 app 和 data |
| subtype | app：factory/ota_0~ota_15/test；data：ota/nvs/phy/spiffs/fat/nvs_keys/coredump | 决定库把这块地当什么用 |
| offset | 起始地址 | 可留空自动分配；所有分区至少 `0x1000` 对齐；app 分区必须 `0x10000` 对齐 |
| size | 大小 | 支持 K/M 后缀；app 分区大小须 4 KB 对齐 |
| flags | encrypted / readonly | app、bootloader、分区表、otadata、nvs_keys 五类无条件加密，与 flags 无关 |

P10 的 subtype 说明里，本章用得到的是：`factory` 是出厂 app 槽，otadata 无效时 bootloader 的兜底；`ota_0/ota_1` 是两个升级槽；`otadata`（data/ota）是“下次启动谁坐庄”的记票板；`nvs` 是键值库；`phy_init` 放射频初始化数据；`spiffs/fat` 是文件系统分区。两个 ota 槽要等大；不等大不会立刻报错，但构建系统会在固件只装得进部分槽时警告。

![ESP32 Flash 分区与 OTA：otadata 指向当前 app 槽，新固件写入另一槽；失败可回滚](/figures/esp32-10-flash-nvs-ota.svg)

NVS 是 P10 笔下的“带磨损均衡的键值库”。P10 转述的 Internals 结构是：

- 分区按 4096 字节一页切，一页正好一个物理扇区；
- 页 = 页头 32 字节（状态 4 + 序号 4 + 版本 1 + 保留 19 + CRC32 4）+ 条目状态位图 32 字节 + 126 个条目；
- 条目 32 字节：命名空间索引 + 类型 + 跨度 + CRC32 + key（最长 15 字符）+ 数据。

核心机制是追加写：更新一个 key 不是改旧条目，而是尾部追加新条目、把旧条目标记为 erased。P10 说这个设计同时买到三样东西：写入摊到整个分区（官方量化说法是擦除频率相对写入频率降低 126 倍）、半写条目 CRC 不过被当不存在（任意时刻断电，除正在写的那个键值对外不丢数据）、页满后自动整理（Active→Full→Erasing，把有效条目搬走再整页擦除）。页状态还有 Corrupted，页头 CRC 不过就整页弃用。

```c
nvs_handle_t h;
nvs_open("counter", NVS_READWRITE, &h);
nvs_set_i32(h, "boot_count", 42);
nvs_commit(h);          /* P10：commit 之前不真正落盘 */
nvs_close(h);
```

P10 给的三条纪律：`nvs_commit` 是每批写入的句号；读不存在的 key 返回 `ESP_ERR_NVS_NOT_FOUND`，不是错误；初始化要接住 `ESP_ERR_NVS_NO_FREE_PAGES` 与 `ESP_ERR_NVS_NEW_VERSION_FOUND`，必要时 `nvs_flash_erase()` 后重新初始化。P10 的 boot_count 例是每次启动读旧值、加一、写回、commit；它说烧录后连续断电重启五次会看到 1→2→3→4→5。这是 P10 的自述（它声称有实物实验留档），不是本章的实测记录。

OTA 的 API 五步（P10 的写法，最后加 `esp_restart()`）：

```c
const esp_partition_t *next = esp_ota_get_next_update_partition(NULL);
esp_ota_handle_t ota;
esp_ota_begin(next, OTA_SIZE_UNKNOWN, &ota);  /* 大小未知则先整槽擦除 */
esp_ota_write(ota, chunk, len);               /* 循环分块写 */
esp_ota_end(ota);                             /* 校验闸：镜像不合法在此拦下 */
esp_ota_set_boot_partition(next);             /* 改票：下次启动换槽 */
esp_restart();
```

P10 强调两个设计：`esp_ota_get_next_update_partition()` 从当前运行槽自动轮转找另一个槽；`esp_ota_end()` 是校验闸，镜像不是合法 app（或开了安全启动后签名不过）就返回 `ESP_ERR_OTA_VALIDATE_FAILED`，坏 bin 在这里被拦下。

防变砖的状态机只在 `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` 打开后存在，P10 明确说它默认未启用：

| 状态 | bootloader 会选它吗 | 谁设置 |
| --- | --- | --- |
| `ESP_OTA_IMG_VALID` | 正常选 | `esp_ota_mark_app_valid_cancel_rollback()`：自检通过、转正 |
| `ESP_OTA_IMG_UNDEFINED` | 正常选 | `esp_ota_set_boot_partition()`，未开回滚时设的就是它 |
| `ESP_OTA_IMG_INVALID` | 永不选 | `esp_ota_mark_app_invalid_rollback_and_reboot()`：主动判死 |
| `ESP_OTA_IMG_ABORTED` | 永不选 | bootloader：发现上次停在 PENDING_VERIFY，改写为 ABORTED |
| `ESP_OTA_IMG_NEW` | 只给一次启动机会，且立即被改写为 PENDING_VERIFY | `esp_ota_set_boot_partition()`，开了回滚时设它 |
| `ESP_OTA_IMG_PENDING_VERIFY` | 不选，改写为 ABORTED 后弃用 | bootloader 首次启动 NEW 镜像时设置 |

开了回滚后，P10 的完整生命周期是：`esp_ota_set_boot_partition()` 把新镜像标 NEW → 重启后 bootloader 把 NEW 改写为 PENDING_VERIFY 并启动新固件 → 新固件自检通过就调 `esp_ota_mark_app_valid_cancel_rollback()` 转 VALID，失败就调 `esp_ota_mark_app_invalid_rollback_and_reboot()` 转 INVALID 并立即回旧槽；如果 PENDING_VERIFY 没确认就断电、崩溃或看门狗复位，下次启动 bootloader 把它改写为 ABORTED、弃用，自动回旧槽。只要不重启，PENDING_VERIFY 可以一直挂着；回滚永远发生在下次启动。

默认不开回滚时，P10 说 NEW 与 PENDING_VERIFY 两个状态根本不会被使用，`esp_ota_set_boot_partition()` 设的是 UNDEFINED，bootloader 直接启动新槽、立即视为有效，坏固件也照样坐庄，不会自动回滚。P10 还给了三个附带事实：回滚状态记在 otadata 分区里，不在固件镜像里；只有 ota 槽会回滚，factory 槽不参与；当前固件还停在 PENDING_VERIFY 时就发起下一次 OTA，`esp_ota_begin()` 会报 `ESP_ERR_OTA_ROLLBACK_INVALID_STATE`。最后一条工具链事实是：这个选项编译在 bootloader 里，menuconfig 改完必须 `idf.py flash` 连 bootloader 一起重烧，只烧 app 不生效。

![OTA 双槽轮流坐庄：下载、切槽、自检、回滚](/anim/esp32-ota-rollback.svg)

### 八、读保护与写保护：解锁之外的两把锁

解锁只打开 Flash 控制器；读保护（RDP）和写保护（WRP）是另一层。P10 的 ESP32 安全选项、S13 的 F4 选项字节与根书第 12 章的 F1/F4 对照，都指向同一条：这两把锁不是“解锁就能绕过”的。

| 项 | STM32F1 | STM32F4 |
| --- | --- | --- |
| 读保护的无保护值 | `0xA5` | `0xAA`（Level 0） |
| 读保护的中间档 | 其他值是保护；没有 Level 2 | 非 `0xAA`、非 `0xCC` 是 Level 1 |
| 读保护的不可逆档 | 无 | `0xCC`（Level 2），不可逆 |
| 解除读保护的代价 | 整片擦除主 Flash | Level 1 可回 Level 0，但会整片擦除；Level 2 不能回 |
| 写保护粒度 | 按页 | 按扇区 |

F1 的 RDP 只有“保护/不保护”两态，`0xA5` 是不保护，改成别的值就启用保护；把 `0xA5` 写回去会先整片擦除主 Flash。F4 分三档：`0xAA` 无保护；其他非 `0xCC` 的值是 Level 1，调试器能擦但不能读 Flash 内容；`0xCC` 是 Level 2，写入后 Flash 永远不能再被调试器访问，也不能降回 Level 0/1。S13 与根书都提醒 Level 2 是单向门，开发期不要碰。

读保护不是加密：它挡的是调试器读 Flash，用户代码自己仍能读；真要防拆片读固件，是另一套加密话题。写保护则直接让擦写失败：WRP 开着的页/扇区，解锁后照样置 WRPERR。选项字节有独立的解锁序列，和主 Flash 的两把钥匙不是同一套；改之前先备份，改读保护会整片擦除。

## 测量与证据

本章没有上板读数。S13 没有独立工程，根书第 12 章的动手实验是待做清单，P10 声称 boot_count 1→5 与回滚日志有实物实验留档，但本仓库未见原始日志文件；本章手上没有示波器、逻辑分析仪或串口日志。能拿出来的证据分四类：手册位与规则、按地址和位宽算出的账、来源自述与静态代码、待做的实验设计。下面的台架只写步骤、预期与记录模板，不替它们填数。

### 台架一：F407 扇区 11 擦写读回（待做）

1. 前置：查链接脚本与 map，确认没有代码、常量或栈落在 `0x080E0000`–`0x08100000`。正式 App 如果已经用到扇区 11，先换布局，不要在运行中的产品上做这一步。
2. 读前：用调试器读 `0x080E0000` 起 16 个字并记录；未用过的扇区应是 `0xFFFFFFFF`。
3. 擦除：按机制第三节的 `flash_erase_sector(11)` 执行，用 GPIO 翻转或 DWT 周期计数记录从置 STRT 到 BSY 落下的时间。
4. 写读：向 `0x080E0000` 写 `0xA5A50001`，向 `0x080E0004` 写 `0x5A5A0002`；读回并逐字比对。
5. 断电重启：断开电源再上电，读回同样两个字；记录日期、板子、供电电压、PSIZE 档位、擦除时间、读回值。

预期是两个字都保留。擦除时间只写“毫秒到秒级”，因为 S13 说 128 KB 扇区“最坏几百毫秒”，根书表写 0.4–4 s，两个来源对不上，具体以实测和 DS 的 max 值为准。

| 日期 | 板子 | 供电/PSIZE | 擦除时间 | 写入值 | 断电后读回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

### 台架二：F103C8 页擦写与 1→0 规则（待做）

1. 前置：用只占前 16 页的测试工程，或在链接脚本里显式保留页 63。本书的 46 KB APP 布局把页 63（`0x0800FC00`）包在 APP 内，正式固件里擦它等于擦自己。
2. 擦页 63：按机制第三节的 `f1_flash_erase_page(0x0800FC00)`，读回应为 `0xFFFF`。
3. 写半字：向 `0x0800FC00` 写 `0xA5A5`，向 `0x0800FC02` 写 `0x5A5A`，读回比对。
4. 不擦除再写：向同一地址写 `0x0000`，预期 PGERR 或读回不是 `0x0000`；这一步验的是“只能把 1 写成 0，想把 0 变回 1 必须先擦页”。
5. 断电重启读回；记录页地址、页大小、写入值、错误位与读回值。

| 日期 | 板子 | 页地址/页大小 | 写入值 | 不擦重写的结果 | 断电后读回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

### 台架三：IAP 跳转与坏镜像拒绝（待做）

1. Bootloader 链接 `0x08000000`，App 链接 `0x08004000`（F407）或 `0x08004800`（F103C8）；App 在 `main` 开头写 `SCB->VTOR`，启动后打印版本心跳。
2. 正常镜像：Bootloader 校验向量后跳转，串口应打印 App 心跳；记录从复位到心跳的时间。
3. 坏向量：把 App 向量表第 0 字改成 `0x30000000`（不在 SRAM），重新烧录；Bootloader 应拒绝跳转，留在升级模式并打印错误码。
4. 坏入口：把第 1 字改成槽外地址，或把 Thumb 位清零；Bootloader 应拒绝。
5. 坏 CRC：改镜像里一个字节但不改 CRC；Bootloader 应在写槽阶段拒绝，而不是跳转后才发现。

| 日期 | 板子 | 镜像 | 向量/CRC 检查 | Bootloader 行为 | App 心跳 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

### 台架四：STM32 双槽切换与回滚（待做）

1. 按机制第六节的 F407 或 F103C8 布局建两个等大槽；A 放 1.0.0，B 空。
2. 正常升级：写 B、校验、追加记录、重启；串口应打印 1.1.0 且运行槽为 B；App 自检通过后追加“有效”记录。
3. 传输中断：再升级 1.2.0，在写 B 到一半时断电；重新上电应仍启动 A（或当前有效槽），B 的不完整记录不生效。
4. 坏 CRC：写一个 CRC 错的镜像到 B；Bootloader 应拒绝换槽，A 继续运行。
5. 不确认回滚：让 B 启动后既不追加“有效”也不复位，手动复位；Bootloader 应把 B 标无效并回 A。记录每步的串口输出与元数据区内容。

| 日期 | 板子 | 场景 | 记录区 seq/state | 启动槽 | 串口输出 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

### ESP32 侧：来源步骤，未复跑

P10 的 boot_count 与 OTA 回滚是 P10 的自述（声称有实物实验与日志存档，本仓库未见原始日志文件），不是本章的实测。如果手上有 ESP32-S3，按 P10 的步骤复跑：`nvs_rw_value` 连续断电五次看 1→5；开 `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` 后做一次“不 mark valid”的 OTA，看下次启动是否回滚。记录表另开，不与 STM32 台架混在一起。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| F407 扇区表 0–11 | S13 表格；本章按总和复算 | 4×16+64+7×128=1024 KB；扇区 11 从 `0x080E0000` 起 | 手册规则/复算（S13 正文“11 个扇区”是计数笔误） |
| F407 512 KB 型号只到扇区 7 | RM0090 存储器映射的通行定义；S13/P10 未列，根书第 12 章把 S0–S7 标在 F407VG 名下（`docs/12-Flash与IAP升级.md:138`，512 KB 的扇区表标错了型号） | 扇区 8–11 是 1 MB 型号的版图 | 手册规则，未核原件；来源标注冲突 |
| F103C8 1 KB/64 页/末页 | 根书第 12 章；本章复算 | `0x08000000+63×0x400=0x0800FC00` | 手册规则/复算 |
| F103 高密度 2 KB 页 | 根书第 12 章 | 页大小 2 KB，地址按 `n×0x800` | 来源说法（RM0008 转引，未核原件） |
| 两把钥匙 | S13、根书第 12 章 | `0x45670123` → `0xCDEF89AB`；顺序错锁到复位 | 手册规则（两家一致；不是 CMSIS 宏） |
| F4 PSIZE 三档与电压 | S13 只给 3.3 V→x32 与三档编码；电压区间按 RM0090 语义补 | x32/x16/x8；2.7–3.6/2.1–2.7/1.8–2.1 V（各区间的最高档） | 手册规则，区间待复核 |
| F407 无 x64 | S13 | x64 仅 F42x/F43x | 手册规则（未核原件） |
| F1 半字编程 | 根书第 12 章 | 16 位、2 字节对齐、无按字节编程 | 手册规则 |
| F4 CR 位号 | S13 与本章代码注释对过 | PG0/SER1/MER2/SNB3–6/PSIZE8–9/STRT16/LOCK31 | 手册规则（S13 已列主位） |
| F4 SR 错误位 | S13 给 EOP0/BSY16/WRPERR4；其余按 RM0090 语义补 | EOP0/OPERR1/WRPERR4/PGAERR5/PGPERR6/PGSERR7/BSY16 | 手册规则，补全位待复核 |
| F1 CR/SR 位号 | 本章按 RM0008 第 3 章语义填；两个来源都没有逐位列出 | PG0/PER1/STRT6/LOCK7；BSY0/PGERR2/WRPRTERR4/EOP5 | 手册规则，待复核 |
| F4 FLASH 基址 | S13 | AHB1 `0x40020000`+`0x3C00`=`0x40023C00` | 手册规则/复算 |
| F1 FLASH 基址 | 手册常识；来源未列 | `0x40022000` | 手册规则，未核原件 |
| F407/F103C8 的 SRAM 区间 | 数据手册的通行定义；来源只提“MSP 在 SRAM” | F407 主 SRAM 128 KB；F103C8 20 KB | 手册规则，未核原件 |
| 擦写寿命 | 根书第 12 章引数据手册 | ≥1 万次、20 年 @ 85 °C | 来源说法，待复核 |
| 擦除时间 | S13“几百毫秒”与根书“0.4–4 s” | 两处不一致 | 来源说法冲突，待复核 |
| 单槽 IAP 布局 | S13（F407 0x08004000）、根书（F103C8 0x08004800） | 两处都是本书布局 | 来源设定（RM 没有规定这样分） |
| 向量表两字与 VTOR | 根书第 12 章、S13；PM0056 转引 | [0]=MSP，[1]=Reset_Handler；VTOR 指 App 基址 | 手册规则 |
| 跳转顺序与 PRIMASK | S13 不重开中断；根书清 NVIC 后开；本章选 App 早期开 | 两种都能工作，不能两边都不做 | 设计选择/来源差异 |
| SystemInit 覆盖 VTOR | STM32 HAL 通行实现；三个来源都没有展开 | 默认写回 `FLASH_BASE | VECT_TAB_OFFSET` | 源码行为，未核具体版本 |
| STM32 双槽布局 | 本章按扇区/页算术 | F407 480 KB+480 KB；F103C8 22 KB+22 KB | 本章推导，未上板 |
| OTA 记录格式与回滚 | 本章设计；根书实验 3 只要求 A/B 回滚 | 追加记录、CRC、待确认/有效/无效 | 设计，待上板 |
| ESP32 分区表位置与长度 | P10 | `0x8000`、`0xC00`、95 条、MD5、占满 `0x1000` 扇区 | 来源说法（IDF 文档转引，未核原文） |
| ESP32 CSV 六字段与对齐 | P10 | `0x1000` 对齐、app `0x10000` 对齐、app 4 KB 对齐 | 来源说法 |
| ESP32 NVS 页/条目/追加写 | P10 转述 IDF Internals | 4096 字节页、32 字节页头、126 条目、32 字节条目 | 来源说法 |
| ESP32 OTA 五步与状态机 | P10 转述 IDF OTA | 默认未开回滚；otadata 两个扇区；只有 ota 槽回滚 | 来源说法 |
| ESP32 boot_count 1→5 | P10 的实物实验自述，声称日志存档 | 本仓库未见原始日志文件 | 来源说法，待复核 |
| 本章所有台架读数 | 本章未做 | 四张记录表为空 | 待做实验 |

这些数能互相对上的只有手册位、算术与静态代码：1 MB 的总和能证明 12 个扇区，`0x08000000+63×0x400` 能证明末页地址，F407 的 480 KB+480 KB 能证明两个槽等大；它们都不能证明某块板上的扇区 11 真的擦成了 `0xFFFFFFFF`，也不能证明某次 OTA 断电后真的回到了旧槽。要补上后者，得按四个台架留下调试器读回、串口日志、GPIO 翻转时间和元数据区内容。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 擦除或编程完全没反应，SR 只有 BSY 在动 | Flash 还锁着，或钥匙顺序写反 | 读 CR 的 LOCK 位；确认 KEY1/KEY2 的写入顺序 | 重新上电清掉错误序列，先 KEY1 后 KEY2；已解锁就不要重复写钥匙 |
| 擦除返回 WRPERR | 目标页/扇区被 WRP 保护，或地址不在页/扇区边界 | 读 SR 的错误位；对照选项字节与页/扇区表 | 先解 WRP 或换未保护页；擦除地址按页/扇区边界对齐 |
| 写进去读回不是目标值 | 目标没擦干净，PSIZE 高于供电允许的最高档，或 F1 没按半字/偶地址写 | 读回擦除态是不是 `0xFFFFFFFF`；查 PSIZE 与供电、写入宽度是否配对 | 先擦后写；PSIZE 按电压选不超过上限的档，写宽度与 PSIZE 一致；F1 按 2 字节对齐写半字 |
| 编程报 PGAERR/PGPERR/PGSERR，或 F1 报 PGERR | PSIZE 与写宽度不符（PGPERR/PGSERR），地址或宽度与 PSIZE 不对齐（PGAERR）；F1 则是往未擦除的半字再写（PGERR） | 读 SR 错误位；读目标字是否仍非 `0xFFFFFFFF`；查地址对齐与 PSIZE | 先擦目标扇区/页；按 PSIZE 的宽度与对齐写；F4 往未擦除单元再写的具体报错路径待复核 |
| 擦一个 128 KB 扇区时看门狗复位 | 擦除时间远超喂狗周期，或中断处理也在 Flash 里等总线 | 看复位前是否刚置 STRT；量 BSY 持续时间 | 擦写关键路径放 RAM；按最坏擦除时间喂狗或临时关狗 |
| 跳转后立刻 HardFault | MSP 不在 SRAM，向量表第 1 字在槽外，或 Thumb 位为 0 | 读 App 基址第 0/1 字；对照 SRAM 区间与槽边界 | 修链接脚本与向量表；跳转前做 `app_vector_ok()` 检查 |
| App 能跑，但中断全跑到 Bootloader | VTOR 还是 0，或 App 的 `SystemInit()` 把它写回 `0x08000000` | 读 `SCB->VTOR`；看 App 是否设置 `VECT_TAB_OFFSET` | Bootloader 跳转前设 VTOR；App 在 `main` 开头再设一次 |
| App 能跑，但所有可屏蔽中断都不来 | PRIMASK 还是 1，Bootloader 与 App 都没开中断 | 读 PRIMASK；看跳转函数是否 `__enable_irq()` | App 启动早期 `__enable_irq()`，或跳转前最后一步开（前提是 NVIC 已清空） |
| 跳转后 App 反复复位 | 看门狗没喂、时钟/外设不是 App 期望的状态，或向量表只对了一半 | 看复位原因；读 RCC 与外设寄存器；确认 App 重新初始化 | App 重新配时钟与外设；Bootloader 跳转前 `HAL_RCC_DeInit()`/`HAL_DeInit()` 或明确交接 |
| 参数断电后变回默认值 | 擦到一半断电，魔数或 CRC 不过；A/B 两份在同一擦除单位 | 读两份的魔数、seq、CRC；看地址是否同扇区/同页 | 把 A/B 放到不同扇区/页；先写备份、校验、再提交 |
| 参数区写几次就坏 | 同一扇区反复擦写，寿命单点消耗 | 统计擦写次数与地址；看是否每次都在同一页 | 做磨损均衡、双备份或换外部 FRAM/EEPROM |
| 单槽升级失败后设备停在 Bootloader | 旧 App 已被擦掉，没有备份可回 | 看 App 区是否已被擦；CRC/传输是否失败 | 改双槽；失败时留在升级模式等重传，别跳无效镜像 |
| 双槽升级后还是启动旧槽 | 新记录没提交、CRC 不过，或新槽镜像长度超过槽大小 | 读元数据区最新记录的 seq/state/crc；比镜像长度与槽大小 | 重新写槽并提交；两槽等大；校验通过再追加记录 |
| 新槽启动一次就回旧槽 | 新固件没在下次启动前追加“有效”记录 | 读记录区的 state 是否仍是“待确认” | App 自检通过后追加“有效”；失败则主动标无效 |
| 双槽永远不回滚 | 没有“待确认/有效”状态，或 Bootloader 不检查记录 | 看记录格式里有没有 state 与 boot 次数 | 加待确认状态与回滚路径；回滚在下次启动执行 |
| F103 大容量型号擦错页 | 把 1 KB 页表套到 2 KB 页的型号上 | 查芯片密度与页大小；看擦除地址是否页边界 | 高密度按 2 KB 页重算地址 |
| ESP32 app 分区装不下 | 镜像超过 CSV 里的 size，或分区表没换 | 看构建期 Partition Size Checks 与 `idf.py partition-table` | 扩 app 分区或 `-Os` 瘦身；换双槽表后全量烧录 |
| ESP32 NVS 初始化报 NO_FREE_PAGES | 分区太小或没有空页；`NEW_VERSION_FOUND` 则是格式版本变了 | 读返回码；看分区大小与页数 | `nvs_flash_erase()` 后重新初始化；分区至少 0x3000、三页 |
| ESP32 OTA 后坏固件照样启动 | `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` 没开 | 看 menuconfig 与 bootloader 日志；state 是不是 UNDEFINED | 开回滚并 `idf.py flash` 连 bootloader 重烧；App 自检后 mark valid |
| ESP32 改了分区表但启动还是旧布局 | 只烧了 app，没烧分区表/bootloader | 看 `idf.py partition-table` 与烧录日志 | `idf.py flash` 全量重烧 |

## 跨平台边界

F407 一侧：1 MB 主 Flash 从 `0x08000000` 起，12 个扇区按 16/64/128 KB 分布，扇区 11 在 `0x080E0000`。单槽 Bootloader 占扇区 0，App 从 `0x08004000` 起；双槽把扇区 1 做元数据，扇区 2–7 与 8–11 分成两个 480 KB 槽。Flash 控制器基址 `0x40023C00`（AHB1 `0x40020000`+`0x3C00`），CR 的 PG/SER/SNB/PSIZE/STRT/LOCK 与 SR 的 EOP/BSY/WRPERR 按 S13 的位号；PSIZE 在 2.7–3.6 V 选 x32，F407 不选 x64。IAP 跳转用 `SCB->VTOR`、`__set_MSP` 与向量表第 1 字；App 的 `SystemInit()` 可能把 VTOR 写回 `0x08000000`，要在 App 里再设一次。擦写关键路径放 `.ramfunc`，链接脚本给 RAM 的 VMA 与 Flash 的 LMA。读保护 `0xAA` 无保护、`0xCC` 是 Level 2 单向门；写保护按扇区。512 KB 的 F407xE 只用到扇区 7，扇区 8–11 是 1 MB 型号的版图。F42x/F43x 才有 x64 与双字编程，换系列先查数据手册，不要把 F407 的配置直接搬过去。

F103 一侧：C8 是 64 KB、中容量、1 KB 一页、64 页，页 63 在 `0x0800FC00`；高密度型号是 2 KB 一页，地址按 `n×0x800` 重算。Flash 控制器基址 `0x40022000`，CR 的 PG/PER/STRT/LOCK 与 SR 的 BSY/PGERR/WRPRTERR/EOP 位号和 F4 不同；编程粒度是半字，没有 PSIZE 与按字节编程。本书布局是 Bootloader 16 KB、参数区 2 KB、App 46 KB；双槽把 App 区切成 22 KB+22 KB+2 KB。IAP 的 App 起点是 `0x08004800`，VTOR 同样要在 App 里写。读保护 `0xA5` 是不保护，其他值启用保护，没有 Level 2；解除保护会整片擦除主 Flash。F103C8 只有 20 KB SRAM，向量表第 0 字的 MSP 检查要用 `0x20000000`–`0x20005000`，不要照抄 F407 的 `0x20020000`。GD32 的 Flash 控制器是另一套寄存器，本章不展开。

ESP32 只划边界。ESP32-S3 没有 STM32 的 FLASH_KEYR/CR/SR，也没有扇区 11 或页 63 这套地址；它的版图由 CSV 分区表管，参数由 NVS 管，升级由 `esp_ota_*` 管。P10 的 16 MB 示例表里，`0x8000` 放分区表，`0x9000` 起放 nvs，`0xE000` 放 otadata，两个 3 MB 的 ota_0/ota_1 轮流坐庄；NVS 按 4096 字节页追加写；OTA 的 NEW/PENDING_VERIFY/VALID/ABORTED 状态机只在 `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` 打开后存在，默认不开时 NEW 与 PENDING_VERIFY 不被使用。这些是 P10 的来源说法，本章没有核 IDF 原文，也没有在 ESP32 上复跑；P10 声称 OTA 回滚做过实物实验并日志存档，但本仓库未见原始日志文件。ESP32 的启动、外设与驱动框架在[第 31 章][ch31]；低功耗与看门狗分别在[第 18 章][ch18]与[第 19 章][ch19]。

其它分工：W25Q 外部 Flash 的 SPI 读写在[第 16 章](./16-i2c-spi.md)；存储器地图与时钟树在[第 8 章](./08-architecture-memory-clock.md)；链接脚本、VMA/LMA 与启动序列在[第 6 章](../v0-foundations/06-linker-startup-map.md)；长擦除期间的看门狗与复位原因在[第 19 章][ch19]；低功耗下的 Flash 掉电与唤醒在[第 18 章][ch18]。

## 离开检查

1. 为什么 Flash 必须“先擦后写”？擦除单位为什么不是字节？
2. F407VG 的 1 MB 分成几个扇区？扇区 11 从哪开始、多大？512 KB 型号为什么用不到扇区 8–11？
3. F103C8 的页大小、页数、末页地址各是多少？换成高密度型号后哪几个数要改？
4. 两把钥匙的顺序是什么？写反了会怎样？F4 的 PSIZE 与供电电压怎么配，F407 为什么不能选 x64？
5. IAP 跳转前要做哪几件事？为什么跳复位入口而不是 `main`？VTOR 与 MSP 各自由谁设，PRIMASK 由谁打开？
6. 单槽升级为什么没有回头路？双槽的“原子切换”靠什么记录实现，回滚在什么时候发生？
7. ESP32 的分区表、NVS 与 OTA 各管什么？默认不开回滚时，NEW 与 PENDING_VERIFY 会出现吗？
8. 本章哪些数字是手册规则、哪些是本章算术、哪些只是来源说法或还没有人量过？

<details>
<summary>对照答案</summary>

1. Flash 的位只能把 1 写成 0，目标位模式里只要有 0→1，就必须先擦。擦除的最小单位是页（F1，1/2 KB）或扇区（F4，16/64/128 KB），硬件不提供按字节擦除；所以改一个字节也要把整页/整扇区读出来、擦掉、再连同改过的字节写回去。
2. 12 个扇区：扇区 0–3 各 16 KB，扇区 4 是 64 KB，扇区 5–11 各 128 KB；总数 4×16+64+7×128=1024 KB。扇区 11 从 `0x080E0000` 起，128 KB，到 `0x08100000`。512 KB 的 F407xE 只实现到扇区 7（16×4+64+128×3=512 KB），扇区 8–11 是 1 MB 型号才有的版图。
3. F103C8 是 1 KB 一页、64 页，页 0 从 `0x08000000` 起，页 63 从 `0x08000000+63×0x400=0x0800FC00` 起，到 `0x08010000` 结束。高密度型号是 2 KB 一页，页号与地址的乘法改成 `n×0x800`，页数按容量重算；把 1 KB 表套过去会擦到页中间。
4. 先写 `0x45670123`，再写 `0xCDEF89AB` 到 `FLASH_KEYR`；顺序或数值不对，Flash 保持锁定到下次复位。F4 在 2.7–3.6 V 最高选 x32，2.1–2.7 V 最高 x16，1.8–2.1 V 最高 x8；低档在高压下也能用，但写宽度必须与 PSIZE 一致。x64 只在 F42x/F43x 上存在，F407 的 CR 没有这一档可用。F1 没有 PSIZE，编程粒度固定为半字。
5. 关中断；按芯片实际中断数清 NVIC 使能与挂起、关 SysTick；设 `SCB->VTOR` 指向 App 基址；从 App 基址第 0 字设 MSP；从第 1 字跳复位入口。跳 `main` 会跳过 `.data` 拷贝、`.bss` 清零与 `SystemInit` 时钟配置，App 会跑在半初始化状态。VTOR 由 Bootloader 先设、App 再设一次（HAL 的 `SystemInit()` 可能把它写回 `0x08000000`）；MSP 由跳转函数从 App 向量表第 0 字显式读入；PRIMASK 由 App 在启动早期 `__enable_irq()` 打开，或由 Bootloader 在跳转前最后一步打开，两边不能都不做。
6. 单槽升级在擦掉旧 App 的那一刻就没有备份了：传输失败、CRC 不过、写一半断电，旧程序都不在，只能留在 Bootloader 等重传。双槽把新镜像写另一个槽，校验通过后追加一条带 CRC 和序号的“换槽”记录；这条记录是短事务，写完并通过 `meta_crc` 才算提交，写一半断电则上一条记录仍然有效。回滚发生在下一次启动：新槽处于“待确认”却没转“有效”，Bootloader 就追加一条回旧槽的记录。参数区的 A/B 两份要落在不同的擦除单位，否则擦除时一起没。
7. 分区表管 Flash 的版图（factory/ota_0/ota_1/nvs/phy_init/spiffs 等分区的 offset/size）；NVS 管键值参数，按 4096 字节页追加写、带 CRC 与页满整理；OTA 管双槽升级，`esp_ota_*` 五步写备槽、校验、改 otadata、重启。默认不开 `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` 时，NEW 与 PENDING_VERIFY 不会被使用，`esp_ota_set_boot_partition()` 设的是 UNDEFINED，bootloader 直接启动新槽、立即视为有效，坏固件不会自动回滚；只有开了回滚，才有 NEW→PENDING_VERIFY→VALID/ABORTED 这套状态机。
8. 手册规则：扇区/页结构、两把钥匙、PSIZE 三档（电压区间待复核）、CR/SR 的 F4 主位、F1 的逐位位号（待复核）、向量表两字与 VTOR。本章算术：1 MB 总和、页 63 地址、双槽 480 KB/22 KB 的加减。来源说法：擦写寿命 1 万次/20 年、擦除时间、ESP32 的分区表/NVS/OTA 细节、P10 的 boot_count 1→5。还没有人量过：四个台架的全部读数，记录表为空；STM32 的双槽布局与记录格式是本章设计，也没有上板。

</details>

[ch18]: ../v2-reliability/18-low-power.md
[ch19]: ../v2-reliability/19-watchdog-reset-hardfault.md
[ch31]: ../v4-platforms/31-esp32-drivers-audio.md
