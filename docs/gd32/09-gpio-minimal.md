---
title: V4 GPIO 最小系统
status: done
difficulty: 2
minutes: 55
---

# V4 GPIO 最小系统

> 🎯 [G2](02-gpio-af.md) 带来过好消息：GD32F4xx 的 GPIO 与 STM32F4 七张表逐字相同，只换名字。到了 VF103，好消息一条不成立——它的 GPIO 是 F1 血统：两张配置表每脚 4 位、复用走 AFIO 重映射、时钟挂在 APB2 不在 AHB1。判据不用猜，就在 `gd32vf103.h` 的三行宏里。本章用 V0 的启动、V2 的 108M、V3 的 mtime 延时，拼出第一个完整的 RISC-V 点灯闭环，V 篇到此收官。

## 本章精髓

1. **血统鉴定看头文件**：`gd32vf103.h` 给了 `AFIO_BASE = APB2+0x0000`（:219）：AFIO（复用重映射机关）是 F1 时代的活化石，F4xx 早已用每脚 4 位的 AFSEL0/1 替掉它（[G2 第五节](02-gpio-af.md)）。**有 AFIO 就是 F1 家**：VF103 的 GPIO 因此是 CTL0/CTL1 两张配置表、每脚 4 位（MD+CTL 合体），不是 G2 那套七寄存器家族。
2. **数据四剑客换编制不换岗**：ISTAT/OCTL/BOP/BC 对应 [S3](../stm32/03-gpio.md) 的 IDR/ODR/BSRR：BOP 低 16 位置位、高 16 位复位，写 0 无影响；BC 是独立清零寄存器（STM32F407 没有，得用 BSRR 高 16 位绕）；"读-改-写暗伤"与"原子写"的教训（S3 第二节）原样平移。
3. **五步闭环即收官**：开时钟（RCU_APB2EN.PAEN = bit2，注意在 APB2）→ CTL0 四位配置 → OCTL 设初值 → BOP/BC 原子翻转 → mtime delay_ms（[V3](08-mtime-delay.md)）：V0~V3 的产出在此合体烧录，点灯即毕业。

## 先修

- [V0 RISC-V 工具链与启动文件](05-riscv-toolchain.md)（启动文件、链接脚本、Makefile 标志）；
- [V1 Bumblebee 内核与 CLIC 中断](06-clic-irq.md)（AFIO/EXTI 的 F1 血统与 V 篇全局观）；
- [V2 RCU 与 108MHz](07-rcu-108m.md)（SystemInit 默认拉到 108M 档）；
- [V3 MTIME 与裸机延时](08-mtime-delay.md)（delay_ms 的 mtime 实现）。

## 先跑起来（10 分钟 quick win）

拿你板子的原理图（GD32VF103 板各家 LED 引脚不同，Sipeed、GigaDevice、自制板各归各；仓库基准板指定后本节接线回填），查出 LED 的端口、脚号与极性（共阳低亮/共阴高亮）。然后做两笔账：

```text
① 核基址：GPIO_BASE = APB2 + 0x0800 = 0x40010000 + 0x0800 = 0x40010800（gd32vf103.h:201,221）
② 算配置：推挽输出 2MHz → MD=10（2MHz 档）、CTL=00（推挽）→ 四位合体 0b1000
   落位：CTL0 的 [pin*4+3 : pin*4] = 0b1000；掩码 0xF、移位 pin*4（S3 是 0x3、pin*2——别混）
```

十分钟后你写的每行代码都有账可查：本章 main.c 就是这两笔账的展开。

先押个家谱：VF103 的 GPIO，是 G2 那套七寄存器家族原班人马，还是另认祖宗换了编制？判据就藏在头文件的一个符号里，押完翻 gd32vf103.h 找它。

## 动画：RISC-V 点灯闭环

开时钟 → CTL0 四位配置 → OCTL 设初值 → BOP/BC 原子翻转 → mtime 延时，五步装配，V0~V4 的产出在此合体成第一个完整的 RISC-V 点灯闭环。

![RISC-V 点灯闭环：五步装配](/anim/riscv-blink-closed.svg)

## 小节结构

| 小节 | 内容 |
|---|---|
| 一、血统鉴定 | AFIO 判据；S3/G2/V4 三代 GPIO 对照表 |
| 二、四位一坑 | CTL0/CTL1 的 MD+CTL 编码与 pin×4 落位 |
| 三、数据四剑客 | ISTAT/OCTL/BOP/BC 对照 S3；BC 的直路价值 |
| 四、点灯五步 | 完整 main.c：时钟→CTL→OCTL→BOP/BC→mtime 延时 |
| 五、工程拼图 | 启动+链接+Makefile+main 组成可烧工程；验收三件事 |
| 六、收官对账 | V0~V4 迁移清单总表：ARM 世界的五件替身 |

## 一、血统鉴定：有 AFIO 就是 F1 家

先看判据，再谈结论。`gd32vf103.h` 的外设地图（:201-227）里躺着三行：

```c
#define AFIO_BASE   (APB2_BUS_BASE + 0x00000000U)   /* :219 复用重映射机关 */
#define EXTI_BASE   (APB2_BUS_BASE + 0x00000400U)   /* :220 */
#define GPIO_BASE   (APB2_BUS_BASE + 0x00000800U)   /* :221 → 0x40010800 */
```

AFIO 是"复用重映射"的 F1 制机关：F1 家族的复用功能只有固定几个引脚候选，靠 AFIO 的选择寄存器"选门"；F4xx 起改为每脚 4 位的 AFSEL 编号自由 mux（[G2 第五节](02-gpio-af.md)）。**AFIO_BASE 的存在本身就是血统证明**：F4xx 头文件里没有这个外设。[V1 第三节](06-clic-irq.md)用 EXTI/AFIO 基址验过"外设脱胎自 GD32F1"，GPIO 是同一血统的下一块拼图。

三代对照一次摆开：

| 维度 | STM32F407（[S3](../stm32/03-gpio.md)） | GD32F4xx（[G2](02-gpio-af.md)） | GD32VF103（本章） |
|---|---|---|---|
| 配置寄存器 | MODER/OTYPER/OSPEEDR/PUPDR 四张 | 同四张改名 CTL/OMODE/OSPD/PUD | **CTL0/CTL1 两张，每脚 4 位** |
| 每脚位宽 | 2+1+2+2 分居四表 | 同左 | **4 位一张表统管（MD+CTL）** |
| 复用 | AFRL/AFRH 每脚 4 位编号 | AFSEL0/1 同款 | **AFIO 选门 + CTL 选复用形态** |
| 时钟总线 | RCC_AHB1ENR bit0~8 | RCU_AHB1EN bit0~8 | **RCU_APB2EN bit2~6（PA~PE）** |
| 数据寄存器 | IDR/ODR/BSRR | ISTAT/OCTL/BOP/BC/TG | ISTAT/OCTL/BOP/BC |
| GPIO 基址 | 0x40020000（GPIOA） | 0x40020000 | **0x40010800——与 STM32F103 同址** |

最后一行再补一记铁证：0x40010800 恰是 STM32F103 GPIOA 的老地址，端口步进 0x400（A~E 依次 +0x400，与 F103 完全同址；逐口基址已核验：GPIOA=GPIO_BASE+0，B~E 各 +0x400，gd32vf103_gpio.h:41-45）。[V2](07-rcu-108m.md) 的 RCU 跟 F1 同门牌、本章 GPIO 也跟 F1 同门牌，"外设层像 F1、内核是 RISC-V"这个混血判断，处处有地址背书。

## 二、四位一坑：CTL0/CTL1 的 MD+CTL 编码

F1 血统把 S3 的四张表压成一张：每脚 4 位，低 2 位是 **MD**（速度/方向），高 2 位是 **CTL**（输入/输出形态）。CTL0（偏移 0x00）管脚 0~7，CTL1（偏移 0x04）管脚 8~15。四位语义已核验（gd32vf103_gpio.h:53-104：每脚 MD 占低 2 位、CTL 占高 2 位，逐位编码与 F1 惯例一致）：

| MD | 含义 | CTL | 输入时 | 输出/复用时 |
|---|---|---|---|---|
| 00 | 输入模式 | 00/01/10 | 模拟/浮空/上拉下拉 | —— |
| 01 | 输出 10MHz | 00/01/10/11 | —— | 推挽/开漏/复用推挽/复用开漏 |
| 10 | 输出 2MHz | 同上 | —— | 同上 |
| 11 | 输出 50MHz | 同上 | —— | 同上 |

点灯用"推挽输出 2MHz"：MD=10、CTL=00 → 四位 `1000`。落位两步走，S3 的"先清后置"纪律原样有效，但**掩码和移位都换挡**：

```c
/* S3（F407，每脚 2 位）                     本章（VF103，每脚 4 位） */
GPIOx_MODER &= ~(3UL << (pin * 2U));      GPIO_CTL0(x) &= ~(0xFUL << (pin * 4U));  /* 掩 0xF 不是 0x3 */
GPIOx_MODER |=  (1UL << (pin * 2U));      GPIO_CTL0(x) |=  (0x8UL << (pin * 4U));  /* 四位合体 0b1000 */
```

照搬 S3 的 0x3 掩码会留下两个旧位，是"模式改不干净"的暗病。配复用脚时尤其致命：残留位能把推挽变开漏，信号半死不活。

要上拉/下拉输入：MD=00、CTL=10，再写 OCTL 对应位。F1 血统的"输出锁存器"兼任上拉/下拉选择（写 1 上拉、写 0 下拉），这是与 S3 PUPDR 独立寄存器的又一个结构差异（已按用户手册实证：UM §7.5 配置表 Input pull-up=CTL10+OCTL1、pull-down=CTL10+OCTL0）。复用输出（如 USART_TX）：MD 选速度、CTL 选"复用推挽"，重映射候选脚多时还要动 AFIO：三件套见 [V1 第七节](06-clic-irq.md) 第 3、4 步。

## 三、数据四剑客：ISTAT/OCTL/BOP/BC

| 岗位 | STM32F407（[S3](../stm32/03-gpio.md)） | VF103（偏移已核验，gd32vf103_gpio.h:55-58） | 备注 |
|---|---|---|---|
| 看电平 | IDR（只读） | **ISTAT**（+0x08） | 输入的耳朵 |
| 写电平 | ODR（读写） | **OCTL**（+0x0C） | 读-改-写暗伤同 S3 第二节 |
| 原子置位/复位 | BSRR（低置高复） | **BOP**（+0x10） | 低 16 置位、高 16 复位，写 0 无影响 |
| 独立清零 | ——（用 BSRR 高 16 位绕） | **BC**（+0x14） | F407 要 +16 挪半档，这里直路 |

四条纪律全部从 S3 平移，只有第四条是"减负"：

- **OCTL 的暗伤**：`OCTL 或上一个值`是"读-改-写"三条指令，中断插进读与写之间就冲掉别人的改动，S3 第二节的翻车现场在 RISC-V 上一字不差。
- **BOP 只能纯赋值**：读回恒 0、写 0 无影响：对它做读-改-写等于把自己的位全清空（S3 坑 5 的 F1 版）。
- **BC 是 GD32 家的直路**：F407 想清一个脚得往 BSRR 高 16 位写（pin+16 半档）；VF103 直接把 1 左移 pin 位写 BC，不用挪半档（[G2 第三节](02-gpio-af.md) 在 F4xx 上已点名这件兵器）。
- **没有 TG**：G2 介绍的硬件翻转寄存器在 VF103 上没有（头文件实证：寄存器列表只有 CTL0/1、ISTAT、OCTL、BOP、BC、LOCK 六枚，无 TG，gd32vf103_gpio.h:53-59），翻转老老实实 BOP/BC 各写一次。

## 四、点灯五步：完整 main.c

五步闭环，每一行都标了出处（LED 接线以你板子的原理图为准；仓库基准板指定后本节回填）：

```c
#include <stdint.h>

/* ---------- 板级接线：查原理图回填（基准板指定后更新） ---------- */
#define LED_PORT_BASE   0x40010800U     /* 示例 GPIOA；B~E 依次 +0x400 */
#define LED_PIN         1U              /* 示例 PA1 */

/* ---------- RCU（gd32vf103.h:226；gd32vf103_rcu.h:52,165） ---------- */
#define RCU_BASE        0x40021000U
#define RCU_APB2EN      (*(volatile uint32_t *)(RCU_BASE + 0x18U))
#define RCU_APB2EN_PAEN (1UL << 2)      /* PA 时钟位 bit2；PB~PE 是 bit3~6 */

/* ---------- GPIO（偏移已核验，gd32vf103_gpio.h:53-58） ---------- */
#define GPIO_CTL0(x)    (*(volatile uint32_t *)((x) + 0x00U))
#define GPIO_OCTL(x)    (*(volatile uint32_t *)((x) + 0x0CU))
#define GPIO_BOP(x)     (*(volatile uint32_t *)((x) + 0x10U))
#define GPIO_BC(x)      (*(volatile uint32_t *)((x) + 0x14U))

/* ---------- mtime 延时（V3 第四节原样搬运；基址按官方库实证更新） ---------- */
#define CLINT_BASE      0xD1000000U      /* GD32VF103 TIMER 域（n200_timer.h:29） */
#define MTIME_LO        (*(volatile uint32_t *)(CLINT_BASE + 0x0U))
#define MTIME_HI        (*(volatile uint32_t *)(CLINT_BASE + 0x4U))
extern uint32_t SystemCoreClock;        /* V2：SystemInit 后为 108000000 */

static uint64_t mtime_read(void)
{
    uint32_t hi, lo;
    do { hi = MTIME_HI; lo = MTIME_LO; } while (hi != MTIME_HI);
    return ((uint64_t)hi << 32) | lo;
}

static void delay_ms(uint32_t ms)
{
    uint64_t start = mtime_read();
    uint64_t ticks = (uint64_t)ms * (SystemCoreClock / 4U / 1000U);
    while ((mtime_read() - start) < ticks) { }
}

#define CTL_OUT_PP_2M   0x8UL           /* MD=10（2MHz）+ CTL=00（推挽） */

int main(void)
{
    /* 启动文件已 call SystemInit：时钟在 108M 档（V0 第六节） */

    RCU_APB2EN |= RCU_APB2EN_PAEN;                                 /* ① 时钟先行 */
    GPIO_CTL0(LED_PORT_BASE) &= ~(0xFUL << (LED_PIN * 4U));         /* ② 先清四位 */
    GPIO_CTL0(LED_PORT_BASE) |=  (CTL_OUT_PP_2M << (LED_PIN * 4U));
    GPIO_OCTL(LED_PORT_BASE) |=  (1UL << LED_PIN);                  /* ③ 初值：先置高（按极性定亮灭） */

    while (1) {
        GPIO_BOP(LED_PORT_BASE) = (1UL << LED_PIN);                 /* ④ 原子置位 */
        delay_ms(500);
        GPIO_BC(LED_PORT_BASE)  = (1UL << LED_PIN);                 /*    原子清零；⑤ mtime 延时 */
        delay_ms(500);
    }
}
```

五步对号：**① 开时钟 → ② CTL0 四位配置 → ③ OCTL 初值 → ④ BOP/BC 原子翻转 → ⑤ mtime delay**。三点说明：

- **时钟位换总线了**：S3/G2 的 GPIO 时钟在 AHB1ENR/RCU_AHB1EN，VF103 在 **RCU_APB2EN** bit2~6（PA~PE 逐一对应，gd32vf103_rcu.h:165-169），"外设像 F1"的又一处落地（F1 的 GPIO 时钟就在 APB2）。照搬 F407 的 AHB1 肌肉记忆，连寄存器都摸错。
- **④ 的极性由硬件定**：共阳灯低电平亮：初值给高（灭），BOP 置高是"灭"、BC 清零才是"亮"；共阴反过来。不看原理图抄极性，程序对灯不亮。
- **⑤ 的时间观来自 V3**：mtime 27MHz、1ms=27000 tick，delay 精度受整 tick 限制，500ms 误差在微秒级，肉眼与逻辑分析仪都无感。

## 五、工程拼图：四份产出合成一个能烧的工程

| 组成 | 出处 | 作用 |
|---|---|---|
| `start_gd32vf103.S` | [V0 第二/四节](05-riscv-toolchain.md) | 设栈、搬 .data、清 .bss、call SystemInit、call main |
| `gcc_gd32vf103.ld` | [V0 第五节](05-riscv-toolchain.md) | FLASH 0x08000000 / RAM 0x20000000、`__stack_top` |
| `system_gd32vf103.c` | 官方库（[V2](07-rcu-108m.md)） | SystemInit 把 RCU 拉到 108M 档 |
| `main.c` | 本章第四节 | 点灯五步 + V3 延时 |
| Makefile 标志 | [V0 第一节](05-riscv-toolchain.md) | `-march=rv32imac -mabi=ilp32`（无 FPU 标志——RV32IMAC 没有 F） |

烧录与调试沿用 V0 实验的 GDB 流程（调试后端按你的板卡定）。上电验收三件事：

1. **灯闪**：1 秒周期（500ms 亮 500ms 灭），闭环 OK；
2. **GDB 读 SCSS**：RCU_CFG0 bits[2:3] 应为 2（PLL，[V2 实物实验](07-rcu-108m.md)），时钟真在 108M；
3. **mtime 差值**：连续读差反推约 27MHz（[V3 实物实验](08-mtime-delay.md)），时基真的在跑。

三条全中，说明 V0~V4 没有一环是"抄来的"：每章的账都在你的板上对上了。

## 六、收官对账：ARM 世界的五件替身

V 篇五章，替你把 Cortex-M 的"标配"换成了 RISC-V 的对应物：

| ARM 世界的件 | RISC-V 替身 | 章 |
|---|---|---|
| arm-none-eabi 工具链 + FPU 四标志 | riscv-none-elf + march/mabi 两标志 | [V0](05-riscv-toolchain.md) |
| 复位硬件两读、向量表第 0 项栈顶 | reset_handler 显式设栈，无向量表 | [V0](05-riscv-toolchain.md) |
| NVIC：IRQn+16 槽号、PRIGROUP 分组、大向量表 | ECLIC：索引直用、level+priority 两维、向量直跳 | [V1](06-clic-irq.md) |
| RCC：PLL 大 VCO、电压三件套、提频六步 | RCU：PREDV0×PLLMF 两步走、4MHz 家族、提频四步 | [V2](07-rcu-108m.md) |
| SysTick：24 位倒数、LOAD 自动重装、COUNTFLAG | mtime：64 位顺数、软件续约、比大小（主频/4） | [V3](08-mtime-delay.md) |
| GPIO：MODER 七表、AHB1 时钟、AFSEL 编号 | GPIO：CTL0/CTL1 四位表、APB2 时钟、AFIO 选门 | V4（本章） |

外设层与 F1 同源的"混血"红利贯穿全程：EXTI 配置、ISR 清挂起、GPIO 编码，凡是 F1 有的几乎照搬；要重学的只有内核三件：启动方式、中断控制器、时基。**这就是"学透一颗再举一反三"的实战版：先 STM32、再 GD32F4xx、最后 RISC-V，每一步都只学"差的那一点"。**

## 记忆锚点

::: tip 一句话记住
**有 AFIO 就是 F1 家：两张表每脚四位，掩 0xF 移 pin×4；时钟在 APB2 bit2~6 不在 AHB1；数据四剑客 ISTAT/OCTL/BOP/BC，BC 清脚不用 +16；五步闭环：时钟、CTL、OCTL、BOP/BC、mtime delay。**
:::

**延伸**：RISC-V 点灯闭环动画见 [V4 动画](/anim/riscv-blink-closed.svg)；STM32 GPIO 对照见 [S3](../stm32/03-gpio.md)；MTIME 延时在 [V3](08-mtime-delay.md) 展开。

## 实物实验

- **基础**：跑通五步闭环，LED 1 秒周期翻转；逻辑分析仪量高电平段，应为 500ms 整（整 tick 误差内）。
- **换档联动**：[V2](07-rcu-108m.md) 切 72M 档重编译，delay 用 SystemCoreClock 现算，灯仍应 500ms 翻转；若变慢，查 V3 坑 5（常数写死）。
- **输入侧复刻**：LED 脚改输入浮空/上拉（CTL0 改 MD=00、CTL=01/10），GDB 读 ISTAT，杜邦线拉地看 1 变 0，[S3 第六节](../stm32/03-gpio.md)的实验在 RISC-V 上再走一遍。
- **七色扩展**：板上有 RGB 三灯的，三脚各配一段 CTL0/CTL1，主循环按位图轮流点亮，顺手练"多位配置不串位"。

## 常见坑

1. **忘开 RCU_APB2EN.PAEN**：症状与 S3 一模一样（写入无效、读回全 0），但解法换门牌：bit2~6 对应 PA~PE（gd32vf103_rcu.h:165-169），且寄存器是 **APB2EN** 不是 AHB1EN。第一大坑跨架构永恒，坑的坐标每颗芯都要重查。
2. **照搬 S3 的 0x3 掩码 / pin×2 移位**：VF103 每脚 4 位：掩 0xF、移 pin×4。掩浅了留旧位，配出的"半新半旧"模式是间歇性怪病的温床。
3. **OCTL 读-改-写翻转 + 对 BOP/BC 也读-改-写**：前者是 S3 第二节的暗伤（中断插队丢状态），后者更隐蔽：BOP 读回恒 0，读-改-写等于清空自己。原子寄存器只配纯赋值。
4. **极性与基址拍脑袋**：共阳/共阴不查原理图就抄亮灭逻辑；端口基址步进记错（B 口是 +0x400，不是 +0x100）。
5. **复用三件套缺一件**：F1 血统的复用 = CTL 选"复用推挽/开漏" + AFIO_EXTISSx 选门 + RCU_APB2EN.AFEN（bit0）开 AFIO 时钟，缺一件外设就哑（[V1 第七节](06-clic-irq.md)）。

## 短自测

**1. 给出 VF103 GPIO 是 F1 血统的头文件级判据，并说出它带来的两处结构差异。**

<details><summary>看答案</summary>

`gd32vf103.h` 给了 AFIO_BASE = APB2+0x0000（:219）：AFIO 是 F1 制的复用重映射机关，F4xx 没有（F4xx 用每脚 4 位的 AFSEL0/1 替掉，见 G2 第五节）。有 AFIO 就是 F1 家。两处结构差异：① 配置从四张表（MODER 家族）变两张表 CTL0/CTL1、每脚 4 位（MD+CTL）；② 复用从"AFSEL 编号自由 mux"变"AFIO 选门 + CTL 选复用形态"。附带证据：GPIO 基址 0x40010800 与 STM32F103 的 GPIOA 同址。

</details>

**2. PA1 配"推挽输出 2MHz"：CTL0 的目标 32 位值是多少？写出掩码与移位。**

<details><summary>看答案</summary>

MD=10（2MHz 输出）、CTL=00（推挽）→ 四位合体 0b1000 = 0x8。PA1 在 CTL0 占 bits[7:4]：先把该四段清零（掩码 0xF 左移 4 位后取反相与），再或上 0x8 左移 4 位，目标段值 0x00000080。注意每脚 4 位：掩 0xF、移 pin×4（S3 是 0x3、pin×2）。

</details>

**3. "清零一个引脚"在 STM32F407 与 VF103 上各怎么写？BC 的价值是什么？**

<details><summary>看答案</summary>

F407 没有独立清零寄存器，用 BSRR 高 16 位复位区：把 1 左移 (pin+16) 位后写入。VF103 有 BC（GD32 家兵器，F4xx 同款见 G2 第三节）：把 1 左移 pin 位直接写 GPIO_BC，不用 +16 挪半档。两者都是纯赋值原子写、写 0 无影响。

</details>

**4. 以 PA 口为例：点灯五步的第一步写哪个寄存器的哪一位？依据在哪？**

<details><summary>看答案</summary>

写 RCU_APB2EN（RCU+0x18）的 bit2，PAEN。依据 gd32vf103_rcu.h:165（RCU_APB2EN_PAEN = BIT(2)），bit3~6 依次对应 PB~PE。注意 GPIO 时钟在 APB2 不在 AHB1（F1 血统），别用 F407 的 AHB1ENR bit5 肌肉记忆。

</details>

**5. 为什么说 V4 是"闭环"和"收官"？V0~V3 各贡献了哪个件？**

<details><summary>看答案</summary>

点灯需要"起得来、有时钟、有时间观、能动引脚"四件，正好对应 V0~V3 的产出：V0 给启动文件与链接脚本（程序起得来，SystemInit 被调起）；V2/SystemInit 给 108MHz 档（时钟）；V3 给 mtime 延时（时间观）；V4 本章给 GPIO 五步（动引脚）。合起来是第一个能从上电跑到现象的完整 RISC-V 工程，所以是闭环；V 篇"从工具链到点灯"的迁移故事在此讲完，所以是收官。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 落点 |
|---|---|
| AFIO/EXTI/GPIO 基址（F1 血统判据） | gd32vf103.h:219-221 |
| APB2_BUS_BASE = 0x40010000 | gd32vf103.h:201 |
| GPIO 时钟使能 PA~PE = APB2EN bit2~6 | gd32vf103_rcu.h:165-169 |
| AFEN = APB2EN bit0 | gd32vf103_rcu.h:164 |
| RCU 基址 0x40021000、APB2EN 偏移 0x18 | gd32vf103.h:226；gd32vf103_rcu.h:52 |
| CTL0/CTL1/ISTAT/OCTL/BOP/BC 偏移与四位编码 | gd32vf103_gpio.h:53-104（已核验） |
| 端口基址步进 0x400、逐口地址 | gd32vf103_gpio.h:41-45（已核验，与 F103 同址） |
| 读-改-写暗伤与 BSRR 纪律 | [S3 第二节](../stm32/03-gpio.md) |
| BOP/BC/TG 与 F4xx 对照 | [G2 第一/三节](02-gpio-af.md)；VF103 无 TG 已实证（寄存器列表无 TG 项） |
| mtime 延时实现 | [V3 第四节](08-mtime-delay.md) |
| 启动文件/链接脚本/Makefile 标志 | [V0](05-riscv-toolchain.md) |
| SystemInit 默认 108M 档 | [V2 第二节](07-rcu-108m.md)；system_gd32vf103.c:62 |

## 你做到了

- 第一个完整的 RISC-V 工程从你手里跑起来：启动、时钟、时基、GPIO 四环都验过账；
- "外设像 F1、内核是 RISC-V"的混血地图刻进脑子，以后看任何 F1 兼容芯，知道哪部分照搬、哪部分重学；
- V 篇毕业：从 arm-none-eabi 到 riscv-none-elf，你完成了一次架构迁移的全流程演练。

家谱是 F1：AFIO_BASE 还钉在 APB2 头上，有 AFIO 就是 F1 家；于是 CTL0/CTL1 两张配置表每脚 4 位，掩码 0xF、移位 pin*4，别拿 S3 的 0x3、pin*2 去套；数据四剑客 ISTAT/OCTL/BOP/BC 换编制不换岗，BC 独立清零是 STM32F407 没有的待遇。

<div class="achievement">
✅ <b>V 篇收官</b>。下一站：<a href="../lab/index.html">实验中心</a>把闭环上板实测；或直奔 <a href="../rtos/index.html">RTOS 篇</a>：看 SysTick 的 tick 到了 RISC-V 怎么落进 mtimecmp。
</div>
