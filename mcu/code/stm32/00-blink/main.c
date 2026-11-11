/**
 * main.c —— 寄存器级点灯：霸天虎板载 RGB 红灯（PF6，低电平点亮）
 *
 * 全过程只有三步，对应 GPIO 章节的"先时钟、再模式、后数据"：
 *   1. 开时钟：RCC_AHB1ENR 的 GPIOFEN 位（bit5）——不开时钟，
 *      外设寄存器写了也白写（这是新手第一大坑）。
 *   2. 配模式：MODER6=01(输出) / OTYPER6=0(推挽) / OSPEEDR6=00(低速) /
 *      PUPDR6=00(无上下拉)。
 *   3. 控数据：BSRR 低 16 位置位、高 16 位复位，写 1 有效写 0 无影响，
 *      所以读-改-写都不需要，一条赋值搞定（这就是 BSRR 存在的意义）。
 *
 * 硬件依据：霸天虎 RGB 灯共阳接 3.3V，阴极经限流电阻到 PF6/PF7/PF8，
 * 引脚输出低电平 → 灯亮（野火《库开发实战指南·寄存器点灯》）。
 *
 * 时钟说明：复位后默认跑 HSI 16MHz，点灯不需要 PLL；
 * HSE→PLL→168MHz 的配置见 stm32/02-rcc-clock 章。
 */

#include <stdint.h>

/* ---------------- 寄存器地址（RM0090 §2.3 / §7.4 / §8.4） ---------------- */
#define PERIPH_BASE         0x40000000UL
#define AHB1PERIPH_BASE     (PERIPH_BASE + 0x00020000UL)

#define RCC_BASE            (AHB1PERIPH_BASE + 0x3800UL)          /* 0x40023800 */
#define RCC_AHB1ENR         (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#define RCC_AHB1ENR_GPIOFEN (1UL << 5)                            /* GPIOF 时钟使能 */

#define GPIOF_BASE          (AHB1PERIPH_BASE + 0x1400UL)          /* 0x40021400 */
#define GPIOF_MODER         (*(volatile uint32_t *)(GPIOF_BASE + 0x00UL))
#define GPIOF_OTYPER        (*(volatile uint32_t *)(GPIOF_BASE + 0x04UL))
#define GPIOF_OSPEEDR       (*(volatile uint32_t *)(GPIOF_BASE + 0x08UL))
#define GPIOF_PUPDR         (*(volatile uint32_t *)(GPIOF_BASE + 0x0CUL))
#define GPIOF_BSRR          (*(volatile uint32_t *)(GPIOF_BASE + 0x18UL))

#define LED_R_PIN           6U    /* PF6 红灯；绿灯 PF7、蓝灯 PF8 同理 */

/* 粗略软件延时：HSI 16MHz 下约 0.5s（-O0 实测校准，本章不追求准） */
static void delay(volatile uint32_t count)
{
    while (count--) {
        __asm__ volatile ("nop");
    }
}

int main(void)
{
    /* 第 1 步：开 GPIOF 时钟（不先开时钟，下面全白配） */
    RCC_AHB1ENR |= RCC_AHB1ENR_GPIOFEN;

    /* 第 2 步：配 PF6 为通用推挽输出 */
    GPIOF_MODER   &= ~(3UL << (LED_R_PIN * 2));  /* 先清零        */
    GPIOF_MODER   |=  (1UL << (LED_R_PIN * 2));  /* 01 = 输出模式 */
    GPIOF_OTYPER  &= ~(1UL << LED_R_PIN);        /* 0  = 推挽     */
    GPIOF_OSPEEDR &= ~(3UL << (LED_R_PIN * 2));  /* 00 = 低速     */
    GPIOF_PUPDR   &= ~(3UL << (LED_R_PIN * 2));  /* 00 = 无上下拉 */

    /* 第 3 步：呼吸式闪烁 —— BSRR 高 16 位写 1 拉低（亮），低 16 位写 1 拉高（灭） */
    while (1) {
        GPIOF_BSRR = (1UL << (LED_R_PIN + 16));  /* BR6：输出低 → 红灯亮 */
        delay(2000000);
        GPIOF_BSRR = (1UL << LED_R_PIN);         /* BS6：输出高 → 红灯灭 */
        delay(2000000);
    }
}
