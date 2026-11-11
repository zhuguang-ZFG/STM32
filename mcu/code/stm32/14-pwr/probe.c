/**
 * probe.c —— 14-pwr 无板取证
 *
 * 手法与 01-rcc-clock 相同：把 main.c 里那组寄存器宏改指到一组 static 变量上，
 * 然后 #include "main.c"。于是下面每一条断言跑的都是固件本体，
 * 不是另抄一遍算术；宿主机就能把三档睡眠的账全部摊开。
 *
 * 第 2 节打印的位号表由 probe.sh 与 CMSIS 官方头文件逐位 diff。
 * 注意：假寄存器不会自己变——凡"硬件会清掉/会就绪"的部分，这里只断言
 * 固件发出了那个动作，不冒充硬件的回执。
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>

/* ---- 假寄存器：真实地址在这一遍里全部作废 ---- */
static volatile uint32_t f_pwr_cr, f_pwr_csr;
static volatile uint32_t f_rcc_apb1enr, f_rcc_ahb1enr, f_rcc_bdcr, f_rcc_csr;
static volatile uint32_t f_scr, f_dbgmcu_cr, f_systick_load;
static uint32_t f_bkpsram[1024];

#define PWR_CR              f_pwr_cr
#define PWR_CSR             f_pwr_csr
#define RCC_APB1ENR         f_rcc_apb1enr
#define RCC_AHB1ENR         f_rcc_ahb1enr
#define RCC_BDCR            f_rcc_bdcr
#define RCC_CSR             f_rcc_csr
#define SCB_SCR             f_scr
#define DBGMCU_CR           f_dbgmcu_cr
#define SysTick_LOAD        f_systick_load
#define BKPSRAM_BASE        ((uintptr_t)f_bkpsram)

#define MCU_PROBE_NO_MAIN
#include "main.c"
#undef main

static int fails;

static void check(const char *what, uint32_t got, uint32_t want)
{
    if (got == want) {
        printf("  ✓ %-32s = 0x%08lX\n", what, (unsigned long)got);
    } else {
        printf("  ✗ %-32s 得 0x%08lX，期望 0x%08lX\n",
               what, (unsigned long)got, (unsigned long)want);
        fails++;
    }
}

static uint32_t bitv(uint32_t word, uint32_t mask)
{
    return (word & mask) ? 1UL : 0UL;
}

static unsigned bitpos(uint32_t mask)
{
    unsigned b = 0;
    while (mask > 1UL) { mask >>= 1; b++; }
    return b;
}

/* ---------------------------------------------------------------- */
static void probe_bit_positions(void)
{
    puts("=== 2. 位号表（probe.sh 拿它和 CMSIS 官方头文件逐位 diff）===");
#define PUT(name) printf("%s %u\n", #name, bitpos(name))
    PUT(PWR_CR_LPDS); PUT(PWR_CR_PDDS); PUT(PWR_CR_CWUF); PUT(PWR_CR_CSBF);
    PUT(PWR_CR_DBP); PUT(PWR_CR_FPDS); PUT(PWR_CR_VOS);
    PUT(PWR_CSR_WUF); PUT(PWR_CSR_SBF); PUT(PWR_CSR_BRR);
    PUT(PWR_CSR_EWUP); PUT(PWR_CSR_BRE);
    PUT(SCB_SCR_SLEEPONEXIT); PUT(SCB_SCR_SLEEPDEEP); PUT(SCB_SCR_SEVONPEND);
    PUT(RCC_APB1ENR_PWREN); PUT(RCC_AHB1ENR_BKPSRAMEN); PUT(RCC_BDCR_RTCEN);
    PUT(RCC_CSR_RMVF); PUT(RCC_CSR_BORRSTF); PUT(RCC_CSR_PINRSTF);
    PUT(RCC_CSR_PORRSTF); PUT(RCC_CSR_SFTRSTF); PUT(RCC_CSR_IWDGRSTF);
    PUT(RCC_CSR_WWDGRSTF); PUT(RCC_CSR_LPWRRSTF);
    PUT(DBGMCU_CR_DBG_SLEEP); PUT(DBGMCU_CR_DBG_STOP); PUT(DBGMCU_CR_DBG_STANDBY);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_three_modes(void)
{
    puts("=== 1. 三档睡眠：定档的只有两个位 ===");
    /* 起点故意带上 VOS/FPDS/SEVONPEND 这些杂位：定档不该把它们冲掉 */
    const uint32_t cr0 = PWR_CR_VOS | PWR_CR_FPDS;
    const uint32_t scr0 = SCB_SCR_SEVONPEND;

    uint32_t cr, scr;
    pwr_mode_words(MODE_SLEEP, cr0, scr0, &cr, &scr);
    printf("  Sleep    ：CR=0x%08lX SCR=0x%08lX  (SLEEPDEEP=%u PDDS=%u)\n",
           (unsigned long)cr, (unsigned long)scr,
           (unsigned)bitv(scr, SCB_SCR_SLEEPDEEP), (unsigned)bitv(cr, PWR_CR_PDDS));
    check("Sleep 的 SCR bit2", bitv(scr, SCB_SCR_SLEEPDEEP), 0UL);
    check("Sleep 完全不动 CR", cr, cr0);

    pwr_mode_words(MODE_STOP, cr0, scr0, &cr, &scr);
    printf("  Stop     ：CR=0x%08lX SCR=0x%08lX  (SLEEPDEEP=%u PDDS=%u)\n",
           (unsigned long)cr, (unsigned long)scr,
           (unsigned)bitv(scr, SCB_SCR_SLEEPDEEP), (unsigned)bitv(cr, PWR_CR_PDDS));
    check("Stop 的 SCR bit2", bitv(scr, SCB_SCR_SLEEPDEEP), 1UL);
    check("Stop 的 CR bit1（PDDS）", bitv(cr, PWR_CR_PDDS), 0UL);
    check("Stop 的 CR bit0（LPDS）", bitv(cr, PWR_CR_LPDS), 1UL);
    check("Stop 保留 VOS/FPDS", cr & (PWR_CR_VOS | PWR_CR_FPDS), cr0);
    check("Stop 保留 SEVONPEND", scr & SCB_SCR_SEVONPEND, scr0);

    pwr_mode_words(MODE_STANDBY, cr0, scr0, &cr, &scr);
    printf("  Standby  ：CR=0x%08lX SCR=0x%08lX  (SLEEPDEEP=%u PDDS=%u)\n",
           (unsigned long)cr, (unsigned long)scr,
           (unsigned)bitv(scr, SCB_SCR_SLEEPDEEP), (unsigned)bitv(cr, PWR_CR_PDDS));
    check("Standby 的 SCR bit2", bitv(scr, SCB_SCR_SLEEPDEEP), 1UL);
    check("Standby 的 CR bit1（PDDS）", bitv(cr, PWR_CR_PDDS), 1UL);
    check("Standby 的 CR bit0（LPDS）", bitv(cr, PWR_CR_LPDS), 0UL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_clock_bill(void)
{
    puts("=== 3. 醒来那笔时钟账：不崩，只是数全错 ===");
    const uint32_t load_run = systick_load_1ms(RUN_HCLK_HZ);
    const uint32_t load_wake = systick_load_1ms(HSI_HZ);
    printf("  运行 168MHz：1ms 的装载值 = %lu\n", (unsigned long)load_run);
    printf("  醒来 16MHz ：1ms 的装载值 = %lu\n", (unsigned long)load_wake);
    check("装载值不改，真实周期（µs×10）",
          systick_period_us10(load_run, HSI_HZ), 105000UL);
    check("改对之后的周期（µs×10）",
          systick_period_us10(load_wake, HSI_HZ), 10000UL);
    printf("  以为 1ms，量出来 %.1fms —— 就是 %lu / %lu 这个比例\n",
           (double)systick_period_us10(load_run, HSI_HZ) / 10000.0,
           (unsigned long)RUN_HCLK_HZ, (unsigned long)HSI_HZ);

    const uint32_t brr = usart_brr(RUN_PCLK2_HZ, 115200UL);
    printf("  USART：BRR 按 PCLK2=%lu 配 → %lu（0x%lX），实际 %.1f baud，误差 %+.3f%%\n",
           (unsigned long)RUN_PCLK2_HZ, (unsigned long)brr, (unsigned long)brr,
           (double)usart_baud_from_brr(RUN_PCLK2_HZ, brr),
           100.0 * ((double)usart_baud_from_brr(RUN_PCLK2_HZ, brr) / 115200.0 - 1.0));
    printf("  醒来 PCLK2 掉到 %lu，BRR 还是 %lu → 真波特率 %lu\n",
           (unsigned long)WAKE_PCLK2_HZ, (unsigned long)brr,
           (unsigned long)usart_baud_from_brr(WAKE_PCLK2_HZ, brr));
    check("醒来后真正打出去的波特率", usart_baud_from_brr(WAKE_PCLK2_HZ, brr), 10973UL);
    check("醒来要重算的 BRR", usart_brr(WAKE_PCLK2_HZ, 115200UL), 69UL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_iwdg(void)
{
    puts("=== 4. 看门狗在 Stop 里还在数：LSI 不归 Stop 管 ===");
    printf("  PR 编码 → 分频：");
    for (uint32_t pr = 0; pr <= 7UL; pr++) printf("/%lu ", (unsigned long)iwdg_pr_div(pr));
    puts("\n  （八个编码只有七个分频：11x 两种写法都是 /256）");
    check("PR=6 与 PR=7 同一个分频", iwdg_pr_div(6UL), iwdg_pr_div(7UL));

    for (uint32_t pr = 0; pr <= 7UL; pr++) {
        const uint32_t t = iwdg_timeout_ms(pr, 4095UL, LSI_HZ);
        printf("  PR=%lu（/%lu）reload=4095 → 超时 %lu ms；LSI ±5%% 时 %lu ~ %lu ms\n",
               (unsigned long)pr, (unsigned long)iwdg_pr_div(pr), (unsigned long)t,
               (unsigned long)(t * 95UL / 100UL), (unsigned long)(t * 105UL / 100UL));
    }
    check("PR=0（/4）超时 ms", iwdg_timeout_ms(0UL, 4095UL, LSI_HZ), 511UL);
    check("PR=7（/256）超时 ms", iwdg_timeout_ms(7UL, 4095UL, LSI_HZ), 32760UL);
    /* 想当然的那一版（div = 4 << pr，把第八个码当 /512）会把最长超时算成两倍 */
    check("PR=7 按「/512」想算出来的 ms", (512UL * 4095UL * 1000UL) / LSI_HZ, 65520UL);
    check("PR=0 时睡 1 秒会被咬吗", iwdg_timeout_ms(0UL, 4095UL, LSI_HZ) < 1000UL, 1UL);
    check("PR=7 时睡 30 秒安全吗", iwdg_timeout_ms(7UL, 4095UL, LSI_HZ) > 30000UL, 1UL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_backup(void)
{
    puts("=== 5. 备份域：解锁之前写进去的是空气 ===");
    check("BKPSRAM 容量（32 位字）", bkp_capacity_words(), 1024UL);

    const uint32_t msg[3] = { 0xA5A5A5A5UL, 0x0012EDUL, 0xDEADBEEFUL };
    memset(f_bkpsram, 0, sizeof f_bkpsram);

    PWR_CR = 0UL; PWR_CSR = 0UL;
    check("DBP=0 就写（返回 -1）", (uint32_t)bkp_store(msg, 3UL), 0xFFFFFFFFUL);
    check("此时备份 SRAM 未被写过", f_bkpsram[0], 0UL);

    PWR_CR = PWR_CR_DBP;
    check("DBP 有、调压器没开（-2）", (uint32_t)bkp_store(msg, 3UL), 0xFFFFFFFEUL);
    check("此时备份 SRAM 仍未被写过", f_bkpsram[0], 0UL);

    PWR_CSR = 0UL; PWR_CR = 0UL;
    const uint32_t notready = backup_domain_unlock();
    printf("  backup_domain_unlock() 第一遍回执 = %lu（1 = 没读到 BRR 就绪位）\n",
           (unsigned long)notready);
    check("APB1 的 PWREN（bit28）", bitv(RCC_APB1ENR, RCC_APB1ENR_PWREN), 1UL);
    check("AHB1 的 BKPSRAMEN（bit18）", bitv(RCC_AHB1ENR, RCC_AHB1ENR_BKPSRAMEN), 1UL);
    check("BDCR 的 RTCEN（bit15）", bitv(RCC_BDCR, RCC_BDCR_RTCEN), 1UL);
    check("CR 的 DBP（bit8）", bitv(PWR_CR, PWR_CR_DBP), 1UL);
    check("CSR 的 BRE（bit9）", bitv(PWR_CSR, PWR_CSR_BRE), 1UL);

    /* BRR 是硬件给的"备份调压器起来了"回执；假寄存器不会自己置位，
     * 这里手工置上，等价于板子上等了一会儿之后读到的那个 1。 */
    PWR_CSR |= PWR_CSR_BRR;
    check("置上 BRR 后第二遍回执", backup_domain_unlock(), 0UL);
    check("三关全过才让写（返回 0）", (uint32_t)bkp_store(msg, 3UL), 0UL);
    check("遗言第一个字", f_bkpsram[0], 0xA5A5A5A5UL);
    check("遗言第三个字", f_bkpsram[2], 0xDEADBEEFUL);
    check("超出容量（返回 -3）", (uint32_t)bkp_store(msg, 1025UL), 0xFFFFFFFDUL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_wake_sources(void)
{
    puts("=== 6. 唤醒源：睡前不配，写下去的 WFI 就是睡死 ===");
    const uint32_t bare = 0UL;
    check("PA0/WKUP 没使能 EWUP",
          (uint32_t)wake_source_armed(bare, bare, WKUP_LINE_PA0), 0xFFFFFFFFUL);
    check("RTC 闹钟线（EXTI17）没使能",
          (uint32_t)wake_source_armed(bare, bare, WKUP_LINE_RTC_ALARM), 0xFFFFFFFFUL);
    check("PVD 线（EXTI16）没使能",
          (uint32_t)wake_source_armed(bare, bare, WKUP_LINE_PVD), 0xFFFFFFFFUL);

    const uint32_t csr = PWR_CSR_EWUP;
    const uint32_t imr = (1UL << WKUP_LINE_RTC_ALARM);
    printf("  EXTI 屏蔽寄存器写 1<<17 = 0x%08lX（RTC 闹钟在硬件上就是这一根线）\n",
           (unsigned long)imr);
    check("PA0 配了 EWUP 就叫得醒",
          (uint32_t)wake_source_armed(csr, bare, WKUP_LINE_PA0), 0UL);
    check("RTC 闹钟配了 EXTI17",
          (uint32_t)wake_source_armed(csr, imr, WKUP_LINE_RTC_ALARM), 0UL);
    check("EWUP 管不到 EXTI17 这根线",
          (uint32_t)wake_source_armed(csr, bare, WKUP_LINE_RTC_ALARM), 0xFFFFFFFFUL);
    check("RTC 唤醒线（EXTI18）仍没配",
          (uint32_t)wake_source_armed(csr, imr, WKUP_LINE_RTC_WAKEUP), 0xFFFFFFFFUL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_reset_causes(void)
{
    puts("=== 7. 醒来是哪一种醒：SBF 加七个复位标志 ===");
    const struct { const char *name; uint32_t rcsr; uint32_t pwcr; uint32_t want; } cases[] = {
        { "刚上电（POR+PIN）",   RCC_CSR_PORRSTF | RCC_CSR_PINRSTF, 0UL, (1UL << 2) | (1UL << 3) },
        { "Standby 醒来",        RCC_CSR_PORRSTF, PWR_CSR_SBF, (1UL << 0) | (1UL << 3) },
        { "看门狗咬的",          RCC_CSR_IWDGRSTF, 0UL, 1UL << 5 },
        { "软复位（NVIC）",      RCC_CSR_SFTRSTF, 0UL, 1UL << 4 },
        { "欠压＋BOR",           RCC_CSR_LPWRRSTF | RCC_CSR_BORRSTF, 0UL, (1UL << 1) | (1UL << 7) },
    };
    for (unsigned i = 0; i < sizeof cases / sizeof cases[0]; i++) {
        const uint32_t got = reset_cause_decode(cases[i].rcsr, cases[i].pwcr);
        printf("  %-16s RCC_CSR=0x%08lX PWR_CSR=0x%08lX → 解码 0x%02lX\n",
               cases[i].name, (unsigned long)cases[i].rcsr,
               (unsigned long)cases[i].pwcr, (unsigned long)got);
        check(cases[i].name, got, cases[i].want);
    }
    printf("  读完要写 RCC_CSR.RMVF（bit%u）清标志，否则下次开机照抄这次的结论\n",
           (unsigned)bitpos(RCC_CSR_RMVF));
    check("全零 = 分不清（标志已被清过）", reset_cause_decode(0UL, 0UL), 0UL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_firmware_run(void)
{
    puts("=== 8. 把固件本体跑一遍：从 168MHz 睡到醒来 ===");
    PWR_CR = PWR_CR_VOS | PWR_CR_FPDS;
    PWR_CSR = PWR_CSR_WUF;                     /* 上一轮是 WKUP 引脚叫醒的 */
    SCB_SCR = 0UL;
    DBGMCU_CR = 0x37UL;                        /* bit0/1/2 调试位 + bit4/5 */
    RCC_CSR = RCC_CSR_PORRSTF | RCC_CSR_PINRSTF;
    SysTick_LOAD = 0xDEADBEEFUL;

    firmware_main();

    printf("  跑完：CR=0x%08lX SCR=0x%08lX DBGMCU=0x%08lX LOAD=0x%08lX CSR=0x%08lX\n",
           (unsigned long)PWR_CR, (unsigned long)SCB_SCR, (unsigned long)DBGMCU_CR,
           (unsigned long)SysTick_LOAD, (unsigned long)PWR_CSR);
    check("调试三个位被清、其余保留", DBGMCU_CR, 0x30UL);
    check("醒来 SCR 的 SLEEPDEEP 仍是 1", bitv(SCB_SCR, SCB_SCR_SLEEPDEEP), 1UL);
    check("醒来 CR 的 PDDS=0（是 Stop）", bitv(PWR_CR, PWR_CR_PDDS), 0UL);
    check("醒来 CR 的 LPDS=1", bitv(PWR_CR, PWR_CR_LPDS), 1UL);
    check("固件发了 CWUF 这个清除动作", bitv(PWR_CR, PWR_CR_CWUF), 1UL);
    check("上一轮没有 SBF，就不该发 CSBF", bitv(PWR_CR, PWR_CR_CSBF), 0UL);
    check("SysTick 装载值按 16MHz 改过", SysTick_LOAD, 15999UL);

    /* 换个现场再跑一遍：这次硬件留的是 SBF（Standby 式醒来的痕迹） */
    PWR_CR = PWR_CR_VOS | PWR_CR_FPDS;
    PWR_CSR = PWR_CSR_SBF;
    firmware_main();
    printf("  再跑（现场=SBF）：CR=0x%08lX\n", (unsigned long)PWR_CR);
    check("这一轮该发 CSBF", bitv(PWR_CR, PWR_CR_CSBF), 1UL);
    check("这一轮没有 WUF，不该发 CWUF", bitv(PWR_CR, PWR_CR_CWUF), 0UL);

    /* 三个入口各敲一次，看落在寄存器里的档位 */
    PWR_CR = 0UL; SCB_SCR = SCB_SCR_SLEEPDEEP;
    enter_sleep();
    check("enter_sleep() 之后 SLEEPDEEP", bitv(SCB_SCR, SCB_SCR_SLEEPDEEP), 0UL);
    PWR_CR = 0UL; SCB_SCR = 0UL;
    enter_stop();
    printf("  enter_stop()   ：CR=0x%08lX SCR=0x%08lX\n",
           (unsigned long)PWR_CR, (unsigned long)SCB_SCR);
    check("enter_stop() 之后 SLEEPDEEP", bitv(SCB_SCR, SCB_SCR_SLEEPDEEP), 1UL);
    check("enter_stop() 之后 PDDS", bitv(PWR_CR, PWR_CR_PDDS), 0UL);
    PWR_CR = 0UL; SCB_SCR = 0UL; SysTick_LOAD = 0UL;
    enter_standby();
    printf("  enter_standby()：CR=0x%08lX SCR=0x%08lX（醒来=复位，这两行不会再执行）\n",
           (unsigned long)PWR_CR, (unsigned long)SCB_SCR);
    check("enter_standby() 之后 PDDS", bitv(PWR_CR, PWR_CR_PDDS), 1UL);
    check("Standby 不碰 SysTick 装载值", SysTick_LOAD, 0UL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_addresses(void)
{
    puts("=== 9. 地址表（probe.sh 拿 base+偏移与 CMSIS 对账）===");
    /* 这里刻意用 offsetof 之外的手写偏移：对账的对象是"我们的注释"，
     * CMSIS 那边用的是结构体成员顺序 + Offset 注释，两边独立。 */
    printf("PWR_CR 0x%08lX\n", (unsigned long)(PWR_BASE + 0x00UL));
    printf("PWR_CSR 0x%08lX\n", (unsigned long)(PWR_BASE + 0x04UL));
    printf("RCC_APB1ENR 0x%08lX\n", (unsigned long)(RCC_BASE + 0x40UL));
    printf("RCC_AHB1ENR 0x%08lX\n", (unsigned long)(RCC_BASE + 0x30UL));
    printf("RCC_BDCR 0x%08lX\n", (unsigned long)(RCC_BASE + 0x70UL));
    printf("RCC_CSR 0x%08lX\n", (unsigned long)(RCC_BASE + 0x74UL));
    printf("SCB_SCR 0x%08lX\n", (unsigned long)0xE000ED10UL);
    printf("SysTick_LOAD 0x%08lX\n", (unsigned long)0xE000E014UL);
    printf("DBGMCU_CR 0x%08lX\n", (unsigned long)(DBGMCU_BASE + 0x04UL));
    printf("BKPSRAM 0x%08lX\n", (unsigned long)0x40024000UL);
    puts("");
}

/* ---------------------------------------------------------------- */
int main(void)
{
    printf("运行档 HCLK = %lu Hz，醒来档 HSI = %lu Hz，比例 %.1f\n\n",
           (unsigned long)RUN_HCLK_HZ, (unsigned long)HSI_HZ,
           (double)RUN_HCLK_HZ / (double)HSI_HZ);

    probe_bit_positions();
    probe_addresses();
    probe_three_modes();
    probe_clock_bill();
    probe_iwdg();
    probe_backup();
    probe_wake_sources();
    probe_reset_causes();
    probe_firmware_run();

    printf(fails ? "断言 %d 条失败\n" : "断言全绿\n", fails);
    return fails ? 1 : 0;
}
