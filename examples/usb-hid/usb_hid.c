/**
 * @file    usb_hid.c
 * @brief   启动式键盘：8 字节输入报告，HAL PCD 枚举。
 *
 * 报告描述符按 HID 1.11 附录 B 的键盘格式列（修饰键 + 保留 + 6 个用法码）。
 * 不链接 ST 的 USB 中间件。VID 0x1209 / PID 0x0002 只给实验板占位。
 *
 * PA11 = DM，PA12 = DP。中断是 USB_LP_CAN1_RX0，和 bxCAN 接收共用，不要和 CAN 示例编在一起。
 */

#include "usb_hid.h"

#include "stm32f1xx_hal.h"

#include <string.h>

static PCD_HandleTypeDef hpcd;

static uint8_t ctrl[96];
static uint16_t ctrl_total;
static uint16_t ctrl_sent;
static uint16_t ctrl_wlen;
static uint8_t ctrl_stage;
static uint8_t pending_addr;
static uint8_t addr_arm;
static uint8_t configured;

static uint8_t report[8];
static volatile uint8_t tx_busy;
static uint8_t protocol = 1U;

/* 63 字节。逻辑最大 101，6 键无冲。 */
static const uint8_t report_desc[] = {
    0x05, 0x01, 0x09, 0x06, 0xA1, 0x01, 0x05, 0x07, 0x19, 0xE0, 0x29, 0xE7,
    0x15, 0x00, 0x25, 0x01, 0x75, 0x01, 0x95, 0x08, 0x81, 0x02, 0x95, 0x01,
    0x75, 0x08, 0x81, 0x01, 0x95, 0x05, 0x75, 0x01, 0x05, 0x08, 0x19, 0x01,
    0x29, 0x05, 0x91, 0x02, 0x95, 0x01, 0x75, 0x03, 0x91, 0x01, 0x95, 0x06,
    0x75, 0x08, 0x15, 0x00, 0x25, 0x65, 0x05, 0x07, 0x19, 0x00, 0x29, 0x65,
    0x81, 0x00, 0xC0,
};

static const uint8_t dev_desc[] = {
    0x12, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x40,
    0x09, 0x12, 0x02, 0x00, 0x00, 0x01, 0x01, 0x02, 0x03, 0x01,
};

/* 配置总长 34（0x22）：一个启动键盘接口 + 中断 IN。 */
static const uint8_t cfg_desc[] = {
    0x09, 0x02, 0x22, 0x00, 0x01, 0x01, 0x00, 0x80, 0x32,
    0x09, 0x04, 0x00, 0x00, 0x01, 0x03, 0x01, 0x01, 0x00,
    0x09, 0x21, 0x11, 0x01, 0x00, 0x01, 0x22, 0x3F, 0x00,
    0x07, 0x05, 0x81, 0x03, 0x08, 0x00, 0x0A,
};

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
        if (req == 0x06U && (uint8_t)(wvalue >> 8) == 0x22U)
        {
            ctrl_in(report_desc, sizeof report_desc);
            return;
        }
        if (req == 0x0AU)
        {
            status_in();
            return;
        }
        if (req == 0x0BU)
        {
            protocol = (uint8_t)(wvalue & 0xFFU);
            status_in();
            return;
        }
        if (req == 0x03U)
        {
            uint8_t p = protocol;
            ctrl_in(&p, 1);
            return;
        }
        if (req == 0x09U)
        {
            /* SET_REPORT：主机写 LED。收完再应答。 */
            ctrl_stage = 2U;
            (void)HAL_PCD_EP_Receive(&hpcd, 0x00, ctrl, (wlen > 8U) ? 8U : wlen);
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
            n = fill_string(index == 1U ? "STM32 lab" :
                            index == 2U ? "HID keyboard" : "0002");
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
    if (req == 0x09U && (bm & 0x60U) == 0U)
    {
        configured = (wvalue != 0U) ? 1U : 0U;
        if (configured != 0U)
        {
            (void)HAL_PCD_EP_Open(&hpcd, 0x81, 8, EP_TYPE_INTR);
        }
        status_in();
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
        if (addr_arm != 0U)
        {
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
    if (epnum == 1U)
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
    }
}

void HAL_PCD_ResetCallback(PCD_HandleTypeDef *h)
{
    (void)HAL_PCD_EP_Open(h, 0x00, 64, EP_TYPE_CTRL);
    (void)HAL_PCD_EP_Open(h, 0x80, 64, EP_TYPE_CTRL);
    (void)HAL_PCD_SetAddress(h, 0);
    configured = 0U;
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

void usb_hid_init(void)
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

uint8_t usb_hid_ready(void)
{
    return configured;
}

int usb_hid_key(uint8_t usage, uint8_t down)
{
    if (configured == 0U || tx_busy != 0U)
    {
        return -1;
    }
    memset(report, 0, sizeof report);
    if (down != 0U)
    {
        report[2] = usage;
    }
    tx_busy = 1U;
    if (HAL_PCD_EP_Transmit(&hpcd, 0x81, report, sizeof report) != HAL_OK)
    {
        tx_busy = 0U;
        return -1;
    }
    return 0;
}
