/* IRQ 路由（CANDIDATE）。 */
#include "main.h"

void TIM4_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim4);
}

void USART1_IRQHandler(void)
{
    HAL_UART_IRQHandler(&huart1);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM4) {
        board_control_isr();
    }
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1) {
        board_uart_rx_byte(*board_uart_rx_buf());
        HAL_UART_Receive_IT(&huart1, board_uart_rx_buf(), 1);
    }
}
