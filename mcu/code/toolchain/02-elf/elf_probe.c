/* elf_probe.c —— B2 章的解剖标本：一个刻意"五脏俱全"的小固件
 *
 * 五个对象，正好占满 ELF 的四种归宿：
 *   g_init → .data（Flash 有镜像、RAM 有本体，VMA≠LMA）
 *   g_zero → .bss（NOBITS，文件里查无此人）
 *   g_msg  → .data（数组本体在 RAM，初值字节躺在 Flash 的镜像里）
 *   tag    → .rodata，本工程链接脚本把它并进 .text（-DTAG_RAM 可切成 .data 对照）
 *   buf    → .bss
 *
 * 不需要开发板：所有结论都从 ELF 里读出来。跑 ./probe.sh 一次拿全。
 */

#include <stdint.h>

int g_init = 0x1234ABC5;         /* .data */
int g_zero;                      /* .bss */
char g_msg[] = "hello";          /* .data：6 字节本体 */

#ifdef TAG_RAM
uint8_t tag[8] = { 'M', 'C', 'U', 0, 0, 0, 0, 0 };   /* .data：占 RAM 又占 Flash */
#else
const uint8_t tag[8] = { 'M', 'C', 'U', 0, 0, 0, 0, 0 }; /* .rodata→.text：只占 Flash */
#endif

uint32_t buf[4];                 /* .bss */

static void sink(const volatile void *p) { (void)p; }

int main(void)
{
    sink(&g_init);
    sink(&g_zero);
    sink(g_msg);
    sink(tag);
    sink(buf);
    for (;;) { }
}
