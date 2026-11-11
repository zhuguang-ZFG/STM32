#include "FreeRTOS.h"
#include "task.h"
#include "../../common/logger/port.h"
void console_putc(char c){(void)c;}
void vApplicationStackOverflowHook(TaskHandle_t t,char *n){(void)t;(void)n;taskDISABLE_INTERRUPTS();for(;;){}}
int main(void){logger_create_tasks();vTaskStartScheduler();for(;;){}}
