#include "stm32f10x.h"

extern volatile uint32_t g_ms;

/* This file replaces the V3.5.0 template stm32f10x_it.c. Do not compile both. */
void SysTick_Handler(void)
{
    g_ms++;
}
