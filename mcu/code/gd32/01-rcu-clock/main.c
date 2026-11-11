/**
 * main.c —— gd32/01-rcu-clock：GD32F4xx RCU 时钟树配置（寄存器级）
 *
 * 教学点（对照 docs/gd32/01-rcu-clock.md，全部事实有官方源）：
 *   1. PLL 与 STM32F4 同布局：RCU_PLL = PSC[5:0] | N[14:6] | P[17:16]=(P/2)-1
 *      | SRC[22] | Q[27:24]；官方 200M 档参数 PSC=25/N=400/P=2/Q=9
 *      （system_gd32f4xx.c:946-948 @10d02f4）。
 *   2. 电压档三件套带硬件回执：LDOVS → HDEN 等 PMU_CS.HDRF → HDS 等 HDSRF
 *      （gd32f4xx_pmu.h:59-73）。F405/407 的 VOS 无回执，这里恰恰相反。
 *   3. 官方 system 文件不设 FMC 等待周期——FMC_WS 由本工程显式设置；
 *      WSCNT 支持 0~11 档（gd32f4xx_fmc.h:150-161）。
 *      FMC_WS_VALUE 默认保守超配：欠配等待会取指跑飞，超配只损失一点速度；
 *      准确对照表在用户手册（UM），待核验后回填。
 *   4. 官方 demo 晶振超时是 while(1) 死等（system_gd32f4xx.c:942-945）——
 *      本工程改为回退 IRC16M 并置 g_clock_status，错误路径不摆烂。
 *
 * 目标芯片：GD32F450（宏 GD32F450；RAM/Flash 容量见 gd32f4xx.ld 顶部注释）。
 * 构建：make（xPack arm-none-eabi-gcc，见 README）。
 */

#include <stdint.h>

/* ================= 基地址（gd32f4xx.h @10d02f4） ================= */
#define AHB1_BUS_BASE   0x40020000U
#define APB1_BUS_BASE   0x40000000U
#define GPIOA_BASE      (AHB1_BUS_BASE + 0x0000U)
#define RCU_BASE        (AHB1_BUS_BASE + 0x3800U)   /*!< RCU（gd32f4xx.h:343） */
#define FMC_BASE        (AHB1_BUS_BASE + 0x3C00U)   /*!< FMC（gd32f4xx.h:344） */
#define PMU_BASE        (APB1_BUS_BASE + 0x7000U)   /*!< PMU（gd32f4xx.h:330） */

/* RCU 寄存器（gd32f4xx_rcu.h:44-56） */
#define RCU_CTL         (*(volatile uint32_t *)(RCU_BASE + 0x00U))
#define RCU_PLL         (*(volatile uint32_t *)(RCU_BASE + 0x04U))
#define RCU_CFG0        (*(volatile uint32_t *)(RCU_BASE + 0x08U))
#define RCU_AHB1EN      (*(volatile uint32_t *)(RCU_BASE + 0x30U))
#define RCU_APB1EN      (*(volatile uint32_t *)(RCU_BASE + 0x40U))

/* PMU / FMC（gd32f4xx_pmu.h:45-46 / gd32f4xx_fmc.h:46） */
#define PMU_CTL         (*(volatile uint32_t *)(PMU_BASE + 0x00U))
#define PMU_CS          (*(volatile uint32_t *)(PMU_BASE + 0x04U))
#define FMC_WS          (*(volatile uint32_t *)(FMC_BASE + 0x00U))

/* GPIOA（gd32f4xx_gpio.h:52-61） */
#define GPIOA_CTL       (*(volatile uint32_t *)(GPIOA_BASE + 0x00U))
#define GPIOA_AFSEL1    (*(volatile uint32_t *)(GPIOA_BASE + 0x24U))  /*!< AFSEL1 管脚 8~15（:61） */

/* ================= 位定义（官方库头文件） ================= */
/* RCU_CTL（gd32f4xx_rcu.h:83-88） */
#define RCU_CTL_HXTALEN     (1UL << 16)
#define RCU_CTL_HXTALSTB    (1UL << 17)
#define RCU_CTL_PLLEN       (1UL << 24)
#define RCU_CTL_PLLSTB      (1UL << 25)

/* RCU_CFG0（gd32f4xx_rcu.h:102-112） */
#define RCU_CFG0_SCS        (3UL << 0)
#define RCU_CFG0_SCSS       (3UL << 2)
#define RCU_CKSYSSRC_IRC16M (0UL << 0)
#define RCU_CKSYSSRC_PLLP   (2UL << 0)
#define RCU_SCSS_IRC16M     (0UL << 2)
#define RCU_SCSS_HXTAL      (1UL << 2)   /*!< gd32f4xx_rcu.h:819 */
#define RCU_SCSS_PLLP       (2UL << 2)
#define RCU_AHB_CKSYS_DIV1  (0UL << 4)   /*!< AHBPSC[6:4 区] = 0（gd32f4xx_rcu.h:824） */
#define RCU_APB2_CKAHB_DIV2 (4UL << 13)  /*!< APB2PSC = 4（:845） */
#define RCU_APB1_CKAHB_DIV4 (5UL << 10)  /*!< APB1PSC = 5（:838） */
#define RCU_CFG0_CKOUT0SEL  (3UL << 21)  /*!< CKOUT0SEL[22:21] */
#define RCU_CFG0_CKOUT0DIV  (7UL << 24)  /*!< CKOUT0DIV[26:24] */
#define RCU_CKOUT0SRC_PLLP  (3UL << 21)  /*!< CK_OUT0 源 = PLLP（:889） */
#define RCU_CKOUT0_DIV4     (6UL << 24)  /*!< /4（:900） */

/* RCU_PLL（system_gd32f4xx.c:946-948 反推位域 + gd32f4xx_rcu.h:993） */
#define RCU_PLLSRC_HXTAL    (1UL << 22)

/* RCU_APB1EN（gd32f4xx_rcu.h:261） */
#define RCU_APB1EN_PMUEN    (1UL << 28)

/* PMU（gd32f4xx_pmu.h:59-73） */
#define PMU_CTL_LDOVS       (3UL << 14)
#define PMU_CTL_HDEN        (1UL << 16)
#define PMU_CTL_HDS         (1UL << 17)
#define PMU_CS_HDRF         (1UL << 16)
#define PMU_CS_HDSRF        (1UL << 17)

/* FMC（gd32f4xx_fmc.h:150-161） */
#define FMC_WC_WSCNT        (0xFUL << 0)

/* GPIO（gd32f4xx_gpio.h:67,290,60） */
#define GPIO_CTL_MODE8_AF   (2UL << 16)  /*!< pin8 配 AF（2bit/脚，gd32f4xx_gpio.h:67） */
#define GPIO_AF0_PIN8       (0UL << 0)   /*!< AFSEL1[3:0] = AF0（pin8 在 AFSEL1 内偏移 0） */
#define RCU_AHB1EN_GPIOAEN  (1UL << 0)

/* ================= 工程参数 ================= */
#ifndef HXTAL_VALUE_HZ
#define HXTAL_VALUE_HZ      25000000UL
#endif

/* PLL 目标：官方 200M 档（system_gd32f4xx.c:946-948）
 * VCO 输入 = 25M/25 = 1MHz；VCO = 1M × 400 = 400MHz；/P2 = 200MHz */
#define PLL_PSC             25U
#define PLL_N               400U
#define PLL_P               2U
#define PLL_Q               9U

/* FMC 等待周期：保守超配（对照表待 UM 核验；欠配跑飞，超配只慢） */
#ifndef FMC_WS_VALUE
#define FMC_WS_VALUE        6U
#endif

#define HXTAL_STARTUP_TIMEOUT   0x0FFFFU
#define PMU_STARTUP_TIMEOUT     0x0FFFFU
#define PLL_STARTUP_TIMEOUT     0x0FFFFU

/* ================= 状态与对账 ================= */
volatile uint32_t g_clock_status;        /*!< 0=PLL 档；1=回退 IRC16M */
volatile uint32_t g_clock_tree[4];       /*!< CK_SYS / CK_AHB / CK_APB1 / CK_APB2 */

static void soft_delay(volatile uint32_t n)
{
    while (n--) { __asm volatile ("nop"); }
}

/* ① 起振 HXTAL；失败回退 IRC16M（官方 demo 是 while(1)，我们不抄） */
static int hxtal_enable(void)
{
    uint32_t timeout = HXTAL_STARTUP_TIMEOUT;
    RCU_CTL |= RCU_CTL_HXTALEN;
    while ((0 == (RCU_CTL & RCU_CTL_HXTALSTB)) && (0 != timeout)) {
        timeout--;
    }
    return (RCU_CTL & RCU_CTL_HXTALSTB) ? 0 : -1;
}

/* ② 电压档三件套：PMUEN → LDOVS → HDEN 等 HDRF → HDS 等 HDSRF */
static int pmu_highdrive_enter(void)
{
    uint32_t timeout = PMU_STARTUP_TIMEOUT;

    RCU_APB1EN |= RCU_APB1EN_PMUEN;      /* PMU 挂 APB1，先给时钟 */
    soft_delay(1000);                    /* 官方 _soft_delay_：防 Vcore 波动 */

    PMU_CTL |= PMU_CTL_LDOVS;

    PMU_CTL |= PMU_CTL_HDEN;
    while ((0 == (PMU_CS & PMU_CS_HDRF)) && (0 != timeout)) { timeout--; }
    if (0 == (PMU_CS & PMU_CS_HDRF)) { return -1; }

    timeout = PMU_STARTUP_TIMEOUT;
    PMU_CTL |= PMU_CTL_HDS;
    while ((0 == (PMU_CS & PMU_CS_HDSRF)) && (0 != timeout)) { timeout--; }
    if (0 == (PMU_CS & PMU_CS_HDSRF)) { return -1; }

    return 0;
}

/* ③ 官方同款 PLL 参数 */
static int pll_start(void)
{
    uint32_t timeout = PLL_STARTUP_TIMEOUT;

    RCU_PLL = (PLL_PSC | (PLL_N << 6) | (((PLL_P >> 1) - 1U) << 16) |
               RCU_PLLSRC_HXTAL | (PLL_Q << 24));

    RCU_CTL |= RCU_CTL_PLLEN;
    while ((0 == (RCU_CTL & RCU_CTL_PLLSTB)) && (0 != timeout)) { timeout--; }
    return (RCU_CTL & RCU_CTL_PLLSTB) ? 0 : -1;
}

/* ④ 总线分频 + 切钟 + 回读 SCSS */
static int clock_switch_to_pllp(void)
{
    uint32_t timeout = PLL_STARTUP_TIMEOUT;
    uint32_t reg;

    RCU_CFG0 |= RCU_AHB_CKSYS_DIV1;      /* AHB = CK_SYS */
    RCU_CFG0 |= RCU_APB2_CKAHB_DIV2;     /* APB2 = AHB/2 */
    RCU_CFG0 |= RCU_APB1_CKAHB_DIV4;     /* APB1 = AHB/4 */

    reg = RCU_CFG0;
    reg &= ~RCU_CFG0_SCS;
    reg |= RCU_CKSYSSRC_PLLP;
    RCU_CFG0 = reg;

    while ((0 == (RCU_CFG0 & RCU_SCSS_PLLP)) && (0 != timeout)) { timeout--; }
    return (RCU_CFG0 & RCU_SCSS_PLLP) ? 0 : -1;
}

/* ⑤ 官方留白由工程补上：Flash 等待周期 */
static void fmc_ws_set(uint32_t ws)
{
    FMC_WS = (FMC_WS & ~FMC_WC_WSCNT) | (ws & FMC_WC_WSCNT);
}

/* ⑥ 从寄存器反推真实时钟树（GDB 里看 g_clock_tree[]）。
 *    源由 SCSS 如实解码、PLL 频率由 RCU_PLL 参数重算——故障路径也报真账，
 *    绝不"调用方以为是哪档就填哪档"。 */
static uint32_t pll_output_hz(void)
{
    uint32_t pll = RCU_PLL;
    uint32_t psc = pll & 0x3FUL;
    uint32_t n = (pll >> 6) & 0x1FFUL;
    uint32_t p = (((pll >> 16) & 0x3UL) + 1UL) * 2UL;
    uint32_t src = (pll & RCU_PLLSRC_HXTAL) ? HXTAL_VALUE_HZ : 16000000UL;

    if ((0 == psc) || (0 == n)) {
        return 0UL;                      /* PLL 未配置 */
    }
    return (src / psc) * n / p;
}

static void clock_tree_readback(void)
{
    uint32_t cfg = RCU_CFG0;
    uint32_t ahb_div = 1U, apb1_div = 1U, apb2_div = 1U;
    uint32_t ck_sys;

    switch (cfg & RCU_CFG0_SCSS) {       /* 实际源：SCSS 回执，不是"我们以为" */
    case RCU_SCSS_PLLP:  ck_sys = pll_output_hz(); break;
    case RCU_SCSS_HXTAL: ck_sys = HXTAL_VALUE_HZ; break;
    default:             ck_sys = 16000000UL; break;   /* IRC16M */
    }

    switch ((cfg >> 4) & 0xFUL) {        /* AHBPSC（gd32f4xx_rcu.h:824-831） */
    case 8:  ahb_div = 2U; break;
    case 9:  ahb_div = 4U; break;
    case 10: ahb_div = 8U; break;
    case 11: ahb_div = 16U; break;
    case 12: ahb_div = 64U; break;
    case 13: ahb_div = 128U; break;
    case 14: ahb_div = 256U; break;
    case 15: ahb_div = 512U; break;
    default: break;
    }
    switch ((cfg >> 10) & 0x7UL) {       /* APB1PSC（:836-840） */
    case 4: apb1_div = 2U; break;
    case 5: apb1_div = 4U; break;
    case 6: apb1_div = 8U; break;
    case 7: apb1_div = 16U; break;
    default: break;
    }
    switch ((cfg >> 13) & 0x7UL) {       /* APB2PSC（:844-848） */
    case 4: apb2_div = 2U; break;
    case 5: apb2_div = 4U; break;
    case 6: apb2_div = 8U; break;
    case 7: apb2_div = 16U; break;
    default: break;
    }

    g_clock_tree[0] = ck_sys;            /* CK_SYS */
    g_clock_tree[1] = ck_sys / ahb_div;  /* CK_AHB */
    g_clock_tree[2] = ck_sys / ahb_div / apb1_div;
    g_clock_tree[3] = ck_sys / ahb_div / apb2_div;
}

/* ⑦ CK_OUT0 对账：PA8（AF0）输出 PLLP/4 */
static void ckout0_init(void)
{
    uint32_t reg;

    RCU_AHB1EN |= RCU_AHB1EN_GPIOAEN;
    GPIOA_CTL = (GPIOA_CTL & ~(3UL << 16)) | GPIO_CTL_MODE8_AF;
    GPIOA_AFSEL1 = (GPIOA_AFSEL1 & ~(0xFUL << 0)) | GPIO_AF0_PIN8;

    reg = RCU_CFG0;
    reg &= ~(RCU_CFG0_CKOUT0SEL | RCU_CFG0_CKOUT0DIV);
    reg |= RCU_CKOUT0SRC_PLLP | RCU_CKOUT0_DIV4;
    RCU_CFG0 = reg;
}

static void clock_init(void)
{
    if (hxtal_enable() != 0) {           /* 晶振不来：回退，不死等 */
        g_clock_status = 1U;
        clock_tree_readback();
        return;
    }
    if (pmu_highdrive_enter() != 0) {    /* 电压档没握手成功 */
        g_clock_status = 2U;
        clock_tree_readback();
        return;
    }

    fmc_ws_set(FMC_WS_VALUE);            /* 官方 system 文件不设，我们来设 */

    if (pll_start() != 0) {
        g_clock_status = 3U;
        clock_tree_readback();
        return;
    }
    if (clock_switch_to_pllp() != 0) {
        g_clock_status = 4U;
        clock_tree_readback();
        return;
    }

    g_clock_status = 0U;
    clock_tree_readback();
    ckout0_init();                       /* 理论 50MHz 上 PA8，待上板实测 */
}

int main(void)
{
    clock_init();
    while (1) {
        /* GDB 观察点：g_clock_status / g_clock_tree[] */
    }
    return 0;
}
