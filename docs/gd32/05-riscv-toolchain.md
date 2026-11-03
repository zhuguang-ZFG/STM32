---
title: V0 RISC-V 工具链与启动文件
status: done
difficulty: 2
minutes: 30
---

# V0 RISC-V 工具链与启动文件

> 🎯 `arm-none-eabi-gcc` 换成 `riscv-none-elf-gcc`、`startup_stm32f407xx.s` 换成 `start_gd32vf103.S`——名字变了，"上电到 main"的工序却几乎一模一样。但有三处根本不同：没有 FPU 要开、没有"硬件两读"栈顶、复位靠的是 `reset_handler` 而不是向量表第 1 项。学会这三处差异，B4 的知识就能整个平移到 RISC-V。

## 本章精髓

1. **工具链命名遵循 RISC-V 规范**：`riscv-none-elf-gcc`（曾用 `riscv-none-embed-gcc` / `riscv64-unknown-elf-gcc`），编译标志从 `-mcpu/-mthumb/-mfloat-abi/-mfpu` 换成 `-march=rv32imac -mabi=ilp32`："目标三元组 + march/mabi"是 RISC-V 工具链的身份证。
2. **启动文件 `start_gd32vf103.S` 与 B4 的 `startup_stm32f407xx.s` 同构**：设 sp → 搬 .data → 清 .bss → 调 SystemInit → `call main`。**删掉的**是"开 CPACR"那一节：RV32IMAC 没有 FPU，硬浮点编译选项根本不存在。
3. **RISC-V 复位不做"硬件两读"**：PC 由复位向量直接装入，sp 必须由启动代码显式 `la sp, __stack_top` 设好。向量表那套机制在 [V1](06-clic-irq.md) 才登场（ECLIC 的向量直跳），复位这一刻它不参与。

## 先修

无（建议对照 [B0 工具链全景](../build/00-toolchain.md)、[B4 启动过程](../build/04-startup.md) 作锚点）。

## 先跑起来（10 分钟 quick win）

```bash
riscv-none-elf-gcc --version
# 输出里找 "riscv-none-elf-gcc" —— 工具链到位的标志
# 若 "command not found"，先装 xPack 的 riscv-none-elf-gcc 发行包

riscv-none-elf-gcc -march=rv32imac -mabi=ilp32 -print-libgcc-file-name
# 能打印出 libgcc 路径，说明 rv32imac/ilp32 这个 multilib 组合在工具链里有效
```

读两行输出：版本号、libgcc 路径里藏的 `rv32imac/ilp32`，这就是 RISC-V 工具链的身份证。本章每个标志位都能对回这两行。

先押张工序单：身份证正面是工具链，背面印的是启动工序。搬 .data、清 .bss、调 SystemInit、进 main 这几道，RISC-V 那边还用同一套指令拼写吗？押完对第二节的对照表。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、工具链换岗 | riscv-none-elf-gcc 命名、-march/-mabi 标志、multilib | 配置 |
| 二、启动文件骨架 | start_gd32vf103.S 与 B4 启动文件的工序逐段对照 | 代码分析 |
| 三、没有 CPACR | RV32IMAC 无 FPU，"开 FPU"那一节为何整体删除 | 配置 |
| 四、没有硬件两读 | RISC-V 复位如何装 PC、sp 谁来设 | 代码分析 |
| 五、链接脚本 | gcc_gd32vf103.ld 的 MEMORY/ENTRY/段与 B3 五符号 | 配置 |
| 六、SystemInit | system_gd32vf103.c 复位 RCU、main 之前拉到 108M | 代码分析 |

## 一、工具链换岗：arm-none-eabi → riscv-none-elf

![RISC-V 工具链流程](/anim/riscv-toolchain-flow.svg)

[B0](../build/00-toolchain.md) 讲过"四个软件一台戏"：编译器、汇编器、链接器、调试器。换到 RISC-V，这四件套全有，只是前缀变了：

| ARM 裸机 | RISC-V 裸机 | 备注 |
|---|---|---|
| `arm-none-eabi-gcc` | `riscv-none-elf-gcc` | 曾用 `riscv-none-embed-gcc`（xPack 早期）、`riscv64-unknown-elf-gcc`（更早） |
| `arm-none-eabi-objdump` | `riscv-none-elf-objdump` | 同 |
| `arm-none-eabi-gdb` | `riscv-none-elf-gdb` | 同 |
| `arm-none-eabi-objcopy` | `riscv-none-elf-objcopy` | 同 |

**目标三元组**的读法：`riscv`（厂商）+ `none`（无操作系统/裸机）+ `elf`（目标格式）。ARM 那边写 `none-eabi` 是因为 ARM 用 EABI 规范；RISC-V 这边直接 `elf`， ABI 由 `-mabi` 单独指定。

**编译标志对照**，这是最关键的一行差异：

| 项 | ARM (STM32F407) | RISC-V (GD32VF103) |
|---|---|---|
| 架构标志 | `-mcpu=cortex-m4 -mthumb` | `-march=rv32imac` |
| 浮点标志 | `-mfloat-abi=hard -mfpu=fpv4-sp-d16` | **无**（IMAC 无 F/D 扩展） |
| ABI 标志 | （隐含在 -mfloat-abi） | `-mabi=ilp32` |

把 `-march=rv32imac` 拆开念：`rv32` = 32 位 RISC-V；`I` = 基础整数指令；`M` = 乘除法；`A` = 原子指令；`C` = 压缩指令（16 位编码，省 Flash）。`-mabi=ilp32` = ILP32 数据模型（int/long/指针都是 32 位），不带 `f`/`d` 后缀，因为没有浮点硬件，浮点运算走 libgcc 软件模拟。

> **【注】别把 `riscv64-unknown-elf-gcc` 当 64 位用**。它支持 rv32 multilib，但默认目标是 rv64。不显式带 `-march=rv32imac -mabi=ilp32`，链接脚本里 `ORIGIN(RAM)=0x20000000` 这种 32 位地址会和 64 位默认重定位对不上，报一堆 `relocation truncated to fit`。

## 二、启动文件骨架：与 B4 逐段对照

`start_gd32vf103.S`（注意大写 `.S` = 要过预处理器，所以能用 `#include` 和宏）与 B4 的 `startup_stm32f407xx.s` 工序几乎一一对应：

| B4 工序 | B4 实现（ARM 汇编） | V0 实现（RISC-V 汇编） | 差异 |
|---|---|---|---|
| 设栈 | 硬件两读自动装 MSP | `la sp, __stack_top` | **软件显式**（见第四节） |
| 开 FPU | `ldr r0,=0xE000ED88; orr #(0xF<<20)` | **删除** | 架构级删除（见第三节） |
| 搬 .data | `ldr r0,=_sdata...ldr r4,[r2,r3]; str` | `la t0,_sidata; la t1,_sdata; lw/sw/addi` | 同义换指令 |
| 清 .bss | `ldr r2,=_sbss; str r3` | `la t0,_sbss; sw zero` | 同义换指令 |
| 调 SystemInit | `bl SystemInit` | `call SystemInit` | 同 |
| 进 main | `bl main; b .` | `call main; j .`（或 `wfi` 循环） | 同 |

搬运 .data 的循环骨架（RISC-V 版，与 B4 第三节对照读）：

```asm
    la      t0, _sidata      /* Flash 源起点（链接脚本给的） */
    la      t1, _sdata       /* RAM 目标起点 */
    la      t2, _edata       /* RAM 目标终点 */
    mv      t3, zero         /* 偏移 = 0 */
.L_copy_loop:
    bgeu    t1, t2, .L_copy_done    /* 目标到终点了？先判后干 */
    lw      t4, 0(t0)        /* 从 Flash 读一个字 */
    sw      t4, 0(t1)        /* 写到 RAM */
    addi    t0, t0, 4
    addi    t1, t1, 4
    j       .L_copy_loop
.L_copy_done:
```

`_sidata = LOADADDR(.data)`、`_sdata`/`_edata` 是 [B3 链接脚本](../build/03-linker-script.md)讲的五个符号里的三个，这套约定跨架构通用，RISC-V 链接脚本照样发这些"地址条"。`bgeu t1, t2`（无符号大于等于则跳）对应 B4 的 `cmp r4, r1; bcc`，同样是"先判后干"，长度为零的 .data 也安全。

清 .bss 更瘦：源操作数都不需要，一路 `sw zero` 扫过去，与 B4 第四节同思路，只是指令换成了 RISC-V 的 `sw`。

## 三、没有 CPACR：RV32IMAC 无 FPU 这件事

B4 的"第 0 步"是开 `SCB->CPACR` 的 CP10/CP11，否则第一条 FPU 指令触发 `UsageFault(NOCP)`，程序静默卡死。这一步在 V0 **整体删除**——不是省略，是架构上不存在：

- **指令集没有浮点扩展**：`-march=rv32imac` 里的 `IMAC` 不含 `F`（单精度）也不含 `D`（双精度），编译器根本不会生成 FPU 指令。
- **没有"协处理器使能"机制**：ARM 用 CPACR 管协处理器权限是因为它有 CP0~CP15 的协处理器编号空间；RISC-V 的自定义扩展走 CSR 编码空间，浮点若有则由 `mstatus.FS` 字段管，但 IMAC 没有浮点，`mstatus.FS` 都不用碰。
- **`-mfloat-abi=hard` 是非法组合**：在 `rv32imac` 上加 `-mfloat-abi=hard`，工具链要么报错，要么默默走软浮点（libgcc 软件模拟）。这与 B4 里"硬浮点工程忘开 CPACR"的坑是镜像关系：ARM 是"有 FPU 但没开门"，RISC-V 是"门都没有"。

推论：GD32VF103 上做浮点运算（`float a = 1.5f * 2.0f;`）走的是 libgcc 的软浮点函数调用，慢且占 Flash，但能跑，不会 fault。要不要用浮点、用多少，是个工程权衡，不是"开了就崩"的开关。

## 四、没有硬件两读：RISC-V 复位与 Cortex-M 的根本差异

[B4 第一节](../build/04-startup.md)讲过：Cortex-M 复位时**硅片硬逻辑**从 0 号地址读 4 字节装 MSP、从 4 号地址读 4 字节装 PC，然后开始取指。RISC-V 没有这套机制：

| | Cortex-M (B4) | RISC-V (V0) |
|---|---|---|
| 初始 sp | 硬件从 0x0 读 MSP | **sp = 0**，启动代码 `la sp, __stack_top` 设 |
| 初始 PC | 硬件从 0x4 读 Reset_Handler | 复位向量地址装入（实现定义） |
| 向量表位置 | Flash 起始，第 0 项是栈顶 | 无"向量表"概念，复位不靠它 |
| 谁先干活 | 硬件两读，再跳 Reset_Handler | 直接跳 `reset_handler`，sp 自己设 |

所以 `start_gd32vf103.S` 的 `reset_handler` 第一件事不是搬数据，是**设栈**：

```asm
reset_handler:
    la      sp, __stack_top    /* 没人替你设 sp，自己来 */
    /* ... 之后才是搬 .data、清 .bss、call SystemInit、call main ... */
```

`__stack_top` 由链接脚本给（见第五节），值 = `ORIGIN(RAM) + LENGTH(RAM)`，栈从 RAM 顶向下长，与 B4 的 `_estack` 同思路，只是 B4 那是"硬件读进去"，这里是"软件装进去"。

> **【坑】** 别以为 RISC-V 也有"向量表第 0 项是栈顶值"的约定，把 `__stack_top` 写进链接脚本当向量：RISC-V 复位不读它，sp 还是 0，第一条用到栈的指令就跑飞。向量机制在 [V1](06-clic-irq.md) 讲（ECLIC 向量直跳），复位这一刻它完全不参与。

## 五、链接脚本：gcc_gd32vf103.ld 与 B3 五符号

`gcc_gd32vf103.ld`（官方固件库 `Firmware/GD32VF103/GCC/LinkerScripts/` 下）与 `stm32f407xx.ld` 同构：

```ld
MEMORY
{
    FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 256K    /* gd32vf103.h:193 */
    RAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 32K     /* gd32vf103.h:194 */
}
ENTRY(reset_handler)

SECTIONS
{
    .text : { *(.text*) } > FLASH
    .data : { *(.data*) } > RAM AT> FLASH              /* 运行在 RAM，初值存 Flash */
    .bss  : { *(.bss*)  } > RAM
    __stack_top = ORIGIN(RAM) + LENGTH(RAM);
}
```

**关键事实核验**（`gd32vf103.h:193-194`）：

```c
#define FLASH_BASE  ((uint32_t)0x08000000U)   /* main FLASH base */
#define SRAM_BASE   ((uint32_t)0x20000000U)   /* SRAM base        */
```

**与 STM32F407 完全相同的地址**（见 [S1 架构总览](../stm32/01-arch.md)）。这是 GD32 刻意保持的移植兼容点：把 STM32 固件搬到 GD32VF103，Flash 和 RAM 起始地址不用改。

[B3](../build/03-linker-script.md) 讲的五个符号在这里同名同义：`_sidata = LOADADDR(.data)`（初值仓库在 Flash 的位置）、`_sdata`/`_edata`（.data 在 RAM 的头尾）、`_sbss`/`_ebss`（.bss 在 RAM 的头尾）、`__stack_top`（栈顶）。这套符号是链接脚本约定，跨架构通用。

**唯一差异**：RISC-V 链接脚本没有 `.isr_vector` 段（ARM 把向量表放 Flash 起始，对应 `g_pfnVectors`）。RISC-V 的"向量"由 ECLIC 管理（[V1](06-clic-irq.md) 详述），不需要在 Flash 起始摆一张大表。

## 六、SystemInit：main 之前把时钟拉到 108M

`system_gd32vf103.c:150` 的 `SystemInit()` 干两件事：复位 RCU 配置位 → 调 `system_clock_config()`。后者默认走 `system_clock_108m_hxtal()`（`system_gd32vf103.c:62` 定义 `__SYSTEM_CLOCK_108M_PLL_HXTAL`）。

108M 流程（`system_gd32vf103.c:751-830`）：

1. 使能 HXTAL：`RCU_CTL |= HXTALEN`（bit16），轮询 `HXTALSTB`（bit17）
2. 总线分频：AHB = SYSCLK/1、APB2 = AHB/1、APB1 = AHB/2
3. PLL 配置：`RCU_PLL_MUL27`（× 27）+ PREDV0 分频
   - 8M 晶振（V_EVAL/C_START/T_START）：PREDV0_DIV2 → 4MHz × 27 = **108MHz**
   - 25M 晶振（R_START）：经 PREDV1_DIV5 × PLL1_MUL8 → 40MHz，再 PREDV0_DIV10 → 4MHz × 27 = 108MHz
4. 使能 PLL：`RCU_CTL |= PLLEN`（bit24），轮询 `PLLSTB`（bit25）
5. 选 PLL 为系统时钟：`RCU_CFG0 |= RCU_CKSYSSRC_PLL`，轮询 `SCSS = PLL`

这与 STM32 RCC 提频六步同构，只是寄存器名 `RCC→RCU`、位名 `PLLRDY→PLLSTB`、`SWS→SCSS`（[G1](01-rcu-clock.md) 已在 GD32F4 上逐字段对照过）。**同样"官方留白"**：`system_gd32vf103.c` 全文不设 Flash 等待周期，但 VF103 的 FMC_WS 寄存器确实存在（@0x4002 2000 + 0x00，gd32vf103_fmc.h:45,64），而且 UM 已核验出一个 G1 没有的收窄：**VF103 的 WSCNT[2:0] 只有 000/001/010 三档有效，011~111 全部保留**（UM §2.4.1），同样要先置 FMC_WSEN 才生效。108MHz 档实际该配几拍，UM 不给映射表（与 G1 在 GD32F4 的发现一致），**待上板实测**。

启动序列全景：

```text
reset_handler
  → la sp, __stack_top          /* 设栈 */
  → 搬 .data (Flash → RAM)
  → 清 .bss
  → call SystemInit             /* 把 RCU 配成 PLL×27 = 108M */
  → call main                   /* main 一进来就在 108MHz 跑 */
```

`SystemInit` 在 `main` 之前把时钟拉到 108M，所以你的 `main` 第一行就在 108MHz 跑。跳过它就只在 8M IRC8M 跑，串口波特率全错。

## 记忆锚点

::: tip 一句话记住
**工具链换 riscv-none-elf，march rv32imac 配 ilp32；启动删 FPU、栈自己设；FLASH 0x0800 / RAM 0x2000 与 STM32 同址，main 进来就在 108M。**
:::

**延伸**：RISC-V 工具链流程动画见 [V0 动画](/anim/riscv-toolchain-flow.svg)；ARM 工具链对照见 [B0](../build/00-toolchain.md)；链接脚本在 [B3](../build/03-linker-script.md) 详解。

## 实物实验

- `riscv-none-elf-objdump -d your.elf | findstr reset_handler`：看 `reset_handler` 第一条是 `la sp`（设栈），与 Cortex-M reset 第一条"读向量表"对比。
- GDB `monitor reset halt` 后 `info registers sp pc`：sp = 0、pc = `reset_handler` 地址，亲眼看到"sp 没人设"。
- 进阶：在 `reset_handler` 的 `la sp, __stack_top` 行下断，单步过后 sp 变成 RAM 顶值（0x20000000 + RAM 长度）；再单步过 `call SystemInit`，`RCU_CFG0` 的 SCSS 字段应变成 PLL。

## 常见坑

1. **用了 `riscv64-unknown-elf-gcc` 旧名又不带 `-march/-mabi`**：默认 rv64，链接脚本里 32 位地址对不上，报 `relocation truncated to fit` 一堆。要么换 `riscv-none-elf-gcc`，要么每次显式带 `-march=rv32imac -mabi=ilp32`。
2. **`-march=rv32imac` 误写成 `rv32imacF`**：加了 F 但芯片没 FPU，工具链报 `unsupported ISA extension`。GD32VF103 就是 IMAC，别画蛇添足。
3. **以为 RISC-V 也有"向量表第 0 项是栈顶"**：把 `__stack_top` 当向量写，复位还是不读它，sp 留 0，第一条 push 就跑飞。RISC-V 复位只跳 `reset_handler`，栈是软件设。
4. **忘了 `call SystemInit`**：`main` 在 8MHz IRC8M 跑，串口波特率、延时全错，现象是"程序能跑但时序诡异"，难查。
5. **照搬 STM32 的 `-mfloat-abi=hard`**：RISC-V 上无 F 扩展，编译报错或默默走软浮点；想要硬件浮点得换带 F/D 的 RISC-V 芯片，GD32VF103 不行。

## 短自测

**1. `riscv-none-elf-gcc` 替代 `arm-none-eabi-gcc` 后，编译标志哪两套变了？**

<details><summary>看答案</summary>

**架构标志**与 **ABI/浮点标志**两套。ARM 写 `-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16`；RISC-V 写 `-march=rv32imac -mabi=ilp32`。RISC-V 没有 `-mcpu`（用 march 指令集代替），也没有 `-mfloat-abi/-mfpu`（IMAC 无 FPU，浮点走软模拟）。

</details>

**2. `start_gd32vf103.S` 相比 `startup_stm32f407xx.s` 删除了哪一节？为什么？**

<details><summary>看答案</summary>

**开 CPACR / 开 FPU 那一节**（B4 的"第 0 步"）。RV32IMAC 指令集不含 F/D 浮点扩展，编译器不生成 FPU 指令，也没有"协处理器使能"机制可开。这是架构级删除，不是省略。

</details>

**3. RISC-V 复位后 sp 是多少？谁来设？与 Cortex-M 有何不同？**

<details><summary>看答案</summary>

sp = 0。由启动代码 `la sp, __stack_top` 显式设，`__stack_top` 由链接脚本给（`ORIGIN(RAM) + LENGTH(RAM)`）。Cortex-M 复位时硬件从 0 号地址读 4 字节自动装 MSP，软件不用管；RISC-V 没有"硬件两读"机制，sp 必须软件设。

</details>

**4. GD32VF103 的 FLASH 与 RAM 起始地址是多少？和 STM32F407 比如何？**

<details><summary>看答案</summary>

FLASH = 0x08000000、RAM = 0x20000000（`gd32vf103.h:193-194`）。与 STM32F407 **完全相同**，这是 GD32 刻意保持的移植兼容点，把 STM32 固件搬到 GD32VF103，Flash 和 RAM 起始地址不用改。

</details>

**5. `main` 一进来就在 108MHz 跑，是谁干的？跳过会怎样？**

<details><summary>看答案</summary>

`reset_handler` 在 `call main` 之前先 `call SystemInit`（`system_gd32vf103.c:150`），后者调 `system_clock_108m_hxtal()` 把 RCU 配成 PLL × 27 = 108M。跳过它，`main` 只在 8M IRC8M 跑，程序能跑但串口波特率、延时时序全错，难查。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库/文件落点 |
|---|---|
| `riscv-none-elf-gcc` 命名、替代 `arm-none-eabi-gcc` | 工具链发行说明；Makefile |
| `-march=rv32imac -mabi=ilp32` | 启动工程 Makefile / 启动文件头注释 |
| `start_gd32vf103.S` 工序对照 | 官方固件库 `Firmware/GD32VF103/Source/` 启动文件 |
| 搬 .data / 清 .bss 的 RISC-V 实现 | `start_gd32vf103.S` `reset_handler` 段 |
| RV32IMAC 无 FPU、删 CPACR 节 | 架构事实（IMAC 无 F/D 扩展） |
| 复位无硬件两读、sp 软件设 | `start_gd32vf103.S` 首条 `la sp, __stack_top` |
| `__stack_top = ORIGIN(RAM)+LENGTH(RAM)` | `gcc_gd32vf103.ld` |
| `_sidata/_sdata/_edata/_sbss/_ebss` 五符号 | `gcc_gd32vf103.ld`（与 [B3](../build/03-linker-script.md) 同名同义） |
| FLASH/SRAM 基址 0x08000000 / 0x20000000 | `gd32vf103.h:193-194` |
| `SystemInit` 复位 RCU | `system_gd32vf103.c:150` |
| 108M 流程 HXTAL→MUL27→PREDV0 | `system_gd32vf103.c:751-830` |
| HXTALEN/STB bit16/17、PLLEN/STB bit24/25 | `gd32vf103_rcu.h:67-68 / :71-72` |
| 默认 `__SYSTEM_CLOCK_108M_PLL_HXTAL` | `system_gd32vf103.c:62` |
| VF103 的 WSCNT 只有 0/1/2 三档有效（011~111 保留），须 WSEN 使能 | **GD32VF103 UM EN V1.0 §2.4.1 已核验**（p40）；FMC 基址 0x4002 2000 |
| 108M 档实际等待拍数 | UM 不给"频率↔等待"映射表（已检索）——**待上板实测** |

## 你做到了

- 工具链从 ARM 换到 RISC-V，编译标志两套差异、multilib 选择都讲得出来；
- 启动文件逐段对照 B4，知道哪节删了（FPU）、哪节换了写法（搬数据指令）、哪节完全照搬（清 bss、调 main）；
- RISC-V 复位"sp 自己设、PC 由 reset 装入"的机制入肌肉记忆，不再误以为有"硬件两读"。

工序单对上：搬 .data、清 .bss 同义换指令，ldr/str 那套换成 la 与 lw/sw；调 SystemInit、进 main 工序照旧。背面另两行空缺：一是"开 CPACR"那一节整个消失，RV32IMAC 没有 FPU，硬浮点编译选项根本不存在；二是复位不做"硬件两读"，PC 由复位向量直接装入，sp 由启动代码显式设好。这就是架构差异落在启动文件上的分量。

<div class="achievement">
✅ 下一站：<a href="06-clic-irq.html">V1 Bumblebee 内核与 CLIC 中断</a>：去看没有 NVIC 的世界里，向量怎么"直跳"。
</div>
