/**
 * main.c —— 位带（Bit-Band）操作演示：用别名地址原子翻转 PF6 红灯
 *
 * 位带原理（RM0090 §3.3.4）：
 *   Cortex-M4 把 SRAM 和外设的每一位都映射到一个"别名区"，
 *   对别名地址的 32 位写 = 对目标位的原子写（不扰邻居位）。
 *
 * 别名地址公式：
 *   alias_addr = alias_base + (byte_offset << 5) + (bit_number << 2)
 *
 * 外设位带区：0x42000000 ~ 0x43FFFFFF（映射 0x40000000 ~ 0x400FFFFF）
 *   GPIOF_ODR 在 0x40021414，bit6 的别名地址：
 *     0x42000000 + (0x14 << 5) + (6 << 2) = 0x42000298
 *
 * 对比 BSRR：BSRR 也是原子操作，但位带的好处是"读-改-写"不需要，
 *   直接写别名地址即可翻转指定位——适合需要频繁单比特操作的场景。
 *
 * 硬件：霸天虎 RGB 红灯 PF6（低电平点亮）
 */

#include <stdint.h>

/* ---------------- 寄存器地址（RM0090 §2.3 / §7.4 / §8.4） ---------------- */
#define PERIPH_BASE         0x40000000UL
#define AHB1PERIPH_BASE     (PERIPH_BASE + 0x00020000UL)

#define RCC_BASE            (AHB1PERIPH_BASE + 0x3800UL)
#define RCC_AHB1ENR         (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#define RCC_AHB1ENR_GPIOFEN (1UL << 5)

#define GPIOF_BASE          (AHB1PERIPH_BASE + 0x1400UL)
#define GPIOF_MODER         (*(volatile uint32_t *)(GPIOF_BASE + 0x00UL))
#define GPIOF_OTYPER        (*(volatile uint32_t *)(GPIOF_BASE + 0x04UL))
#define GPIOF_OSPEEDR       (*(volatile uint32_t *)(GPIOF_BASE + 0x08UL))
#define GPIOF_PUPDR         (*(volatile uint32_t *)(GPIOF_BASE + 0x0CUL))
#define GPIOF_ODR           (*(volatile uint32_t *)(GPIOF_BASE + 0x14UL))

/* 位带别名地址：GPIOF_ODR bit6 */
#define BITBAND_PERIPH_BASE 0x42000000UL
#define GPIOF_ODR_BIT6_ALIAS \
    (*(volatile uint32_t *)(BITBAND_PERIPH_BASE + ((GPIOF_BASE + 0x14UL - PERIPH_BASE) << 5) + (6 << 2)))

#define LED_R_PIN           6U

/* 粗略软件延时 */
static void delay(volatile uint32_t count)
{
    while (count--) {
        __asm__ volatile ("nop");
    }
}

int main(void)
{
    /* 第 1 步：开 GPIOF 时钟 */
    RCC_AHB1ENR |= RCC_AHB1ENR_GPIOFEN;

    /* 第 2 步：配 PF6 为通用推挽输出 */
    GPIOF_MODER   &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_MODER   |=  (1UL << (LED_R_PIN * 2));
    GPIOF_OTYPER  &= ~(1UL << LED_R_PIN);
    GPIOF_OSPEEDR &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_PUPDR   &= ~(3UL << (LED_R_PIN * 2));

    /* 第 3 步：位带操作翻转红灯 */
    while (1) {
        /* 写 0 到别名地址 = ODR bit6 清 0 = PF6 输出低 = 红灯亮 */
        GPIOF_ODR_BIT6_ALIAS = 0;
        delay(2000000);
        
        /* 写 1 到别名地址 = ODR bit6 置 1 = PF6 输出高 = 红灯灭 */
        GPIOF_ODR_BIT6_ALIAS = 1;
        delay(2000000);
    }
}
