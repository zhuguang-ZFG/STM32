/**
 * main.c —— 01-rcc-clock：把时钟树从图纸变成方波
 *
 * 本工程回答一个问题：为什么芯片"跑起来"的第一件事是配时钟？
 * 因为复位那一刻芯片只有内部 RC（HSI 16MHz）在供电，外部晶振没起振、
 * Flash 没准备好、主频还锁在最低档。所以正确顺序是：
 *
 *   电压档 → Flash 等待周期 → 开 HSE 并等就绪 → 配 PLL → 切 SYSCLK → 回读确认
 *
 * 这一步顺序错了，典型后果不是"跑得慢"，而是"随机跑飞"。
 *
 * 观测手段（都不需要改动代码）：
 *   1. PA8 (MCO1) 用示波器/逻辑分析仪量频率，验证算出来的 SYSCLK；
 *   2. PF6 红灯按 1Hz 闪烁——如果延时函数没跟着改时钟，闪烁会快 10.5 倍；
 *   3. GDB 观察 g_clock_tree[] 全局量，直接读出 CPU 认为的时钟。
 *
 * 事实基准：ST 官方 CMSIS 头文件 cmsis_device_f4/Include/stm32f407xx.h
 *          （寄存器偏移与位定义，本文注释中的 bit 位置均对应该文件）。
 */

#include <stdint.h>

/* ============================ 寄存器定义 ============================
 * 基址与偏移全部对应该文件：RCC = AHB1PERIPH_BASE+0x3800，
 * GPIOA = AHB1PERIPH_BASE+0x0000，GPIOF = AHB1PERIPH_BASE+0x1400，
 * PWR = APB1PERIPH_BASE+0x7000，FLASH = AHB1PERIPH_BASE+0x3C00。
 */
#define RCC_BASE            (0x40023800UL)
#define RCC_CR              (*(volatile uint32_t *)(RCC_BASE + 0x00UL))
/* 这两个寄存器宏给了 #ifndef 口子：probe.c 在宿主上 #include 本文件，
 * 把它们改指一组假寄存器，于是 clock_tree_readback() 跑的是真代码而不是抄一份。
 * 不定义时就是下面的真实地址，固件侧一字不变。 */
#ifndef RCC_PLLCFGR
#define RCC_PLLCFGR         (*(volatile uint32_t *)(RCC_BASE + 0x04UL))
#endif
#ifndef RCC_CFGR
#define RCC_CFGR            (*(volatile uint32_t *)(RCC_BASE + 0x08UL))
#endif

#define PWR_BASE            (0x40007000UL)
#define PWR_CR              (*(volatile uint32_t *)(PWR_BASE + 0x00UL))

#define FLASH_ACR           (*(volatile uint32_t *)(0x40023C00UL))

#define GPIOA_BASE          (0x40020000UL)
#define GPIOA_MODER         (*(volatile uint32_t *)(GPIOA_BASE + 0x00UL))
#define GPIOA_AFRH          (*(volatile uint32_t *)(GPIOA_BASE + 0x24UL)) /* [9:8]=PA8 */

#define GPIOF_BASE          (0x40021400UL)
#define GPIOF_MODER         (*(volatile uint32_t *)(GPIOF_BASE + 0x00UL))
#define GPIOF_BSRR          (*(volatile uint32_t *)(GPIOF_BASE + 0x18UL))

/* SysTick 是 Cortex-M 内核外设，不在 STM32 外设地址空间里 */
#define SysTick_CTRL        (*(volatile uint32_t *)(0xE000E010UL))
#define SysTick_LOAD        (*(volatile uint32_t *)(0xE000E014UL))
#define SysTick_VAL         (*(volatile uint32_t *)(0xE000E018UL))

/* ---- 位定义（RCC_CR / RCC_PLLCFGR / RCC_CFGR，见 CMSIS 头文件） ---- */
#define RCC_CR_HSION        (1UL << 0)
#define RCC_CR_HSIRDY       (1UL << 1)
#define RCC_CR_HSEON        (1UL << 16)
#define RCC_CR_HSERDY       (1UL << 17)
#define RCC_CR_PLLON        (1UL << 24)
#define RCC_CR_PLLRDY       (1UL << 25)

#define RCC_PLLCFGR_PLLM    (0x3FUL << 0)    /* [5:0]   分频，2..63     */
#define RCC_PLLCFGR_PLLN    (0x1FFUL << 6)   /* [14:6]  倍频，50..432   */
#define RCC_PLLCFGR_PLLP    (0x3UL << 16)    /* [17:16] 00=/2, 01=/4    */
#define RCC_PLLCFGR_PLLSRC  (1UL << 22)      /* 0=HSI, 1=HSE          */
#define RCC_PLLCFGR_PLLQ    (0xFUL << 24)    /* [27:24] 给 USB，2..15   */

#define RCC_CFGR_SW         (0x3UL << 0)     /* [1:0]   系统时钟选择   */
#define RCC_CFGR_SWS        (0x3UL << 2)     /* [3:2]   切换状态回执   */
#define RCC_CFGR_SWS_PLL    (0x2UL << 2)     /* 回执=2x 表示已用 PLL  */
#define RCC_CFGR_HPRE       (0xFUL << 4)     /* [7:4]   AHB 预分频     */
#define RCC_CFGR_PPRE1      (0x7UL << 10)    /* [12:10] APB1 预分频    */
#define RCC_CFGR_PPRE2      (0x7UL << 13)    /* [15:13] APB2 预分频    */
#define RCC_CFGR_MCO1PRE    (0x7UL << 24)    /* [26:24] MCO1 预分频    */

#define FLASH_ACR_LATENCY   (0x7UL << 0)     /* [2:0] 等待周期数       */
#define FLASH_ACR_PRFTEN    (1UL << 8)       /* 预取缓冲               */

#define PWR_CR_VOS          (1UL << 14)      /* 0=Scale2(≤144MHz) 1=Scale1(≤168MHz) */

/* ============================ 编译期配置 ============================ */
#ifndef USE_HSE_PLL
#define USE_HSE_PLL 0          /* 0：留在 HSI 16MHz（默认，无晶振也能跑）
                                 1：走 HSE + PLL 到 168MHz              */
#endif

#ifndef HSE_VALUE_HZ
#define HSE_VALUE_HZ 8000000UL /* 板上 HSE 晶振频率。
                                * 改错这里会算出完全错误的 SYSCLK，
                                * 而程序不会有任何报错——这正是本章要讲的风险。
                                * 用不起确定值就保持 USE_HSE_PLL=0。 */
#endif

#define SYSCLK_TARGET_HZ 168000000UL
#define VCO_INPUT_HZ     1000000UL   /* PLL 参考输入，芯片允许 1~2MHz */

#define LED_R_PIN 6U              /* 霸天虎板载红灯 PF6，低电平点亮 */
#define MCO1_PIN  8U              /* PA8 复用为 MCO1（AF0）        */

/* ============================ 时钟状态 ============================ */

/* GDB 里可以直接 watch 这几个量验证"程序以为自己是多少Hz" */
volatile uint32_t SystemCoreClock;                 /* SPL/工程惯用名字 */
volatile uint32_t g_pll_m, g_pll_n, g_pll_p, g_pll_q;
volatile uint32_t g_clock_tree[5];                  /* {SYSCLK,HCLK,PCLK1,PCLK2,TIM2CLK} */
volatile uint32_t g_clock_status;                   /* 0=PLL 成功，1=回退 HSI，2=HSE 起振超时 */

static volatile uint32_t g_ms;                      /* SysTick 毫秒计数 */

/* ============================ 延时 ============================ */

/** SysTick 按 HCLK 打拍，1ms 中断一次。这里是本章最容易被忽略的联动：
 *  时钟从 16MHz 提到 168MHz 后，如果不重配 LOAD，延时就会短 10.5 倍。 */
static void systick_init(uint32_t hclk_hz)
{
    g_ms = 0;
    SysTick_CTRL = 0;
    SysTick_LOAD = hclk_hz / 1000UL - 1UL;         /* CLKSOURCE=0 → 用处理器时钟 */
    SysTick_VAL  = 0;
    SysTick_CTRL = 0x7UL;                           /* ENABLE|TICKINT|CLKSOURCE */
}

void SysTick_Handler(void)
{
    g_ms++;
}

static uint32_t millis(void)
{
    return g_ms;
}

static void delay_ms(uint32_t ms)
{
    uint32_t start = millis();
    while ((millis() - start) < ms) {
        /* 忙等，但单位是"毫秒"而不是"循环圈数"——这才与时钟解耦 */
    }
}

/* ============================ 板上资源 ============================ */

static void led_init(void)
{
    /* GPIOFEN = RCC_AHB1ENR bit5（RCC_AHB1ENR + 0x30，CMSIS 头文件同款定义） */
    *(volatile uint32_t *)(RCC_BASE + 0x30UL) |= (1UL << 5);

    GPIOF_MODER &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_MODER |=  (1UL << (LED_R_PIN * 2));      /* 01 = 通用输出 */
    GPIOF_BSRR  =  (1UL << (LED_R_PIN + 16));     /* 初始输出低 → 亮 */
}

static void led_set(uint32_t on)
{
    GPIOF_BSRR = on ? (1UL << (LED_R_PIN + 16)) : (1UL << LED_R_PIN);
}

/** MCO1：把内部时钟引到引脚上，这是"不可见的时钟"变可见的最短路径。
 *  这里选 /4：168/4 = 42MHz，示波器量起来轻松，量到的数乘以 4 就是 SYSCLK。
 *
 *  编码陷阱：MCO1PRE[2:0] 不是"分频比 − 1"，而是
 *    0xx = 不分频, 100 = /2, 101 = /3, 110 = /4, 111 = /5
 *  （ST 官方 HAL 头文件 RCC_MCODIV_1..5 = 0/4/5/6/7，stm32f4xx_hal_rcc.h:314-318 @1f6451c）。
 *  想当然写 div−1 的话，/4 会得到 0b011——落进"不分频"区，PA8 直接吐 168MHz，
 *  对账结论整个作废。这张显式映射表就是防呆。 */
static uint32_t mco1_pre_for(uint32_t sysclk_hz)
{
    static const struct { uint32_t div; uint32_t pre; } mco_pre[] = {
        { 1U, 0U }, { 2U, 4U }, { 3U, 5U }, { 4U, 6U }, { 5U, 7U },
    };
    uint32_t div = 1UL;
    uint32_t pre = 0UL;

    while ((sysclk_hz / div) > 42000000UL) { div++; }   /* 目标 ≈42MHz */

    for (uint32_t i = 0; i < sizeof mco_pre / sizeof mco_pre[0]; i++) {
        if (mco_pre[i].div == div) { pre = mco_pre[i].pre; break; }
    }
    return pre;
}

static void mco1_init(uint32_t sysclk_hz)
{
    const uint32_t pre = mco1_pre_for(sysclk_hz);

    RCC_CFGR = (RCC_CFGR & ~RCC_CFGR_MCO1PRE) | (pre << 24);

    /* GPIOA 使能在 RCC_AHB1ENR bit0 */
    *(volatile uint32_t *)(RCC_BASE + 0x30UL) |= (1UL << 0);
    GPIOA_MODER &= ~(3UL << (MCO1_PIN * 2));
    GPIOA_MODER |=  (1UL << (MCO1_PIN * 2));          /* 通用输出 */
    GPIOA_AFRH  &= ~(0xFUL << ((MCO1_PIN - 8U) * 4U));
    GPIOA_AFRH  |=  (0x0UL << ((MCO1_PIN - 8U) * 4U)); /* AF0 = MCO1 */
}

/** 电压范围分档的等待周期表（RM0090 Rev 18 Table 10，VDD 与 HCLK 的组合）。
 *  常见开发板 VDD=3.3V，落在 2.7~3.6V 这一列；
 *  2.4~2.7V 那一列留给低压供电的板子——同一颗芯片、同样的 168MHz，
 *  电压低一档就要多等一个周期。列错了就是随机 HardFault，而不是"稳定地跑慢"。 */
static uint32_t flash_latency_ws_3v3(uint32_t sysclk_hz)
{
    static const uint32_t ws_limit_mhz[] = { 30, 60, 90, 120, 150, 168 };
    const uint32_t mhz = sysclk_hz / 1000000UL;

    for (uint32_t i = 0; i < sizeof ws_limit_mhz / sizeof ws_limit_mhz[0]; i++) {
        if (mhz <= ws_limit_mhz[i]) {
            return i;
        }
    }
    return sizeof ws_limit_mhz / sizeof ws_limit_mhz[0] - 1U;  /* 超表尾取最保守值 */
}

/** VOS 只决定 HCLK 的天花板，不决定等待周期：
 *  RM0090 注明 F405/407 在 VOS='0' 时 fHCLK 上限 144MHz，VOS='1' 时 168MHz。
 *  所以"能不能跑 168MHz"要先过电压档这一关，再谈等待周期。 */
static void flash_config(uint32_t sysclk_hz, uint32_t need_scale1)
{
    if (need_scale1 && sysclk_hz > 144000000UL) {
        PWR_CR |= PWR_CR_VOS;        /* Scale 1：解锁 168MHz 的必要条件。
                                          F405/407 没有 VOSRDY 就绪位（那是 F42x/43x 的）——
                                          VOS 是普通 RW 配置位，写完即生效，没有可等待的回执；
                                          轮询它只会读回刚写入的 1，纯属误导。 */
    }

    FLASH_ACR &= ~FLASH_ACR_LATENCY;
    FLASH_ACR |= flash_latency_ws_3v3(sysclk_hz);
    FLASH_ACR |= FLASH_ACR_PRFTEN;   /* 预取：顺序取指时提前搬运下一条 */
}



/* ============================ PLL 与系统时钟 ============================ */

/** 由晶振频率算出 M/N/P/Q。约束全部来自 RM0090 Rev 18 的 RCC_PLLCFGR 说明：
 *    - PLLM ∈ [2, 63]，且必须让 VCO 输入落在 1~2MHz（原文推荐 2MHz 以压低抖动；
 *      本工程默认取 1MHz，也就是 8MHz 晶振时最常见的 M=8/N=336 组合）
 *    - PLLN ∈ [50, 432]，且 VCO 输出必须在 100~432MHz
 *    - PLLP 取 /2（位域 00）或 /4（01）
 *    - PLLQ ∈ [2, 15]，VCO/PLLQ 必须正好 48MHz 才是可用的 USB OTG FS 时钟
 *  8MHz 例：M=8 → VCO 输入 1MHz；N=336 → VCO 336MHz；P=2 → SYSCLK 168MHz；
 *            Q=7 → 48MHz。
 *  换成 2MHz 输入的写法是 M=4、N=168（VCO 仍 336MHz），其余不变。 */
static int pll_params_from_hse(uint32_t hse_hz, uint32_t *m, uint32_t *n,
                               uint32_t *p, uint32_t *q)
{
    uint32_t mm = hse_hz / VCO_INPUT_HZ;

    if (mm < 2UL) {
        mm = 2UL;                    /* PLLM 下限是 2 */
    }
    if (mm > 63UL) {
        return -1;                   /* 晶振太高，本工程这套参数不够用 */
    }
    if ((hse_hz % VCO_INPUT_HZ) != 0UL) {
        return -2;                   /* 整除不了就得不到干净的 1MHz */
    }

    *m = mm;
    *n = 336UL;                      /* 1MHz × 336 = 336MHz VCO */
    *p = 2UL;
    *q = 7UL;                        /* 336 / 7 = 48MHz，专供 USB OTG FS */
    return 0;
}

/** 回读 CFGR，把硬件实际生效的时钟树解出来。
 *  为什么要回读：位写错了、芯片复位了、外设还锁着——只有读回来的值算数。 */
static void clock_tree_readback(uint32_t hsi_hz)
{
    /* RM0090 Rev 18 对 CFGR[7:4] HPRE 的定义：0xxx=/1、1000=/2、1001=/4、1010=/8、
     * 1011=/16、1100=/64、1101=/128、1110=/256、1111=/512。
     * 注意 F4 没有 /32：把索引 12 写成 32 会让 /64 的配置静默算错。 */
    static const uint16_t hpre_div[] = { 1,1,1,1,1,1,1,1,2,4,8,16,64,128,256,512 };
    /* CFGR[12:10] PPRE1 / [15:13] PPRE2：0xx=/1、100=/2、101=/4、110=/8、111=/16。
     * 表长必须按 3 位来：HPRE 是 4 位、PPRE 是 3 位，照 HPRE 那样开 16 格，
     * 索引最大只到 7，/2 /4 /8 /16 全落在前八格的 1 上——APB 分频被静默读成 /1，
     * 定时器 ×2 那条也会跟着算出 336MHz 这种不存在的数。 */
    static const uint16_t ppre_div[] = { 1,1,1,1,2,4,8,16 };

    uint32_t cfgr    = RCC_CFGR;
    uint32_t pllcfgr = RCC_PLLCFGR;
    uint32_t src;

    if ((cfgr & RCC_CFGR_SWS) == RCC_CFGR_SWS_PLL) {
        uint32_t m =  pllcfgr & 0x3FUL;
        uint32_t n = (pllcfgr >> 6) & 0x1FFUL;
        uint32_t p = ((pllcfgr >> 16) & 0x3UL) ? 4UL : 2UL;
        src = ((pllcfgr & RCC_PLLCFGR_PLLSRC) ? HSE_VALUE_HZ : hsi_hz) / m * n / p;
    } else {
        src = hsi_hz;
    }

    g_clock_tree[0] = src;                                    /* SYSCLK */
    g_clock_tree[1] = src / hpre_div[(cfgr & RCC_CFGR_HPRE)  >> 4];   /* HCLK  */
    g_clock_tree[2] = g_clock_tree[1] / ppre_div[(cfgr & RCC_CFGR_PPRE1) >> 10]; /* PCLK1 */
    g_clock_tree[3] = g_clock_tree[1] / ppre_div[(cfgr & RCC_CFGR_PPRE2) >> 13]; /* PCLK2 */
    /* 隐藏规则：APBx 预分频≠1 时，定时器时钟 = PCLK×2 */
    g_clock_tree[4] = ((cfgr & RCC_CFGR_PPRE1) >> 10) ? g_clock_tree[2] * 2UL
                                                      : g_clock_tree[2];

    SystemCoreClock = g_clock_tree[1];
}

/** 完整提频流程。返回 0 成功切到 PLL，非 0 表示回退到 HSI。 */
static int clock_init(void)
{
    const uint32_t hsi_hz = 16000000UL;
    uint32_t m, n, p, q;

    g_clock_status = 0;

    if (USE_HSE_PLL == 0) {
        SystemCoreClock = hsi_hz;
        g_clock_tree[0] = hsi_hz; g_clock_tree[1] = hsi_hz;
        g_clock_tree[2] = hsi_hz; g_clock_tree[3] = hsi_hz;
        g_clock_tree[4] = hsi_hz;
        return 0;
    }

    if (pll_params_from_hse(HSE_VALUE_HZ, &m, &n, &p, &q) != 0) {
        g_clock_status = 2;                /* 参数与晶振不匹配，别硬切 */
        SystemCoreClock = hsi_hz;
        return -1;
    }
    g_pll_m = m; g_pll_n = n; g_pll_p = p; g_pll_q = q;

    /* 第 1 步：电压档 + Flash 等待周期，必须在提速之前 */
    flash_config(SYSCLK_TARGET_HZ, 1UL);

    /* 第 2 步：开 HSE 并等就绪。晶振虚焊时 HSERDY 永远不来，必须带超时 */
    RCC_CR |= RCC_CR_HSEON;
    {
        uint32_t timeout = 0x00100000UL;
        while (((RCC_CR & RCC_CR_HSERDY) == 0UL) && (timeout-- != 0UL)) {
        }
        if ((RCC_CR & RCC_CR_HSERDY) == 0UL) {
            RCC_CR &= ~RCC_CR_HSEON;      /* 关掉没起来的晶振，省得白耗电 */
            g_clock_status = 1;            /* 回退 HSI，程序继续活着 */
            SystemCoreClock = hsi_hz;
            g_clock_tree[0] = hsi_hz; g_clock_tree[1] = hsi_hz;
            g_clock_tree[2] = hsi_hz; g_clock_tree[3] = hsi_hz;
            g_clock_tree[4] = hsi_hz;
            return -1;
        }
    }

    /* 第 3 步：配 PLL（先配参数，再开 PLL） */
    RCC_CR &= ~RCC_CR_PLLON;
    while (RCC_CR & RCC_CR_PLLRDY) { }     /* 等待 PLL 完全停下 */
    RCC_PLLCFGR = m
                | ((n & 0x1FFUL) << 6)
                | (((p == 4UL) ? 1UL : 0UL) << 16)
                | RCC_PLLCFGR_PLLSRC
                | ((q & 0xFUL) << 24);
    RCC_CR |= RCC_CR_PLLON;
    while ((RCC_CR & RCC_CR_PLLRDY) == 0UL) { }   /* 等 PLL 锁定 */

    /* 第 4 步：切 SYSCLK，然后读 SWS 确认硬件真的换了 */
    RCC_CFGR = (RCC_CFGR & ~RCC_CFGR_SW) | 0x2UL;   /* 10 = PLL */
    {
        uint32_t timeout = 0x00100000UL;
        while (((RCC_CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) && (timeout-- != 0UL)) {
        }
        if ((RCC_CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) {
            g_clock_status = 1;
            SystemCoreClock = hsi_hz;
            return -1;
        }
    }

    /* 第 5 步：总线分频。AHB=168，APB1 上限 42 → /4，APB2 上限 84 → /2 */
    RCC_CFGR = (RCC_CFGR & ~RCC_CFGR_HPRE)  | (0x0UL << 4);   /* AHB  = /1 */
    RCC_CFGR = (RCC_CFGR & ~RCC_CFGR_PPRE1) | (0x5UL << 10);  /* APB1 = /4 */
    RCC_CFGR = (RCC_CFGR & ~RCC_CFGR_PPRE2) | (0x4UL << 13);  /* APB2 = /2 */

    clock_tree_readback(hsi_hz);
    return 0;
}

/* ============================ main ============================ */

int main(void)
{
    led_init();

    const int rc = clock_init();
    clock_tree_readback(16000000UL);   /* 无论成功与否都以硬件实际值为准 */

    systick_init(g_clock_tree[1]);     /* 关键：用"实际的 HCLK"配 1ms 节拍 */
    mco1_init(g_clock_tree[0]);        /* PA8 输出 ≈42MHz */

    while (1) {
        if (rc == 0) {
            led_set(1); delay_ms(500);
            led_set(0); delay_ms(500);
        } else {
            /* 回退模式：连闪两下再停，肉眼就能和正常闪烁区分开 */
            for (int i = 0; i < 2; i++) {
                led_set(0); delay_ms(150);
                led_set(1); delay_ms(150);
            }
            delay_ms(600);
        }
    }
}