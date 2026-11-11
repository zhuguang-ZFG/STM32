/* sim_daemon.c —— 把守护任务的分派规则抄成一台宿主机模拟器
 *
 * 为什么要这个文件：nm 和 objdump 能算出"打开定时器花多少字节"，但"一个回调磨蹭，
 * 别的定时器晚多少拍"是时序问题，静态机身给不出数。本仓库的 V11.1.0 里没有 POSIX
 * 端口（portable/GCC/ 下全是交叉端口），真内核在宿主机上跑不起来，所以这里把
 * timers.c 的分派规则原样抄一遍：事件表写死，每次跑出来的数都一样，可以直接印屏幕。
 *
 * 抄的是规则，不是内核本体——那三个函数都是 static，外面调不到。
 * 每条规则后面标了上游 V11.1.0 timers.c / list.c 的行号；probe.sh 第 7 步会逐条核对
 * 那些行号处的代码仍然长这样——内核一升级行号就漂，漂了这份取证直接报错，
 * 而不是悄悄给出一个错的数。
 *
 * 被抄的七条规则：
 *   R1 取下一到期时刻：表空返回 0，否则取链表头的 xItemValue          timers.c:859
 *   R2 一轮只处理"头那一个"到期定时器，其余等下一轮                    timers.c:800-803
 *   R3 没到期就睡到那个时刻：阻塞时长 = xNextExpireTime - xTimeNow     timers.c:820
 *   R4 auto-reload 的下一拍锚在【原到期时刻 + 周期】，不锚在回调结束   timers.c:727-735
 *   R5 补拍：插入点已过期且 (xTimeNow - xCommandTime) >= 周期
 *      → 当场再调一次回调，xExpiredTime 前推一拍，继续判               timers.c:706,709
 *      判据本体（那两个 if）                                          timers.c:904,908
 *   R6 排序插入遇到相等值插在【等值项之后】→ 同刻到期时先入表者先服务   list.c:192
 *      （那个 for 的条件是 <=，不是 <；就是它决定同刻谁在前）
 *   R7 xTimeNow 是本轮快照，回调期间墙上时间继续走，但 R5 的循环不看它   timers.c:795-803
 *
 * 两处明说的简化：
 *   1) START 命令建模成"t=0 布防，到期时刻 = 0 + 周期"。真实路径是
 *      xTimerStart → 命令队列 → 守护任务 prvProcessReceivedCommands 一次排空；
 *      两个 START 都在守护任务起来前进队，排空顺序即创建顺序，结果与建模一致。
 *   2) 表用数组存，用 (到期时刻, 入表序号) 的字典序代替链表位置——这正是 R6 的语义。
 */

#include <stdio.h>
#include <string.h>

#define MAXT   4
#define MAXLOG 40

typedef struct {
    const char * name;
    unsigned long period;     /* ticks */
    unsigned long cost;       /* 回调占用的墙上时间，单位 tick */
    unsigned long expiry;     /* 当前这一拍的到期时刻 */
    unsigned long seq;        /* 入表序号：等值时后入表者排在后面（R6） */
    int armed, autoreload;
    unsigned long served;     /* 实际执行的回调数（含补拍） */
    unsigned long late_n;     /* 迟到的次数 */
    unsigned long late_max, late_sum;
    unsigned long catchup;    /* 被 R5 的 while 当场补拍的次数 */
    unsigned long backlog_max;/* 单轮补拍的最大值 */
    unsigned long burst_max;  /* 同一时刻连开几枪（补拍 N 次 + 本拍 1 次） */
} tmr_t;

typedef struct {
    tmr_t t[MAXT];
    int n;
    const char * tag;       /* 场景名：LOG 行要带上它，probe.sh 才能按场景读动作序列 */
    unsigned long now;        /* 墙上时间 */
    unsigned long iters;      /* 守护任务循环圈数 */
    unsigned long seqgen;
    int truncated;
    struct {
        unsigned long wake;   /* 这一拍守护任务实际动手的时刻 */
        unsigned long sched;  /* 本该到期的时刻 */
        unsigned long late;
        char who[12];
        int catchup;          /* 这次是补拍还是正常拍 */
    } log[MAXLOG];
    int nlog;
} sim_t;

static sim_t S;

static void reset(void)
{
    memset(&S, 0, sizeof S);
}

static void arm(const char * name, unsigned long period, unsigned long cost, int autoreload)
{
    tmr_t * t = &S.t[S.n++];
    t->name = name; t->period = period; t->cost = cost;
    t->expiry = period;      /* 简化 1：t=0 布防 → 到期时刻 = 0 + period */
    t->seq = S.seqgen++;
    t->autoreload = autoreload;
    t->armed = 1;
}

/* R1 + R6：字典序 (expiry, seq) 最小者 = 链表头 */
static tmr_t * head_of(void)
{
    tmr_t * best = 0;
    int i;
    for (i = 0; i < S.n; i++) {
        tmr_t * t = &S.t[i];
        if (!t->armed) continue;
        if (!best) { best = t; continue; }
        if ((t->expiry < best->expiry) ||
            ((t->expiry == best->expiry) && (t->seq < best->seq))) {
            best = t;
        }
    }
    return best;
}

static void logline(tmr_t * t, unsigned long sched, int catchup)
{
    unsigned long late = (S.now > sched) ? (S.now - sched) : 0;
    if (S.nlog < MAXLOG) {
        S.log[S.nlog].wake = S.now;
        S.log[S.nlog].sched = sched;
        S.log[S.nlog].late = late;
        S.log[S.nlog].catchup = catchup;
        snprintf(S.log[S.nlog].who, sizeof S.log[S.nlog].who, "%s", t->name);
        S.nlog++;
    }
    t->served++;
    if (late) { t->late_n++; t->late_sum += late; if (late > t->late_max) t->late_max = late; }
    S.now += t->cost;
}

/* R5 + R7：prvReloadTimer 的 while。xTimeNow 是进来的快照，循环里不再更新。 */
static unsigned long reload(tmr_t * t, unsigned long expired_at, unsigned long xTimeNow)
{
    unsigned long next = expired_at + t->period;
    unsigned long rounds = 0;
    while ((next <= xTimeNow) && ((xTimeNow - expired_at) >= t->period)) {
        expired_at = next;                 /* 前推一拍 */
        rounds++;
        t->catchup++;
        logline(t, expired_at, 1);         /* 当场补拍一次真回调 */
        next = expired_at + t->period;
    }
    if (rounds > t->backlog_max) t->backlog_max = rounds;
    t->expiry = next;                      /* R4：锚在原到期时刻 + 周期上 */
    t->seq = S.seqgen++;
    return rounds;
}

static void simulate(unsigned long horizon, unsigned long iter_cap)
{
    while (S.now <= horizon) {
        tmr_t * h = head_of();
        if (!h) return;                    /* 表空：守护任务睡死，模拟到此为止 */
        if (h->expiry <= S.now) {          /* R2：这一轮只处理头这一个 */
            unsigned long snap = S.now;    /* R7 */
            unsigned long sched = h->expiry;
            if (h->autoreload) {
                unsigned long rounds = reload(h, sched, snap); /* 先重排，再回调 */
                logline(h, sched, 0);
                if (rounds + 1u > h->burst_max) h->burst_max = rounds + 1u;
            } else {
                h->armed = 0;              /* one-shot：摘链，置 inactive */
                logline(h, sched, 0);
            }
        } else {
            S.now = h->expiry;             /* R3：睡到那个时刻 */
        }
        if (++S.iters > iter_cap) { S.truncated = 1; return; }
    }
}

static unsigned long should_have_fired(unsigned long period, unsigned long horizon)
{
    return horizon / period;
}

/* 收工时这个定时器欠了几整拍：它的下一拍到期时刻已经落在墙上时间后面多远 */
static unsigned long owed_ticks(const tmr_t * t)
{
    if (!t->armed) return 0;
    return (S.now > t->expiry) ? (S.now - t->expiry) : 0;
}

static void run_case(const char * tag, unsigned long horizon, unsigned long iter_cap,
                     const char * n1, unsigned long p1, unsigned long c1,
                     const char * n2, unsigned long p2, unsigned long c2)
{
    int i;
    unsigned long duty;
    reset();
    S.tag = tag;
    arm(n1, p1, c1, 1);
    arm(n2, p2, c2, 1);
    simulate(horizon, iter_cap);
    /* 守护任务的占空比 = Σ(耗时/周期)，用千分比表示，避免浮点 */
    duty = c1 * 1000 / p1 + c2 * 1000 / p2;

    printf("\n== 场景 %s：%s 周期%lu 耗时%lu ｜ %s 周期%lu 耗时%lu ｜ 跑到 %lu 拍 ｜ 占空比 %lu.%03lu ==\n",
           tag, n1, p1, c1, n2, p2, c2, horizon, duty / 1000, duty % 1000);
    printf("  %-8s %7s %7s %7s %7s %8s %9s %9s %8s %8s %8s\n",
           "timer", "周期", "耗时", "应拍", "实拍", "迟到次", "最大迟到", "迟到和", "补拍", "连发", "欠(tick)");
    for (i = 0; i < S.n; i++) {
        tmr_t * t = &S.t[i];
        printf("  %-8s %7lu %7lu %7lu %7lu %8lu %9lu %9lu %8lu %8lu %8lu\n",
               t->name, t->period, t->cost,
               should_have_fired(t->period, horizon),
               t->served, t->late_n, t->late_max, t->late_sum, t->catchup, t->burst_max,
               owed_ticks(t));
        printf("    RES tag=%s timer=%s period=%lu cost=%lu duty_permille=%lu should=%lu "
               "served=%lu late_n=%lu late_max=%lu late_sum=%lu catchup=%lu backlog_max=%lu "
               "burst_max=%lu owed=%lu\n",
               tag, t->name, t->period, t->cost, t->cost * 1000 / t->period,
               should_have_fired(t->period, horizon),
               t->served, t->late_n, t->late_max, t->late_sum, t->catchup,
               t->backlog_max, t->burst_max, owed_ticks(t));
    }
    printf("  RES tag=%s iters=%lu truncated=%d duty_permille=%lu\n", tag, S.iters, S.truncated, duty);

    printf("  --- 守护任务动作序列（前 %d 条）---\n", S.nlog);
    printf("  %-10s %-10s %-10s %-10s %s\n", "动手时刻", "本该到期", "迟到", "类型", "回调");
    for (i = 0; i < S.nlog; i++) {
        printf("  %-10lu %-10lu %-10lu %-10s %s\n",
               S.log[i].wake, S.log[i].sched, S.log[i].late,
               S.log[i].catchup ? "补拍" : "本拍", S.log[i].who);
        /* 同一份数据再发一遍机器可读行：probe.sh 只认这行，不认上面那张中文表——
         * 表的列宽会因为对齐调整而变，机器可读行不会。 */
        printf("    LOG tag=%s i=%d wake=%lu sched=%lu late=%lu kind=%s who=%s\n",
               S.tag, i, S.log[i].wake, S.log[i].sched, S.log[i].late,
               S.log[i].catchup ? "catchup" : "ontime", S.log[i].who);
    }
}

int main(void)
{
    printf("== F6 守护任务分派模拟 ==\n");
    printf("规则抄自上游 FreeRTOS-Kernel V11.1.0 timers.c / list.c，事件表写死，\n");
    printf("所以每次跑的数一样。单位是 tick（本工程 configTICK_RATE_HZ=1000，1 拍 = 1ms）。\n");

    /* A 对照组：两个回调都快进快出 —— 证明后面的迟到纯粹是"耗时"造成的 */
    run_case("A", 1200, 200000, "fast", 100, 0, "slow", 120, 0);
    /* B lab 现场：01-freertos-lab 场景 4 的两个定时器，slow 忙等 50 拍 */
    run_case("B", 1200, 200000, "fast", 100, 0, "slow", 120, 50);
    /* C 章节里那句"改到 200ms 数 fast 丢了几拍" */
    run_case("C", 1200, 200000, "fast", 100, 0, "slow", 120, 200);
    /* D 耗时超过自己的周期：补拍失控 */
    run_case("D", 1200, 400000, "fast", 100, 0, "slow", 120, 250);
    /* E 耗时 200 大于别人的周期 100、但小于自己的周期 300 */
    run_case("E", 1200, 400000, "fast", 100, 0, "slow", 300, 200);
    return 0;
}
