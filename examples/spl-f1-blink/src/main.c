#include "stm32f10x.h"

volatile uint32_t g_ms;

static void delay_ms(uint32_t delay)
{
    const uint32_t start = g_ms;
    while ((uint32_t)(g_ms - start) < delay) {
        __NOP();
    }
}

static void led_init(void)
{
    GPIO_InitTypeDef io;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    GPIO_StructInit(&io);
    io.GPIO_Pin = GPIO_Pin_13;
    io.GPIO_Mode = GPIO_Mode_Out_PP;
    io.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOC, &io);
    GPIO_SetBits(GPIOC, GPIO_Pin_13);
}

int main(void)
{
    SystemCoreClockUpdate();
    if (SysTick_Config(SystemCoreClock / 1000U) != 0U) {
        for (;;) {
            __NOP();
        }
    }

    led_init();
    for (;;) {
        GPIO_ResetBits(GPIOC, GPIO_Pin_13);
        delay_ms(500U);
        GPIO_SetBits(GPIOC, GPIO_Pin_13);
        delay_ms(500U);
    }
}
