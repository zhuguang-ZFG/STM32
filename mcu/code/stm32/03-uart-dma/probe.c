/**
 * probe.c —— 03-uart-dma 无板取证（S7《波特率是算出来的》）
 *
 * 手法与 14-pwr 相同：把 main.c 里那组寄存器宏改指到一组 static 变量上，
 * 然后 #include "main.c"。于是下面每一条断言跑的都是固件本体
 * （clocks_read / usart1_init / usart1_pins / dma2_stream5_rx_init /
 *   uart_write_blocking / consume_rx / USART1_IRQHandler），
 * 不是另抄一遍算术——包括那张 BRR 误差表，用的就是固件自己的
 * BAUD_FROM_PCLK / PCLK_OF_BRR 两个宏。
 *
 * 假寄存器不会自己变：凡「硬件会置位/会清标志/会搬数据」的部分，
 * 这里只断言固件发出了那个动作（写了哪个字、读了哪一次 DR），
 * 不冒充硬件的回执。DMA 真实搬运量由我们手工写进 NDTR 来模拟。
 *
 * 第 2 节的位号表与第 9 节的地址表，由 probe.sh 分别和 CMSIS 官方头文件的
 * *_Pos、base+结构体成员 Address offset 逐条 diff；
 * 第 6 节那批 markdown 表格行，由 probe.sh 和站内 docs/stm32/07-usart.md
 * 的那张误差表逐行 diff——文章里的数字与本机算出来的数字必须是同一份。
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>

/* ---- 假寄存器：真实地址在这一遍里全部作废 ---- */
static volatile uint32_t f_gpioa_moder, f_gpioa_afrh;
static volatile uint32_t f_gpiof_moder, f_gpiof_bsrr;
static volatile uint32_t f_rcc_cfgr, f_rcc_pllcfgr, f_rcc_ahb1enr, f_rcc_apb2enr;
static volatile uint32_t f_usart1_sr, f_usart1_cr1, f_usart1_cr2, f_usart1_cr3;
static volatile uint32_t f_usart1_brr;
/* DR 是「读写都会走到」的窗口：发送写它、中断读它（ORE 的握手要求先读 SR 再读 DR）。
 * 所以这里记的是一串 DR 访问，写进去的值与读取次数都留痕。 */
static volatile uint32_t f_dr_log[64];
static volatile uint32_t f_dr_n;
#define USART1_DR (f_dr_log[f_dr_n++ & 63U])

static volatile uint32_t f_dma2_lisr, f_dma2_hisr, f_dma2_hifcr;
static volatile uint32_t f_dma_s5_cr, f_dma_s5_ndtr, f_dma_s5_par;
static volatile uint32_t f_dma_s5_m0ar, f_dma_s5_fcr;
static volatile uint32_t f_nvic_iser0, f_nvic_iser1, f_nvic_iser2;
static volatile uint32_t f_systick_ctrl, f_systick_load, f_systick_val;

#define GPIOA_MODER       f_gpioa_moder
#define GPIOA_AFRH        f_gpioa_afrh
#define GPIOF_MODER       f_gpiof_moder
#define GPIOF_BSRR        f_gpiof_bsrr
#define RCC_CFGR          f_rcc_cfgr
#define RCC_PLLCFGR       f_rcc_pllcfgr
#define RCC_AHB1ENR       f_rcc_ahb1enr
#define RCC_APB2ENR       f_rcc_apb2enr
#define USART1_SR         f_usart1_sr
#define USART1_CR1        f_usart1_cr1
#define USART1_CR2        f_usart1_cr2
#define USART1_CR3        f_usart1_cr3
#define USART1_BRR        f_usart1_brr
#define DMA2_LISR         f_dma2_lisr
#define DMA2_HISR         f_dma2_hisr
#define DMA2_HIFCR        f_dma2_hifcr
#define DMA_S5_CR         f_dma_s5_cr
#define DMA_S5_NDTR       f_dma_s5_ndtr
#define DMA_S5_PAR        f_dma_s5_par
#define DMA_S5_M0AR       f_dma_s5_m0ar
#define DMA_S5_FCR        f_dma_s5_fcr
#define NVIC_ISER0        f_nvic_iser0
#define NVIC_ISER1        f_nvic_iser1
#define NVIC_ISER2        f_nvic_iser2
#define SysTick_CTRL      f_systick_ctrl
#define SysTick_LOAD      f_systick_load
#define SysTick_VAL       f_systick_val

#define MCU_PROBE_NO_MAIN
#include "main.c"

static int fails;

static void check(const char *what, uint32_t got, uint32_t want)
{
    if (got == want) {
        printf("  ✓ %-34s = 0x%08lX\n", what, (unsigned long)got);
    } else {
        printf("  ✗ %-34s 得 0x%08lX，期望 0x%08lX\n",
               what, (unsigned long)got, (unsigned long)want);
        fails++;
    }
}

static void check_eq(const char *what, uint32_t got, uint32_t want)
{
    if (got == want) {
        printf("  ✓ %-34s = %lu\n", what, (unsigned long)got);
    } else {
        printf("  ✗ %-34s 得 %lu，期望 %lu\n",
               what, (unsigned long)got, (unsigned long)want);
        fails++;
    }
}

static unsigned bitpos(uint32_t mask)
{
    unsigned b = 0;
    while (mask > 1UL) { mask >>= 1; b++; }
    return b;
}

/* 一个域占多位时（MODER 两位、AFRH 四位）得从低位往上认域起点，
 * 上面那个 bitpos() 是从高位往下数的——它服务的是 BSRR/EN 那一类单笔只写一位的地方。 */
static unsigned lowbit(uint32_t mask)
{
    unsigned b = 0;
    if (mask == 0UL) { fails++; return 0U; }   /* 没写进去：宁可报错也不能在这里转圈 */
    while ((mask & 1UL) == 0UL) { mask >>= 1; b++; }
    return b;
}

static uint32_t bitv(uint32_t word, uint32_t mask)
{
    return (word & mask) ? 1UL : 0UL;
}

/* 真实波特率 = PCLK / BRR（OVER8=0）。这里只把整数除法换成 double 打印，
 * BRR 本身仍然出自固件那个宏，不另算一套。 */
static double baud_real(uint32_t pclk, uint32_t brr)
{
    return (double)pclk / (double)brr;
}

static double baud_err_pct(uint32_t pclk, uint32_t brr, uint32_t want)
{
    return 100.0 * (baud_real(pclk, brr) / (double)want - 1.0);
}

/* 四舍五入到整数，跟站内文章表格里那一列同一口径 */
static uint32_t baud_rounded(uint32_t pclk, uint32_t brr)
{
    return (uint32_t)((pclk + brr / 2U) / brr);
}

static void reset_regs(void)
{
    f_gpioa_moder = f_gpioa_afrh = 0UL;
    f_gpiof_moder = f_gpiof_bsrr = 0UL;
    f_rcc_cfgr = f_rcc_pllcfgr = f_rcc_ahb1enr = f_rcc_apb2enr = 0UL;
    f_usart1_sr = f_usart1_cr1 = f_usart1_cr2 = f_usart1_cr3 = 0UL;
    f_usart1_brr = 0UL;
    memset((void *)f_dr_log, 0, sizeof f_dr_log);
    f_dr_n = 0UL;
    f_dma2_lisr = f_dma2_hisr = f_dma2_hifcr = 0UL;
    f_dma_s5_cr = f_dma_s5_ndtr = f_dma_s5_par = f_dma_s5_m0ar = f_dma_s5_fcr = 0UL;
    f_nvic_iser0 = f_nvic_iser1 = f_nvic_iser2 = 0UL;
    f_systick_ctrl = f_systick_load = f_systick_val = 0UL;
    g_rx_bytes = g_frames = g_overruns = g_half_events = g_full_events = 0UL;
    g_pclk2 = g_hclk = g_brr = 0UL;
    memset((void *)g_rx_buf, 0, sizeof g_rx_buf);
    rx_cursor.read = rx_cursor.lost = 0UL;
    tx_head = tx_tail = 0UL;
    memset((void *)tx_queue, 0, sizeof tx_queue);
}

/* ---------------------------------------------------------------- */
/* 站内 docs/stm32/07-usart.md 那张表就是这几个档位；probe.sh 逐行 diff。
 * 每一行的 BRR 都由固件的 BAUD_FROM_PCLK 算出，实际波特率由 PCLK_OF_BRR 反算。 */
static const uint32_t CLK[] = { 1000000UL, 8000000UL, 16000000UL, 42000000UL, 84000000UL };
static const uint32_t BAUDS[] = { 9600UL, 115200UL, 460800UL, 921600UL };

/* 表里要出现的组合：站内正文引用到的全部档位 */
static int table_wanted(uint32_t clk, uint32_t baud)
{
    if (clk == 16000000UL) return 1;                          /* 四个波特率全要 */
    return baud == 115200UL && clk != 16000000UL;             /* 其余时钟只看 115200 */
}

static void probe_baud_table(int markdown)
{
    puts(markdown ? "=== 6. 站内误差表（probe.sh 与 docs/stm32/07-usart.md 逐行 diff）==="
                  : "=== 1. BRR 是算出来的：同一个波特率，时钟一变它就变 ===");
    if (markdown) {
        size_t ci, bi;
        for (ci = 0; ci < sizeof CLK / sizeof CLK[0]; ci++) {
            for (bi = 0; bi < sizeof BAUDS / sizeof BAUDS[0]; bi++) {
                uint32_t clk = CLK[ci], baud = BAUDS[bi];
                uint32_t brr;
                if (!table_wanted(clk, baud)) continue;
                brr = BAUD_FROM_PCLK(clk, baud);
                printf("| %lu MHz | %lu | %lu | %lu | %+.3f%% |\n",
                       (unsigned long)(clk / 1000000UL), (unsigned long)baud,
                       (unsigned long)brr, (unsigned long)baud_rounded(clk, brr),
                       baud_err_pct(clk, brr, baud));
            }
        }
        puts("");
        return;
    }
    {
        size_t ci, bi;
        for (ci = 0; ci < sizeof CLK / sizeof CLK[0]; ci++) {
            for (bi = 0; bi < sizeof BAUDS / sizeof BAUDS[0]; bi++) {
                uint32_t clk = CLK[ci], baud = BAUDS[bi];
                uint32_t brr = BAUD_FROM_PCLK(clk, baud);
                printf("  PCLK2=%-9lu 目标 %-7lu → BRR %-5lu(0x%lX) 实际 %-9.1f 误差 %+.3f%%",
                       (unsigned long)clk, (unsigned long)baud, (unsigned long)brr,
                       (unsigned long)brr, baud_real(clk, brr), baud_err_pct(clk, brr, baud));
                if (brr == 0UL) puts("  ← BRR=0：硬件禁止");
                else if (brr > 0xFFFFUL) puts("  ← 超出 16 位");
                else puts("");
            }
        }
        /* 固件在 16MHz/HSI 下真正写下的那一个 */
        check_eq("16MHz→115200 的 BRR", BAUD_FROM_PCLK(16000000UL, 115200UL), 139UL);
        check_eq("BRR=139 反算出的波特率", PCLK_OF_BRR(16000000UL, 139UL), 115107UL);
        check_eq("1MHz→115200 的 BRR", BAUD_FROM_PCLK(1000000UL, 115200UL), 9UL);
        check_eq("BRR=9 反算出的波特率", PCLK_OF_BRR(1000000UL, 9UL), 111111UL);
        check_eq("84MHz→115200 的 BRR", BAUD_FROM_PCLK(84000000UL, 115200UL), 729UL);
        check_eq("BRR=729 反算出的波特率", PCLK_OF_BRR(84000000UL, 729UL), 115226UL);
        puts("");
    }
}

/* CFGR / PLLCFGR 的域位置：本文件用它拼测试输入，第 2 节的位号表也用它，
 * 两处同一个常数，probe.sh 再把这组常数和 CMSIS 的 *_Pos 逐条对。 */
#define F_PLLM   0U
#define F_PLLN   6U
#define F_PLLP  16U
#define F_PLLSRC 22U
#define F_PLLQ  24U
#define F_SWS    2U
#define F_HPRE   4U
#define F_PPRE2 13U

/* ---------------------------------------------------------------- */
/* 只有一位被点亮时才有意义：把固件真正写下去的那一位的位号交出去。 */
static unsigned one_bit(const char *what, uint32_t word)
{
    if (word == 0UL || (word & (word - 1UL)) != 0UL) {
        printf("  ✗ %s：期望只有一个位被写，实际 0x%08lX\n", what, (unsigned long)word);
        fails++;
    }
    return bitpos(word);
}

static void probe_bit_table(void)
{
    unsigned pfen, paen, us1en, dma2en, br6, bs6, moder9, moder10, afsel9, afsel10;

    puts("=== 2. 位号表（probe.sh 拿它和 CMSIS 官方头文件逐位 diff）===");
    /* 三个来源，强度不一样，分清楚写：
     *   a) 固件自己命名的位宏（USART_* / DMA_SxCR_* / DMA_HISR_*，拼写与 CMSIS 一致）；
     *   b) 固件真跑一遍之后，从写进假寄存器的值里挖出来的那一位——main.c 在这些地方
     *      写的是裸移位（1UL<<5 之类），所以这里的位号是行为，不是抄来的常数；
     *   c) CFGR/PLLCFGR 的域位置出自本文件构造测试输入的同一组常数（下面 F_* 那些），
     *      固件解得对不对由第 7 节那六组回读判定。 */
    reset_regs();
    led_init();
    pfen = one_bit("led_init 之后的 AHB1ENR", f_rcc_ahb1enr);
    led_set(LED_R_PIN, 1U);
    br6 = bitpos(f_gpiof_bsrr);                    /* 亮 = 写复位半区 */
    led_set(LED_R_PIN, 0U);
    bs6 = bitpos(f_gpiof_bsrr);                    /* 灭 = 写置位半区 */
    usart1_pins();
    paen = one_bit("usart1_pins 新加的那一位", f_rcc_ahb1enr & ~(1UL << pfen));
    us1en = one_bit("usart1_pins 之后的 APB2ENR", f_rcc_apb2enr);
    /* MODER 里 PA9 的域值是 10：域起点 = 最低置位位减一。
     * AFRH 里 AF7 = 0111：域起点就是最低置位位。
     * 先认 PA9 那一位，把它抹掉再认 PA10——两个域在同一个寄存器里。 */
    moder9 = lowbit(f_gpioa_moder) - 1U;
    moder10 = lowbit(f_gpioa_moder & ~(0x3UL << moder9)) - 1U;
    afsel9 = lowbit(f_gpioa_afrh);
    afsel10 = lowbit(f_gpioa_afrh & ~(0xFUL << afsel9));
    dma2_stream5_rx_init();
    dma2en = one_bit("dma2_stream5_rx_init 新加的那一位",
                     f_rcc_ahb1enr & ~((1UL << pfen) | (1UL << paen)));

    printf("RCC_AHB1ENR_GPIOFEN %u\n", pfen);
    printf("RCC_AHB1ENR_GPIOAEN %u\n", paen);
    printf("RCC_AHB1ENR_DMA2EN %u\n", dma2en);
    printf("RCC_APB2ENR_USART1EN %u\n", us1en);
    printf("GPIO_MODER_MODER9 %u\n", moder9);
    printf("GPIO_MODER_MODER10 %u\n", moder10);
    printf("GPIO_AFRH_AFSEL9 %u\n", afsel9);
    printf("GPIO_AFRH_AFSEL10 %u\n", afsel10);
    printf("GPIO_BSRR_BR6 %u\n", br6);
    printf("GPIO_BSRR_BS6 %u\n", bs6);

#define PUT(name) printf("%s %u\n", #name, bitpos(name))
    PUT(USART_CR1_UE); PUT(USART_CR1_TE); PUT(USART_CR1_RE); PUT(USART_CR1_IDLEIE);
    PUT(USART_CR3_DMAR);
    PUT(USART_SR_RXNE); PUT(USART_SR_TC); PUT(USART_SR_TXE); PUT(USART_SR_IDLE);
    PUT(USART_SR_ORE); PUT(USART_SR_FE); PUT(USART_SR_NE);
    PUT(DMA_SxCR_EN); PUT(DMA_SxCR_DMEIE); PUT(DMA_SxCR_TEIE); PUT(DMA_SxCR_HTIE);
    PUT(DMA_SxCR_TCIE); PUT(DMA_SxCR_CIRC); PUT(DMA_SxCR_MINC); PUT(DMA_SxCR_CHSEL);
    PUT(DMA_SxCR_DIR);
    /* 这两个在 main.c 里叫 PS/MSIZE，CMSIS 的字段名是 PSIZE/MSIZE */
    printf("DMA_SxCR_PSIZE %u\n", bitpos(DMA_SxCR_PS));
    PUT(DMA_SxCR_MSIZE);
    PUT(DMA_HISR_TEIF5); PUT(DMA_HISR_HTIF5); PUT(DMA_HISR_TCIF5);

    printf("RCC_CFGR_SWS %u\n", F_SWS);
    printf("RCC_CFGR_HPRE %u\n", F_HPRE);
    printf("RCC_CFGR_PPRE2 %u\n", F_PPRE2);
    printf("RCC_PLLCFGR_PLLM %u\n", F_PLLM);
    printf("RCC_PLLCFGR_PLLN %u\n", F_PLLN);
    printf("RCC_PLLCFGR_PLLP %u\n", F_PLLP);
    printf("RCC_PLLCFGR_PLLQ %u\n", F_PLLQ);
    printf("RCC_PLLCFGR_PLLSRC %u\n", F_PLLSRC);
    puts("");
}

/* ---------------------------------------------------------------- */
/* BRR 只有整数格：一格多高、四舍五入是不是最优解，都用穷举回答。 */
static uint32_t argmin_brr(uint32_t pclk, uint32_t baud)
{
    uint32_t b, best = 0UL;
    unsigned long long bestd = 0ULL;
    for (b = 1UL; b <= 0xFFFFUL; b++) {
        unsigned long long prod = (unsigned long long)baud * b;
        unsigned long long diff = prod > pclk ? prod - pclk : (unsigned long long)pclk - prod;
        /* 比 |pclk/b - baud|，即 diff/b：交叉相乘避免浮点 */
        if (best == 0UL || diff * best < bestd * b) { best = b; bestd = diff; }
    }
    return best;
}

static void probe_quantization(void)
{
    puts("=== 3. 量化：BRR 是整数，最小一步就是 1/BRR ===");
    {
        uint32_t lo = BAUD_FROM_PCLK(16000000UL, 115200UL);
        printf("  16MHz 下 BRR 从 %lu 走到 %lu，波特率从 %.1f 掉到 %.1f —— 一格 %.1f baud，占目标的 %.3f%%\n",
               (unsigned long)lo, (unsigned long)(lo + 1UL),
               baud_real(16000000UL, lo), baud_real(16000000UL, lo + 1UL),
               baud_real(16000000UL, lo) - baud_real(16000000UL, lo + 1UL),
               100.0 * (baud_real(16000000UL, lo) - baud_real(16000000UL, lo + 1UL)) / 115200.0);
        printf("  所以四舍五入的最大误差是半格：%.3f%%\n",
               50.0 * (baud_real(16000000UL, lo) - baud_real(16000000UL, lo + 1UL)) / 115200.0);
    }
    {
        size_t k;
        struct { uint32_t clk, baud; } cases[] = {
            { 1000000UL, 115200UL }, { 8000000UL, 115200UL }, { 16000000UL, 115200UL },
            { 16000000UL, 9600UL },  { 16000000UL, 460800UL }, { 16000000UL, 921600UL },
            { 84000000UL, 115200UL }, { 42000000UL, 115200UL }, { 168000000UL, 115200UL },
        };
        puts("  穷举 1..65535 找误差最小的 BRR，再和固件的 +baud/2 四舍五入比：");
        for (k = 0; k < sizeof cases / sizeof cases[0]; k++) {
            uint32_t round_b = BAUD_FROM_PCLK(cases[k].clk, cases[k].baud);
            uint32_t scan_b = argmin_brr(cases[k].clk, cases[k].baud);
            printf("    PCLK2=%-10lu 目标 %-7lu 四舍五入 %-6lu 穷举 %-6lu 实际(穷举) %-9.1f 误差 %+.3f%%\n",
                   (unsigned long)cases[k].clk, (unsigned long)cases[k].baud,
                   (unsigned long)round_b, (unsigned long)scan_b,
                   baud_real(cases[k].clk, scan_b), baud_err_pct(cases[k].clk, scan_b, cases[k].baud));
            check_eq("穷举最优 = 固件的四舍五入", round_b == scan_b ? 1UL : 0UL, 1UL);
        }
    }
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_over8(void)
{
    puts("=== 4. OVER8=1：同一个 BRR，波特率直接翻倍 ===");
    {
        uint32_t brr = BAUD_FROM_PCLK(16000000UL, 115200UL);
        double over16 = baud_real(16000000UL, brr);
        double over8 = 2.0 * over16;
        printf("  同一颗 16MHz、同一个 BRR=%lu：16 倍过采样 %.1f，8 倍过采样 %.1f\n",
               (unsigned long)brr, over16, over8);
        check_eq("翻倍就是 2×115200 这一档", (uint32_t)(over8 + 0.5), 230216UL);

        /* 16MHz 想上 921600：16 倍过采样只能到 17 那一格，8 倍过采样能到 35 */
        {
            uint32_t b16 = BAUD_FROM_PCLK(16000000UL, 921600UL);
            uint32_t b8 = BAUD_FROM_PCLK(2UL * 16000000UL, 921600UL);
            printf("  921600@16MHz：OVER8=0 只能 BRR=%lu → %.1f（%+.3f%%）；"
                   "OVER8=1 等价于把时钟当 32MHz 算 → BRR=%lu → %.1f（%+.3f%%）\n",
                   (unsigned long)b16, baud_real(16000000UL, b16), baud_err_pct(16000000UL, b16, 921600UL),
                   (unsigned long)b8, baud_real(32000000UL, b8) / 2.0,
                   100.0 * ((baud_real(32000000UL, b8) / 2.0) / 921600.0 - 1.0));
            check_eq("OVER8=1 那格的 BRR", b8, 35UL);
        }
        /* 8 倍过采样只采 8 次：位数从 16 掉到 8，抗噪按同比例缩水 */
        printf("  代价：过采样 16→8，每位中点的位置判断余量减半（本章固件保持 OVER8=0）\n");
    }
    puts("");
}

/* ---------------------------------------------------------------- */
/* 帧预算：接收端在每个位的中点重采样，最危险的是最后一个被采样的位。
 * 站内公式与 docs/.vitepress/theme/BaudCalc.vue 同一口径：0.5/(帧位数-1.5)。 */
static void probe_frame_budget(void)
{
    puts("=== 5. 帧预算倒推：±2% 这个经验值是从哪来的 ===");
    {
        struct { const char *name; uint32_t bits; } f[] = {
            { "8N1", 10UL }, { "8E1", 11UL }, { "8E2", 12UL }, { "9N1", 11UL },
        };
        size_t i;
        for (i = 0; i < sizeof f / sizeof f[0]; i++) {
            double mid = (double)f[i].bits - 1.5;
            double total = 0.5 / mid * 100.0;
            printf("  %s：%lu 位帧，最后中点在 %.1f 位 → 两端合计 %.3f%%，各自 %.3f%%\n",
                   f[i].name, (unsigned long)f[i].bits, mid, total, total / 2.0);
        }
        check("8N1 的合计预算（×1000）", (uint32_t)(0.5 / 8.5 * 100000.0 + 0.5), 5882UL);

        /* 量化误差先吃掉多少，剩下才是两端各自能带的时钟源容差 */
        puts("  把上面的档位套进真实档位：量化误差先扣，剩下的对半分，HSI 是 ±1%");
        {
            struct { uint32_t clk, baud; const char *what; } c[] = {
                { 16000000UL, 115200UL, "16MHz/115200（HSI 默认）" },
                { 84000000UL, 115200UL, "84MHz/115200（PLL，APB2=/2）" },
                { 8000000UL,  115200UL, "8MHz/115200（HSE 直出）" },
                { 1000000UL,  115200UL, "1MHz/115200（PLL 参考输入）" },
                { 16000000UL, 921600UL, "16MHz/921600（OVER8=0）" },
                { 32000000UL, 921600UL, "32MHz/921600（OVER8=1 的等效值）" },
            };
            size_t k;
            for (k = 0; k < sizeof c / sizeof c[0]; k++) {
                uint32_t brr = BAUD_FROM_PCLK(c[k].clk, c[k].baud);
                double q = baud_err_pct(c[k].clk, brr, c[k].baud);
                double left = (5.882352941 - (q < 0 ? -q : q)) / 2.0;
                printf("    %-30s BRR=%-5lu 量化 %+.3f%% → 每端还剩 %.3f%%%s\n",
                       c[k].what, (unsigned long)brr, q, left,
                       left >= 2.0 ? "（够 HSI ±1%，还有余量）"
                                   : left >= 1.0 ? " ← 只够 HSI，几乎没余量"
                                                 : " ← 连 ±1% 都放不下，必然不可靠");
            }
            /* 判决口径：每端余量 ≥2% 才算安全（站内「±2% 经验值」） */
            check_eq("16MHz/115200 每端余量够 2%",
                     (5.882352941 - 0.0800245) / 2.0 >= 2.0 ? 1UL : 0UL, 1UL);
            check_eq("1MHz/115200 每端余量不够 2%",
                     (5.882352941 - 3.548980) / 2.0 >= 2.0 ? 1UL : 0UL, 0UL);
        }
    }
    puts("");
}

/* ---------------------------------------------------------------- */
/* PLLCFGR 的构造按 CMSIS 字段位置拼：M/N/P/Q/PLLSRC，别写死魔数 */
static uint32_t pllword(uint32_t m, uint32_t n, uint32_t p, uint32_t q, int from_hse)
{
    return (m & 0x3FUL) | ((n & 0x1FFUL) << F_PLLN)
         | ((((p / 2UL) - 1UL) & 0x3UL) << F_PLLP)
         | ((q & 0xFUL) << F_PLLQ)
         | (from_hse ? (1UL << F_PLLSRC) : 0UL);
}

static uint32_t cfgrword(uint32_t sws, uint32_t hpre_code, uint32_t ppre2_code)
{
    return ((sws & 0x3UL) << F_SWS) | ((hpre_code & 0xFUL) << F_HPRE)
         | ((ppre2_code & 0x7UL) << F_PPRE2);
}

static void probe_clocks_read(void)
{
    uint32_t hclk, pclk2;

    puts("=== 7. clocks_read()：BRR 用的时钟是回读出来的，不是假设的 ===");

    reset_regs();
    RCC_CFGR = cfgrword(0UL, 0UL, 0UL);            /* SWS=00 HSI，HPRE=/1，PPRE2=/1 */
    clocks_read(16000000UL, &g_hclk, &g_pclk2);
    hclk = g_hclk; pclk2 = g_pclk2;
    printf("  ① 复位默认（CFGR=0x%08lX）：HCLK=%lu PCLK2=%lu → BRR=%lu → %.1f（%+.3f%%）\n",
           (unsigned long)RCC_CFGR, (unsigned long)hclk, (unsigned long)pclk2,
           (unsigned long)BAUD_FROM_PCLK(pclk2, BAUD), baud_real(pclk2, BAUD_FROM_PCLK(pclk2, BAUD)),
           baud_err_pct(pclk2, BAUD_FROM_PCLK(pclk2, BAUD), BAUD));
    check_eq("HSI 档 HCLK", hclk, 16000000UL);
    check_eq("HSI 档 PCLK2", pclk2, 16000000UL);
    check_eq("HSI 档 BRR", BAUD_FROM_PCLK(pclk2, BAUD), 139UL);

    reset_regs();
    RCC_CFGR = cfgrword(2UL, 0UL, 4UL);            /* SWS=10 PLL，HPRE=/1，PPRE2=/2 */
    RCC_PLLCFGR = pllword(8UL, 336UL, 2UL, 7UL, 1);
    clocks_read(16000000UL, &g_hclk, &g_pclk2);
    hclk = g_hclk; pclk2 = g_pclk2;
    printf("  ② 板上跑 PLL(HSE 8M，M=8 N=336 P=2)：SYSCLK=%lu → AHB /1 → APB2 /2 → PCLK2=%lu\n",
           (unsigned long)hclk, (unsigned long)pclk2);
    printf("     → BRR=%lu → %.1f（%+.3f%%）：比 16MHz 那一档准 3 倍\n",
           (unsigned long)BAUD_FROM_PCLK(pclk2, BAUD), baud_real(pclk2, BAUD_FROM_PCLK(pclk2, BAUD)),
           baud_err_pct(pclk2, BAUD_FROM_PCLK(pclk2, BAUD), BAUD));
    check_eq("PLL 档 HCLK=168MHz", hclk, 168000000UL);
    check_eq("PLL 档 PCLK2=84MHz", pclk2, 84000000UL);
    check_eq("PLL 档 BRR", BAUD_FROM_PCLK(pclk2, BAUD), 729UL);

    reset_regs();
    RCC_CFGR = cfgrword(2UL, 0xDUL, 0UL);          /* SWS=PLL，HPRE=/128，PPRE2=/1 */
    RCC_PLLCFGR = pllword(8UL, 336UL, 2UL, 7UL, 1);
    clocks_read(16000000UL, &g_hclk, &g_pclk2);
    printf("  ③ HPRE 编码 1101 = /128（F4 没有 /32）：HCLK=%lu PCLK2=%lu → BRR=%lu → %.1f（%+.3f%%）\n",
           (unsigned long)g_hclk, (unsigned long)g_pclk2,
           (unsigned long)BAUD_FROM_PCLK(g_pclk2, BAUD), baud_real(g_pclk2, BAUD_FROM_PCLK(g_pclk2, BAUD)),
           baud_err_pct(g_pclk2, BAUD_FROM_PCLK(g_pclk2, BAUD), BAUD));
    check_eq("/128 那档的 HCLK", g_hclk, 1312500UL);

    reset_regs();
    RCC_CFGR = cfgrword(0UL, 0xFUL, 0UL);          /* SWS 还停在 HSI，HPRE=/512 */
    clocks_read(16000000UL, &g_hclk, &g_pclk2);
    printf("  ④ HPRE=1111 = /512：HCLK=%lu → PCLK2=%lu → BRR=%lu\n",
           (unsigned long)g_hclk, (unsigned long)g_pclk2, (unsigned long)BAUD_FROM_PCLK(g_pclk2, BAUD));
    check_eq("/512 那档的 HCLK", g_hclk, 31250UL);
    /* 分频到这份上，115200 需要的 BRR 连 1 都凑不到——四舍五入直接给 0，
     * 而 RM0090 明确 USARTDIV 不得为 0。这就是「BRR=0 是算出来的非法值」。 */
    check_eq("PCLK2=31250 时算出的 BRR（非法）", BAUD_FROM_PCLK(g_pclk2, BAUD), 0UL);
    check_eq("PCLK2=57600（正好半个波特率）时 BRR", BAUD_FROM_PCLK(57600UL, BAUD), 1UL);
    check_eq("PCLK2=57599 时 BRR（塌到 0）", BAUD_FROM_PCLK(57599UL, BAUD), 0UL);

    /* 最关键的一条反例：PLLCFGR 配好了但 SWS 没切过去，固件回读到的是 HSI，
     * 于是 BRR 按 16MHz 算；人如果写死 84MHz 那一版的 729，串口就偏到十万八千里。 */
    reset_regs();
    RCC_CFGR = cfgrword(0UL, 0UL, 0UL);            /* SWS=00：PLL 起来了但没切，分频也没动 */
    RCC_PLLCFGR = pllword(8UL, 336UL, 2UL, 7UL, 1);
    clocks_read(16000000UL, &g_hclk, &g_pclk2);
    printf("  ⑤ 只配 PLLCFGR、没切 SWS：回读 PCLK2=%lu → 固件算出 BRR=%lu（按 84MHz 写死的是 729）\n",
           (unsigned long)g_pclk2, (unsigned long)BAUD_FROM_PCLK(g_pclk2, BAUD));
    check_eq("没切过去时固件算的 BRR", BAUD_FROM_PCLK(g_pclk2, BAUD), 139UL);
    printf("     写死 729 的话，16MHz 下真波特率 = %.1f（目标 115200，差 %+.1f%%）——乱码就是这么来的\n",
           baud_real(16000000UL, 729UL), baud_err_pct(16000000UL, 729UL, BAUD));
    check_eq("写死 729 的误差量级（|%%|×10）", (uint32_t)(-baud_err_pct(16000000UL, 729UL, BAUD) * 10.0 + 0.5), 809UL);

    /* HSE_VALUE_HZ 填错：编译期常量，不会报错，只会让算出来的时钟整体偏 */
    reset_regs();
    RCC_CFGR = cfgrword(2UL, 0UL, 4UL);
    RCC_PLLCFGR = pllword(8UL, 336UL, 2UL, 7UL, 1);
    clocks_read(16000000UL, &g_hclk, &g_pclk2);
    printf("  ⑥ 宏按 8MHz 算出 PCLK2=%lu；板上其实是 25MHz 晶振 → 真 PCLK2=%lu，"
           "BRR=%lu 打出的波特率是 %.1f（%+.1f%%）\n",
           (unsigned long)g_pclk2, (unsigned long)(g_pclk2 / 8UL * 25UL),
           (unsigned long)BAUD_FROM_PCLK(g_pclk2, BAUD),
           baud_real(g_pclk2 / 8UL * 25UL, BAUD_FROM_PCLK(g_pclk2, BAUD)),
           baud_err_pct(g_pclk2 / 8UL * 25UL, BAUD_FROM_PCLK(g_pclk2, BAUD), BAUD));
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_pin_writes(void)
{
    puts("=== 8. 写入动作：固件确实把这些位写下去了 ===");

    reset_regs();
    led_init();
    printf("  led_init()   → AHB1ENR=0x%08lX GPIOF_MODER=0x%08lX\n",
           (unsigned long)f_rcc_ahb1enr, (unsigned long)f_gpiof_moder);
    check("GPIOF 时钟（AHB1 bit5）", bitv(RCC_AHB1ENR, 1UL << 5), 1UL);
    check_eq("PF6 模式位 = 01（输出）", (f_gpiof_moder >> 12) & 0x3UL, 1UL);
    check_eq("PF8 模式位 = 01（输出）", (f_gpiof_moder >> 16) & 0x3UL, 1UL);

    led_set(LED_R_PIN, 1U);
    printf("  led_set(6, 亮) → BSRR=0x%08lX = 1<<%lu：站内点灯公式写的那一个字\n",
           (unsigned long)f_gpiof_bsrr, (unsigned long)bitpos(f_gpiof_bsrr));
    check_eq("点亮写的是 BSRR 复位半区 bit22", f_gpiof_bsrr, 1UL << 22);
    led_set(LED_R_PIN, 0U);
    check_eq("熄灭写的是 BSRR 置位半区 bit6", f_gpiof_bsrr, 1UL << 6);

    reset_regs();
    usart1_pins();
    printf("  usart1_pins()→ AHB1ENR=0x%08lX APB2ENR=0x%08lX MODER=0x%08lX AFRH=0x%08lX\n",
           (unsigned long)f_rcc_ahb1enr, (unsigned long)f_rcc_apb2enr,
           (unsigned long)f_gpioa_moder, (unsigned long)f_gpioa_afrh);
    check("GPIOA 时钟（AHB1 bit0）", bitv(RCC_AHB1ENR, 1UL << 0), 1UL);
    check("USART1 时钟（APB2 bit4）", bitv(RCC_APB2ENR, 1UL << 4), 1UL);
    check_eq("PA9 模式位 = 10（复用）", (f_gpioa_moder >> 18) & 0x3UL, 2UL);
    check_eq("PA10 模式位 = 10（复用）", (f_gpioa_moder >> 20) & 0x3UL, 2UL);
    check_eq("PA9 的 AFSEL = AF7", (f_gpioa_afrh >> 4) & 0xFUL, 7UL);
    check_eq("PA10 的 AFSEL = AF7", (f_gpioa_afrh >> 8) & 0xFUL, 7UL);
    /* PA9/PA10 是引脚 8..15 那一半，所以走 AFRH 而不是 AFRL：
     * 索引算错的话，AF 写进 AFRL 就等于没写。 */
    check_eq("AFRH 相对 GPIOF_BASE 那类端口的偏移",
             (uint32_t)(GPIOA_BASE + 0x24UL) - (uint32_t)GPIOA_BASE, 0x24UL);

    reset_regs();
    f_usart1_sr = USART_SR_TXE | USART_SR_TC;      /* 「硬件随时可发」的回执 */
    usart1_init(16000000UL);
    printf("  usart1_init(16MHz) → BRR=%lu CR1=0x%04lX g_brr=%lu\n",
           (unsigned long)f_usart1_brr, (unsigned long)f_usart1_cr1, (unsigned long)g_brr);
    check_eq("写进 BRR 寄存器的那个值", f_usart1_brr, 139UL);
    check_eq("同一个值也存进可观测量 g_brr", g_brr, 139UL);
    check_eq("CR1 = UE|TE|RE|IDLEIE", f_usart1_cr1, 0x201CUL);
    check("CR1.UE（bit13）", bitv(USART1_CR1, USART_CR1_UE), 1UL);
    check("CR1.TE（bit3）", bitv(USART1_CR1, USART_CR1_TE), 1UL);
    check("CR1.RE（bit2）", bitv(USART1_CR1, USART_CR1_RE), 1UL);
    check("CR1.IDLEIE（bit4）", bitv(USART1_CR1, USART_CR1_IDLEIE), 1UL);
    check("CR1 里 RXNEIE（bit5）没被顺手打开", bitv(USART1_CR1, 1UL << 5), 0UL);
    check_eq("CR2/CR3 先被清零（DMA 那一步还没来）", f_usart1_cr2 | f_usart1_cr3, 0UL);

    reset_regs();
    dma2_stream5_rx_init();
    printf("  dma2_stream5_rx_init() → PAR=0x%08lX NDTR=%lu M0AR=0x%08lX FCR=%lu CR=0x%08lX CR3=0x%02lX\n",
           (unsigned long)f_dma_s5_par, (unsigned long)f_dma_s5_ndtr,
           (unsigned long)f_dma_s5_m0ar, (unsigned long)f_dma_s5_fcr,
           (unsigned long)f_dma_s5_cr, (unsigned long)f_usart1_cr3);
    check("DMA2 时钟（AHB1 bit22）", bitv(RCC_AHB1ENR, 1UL << 22), 1UL);
    check_eq("PAR 指向 USART1->DR（0x40011004）", f_dma_s5_par, 0x40011004UL);
    check_eq("NDTR = 环形数组长度", f_dma_s5_ndtr, RX_BUF_LEN);
    check_eq("M0AR = &g_rx_buf（宿主机地址，只验类型转换）",
             f_dma_s5_m0ar, (uint32_t)(uintptr_t)g_rx_buf);
    check_eq("FCR = 0：不走 FIFO，直接模式", f_dma_s5_fcr, 0UL);
    check_eq("CR 终值 = 环形|增量|HTIE|TCIE|TEIE|CH4|EN", f_dma_s5_cr, 0x0800051DUL);
    check("CR.CHSEL = 4（bit25..27）", (f_dma_s5_cr >> 25) & 0x7UL, 4UL);
    check("CR.CIRC（bit8）", bitv(DMA_S5_CR, DMA_SxCR_CIRC), 1UL);
    check("CR.MINC（bit10）", bitv(DMA_S5_CR, DMA_SxCR_MINC), 1UL);
    check("CR.HTIE（bit3）", bitv(DMA_S5_CR, DMA_SxCR_HTIE), 1UL);
    check("CR.TCIE（bit4）", bitv(DMA_S5_CR, DMA_SxCR_TCIE), 1UL);
    check("CR.EN（bit0，最后才置）", bitv(DMA_S5_CR, DMA_SxCR_EN), 1UL);
    check("CR.DIR=00（外设→内存）", (f_dma_s5_cr >> 6) & 0x3UL, 0UL);
    check_eq("CR3.DMAR（bit6）：RXNE 交给 DMA 取", f_usart1_cr3, USART_CR3_DMAR);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_tx_path(void)
{
    puts("=== 9. 发送：每一字节都先等 TXE，收尾等 TC ===");

    reset_regs();
    f_usart1_sr = USART_SR_TXE | USART_SR_TC;
    uart_write_blocking("uart-dma ready\r\n");
    {
        const char *want = "uart-dma ready\r\n";
        size_t i, n = strlen(want);
        printf("  发 %lu 字节 → DR 被写了 %lu 次，最后一笔 = 0x%02lX（'%c'）\n",
               (unsigned long)n, (unsigned long)f_dr_n,
               (unsigned long)(f_dr_log[(f_dr_n - 1U) & 63U] & 0xFFUL),
               (f_dr_log[(f_dr_n - 1U) & 63U] & 0xFFUL) >= 0x20UL
                   ? (char)(f_dr_log[(f_dr_n - 1U) & 63U] & 0xFFUL) : '.');
        check_eq("每个字节一次 DR 写，不多不少", f_dr_n, (uint32_t)n);
        for (i = 0; i < n; i++) {
            if ((f_dr_log[i] & 0xFFUL) != (uint32_t)(unsigned char)want[i]) {
                printf("  ✗ DR 第 %lu 次写的是 0x%02lX，期望 0x%02lX\n",
                       (unsigned long)i, (unsigned long)(f_dr_log[i] & 0xFFUL),
                       (unsigned long)(unsigned char)want[i]);
                fails++;
                break;
            }
        }
        if (!fails) printf("  ✓ DR 写入序列与字符串逐字节一致（含 \\r\\n）\n");
    }
    /* 截断检查：char 转 uint8_t 再转 uint32_t，高位必须干净 */
    reset_regs();
    f_usart1_sr = USART_SR_TXE | USART_SR_TC;
    uart_write_blocking("\xFF\x7F\x01");
    check_eq("0xFF 写进 DR 时没有符号扩展", f_dr_log[0] & 0xFFFFFFFFUL, 0xFFUL);
    printf("  （main.c 里那句 (uint32_t)(uint8_t)*s 就是在防这个：%s 会写成 0xFFFFFFFF）\n",
           "char 为有符号时");
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_rx_path(void)
{
    puts("=== 10. 接收两级缓冲：DMA 搬进数组，IDLE 只是「总线空了」");

    reset_regs();
    dma2_stream5_rx_init();
    {
        uint32_t i;
        for (i = 0; i < RX_BUF_LEN; i++) g_rx_buf[i] = (uint8_t)(0x40U + i);
    }

    /* 硬件搬到一半：NDTR 从 64 递减，剩 24 → 已写 40 字节 */
    f_dma_s5_ndtr = 24UL;
    f_dma2_hisr = DMA_HISR_HTIF5;                  /* 半传中断标志 */
    DMA2_Stream5_IRQHandler();
    printf("  半传：pos=%lu → 取出 %lu 字节，g_rx_bytes=%lu g_half_events=%lu\n",
           (unsigned long)((RX_BUF_LEN - 24UL) % RX_BUF_LEN), (unsigned long)tx_head,
           (unsigned long)g_rx_bytes, (unsigned long)g_half_events);
    check_eq("半传取出 40 字节", tx_head, 40UL);
    check_eq("观测量 g_rx_bytes 同步", g_rx_bytes, 40UL);
    check_eq("半传事件计数", g_half_events, 1UL);
    check_eq("整传事件计数还没动", g_full_events, 0UL);
    check_eq("清标志写的是 HIFCR（不是只读的 HISR）", f_dma2_hifcr, DMA_HISR_HTIF5);
    {
        uint32_t i, bad = 0UL;
        for (i = 0; i < 40UL; i++) {
            if (tx_queue[i] != (uint8_t)(0x40U + i)) bad++;
        }
        check_eq("搬进发送队列的顺序与原数组一致（坏字节数）", bad, 0UL);
    }

    /* 搬到尾：NDTR=0 → pos 回到 0，跨环形边界再取 24 字节 */
    f_dma_s5_ndtr = 0UL;
    f_dma2_hisr = DMA_HISR_TCIF5;
    DMA2_Stream5_IRQHandler();
    printf("  整传：pos=%lu → 累计 %lu 字节，g_full_events=%lu\n",
           (unsigned long)((RX_BUF_LEN - 0UL) % RX_BUF_LEN), (unsigned long)tx_head,
           (unsigned long)g_full_events);
    check_eq("跨边界补齐剩下 24 字节", tx_head, 64UL);
    check_eq("g_rx_bytes = 一整圈", g_rx_bytes, 64UL);
    check_eq("整传事件计数", g_full_events, 1UL);
    check_eq("环形游标回到 0", rx_cursor.read, 0UL);

    /* 传输错误：游标整段作废，宁丢不猜 */
    f_dma_s5_ndtr = 8UL;
    f_dma2_hisr = DMA_HISR_TEIF5;
    DMA2_Stream5_IRQHandler();
    printf("  错误（TEIF5）：丢弃 %lu 字节段，g_overruns=%lu，游标 lost=%lu\n",
           (unsigned long)64UL, (unsigned long)g_overruns, (unsigned long)rx_cursor.lost);
    check_eq("错误段整段丢弃 → 不再追加字节", tx_head, 64UL);
    check_eq("溢出计数 +1", g_overruns, 1UL);
    check_eq("游标 lost +1", rx_cursor.lost, 1UL);

    /* IDLE：只证明总线空了，它不是协议帧边界 */
    reset_regs();
    dma2_stream5_rx_init();
    f_usart1_sr = USART_SR_IDLE | USART_SR_ORE;
    f_dma_s5_ndtr = RX_BUF_LEN;                    /* DMA 一个字节都还没搬 */
    f_dr_n = 0UL;
    USART1_IRQHandler();
    printf("  IDLE|ORE：读 DR 握手 %lu 次，g_frames=%lu（名字叫 frames，其实是 IDLE 通知数）\n",
           (unsigned long)f_dr_n, (unsigned long)g_frames);
    check_eq("先读 SR 再读 DR（ORE 的清除握手）", f_dr_n, 1UL);
    check_eq("IDLE 让 g_frames +1", g_frames, 1UL);
    check_eq("ORE 让 g_overruns +1", g_overruns, 1UL);
    check_eq("没有字节可取时 tx_head 不动", tx_head, 0UL);

    /* 一帧文本进来：IDLE 到时 DMA 已经搬了 5 字节 */
    reset_regs();
    dma2_stream5_rx_init();
    {
        static const uint8_t msg[5] = { 'A', 'T', 0x0DU, 0x0AU, '!' };
        uint32_t i;
        for (i = 0; i < 5UL; i++) g_rx_buf[i] = msg[i];
    }
    f_usart1_sr = USART_SR_IDLE;
    f_dma_s5_ndtr = RX_BUF_LEN - 5UL;
    USART1_IRQHandler();
    printf("  收到 5 字节后空闲：g_rx_bytes=%lu，队列里是 %02lX %02lX %02lX %02lX %02lX（AT\\r\\n!）\n",
           (unsigned long)g_rx_bytes,
           (unsigned long)tx_queue[0], (unsigned long)tx_queue[1], (unsigned long)tx_queue[2],
           (unsigned long)tx_queue[3], (unsigned long)tx_queue[4]);
    check_eq("IDLE 这一次把 5 字节交给上层", g_rx_bytes, 5UL);
    check_eq("帧数=IDLE 通知数，不是协议帧数", g_frames, 1UL);
    puts("");
}

/* ---------------------------------------------------------------- */
static void probe_addresses(void)
{
    puts("=== 11. 地址表（probe.sh 拿 base+偏移与 CMSIS 对账）===");
    /* 这里刻意用 main.c 里手写的偏移：对账对象是「固件注释里的数字」，
     * CMSIS 那边用的是结构体成员顺序 + Address offset 注释，两边独立。 */
    printf("USART1_SR 0x%08X\n", (unsigned)(USART1_BASE + 0x00UL));
    printf("USART1_DR 0x%08X\n", (unsigned)(USART1_BASE + 0x04UL));
    printf("USART1_BRR 0x%08X\n", (unsigned)(USART1_BASE + 0x08UL));
    printf("USART1_CR1 0x%08X\n", (unsigned)(USART1_BASE + 0x0CUL));
    printf("USART1_CR2 0x%08X\n", (unsigned)(USART1_BASE + 0x10UL));
    printf("USART1_CR3 0x%08X\n", (unsigned)(USART1_BASE + 0x14UL));
    printf("GPIOA_MODER 0x%08X\n", (unsigned)(GPIOA_BASE + 0x00UL));
    printf("GPIOA_AFRH 0x%08X\n", (unsigned)(GPIOA_BASE + 0x24UL));
    printf("GPIOF_MODER 0x%08X\n", (unsigned)(GPIOF_BASE + 0x00UL));
    printf("GPIOF_BSRR 0x%08X\n", (unsigned)(GPIOF_BASE + 0x18UL));
    printf("RCC_PLLCFGR 0x%08X\n", (unsigned)(RCC_BASE + 0x04UL));
    printf("RCC_CFGR 0x%08X\n", (unsigned)(RCC_BASE + 0x08UL));
    printf("RCC_AHB1ENR 0x%08X\n", (unsigned)(RCC_BASE + 0x30UL));
    printf("RCC_APB2ENR 0x%08X\n", (unsigned)(RCC_BASE + 0x44UL));
    printf("DMA2_LISR 0x%08X\n", (unsigned)(DMA2_BASE + 0x00UL));
    printf("DMA2_HISR 0x%08X\n", (unsigned)(DMA2_BASE + 0x04UL));
    printf("DMA2_HIFCR 0x%08X\n", (unsigned)(DMA2_BASE + 0x0CUL));
    printf("DMA2_S5_CR 0x%08X\n", (unsigned)(DMA2_S5_BASE + 0x00UL));
    printf("DMA2_S5_NDTR 0x%08X\n", (unsigned)(DMA2_S5_BASE + 0x04UL));
    printf("DMA2_S5_PAR 0x%08X\n", (unsigned)(DMA2_S5_BASE + 0x08UL));
    printf("DMA2_S5_M0AR 0x%08X\n", (unsigned)(DMA2_S5_BASE + 0x0CUL));
    printf("DMA2_S5_FCR 0x%08X\n", (unsigned)(DMA2_S5_BASE + 0x14UL));
    printf("SysTick_CTRL 0x%08X\n", (unsigned)0xE000E010UL);
    printf("SysTick_LOAD 0x%08X\n", (unsigned)0xE000E014UL);
    printf("NVIC_ISER1 0x%08X\n", (unsigned)0xE000E104UL);
    puts("");
}

/* ---------------------------------------------------------------- */
int main(void)
{
    printf("USART1 挂在 APB2 上：本工程 PCLK2 取 %s，目标波特率 %lu 8N1\n\n",
           "16 MHz（HSI 复位默认）", (unsigned long)BAUD);

    probe_baud_table(0);
    probe_bit_table();
    probe_quantization();
    probe_over8();
    probe_frame_budget();
    probe_baud_table(1);
    probe_clocks_read();
    probe_pin_writes();
    probe_tx_path();
    probe_rx_path();
    probe_addresses();

    printf(fails ? "断言 %d 条失败\n" : "断言全绿\n", fails);
    return fails ? 1 : 0;
}
