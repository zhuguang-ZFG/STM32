/* 五个符号，五种落址。全部只靠 nm 与 .map 指认，不需要开发板。
 *
 * 这一集要立的规矩：Cache 关闭期间，只有内部存储（IRAM/DRAM/ROM）里的
 * 东西取得到。所以"ISR 能不能在关 Cache 时跑"不是标一个 IRAM_ATTR 就完事，
 * 而是整条链——本体、被调用的函数、读到的常量——每一环都要落在内部存储。
 *
 * 每个 helper 都强制 noinline：链条断没断，得让 nm 看得见，
 * 不能靠编译器今天心情好内联掉了、明天没内联。
 */
#include <stdint.h>
#include "esp_attr.h"

volatile uint32_t g_hits;

/* ① 什么都不标 —— 等着掉进 Flash 映射段 */
void isr_plain(void *arg)
{
    g_hits++;
}

/* ② 只标本体，helper 不标 —— 链子在这里断 */
void __attribute__((noinline)) helper_far(void)
{
    g_hits += 2;
}

void IRAM_ATTR isr_leaky(void *arg)
{
    helper_far();
}

/* ③ 整条链都标 —— 真正的 IRAM-safe */
void IRAM_ATTR __attribute__((noinline)) helper_near(void)
{
    g_hits += 3;
}

void IRAM_ATTR isr_tight(void *arg)
{
    helper_near();
}

/* ④ 代码进了 IRAM，读的常量还在 Flash —— 取数一样要过 Cache */
const uint32_t k_table[4] = { 0x11111111u, 0x22222222u, 0x33333333u, 0x44444444u };

void IRAM_ATTR isr_rodata(void *arg)
{
    g_hits += k_table[g_hits & 3u];
}

/* 真项目里这一步是 esp_intr_alloc(...)：把 ISR 交给驱动，符号自然有人引用。
 * 这里是探针工程，没人挂中断，而 IDF 默认开着 -Wl,--gc-sections ——
 * 实测：不钉住的话，上面七个符号一个都不在 ELF 里（nm 只剩 app_main 和 g_hits），
 * 链接器把整段当垃圾收了。这张表就是让链条活着被 nm 看见，顺便记下这个坑。 */
void (*volatile g_isr_table[4])(void *);

void app_main(void)
{
    g_hits = 0;
    g_isr_table[0] = isr_plain;
    g_isr_table[1] = isr_leaky;
    g_isr_table[2] = isr_tight;
    g_isr_table[3] = isr_rodata;
}
