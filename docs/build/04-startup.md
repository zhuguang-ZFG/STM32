---
title: B4 启动过程：上电到 main 的每一条指令
status: done
difficulty: 3
minutes: 30
---

# B4 启动过程：从复位向量到 main

> 🎯 按一下复位，到你的 `main()` 跑起来，中间其实只有**十几条指令**。就是它们，完成了栈的准备、FPU 的开门、全局变量的搬家、空房间的清零。这十几条指令，是 C 世界的"接生婆"，值得一条条过目。

## 本章精髓

1. 硬件只做两件事：从 0 号地址读初始 MSP、从 4 号地址读 PC，剩下的全是软件的事（这就是"启动文件"存在的理由）。
2. Reset_Handler 的四道工序：**使能 FPU**（CPACR，硬浮点编译的生死开关）→ 搬 .data（Flash→RAM）→ 清 .bss → 跳 main：[C1](../c/01-memory-model.md) 的"三段旅程"在这里闭环。
3. Boot 引脚决定"0 号地址是谁"：用户 Flash / 系统 Bootloader / SRAM 三种映射的区别（霸天虎正常就是从用户 Flash 启）。

- **能理解**：指出"全局变量天生有初值"这句话背后，初值存在哪、由谁搬到变量的位置（第三节的搬家现场）。
- **能用**：打开 [startup_stm32f407xx.s](https://github.com/zhuguang-ZFG/mcu/blob/main/code/stm32/00-blink/startup_stm32f407xx.s) 逐行讲出每条指令在干什么，并在 GDB 里从复位单步验证。

## 先修

- [B3 链接脚本](03-linker-script.md)（五个符号）、[C6 调用约定](../c/06-abi-stack.md)（可读）。

## 先跑起来（10 分钟 quick win）

`make gdb` 后在 GDB 里：

单步之前先押个数：从复位到进入主函数，中间隔着几条指令？十几、几十、还是几百？押完一条条数过去，看实际数字离你的直觉有多远。

```gdb
monitor reset halt    # 停在 Reset_Handler 第一条指令
x/2xw 0x08000000      # 看向量表头两项：栈顶值 + Reset_Handler 地址
si                    # 一条条单步，info registers sp pc 跟着看
```

## 动画：复位之后一毫秒

七站流水线循环播放：硬件两读 → 开 FPU → 搬 .data → 清 .bss → bl main。盯紧那三个橙色小方块，它们就是全局变量的初值在"搬家"。

![启动时序动画](/anim/boot-sequence.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、硬件的两读 | 0 号地址/4 号地址；MSP 与 PC 的分工 | 配置 |
| 二、使能 FPU | CPACR 的 CP10/CP11 置位；不做它，第一条 FPU 指令就 UsageFault(NOCP) | 配置 |
| 三、搬家 .data | 搬运循环五条指令逐条讲 | 代码分析 |
| 四、清零 .bss | C 标准的"零初始化"承诺谁来兑现 | 代码分析 |
| 五、跳 main 与返回 | bl main 之后 main return 去哪 | 代码分析 |
| 六、Boot 引脚 | BOOT0/BOOT1 与三种地址映射 | 配置 |
| 七、weak 向量表 | 默认死循环 + 同名覆盖机制 | 库解析 |

## 一、硬件的两读：上电第一纳秒

五站流水线先收进一张图：前四站挤在 Reset_Handler 里，第五站一出去就是 C 世界。

![启动五站流水线：硬件两读、开 FPU、搬 .data、清 .bss、bl main](/arch/boot-sequence.png)

复位松手那一刻，CPU 醒来了：RAM 里是上电垃圾，没有操作系统，没有 C 世界，连栈都没有。硬件（注意，是**硅片里的硬逻辑**，不是任何程序）只会做两件事：

1. 从 **0 号地址**读 4 字节，塞进 **MSP**（主栈指针）；
2. 从 **4 号地址**读 4 字节，塞进 **PC**（程序计数器），开始取指。

"0 号地址是谁"由 BOOT 引脚的映射决定（第六节细讲）；正常情况它就是用户 Flash 0x08000000 的**别名**。所以 Flash 最前面必须躺一张向量表，头两项长这样（摘自我们的启动文件）：

```asm
g_pfnVectors:
  .word _estack        /* 0x00 初始 MSP */
  .word Reset_Handler  /* 0x04 复位入口 */
  .word NMI_Handler
  .word HardFault_Handler
  /* ...共 16 项内核 + 82 项外设中断（RM0090 §12.2，IRQn 0..81） */
```

> **【注】为什么第 0 项不是指令而是栈顶值？** 因为 C 函数调用要用栈保存现场，而栈指针得先有着落：硬件先把"拐杖"递给你，才让你走路。顺序不能反。

> **【注】复位后 CPU 用 MSP 跑。** 等 FreeRTOS 上场，任务会改用 PSP，MSP 留给内核与中断，[F2 上下文切换](../rtos/freertos/02-context-switch.md)会接着讲这条线。

## 二、第 0 步：使能 FPU——编译器与硬件的契约

Makefile 里写着 `-mfloat-abi=hard -mfpu=fpv4-sp-d16`：这是**编译器的信念**："FPU 随时可用，浮点运算直接生成 FPU 指令"。但复位后硬件的默认状态是：**CP10/CP11（FPU 协处理器）关闭**。编译器的信念和硬件的现实之间，差一道开门手续（PM0214 §4.6.6）：

```asm
  ldr   r0, =0xE000ED88        /* SCB->CPACR */
  ldr   r1, [r0]
  orr   r1, r1, #(0xF << 20)   /* CP10/CP11 全权限（bit20~23） */
  str   r1, [r0]
  dsb                          /* 数据同步屏障：写必须生效 */
  isb                          /* 指令同步屏障：后续取指重新来 */
```

漏了这一步会怎样？第一条 FPU 指令触发 **UsageFault(NOCP)**——灯不闪、串口无声、没有任何"报错弹窗"，程序悄悄死在 fault handler 里。这是硬浮点工程最阴的坑，所以它是启动的**第 0 步**，排在搬家清零之前（与 ST 官方 SystemInit 同款）。

## 三、搬家：.data 的 Flash→RAM 之旅

"全局变量天生就有初值"，这是 C 给你的承诺，但硬件不认账。先看两处位置：初值**存**在 Flash（占空间、断电不丢），变量**用**在 RAM（可读写）。把初值从前一处搬到后一处，是启动代码的工作；下面就是负责搬运的循环（启动文件原文）：

```asm
  ldr   r0, =_sdata        /* RAM 目标起点 */
  ldr   r1, =_edata        /* RAM 目标终点 */
  ldr   r2, =_sidata       /* Flash 源起点 */
  movs  r3, #0
  b     .L_check_copy
.L_copy_loop:
  ldr   r4, [r2, r3]       /* 从 Flash 读一个字 */
  str   r4, [r0, r3]       /* 写到 RAM     */
  adds  r3, r3, #4
.L_check_copy:
  adds  r4, r0, r3
  cmp   r4, r1
  bcc   .L_copy_loop
```

| 指令 | 在干什么 | 为什么 |
|---|---|---|
| `ldr r0, =_sdata` 等三条 | 把链接脚本给的三个边界装进寄存器 | 搬家先得知道：从哪、到哪、搬多长 |
| `movs r3, #0` | r3 = 偏移量，从 0 开始 | 用"基址+偏移"寻址，一份代码通吃任意长度 |
| `ldr r4, [r2, r3]` / `str r4, [r0, r3]` | 读 Flash 一字 → 写 RAM 一字 | 搬运本体，每次 4 字节 |
| `adds r3, r3, #4` | 偏移前进一个字 | |
| `cmp r4, r1` / `bcc` | 目标地址到 `_edata` 了吗？没到继续 | 先判断后干活（`b .L_check_copy` 开局直跳），**长度为零的 .data 也安全** |

三个符号都是链接脚本给启动文件用的地址：`_sidata = LOADADDR(.data)` 指向 Flash 中的初值起点，`_sdata`/`_edata` 给出 .data 段在 RAM 的头尾。把这两处位置放在一起看，`>RAM AT> FLASH` 表达的就是"运行在 RAM，初值存 Flash"。

## 四、清零：.bss 的归零仪式

没写初值的全局变量（`static int cnt;`），C11 标准（§6.7.9）承诺它们是 0。这批变量住 .bss 段，**不占 Flash 一个字节**（初值全是 0，仓库不存货），启动时现场清零：

```asm
  ldr   r2, =_sbss
  ldr   r4, =_ebss
  movs  r3, #0
  b     .L_check_zero
.L_zero_loop:
  str   r3, [r2], #4       /* 写 0，r2 自动 +4 */
.L_check_zero:
  cmp   r2, r4
  bcc   .L_zero_loop
```

比搬家循环还瘦：源操作数都不需要，一路 `str r3` 扫过去。删掉这段"优化"会怎样？全局变量全是上电垃圾值，bug 玄学到怀疑人生。而且这种 bug **换块板子、换个温度就变样**。

## 五、进 C 世界与"main 不能 return"

```asm
  bl    main
.L_hang:
  b     .L_hang
```

`bl main`——C 世界开门营业。注意第二行：裸机的 `main` **没有命令行可以退回**。它真敢 return，就掉进 `.L_hang` 原地转圈，等看门狗或调试器收尸。所以裸机 main 的标配是 `while(1)`，return 是事故不是设计。

## 六、Boot 引脚：0 号地址是谁

第一节说"0 号地址由 BOOT 引脚决定"，F4 这里三选一：

| BOOT0 | BOOT1(PB2) | 0 号地址映射到 | 用途 |
|---|---|---|---|
| 0 | × | 用户 Flash（0x08000000） | **日常**：跑你的固件 |
| 1 | 0 | 系统存储器（0x1FFF0000） | ST 出厂 ISP bootloader：串口/USB DFU 烧录，**救砖专用** |
| 1 | 1 | 内部 SRAM（0x20000000） | 调试花活：固件下 RAM 里跑，不烧 Flash |

霸天虎板子上 BOOT0 跳帽默认接 GND（下拉），所以一上电就跑你的固件。哪天"烧录把芯片锁死了"，把 BOOT0 接高从 ISP 启动，就是留的后门。

## 七、weak 向量表：同名覆盖的温柔机关

向量表 98 项，绝大多数中断你这辈子都用不到，它们的默认出口全是 `Default_Handler: b .`（原地死循环，调试时一眼能抓到"谁闯进来了"）。机关在于每个默认处理函数都是 **weak 符号**（启动文件尾部 `IRQ_DEFAULT` 宏批量定义）：

**你在任何 C 文件里写个同名函数，链接器就悄悄"顶掉"默认实现**，不用改启动文件一个字：

```c
void SysTick_Handler(void) {  /* 你写的强符号，覆盖 weak 默认 */
    tick++;
}
```

## 记忆锚点

::: tip 一句话记住
**上电两读定生死，开门搬家再清零，bl 一声进 main；向量表头不是代码是栈顶，第二条才是入口。**
:::

**延伸**：启动过程与 IAP 跳转（[S13](../stm32/13-flash-iap.md)）同构；`.data` 搬运与内存模型（[C1](../c/01-memory-model.md)）直接对应；调用约定（[C6](../c/06-abi-stack.md)）决定 main 入口的栈帧布局。

## 实物实验

- 在 main 里定义 `volatile int g = 0x12345678;`，GDB 从复位单步：搬运循环结束后 `x/wx &g` 应为 `0x12345678`。那一刻，就是"搬家完成"的现场。
- 进阶：把 CPACR 那五行注释掉重烧，main 里加一行 `volatile float f = 1.5f * 2.0f;`，观察程序卡死，再用 GDB 读 SCB->CFSR 的 NOCP 位，亲手抓到"门没开"的现场。

## 常见坑

- **换芯片忘换启动文件**：F407 有 98 项向量（16 内核 + 82 外设），F103 按密度只有 59~76 项（C8 中密度 59，ZE 高密度 76）。用错启动文件，中断号对不上，直接 HardFault 或行为诡异。
- **在 Reset_Handler 之前下断点**：那是硬件行为，断不住。调试从 `monitor reset halt` 开始才对。
- **把 .data 搬运删掉"优化"**：全局变量初值全无，bug 隐蔽到怀疑人生。
- **BOOT0 悬空/接错**：从系统存储器启动了，你的固件"没被运行"（霸天虎 BOOT0 默认下拉，自己飞线时注意）。
- **硬浮点工程忘开 CPACR**：第一条 FPU 指令 UsageFault(NOCP)，静默卡死（本章第二节）。

## 短自测

1. 向量表第 0 项是什么？为什么不能是指令？
2. 硬浮点工程忘了开 CPACR，运行时会发生什么？
3. .data 的初值存在哪、运行在哪、谁负责搬？
4. BOOT0=1、BOOT1=0 时 CPU 从哪启动？这个模式拿来干嘛？

<details><summary><b>参考答案（先自己想完再展开）</b></summary>

1. 初始 MSP 值。没栈就没法保存现场、没法函数调用：硬件先把拐杖递上，才让你走路。
2. 第一条 FPU 指令触发 UsageFault(NOCP)，程序静默卡死，没有任何直观报错。
3. 初值存 Flash（`_sidata`），变量运行在 RAM（`_sdata`..`_edata`），Reset_Handler 的搬运循环负责搬。
4. 系统存储器 0x1FFF0000 的 ST 出厂 ISP bootloader：串口/USB DFU 烧录，救砖后门。

</details>

## 对照表：本章概念 → 仓库落点

| 本章说的 | 仓库里哪一行 |
|---|---|
| 向量表头两项 | [startup_stm32f407xx.s](https://github.com/zhuguang-ZFG/mcu/blob/main/code/stm32/00-blink/startup_stm32f407xx.s) `g_pfnVectors` 开头 |
| 使能 FPU 五条 + dsb/isb | 同文件 Reset_Handler 第 0 步 |
| 搬家循环五条指令 | 同文件 `.L_copy_loop` |
| `_estack` / `_sidata` / `_sdata` / `_edata` | [stm32f407xx.ld](https://github.com/zhuguang-ZFG/mcu/blob/main/code/stm32/00-blink/stm32f407xx.ld) 第 16 / 88-97 行 |
| weak 同名覆盖 | 启动文件尾部 `IRQ_DEFAULT` 宏 |
| Boot 三映射 | [hardware.md](../guide/hardware.md) 板卡资料 |

## 你做到了

- 上电到 main 的每一纳秒都讲得出来；
- 启动文件从此不是"官方给的神秘文件"，是你可以逐行批改的自己人；
- 再听到"全局变量天生有初值"，你会心一笑：那是十几条指令搬出来的。

开场那位「接生婆」，你现在能一条条报名字了：硬件的两读、给浮点单元开的门、搬家的循环、清零的循环，最后才轮到你的代码出场。所谓「全局变量天生有初值」，其实是这十几条指令在人没有到场时就把家搬好了。

<div class="achievement">
✅ 下一站：<a href="05-map-size.html">B5 map 与体积</a>：固件 200 字节还是 200KB，这笔账该谁认？
</div>
