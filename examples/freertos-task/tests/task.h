#ifndef TEST_TASK_H
#define TEST_TASK_H
#include "FreeRTOS.h"
typedef void (*TaskFunction_t)(void *);
typedef void *TaskHandle_t;
BaseType_t xTaskCreate(TaskFunction_t task, const char *name, uint16_t depth,
                       void *argument, UBaseType_t priority, TaskHandle_t *handle);
void vTaskStartScheduler(void);
void vTaskDelay(TickType_t ticks);
TickType_t xTaskGetTickCount(void);
#endif
