---
title: V1 Bumblebee 内核与 CLIC 中断
status: done
difficulty: 3
minutes: 35
---

# V1 Bumblebee 内核与 CLIC 中断

> 🎯 同样是"按键打断 CPU"，Cortex-M4 走 NVIC → ISER → IPR → 向量槽 22；GD32VF103 走 ECLIC → clicintie → level+priority → 向量直跳。没有 NVIC、没有 SysTick、没有 `SCB->VTOR`、没有 PendSV——但中断照样嵌套、照样抢占。这一章用 [S4](../stm32/04-nvic-exti.md) 的六步清单当尺子，量出 RISC-V 的中断世界差在哪、又奇巧地神似在哪。

## 本章精髓

1. **中断控制器换名换架构**：**ECLIC**（Enhanced Core-Level Interrupt Controller，Bumblebee 内核私有，Nuclei 与 Andes 联合开发）取代 ARM 的 NVIC。RISC-V 标准的 software / timer / external 三类中断它都管，外部中断源数交给芯片定（GD32VF103 在 `gd32vf103.h` 里用 `CLIC_INT_*` 与 `*_IRQn` 编号）。
2. **优先级变成两维**：**level（抢占级，最多 16 级，决定能否打断别人）+ priority（同级排序，最多 16 级）**。不是 ARM 那套"4 位单一优先级 + PRIGROUP 切分组 + 0x5FA 钥匙"。
3. **"向量"换语义**：ARM 是"向量表第 N 项放 ISR 地址，硬件读表跳转"；ECLIC 是"每个中断有 shv 位，置 1 即**向量直跳**到该中断专属入口，置 0 则进公共入口再软件分发"，省了一张大表，但每个要向量的中断都得显式配入口。

## 先修

- [V0 RISC-V 工具链与启动](05-riscv-toolchain.md)（知道复位序列与启动文件）；
- [S4 NVIC 与 EXTI](../stm32/04-nvic-exti.md)（六步清单与三层链路，本章的对照锚点）。

## 先跑起来（10 分钟 quick win）

在 GD32VF103 官方固件库的 `gd32vf103.h` 里翻中断号（`findstr /n "CLIC_INT  _IRQn" gd32vf103.h`），本章骨架就在这五行：

```text
101:     CLIC_INT_SFT                 = 3,       /*!< Software interrupt */
102:     CLIC_INT_TMR                 = 7,       /*!< CPU Timer interrupt */
104:     CLIC_INT_PMOVI               = 18,      /*!< Performance Monitor */
113:     EXTI0_IRQn                   = 25,      /*!< EXTI line 0 interrupts */
144:     USART0_IRQn                  = 56,      /*!< USART0 interrupt */
171:     ECLIC_NUM_INTERRUPTS                    /* 中断总数哨兵 */
```

读完本章再回看这五行，每个编号你都能讲出它与 ARM `IRQn` 的区别。

先押两扇门：硬件读表跳转的老剧情，这边还演不演？每个中断名下那位 shv，置 1 与置 0 各进哪扇门、谁在门口分发？ARM 那把 0x5FA 钥匙，这边还认不认？

## 动画：ECLIC 两维优先级

level 决定能否打断别人（抢占），priority 决定同 level 内谁先响应（排序）。两维配合完成中断嵌套与同级排序，无需 ARM 的 PRIGROUP 分组钥匙。

![ECLIC 两维优先级：level 定抢占，priority 定序](/anim/riscv-clic-priority.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、内核换魂 | Cortex-M4 → Bumblebee RV32IMAC，少了什么 | 配置 |
| 二、ECLIC 取代 NVIC | 增强版 CLIC 的职责、16 level + 16 priority、向量/非向量、尾链、NMI | 配置 |
| 三、中断号地图 | CLIC_INT_* / *_IRQn 与 ARM IRQn+16 的差异 | 配置 |
| 四、两维优先级 | level 抢占 + priority 同级 vs ARM 单一优先级 + PRIGROUP | 配置 |
| 五、向量直跳 | shv 模式与 ARM 向量表的机制差异 | 代码分析 |
| 六、MTIME 不是 SysTick | 内存映射 mtime/mtimecmp、mtime_toggle_a 频率 | 配置 |
| 七、对照落地 | 配通 EXTI0 的步骤与 S4 六步逐条对比 | 配置 |

## 一、内核换魂：Cortex-M4 → Bumblebee RV32IMAC

GD32VF103 把 ARM Cortex-M4 换成了 Nuclei/Andes 联合定制的 **Bumblebee** 内核。先把"少了什么"一次列清（凭证来自 Bumblebee 处理器内核简明手册 §1.1 / §2.4 / §2.6 / §2.13）：

| 维度 | Cortex-M4 (STM32F407) | Bumblebee (GD32VF103) | 凭证 |
|---|---|---|---|
| ISA | ARMv7E-M (Thumb-2) | RV32IMAC | 手册 §1.1 |
| 流水线 | 3 级 | 2 级可变 + 简单分支预测 + 预取 2 条 | 手册 §1.1 |
| 特权模式 | Handler/Thread + 特权/非特权 | Machine / User | 手册 §2.4 |
| 中断控制器 | NVIC | **ECLIC** | 手册 §1.1 / §2.6 |
| 内核定时器 | SysTick（24 位递减） | **MTIME**（64 位递增，内存映射） | 手册 §2.13 |
| 向量表重定位 | `SCB->VTOR` | 无 SCB、无 VTOR；ECLIC 自管向量 | — |
| PendSV | 有（RTOS 上下文切换用） | 无 | — |
| FPU | 有（CP10/CP11） | 无（IMAC 无 F/D） | [V0 第三节](05-riscv-toolchain.md) |
| 复位两读 | 硬件读 0x0 / 0x4 | 无 | [V0 第四节](05-riscv-toolchain.md) |
| PMP | 有（可选） | 无 | 手册 §2.7 |

**少了 NVIC、SysTick、`SCB->VTOR`、PendSV：这四样是 Cortex-M 内核的"标配"，RISC-V 一个都没有。** 但中断该有的能力（嵌套、抢占、向量、NMI）ECLIC 全给，只是实现的姿势不同。本章就是把这"不同"逐项讲清。

## 二、ECLIC 取代 NVIC：增强版 CLIC 的职责

ECLIC 是 Bumblebee 核的私有外设（与 DEBUG、TIMER 并列在 Core 层级下），通过内存地址访问（手册 §2.6）。它的职责（手册 §1.1 ECLIC 条目）：

- 管 RISC-V 标准三类中断：**software / timer / external**；
- 外部中断源数交给芯片定（GD32VF103 见 `gd32vf103.h` 的 `IRQn_Type`）；
- **最多 16 级 level + 16 级 priority**，软件可动态改；
- 基于 level 的抢占；
- 快速向量中断处理（fast vectored interrupt processing）；
- 快速中断尾链（tail-chaining）；
- 支持 NMI。

与 NVIC 的结构对照（ECLIC 寄存器精确偏移已由官方固件驱动实证，见 n200_eclic.h：基址 0xD2000000、cliccfg@0x0、clicintip@0x1000、clicintie@0x1001、clicintattr@0x1002、clicintctl@0x1003，每中断间隔 4 字节；这里讲结构与维度）：

| | ARM NVIC (S4) | ECLIC (V1) |
|---|---|---|
| 使能 | ISER/ICER 位图 | clicintie[i] 每中断一位 |
| 挂起 | ISPR/ICPR 位图 | clicintip[i] 每中断一位 |
| 优先级 | IPR 字节（高 4 位有效） | clicintctl[i]（level + priority 两维） |
| 触发沿 | 放在 EXTI 寄存器 | clicintattr[i]（属性寄存器收进来管） |
| 向量模式 | 向量表读表跳转 | clicintattr[i].shv（向量/非向量） |
| 全局配置 | SCB->AIRCR（PRIGROUP） | cliccfg（全局配置，如 nlbits） |

注意一个收敛点：ARM 把"触发沿"放在外设（EXTI RTSR/FTSR）、把"优先级"放在内核（NVIC IPR），两处分；ECLIC 把这些都收进来统一管：每个中断一组完整的属性（使能、挂起、触发沿、level/priority、向量模式）。

## 三、中断号地图：CLIC_INT_* 与 ARM IRQn+16 的差异

[S4 第四节](../stm32/04-nvic-exti.md)讲过：ARM 的"槽号 = IRQn + 16"（前 16 项是内核异常），外设中断从槽 16 开始排。RISC-V ECLIC **没有这个 +16 偏移**：中断号就是 ECLIC 的索引。

`gd32vf103.h:97-172` 的 `IRQn_Type` 给了全部编号（节选）：

```c
CLIC_INT_RESERVED = 0,       /* RISC-V reserved */
CLIC_INT_SFT      = 3,       /* Software interrupt       */
CLIC_INT_TMR      = 7,       /* CPU Timer interrupt      */
CLIC_INT_BWEI     = 17,      /* Bus Error interrupt      */
CLIC_INT_PMOVI    = 18,      /* Performance Monitor      */
WWDGT_IRQn   = 19,
EXTI0_IRQn   = 25,           /* EXTI line 0              */
EXTI5_9_IRQn = 42,           /* EXTI[9:5]                */
USART0_IRQn  = 56,
EXTI10_15_IRQn = 59,         /* EXTI[15:10]              */
USBFS_IRQn   = 86,
ECLIC_NUM_INTERRUPTS         /* 中断总数哨兵（gd32vf103.h:171） */
```

**关键差异**：EXTI0 在 STM32F407 是 `IRQn = 6`（槽 22，`stm32f407xx.h:83`），在 GD32VF103 是 `IRQn = 25`（ECLIC 索引 25，无 +16）。**同一条 EXTI0 线，两颗芯片的中断号差很远**，移植时不能照搬 S4 那张映射表。

> **【混血特征】** GD32VF103 的外设脱胎自 GD32F1（与 STM32F1 同源）：EXTI 在 `APB2 + 0x400 = 0x40010400`（`gd32vf103.h:220`），AFIO 在 `APB2 + 0x000 = 0x40010000`（`gd32vf103.h:219`），这俩地址与 STM32F1 完全一致。所以 GD32VF103 是"**外设像 F1、内核是 RISC-V**"的混血：第七节配 EXTI 时，外设层那几步几乎照搬 F1，只有控制器层（第 6 步）换成 ECLIC。

## 四、两维优先级：level + priority vs ARM 单一优先级

[S4 第三节](../stm32/04-nvic-exti.md)讲过 ARM 的优先级：4 位单一字段，PRIGROUP 把它切成"抢占 + 子"两份，写 AIRCR 必须带 0x5FA 钥匙。ECLIC **天生两维**，不用切分组：

| | ARM NVIC (S4) | ECLIC (V1) |
|---|---|---|
| 优先级位宽 | 4 位（高 4 位有效） | level 4 位 + priority 4 位（手册"up to 16"） |
| 抢占/子 切分 | PRIGROUP 切 4 位 | 天生两维，不用切 |
| 全局配置 | AIRCR + 0x5FA 钥匙 | cliccfg（如 nlbits 设 level 位数） |
| 调优先级 API | `NVIC_SetPriority(n, x)` | 写 clicintctl[n] 的 level + priority |
| 分组钥匙 | `0x5FA` | 无钥匙机制 |

- **level**（抢占级，最多 16 级）：决定"能不能打断别人"。高 level 抢断低 level，类似 ARM 的抢占优先级。
- **priority**（同级排序，最多 16 级）：决定"同 level 同时挂起时谁先上"，类似 ARM 的子优先级，但**没有打断能力**。

**推论一**：移植 RTOS 时"优先级数值没变、行为全变"的灵异事件（S4 3.2 讲的 PRIGROUP 尺子换了）在 RISC-V 上不会发生：没有"分组尺子"可换。但 RTOS 仍要求"全部 level 给抢占"这类约定，对应到 cliccfg 的 nlbits 设置（官方驱动已给掩码与移位：`ECLIC_CFG_NLBITS_MASK=0x1E`、`NLBITS_LSB=1`，n200_eclic.h:54-55；**精确语义**仍以 ISA 手册为准）。

**推论二**：ARM 那套 `NVIC_SetPriorityGrouping()` / `0x5FA` 钥匙在 RISC-V 上完全不存在。看到 GD32VF103 例程里"设优先级分组"的写法，那是在配 cliccfg，不是 ARM 的 AIRCR。

## 五、向量直跳：shv 模式与 ARM 向量表的机制差异

[S4 第四节](../stm32/04-nvic-exti.md)讲过 ARM 向量表：Flash 起始一张大表，槽 N 放 ISR 函数指针，硬件进异常时读槽跳转；函数名拼错 = weak 默认顶替 = 死循环。

ECLIC 有两种向量模式（手册 §1.1 "fast vectored interrupt processing"）：

- **向量模式（shv = 1）**：每个中断有自己的入口地址，硬件**直接跳到该入口**，叫"向量直跳"。不需要"读一张大表"，每个中断的向量独立配置在 ECLIC 内部。
- **非向量模式（shv = 0）**：所有中断进公共入口（`mtvec` 指向），由软件读 `mcause` / clicintip 分发，省向量存储，但多一次软件分派。

| | ARM NVIC (S4) | ECLIC (V1) |
|---|---|---|
| 向量存储 | Flash 起始一张大表（98 项 × 4 字节） | 每中断入口地址存 ECLIC 内部（clicintattr.shv + 向量寄存器） |
| 跳转方式 | 硬件读槽 → 跳 | shv=1 硬件直跳专属入口；shv=0 进公共入口软件分 |
| 函数名约定 | 必须与向量表 weak 同名 | 向量模式下入口地址直接配进 ECLIC，名字不一定要对表 |
| 函数名拼错 | weak 符号顶替 → 死循环 | 取决于配置；公共入口模式下"没注册"进默认处理 |
| 异常返回 | `EXC_RETURN` 魔法值（0xFFFFFFFD）+ 硬件弹栈 8 字 | `mret` + 从 mepc 恢复（软件在 prologue 压栈） |

ECLIC 的"向量直跳"省了 ARM 那张大表，但代价是每个要用向量的中断都得显式配入口，灵活但要写更多配置代码。

> **【注】RISC-V 异常返回没有"魔法值"**。ARM 进 ISR 时 LR 被硬件换成 `EXC_RETURN`（0xFFFFFFFD），出 ISR 一条 `bx lr` 触发硬件弹栈。RISC-V 进 ISR 时硬件把返回地址存进 `mepc`、把中断使能存进 `mstatus.MPIE`，ISR 末尾一条 `mret` 指令恢复：没有"LR 换魔法值"这一步，压栈也是软件在 prologue 干（不像 ARM 硬件自动压 8 字）。
>
> 精确的 shv 位位置、向量寄存器布局、clicintattr 字段：官方固件驱动已实证偏移（clicintattr@+0x1002、SHV 位 0x01、TRIG_LEVEL/EDGE=0x00/0x02、TRIG_POS/NEG=0x00/0x04，n200_eclic.h:40-46），语义细节仍以 ISA 手册为准。

## 六、MTIME 不是 SysTick：内存映射定时器

[S5](../stm32/05-systick.md) 讲过 SysTick：24 位递减计数器、CLKSOURCE 选 HCLK/8 或 HCLK、IRQn = -1（内核异常）、寄存器在 SCS 区 `0xE000E010`。Bumblebee 的 MTIME 完全不同（手册 §2.13）：

- **RISC-V 标准 64 位递增定时器**，CLK 由系统低速 RTC 频率驱动；
- **mtime**：64 位当前计数值；
- **mtimecmp**：64 位比较值，**mtime 不小于 mtimecmp 时触发定时器中断**；
- **mtime/mtimecmp 不是 CSR**：手册明说："not CSR registers, but Memory Address Mapped system registers"（内存映射系统寄存器）；
- 具体映射地址 RISC-V 架构不定义，由实现定；Bumblebee 把它们做在 TIMER 单元里。官方固件驱动实证：`TIMER_CTRL_ADDR = 0xD1000000`，mtime @ +0x0、mtimecmp @ +0x8（n200_timer.h:24-30）。

| | SysTick (Cortex-M, S5) | MTIME (Bumblebee) |
|---|---|---|
| 位数 | 24 位递减 | 64 位递增 |
| 比较方式 | 倒数到 0 触发 | mtime 不小于 mtimecmp 触发 |
| 寄存器位置 | SCS 内存映射 0xE000E010 | TIMER 单元内存映射（官方驱动实证 0xD1000000） |
| 是否 CSR | 否 | **否**（常被误以为 CSR） |
| IRQn | -1（内核异常） | `CLIC_INT_TMR = 7`（ECLIC，gd32vf103.h:102） |
| 重装 | 写 LOAD 自动重装 | **软件写 mtimecmp = mtime + 周期** |
| RTOS tick | 直接用 | 直接用（[V3](08-mtime-delay.md) 详述） |

**驱动频率**（手册 §3.1 + GD32VF103 注记）：mtime 由 SoC 的 `mtime_toggle_a` 脉冲驱动，每检测到一个边沿 mtime 加 1。GD32VF103 上 `rtc_clk = core_clk_aon / 4`，所以 **mtime 自增频率 = core_clk_aon / 4**。若核心跑 108MHz，mtime 约 27MHz 自增（`core_clk_aon` 与核心时钟同源同频的关系已由 [V3](08-mtime-delay.md) 收案：手册 §2.1）。

**推论**：MTIME 是 64 位递增 + 软件比较，意味着"周期定时"要软件每次中断后把 mtimecmp 加一个周期（不像 SysTick 硬件自动重装）。这是 RTOS port 到 RISC-V 必须处理的差异（[V3](08-mtime-delay.md) 详述）。SysTick 的"写一次 LOAD 一劳永逸"在 MTIME 上不成立。

## 七、对照落地：配通 EXTI0，与 S4 六步逐条对比

以 PA0 → EXTI0 为例，与 [S4 第六节](../stm32/04-nvic-exti.md)的六步逐条对比：

| # | S4 (STM32F407) | V1 (GD32VF103) | 差异 |
|---|---|---|---|
| 1 | 开 GPIOF 时钟 `RCC_AHB1ENR` | 开 GPIOA 时钟 `RCU_APB2EN.PAEN`（bit2） | RCU 命名，APB2 上（`gd32vf103_rcu.h:165`） |
| 2 | PF6 配输入 | PA0 配输入 | 同 |
| 3 | 开 SYSCFG 时钟 `RCC_APB2ENR` bit14 | 开 AFIO 时钟 `RCU_APB2EN.AFEN`（bit0） | F1 风格 AFIO（`gd32vf103_rcu.h:164`） |
| 4 | SYSCFG EXTICR 选门 | AFIO_EXTISS 选门 | F1 风格选门（AFIO@0x40010000） |
| 5 | EXTI IMR/FTSR 设沿放行 | EXTI IMR/FTSR 设沿放行 | **外设同源（F1），几乎照搬** |
| 6 | `NVIC_SetPriority` + `EnableIRQ`（ISER） | ECLIC clicintie[25]=1 + clicintctl[25] 设 level/priority + clicintattr[25] 配 shv | **控制器不同，三动作** |
| ISR | `EXTI0_IRQHandler` 清 PR | 同名 ISR 清 PR | ISR 写法照搬（EXTI 外设同 F1） |

**关键差异在第 6 步**：ARM 是"使能 + 设优先级"两动作；ECLIC 是"使能 + 设 level/priority + 配向量模式"三动作。多出来的"配向量模式"决定该中断是直跳专属入口（shv=1）还是进公共入口再分发（shv=0）。

ISR 写法照搬（因为 EXTI 外设与 F1 同源，挂起位还是 `EXTI_PD` 写 1 清除）：

```c
void EXTI0_IRQHandler(void)          /* GD32VF103 上 EXTI0 的 ECLIC 中断号 = 25 */
{
    EXTI_PD = (1UL << 0);            /* 第一件事：清挂起（与 S4 5.3 同语义） */
    /* ... 记账式干活，快进快出 ... */
}
```

GD32VF103 的"混血"在这里体现得最清楚：外设层（EXTI/AFIO/GPIO）是 ARM F1 的亲戚，所以第 1~5 步、ISR 清挂起都几乎照搬；只有控制器层（第 6 步）换成 ECLIC 的三动作。**会用 STM32F1 的人，学完 ECLIC 第 6 步就能在 GD32VF103 上配通任意外部中断。**

## 记忆锚点

::: tip 一句话记住
**控制器 NVIC→ECLIC，优先级单维→level+priority 两维，向量大表→每中断 shv 直跳；SysTick→MTIME 内存映射、64 位递增软件比较；EXTI 外设照搬 F1，第 6 步换 ECLIC 三动作。**
:::

## 实物实验

- 用 GDB 读 `mtvec`（`info registers mtvec`）与 cliccfg，看 ECLIC 全局配置（寄存器偏移已实证，语义细节见 ISA 手册）。
- 配 EXTI0 为 shv=1 向量模式，按键触发，在 ISR 入口设断点，应直接断在专属入口，不停在公共入口。
- 配同 EXTI0 为 shv=0 非向量模式，再触发，应先停在公共入口，单步后分发到 ISR。两种模式一对比，"向量直跳"就直观了。
- MTIME 实验（[V3](08-mtime-delay.md) 详述）：读 mtime 两次间隔，反推自增频率，验证 `core_clk_aon / 4`。

## 常见坑

1. **用 STM32 的"槽号 = IRQn + 16"算 GD32VF103 中断号**：EXTI0 应是 25 不是 22（S4 表里 EXTI0 槽 22 是 STM32F407 的），算错就配错 ECLIC 寄存器。
2. **以为 ECLIC 也有 AIRCR / 0x5FA 钥匙、PRIGROUP 分组**：RISC-V 没这套，level + priority 本来就两维，硬写 AIRCR 无效。看到"设优先级分组"的代码，那是配 cliccfg，不是 ARM 的 AIRCR。
3. **把 mtime/mtimecmp 当 CSR 用 `csrr`/`csrw` 读写**：它们是内存映射，要用 `lw`/`sw` 普通访存指令，`csrr` 会触发非法指令异常。
4. **SysTick 周期定时照搬到 MTIME**：以为硬件自动重装 → MTIME 是软件写 mtimecmp 加周期，不写就只响一次。RTOS tick 必须每次中断后更新 mtimecmp。
5. **EXTI 外设照搬 F1，但忘了 GD32VF103 时钟使能位编码不同**：`RCU_APB2EN.PAEN` 是 bit2（`gd32vf103_rcu.h:165`），不是 F1 的 bit2（PAEN 恰好同位），但 AFEN 是 bit0、USART0EN 是 bit14：照搬 F1 位号前要核对 `gd32vf103_rcu.h`，别想当然。

## 短自测

**1. GD32VF103 上 EXTI0 的中断号是多少？和 STM32F407 的 EXTI0 比，编号差多少？**

<details><summary>看答案</summary>

`EXTI0_IRQn = 25`（`gd32vf103.h:113`）。STM32F407 的 `EXTI0_IRQn = 6`（槽 22，`stm32f407xx.h:83`）。差很多：RISC-V ECLIC 没有"IRQn + 16"偏移，ECLIC 索引就是中断号本身。S4 那张"槽号 = IRQn + 16"的映射表在 GD32VF103 上完全不适用，移植不能照搬。

</details>

**2. ECLIC 的优先级有哪两个维度？各自管什么？ARM 用一个什么机制实现类似效果？**

<details><summary>看答案</summary>

**level**（抢占级，最多 16 级，决定能否打断别人）+ **priority**（同级排序，最多 16 级，决定同 level 同时挂起时谁先上，无打断能力）。ARM 用单一 4 位优先级 + PRIGROUP 切分组（写 AIRCR 带 0x5FA 钥匙）实现"抢占 + 子"两份。ECLIC 天生两维，不用切分组，也没有 0x5FA 钥匙。

</details>

**3. mtime 与 mtimecmp 是 CSR 吗？放在哪？怎么读写？**

<details><summary>看答案</summary>

**不是 CSR**。Bumblebee 手册 §2.13 明说它们是 "Memory Address Mapped system registers"，做在 TIMER 单元里，精确地址由实现定（官方固件驱动实证：0xD1000000，n200_timer.h:29）。要用 `lw`/`sw` 普通访存指令读写，不能用 `csrr`/`csrw`，后者会触发非法指令异常。

</details>

**4. ECLIC 的 shv=1 与 shv=0 各是什么模式？与 ARM 向量表机制比有何不同？**

<details><summary>看答案</summary>

shv=1 是**向量模式**：硬件直跳到该中断专属入口（向量直跳）；shv=0 是**非向量模式**：进公共入口（`mtvec` 指向）再软件读 `mcause`/clicintip 分发。ARM 是"Flash 起始一张大表，硬件读槽跳"，所有中断都走读表；ECLIC 每中断独立配，可直跳（shv=1）也可分发（shv=0），省了一张大表但每个要向量的中断都得显式配入口。

</details>

**5. GD32VF103 上 mtime 的自增频率约为什么？依据是什么？**

<details><summary>看答案</summary>

约为 `core_clk_aon / 4`。依据：mtime 由 SoC 的 `mtime_toggle_a` 脉冲驱动（每检测到边沿 mtime 加 1），Bumblebee 手册 §3.1 注记 GD32VF103 上 `rtc_clk = core_clk_aon / 4`，而 mtime_toggle_a 推荐 由 rtc_clk 驱动。若核心跑 108MHz，mtime 约 27MHz 自增（`core_clk_aon` 与核心时钟同源同频已由 [V3](08-mtime-delay.md) 收案：手册 §2.1）。

</details>

## 对照表：本章概念 → 仓库/手册落点

| 概念 | 仓库/手册落点 |
|---|---|
| Bumblebee RV32IMAC、2 级流水线、Machine/User 模式 | Bumblebee 手册 §1.1 / §2.4 |
| 无 NVIC / SysTick / SCB-VTOR / PendSV | Bumblebee 手册 §1.1 / §2.6 / §2.13 |
| 无 PMP | Bumblebee 手册 §2.7 |
| ECLIC 16 level + 16 priority、向量、尾链、NMI | Bumblebee 手册 §1.1 ECLIC 条目 / §2.6 |
| `CLIC_INT_SFT=3` / `CLIC_INT_TMR=7` / `BWEI=17` / `PMOVI=18` | `gd32vf103.h:101-104` |
| `EXTI0_IRQn=25` / `USART0_IRQn=56` / `USBFS_IRQn=86` | `gd32vf103.h:113` / `:144` / `:169` |
| `ECLIC_NUM_INTERRUPTS` 哨兵 | `gd32vf103.h:171` |
| EXTI_BASE=0x40010400、AFIO_BASE=0x40010000（F1 风格） | `gd32vf103.h:220` / `:219` |
| `RCU_APB2EN.PAEN=bit2` / `AFEN=bit0` | `gd32vf103_rcu.h:165` / `:164` |
| MTIME 64 位、mtime/mtimecmp 内存映射、非 CSR | Bumblebee 手册 §2.13 |
| mtime_toggle_a、rtc_clk = core_clk_aon / 4 | Bumblebee 手册 §3.1 + GD32VF103 注记 |
| ARM 对照：IRQn+16、4 位优先级、PRIGROUP、0x5FA、向量表 | [S4](../stm32/04-nvic-exti.md) 第二/三/四节 |
| ECLIC 寄存器精确偏移、shv 位、clicintattr/clicintctl 字段 | 官方固件驱动实证（n200_eclic.h:28-49）；语义细节以 ISA 手册为准 |
| mtime/mtimecmp 精确映射基地址 | 官方固件驱动实证：0xD1000000（n200_timer.h:24-30）；nlbits 语义待 ISA 手册 |
| `core_clk_aon` 与核心时钟的精确关系 | 已收案：同源同频（[V3](08-mtime-delay.md)，手册 §2.1） |

## 延伸阅读

ECLIC 的标准原型与权威寄存器表：

- **[\[C9\]](../reference/bibliography.md#toolchain)** RISC-V CLIC 规范草案 — "级别 + 优先级"双字段、向量直跳模式的标准原型，ECLIC 是它的增强实现。
- **[\[A14\]](../reference/bibliography.md#chips)** Bumblebee Core Datasheet — ECLIC 寄存器与 CSR 的权威表，GD32VF103 的中断源编号以它为准。
- **[\[C8\]](../reference/bibliography.md#toolchain)** RISC-V Privileged 20211203 — mstatus/mtvec/mie 的架构定义。

## 你做到了

- 中断控制器从 NVIC 换到 ECLIC，三处架构差异（控制器、两维优先级、向量直跳）入肌肉记忆；
- 中断号不再"IRQn + 16"，能从 `gd32vf103.h` 直接读 ECLIC 索引，知道同一条 EXTI0 线在两颗芯片上编号差很远；
- MTIME 不是 SysTick：64 位递增、内存映射、软件比较、`mtime_toggle_a` 驱动，RTOS tick 的地基（[V3](08-mtime-delay.md) 接着盖）；
- 手握"EXTI 外设照搬 F1、第 6 步换 ECLIC 三动作"的清单，能在 GD32VF103 上配通任意外部中断。

两扇门对答案：shv 置 1，硬件直跳该中断的专属入口；置 0，进公共入口由软件读 mcause 分发，ARM 那张向量大表没了。优先级另拆成两张：level 管抢占、priority 管同级排序。0x5FA 那把钥匙，这个世界不认。

<div class="achievement">
✅ 下一站：<a href="07-rcu-108m.html">V2 RCU 与 108MHz</a>：G1 的 RCU 知识平移到 RISC-V，预设档 48/72/108M 一次算清。
</div>
