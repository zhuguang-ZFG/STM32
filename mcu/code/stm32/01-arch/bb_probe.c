/* bb_probe.c —— S1 位带别名取证（不需要开发板，只要交叉工具链）
 *
 *   ./probe.sh bitband    算别名地址 → 编译期断言 → 三种写法的真实反汇编
 *
 * 三件事一次说清：
 *   1. 别名地址是算出来的，不是查表查来的：式子来自 Cortex-M4 TRM，
 *      基址与 ODR 偏移来自 CMSIS `stm32f407xx.h`。编译期断言替我们验算。
 *   2. `|=` / `&=` / `^=` 落到反汇编都是 **读-改-写三步**，三步之间有窗口。
 *   3. 位带别名与 BSRR 都是**一条 str 写完**，不存在"先读回来"这一步。
 */

#include <stdint.h>

/* CMSIS stm32f407xx.h：GPIOF_BASE = AHB1PERIPH_BASE(0x40020000) + 0x1400 */
#define GPIOF_BASE   0x40021400UL
#define ODR_OFFSET   0x14u      /* GPIO_TypeDef 里第 6 个 uint32_t */
#define BSRR_OFFSET  0x18u
#define PERIPH_BB    0x40000000UL   /* 位带源区基址 */
#define PERIPH_ALIAS 0x42000000UL   /* 外设别名区基址（PERIPH_BB_BASE） */

typedef struct {
    volatile uint32_t MODER, OTYPER, OSPEEDR, PUPDR, IDR, ODR, BSRR, LCKR, AFRH, AFRL;
} GPIO_TypeDef;

#define GPIOF ((GPIO_TypeDef *)GPIOF_BASE)

/* Cortex-M4 TRM 的别名地址公式：一个位被映射成别名区里的一个字 */
#define BITBAND_ADDR(addr, bit) \
    (PERIPH_ALIAS + (((addr) - PERIPH_BB) << 5) + ((bit) << 2))

#define PF6   6u
#define ODR6  BITBAND_ADDR(GPIOF_BASE + ODR_OFFSET, PF6)

_Static_assert(GPIOF_BASE + ODR_OFFSET == 0x40021414UL, "ODR 地址");
_Static_assert(ODR6 == 0x42428298UL, "PF6 在 ODR 里的别名地址");
_Static_assert(BITBAND_ADDR(GPIOF_BASE + ODR_OFFSET, 0) == 0x42428280UL,
               "一个字节 8 位 → 别名区 8 个字，正好 32 字节");

volatile uint32_t *const PF6_ALIAS = (volatile uint32_t *)ODR6;

void or_bits(void)   { GPIOF->ODR |= (1UL << PF6); }
void and_bits(void)  { GPIOF->ODR &= ~(1UL << PF6); }
void xor_bits(void)  { GPIOF->ODR ^= (1UL << PF6); }
void alias_set(void) { *PF6_ALIAS = 1UL; }
void bsrr_set(void)  { GPIOF->BSRR = (1UL << PF6); }
