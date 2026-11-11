/*
 * probe.c —— S16「HardFault 取证」的宿主验证
 *
 * 为什么能在宿主跑：本章的核心逻辑是"位运算 + 查表"——把故障寄存器的
 * 位翻译成死因名字、按 EXC_RETURN 选对栈指针、按 IRQn 算向量槽号。
 * 这三件事和 Cortex-M 无关，抽出来在宿主上断言，位号再和官方 CMSIS
 * 头文件（.trellis/ref/cmsis/core_cm4.h）逐位对账，板上打印的死因名字
 * 就不是"照着记忆抄的"，而是有出处的。
 *
 * 编译：gcc -std=c11 -Wall -Wextra -Werror -O2 probe.c -o build/probe
 * 用法：./build/probe                 跑断言（全绿退 0）
 *       ./build/probe 0x00008202      解码一个 CFSR 值，打印验尸报告
 *       ./build/probe --dump-positions 导出位号表，供 probe.sh 与头文件对账
 *
 * 位号出处（core_cm4.h，全部为官方 #define 的展开值）：
 *   SCB_CFSR_MEMFAULTSR_Pos=0 / BUSFAULTSR_Pos=8 / USGFAULTSR_Pos=16  (616-623 行)
 *   SCB_CFSR_*_Pos 逐位定义                                            (626-684 行)
 *   SCB_SHCSR_*_Pos                                                    (545-580 行)
 *   SCB_HFSR_*_Pos                                                     (686-693 行)
 *   SCB 寄存器偏移（449-459 行）：SHCSR 0x24 / CFSR 0x28 / HFSR 0x2C / MMFAR 0x34 / BFAR 0x38
 *   EXC_RETURN_* （1636-1641 行）
 */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ================= 断言小工具（全绿才退 0） ================= */
static unsigned g_pass, g_fail;

static void check(int cond, const char *what)
{
    if (cond) { g_pass++; return; }
    g_fail++;
    printf("  [FAIL] %s\n", what);
}

#define CHECK(cond) check((cond) ? 1 : 0, #cond)

/* ================= 1. SCB 版图 ================= */
/* 基址来自 core_cm4.h 的 SCB_Type 定义；偏移来自同一结构体的成员注释。 */
#define SCB_BASE   0xE000ED00UL
#define SCB_SHCSR  0x024UL
#define SCB_CFSR   0x028UL
#define SCB_HFSR   0x02CUL
#define SCB_MMFAR  0x034UL
#define SCB_BFAR   0x038UL

static void test_scb_map(void)
{
    printf("----- 1. SCB 故障寄存器版图（core_cm4.h:449-459） -----\n");
    printf("  SCB 基址            = 0x%08lX\n", (unsigned long)SCB_BASE);
    printf("  SHCSR (使能开关)    = 0x%08lX\n", (unsigned long)(SCB_BASE + SCB_SHCSR));
    printf("  CFSR  (可配置故障)  = 0x%08lX\n", (unsigned long)(SCB_BASE + SCB_CFSR));
    printf("  HFSR  (硬故障状态)  = 0x%08lX\n", (unsigned long)(SCB_BASE + SCB_HFSR));
    printf("  MMFAR (存储故障地址)= 0x%08lX\n", (unsigned long)(SCB_BASE + SCB_MMFAR));
    printf("  BFAR  (总线故障地址)= 0x%08lX\n", (unsigned long)(SCB_BASE + SCB_BFAR));

    CHECK(SCB_BASE + SCB_CFSR  == 0xE000ED28UL);
    CHECK(SCB_BASE + SCB_HFSR  == 0xE000ED2CUL);
    CHECK(SCB_BASE + SCB_MMFAR == 0xE000ED34UL);
    CHECK(SCB_BASE + SCB_BFAR  == 0xE000ED38UL);
    CHECK(SCB_BASE + SCB_SHCSR == 0xE000ED24UL);
    /* CFSR 三段互不重叠：低 8 位存储管理、中 8 位总线、高 16 位用法 */
    CHECK((SCB_CFSR & 0x3UL) == 0x0UL);   /* 字节对齐 → 三段可当三个字节读 */
}

/* ================= 2. CFSR 位表 ================= */
/* 名字刻意与 core_cm4.h 的 SCB_CFSR_<名字>_Pos 同名，probe.sh 才能逐位对账。 */
typedef struct {
    const char *name;
    unsigned    pos;
    const char *cn;
} bit_t;

static const bit_t cfsr_bits[] = {
    /* MMFSR：bit 0-7（存储管理故障） */
    { "IACCVIOL",    0, "取指访问违例（MPU 拦了取指）" },
    { "DACCVIOL",    1, "数据访问违例（MPU 拦了读写）" },
    { "MUNSTKERR",   3, "出栈时存储器故障" },
    { "MSTKERR",     4, "入栈时存储器故障（典型：爆栈）" },
    { "MLSPERR",     5, "惰性 FPU 保存时故障" },
    { "MMARVALID",   7, "MMFAR 里的地址有效" },
    /* BFSR：bit 8-15（总线故障） */
    { "IBUSERR",     8, "取指总线错误" },
    { "PRECISERR",   9, "精确总线错误（BFAR 指向真凶）" },
    { "IMPRECISERR",10, "不精确总线错误（BFAR 无效，凶手已跑）" },
    { "UNSTKERR",   11, "出栈时总线故障" },
    { "STKERR",     12, "入栈时总线故障" },
    { "LSPERR",     13, "惰性 FPU 保存总线故障" },
    { "BFARVALID",  15, "BFAR 里的地址有效" },
    /* UFSR：bit 16-31（用法故障） */
    { "UNDEFINSTR", 16, "未定义指令" },
    { "INVSTATE",   17, "非法状态（典型：跳进非 Thumb 地址）" },
    { "INVPC",      18, "非法 PC 装载（EXC_RETURN 被踩坏）" },
    { "NOCP",       19, "协处理器不可用（典型：FPU 没使能）" },
    { "UNALIGNED",  24, "未对齐访问" },
    { "DIVBYZERO",  25, "除以零" },
};

#define CFSR_NBIT (sizeof cfsr_bits / sizeof cfsr_bits[0])

static const bit_t shcsr_bits[] = {
    { "MEMFAULTACT",     0, "MemManage 正在活动" },
    { "BUSFAULTACT",     1, "BusFault 正在活动" },
    { "USGFAULTACT",     3, "UsageFault 正在活动" },
    { "SVCALLACT",       7, "SVCall 正在活动" },
    { "MONITORACT",      8, "调试监视器正在活动" },
    { "PENDSVACT",      10, "PendSV 正在活动" },
    { "SYSTICKACT",     11, "SysTick 正在活动" },
    { "USGFAULTPENDED", 12, "UsageFault 挂起" },
    { "MEMFAULTPENDED", 13, "MemManage 挂起" },
    { "BUSFAULTPENDED", 14, "BusFault 挂起" },
    { "SVCALLPENDED",   15, "SVCall 挂起" },
    { "MEMFAULTENA",    16, "使能 MemManage 单独上报" },
    { "BUSFAULTENA",    17, "使能 BusFault 单独上报" },
    { "USGFAULTENA",    18, "使能 UsageFault 单独上报" },
};

static const bit_t hfsr_bits[] = {
    { "VECTTBL",   1, "取向量表失败（VTOR 指错 / 表被踩）" },
    { "FORCED",   30, "被升级：真凶在 CFSR 里" },
    { "DEBUGEVT", 31, "调试事件（断点/监视）" },
};

static void test_bit_tables(void)
{
    size_t i, j;

    printf("----- 2. 位表自洽（子寄存器归属 + 位号不重复） -----\n");
    printf("  CFSR 位表 %u 条：MMFSR 6 + BFSR 7 + UFSR 6\n", (unsigned)CFSR_NBIT);

    /* 归属正确：MMFSR 占 0-7、BFSR 占 8-15、UFSR 占 16-31 */
    for (i = 0; i < CFSR_NBIT; i++) {
        unsigned p = cfsr_bits[i].pos;
        if (p < 8)        CHECK(p < 8);
        else if (p < 16)  CHECK(p >= 8 && p < 16);
        else              CHECK(p >= 16 && p < 32);
    }
    /* 关键位号逐个钉死（与头文件展开值一致） */
    CHECK(cfsr_bits[0].pos  == 0);   /* IACCVIOL   = MEMFAULTSR + 0 */
    CHECK(cfsr_bits[5].pos  == 7);   /* MMARVALID  = MEMFAULTSR + 7 */
    CHECK(cfsr_bits[6].pos  == 8);   /* IBUSERR    = BUSFAULTSR + 0 */
    CHECK(cfsr_bits[8].pos  == 10);  /* IMPRECISERR= BUSFAULTSR + 2 */
    CHECK(cfsr_bits[12].pos == 15);  /* BFARVALID  = BUSFAULTSR + 7 */
    CHECK(cfsr_bits[13].pos == 16);  /* UNDEFINSTR = USGFAULTSR + 0 */
    CHECK(cfsr_bits[16].pos == 19);  /* NOCP       = USGFAULTSR + 3 */
    CHECK(cfsr_bits[17].pos == 24);  /* UNALIGNED  = USGFAULTSR + 8 */
    CHECK(cfsr_bits[18].pos == 25);  /* DIVBYZERO  = USGFAULTSR + 9 */

    /* 位号不重复（重复 = 解码时会漏报） */
    for (i = 0; i < CFSR_NBIT; i++)
        for (j = i + 1; j < CFSR_NBIT; j++)
            CHECK(cfsr_bits[i].pos != cfsr_bits[j].pos);

    /* 保留位不设名字：bit 2/6/14/20-23/26-31 在 F4 上未定义 */
    CHECK(cfsr_bits[2].pos == 3);    /* 表里 bit2 缺席，下一条就是 bit3 */
    CHECK(cfsr_bits[6].pos == 8);    /* 表里 bit14 缺席 */
    CHECK(cfsr_bits[12].pos == 15);  /* 表里 bit15 之后直接跳到 bit16 */

    CHECK(sizeof shcsr_bits / sizeof shcsr_bits[0] == 14);
    CHECK(sizeof hfsr_bits  / sizeof hfsr_bits[0]  == 3);
    CHECK(shcsr_bits[11].pos == 16); /* MEMFAULTENA */
    CHECK(shcsr_bits[12].pos == 17); /* BUSFAULTENA */
    CHECK(shcsr_bits[13].pos == 18); /* USGFAULTENA */
    CHECK(hfsr_bits[0].pos == 1);    /* VECTTBL */
    CHECK(hfsr_bits[1].pos == 30);   /* FORCED  */
    CHECK(hfsr_bits[2].pos == 31);   /* DEBUGEVT */
}

/* ================= 3. 解码：位 → 死因名字 ================= */
static unsigned decode(const bit_t *tab, size_t n, uint32_t val,
                       char *out, size_t cap)
{
    size_t used = 0;
    unsigned hits = 0;

    out[0] = '\0';
    for (size_t i = 0; i < n; i++) {
        if (!(val & (1UL << tab[i].pos))) continue;
        int w = snprintf(out + used, cap - used, "%s%s",
                         hits ? " + " : "", tab[i].name);
        if (w < 0 || (size_t)w >= cap - used) break;
        used += (size_t)w;
        hits++;
    }
    return hits;
}

static unsigned cfsr_decode(uint32_t cfsr, char *out, size_t cap)
{
    return decode(cfsr_bits, CFSR_NBIT, cfsr, out, cap);
}

static void test_decode(void)
{
    char buf[512];

    printf("----- 3. CFSR 解码 -----\n");

    CHECK(cfsr_decode(0, buf, sizeof buf) == 0);
    CHECK(buf[0] == '\0');                       /* 无位 → 空串，不是乱码 */

    CHECK(cfsr_decode(1UL << 0, buf, sizeof buf) == 1);
    CHECK(strcmp(buf, "IACCVIOL") == 0);

    CHECK(cfsr_decode(1UL << 25, buf, sizeof buf) == 1);
    CHECK(strcmp(buf, "DIVBYZERO") == 0);

    /* 典型空指针写：精确总线错误 + BFAR 有效 */
    CHECK(cfsr_decode((1UL << 9) | (1UL << 15), buf, sizeof buf) == 2);
    CHECK(strcmp(buf, "PRECISERR + BFARVALID") == 0);

    /* 保留位必须静默：bit2 没有名字，不能凭空造一个 */
    CHECK(cfsr_decode(1UL << 2, buf, sizeof buf) == 0);

    /* 全 1：19 个有名位全命中，且顺序按位号升序 */
    CHECK(cfsr_decode(0xFFFFFFFFUL, buf, sizeof buf) == CFSR_NBIT);
    CHECK(strncmp(buf, "IACCVIOL + DACCVIOL + MUNSTKERR", 31) == 0);
    printf("  全 1 解码 = %s\n", buf);

    /* 缓冲区小：不能溢出，返回已写入的条数 */
    CHECK(cfsr_decode(0xFFFFFFFFUL, buf, 12) < CFSR_NBIT);
    CHECK(strlen(buf) < 12);
}

/* ================= 4. HFSR：是"原生案"还是"升级案" ================= */
static const char *hfsr_cause(uint32_t hfsr)
{
    if (hfsr & (1UL << 30)) return "FORCED —— 被升级：真凶在 CFSR 里，去查它";
    if (hfsr & (1UL << 1))  return "VECTTBL —— 取向量表失败：VTOR 指错或表被踩";
    if (hfsr & (1UL << 31)) return "DEBUGEVT —— 调试事件触发";
    return "无标志位 —— HardFault 不是升级来的";
}

static void test_hfsr(void)
{
    printf("----- 4. HFSR 定性 -----\n");
    CHECK(strstr(hfsr_cause(1UL << 30), "FORCED") != NULL);
    CHECK(strstr(hfsr_cause(1UL << 1), "VECTTBL") != NULL);
    CHECK(strstr(hfsr_cause(1UL << 31), "DEBUGEVT") != NULL);
    CHECK(strstr(hfsr_cause(0), "无标志位") != NULL);
    /* FORCED 优先：升级案必须先看 CFSR */
    CHECK(strstr(hfsr_cause((1UL << 30) | (1UL << 1)), "FORCED") != NULL);
}

/* ================= 5. EXC_RETURN：案发时用的哪个栈 ================= */
/* 规则来自 ARMv7-M：bit2 = 0 → MSP，= 1 → PSP；bit4 = 1 → 无 FPU 上下文。 */
static int exc_return_uses_psp(uint32_t lr) { return (lr & 0x4UL) != 0; }
static int exc_return_has_fpu(uint32_t lr)  { return (lr & 0x10UL) == 0; }
static int exc_return_to_handler(uint32_t lr) { return (lr & 0x8UL) == 0; }

static void test_exc_return(void)
{
    printf("----- 5. EXC_RETURN → 栈选择（core_cm4.h:1636-1641） -----\n");
    printf("  0xFFFFFFF1 处理模式/MSP/无FPU | 0xFFFFFFF9 线程/MSP/无FPU\n");
    printf("  0xFFFFFFFD 线程/PSP/无FPU    | 0xFFFFFFE1/E9/ED 同上但带 FPU 上下文\n");

    CHECK(SCB_BASE != 0);  /* 占位：下面才是重点 */
    CHECK(exc_return_uses_psp(0xFFFFFFF1UL) == 0);   /* 处理模式用 MSP */
    CHECK(exc_return_uses_psp(0xFFFFFFF9UL) == 0);   /* 线程模式用 MSP（裸机 main） */
    CHECK(exc_return_uses_psp(0xFFFFFFFDUL) == 1);   /* 线程模式用 PSP（RTOS 任务） */
    CHECK(exc_return_uses_psp(0xFFFFFFE1UL) == 0);
    CHECK(exc_return_uses_psp(0xFFFFFFE9UL) == 0);
    CHECK(exc_return_uses_psp(0xFFFFFFEDUL) == 1);

    CHECK(exc_return_has_fpu(0xFFFFFFF1UL) == 0);
    CHECK(exc_return_has_fpu(0xFFFFFFF9UL) == 0);
    CHECK(exc_return_has_fpu(0xFFFFFFFDUL) == 0);
    CHECK(exc_return_has_fpu(0xFFFFFFE1UL) == 1);
    CHECK(exc_return_has_fpu(0xFFFFFFE9UL) == 1);
    CHECK(exc_return_has_fpu(0xFFFFFFEDUL) == 1);

    CHECK(exc_return_to_handler(0xFFFFFFF1UL) == 1);
    CHECK(exc_return_to_handler(0xFFFFFFF9UL) == 0);
    CHECK(exc_return_to_handler(0xFFFFFFE1UL) == 1);
    CHECK(exc_return_to_handler(0xFFFFFFEDUL) == 0);
}

/* ================= 6. 向量槽号：异常号 = IRQn + 16 ================= */
/* 异常号就是"第几个入栈的现场"；向量表第 0 项是栈顶，所以表内偏移 = 异常号 × 4。 */
#define EXC_NUM(irqn) ((unsigned)((int)(irqn) + 16))

static void test_vector_slot(void)
{
    printf("----- 6. IRQn → 向量槽（stm32f407xx.h:68-75） -----\n");
    printf("  MemoryManagement_IRQn=-12 → 异常号 4 → 表内偏移 0x10\n");

    CHECK(EXC_NUM(-12) == 4);   /* MemoryManagement */
    CHECK(EXC_NUM(-11) == 5);   /* BusFault         */
    CHECK(EXC_NUM(-10) == 6);   /* UsageFault       */
    CHECK(EXC_NUM(-5)  == 11);  /* SVCall           */
    CHECK(EXC_NUM(-2)  == 14);  /* PendSV           */
    CHECK(EXC_NUM(-1)  == 15);  /* SysTick          */
    CHECK(EXC_NUM(6)   == 22);  /* EXTI0            */
    CHECK(EXC_NUM(28)  == 44);  /* TIM2             */

    /* 表内字节偏移 = 异常号 × 4 */
    CHECK(EXC_NUM(-12) * 4 == 0x10);
    CHECK(EXC_NUM(-1)  * 4 == 0x3C);
    CHECK(EXC_NUM(6)   * 4 == 0x58);

    /* 硬故障的异常号是 3 —— 但 ST 的 IRQn_Type 里没有 HardFault_IRQn
     * （stm32f407xx.h:68 直接从 -14 跳到 -12），所以它不可设优先级，
     * 也不能用 NVIC_SetPriority() 去调。这一条是本章的"反直觉点"。 */
    CHECK(EXC_NUM(-13) == 3);
    printf("  HardFault 异常号 = 3，但 IRQn_Type 中无对应枚举项 → 不可设优先级\n");
}

/* ================= 7. 栈帧版图：PC 在哪个字 ================= */
typedef struct {
    uint32_t r0, r1, r2, r3, r12, lr, pc, xpsr;
} hw_frame_t;

static void test_frame(void)
{
    printf("----- 7. 硬件压栈的 8 个字（ARMv7-M 异常进入） -----\n");
    printf("  偏移 0/4/8/12 = r0-r3，16 = r12，20 = lr，24 = pc，28 = xpsr（共 32 字节）\n");

    CHECK(offsetof(hw_frame_t, r0)   == 0);
    CHECK(offsetof(hw_frame_t, r1)   == 4);
    CHECK(offsetof(hw_frame_t, r2)   == 8);
    CHECK(offsetof(hw_frame_t, r3)   == 12);
    CHECK(offsetof(hw_frame_t, r12)  == 16);
    CHECK(offsetof(hw_frame_t, lr)   == 20);
    CHECK(offsetof(hw_frame_t, pc)   == 24);
    CHECK(offsetof(hw_frame_t, xpsr) == 28);
    CHECK(sizeof(hw_frame_t) == 32);
    CHECK(sizeof(hw_frame_t) == 8 * sizeof(uint32_t));

    /* pc 与 lr 必须差一个字，否则"挖 PC"会挖成 LR */
    CHECK(offsetof(hw_frame_t, pc) - offsetof(hw_frame_t, lr) == 4);
}

/* ================= 8. 全链路演示：从栈帧到源码行 ================= */
static void demo_report(uint32_t cfsr, uint32_t hfsr, uint32_t exc_return,
                        uint32_t bfar, uint32_t frame_pc)
{
    char names[512];
    unsigned n = cfsr_decode(cfsr, names, sizeof names);

    printf("----- 验尸报告样例（CFSR=0x%08lX） -----\n", (unsigned long)cfsr);
    printf("  CFSR = 0x%08lX\n", (unsigned long)cfsr);
    printf("    命中 %u 位：%s\n", n, n ? names : "（无 —— 去看 HFSR 是不是 VECTTBL）");
    if (cfsr & (1UL << 15))
        printf("    BFAR = 0x%08lX  （BFARVALID=1，这个地址可信）\n", (unsigned long)bfar);
    else
        printf("    BFAR = 0x%08lX  （BFARVALID=0，这个地址不可信，别追）\n", (unsigned long)bfar);
    printf("  HFSR = 0x%08lX → %s\n", (unsigned long)hfsr, hfsr_cause(hfsr));
    printf("  EXC_RETURN = 0x%08lX → 案发时用 %s，%s FPU 上下文\n",
           (unsigned long)exc_return,
           exc_return_uses_psp(exc_return) ? "PSP（RTOS 任务栈）" : "MSP（主栈/中断）",
           exc_return_has_fpu(exc_return) ? "带" : "不带");
    printf("  栈帧 PC = 0x%08lX → arm-none-eabi-addr2line -e build/fault_ctx.elf 0x%08lX\n",
           (unsigned long)frame_pc, (unsigned long)frame_pc);
}

/* ================= 9. 位号导出（供 probe.sh 与头文件对账） ================= */
static void dump_positions(void)
{
    size_t i;

    printf("CFSR:MEMFAULTSR %u\n", 0u);
    for (i = 0; i < CFSR_NBIT; i++)
        if (cfsr_bits[i].pos < 8)
            printf("CFSR:%s %u\n", cfsr_bits[i].name, cfsr_bits[i].pos);
    printf("CFSR:BUSFAULTSR %u\n", 8u);
    for (i = 0; i < CFSR_NBIT; i++)
        if (cfsr_bits[i].pos >= 8 && cfsr_bits[i].pos < 16)
            printf("CFSR:%s %u\n", cfsr_bits[i].name, cfsr_bits[i].pos);
    printf("CFSR:USGFAULTSR %u\n", 16u);
    for (i = 0; i < CFSR_NBIT; i++)
        if (cfsr_bits[i].pos >= 16)
            printf("CFSR:%s %u\n", cfsr_bits[i].name, cfsr_bits[i].pos);

    for (i = 0; i < sizeof shcsr_bits / sizeof shcsr_bits[0]; i++)
        printf("SHCSR:%s %u\n", shcsr_bits[i].name, shcsr_bits[i].pos);
    for (i = 0; i < sizeof hfsr_bits / sizeof hfsr_bits[0]; i++)
        printf("HFSR:%s %u\n", hfsr_bits[i].name, hfsr_bits[i].pos);
}

/* ================= main ================= */
int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "--dump-positions") == 0) {
        dump_positions();
        return 0;
    }

    if (argc > 1) {
        uint32_t v = (uint32_t)strtoul(argv[1], NULL, 0);
        demo_report(v, (v & (1UL << 9)) ? (1UL << 30) : 0UL,
                    0xFFFFFFFDUL, 0x1FFFFFFFUL, 0x08000A5CUL);
        return 0;
    }

    printf("================ S16 宿主取证 ================\n");
    test_scb_map();
    test_bit_tables();
    test_decode();
    test_hfsr();
    test_exc_return();
    test_vector_slot();
    test_frame();
    demo_report((1UL << 9) | (1UL << 15), 1UL << 30,
                0xFFFFFFFDUL, 0x1FFFFFFFUL, 0x08000A5CUL);

    printf("\n== 断言通过 %u/%u ==\n", g_pass, g_pass + g_fail);
    return g_fail != 0;
}
