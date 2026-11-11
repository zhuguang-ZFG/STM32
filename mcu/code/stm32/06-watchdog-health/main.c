/* Two genuine task-progress reporters, supervisor feeds only when healthy.
 * MODE=0 IWDG, MODE=1 WWDG; FAULTS=1 enables explicit command injection.
 * Watchdogs must be tested after disconnecting debugger and resetting. */
#include "FreeRTOS.h"
#include "task.h"
#include "../platform/watchdog.h"
#include "../../common/reliability/service.h"
#include "../../common/reliability/health.h"
#include "../../common/reliability/record.h"
#ifndef MODE
#define MODE 0
#endif
#ifndef FAULTS
#define FAULTS 0
#endif
static health_t health;
static health_supervisor_t supervisor;
static device_service_t service;
static volatile uint8_t pause_mask;
static volatile bool stop_supervisor;
static volatile uint8_t pending_kind,pending_id;
static volatile uint32_t fault_at;
static volatile fault_record_t retained __attribute__((section(".noinit")));
volatile uint32_t g_previous_fault;
static uint32_t now_ms(void){return (uint32_t)xTaskGetTickCount();}
static void progress(uint8_t id){taskENTER_CRITICAL();health_progress(&health,id,now_ms());taskEXIT_CRITICAL();}
#if FAULTS
static void inject(void *u,uint8_t kind,uint8_t id){(void)u;pending_kind=kind;pending_id=id;fault_at=now_ms()+200U;}
#endif
static void worker(void *u){(void)u;for(;;){if(!(pause_mask&1U))progress(0);vTaskDelay(pdMS_TO_TICKS(10));}}
static void communication(void *u){
    (void)u;
    for(;;){
        if(!(pause_mask&2U)){
            for(unsigned i=0;i<128;i++){uint8_t b;bool loss;bool got=f407_uart_read(&b,&loss);if(loss)protocol_rx_loss(&service.rx);if(!got)break;taskENTER_CRITICAL();device_service_feed(&service,b,now_ms());taskEXIT_CRITICAL();}
            protocol_rx_poll(&service.rx,now_ms());progress(1);
        }
        protocol_tx_step(&service.tx,now_ms(),f407_uart_write,0);
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
static void supervise(void *u){
    (void)u;
#if MODE != 0
    f407_wwdg_start();
#else
    if(!f407_iwdg_start())for(;;){}
#endif
    bool recorded=false;
    for(;;){
        if(pending_kind && (int32_t)(now_ms()-fault_at)>=0){
            if(pending_kind==1)pause_mask|=(uint8_t)(1U<<pending_id);else stop_supervisor=true;
            pending_kind=0;
        }
        if(!stop_supervisor){
            taskENTER_CRITICAL();
            health_result_t result=health_evaluate(&health,now_ms());
            bool allowed=health_supervise(&supervisor,result);
            service.required=3;service.overdue=(uint8_t)result.overdue_mask;
            service.flags=(result.in_grace?1U:0U)|(supervisor.restart_latched?2U:0U);
            taskEXIT_CRITICAL();
            if(allowed){
#if MODE != 0
                f407_wwdg_feed();
#else
                f407_iwdg_feed();
#endif
            }else if(!recorded){fault_record_save(&retained,supervisor.first_overdue);recorded=true;}
        }else {
            if(!recorded){fault_record_save(&retained,0x80);recorded=true;}
#if MODE == 2
            REG32(0x40002c00UL,0UL)=0xff;REG32(0x40002c00UL,0UL)=0xff;
#endif
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}
void console_putc(char c){(void)c;}
void vApplicationStackOverflowHook(TaskHandle_t t,char *n){(void)t;(void)n;taskDISABLE_INTERRUPTS();for(;;){}}
int main(void){
    uint32_t reset=f407_reset_reason();
    fault_record_take(&retained,(reset&((1UL<<29)|(1UL<<30)))!=0,(uint32_t *)&g_previous_fault);
    if(!f407_uart_init())for(;;){}
    uint32_t deadlines[8]={MODE?30:500,MODE?30:500};
    if(!health_init(&health,3,deadlines,1000,0))for(;;){}
    device_service_init(&service,1,reset,true,
#if FAULTS
    inject,
#else
    NULL,
#endif
    NULL);
    if(xTaskCreate(worker,"worker",256,NULL,2,NULL)!=pdPASS || xTaskCreate(communication,"comm",768,NULL,3,NULL)!=pdPASS || xTaskCreate(supervise,"supervisor",384,NULL,4,NULL)!=pdPASS)for(;;){}
    vTaskStartScheduler();for(;;){}
}
