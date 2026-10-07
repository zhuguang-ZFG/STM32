/**
 * @file    main.c
 * @brief   i2c-oled —— 硬件 I2C 驱动 SSD1306 OLED（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) 用硬件 I2C1(PB6=SCL, PB7=SDA) 驱动 0.96" SSD1306(128×64) OLED；
 *   2) 完整的初始化命令表（上电时序 + 电荷泵 + 显示参数）；
 *   3) 软件显存（framebuffer 1024 字节）→ 一次性刷屏，避免逐点写慢；
 *   4) 内置 5×7 点阵字库，可显示字符串；每 500ms 刷新一次计数器与进度条；
 *   5) 带 I2C 超时判断与「总线死锁恢复」函数（9 个时钟脉冲解锁）。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz，I2C1 标准模式 100kHz。
 * SSD1306 I2C 地址：0x3C（7 位），HAL 用左移后的 0x78（8 位）。
 */

#include "stm32f1xx_hal.h"
#include <string.h>

/* ------------------------------------------------------------------ 宏定义 */

#define OLED_I2C            I2C1
#define OLED_SCL_PORT       GPIOB
#define OLED_SCL_PIN        GPIO_PIN_6      /* I2C1_SCL = PB6 */
#define OLED_SDA_PORT       GPIOB
#define OLED_SDA_PIN        GPIO_PIN_7      /* I2C1_SDA = PB7 */

#define OLED_ADDR           0x78U           /* 0x3C << 1 */
#define OLED_WIDTH          128U
#define OLED_HEIGHT         64U
#define OLED_PAGES          (OLED_HEIGHT / 8U)   /* 8 页 */
#define OLED_BUF_SIZE       (OLED_WIDTH * OLED_PAGES)  /* 1024 字节显存 */

#define I2C_TIMEOUT_MS      100U            /* I2C 传输超时（毫秒） */
#define I2C_RECOVER_PULSES  9U              /* 总线恢复时钟脉冲数 */

#define SSD1306_CTRL_CMD    0x00U           /* 控制字节：后续为命令 */
#define SSD1306_CTRL_DATA   0x40U           /* 控制字节：后续为数据 */

/* ---------------------------------------------------------------- 全局句柄 */

I2C_HandleTypeDef hi2c1;

static uint8_t g_oled_buf[OLED_BUF_SIZE];   /* 显存：页优先，每页 128 字节 */

/* ------------------------------------------------------------- SSD1306 命令表 */

/* 上电初始化命令序列（末尾 0x00 为哨兵，表示结束） */
static const uint8_t g_ssd1306_init_cmds[] =
{
    0xAE,               /* 关闭显示 */
    0x20, 0x00,         /* 水平寻址模式 */
    0xB0,               /* 页地址 = 0（页寻址用） */
    0xC8,               /* COM 扫描方向：反向（上下不颠倒） */
    0x00,               /* 低列地址 = 0 */
    0x10,               /* 高列地址 = 0 */
    0x40,               /* 显示起始行 = 0 */
    0x81, 0x7F,         /* 对比度 = 0x7F */
    0xA1,               /* 段重映射：左右不颠倒 */
    0xA6,               /* 正常显示（非反白） */
    0xA8, 0x3F,         /* 多路复用比 = 0x3F + 1 = 64 */
    0xA4,               /* 输出跟随显存 */
    0xD3, 0x00,         /* 显示偏移 = 0 */
    0xD5, 0x80,         /* 时钟分频/振荡频率 */
    0xD9, 0xF1,         /* 预充电周期 */
    0xDA, 0x12,         /* COM 引脚配置：128×64 */
    0xDB, 0x40,         /* VCOMH 反压 */
    0x8D, 0x14,         /* 使能电荷泵 */
    0xAF,               /* 打开显示 */
};

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void i2c_init(void);
static void error_handler(void);

static uint8_t ssd1306_write_cmd(uint8_t cmd);
static uint8_t ssd1306_write_data(const uint8_t *data, uint16_t len);
static uint8_t ssd1306_init(void);
static uint8_t ssd1306_flush(void);
static void    ssd1306_clear(void);
static void    ssd1306_draw_pixel(uint8_t x, uint8_t y, uint8_t on);
static void    ssd1306_draw_char(uint8_t x, uint8_t y, char c);
static void    ssd1306_draw_string(uint8_t x, uint8_t y, const char *s);
static void    ssd1306_draw_rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h);
static void    ssd1306_fill_rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h);
static void    i2c_bus_recovery(void);

/* 5×7 点阵字库：每字符 5 列，每列 7 位（bit0 在顶部）。
 * 顺序：' '(0) → '0'..'9'(1..10) → 'A'..'Z'(11..36) → ':'(37) '.'(38) '-'(39) */
static const uint8_t g_font5x7[][5] =
{
    {0x00,0x00,0x00,0x00,0x00}, /* ' ' */  {0x3E,0x51,0x49,0x45,0x3E}, /* '0' */
    {0x00,0x42,0x7F,0x40,0x00}, /* '1' */  {0x42,0x61,0x51,0x49,0x46}, /* '2' */
    {0x21,0x41,0x45,0x4B,0x31}, /* '3' */  {0x18,0x14,0x12,0x7F,0x10}, /* '4' */
    {0x27,0x45,0x45,0x45,0x39}, /* '5' */  {0x3C,0x4A,0x49,0x49,0x30}, /* '6' */
    {0x01,0x71,0x09,0x05,0x03}, /* '7' */  {0x36,0x49,0x49,0x49,0x36}, /* '8' */
    {0x06,0x49,0x49,0x29,0x1E}, /* '9' */  {0x7E,0x11,0x11,0x11,0x7E}, /* 'A' */
    {0x7F,0x49,0x49,0x49,0x36}, /* 'B' */  {0x3E,0x41,0x41,0x41,0x22}, /* 'C' */
    {0x7F,0x41,0x41,0x22,0x1C}, /* 'D' */  {0x7F,0x49,0x49,0x49,0x41}, /* 'E' */
    {0x7F,0x09,0x09,0x09,0x01}, /* 'F' */  {0x3E,0x41,0x49,0x49,0x7A}, /* 'G' */
    {0x7F,0x08,0x08,0x08,0x7F}, /* 'H' */  {0x00,0x41,0x7F,0x41,0x00}, /* 'I' */
    {0x20,0x40,0x41,0x3F,0x01}, /* 'J' */  {0x7F,0x08,0x14,0x22,0x41}, /* 'K' */
    {0x7F,0x40,0x40,0x40,0x40}, /* 'L' */  {0x7F,0x02,0x0C,0x02,0x7F}, /* 'M' */
    {0x7F,0x04,0x08,0x10,0x7F}, /* 'N' */  {0x3E,0x41,0x41,0x41,0x3E}, /* 'O' */
    {0x7F,0x09,0x09,0x09,0x06}, /* 'P' */  {0x3E,0x41,0x51,0x21,0x5E}, /* 'Q' */
    {0x7F,0x09,0x19,0x29,0x46}, /* 'R' */  {0x46,0x49,0x49,0x49,0x31}, /* 'S' */
    {0x01,0x01,0x7F,0x01,0x01}, /* 'T' */  {0x3F,0x40,0x40,0x40,0x3F}, /* 'U' */
    {0x1F,0x20,0x40,0x20,0x1F}, /* 'V' */  {0x7F,0x20,0x18,0x20,0x7F}, /* 'W' */
    {0x63,0x14,0x08,0x14,0x63}, /* 'X' */  {0x07,0x08,0x70,0x08,0x07}, /* 'Y' */
    {0x61,0x51,0x49,0x45,0x43}, /* 'Z' */  {0x00,0x36,0x36,0x00,0x00}, /* ':' */
    {0x00,0x60,0x60,0x00,0x00}, /* '.' */  {0x08,0x08,0x08,0x08,0x08}, /* '-' */
};

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    i2c_init();

    if (ssd1306_init() != HAL_OK)
    {
        i2c_bus_recovery();                 /* 初始化失败先尝试解锁总线 */
        (void)ssd1306_init();
    }

    uint32_t seconds = 0U;
    uint32_t last    = 0U;

    while (1)
    {
        if ((HAL_GetTick() - last) >= 500U)
        {
            last = HAL_GetTick();
            seconds++;

            ssd1306_clear();

            /* 外框 + 标题 */
            ssd1306_draw_rect(0, 0, OLED_WIDTH, OLED_HEIGHT);
            ssd1306_draw_string(6, 2, "STM32 OLED");
            ssd1306_draw_string(6, 12, "I2C SSD1306");

            /* 计数器（数字右对齐到第 4 行） */
            char line[24];
            (void)snprintf(line, sizeof(line), "TIME:%u", (unsigned)seconds);
            ssd1306_draw_string(6, 24, line);

            /* 进度条：每 8 秒走满一轮 */
            uint8_t w = (uint8_t)((seconds % 8U) * (OLED_WIDTH - 12U) / 8U);
            ssd1306_fill_rect(6, 40, w, 10);
            ssd1306_draw_rect(5, 39, OLED_WIDTH - 10U, 12U);

            /* 一次性刷屏 */
            (void)ssd1306_flush();
        }
    }
}

/* ----------------------------------------------------------- 字库索引 */

static int font_index(char c)
{
    if (c == ' ')
    {
        return 0;
    }
    if (c >= '0' && c <= '9')
    {
        return 1 + (c - '0');
    }
    if (c >= 'A' && c <= 'Z')
    {
        return 11 + (c - 'A');
    }
    switch (c)
    {
        case ':': return 37;
        case '.': return 38;
        case '-': return 39;
        default:  return 0;     /* 未收录字符按空格处理 */
    }
}

/* --------------------------------------------------- SSD1306 底层通信 */

/**
 * @brief  写一条命令
 */
static uint8_t ssd1306_write_cmd(uint8_t cmd)
{
    uint8_t buf[2] = { SSD1306_CTRL_CMD, cmd };
    return HAL_I2C_Master_Transmit(&hi2c1, OLED_ADDR, buf, 2U, I2C_TIMEOUT_MS);
}

/**
 * @brief  写一段显存数据
 */
static uint8_t ssd1306_write_data(const uint8_t *data, uint16_t len)
{
    /* SSD1306 要求：控制字节 0x40 + 连续数据。这里用「分块」方式发送，
     * 避免每次只发 1 字节导致 I2C 效率低。 */
    static uint8_t tx[1 + OLED_WIDTH];
    uint16_t offset = 0U;

    while (offset < len)
    {
        uint16_t chunk = len - offset;
        if (chunk > OLED_WIDTH)
        {
            chunk = OLED_WIDTH;
        }
        tx[0] = SSD1306_CTRL_DATA;
        (void)memcpy(&tx[1], &data[offset], chunk);
        if (HAL_I2C_Master_Transmit(&hi2c1, OLED_ADDR, tx,
                                    (uint16_t)(chunk + 1U), I2C_TIMEOUT_MS) != HAL_OK)
        {
            return HAL_ERROR;
        }
        offset = (uint16_t)(offset + chunk);
    }
    return HAL_OK;
}

/**
 * @brief  发送初始化命令表
 */
static uint8_t ssd1306_init(void)
{
    for (uint32_t i = 0; i < sizeof(g_ssd1306_init_cmds); i++)
    {
        if (ssd1306_write_cmd(g_ssd1306_init_cmds[i]) != HAL_OK)
        {
            return HAL_ERROR;
        }
    }
    ssd1306_clear();
    return ssd1306_flush();
}

/**
 * @brief  把整个显存刷到 OLED（页寻址：逐页设置列地址后写 128 字节）
 */
static uint8_t ssd1306_flush(void)
{
    for (uint8_t page = 0; page < OLED_PAGES; page++)
    {
        if (ssd1306_write_cmd((uint8_t)(0xB0U + page)) != HAL_OK)   /* 页地址 */
        {
            return HAL_ERROR;
        }
        if (ssd1306_write_cmd(0x00) != HAL_OK)                      /* 列低 4 位 */
        {
            return HAL_ERROR;
        }
        if (ssd1306_write_cmd(0x10) != HAL_OK)                      /* 列高 4 位 */
        {
            return HAL_ERROR;
        }
        if (ssd1306_write_data(&g_oled_buf[page * OLED_WIDTH], OLED_WIDTH) != HAL_OK)
        {
            return HAL_ERROR;
        }
    }
    return HAL_OK;
}


/* --------------------------------------------------------- 绘图函数 */

static void ssd1306_clear(void)
{
    (void)memset(g_oled_buf, 0x00, sizeof(g_oled_buf));
}

/**
 * @brief  设置单个像素（软件显存，on=1 亮）
 * @note   显存按「页」组织：每个字节表示同一页（8 行）里的一列 8 个像素，
 *         bit0 在顶部、bit7 在底部。
 */
static void ssd1306_draw_pixel(uint8_t x, uint8_t y, uint8_t on)
{
    if (x >= OLED_WIDTH || y >= OLED_HEIGHT)
    {
        return;
    }
    uint16_t idx = (uint16_t)(x + (y / 8U) * OLED_WIDTH);
    uint8_t  bit = (uint8_t)(1U << (y % 8U));
    if (on)
    {
        g_oled_buf[idx] |= bit;
    }
    else
    {
        g_oled_buf[idx] &= (uint8_t)~bit;
    }
}

/**
 * @brief  画一个 5×7 字符（右边留 1 列间隔，共占 6 列宽）
 */
static void ssd1306_draw_char(uint8_t x, uint8_t y, char c)
{
    const uint8_t *glyph = g_font5x7[font_index(c)];
    for (uint8_t col = 0; col < 5U; col++)
    {
        uint8_t bits = glyph[col];
        for (uint8_t row = 0; row < 7U; row++)
        {
            ssd1306_draw_pixel((uint8_t)(x + col), (uint8_t)(y + row),
                               (uint8_t)((bits >> row) & 0x01U));
        }
    }
}

static void ssd1306_draw_string(uint8_t x, uint8_t y, const char *s)
{
    while (*s != '\0')
    {
        ssd1306_draw_char(x, y, *s++);
        x = (uint8_t)(x + 6U);      /* 5 列字形 + 1 列间隔 */
        if (x > (OLED_WIDTH - 6U))
        {
            break;
        }
    }
}

/**
 * @brief  画矩形（fill=0 描边，fill=1 填充）
 */
static void ssd1306_rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t fill)
{
    for (uint8_t i = 0; i < w; i++)
    {
        for (uint8_t j = 0; j < h; j++)
        {
            if (fill || i == 0U || j == 0U || i == (w - 1U) || j == (h - 1U))
            {
                ssd1306_draw_pixel((uint8_t)(x + i), (uint8_t)(y + j), 1U);
            }
        }
    }
}

static void ssd1306_draw_rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h)
{
    ssd1306_rect(x, y, w, h, 0U);
}

static void ssd1306_fill_rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h)
{
    ssd1306_rect(x, y, w, h, 1U);
}

/* -------------------------------------------------- I2C 总线死锁恢复 */

/**
 * @brief  从机把 SDA 拉低导致总线死锁时的恢复流程
 * @note   原理：主机手动发 9 个 SCL 时钟脉冲，把从机残留的数据位移出，
 *         从机释放 SDA 后再补一个 STOP，最后重新初始化 I2C 外设。
 */
static void i2c_bus_recovery(void)
{
    GPIO_InitTypeDef io = {0};

    /* 1) 先把 SCL/SDA 切成开漏输出的普通 GPIO */
    HAL_I2C_DeInit(&hi2c1);

    io.Mode  = GPIO_MODE_OUTPUT_OD;
    io.Pull  = GPIO_PULLUP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    io.Pin   = OLED_SCL_PIN;
    HAL_GPIO_Init(OLED_SCL_PORT, &io);
    io.Pin   = OLED_SDA_PIN;
    HAL_GPIO_Init(OLED_SDA_PORT, &io);

    HAL_GPIO_WritePin(OLED_SDA_PORT, OLED_SDA_PIN, GPIO_PIN_SET);

    /* 2) 发 9 个时钟脉冲（先低后高），逼从机释放 SDA */
    for (uint8_t i = 0; i < I2C_RECOVER_PULSES; i++)
    {
        HAL_GPIO_WritePin(OLED_SCL_PORT, OLED_SCL_PIN, GPIO_PIN_RESET);
        HAL_Delay(1);
        HAL_GPIO_WritePin(OLED_SCL_PORT, OLED_SCL_PIN, GPIO_PIN_SET);
        HAL_Delay(1);
    }

    /* 3) 产生一个 STOP：SCL 高时把 SDA 由低拉高 */
    HAL_GPIO_WritePin(OLED_SDA_PORT, OLED_SDA_PIN, GPIO_PIN_RESET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(OLED_SCL_PORT, OLED_SCL_PIN, GPIO_PIN_SET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(OLED_SDA_PORT, OLED_SDA_PIN, GPIO_PIN_SET);
    HAL_Delay(1);

    /* 4) 重新初始化 I2C 外设 */
    i2c_init();
}

/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化硬件 I2C1（PB6/PB7，100kHz）
 */
static void i2c_init(void)
{
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_I2C1_CLK_ENABLE();

    hi2c1.Instance             = OLED_I2C;
    hi2c1.Init.ClockSpeed      = 100000U;       /* 标准模式 100kHz */
    hi2c1.Init.DutyCycle       = I2C_DUTYCYCLE_2;
    hi2c1.Init.OwnAddress1     = 0U;
    hi2c1.Init.AddressingMode  = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c1.Init.OwnAddress2     = 0U;
    hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c1.Init.NoStretchMode   = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c1) != HAL_OK)
    {
        error_handler();
    }
    /* PB6=SCL、PB7=SDA 的复用开漏由 HAL_I2C_Init 内部配置（AF_OD） */
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

