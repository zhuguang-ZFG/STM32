/* probe.c —— C6 调用约定与栈帧取证（宿主可跑，交叉可看反汇编）
 *
 * 六个实验函数，每个对应章内一节：
 *   add2      叶子函数：不调用任何人 → prologue 不需要 push {lr}
 *   sum6      6 个 int 参数：r0–r3 装前 4 个，第 5、6 个由调用方写上栈
 *   add64     两个 long long：每个占一对偶奇寄存器（x=r0:r1，y=r2:r3）
 *   mix       int + long long：64 位参数必须对齐到偶数寄存器 → r1 被跳过
 *   add_d     两个 double：硬浮点 ABI 下走 d0/d1（对照组：不占 r0:r1）
 *   non_leaf  带局部数组、内部再调用 → push {r4, lr} + sub sp + pop {r4, pc}
 *
 * 宿主侧打印"活"的栈数值：sp 在被调函数体内往下走了多少、buf 离 sp 多远。
 * 交叉侧（arm-none-eabi-gcc -O2）只编译不运行，用 objdump 看指令。
 */
#include <stdint.h>
#include <stdio.h>

/* ---- 读当前栈指针（各架构一条内联汇编；都不认识就用局部变量地址近似） ---- */
static uintptr_t read_sp(void)
{
    uintptr_t v;
#if defined(__x86_64__)
    __asm__ volatile("mov %%rsp, %0" : "=r"(v));
#elif defined(__arm__)
    __asm__ volatile("mov %0, sp" : "=r"(v));
#else
    volatile uintptr_t t = 0;
    v = (uintptr_t)&t;
#endif
    return v;
}

/* ---- 实验 1：叶子函数（对照组） ---- */
__attribute__((noinline))
int add2(int a, int b)
{
    return a + b;
}

/* ---- 实验 2：6 个参数，寄存器不够分了 ---- */
__attribute__((noinline))
int sum6(int a, int b, int c, int d, int e, int f)
{
    return a + b + c + d + e + f;
}

/* ---- 实验 3：64 位参数占寄存器对 ---- */
__attribute__((noinline))
long long add64(long long x, long long y)
{
    return x + y;
}

__attribute__((noinline))
long long mix(int tag, long long v)
{
    return tag + v;
}

/* ---- 实验 4：double 在硬浮点 ABI 下的对照 ---- */
__attribute__((noinline))
double add_d(double a, double b)
{
    return a + b;
}

/* ---- 实验 5：非叶子函数与它的栈帧 ---- */
static uintptr_t g_sp_callee;   /* non_leaf 体内的 sp（prologue 之后） */
static uintptr_t g_buf_addr;    /* non_leaf 局部数组 buf 的地址 */

__attribute__((noipa))   /* noipa：禁用一切过程间分析——调用方只能按 ABI 假定 r0–r3/r12 全被改写，
                             想活过这次调用的值只能放进被调用者保存寄存器（r4–r11），r4 由此登场 */
void sink(void *p)
{
    /* 空函数 + memory clobber：拿到 p 就必须让 buf 真实存在于内存（栈）里 */
    __asm__ volatile("" :: "r"(p) : "memory");
}

__attribute__((noinline))
int non_leaf(int x)
{
    char buf[16];
    buf[0] = (char)(x & 0xFF);
    g_sp_callee = read_sp();
    g_buf_addr  = (uintptr_t)buf;
    sink(buf);                  /* buf 的地址被交出去 → 编译器不敢把它塞进寄存器 */
    return add2(x, buf[0]) + 1; /* +1：拿到返回值后还有活要干 → 不能尾调用；
                                   bl add2 会覆盖 lr → prologue 必须保存 lr */
}

int main(void)
{
    int pass = 0;
    const int total = 9;
    uintptr_t sp_main = read_sp();   /* 调用前的 sp（≈ non_leaf prologue 之前的值） */

    int       r2  = add2(1, 2);
    int       r6  = sum6(1, 2, 3, 4, 5, 6);
    long long r64 = add64(0x100000000LL, 0x200000001LL);
    long long rm  = mix(7, 0x100000000LL);
    double    rd  = add_d(0.5, 0.25);
    int       rn  = non_leaf(40);

    /* 行为断言：函数语义不因传参方式改变 */
    if (r2  == 3)                       pass++;
    if (r6  == 21)                      pass++;
    if (r64 == 0x300000001LL)           pass++;
    if (rm  == 0x100000007LL)           pass++;
    if (rd  == 0.75)                    pass++;
    if (rn  == 81)                      pass++;
    /* 布局断言：栈向下生长；buf 落在本帧之内（sp_callee ≤ buf < sp_main） */
    if (g_sp_callee < sp_main)                                   pass++;
    if (g_buf_addr >= g_sp_callee && g_buf_addr < sp_main)       pass++;
    if ((sp_main - g_sp_callee) % 8 == 0)                        pass++;  /* 帧按 8 字节对齐 */

    printf("sp(main, 调用前)      = 0x%llx\n", (unsigned long long)sp_main);
    printf("sp(non_leaf 体内)     = 0x%llx\n", (unsigned long long)g_sp_callee);
    printf("一帧吃掉的栈          = %llu 字节（两次 sp 之差，含返回地址+保存寄存器+buf）\n",
           (unsigned long long)(sp_main - g_sp_callee));
    printf("buf 地址              = 0x%llx\n", (unsigned long long)g_buf_addr);
    printf("buf 距 sp(non_leaf)   = %llu 字节\n",
           (unsigned long long)(g_buf_addr - g_sp_callee));
    printf("sum6(1,2,3,4,5,6)     = %d（第 5、6 个参数 5、6 是走栈送进去的）\n", r6);
    printf("add64(0x100000000, 0x200000001) = 0x%llx（64 位结果走寄存器对回来）\n",
           (unsigned long long)r64);
    printf("mix(7, 0x100000000)   = 0x%llx\n", (unsigned long long)rm);
    printf("non_leaf(40)          = %d\n", rn);
    printf("== 断言通过 %d/%d ==\n", pass, total);
    return pass == total ? 0 : 1;
}
