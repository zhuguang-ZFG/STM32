/* probe.c —— C5 章取证：函数指针 + 查表法状态机 + 单生产单消费环形缓冲
 *
 * 一条命令跑完：sh probe.sh（宿主 gcc 编译并运行，断言全绿退出码 0）
 *
 * 四个现场：
 *   1. 回调注册表：void (*table[8])(void) 的注册 / 分派 / 计数
 *   2. 查表法状态机：串口命令解析（状态×事件→动作表），逐字节喂入
 *   3. 环形缓冲 A 派：牺牲一格，可用容量 = CAP-1
 *   4. 环形缓冲 B 派：单调索引 + (w-r) 计数，可用容量 = CAP，跨 255 自然回绕
 *
 * 交叉段（probe.sh 自动探测）：arm-none-eabi-gcc -c 后 objdump，
 * 看"通过函数指针调用"在 Cortex-M4 上就是一条 blx。
 */

#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

/* ---------------------------------------------------------------- 断言框架 */

static int g_pass, g_fail;

#define CHECK(cond)                                                          \
    do {                                                                     \
        if (cond) {                                                          \
            g_pass++;                                                        \
        } else {                                                             \
            g_fail++;                                                        \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);           \
        }                                                                    \
    } while (0)

/* ------------------------------------------------- 现场 1：回调注册表与右左法则 */

typedef void (*cb_t)(void);   /* cb_t = “指向 void(void) 函数的指针”这个类型 */

static int g_hits[3];
static void on_press(void)   { g_hits[0]++; }
static void on_release(void) { g_hits[1]++; }
static void on_long(void)    { g_hits[2]++; }

/* 右左法则逐层读：key_table 是数组（8 个元素），
 * 元素是指针，指针指向函数，函数无参、返回 void。 */
static cb_t key_table[8];

_Static_assert(sizeof(key_table) == 8 * sizeof(cb_t), "8 个函数指针占 8 份");

/* 函数返回函数指针：typedef 写法与裸写法等价（裸写法正是右左法则的考题） */
static cb_t pick(int id) { return id == 0 ? on_press : id == 1 ? on_release : on_long; }
static void (*pick_raw(int id))(void) { return pick(id); }

static void probe_callback(void)
{
    key_table[0] = on_press;
    key_table[3] = on_release;
    key_table[7] = on_long;

    for (int i = 0; i < 8; i++)       /* 空槽跳过：分派前判空是纪律 */
        if (key_table[i] != NULL)
            key_table[i]();           /* ← 交叉编译后这一行就是 blx */

    CHECK(g_hits[0] == 1 && g_hits[1] == 1 && g_hits[2] == 1);
    CHECK(pick_raw(0) == on_press && pick_raw(2) == on_long);

    cb_t via_typedef = on_press;
    void (*via_raw)(void) = on_press; /* 两种写法指向同一对象 */
    CHECK(via_typedef == via_raw);
}

/* --------------------------------------- 现场 2：查表法状态机（串口命令解析） */

/* 协议：单行命令  <字母><数字>\n ，字母 ∈ {R,G,B}，数字 ∈ 0..9
 * 例："R5\n" = 把 R 通道设为 5。畸形帧计入 n_err，不崩溃、不死等。 */
typedef enum { S_IDLE, S_ARG, S_END } state_t;
typedef enum { EV_LETTER, EV_DIGIT, EV_LF, EV_OTHER } event_t;

typedef struct {
    state_t state;
    char    cmd;            /* S_ARG/S_END 里暂存的命令字母 */
    int     arg;            /* 暂存的数字                  */
    int     n_exec;         /* 成功执行的命令数            */
    int     n_err;          /* 畸形帧数                    */
    char    log_cmd[16];    /* 执行日志（最多记 16 条）    */
    int     log_arg[16];
} fsm_t;

typedef state_t (*trans_t)(fsm_t *f, char ch);   /* 动作 = 返回下一状态的函数 */

static event_t classify(char ch)
{
    if (ch == 'R' || ch == 'G' || ch == 'B') return EV_LETTER;
    if (ch >= '0' && ch <= '9')              return EV_DIGIT;
    if (ch == '\n')                          return EV_LF;
    return EV_OTHER;
}

static state_t act_ignore(fsm_t *f, char ch) { (void)ch; return f->state; }
static state_t act_save_cmd(fsm_t *f, char ch) { f->cmd = ch; return S_ARG; }
static state_t act_save_arg(fsm_t *f, char ch) { f->arg = ch - '0'; return S_END; }
static state_t act_exec(fsm_t *f, char ch)
{
    (void)ch;
    if (f->n_exec < 16) {
        f->log_cmd[f->n_exec] = f->cmd;
        f->log_arg[f->n_exec] = f->arg;
    }
    f->n_exec++;
    return S_IDLE;
}
static state_t act_error(fsm_t *f, char ch) { (void)ch; f->n_err++; return S_IDLE; }

/* 状态×事件 → 动作；动作的返回值就是下一状态。整张表 const，住 Flash。 */
static trans_t const FSM[3][4] = {
    /*              EV_LETTER     EV_DIGIT      EV_LF       EV_OTHER  */
    /* S_IDLE */ { act_save_cmd, act_ignore,  act_ignore, act_ignore },
    /* S_ARG  */ { act_save_cmd, act_save_arg, act_error, act_error  },
    /* S_END  */ { act_error,    act_error,    act_exec,  act_error  },
};

__attribute__((noinline))           /* 保住符号，方便 objdump 里指认 blx */
static void fsm_feed(fsm_t *f, char ch)
{
    trans_t t = FSM[f->state][classify(ch)];
    f->state = t(f, ch);            /* ← 查表 + 间接调用：中断里只做这点事 */
}

static void fsm_feed_str(fsm_t *f, const char *s)
{
    while (*s != '\0')
        fsm_feed(f, *s++);
}

static void probe_fsm(void)
{
    fsm_t f = { .state = S_IDLE };

    fsm_feed_str(&f, "R5\n");                     /* 正常帧 */
    CHECK(f.n_exec == 1 && f.log_cmd[0] == 'R' && f.log_arg[0] == 5);
    CHECK(f.state == S_IDLE && f.n_err == 0);

    fsm_feed_str(&f, "G0\nB9\n");                 /* 连续两帧 */
    CHECK(f.n_exec == 3 && f.log_cmd[2] == 'B' && f.log_arg[2] == 9);

    fsm_feed_str(&f, "R\n");                      /* 缺参数：畸形帧 */
    CHECK(f.n_err == 1 && f.n_exec == 3 && f.state == S_IDLE);

    fsm_feed_str(&f, "Q7! \n");                   /* 垃圾字节：IDLE 里全吞 */
    CHECK(f.n_exec == 3 && f.n_err == 1);

    fsm_feed(&f, 'R');                            /* 逐字节喂（中断来一字喂一字） */
    fsm_feed(&f, '4');
    CHECK(f.state == S_END && f.n_exec == 3);     /* 状态活着，跨调用续命 */
    fsm_feed(&f, '\n');
    CHECK(f.n_exec == 4 && f.log_arg[3] == 4);

    fsm_feed_str(&f, "R5X\n");                    /* 参数后混入垃圾：报错复位 */
    CHECK(f.n_err == 2 && f.n_exec == 4 && f.state == S_IDLE);

    fsm_feed_str(&f, "R3");
    CHECK(f.state == S_END);                      /* 半帧挂起，等下一字节 */
}

/* -------------------------------------- 现场 3：环形缓冲 A 派——牺牲一格 */

#define RB_CAP 8   /* 物理格数（两派相同，便于对照） */

typedef struct {
    uint8_t data[RB_CAP];
    volatile uint8_t w;   /* 写指针：只有生产者写 */
    volatile uint8_t r;   /* 读指针：只有消费者写 */
} rb_slot_t;

static bool rb_slot_put(rb_slot_t *q, uint8_t v)
{
    uint8_t w = q->w;
    if ((uint8_t)((w + 1) % RB_CAP) == q->r)
        return false;                            /* 满：再塞一格就分不清满/空 */
    q->data[w] = v;
    atomic_signal_fence(memory_order_release);   /* 数据先于写指针发布 */
    q->w = (uint8_t)((w + 1) % RB_CAP);
    return true;
}

static bool rb_slot_get(rb_slot_t *q, uint8_t *out)
{
    uint8_t r = q->r;
    if (r == q->w)
        return false;                            /* 空 */
    atomic_signal_fence(memory_order_acquire);   /* 先看到写指针，才允许取数据 */
    uint8_t v = q->data[r];
    q->r = (uint8_t)((r + 1) % RB_CAP);
    *out = v;
    return true;
}

static void probe_ring_slot(void)
{
    rb_slot_t q = { {0}, 0, 0 };
    uint8_t v = 0;

    CHECK(!rb_slot_get(&q, &v));                 /* 空读：失败，不出垃圾 */

    for (int i = 0; i < RB_CAP; i++) {           /* 能塞 CAP-1=7 个，第 8 个被拒 */
        bool ok = rb_slot_put(&q, (uint8_t)i);
        CHECK(ok == (i < RB_CAP - 1));
    }
    for (int i = 0; i < RB_CAP - 1; i++) {       /* FIFO：先进先出 */
        CHECK(rb_slot_get(&q, &v) && v == (uint8_t)i);
    }
    CHECK(!rb_slot_get(&q, &v));                 /* 又空了 */

    /* 长跑跨回绕：塞取交错共 600 步，满写被拒的路径也要走到。
     * 在飞窗口 ≤7，序号对 256 取模后与读出值逐一比对即真值。 */
    int n_put = 0, n_get = 0, n_refused = 0;
    for (int step = 0; step < 600; step++) {
        if (step % 3 != 2) {                       /* 塞 2 步、取 1 步：制造积压 */
            if (rb_slot_put(&q, (uint8_t)n_put)) n_put++;
            else n_refused++;
        } else {
            if (rb_slot_get(&q, &v)) {
                CHECK(v == (uint8_t)n_get);
                n_get++;
            }
        }
    }
    while (rb_slot_get(&q, &v)) {                  /* 排干尾货 */
        CHECK(v == (uint8_t)n_get);
        n_get++;
    }
    CHECK(n_put == n_get);                         /* 一个不多一个不少 */
    CHECK(n_refused > 0);                          /* “满写被拒”真的触发过 */
    CHECK(n_put > 2 * RB_CAP);                     /* 索引已在 8 格上绕了多圈 */
}

/* --------------------------- 现场 4：环形缓冲 B 派——单调索引 + (w-r) 计数 */

typedef struct {
    uint8_t data[RB_CAP];
    volatile uint8_t w;   /* 永不取模，交给 uint8_t 自然溢出；只生产者写 */
    volatile uint8_t r;   /* 同上；只消费者写 */
} rb_mono_t;

static bool rb_mono_put(rb_mono_t *q, uint8_t v)
{
    uint8_t w = q->w;
    if ((uint8_t)(w - q->r) >= RB_CAP)           /* 满：无符号减法天然抗回绕 */
        return false;
    q->data[w % RB_CAP] = v;
    atomic_signal_fence(memory_order_release);
    q->w = (uint8_t)(w + 1);
    return true;
}

static bool rb_mono_get(rb_mono_t *q, uint8_t *out)
{
    uint8_t r = q->r;
    if (r == q->w)
        return false;
    atomic_signal_fence(memory_order_acquire);   /* 先看到写指针，才允许取数据 */
    uint8_t v = q->data[r % RB_CAP];
    q->r = (uint8_t)(r + 1);
    *out = v;
    return true;
}

static void probe_ring_mono(void)
{
    rb_mono_t q = { {0}, 0, 0 };
    uint8_t v = 0;

    CHECK(!rb_mono_get(&q, &v));                 /* 空读 */

    for (int i = 0; i < RB_CAP; i++)             /* 能塞满 CAP=8 个（比 A 派多一格） */
        CHECK(rb_mono_put(&q, (uint8_t)i));
    CHECK(!rb_mono_put(&q, 99));                 /* 第 9 个被拒 */

    for (int i = 0; i < RB_CAP; i++)
        CHECK(rb_mono_get(&q, &v) && v == (uint8_t)i);
    CHECK(!rb_mono_get(&q, &v));

    /* 跨 uint8_t 边界（255→0）长跑：队列清零重开，塞取交错共 600 次操作，
     * 顺序号对 256 取模后与读出值逐一比对（在飞窗口 ≤8，无歧义）。 */
    q = (rb_mono_t){ {0}, 0, 0 };
    int n_put = 0, n_get = 0;
    for (int step = 0; step < 600; step++) {
        if (step % 2 == 0) {
            if (rb_mono_put(&q, (uint8_t)n_put))
                n_put++;
        } else {
            if (rb_mono_get(&q, &v)) {
                CHECK(v == (uint8_t)n_get);
                n_get++;
            }
        }
    }
    while (rb_mono_get(&q, &v)) {                /* 排干尾货 */
        CHECK(v == (uint8_t)n_get);
        n_get++;
    }
    CHECK(n_put == n_get);                       /* 一个不多一个不少 */
    CHECK(n_put > 256);                          /* 确实跨过了 255→0 回绕 */
    CHECK(q.w == (uint8_t)n_put && q.r == (uint8_t)n_get); /* 索引=总数 mod 256 */
}

/* ------------------------------------------------------------------ main */

int main(void)
{
    probe_callback();
    probe_fsm();
    probe_ring_slot();
    probe_ring_mono();

    printf("环形缓冲容量对照：A 派（牺牲一格）可用 %d 格，B 派（单调索引）可用 %d 格\n",
           RB_CAP - 1, RB_CAP);
    printf("== 断言通过 %d/%d ==\n", g_pass, g_pass + g_fail);
    return g_fail == 0 ? 0 : 1;
}
