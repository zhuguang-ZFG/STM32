/**
 * @file    usb_cdc.h
 * @brief   F103 全速 USB CDC（虚拟串口），只用 HAL PCD，不链接 ST USB 中间件。
 */
#ifndef USB_CDC_H
#define USB_CDC_H

#include <stdint.h>

void usb_cdc_init(void);
uint8_t usb_cdc_ready(void);
uint8_t usb_cdc_dtr(void);
uint16_t usb_cdc_read(uint8_t *dst, uint16_t cap);
int usb_cdc_write(const uint8_t *src, uint16_t len);

#endif
