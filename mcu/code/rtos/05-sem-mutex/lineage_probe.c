/* lineage_probe.c —— 把「xSemaphore* 到底是什么」交给预处理器和链接器回答
 *
 * 这一集第一个要钉死的事：semphr.h 里那四个 xSemaphore* 到底是四个 API，
 * 还是四个别名。读源码能看到 #define，但看到 #define 不等于证明了调用最后落到哪。
 * 所以这里做两件不靠"读"的事：
 *   第 2 步：拿 -E 把本文件展开，数展开文本里还剩几个 xSemaphore 字样——
 *            应当一个不剩；再看四个 xQueue* 名字各出现几次。
 *   第 3 步：只 -c 不链，nm 读这个 .o 的未定义引用——里面必须只有 xQueue*，
 *            一个 xSemaphore* 都不该出现（宏不留符号，函数才会）。
 * 两个方向夹过来，"信号量 API 是队列 API 的宏别名"就不是我的一句话，是两张表。
 *
 * 每个 API 各占一个函数（配 -ffunction-sections），这样符号表里谁引用了谁能逐函数看。
 * 本文件永远不参与链接，也不烧板子：它是一台纯编译期的仪器。
 *
 * 事实基准：上游 FreeRTOS-Kernel tag V11.1.0。
 */

#include "FreeRTOS.h"
#include "semphr.h"

QueueHandle_t g_binary;
QueueHandle_t g_mutex;
QueueHandle_t g_counting;

void use_semaphore_create_binary(void)
{
    g_binary = xSemaphoreCreateBinary();
}

void use_semaphore_create_mutex(void)
{
    g_mutex = xSemaphoreCreateMutex();
}

void use_semaphore_create_counting(void)
{
    /* 第三个创建宏，走的是第三条不同的队列入口：这一档留给"计数 N"那条对照 */
    g_counting = xSemaphoreCreateCounting(4U, 2U);
}

BaseType_t use_semaphore_take(QueueHandle_t x, TickType_t t)
{
    return xSemaphoreTake(x, t);
}

BaseType_t use_semaphore_give(QueueHandle_t x)
{
    return xSemaphoreGive(x);
}
