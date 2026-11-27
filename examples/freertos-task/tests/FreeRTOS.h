#ifndef TEST_FREERTOS_H
#define TEST_FREERTOS_H
#include <stddef.h>
#include <stdint.h>
/* Controlled API boundary; this fixture does not implement a scheduler. */
typedef int BaseType_t;
typedef unsigned UBaseType_t;
typedef uint32_t TickType_t;
typedef uint32_t StackType_t;
#define pdFALSE 0
#define pdTRUE 1
#define pdPASS 1
#define pdFAIL 0
#define portMAX_DELAY UINT32_MAX
#define pdMS_TO_TICKS(ms) ((TickType_t)(ms))
#ifndef TEST_SYSCALL_RAW
#define TEST_SYSCALL_RAW 0x50U
#endif
#define configMAX_SYSCALL_INTERRUPT_PRIORITY TEST_SYSCALL_RAW
void test_yield_from_isr(BaseType_t woken);
#define portYIELD_FROM_ISR(woken) test_yield_from_isr(woken)
#endif
