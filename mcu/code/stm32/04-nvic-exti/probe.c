/* probe.c —— S4 NVIC/EXTI 章全部数值取证（宿主运行，不需要开发板）
 *
 * 两道防线：
 *   1. 编译期 _Static_assert：正文手抄数字（CH_*）对撞 probe.sh 从
 *      .trellis/ref/cmsis 头文件现挖的 -D 宏（HDR_*）——两边不一致直接编译失败，
 *      章节里的每个地址/位号因此都被"钉"在头文件上；
 *   2. 运行期 CHECK()：由头文件常数推导向量槽位 / ISER / IPR / 优先级编码，
 *      与手算基准值逐一比对，末尾打印 == 断言通过 N/N ==。
 *
 * 头文件出处（probe.sh 会打印同样的行号）：
 *   stm32f407xx.h —— IRQn 枚举、PERIPH/APB2/SYSCFG/EXTI 基址、EXTI/SYSCFG 结构体
 *   core_cm4.h    —— SCS/NVIC/SCB/SysTick 基址、AIRCR.PRIGROUP、NVIC_SetPriority
 */

#include <stdint.h>
#include <stdio.h>

#ifndef HDR_PERIPH_BASE
#error "请用 probe.sh 构建：它会从头文件提取 HDR_* 宏再编译本文件"
#endif

/* ========== 正文手抄数字（人读头文件的第二来源） ========== */
#define CH_PERIPH_BASE     0x40000000UL /* stm32f407xx.h:910  */
#define CH_APB2_OFF        0x00010000UL /* stm32f407xx.h:928  */
#define CH_SYSCFG_OFF      0x3800UL     /* stm32f407xx.h:974  */
#define CH_EXTI_OFF        0x3C00UL     /* stm32f407xx.h:975  */
#define CH_SCS_BASE        0xE000E000UL /* core_cm4.h:1550    */
#define CH_SYSTICK_OFF     0x0010UL     /* core_cm4.h:1555    */
#define CH_NVIC_OFF        0x0100UL     /* core_cm4.h:1556    */
#define CH_SCB_OFF         0x0D00UL     /* core_cm4.h:1557    */
#define CH_PRIO_BITS       4U           /* stm32f407xx.h:49   */
#define CH_PRIGROUP_POS    8U           /* core_cm4.h:531     */
#define CH_VECTKEY         0x5FAUL      /* core_cm4.h:1661    */
#define CH_SYSCFGEN_POS    14U          /* stm32f407xx.h:10076 */
#define CH_EXTI0_PF_CODE   0x5U         /* stm32f407xx.h:11662 */

/* ========== 编译期对撞：头文件提取值 vs 正文数字 ========== */
_Static_assert(CH_PERIPH_BASE  == HDR_PERIPH_BASE,  "PERIPH_BASE 与 stm32f407xx.h 不符");
_Static_assert(CH_APB2_OFF     == HDR_APB2_OFF,     "APB2 偏移与 stm32f407xx.h 不符");
_Static_assert(CH_SYSCFG_OFF   == HDR_SYSCFG_OFF,   "SYSCFG 偏移与 stm32f407xx.h 不符");
_Static_assert(CH_EXTI_OFF     == HDR_EXTI_OFF,     "EXTI 偏移与 stm32f407xx.h 不符");
_Static_assert(CH_SCS_BASE     == HDR_SCS_BASE,     "SCS_BASE 与 core_cm4.h 不符");
_Static_assert(CH_SYSTICK_OFF  == HDR_SYSTICK_OFF,  "SysTick 偏移与 core_cm4.h 不符");
_Static_assert(CH_NVIC_OFF     == HDR_NVIC_OFF,     "NVIC 偏移与 core_cm4.h 不符");
_Static_assert(CH_SCB_OFF      == HDR_SCB_OFF,      "SCB 偏移与 core_cm4.h 不符");
_Static_assert(CH_PRIO_BITS    == HDR_PRIO_BITS,    "__NVIC_PRIO_BITS 与头文件不符");
_Static_assert(CH_PRIGROUP_POS == HDR_PRIGROUP_POS, "PRIGROUP_Pos 与 core_cm4.h 不符");
_Static_assert(CH_VECTKEY      == HDR_VECTKEY,      "AIRCR 写入钥匙与 core_cm4.h 不符");
_Static_assert(CH_SYSCFGEN_POS == HDR_SYSCFGEN_POS, "SYSCFGEN 位号与头文件不符");
_Static_assert(CH_EXTI0_PF_CODE == HDR_EXTI0_PF,    "EXTI0 选 F 口的编码与头文件不符");

/* IRQn 枚举值对撞（stm32f407xx.h:75..117） */
_Static_assert(HDR_SYSTICK_IRQN   == -1, "SysTick_IRQn 应为 -1");
_Static_assert(HDR_EXTI0_IRQN     ==  6, "EXTI0_IRQn 应为 6");
_Static_assert(HDR_EXTI1_IRQN     ==  7, "EXTI1_IRQn 应为 7");
_Static_assert(HDR_EXTI9_5_IRQN   == 23, "EXTI9_5_IRQn 应为 23");
_Static_assert(HDR_TIM2_IRQN      == 28, "TIM2_IRQn 应为 28");
_Static_assert(HDR_USART1_IRQN    == 37, "USART1_IRQn 应为 37");
_Static_assert(HDR_EXTI15_10_IRQN == 40, "EXTI15_10_IRQn 应为 40");

/* ========== 由基址链推出绝对地址 ========== */
#define APB2_BASE    (CH_PERIPH_BASE + CH_APB2_OFF)    /* 0x40010000 */
#define SYSCFG_BASE  (APB2_BASE + CH_SYSCFG_OFF)       /* 0x40013800 */
#define EXTI_BASE    (APB2_BASE + CH_EXTI_OFF)         /* 0x40013C00 */
#define NVIC_BASE    (CH_SCS_BASE + CH_NVIC_OFF)       /* 0xE000E100 */
#define SCB_BASE     (CH_SCS_BASE + CH_SCB_OFF)        /* 0xE000ED00 */
#define SYSTICK_BASE (CH_SCS_BASE + CH_SYSTICK_OFF)    /* 0xE000E010 */
#define NVIC_ISER0   (NVIC_BASE + 0x000UL)             /* core_cm4.h:413 偏移 0x000 */
#define NVIC_IP0     (NVIC_BASE + 0x300UL)             /* core_cm4.h:423 偏移 0x300 */
#define SCB_AIRCR    (SCB_BASE + 0x00CUL)              /* core_cm4.h:450 偏移 0x00C */

/* EXTI 寄存器偏移（stm32f407xx.h:444-449 结构体注释里的 Address offset） */
_Static_assert(HDR_EXTI_IMR_OFF   == 0x00UL, "IMR 偏移");
_Static_assert(HDR_EXTI_EMR_OFF   == 0x04UL, "EMR 偏移");
_Static_assert(HDR_EXTI_RTSR_OFF  == 0x08UL, "RTSR 偏移");
_Static_assert(HDR_EXTI_FTSR_OFF  == 0x0CUL, "FTSR 偏移");
_Static_assert(HDR_EXTI_SWIER_OFF == 0x10UL, "SWIER 偏移");
_Static_assert(HDR_EXTI_PR_OFF    == 0x14UL, "PR 偏移");
_Static_assert(HDR_SYSCFG_EXTICR_OFF == 0x08UL, "EXTICR 起始偏移");

/* ========== 运行期核对 ========== */
static int n_check, n_fail;
#define CHECK(cond)                                                          \
    do {                                                                     \
        n_check++;                                                           \
        if (!(cond)) {                                                       \
            n_fail++;                                                        \
            printf("  [失败] probe.c:%d: %s\n", __LINE__, #cond);            \
        }                                                                    \
    } while (0)

typedef struct {
    const char *name;
    int32_t     irqn;
} irq_row_t;

static void print_irq_table(void)
{
    static const irq_row_t rows[] = {
        { "SysTick",    HDR_SYSTICK_IRQN   },
        { "EXTI0",      HDR_EXTI0_IRQN     },
        { "EXTI1",      HDR_EXTI1_IRQN     },
        { "EXTI9_5",    HDR_EXTI9_5_IRQN   },
        { "TIM2",       HDR_TIM2_IRQN      },
        { "USART1",     HDR_USART1_IRQN    },
        { "EXTI15_10",  HDR_EXTI15_10_IRQN },
    };

    printf("IRQn -> 向量槽 / ISER / IPR 映射（槽=IRQn+16, ISER下标=IRQn/32, 位=IRQn%%32）\n");
    printf("%-10s %5s %6s %7s %8s %5s %12s %12s\n",
           "中断", "IRQn", "槽", "槽偏移", "ISER下标", "位", "ISER地址", "IP字节地址");
    for (unsigned i = 0; i < sizeof(rows) / sizeof(rows[0]); i++) {
        int32_t n = rows[i].irqn;
        if (n >= 0) {
            printf("%-10s %5d %6d 0x%04x %8d %5d 0x%08X 0x%08X\n",
                   rows[i].name, n, n + 16, (unsigned)(n + 16) * 4U,
                   n / 32, n % 32,
                   (unsigned)(NVIC_ISER0 + (uint32_t)(n / 32) * 4U),
                   (unsigned)(NVIC_IP0 + (uint32_t)n));
        } else {
            /* 负数 IRQn 是内核异常：优先级走 SCB->SHP[(IRQn & 0xF) - 4]（core_cm4.h:1822） */
            uint32_t shp_idx = (((uint32_t)n) & 0xFUL) - 4UL;
            printf("%-10s %5d %6d 0x%04x %8s %5s %12s 0x%08X\n",
                   rows[i].name, n, n + 16, (unsigned)(n + 16) * 4U,
                   "-", "-", "(SHP)", (unsigned)(SCB_BASE + 0x18UL + shp_idx));
        }
    }

    /* 手算基准值逐一钉死 */
    CHECK(HDR_EXTI0_IRQN + 16 == 22);                 /* EXTI0 占向量表第 22 槽      */
    CHECK((HDR_EXTI0_IRQN + 16) * 4 == 0x58);         /* 槽字节偏移 0x58             */
    CHECK(HDR_EXTI0_IRQN / 32 == 0 && HDR_EXTI0_IRQN % 32 == 6);   /* ISER0 bit6   */
    CHECK(NVIC_ISER0 == 0xE000E100UL);
    CHECK(NVIC_IP0 + HDR_EXTI0_IRQN == 0xE000E406UL); /* EXTI0 优先级字节地址      */
    CHECK(HDR_EXTI9_5_IRQN + 16 == 39);
    CHECK(HDR_EXTI9_5_IRQN % 32 == 23);
    CHECK(NVIC_IP0 + HDR_EXTI9_5_IRQN == 0xE000E417UL);
    CHECK(HDR_TIM2_IRQN / 32 == 0 && HDR_TIM2_IRQN % 32 == 28);    /* ISER0 bit28  */
    CHECK(HDR_USART1_IRQN / 32 == 1 && HDR_USART1_IRQN % 32 == 5); /* ISER1 bit5   */
    CHECK(NVIC_ISER0 + 4 == 0xE000E104UL);            /* ISER1 的地址              */
    CHECK(HDR_EXTI15_10_IRQN + 16 == 56);
    CHECK(HDR_EXTI15_10_IRQN / 32 == 1 && HDR_EXTI15_10_IRQN % 32 == 8);
    CHECK(NVIC_IP0 + HDR_EXTI15_10_IRQN == 0xE000E428UL);
    /* SysTick：槽 15，优先级字节在 SCB_SHP[11] = 0xE000ED18+11 */
    CHECK(HDR_SYSTICK_IRQN + 16 == 15);
    CHECK(((((uint32_t)HDR_SYSTICK_IRQN) & 0xFUL) - 4UL) == 11UL);
    CHECK(SCB_BASE + 0x18UL + 11UL == 0xE000ED23UL);
}

/* PRIGROUP 位段拆分 —— 照抄 core_cm4.h:1867-1868 的公式 */
static void split_prigroup(uint32_t g, uint32_t *pre_bits, uint32_t *sub_bits)
{
    *pre_bits = ((7UL - g) > CH_PRIO_BITS) ? CH_PRIO_BITS : (7UL - g);
    *sub_bits = ((g + CH_PRIO_BITS) < 7UL) ? 0UL : ((g - 7UL) + CH_PRIO_BITS);
}

static void print_prigroup_table(void)
{
    printf("\nAIRCR.PRIGROUP（位 [%d:%d]，core_cm4.h:531-532）如何切 %d 位优先级字段\n",
           CH_PRIGROUP_POS + 2, CH_PRIGROUP_POS, CH_PRIO_BITS);
    printf("%-9s %-10s %-10s %s\n", "PRIGROUP", "抢占位数", "子优先级位", "写法（VECTKEY|组值<<8）");
    for (uint32_t g = 0; g <= 7; g++) {
        uint32_t pre, sub, aircr;
        split_prigroup(g, &pre, &sub);
        aircr = (CH_VECTKEY << 16) | (g << CH_PRIGROUP_POS);
        printf("%-9d %-10d %-10d 0x%08X\n", (int)g, (int)pre, (int)sub, (unsigned)aircr);
        CHECK(pre + sub == CH_PRIO_BITS);
    }
    {   uint32_t pre, sub;
        split_prigroup(3, &pre, &sub); CHECK(pre == 4 && sub == 0);  /* "全抢占"组   */
        split_prigroup(4, &pre, &sub); CHECK(pre == 3 && sub == 1);
        split_prigroup(5, &pre, &sub); CHECK(pre == 2 && sub == 2);
        split_prigroup(7, &pre, &sub); CHECK(pre == 0 && sub == 4);  /* "全子优先级" */
    }
    CHECK(((CH_VECTKEY << 16) | (3UL << CH_PRIGROUP_POS)) == 0x05FA0300UL);
    CHECK(((CH_VECTKEY << 16) | (5UL << CH_PRIGROUP_POS)) == 0x05FA0500UL);
    CHECK(SCB_AIRCR == 0xE000ED0CUL);
}

/* NVIC_SetPriority 编码 —— core_cm4.h:1818：IP[IRQn] = (priority << (8-4)) & 0xFF */
static uint8_t encode_prio(uint32_t prio)
{
    return (uint8_t)((prio << (8U - CH_PRIO_BITS)) & 0xFFUL);
}

static void print_prio_encoding(void)
{
    static const uint32_t demos[] = { 0, 1, 5, 10, 15 };
    printf("\nNVIC_SetPriority 编码（写入 IP 字节的值 = 逻辑优先级 << %d，只占高 %d 位）\n",
           8U - CH_PRIO_BITS, CH_PRIO_BITS);
    printf("%-10s %s\n", "逻辑优先级", "存入 0xE000E4xx 的字节");
    for (unsigned i = 0; i < sizeof(demos) / sizeof(demos[0]); i++)
        printf("%-10d 0x%02X\n", (int)demos[i], encode_prio(demos[i]));
    CHECK(encode_prio(0)  == 0x00);
    CHECK(encode_prio(5)  == 0x50);
    CHECK(encode_prio(15) == 0xF0);
    /* 越界写法：& 0xFF 把高位截掉，不报错，而是变成另一个合法优先级。
       注意不是"溢到隔壁中断的字节"——IP[] 按下标取字节，越界只截本字节的值。 */
    static const uint32_t over[] = { 16, 17, 20, 255, 256 };
    printf("越界写法（同一个字节被截断，读回来是另一个合法优先级）\n");
    printf("%-10s %-8s %s\n", "逻辑优先级", "存入字节", "读回来当作");
    for (unsigned i = 0; i < sizeof(over) / sizeof(over[0]); i++)
        printf("%-10d 0x%02X     %u\n",
               (int)over[i], encode_prio(over[i]), encode_prio(over[i]) >> (8U - CH_PRIO_BITS));
    CHECK(encode_prio(16) == 0x00);   /* 16<<4 = 256 → &0xFF → 最高优先级 0 */
    CHECK(encode_prio(17) == 0x10);   /* 变成优先级 1 */
    CHECK(encode_prio(20) == 0x40);   /* 变成优先级 4 */
    CHECK(encode_prio(256) == 0x00);
    /* 回读解码：GetPriority 右移 4 位（core_cm4.h:1841），原样回来 */
    CHECK((encode_prio(5) >> (8U - CH_PRIO_BITS)) == 5U);
    /* 写低 4 位是无效的：0x5F 读回来还是 5 */
    CHECK(((encode_prio(5) | 0x0FU) >> (8U - CH_PRIO_BITS)) == 5U);
}

/* SYSCFG EXTICR 多路选择：线 N -> EXTICR[N/4] 的 [(N%4)*4+3 : (N%4)*4] */
static void print_exticr_mux(void)
{
    printf("\nSYSCFG EXTICR 多路选择（EXTICR 基址 0x%08X，起始偏移 0x%02X）\n",
           (unsigned)(SYSCFG_BASE + HDR_SYSCFG_EXTICR_OFF),
           (unsigned)HDR_SYSCFG_EXTICR_OFF);
    printf("%-8s %-9s %-12s %s\n", "EXTI线", "寄存器", "字段位", "选 F 口要写的值");
    static const uint32_t lines[] = { 0, 1, 6, 10 };
    for (unsigned i = 0; i < sizeof(lines) / sizeof(lines[0]); i++) {
        uint32_t n = lines[i], reg = n / 4, shift = (n % 4) * 4U;
        printf("%-8d EXTICR%-2d [%2d:%2d]   0x%08X\n", (int)n, (int)reg + 1,
               (int)(shift + 3), (int)shift,
               (unsigned)(CH_EXTI0_PF_CODE << shift));
    }
    CHECK(SYSCFG_BASE == 0x40013800UL);
    CHECK(SYSCFG_BASE + HDR_SYSCFG_EXTICR_OFF == 0x40013808UL);   /* EXTICR1 地址 */
    CHECK((CH_EXTI0_PF_CODE << ((6 % 4) * 4U)) == 0x00000500UL);  /* PF6 -> EXTICR2[11:8]=0101 */
    CHECK((6 / 4) == 1 && (6 % 4) == 2 && (6 % 4) * 4 == 8);
    CHECK((10 / 4) == 2 && (10 % 4) == 2);                        /* EXTI10 -> EXTICR3 */
    /* SYSCFG 时钟使能位：RCC_APB2ENR bit14 = 0x00004000（stm32f407xx.h:10076） */
    CHECK((1UL << CH_SYSCFGEN_POS) == 0x00004000UL);
}

static void print_exti_block(void)
{
    printf("\nEXTI 寄存器块（基址 0x%08X = APB2 0x%08X + 0x%02X）\n",
           (unsigned)EXTI_BASE, (unsigned)APB2_BASE, (unsigned)CH_EXTI_OFF);
    printf("IMR=0x%08X EMR=0x%08X RTSR=0x%08X FTSR=0x%08X SWIER=0x%08X PR=0x%08X\n",
           (unsigned)(EXTI_BASE + 0x00UL), (unsigned)(EXTI_BASE + 0x04UL),
           (unsigned)(EXTI_BASE + 0x08UL), (unsigned)(EXTI_BASE + 0x0CUL),
           (unsigned)(EXTI_BASE + 0x10UL), (unsigned)(EXTI_BASE + 0x14UL));
    CHECK(EXTI_BASE == 0x40013C00UL);
    CHECK(EXTI_BASE + HDR_EXTI_PR_OFF == 0x40013C14UL);   /* ISR 里写 1 清挂起的就是它 */
    CHECK(EXTI_BASE + HDR_EXTI_IMR_OFF == 0x40013C00UL);
    CHECK(EXTI_BASE + HDR_EXTI_FTSR_OFF == 0x40013C0CUL);
    CHECK(SYSTICK_BASE == 0xE000E010UL);
}

int main(void)
{
    printf("== 编译期 _Static_assert 全部通过：正文数字与头文件提取值一致 ==\n\n");
    printf("基址链：PERIPH 0x%08X -> APB2 +0x%05X -> SYSCFG +0x%04X / EXTI +0x%04X\n",
           (unsigned)CH_PERIPH_BASE, (unsigned)CH_APB2_OFF,
           (unsigned)CH_SYSCFG_OFF, (unsigned)CH_EXTI_OFF);
    printf("内核链：SCS 0x%08X -> SysTick +0x%04X / NVIC +0x%04X / SCB +0x%04X\n\n",
           (unsigned)CH_SCS_BASE, (unsigned)CH_SYSTICK_OFF,
           (unsigned)CH_NVIC_OFF, (unsigned)CH_SCB_OFF);

    print_irq_table();
    print_prigroup_table();
    print_prio_encoding();
    print_exticr_mux();
    print_exti_block();

    printf("\n== 断言通过 %d/%d ==\n", n_check - n_fail, n_check);
    return n_fail ? 1 : 0;
}
