/*
 * S2 RCC 时钟树 —— 取证工程（不需要开发板）
 *
 * 这份文件不重写任何算术。它把固件的 main.c 整个 #include 进来，
 * 只把 RCC_CFGR / RCC_PLLCFGR 两个宏改指一组宿主假寄存器（main.c 里给这两个
 * 宏留了 #ifndef 口子），于是下面这些跑的都是板子上那一份代码：
 *
 *   pll_params_from_hse()   —— M/N/P/Q 怎么从晶振推出来、什么时候拒绝
 *   flash_latency_ws_3v3()  —— 3.3V 那一列的等待周期表
 *   clock_tree_readback()   —— 从 CFGR/PLLCFGR 反推真实时钟树（含定时器 ×2）
 *   mco1_pre_for()          —— MCO1 分频编码查表
 *
 * 第 6 节要跑两遍：同一份源码只改 -DHSE_VALUE_HZ，看"程序以为"和"板上实际"
 * 怎么在没有任何一行代码报错的情况下分家。probe.sh 负责跑这两遍。
 */

#include <stdio.h>
#include <stdint.h>

/* ---- 假寄存器：只有 clock_tree_readback() 会读它们 ---- */
static uint32_t g_fake_pllcfgr;
static uint32_t g_fake_cfgr;
#define RCC_PLLCFGR g_fake_pllcfgr
#define RCC_CFGR    g_fake_cfgr
#define main        firmware_main   /* 让位给宿主的 main */

#include "main.c"

#undef main   /* 上面那个 #define 只管固件的 main，本文件的 main 要还回来 */

/* 板上真正焊着的晶振。第 6 节故意让它和 HSE_VALUE_HZ 不相等。 */
#ifndef BOARD_HSE_HZ
#define BOARD_HSE_HZ 8000000UL
#endif

static int fails;

static void check(const char *what, uint32_t got, uint32_t want)
{
    if (got != want) {
        printf("  !! 断言失败：%s 期望 %u，实得 %u\n", what, want, got);
        fails++;
    }
}

/* 芯片侧的 PLL：完全按 RM0090 的位域定义把一个字拆开，不借 main.c 的宏，
 * 这样第 2 节"源码算出来的字"和"从这里解出来的数"互为独立验证。 */
static uint32_t pllcfgr_word(uint32_t m, uint32_t n, uint32_t p, uint32_t q)
{
    return (m & 0x3FUL) | ((n & 0x1FFUL) << 6)
         | ((((p == 4UL) ? 1UL : 0UL) & 3UL) << 16) | (1UL << 22)
         | ((q & 0xFUL) << 24);
}

/* 打印成 0b110 这种形式——编码陷阱只有写成二进制才看得出来 */
static const char *bin3(uint32_t v)
{
    static char s[4];
    for (int i = 0; i < 3; i++) s[i] = (char)('0' + ((v >> (2 - i)) & 1U));
    s[3] = '\0';
    return s;
}

/* MCO1PRE[2:0] 的真值：0xx=不分频、100=/2、101=/3、110=/4、111=/5 */
static uint32_t mco_div_of(uint32_t pre)
{
    if ((pre & 4UL) == 0UL) return 1UL;
    return pre - 2UL;
}

/* 第 1~5 节的断言都以"HSE_VALUE_HZ 填对了"为前提，所以错宏那一遍不跑它们。 */
static void probe_board_side(void)
{
    /* ================= 1. PLL 手算：一个都不能猜 ================= */
    puts("=== 1. pll_params_from_hse() 逐种晶振实跑 ===");
    printf("%-12s %-4s %-4s %-4s %-4s %-4s %-12s %-12s %-12s %s\n",
           "晶振Hz", "rc", "M", "N", "P", "Q", "VCO输入Hz", "VCO Hz", "SYSCLK Hz", "USB Hz");
    static const uint32_t crystals[] = {
        8000000UL, 25000000UL, 16000000UL, 12000000UL, 6000000UL,
        4000000UL, 11059200UL, 64000000UL,
    };
    uint32_t m8 = 0, n8 = 0, p8 = 0, q8 = 0;
    for (unsigned i = 0; i < sizeof crystals / sizeof crystals[0]; i++) {
        const uint32_t hz = crystals[i];
        uint32_t m = 0, n = 0, p = 0, q = 0;
        const int rc = pll_params_from_hse(hz, &m, &n, &p, &q);
        if (rc == 0) {
            printf("%-12lu %-4d %-4lu %-4lu %-4lu %-4lu %-12lu %-12lu %-12lu %lu\n",
                   (unsigned long)hz, rc, (unsigned long)m, (unsigned long)n,
                   (unsigned long)p, (unsigned long)q,
                   (unsigned long)(hz / m), (unsigned long)(hz / m * n),
                   (unsigned long)(hz / m * n / p), (unsigned long)(hz / m * n / q));
        } else {
            printf("%-12lu %-4d  拒绝：rc=%d（%s）\n", (unsigned long)hz, rc, rc,
                   rc == -1 ? "晶振太高，M 会溢出 6 位" : "整除不了 1MHz，得不到干净的参考");
        }
        if (hz == 8000000UL) { m8 = m; n8 = n; p8 = p; q8 = q; }
    }
    check("8MHz 的 M", m8, 8); check("8MHz 的 N", n8, 336);
    check("8MHz 的 P", p8, 2); check("8MHz 的 Q", q8, 7);
    check("11.0592MHz 被拒", (uint32_t)pll_params_from_hse(11059200UL, &m8, &n8, &p8, &q8), (uint32_t)-2);
    check("64MHz 被拒", (uint32_t)pll_params_from_hse(64000000UL, &m8, &n8, &p8, &q8), (uint32_t)-1);
    puts("");

    /* ================= 2. 四个数最后就是一个寄存器字 ================= */
    puts("=== 2. M/N/P/Q 打包成 RCC_PLLCFGR 那一个字 ===");
    const uint32_t word8 = pllcfgr_word(8, 336, 2, 7);
    printf("M=8 N=336 P=/2 SRC=HSE Q=7  →  0x%08lX\n", (unsigned long)word8);
    printf("  位段：M[5:0]=%lu  N[14:6]=%lu  P[17:16]=%lu  SRC[22]=%lu  Q[27:24]=%lu\n",
           (unsigned long)(word8 & 0x3FUL), (unsigned long)((word8 >> 6) & 0x1FFUL),
           (unsigned long)((word8 >> 16) & 3UL), (unsigned long)((word8 >> 22) & 1UL),
           (unsigned long)((word8 >> 24) & 0xFUL));
    /* 这个字必须等于 -O2 反汇编里 literal pool 的那一个词
     * （build/main.o 的 .word 0x07405408）——源码与机器码在这里对上。 */
    check("PLLCFGR 字 == 反汇编 literal", word8, 0x07405408UL);
    puts("");

    /* ================= 3. Flash 等待周期：3.3V 那一列 ================= */
    puts("=== 3. flash_latency_ws_3v3() 逐档实跑（RM0090 Table 10 的 2.7~3.6V 列）===");
    static const uint32_t mhz_list[] = { 16, 30, 31, 60, 61, 90, 120, 150, 151, 168 };
    for (unsigned i = 0; i < sizeof mhz_list / sizeof mhz_list[0]; i++) {
        const uint32_t hz = mhz_list[i] * 1000000UL;
        printf("  HCLK %3lu MHz → LATENCY = %lu WS\n",
               (unsigned long)mhz_list[i], (unsigned long)flash_latency_ws_3v3(hz));
    }
    check("168MHz 要 5WS", flash_latency_ws_3v3(168000000UL), 5);
    check("150MHz 是 4WS 的上沿", flash_latency_ws_3v3(150000000UL), 4);
    check("151MHz 已经越界", flash_latency_ws_3v3(151000000UL), 5);
    puts("");

    /* ================= 4. 回读 CFGR：定时器那条隐藏规则 ================= */
    puts("=== 4. clock_tree_readback() 从寄存器反推（真代码，假寄存器）===");
    /* 提频完成后的 CFGR：SWS=10(PLL)、HPRE=/1、PPRE1=101(/4)、PPRE2=100(/2) */
    g_fake_pllcfgr = word8;
    g_fake_cfgr = RCC_CFGR_SWS_PLL | (0x5UL << 10) | (0x4UL << 13);
    clock_tree_readback(16000000UL);
    printf("  SYSCLK=%lu  HCLK=%lu  PCLK1=%lu  PCLK2=%lu  TIM2CLK=%lu\n",
           (unsigned long)g_clock_tree[0], (unsigned long)g_clock_tree[1],
           (unsigned long)g_clock_tree[2], (unsigned long)g_clock_tree[3],
           (unsigned long)g_clock_tree[4]);
    printf("  PPRE1=/4 → 定时器时钟 = PCLK1 × %lu\n",
           (unsigned long)(g_clock_tree[4] / g_clock_tree[2]));
    check("SYSCLK", g_clock_tree[0], 168000000UL);
    check("HCLK", g_clock_tree[1], 168000000UL);
    check("PCLK1", g_clock_tree[2], 42000000UL);
    check("PCLK2", g_clock_tree[3], 84000000UL);
    check("TIM2CLK", g_clock_tree[4], 84000000UL);
    /* 对照：APB1 不分频时 ×2 规则不触发 */
    g_fake_cfgr = RCC_CFGR_SWS_PLL | (0x0UL << 10) | (0x4UL << 13);
    clock_tree_readback(16000000UL);
    printf("  把 PPRE1 改回 /1：PCLK1=%lu  TIM2CLK=%lu（×%lu，规则不触发）\n",
           (unsigned long)g_clock_tree[2], (unsigned long)g_clock_tree[4],
           (unsigned long)(g_clock_tree[4] / g_clock_tree[2]));
    check("/1 时定时器不乘二", g_clock_tree[4], 168000000UL);
    puts("");

    /* ---- 4b. 这一节是修出来的 bug：表长按 4 位开，索引却只有 3 位 ---- */
    puts("=== 4b. PPRE 表如果照 HPRE 开 16 格（本仓库改之前的写法）===");
    static const uint16_t ppre_wrong[] = { 1,1,1,1,1,1,1,1,2,4,8,16,16,16,16,16 };
    static const uint16_t ppre_right[] = { 1,1,1,1,2,4,8,16 };
    printf("  %-8s %-14s %s\n", "PPRE 字段", "16 格表（旧）", "8 格表（现）");
    for (uint32_t f = 0; f < 8; f++) {
        printf("  0b%s     /%-13lu /%-13lu%s\n", bin3(f),
               (unsigned long)ppre_wrong[f], (unsigned long)ppre_right[f],
               (f >= 4 && ppre_wrong[f] == 1UL) ? "   ← 分频被静默读成 /1" : "");
    }
    check("旧表在 /4 档读成 1", ppre_wrong[5], 1);
    check("新表在 /4 档读成 4", ppre_right[5], 4);
    puts("");

    /* ================= 5. MCO1PRE：想当然按"分频比 − 1"写 ================= */
    puts("=== 5. mco1_pre_for() 与 MCO1PRE 编码陷阱 ===");
    const uint32_t pre = mco1_pre_for(168000000UL);
    printf("  SYSCLK 168MHz → 目标 ≤42MHz → div=4 → 正确写法 pre=0b%s（%lu），PA8 = %lu Hz\n",
           bin3(pre), (unsigned long)pre,
           (unsigned long)(168000000UL / mco_div_of(pre)));
    const uint32_t naive = 4UL - 1UL;
    printf("  按 div-1 想当然写 pre=0b%s（%lu）→ 落进 0xx 区 → div=%lu → PA8 = %lu Hz\n",
           bin3(naive), (unsigned long)naive,
           (unsigned long)mco_div_of(naive), (unsigned long)(168000000UL / mco_div_of(naive)));
    printf("  你还以为 PA8 是 /4，于是把示波器读数乘 4：%lu Hz —— 对账结论凭空多出 %lu MHz\n",
           (unsigned long)(168000000UL / mco_div_of(naive) * 4UL),
           (unsigned long)((168000000UL / mco_div_of(naive) * 4UL - 168000000UL) / 1000000UL));
    check("正确编码是 6", pre, 6);
    check("正确编码分 4", mco_div_of(6), 4);
    check("div-1 的 3 其实不分频", mco_div_of(3), 1);
    puts("");

}

/* ================= 6. 只有一个宏填错了 ================= */
static void probe_macro_mismatch(void)
{
    puts("=== 6. HSE_VALUE_HZ 与真实晶振不符：程序一声不吭 ===");
    uint32_t mm, nn, pp, qq;
    const int rc6 = pll_params_from_hse(HSE_VALUE_HZ, &mm, &nn, &pp, &qq);
    check("第 6 节参数可算", (uint32_t)rc6, 0U);
    g_fake_pllcfgr = pllcfgr_word(mm, nn, pp, qq);
    g_fake_cfgr = RCC_CFGR_SWS_PLL | (0x5UL << 10) | (0x4UL << 13);
    clock_tree_readback(16000000UL);
    const uint32_t belief = g_clock_tree[0];
    const uint32_t reality = BOARD_HSE_HZ / mm * nn / pp;
    printf("  程序写入 PLLCFGR：M=%lu N=%lu P=/%lu Q=%lu → 0x%08lX\n",
           (unsigned long)mm, (unsigned long)nn, (unsigned long)pp,
           (unsigned long)qq, (unsigned long)g_fake_pllcfgr);
    printf("  程序以为 SYSCLK = %lu Hz（g_clock_tree[0]，回读算出来的）\n",
           (unsigned long)belief);
    printf("  板上晶振 %lu Hz，硅片真的按 M=%lu 分：VCO 输入 = %lu Hz（芯片要求 1~2MHz）\n",
           (unsigned long)BOARD_HSE_HZ, (unsigned long)mm,
           (unsigned long)(BOARD_HSE_HZ / mm));
    printf("  引脚上实际 = %lu Hz；USB 那一路实际 = %lu Hz（要 48MHz）\n",
           (unsigned long)reality, (unsigned long)(BOARD_HSE_HZ / mm * nn / qq));
    /* 这里不写死"0 条错误"：报的是固件那个函数自己的返回值。
     * rc=0 就是它口中的"一切正常"——差 114MHz 也照样返回正常，这才是本节的看点。 */
    printf("  差 %lu Hz；pll_params_from_hse() 返回值 = %d（0 = 程序认为一切正常）\n",
           (unsigned long)(belief - reality), rc6);
    if (BOARD_HSE_HZ == HSE_VALUE_HZ) {
        check("晶振填对时两者相等", belief, reality);
    } else {
        check("填错时程序仍以为 168MHz", belief, 168000000UL);
        check("填错时实际是 53.76MHz", reality, 53760000UL);
    }
    puts("");
}

int main(int argc, char **argv)
{
    printf("HSE_VALUE_HZ（程序以为的晶振）= %lu Hz\n", (unsigned long)HSE_VALUE_HZ);
    printf("BOARD_HSE_HZ （板上实际焊的）  = %lu Hz\n\n", (unsigned long)BOARD_HSE_HZ);
    /* probe.exe 6 → 只跑第 6 节：错宏那一遍里，第 1~5 节的断言前提不成立 */
    if (!(argc > 1 && argv[1][0] == '6')) probe_board_side();
    probe_macro_mismatch();
    printf(fails ? "断言 %d 条失败\n" : "断言全绿\n", fails);
    return fails ? 1 : 0;
}
