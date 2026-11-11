/*
 * C4 结构体与 ABI —— "写错一位"取证工程
 *
 * probe.c 证明的是"照抄官方顺序会得到什么"；这个工程证明反面：
 * 1. 少写一个寄存器（AFR[2] 写成 AFR），哪个偏移会变、哪个不会；
 * 2. 寄存器地图里的空洞没补保留字，字段会整体前移多少；
 * 3. 尾部填充到底在买什么（数组 stride）；
 * 4. #pragma pack(1) 真把洞消掉了，代价是谁的对齐。
 *
 * 全部数字由 broken.sh 在本机实测打印，不是推算。
 */

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>

/* ---- 1. 少写一个寄存器 ----
 * 官方 GPIO_TypeDef 有 9 个成员 / 10 个寄存器（AFR 是数组，占两格）。
 * 这里把 AFR[2] 写成单个 AFR，其余顺序一字未动。 */
typedef struct {
    volatile uint32_t MODER;    /* 0x00 */
    volatile uint32_t OTYPER;   /* 0x04 */
    volatile uint32_t OSPEEDR;  /* 0x08 */
    volatile uint32_t PUPDR;    /* 0x0C */
    volatile uint32_t IDR;      /* 0x10 */
    volatile uint32_t ODR;      /* 0x14 */
    volatile uint32_t BSRR;     /* 0x18 —— 仍然正确 */
    volatile uint32_t LCKR;     /* 0x1C */
    volatile uint32_t AFR;      /* BUG: 应为 AFR[2] */
} Short_t;

/* ---- 2. 地图里的空洞没补保留字 ----
 * 假想某外设地图：CR@0x00，RESERVED@0x04，DR@0x08。 */
typedef struct {
    volatile uint32_t CR;       /* 0x00 */
    volatile uint32_t DR;       /* BUG: 本该 0x08，被空洞顶到 0x04 */
} NoReserved_t;

typedef struct {
    volatile uint32_t CR;       /* 0x00 */
    volatile uint32_t RESERVED; /* 占位成员把后面的偏移按回原位 */
    volatile uint32_t DR;       /* 0x08 */
} WithReserved_t;

_Static_assert(offsetof(WithReserved_t, DR) == 0x08, "DR must be 0x08");
_Static_assert(sizeof(WithReserved_t) == 0x0C, "空洞必须由占位成员顶住");

/* ---- 3. 尾部填充买的是数组 stride ---- */
typedef struct {
    uint8_t  a;
    uint32_t b;
    uint8_t  c;
} Padded_t;

/* ---- 4. pack(1)：洞没了，对齐也没了 ---- */
#pragma pack(push, 1)
typedef struct {
    uint8_t  a;
    uint32_t b;
    uint8_t  c;
} Packed1_t;
#pragma pack(pop)

int main(void) {
    Padded_t arr[2];

    printf("=== C4 struct-abi broken probe ===\n\n");

    printf("--- 少写一个寄存器 ---\n");
    printf("Short_t: offsetof(BSRR) = 0x%02lX  sizeof = 0x%lX   (GPIO_TypeDef 应为 0x28)\n",
           (unsigned long)offsetof(Short_t, BSRR), (unsigned long)sizeof(Short_t));
    printf("offsetof(GPIO_TypeDef) 的正确写法见 probe.c：sizeof = 0x28\n\n");

    printf("--- 空洞没补保留字 ---\n");
    printf("NoReserved_t:  offsetof(DR) = 0x%lX   (手册说 0x08)\n",
           (unsigned long)offsetof(NoReserved_t, DR));
    printf("WithReserved_t: offsetof(DR) = 0x%lX\n\n",
           (unsigned long)offsetof(WithReserved_t, DR));

    printf("--- 尾部填充与数组 stride ---\n");
    printf("Padded_t: sizeof = %lu  a=%lu b=%lu c=%lu\n",
           (unsigned long)sizeof(Padded_t),
           (unsigned long)offsetof(Padded_t, a),
           (unsigned long)offsetof(Padded_t, b),
           (unsigned long)offsetof(Padded_t, c));
    printf("arr[1] - arr[0] = %ld 字节\n", (long)((char *)&arr[1] - (char *)&arr[0]));
    printf("arr[0].b 距基址 %ld 字节，arr[1].b 距基址 %ld 字节\n",
           (long)((char *)&arr[0].b - (char *)arr),
           (long)((char *)&arr[1].b - (char *)arr));
    printf("若 sizeof 只算到 c 结束的 9，arr[1].b 就会落在 %d —— 不再是 4 的倍数\n\n", 9 + 4);

    printf("--- pack(1) ---\n");
    printf("Packed1_t: sizeof = %lu  a=%lu b=%lu c=%lu   (b 落在 1 = 非对齐访问)\n",
           (unsigned long)sizeof(Packed1_t),
           (unsigned long)offsetof(Packed1_t, a),
           (unsigned long)offsetof(Packed1_t, b),
           (unsigned long)offsetof(Packed1_t, c));

    return 0;
}

/* 想亲眼看编译器拦住第一种错，把这两行放进工程再编译一次：
 *   _Static_assert(sizeof(Short_t) == 0x28, "GPIO_TypeDef size must be 0x28 (10 x uint32)");
 * broken.sh 会单独演示这次失败编译，并把编译器的原话打出来。 */
