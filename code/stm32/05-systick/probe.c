/* probe.c —— S5《SysTick：内核的心跳》全部宿主侧取证
 *
 * 一条命令跑完：sh probe.sh（宿主 gcc 真跑 + arm-none-eabi 交叉验证）
 * 本文件是纯 C11：同一源码宿主 gcc 与 arm-none-eabi-gcc 都能编。
 *
 * 寄存器/位定义的权威来源（章内逐条引用行号）：
 *   .trellis/ref/cmsis/core_cm4.h:764-770   SysTick_Type 结构体（CTRL/LOAD/VAL/CALIB）
 *   .trellis/ref/cmsis/core_cm4.h:773-783   CTRL 四个位
 *   .trellis/ref/cmsis/core_cm4.h:786-791   LOAD/VAL 只有低 24 位
 *   .trellis/ref/cmsis/core_cm4.h:793-801   CALIB（NOREF/SKEW/TENMS）
 *   .trellis/ref/cmsis/core_cm4.h:1550,1555 基地址拼装
 *   .trellis/ref/cmsis/core_cm4.h:2022-2036 SysTick_Config 函数体
 */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

static int g_pass = 0, g_total = 0;
#define CHECK(cond) do {                                            \
    g_total++;                                                      \
    if (cond) { g_pass++; }                                         \
    else { printf("!! 断言失败 probe.c:%d: %s\n", __LINE__, #cond); } \
} while (0)

/* ---- 现场1：寄存器布局（镜像 core_cm4.h:764-770） -------------------- */
typedef struct {
    volatile uint32_t CTRL;   /* 偏移 0x000 控制与状态 */
    volatile uint32_t LOAD;   /* 偏移 0x004 重载值     */
    volatile uint32_t VAL;    /* 偏移 0x008 当前值     */
    volatile uint32_t CALIB;  /* 偏移 0x00C 校准（只读）*/
} SysTick_Model;

#define SCS_BASE      0xE000E000UL          /* core_cm4.h:1550 */
#define SYSTICK_BASE  (SCS_BASE + 0x0010UL) /* core_cm4.h:1555 */

/* CTRL 位（core_cm4.h:773-783） */
#define CTRL_ENABLE     (1UL << 0)    /* bit0  计数器使能        */
#define CTRL_TICKINT    (1UL << 1)    /* bit1  归零是否申请中断   */
#define CTRL_CLKSOURCE  (1UL << 2)    /* bit2  1=内核时钟 0=参考  */
#define CTRL_COUNTFLAG  (1UL << 16)   /* bit16 归零标志，读过自清 */

#define LOAD_MAX        0x00FFFFFFUL  /* core_cm4.h:786-787：24 位上限 */
#define F_CPU           168000000UL   /* S2 时钟树成果：SYSCLK=168MHz */

/* ---- 现场2：24 位倒数计数器模型 -------------------------------------- */
/* 硬件语义：使能后每个周期 VAL--；VAL 已经为 0 的那个周期归零重载、
 * 置 COUNTFLAG（若 TICKINT=1 同时申请中断）。所以从 LOAD 数到 0 再重载，
 * 一个完整周期是 LOAD+1 个时钟——这就是"减一"的由来。 */
typedef struct {
    uint32_t CTRL, LOAD, VAL;
    uint32_t n_reload;   /* 归零重载（=中断）次数 */
} Sim;

static void sim_cycle(Sim *s)
{
    if (!(s->CTRL & CTRL_ENABLE)) return;
    if (s->VAL == 0U) {
        s->VAL = s->LOAD;             /* 归零自动重载 */
        s->CTRL |= CTRL_COUNTFLAG;
        s->n_reload++;
    } else {
        s->VAL--;
    }
}

static void sim_run(Sim *s, uint32_t cycles)
{
    for (uint32_t i = 0; i < cycles; i++) sim_cycle(s);
}

/* 读 CTRL 这个动作本身清 COUNTFLAG（PM0214：read-to-clear） */
static uint32_t sim_read_ctrl(Sim *s)
{
    uint32_t v = s->CTRL;
    s->CTRL &= ~CTRL_COUNTFLAG;
    return v;
}

/* ---- 现场3：SysTick_Config 模型（镜像 core_cm4.h:2022-2036） --------- */
typedef struct {
    SysTick_Model r;
    uint8_t shp[12];   /* SCB->SHP，系统异常优先级字节数组 */
} Core;

/* F407 的 __NVIC_PRIO_BITS = 4（stm32f407xx.h:49）；SysTick_IRQn = -1（:75）。
 * NVIC_SetPriority 对负数 IRQn 走 SCB->SHP[((IRQn)&0xF)-4]，
 * 写入字节 = priority << (8-4)（core_cm4.h:1814-1824）。 */
static uint32_t model_SysTick_Config(Core *c, uint32_t ticks)
{
    if ((ticks - 1UL) > LOAD_MAX) return 1UL;   /* 2024-2027 行：超界拒配 */
    c->r.LOAD = ticks - 1UL;                    /* 2029 行 */
    c->shp[11] = (uint8_t)(15UL << 4);          /* 2030 行：(-1&0xF)-4=11，15<<4 */
    c->r.VAL  = 0UL;                            /* 2031 行 */
    c->r.CTRL = CTRL_CLKSOURCE | CTRL_TICKINT | CTRL_ENABLE; /* 2032-2034 行 */
    return 0UL;
}

/* us 微秒对应的 LOAD 值（频率/1e6*us 再减一） */
static uint32_t reload_for_us(uint32_t us)
{
    return (uint32_t)(F_CPU / 1000000UL * (unsigned long)us) - 1UL;
}

int main(void)
{
    /* ===== 1. 布局与地址 ===== */
    CHECK(offsetof(SysTick_Model, CTRL)  == 0x0U);
    CHECK(offsetof(SysTick_Model, LOAD)  == 0x4U);
    CHECK(offsetof(SysTick_Model, VAL)   == 0x8U);
    CHECK(offsetof(SysTick_Model, CALIB) == 0xCU);
    CHECK(SYSTICK_BASE == 0xE000E010UL);
    printf("[1] 布局：CTRL/LOAD/VAL/CALIB 偏移 = 0x%zX/0x%zX/0x%zX/0x%zX，"
           "SysTick_BASE = 0x%08lX（内核外设，所有 Cortex-M 通用）\n",
           offsetof(SysTick_Model, CTRL), offsetof(SysTick_Model, LOAD),
           offsetof(SysTick_Model, VAL), offsetof(SysTick_Model, CALIB),
           SYSTICK_BASE);

    /* ===== 2. 168MHz 下三种周期的 LOAD ===== */
    uint32_t l1ms  = reload_for_us(1000);
    uint32_t l100us = reload_for_us(100);
    uint32_t l10ms = reload_for_us(10000);
    CHECK(l1ms   == 167999UL);
    CHECK(l100us == 16799UL);
    CHECK(l10ms  == 1679999UL);
    printf("[2] 168MHz：1ms → LOAD=%lu，100us → LOAD=%lu，10ms → LOAD=%lu"
           "（= 周期周期数-1）\n",
           (unsigned long)l1ms, (unsigned long)l100us, (unsigned long)l10ms);

    /* ===== 3. 周期 = LOAD+1：模型跑 1680000 周期 ===== */
    Sim s = { CTRL_ENABLE | CTRL_TICKINT | CTRL_CLKSOURCE, 167999UL, 0UL, 0UL };
    sim_run(&s, 1680000UL);
    CHECK(s.n_reload == 10UL);
    printf("[3] 模型：LOAD=167999 跑 1680000 周期 → 归零重载 %lu 次"
           "（周期 = LOAD+1 = 168000 周期 = 1.000000ms）\n",
           (unsigned long)s.n_reload);

    /* 忘减一：LOAD=168000，周期变 168001。别指望在"次数"上露馅——
     * 同跑 1680000 个时钟，两种配置都是 10 次重载，差别在相位。 */
    Sim bad = { CTRL_ENABLE, 168000UL, 0UL, 0UL };
    sim_run(&bad, 1680000UL);
    CHECK(bad.n_reload == 10UL);   /* 第 10 次落在 1+9×168001=1512010 < 1680000 */
    /* 日漂移：每个"1ms"慢 1/168000，86400s × 1/168000 = 0.514s */
    CHECK(86400UL * 1000UL / 168000UL == 514UL);   /* 514 ms/天 */
    printf("    忘减一：同跑 1680000 周期两者都重载 %lu 次——差别不在次数在相位；"
           "每个 tick 慢 1/168000（5.95ppm），日漂移 %lums\n",
           (unsigned long)bad.n_reload, 86400UL * 1000UL / 168000UL);

    /* 相位才是铁证：逐周期跑，记下第 10 次重载落在第几个时钟 */
    Sim g2 = { CTRL_ENABLE, 167999UL, 0UL, 0UL };
    Sim b2 = { CTRL_ENABLE, 168000UL, 0UL, 0UL };
    uint32_t g_t10 = 0UL, b_t10 = 0UL;
    for (uint32_t i = 1UL; i <= 1700000UL && (g_t10 == 0UL || b_t10 == 0UL); i++) {
        uint32_t gp = g2.n_reload, bp = b2.n_reload;
        sim_cycle(&g2);
        sim_cycle(&b2);
        if (gp < 10UL && g2.n_reload == 10UL) g_t10 = i;
        if (bp < 10UL && b2.n_reload == 10UL) b_t10 = i;
    }
    CHECK(g_t10 == 1512001UL);          /* 1 + 9×168000 */
    CHECK(b_t10 == 1512010UL);          /* 1 + 9×168001 */
    CHECK(b_t10 - g_t10 == 9UL);        /* 9 个间隔，每个多欠 1 个时钟 */
    printf("    相位：第 10 次重载——正确配置在第 %lu 个时钟，忘减一在第 %lu 个，"
           "9 个间隔共欠 %lu 个时钟\n",
           (unsigned long)g_t10, (unsigned long)b_t10,
           (unsigned long)(b_t10 - g_t10));

    /* ===== 4. 24 位上限与"快 737 倍"经典 bug ===== */
    CHECK(LOAD_MAX == 16777215UL);
    /* 最长单次：LOAD+1 = 16777216 周期 = 16777216/168 us = 99864.38us */
    uint32_t max_us = (uint32_t)((LOAD_MAX + 1UL) / 168UL);
    CHECK(max_us == 99864UL);
    printf("[4] 24 位上限：LOAD 最大 %lu（0xFFFFFF）→ 最长单次 %luus"
           "（≈99.86ms，1ms tick 无压力，100ms 单次不行）\n",
           (unsigned long)LOAD_MAX, (unsigned long)max_us);

    Core c = { {0,0,0,0}, {0} };
    CHECK(model_SysTick_Config(&c, 16800000UL) == 1UL);  /* 请求 100ms：被拒 */
    CHECK(c.r.LOAD == 0UL);                              /* 寄存器没被写坏   */
    /* 经典 bug：不查返回值、强行掩码写 LOAD */
    uint32_t bad_load = (16800000UL - 1UL) & LOAD_MAX;
    CHECK(bad_load == 22783UL);
    /* 实际周期 22784 周期 = 135.6us，比请求的 100ms 快 737 倍 */
    CHECK(16800000UL / 22784UL == 737UL);
    printf("    请求 100ms（ticks=16800000）：SysTick_Config 返回 1 拒配；"
           "若强行 &0xFFFFFF → LOAD=%lu，tick 变成 135.6us，ISR 狂跳 737 倍速\n",
           (unsigned long)bad_load);

    /* ===== 5. tick↔时间整数换算与 uint32_t 回绕 ===== */
    /* 168MHz：1 周期 = 1000/168 ns = 125/21 ns ≈ 5.952ns，整数除法向零截断 */
    CHECK(1UL * 1000UL / 168UL == 5UL);       /* 1 周期 → 5ns（真值 5.952） */
    CHECK(168UL * 1000UL / 168UL == 1000UL);  /* 168 周期 → 1000ns = 1us，整 us 无损 */
    CHECK(1000UL * 1000UL / 168UL == 5952UL); /* 1000 周期 → 5952ns = 5.952us */
    printf("[5] 换算：1 周期 = 125/21 ns ≈ 5.952ns；整数公式 ns=c*1000/168："
           "c=1 → 5ns、c=168 → 1000ns=1us（整 us 无损）、"
           "c=1000 → 5952ns=5.952us（按整数 us 取 5us，丢 0.952us）\n");

    /* uint32_t 毫秒计数器：2^32 ms = 49.71 天回绕 */
    CHECK(4294967296ULL / 86400000ULL == 49ULL);
    /* 无符号减法天然抗回绕 */
    uint32_t then = 0xFFFFFC18UL;   /* = 2^32-1000 = 4294966296，回绕前 1000ms */
    uint32_t now  = 5000UL;         /* 回绕后 */
    CHECK((uint32_t)(now - then) == 6000UL);
    /* 超时判断正确姿势：(now - then) >= timeout */
    CHECK((uint32_t)(now - then) >= 5999UL);
    CHECK(!((uint32_t)(now - then) >= 6001UL));
    /* 错误姿势：now >= then + timeout——then+timeout 尚未回绕、now 已回绕时误判 */
    uint32_t timeout = 500UL;       /* then+500 = 4294966796，没回绕 */
    uint32_t now2 = 2000UL;         /* 真实 elapsed = 3000ms ≥ 500ms → 已超时 */
    CHECK((uint32_t)(now2 - then) == 3000UL);
    CHECK((uint32_t)(now2 - then) >= timeout);     /* 正确写法：判为超时 */
    CHECK((now2 >= then + timeout) == 0);          /* 朴素写法：误判为未超时！ */
    unsigned long long days10 = 4294967296ULL * 10ULL / 86400000ULL;
    printf("    回绕：uint32_t ms 计数 %llu.%llu 天绕一圈；"
           "then=0x%08lX now=5000 → (now-then)=%lums（无符号减法跨回绕正确）；"
           "而 now>=then+timeout 在 now=2000 时漏报未超时\n",
           days10 / 10ULL, days10 % 10ULL,
           (unsigned long)then, (unsigned long)(now - then));

    /* ===== 6. SysTick_Config 全貌：寄存器三写 + 优先级最低 ===== */
    Core k = { {0,0,0,0}, {0} };
    CHECK(model_SysTick_Config(&k, 168000UL) == 0UL);
    CHECK(k.r.LOAD == 167999UL);
    CHECK(k.r.VAL  == 0UL);
    CHECK(k.r.CTRL == (CTRL_CLKSOURCE | CTRL_TICKINT | CTRL_ENABLE));
    CHECK(k.r.CTRL == 0x7UL);
    CHECK(k.shp[11] == 0xF0U);              /* 15 << 4：4 位优先级的最低档 */
    CHECK((k.shp[11] >> 4) == 15U);
    printf("[6] SysTick_Config(168000)：LOAD=%lu VAL=%lu CTRL=0x%08lX，"
           "SHP[11]=0x%02X → 逻辑优先级 %lu（4 位里的最低档，RTOS 就要它在最低）\n",
           (unsigned long)k.r.LOAD, (unsigned long)k.r.VAL,
           (unsigned long)k.r.CTRL, k.shp[11],
           (unsigned long)(k.shp[11] >> 4));

    /* ===== 7. COUNTFLAG 读过自清：正确/错误读法对照 ===== */
    Sim a = { CTRL_ENABLE | CTRL_CLKSOURCE, 99UL, 0UL, 0UL };
    sim_run(&a, 100UL);   /* 一个周期，置 COUNTFLAG */
    CHECK((a.CTRL & CTRL_COUNTFLAG) != 0UL);
    uint32_t r1 = sim_read_ctrl(&a);
    uint32_t r2 = sim_read_ctrl(&a);
    CHECK((r1 & CTRL_COUNTFLAG) != 0UL);
    CHECK((r2 & CTRL_COUNTFLAG) == 0UL);
    printf("[7] COUNTFLAG：周期到后第一次读 CTRL=0x%08lX（有标志），"
           "紧接第二次读=0x%08lX（标志已被上一次读清掉）\n",
           (unsigned long)r1, (unsigned long)r2);

    /* 错误姿势：先读一次干别的，再读第二次查标志 → 永远查不到 */
    Sim b = { CTRL_ENABLE | CTRL_CLKSOURCE, 99UL, 0UL, 0UL };
    uint32_t got_right = 0, got_wrong = 0;
    for (int p = 0; p < 5; p++) {
        sim_run(&b, 100UL);
        if (sim_read_ctrl(&b) & CTRL_COUNTFLAG) got_right++;   /* 单次读 */
    }
    for (int p = 0; p < 5; p++) {
        sim_run(&b, 100UL);
        (void)sim_read_ctrl(&b);                               /* 偷看一眼 */
        if (sim_read_ctrl(&b) & CTRL_COUNTFLAG) got_wrong++;   /* 再查已没 */
    }
    CHECK(got_right == 5UL);
    CHECK(got_wrong == 0UL);
    printf("    对照：5 个周期里单读法数到 %lu 次；"
           "「先偷看再查」双读法数到 %lu 次——标志被第一次读偷走，延时死等\n",
           (unsigned long)got_right, (unsigned long)got_wrong);

    printf("HOST_ASSERTS=%d\n", g_total);
    printf("[宿主] 断言通过 %d/%d\n", g_pass, g_total);
    return (g_pass == g_total) ? 0 : 1;
}
