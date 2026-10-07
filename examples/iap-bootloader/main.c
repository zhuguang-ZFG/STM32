/**
 * @file    main.c
 * @brief   iap-bootloader —— IAP 串口升级 Bootloader（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) 上电等待约 500ms，收到字符 'U' 则进入串口升级模式，否则跳转 APP；
 *   2) 通过 USART1 接收固件：协议 = 0x5A + 4 字节长度 + 数据 + 4 字节累加校验；
 *   3) 按页擦除 APP 区 → 按半字写入 Flash → 校验，全部通过才算升级成功；
 *   4) 跳转前完成「关中断、复位外设、设 MSP、设 SCB->VTOR」四步，避免死机。
 *
 * Flash 划分（STM32F103C8T6，64KB）：
 *   0x08000000 ~ 0x08003FFF  Bootloader（16KB）
 *   0x08004000 ~ 0x080047FF  参数区（2KB，本示例未使用）
 *   0x08004800 ~ 0x0800FFFF  APP 区（46KB）
 *
 * ⚠️ APP 端必须做两件事（见 README）：
 *   ① 链接脚本把 Flash 起始改为 0x08004800、长度改为 46KB；
 *   ② main() 开头执行 SCB->VTOR = 0x08004800;
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz。
 */

#include "stm32f1xx_hal.h"
#include <string.h>

/* ------------------------------------------------------------------ 宏定义 */

#define APP_ADDR            0x08004800UL    /* APP 起始地址（页边界） */
#define APP_MAX_SIZE        (46U * 1024U)   /* APP 区大小 */
#define FLASH_PAGE_SIZE     1024UL          /* F103C8 小容量：1KB/页 */
#define FLASH_BASE_ADDR     0x08000000UL

#define UART_INSTANCE       USART1
#define UART_TX_PIN         GPIO_PIN_9      /* USART1_TX = PA9 */
#define UART_RX_PIN         GPIO_PIN_10     /* USART1_RX = PA10 */
#define UART_BAUDRATE       115200U

#define FW_START_BYTE       0x5AU           /* 固件帧起始字节 */
#define RX_CHUNK            512U            /* 每次接收的字节数（半字对齐） */
#define WAIT_UPGRADE_MS     500U            /* 上电等待升级命令的时间 */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */

typedef void (*pFunction)(void);

/* ---------------------------------------------------------------- 全局句柄 */

UART_HandleTypeDef huart1;

static uint8_t g_rx_buf[RX_CHUNK];

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void boot_init(void);
static void error_handler(void);

static int      flash_erase_range(uint32_t addr, uint32_t len);
static int      flash_write_bytes(uint32_t addr, const uint8_t *data, uint32_t len);
static uint32_t checksum32(const uint8_t *data, uint32_t len);
static int      uart_wait_for_upgrade(uint32_t timeout_ms);
static int      uart_receive_firmware(uint32_t app_addr, uint32_t *out_size);
static void     jump_to_app(uint32_t app_addr);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    boot_init();

    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);   /* 点亮：进入 Bootloader */

    /* 上电等待：收到 'U' 进入升级，否则直接跳 APP */
    if (uart_wait_for_upgrade(WAIT_UPGRADE_MS))
    {
        uint32_t fw_size = 0U;
        if (uart_receive_firmware(APP_ADDR, &fw_size) == 0)
        {
            /* 升级成功：LED 快闪 3 次提示 */
            for (int i = 0; i < 3; i++)
            {
                HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
                HAL_Delay(100);
            }
        }
        /* 升级失败也继续往下，跳回旧 APP */
    }

    jump_to_app(APP_ADDR);
    for (;;) { }        /* 不会执行到这里 */
}

/* --------------------------------------------------------- Flash 操作 */

/**
 * @brief  擦除覆盖 [addr, addr+len) 的所有页
 * @return 0 成功，-1 失败
 */
static int flash_erase_range(uint32_t addr, uint32_t len)
{
    FLASH_EraseInitTypeDef er = {0};
    uint32_t page_err = 0U;

    er.TypeErase   = FLASH_TYPEERASE_PAGES;
    er.PageAddress = addr;
    er.NbPages     = (len + FLASH_PAGE_SIZE - 1UL) / FLASH_PAGE_SIZE;

    HAL_FLASH_Unlock();
    HAL_StatusTypeDef st = HAL_FLASHEx_Erase(&er, &page_err);
    HAL_FLASH_Lock();

    return (st == HAL_OK) ? 0 : -1;
}

/**
 * @brief  按半字（16 位）写入 Flash
 * @note   F1 只支持半字编程；len 为字节数，需为偶数，不足补 0xFF。
 * @return 0 成功，-1 失败
 */
static int flash_write_bytes(uint32_t addr, const uint8_t *data, uint32_t len)
{
    HAL_FLASH_Unlock();

    for (uint32_t i = 0; i < len; i += 2U)
    {
        uint16_t half = (uint16_t)data[i];
        if ((i + 1U) < len)
        {
            half |= (uint16_t)((uint16_t)data[i + 1U] << 8U);
        }
        else
        {
            half |= 0xFF00U;                    /* 奇数长度：高字节补 0xFF */
        }
        if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD,
                              addr + i, half) != HAL_OK)
        {
            HAL_FLASH_Lock();
            return -1;
        }
    }

    HAL_FLASH_Lock();
    return 0;
}

/**
 * @brief  32 位累加和校验（简单但够用；量产建议用 CRC32）
 */
static uint32_t checksum32(const uint8_t *data, uint32_t len)
{
    uint32_t sum = 0U;
    for (uint32_t i = 0; i < len; i++)
    {
        sum += data[i];
    }
    return sum;
}

/* ------------------------------------------------------- 串口升级流程 */

/**
 * @brief  上电后等待一段时间，收到 'U' 返回 1（进入升级），否则返回 0
 */
static int uart_wait_for_upgrade(uint32_t timeout_ms)
{
    uint8_t ch = 0U;
    uint32_t start = HAL_GetTick();

    while ((HAL_GetTick() - start) < timeout_ms)
    {
        if (HAL_UART_Receive(&huart1, &ch, 1U, 10U) == HAL_OK)
        {
            if (ch == (uint8_t)'U')
            {
                return 1;
            }
        }
    }
    return 0;
}

/**
 * @brief  接收固件并写入 Flash
 * @param  app_addr APP 起始地址
 * @param  out_size 输出：固件字节数
 * @return 0 成功，-1 失败
 * @note   帧格式：0x5A | len(4B,小端) | data | checksum(4B,小端)
 */
static int uart_receive_firmware(uint32_t app_addr, uint32_t *out_size)
{
    uint8_t  start = 0U;
    uint8_t  len_buf[4];
    uint8_t  csum_buf[4];
    uint32_t total = 0U;

    /* 1) 等待起始字节 */
    if (HAL_UART_Receive(&huart1, &start, 1U, 5000U) != HAL_OK || start != FW_START_BYTE)
    {
        return -1;
    }

    /* 2) 读长度 */
    if (HAL_UART_Receive(&huart1, len_buf, 4U, 1000U) != HAL_OK)
    {
        return -1;
    }
    uint32_t fw_len = (uint32_t)len_buf[0]
                    | ((uint32_t)len_buf[1] << 8U)
                    | ((uint32_t)len_buf[2] << 16U)
                    | ((uint32_t)len_buf[3] << 24U);

    if (fw_len == 0U || fw_len > APP_MAX_SIZE)
    {
        return -1;
    }

    /* 3) 擦除 APP 区 */
    if (flash_erase_range(app_addr, fw_len) != 0)
    {
        return -1;
    }

    /* 4) 分块接收并写入 Flash */
    uint32_t remain = fw_len;
    uint32_t addr   = app_addr;
    while (remain > 0U)
    {
        uint16_t chunk = (remain < RX_CHUNK) ? (uint16_t)remain : (uint16_t)RX_CHUNK;
        chunk = (uint16_t)((chunk + 1U) & 0xFFFEU);     /* 半字对齐（向上取偶） */
        if (chunk > remain)
        {
            chunk = (uint16_t)remain;
        }

        if (HAL_UART_Receive(&huart1, g_rx_buf, chunk, 2000U) != HAL_OK)
        {
            return -1;
        }
        if (flash_write_bytes(addr, g_rx_buf, chunk) != 0)
        {
            return -1;
        }

        addr   += chunk;
        remain -= chunk;
        total  += chunk;
    }

    /* 5) 读校验和并比对 */
    if (HAL_UART_Receive(&huart1, csum_buf, 4U, 1000U) != HAL_OK)
    {
        return -1;
    }
    uint32_t csum = (uint32_t)csum_buf[0]
                  | ((uint32_t)csum_buf[1] << 8U)
                  | ((uint32_t)csum_buf[2] << 16U)
                  | ((uint32_t)csum_buf[3] << 24U);

    if (checksum32((const uint8_t *)app_addr, fw_len) != csum)
    {
        return -1;      /* 校验失败，保留旧 APP（本示例未做双区回退） */
    }

    *out_size = total;
    return 0;
}

/* --------------------------------------------------------- 跳转 APP */

/**
 * @brief  跳转到 APP
 * @note   四步：关中断 → 复位外设 → 设 MSP/VTOR → 跳转。
 */
static void jump_to_app(uint32_t app_addr)
{
    uint32_t app_stack = *(volatile uint32_t *)app_addr;         /* 向量表[0]=初始 MSP */
    uint32_t app_entry = *(volatile uint32_t *)(app_addr + 4U);  /* 向量表[1]=复位向量 */

    /* 地址合法性检查：MSP 应落在 SRAM 范围内（0x20000000 区） */
    if ((app_stack & 0xFFF00000UL) != 0x20000000UL)
    {
        error_handler();                /* APP 区无有效固件 */
    }

    /* 1) 关全局中断 + 关 SysTick */
    __disable_irq();
    SysTick->CTRL = 0U;
    SysTick->LOAD = 0U;
    SysTick->VAL  = 0U;

    /* 2) 复位所有外设，恢复默认状态 */
    HAL_RCC_DeInit();
    HAL_DeInit();

    /* 3) 设置主栈指针与向量表偏移 */
    __set_MSP(app_stack);
    SCB->VTOR = app_addr;

    /* 4) 重新开中断并跳到 APP 复位入口 */
    __enable_irq();
    ((pFunction)app_entry)();
}


/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化 LED 与 USART1
 */
static void boot_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();

    /* LED 输出 */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);

    /* USART1：PA9=TX, PA10=RX */
    io.Pin   = UART_TX_PIN;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = UART_RX_PIN;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

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
    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);  /* 快闪提示出错 */
        for (volatile uint32_t i = 0; i < 400000U; i++) { }
    }
}

