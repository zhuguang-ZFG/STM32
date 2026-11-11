/* scan_cost.c —— 复刻 tasks.c 那两条选择路径的"比较次数"，用宿主机跑一遍
 *
 * 为什么要这个文件：反汇编能证明"一条 clz" 和"一个循环"这两种形状，
 * 但循环到底跑几遍，取决于 uxTopReadyPriority 这个缓存当时停在哪儿。
 * 这里把两条路的规则原样抄成一个模拟器，事件表写死，
 * 所以每次跑出来的数都一样、可以印在屏幕上。
 *
 * 抄的是规则，不是内核本体——内核里那段是 static 宏，外面调不到。
 * 三条纪律必须和源码一致：
 *   通用路：缓存只会被 taskRECORD_READY_PRIORITY 往上顶（tasks.c:168-174），
 *           任务离开就绪表时 taskRESET_READY_PRIORITY 是空宏（tasks.c:205-206），
 *           往下修正只发生在扫描结束那一次写回（tasks.c:192）。
 *   位图路：置位/清位各一个 |= / &=（portmacro.h:166-167），
 *           选优 = 31 - clz(bitmap)（portmacro.h:171）。
 */

#include <stdio.h>

#define MAXN 40   /* 只用来放数组；位图那侧本身只能到 32 级 */

/* ---------- 通用路：标量缓存 + 递减扫描 ---------- */

typedef struct {
    unsigned char empty[MAXN];   /* 1 = 这条就绪链表是空的 */
    unsigned long cache;         /* uxTopReadyPriority */
    unsigned long tests;         /* 累计执行了几次"这条链表空不空"的判断 */
} generic_t;

static void g_init(generic_t *g, unsigned long n, unsigned long initial_cache)
{
    unsigned long i;
    for (i = 0; i < n; i++) {
        g->empty[i] = 1u;
    }
    g->cache = initial_cache;
    g->tests = 0u;
}

/* taskRECORD_READY_PRIORITY：只取大，别的位一概不管 */
static void g_record(generic_t *g, unsigned long p)
{
    g->empty[p] = 0u;
    if (p > g->cache) {
        g->cache = p;
    }
}

/* 任务离开就绪表：通用路径里 taskRESET_READY_PRIORITY( p ) 是空的，
   缓存不动，只把链表标空——这就是缓存会"虚高"的唯一原因。 */
static void g_drop(generic_t *g, unsigned long p)
{
    g->empty[p] = 1u;
}

/* taskSELECT_HIGHEST_PRIORITY_TASK()：从缓存开始往下摸，摸到之后写回。
   源码形状是 while( listLIST_IS_EMPTY( ... ) != pdFALSE ) { --uxTopPriority; }
   ——循环条件每转一圈判一次，跳出那次也判了，所以次数 = 递减次数 + 1。 */
static unsigned long g_select(generic_t *g)
{
    unsigned long top = g->cache;

    for (;;) {
        g->tests++;
        if (g->empty[top] == 0u) {
            break;
        }
        if (top == 0u) {
            break;   /* 优先级 0（空闲任务）永远非空，内核靠这条兜底，正常跑不到 */
        }
        top--;
    }
    g->cache = top;
    return top;
}

/* ---------- 位图路：|= 1<<p / &= ~(1<<p) / 31 - clz ---------- */

typedef struct {
    unsigned long bitmap;
    unsigned long clz_calls;
} bitmap_t;

static void b_init(bitmap_t *m)
{
    m->bitmap = 0u;
    m->clz_calls = 0u;
}

static void b_record(bitmap_t *m, unsigned long p)
{
    m->bitmap |= 1UL << p;              /* portRECORD_READY_PRIORITY */
}

static void b_drop(bitmap_t *m, unsigned long p)
{
    m->bitmap &= ~(1UL << p);           /* portRESET_READY_PRIORITY */
}

/* 这里用手写的数前导零代替 __builtin_clz：屏幕上要报的是"一次"这件事，
   不是宿主机 x86 上 bsr 的周期数。M4 上它是 clz 一条指令。 */
static unsigned long b_clz(unsigned long v)
{
    unsigned long n = 0u;
    int i;
    for (i = 31; i >= 0; i--) {
        if ((v & (1UL << i)) != 0u) {
            break;
        }
        n++;
    }
    return n;
}

static unsigned long b_select(bitmap_t *m)
{
    m->clz_calls++;
    return 31UL - b_clz(m->bitmap);     /* portGET_HIGHEST_PRIORITY */
}

/* ---------- 场景一：只有优先级 0 上有人，缓存停在最高位 ---------- */

static void scene_stale_cache(unsigned long n)
{
    unsigned long p;
    printf("### 场景一：缓存虚高停在 %lu，实际只有下面这一层有人（configMAX_PRIORITIES = %lu）\n",
           n - 1u, n);
    printf("   真实最高位   通用路判空次数   位图路 clz 次数\n");
    for (p = 0; p < n; p++) {
        generic_t g;
        bitmap_t m;

        g_init(&g, n, n - 1u);          /* 缓存摆最高，制造虚高 */
        g.empty[p] = 0u;                /* 只有 p 这一层有任务 */
        (void) g_select(&g);

        b_init(&m);
        b_record(&m, p);
        (void) b_select(&m);

        printf("      %2lu              %3lu                %lu\n", p, g.tests, m.clz_calls);
    }
    printf("  → 右列全是 1：一次 clz，与最高位在第几层无关。\n");
    printf("  → 左列 = 虚高了几层 + 1；虚高的上限就是 configMAX_PRIORITIES - 1。\n\n");
}

/* ---------- 场景二：一张写死的事件表，两条路各跑一遍 ---------- */

/* 每个事件：R = 优先级 p 上有任务就绪，D = 它离开就绪表，S = 调度器选一次下一个 */
typedef struct { char op; unsigned long p; } event_t;

static const event_t trace[] = {
    { 'R', 0u },                                  /* 空闲任务永远在场 */
    { 'R', 3u }, { 'S', 0u }, { 'D', 3u }, { 'S', 0u },   /* 一个短命的活 */
    { 'R', 4u }, { 'S', 0u }, { 'D', 4u }, { 'S', 0u },   /* 顶上去再撤走 */
    { 'R', 2u }, { 'R', 3u }, { 'S', 0u },                 /* 两个同场，轮转 */
    { 'D', 3u }, { 'S', 0u },
    { 'D', 2u }, { 'S', 0u },
    { 'R', 30u }, { 'S', 0u },                              /* 只有高位来了一下 */
    { 'D', 30u }, { 'S', 0u },                              /* 撤走：缓存还停在 30 */
    { 'R', 1u }, { 'D', 1u }, { 'S', 0u }                  /* 剩下的全在低层 */
};

static void scene_trace(unsigned long n)
{
    generic_t g;
    bitmap_t m;
    size_t i;
    unsigned long sel = 0u, mismatch = 0u;
    unsigned long worst = 0u, worst_at = 0u, worst_from = 0u, worst_to = 0u;

    g_init(&g, n, 0u);
    b_init(&m);
    g_record(&g, 0u);
    b_record(&m, 0u);

    for (i = 0; i < sizeof trace / sizeof trace[0]; i++) {
        const event_t *e = &trace[i];
        if (e->p >= n) {
            continue;                       /* n=5 时自动跳过优先级 30 那两个事件 */
        }
        switch (e->op) {
            case 'R': g_record(&g, e->p); b_record(&m, e->p); break;
            case 'D': g_drop(&g, e->p);   b_drop(&m, e->p);   break;
            default: {
                unsigned long before = g.tests;
                unsigned long from = g.cache;
                unsigned long a = g_select(&g);
                unsigned long b = b_select(&m);
                unsigned long delta = g.tests - before;

                sel++;
                if (a != b) {
                    mismatch++;
                    printf("  !! 第 %lu 次选择两条路不一致：通用 %lu vs 位图 %lu\n", sel, a, b);
                }
                if (delta > worst) {
                    worst = delta;
                    worst_at = sel;
                    worst_from = from;
                    worst_to = a;
                }
                break;
            }
        }
    }
    printf("### 场景二：同一张事件表跑完（configMAX_PRIORITIES = %lu）\n", n);
    printf("  事件 %lu 个，其中选择 %lu 次；两条路选出不同优先级的次数 = %lu\n",
           (unsigned long) (sizeof trace / sizeof trace[0]), sel, mismatch);
    printf("  通用路累计判空 %lu 次，平均每次选择 %.2f 次\n",
           g.tests, sel ? (double) g.tests / (double) sel : 0.0);
    printf("  位图路累计 clz %lu 次，平均 %.2f 次\n",
           m.clz_calls, sel ? (double) m.clz_calls / (double) sel : 0.0);
    printf("  通用路最坏那一次是第 %lu 次选择：缓存停在 %lu，真实最高位是 %lu，判空 %lu 次；\n",
           worst_at, worst_from, worst_to, worst);
    printf("  位图路同一次选择只花 1 次 clz：它的累计/平均/最坏三个数必然相等。\n\n");
}

int main(void)
{
    printf("== 调度器选优：两条路各比几次（规则抄自 tasks.c 与 ARM_CM4F portmacro.h）==\n\n");
    scene_stale_cache(5u);
    scene_stale_cache(32u);
    scene_trace(5u);
    scene_trace(32u);
    printf("== 形状：位图路与优先级个数无关，恒为 1；通用路 = 缓存虚高的层数 + 1 ==\n");
    return 0;
}
