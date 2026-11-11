/* link_probe.c —— B3 链接脚本取证的标本
 *
 * 三个全局变量刻意分三类，让 .data / .bss 在图纸里同时在场：
 *   g_live  有初值      → .data（身在 RAM，行李存 Flash）
 *   g_dark  零初值      → .bss（不占 Flash，启动清零）
 *   g_big   4KB 没初值  → .bss（专门用来把 RAM 撑爆）
 *
 * RAM 用量必须能用手算复核：
 *   .data 4 + .bss (4 + 4096) + _user_heap_stack (0x200 + 0x400 = 1536) = 5640 B
 * 这个 5640 就是 `-Wl,--print-memory-usage` 报出来的那个数，
 * 也是把 RAM LENGTH 改成 2K 之后 `overflowed by 3592 bytes` 的左半边
 * （5640 − 2048 = 3592，与 ld 的报错一字不差）。
 *
 * 加 -DWITH_CCM 再多一个住自定义段的 g_ccm——CCM 那一刀用它连演三态：
 * 图纸没留房间（orphan 被塞进 SRAM 的 0x20000004）、留了房间没写 AT>（objcopy 撑出
 * 134,217,744 字节的 bin）、补上 AT> FLASH（bin 收回到 576 字节，但启动文件不搬它，
 * 初值照旧到不了 CCM）。
 */

volatile int g_live = 0x5A5A;
volatile int g_dark;
char g_big[4096];

#ifdef WITH_CCM
__attribute__((section(".ccmram"), used)) int g_ccm[4] = { 1, 2, 3, 4 };
#endif

int main(void)
{
    g_dark = g_live + g_big[0];
#ifdef WITH_CCM
    g_dark += g_ccm[0];
#endif
    return g_dark;
}
