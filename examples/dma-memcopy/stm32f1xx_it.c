#include "stm32f1xx_hal.h"

extern DMA_HandleTypeDef hdma_memcopy;

void SysTick_Handler(void)
{
    HAL_IncTick();
}

void DMA1_Channel1_IRQHandler(void)
{
    HAL_DMA_IRQHandler(&hdma_memcopy);
}
