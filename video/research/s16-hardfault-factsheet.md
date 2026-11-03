# S16 HardFault 事实表（v2 重制底稿）

来源：

- `.temp/v2-facts/s16-probe.log`（2026-10-29 本机实跑，EXIT=0；宿主 gcc 16.1.0，交叉 arm-none-eabi-gcc 10.3.1）
- `code/stm32/16-debug-hardfault/probe.sh` / `fault_ctx.c` / `probe.c`
- `docs/stm32/16-debug-hardfault.md`（S16 正文，已与探针同步）

## 一、探针四段输出（屏幕上每条都可回指）

### 第 1 段：宿主断言（274/274）

- SCB 基址 0xE000ED00；SHCSR 0xE000ED24；CFSR 0xE000ED28；HFSR 0xE000ED2C；MMFAR 0xE000ED34；BFAR 0xE000ED38。
- CFSR 位表 19 条：MMFSR 6 + BFSR 7 + UFSR 6；全 1 解码 19 个名字全中。
- 样例验尸报告：CFSR = 0x00008200 → 命中 PRECISERR + BFARVALID；BFAR = 0x1FFFFFFF（BFARVALID=1 可信）；HFSR = 0x40000000 → FORCED；EXC_RETURN = 0xFFFFFFFD → PSP（无 FPU 上下文）；栈帧 PC = 0x08000A5C。
- EXC_RETURN 全集：0xFFFFFFF1 处理/MSP/无FPU；0xFFFFFFF9 线程/MSP/无FPU；0xFFFFFFFD 线程/PSP/无FPU；0xFFFFFFE1/E9/ED 带 FPU。
- IRQn：MemoryManagement_IRQn = -12 → 异常号 4 → 表内偏移 0x10；HardFault 异常号 = 3，IRQn_Type 无对应枚举 → 不可设优先级。
- 硬件压栈 8 字：偏移 0/4/8/12 = r0-r3，16 = r12，20 = lr，24 = pc，28 = xpsr，共 32 字节。

### 第 2 段：位号对账

- 头文件（.trellis/ref/cmsis/core_cm4.h）39 条位号 vs 本章侧 39 条，逐位一致。

### 第 3 段：交叉反汇编

- HardFault_Handler 全文：
  `8000070 f01e 0f04 tst.w lr,#4` / `8000074 bf0c ite eq` / `8000076 f3ef 8008 mrseq r0,MSP` / `800007a f3ef 8009 mrsne r0,PSP` / `800007e f7ff bfbf b.w 8000000 <hardfault_report>` / `8000082 bf00 nop`。
- .text：`0 .text 0000010c 08000000 08000000 00010000 2**2` → 268 字节，VMA 0x08000000。
- 符号：crash_divzero 0x080000c4；crash_null 0x08000084；crash_unaligned 0x080000a4；HardFault_Handler 0x08000070；hardfault_report 0x08000000。
- crash_null：入口 0x08000084 → fault_ctx.c:69（左花括号）；str 指令 0x0800008e → fault_ctx.c:70（真凶行）。**差 0x0A = 10 个字节**（v1 文稿写 6，错）。
- crash_null 机身：8000084 push {r7}；8000086 add r7,sp,#0；8000088 ldr r3,[pc,#16]→800009c；800008a ldr r3,[r3,#0]（取 0）；800008c ldr r2,[pc,#16]→80000a0；800008e str r2,[r3,#0]（往 0 写）；8000090 nop；8000092 mov sp,r7；8000094 ldr.w r7,[sp],#4；8000098 bx lr；literal 800009c = 0x0801012c（g_null_ptr），80000a0 = 0xdeadbeef。
- crash_unaligned：80000aa ldr r3,[pc,#20]→80000c0；80000ac str r3,[r7,#4]；80000ae ldr r3,[r7,#4]；80000b0 movs r2,#1；80000b2 str r2,[r3,#0]（普通 str）；80000c0 = 0x08010131（奇地址，末位 1）。
- crash_divzero：80000d0 ldr r3,[r7,#12]；80000d2 ldr r2,[r7,#4]；80000d4 fb92 f3f3 sdiv r3,r2,r3；机身再无 bl / b.xx / udf / bkpt / svc（反向断言命中 = 0）。
- fault_demo_entry：80000e8 ldr r3,[pc,#28]→8000108；80000ee f043 0318 orr.w r3,r3,#24；80000f2 str；8000108 = 0xe000ed14（SCB->CCR）；之后依次调用 crash_null / crash_unaligned / crash_divzero。
- map 文件同一地址：`0x08000084 crash_null`。
- 机身断言 6 条全中：orr #24、0xe000ed14、crash_null 有 str、crash_divzero 有 sdiv、crash_divzero 无陷阱指令、crash_unaligned 字面量池奇地址。

### 第 4 段：条件指令字节学

- 正确版 h_psp：f01e 0f04 / bf0c / f3ef 8008 / f3ef 8009 / 4770；hex `1ef0040f0cbfeff30880eff309807047`。
- 笔误版 h_msp：f3ef 8008 / f3ef 8008；hex `1ef0040f0cbfeff30880eff308807047`。
- cmp -l：差异字节数 = 1，明细：偏移 13，octal 11 → 10（0x09 → 0x08）。
- MRS 编码矩阵 5 对：f3ef 8008 MSP、f3ef 8108 r1 MSP、f3ef 8c08 ip MSP、f3ef 8009 PSP、f3ef 8000 CPSR；每对 eq / ne 两个词字节完全相同；条件只在 ite 的 bf0c 词里；Rd 在 bits[11:8]，源寄存器编号在 imm5（MSP=0x08，PSP=0x09）。
- 三种写错：bad_slot（eq 槽 PSP / ne 槽 MSP）GAS 照收；bad_cond 拒绝 `incorrect condition in IT block`；bad_noite 拒绝 `thumb conditional instruction should be in IT block`。

## 二、正文补充口径（docs 第七节等）

- 五虎：空指针（PRECISERR + BFARVALID）；未对齐（UNALIGNED，默认被硬件兜住，CCR.UNALIGN_TRP bit3 打开才报案；多字 LDM/STM、LDRD/STRD 永远不许未对齐）；除零（DIVBYZERO，CCR.DIV_0_TRP bit4；不开 SDIV 返回 0）；爆栈（MSTKERR/MUNSTKERR 或 STKERR/UNSTKERR，最有诊断价值）；优先级配错（通常无 CFSR 位，卡死在 handler，靠栈帧 LR/PC 还原）。
- 两个 CCR 开关复位默认值：文档明写「待回填核对」，视频不猜。
- addr2line 前提：编译带 -g3，优先 -O0；-O2 行号可能对不上。

## 三、v1 文稿需修正的硬伤（本轮一并改）

1. 入口 0x08000084 → 真凶 0x0800008e 差 **10** 字节；v1 cover/proof、codeB、旁白、发布简介均写「差 6 个字节」→ 全改 10。
2. addr2line 69 行是函数左花括号，70 行才是空指针写；v1 code-a2l 写成「69 行取出 0」→ 改按文档口径。
3. `ep.title` / 开场「三条寄存器」→「三个寄存器」。
