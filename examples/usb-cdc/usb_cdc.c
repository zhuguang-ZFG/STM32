/**
 * @file    usb_cdc.c
 * @brief   虚拟串口：设备描述符 + CDC ACM 配置描述符 + HAL PCD 枚举。
 *
 * 描述符按 USB 2.0 第 9 章和 CDC PSTN 子类（ACM）自己列的，不是从 ST 中间件抄的。
 * VID 0x1209 是 pid.codes 的开源厂商号；PID 0x0001 只给这块实验板用，不要拿去量产。
 *
 * F103 的 USB 与 CAN1_RX0 共用 USB_LP_CAN1_RX0_IRQn。本文件占用这条中断。
 * PA11 = DM，PA12 = DP。BluePill 上 D+ 通常已经焊了 1.5 kΩ 上拉。
 */

#include "usb_cdc.h"

#include "stm32f1xx_hal.h"

#include <string.h>

#define CDC_RX_EP          0x02U
#define CDC_TX_EP          0x82U
#define CDC_NTF_EP         0x81U
#define CDC_RX_NUM         0x02U
#define CDC_TX_NUM         0x02U

static PCD_HandleTypeDef hpcd;

static uint8_t ctrl[96];
static uint16_t ctrl_total;
static uint16_t ctrl_sent;
static uint16_t ctrl_wlen;
static uint8_t ctrl_stage;          /* 0 空闲，1 数据 IN，2 数据 OUT，3 状态 IN（随后写地址） */
static uint8_t pending_addr;
static uint8_t addr_arm;

static uint8_t configured;
static uint8_t dtr;
static uint8_t line_coding[7] = {0x00, 0xC2, 0x01, 0x00, 0x00, 0x00, 0x08};

static uint8_t rx_pkt[64];
static uint8_t rx_ring[256];
static volatile uint16_t rx_w;
static volatile uint16_t rx_r;

static uint8_t tx_pkt[64];
static volatile uint8_t tx_busy;

static const uint8_t dev_desc[] = {
    0x12, 0x01, 0x00, 0x02, 0x02, 0x02, 0x00, 0x40,
    0x09, 0x12, 0x01, 0x00, 0x00, 0x01, 0x01, 0x02, 0x03, 0x01,
};

/* 配置总长 67（0x43）：通信接口 + 数据接口。 */
static const uint8_t cfg_desc[] = {
    0x09, 0x02, 0x43, 0x00, 0x02, 0x01, 0x00, 0x80, 0x32,
    0x09, 0x04, 0x00, 0x00, 0x01, 0x02, 0x02, 0x01, 0x00,
    0x05, 0x24, 0x00, 0x10, 0x01,
    0x05, 0x24, 0x01, 0x00, 0x01,
    0x04, 0x24, 0x02, 0x02,
    0x05, 0x24, 0x06, 0x00, 0x01,
    0x07, 0x05, 0x81, 0x03, 0x08, 0x00, 0x10,
    0x09, 0x04, 0x01, 0x00, 0x02, 0x0A, 0x00, 0x00, 0x00,
    0x07, 0x05, 0x02, 0x02, 0x40, 0x00, 0x00,
    0x07, 0x05, 0x82, 0x02, 0x40, 0x00, 0x00,
};

static void ctrl_in(const uint8_t *src, uint16_t len);
static void open_data_eps(void);

static uint8_t str_buf[48];

static uint16_t fill_string(const char *text)
{
    uint8_t n = 0U;
    while (text[n] != '\0' && n < 20U)
    {
        n++;
    }
    str_buf[0] = (uint8_t)(2U + (uint16_t)n * 2U);
    str_buf[1] = 0x03;
    for (uint8_t i = 0U; i < n; i++)
    {
        str_buf[2U + 2U * i] = (uint8_t)text[i];
        str_buf[3U + 2U * i] = 0U;
    }
    return str_buf[0];
}

static void ctrl_in(const uint8_t *src, uint16_t len)
{
    if (len > ctrl_wlen)
    {
        len = ctrl_wlen;
    }
    if (len > sizeof ctrl)
    {
        len = (uint16_t)sizeof ctrl;
    }
    if (len > 0U)
    {
        memcpy(ctrl, src, len);
    }
    ctrl_total = len;
    ctrl_sent = 0U;
    ctrl_stage = 1U;
    {
        uint16_t n = (len > 64U) ? 64U : len;
        (void)HAL_PCD_EP_Transmit(&hpcd, 0x80, ctrl, n);
        ctrl_sent = n;
    }
}

static void status_in(void)
{
    ctrl_stage = 3U;
    (void)HAL_PCD_EP_Transmit(&hpcd, 0x80, NULL, 0);
}

static void open_data_eps(void)
{
    (void)HAL_PCD_EP_Open(&hpcd, CDC_NTF_EP, 8, EP_TYPE_INTR);
    (void)HAL_PCD_EP_Open(&hpcd, CDC_TX_EP, 64, EP_TYPE_BULK);
    (void)HAL_PCD_EP_Open(&hpcd, CDC_RX_EP, 64, EP_TYPE_BULK);
    (void)HAL_PCD_EP_Receive(&hpcd, CDC_RX_EP, rx_pkt, 64);
}

static void handle_setup(void)
{
    uint8_t *s = (uint8_t *)hpcd.Setup;
    uint8_t bm = s[0];
    uint8_t req = s[1];
    uint16_t wvalue = (uint16_t)(s[2] | (s[3] << 8));
    uint16_t wlen = (uint16_t)(s[6] | (s[7] << 8));
    ctrl_wlen = wlen;
    addr_arm = 0U;

    if ((bm & 0x60U) == 0x20U)
    {
        /* CDC 类请求，收件人是接口。 */
        if (req == 0x20U && wlen == 7U)
        {
            ctrl_stage = 2U;
            (void)HAL_PCD_EP_Receive(&hpcd, 0x00, line_coding, 7);
            return;
        }
        if (req == 0x21U)
        {
            ctrl_in(line_coding, 7);
            return;
        }
        if (req == 0x22U)
        {
            dtr = (uint8_t)(wvalue & 0x01U);
            status_in();
            return;
        }
    }

    if (req == 0x06U && (bm & 0x80U) != 0U)
    {
        uint8_t kind = (uint8_t)(wvalue >> 8);
        uint8_t index = (uint8_t)(wvalue & 0xFFU);
        if (kind == 0x01U)
        {
            ctrl_in(dev_desc, sizeof dev_desc);
            return;
        }
        if (kind == 0x02U)
        {
            ctrl_in(cfg_desc, sizeof cfg_desc);
            return;
        }
        if (kind == 0x03U)
        {
            static const uint8_t lang[] = {0x04, 0x03, 0x09, 0x04};
            uint16_t n;
            if (index == 0U)
            {
                ctrl_in(lang, sizeof lang);
                return;
            }
            if (index == 1U)
            {
                n = fill_string("STM32 lab");
            }
            else if (index == 2U)
            {
                n = fill_string("CDC virtual COM");
            }
            else
            {
                n = fill_string("0001");
            }
            ctrl_in(str_buf, n);
            return;
        }
    }

    if (req == 0x05U)
    {
        pending_addr = (uint8_t)(wvalue & 0x7FU);
        addr_arm = 1U;
        status_in();
        return;
    }
    if (req == 0x09U)
    {
        configured = (wvalue != 0U) ? 1U : 0U;
        if (configured != 0U)
        {
            open_data_eps();
        }
        status_in();
        return;
    }
    if (req == 0x08U)
    {
        uint8_t v = configured;
        ctrl_in(&v, 1);
        return;
    }
    if (req == 0x00U)
    {
        uint8_t z[2] = {0, 0};
        ctrl_in(z, 2);
        return;
    }

    (void)HAL_PCD_EP_SetStall(&hpcd, 0x80);
    (void)HAL_PCD_EP_SetStall(&hpcd, 0x00);
}

void HAL_PCD_SetupStageCallback(PCD_HandleTypeDef *h)
{
    (void)h;
    handle_setup();
}

void HAL_PCD_DataInStageCallback(PCD_HandleTypeDef *h, uint8_t epnum)
{
    (void)h;
    if (epnum == 0U)
    {
        if (ctrl_stage == 1U && ctrl_sent < ctrl_total)
        {
            uint16_t left = (uint16_t)(ctrl_total - ctrl_sent);
            uint16_t n = (left > 64U) ? 64U : left;
            (void)HAL_PCD_EP_Transmit(&hpcd, 0x80, ctrl + ctrl_sent, n);
            ctrl_sent = (uint16_t)(ctrl_sent + n);
            return;
        }
        if (ctrl_stage == 1U && ctrl_total != 0U &&
            (ctrl_total % 64U) == 0U && ctrl_sent == ctrl_total &&
            ctrl_total < ctrl_wlen)
        {
            ctrl_sent = (uint16_t)(ctrl_sent + 1U); /* 只发一次零长包 */
            (void)HAL_PCD_EP_Transmit(&hpcd, 0x80, NULL, 0);
            return;
        }
        if (addr_arm != 0U)
        {
            /* SET_ADDRESS 的状态阶段是 IN。零长包发完再写入设备地址。 */
            (void)HAL_PCD_SetAddress(&hpcd, pending_addr);
            addr_arm = 0U;
            ctrl_stage = 0U;
            return;
        }
        if (ctrl_stage == 3U)
        {
            ctrl_stage = 0U;
            return;
        }
        ctrl_stage = 0U;
        (void)HAL_PCD_EP_Receive(&hpcd, 0x00, NULL, 0);
        return;
    }
    if (epnum == CDC_TX_NUM)
    {
        tx_busy = 0U;
    }
}

void HAL_PCD_DataOutStageCallback(PCD_HandleTypeDef *h, uint8_t epnum)
{
    (void)h;
    if (epnum == 0U && ctrl_stage == 2U)
    {
        ctrl_stage = 0U;
        status_in();
        return;
    }
    if (epnum == CDC_RX_NUM)
    {
        uint32_t n = HAL_PCD_EP_GetRxCount(&hpcd, CDC_RX_EP);
        for (uint32_t i = 0U; i < n; i++)
        {
            uint16_t next = (uint16_t)((rx_w + 1U) & 0xFFU);
            if (next == rx_r)
            {
                break;
            }
            rx_ring[rx_w] = rx_pkt[i];
            rx_w = next;
        }
        (void)HAL_PCD_EP_Receive(&hpcd, CDC_RX_EP, rx_pkt, 64);
    }
}

void HAL_PCD_ResetCallback(PCD_HandleTypeDef *h)
{
    (void)HAL_PCD_EP_Open(h, 0x00, 64, EP_TYPE_CTRL);
    (void)HAL_PCD_EP_Open(h, 0x80, 64, EP_TYPE_CTRL);
    (void)HAL_PCD_SetAddress(h, 0);
    configured = 0U;
    dtr = 0U;
    tx_busy = 0U;
    ctrl_stage = 0U;
}

void HAL_PCD_MspInit(PCD_HandleTypeDef *h)
{
    GPIO_InitTypeDef io = {0};
    (void)h;
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USB_CLK_ENABLE();
    io.Pin = GPIO_PIN_11 | GPIO_PIN_12;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &io);
    HAL_NVIC_SetPriority(USB_LP_CAN1_RX0_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(USB_LP_CAN1_RX0_IRQn);
}

void USB_LP_CAN1_RX0_IRQHandler(void)
{
    HAL_PCD_IRQHandler(&hpcd);
}

void usb_cdc_init(void)
{
    hpcd.Instance = USB;
    hpcd.Init.dev_endpoints = 8;
    hpcd.Init.speed = PCD_SPEED_FULL;
    hpcd.Init.ep0_mps = EP_MPS_64;
    hpcd.Init.phy_itface = PCD_PHY_EMBEDDED;
    hpcd.Init.Sof_enable = DISABLE;
    hpcd.Init.low_power_enable = DISABLE;
    hpcd.Init.lpm_enable = DISABLE;
    hpcd.Init.battery_charging_enable = DISABLE;
    if (HAL_PCD_Init(&hpcd) != HAL_OK)
    {
        return;
    }
    (void)HAL_PCD_Start(&hpcd);
}

uint8_t usb_cdc_ready(void)
{
    return configured;
}

uint8_t usb_cdc_dtr(void)
{
    return dtr;
}

uint16_t usb_cdc_read(uint8_t *dst, uint16_t cap)
{
    uint16_t n = 0U;
    while (n < cap && rx_r != rx_w)
    {
        dst[n] = rx_ring[rx_r];
        rx_r = (uint16_t)((rx_r + 1U) & 0xFFU);
        n++;
    }
    return n;
}

int usb_cdc_write(const uint8_t *src, uint16_t len)
{
    if (configured == 0U || tx_busy != 0U || len == 0U || len > 64U)
    {
        return -1;
    }
    memcpy(tx_pkt, src, len);
    tx_busy = 1U;
    if (HAL_PCD_EP_Transmit(&hpcd, CDC_TX_EP, tx_pkt, len) != HAL_OK)
    {
        tx_busy = 0U;
        return -1;
    }
    return 0;
}
