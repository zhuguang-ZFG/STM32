/* 板级初始化（CANDIDATE 配置，P2 上板核验后冻结）。 */
#include "main.h"
#include "board_config.h"

TIM_HandleTypeDef htim2;
TIM_HandleTypeDef htim3;
TIM_HandleTypeDef htim4;
UART_HandleTypeDef huart1;

static uint8_t s_rx_byte;

uint8_t *board_uart_rx_buf(void) { return &s_rx_byte; }
uint32_t board_micros(void) { return HAL_GetTick() * 1000u; }  /* P2 换更高分辨率计时 */

void board_clock_init(void)
{
    RCC_OscInitTypeDef o = {0};
    RCC_ClkInitTypeDef c = {0};
    o.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    o.HSEState = RCC_HSE_ON;
    o.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    o.PLL.PLLState = RCC_PLL_ON;
    o.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    o.PLL.PLLMUL = RCC_PLL_MUL9;                 /* 8 MHz ×9 = 72 MHz 候选 */
    HAL_RCC_OscConfig(&o);
    c.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                  RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    c.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    c.AHBCLKDivider = RCC_SYSCLK_DIV1;
    c.APB1CLKDivider = RCC_HCLK_DIV2;            /* 36 MHz；TIM2/3/4CLK=72 MHz */
    c.APB2CLKDivider = RCC_HCLK_DIV1;
    HAL_RCC_ClockConfig(&c, FLASH_LATENCY_2);
}

void board_gpio_init(void)
{
    GPIO_InitTypeDef g = {0};
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* 默认安全态先写电平再开时钟方向：STBY 低（驱动不使能） */
    HAL_GPIO_WritePin(BOARD_PIN_STBY_PORT, BOARD_PIN_STBY_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(BOARD_PIN_AIN1_PORT, BOARD_PIN_AIN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(BOARD_PIN_AIN2_PORT, BOARD_PIN_AIN2_PIN, GPIO_PIN_RESET);
    g.Pin = BOARD_PIN_STBY_PIN | BOARD_PIN_AIN1_PIN | BOARD_PIN_AIN2_PIN | BOARD_PIN_MEAS_PIN;
    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOB, &g);

    /* PA0/PA1 编码器输入（上拉；TIM2 编码器模式在 board_tim_init 启用） */
    g.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLUP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;   /* 输入滤波器前的边沿速率余量 */
    HAL_GPIO_Init(GPIOA, &g);

    /* PA6 TIM3_CH1 复用推挽 */
    g.Pin = GPIO_PIN_6;
    g.Mode = GPIO_MODE_AF_PP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &g);

    /* PA9/PA10 USART1 */
    g.Pin = GPIO_PIN_9;
    g.Mode = GPIO_MODE_AF_PP;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pin = GPIO_PIN_10;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &g);
}

void board_tim_init(void)
{
    __HAL_RCC_TIM2_CLK_ENABLE();
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();

    /* TIM2 编码器模式 3（SMS=011，双边沿计数）——RM0008 Rev21 p.329/392 */
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 0;
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = 0xFFFF;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    TIM_Encoder_InitTypeDef enc = {0};
    enc.EncoderMode = TIM_ENCODERMODE_TI12;
    enc.IC1Polarity = TIM_ICPOLARITY_RISING;
    enc.IC2Polarity = TIM_ICPOLARITY_RISING;
    enc.IC1Selection = TIM_ICSELECTION_DIRECTTI;
    enc.IC2Selection = TIM_ICSELECTION_DIRECTTI;
    enc.IC1Prescaler = TIM_ICPSC_DIV1;
    enc.IC2Prescaler = TIM_ICPSC_DIV1;
    enc.IC1Filter = 0;      /* 输入滤波 P2 按波形核验 */
    enc.IC2Filter = 0;
    HAL_TIM_Encoder_Init(&htim2, &enc);
    HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);

    /* TIM3 CH1 PWM：20 kHz 候选（PSC=0, ARR=3599 @72MHz；100% 端点 B02 验证） */
    htim3.Instance = TIM3;
    htim3.Init.Prescaler = 0;
    htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim3.Init.Period = BOARD_PWM_ARR;
    htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_PWM_Init(&htim3);
    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode = TIM_OCMODE_PWM1;
    oc.Pulse = 0;
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    HAL_TIM_PWM_ConfigChannel(&htim3, &oc, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);

    /* TIM4 控制周期：PSC=7199（10 kHz），ARR=99 → 100 Hz（16 位安全） */
    htim4.Instance = TIM4;
    htim4.Init.Prescaler = BOARD_TIM4_PSC;
    htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim4.Init.Period = BOARD_TIM4_ARR;
    htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_Base_Init(&htim4);
    HAL_NVIC_SetPriority(TIM4_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(TIM4_IRQn);
    HAL_TIM_Base_Start_IT(&htim4);
}

void board_uart_init(void)
{
    __HAL_RCC_USART1_CLK_ENABLE();
    huart1.Instance = USART1;
    huart1.Init.BaudRate = BOARD_UART_BAUD;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    HAL_UART_Init(&huart1);
    HAL_NVIC_SetPriority(USART1_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_UART_Receive_IT(&huart1, &s_rx_byte, 1);
}
