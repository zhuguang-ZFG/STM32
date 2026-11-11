/* sim_invert.c —— 优先级反转的宿主机模型：E04 剧本，不烧板也能算出 H 等了多久
 *
 * 这一集屏上只有两类证据：objdump/nm 能钉死的静态血缘（probe.sh 前六步），
 * 和这一步跑出来的动态时序。动态那半边难在哪：E04 的 6000/2500 在文档里明确
 * 标着「理论值，不是实测数据」(docs/lab/e04-priority-inversion.md:78)，
 * 实测记录那张表到今天还是空的。所以这里跑出来的数【只能叫模型值】——
 * 它证的是「继承与不继承这两条规则，按剧本参数各自会推到哪一刻」，
 * 不是「我的板子上串口打出来是几毫秒」。屏上必须把这句话说全。
 *
 * 剧本逐条对齐 code/rtos/01-freertos-lab/main.c:309-358（DEMO_SCENE=6）：
 *   L 优先级 1，take 锁后 cpu_work_ms(3000)——只计自己真正跑到的拍
 *   M 优先级 2，vTaskDelay(500) 起，busy_until(4500) 连续占 CPU，不碰锁
 *   H 优先级 3，vTaskDelay(1000) 起，要锁并记下 waited
 *   USE_MUTEX=0 → xSemaphoreCreateBinary() 再补一次 give（计数 1，无继承）
 *   USE_MUTEX=1 → xSemaphoreCreateMutex()（出生即计数 1，有继承）
 *
 * 调度和继承的规则不是我发明的，是抄内核的。每抄一条都在后面标内核行号，
 * probe.sh 第 8 步逐条核对这些行号还在不在——内核一升级行号就漂，
 * 漂了要报错，而不是悄悄给出一个看着对的数。
 *   R1 只有互斥锁那道门才走继承        queue.c:1784  pxQueue->uxQueueType == queueQUEUE_IS_MUTEX
 *   R2 继承的调用点在 take 失败之后    queue.c:1788  xTaskPriorityInherit( … xMutexHolder )
 *   R0 holder 为 NULL 就不继承          tasks.c:6589 if( pxMutexHolder != NULL )
 *      （holder 怎么会是 NULL：中断那条路的 take 展开成 xQueueReceiveFromISR，
 *        semphr.h:675 → queue.c:2035，那个函数从头到尾不登记持有者。
 *        所以这一问是「机制被跳过」，不是「中断禁止 take」——内核注释 tasks.c:6587 自己就这么举的中断）
 *   R3 判：持锁者比等待者低才抬        tasks.c:6594  pxMutexHolderTCB->uxPriority < pxCurrentTCB->uxPriority
 *   R4 事件表值 = MAX_PRIO - 等待者    tasks.c:6601  listSET_LIST_ITEM_VALUE( … configMAX_PRIORITIES - … )
 *   R5 搬：先从旧就绪表摘出来          tasks.c:6612  uxListRemove( &( pxMutexHolderTCB->xStateListItem ) )
 *   R6 摘空了要复位位图                tasks.c:6617  portRESET_READY_PRIORITY( … )
 *   R7 改数，再挂进新优先级的表        tasks.c:6625  pxMutexHolderTCB->uxPriority = pxCurrentTCB->uxPriority
 *                                       tasks.c:6626  prvAddTaskToReadyList( pxMutexHolderTCB )
 *   R8 还锁走镜像路径回落              queue.c:2408  xTaskPriorityDisinherit( … xMutexHolder )
 *   R9 交棒给优先级最高的等待者，同级先到先得    list.c:192 的 <=：同值时先入表的离表头更近
 *
 * 时间口径（这一条决定 6000/2500 能不能对上文档，写死在这里）：
 *   一拍 = 1ms = 一个任务的连续 CPU 时间。登记 vTaskDelay、take 失败挂起、give、
 *   还锁回落这些都是【瞬间动作】，不吃掉这一拍——动作做完后同一拍重新选人。
 *   否则三任务开跑时 H、M 各占一拍，L 就从 t=2 才开始干活，两档都会平白多出 2ms，
 *   跟文档那张表（L 从 t=0 起算）对不上，而我没法说清多出来的是模型误差还是我的错。
 *   代价是同一拍里可能连做好几个动作，所以要有『一拍瞬间动作有上限』的护栏：
 *   超上限就是模型自己打死了，硬失败，不许静默空转。
 *
 * 编译：gcc -std=c11 -O0 -Wall -Wextra -Werror -o sim sim_invert.c
 * 没有真时钟、没有随机数：同一个二进制连跑两次输出必须逐字节相同（probe.sh 会 cmp）。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CRIT_WORK_MS   3000u   /* main.c:315 cpu_work_ms(3000) */
#define M_START_MS      500u   /* main.c:324 vTaskDelay(pdMS_TO_TICKS(500)) */
#define M_END_MS       4500u   /* main.c:326 busy_until(pdMS_TO_TICKS(4500)) */
#define H_WANT_MS      1000u   /* main.c:334 vTaskDelay(pdMS_TO_TICKS(1000)) */
#define MAX_PRIORITIES    5u   /* FreeRTOSConfig.h:23 configMAX_PRIORITIES，R4 算事件表值要用 */
#define MAX_TICKS     20000u   /* 剧本最迟 7000 拍就该收，超了就是模型自己打死了，硬失败 */
#define NEVER       0xffffffffu /* vTaskDelay(portMAX_DELAY) */

enum { L, M, H, NTASK };
#define IDLE        ((int) NTASK)   /* 绝不与 L/M/H 同值：曾经踩过 IDLE==L==0，L 一轮都跑不到 */
#define INSTANT_MAX (NTASK * 3)     /* 同一拍里瞬间动作的上限（护栏，不是剧本参数） */

enum { DORMANT, READY, BLOCKED };
enum { LOCK_BINARY, LOCK_MUTEX };

typedef struct {
    const char *name;
    unsigned base_prio;   /* 剧本写死的 1/2/3 */
    unsigned prio;        /* 当前优先级：互斥量档里会被继承抬高，R7 */
    int state;
    unsigned wake;        /* 到期拍 */
    int waits_lock;       /* 是不是因为这把锁在这儿阻塞（R2 的等待者） */
    unsigned work_left;   /* cpu_work_ms 还剩几拍，被抢占的拍不计 */
    int parked;           /* 剧本跑完，不再参与调度 */
    unsigned ran;         /* 累计真正跑到的拍 */
    unsigned t0;          /* H 算 waited 的起点 */
    unsigned phase;
} task_t;

typedef struct {
    int kind;
    unsigned count;   /* 信号量/互斥量都是 uxItemSize=0 队列里的那个计数，见 probe.sh 第 1 步 */
    int holder;       /* 互斥锁持有者；二值信号量没有这个概念，恒为 -1 */
} lock_t;

static task_t T[NTASK];
static lock_t K;
static unsigned block_seq[NTASK];   /* R9 同级先到先得：等价于事件链表里谁离表头更近 */
static unsigned block_ctr;
static unsigned tick;
static unsigned at_give;
static unsigned at_mend;
static unsigned at_hwant;
static unsigned at_hgot;
static const char *tag_now = "binary";

static void ev(const char *who, const char *what, long v)
{
    /* 每一行都带上 tag：两幕共用同一个 tick 轴，屏上要把「哪一幕的哪一拍」一次说清，
       否则 grep t=1000 会把二值档和互斥量档叠成一条假时间线。 */
    printf("EVT tag=%-6s t=%u who=%-4s %s=%ld\n", tag_now, tick, who, what, v);
}

static void t_init(int id, const char *name, unsigned prio)
{
    memset(&T[id], 0, sizeof(T[id]));
    T[id].name = name;
    T[id].base_prio = prio;
    T[id].prio = prio;
    T[id].state = READY;
    block_seq[id] = NEVER;
}

/* main.c:318/328/342 park_forever() = vTaskDelay(portMAX_DELAY)。
 * 延时挂在 infinity 上，所以【必须把 wake 一起设成 NEVER】：
 * 早先我只置了 state=BLOCKED，pick() 每次进来都拿它那个过期的 wake 把它复活，
 * 于是 t=4500 那一拍里 M 反复「收摊→醒来→收摊」，护栏当场把它抓出来了。 */
static void park(int id)
{
    T[id].parked = 1;
    T[id].state = BLOCKED;
    T[id].waits_lock = 0;
    T[id].wake = NEVER;
    ev(T[id].name, "park_forever", (long) T[id].ran);
}

/* R1/R0/R3/R4/R5/R6/R7：内核 xTaskPriorityInherit 的「判 → 改 → 搬」 */
static void priority_inherit(int waiter)
{
    int holder;

    if (K.kind != LOCK_MUTEX) {                 /* R1：二值信号量根本进不到这道门 */
        ev(T[waiter].name, "inherit_skipped", 0);
        return;
    }
    holder = K.holder;
    if (holder < 0) {                           /* R0：中断里 take，没有持有者 */
        ev(T[waiter].name, "inherit_no_holder", 0);
        return;
    }
    if (T[holder].prio >= T[waiter].prio) {     /* R3 判 */
        ev(T[holder].name, "inherit_not_lower", (long) T[holder].prio);
        return;
    }
    /* R4：事件表项的值换成 configMAX_PRIORITIES - 等待者优先级 */
    ev(T[holder].name, "event_value_set", (long) (MAX_PRIORITIES - T[waiter].prio));

    if (T[holder].state == READY) {
        /* R5 摘 + R6 位图 + R7 改数、挂进新表。
         * 本模型的「就绪表」就是 state/prio 两个字段，摘与挂表现为「优先级换了」。
         * 位图记账省下来不改结论：holder 抬到最高级后，同一拍重新选人必然选中它。
         * 但省掉的动作要在日志里单独打出来——它是这一集要讲的三步之一，不是实现细节。 */
        ev(T[holder].name, "ready_list_detach", (long) T[holder].prio);   /* R5/R6 */
        T[holder].prio = T[waiter].prio;                                  /* R7 改数 */
        ev(T[holder].name, "prio_inherited", (long) T[holder].prio);
        ev(T[holder].name, "ready_list_attach", (long) T[holder].prio);   /* R7 搬 */
    } else {
        T[holder].prio = T[waiter].prio;   /* 内核 else：阻塞中只改数不搬表，tasks.c:6641 */
        ev(T[holder].name, "prio_inherited_blocked", (long) T[holder].prio);
    }
}

/* R8：还锁走 xTaskPriorityDisinherit，回落原值 */
static void priority_disinherit(int holder)
{
    if (K.kind != LOCK_MUTEX) return;
    if (T[holder].prio != T[holder].base_prio) {
        T[holder].prio = T[holder].base_prio;
        ev(T[holder].name, "prio_disinherited", (long) T[holder].prio);
    }
}

/* xQueueSemaphoreTake 的模型。返回 1=拿到，0=挂起（并可能触发继承） */
static int lock_take(int id)
{
    if (K.count > 0) {
        K.count--;
        if (K.kind == LOCK_MUTEX) {
            K.holder = id;
            ev(T[id].name, "holder_set", 1);
        }
        return 1;
    }
    T[id].state = BLOCKED;
    T[id].waits_lock = 1;
    T[id].wake = NEVER;
    block_seq[id] = block_ctr++;
    ev(T[id].name, "take_blocked", (long) K.count);
    priority_inherit(id);                       /* R2 */
    return 0;
}

/* xQueueGenericSend 的模型：give 永不阻塞（semGIVE_BLOCK_TIME=0）。
 * 互斥量先回落优先级、清 holder，再把计数放回 1，然后从事件链表头上摘一个等待者叫醒。
 * 注意叫醒不等于交棒：内核的 send 路径是把计数摆回队列再 xTaskRemoveFromEventList，
 * 计数留在队列里，被叫醒的那个自己 take 得到。所以这里【不减回去】——
 * 早先我在这儿写了一次 count--，二值信号量档里 H 被叫醒后再 take 一次空的，直接卡死。 */
static void lock_give(int id)
{
    int best = -1;
    unsigned i;

    if (K.kind == LOCK_MUTEX) {
        priority_disinherit(id);                /* R8 */
        K.holder = -1;
    }
    K.count++;
    ev(T[id].name, "give", (long) K.count);

    for (i = L; i < NTASK; i++) {               /* R9：最高优先级等待者，同级先到先得 */
        if (!T[i].waits_lock) continue;
        if (best < 0) { best = (int) i; continue; }
        if (T[i].prio > T[best].prio) best = (int) i;
        else if (T[i].prio == T[best].prio && block_seq[i] < block_seq[best]) best = (int) i;
    }
    if (best >= 0) {
        T[best].state = READY;
        T[best].waits_lock = 0;
        ev(T[best].name, "unblocked", (long) tick);   /* 内核：xTaskRemoveFromEventList 在计数落回之后 */
    }
}

/* 一拍里只有一人真正占 CPU；抢占只发生在拍边界 */
static int pick(void)
{
    int best = -1;
    unsigned i;

    for (i = L; i < NTASK; i++) {
        if (T[i].state == BLOCKED && !T[i].waits_lock && T[i].wake <= tick) {
            T[i].state = READY;
            ev(T[i].name, "tick_wake", (long) tick);
        }
        if (T[i].state != READY) continue;
        if (best < 0 || T[i].prio > T[best].prio) best = (int) i;
    }
    return best < 0 ? IDLE : best;
}

/* step 返回 1 = 这一拍被它占用了；返回 0 = 只做了瞬间动作，这一拍要重新交给别人 */
static int step(int id)
{
    task_t *t = &T[id];

    switch (id) {
    case L:
        if (t->phase == 0) {
            ev("L", "want_lock", 0);
            if (!lock_take(L)) return 0;         /* 抢不到：瞬间挂起，这一拍重新选人 */
            ev("L", "got_lock_work_ms", (long) CRIT_WORK_MS);
            t->work_left = CRIT_WORK_MS;
            t->phase = 1;
            /* 拿到锁的这一拍本来就是 L 跑到的，直接落进下面的计时分支 */
        }
        if (t->phase == 1) {
            t->ran++;
            if (--t->work_left == 0) t->phase = 2;
            return 1;
        }
        if (t->phase == 2) {
            ev("L", "crit_done_ran_ms", (long) t->ran);
            at_give = tick;
            lock_give(L);
            t->phase = 3;
            return 0;                             /* 还锁是瞬间动作，H 同一拍就能接上 */
        }
        park(L);
        return 0;

    case M:
        if (t->phase == 0) {
            t->state = BLOCKED;
            t->wake = tick + M_START_MS;
            ev("M", "delay_ms", (long) M_START_MS);
            t->phase = 1;
            return 0;
        }
        if (t->phase == 1) {
            if (tick < M_END_MS) {                /* busy_until 看墙钟，不看自己跑了多久 */
                t->ran++;
                return 1;
            }
            at_mend = tick;
            ev("M", "burst_end", (long) tick);
            t->phase = 2;
            return 0;
        }
        park(M);
        return 0;

    case H:
        if (t->phase == 0) {
            t->state = BLOCKED;
            t->wake = tick + H_WANT_MS;
            ev("H", "delay_ms", (long) H_WANT_MS);
            t->phase = 1;
            return 0;
        }
        if (t->phase == 1) {
            if (t->t0 == 0) {
                ev("H", "want_lock", 0);
                t->t0 = tick;
                at_hwant = tick;
            }
            if (!lock_take(H)) return 0;          /* 被挡：这一拍还给原来那个人 */
            ev("H", "got_lock", (long) tick);     /* holder_set 由 lock_take 按档位打，这里不重复 */
            at_hgot = tick;
            t->phase = 2;
            return 0;
        }
        if (t->phase == 2) {          /* main.c:340-341 拿到就还，剧本里 H 不在临界区里待着 */
            lock_give(H);
            t->phase = 3;
            return 0;
        }
        park(H);
        return 0;

    default:
        return 1;                          /* 不该走到：IDLE 在调用方就 break 了 */
    }
}

static void run(int kind)
{
    unsigned guard, inner;

    tag_now = kind == LOCK_MUTEX ? "mutex" : "binary";
    memset(T, 0, sizeof T);
    memset(block_seq, 0, sizeof block_seq);
    block_ctr = 0;
    at_give = 0;
    at_mend = 0;
    at_hwant = 0;
    at_hgot = 0;
    tick = 0;

    t_init(L, "L", 1);                /* main.c:356 优先级 1=低 */
    t_init(M, "M", 2);                /* main.c:357 */
    t_init(H, "H", 3);                /* main.c:358 */

    K.kind = kind;
    K.holder = -1;
    /* 互斥量：prvInitialiseMutex 创建即白送一次 → 出生计数 1（probe.sh 第 3 步的 objdump 证据）
     * 二值信号量：出生是 0，main.c:352-353 先创建、再靠一句显式 give 把它填成 1，L 才抢得到。
     * 这两句必须分开记：born_count 与 pre_give 分开打，才不至于把「出生即 1」的功劳记错人。 */
    K.count = (kind == LOCK_MUTEX) ? 1u : 0u;
    printf("RUN tag=%s kind=%s born_count=%u\n",
           tag_now,
           kind == LOCK_MUTEX ? "xSemaphoreCreateMutex" : "xSemaphoreCreateBinary",
           K.count);
    if (kind == LOCK_BINARY) {
        K.count = 1u;
        ev("main", "binary_pre_give", (long) K.count);   /* main.c:353 */
    }

    /* 之后不再手动安排起跑：t=0 这一拍交给调度器自己选人（H→M→L 各登记一次瞬间动作，
     * 最后 L 拿到锁占住这拍）。手排会把「谁先跑」变成我的假设而不是内核的规则。 */
    for (guard = 0; guard < MAX_TICKS; guard++) {
        /* 同一拍里允许连续瞬间动作（挂起、还锁、叫醒），直到有人把这拍真正用掉 */
        for (inner = 0; inner < INSTANT_MAX; inner++) {
            int who = pick();
            if (who == IDLE) break;
            if (step(who) == 1) break;
        }
        if (inner >= INSTANT_MAX) {
            printf("FAIL t=%u 同一拍里瞬间动作超过 %d，模型没收住\n", tick, INSTANT_MAX);
            exit(2);
        }
        if (T[L].parked && T[M].parked && T[H].parked) break;
        tick++;
    }
    if (guard >= MAX_TICKS) {
        printf("FAIL 剧本 %u 拍没跑完，模型死循环\n", MAX_TICKS);
        exit(2);
    }
    /* RES 放在整场跑完之后打：m_end 在互斥量档里是 4500，比 H 拿到锁的 3500 还晚，
     * 早先我把这行印在 H 拿锁的那一刻，读出来 m_end=0，「l_give < m_end」这条判别式
     * 当场就没了依据。l_give/m_end 谁大谁小正是这一集区分两档的那句话，必须两个都有值。 */
    printf("RES tag=%s h_want=%u h_got=%u waited=%u l_give=%u m_end=%u l_ran=%u m_ran=%u\n",
           tag_now, at_hwant, at_hgot, at_hgot - at_hwant, at_give, at_mend,
           T[L].ran, T[M].ran);
    printf("END tag=%s total_ticks=%u\n", tag_now, tick);
}

int main(void)
{
    run(LOCK_BINARY);
    run(LOCK_MUTEX);
    return 0;
}
