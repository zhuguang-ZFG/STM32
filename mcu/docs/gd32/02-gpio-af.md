---
title: G2 GPIO 与 AF 复用对照：七大寄存器同名不同姓
status: done
difficulty: 2
minutes: 60
---

# G2 GPIO 与 AF 复用对照：七大寄存器同名不同姓

> 🎯 S3 你把 STM32 的 MODER/OTYPER/OSPEEDR/PUPDR 七张表拆到逐位——到了 GD32，这七张表一张都没多、一张都没少，位置也一模一样，只是**每个都换了名字**：CTL、OMODE、OSPD、PUD……本章把这些"同名不同姓"逐个点名，再揪出 GD32 比 STM32 多出来的两件秘密兵器（BC 与 TG）。

## 本章精髓

1. **七大寄存器全部改名、不改岗**：CTL↔MODER、OMODE↔OTYPER、OSPD↔OSPEEDR、PUD↔PUPDR、ISTAT↔IDR、OCTL↔ODR、BOP↔BSRR。偏移 0x00~0x1C 逐字相同，位宽与编码也相同，**名字是唯一差异**（gd32f4xx_gpio.h:52-63）。
2. **GD32 多两件兵器**：`BC`（0x28，独立清零）和 `TG`（0x2C，**硬件翻转**），STM32F4 压根没有这两个寄存器。点灯的"读-改-写翻转"在 GD32 是一条 `str`。
3. **基址与使能位与 STM32F4 完全相同**：GPIOA=0x40020000、GPIOF=0x40021400，时钟使能 `RCU_AHB1EN` bit0~bit8（GPIOA~GPIOI）；连"忘开时钟"这个新手第一大坑，两边都长一个样。
4. **编码一字不差**：模式 0/1/2/3=输入/输出/复用/模拟，上下拉 0/1/2=浮空/上/下，推挽开漏 0/1，S3 背过的"先清后置"肌肉记忆**原样可用**。

- **能理解**：为什么"基址相同 + 偏移相同 + 编码相同"意味着 S3 的知识几乎全额平移；BC/TG 各自解决什么痛点。
- **能用**：拿 S3 点灯的 PF6 流程，把每个寄存器名换成 GD32 版写出来；查 `gd32f4xx_gpio.h` 确认每一项。

## 先修

- [G1 RCU 时钟树](01-rcu-clock.md)：GD32 的 RCU/CK_* 命名体系与"对照读法"；
- [S3 GPIO：七个寄存器位级图解](../stm32/03-gpio.md)：MODER/OTYPER/OSPEEDR/PUPDR/IDR/ODR/BSRR 的位级理解，本章只讲"哪里不一样"。

## 先跑起来（10 分钟 quick win）

打开 `.trellis/ref/gd32/gd32f4xx_gpio.h` 第 52~63 行（寄存器偏移定义），对照 S3 板卡事实里的 STM32F4 偏移表（RM0090 §8.4：MODER 0x00 / OTYPER 0x04 / OSPEEDR 0x08 / PUPDR 0x0C / IDR 0x10 / ODR 0x14 / BSRR 0x18 / LCKR 0x1C / AFRL 0x20 / AFRH 0x24）：**前 10 个偏移逐个对得上，只有名字换了**。5 分钟点名完，你已经会 GD32 GPIO 的 80%。

先押个平移：S3 背过的"先清后置"肌肉记忆，到 GD32 还能原样用吗？翻转点灯这件小事，GD32 会不会专门备一件兵器，让"读-改-写"缩成一条指令？

## 动画：AF 复用的 16 选 1 选择器

一根引脚一根物理线，AF0~AF15 排队过门；每脚 4 位的 AFSEL 字段决定谁过门。PA8 写 AF0、CK_OUT0 上路这个实例，动画演一遍，"换号 = 换接线"一眼看懂。

![GD32 AF 复用：每脚 4 位的选择器，16 选 1 过门](/anim/gd32-af-mux.svg)

## 小节结构

| 小节 | 内容 |
|---|---|
| 一、改名点名 | 七大寄存器 + LOCK/AFSEL 的 STM32↔GD32 对照表 |
| 二、基址与使能 | GPIO 基址、RCU_AHB1EN 使能位——与 STM32F4 完全同款 |
| 三、多出来的两件兵器 | BC 独立清零、TG 硬件翻转；STM32 的曲线实现对比 |
| 四、编码对照 | 模式/上下拉/速度/输出类型四位配置的逐位核对 |
| 五、AF 复用 | AFSEL0/1 与 datasheet 复用表查法 |
| 六、库函数对照 | gpio_mode_set + gpio_output_options_set vs GPIO_Init |

## 一、改名点名：七大寄存器"同名不同姓"

GD32F4xx 每个 GPIO 端口有 **12 个寄存器**（gd32f4xx_gpio.h:52-63），STM32F4 是 10 个。先看点名表：

| 偏移 | STM32F407（RM0090 §8.4） | GD32F4xx（gd32f4xx_gpio.h） | 岗位 |
|---|---|---|---|
| 0x00 | MODER | **CTL**（port control） | 模式：输入/输出/复用/模拟，每脚 2 位 |
| 0x04 | OTYPER | **OMODE**（output mode） | 推挽/开漏，每脚 1 位 |
| 0x08 | OSPEEDR | **OSPD**（output speed） | 输出速度，每脚 2 位 |
| 0x0C | PUPDR | **PUD**（pull-up/pull-down） | 上拉/下拉/浮空，每脚 2 位 |
| 0x10 | IDR | **ISTAT**（input status） | 读引脚真实电平，只读 |
| 0x14 | ODR | **OCTL**（output control） | 输出数据寄存器 |
| 0x18 | BSRR | **BOP**（bit operate） | 低 16 位置位 + 高 16 位复位，原子写 |
| 0x1C | LCKR | **LOCK**（configuration lock） | 引脚配置锁定 |
| 0x20 | AFRL | **AFSEL0**（AF selected 0） | 引脚 0~7 的复用号，每脚 4 位 |
| 0x24 | AFRH | **AFSEL1**（AF selected 1） | 引脚 8~15 的复用号，每脚 4 位 |
| 0x28 | —（无） | **BC**（bit clear） | GD32 独有：独立清零寄存器 |
| 0x2C | —（无） | **TG**（bit toggle） | GD32 独有：硬件翻转寄存器 |

前 10 行的规律一眼看穿：**偏移、位宽、编码全部相同，只有名字换了**。

GD32 的命名习惯是"把类型塞进缩写"：CTL 是 control，OMODE 是 output mode，OSPD 是 output speed，PUD 是 pull-up/down，ISTAT 是 input status，OCTL 是 output control。名字更长，但和 STM32 一样能按"每脚占多少位"直接推。

改名记忆钩子：

- **模式叫 CTL 不叫 MODER**，最易踩的一个：搜文档搜 "MODER" 永远搜不到；
- **输出两兄弟都带 O**：OMODE 管形态（推挽/开漏）、OSPD 管快慢、OCTL 管电平，三 O 打头；
- **输入叫 ISTAT**：input status，比 STM32 的 IDR 直白；
- **BOP 是 BSRR 的 GD32 名**：bit operate，布局同款（低 16 置位、高 16 复位，gd32f4xx_gpio.h:174-206）；
- **复用叫 AFSEL0/AFSEL1**：比 AFRL/AFRH 更好认：数字 0 管 pin0~7、数字 1 管 pin8~15，见名知义。

> **【注】LOCK 寄存器两边都有，坑位相同**。STM32 的 LCKR 有著名的 LCKK 写序列坑；GD32 的 LOCK 键序列已按用户手册实证（F4xx UM p185）：**Write 1 → Write 0 → Write 1 → Read 0 → Read 1**。
>
> 细节也和 STM32 同款：LKK 在 bit16，序列期间 LK[15:0] 必须保持不变，锁定后直到复位才解锁。本站工程暂不用锁定功能。

## 二、基址与使能：连地址都没换

更狠的事实：**GPIO 基址和时钟使能位与 STM32F4 完全相同**。

| 事实 | GD32F4xx | 凭证 | STM32F407 |
|---|---|---|---|
| GPIO 总基址 | GPIO_BASE = AHB1_BUS_BASE + 0x00 = **0x40020000** | gd32f4xx.h:313,341 | 0x40020000 |
| GPIOA | 0x40020000（+0x00） | gd32f4xx_gpio.h:41 | 0x40020000 |
| GPIOF | 0x40021400（+0x1400，步进 0x400） | gd32f4xx_gpio.h:46 | 0x40021400 |
| 端口数 | A~I 共 9 个（F407 常用 A~I） | gd32f4xx_gpio.h:40-49 | A~I |
| 时钟使能寄存器 | RCU_AHB1EN（RCU + 0x30） | gd32f4xx_rcu.h:53 | RCC_AHB1ENR（+0x30） |
| GPIOA 时钟位 | RCU_AHB1EN_PAEN = **bit0** | gd32f4xx_rcu.h:209 | bit0 |
| GPIOF 时钟位 | RCU_AHB1EN_PFEN = **bit5** | gd32f4xx_rcu.h:214 | bit5 |
| GPIOI 时钟位 | RCU_AHB1EN_PIEN = **bit8** | gd32f4xx_rcu.h:217 | bit8 |

GPIOF 开时钟一行，两边只差寄存器名：

```c
/* STM32F407（S3 工程）                          GD32F4xx（同名不同姓） */
RCC_AHB1ENR |= (1UL << 5);          RCU_AHB1EN |= (1UL << 5);   /* 都是 bit5 */
```

为什么能像到这个份上？F4 系的 AHB1 外设布局早就是 ARM 生态的"行业事实标准"。GD32F4xx 对 STM32F4 做的正是**高兼容设计**：外设基址、总线挂载都刻意对齐，迁移成本压到"改宏名"这一级。这正是 G 篇"对照学习"能省力七成的底牌。

但"兼容"≠"相同"：G1 已经演示过 RCU 内部位域有差异（HDRF/HDSRF 回执、SCSS 解码），本章第四节会看到速度档标签的小差异。**基址相同给你迁移便利，位域还得逐个核**，这是 G 篇的总纪律。

> **【注】"忘开时钟"坑两边一个指纹**：S3 说"不开 GPIOF 时钟，寄存器读回全是 0"，GD32 一模一样，连症状带解法（先写 RCU_AHB1EN）都原样复用。新手第一大坑，在 GD32 上还是第一大坑。

## 三、多出来的两件兵器：BC 与 TG

STM32F4 的 GPIO 到 0x24（AFRH）就结束了；GD32F4xx 在 0x28 和 0x2C 又加了两个寄存器，这是**这颗芯片对 GPIO 的真增强**：

### BC（0x28）：独立清零寄存器

低 16 位每脚一位，写 1 清零对应引脚（gd32f4xx_gpio.h:247-263）。

STM32 里要清一个引脚，两条路：BSRR 高 16 位（`GPIOx_BSRR = 1UL << (pin+16)`）或 ODR 读-改-写。GD32 把"清零"单独发一个寄存器：**低 16 位直接写脚号位**，不用 +16 挪半档：

```c
RCC_...                                    /* STM32：BSRR 高 16 位清零     */
GPIOF_BSRR = (1UL << (6 + 16));            GPIOF_BC = (1UL << 6);      /* GD32：BC 直接写 */
```

顺手一提：BOP（0x18）的高 16 位同样能清零（CR0~CR15，gd32f4xx_gpio.h:191-206），所以 GD32 是**清零有两条路**（BOP 高 16 位、BC 低 16 位），置位只有一条（BOP 低 16 位）。官方库 `gpio_bit_reset()` 走的是 BC（查 gd32f4xx_gpio.c 可核，**本页以 .h 位定义为准**）。

### TG（0x2C）：硬件翻转寄存器

低 16 位每脚一位，**写 1 让引脚电平翻转**（gd32f4xx_gpio.h:265-281）。

这一下就动了 STM32 的奶酪。S3 讲过：STM32 翻转一个引脚要么 ODR 读-改-写（`GPIOF_ODR ^= 1UL<<6`，三条指令、可被中断插队）、要么 BSRR 配合读 ISTAT/ODR 判断当前态。GD32 的答案是**硬件翻转一条写指令**：

```c
GPIOF_TG = (1UL << 6);    /* 一条 str：PF6 电平翻转，原子、无读操作 */
```

点灯场景直接受益：blink 不再需要"记住当前状态"，往 TG 写脚号位就行；官方库也给了对应封装 `gpio_bit_toggle()`（gd32f4xx_gpio.h:402）和整端口翻转 `gpio_port_toggle()`（:404）。

> **【注】TG 与 BOP/BC 一样是"写 1 生效、写 0 无影响"**，对 TG 用读-改-写毫无意义（它不需要读）。但注意 TG 只翻转**输出路径的电平**，输入侧要看 ISTAT；高频翻转时 OSPD 速度档不够会看到边沿变缓，速度档配置见第四节。

### 三剑客变四剑客

S3 的"数据三剑客"（IDR/ODR/BSRR）在 GD32 变成**四剑客**：ISTAT（看）、OCTL（写）、BOP（原子置位/复位）、加上 BC/TG 双兵器。对照记忆：

| 动作 | STM32F407 | GD32F4xx |
|---|---|---|
| 读电平 | IDR | ISTAT |
| 写电平 | ODR（读-改-写有隐患） | OCTL（同隐患） |
| 原子置位/复位 | BSRR 低/高 16 位 | BOP 低/高 16 位（同款） |
| 独立清零 | —（只有 BSRR 高 16 位） | **BC** 低 16 位 |
| 翻转 | ODR `^=`（三条指令） | **TG** 低 16 位（一条写） |

## 四、编码对照：四位配置一字不差

S3 背过的"配置四维"编码，在 GD32 **逐位相同**（全部出自 gd32f4xx_gpio.h 的常量定义）：

| 维度 | 取值编码 | GD32 常量（行号） | STM32 对应 |
|---|---|---|---|
| 模式（CTL） | 00 输入 / 01 输出 / 10 复用 / 11 模拟 | GPIO_MODE_INPUT/OUTPUT/AF/ANALOG = 0/1/2/3（:288-291） | MODER 同款 00/01/10/11 |
| 上下拉（PUD） | 00 浮空 / 01 上拉 / 10 下拉 | GPIO_PUPD_NONE/PULLUP/PULLDOWN = 0/1/2（:295-297） | PUPDR 同款 |
| 输出类型（OMODE） | 0 推挽 / 1 开漏 | GPIO_OTYPE_PP/OD = 0/1（:331-332） | OTYPER 同款 |
| 速度（OSPD） | 00 / 01 / 10 / 11 四档 | GPIO_OSPEED_2MHZ/25MHZ/50MHZ/MAX = 0/1/2/3（:336-345） | OSPEEDR 同款四档 |

唯一值得点名的是**速度第四档的标签**：STM32F4 的 11 档标 **100MHz**（rm0090），GD32 的 LEVEL3 标 **GPIO_OSPEED_MAX**，注释明说 "max speed more than 50MHz"（gd32f4xx_gpio.h:345）：**库头文件不承诺具体数字**。

但 datasheet 承诺了，而且比 100MHz 更激进。GD32F407xx Datasheet Rev2.7 **Table 4-28 I/O port AC characteristics**（p101）把四档全标了名、还按负载电容给了实测上限：

| OSPD[1:0] | datasheet 档位名 | CL=10pF | CL=30pF | CL=50pF |
|---|---|---|---|---|
| 00 | IO_Speed = 2 MHz | 30 MHz | 25 MHz | 15 MHz |
| 01 | IO_Speed = 25 MHz | 95 MHz | 80 MHz | 50 MHz |
| 10 | IO_Speed = 50 MHz | 160 MHz | 125 MHz | 90 MHz |
| 11 | **IO_Speed = 200 MHz** | 200 MHz | 170 MHz | 130 MHz |

三件事带走：

1. **第四档的真名是 200MHz**，不是库注释里含糊的"more than 50MHz"，也不是 STM32 的 100MHz。对照 STM32F407 datasheet 的同款表（2/25/50/100MHz 四档），GD32 把第四档的标称值翻了一倍。
2. **档位名是标称值，不是能跑到的频率**。`IO_Speed = 2 MHz` 这档在 10pF 轻载下实测能到 30MHz；反过来 200MHz 档挂 50pF 只剩 130MHz。真正决定边沿的是**档位 + 负载电容**两个变量，表里每档三列就是这个意思。
3. datasheet 注 (4) 还压了一道天花板：**最高频率不得超过 168 MHz**（F407 的核心上限）。也就是说，200MHz 这个标称值在 F407 上根本吃不满——它是给 F450/F470 的高主频档留的。

> ⚠️ **四个引脚是例外**。datasheet 注 (3) 明说 **PC13 / PC14 / PC15 / PI8 走 Power Switch 供电**，只能取到很小的电流。它们做输出时**速度不得超过 2 MHz**（最大负载 30pF）。这四个脚在 STM32F407 上同样是"备份域弱驱动"脚（PC13-PC15 接 LXTAL/侵入检测），两边都别拿来驱动高速信号或直推 LED。

所以 S3 的 PF6 点灯流程翻译成 GD32，一个字都不用改逻辑，只换寄存器名：

```c
/* GD32F4xx：PF6 推挽输出点灯（对照 S3 的 00-blink，仅换名） */
RCU_AHB1EN  |= (1UL << 5);                          /* GPIOF 时钟：bit5，同 STM32  */
GPIOF_CTL   &= ~(3UL << (6 * 2));                   /* 先清：CTL[13:12]            */
GPIOF_CTL   |=  (1UL << (6 * 2));                   /* 后置：01 = 输出             */
GPIOF_OMODE &= ~(1UL << 6);                          /* 0 = 推挽                    */
GPIOF_OSPD  &= ~(3UL << (6 * 2));                    /* 00 = 低速                   */
GPIOF_PUD   &= ~(3UL << (6 * 2));                    /* 00 = 浮空                   */
GPIOF_BC    =  (1UL << 6);                           /* 清零 PF6 → 拉低（共阳则亮） */
```

"先清零再置位"的纪律（S3 的【注】）原样生效：CTL 是两位格子，不清就置可能踩出意外组合；复位后 PA13/PA14 等调试脚默认复用模式的提醒也照搬。

## 五、AF 复用：AFSEL0/1 与复用表查法

复用机制的框架与 S3 第四节完全一致，改名与分界如下：

| 项 | STM32F407 | GD32F4xx | 凭证 |
|---|---|---|---|
| 复用模式位 | MODER[1:0] = 10 | **CTL[1:0] = 10**（GPIO_MODE_AF=2） | gd32f4xx_gpio.h:290 |
| AF 号寄存器 | AFRL（pin0~7）/ AFRH（pin8~15） | **AFSEL0 / AFSEL1**，每脚 4 位 | gd32f4xx_gpio.h:227-245 |
| AF 号范围 | AF0~AF15 | **AF0~AF15**（GPIO_AF_0..GPIO_AF_15） | gd32f4xx_gpio.h:353-368 |
| nibble 定位 | AFR[pin >> 3] | 同款算法（AFSEL1 管 pin8~15） | — |
| 哪脚能当什么 | datasheet 复用功能表（Table 9，一张表管全部端口） | **datasheet §2.6.6，Table 2-9 ~ 2-17 共九张表**（Port A~I 一端口一张） | GD32F407xx Datasheet Rev2.7 p60-68（已核验） |

G1 已核过一个实例：**PA8 输出 CK_OUT0 用 AF0**（`gpio_af_set(GPIOA, GPIO_AF_0, GPIO_PIN_8)`，官方 example_ckout_main.c:135）；datasheet Table 2-9 的 AF0 列也正是 `CK_OUT0`，与 STM32 MCO1 的 PA8/AF0 同脚同号。

本章把那条"逐脚核对"的作业也做了：**USART0_TX = AF7**，候选脚 **PA9 / PB6 / PA15**（datasheet Table 2-9 / 2-10 的 AF7 列，p60-63）。前两个与 STM32F407 的 USART1_TX（PA9/PB6，AF7）**同号同脚**：GD32 的 USART0 就是 STM32 USART1 的岗位（G3 会讲这套错位编号），连 AF 号都没动。

**但第三个脚是 GD32 加的**。STM32F407 的 PA15 只有 JTDI / TIM2_CH1 / SPI1_NSS / SPI3_NSS，**没有 USART1_TX**（STM32F407 datasheet Table 9，p66）。同一张表看两遍，"大量重合"和"全部重合"的差别就在这种脚上。

> **所以纪律不能省**：拿 STM32 的 AF 表当 GD32 用，PA9/PB6 这种脚会碰巧对，PA15 这种脚会让你以为"GD32 没有"；反过来把 GD32 工程搬回 STM32，PA15 当 TX 用会**静默失效**（AF7 在 STM32 PA15 上是空位）。GD32 多出来的那几个串口（USART5~7，G3 讲）在 STM32F407 上更没有对应岗位，AF 号无从对照。迁移时的正确姿势永远是**按脚查表**，不是按记忆填号。

配置姿势照搬 S3"复用要成对"：CTL 写 10（复用模式）+ AFSEL 选号，缺一不可；只写 AFSEL 不改 CTL，等于章盖了门没开。

```c
/* GD32F4xx：PA8 复用 AF0（CK_OUT0），对照 S3 的 USART1_TX 配置样式 */
GPIOA_CTL    &= ~(3UL << (8 * 2));
GPIOA_CTL    |=  (2UL << (8 * 2));                  /* CTL[17:16] = 10，复用模式    */
GPIOA_AFSEL1 &= ~(0xFUL << 0);                       /* PA8 是 AFSEL1 的第 0 个 nibble */
GPIOA_AFSEL1 |=  (0x0UL << 0);                       /* AF0 = CK_OUT0                */
```

注意 PA8 属于 pin8~15，落在 **AFSEL1**（对应 STM32 的 AFRH），nibble 索引是 `pin & 7`，不是 pin 本身。S3 踩过的"PA9 是 AFRH 第 1 个 nibble"坑，在 GD32 原样存在，只是寄存器名换成 AFSEL1。

## 六、库函数对照：GD32 拆两步，STM32 一把抓

官方库的 GPIO 配置 API 两边思路不同：**STM32 SPL 一个结构体一把抓，GD32 拆成两个语义函数**：

| 语义 | STM32 SPL | GD32 V3.3.3（gd32f4xx_gpio.h:372-404） |
|---|---|---|
| 配模式 + 上下拉 | GPIO_Init（连同输出参数一把抓） | `gpio_mode_set(gpiox, mode, pupd, pin)` → 写 **CTL + PUD** |
| 配输出形态 + 速度 | 同上（同一个结构体） | `gpio_output_options_set(gpiox, otype, speed, pin)` → 写 **OMODE + OSPD** |
| 配复用号 | GPIO_PinAFConfig（单独调） | `gpio_af_set(gpiox, af, pin)` → 写 **AFSEL0/1** |
| 置位/复位/写 | GPIO_SetBits / ResetBits / WriteBit | gpio_bit_set / bit_reset / bit_write |
| 读输入/输出 | GPIO_ReadInputDataBit / ReadOutputDataBit | gpio_input_bit_get / gpio_output_bit_get |
| 翻转 | —（手写 ODR 翻转） | **gpio_bit_toggle / gpio_port_toggle**（走 TG） |
| 锁定 | GPIO_LockPin | gpio_pin_lock |

GD32 的拆分有它的道理：**纯输入引脚根本不需要输出形态和速度**，`gpio_mode_set` 一行就配完（CTL+PUD），不碰 OMODE/OSPD；要输出了再调 `gpio_output_options_set`。STM32 的 GPIO_Init 结构体里 `GPIO_Speed/GPIO_OType` 对输入脚是"填了也白填"。对照记忆：**SPL 一把抓，GD32 按需分两次**，像点菜，套餐改单点。

剥开 `gpio_mode_set` 的实现（gd32f4xx_gpio.c，@10d02f4），骨架就是我们第四节的"先清后置"：

```c
/* 伪代码骨架（原文件逻辑意译） */
GPIO_CTL(gpiox) &= ~GPIO_MODE_MASK(pin);            /* 清 CTL 的两位格子   */
GPIO_CTL(gpiox) |=  GPIO_MODE_SET(pin, mode);       /* 写模式              */
GPIO_PUD(gpiox) &= ~GPIO_PUPD_MASK(pin);            /* 清 PUD              */
GPIO_PUD(gpiox) |=  GPIO_PUPD_SET(pin, pupd);       /* 写上下拉            */
```

这里一个字都没超出本章第四节：**库函数就是手写寄存器的 for 循环封装**。S3 第五节对 `GPIO_Init` 说过的话，对 GD32 原样成立。掩码/置位宏 `GPIO_MODE_SET(n, mode)`、`GPIO_MODE_MASK(n)` 就定义在 gd32f4xx_gpio.h:319-324。

## 记忆锚点

::: tip 一句话记住
**七大寄存器只换名：CTL/OMODE/OSPD/PUD/ISTAT/OCTL/BOP；基址使能全同款；GD32 多 BC 清零、TG 翻转两件兵器；编码一字不差，先清后置照旧；复用找 AFSEL0/1，nibble 算法同款。**
:::

**延伸**：GD32 AF 复用动画见 [G2 动画](/anim/gd32-af-mux.svg)；STM32 GPIO 对照见 [S3](../stm32/03-gpio.md)；指针操作寄存器在 [C2](../c/02-pointer.md) 详解。

## 实物实验

- **桌面点名（5 分钟）**：合上本文，对照 `.trellis/ref/gd32/gd32f4xx_gpio.h:52-63` 把 12 个寄存器的偏移从 0x00 默写到 0x2C，标出哪两个是 STM32 没有的。
- **翻译练习（10 分钟）**：打开 [S3 的 00-blink main.c](https://github.com/zhuguang-ZFG/STM32/blob/main/mcu/code/stm32/00-blink/main.c)，把每行 STM32 寄存器操作翻译成 GD32 版（PF6→PF6，MODER→CTL……），再翻回本文核对。
- **上板（待基准板）**：拿到 GD32F450 板后，用 TG 寄存器写最小 blink（`GPIOF_TG = 1UL<<6` 循环+延时），与 OCTL 读-改-写版对比，示波器上看边沿应完全一致；量 PF6 翻转频率还能顺手验证 G1 的 200MHz 时钟树（**待上板实测**）。

## 常见坑

1. **拿着 STM32 名字搜 GD32 文档**：搜 "MODER"“OTYPER” 永远搜不到：GD32 叫 CTL/OMODE。反向同理：看 GD32 例程里的 OCTL 别当成 STM32 的输出时钟配置（那是 RCC 的活）。
2. **以为 BOP 高 16 位不能用、非写 BC 不可**：两者都能清零（BOP 高 16 位、BC 低 16 位），官方库走 BC。但**置位只有 BOP 低 16 位**一条路，不存在"置位版 BC"。
3. **用 OCTL 读-改-写翻转**：GD32 有现成 TG 一条写搞定，还不用读：OCTL `^=` 的中断插队坑（S3 第二节）在 GD32 完全可以绕开。
4. **AF 写了 AFSEL 忘改 CTL**：CTL[1:0] 还是 00/01（输入/输出），外设接不进引脚：复用要成对（CTL=10 + AFSEL 选号），S3 的坑原样平移。
5. **速度档照抄 STM32 的"100MHz"**。GD32 第四档库里叫 `GPIO_OSPEED_MAX`，注释写 "more than 50MHz"；datasheet 的真名是 **IO_Speed = 200 MHz**（Table 4-28）。两边都不是 100MHz。照 STM32 的 100MHz 设计时序余量，在 GD32 上要么保守浪费、要么按错档算边沿。
6. **拿 PC13~PC15 / PI8 当普通高速脚**。这四个脚走 Power Switch 供电，输出模式**上限 2MHz**（datasheet 注 (3)）。配 200MHz 档也不会变快，只会让人以为"配了就有"。

## 短自测

1. 不看表默写：GD32 的七个核心 GPIO 寄存器（0x00~0x18）分别叫什么？对应 STM32 哪七个名字？
2. BC 和 BOP 高 16 位都能清零，那置位有几条路？走哪个寄存器？
3. STM32 里翻转一个引脚要几条指令？GD32 用哪个寄存器几条？各有什么隐患/优势？
4. PA11 要配复用功能，写 AFSEL0 还是 AFSEL1？nibble 索引怎么算？
5. GD32 的 GPIO_OSPEED_MAX（11）和 STM32F4 OSPEEDR 的 11 档（100MHz）有什么微妙差别？

<details><summary><b>参考答案（先自己想完再展开）</b></summary>
1. 0x00 CTL（↔MODER）、0x04 OMODE（↔OTYPER）、0x08 OSPD（↔OSPEEDR）、0x0C PUD（↔PUPDR）、0x10 ISTAT（↔IDR）、0x14 OCTL（↔ODR）、0x18 BOP（↔BSRR）。偏移、位宽、编码全同，只有名字换了（gd32f4xx_gpio.h:52-63）。
2. 置位只有**一条路**：BOP 低 16 位（BOP0~BOP15）。清零有两条路：BOP 高 16 位（CR0~CR15）或 BC 低 16 位，官方库 gpio_bit_reset 走 BC。不存在"独立置位寄存器"。
3. STM32 翻转要 ODR 读-改-写三条指令（ldr/eor/str），中间可被中断插队、丢状态；GD32 写 TG 对应脚位一条 str 原子完成，还不需要读，点灯循环连状态变量都省了。
4. PA11 属于 pin8~15，写 **AFSEL1**（对应 STM32 的 AFRH）；nibble 索引按 pin 对 8 取余（11 对 8 = 3），即 AFSEL1 的 bits[15:12]（第 3 个 nibble）。写成 bits[43:40] 或 pin 本身当索引是典型错。
5. STM32F4 的 11 档明确标 100MHz。GD32 的 LEVEL3 库里只叫 `GPIO_OSPEED_MAX`，注释写 "max speed more than 50MHz"，**库头文件不承诺数字**；但 datasheet Table 4-28 承诺了：**IO_Speed = 200 MHz**，并给出 200/170/130MHz（CL=10/30/50pF）三档上限。
   所以差别有两层：**库含糊 vs datasheet 明确**，以及**标称 200MHz vs STM32 的 100MHz**。迁移时别按 100MHz 设计时序余量，也别忘了 datasheet 注 (4) 的 168MHz 天花板。</details>

## 对照表：本章概念 → 仓库落点

| 本章说的 | 仓库里哪一行 |
|---|---|
| 12 个寄存器偏移点名（CTL 0x00 ~ TG 0x2C） | .trellis/ref/gd32/gd32f4xx_gpio.h:52-63（@10d02f4） |
| 模式/上下拉编码 0/1/2/3 与 0/1/2 | gd32f4xx_gpio.h:288-297 |
| 速度四档（第四档 MAX 标签） | gd32f4xx_gpio.h:336-345 |
| 速度四档的 datasheet 真名与按负载上限（2/25/50/**200** MHz；200/170/130MHz@10/30/50pF；168MHz 天花板） | GD32F407xx Datasheet Rev2.7 **Table 4-28**（p101，已核验） |
| PC13~PC15 / PI8 输出不得超 2MHz（Power Switch 供电） | 同上 datasheet 注 (3)（已核验） |
| USART0_TX = AF7，候选脚 PA9/PB6（同 STM32）+ PA15（GD32 独有，STM32F407 PA15 无 USART1_TX） | GD32 datasheet **§2.6.6 Table 2-9 / 2-10**（p60-63）↔ STM32F407 datasheet Table 9（p66-67），双边已核验 |
| 九张端口 AF 表（Port A~I，Table 2-9 ~ 2-17） | datasheet §2.6.6（p60-68，已核验） |
| 推挽/开漏编码 | gd32f4xx_gpio.h:331-332 |
| BOP 低 16 置位 + 高 16 复位布局 | gd32f4xx_gpio.h:174-206 |
| BC 独立清零 / TG 硬件翻转位定义 | gd32f4xx_gpio.h:247-263 / :265-281 |
| AFSEL0/1 每脚 4 位 + GPIO_AF_0~15 | gd32f4xx_gpio.h:227-245 / :353-368 |
| GPIO 基址 0x40020000、GPIOF +0x1400 | gd32f4xx.h:313,341；gd32f4xx_gpio.h:41-49 |
| RCU_AHB1EN bit0~8（GPIOA~I） | gd32f4xx_rcu.h:53,209-217 |
| 库函数 API 清单（mode_set/output_options_set/af_set/toggle） | gd32f4xx_gpio.h:372-404 |
| PA8 AF0 配 CK_OUT0 实例 | example_ckout_main.c:135（G1 第五节引用） |
| STM32 侧对照锚（MODER~AFRH 偏移与 PF6 流程） | [code/stm32/00-blink/main.c](https://github.com/zhuguang-ZFG/STM32/blob/main/mcu/code/stm32/00-blink/main.c)；RM0090 §8.4 |

## 你做到了

- GD32F4xx 的 GPIO 从"又要学一套"变成"改七个宏名"，S3 的位级理解全额平移；
- 知道 GD32 的真增强在哪（BC/TG），点灯翻转从此一条指令；
- 会查 `.trellis/ref/gd32/gd32f4xx_gpio.h` 核对任何寄存器事实，为 G3 的 USART 对照备好方法。

平移是全额：编码一字不差，上下拉、推挽开漏全照搬；那件兵器叫 TG，硬件翻转，一条 str 搞定，旁边还站着管独立清零的 BC，STM32F4 压根没这待遇。

<div class="achievement">
✅ 下一站：<a href="03-usart.html">G3 USART 增强点</a>：gd32f4xx_usart.h 里比出的差异清单，接着把串口打印跑通。
</div>
