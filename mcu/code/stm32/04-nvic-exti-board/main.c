/**
 * main.c —— EXTI 外部中断演示：按键触发中断翻转红灯
 *
 * EXTI 三层链路（RM0090 §12 / §11）：
 *   1. EXTI 控制器：检测引脚边沿（上升/下降/双沿），置位挂起位
 *   2. NVIC 中断控制器：优先级仲裁，压栈跳转
 *   3. CPU 内核：执行 ISR，EXC_RETURN 返回
 *
 * 硬件连接：
 *   - PF6：板载红灯（低电平点亮）
 *   - PA0：板载按键 KEY1（按下接地，松开上拉）
 *
 * 配置步骤：
 *   1. 开时钟：RCC_AHB1ENR (GPIOA/GPIOF) + RCC_APB2ENR (SYSCFG)
 *   2. 配 GPIO：PA0 输入上拉，PF6 输出推挽
 *   3. SYSCFG_EXTICR1：PA0 映射到 EXTI0
 *   4. EXTI_IMR：使能 EXTI0 中断
 *   5. EXTI_RTSR：上升沿触发（按键松开时触发）
 *   6. NVIC：使能 EXTI0_IRQn，配优先级
 *   7. ISR：清挂起位 + 翻转 PF6
 *
 * 参考：[S4 NVIC 与 EXTI](../../docs/stm32/04-nvic-exti.md)
 */

#include <stdint.h>

/* ---------------- 寄存器地址 ---------------- */
#define PERIPH_BASE         0x40000000UL
#define AHB1PERIPH_BASE     (PERIPH_BASE + 0x00020000UL)
#define APB2PERIPH_BASE     (PERIPH_BASE + 0x00010000UL)

/* RCC */
#define RCC_BASE            (AHB1PERIPH_BASE + 0x3800UL)
#define RCC_AHB1ENR         (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#define RCC_APB2ENR         (*(volatile uint32_t *)(RCC_BASE + 0x44UL))
#define RCC_AHB1ENR_GPIOAEN (1UL << 0)
#define RCC_AHB1ENR_GPIOFEN (1UL << 5)
#define RCC_APB2ENR_SYSCFGEN (1UL << 14)

/* GPIOA (按键 PA0) */
#define GPIOA_BASE          (AHB1PERIPH_BASE + 0x0000UL)
#define GPIOA_MODER         (*(volatile uint32_t *)(GPIOA_BASE + 0x00UL))
#define GPIOA_PUPDR         (*(volatile uint32_t *)(GPIOA_BASE + 0x0CUL))
#define GPIOA_IDR           (*(volatile uint32_t *)(GPIOA_BASE + 0x10UL))

/* GPIOF (红灯 PF6) */
#define GPIOF_BASE          (AHB1PERIPH_BASE + 0x1400UL)
#define GPIOF_MODER         (*(volatile uint32_t *)(GPIOF_BASE + 0x00UL))
#define GPIOF_OTYPER        (*(volatile uint32_t *)(GPIOF_BASE + 0x04UL))
#define GPIOF_OSPEEDR       (*(volatile uint32_t *)(GPIOF_BASE + 0x08UL))
#define GPIOF_PUPDR         (*(volatile uint32_t *)(GPIOF_BASE + 0x0CUL))
#define GPIOF_BSRR          (*(volatile uint32_t *)(GPIOF_BASE + 0x18UL))

/* SYSCFG (EXTI 复用) */
#define SYSCFG_BASE         (APB2PERIPH_BASE + 0x3800UL)
#define SYSCFG_EXTICR1      (*(volatile uint32_t *)(SYSCFG_BASE + 0x08UL))

/* EXTI */
#define EXTI_BASE           (APB2PERIPH_BASE + 0x3C00UL)
#define EXTI_IMR            (*(volatile uint32_t *)(EXTI_BASE + 0x00UL))
#define EXTI_RTSR           (*(volatile uint32_t *)(EXTI_BASE + 0x08UL))
#define EXTI_PR             (*(volatile uint32_t *)(EXTI_BASE + 0x14UL))

/* NVIC (Cortex-M4 内核外设) */
#define NVIC_ISER           ((volatile uint32_t *)0xE000E100UL)
#define NVIC_IPR            ((volatile uint32_t *)0xE000E400UL)

#define LED_R_PIN           6U
#define KEY1_PIN            0U

/* EXTI0 中断号 = 6（RM0090 §10.3.3） */
#define EXTI0_IRQn          6U

/* 粗略延时（消抖用） */
static void delay_ms(volatile uint32_t ms)
{
    volatile uint32_t count = ms * 4000;
    while (count--) {
        __asm__ volatile ("nop");
    }
}

/* EXTI0 中断服务函数（向量表第 22 项 = EXTI0_IRQn + 16） */
void EXTI0_IRQHandler(void) __attribute__((interrupt("IRQ")));
void EXTI0_IRQHandler(void)
{
    /* 清挂起位（写 1 清 0，W1C） */
    EXTI_PR = (1UL << KEY1_PIN);
    
    /* 翻转 PF6 红灯 */
    if (GPIOF_BSRR & (1UL << (LED_R_PIN + 16))) {
        /* 当前是灭（BR6=1），点亮 */
        GPIOF_BSRR = (1UL << (LED_R_PIN + 16));
    } else {
        /* 当前是亮，熄灭 */
        GPIOF_BSRR = (1UL << LED_R_PIN);
    }
}

int main(void)
{
    /* 第 1 步：开时钟 */
    RCC_AHB1ENR |= RCC_AHB1ENR_GPIOAEN | RCC_AHB1ENR_GPIOFEN;
    RCC_APB2ENR |= RCC_APB2ENR_SYSCFGEN;
    
    delay_ms(10);  /* 等待时钟稳定 */

    /* 第 2 步：配 PA0 为输入上拉 */
    GPIOA_MODER &= ~(3UL << (KEY1_PIN * 2));  /* 00 = 输入 */
    GPIOA_PUPDR &= ~(3UL << (KEY1_PIN * 2));
    GPIOA_PUPDR |=  (1UL << (KEY1_PIN * 2));  /* 01 = 上拉 */

    /* 第 3 步：配 PF6 为输出推挽 */
    GPIOF_MODER   &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_MODER   |=  (1UL << (LED_R_PIN * 2));
    GPIOF_OTYPER  &= ~(1UL << LED_R_PIN);
    GPIOF_OSPEEDR &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_PUPDR   &= ~(3UL << (LED_R_PIN * 2));
    
    /* 初始状态：红灯灭 */
    GPIOF_BSRR = (1UL << LED_R_PIN);

    /* 第 4 步：SYSCFG 映射 PA0 → EXTI0 */
    SYSCFG_EXTICR1 &= ~(0xFUL << (KEY1_PIN * 4));  /* 清零 */
    SYSCFG_EXTICR1 |=  (0x0UL << (KEY1_PIN * 4));  /* 0000 = GPIOA */

    /* 第 5 步：EXTI 配置 */
    EXTI_IMR |= (1UL << KEY1_PIN);      /* 使能 EXTI0 中断 */
    EXTI_RTSR |= (1UL << KEY1_PIN);     /* 上升沿触发（按键松开） */

    /* 第 6 步：NVIC 配置 */
    NVIC_ISER[EXTI0_IRQn / 32] = (1UL << (EXTI0_IRQn % 32));
    NVIC_IPR[EXTI0_IRQn] = (10UL << 4);  /* 优先级 10（0-15，数字越小越高） */

    /* 主循环：空转，等中断 */
    while (1) {
        __asm__ volatile ("wfi");  /* 低功耗等待中断 */
    }
}
