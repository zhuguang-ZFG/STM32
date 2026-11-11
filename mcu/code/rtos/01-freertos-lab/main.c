/**
 * main.c —— 01-freertos-lab：一个工程，五个场景（编译开关 DEMO_SCENE=1..5）
 *
 * 内核：上游 FreeRTOS-Kernel V11.1.0，ARM_CM4F 单核端口，heap_4。
 * 硬件：HSI 16MHz（不走 PLL），USART1 PA9/PA10 @115200 做日志。
 *
 * 场景与章节的对应：
 *   1 任务与 TCB（F1）：两个任务不同优先级，看抢占顺序与 vTaskList
 *   2 任务通知（F6）：xTaskNotifyGive / ulTaskNotifyTake，计数语义 vs 覆盖语义
 *   3 事件组（F6）：ANY/ALL 两类等待者，唤醒后统一汇总清位
 *   4 软件定时器（F6）：命令队列→守护任务→回调；回调慢会拖累别的定时器
 *   5 堆（F7）：heap_4 的相邻块合并与碎片：总空闲≠最大可分配块
 *
 * 一切结论都能在串口日志里直接看到；版本与配置见 FreeRTOSConfig.h。
 */

#include <stdint.h>
#include "FreeRTOS.h"
#include "task.h"
#include "event_groups.h"
#include "timers.h"
#include "semphr.h"

#ifndef DEMO_SCENE
#define DEMO_SCENE 1
#endif

/* ============================ 最小日志（无 libc） ============================ */

#define RCC_BASE      0x40023800UL
#define RCC_AHB1ENR   (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#define RCC_APB2ENR   (*(volatile uint32_t *)(RCC_BASE + 0x44UL))
#define GPIOA_MODER   (*(volatile uint32_t *)(0x40020000UL))
#define GPIOA_AFRH    (*(volatile uint32_t *)(0x40020000UL + 0x24UL))
#define USART1_SR     (*(volatile uint32_t *)(0x40011000UL + 0x00UL))
#define USART1_DR     (*(volatile uint32_t *)(0x40011000UL + 0x04UL))
#define USART1_BRR    (*(volatile uint32_t *)(0x40011000UL + 0x08UL))
#define USART1_CR1    (*(volatile uint32_t *)(0x40011000UL + 0x0CUL))

static void uart_init(void)
{
    RCC_AHB1ENR |= (1UL << 0);                    /* GPIOAEN */
    RCC_APB2ENR |= (1UL << 4);                    /* USART1EN */
    GPIOA_AFRH  = (GPIOA_AFRH  & ~0x00000FF0UL) | 0x00000770UL;  /* AF7 */
    USART1_BRR = 16000000UL / 115200UL;           /* HSI 16MHz → 139，误差 -0.08% */
    USART1_CR1 = (1UL << 13) | (1UL << 3) | (1UL << 2);          /* UE|TE|RE */
    /* PA9 占 bits 19:18、PA10 占 bits 21:20：掩码 0x000FC000，两个都写 10（复用） */
    GPIOA_MODER = (GPIOA_MODER & ~0x000FC000UL) | 0x00280000UL;
}

static void uart_putc(char c)
{
    while ((USART1_SR & (1UL << 7)) == 0UL) { }   /* TXE */
    USART1_DR = (uint8_t)c;
}

/* syscalls.c 的 _write 走这里；uart_putc 保持 static，console_putc 是对外出口 */
void console_putc(char c)
{
    uart_putc(c);
}

static void uart_puts(const char *s) { while (*s) uart_putc(*s++); }

static void uart_putdec(uint32_t v)
{
    char buf[10]; uint32_t i = 0;
    if (v == 0) { uart_putc('0'); return; }
    while (v) { buf[i++] = (char)('0' + v % 10); v /= 10; }
    while (i) uart_putc(buf[--i]);
}

/* tick | 标签 | 数字 的极简格式 */
static void log_line(const char *tag, uint32_t val)
{
    uart_putc('[');
    uart_putdec(xTaskGetTickCount());
    uart_puts("ms] ");
    uart_puts(tag);
    uart_puts(" = ");
    uart_putdec(val);
    uart_puts("\r\n");
}

/* ============================ 场景 1：任务与 TCB ============================ */
#if DEMO_SCENE == 1

static void task_low(void *arg)
{
    (void)arg;
    for (;;) {
        log_line("low  run", 1);
        vTaskDelay(pdMS_TO_TICKS(300));
    }
}

static void task_high(void *arg)
{
    (void)arg;
    for (;;) {
        log_line("high run", 1);
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

static void task_report(void *arg)
{
    static char buf[512];
    (void)arg;
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(2000));
        vTaskList(buf);                      /* 需要 configUSE_TRACE_FACILITY=1 */
        uart_puts("--- vTaskList ---\r\n");
        uart_puts(buf);
        uart_puts("\r\n");
    }
}

static void scene_start(void)
{
    /* 先建低优先级再建高优先级：high 一建好就抢占，直接演示抢占式调度 */
    xTaskCreate(task_low,  "low",  256, NULL, 1, NULL);
    xTaskCreate(task_high, "high", 256, NULL, 2, NULL);
    xTaskCreate(task_report, "rpt", 320, NULL, 1, NULL);
}

/* ============================ 场景 2：任务通知 ============================ */
#elif DEMO_SCENE == 2

static TaskHandle_t g_consumer;

static void task_producer(void *arg)
{
    (void)arg;
    for (;;) {
        /* eIncrement：计数语义——来一次加一，通知值就是"欠了多少次" */
        xTaskNotifyGive(g_consumer);
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

static void task_consumer(void *arg)
{
    (void)arg;
    for (;;) {
        /* ulTaskNotifyTake(pdTRUE)：阻塞到计数非零，并把计数清零（取走） */
        uint32_t got = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        log_line("took", got);                 /* got > 1 说明消费比生产慢 */
    }
}

static void scene_start(void)
{
    xTaskCreate(task_consumer, "consumer", 256, NULL, 2, &g_consumer);
    xTaskCreate(task_producer, "producer", 256, NULL, 1, NULL);
}

/* ============================ 场景 3：事件组 ============================ */
#elif DEMO_SCENE == 3

#define EV_BIT0 (1UL << 0)
#define EV_BIT1 (1UL << 1)

static EventGroupHandle_t g_ev;

static void task_wait_any(void *arg)
{
    (void)arg;
    for (;;) {
        EventBits_t b = xEventGroupWaitBits(g_ev, EV_BIT0,
                          pdTRUE /*退出即清*/, pdFALSE /*ANY*/, portMAX_DELAY);
        log_line("ANY woke", b & EV_BIT0 ? 1 : 0);
    }
}

static void task_wait_all(void *arg)
{
    (void)arg;
    for (;;) {
        EventBits_t b = xEventGroupWaitBits(g_ev, EV_BIT0 | EV_BIT1,
                          pdTRUE, pdTRUE /*ALL*/, portMAX_DELAY);
        log_line("ALL woke", (b & (EV_BIT0 | EV_BIT1)) == (EV_BIT0 | EV_BIT1) ? 1 : 0);
    }
}

static void task_sender(void *arg)
{
    (void)arg;
    vTaskDelay(pdMS_TO_TICKS(500));
    for (;;) {
        xEventGroupSetBits(g_ev, EV_BIT0);     /* 只满足 ANY */
        vTaskDelay(pdMS_TO_TICKS(500));
        xEventGroupSetBits(g_ev, EV_BIT1);     /* 两个都齐 → ALL 也醒 */
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

static void scene_start(void)
{
    g_ev = xEventGroupCreate();
    xTaskCreate(task_wait_any, "waitANY", 256, NULL, 2, NULL);
    xTaskCreate(task_wait_all, "waitALL", 256, NULL, 2, NULL);
    xTaskCreate(task_sender,   "sender",  256, NULL, 1, NULL);
}

/* ============================ 场景 4：软件定时器 ============================ */
#elif DEMO_SCENE == 4

static void cb_fast(TimerHandle_t t)
{
    (void)t;
    log_line("fast cb", 1);
}

static void cb_slow(TimerHandle_t t)
{
    (void)t;
    /* 故意磨蹭 ~50ms：守护任务是串行执行回调的，它磨蹭多久，
     * 排在后面的定时器就迟到多久——这不是 bug，是模型。
     * 本机模拟实测（code/rtos/06-timers/sim_daemon.c 幕 B）：fast 的最大迟到恰好 50 拍。
     * 改成 200ms 就跨过 Σ(耗时/周期)=1 那条线（幕 C），迟到开始超出耗时本身并连环补拍。 */
    uint32_t t0 = xTaskGetTickCount();
    while ((xTaskGetTickCount() - t0) < 50) { /* 忙等，不许 vTaskDelay */ }
    log_line("slow cb", 1);
}

static void scene_start(void)
{
    TimerHandle_t fast = xTimerCreate("fast", pdMS_TO_TICKS(100), pdTRUE, 0, cb_fast);
    TimerHandle_t slow = xTimerCreate("slow", pdMS_TO_TICKS(120), pdTRUE, 0, cb_slow);
    xTimerStart(fast, 0);
    xTimerStart(slow, 0);
    /* 守护任务是 configTIMER_TASK_PRIORITY（本工程=最高 4） */
}

/* ============================ 场景 5：堆 ============================ */
#elif DEMO_SCENE == 5

static void heap_report(const char *tag)
{
    log_line(tag, xPortGetFreeHeapSize());
    log_line("min-ever", xPortGetMinimumEverFreeHeapSize());
}

static void scene_start(void)
{
    heap_report("boot free");

    void *a = pvPortMalloc(1024);
    void *b = pvPortMalloc(1024);
    void *c = pvPortMalloc(1024);
    heap_report("after ABC");

    vPortFree(b);                              /* 中间那个空了 */
    heap_report("after free B");

    void *big = pvPortMalloc(2048);
    log_line("big ok?", big != NULL ? 1 : 0);  /* 总空闲够，但最大连续块不够 → 0 */

    vPortFree(a);                              /* A 与 B 相邻 → heap_4 会合并 */
    heap_report("after free A");

    big = pvPortMalloc(2048);
    log_line("big ok?2", big != NULL ? 1 : 0); /* 合并后成了 */
    (void)c;
}

#endif

/* ============================ 场景 6：优先级反转（E04） ============================ */
#if DEMO_SCENE == 6

/*
 * 三任务演一出戏：L 拿锁干长活，H 等锁，M 死循环抢占 L。
 * 信号量版：H 被 M 间接阻塞（反转）；互斥量版：L 被继承抬级，M 插不进（修复）。
 * 对应实验：E04 优先级反转复现。
 */
static SemaphoreHandle_t g_lock;   /* 同一个句柄，编译期选 sem 或 mutex */

/*
 * 反转只在"真占 CPU"时出现：如果 L 的临界区写成 vTaskDelay(3000)，L 是睡着的，
 * M 抢不抢它都 3 秒后醒，H 的等待两版一样长，实验就演不出来。
 * 所以 L 用 cpu_work_ms 消耗"自己真正跑到的"毫秒数（被抢占的时间不算）；
 * M 用 busy_until 连续占满 CPU 一段墙钟时间，期间不阻塞。
 */
static void cpu_work_ms(uint32_t ms)
{
    while (ms > 0) {
        TickType_t t = xTaskGetTickCount();
        while (xTaskGetTickCount() == t) { }   /* 跑满当前这一拍 */
        if (xTaskGetTickCount() - t == 1U) {   /* 只经过 1 拍 = 这 1ms 是我自己跑的 */
            ms--;
        }                                      /* 跨了多拍 = 中间被抢占过，不计 */
    }
}

static void busy_until(TickType_t deadline)
{
    while ((int32_t)(xTaskGetTickCount() - deadline) < 0) { }
}

static void park_forever(void)
{
    for (;;) {
        vTaskDelay(portMAX_DELAY);   /* 单次剧本：演完就睡，日志只有一轮，复位重演 */
    }
}

static void task_low(void *arg)
{
    (void)arg;
    log_line("L take", 0);
    xSemaphoreTake(g_lock, portMAX_DELAY);
    log_line("L got lock, cpu work 3000ms", 0);
    cpu_work_ms(3000);                 /* 临界区：3000ms 的真实 CPU 工作量 */
    log_line("L give", 0);
    xSemaphoreGive(g_lock);
    park_forever();
}

static void task_mid(void *arg)
{
    (void)arg;
    vTaskDelay(pdMS_TO_TICKS(500));    /* 错峰：等 L 拿到锁后再启动 */
    log_line("M burst start, until ms", 4500);
    busy_until(pdMS_TO_TICKS(4500));   /* 不碰锁、不阻塞，连续占 CPU 到 t=4500ms */
    log_line("M burst end", 0);
    park_forever();
}

static void task_high(void *arg)
{
    (void)arg;
    vTaskDelay(pdMS_TO_TICKS(1000));   /* 等 L 进临界区、M 在跑后再要锁 */
    log_line("H want lock", 0);
    uint32_t t0 = xTaskGetTickCount();
    xSemaphoreTake(g_lock, portMAX_DELAY);
    uint32_t waited = xTaskGetTickCount() - t0;
    log_line("H got lock, waited ms", waited);   /* 理论值：信号量版 ≈6000，互斥量版 ≈2500 */
    log_line("H give", 0);
    xSemaphoreGive(g_lock);
    park_forever();
}

static void scene_start(void)
{
    /* 编译期二选一：USE_MUTEX=1 用互斥量（带继承），=0 用二值信号量（无继承） */
#ifdef USE_MUTEX
    g_lock = xSemaphoreCreateMutex();
    uart_puts("scene=6 mutex (with inheritance)\r\n");
#else
    g_lock = xSemaphoreCreateBinary();
    xSemaphoreGive(g_lock);   /* binary sem 初始空，先 give 让 L 能 take */
    uart_puts("scene=6 binary sem (no inheritance)\r\n");
#endif
    xTaskCreate(task_low,  "L", configMINIMAL_STACK_SIZE, NULL, 1, NULL);  /* 优先级 1=低 */
    xTaskCreate(task_mid,  "M", configMINIMAL_STACK_SIZE, NULL, 2, NULL);  /* 优先级 2=中 */
    xTaskCreate(task_high, "H", configMINIMAL_STACK_SIZE, NULL, 3, NULL);  /* 优先级 3=高 */
}

#endif

/* ============================ main ============================ */

void vApplicationStackOverflowHook(TaskHandle_t t, char *name)
{
    (void)t;
    uart_puts("STACK OVERFLOW in ");
    uart_puts(name);
    uart_puts("\r\n");
    for (;;) { }
}

int main(void)
{
    uart_init();
    uart_puts("freertos-lab scene=");
    uart_putdec(DEMO_SCENE);
    uart_puts("\r\n");

    scene_start();
    vTaskStartScheduler();

    for (;;) { }                               /* 调度器一旦起来就回不到这里 */
}