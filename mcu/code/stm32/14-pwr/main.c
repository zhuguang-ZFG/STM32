/**
 * main.c —— 14-pwr：三档睡眠、唤醒源、以及醒来之后那笔时钟账
 *
 * 这一工程回答三个问题，全部可以在宿主机上算出来、不需要开发板：
 *
 *   1. Sleep / Stop / Standby 三档，在寄存器层面到底是哪几位不一样？
 *      —— 一个内核位（SCB_SCR.SLEEPDEEP，bit2）加一个外设位（PWR_CR.PDDS，bit1），
 *         两位组合出三档，别的都不用改。
 *   2. 醒来那句"程序以为自己还在 168MHz"会错成什么样？
 *      —— SysTick 装载值没跟着改：1ms 变 10.5ms；USART 分频值没跟着改：
 *         115200 变 10973。两者都不是崩溃，是"看起来在跑、数全错"。
 *   3. 备份域那句"睡前遗言"要写哪几行才作数？
 *      —— PWREN 时钟、DBP 解锁、备份调压器 BRE（就绪回执 BRR），少一位就是白写。
 *
 * 事实基准：ST 官方 CMSIS 头文件（本站 .trellis/ref/cmsis/）。
 *   PWR = APB1 + 0x7000 = 0x40007000；BKPSRAM = 0x40024000（4 KB）；
 *   DBGMCU = 0xE0042000；SCB->SCR = 0xE000ED10。位号见 probe.sh 第 2 步的逐位对账。
 */

#include <stdint.h>

/* ============================ 寄存器定义 ============================
 * 需要被宿主探针改指假寄存器的，一律给 #ifndef 口子（与 01-rcc-clock 同一手法）：
 * 探针把下面这些宏换成一组 static 变量后 #include 本文件，跑的就是固件本体，
 * 不是另抄一遍算术。 */

#define PWR_BASE            (0x40007000UL)
#ifndef PWR_CR
#define PWR_CR              (*(volatile uint32_t *)(PWR_BASE + 0x00UL))
#endif
#ifndef PWR_CSR
#define PWR_CSR             (*(volatile uint32_t *)(PWR_BASE + 0x04UL))
#endif

#define RCC_BASE            (0x40023800UL)
#ifndef RCC_APB1ENR
#define RCC_APB1ENR         (*(volatile uint32_t *)(RCC_BASE + 0x40UL))
#endif
#ifndef RCC_AHB1ENR
#define RCC_AHB1ENR         (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#endif
#ifndef RCC_BDCR
#define RCC_BDCR            (*(volatile uint32_t *)(RCC_BASE + 0x70UL))
#endif
#ifndef RCC_CSR
#define RCC_CSR             (*(volatile uint32_t *)(RCC_BASE + 0x74UL))
#endif

/* SCB->SCR 与 DBGMCU->CR 是内核外设，不在 STM32 外设地址空间里 */
#ifndef SCB_SCR
#define SCB_SCR             (*(volatile uint32_t *)(0xE000ED10UL))
#endif
#define DBGMCU_BASE         (0xE0042000UL)
#ifndef DBGMCU_CR
#define DBGMCU_CR           (*(volatile uint32_t *)(DBGMCU_BASE + 0x04UL))
#endif

#ifndef SysTick_LOAD
#define SysTick_LOAD        (*(volatile uint32_t *)(0xE000E014UL))
#endif

/* 备份 SRAM：CMSIS 里 BKPSRAM_BASE = 0x40024000，容量 4 KB */
#ifndef BKPSRAM_BASE
#define BKPSRAM_BASE        (0x40024000UL)
#endif
#define BKPSRAM_BYTES       (4096UL)

/* dsb/wfi 是 ARM 指令，宿主机编不过：探针那一遍只留编译器栅栏。
 * 真实形状由 probe.sh 第 3 步的交叉反汇编给出。 */
#if defined(__arm__)
#define MCU_BARRIER()       __asm volatile("dsb sy" ::: "memory")
#define MCU_WFI()           __asm volatile("wfi")
#else
#define MCU_BARRIER()       __asm volatile("" ::: "memory")
#define MCU_WFI()           ((void)0)
#endif

/* ---- 位定义（全部对照 CMSIS，probe.sh 第 2 步逐位对账） ---- */
#define PWR_CR_LPDS         (1UL << 0)      /* Stop 下调压器进低功耗档      */
#define PWR_CR_PDDS         (1UL << 1)      /* 0=Stop，1=Standby            */
#define PWR_CR_CWUF         (1UL << 2)      /* 清唤醒标志（写 1 清）        */
#define PWR_CR_CSBF         (1UL << 3)      /* 清 Standby 标志              */
#define PWR_CR_DBP          (1UL << 8)      /* 解除备份域写保护             */
#define PWR_CR_FPDS         (1UL << 9)      /* Stop 下 Flash 掉电           */
#define PWR_CR_VOS          (1UL << 14)     /* 电压调节输出档（S2 的主角）  */

#define PWR_CSR_WUF         (1UL << 0)      /* 唤醒标志                     */
#define PWR_CSR_SBF         (1UL << 1)      /* Standby 标志（复位式的醒）   */
#define PWR_CSR_BRR         (1UL << 3)      /* 备份调压器就绪               */
#define PWR_CSR_EWUP        (1UL << 8)      /* 使能 PA0 = WKUP 引脚         */
#define PWR_CSR_BRE         (1UL << 9)      /* 备份调压器使能               */

#define SCB_SCR_SLEEPONEXIT (1UL << 1)
#define SCB_SCR_SLEEPDEEP   (1UL << 2)      /* 0=Sleep，1=深睡（Stop/Standby）*/
#define SCB_SCR_SEVONPEND   (1UL << 4)

#define RCC_APB1ENR_PWREN   (1UL << 28)
#define RCC_AHB1ENR_BKPSRAMEN (1UL << 18)
#define RCC_BDCR_RTCEN      (1UL << 15)

#define RCC_CSR_RMVF        (1UL << 24)     /* 清复位标志（写 1 清）        */
#define RCC_CSR_BORRSTF     (1UL << 25)
#define RCC_CSR_PINRSTF     (1UL << 26)
#define RCC_CSR_PORRSTF     (1UL << 27)
#define RCC_CSR_SFTRSTF     (1UL << 28)
#define RCC_CSR_IWDGRSTF    (1UL << 29)
#define RCC_CSR_WWDGRSTF    (1UL << 30)
#define RCC_CSR_LPWRRSTF    (1UL << 31)

#define DBGMCU_CR_DBG_SLEEP   (1UL << 0)
#define DBGMCU_CR_DBG_STOP    (1UL << 1)
#define DBGMCU_CR_DBG_STANDBY (1UL << 2)

/* 唤醒通道在内核里的编号（F4：RTC 闹钟走 EXTI 17，RTC 唤醒计数器走 18，
 * PA0 的 WKUP 引脚走 EXTI 0）——"谁能叫醒我"是设计出来的，不是默认有的。 */
#define WKUP_LINE_PA0         0U
#define WKUP_LINE_PVD         16U
#define WKUP_LINE_RTC_ALARM   17U
#define WKUP_LINE_RTC_WAKEUP  18U

/* 时钟：Stop 期间 1.2V 域全停、PLL 也停；醒来硬件只把 HSI 顶上 */
#define HSI_HZ                (16000000UL)
#define RUN_HCLK_HZ           (168000000UL)
#define RUN_PCLK2_HZ          (84000000UL)
#define WAKE_PCLK2_HZ         (8000000UL)   /* HSI 16MHz 过 PPRE2=/2 */
#define LSI_HZ                (32000UL)

/* ============================ 可测的纯函数 ============================ */

typedef enum { MODE_SLEEP = 0, MODE_STOP = 1, MODE_STANDBY = 2 } pwr_mode_t;

/**
 * 三档模式的寄存器写法，由 SLEEPDEEP + PDDS 这两个位决定。
 * 输入"当前值"，输出"应当写回的新值"——其余位原样保留，不碰。
 */
void pwr_mode_words(pwr_mode_t mode, uint32_t cr_now, uint32_t scr_now,
                    uint32_t *cr_out, uint32_t *scr_out)
{
    uint32_t cr = cr_now;
    uint32_t scr = scr_now;

    if (mode == MODE_SLEEP) {
        scr &= ~SCB_SCR_SLEEPDEEP;           /* SLEEPDEEP=0 → Sleep */
    } else {
        scr |= SCB_SCR_SLEEPDEEP;            /* SLEEPDEEP=1 → 深睡 */
        if (mode == MODE_STOP) {
            cr &= ~PWR_CR_PDDS;              /* PDDS=0 → Stop（调压器还活着） */
            cr |= PWR_CR_LPDS;               /* 调压器降档，更省 */
        } else {
            cr |= PWR_CR_PDDS;               /* PDDS=1 → Standby（1.2V 域断电） */
            cr &= ~PWR_CR_LPDS;              /* 此时低功耗档没有意义 */
        }
    }
    *cr_out = cr;
    *scr_out = scr;
}

/** 1ms 的 SysTick 装载值：hclk 每毫秒来多少个拍，减一是重载值 */
uint32_t systick_load_1ms(uint32_t hclk_hz)
{
    return hclk_hz / 1000UL - 1UL;
}

/**
 * 装载值不动、时钟变了，真实周期是多少微秒（×10 取整，避开小数）。
 * 这一句就是"醒来变痴呆"的全部数学：程序以为 1ms，硬件量出来是别的。
 */
uint32_t systick_period_us10(uint32_t load, uint32_t real_hclk_hz)
{
    return (uint32_t)(((uint64_t)(load + 1UL) * 10000000ULL) / real_hclk_hz);
}

/** USART 在 OVER8=0 时的 BRR：pclk/baud 四舍五入（小数落在低 4 位） */
uint32_t usart_brr(uint32_t pclk_hz, uint32_t baud)
{
    return (pclk_hz + baud / 2UL) / baud;
}

/** 反过来：给定 BRR 和当前时钟，真正打出去的波特率 */
uint32_t usart_baud_from_brr(uint32_t pclk_hz, uint32_t brr)
{
    return pclk_hz / brr;
}

/** IWDG 预分频寄存器值 → 实际分频。8 个编码只给 7 个分频：11x 全是 /256 */
uint32_t iwdg_pr_div(uint32_t pr)
{
    const uint32_t p = pr & 0x7UL;
    return p >= 6UL ? 256UL : (4UL << p);
}

/** IWDG 超时（ms）：靠 LSI 独立时钟，Stop 期间照样数 */
uint32_t iwdg_timeout_ms(uint32_t pr, uint32_t reload, uint32_t lsi_hz)
{
    return (uint32_t)(((uint64_t)iwdg_pr_div(pr) * reload * 1000ULL) / lsi_hz);
}

/** 备份 SRAM 能装多少个 32 位字（"遗言"容量） */
uint32_t bkp_capacity_words(void)
{
    return BKPSRAM_BYTES / 4UL;
}

/**
 * 把"睡前遗言"写进备份 SRAM。
 * 0 写进去；-1 = 备份域没解锁（DBP=0）；-2 = 备份调压器没开；-3 = 超出容量。
 * 拒绝返回成功是刻意的：没解锁时写进去的是空气，报"成功"就是骗下一次开机。
 */
int bkp_store(const uint32_t *msg, uint32_t n)
{
    if ((PWR_CR & PWR_CR_DBP) == 0UL) return -1;
    if ((PWR_CSR & PWR_CSR_BRE) == 0UL) return -2;
    if (n > bkp_capacity_words()) return -3;
    uint32_t *bkp = (uint32_t *)(uintptr_t)BKPSRAM_BASE;
    for (uint32_t i = 0; i < n; i++) bkp[i] = msg[i];
    return 0;
}

/** 解锁备份域：PWREN 时钟 → DBP → 备份调压器 → 取 BRR 就绪回执 */
uint32_t backup_domain_unlock(void)
{
    RCC_APB1ENR |= RCC_APB1ENR_PWREN;
    PWR_CR |= PWR_CR_DBP;
    PWR_CSR |= PWR_CSR_BRE;
    RCC_AHB1ENR |= RCC_AHB1ENR_BKPSRAMEN;
    RCC_BDCR |= RCC_BDCR_RTCEN;
    return (PWR_CSR & PWR_CSR_BRR) != 0UL ? 0UL : 1UL;   /* 0 = 已就绪 */
}

/** 睡前把调试接口那几个吃电的位清掉（DBGMCU_CR bit0/1/2） */
uint32_t dbg_cr_for_lowpower(uint32_t cr_now)
{
    return cr_now & ~(DBGMCU_CR_DBG_SLEEP | DBGMCU_CR_DBG_STOP | DBGMCU_CR_DBG_STANDBY);
}

/**
 * 某个唤醒源现在叫得醒我吗？
 * csr = PWR_CSR 配置值，exti_imr = EXTI 屏蔽寄存器（位号即线路号）。
 * 返回 0 叫得醒；-1 = 没配，这时候进 WFI 就是睡死。
 */
int wake_source_armed(uint32_t csr, uint32_t exti_imr, uint32_t line)
{
    if (line == WKUP_LINE_PA0) return (csr & PWR_CSR_EWUP) ? 0 : -1;
    return (exti_imr & (1UL << line)) ? 0 : -1;
}

/**
 * 复位原因解码：RCC_CSR 那七个标志位 + PWR_CSR.SBF。
 * 返回位掩码：bit0=Standby 醒，bit1..7 依次 BOR/PIN/POR/SFT/IWDG/WWDG/LPWR。
 */
uint32_t reset_cause_decode(uint32_t rcc_csr, uint32_t pwr_csr)
{
    uint32_t out = 0;
    if (pwr_csr & PWR_CSR_SBF)     out |= 1UL << 0;
    if (rcc_csr & RCC_CSR_BORRSTF) out |= 1UL << 1;
    if (rcc_csr & RCC_CSR_PINRSTF) out |= 1UL << 2;
    if (rcc_csr & RCC_CSR_PORRSTF) out |= 1UL << 3;
    if (rcc_csr & RCC_CSR_SFTRSTF) out |= 1UL << 4;
    if (rcc_csr & RCC_CSR_IWDGRSTF) out |= 1UL << 5;
    if (rcc_csr & RCC_CSR_WWDGRSTF) out |= 1UL << 6;
    if (rcc_csr & RCC_CSR_LPWRRSTF) out |= 1UL << 7;
    return out;
}

/* ============================ 固件本体 ============================ */

static volatile uint32_t g_wake_reason;      /* 醒来第一件事：查是谁叫的 */
static volatile uint32_t g_run_hclk = RUN_HCLK_HZ;

/* Stop 醒来后必须自己补的课：硬件只把 HSI 顶上，PLL 不会自动重启 */
static void clock_restore_after_wake(void)
{
    g_run_hclk = HSI_HZ;
    SysTick_LOAD = systick_load_1ms(HSI_HZ);   /* 装载值必须跟着真实时钟走 */
    /* 真正的 SystemClock_Config() 见 01-rcc-clock：VOS→LATENCY→HSE→PLL→SW */
}

/** 三个进睡眠的入口：定档的两位由 pwr_mode_words() 算，写完就一条 WFI */
void enter_sleep(void)
{
    uint32_t cr = PWR_CR, scr = SCB_SCR;
    pwr_mode_words(MODE_SLEEP, cr, scr, &cr, &scr);
    PWR_CR = cr;
    SCB_SCR = scr;
    MCU_BARRIER();
    MCU_WFI();
    /* Sleep：任何使能的中断都能叫醒，醒来时钟没变，不用重配 */
}

void enter_stop(void)
{
    uint32_t cr = PWR_CR, scr = SCB_SCR;
    pwr_mode_words(MODE_STOP, cr, scr, &cr, &scr);
    PWR_CR = cr;
    SCB_SCR = scr;
    MCU_BARRIER();
    MCU_WFI();
    /* Stop：醒来回到这里，但 HSI 已经接管，第一件事是补时钟 */
    clock_restore_after_wake();
}

void enter_standby(void)
{
    uint32_t cr = PWR_CR, scr = SCB_SCR;
    pwr_mode_words(MODE_STANDBY, cr, scr, &cr, &scr);
    PWR_CR = cr;
    SCB_SCR = scr;
    MCU_BARRIER();
    MCU_WFI();
    /* 走到这里只有两种可能：没睡成（PDDS 被硬件忽略），或者已经醒来=复位。
     * 编译器不知道 wfi 之后不会回来，这一段照样占着 .text——量在 probe.sh 第 3 步。 */
    g_wake_reason = reset_cause_decode(RCC_CSR, PWR_CSR);
}

void firmware_main(void)
{
    /* 1. 睡前准备：抠掉调试接口、看清上一次是怎么醒的 */
    DBGMCU_CR = dbg_cr_for_lowpower(DBGMCU_CR);
    g_wake_reason = reset_cause_decode(RCC_CSR, PWR_CSR);
    RCC_CSR |= RCC_CSR_RMVF;                    /* 读完就清，下次才好分辨 */

    /* 2. 进 Stop 再醒来：两位定档、一条 WFI，然后补课 */
    enter_stop();

    /* 3. 醒来：清标志——注意清的是 CR 那两个"写 1 清"的脉冲位 */
    if (PWR_CSR & PWR_CSR_WUF) PWR_CR |= PWR_CR_CWUF;
    if (PWR_CSR & PWR_CSR_SBF) PWR_CR |= PWR_CR_CSBF;
}

#ifndef MCU_PROBE_NO_MAIN
int main(void)
{
    firmware_main();
    return 0;
}
#endif
