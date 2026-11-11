/* probe.c —— C2《指针》章取证程序：一个文件喂两种工具链
 *
 *   1. arm-none-eabi-gcc -O2 -S（-mcpu=cortex-m4 -mthumb）
 *      → 看 read8/16/32、write8/16/32、next8/16/32、led_on_* 的汇编，
 *        证明「类型定访存宽度」「p[1] 的地址增量=类型宽度」「索引=偏移」。
 *   2. 宿主 gcc 真跑 main()
 *      → 打印 sizeof、指针运算字节增量、寄存器索引地址、const 三组合运行侧。
 *
 *   反例（必须编译失败）由 probe.sh 用 -DBAD_* 逐个触发。
 *
 * 寄存器地址/偏移照抄 code/stm32/00-blink/main.c:29,34（STM32F407 GPIOF）。
 */

#include <stdint.h>
#include <stddef.h>

/* ---------- 现场 1：类型定访存宽度（看汇编） ---------- */
uint8_t  read8 (const uint8_t  *p) { return *p; }
uint16_t read16(const uint16_t *p) { return *p; }
uint32_t read32(const uint32_t *p) { return *p; }

void write8 (uint8_t  *p, uint8_t  v) { *p = v; }
void write16(uint16_t *p, uint16_t v) { *p = v; }
void write32(uint32_t *p, uint32_t v) { *p = v; }

/* ---------- 现场 2：p[1] 的地址增量 = 类型宽度（看汇编 + 真跑） ---------- */
uint8_t  next8 (const uint8_t  *p) { return p[1]; }
uint16_t next16(const uint16_t *p) { return p[1]; }
uint32_t next32(const uint32_t *p) { return p[1]; }

/* ---------- 现场 3：寄存器块的索引访问 ---------- */
#define GPIOF_BASE_ADDR   0x40021400UL   /* 同 code/stm32/00-blink/main.c:29 */
#define GPIOF_BSRR_OFFSET 0x18UL         /* 同 code/stm32/00-blink/main.c:34 */

_Static_assert(6U * sizeof(uint32_t) == GPIOF_BSRR_OFFSET,
               "BSRR 在基址 +0x18，即 (uint32_t *)base 的第 6 个元素");

void led_on_indexed(void)   /* 数组索引写法 */
{
    ((volatile uint32_t *)GPIOF_BASE_ADDR)[6] = 1UL << (6U + 16U);
}

void led_on_macro(void)     /* 00-blink 的宏写法 */
{
    *(volatile uint32_t *)(GPIOF_BASE_ADDR + GPIOF_BSRR_OFFSET) = 1UL << (6U + 16U);
}

/* ---------- 现场 4：const 三组合 ---------- */
#if defined(BAD_WRITE_THROUGH_CONST_P)
void bad1(void) { int a = 0; const int *p = &a; *p = 1; }         /* 须报错 */
#elif defined(BAD_REPOINT_CONST_PTR)
void bad2(void) { static int a, b; int * const p = &a; p = &b; }  /* 须报错 */
#elif defined(BAD_BOTH_CONST)
void bad3(void) { int a = 0; const int * const p = &a; *p = 1; }  /* 须报错 */
#endif

/* ---------- 宿主真跑：步长、索引地址、const 运行侧 ---------- */
#include <stdio.h>

int main(void)
{
    uint8_t  a8[2]  = {0};
    uint16_t a16[2] = {0};
    uint32_t a32[2] = {0};
    uint8_t  *p8  = a8;
    uint16_t *p16 = a16;
    uint32_t *p32 = a32;

    printf("sizeof: uint8_t=%zu uint16_t=%zu uint32_t=%zu  指针自身=%zu 字节\n",
           sizeof(uint8_t), sizeof(uint16_t), sizeof(uint32_t), sizeof(void *));

    ptrdiff_t d8  = (const char *)(p8  + 1) - (const char *)p8;
    ptrdiff_t d16 = (const char *)(p16 + 1) - (const char *)p16;
    ptrdiff_t d32 = (const char *)(p32 + 1) - (const char *)p32;
    printf("p+1 字节增量: uint8_t* +%td  uint16_t* +%td  uint32_t* +%td\n",
           d8, d16, d32);
    if (d8 != 1 || d16 != 2 || d32 != 4) return 1;   /* 步长断言 */

    /* 索引地址 = 基址 + 下标 * 宽度（只取地址，不解引用，宿主上安全） */
    volatile uint32_t * const gpiof =
        (volatile uint32_t *)(uintptr_t)GPIOF_BASE_ADDR;
    printf("寄存器索引: &((uint32_t*)0x%08lX)[6] = 0x%08lX (= 基址 + 6*4 = +0x18)\n",
           (unsigned long)GPIOF_BASE_ADDR, (unsigned long)(uintptr_t)&gpiof[6]);
    if ((uintptr_t)&gpiof[6] != (uintptr_t)GPIOF_BASE_ADDR + GPIOF_BSRR_OFFSET)
        return 2;                                     /* 等价性断言 */

    /* const 三组合的合法半边 */
    int a = 1, b = 2;
    const int *pc = &a;
    pc = &b;                       /* const int*：可以换指向 */
    int * const cp = &a;
    *cp = 42;                      /* int* const：可以改内容 */
    const int * const cpc = &b;    /* 全锁：只能读 */
    printf("const 三组合(合法半边): *pc=%d *cp=%d *cpc=%d\n", *pc, *cp, *cpc);
    printf("驱动惯用法: volatile uint32_t * const gpiof = 0x%08lX"
           "（指针锁死，目标可被硬件改）\n", (unsigned long)(uintptr_t)gpiof);

    printf("全部断言通过\n");
    return 0;
}
