/**
 * @file    main.c
 * @brief   uart-dma-idle —— UART + DMA + IDLE 不定长接收 + 环形缓冲区 + AT 命令行
 *          （STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) 用 HAL_UARTEx_ReceiveToIdle_DMA 交付接收片段，CR/LF 才结束命令行；
 *   2) 收到的数据写入软件环形缓冲区（ring buffer），主循环异步取用；
 *   3) 命令行解析：支持 AT 指令风格的命令（AT / AT+LED / AT+ECHO / AT+RESET / AT+INFO）；
 *   4) 演示 HAL_UARTEx_RxEventCallback、HAL_UART_ErrorCallback 回调与错误重启。
 *
 * 命令格式：以 \r 或 \n 结尾的一行，例如 "AT+LED=1\r\n"。
 *   AT                握手，返回 OK
 *   AT+LED=<0|1>      设置板载 LED（低电平点亮，故 0 点亮）
 *   AT+LED?           查询当前 LED 状态
 *   AT+ECHO=<0|1>     开/关回显
 *   AT+INFO           返回固件信息
 *   AT+RESET          软件复位
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz，USART1@115200-8-N-1。
 */

#include "stm32f1xx_hal.h"
#include <string.h>
#include <stdio.h>
#include <stdatomic.h>

/* ------------------------------------------------------------------ 宏定义 */

#define UART_INSTANCE       USART1
#define UART_BAUDRATE       115200U
#define UART_TX_PORT        GPIOA
#define UART_TX_PIN         GPIO_PIN_9      /* USART1_TX = PA9  → DMA1_CH4 */
#define UART_RX_PORT        GPIOA
#define UART_RX_PIN         GPIO_PIN_10     /* USART1_RX = PA10 → DMA1_CH5 */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */

#define DMA_RX_BUF_SIZE     64U
#define RING_BUF_SIZE       512U            /* 软件环形缓冲区大小（2 的幂便于取模） */
#define CMD_LINE_MAX        96U             /* 命令行最大长度 */
#define RX_GAP             256U

_Static_assert((RING_BUF_SIZE & (RING_BUF_SIZE - 1U)) == 0U, "ring capacity must be a power of two");
_Static_assert(ATOMIC_SHORT_LOCK_FREE == 2, "ISR ring requires lock-free short atomics");

/* ---------------------------------------------------------------- 全局句柄 */

UART_HandleTypeDef huart1;
DMA_HandleTypeDef  hdma_usart1_rx;

/* ------------------------------------------------------------------ 环形缓冲 */

typedef struct
{
    uint16_t buf[RING_BUF_SIZE];
    atomic_ushort head;
    atomic_ushort tail;
    uint8_t gap_pending;
} ring_buf_t;

typedef struct
{
    uint32_t rx_bytes;
    uint32_t dropped_bytes;
    uint32_t stream_gaps;
    uint32_t uart_errors;
    uint32_t rearm_failures;
    uint32_t tx_failures;
    uint32_t last_uart_error;
} uart_stats_t;

static volatile uart_stats_t g_stats;

static ring_buf_t g_rb;

static uint8_t g_dma_rx_buf[DMA_RX_BUF_SIZE];   /* DMA 直接写入的目标缓冲区 */
static char    g_line[CMD_LINE_MAX];            /* 命令行组帧缓冲 */
static uint16_t g_line_len = 0U;
static uint8_t g_line_discard = 0U;
static uint8_t g_echo_on   = 1U;
static uint8_t g_led_state = 0U;                /* 0=点亮(低电平)，1=熄灭 */

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void uart_dma_init(void);
static void error_handler(void);

static void   rb_init(ring_buf_t *rb);
static int    rb_put(ring_buf_t *rb, uint16_t value);
static void   rb_push(ring_buf_t *rb, const uint8_t *data, uint16_t len);
static int    rb_pop(ring_buf_t *rb, uint16_t *out);
static void   rb_mark_gap(ring_buf_t *rb);
static void   receive_rearm(UART_HandleTypeDef *huart);
static void   stream_process(uint16_t value);

static void   cmd_process_char(char c);
static void   cmd_execute(char *line);
static void   uart_send(const char *s);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    uart_dma_init();

    rb_init(&g_rb);
    uart_send("\r\n[BOOT] uart-dma-idle ready. type 'AT' for help\r\n");

    /* 启动第一次「DMA + 空闲」接收，之后在回调里自动重启 */
    receive_rearm(&huart1);

    uint16_t value;
    while (1)
    {
        /* 从环形缓冲区取字节，逐字节喂给命令行解析器 */
        if (rb_pop(&g_rb, &value) == 0)
        {
            stream_process(value);
        }
        /* 这里可插入其它任务（如 LED 心跳），不会被接收阻塞 */
    }
}

/* ------------------------------------------------------- 环形缓冲区实现 */

static void rb_init(ring_buf_t *rb)
{
    atomic_init(&rb->head, 0U);
    atomic_init(&rb->tail, 0U);
    rb->gap_pending = 0U;
}

static int rb_put(ring_buf_t *rb, uint16_t value)
{
    uint16_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);
    uint16_t next = (uint16_t)((head + 1U) & (RING_BUF_SIZE - 1U));
    if (next == atomic_load_explicit(&rb->tail, memory_order_acquire))
    {
        return -1;
    }
    rb->buf[head] = value;
    atomic_store_explicit(&rb->head, next, memory_order_release);
    return 0;
}

static void rb_mark_gap(ring_buf_t *rb)
{
    rb->gap_pending = 1U;
    g_stats.stream_gaps++;
}

static void rb_push(ring_buf_t *rb, const uint8_t *data, uint16_t len)
{
    for (uint16_t index = 0; index < len; index++)
    {
        if (rb->gap_pending != 0U)
        {
            if (rb_put(rb, RX_GAP) != 0)
            {
                g_stats.dropped_bytes += len - index;
                return;
            }
            rb->gap_pending = 0U;
        }
        if (rb_put(rb, data[index]) != 0)
        {
            rb_mark_gap(rb);
            g_stats.dropped_bytes += len - index;
            return;
        }
    }
}

static int rb_pop(ring_buf_t *rb, uint16_t *out)
{
    uint16_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    if (atomic_load_explicit(&rb->head, memory_order_acquire) == tail)
    {
        return -1;      /* 空 */
    }
    *out = rb->buf[tail];
    atomic_store_explicit(&rb->tail, (uint16_t)((tail + 1U) & (RING_BUF_SIZE - 1U)), memory_order_release);
    return 0;
}

static void stream_process(uint16_t value)
{
    if (value == RX_GAP)
    {
        g_line_len = 0U;
        g_line_discard = 1U;
        uart_send("ERROR: rx gap, discard until newline\r\n");
        return;
    }
    cmd_process_char((char)value);
}

/* --------------------------------------------------------- 命令行解析 */

static void cmd_process_char(char c)
{
    if (c == '\r' || c == '\n')
    {
        if (g_line_discard == 0U && g_line_len > 0U)
        {
            g_line[g_line_len] = '\0';
            cmd_execute(g_line);
        }
        g_line_len = 0U;
        g_line_discard = 0U;
        return;
    }

    if (g_line_discard != 0U)
    {
        return;
    }

    if ((uint8_t)c < 0x20U || (uint8_t)c > 0x7eU)
    {
        g_line_len = 0U;
        g_line_discard = 1U;
        uart_send("ERROR: invalid character\r\n");
        return;
    }

    if (g_line_len < (CMD_LINE_MAX - 1U))
    {
        g_line[g_line_len++] = c;
    }
    else
    {
        g_line_len = 0U;
        g_line_discard = 1U;
        uart_send("ERROR: line too long\r\n");
    }
}

static void cmd_execute(char *line)
{
    if (g_echo_on)
    {
        char echo[CMD_LINE_MAX + 8];
        (void)snprintf(echo, sizeof(echo), "> %s\r\n", line);
        uart_send(echo);
    }

    if (strcmp(line, "AT") == 0)
    {
        uart_send("OK\r\n");
    }
    else if (strcmp(line, "AT+LED?") == 0)
    {
        char rsp[32];
        (void)snprintf(rsp, sizeof(rsp), "+LED:%u\r\nOK\r\n", g_led_state);
        uart_send(rsp);
    }
    else if (strcmp(line, "AT+LED=0") == 0 || strcmp(line, "AT+LED=1") == 0)
    {
        g_led_state = (line[7] == '1') ? 1U : 0U;
        HAL_GPIO_WritePin(LED_PORT, LED_PIN,
                          g_led_state ? GPIO_PIN_SET : GPIO_PIN_RESET);
        uart_send("OK\r\n");
    }
    else if (strcmp(line, "AT+ECHO=0") == 0 || strcmp(line, "AT+ECHO=1") == 0)
    {
        g_echo_on = (line[8] == '1') ? 1U : 0U;
        uart_send("OK\r\n");
    }
    else if (strcmp(line, "AT+STATS") == 0)
    {
        char response[240];
        (void)snprintf(response, sizeof(response),
                       "+STATS:rx=%lu,drop=%lu,gaps=%lu,errors=%lu,rearm_fail=%lu,tx_fail=%lu,last_error=%lu\r\nOK\r\n",
                       (unsigned long)g_stats.rx_bytes, (unsigned long)g_stats.dropped_bytes,
                       (unsigned long)g_stats.stream_gaps, (unsigned long)g_stats.uart_errors,
                       (unsigned long)g_stats.rearm_failures, (unsigned long)g_stats.tx_failures,
                       (unsigned long)g_stats.last_uart_error);
        uart_send(response);
    }
    else if (strcmp(line, "AT+INFO") == 0)
    {
        uart_send("STM32F103C8T6 uart-dma-idle demo v1.1\r\nOK\r\n");
    }
    else if (strcmp(line, "AT+RESET") == 0)
    {
        uart_send("OK\r\nrebooting...\r\n");
        HAL_Delay(50);
        NVIC_SystemReset();     /* 软件复位 */
    }
    else
    {
        uart_send("ERROR: unknown command\r\n");
    }
}

static void uart_send(const char *s)
{
    /* 阻塞发送仅用于演示；实际产品建议用 DMA 发送避免占用 CPU */
    if (HAL_UART_Transmit(&huart1, (uint8_t *)s, (uint16_t)strlen(s), 100U) != HAL_OK)
    {
        g_stats.tx_failures++;
    }
}

static void receive_rearm(UART_HandleTypeDef *huart)
{
    if (HAL_UARTEx_ReceiveToIdle_DMA(huart, g_dma_rx_buf, DMA_RX_BUF_SIZE) != HAL_OK)
    {
        g_stats.rearm_failures++;
        error_handler();
    }
}


/* --------------------------------------------------------- UART 回调实现 */

/**
 * @brief  DMA 接收事件回调：IDLE/TC 交付片段，HT 仅报告进度
 * @param  huart UART 句柄
 * @param  Size  本次实际接收到的字节数
 * @note   在回调里把数据搬进环形缓冲，并重新启动接收以支持不定长连续接收。
 */
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    if (huart->Instance == UART_INSTANCE)
    {
        /* DMA_NORMAL: HT只报进度，接收仍活动；等IDLE/TC后复制整个前缀一次。
         * 官方F1 HAL_UARTEx_GetRxEventType说明普通模式HT不终止接收。 */
        if (HAL_UARTEx_GetRxEventType(huart) == HAL_UART_RXEVENT_HT)
        {
            return;
        }
        if (Size > DMA_RX_BUF_SIZE)
        {
            error_handler();
        }
        g_stats.rx_bytes += Size;
        rb_push(&g_rb, g_dma_rx_buf, Size);
        /* 重新武装：下一次不定长接收 */
        receive_rearm(huart);
    }
}

/**
 * @brief  错误回调：发生帧错误/噪声/溢出时重启接收，避免接收卡死
 */
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == UART_INSTANCE)
    {
        g_stats.last_uart_error = huart->ErrorCode;
        g_stats.uart_errors++;
        rb_mark_gap(&g_rb);
        if (HAL_UART_AbortReceive(huart) != HAL_OK)
        {
            g_stats.rearm_failures++;
            error_handler();
        }
        __HAL_UART_CLEAR_OREFLAG(huart);
        receive_rearm(huart);
    }
}

/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化 USART1 + DMA（TX 阻塞、RX DMA + IDLE）
 */
static void uart_dma_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();

    /* LED 输出 */
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    /* PA9 = USART1_TX（复用推挽），PA10 = USART1_RX（上拉输入） */
    io.Pin   = UART_TX_PIN;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(UART_TX_PORT, &io);

    io.Pin  = UART_RX_PIN;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(UART_RX_PORT, &io);

    /* USART1 参数：115200-8-N-1，无流控 */
    huart1.Instance          = UART_INSTANCE;
    huart1.Init.BaudRate     = UART_BAUDRATE;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        error_handler();
    }

    /* RX 用 DMA1 通道 5（F1 映射固定：USART1_RX → DMA1_CH5） */
    hdma_usart1_rx.Instance                 = DMA1_Channel5;
    hdma_usart1_rx.Init.Direction           = DMA_PERIPH_TO_MEMORY;
    hdma_usart1_rx.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_usart1_rx.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_usart1_rx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart1_rx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_usart1_rx.Init.Mode                = DMA_NORMAL;
    hdma_usart1_rx.Init.Priority            = DMA_PRIORITY_HIGH;
    if (HAL_DMA_Init(&hdma_usart1_rx) != HAL_OK)
    {
        error_handler();
    }
    __HAL_LINKDMA(&huart1, hdmarx, hdma_usart1_rx);

    /* 中断：USART1 全局中断（用于 IDLE） + DMA1_CH5 中断 */
    HAL_NVIC_SetPriority(USART1_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_NVIC_SetPriority(DMA1_Channel5_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel5_IRQn);
}

/* ------------------------------------------------------------ 中断向量 */

void USART1_IRQHandler(void)
{
    HAL_UART_IRQHandler(&huart1);       /* 内部处理 IDLE，触发 RxEventCallback */
}

void DMA1_Channel5_IRQHandler(void)
{
    HAL_DMA_IRQHandler(&hdma_usart1_rx);
}


/**
 * @brief  系统时钟配置：HSE 8MHz → PLL ×9 → 72MHz
 */
static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.HSIState       = RCC_HSI_ON;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();
    }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
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

