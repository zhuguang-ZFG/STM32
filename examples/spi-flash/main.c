/**
 * @file    main.c
 * @brief   spi-flash —— 硬件 SPI 驱动 W25Q64（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) 用硬件 SPI1 驱动 W25Q64（8MB SPI NOR Flash）；
 *   2) 读取 JEDEC ID（0xEF 0x40 0x17）确认芯片在位；
 *   3) 扇区擦除（4KB）→ 页写入（256B）→ 读回校验，完整走一遍擦写读；
 *   4) 轮询状态寄存器 BUSY 位等待操作完成（NOR Flash 擦写需要时间）；
 *   5) 演示跨页写入的地址拆分（一页只能写 256 字节）。
 *
 * 引脚（SPI1）：PA5=SCK，PA6=MISO，PA7=MOSI，PA4=CS（软件片选）。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz，SPI1 主机模式。
 */

#include "stm32f1xx_hal.h"
#include <string.h>

/* ------------------------------------------------------------------ 宏定义 */

#define FLASH_SPI           SPI1
#define FLASH_SCK_PORT      GPIOA
#define FLASH_SCK_PIN       GPIO_PIN_5      /* SPI1_SCK  = PA5 */
#define FLASH_MISO_PORT     GPIOA
#define FLASH_MISO_PIN      GPIO_PIN_6      /* SPI1_MISO = PA6 */
#define FLASH_MOSI_PORT     GPIOA
#define FLASH_MOSI_PIN      GPIO_PIN_7      /* SPI1_MOSI = PA7 */
#define FLASH_CS_PORT       GPIOA
#define FLASH_CS_PIN        GPIO_PIN_4      /* 软件片选 CS = PA4 */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */

/* W25Q64 指令集（常用部分） */
#define W25X_CMD_WRITE_ENABLE   0x06U       /* 写使能 */
#define W25X_CMD_READ_STATUS    0x05U       /* 读状态寄存器 1 */
#define W25X_CMD_READ_DATA      0x03U       /* 读数据 */
#define W25X_CMD_PAGE_PROGRAM   0x02U       /* 页编程（≤256B） */
#define W25X_CMD_SECTOR_ERASE   0x20U       /* 4KB 扇区擦除 */
#define W25X_CMD_BLOCK_ERASE    0xD8U       /* 64KB 块擦除 */
#define W25X_CMD_CHIP_ERASE     0xC7U       /* 整片擦除 */
#define W25X_CMD_JEDEC_ID       0x9FU       /* 读 JEDEC ID */

#define W25X_STATUS_BUSY        0x01U       /* 状态寄存器 bit0 = BUSY */
#define W25X_PAGE_SIZE          256U        /* 页大小 */
#define W25X_SECTOR_SIZE        4096U       /* 扇区大小 */

#define TEST_SECTOR_ADDR        0x000000UL  /* 测试用扇区地址（0 号扇区） */
#define TEST_LEN                300U        /* 测试写入长度（跨页，>256） */

#define FLASH_TIMEOUT_MS        5000U       /* 擦写超时（整片擦除需更久） */

/* ---------------------------------------------------------------- 全局句柄 */

SPI_HandleTypeDef hspi1;

static uint8_t g_tx_buf[TEST_LEN];
static uint8_t g_rx_buf[TEST_LEN];

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void spi_init(void);
static void error_handler(void);

static void    w25x_cs_low(void);
static void    w25x_cs_high(void);
static uint8_t w25x_spi_txrx(uint8_t byte);
static void    w25x_write_enable(void);
static uint8_t w25x_read_status(void);
static uint8_t w25x_wait_busy(void);
static void    w25x_read_jedec_id(uint8_t id[3]);
static void    w25x_read_data(uint32_t addr, uint8_t *buf, uint16_t len);
static void    w25x_page_program(uint32_t addr, const uint8_t *buf, uint16_t len);
static void    w25x_write(uint32_t addr, const uint8_t *buf, uint32_t len);
static void    w25x_sector_erase(uint32_t addr);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    spi_init();

    /* 1) 读 JEDEC ID 确认芯片在位：W25Q64 应为 EF 40 17 */
    uint8_t id[3] = {0};
    w25x_read_jedec_id(id);
    if (id[0] != 0xEFU)
    {
        error_handler();                /* 读不到芯片：接线/供电/片选问题 */
    }

    /* 2) 准备测试数据：0,1,2,...,299 */
    for (uint16_t i = 0; i < TEST_LEN; i++)
    {
        g_tx_buf[i] = (uint8_t)i;
        g_rx_buf[i] = 0U;
    }

    while (1)
    {
        /* 3) 擦除 → 写入（跨页）→ 读回校验 */
        w25x_sector_erase(TEST_SECTOR_ADDR);
        w25x_write(TEST_SECTOR_ADDR, g_tx_buf, TEST_LEN);
        w25x_read_data(TEST_SECTOR_ADDR, g_rx_buf, TEST_LEN);

        uint8_t ok = (memcmp(g_tx_buf, g_rx_buf, TEST_LEN) == 0) ? 1U : 0U;

        /* 4) 校验成功点亮 LED，失败闪烁提示 */
        if (ok)
        {
            HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);   /* 点亮 */
        }
        else
        {
            HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        }

        HAL_Delay(1000);
    }
}

/* --------------------------------------------------------- W25Q64 驱动 */

static void w25x_cs_low(void)
{
    HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_RESET);
}

static void w25x_cs_high(void)
{
    HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_SET);
}

/**
 * @brief  SPI 收发一个字节（全双工：发送同时接收）
 */
static uint8_t w25x_spi_txrx(uint8_t byte)
{
    uint8_t rx = 0U;
    if (HAL_SPI_TransmitReceive(&hspi1, &byte, &rx, 1U, 100U) != HAL_OK)
    {
        error_handler();
    }
    return rx;
}

/**
 * @brief  写使能：每次擦除/编程前必须调用，否则操作被忽略
 */
static void w25x_write_enable(void)
{
    w25x_cs_low();
    (void)w25x_spi_txrx(W25X_CMD_WRITE_ENABLE);
    w25x_cs_high();
}

/**
 * @brief  读状态寄存器 1（bit0 = BUSY）
 */
static uint8_t w25x_read_status(void)
{
    w25x_cs_low();
    (void)w25x_spi_txrx(W25X_CMD_READ_STATUS);
    uint8_t sr = w25x_spi_txrx(0xFFU);
    w25x_cs_high();
    return sr;
}

/**
 * @brief  轮询等待 BUSY 位清零（擦写需要时间）
 * @return HAL_OK=完成，HAL_TIMEOUT=超时
 */
static uint8_t w25x_wait_busy(void)
{
    uint32_t start = HAL_GetTick();
    while ((w25x_read_status() & W25X_STATUS_BUSY) != 0U)
    {
        if ((HAL_GetTick() - start) > FLASH_TIMEOUT_MS)
        {
            return HAL_TIMEOUT;
        }
    }
    return HAL_OK;
}

/**
 * @brief  读 JEDEC ID（3 字节：厂商 0xEF + 容量 0x40 + 型号 0x17）
 */
static void w25x_read_jedec_id(uint8_t id[3])
{
    w25x_cs_low();
    (void)w25x_spi_txrx(W25X_CMD_JEDEC_ID);
    id[0] = w25x_spi_txrx(0xFFU);
    id[1] = w25x_spi_txrx(0xFFU);
    id[2] = w25x_spi_txrx(0xFFU);
    w25x_cs_high();
}

/**
 * @brief  读数据（无地址边界限制，可跨页/跨扇区连续读）
 */
static void w25x_read_data(uint32_t addr, uint8_t *buf, uint16_t len)
{
    w25x_cs_low();
    (void)w25x_spi_txrx(W25X_CMD_READ_DATA);
    (void)w25x_spi_txrx((uint8_t)(addr >> 16));
    (void)w25x_spi_txrx((uint8_t)(addr >> 8));
    (void)w25x_spi_txrx((uint8_t)(addr));
    for (uint16_t i = 0; i < len; i++)
    {
        buf[i] = w25x_spi_txrx(0xFFU);
    }
    w25x_cs_high();
}

/**
 * @brief  页编程（写入不超过一页 256 字节，且不能跨页）
 */
static void w25x_page_program(uint32_t addr, const uint8_t *buf, uint16_t len)
{
    w25x_write_enable();

    w25x_cs_low();
    (void)w25x_spi_txrx(W25X_CMD_PAGE_PROGRAM);
    (void)w25x_spi_txrx((uint8_t)(addr >> 16));
    (void)w25x_spi_txrx((uint8_t)(addr >> 8));
    (void)w25x_spi_txrx((uint8_t)(addr));
    for (uint16_t i = 0; i < len; i++)
    {
        (void)w25x_spi_txrx(buf[i]);
    }
    w25x_cs_high();

    (void)w25x_wait_busy();             /* 等待本页编程完成 */
}

/**
 * @brief  写数据（自动按页拆分，可跨页）
 */
static void w25x_write(uint32_t addr, const uint8_t *buf, uint32_t len)
{
    while (len > 0U)
    {
        /* 本页还能写多少字节：到页边界为止 */
        uint32_t page_remain = W25X_PAGE_SIZE - (addr % W25X_PAGE_SIZE);
        uint16_t chunk = (len < page_remain) ? (uint16_t)len : (uint16_t)page_remain;

        w25x_page_program(addr, buf, chunk);

        addr += chunk;
        buf  += chunk;
        len  -= chunk;
    }
}

/**
 * @brief  4KB 扇区擦除（擦除后该扇区数据全为 0xFF）
 */
static void w25x_sector_erase(uint32_t addr)
{
    w25x_write_enable();

    w25x_cs_low();
    (void)w25x_spi_txrx(W25X_CMD_SECTOR_ERASE);
    (void)w25x_spi_txrx((uint8_t)(addr >> 16));
    (void)w25x_spi_txrx((uint8_t)(addr >> 8));
    (void)w25x_spi_txrx((uint8_t)(addr));
    w25x_cs_high();

    (void)w25x_wait_busy();             /* 扇区擦除典型 ~45ms */
}


/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化 SPI1（主机，模式 0，8 位，软件片选）
 */
static void spi_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_SPI1_CLK_ENABLE();

    /* LED 输出 */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    /* SCK / MISO / MOSI：复用推挽 */
    io.Pin   = FLASH_SCK_PIN | FLASH_MISO_PIN | FLASH_MOSI_PIN;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    /* CS：普通推挽输出，软件控制（片选拉低选中） */
    io.Pin   = FLASH_CS_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(FLASH_CS_PORT, &io);
    w25x_cs_high();                     /* 空闲时片选拉高 */

    /* SPI1：主机，模式 0（CPOL=0, CPHA=0），8 位，软件 NSS */
    hspi1.Instance               = FLASH_SPI;
    hspi1.Init.Mode              = SPI_MODE_MASTER;
    hspi1.Init.Direction         = SPI_DIRECTION_2LINES;   /* 全双工 */
    hspi1.Init.DataSize          = SPI_DATASIZE_8BIT;
    hspi1.Init.CLKPolarity       = SPI_POLARITY_LOW;        /* CPOL=0 */
    hspi1.Init.CLKPhase          = SPI_PHASE_1EDGE;         /* CPHA=0 */
    hspi1.Init.NSS               = SPI_NSS_SOFT;
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_8; /* 72/8=9MHz */
    hspi1.Init.FirstBit          = SPI_FIRSTBIT_MSB;        /* MSB 先出 */
    hspi1.Init.TIMode            = SPI_TIMODE_DISABLE;
    hspi1.Init.CRCCalculation    = SPI_CRCCALCULATION_DISABLE;
    hspi1.Init.CRCPolynomial     = 7U;
    if (HAL_SPI_Init(&hspi1) != HAL_OK)
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
    while (1)
    {
    }
}

