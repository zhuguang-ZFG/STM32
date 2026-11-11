/* IDF5.5.2: UART1 GPIO10/11, no GPIO2 output (GPIO2 is board I2C SCL).
 * Task progress != sensor success; only the supervisor resets the health user. */
#include "service.h"
#include "health.h"
#include "record.h"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "esp_task_wdt.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_attr.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
static portMUX_TYPE mux=portMUX_INITIALIZER_UNLOCKED;
static health_t health;static health_supervisor_t supervisor;static device_service_t service;
static esp_task_wdt_user_handle_t health_user;
static uint8_t pause_mask;static bool stop_supervisor;
static uint8_t pending_kind,pending_id;static uint32_t fault_at;
static RTC_NOINIT_ATTR fault_record_t retained;
static uint32_t now_ms(void){return (uint32_t)(esp_timer_get_time()/1000);}
static void progress(uint8_t id){portENTER_CRITICAL(&mux);health_progress(&health,id,now_ms());portEXIT_CRITICAL(&mux);}
#if CONFIG_RELIABILITY_TEST_FAULTS
static void inject(void *u,uint8_t kind,uint8_t id){(void)u;pending_kind=kind;pending_id=id;fault_at=now_ms()+200U;}
#endif
static size_t write_some(void *u,const uint8_t *p,size_t n){(void)u;int sent=uart_tx_chars(UART_NUM_1,(const char *)p,n);return sent>0?(size_t)sent:0;}
static void worker(void *u){(void)u;for(;;){portENTER_CRITICAL(&mux);bool pause=pause_mask&1U;portEXIT_CRITICAL(&mux);if(!pause)progress(0);vTaskDelay(pdMS_TO_TICKS(100));}}
static void communication(void *u){
    (void)u;uint8_t bytes[128];
    for(;;){
        int n=uart_read_bytes(UART_NUM_1,bytes,sizeof(bytes),0);
        portENTER_CRITICAL(&mux);
        if(!(pause_mask&2U)){
            for(int i=0;i<n;i++)device_service_feed(&service,bytes[i],now_ms());
            protocol_rx_poll(&service.rx,now_ms());health_progress(&health,1,now_ms());
        }
        portEXIT_CRITICAL(&mux);
        protocol_tx_step(&service.tx,now_ms(),write_some,NULL);
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
static void supervise(void *u){
    (void)u;
    bool recorded=false;
    for(;;){
        portENTER_CRITICAL(&mux);
        if(pending_kind && (int32_t)(now_ms()-fault_at)>=0){
            if(pending_kind==1)pause_mask|=(uint8_t)(1U<<pending_id);else stop_supervisor=true;
            pending_kind=0;
        }
        health_result_t r=health_evaluate(&health,now_ms());
        bool allowed=!stop_supervisor&&health_supervise(&supervisor,r);
        service.required=3;service.overdue=(uint8_t)r.overdue_mask;
        service.flags=(r.in_grace?1U:0U)|(supervisor.restart_latched?2U:0U);
        uint32_t mask=stop_supervisor?0x80:supervisor.first_overdue;
        portEXIT_CRITICAL(&mux);
        if(allowed)ESP_ERROR_CHECK(esp_task_wdt_reset_user(health_user));
        else if(!recorded){fault_record_save(&retained,mask);recorded=true;}
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
void app_main(void){
    uint32_t reset=(uint32_t)esp_reset_reason(),previous=0;
    bool valid=fault_record_take(&retained,reset==ESP_RST_TASK_WDT||reset==ESP_RST_INT_WDT||reset==ESP_RST_PANIC,&previous);
    ESP_LOGI("health","reset=%lu retained=%d overdue=%lu",(unsigned long)reset,valid,(unsigned long)previous);
    uart_config_t cfg={.baud_rate=115200,.data_bits=UART_DATA_8_BITS,.parity=UART_PARITY_DISABLE,.stop_bits=UART_STOP_BITS_1,.flow_ctrl=UART_HW_FLOWCTRL_DISABLE,.source_clk=UART_SCLK_DEFAULT};
    ESP_ERROR_CHECK(uart_driver_install(UART_NUM_1,1024,0,0,NULL,0));ESP_ERROR_CHECK(uart_param_config(UART_NUM_1,&cfg));
    ESP_ERROR_CHECK(uart_set_pin(UART_NUM_1,10,11,UART_PIN_NO_CHANGE,UART_PIN_NO_CHANGE));
    uint32_t deadlines[8]={500,500};
    ESP_ERROR_CHECK(health_init(&health,3,deadlines,1000,now_ms())?ESP_OK:ESP_FAIL);
    device_service_init(&service,2,reset,true,
#if CONFIG_RELIABILITY_TEST_FAULTS
    inject,
#else
    NULL,
#endif
    NULL);
    esp_task_wdt_config_t wdt={.timeout_ms=2000,.idle_core_mask=(1U<<portNUM_PROCESSORS)-1U,.trigger_panic=true};
    esp_err_t err=esp_task_wdt_init(&wdt);if(err==ESP_ERR_INVALID_STATE)err=esp_task_wdt_reconfigure(&wdt);ESP_ERROR_CHECK(err);
    ESP_ERROR_CHECK(esp_task_wdt_add_user("health",&health_user));
    ESP_ERROR_CHECK(xTaskCreate(worker,"worker",2048,NULL,3,NULL)==pdPASS?ESP_OK:ESP_ERR_NO_MEM);
    ESP_ERROR_CHECK(xTaskCreate(communication,"comm",4096,NULL,4,NULL)==pdPASS?ESP_OK:ESP_ERR_NO_MEM);
    ESP_ERROR_CHECK(xTaskCreate(supervise,"supervisor",2048,NULL,5,NULL)==pdPASS?ESP_OK:ESP_ERR_NO_MEM);
}
