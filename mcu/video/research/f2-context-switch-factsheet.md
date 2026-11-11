# F2《PendSV 换魂术：27 条指令、三层名字与伪造的第一帧》事实底稿

本文件是 `video/episodes/f2-context-switch/episode.json` 的上屏/口播数字对账底稿。所有“实测”输出行都从**本次**运行
`.temp/v2-facts/01-freertos-lab-probe.log`（128 行）原样摘出；`docs/rtos/freertos/02-context-switch.md` 只用于
「叙述前提」与「例外」两处，并逐条标明，不冒充本次读数。v1 的旧句已整体重写，见 §6。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/rtos/freertos/02-context-switch.md` |
| 取证脚本 | `code/rtos/01-freertos-lab/probe.sh`（五步：名字链 / 反汇编与条数 / 三行铁账 / 优先级账 / 伪造帧） |
| 本次日志 | `.temp/v2-facts/01-freertos-lab-probe.log`（128 行） |
| 名字链 | 日志 L1–L15：`port.c:138`、`port.c:505`、`FreeRTOSConfig.h:76`、`startup_stm32f407xx.s:111`、`nm` 输出 |
| 反汇编 | 日志 L17–L50：`PendSV_Handler` 全文、27 条正文、104 字节段大小 |
| 三行铁账 | 日志 L52–L67：9 字 = 36 字节、TCB 偏移 0、`#80` |
| 优先级账 | 日志 L69–L96：`255` 硬写、宏出现 0 次、`History.txt:301-302`、三道断言、`5<<4=80` |
| 首帧 | 日志 L98–L128：`pxPortInitialiseStack`、17+1=18=72、8+9+1、三个立即数、`bit4=1`、26 字 |
| 交叉工具链 | 本次简报记录为 10.3.1；**日志没有打印版本号**，`probe.sh` 注释说 10.3.1 或 15.2.1 均可。v2 不报工具链版本 |
| 板级输出 | 本集不需要开发板；日志没有 LED、串口、示波器或运行时寄存器快照 |
| 周期计数 | **没有**。日志只有指令条数、段大小与源码回退量；v2 不报实测周期 |
| 数字审计 | `npm run video:numbers -- f2-context-switch` → `52 个数字都有依据`（§7） |

本次日志能兑现的“实测”只有：符号链的四处行号与 `nm` 结果（L3–L15）、`PendSV_Handler` 的机器码与
27/104 两个计数（L17–L50）、三条从机器码读出的账（L52–L67）、优先级宏与断言的原文行号（L69–L96）、
以及首帧源码与 17+1/18/72 的加法（L98–L128）。其余技术机制若来自文档或指令语义，在 §5 单列。

## 2. 本集必须回答的 5 个问题

1. **为什么 `b xPortPendSVHandler` 断不到？** 名字有三层：源码层 `port.c:138` 与 `:505` 都叫
   `xPortPendSVHandler`（L3–L4）；预处理层 `FreeRTOSConfig.h:76` 把它宏改成 `PendSV_Handler`（L7）；
   链接层启动文件 `startup_stm32f407xx.s:111` 的向量表认后者（L9），`nm` 里也只剩大写 `T PendSV_Handler`
   （L11–L12）。宏在预处理阶段就把长名字抹掉，调试器查的是最终符号表，所以长名字“不存在”。
2. **为什么切换不能在 SysTick 里直接做？** 切换必须等更高优先级的 ISR 全部收队，否则会把某个 ISR
   切走一半。SysTick 的职责只是发现更高优先级任务就绪后置 PendSV 挂起位；真正的执行者 PendSV 被移植层
   硬设成 `255`，属于最低一档，排在所有更高优先级 ISR 之后（L77–L81、L95–L96）。临界区只把 `BASEPRI`
   抬到 `0x50`（= `5<<4` = `80`），只屏蔽优先级数值 ≥5 的中断；数值 0–4 的中断照样能打断，所以切换
   只能短、只能等。日志能证明“两者都被硬设成 255”与“临界区是 80”；“SysTick 只置挂起位”来自
   `xPortSysTickHandler` 的移植层源码，不在本日志输出里（见 §5）。
3. **三笔铁账。** ① 一条 `stmdb` 把 r4–r11 + EXC_RETURN 压进任务栈：9 个字 = 36 字节（L53–L55）；
   ② 新栈顶写进 TCB 偏移 0，凭据是 `tasks.c:360` 的成员注释“THIS MUST BE THE FIRST MEMBER”（L59–L63）；
   ③ 临界区立即数 `#80`，即 `5 << 4`（L64–L67）。
4. **27 条 / 104 字节买到了什么，分母是什么？** 从入口数到 `bx lr` 是 27 条正文（L49）；整段
   `.text.PendSV_Handler` 是 104 字节，含对齐填充与 `pxCurrentTCBConst` 字面量（L50）。买到的是
   一条没有循环、没有函数内跳转的直线：存、换指针、取。所谓“几百个周期”是**整次换魂**（27 条指令
   加访存）的量级口径，不是本日志的周期计数；本集不把它当实测，也不补一个周期数。
5. **没跑过的任务，第一帧怎么伪造？** `pxPortInitialiseStack` 手工回退 17 个字，加上指针最终停住的
   落点共 18 个字 = 72 字节（L122）；账目是硬件帧 8 + 软件帧 9 + 对齐 1（L123）。18 个槽里只有 5 个
   被真正赋值（xPSR、PC、LR、R0、EXC_RETURN），其余故意留脏。这 5 条赋值来自 `port.c` 的
   `pxPortInitialiseStack` 源码；日志 L98–L116 只保留回退量，没有打印赋值行，所以“5 个写过”按源码叙述计，
   `5` 这个 token 的日志出处另见 L73 / L96（优先级公式）。
   初始 `EXC_RETURN = 0xfffffffd` 的 bit4 = 1，表示没有 FPU 行李（L119、L124）；任务第一次真正用到浮点，
   硬件才把帧扩展成 26 个字（L125），所以首帧是 18 字而不是 26 字。

## 3. 反汇编逐行（日志 L18–L45，正文 27 条）

| # | 地址 | 指令 | 作用 |
|---|---|---|---|
| 1 | `0x00` | `mrs r0, PSP` | 取当前任务栈顶；任务栈用 PSP，MSP 归内核 |
| 2 | `0x04` | `isb sy` | 指令同步屏障 |
| 3 | `0x08` | `ldr r3, [pc, #84]` | 取 `pxCurrentTCBConst`（日志注明目标 `0x60`） |
| 4 | `0x0a` | `ldr r2, [r3, #0]` | r2 = 当前 TCB |
| 5 | `0x0c` | `tst.w lr, #16` | 查 EXC_RETURN 的 bit4 |
| 6 | `0x10` | `it eq` | 为下一条条件执行做准备 |
| 7 | `0x12` | `vstmdbeq r0!, {s16-s31}` | bit4=0（有 FPU 帧）时补压 16 个浮点寄存器 |
| 8 | `0x16` | `stmdb r0!, {r4-r11, sl, fp, lr}` | 软件帧：9 个字，一条压完 |
| 9 | `0x1a` | `str r0, [r2, #0]` | 新栈顶写进 TCB 偏移 0（封棺） |
| 10 | `0x1c` | `stmdb sp!, {r0, r3}` | 在 MSP 上暂存 r0/r3，准备进临界区 |
| 11 | `0x20` | `mov.w r0, #80` | 临界区优先级 `0x50` |
| 12 | `0x24` | `msr BASEPRI, r0` | 抬 BASEPRI，屏蔽数值 ≥5 的中断 |
| 13 | `0x28` | `dsb sy` | 数据同步屏障 |
| 14 | `0x2c` | `isb sy` | 指令同步屏障 |
| 15 | `0x30` | `bl vTaskSwitchContext` | 全剧唯一一句 C：换当前 TCB 指针 |
| 16 | `0x34` | `mov.w r0, #0` | 出口清 r0 |
| 17 | `0x38` | `msr BASEPRI, r0` | BASEPRI 清零，退出临界区 |
| 18 | `0x3c` | `pop {r0, r3}` | 从 MSP 取回 r0/r3 |
| 19 | `0x3e` | `ldr r1, [r3, #0]` | r1 = 换过之后的当前 TCB |
| 20 | `0x40` | `ldr r0, [r1, #0]` | r0 = 新任务栈顶（TCB 偏移 0） |
| 21 | `0x42` | `ldmia.w r0!, {r4-r11, sl, fp, lr}` | 弹回 9 个软件字 |
| 22 | `0x46` | `tst.w lr, #16` | 再查 bit4 |
| 23 | `0x4a` | `it eq` | 为下一条条件执行做准备 |
| 24 | `0x4c` | `vldmiaeq r0!, {s16-s31}` | 有 FPU 行李时领回 16 个浮点寄存器 |
| 25 | `0x50` | `msr PSP, r0` | PSP 指向新栈顶 |
| 26 | `0x54` | `isb sy` | 指令同步屏障 |
| 27 | `0x58` | `bx lr` | 异常返回；硬件按 EXC_RETURN 选栈并弹 8 字硬件帧 |

注：`0x5a`、`0x5c` 是两条 `nop` 填充，不计入 27 条；`0x60` 起是 `pxCurrentTCBConst` 字面量。
104 字节包含这些填充与字面量，所以不能把 104 当成“27 条指令的净长度”。日志没有打印每条指令的
周期数，也没有打印运行时寄存器值。

## 4. 上屏数字逐项对账（52 个 token）

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 同一行日志里的多个 token 合并一行；每个 token 的完整出处同时写在 `f2-context-switch-numbers.json`。

### 4.1 三层名字

| token | 证据 | 代表场景 |
|---|---|---|
| `138` / `505` | L3 `138:void xPortPendSVHandler...`；L4 `505:void xPortPendSVHandler( void )` | B: hook-02、name-map、cta；发行 |
| `76` | L7 `76:#define xPortPendSVHandler  PendSV_Handler` | B: hook-02、name-map、cta；D: name-map；封面；发行 |
| `111` | L9 `111:  .word PendSV_Handler` | B: hook-02、name-map、cta；D: name-map；封面；发行 |

### 4.2 反汇编地址与立即数

| token | 证据 | 代表场景 |
|---|---|---|
| `0x0` | L19 `0: f3ef 8009 mrs r0, PSP`（入口地址 `0x00`） | B: asm-store、count-27 |
| `0xc` | L23 `c: f01e 0f10 tst.w lr, #16` | B: asm-store |
| `0x12` | L25 `12: ed20 8a10 vstmdbeq r0!, {s16-s31}` | B: asm-store |
| `0x16` | L26 `16: e920 4ff0 stmdb r0!, {...}` | B: frame-split、asm-store |
| `0x1a` | L27 `1a: 6010 str r0, [r2, #0]` | B: frame-split、asm-store、tcb-zero |
| `0x20` | L29 `20: f04f 0050 mov.w r0, #80 ; 0x50` | B: asm-switch |
| `0x24` | L30 `24: f380 8811 msr BASEPRI, r0` | B: asm-switch |
| `0x30` | L33 `30: f7ff fffe bl 0 <vTaskSwitchContext>` | B: asm-switch、count-27 |
| `0x34` | L34 `34: f04f 0000 mov.w r0, #0` | B: asm-switch |
| `0x38` | L35 `38: f380 8811 msr BASEPRI, r0` | B: asm-switch |
| `0x42` | L39 `42: e8b0 4ff0 ldmia.w r0!, {...}` | B: asm-load |
| `0x50` | L29 `mov.w r0, #80 ; 0x50`；L43 `50: f380 8809 msr PSP, r0` | B: prio-danger、asm-switch、asm-load、punch；发行 |
| `0x58` | L45 `58: 4770 bx lr` | B: asm-load、count-27 |
| `0x14` | L127 `14: f04f 7280 mov.w r2, #16777216 ; 0x1000000` | B: forge-imm |
| `0x22` | L128 `22: f023 0201 bic.w r2, r3, #1` | B: forge-imm |

注：`0x50` 有两个出处：L29 的立即数（临界区 `#80`）与 L43 的指令地址（`msr PSP`）。两者不是同一个测量，
但都落在同一份反汇编里；v2 在 `prio-danger` 与 `asm-switch` 只用它的“立即数”含义，`asm-load` 标题里的
`0x50` 是地址，不赋予优先级含义。

### 4.3 计数与帧长

| token | 证据 | 代表场景 |
|---|---|---|
| `27` | L49 `正文指令条数 = 27 条（数到 bx lr 为止）` | B: hook-03、count-27、punch、cta；D: count-27；封面；发行 |
| `104` | L50 `段大小 = 104 字节（含对齐填充和 pxCurrentTCBConst 字面量）` | B: count-27、cta；D: count-27；封面；发行 |
| `9` / `36` | L53 `9 个字 = 36 字节`；L123 软件帧 9 | B: hook-03、frame-split、decision、gdb-steps、forge-src、punch、cta；D: cs-2、punch；发行 |
| `8` / `1` / `18` | L123 `硬件帧 8 + 软件帧 9 + 对齐 1 = 18`；L128 `#1` 清 PC 低位；L124 bit4=1 | B: hook-03、frame-split、gdb-steps、forge-src、punch、cta；D: forge-src、punch；发行 |
| `17` / `72` | L122 `指针回退 17 个字，加上最后停住的那个落点共 18 个字 = 72 字节` | B: forge-src、cta；D: forge-src；发行 |
| `26` | L125 `任务第一次跑出彩点（用到浮点）时才由硬件扩展成 26 个字` | B: lazy |
| `16` | L54/L58 `{s16-s31}` 共 16 个浮点寄存器；L78 `<< 16UL` | B: lazy、why-low、asm-store |
| `5` | L73 `5 << (8 - configPRIO_BITS)`；L96 `5<<4 = 80`；首帧“5 个写过”按 `port.c` 源码的 5 条赋值计，日志只保留回退量 | B: prio-danger、forge-src；发行 |

### 4.4 优先级与临界区

| token | 证据 | 代表场景 |
|---|---|---|
| `255` | L77 `portMIN_INTERRUPT_PRIORITY ( 255UL )`；L95 `PendSV/SysTick 由内核硬设成 255` | B: why-systick-not、why-low、punch；D: punch；发行 |
| `65` / `66` / `67` | L77–L79 `portMIN_INTERRUPT_PRIORITY`、`PENDSV_PRI << 16`、`SYSTICK_PRI << 24` | B: why-low |
| `434` / `435` | L80–L81 `SHPR3 |= PENDSV_PRI` / `SYSTICK_PRI` | B: why-low |
| `80` | L29 `mov.w r0, #80 ; 0x50`；L65 `#80 = 5 << 4` | B: asm-switch、cta |
| `4` / `5` / `8` | L71 `configPRIO_BITS 4`；L73 `5 << (8 - configPRIO_BITS)`；L96 `5<<4 = 80` | B: prio-danger；发行 |
| `16` / `24` | L78 / L79 两个左移位数（PendSV 槽 / SysTick 槽） | B: why-low |
| `301` / `302` | L86–L87 `configKERNEL_INTERRUPT_PRIORITY is now obsolete...` | B: why-low |
| `379` / `383` / `413` | L89–L91 三道 `configASSERT` | B: prio-danger；发行 |
| `0` | L27 `[r2, #0]`；L38 `[r1, #0]`；L82–L84 宏在两个文件中各出现 0 次 | 多处；略 |

注：`configKERNEL_INTERRUPT_PRIORITY` 在 `FreeRTOSConfig.h:61` 确实写着 255（L72），但内核不读它；
日志 L82–L84 对 `port.c` 与 `portmacro.h` 的 `grep -c` 都是 0，L86–L87 的变更记录明说 obsolete。
真正被读的是 `configMAX_SYSCALL_INTERRUPT_PRIORITY`（L73），落地 `0x50`。

### 4.5 首帧立即数与入口

| token | 证据 | 代表场景 |
|---|---|---|
| `0x1000000` / `16777216` | L118 `portINITIAL_XPSR ( 0x01000000 )`；L127 `mov.w r2, #16777216 ; 0x1000000` | B: forge-imm |
| `0xfffffffd` | L119 `portINITIAL_EXC_RETURN ( 0xfffffffd )` | B: forge-imm |
| `0xfffffffe` | L120 `portSTART_ADDRESS_MASK ( 0xfffffffeUL )` | B: forge-imm |
| `360` | L63 `凭据 tasks.c:360 ... THIS MUST BE THE FIRST MEMBER` | B: tcb-zero；D: tcb-zero；发行 |
| `01` | 路径 `code/rtos/01-freertos-lab` 的目录编号；不是 probe 读数 | B: cta；D: cta；发行；`exceptions` |

注：`0x01000000` 与 `0x1000000` 是同一个 32 位值的两种写法，数字审计会把前者规范化为后者；
`16777216` 是同一行日志里的十进制写法，不是第三次测量。`01` 是路径编号，已在 numbers JSON 的
`exceptions` 里放行。

## 5. 已知未取证项（明确“不上屏”或只作叙述前提）

| 项 | 状态 | 处理 |
|---|---|---|
| 一次切换的周期数 | 日志没有计时、没有 DWT/周期计数器 | 只说“几百个周期”是量级口径；不报具体周期，不冒充实测 |
| SysTick 写 ICSR bit28 / `0xE000ED04` | 本日志不打印该寄存器与位号 | v2 不上屏 `28`、`0xE000ED04`；只说“置 PendSV 挂起位” |
| 在 ISR 里切换会把 ISR 切走一半 | 来自文档与移植层语义，不在本次日志 | 只作解释性前提，不附数字 |
| `xPortSysTickHandler` 的源码 | 日志只给优先级与临界区，不给 tick handler 行号 | 旁白不报它的行号；只说职责分工 |
| 工具链版本 | 日志没有版本行 | v2 不报 `10.3.1` / `15.2.1` / `gcc` 版本 |
| 正文 90 字节、9 条 16 位编码、6/4/4 填充 | 日志只给 27 条与 104 字节 | v2 不报 90、9 条压缩编码、6/4/4；只说 104 含填充与字面量 |
| 运行时寄存器值、PSP 实际地址 | 日志只有指令与静态源码 | 只讲“r0 里是新栈顶”“PSP 到后半段才更新”，不报地址 |
| 向量表全文 | 日志只摘 `startup:111` 一行 | 只说这一行认 `PendSV_Handler`，不描述整张表 |
| `vTaskSwitchContext` 内部选择算法 | 日志只有 `bl` 目标，没有函数体 | 只说“换当前 TCB 指针”；选任务留给 F3 |
| V11.1.0 完整版本号 | 日志路径含 `freertos-v11`，但未打印完整版本 | 只在 codeLabel 写“V11 的 ARMv7-M 移植层”，不报 `11.1.0` |
| `task.h:171` 同名成员陷阱 | 文档有，日志不打印 | v2 不写这个陷阱，避免无本次凭据的支线 |
| TaskA / TaskB | 动画角色名，不是日志符号 | 只作动画叙事，不当成实测对象 |

## 6. 与 v1 的关系

v1 的 29 场已整体重写为 v2 的 29 场（6 节）；抖音 11 场是本次按 `pick` 重排的短版。v1 中以下说法
**没有本次日志依据或与日志冲突**，已删除或改写：

- **“SysTick 优先级高”**：v1 用它解释“为什么不在 SysTick 里切”。但日志 L80–L81 显示 SysTick 与
  PendSV 都被硬设成 255（最低一档），所以“SysTick 优先级高”不成立。v2 改成“SysTick 只置挂起位，
  PendSV 才是执行者；切换要等更高优先级 ISR 收队”，不再给 SysTick 安一个更高的优先级。
- **ICSR 第 28 位 / `0xE000ED04`**：v1 上屏了这个位号；本次日志没有打印它。v2 删除 `28` 与寄存器
  地址，只说“挂起位”。
- **正文 90 字节、9 条 16 位编码、6/4/4 填充账**：v1 把 104 拆成 90+6+4+4；本次日志只打印 27 与 104，
  没有逐条编码宽度。v2 删除 90、6、4、4 的拆账，明确 104 含对齐填充与字面量。
- **“主栈指针要到第十条才更新”**：v1 用序号数指令；v2 改成“PSP 到后半段 `msr PSP, r0` 才更新”，
  与 L43 对得上，不依赖第几条的口径。
- **“xPSR 的保留位”**：v1 把 bit24 说成“架构要求的保留位”。v2 改说“bit24 是 Thumb 状态位，
  异常返回后任务以 Thumb 模式开跑”，避免把 T 位叫成保留位。
- **“改名只发生在三个异常入口”**：v1 的概括超出了日志；`nm` 只打印 `PendSV_Handler`、`SVC_Handler`、
  `prvTaskExitError` 等符号（L11–L15），不足以证明“只有三个入口被改名”。v2 只讲 PendSV 这一条链，
  并只用 `prvTaskExitError` 说明小写 `t` 是文件内静态符号。
- **“三十多个优先级选一个只要一个周期”**：v1 的下一集预告没有本次日志依据；v2 删除数字，只说
  “就绪位图 + 前导零计数指令”，把具体账留给 F3。
- **“两个任务同时在跑”作为实测**：这是动画隐喻，不是日志读数。v2 保留“换魂”的叙事框架，但没有
  把它写成 probe 结论。

逐句比对：v1 与 v2 的旁白**没有整句复用**；最长公共片段 26 字，是复现命令里的路径
`code/rtos/01-freertos-lab`，不是叙述句。v2 没有“最快/最简单/只要一个周期”这类绝对化说法。

## 7. 审计回填

- `npm run video:lint -- f2-context-switch`：✅ 通过：bilibili 29 场，douyin 11 场。
- `npm run video:numbers -- f2-context-switch`：✅ f2-context-switch: 52 个数字都有依据。
- 旁白字数（实测，`resolveScenes` 后逐场相加）：bilibili **3262** 字（目标 3000–3400，硬 2087–3510）；
  douyin **276** 字（目标 240–280，硬 135–305）。
- 片头钩子：只有 `hook-01` 是 `kind: "hook"`，62 字 × 0.1955 s/字 ≈ **12.12 s**，≤15.0 s；
  `hook-02` 是 `code`、`hook-03` 是 `card`，不并入钩子时长。
- 抖音文案：caption 三行非空白字数 12 / 18 / 21，合计 51（上限 20 / 24 / 62）；pinned 含
  `sh code/rtos/01-freertos-lab/probe.sh`；repro 同命令。
- 小红书：标题 12 字（≤20）；正文 613 字（≤1000）；合集“通往单片机之路”非空；pinned 含复现命令。
- 封面：`variant: "vs"`，四尺寸齐全；`vs.labels = ["SOURCE","SYMBOL"]` 是“源码名 / 符号名”的角色标签，
  不是两次测量；数字只用了 27 与 104，均在 L49–L50 有行。
- 本稿未构建视频、未提交、未改本任务三份交付物之外的文件（报告另存于
  `.superpowers/sdd/implement/task-13-f2-authoring.md`）。
