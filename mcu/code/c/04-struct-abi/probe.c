/*
 * C4 结构体与 ABI —— 取证工程
 *
 * 目标：
 * 1. 用 offsetof/sizeof 验证 GPIO_TypeDef 的 BSRR=0x18、总大小=0x28；
 * 2. 手算 + 机器验证对齐三规则；
 * 3. 端序确认（小端）；
 * 4. 位域布局不可移植的证据。
 *
 * 事实来源：STM32F407xx CMSIS 头文件（stm32f407xx.h），
 * 成员顺序照抄官方定义，见 https://github.com/STMicroelectronics/cmsis_device_f4
 */

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

/* ---- 1. 最小 GPIO_TypeDef（照抄 CMSIS 成员顺序） ----
 * 第二来源：github.com/STMicroelectronics/cmsis_device_f4 master 分支
 * stm32f407xx.h 第 526-537 行，GPIO_TypeDef 共 10 个寄存器：
 * MODER/OTYPER/OSPEEDR/PUPDR/IDR/ODR/BSRR/LCKR/AFR[2]，无 BRR。 */
typedef struct {
    volatile uint32_t MODER;    /* 0x00 */
    volatile uint32_t OTYPER;   /* 0x04 */
    volatile uint32_t OSPEEDR;  /* 0x08 */
    volatile uint32_t PUPDR;    /* 0x0C */
    volatile uint32_t IDR;      /* 0x10 */
    volatile uint32_t ODR;      /* 0x14 */
    volatile uint32_t BSRR;     /* 0x18 */
    volatile uint32_t LCKR;     /* 0x1C */
    volatile uint32_t AFR[2];   /* 0x20-0x24 */
} GPIO_TypeDef;

/* 编译期硬断言：成员顺序错→编译失败。
 * 10 个寄存器 × 4 字节 = 40 = 0x28。 */
_Static_assert(offsetof(GPIO_TypeDef, BSRR) == 0x18,
               "BSRR offset must be 0x18");
_Static_assert(sizeof(GPIO_TypeDef) == 0x28,
               "GPIO_TypeDef size must be 0x28 (10 x uint32)");

/* ---- 2. 对齐三规则验证结构体（故意含洞） ---- */
typedef struct {
    uint8_t  a;      /* 偏移 0，占 1 字节 */
    /* 编译器插 3 字节填充 */
    uint32_t b;      /* 偏移 4，占 4 字节 */
    uint8_t  c;      /* 偏移 8，占 1 字节 */
    /* 尾部再填 3 字节，使总大小为 4 的倍数 */
} Padded_t;

_Static_assert(offsetof(Padded_t, b) == 4, "Padded_t.b at 4");
_Static_assert(sizeof(Padded_t) == 12, "Padded_t size 12 with tail padding");

/* 重排后零填充版本 */
typedef struct {
    uint32_t b;      /* 偏移 0 */
    uint8_t  a;      /* 偏移 4 */
    uint8_t  c;      /* 偏移 5 */
    /* 尾部 2 字节填充 */
} Packed_t;

_Static_assert(sizeof(Packed_t) == 8, "Packed_t size 8");

/* ---- 3. 端序检测 ---- */
static void endian_check(void) {
    uint32_t x = 0x12345678;
    uint8_t *p = (uint8_t *)&x;
    printf("endian: 0x12345678 stored as %02X %02X %02X %02X -> %s\n",
           p[0], p[1], p[2], p[3],
           (p[0] == 0x78) ? "little-endian" : "big-endian");
}

/* ---- 4. 位域布局不可移植 ---- */
typedef struct {
    uint32_t a : 1;
    uint32_t b : 2;
    uint32_t c : 5;
    uint32_t d : 24;
} Bitfield_1_t;

typedef struct {
    uint32_t d : 24;
    uint32_t c : 5;
    uint32_t b : 2;
    uint32_t a : 1;
} Bitfield_2_t;

/* 掩码宏替代方案（可移植） */
#define REG_FIELD_A_MASK  (1UL << 0)
#define REG_FIELD_B_MASK  (3UL << 1)
#define REG_FIELD_C_MASK  (31UL << 3)
#define REG_FIELD_D_MASK  (0xFFFFFFUL << 8)

static void bitfield_check(void) {
    printf("bitfield_1 sizeof=%zu, bitfield_2 sizeof=%zu\n",
           sizeof(Bitfield_1_t), sizeof(Bitfield_2_t));
    printf("bitfield layout is implementation-defined; "
           "use mask macros for hardware registers\n");
}

int main(void) {
    printf("=== C4 struct-abi probe ===\n\n");

    /* 1. GPIO_TypeDef 取证 */
    printf("--- GPIO_TypeDef offsets ---\n");
    printf("offsetof(MODER)   = 0x%02zX\n", offsetof(GPIO_TypeDef, MODER));
    printf("offsetof(OTYPER)  = 0x%02zX\n", offsetof(GPIO_TypeDef, OTYPER));
    printf("offsetof(OSPEEDR) = 0x%02zX\n", offsetof(GPIO_TypeDef, OSPEEDR));
    printf("offsetof(PUPDR)   = 0x%02zX\n", offsetof(GPIO_TypeDef, PUPDR));
    printf("offsetof(IDR)     = 0x%02zX\n", offsetof(GPIO_TypeDef, IDR));
    printf("offsetof(ODR)     = 0x%02zX\n", offsetof(GPIO_TypeDef, ODR));
    printf("offsetof(BSRR)    = 0x%02zX  <-- target: 0x18\n", offsetof(GPIO_TypeDef, BSRR));
    printf("offsetof(LCKR)    = 0x%02zX\n", offsetof(GPIO_TypeDef, LCKR));
    printf("offsetof(AFR)     = 0x%02zX\n", offsetof(GPIO_TypeDef, AFR));
    printf("sizeof(GPIO_TypeDef) = 0x%02zX  <-- target: 0x28\n\n", sizeof(GPIO_TypeDef));

    /* 2. 对齐三规则 */
    printf("--- alignment rules ---\n");
    printf("Padded_t: sizeof=%zu, offsets a=%zu b=%zu c=%zu\n",
           sizeof(Padded_t),
           offsetof(Padded_t, a),
           offsetof(Padded_t, b),
           offsetof(Padded_t, c));
    printf("Packed_t: sizeof=%zu, offsets a=%zu b=%zu c=%zu\n\n",
           sizeof(Packed_t),
           offsetof(Packed_t, a),
           offsetof(Packed_t, b),
           offsetof(Packed_t, c));

    /* 3. 端序 */
    endian_check();

    /* 4. 位域 */
    bitfield_check();

    printf("\n=== probe done ===\n");
    return 0;
}
