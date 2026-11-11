/*
 * ub.c —— UBSan 现场取证：让"未定义"三个字在运行期被点名
 *
 * 编译：gcc -std=c11 -O2 -fsanitize=undefined ub.c -o build/ub.exe
 * 预期：stderr 打出 signed integer overflow 的诊断（UBSan 默认不中止，只点名）。
 * 交叉链 / 无 ubsan 运行库的环境由 probe.sh 自动跳过这一步。
 */
#include <limits.h>
#include <stdio.h>

int main(void)
{
    volatile int x = INT_MAX;   /* volatile 防止编译期折叠，逼出真实加法指令 */
    int y = x + 1;             /* ← UBSan 在这一行点名 */
    printf("INT_MAX + 1 = %d (0x%08X)\n", y, (unsigned)y);
    return 0;
}
