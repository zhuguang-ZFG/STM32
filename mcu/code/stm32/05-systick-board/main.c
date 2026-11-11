/**
 * main.c —— SysTick 延时演示：精确 1ms 节拍 + delay_ms 函数
 *
 * SysTick 原理（Cortex-M4 内核定时器）：
 *   - 4 个寄存器：CTRL、LOAD、VAL、CALIB（地址 0xE000E010 ~ 0xE000E01C）
 *   - 24 位递减计数器：从 LOAD 倒数到 0，触发中断后自动重装
 *   - 周期 = (LOAD + 1) / 时钟频率
 *
 * 本实现：
 *   - SysTick 配置为 1ms 中断（168MHz / 1000 - 1 = 167999）
 *   - 中断服务函数递增全局计数器 g_ms_ticks
 *   - delay_ms() 轮询计数器实现阻塞延时
 *
 * 硬件：PF6 红灯翻转，可用逻辑分析仪测量精确周期
 *
 * 参考：[S5 SysTick](../../docs/stm32/05-systick.md)
 */

#include <stdint.h>

/* ---------------- 寄存器地址 ---------------- */
#define PERIPH_BASE         0x40000000UL
#define AHB1PERIPH_BASE     (PERIPH_BASE + 0x00020000UL)

/* RCC */
#define RCC_BASE            (AHB1PERIPH_BASE + 0x3800UL)
#define RCC_AHB1ENR         (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#define RCC_AHB1ENR_GPIOFEN (1UL << 5)

/* GPIOF (红灯 PF6) */
#define GPIOF_BASE          (AHB1PERIPH_BASE + 0x1400UL)
#define GPIOF_MODER         (*(volatile uint32_t *)(GPIOF_BASE + 0x00UL))
#define GPIOF_OTYPER        (*(volatile uint32_t *)(GPIOF_BASE + 0x04UL))
#define GPIOF_OSPEEDR       (*(volatile uint32_t *)(GPIOF_BASE + 0x08UL))
#define GPIOF_PUPDR         (*(volatile uint32_t *)(GPIOF_BASE + 0x0CUL))
#define GPIOF_BSRR          (*(volatile uint32_t *)(GPIOF_BASE + 0x18UL))

/* SysTick (Cortex-M4 内核外设) */
#define SYSTICK_CSR         (*(volatile uint32_t *)0xE000E010UL)
#define SYSTICK_RVR         (*(volatile uint32_t *)0xE000E014UL)
#define SYSTICK_CVR         (*(volatile uint32_t *)0xE000E018UL)
#define SYSTICK_CALIB       (*(volatile uint32_t *)0xE000E01CUL)

/* SysTick CTRL 位定义 */
#define SYSTICK_CTRL_ENABLE     (1UL << 0)
#define SYSTICK_CTRL_TICKINT    (1UL << 1)
#define SYSTICK_CTRL_CLKSOURCE  (1UL << 2)
#define SYSTICK_CTRL_COUNTFLAG  (1UL << 16)

#define LED_R_PIN           6U

/* 系统时钟：HSI 16MHz（复位默认，未配 PLL） */
#define SYSTEM_CLOCK_HZ     16000000UL

/* 全局毫秒计数器 */
static volatile uint32_t g_ms_ticks = 0;

/* SysTick 中断服务函数（中断号 -1，Cortex-M4 内核异常） */
void SysTick_Handler(void) __attribute__((interrupt));
void SysTick_Handler(void)
{
    g_ms_ticks++;
}

/**
 * 初始化 SysTick 为 1ms 中断
 * 
 * @param ticks_per_ms  每毫秒的 tick 数（通常 = 时钟频率 / 1000）
 * @return 0=成功, 1=失败（LOAD 超出 24 位范围）
 */
static int systick_init(uint32_t ticks_per_ms)
{
    /* 24 位计数器最大值：0xFFFFFF = 16777215 */
    if (ticks_per_ms > 0x01000000UL) {
        return 1;  /* 超出范围 */
    }
    
    SYSTICK_RVR = ticks_per_ms - 1;  /* LOAD = 周期 - 1 */
    SYSTICK_CVR = 0;                  /* 清当前值 */
    SYSTICK_CSR = SYSTICK_CTRL_ENABLE | 
                  SYSTICK_CTRL_TICKINT | 
                  SYSTICK_CTRL_CLKSOURCE;  /* 使能 + 中断 + 处理器时钟 */
    
    return 0;
}

/**
 * 毫秒级阻塞延时
 * 
 * @param ms  延时毫秒数
 */
static void delay_ms(uint32_t ms)
{
    uint32_t start = g_ms_ticks;
    while ((g_ms_ticks - start) < ms) {
        /* 忙等 */
    }
}

int main(void)
{
    /* 第 1 步：开 GPIOF 时钟 */
    RCC_AHB1ENR |= RCC_AHB1ENR_GPIOFEN;

    /* 第 2 步：配 PF6 为输出推挽 */
    GPIOF_MODER   &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_MODER   |=  (1UL << (LED_R_PIN * 2));
    GPIOF_OTYPER  &= ~(1UL << LED_R_PIN);
    GPIOF_OSPEEDR &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_PUPDR   &= ~(3UL << (LED_R_PIN * 2));
    
    /* 初始状态：红灯灭 */
    GPIOF_BSRR = (1UL << LED_R_PIN);

    /* 第 3 步：初始化 SysTick（16MHz / 1000 = 16000 ticks/ms） */
    if (systick_init(SYSTEM_CLOCK_HZ / 1000) != 0) {
        /* 初始化失败，死循环 */
        while (1) {}
    }

    /* 主循环：500ms 翻转红灯 */
    while (1) {
        GPIOF_BSRR = (1UL << (LED_R_PIN + 16));  /* 亮 */
        delay_ms(500);
        GPIOF_BSRR = (1UL << LED_R_PIN);         /* 灭 */
        delay_ms(500);
    }
}
