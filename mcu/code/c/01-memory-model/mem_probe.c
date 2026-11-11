/* mem_probe.c —— 同一份源码，十一个对象的十一种归宿（C1 章取证工程）
 *
 * 不需要开发板：每个变量住在哪个段、占 Flash 还是 RAM，全部由
 * size / nm / readelf / objdump 从 ELF 里读出来。跑 ./probe.sh 一次拿全。
 *
 * 三个反直觉答案就藏在这里：g_zero（写了初值却在 .bss）、
 * auto_var（源码里有，符号表里查无此人）、lit（指针在栈上，字符串在 Flash）。
 */

#include <stdint.h>

/* 存在的唯一意义：把下面每个对象的地址"用一次"。
 * 不然 -fdata-sections + --gc-sections 会把没人碰的变量整段丢掉，
 * 你会以为"编译器把它优化没了"，其实是链接器把它回收了。 */
static void sink(const volatile void *p)
{
    (void)p;
}

/* ===== 文件作用域：段归属在链接期就定了 ===== */
int g_init = 5;                    /* 有初值 → .data：Flash 存粮票，RAM 住人 */
int g_zero = 0;                    /* 显式写 0 → .data 还是 .bss？ */
int g_uninit;                      /* 没初值 → .bss：只分房，不带行李 */
const int g_ro = 7;                /* const → .rodata：不动产，一辈子住 Flash */
const uint8_t k_tab[4] = {1, 2, 3, 4};  /* const 数组同样留 Flash */
static uint8_t s_buf[16];          /* static 全局 → .bss，只是别人看不见 */
volatile int g_flag = 1;           /* volatile 不改段归属，只改访问方式 */
char g_msg[] = "hi";               /* 数组本体在 .data，字面量"hi\0"在 .rodata */

/* ===== 函数作用域：static 与 auto 是两种寿命 ===== */
void probe(void)
{
    static uint8_t s_local[8];     /* .bss：写在函数里，寿命却是全程序 */
    int auto_var = 3;              /* 栈：函数返回即蒸发，符号表里没有它 */
    const char *lit = "flash";     /* 指针本身在栈上，指向的内容在 Flash */

    sink(&g_init);
    sink(&g_zero);
    sink(&g_uninit);
    sink(&g_ro);
    sink(k_tab);
    sink(s_buf);
    sink(&g_flag);
    sink(g_msg);
    sink(s_local);
    sink(&auto_var);
    sink(lit);
}

int main(void)
{
    probe();
    for (;;) { }                   /* 裸机惯例：别让 CPU 跑飞 */
}
