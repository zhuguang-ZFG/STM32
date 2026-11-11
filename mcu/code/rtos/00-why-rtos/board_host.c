/*
 * board_host.c —— 宿主机那一层：一把高精度时钟 + 一张事件脚本表
 *
 * 为什么不用线程、不用真实串口：字节到达时刻与按键按下/松开时刻全部由脚本决定，
 * 于是"阻塞版"和"改良版"跑的是同一条剧情，两边的数字可以并排比。
 * 时钟只要一把单调纳秒表：Windows 用 QueryPerformanceCounter，POSIX 用
 * clock_gettime(CLOCK_MONOTONIC)——1 ms 的 SysTick 读数都由它换算，粒度真实。
 * 发送用线上速率记账：115200 8N1 一个字符 10 bit → 86.805 µs，谁也快不了。
 *
 * 打印全部攒到报告阶段：跑循环的时候一个字符都不往 stdout 写，
 * 否则终端 I/O 会把要量的东西量歪。
 */
#if !defined(_WIN32)
/* 必须抢在任何一个系统头文件之前：glibc 的 features.h 在第一次 include 就定好了
   暴露哪些符号，而 probe 用 -std=c11（=__STRICT_ANSI__）会把 clock_gettime 藏起来。 */
#define _POSIX_C_SOURCE 199309L
#endif

#include "superloop.h"
#include "board_host.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RUN_END_MS  6000u        /* 脚本放完的时刻，也是本局的终点 */
#define TX_CHAR_NS  86805LL      /* 10 bit ÷ 115200 bit/s = 86.805 µs/字符 */

/* ---------------- 时钟 ---------------- */

#if defined(_WIN32)

#include <windows.h>

static LARGE_INTEGER s_qpc_freq;

static void clock_init(void)
{
    QueryPerformanceFrequency(&s_qpc_freq);
}

/* 绝对纳秒：只问 QPC，不做任何平移 */
static long long clock_ns(void)
{
    LARGE_INTEGER c;

    QueryPerformanceCounter(&c);
    return (long long)((double)c.QuadPart * 1e9 / (double)s_qpc_freq.QuadPart);
}

#else

#include <time.h>

static void clock_init(void) {}

static long long clock_ns(void)
{
    struct timespec ts;

    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

#endif

static long long     s_t0_ns;

/* 本局纳秒：一局从 0 起算，所以 host_run_begin 换局时各局的剧情时刻完全对齐 */
static long long now_ns(void)
{
    return clock_ns() - s_t0_ns;
}

uint32_t board_tick_ms(void)
{
    return (uint32_t)(now_ns() / 1000000);
}

/* ---------------- 事件脚本 ---------------- */

#define RX_MAX  64                       /* 12 + 换行 + 40 + 换行 + 哨兵 */
#define KEY_MAX  8
#define ECHO_MAX 8
#define FLIP_MAX 64
#define EDGE_MAX 8

typedef struct { uint32_t at_ms; char ch; } rx_ev_t;
typedef struct { uint32_t from_ms; uint32_t to_ms; const char *what; } key_ev_t;

static rx_ev_t  s_rx[RX_MAX];
static int      s_rx_n, s_rx_i;
static key_ev_t s_key[KEY_MAX];
static int      s_key_n;

static void rx_add(uint32_t at_ms, char ch)
{
    if (s_rx_n >= RX_MAX) {
        fprintf(stderr, "脚本超了：RX_MAX=%d 装不下\n", RX_MAX);
        exit(2);
    }
    s_rx[s_rx_n].at_ms = at_ms;
    s_rx[s_rx_n].ch = ch;
    s_rx_n++;
}

static void key_add(uint32_t from_ms, uint32_t to_ms, const char *what)
{
    if (s_key_n >= KEY_MAX) {
        fprintf(stderr, "脚本超了：KEY_MAX=%d 装不下\n", KEY_MAX);
        exit(2);
    }
    s_key[s_key_n].from_ms = from_ms;
    s_key[s_key_n].to_ms = to_ms;
    s_key[s_key_n].what = what;
    s_key_n++;
}

/*
 * 剧情（两个模式一字不差）：
 *   600–875   打出 "hello world!"，每 25 ms 一个字节
 *   900       回车 → 回显这 12 个字符（1.04 ms）
 *   702–717   短按一下（15 ms，故意落在字节流中间）
 *   1000–4300 长按 3.3 s —— 而 901 之后再也没有字节进来
 *   4200–5175 再来 40 个 'A'，仍 25 ms 一个
 *   5498      回车 → 回显 40 个字符（3.47 ms），正好盖住 5500 那次到点的翻灯
 *   5499      再短按一下（故意落在回显发送里）
 *   6000      哨兵：死等的在这里醒来，本局收工
 */
static void script_build(void)
{
    const char *line = "hello world!";

    for (int i = 0; line[i] != '\0'; i++) {
        rx_add(600u + 25u * (uint32_t)i, line[i]);
    }
    rx_add(900u, '\n');
    for (int i = 0; i < 40; i++) {
        rx_add(4200u + 25u * (uint32_t)i, 'A');
    }
    rx_add(5498u, '\n');
    rx_add(RUN_END_MS, '\0');            /* 哨兵：不是数据，只是叫醒死等的人 */

    key_add(702u, 717u, "短按 15 ms（落在字节流里）");
    key_add(1000u, 4300u, "长按 3.3 s（这期间一个字节都没有）");
    key_add(5499u, 5514u, "短按 15 ms（落在回显发送里）");
}

/* ---------------- 串口：收 = 查脚本时刻，发 = 按线上速率耗时间 ---------------- */

static unsigned long s_rx_bytes;
static unsigned long s_tx_bytes;
static long long     s_tx_ns;

static struct { long long at_ns; char text[64]; uint16_t len; } s_echo[ECHO_MAX];
static int s_echo_n;

static int rx_due(void)
{
    if (s_rx_i >= s_rx_n) {
        return 1;                        /* 脚本放完：别把循环焊死在这里 */
    }
    return now_ns() >= (long long)s_rx[s_rx_i].at_ms * 1000000;
}

int board_uart_rx_ready(void)
{
    return rx_due();
}

char board_uart_read_byte(void)
{
    char c;

    if (s_rx_i >= s_rx_n) {
        return '\0';
    }
    c = s_rx[s_rx_i].ch;
    s_rx_i++;
    if (c != '\0') {
        s_rx_bytes++;
    }
    return c;
}

char board_uart_getc(void)
{
    while (!rx_due()) {
        /* 死等 RXNE：章节里点名的那一行 while */
    }
    return board_uart_read_byte();
}

void board_uart_write(const char *s, uint16_t n)
{
    long long t0 = now_ns();
    long long deadline = t0;

    for (uint16_t i = 0u; i < n; i++) {
        deadline += TX_CHAR_NS;
        while (now_ns() < deadline) {
            /* 等 TXE：线上速率就这么多，代码写再快也没用 */
        }
    }
    s_tx_bytes += n;
    s_tx_ns += now_ns() - t0;

    if (s_echo_n < ECHO_MAX && n < sizeof s_echo[0].text) {
        memcpy(s_echo[s_echo_n].text, s, n);
        s_echo[s_echo_n].text[n] = '\0';
        s_echo[s_echo_n].at_ns = t0;
        s_echo[s_echo_n].len = n;
        s_echo_n++;
    }
}

/* ---------------- 按键：电平查脚本窗口，顺手记下"软件看见的按下沿" ---------------- */

static int       s_key_reported_down;
static long long s_edge_ns[EDGE_MAX];
static int       s_edge_n;

int board_key_down(void)
{
    uint32_t ms = board_tick_ms();
    int down = 0;

    for (int i = 0; i < s_key_n; i++) {
        if (ms >= s_key[i].from_ms && ms < s_key[i].to_ms) {
            down = 1;
        }
    }
    if (down && !s_key_reported_down && s_edge_n < EDGE_MAX) {
        s_edge_ns[s_edge_n++] = now_ns();
    }
    s_key_reported_down = down;
    return down;
}

/* ---------------- LED ---------------- */

static long long s_flip_ns[FLIP_MAX];
static int       s_flip_n;

void board_led_set(int on)
{
    (void)on;   /* 翻转就是翻转：灭的那一半同样是"灯按时眨了一下" */
    if (s_flip_n < FLIP_MAX) {
        s_flip_ns[s_flip_n++] = now_ns();
    }
}

void board_led2_toggle(void)
{
    /* 第二颗灯只是 key_scan 的"我看见了"的信号，本局不统计它 */
}

/* ---------------- 单圈计时与直方图 ---------------- */

static unsigned long s_pass_n;
static long long     s_pass_min_ns, s_pass_max_ns, s_pass_sum_ns;
static long long     s_pass_t0;

/* 桶宽覆盖 1 µs 到 1 s 以上：阻塞版的 3.3 s 和最省的那一圈要能同时装下 */
#define BUCKET_N 12
static const long long   bucket_hi[BUCKET_N] = {
    1000, 2000, 5000, 10000, 50000, 100000, 500000, 1000000,
    5000000, 50000000, 500000000, 0            /* 0 = 兜底桶 */
};
static const char *const bucket_label[BUCKET_N] = {
    "<1", "1–2", "2–5", "5–10", "10–50", "50–100", "100–500", "500–1000",
    "1k–5k", "5k–50k", "50k–500k", ">=500k"
};
static unsigned long s_bucket[BUCKET_N];

void host_pass_begin(void)
{
    s_pass_t0 = now_ns();
}

/*
 * 一段"跑不掉的活"：章里第三节说 key_scan 的响应时间等于"排在它前面所有任务本次耗时之和"。
 * 这一坨就是那个"前面的人"——2 ms 的批量采样，摆在哪一行，按键就迟到多少。
 */
void host_burn_us(uint32_t us)
{
    long long until = now_ns() + (long long)us * 1000LL;

    while (now_ns() < until) {
        /* 忙等：没有中断、没有 RTOS，谁也抢不走这一圈 */
    }
}

void host_pass_end(void)
{
    long long d = now_ns() - s_pass_t0;

    if (s_pass_n == 0 || d < s_pass_min_ns) {
        s_pass_min_ns = d;
    }
    if (d > s_pass_max_ns) {
        s_pass_max_ns = d;
    }
    s_pass_sum_ns += d;
    s_pass_n++;

    for (int i = 0; i < BUCKET_N; i++) {
        if (bucket_hi[i] == 0 || d < bucket_hi[i]) {
            s_bucket[i]++;
            break;
        }
    }
}

/* ---------------- 报告 ---------------- */

void host_init(void)
{
    clock_init();
    script_build();
    host_run_begin();
}

/*
 * 开新局：整局时间轴重零，剧情指针退回第一个字节。
 * s_rx / s_key 两张剧本表是只读的，所以跨局完全一致，只有真实耗时每局不同。
 */
void host_run_begin(void)
{
    s_t0_ns = clock_ns();

    s_rx_i = 0;
    s_rx_bytes = 0;
    s_tx_bytes = 0;
    s_tx_ns = 0;
    s_echo_n = 0;

    s_key_reported_down = 0;
    s_edge_n = 0;
    s_flip_n = 0;

    s_pass_n = 0;
    s_pass_min_ns = 0;
    s_pass_max_ns = 0;
    s_pass_sum_ns = 0;
    for (int i = 0; i < BUCKET_N; i++) {
        s_bucket[i] = 0;
    }
}

/* 脚本里第 i 个键，软件侧采到的时刻；-1 = 这一局压根没采到（丢了） */
static long long key_hit_ns(int i)
{
    for (int e = 0; e < s_edge_n; e++) {
        long long ms = s_edge_ns[e] / 1000000;

        if (ms >= (long long)s_key[i].from_ms && ms < (long long)s_key[i].to_ms) {
            return s_edge_ns[e];
        }
    }
    return -1;
}

/* 翻灯间隔的三个读数：报告与跨局统计都从这里取，两边口径必须一致 */
static void flip_span(long long *min_iv, long long *max_iv, int *overdue)
{
    *min_iv = 0;
    *max_iv = 0;
    *overdue = 0;
    for (int i = 1; i < s_flip_n; i++) {
        long long iv = s_flip_ns[i] - s_flip_ns[i - 1];

        if (i == 1 || iv < *min_iv) {
            *min_iv = iv;
        }
        if (iv > *max_iv) {
            *max_iv = iv;
        }
        if (iv > 550000000LL) {
            (*overdue)++;
        }
    }
}

/* 本局结算：一个键都没漏时最坏迟到是最大迟到，漏了一个就按一整圈的上界算 */
typedef struct {
    long long worst_late_ns;
    long long pass_max_ns;
    long long flip_max_iv_ns;
    int       lost_keys;
    int       overdue_flips;
    int       flips;
    unsigned long pass_n;
} run_stats_t;

static run_stats_t s_rep[HOST_REPS_MAX];
static int         s_rep_n;

static run_stats_t run_measure(void)
{
    run_stats_t st;
    long long min_iv, max_iv;

    flip_span(&min_iv, &max_iv, &st.overdue_flips);
    st.flips = s_flip_n;
    st.pass_n = s_pass_n;
    st.flip_max_iv_ns = max_iv;

    st.worst_late_ns = 0;
    st.lost_keys = 0;
    for (int i = 0; i < s_key_n; i++) {
        long long hit = key_hit_ns(i);

        if (hit < 0) {
            st.lost_keys++;
            st.worst_late_ns = s_pass_max_ns;   /* 丢键 = 迟到超过一整圈，按上界算 */
        } else {
            long long late = hit - (long long)s_key[i].from_ms * 1000000;

            if (late > st.worst_late_ns) {
                st.worst_late_ns = late;
            }
        }
    }
    st.pass_max_ns = s_pass_max_ns;
    return st;
}

void host_measure(void)
{
    if (s_rep_n < HOST_REPS_MAX) {
        s_rep[s_rep_n++] = run_measure();
    }
}

/* 小数组取中位：先排序副本，偶数局取中间两个的平均；返回原始值，单位由调用方换算 */
static double median_raw(long long *v, int n)
{
    long long a[HOST_REPS_MAX];
    long long t;

    if (n <= 0) {
        return 0.0;
    }
    for (int i = 0; i < n; i++) {
        a[i] = v[i];
    }
    for (int i = 1; i < n; i++) {
        for (int j = i; j > 0 && a[j - 1] > a[j]; j--) {
            t = a[j - 1];
            a[j - 1] = a[j];
            a[j] = t;
        }
    }
    if (n % 2 == 1) {
        return (double)a[n / 2];
    }
    return ((double)a[n / 2 - 1] + (double)a[n / 2]) / 2.0;
}

static long long rep_stat(const run_stats_t *st, int field)
{
    switch (field) {
    case 1:  return st->pass_max_ns;
    case 2:  return st->flip_max_iv_ns;
    case 3:  return st->flips;
    case 4:  return (long long)st->pass_n;
    default: return st->worst_late_ns;
    }
}

/* 从 s_rep 里挑一个字段，打跨局的 min / 中位 / max */
static void summary_pick(const char *label, const char *unit, int field, int is_ns)
{
    long long v[HOST_REPS_MAX];
    long long lo = 0, hi = 0;

    for (int i = 0; i < s_rep_n; i++) {
        long long x = rep_stat(&s_rep[i], field);

        v[i] = x;
        if (i == 0 || x < lo) {
            lo = x;
        }
        if (x > hi) {
            hi = x;
        }
    }
    if (is_ns) {
        printf("  %-12s %s：min %.2f / 中位 %.2f / max %.2f\n",
               label, unit, (double)lo / 1e6, median_raw(v, s_rep_n) / 1e6, (double)hi / 1e6);
    } else {
        printf("  %-12s %s：min %.0f / 中位 %.0f / max %.0f\n",
               label, unit, (double)lo, median_raw(v, s_rep_n), (double)hi);
    }
}

void host_summary(const char *mode_name)
{
    int lost_runs = 0;
    int overdue_runs = 0;

    for (int i = 0; i < s_rep_n; i++) {
        if (s_rep[i].lost_keys > 0) {
            lost_runs++;
        }
        if (s_rep[i].overdue_flips > 0) {
            overdue_runs++;
        }
    }
    printf("\n---- 跨 %d 局统计（同一档连跑 %d 遍，宿主机上的数只能这样看）----\n",
           s_rep_n, s_rep_n);
    printf("  %s\n", mode_name);
    summary_pick("最坏迟到", "ms", 0, 1);
    summary_pick("最长单圈", "ms", 1, 1);
    summary_pick("最长翻灯间隔", "ms", 2, 1);
    summary_pick("LED 翻转", "次", 3, 0);
    summary_pick("超级循环", "圈", 4, 0);
    printf("  丢过键的局：%d / %d；翻灯迟到 >550 ms 的局：%d / %d\n",
           lost_runs, s_rep_n, overdue_runs, s_rep_n);
}

int host_done(void)
{
    return board_tick_ms() >= RUN_END_MS;
}

void host_print_script(void)
{
    printf("---- 事件脚本（两个模式共用，1 ms 网格）----\n");
    printf("  接收：");
    for (int i = 0; i < s_rx_n; i++) {
        if (s_rx[i].ch == '\0') {
            printf(" %u=哨兵", s_rx[i].at_ms);
        } else if (s_rx[i].ch == '\n') {
            printf(" %u=CR", s_rx[i].at_ms);
        } else {
            printf(" %u=%c", s_rx[i].at_ms, s_rx[i].ch);
        }
        if (i == 13 || i == 42) {
            printf("\n         ");
        }
    }
    printf("\n");
    for (int i = 0; i < s_key_n; i++) {
        printf("  按键：%u–%u ms  %s\n", s_key[i].from_ms, s_key[i].to_ms, s_key[i].what);
    }
    printf("  发送：115200 8N1 → %.3f µs/字符；本局跑满 %u ms 后收工\n",
           (double)TX_CHAR_NS / 1000.0, RUN_END_MS);
    printf("\n");
}

static void report_passes(void)
{
    unsigned long half = (s_pass_n + 1) / 2;
    unsigned long acc = 0;
    const char *median_bucket = "?";

    printf("超级循环：%lu 圈\n", s_pass_n);
    printf("  单圈 µs：min %.2f / max %.2f / 平均 %.2f\n",
           (double)s_pass_min_ns / 1000.0,
           (double)s_pass_max_ns / 1000.0,
           (double)s_pass_sum_ns / (double)s_pass_n / 1000.0);
    for (int i = 0; i < BUCKET_N; i++) {
        if (s_bucket[i] == 0) {
            continue;
        }
        acc += s_bucket[i];
        if (acc >= half && median_bucket[0] == '?') {
            median_bucket = bucket_label[i];
        }
        printf("  单圈直方图 %8s µs : %10lu\n", bucket_label[i], s_bucket[i]);
    }
    printf("  中位数落在 %s µs 这个桶（按直方图读数，误差 ≤ 桶宽）\n", median_bucket);
}

void host_report(const char *mode_name)
{
    printf("\n==== %s ====\n", mode_name);
    printf("运行 %u ms\n", (unsigned)board_tick_ms());
    report_passes();

    printf("LED 翻转 %d 次（应每 500 ms 一次）\n", s_flip_n);
    long long min_iv, max_iv;
    int overdue;

    flip_span(&min_iv, &max_iv, &overdue);
    printf("  间隔 ms：");
    for (int i = 1; i < s_flip_n; i++) {
        printf("%.2f ", (double)(s_flip_ns[i] - s_flip_ns[i - 1]) / 1e6);
    }
    printf("\n");
    printf("  最短 %.2f / 最长 %.2f ms；超过 550 ms 的迟到翻灯 %d 次\n",
           (double)min_iv / 1e6, (double)max_iv / 1e6, overdue);
    printf("  翻转时刻 ms：");
    for (int i = 0; i < s_flip_n; i++) {
        printf("%.2f ", (double)s_flip_ns[i] / 1e6);
    }
    printf("\n");

    printf("按键 %d 次按下：\n", s_key_n);
    for (int i = 0; i < s_key_n; i++) {
        long long hit = key_hit_ns(i);

        if (hit < 0) {
            printf("  %u–%u ms  %-28s 未采到 ← 这个键丢了\n",
                   s_key[i].from_ms, s_key[i].to_ms, s_key[i].what);
        } else {
            printf("  %u–%u ms  %-28s 软件在 %.2f ms 采到，迟到 %.2f ms\n",
                   s_key[i].from_ms, s_key[i].to_ms, s_key[i].what,
                   (double)hit / 1e6,
                   (double)(hit - (long long)s_key[i].from_ms * 1000000) / 1e6);
        }
    }
    /*
     * 本章第三节的落点：超级循环里任何任务的最坏响应时间都是"一整圈的耗时"，
     * 和它排在第几行无关。所以这两个数应当贴在一起——不贴就说明量具自己先不自洽了。
     * 取的是 host_measure 存下的那份结算，和跨局统计同一个数。
     */
    printf("  最坏迟到 %.2f ms ← 对照最长单圈 %.2f ms（响应上界 = 一圈，与行序无关）\n",
           (double)s_rep[s_rep_n - 1].worst_late_ns / 1e6,
           (double)s_rep[s_rep_n - 1].pass_max_ns / 1e6);

    printf("串口：收 %lu 字节，发 %lu 字节，发送累计 %.2f ms\n",
           s_rx_bytes, s_tx_bytes, (double)s_tx_ns / 1e6);
    for (int i = 0; i < s_echo_n; i++) {
        printf("  回显 @%.2f ms：%s（%u 字符 → 线上要 %.2f ms）\n",
               (double)s_echo[i].at_ns / 1e6, s_echo[i].text, (unsigned)s_echo[i].len,
               (double)s_echo[i].len * TX_CHAR_NS / 1e6);
    }
}
