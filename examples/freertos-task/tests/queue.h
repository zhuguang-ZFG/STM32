#ifndef TEST_QUEUE_H
#define TEST_QUEUE_H
#include "FreeRTOS.h"
typedef void *QueueHandle_t;
QueueHandle_t xQueueCreate(UBaseType_t length, UBaseType_t item_size);
BaseType_t xQueueReceive(QueueHandle_t queue, void *item, TickType_t wait);
BaseType_t xQueueSendFromISR(QueueHandle_t queue, const void *item, BaseType_t *woken);
#endif
