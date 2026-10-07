/**
 * @file    usb_hid.h
 * @brief   F103 全速 USB HID 键盘，只用 HAL PCD。
 */
#ifndef USB_HID_H
#define USB_HID_H

#include <stdint.h>

void usb_hid_init(void);
uint8_t usb_hid_ready(void);
int usb_hid_key(uint8_t usage, uint8_t down);

#endif
