/**
 * @file    main.c
 * @brief   bxCAN：环回自测、双节点、掩码过滤器、Bus-Off 恢复（STM32F103C8）
 *
 * 时钟：HSE 8 MHz × 9 = 72 MHz，APB1 = 36 MHz。
 * 位时序按 RM0008 的 CAN_BTR：
 *   波特率 = f_APB1 / (Prescaler × (1 + BS1 + BS2))
 *   Prescaler = 9，BS1 = 5 TQ，BS2 = 2 TQ
 *   36 MHz / (9 × 8) = 500 kbit/s，采样点 (1+5)/8 = 75%。
 *
 * 引脚：__HAL_AFIO_REMAP_CAN1_1() 把 CAN_RX/TX 放到 PB8/PB9。
 * HAL 里 CAN1_1 对应 MAPR.CAN_REMAP = 01。CAN1_2 是 PD0/PD1，
 * 48 脚的 F103C8 没有这两只脚。默认 PA11/PA12 又和 BluePill 的 USB 挤在一起。
 *
 * 开关（改宏后重编译）：
 *   APP_CAN_LOOPBACK  1 = 环回，单板自发自收，不用收发器
 *                     0 = 正常模式，两块板各改 NODE_ID / PEER_ID
 *   APP_CAN_ABOM      1 = 硬件 ABOM，数完 128×11 个隐性位自己恢复
 *                     0 = 错误回调里 HAL_CAN_Stop + HAL_CAN_Start
 *
 * 过滤器是 32 位掩码，只收 PEER_ID。标准 ID 放在 FilterIdHigh，左移 5 位
 * （32 位过滤寄存器的 STID 在 [31:21]）。
 */

#include "stm32f1xx_hal.h"
#include <stdio.h>

#define APP_CAN_LOOPBACK    1
#define APP_CAN_ABOM        1

#define NODE_ID             0x101U
#define PEER_ID             0x102U
#define DECOY_ID            0x456U

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13

static CAN_HandleTypeDef hcan;
static UART_HandleTypeDef huart1;

static volatile uint32_t rx_ok;
static volatile uint32_t rx_id;
static volatile uint8_t rx_data0;
static volatile uint8_t busoff_hits;
static volatile uint8_t busoff_recover;

static void SystemClock_Config(void);
static void gpio_init(void);
static void uart_init(void);
static void can_init(void);
static void can_filter_peer(void);
static void can_send(uint16_t std_id, uint8_t tag);
static void uart_puts(const char *s);
static void error_handler(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    gpio_init();
    uart_init();
    can_init();
    can_filter_peer();

    if (HAL_CAN_Start(&hcan) != HAL_OK)
    {
        error_handler();
    }
    if (HAL_CAN_ActivateNotification(
            &hcan,
            CAN_IT_RX_FIFO0_MSG_PENDING | CAN_IT_BUSOFF | CAN_IT_ERROR) != HAL_OK)
    {
        error_handler();
    }

    uart_puts("\r\ncan-bxcan ready\r\n");
#if APP_CAN_LOOPBACK
    uart_puts("mode loopback, filter accepts PEER_ID only\r\n");
    can_send(DECOY_ID, 0xD0);
    HAL_Delay(30);
    if (rx_ok != 0U)
    {
        uart_puts("FAIL decoy passed the filter\r\n");
        error_handler();
    }
    can_send(PEER_ID, 0xA5);
    HAL_Delay(30);
    if (rx_ok != 1U || rx_id != PEER_ID || rx_data0 != 0xA5)
    {
        uart_puts("FAIL peer frame missing\r\n");
        error_handler();
    }
    uart_puts("loopback filter ok\r\n");
#else
    uart_puts("mode normal, sending NODE_ID\r\n");
#endif

    uint32_t last = 0U;
    while (1)
    {
#if !APP_CAN_ABOM
        if (busoff_recover != 0U)
        {
            busoff_recover = 0U;
            (void)HAL_CAN_Stop(&hcan);
            (void)HAL_CAN_Start(&hcan);
            (void)HAL_CAN_ActivateNotification(
                &hcan,
                CAN_IT_RX_FIFO0_MSG_PENDING | CAN_IT_BUSOFF | CAN_IT_ERROR);
            uart_puts("bus-off software restart\r\n");
        }
#endif
        uint32_t now = HAL_GetTick();
        if ((now - last) >= 500U)
        {
            last = now;
#if APP_CAN_LOOPBACK
            can_send(PEER_ID, 0xA5);
#else
            can_send(NODE_ID, (uint8_t)(now & 0xFFU));
#endif
        }
    }
}

static void can_send(uint16_t std_id, uint8_t tag)
{
    CAN_TxHeaderTypeDef tx = {0};
    uint32_t mailbox = 0U;
    uint8_t data[8] = {tag, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77};

    tx.StdId = std_id;
    tx.IDE = CAN_ID_STD;
    tx.RTR = CAN_RTR_DATA;
    tx.DLC = 8U;
    tx.TransmitGlobalTime = DISABLE;
    (void)HAL_CAN_AddTxMessage(&hcan, &tx, data, &mailbox);
}

static void can_filter_peer(void)
{
    CAN_FilterTypeDef f = {0};

    f.FilterBank = 0;
    f.FilterMode = CAN_FILTERMODE_IDMASK;
    f.FilterScale = CAN_FILTERSCALE_32BIT;
    f.FilterIdHigh = (uint16_t)(PEER_ID << 5);
    f.FilterIdLow = 0x0000;
    f.FilterMaskIdHigh = (uint16_t)(0x7FFU << 5);
    f.FilterMaskIdLow = 0x0000;
    f.FilterFIFOAssignment = CAN_RX_FIFO0;
    f.FilterActivation = ENABLE;
    f.SlaveStartFilterBank = 14;
    if (HAL_CAN_ConfigFilter(&hcan, &f) != HAL_OK)
    {
        error_handler();
    }
}

static void can_init(void)
{
    hcan.Instance = CAN1;
    hcan.Init.Prescaler = 9;
    hcan.Init.Mode = (APP_CAN_LOOPBACK != 0) ? CAN_MODE_LOOPBACK : CAN_MODE_NORMAL;
    hcan.Init.SyncJumpWidth = CAN_SJW_1TQ;
    hcan.Init.TimeSeg1 = CAN_BS1_5TQ;
    hcan.Init.TimeSeg2 = CAN_BS2_2TQ;
    hcan.Init.TimeTriggeredMode = DISABLE;
    hcan.Init.AutoBusOff = (APP_CAN_ABOM != 0) ? ENABLE : DISABLE;
    hcan.Init.AutoWakeUp = DISABLE;
    hcan.Init.AutoRetransmission = ENABLE;
    hcan.Init.ReceiveFifoLocked = DISABLE;
    hcan.Init.TransmitFifoPriority = DISABLE;
    if (HAL_CAN_Init(&hcan) != HAL_OK)
    {
        error_handler();
    }
}

void HAL_CAN_MspInit(CAN_HandleTypeDef *h)
{
    GPIO_InitTypeDef io = {0};

    if (h->Instance != CAN1)
    {
        return;
    }
    __HAL_RCC_AFIO_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_CAN1_CLK_ENABLE();
    __HAL_AFIO_REMAP_CAN1_1();

    io.Pin = GPIO_PIN_9;
    io.Mode = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &io);

    io.Pin = GPIO_PIN_8;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOB, &io);

    HAL_NVIC_SetPriority(USB_LP_CAN1_RX0_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(USB_LP_CAN1_RX0_IRQn);
    HAL_NVIC_SetPriority(CAN1_SCE_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(CAN1_SCE_IRQn);
}

void USB_LP_CAN1_RX0_IRQHandler(void)
{
    HAL_CAN_IRQHandler(&hcan);
}

void CAN1_SCE_IRQHandler(void)
{
    HAL_CAN_IRQHandler(&hcan);
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *h)
{
    CAN_RxHeaderTypeDef rx = {0};
    uint8_t data[8] = {0};
    char line[48];

    if (HAL_CAN_GetRxMessage(h, CAN_RX_FIFO0, &rx, data) != HAL_OK)
    {
        return;
    }
    rx_id = rx.StdId;
    rx_data0 = data[0];
    rx_ok++;
    HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
    (void)snprintf(line, sizeof line, "rx id=0x%03lX d0=0x%02X\r\n",
                   (unsigned long)rx.StdId, data[0]);
    uart_puts(line);
}

void HAL_CAN_ErrorCallback(CAN_HandleTypeDef *h)
{
    uint32_t err = HAL_CAN_GetError(h);
    if ((err & HAL_CAN_ERROR_BOF) == 0U)
    {
        return;
    }
    busoff_hits++;
    uart_puts("bus-off\r\n");
#if APP_CAN_ABOM
    /* ABOM=1 时硬件自己回到主动错误，软件不要 Stop/Start。 */
    (void)h;
#else
    busoff_recover = 1U;
#endif
}

static void gpio_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    io.Pin = LED_PIN;
    io.Mode = GPIO_MODE_OUTPUT_PP;
    io.Pull = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
}

static void uart_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    io.Pin = GPIO_PIN_9;
    io.Mode = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin = GPIO_PIN_10;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance = USART1;
    huart1.Init.BaudRate = 115200;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        error_handler();
    }
}

static void uart_puts(const char *s)
{
    uint16_t n = 0U;
    while (s[n] != '\0')
    {
        n++;
    }
    (void)HAL_UART_Transmit(&huart1, (uint8_t *)s, n, 50);
}

static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.HSIState = RCC_HSI_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();
    }
}

static void error_handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}
