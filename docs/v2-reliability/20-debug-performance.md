---
title: "调试、性能与测量"
platforms: [f407, f103]
---

# 调试、性能与测量

调试器能让内核停住，能读寄存器，能改内存；这三件事都不自动等于证据。断点可能根本没有落进 Flash，SWO 可能一个字节都没发出来，`DWT->CYCCNT` 可能一直停在 0，示波器上看到的"干净"也可能只是探头把边沿滤掉了。本章把调试链、断点、跟踪、计时、优化与三件测量仪器拆开，最后只认一种结论：寄存器 dump、反汇编与时间戳能互相对上，并且能说清这份固件是怎么构建出来的。

两个来源都没有留下本章的上板读数：`docs/17` 的实验节写的是现象与步骤，没有原始时间戳；`mcu/docs/build/06-flash-debug.md` 没有调试会话记录。本章把手册规则、算术推导、宿主上的工具链实验与尚未执行的板级实验分开写，凡是没有读数的断言都在原处标出来。

## 本章罗盘

- **问题**：IDE 点下"暂停"之后，谁让内核停住，谁又在 CPU 继续跑的时候替它读内存？SWD 只接 SWDIO/SWCLK/GND 为什么有时能连、有时连不上，VTref 和 NRST 各管什么？硬件断点与软件断点差在哪，为什么 `break` 在 Flash 上会悄悄退回 FPB，而 M0+ 只有 2 个比较器时又会突然"打不上"？SWO 明明接了线却没有输出，四个前提里缺的是哪一个？DWT 的 `CYCCNT` 为什么必须先开 `TRCENA` 再清零，72 MHz 与 168 MHz 下同一个 cycle 数为什么不是同一个微秒数？`-g3` 为什么救不了被内联掉的函数与漂走的断点？逻辑分析仪能看到协议却看不到振铃，示波器能看到边沿却读不出协议，万用表读到的电流为什么总比峰值小？调试器又怎样把看门狗关掉，制造"从不复位"的假阴性？
- **交付**：能画出 IDE → GDB → OpenOCD → DP/AP → 总线的分层，并说清 halt 只是请求、AP 访问不经过 CPU；能按芯片列出 FPB 指令比较器数量（M0=4、M0+=2、M3=6、M4=6、M7=8），并给"断点打不上"的三种原因与排查顺序；能按引脚、`DBGMCU_CR`、TRACECLK、调试器四项逐一核对 SWO；能写出 DWT 计时的四步流水线，并用 `cycles = µs × f_cpu` 在 72 MHz 与 168 MHz 下各算一组；能判断 Cortex-M7 的 DWT 是否需要先写 `LAR`；能用同一段代码的 `-Og`/`-O2` 汇编对照与 `info line` 验证断点漂移；能按"协议/时序、信号质量、平均电流"给三件仪器分工；能把寄存器 dump、反汇编与时间戳组成证据三角；能说出 OpenOCD 关狗造成的假阴性，并回链看门狗章。
- **边界**：双平台章，主线是 F103（Cortex-M3，72 MHz）与 F407（Cortex-M4F，168 MHz）。调试链、SWD 最小集、FPB 与 BKPT、SWO/ITM、DWT、优化等级来自 `docs/17-调试与性能优化.md` 与 `mcu/docs/build/06-flash-debug.md` 的转引；FPB 数量按 ARMv6-M/ARMv7-M/ARMv7E-M 的定义写，`06-flash:112` 的"M0/M0+ 只有 2 个"是错的，本章不照抄。Cortex-M7 的 `DWT->LAR` 两个来源都没有提，只作为边界提示。HardFault 的寄存器细节、CFSR 位图与栈帧布局归[第 19 章](./19-watchdog-reset-hardfault.md)，本章只取工具链段。两个来源都没有上板读数；本工作树没有 `mcu/.trellis/ref/cmsis`，涉及 CMSIS 的位号与寄存器定义一律按"来源说法(未复核)"处理。低功耗下 DWT 是否继续计数、Stop 模式怎样影响调试，回链[第 18 章](./18-low-power.md)。
- **依据锚点**：根书第 17 章《调试与性能优化》（`docs/17-调试与性能优化.md`）、B6《烧录与调试：SWD 与断点的真相》（`mcu/docs/build/06-flash-debug.md`）；工具链四步与 ELF 读法见[v0 第 5 章](../v0-foundations/05-toolchain-four-steps.md)；定时器与输入捕获的时基见[v1 第 12 章](../v1-drivers/12-timers-pwm.md)；HardFault 取证见[第 19 章](./19-watchdog-reset-hardfault.md)；低功耗与调试冻结的交叉见[第 18 章](./18-low-power.md)。ARMv6-M/ARMv7-M/ARMv7E-M 架构手册、RM0008、RM0090、DS5319、DS8626、OpenOCD 与 GDB 文档均转引自上述来源，本章没有取到原件逐页核对。

## 先做出来

先不接板子，把四笔账算在纸上。它们决定你上板后看到的"没反应"到底是工具坏了，还是前提少了一个。

1. **断点预算账**：F407 的 M4 有 6 个 FPB 指令比较器，F103 的 M3 也是 6 个；M7 是 8 个，M0 是 4 个，M0+ 只有 2 个。条件断点 `hbreak if ...` 仍然占一个比较器，因为条件是在命中之后由调试器求值的。一个工程里同时留 3 个普通断点、2 个条件断点和 1 个数据观察点，在 M0+ 上必然有人打不上；先数预算，再怀疑代码。
2. **周期换算账**：`cycles = µs × f_cpu`。100 µs 在 72 MHz 下是 7200 cycles，在 168 MHz 下是 16800 cycles；反过来，1000 cycles 在 72 MHz 下是 13.89 µs，在 168 MHz 下是 5.95 µs。同一个 1000 cycles 的读数，换一颗芯片就换了一个时间；不写主频的"1000 cycles"不是时间。
3. **SWO 前提账**：引脚复用、`DBGMCU_CR` 的 `TRACE_IOEN`/`TRACE_MODE`、TRACECLK 有源、调试器支持并接上 SWO。四项是与门关系，缺一项就静默；SWO 不会因为时钟没配好而打印一条错误。
4. **仪器分工账**：问"这一帧 SPI 的 CPOL/CPHA 对不对"用逻辑分析仪；问"这个边沿有没有过冲、振铃、地弹"用示波器；问"这块板平均耗多少毫安"用万用表。拿逻辑分析仪看边沿形状，得到的是一条被阈值切平的数字线；拿万用表看 μs 级峰值，得到的是平均值。

四笔账都能用纸笔和一张数据手册复算。它们对上之后，再决定要不要买探头、接 SWO、开 DWT。

本章还有一笔可以在没有开发板的机器上复跑的账：用 `arm-none-eabi-gcc` 把同一段 C 代码分别按 `-Og -g3` 与 `-O2 -g3` 编译，再用 `arm-none-eabi-nm` 与 GDB 看符号和行表怎样变化。这是实测记录，但测的是宿主上的编译器与 GDB，不是板上的 FPB、SWO 或 DWT；复跑方法写在"优化等级与可调试性"一节。

## 机制

### 一、调试链：halt 是请求，内存访问由 AP 代办

把 IDE 上的"暂停"一路拆下去，链条是：

```text
IDE → GDB（RSP，默认 :3333）→ OpenOCD → ST-Link → SWD → DP → MEM-AP → AHB 总线 → 目标地址
```

GDB 不直接碰硬件，它通过 GDB Remote Serial Protocol 把"读这个地址""写这个寄存器""停住"发给 OpenOCD；OpenOCD 把请求翻译成 SWD 事务；ST-Link 负责 USB 与 SWD 的电平转换；目标端的 DP（Debug Port）再选到 MEM-AP（Memory Access Port），由 AP 发起 AHB 读写。

关键性质是：**AP 访问总线不经过 CPU**。CPU 在跑代码、停在断点、甚至睡死，AP 都能读写目标地址。烧录与调试在物理上是同一件事：读写 Flash 控制器寄存器就是烧录，读写 RAM 与外设寄存器就是调试，读写 PC/MSP 就是控制 CPU。`halt` 只是往调试寄存器里写一个"请求停"的位，内核在下一个指令边界停下来；它不是把总线闸住，也不是把外设时钟停掉。

![SWD 调试链：IDE、GDB、OpenOCD、ST-Link、DP/AP 与目标总线](/anim/swd-debug-chain.svg)

图中每一层都可能断开：GDB 连不上 OpenOCD 是 RSP 层，OpenOCD 连不上目标跑的是 SWD 层，SWD 连上但读写失败是 AP/总线层。分层排障，比在 IDE 里反复点"重新连接"有效。

SWD 的最小集是三根线：SWDIO（双向数据）、SWCLK（时钟）、GND。实际接线还要 VTref：它是目标板给调试器的电压参考，不是第二路电源；ST-Link 用 VTref 判断目标电平，缺了它，某些探头会拒绝连接或把 3.3 V 当成 5 V。NRST 是可选项，接上才能做"connect under reset"：调试器先把复位按住，再在复位释放前抢进调试口，专门对付一上电就睡死、把 SWD 引脚复用掉或看门狗立即复位的板子。JTAG 则多出 TCK/TMS/TDI/TDO，支持菊花链，但引脚更多；SWD 是 JTAG 的子集，两根信号线换来的代价是不能菊花链。

调试时钟 4 MHz、10 MHz 之类的数字是探头与线长的折中，属于厂商标称，不是"设得越高越好"：线越长、地回流越差，能稳定的时钟越低。先用低时钟连上，再逐步抬高；连不上时先降时钟、缩短地线，而不是先怀疑芯片坏了。

### 二、断点：FPB 比较器与 BKPT 指令替换

断点有两副面孔，硬件实现完全不同。

**硬件断点**走 FPB（Flash Patch and Breakpoint）单元。CPU 取指时，FPB 把取指地址与比较器里的地址比对，命中就停住，不改 Flash 内容。Cortex-M3 与 M4 各有 6 个指令地址比较器；Cortex-M7 有 8 个；Cortex-M0 有 4 个；Cortex-M0+ 只有 2 个。`06-flash-debug.md` 第 112 行写"M0/M0+ 只有 2 个"，把 M0 的 4 个也吞掉了，照抄会在 M0 上低估预算。这些是 ARM 的典型配置，具体型号可能裁剪，选型时以 TRM 为准。M3/M4 另有 2 个字面量比较器，用于 Flash 补丁；字面量比较器不算指令断点预算。数据观察点走 DWT 比较器，是另一本账。

**软件断点**由 GDB 把目标地址的指令改写成 `BKPT #0`，Thumb 编码是 `0xBE00`。CPU 执行到它，触发调试异常并停住。它要求目标地址可写：RAM 里的代码随便改；Flash 里的代码要先擦整扇区才能改，所以 GDB 的 `break` 在 Flash 上经常悄悄退回 FPB，或者在写入失败时直接报错。`hbreak` 明确要求硬件断点，Flash 代码用它；`break` 适合 RAM 代码或调试器支持 Flash 补丁的场合。`BKPT #0` 是调试断点，半主机用的是另一个立即数 `BKPT 0xAB`，两者不要混。

断点打不上，先查三种原因：

1. **比较器用完了**：普通断点、`hbreak`、条件 `hbreak` 都在抢同一组 FPB 槽位。条件断点并不会因为"条件在软件里判断"就免费；命中之前它仍然占一个硬件比较器。先把 `info break` 里的断点删到预算以内，再谈其他。
2. **地址不可写**：软件断点在 Flash/ROM 上没有落脚点。换 `hbreak`，或者把函数放进 RAM（链接脚本给一个 RAM 执行段），再下软件断点。调试器报告 "Cannot insert breakpoint" 时，先看它用的是软还是硬。
3. **那一行没有代码**：优化把语句删了、合并了、内联了，或者 ELF 与板上固件不是同一次构建。`info line file:line` 会直接说 "contains no code"；`break file:line` 却仍然可能给你一个地址，这个地址往往是附近的函数入口，界面上的行号还是你写的那个行号。第三种原因最容易被误判成"断点坏了"。

### 三、SWO/ITM：四个前提，缺一即静默

SWO 是目标到主机的一条单向跟踪通道，ITM 是它上面的"软件 printf"：代码往 ITM 的 stimulus 端口写一个字节，调试器从 SWO 收走。它不占 UART，也不需要目标停下，但四个前提必须同时成立：

1. **引脚复用**：SWO 在 PB3（F103 与 F407 都是）。F103 上 PB3 默认是 JTDO，必须先把 JTAG-DP 关掉、保留 SW-DP（`AFIO_MAPR` 的 `SWJ_CFG`），PB3 才让给 TRACESWO；F407 上把 PB3 配成 AF0。引脚还被别的外设占着，SWO 就没有出口。
2. **DBGMCU 使能**：`DBGMCU_CR`（F103/F407 都是 `0xE0042004`）的 `TRACE_IOEN`（bit5）置 1，`TRACE_MODE`（bit7:6）写 `00` 选异步 SWO。写别的模式会切到同步跟踪，需要额外的 TRACECLK/TRACEDATA 引脚。
3. **TRACECLK 有源**：跟踪单元与 TPIU 靠 HCLK 推动；TPIU 的分频（`ACPR`）与调试器里配置的 SWO 时钟必须对上。目标主频改了、调试器的 SWO 速度没改，收到的是错位的数据流。
4. **调试器支持并接上 SWO**：ST-Link 的 SWO 引脚要接到 PB3，OpenOCD/GDB 要启用 TPIU 并配置通道；只接 SWDIO/SWCLK 的探头不会自动有 SWO。

缺任何一项，表现都是"没有输出"，没有错误码。排查顺序就按这四项走：先看引脚，再看 `DBGMCU_CR`，再看时钟与 TPIU 分频，最后看探头与接线。ITM 端口 0 常被 `ITM_SendChar` 占用；如果 FIFO 满了，阻塞式发送会让目标停在 `ITM_SendChar` 里，这时断点看起来像"程序卡死"，其实是跟踪通道没有消费者。

半主机（semihosting）不是 SWO。它用 `BKPT 0xAB` 主动触发调试器，调试器在主机上代打开文件、读写标准输出，再回到目标；一次 `printf` 要经过"停住—请求—主机服务—恢复"的往返。`docs/17` 说它比串口慢一个数量级、每次调用数十微秒，但没有给出计时记录，本章按"来源说法(未复核)"处理。生产固件必须去掉 `--specs=rdimon.specs` 或提供自己的 `_write`：没有调试器时，`BKPT 0xAB` 没有人服务，多数配置下会升级成 HardFault。

### 四、DWT：先开 TRCENA，再清 CYCCNT

DWT 的周期计数器是 Cortex-M 上最便宜的性能计时器。流水线四步，顺序不能反：

```c
CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;  /* 0xE000EDFC bit24：打开跟踪与 DWT 时钟 */
DWT->CYCCNT = 0;                                 /* 0xE0001004：清零 */
DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;            /* 0xE0001000 bit0：启动计数 */
uint32_t start = DWT->CYCCNT;                    /* 读当前周期数 */
/* ... 被测代码 ... */
uint32_t cycles = DWT->CYCCNT - start;           /* 无符号减法，单次回绕仍成立 */
```

先开 `TRCENA`，因为 DWT 与 ITM 共用这个使能；没开时写 `CYCCNTENA` 可能不生效，读 `CYCCNT` 一直是 0。清零放在启动之前，否则第一次读到的可能是上电以来的累计值。启动之后再读，读到的才是从零开始的周期数。

换算只认当前主频：

```text
cycles = µs × f_cpu
```

| 主频 | 1 µs | 1000 cycles | 100 µs | 2^32 cycles 回绕 |
| --- | --- | --- | --- | --- |
| 72 MHz（F103） | 72 cycles | 13.89 µs | 7200 cycles | 59.65 s |
| 168 MHz（F407） | 168 cycles | 5.95 µs | 16800 cycles | 25.57 s |

![DWT 计时窗口：CYCCNT 从 0 起算，区间的 cycles 要按当前主频换算成微秒](/images/ch17-dwt-window.png)

图中窗口的宽度是 cycles，不是微秒；同一个窗口在 72 MHz 与 168 MHz 下对应的时间不同，换算系数必须跟着主频走。

"72 cycles = 1 µs"只对 72 MHz 成立，不能当通例。F407 跑 168 MHz 时，同样的 72 cycles 只有 0.43 µs；把 F103 的换算搬到 F407，读数会差 2.33 倍。时钟树改了、APB 分频改了、低功耗降频了，换算系数都要跟着改。DWT 数的是内核周期，不是墙上时间；中断、Flash 等待周期、调试 halt 都会影响它与外部时间戳的对应关系。

回绕用无符号减法处理：`end - start` 在一次 2^32 回绕内仍然给出正确的差值，前提是被测区间短于 59.65 s（72 MHz）或 25.57 s（168 MHz）。超过这个长度，要么改用定时器，要么在中间记一次快照。不要用有符号数比较 `end > start`，回绕后它会把正常区间判成负值。

Cortex-M7 多一道锁：DWT 的寄存器受 `DWT->LAR`（`0xE0001FB0`）保护，先写 `0xC5ACCE55` 解锁，再配置 `CYCCNT`。两个来源都没有提这一步，本章只作为边界提示；在 M7 上按 M4 的代码原样抄，可能看到 `CYCCNT` 不动。M0/M0+ 的 DWT 能力更窄，使用前先查对应型号的 TRM，不要假设 `CYCCNT` 一定存在。

低功耗是另一个边界：Stop/Standby 下内核时钟停了，`CYCCNT` 是否继续数取决于芯片与低功耗模式；用 DWT 测低功耗唤醒间隔，得到的可能不是墙上时间。低功耗模式与唤醒源的细节见[第 18 章](./18-low-power.md)。

### 五、HardFault 的工具链段：从 VALID 到源码行

HardFault 的寄存器地图、CFSR 的 19 个位、栈帧怎样压、`naked` handler 怎么写，归[第 19 章](./19-watchdog-reset-hardfault.md)。本章只接工具链这一段：拿到现场之后，怎样把它变成一行源码。

顺序是：

1. **先看 CFSR/HFSR，确认这是不是一条能落到地址上的故障**。`MMARVALID`/`BFARVALID` 为 0 时，`MMFAR`/`BFAR` 里的值不可信；`IMPRECISERR` 下 PC 也可能已经跑远。VALID 位不亮的地址，不要拿去做 `addr2line`。
2. **按 `EXC_RETURN` 选栈**。bit2=0 用 MSP，bit2=1 用 PSP；bit4=0 表示 FPU 扩展帧（`0xFFFFFFE1/E9/ED`），bit4=1 是基本帧（`0xFFFFFFF1/F9/FD`）。取 PC 前要先按扩展帧布局定位基本帧。基本帧里 PC 在 `sp[6]`，也就是 `((uint32_t *)sp)[6]`。拿错栈，读出来的 8 个字全是垃圾。

![异常栈帧：基本帧 8 个字，PC 在偏移 24；FPU 扩展帧要先定位基本帧](/images/ch17-stack-frame.png)

图中基本帧的 8 个字按 r0、r1、r2、r3、r12、LR、PC、xPSR 排列；扩展帧在前面多了 S0–S15、FPSCR 与一个保留字，取 PC 前先按 `EXC_RETURN` 把指针移到基本帧。
3. **把 PC 交给 GDB 或 `addr2line`**。GDB 连上时可以直接：

```text
(gdb) p/x *(uint32_t *)0xE000ED28
(gdb) x/8wx $sp
(gdb) info line *0x08001234
(gdb) disassemble /m 0x08001234
```

离线时用：

```bash
arm-none-eabi-addr2line -e build/firmware.elf -f -C 0x08001234
```

![HardFault 取证阶梯：CFSR 定性、VALID 取址、栈帧取 PC、addr2line 对行](/figures/fault-triage-ladder.svg)

图中每一步都可能断：CFSR 只说明故障类别，VALID 位不亮时地址不可信，栈帧可能不完整，ELF 可能不是板上那一份。任何一步断了，后面的行号都不算数。

`??:0` 不是"地址不存在"的同义词。它可能是 ELF 没带 `-g`、ELF 与板上固件不是同一次构建、地址落在数据区而不是代码区，或者地址的最低位带着 Thumb 标志位而工具期望纯地址。先核对 ELF 的 SHA256 或 build ID，再核对地址是否落在 `.text` 的范围内，最后才怀疑 `addr2line`。

GDB 里的 `bt` 在 HardFault handler 里不是故障现场的调用栈。它展开的是 handler 自己的栈，或者被异常帧打断后的当前栈；故障发生前的调用关系要靠栈帧与栈上残留的 LR 去重建，不能直接读 `bt` 的前几行。把 `bt` 当成"案发调用链"，会把排查带到 handler 里面去。

### 六、优化等级与可调试性

优化等级改变的是代码与源码行的对应关系，不只是速度。

| 等级 | 主要目标 | 对调试的影响 | 适用 |
| --- | --- | --- | --- |
| `-O0` | 不优化 | 语句与指令接近一一对应，变量多在栈上；代码大、慢 | 单步跟逻辑、首次 Bring-up |
| `-Og` | 兼顾调试的优化 | 仍会删死代码、合并变量、做有限内联；行表通常比 `-O2` 稳 | 日常调试构建 |
| `-O2` | 速度 | 内联、重排、向量化、循环变换；断点漂移、变量被优化掉 | 发布构建、性能对比 |
| `-Os` | 体积 | 与 `-O2` 类似的变换，偏向缩小代码 | Flash 紧张时 |

`-g3` 只增加调试信息的种类（宏定义等），不改变代码生成；它不能阻止内联，也不能阻止指令重排。把 `-O2 -g3` 当成"既能优化又能单步"，是把优化与可调试性混为一谈。要判断某个函数有没有被内联，看符号表与反汇编，不看编译命令行里有没有 `-g3`。

下面这段宿主实验可以复跑。它只用 `arm-none-eabi-gcc`、`arm-none-eabi-nm` 与 GDB，不需要开发板；本节的数据是本章唯一的"实测记录"，测的是编译器与 GDB 的行为，不是板上的 FPB 或 DWT。

```c
#include <stdint.h>

volatile uint32_t g_sink;

__attribute__((noinline)) uint32_t sum_bytes(const uint8_t *p, uint32_t n)
{
    uint32_t s = 0;
    for (uint32_t i = 0; i < n; i++) {
        s += p[i];
    }
    return s;
}

static uint32_t scale(uint32_t x)
{
    return (x * 3u + 7u) >> 2;
}

int main(void)
{
    static const uint8_t data[16] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16};
    g_sink = sum_bytes(data, 16) + scale(g_sink);
    for (;;) { }
}
```

把这段代码原样存成 `debug_demo.c`；`s = 0` 在第 7 行，`s += p[i]` 在第 9 行，`scale` 在第 14 行。若编辑器少了空行，行号会变，下面的命令跟着改。

```bash
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -Og -g3 -ffreestanding -c debug_demo.c -o debug_demo-Og.o
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O2 -g3 -ffreestanding -c debug_demo.c -o debug_demo-O2.o

arm-none-eabi-nm -n -S debug_demo-Og.o | grep -E 'sum_bytes|scale'
arm-none-eabi-nm -n -S debug_demo-O2.o | grep -E 'sum_bytes|scale'

arm-none-eabi-gdb -q -batch debug_demo-Og.o \
    -ex 'info line debug_demo.c:7' \
    -ex 'info line debug_demo.c:9' \
    -ex 'break debug_demo.c:7'
arm-none-eabi-gdb -q -batch debug_demo-O2.o \
    -ex 'info line debug_demo.c:7' \
    -ex 'info line debug_demo.c:9' \
    -ex 'break debug_demo.c:7'
```

本机工具链是 GNU Arm Embedded 10.3-2021.10（GCC 10.3.1、GDB 10.2.90、binutils 2.36.1）。两组 `nm` 输出：

```text
$ arm-none-eabi-nm -n -S debug_demo-Og.o | grep -E 'sum_bytes|scale'
00000000 0000000a t scale
0000000a 00000016 T sum_bytes
$ arm-none-eabi-nm -n -S debug_demo-O2.o | grep -E 'sum_bytes|scale'
00000000 00000018 T sum_bytes
```

`-O2` 下 `scale` 的符号消失了：它被内联进 `main`，独立的函数体不再存在。`sum_bytes` 从 0x16 字节变成 0x18 字节，反而更大；`-O2` 优化的是执行速度，不是无条件缩小体积，别把"优化"等同于"更小"。`sum_bytes` 的 `noinline` 是为了让它保留独立符号，方便下一段对比；`scale` 没有这个属性，正好用来演示内联。

两档反汇编（`objdump -d` 的 `sum_bytes` 段）：

```text
$ arm-none-eabi-objdump -d debug_demo-Og.o | sed -n '/<sum_bytes>:/,/^$/p'
0000000a <sum_bytes>:
   a:  4684        mov     ip, r0
   c:  2300        movs    r3, #0
   e:  4618        mov     r0, r3
  10:  e003        b.n     1a <sum_bytes+0x10>
  12:  f81c 2003   ldrb.w  r2, [ip, r3]
  16:  4410        add     r0, r2
  18:  3301        adds    r3, #1
  1a:  428b        cmp     r3, r1
  1c:  d3f9        bcc.n   12 <sum_bytes+0x8>
  1e:  4770        bx      lr

$ arm-none-eabi-objdump -d debug_demo-O2.o | sed -n '/<sum_bytes>:/,/^$/p'
00000000 <sum_bytes>:
   0:  b141        cbz     r1, 14 <sum_bytes+0x14>
   2:  1e43        subs    r3, r0, #1
   4:  4419        add     r1, r3
   6:  2000        movs    r0, #0
   8:  f813 2f01   ldrb.w  r2, [r3, #1]!
   c:  428b        cmp     r3, r1
   e:  4410        add     r0, r2
  10:  d1fa        bne.n   8 <sum_bytes+0x8>
  12:  4770        bx      lr
  14:  4608        mov     r0, r1
  16:  4770        bx      lr
```

`-Og` 的循环是"先取 `p[i]`，再加到累加器，再递增下标"；`-O2` 用 `ldrb.w r2, [r3, #1]!` 把取数与指针递增合成一条，并且先判 `n == 0` 走早退分支。同一段源码，指令顺序与循环形状都变了；行表跟着指令走，断点也就跟着漂。

GDB 的行表输出更直接：

```text
$ arm-none-eabi-gdb -q -batch debug_demo-Og.o -ex 'info line debug_demo.c:7' -ex 'info line debug_demo.c:9' -ex 'break debug_demo.c:7'
Line 7 of "debug_demo.c" is at address 0xc <sum_bytes+2> but contains no code.
Line 9 of "debug_demo.c" starts at address 0x12 <sum_bytes+8> and ends at 0x18 <sum_bytes+14>.
Breakpoint 1 at 0xc: file debug_demo.c, line 7.

$ arm-none-eabi-gdb -q -batch debug_demo-O2.o -ex 'info line debug_demo.c:7' -ex 'info line debug_demo.c:9' -ex 'break debug_demo.c:7'
Line 7 of "debug_demo.c" is at address 0x0 <sum_bytes> but contains no code.
Line 9 of "debug_demo.c" starts at address 0x8 <sum_bytes+8> and ends at 0xc <sum_bytes+12>.
Breakpoint 1 at 0x0: file debug_demo.c, line 7.
```

两档都带 `-g3`，第 7 行都报 "contains no code"，但断点落点不同：`-Og` 落在 0xc（循环初始化附近），`-O2` 落在 0x0（函数入口）。`break debug_demo.c:7` 没有失败，`info break` 还会显示 "line 7"；它悄悄替换成了附近的地址。停在函数入口时，局部变量 `s` 还没初始化，看到的现场与源码第 7 行不是一回事。这就是断点漂移，`-g3` 不会修它。

同一段代码两档对照的验证步骤：

1. **保留两份构建产物**：同一份源码、同一套头文件，只改优化等级；记录编译器版本与完整命令行。
2. **对照汇编**：用 `nm -S` 看符号有无、函数大小；用 `objdump -d` 看调用是否被内联、循环是否被改写。不要只看源码。
3. **验证断点**：用 `info line file:line` 看目标行有没有代码、起止地址在哪；用 `break` 后 `info break` 看实际落点。落在函数入口或 "contains no code" 的行，不是稳定的观察点。
4. **验证行为**：能上板就喂同一组输入，比较输出或校验和；优化不能改变可观察结果。改变的是时序与调试映射，不是功能。
5. **验证时间**：用 DWT 在同一主频下比较 cycles；不要在 72 MHz 与 168 MHz 之间直接比微秒，也不要把 `-O0` 的 cycles 当成发布固件的性能。

局部调试手段只在必要时用：`__attribute__((noinline))` 可以阻止单个函数被内联；GCC 的 `__attribute__((optimize("O0")))` 是编译器扩展，跨版本行为不保证；`-fno-inline` 影响整个编译单元，会改变时序。`volatile` 只约束被标注的访问，不阻止其他指令重排，也不提供跨线程同步；把它当成"关优化开关"会写出更隐蔽的错。

### 七、测量三件套：协议、信号质量、平均电流

三件仪器回答三个不同的问题，不能互相替代。

| 问题 | 仪器 | 能看到 | 看不到 |
| --- | --- | --- | --- |
| 这一帧 SPI 的位序、CPOL/CPHA、片选时序对不对 | 逻辑分析仪 | 多路数字电平、协议解码、通道间时序、触发 | 边沿形状、过冲、振铃、噪声、真实电压 |
| 这个边沿有多快，有没有过冲/振铃/地弹，电源纹波多大 | 示波器 | 模拟波形、上升/下降时间、过冲、噪声、功率纹波 | 长时间协议流（存储深度有限）、多路慢速控制信号 |
| 这块板平均耗多少电流，某根线通不通 | 万用表 | 平均电压/电流、通断、电阻 | μs 级峰值、动态负载、瞬态跌落 |

**逻辑分析仪**的核心参数是采样率、通道数与阈值。采样率要高于被测信号最快边沿或时钟的 5–10 倍：1 MHz 的 SPI 时钟，10 MSa/s 只有 10 点/bit，解码够用但边沿位置粗；24 MSa/s 有 24 点/bit，宽裕。到 10 MHz，24 MSa/s 只剩 2.4 点/bit，协议解码可能开始丢位。本章配图用的 8 通道分析仪标称 24 MHz 采样，这是厂商标称，不是本章实测；实际能用多高，要在目标板上用已知时钟验证。

阈值决定"什么算高"。3.3 V CMOS 与 1.8 V 信号不是同一个阈值；阈值设错，逻辑分析仪会把半高电平判成翻转或恒定。它只输出 0/1，边沿形状、过冲、振铃、地弹都被阈值切掉；采样点之间的窄毛刺也可能完全漏掉。所以"逻辑分析仪上很干净"不能证明信号质量好。

**示波器**的核心参数是带宽、采样率、探头与接地。带宽至少是被测信号最高有效频率的 5 倍；上升时间与带宽的近似关系是：

```text
tr ≈ 0.35 / BW
```

50 MHz 带宽对应约 7 ns 的上升时间。用 50 MHz 示波器看 10 MHz 时钟的边沿，看到的 7 ns 主要是示波器自己的响应，不是信号本来的边沿；要判断 2 ns 的边沿，需要几百 MHz 带宽。采样率再高也不能补带宽：1 GSa/s 的采样间隔是 1 ns，但 50 MHz 的模拟前端已经把快边沿抹平了。

探头同样参与测量。10× 探头带宽高、输入电容小（典型约 10 pF），但需要补偿：把探头接到示波器的 1 kHz 方波校准端，调补偿电容直到方波顶部平直；补偿不对，测到的过冲可能是探头造成的。1× 探头输入电容大、带宽低，只适合低频小信号。地线要短：长地线电感与探头电容形成 LC，振铃频率可能落在被测信号的频段里，测到的"振铃"其实是探头系统。

![Rigol DS1054Z 示波器：50 MHz 带宽、4 通道、单通道 1 GSa/s 标称](/images/tools/oscilloscope-ds1054z.jpg)

图中这台 DS1054Z 的标称是 50 MHz 带宽、4 通道、单通道最大 1 GSa/s；通道开得越多，单通道采样率越低。它是"看信号质量"的入门工具，不是"看 100 MHz 时钟眼图"的工具。

![8 通道逻辑分析仪：协议解码与多路时序，不替代示波器](/images/tools/logic-analyzer-8ch.jpg)

逻辑分析仪的通道数多、能解码协议，但它把模拟世界压成 0/1；图中这种 8 通道分析仪的 24 MHz 采样是标称值，测 10 MHz 信号时每 bit 只有 2.4 个采样点，边沿与毛刺都不可信。

**万用表**读的是平均值。它适合确认电源轨的直流值、平均电流、通断与电阻；不适合读电机启动、无线发射、LED 脉冲调光这类 μs/ms 级峰值。用万用表串在电源里测电流，还会有 burden voltage（分流电阻上的压降），目标可能因为供电降低而改变行为。要看峰值电流，用分流电阻加示波器（低端分流直接测，高端分流用差分探头或隔离），把电压换成电流，并把探头与地线的带宽算进去。

测量记录要写全设置：示波器的时间档、带宽限制、耦合方式、探头衰减、触发方式；逻辑分析仪的采样率、阈值、通道映射、协议参数；万用表的量程与 burden voltage。只留一张"波形截图"而不留设置，下一次复现不了。

### 八、调试器会改变目标，证据要三元对齐

调试器不是透明观察者。halt 停住内核，但外设时钟、DMA、定时器、看门狗可能继续跑；AP 读写内存不经过 CPU，读一个状态寄存器可能把标志清掉；断点改写 Flash 或占用 FPB；半主机把 `printf` 变成一次调试器往返。测量本身也会扰动时序：ITM 发送可能阻塞，DWT 读取要几个周期，逻辑分析仪的探头电容会加载信号。

最典型的假阴性是看门狗。OpenOCD 在断点处会关掉 ESP32 的 IWDT 与 TWDT，离开断点后也不再打开；STM32 侧则有 `DBGMCU` 的冻结位，调试器启动脚本常把 IWDG/WWDG 在 halt 时冻住。调试会话里"卡死后从不复位"，脱机后可能立刻复位。复位实验的固定流程是：烧录、断开调试器、板子断电再上电、再发故障命令。细节与冻结位号见[第 19 章](./19-watchdog-reset-hardfault.md)。

证据三角是：

- **寄存器 dump**：内核与外设当时看到了什么。没有符号，它只是地址与数值。
- **反汇编**：这份 ELF 在那个地址上原本要执行什么。没有 build ID，它可能不是板上那一份。
- **时间戳/周期数**：这件事发生在什么时候，和哪个事件前后相邻。没有时钟来源，它无法换算成时间。

三者互相对上，才是一条可复现的结论。只有 `printf("here")` 不算：它没有时间戳，没有构建标识，也无法证明打印的固件就是板上的固件。只有一张波形也不算：不知道触发点对应哪行代码。只有 CFSR 也不算：知道是总线错误，不知道是哪条指令。

记录模板至少包含：

```text
ELF SHA256 / build ID:
git commit:
compiler + version:
CFLAGS / LDFLAGS:
board / MCU / clock tree:
probe firmware + OpenOCD version:
GDB / OpenOCD commands:
raw output file:
```

## 测量与证据

本章的读数按来路分四类：实测记录、来源说法(未复核)、文档推导、未实测。下表逐项标出来路；只有宿主上的优化对照是实测记录，没有一条是本章的上板读数。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| FPB 指令比较器数量 | `06-flash-debug.md` 与 ARMv6-M/ARMv7-M/ARMv7E-M 架构定义，经来源勘误转引；未核 ARM 原件 | M0=4、M0+=2、M3=6、M4=6、M7=8；`06-flash:112` 的"M0/M0+ 2 个"错 | 来源说法(未复核) |
| SWD 最小集与调试链 | `06-flash-debug.md` 第 1–2 节与 OpenOCD/GDB 文档转引；未上板 | SWDIO/SWCLK/GND；VTref 是参考电压、NRST 可选；AP 访问不经过 CPU | 来源说法(未复核) |
| SWO 四前提 | `docs/17` 的 SWO/ITM 段与 RM 转引；未上板 | 引脚复用、`TRACE_IOEN`/`TRACE_MODE`、TRACECLK、调试器；缺一静默 | 来源说法(未复核) |
| DWT 寄存器地址与位号 | ARMv7-M PPB 地图与 `docs/17` 转引；本工作树无 CMSIS 参考 | `DEMCR` 0xE000EDFC bit24；`CYCCNT` 0xE0001004；`CTRL` 0xE0001000 bit0 | 来源说法(未复核) |
| DWT 换算 | 本章按 f=72/168 MHz 复算 | 1 µs=72/168 cycles；1000 cycles=13.89/5.95 µs；100 µs=7200/16800；回绕 59.65/25.57 s | 文档推导 |
| Cortex-M7 的 DWT 解锁 | Cortex-M7 TRM 转引；两个来源未提 | `DWT->LAR` 0xE0001FB0 写 0xC5ACCE55 | 来源说法(未复核) |
| 两档优化下的符号 | 宿主 `arm-none-eabi-gcc` 10.3.1，`-Og -g3` 与 `-O2 -g3`，`nm -n -S` | `scale` 在 `-Og` 为 0xa 字节，`-O2` 无符号；`sum_bytes` 0x16→0x18 字节 | 实测记录 |
| 两档优化下的断点落点 | 同一对对象文件，GDB 10.2.90 的 `info line` 与 `break` | 第 7 行两档都 "contains no code"；断点 `-Og` 落 0xc，`-O2` 落 0x0（函数入口） | 实测记录 |
| 半主机耗时 | `docs/17` 称慢一个数量级、每次数十 µs；无计时记录 | 来源称每次数十 µs，未记录 | 来源说法(未复核) |
| 半主机与 BKPT | `docs/17` 与 newlib 文档转引 | `BKPT 0xAB` 触发服务；`--specs=rdimon.specs`；无调试器可能 HardFault | 来源说法(未复核) |
| 测量三件套分工 | `docs/17` 与仪器手册转引 | 逻辑分析仪=协议/时序；示波器=信号质量；万用表=平均 | 来源说法(未复核) |
| DS1054Z 标称 | 厂商页面/说明书转引，未核原件 | 50 MHz、4 通道、单通道最大 1 GSa/s | 来源说法(未复核) |
| 8 通道分析仪标称 | 厂商页面/说明书转引，未核原件 | 8 通道、24 MHz 采样 | 来源说法(未复核) |
| 采样率账 | 本章按采样率/时钟复算 | 24 MSa/s 在 1 MHz 下 24 点/bit，10 MHz 下 2.4 点/bit；5–10× 规则 | 文档推导 |
| 示波器上升时间 | 本章按 `tr≈0.35/BW` 复算 | 50 MHz ≈ 7 ns；10× 探头要补偿、地线要短 | 文档推导 |
| HardFault 工具链段 | 第 19 章的寄存器/栈帧结论；本章只取工具链段 | CFSR→VALID→`EXC_RETURN`→栈帧 PC→`addr2line`；PC 在 `sp[6]` | 文档推导 |
| 本章板级实验 | 尚未执行 | 待实测 | 未实测 |
| 来源实验表 | `docs/17` 实验节无原始读数；`06-flash` 无调试会话记录 | 没有上板时间戳或波形 | 未实测 |
| CMSIS 对账 | 本工作树缺 `mcu/.trellis/ref/cmsis` | 位号与寄存器定义未逐位复核 | 来源说法(未复核) |
| F103/F407 主频与回绕 | DS5319/DS8626/RM0008/RM0090 转引 + 本章复算 | 72/168 MHz；2^32 cycles 回绕 59.65/25.57 s | 文档推导 |
| 调试器关狗 | 第 19 章与 OpenOCD 文档转引；未在本章复跑 | OpenOCD 关 IWDT/TWDT；STM32 冻结位造成假阴性 | 来源说法(未复核) |

能互相对上的只有手册位、算术与宿主产物：7200 cycles 是 100 × 72 算出来的，0x18 字节是从 `nm` 输出里读出来的，断点落点 0x0 是 GDB 打印出来的。它们都不能证明某块板上的 SWO 真的通了，也不能证明某次 DWT 读数真的对应 100 µs。要补上后者，得按下面的台架留下原始输出。

### 待做台架

1. **断点预算**：在 F407 上同时下 6 个 `hbreak`，再加第 7 个，记录 GDB 的报错原文；在 M0+ 板（如有）上重复，确认第 3 个就失败。再下一个条件 `hbreak`，确认它仍占一个槽位。
2. **断点漂移**：同一份源码用 `-Og -g3` 与 `-O2 -g3` 各烧一次，在 `s = 0` 与 `s += p[i]` 两行下断点，记录 `info line`、`info break` 与实际停下的 PC；与本章宿主结果对照。
3. **SWO 四前提**：在 F407 上先断开 SWO 线、再关 `TRACE_IOEN`、再改错 TPIU 分频，各记录一次"无输出"；恢复后确认 ITM 端口 0 的字节流。用已知主频与已知字节数算实际波特率，和配置值对照。
4. **DWT 与外部时间戳**：用 DWT 测 100 µs 忙等，同时用逻辑分析仪在 GPIO 翻转沿上打时间戳；记录两者差值。再把主频从 72 MHz 换到 168 MHz，确认换算系数跟着换，而不是继续用 72。
5. **测量三件套**：对同一路 1 MHz 与 10 MHz SPI，分别用 24 MSa/s 逻辑分析仪与 50 MHz 示波器看；记录解码是否失败、边沿是否被带宽抹平、探头地线长短对振铃的影响。
6. **调试器假阴性**：在 F407 上让看门狗超时，先在调试器连着时观察，再按"烧录→断开→断电重上电"观察；记录两次是否复位。与[第 19 章](./19-watchdog-reset-hardfault.md)的台架合并执行。

这些台架都还没做。没有原始输出之前，本章只给判据与记录方法。

| 日期 | 平台/板卡 | 实验 | 原始结果 | 结论 |
| --- | --- | --- | --- | --- |
| 待实测 | F407 | 7 个硬件断点与条件断点 | | |
| 待实测 | F407 | `-Og`/`-O2` 断点落点 | | |
| 待实测 | F407 | SWO 四前提逐项拆除 | | |
| 待实测 | F407 | DWT 100 µs 对照逻辑分析仪 | | |
| 待实测 | F407 | 1/10 MHz SPI 三件套对照 | | |
| 待实测 | F407 | 调试器连着与脱机的看门狗复位 | | |

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 断点打不上，GDB 报 Cannot insert breakpoint | FPB 比较器用完，或软件断点写不进 Flash | `info break` 里的类型与数量；目标地址在 Flash 还是 RAM | 删旧断点；Flash 用 `hbreak`；或把函数搬进 RAM |
| 条件 `hbreak` 一加就超预算 | 条件断点仍占一个 FPB 比较器 | 数一数普通断点 + 条件断点 + 观察点 | 减少同时存在的断点，条件改在代码里判断 |
| `break file:line` 停在函数入口 | 该行被优化掉/内联，行表把断点挪到附近 | `info line` 报 "contains no code"；`info break` 的地址 | 用 `-Og`/`-O0` 重建；改断在稳定行或具体指令 |
| 断点地址与源码对不上 | ELF 与板上固件不是同一次构建，或链接地址有偏移 | ELF 的 SHA256/build ID；`info files`；反汇编地址 | 重烧同一份 ELF；用 `break *addr` 并核对 map |
| 软件断点在 Flash 上时好时坏 | 调试器在 Flash 补丁与 FPB 之间切换 | 换 `hbreak` 是否稳定；OpenOCD 的 flash breakpoint 设置 | Flash 代码统一用 `hbreak` |
| SWO 一个字节都没有 | 引脚、`DBGMCU_CR`、TRACECLK、探头四项缺一 | 逐项读回 PB3 复用、`TRACE_IOEN`/`TRACE_MODE`、TPIU 分频、SWO 接线 | 按四项顺序排查，不要先换板 |
| SWO 有数据但全是乱码 | TPIU 分频与调试器 SWO 时钟不匹配 | 目标主频、`ACPR`、调试器配置三者的数 | 把三者改成同一组 |
| ITM printf 卡死 | FIFO 满、没有消费者，或脱机后 `BKPT 0xAB` 无人服务 | 停在 `ITM_SendChar` 或 `BKPT` 指令；调试器是否连着 | 改成非阻塞/丢包；生产固件去掉半主机 |
| `CYCCNT` 一直是 0 | `TRCENA` 没开、`CYCCNTENA` 没开，或 M7 的 DWT 还锁着 | 读 `DEMCR` bit24、`DWT_CTRL` bit0；M7 读 `LAR` 状态 | 按四步流水线重来；M7 先写 `LAR` |
| cycles 换算出的时间不对 | 用了错误的主频，或时钟树/低功耗改了频 | 读 `SystemCoreClock`；对照示波器/逻辑分析仪时间戳 | 用当前实际主频换算；换主频就重算 |
| DWT 区间回绕后差出一个大数 | 区间超过 59.65 s（72 MHz）或 25.57 s（168 MHz） | 起止 cycles 的大小关系；区间长度 | 缩短区间，或中途记快照，用无符号减法 |
| DWT 读数抖动大 | 中断、Flash 等待周期、调试 halt、缓存 | 多次重复的分布；开/关中断对比 | 取多次中位数；报告测试条件，不跨构建比较 |
| `addr2line` 报 `??:0` | ELF 没带 `-g`、ELF 不对、地址不在代码区、Thumb 位没处理 | `readelf -S` 有无调试段；地址是否落在 `.text`；ELF 校验和 | 换正确的 `-g3` ELF；核对地址；必要时清 bit0 |
| HardFault 里 `bt` 看不到故障点 | `bt` 展开的是 handler 当前栈，不是异常帧 | `bt` 的帧地址与 `sp[6]` 的 PC 不一致 | 用栈帧 PC 与 `addr2line`，回链第 19 章 |
| 脱机后立刻 HardFault，调试时正常 | 半主机 `BKPT 0xAB` 无人服务，或依赖调试器冻结位 | 故障 PC 是否落在半主机 stub；脱机与在线的差异 | 去掉 `rdimon.specs`，重定向 `_write`；复位实验按脱机流程 |
| 优化后行为变了 | 代码有 UB、数据竞争、`volatile` 用错 | `-O0` 与 `-O2` 的输出差异；宿主 sanitizer | 修代码，不用 `-O0` 掩盖；`volatile` 不是同步 |
| 逻辑分析仪看不到毛刺 | 采样率不够、阈值不对，或毛刺窄于采样间隔 | 提高采样率后是否出现；换示波器看 | 用示波器看模拟边沿 |
| 示波器有振铃，逻辑分析仪却正常 | 逻辑分析仪把模拟波形切成 0/1 | 探头地线长度、带宽限制、10×/1× 设置 | 短地线、正确补偿、按带宽选探头 |
| 万用表电流比预期小 | 读的是平均值，或 burden voltage 改变了负载 | 串入分流电阻用示波器看峰值 | 用分流 + 差分探头测动态电流 |
| 调试器连着从不复位 | OpenOCD 关狗，或 `DBGMCU` 冻结位 | 脱机断电重上电后是否复位 | 烧录→断开→断电重上电；回链第 19 章 |

## 跨平台边界

F103 与 F407 在调试资源上同属 Cortex-M3/M4 一档，但时钟、FPU 与栈帧不同；M0/M0+ 与 M7 又是另外两档。

| 维度 | F103 | F407 |
| --- | --- | --- |
| 内核 | Cortex-M3 | Cortex-M4F |
| 最高主频 | 72 MHz | 168 MHz |
| FPB 指令比较器 | 6 | 6 |
| DWT `CYCCNT` | 有；按 72 MHz 换算 | 有；按 168 MHz 换算 |
| SWO 引脚 | PB3；需关 JTAG-DP、保留 SW-DP | PB3；配 AF0 |
| `DBGMCU_CR` | 0xE0042004，`TRACE_IOEN` bit5、`TRACE_MODE` bit7:6 | 同左 |
| 异常栈帧 | 基本 32 字节 | 基本 32 字节；FPU 扩展帧按 `EXC_RETURN` bit4 判断 |
| 2^32 cycles 回绕 | 59.65 s | 25.57 s |
| 调试接口 | SWD（JTAG 可选） | SWD（JTAG 可选） |
| 测量方法 | 逻辑分析仪/示波器/万用表同一套 | 同一套；高频边沿对带宽要求更高 |

跨内核时先改数字：M0 是 4 个 FPB，M0+ 只有 2 个，M7 是 8 个且 DWT 多一道 `LAR` 解锁。M0/M0+ 没有 FPU 扩展帧，`EXC_RETURN` 的取值集合更小；M7 的双发射与缓存会让 DWT cycles 与外部时间戳的对应更复杂，测时间要说明缓存与等待周期条件。

ESP32 不在本章主线内，但边界要划清：它没有 Cortex-M 的 CFSR/`EXC_RETURN`，调试走 JTAG/OpenOCD，panic 给的是 backtrace 而不是异常栈帧；OpenOCD 还会关掉 IWDT/TWDT。把 STM32 的 HardFault 取证或 SWD 接线原样搬过去，会把两套模型拼错。

换芯片时先查对应型号的 TRM 调试章、RM 的 DBGMCU 章与数据手册的时钟树，再改本章的换算表。工具链四步与 ELF 读法见[v0 第 5 章](../v0-foundations/05-toolchain-four-steps.md)；用定时器做外部时间基准见[v1 第 12 章](../v1-drivers/12-timers-pwm.md)；HardFault 寄存器细节见[第 19 章](./19-watchdog-reset-hardfault.md)；低功耗与调试冻结的交叉见[第 18 章](./18-low-power.md)。

## 离开检查

1. 为什么 `halt` 只是"请求停"，而不是把总线停住？AP 为什么能在 CPU 跑代码时读写内存？
2. SWD 的最小三线是什么？VTref 与 NRST 各做什么？为什么 JTAG 不能只用两根线？
3. FPB 指令比较器在 M0、M0+、M3、M4、M7 上各有多少？`06-flash:112` 错在哪？
4. 软件断点 `BKPT #0` 的机器码是什么？为什么 Flash 上可能打不上？"断点打不上"的三种原因是什么？
5. SWO 的四个前提是什么？缺一项时表现如何？为什么说它是"静默失败"？
6. 半主机用的是哪个 BKPT 立即数？为什么生产固件要去掉 `--specs=rdimon.specs`？
7. DWT 计时的四步流水线是什么？为什么先开 `TRCENA` 再清 `CYCCNT`？
8. 100 µs 在 72 MHz 与 168 MHz 下各是多少 cycles？1000 cycles 又各是多少 µs？2^32 cycles 的回绕时间各是多少？
9. Cortex-M7 的 DWT 为什么要写 `LAR`？地址与键值是什么？
10. `-g3` 能阻止内联吗？怎样用同一段代码的两档汇编与 `info line` 验证断点漂移？
11. 逻辑分析仪、示波器、万用表各回答什么问题？为什么逻辑分析仪不能替代示波器？
12. 采样率的 5–10× 规则怎么算？24 MSa/s 在 1 MHz 与 10 MHz 下每 bit 各有多少采样点？
13. 50 MHz 示波器的上升时间约是多少？10× 探头为什么要补偿？地线为什么要短？
14. 证据三角的三项是什么？为什么单有寄存器 dump 或单有 `printf` 都不算证据？
15. 调试器怎样制造"从不复位"的假阴性？复位实验的正确流程是什么？
16. HardFault 工具链段里，PC 在基本栈帧的哪个偏移？`EXC_RETURN` 的 bit2 与 bit4 各决定什么？为什么 `bt` 不可信？

<details>
<summary>对照答案</summary>

1. `halt` 是调试器往调试寄存器写的停核请求，内核在下一个指令边界停下；外设、DMA、看门狗可能继续跑。AP 是独立的访问端口，直接挂 AHB 总线矩阵，读写请求不经过 CPU，所以 CPU 跑着、停着或睡着都能访问目标地址。
2. SWDIO、SWCLK、GND。VTref 是目标给调试器的电压参考，不是第二路电源；NRST 可选，用于 connect under reset。JTAG 还需要 TMS 做状态机、TDI/TDO 做数据，至少四到五根，所以不能只用两根。
3. M0=4、M0+=2、M3=6、M4=6、M7=8。`06-flash:112` 写"M0/M0+ 只有 2 个"，把 M0 的 4 个也算成 2 个；M0+ 才是 2 个。
4. `BKPT #0` 是 `0xBE00`。它要求目标地址可写；Flash 要先擦扇区，软件断点写不进去。三种原因：FPB 比较器用完；地址不可写；该行没有代码或 ELF 不是板上那一份。
5. 引脚复用为 TRACESWO；`DBGMCU_CR` 的 `TRACE_IOEN=1`、`TRACE_MODE=00`；TRACECLK 有源且 TPIU 分频与调试器匹配；调试器支持 SWO 并接上。缺一项就没有输出，也没有错误提示。
6. 半主机用 `BKPT 0xAB`；`BKPT #0` 是调试断点。`rdimon.specs` 把 newlib 的 I/O 接到半主机，脱机后 `BKPT 0xAB` 无人服务，多数配置下升级成 HardFault，所以生产固件要去掉它并重定向 `_write`。
7. 开 `DEMCR.TRCENA`（bit24）→ `DWT->CYCCNT=0` → 置 `DWT_CTRL.CYCCNTENA`（bit0）→ 读 `DWT->CYCCNT`。先开 `TRCENA` 是因为 DWT 与 ITM 共用这个使能；没开时启动位可能不生效，读数一直是 0。
8. 100 µs：72 MHz 为 7200 cycles，168 MHz 为 16800 cycles。1000 cycles：72 MHz 为 13.89 µs，168 MHz 为 5.95 µs。2^32 cycles 回绕：72 MHz 为 59.65 s，168 MHz 为 25.57 s。
9. Cortex-M7 的 DWT 寄存器受锁保护；先往 `DWT->LAR`（0xE0001FB0）写 `0xC5ACCE55` 解锁，再配置 `CYCCNT`。两个来源都没提这一步，属于边界提示。
10. 不能。`-g3` 只增加调试信息种类，不改变代码生成，内联与重排照旧。验证方法：同一份源码分别用 `-Og -g3` 与 `-O2 -g3` 编译，`nm -S` 看符号有无、`objdump -d` 看指令与调用、GDB 的 `info line` 看目标行有无代码、`break` 后 `info break` 看实际落点；本章宿主实验里 `scale` 在 `-O2` 下消失，第 7 行断点从 0xc 漂到 0x0。
11. 逻辑分析仪答协议、时序与多路数字关系；示波器答边沿、过冲、振铃、噪声与电源纹波；万用表答平均电压/电流与通断。逻辑分析仪把模拟波形按阈值切成 0/1，看不到边沿形状、真实电压与采样点之间的窄毛刺，所以不能替代示波器。
12. 采样率至少是最快信号频率或边沿速率的 5–10 倍。24 MSa/s 在 1 MHz 下是 24 点/bit，在 10 MHz 下是 2.4 点/bit；后者对协议解码已经偏紧。
13. `tr≈0.35/BW`，50 MHz 约 7 ns。10× 探头要补偿，是为了让探头与示波器输入端的频率响应平坦，否则测到的过冲/振铃可能是探头造成的；地线短是为了减小地线电感，避免 LC 振铃污染被测信号。
14. 寄存器 dump、反汇编、时间戳/周期数。寄存器 dump 没有符号，反汇编没有 build ID 就可能不是板上固件，时间戳没有时钟来源就无法换算；`printf` 没有构建标识与时间基准，单有它不能证明因果。
15. 调试器通过 `DBGMCU` 冻结位或 OpenOCD 直接关掉看门狗，断点停住时狗不叫，于是"卡死后从不复位"。正确流程是烧录、断开调试器、断电再上电，再发故障命令；不能拿调试会话里的"没复位"当证据。
16. 基本栈帧里 PC 在偏移 24，即 `sp[6]`。`EXC_RETURN` bit2=0 用 MSP、bit2=1 用 PSP；bit4=0 表示 FPU 扩展帧（`0xFFFFFFE1/E9/ED`），bit4=1 是基本帧（`0xFFFFFFF1/F9/FD`）。取 PC 前要先按扩展帧布局定位基本帧。`bt` 展开的是 handler 当前的栈，不是异常发生前的调用栈，所以不能用它找故障点。

</details>
