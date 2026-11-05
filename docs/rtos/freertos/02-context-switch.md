---
title: F2 上下文切换：PendSV 换魂术
status: done
difficulty: 3
minutes: 40
---

# F2 上下文切换：PendSV 逐汇编指令

> 🎯 两个任务"同时在跑"的幻觉，每毫秒发生一次偷梁换柱：把当前任务的魂（寄存器）抽走封进它的栈，把下一个任务的魂从它的栈里请回来。执刑官是 PendSV——全系统优先级最低的中断。本章把这段编出来只有 **27 条机器指令、104 字节**的 naked 函数逐行过堂。

动手前先押个响不响：断点压在内核源码写的 xPortPendSVHandler 上，切一次任务，断得住吗？押完进第五节的目击实验亲手试。

## 本章精髓

1. 为什么是 PendSV 且必须最低：切换要等所有中断服完役才进行，否则 ISR 被"切走一半"就乱套：最低优先级保证 PendSV 永远最后执行。**而且这个"最低"不用你配**：V11 的 ARMv7-M 移植层自己硬写成 255，`configKERNEL_INTERRUPT_PRIORITY` 在这个端口上是不被读取的死宏（第一节翻案）。
2. 切换就两个动作：**存**（当前任务的 r4-r11 软件补压 + 栈顶存进 TCB）与**取**（从下个任务 TCB 取栈顶 + r4-r11 弹回），硬件帧（r0-r3 等）由异常进出自动完成，软件只需管 r4-r11。
3. 选择下一个任务靠 `pxCurrentTCB` 换指针：`vTaskSwitchContext` 只是改了这个全局变量，PendSV 按新值取栈，"换魂"完成。
4. **源码名和板子上的名字不是一回事**：内核里写的是 `xPortPendSVHandler`，`FreeRTOSConfig.h:76` 一行 `#define xPortPendSVHandler PendSV_Handler` 把它改名，启动文件向量表里躺着的才是 `PendSV_Handler`，GDB 断点要断后者，断前者什么都断不到（第五节踩过）。

- **能理解**：为什么硬件管一半、软件管另一半（第二节，AAPCS 的账）。
- **能用**：在 GDB 里给 PendSV 打断点，把动画里的每一帧在真板上找到（第五节，注意断点要断改名后的符号）。

## 先修

- [F1 任务与 TCB](01-task-tcb.md)、[S4 中断现场](../../stm32/04-nvic-exti.md)、[C6 调用约定](../../c/06-abi-stack.md)。

## 动画：换魂全程

TaskA 的魂（r4-r11）被压进它自己的栈、栈顶藏进 TCB；换指针；TaskB 的魂从它的栈里弹回，注意两个栈此消彼长，CPU 还是那个 CPU。

![上下文切换动画](/anim/context-switch.svg)

## 配套视频

<VideoEmbed type="bilibili" id="BV1Jx411X7NS" title="野火《FreeRTOS 内核实现与应用开发实战指南》配套视频（42 集，从 0 到 1 写内核）" />

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、PendSV 定位 | 为什么最低优先级；与 SysTick 的配合 | 配置 |
| 二、软硬分工 | 硬件帧 vs r4-r11：AAPCS 的账（回 C6） | 代码分析 |
| 三、汇编逐行 | 十一条语义步骤、编出来 27 条指令，逐条过堂 | 库解析 |
| 四、换指针即换魂 | vTaskSwitchContext 与 TCB 第一成员 | 库解析 |
| 五、GDB 目击 | 断点 + 双任务栈对照实验（含名字改名坑） | 代码分析 |
| 六、第一帧是伪造的 | 没跑过的任务，栈帧由 pxPortInitialiseStack 手工造 | 库解析 |

## 一、PendSV 定位：执刑官为什么永远最后上场

SysTick 每 1ms 来一次，但它的活只是**报案**：`xTaskIncrementTick()` 发现"有更高优先级任务就绪了"，就写一笔挂起位：

```
ICSR（0xE000ED04）bit28 = PENDSVSET：把 PendSV 异常挂起
```

报案这条在本机两份源码里都能对上号，不用背：

```c
/* portmacro.h:99-100 —— 寄存器地址和位号就是章首那行写的 0xE000ED04 / bit28 */
#define portNVIC_INT_CTRL_REG   ( *( ( volatile uint32_t * ) 0xe000ed04 ) )
#define portNVIC_PENDSVSET_BIT  ( 1UL << 28UL )

/* portmacro.h:91 —— portYIELD_WITHIN_API() 的全部动作，就是写这一笔 */
portNVIC_INT_CTRL_REG = portNVIC_PENDSVSET_BIT;
```

位号本身另有架构出处：CMSIS 的 `core_cm4.h:490` 写死 `SCB_ICSR_PENDSVSET_Pos = 28U`（同文件 `:487` 的 `NMIPENDSET_Pos` 才是 31U，别记混）。

而"最低优先级"也不是只写在配置文档里，是启动时真写进去的两行（`port.c:434-435`）：

```c
portNVIC_SHPR3_REG |= portNVIC_PENDSV_PRI;    /* port.c:66 → portMIN_INTERRUPT_PRIORITY << 16 */
portNVIC_SHPR3_REG |= portNVIC_SYSTICK_PRI;   /* port.c:67 → portMIN_INTERRUPT_PRIORITY << 24 */
```

`portMIN_INTERRUPT_PRIORITY` 就是 `configKERNEL_INTERRUPT_PRIORITY`（255），Shift 16 / 24 对应 SHPR3 里 PendSV 与 SysTick 各自的 8 位槽，两个都填满 0xFF，全系统最低。

真正的执法交给 PendSV。为什么绕这一手？因为 SysTick 优先级高，**若在 ISR 堆里直接切换，等于把某个中断服务程序切走一半**：外设寄存器读到一半、标志位清到一半，回来全乱。PendSV 的优先级是 **0xFF，全系统最低**：上面 `:434` 那两行就是写这个值的现场：它永远排队到最后，等所有 ISR 收队完毕，才出来执行切换。

> **【注】"把 `configKERNEL_INTERRUPT_PRIORITY` 配错"这个坑，在 ARMv7-M 的新内核上已经不存在了。** 本仓库用的 V11.1.0 里，内核自己把两个优先级硬写成最低（`port.c:65` `portMIN_INTERRUPT_PRIORITY ( 255UL )` → `:434-435` 落到 SHPR3），**根本不读这个宏**。内核自己的变更记录把话说得很白（`History.txt:301-303`）：*"Update ARMv7-M ports to ensure that kernel interrupts run at the lowest priority. configKERNEL_INTERRUPT_PRIORITY is now obsolete for ARMv7-M ports."* 所以本站工程里 `FreeRTOSConfig.h:61` 那行 255 是一段无害的死代码，留着是为了兼容老教程的口径，删了也不会有行为变化。
>
> **真正会炸的是 `configMAX_SYSCALL_INTERRUPT_PRIORITY`**，它被 `:525` 的 `mov r0, %0` 代进汇编、又被 `vPortSetupTimerAndInterrupts` 连查三遍（`configASSERT_DEFINED == 1` 时）：
>
> | 断言 | 出处 | 配错的后果 |
> |---|---|---|
> | `configASSERT( ucMaxSysCallPriority )` | `port.c:379` | 填 0 → 优先级比所有中断都高，临界区关不掉任何东西 |
> | `( configMAX_SYSCALL_INTERRUPT_PRIORITY & ~ucMaxPriorityValue ) == 0` | `port.c:383` | 写了超出硬件优先级位宽的数 → 低位被吃掉，语义漂移 |
> | `( configMAX_SYSCALL_INTERRUPT_PRIORITY & 0x1U ) == 0` | `port.c:413` | 填奇数 → 某些芯片上会漏掉一批本该被屏蔽的中断（注释举例：设成 5 时 4 和 5 的行为反直觉） |
>
> **开机就断言炸，比"一周崩一次"好得多**。老说法里那个"偶发灵异 bug"，今天的形态是启动即死，除非你把 `configASSERT` 定义成空，那它才会退化成人格分裂式的偶发崩溃。常见坑一节还会点名。

## 二、软硬分工：硬件管一半，软件管另一半

先看分工图：左列是芯片免费送的，右列是 xPortPendSVHandler 一条条汇编挣来的。

![PendSV 换魂软硬分工：八寄存器压栈与 PSP 切换归硬件，R4-R11 存 TCB 与换 PSP 归软件](/arch/context-switch.png)

异常入场时，硬件已自动压好 8 个字的**硬件帧**（[S4 动画](../../stm32/04-nvic-exti.md)演示过）：xPSR、PC、LR、R12、R3~R0。这是 AAPCS 的"调用者保存"部分，硬件替你管了。

那 **r4-r11** 呢？AAPCS 说它们是"被调者保存"：函数要用就自己存。硬件不认识这个约定，所以 PendSV 里**软件手工补压 r4-r11**。软硬两半合起来，才是一个任务完整的"魂"。

FPU 再加一层：若任务用过浮点（EXC_RETURN **bit4 = 0** 为证），硬件帧会扩展带上 s0-s15+FPSCR，软件还要加存 **s16-s31**。

> **【注】懒堆叠（lazy stacking）**：M4F 的 FPCCR（LSPEN 默认开）让硬件"先占座、后写真"：入场时先给 FPU 帧**预留空间**，真用到 FPU 才写数，大多数不用浮点的中断省下这笔开销。所以 EXC_RETURN bit4 是"这趟有没有 FPU 行李"的牌子。

## 三、汇编逐行：xPortPendSVHandler 过堂

以下摘自本机 `.trellis/ref/freertos-v11/kernel` 的 FreeRTOS-Kernel **V11.1.0** `portable/GCC/ARM_CM4F/port.c:509-556`（M4F + GCC 移植层的 naked 内联汇编，注释为本章所加）。两处转写与本仓库真实源码不同，注意分辨：② 号源码写 `ldr r3, pxCurrentTCBConst`（`:514`），这里写成教学常见的 `=pxCurrentTCB`；⑥ 号源码写 `mov r0, %0`（`:525`），操作数在 `:557` 由 `"i" ( configMAX_SYSCALL_INTERRUPT_PRIORITY )` 代入，所以编出来是一个硬立即数，下面实测段会看到它落地成 `#80`：

```asm
mrs   r0, psp                ; ① 取出当前任务的栈顶（PSP）
isb
ldr   r3, =pxCurrentTCB      ; ② r3 = &pxCurrentTCB
ldr   r2, [r3]               ;    r2 = 当前任务的 TCB
tst   r14, #0x10             ; ③ 这趟有 FPU 行李吗（EXC_RETURN bit4=0）？
it    eq
vstmdbeq r0!, {s16-s31}      ;    有：先把 FPU 高 16 寄存器压栈
stmdb r0!, {r4-r11, r14}     ; ④ 软件帧：r4-r11 + EXC_RETURN 压进任务栈
str   r0, [r2]               ; ⑤ 新栈顶存进 TCB 第一个成员——封棺！
stmdb sp!, {r0, r3}          ;    （保护现场，进临界区）
mov   r0, #configMAX_SYSCALL_INTERRUPT_PRIORITY
msr   basepri, r0            ; ⑥ 临界区：屏蔽低优先级中断
dsb
isb
bl    vTaskSwitchContext     ; ⑦ 换指针：pxCurrentTCB = 下一个任务
mov   r0, #0
msr   basepri, r0            ;    出临界区
ldmia sp!, {r0, r3}
ldr   r1, [r3]               ; ⑧ r1 = 新 TCB（pxCurrentTCB 已换人）
ldr   r0, [r1]               ;    r0 = 新任务的栈顶
ldmia r0!, {r4-r11, r14}     ; ⑨ 还魂：软件帧从新任务栈弹回
tst   r14, #0x10
it    eq
vldmiaeq r0!, {s16-s31}      ;    FPU 行李也领回
msr   psp, r0                ; ⑩ PSP 指向新任务的栈顶
isb
bx    r14                    ; ⑪ 异常返回：硬件弹出硬件帧，新任务复活
```

| 步骤 | 指令 | 一句话 |
|---|---|---|
| ① | `mrs r0, psp` | 当前任务的栈顶在哪？（线程用的是 PSP，不是 MSP） |
| ② | `ldr r3/ldr r2` | 拿到"当前任务档案"TCB |
| ③ | `tst + it + vstmdb` | 有 FPU 行李就先托运 s16-s31 |
| ④ | `stmdb {r4-r11, r14}` | 软件帧入栈——魂魄抽离 |
| ⑤ | `str r0, [r2]` | **栈顶存进 TCB 第一个成员**——为什么敢写偏移 0？第四节揭晓 |
| ⑥ | `basepri` | 换指针时要安静：临界区 |
| ⑦ | `bl vTaskSwitchContext` | 全剧就这一句：换个全局指针 |
| ⑧⑨ | `ldr/ldmia` | 新 TCB → 新栈顶 → 魂魄归还 |
| ⑪ | `bx r14` | 异常返回，硬件弹硬件帧——**新任务从它上次停下的那条指令接着跑** |

### 这十一条编出来是多少条？本机实测

源码是十一个语义步骤，编译器会把 `ldr r3, =pxCurrentTCB` 拆成真指令、给 naked 函数补对齐。`code/rtos/01-freertos-lab/probe.sh` 第 2 步直接数 `bx lr` 之前的指令行：

```
  正文指令条数 = 27 条（数到 bx lr 为止，后面的 nop 填充与字面量池不算）
  段大小 = 104 字节（含对齐填充和 pxCurrentTCBConst 字面量）
```

27 条按十一段落地的分布（`probe.sh` 第 2 步的完整反汇编就在这段前面，可逐条对）：

| 段 | 指令 | 条数 | 编译器多做了什么 |
|---|---|---|---|
| ① | `mrs PSP` + `isb` | 2 | — |
| ② | `ldr r3,[pc,#84]` + `ldr r2,[r3,#0]` | 2 | 源码 `port.c:514` 写的是 `ldr r3, pxCurrentTCBConst`（字面量池符号，`:556` 那行 `.word pxCurrentTCB` 就是它读的地址）；本章上面转写成教学常见的 `ldr r3, =pxCurrentTCB` |
| ③ | `tst.w lr,#16` + `it eq` + `vstmdbeq` | 3 | `#0x10` 打印成十进制 16 |
| ④⑤ | `stmdb` 9 字 + `str [r2,#0]` | 2 | — |
| — | `stmdb sp!, {r0, r3}` | 1 | 进临界区前先保 r0/r3，源码有、上表没单列 |
| ⑥ | `mov #80` + `msr BASEPRI` + `dsb` + `isb` | 4 | — |
| ⑦ | `bl vTaskSwitchContext` | 1 | — |
| — | `mov #0` + `msr BASEPRI` + `pop {r0, r3}` | 3 | 出临界区，同上 |
| ⑧ | `ldr r1,[r3,#0]` + `ldr r0,[r1,#0]` | 2 | — |
| ⑨ | `ldmia` 9 字 + `tst` + `it` + `vldmia` | 4 | — |
| ⑩⑪ | `msr PSP` + `isb` + `bx lr` | 3 | `bx r14` 打印成 `bx lr`（r14 就是 lr） |

合计 2+2+3+2+1+4+1+3+2+4+3 = **27**。字节账也对得上：27 条里有 9 条是 16 位 Thumb 编码（`4b15`/`681a`/`bf08`/`6010`/`bc09`/`6819`/`6808`/`bf08`/`4770`），所以正文只占 9×2 + 18×4 = **90 字节**（`0x00`–`0x5a`）；`objdump -s` 看尾部：`0x5a`/`0x5c` 是 `port.c:555` 那句 `.align 4` 补的两条 nop（6 字节），`0x60` 是 4 字节的 `pxCurrentTCBConst` 字面量，`0x64` 再两条 nop 凑到 8 字节对齐：**90 + 6 + 4 + 4 = 104**，正是 `size -A` 报的段大小。

数字会随工具链浮动，**账不在条数而在"一次切换只走这一段直线代码，没有循环、没有函数内的分支跳转"**（`tst/it` 那两条是条件执行，不改变控制流），所以第四节才敢说百周期量级。

三行最该亲眼看到的指令（`probe.sh` 第 3 步）：

```asm
  16:  e920 4ff0   stmdb  r0!, {r4, r5, r6, r7, r8, r9, sl, fp, lr}   ; ④ 一条指令 9 个字 = 36 字节
  1a:  6010        str    r0, [r2, #0]                                ; ⑤ 偏移 0——凭据见第四节
  20:  f04f 0050   mov.w  r0, #80    ; 0x50                           ; ⑥ = 5 << (8 - configPRIO_BITS)
```

`stmdb` 那一行是整章最贵的一条：一条指令写 9 个字。⑥ 的立即数在源码里写作宏，编出来是硬碰硬的 `#80`：`configPRIO_BITS` 是 4（F407 有 4 个优先级位），所以 `5 << 4 = 80`。`probe.sh` 第 4 步把这条账的两个来源并排打出：`FreeRTOSConfig.h:61` 的 `configKERNEL_INTERRUPT_PRIORITY 255` 和 `:62` 的 `(5 << (8 - configPRIO_BITS))`。

## 四、换指针即换魂

`vTaskSwitchContext`（tasks.c）的核心动作只有一步：`pxCurrentTCB = 最高优先级就绪任务的 TCB`（怎么选出最高的？位图 + CLZ 一条指令，[F3 调度器](03-scheduler.md)细讲）。

⑤ 号指令 `str r0, [r2]` 为什么敢往偏移 0 写？因为 FreeRTOS 立下铁律：**TCB 结构体的第一个成员永远是 `pxTopOfStack`**。这条铁律不是口口相传，内核源码里就写在成员自己的注释上（`tasks.c:360`，本机 `.trellis/ref/freertos-v11/kernel` 实测行号）：

```c
volatile StackType_t * pxTopOfStack; /**< Points to the location of the last item placed on the tasks stack.
                                          THIS MUST BE THE FIRST MEMBER OF THE TCB STRUCT. */
```

偏移 0 就是栈顶的家——封棺与起棺都从这进门。反汇编里三处 `#0` 全都指向同一个约定：`ldr r2, [r3, #0]`（取当前 TCB）、`str r0, [r2, #0]`（封）、`ldr r1, [r3, #0]` + `ldr r0, [r1, #0]`（起）。

顺带一个容易踩的空格：`include/task.h:171` 也有个同名成员 `pxTopOfStack`，但它属于 `TaskStatus_t`，那是 `uxTaskGetSystemInfo()` 用来给外部看的信息结构，**不是** TCB。移植层要写的偏移 0，永远指 `tasks.c` 里的那个。

整个切换，C 部分只换了一个指针；真正的体力活全在 PendSV 那十一条汇编里。**换指针是决策，PendSV 是执行**：决策与执行分离，这就是 FreeRTOS 切换设计的全部智慧。

> **【注】切换有多快？** M4 @168MHz 下一次完整切换是**百周期量级**，微秒不到，"RTOS 开销大"的直觉多为谣言，[F7](07-heap.md) 会算这笔账。

## 五、GDB 目击实验

双任务各闪一灯（E 系列实验工程），把动画的每一帧在真板上抓到。

**先解决名字**：断点必须断在向量表里那个名字上，不是内核源码里那个。本工程三层对应关系（`probe.sh` 第 1 步一次打全，含 `nm` 的实际符号）：

```
port.c:505        void xPortPendSVHandler( void )        ← 内核源码写的名字
FreeRTOSConfig.h:76  #define xPortPendSVHandler PendSV_Handler  ← 一行改名
startup_stm32f407xx.s:111  .word PendSV_Handler          ← 向量表躺的是这个
nm port.o         00000000 T PendSV_Handler              ← 编出来只剩这个
```

改名之后 `xPortPendSVHandler` 在目标文件里根本不存在，`b xPortPendSVHandler` 会直接报 "Function not defined"（或者更坑：某些前端默默接受然后永不命中）。

```gdb
b PendSV_Handler          # 断在换魂入口——用向量表的名字，不是源码的名字
p pxCurrentTCB            # 旧任务 TCB 地址
p/x $psp                  # 此刻 PSP 指硬件帧最低字（R0）——软件帧还没压
x/8xw $psp                # 硬件帧 8 字：R0 R1 R2 R3 R12 LR PC xPSR（回 S4）
stepi 8                   # 走到第 9 条 str r0, [r2, #0]（断下时它还没执行）
p/x $r0                   # ④ 压完之后的任务栈顶。注意：PSP 到 ⑩ 才改，这里只能看 r0
x/9xw $r0                 # 软件帧 9 字：r4 r5 r6 r7 r8 r9 sl fp lr(EXC_RETURN)
x/8xw $r0+36              # 紧接其上就是硬件帧，$r0+36 应当等于 $psp
finish                    # 跑完整个 handler
p pxCurrentTCB            # 已换人！对比两次地址
```

三个容易读错的点：

- **别在入口读软件帧**。`stmdb r0!` 改的是 r0，不是 PSP，PSP 直到 ⑩ 那条 `msr PSP, r0` 才被更新。所以想看 ④ 的成果，必须 `stepi` 过 ④ 再读 `$r0`，读 `$psp` 只会读到旧值。
- **`x/9xw` 不是 `x/8xw`**。软件帧数下来 9 个字：r4~r11 八个 + EXC_RETURN 一个。第 3 步的寄存器列表 `{r4, r5, r6, r7, r8, r9, sl, fp, lr}` 正好 9 项，`sl` 是 r9、`fp` 是 r11 的 ABI 别名（[C6](../../c/06-abi-stack.md) 见过）。
- **`$r0+36 == $psp` 这条等式只在没有 FPU 行李时成立**。若 ③ 走了 `eq` 分支（任务跑过浮点），`vstmdbeq` 先把 s16-s31 压了 16 个字 = 64 字节，`$r0` 会再低 64。这正是 `tst lr, #16` 存在的理由，也是"同一个任务两次切换栈顶差得不一样"的合法解释。

## 六、没跑过的任务，第一帧是伪造的

前面所有动作都假设"这个任务曾经被切走"。可 `xTaskCreate` 刚建好的任务从没被中断过，**没有硬件会替它压那一帧**。所以第一帧是手工造的：`port.c:202` 的 `pxPortInitialiseStack()` 直接往任务栈里写出一份和"被切走时"形状完全一致的栈帧。

形状必须严格一致，否则 ⑧⑨⑩⑪ 那四条"起棺"指令会读错位置。`probe.sh` 第 5 步把源码里的回退量当场加了一遍：

```
  指针回退 17 个字，加上最后停住的那个落点共 18 个字 = 72 字节
  对得上账：硬件帧 8 + 软件帧 9 + 对齐 1 = 18
```

三个立即数撑起这 18 个字里被真正写入的 5 个（xPSR / PC / LR / R0 / EXC_RETURN）；其余 13 个槽位（1 个对齐空位 + R12/R3/R2/R1 + R4-R11）源码明说 *Save code space by skipping register initialisation*，故意留脏：

| 写进帧的值 | 宏（port.c 行号） | 为什么是它 |
|---|---|---|
| `0x01000000` → xPSR | `portINITIAL_XPSR`（:92） | bit24 = 1。ARMv7-M 规定异常返回时这个保留位必须为 1，它同时就是 THUMB 状态位——新任务从此以 Thumb 模式开跑 |
| `pxCode & 0xfffffffe` → PC | `portSTART_ADDRESS_MASK`（:100） | 清掉函数指针低位的 Thumb bit。Thumb 状态由 xPSR bit24 说，不许 PC 的 bit0 越权——所以 `bic r2, r3, #1` |
| `0xfffffffd` → EXC_RETURN | `portINITIAL_EXC_RETURN`（:93） | bit2=1 出栈用 PSP、bit3=1 回 Thread 模式、**bit4=1 表示这趟没有 FPU 行李**（所以初始帧是 18 个字而不是 26 个） |
| `pvParameters` → R0 | — | 新任务第一次拿到的实参，AAPCS 说整型参数走 r0（[C6](../../c/06-abi-stack.md)） |
| `prvTaskExitError` → LR | `portTASK_RETURN_ADDRESS`（:125 → :234） | 任务函数不许 `return`。真返回了就落进这个"触发 configASSERT + 关中断 + 死循环"的陷阱 |

编译产物里能直接看到前两条（`probe.sh` 第 5 步末尾的 objdump）：

```asm
  14:  f04f 7280   mov.w  r2, #16777216   ; 0x1000000  ← portINITIAL_XPSR
  22:  f023 0201   bic.w  r2, r3, #1                    ← & portSTART_ADDRESS_MASK
```

**这一节的实用价值**：任务函数跑完没死、程序"莫名卡住"、`configASSERT` 在没人预料的地方炸：先怀疑有人 `return` 了，断点打在 `prvTaskExitError` 上。

顺手分清两类符号（`nm build/scene-1/port.o` 实测）：

```
00000000 T PendSV_Handler          ← 大写 T：全局，被宏改过名，源码名已不存在
00000000 T SVC_Handler             ← 同上
00000000 T pxPortInitialiseStack   ← 大写 T：全局，没被改名，源码名 == 符号名
00000000 t prvTaskExitError        ← 小写 t：static 局部符号，没被改名
```

改名只发生在 `FreeRTOSConfig.h:75-77` 那三行宏覆盖的三个 handler 上；`pxPortInitialiseStack`、`prvTaskExitError` 都按源码名直接断即可。

## 记忆锚点

::: tip 一句话记住
**PendSV 最后上场，r4-r11 手工进栈，栈顶藏进 TCB；换个指针换个魂，异常返回新人生。**
:::

## 实物实验

- **不上板也能全过一遍**：`cd code/rtos/01-freertos-lab && sh probe.sh`，五步一条命令跑完（符号改名链、27 条反汇编、三行铁账、优先级账、伪造帧的长度账）。本章每一个数字都出自这里。
- 见第五节 GDB 目击清单；装备：霸天虎板 + FreeRTOS 双任务工程 + ST-Link。
- 进阶：在任务里加一行浮点运算，再观察 `tst r14, #0x10` 走 `eq` 分支，亲眼确认 FPU 行李托运。

## 常见坑

- **中断里调 API 忘 FromISR 版**：普通版 API 在 ISR 里可能直接触发切换，现场混乱，ISR 一律 `xQueueSendFromISR` 家族（[F4 队列](04-queue.md)）。
- **以为还要自己把 PendSV/SysTick 设最低**：V11.1.0 的 ARMv7-M 移植层自己硬写成最低（`port.c:65/434-435`），`configKERNEL_INTERRUPT_PRIORITY` 在这个端口上是**不被读取的死宏**（`History.txt:301-303` 明说 obsolete）。真正要盯的是 `configMAX_SYSCALL_INTERRUPT_PRIORITY`：内核连查三遍（`port.c:379/383/413`），填 0、超出优先级位宽、填奇数都会开机即断言。
- **把 `configASSERT` 定义成空**：上面三道检查全部消失，配置错误就从"启动即死"退化成"一周崩一次的灵异现场"。调试期一定留着。
- **handler 没接到向量表**：`port.c:343-344` 会查 `SVC`/`PendSV` 两个槽是不是指向内核的 handler，这正是 `FreeRTOSConfig.h:75-77` 那三行宏改名的用途（第五节）。直接把 `xPortPendSVHandler` 写进启动文件反而链接不上。
- **栈对齐不是 8 字节**：xPSR 异常入场要求 8 对齐，栈起点错对齐直接 UsageFault（S16 取证）。
- **GDB 里 `b xPortPendSVHandler` 断不上**：这个符号在目标文件里不存在（`FreeRTOSConfig.h:76` 已经把它宏改名为 `PendSV_Handler`），向量表认的是后者（第五节有三层对应表）。同理 `SVC_Handler`、`SysTick_Handler`。
- **任务函数写了 `return`**：没地方可回（源码原话 *there is nothing to return to*），落进 `prvTaskExitError` 关中断死循环（第六节）。要退出就 `vTaskDelete( NULL )`。
- **以为切换很慢**：M4 上一次切换是百周期量级，"RTOS 开销大"的直觉多为谣言。

## 短自测

1. 切换为什么在 PendSV 里做，而不是在 SysTick 中断里直接做？
2. 硬件帧和软件帧各包含哪些寄存器？（FPU 情况各加什么？）
3. `str r0, [r2]` 把栈顶存到了 TCB 的哪里？凭什么敢这么写？
4. `bx r14` 之后硬件做了什么？新任务从哪条指令开始跑？
5. 内核源码里函数明明叫 `xPortPendSVHandler`，为什么 `b xPortPendSVHandler` 断不上？
6. 从没跑过的任务，它的第一帧是谁压的？这帧多大、哪几个字被真正写过？
7. `portINITIAL_EXC_RETURN` 是 `0xfffffffd`，bit4 = 1 说明什么？

<details><summary><b>参考答案（先自己想完再展开）</b></summary>

1. SysTick 优先级高，ISR 堆里直接切换会把某个中断服务切走一半；PendSV 优先级最低（0xFF），等所有 ISR 收队才执法。
2. 硬件帧：R0-R3、R12、LR、PC、xPSR（FPU 加 s0-s15+FPSCR）；软件帧：R4-R11 和 EXC_RETURN（FPU 加 s16-s31）。
3. TCB 第一个成员 `pxTopOfStack`，偏移 0 是 FreeRTOS 的铁律，原文写在 `tasks.c:360` 的成员注释里（*THIS MUST BE THE FIRST MEMBER OF THE TCB STRUCT*）。注意 `task.h:171` 那个同名字段属于 `TaskStatus_t`，不是 TCB。
4. 硬件按 EXC_RETURN 选用 PSP，从任务栈弹出硬件帧；新任务从它上次被切走时的 PC（就在硬件帧里）继续执行。
5. `FreeRTOSConfig.h:76` 有一行 `#define xPortPendSVHandler PendSV_Handler`，预处理阶段就把源码里的名字整体换掉了；向量表（`startup_stm32f407xx.s:111 .word PendSV_Handler`）和 `nm` 里只剩 `PendSV_Handler`。断点要断后者。`SVC_Handler`、`SysTick_Handler` 同理（:75、:77）。
6. `port.c:202` 的 `pxPortInitialiseStack()` 手工造的，形状和"被切走时"完全一致：18 个字 = 72 字节 = 硬件帧 8 + 软件帧 9 + 对齐 1。真正写入的只有 5 个字（xPSR、PC、LR、R0、EXC_RETURN），剩下 13 个槽位故意留脏：省代码空间，反正这些寄存器接下来会被任务自己覆盖。
7. bit4 = 1 表示这趟异常没有 FPU 行李：硬件按 8 字的核心帧出栈，③ 号 `tst r14, #0x10` 也不等零，`vstmdbeq/vldmiaeq` 双双跳过。任务真跑过浮点后被切走，软件侧还要多压 s16-s31 共 16 个字（64 字节）。

</details>

## 对照表：本章概念 → 源码落点

| 本章说的 | 源码里哪里 |
|---|---|
| 换魂十一条语义步骤（编出来 27 条指令 / 正文 90 字节） | FreeRTOS-Kernel V11.1.0 `portable/GCC/ARM_CM4F/port.c:505-559` 的 `xPortPendSVHandler`（naked） |
| `mov r0, %0` 为什么编出来是 `#80` | 同文件 `:525` 的 GCC 扩展汇编操作数 + `:557` 的 `::"i" ( configMAX_SYSCALL_INTERRUPT_PRIORITY )` |
| 换指针 | 同内核 `tasks.c` 的 `vTaskSwitchContext` |
| TCB 首成员铁律（`str r0,[r2,#0]` 的凭据） | `tasks.c:360`（不是 `task.h:171`，那个属于 `TaskStatus_t`） |
| 源码名 → 符号名的改名 | 本工程 `FreeRTOSConfig.h:75-77` + `startup_stm32f407xx.s:111` |
| 新任务第一帧的伪造 | `port.c:202-231` `pxPortInitialiseStack`；三个立即数 `port.c:92/93/100` |
| 任务 `return` 掉进哪 | `port.c:125` `portTASK_RETURN_ADDRESS` → `port.c:234` `prvTaskExitError` |
| PendSV 挂起位 | ICSR = 0xE000ED04，bit28（PENDSVSET）——本机出处：移植层 `portmacro.h:99-100`（`0xe000ed04` / `1UL << 28UL`）与 `:91` 的 `portYIELD_WITHIN_API`；架构侧 `core_cm4.h:490` `SCB_ICSR_PENDSVSET_Pos = 28U` |
| 内核把两个 handler 硬设最低 | `port.c:65` `portMIN_INTERRUPT_PRIORITY ( 255UL )` → `:66-67` → `:434-435` 写 SHPR3 |
| `configKERNEL_INTERRUPT_PRIORITY` 作废 | 内核 `History.txt:301-303`；本机实测该宏在 `ARM_CM4F/port.c` 与 `portmacro.h` 中出现 **0 次** |
| 优先级配置错误的三道断言 | `port.c:379`（非 0）、`:383`（不超出实现的优先级位宽）、`:413`（必须为偶数） |
| handler 有没有真接进向量表 | `port.c:343-344` 查 `SVC`/`PendSV` 两个槽（受 `configCHECK_HANDLER_INSTALLATION` 控制） |
| 栈帧约定 | [C6 调用约定](../../c/06-abi-stack.md) + [S4 中断动画](../../stm32/04-nvic-exti.md) |
| 启动时 MSP 的来历 | [B4 启动过程](../../build/04-startup.md) 第一节 |
| 选最高优先级任务 | [F3 调度器](03-scheduler.md)（位图 + CLZ） |
| 本章所有数字怎么复核 | `code/rtos/01-freertos-lab/probe.sh` 五步一条命令跑完（符号名 / 27 条反汇编 / 三行铁账 / 优先级账 / 伪造帧） |

## 延伸阅读

懒堆叠与异常帧的权威出处：

- **[\[C5\]](../../reference/bibliography.md#toolchain)** AN298 — 懒堆叠（lazy stacking）的官方应用笔记：FPCCR.LSPEN 怎么让硬件"先占座、后写真"、EXC_RETURN bit4 的含义，本章【注】的全文版。
- **[\[A6\]](../../reference/bibliography.md#chips)** ARMv7-M 架构参考手册 — 异常入栈帧与 EXC_RETURN 的规范定义。

## 你做到了

- "换魂术"全程目击并能逐行讲解；
- 上下文切换从此没有黑盒，这是理解一切 RTOS 行为的总钥匙；
- 三个数张口就来：软件帧 9 个字、正文 27 条指令、新任务第一帧 18 个字 72 字节；
- 拿到任何一份 RTOS 移植层，先看它的 `FreeRTOSConfig.h` 改了哪些 handler 名，这是 GDB 能不能断上的分水岭；
- 再看到 `taskYIELD()` 或 `portYIELD_FROM_ISR`，你知道它们在跟 PendSV 打招呼。

断点没响，不是 GDB 坏了：源码里的名字被一行宏换掉了，向量表里躺着的才是真身。往后拿到任何移植层，先翻改名表再下断点，这一炮才响得起来。

<div class="achievement">
✅ 下一站：<a href="03-scheduler.html">F3 调度器</a>：位图就绪表 32 选 1 只要一条 CLZ，tick 里到底发生了什么。
</div>
