/*
 * fault_ctx.c —— S16 的"板上侧"：naked HardFault_Handler + 栈帧取证
 *
 * 本文件只编译、不在宿主运行（宿主跑不动 Cortex-M 代码）。
 * probe.sh 用 arm-none-eabi-gcc -g3 把它编成 ELF，然后：
 *   1. objdump -d  → 看"选栈指针"在 Thumb-2 下的真实指令序列；
 *   2. nm + addr2line → 走一遍 PC → 源码行 的全链路；
 *   3. -Wl,-Map → 用 map 文件交叉验证符号地址。
 *
 * 死因常量出处：.trellis/ref/cmsis/core_cm4.h
 *   CFSR 0xE000ED28 (455 行) / HFSR 0xE000ED2C (456 行)
 *   MMFAR 0xE000ED34 (458 行) / BFAR 0xE000ED38 (459 行)
 *   硬件压栈的 8 个字顺序：r0,r1,r2,r3,r12,lr,pc,xpsr
 */
#include <stdint.h>

/* 事故记录本：GDB 连上来直接读这几个符号 */
volatile uint32_t g_cfsr, g_hfsr, g_mmfar, g_bfar;
volatile uint32_t g_frame_pc, g_frame_lr, g_frame_xpsr;
volatile uint32_t g_used_psp;

typedef struct {
    uint32_t r0, r1, r2, r3, r12, lr, pc, xpsr;
} hw_frame_t;

/* C 侧：拿到栈帧指针，抄走三份验尸报告 */
__attribute__((noinline))
void hardfault_report(uint32_t *frame)
{
    g_cfsr      = *(volatile uint32_t *)0xE000ED28UL;   /* CFSR  */
    g_hfsr      = *(volatile uint32_t *)0xE000ED2CUL;   /* HFSR  */
    g_mmfar     = *(volatile uint32_t *)0xE000ED34UL;   /* MMFAR */
    g_bfar      = *(volatile uint32_t *)0xE000ED38UL;   /* BFAR  */
    g_frame_lr  = frame[5];
    g_frame_pc  = frame[6];                             /* ← 案发时的 PC */
    g_frame_xpsr = frame[7];
    for (;;) {
        /* 停在这里，等 GDB 来读上面这些符号。
         * 故意不用 printf：故障上下文里跑复杂库函数可能二次故障。 */
    }
}

/*
 * 汇编侧：唯一的难点是"案发时用的是 MSP 还是 PSP"。
 * 异常进入时 LR 被硬件写成 EXC_RETURN：
 *   bit2 = 0 → 用 MSP（裸机 / 中断嵌套）
 *   bit2 = 1 → 用 PSP（RTOS 任务）
 * 所以先 tst lr,#4，再把对应栈指针塞进 r0 当第一个参数。
 */
__attribute__((naked))
void HardFault_Handler(void)
{
    __asm volatile(
        "tst   lr, #4            \n"  /* bit2 决定用哪个栈 */
        "ite   eq                \n"
        "mrseq r0, msp           \n"  /* eq：MSP */
        "mrsne r0, psp           \n"  /* ne：PSP */
        "b     hardfault_report  \n"  /* 交给 C 侧抄报告 */
    );
}

/* ================= 三大命案的"尸体"：只编译，不运行 ================= */
/* 每具尸体都在下一行留了 PC 落点，addr2line 应指回这些行号。 */

volatile uint32_t *g_null_ptr = (volatile uint32_t *)0;

__attribute__((noinline))
void crash_null(void)
{
    *g_null_ptr = 0xDEADBEEF;   /* 空指针写 → 预期 PRECISERR + BFARVALID，BFAR≈0 */
}

__attribute__((noinline))
void crash_unaligned(void)
{
    static volatile uint8_t buf[8];
    volatile uint32_t *p = (volatile uint32_t *)(buf + 1);  /* 奇地址 */
    *p = 1;   /* → 预期 UNALIGNED（前提：CCR.UNALIGN_TRP=1，见 fault_demo_entry） */
}

__attribute__((noinline))
int crash_divzero(int x)
{
    volatile int zero = 0;
    return x / zero;   /* → 预期 DIVBYZERO（前提：CCR.DIV_0_TRP=1，见 fault_demo_entry） */
}

/* 让 ELF 有个入口，且不依赖启动文件（-nostdlib 链接）。
 *
 * 关键前提：Cortex-M4 默认**容忍**未对齐的单字 LDR/STR，除零也只是让 SDIV
 * 返回 0——两具尸体都会"死不掉"。要它们真按上面的注释触发故障，得先打开
 * SCB->CCR 里的两个 trap 位：
 *   UNALIGN_TRP = bit3（core_cm4.h:563）
 *   DIV_0_TRP   = bit4（core_cm4.h:560）
 * SCB->CCR 地址 = 0xE000ED00 + 0x014 = 0xE000ED14（core_cm4.h:452 给出偏移 0x014） */
__attribute__((noinline))
void fault_demo_entry(void)
{
    *(volatile uint32_t *)0xE000ED14UL |= (1UL << 3) | (1UL << 4);
    crash_null();
    crash_unaligned();
    (void)crash_divzero(1);
}
