/*
 * probe.c —— C7《未定义行为与 MISRA-C 精要》取证代码（运行期部分）
 *
 *   1) 有符号溢出：x+1 > x 在数学上只有 INT_MAX 会输——UB 让编译器"有权"整段判真。
 *      编译档位/编译旗不同，读数可能不同（gcc 16 实测：-O0 与 -O2 都已折叠）。
 *   2) 移位越界：32 位操作数移 33 位是 UB（与有无符号无关）。-O0 下硬件移位器
 *      只认计数低 5 位（33&31=1 → 结果 2）；-O2 下编译器可以给出完全不同的答案。
 *   3) float 位模式读法：union（C11 允许的双关）与 memcpy（永远合法）必须给出同一位串。
 *
 * 纪律分工：故意违规、专供编译器警告现场抓人的片段（严格别名/数组越界/未初始化）
 * 放在 alias-violate.c / oob-static.c，由 probe.sh 单独触发——probe.c 自己保持 -Werror 清白。
 *
 * 断言口径：UB 的观察项没有"标准答案"，main 只打印现象、不做对错断言；
 *          断言只落在非 UB 的铁事实上（合法移位的结果、两种合法读法位级一致）。
 * 函数故意不写 static：交叉汇编（probe.sh 第 5 步）要按符号名单独取证。
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>

/* ① 有符号溢出：signed int 的 x+1 在 INT_MAX 处是 UB，编译器可假定它永不发生 */
int is_bigger_after_inc(int x) { return x + 1 > x; }

/* ② 移位越界：count 用参数走运行期，防止编译器在编译期就报错拦下 */
uint32_t shift_oob(uint32_t v, uint32_t count) { return v << count; }

/* ③ 位模式读法一：union 双关——C11 起对"写一个成员、读另一个"给出了正式说法 */
static uint32_t bits_union(float f)
{
    union { float f; uint32_t u; } pun;
    pun.u = 0u;
    pun.f = f;
    return pun.u;
}

/* ③ 位模式读法二：memcpy——标准层面永远合法，编译器会把它优化成一条 load */
static uint32_t bits_memcpy(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof u);
    return u;
}

int main(void)
{
    int pass = 0, total = 0;

    /* ①② 现象打印：读数随编译档位/编译旗而变——这正是 UB 的全部含义 */
    printf("is_bigger_after_inc(INT_MAX) = %d\n", is_bigger_after_inc(INT_MAX));
    printf("shift_oob(1u, 33u)          = %u\n", shift_oob(1u, 33u));

    /* 以下才是非 UB 的铁事实，才配得上断言 */
    total++;
    if (shift_oob(1u, 1u) == 2u) {  /* 合法移位：1 位，结果必然是 2 */
        pass++;
    }

    total++;
    /* 两种合法读法必须位级一致：1.0f 的 IEEE-754 位模式是 0x3F800000 */
    const uint32_t by_union = bits_union(1.0f);
    const uint32_t by_memcpy = bits_memcpy(1.0f);
    printf("bits_union(1.0f)            = 0x%08X\n", by_union);
    printf("bits_memcpy(1.0f)           = 0x%08X\n", by_memcpy);
    if (by_union == 0x3F800000u && by_memcpy == by_union) {
        pass++;
    }

    printf("== 断言通过 %d/%d（只断言非 UB 铁事实）==\n", pass, total);
    return pass == total ? 0 : 1;
}
