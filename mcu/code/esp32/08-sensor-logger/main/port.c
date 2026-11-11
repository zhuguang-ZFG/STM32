/* Real board QMI8658 (GPIO1/2, 0x6a), UART1 (10/11), dedicated NVS key. */
#include "../../../common/logger/port.h"
#include "driver/uart.h"
#include "driver/i2c_master.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "esp_task_wdt.h"
#include "esp_attr.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>
static QueueHandle_t events;
static i2c_master_dev_handle_t imu;
static bool imu_ready, nvs_ready;
static uint32_t retry_at;
static bool attempted;
static TickType_t wake;
static uint16_t previous_period;
static esp_task_wdt_user_handle_t health_user;
static RTC_NOINIT_ATTR fault_record_t retained;
static uint32_t previous_reset;
static uint8_t rx[128];static int rx_len,rx_pos;
uint8_t logger_port_platform(void){return 2;}
uint8_t logger_port_sensor(void){return 2;}
uint32_t logger_port_now(void){return (uint32_t)(esp_timer_get_time()/1000);}
uint32_t logger_port_reset(void){previous_reset=(uint32_t)esp_reset_reason();return previous_reset;}
uint32_t logger_port_previous_fault(bool *valid){uint32_t mask=0;*valid=fault_record_take(&retained,previous_reset==ESP_RST_TASK_WDT||previous_reset==ESP_RST_INT_WDT||previous_reset==ESP_RST_PANIC,&mask);return mask;}
static bool read_reg(uint8_t reg,uint8_t *p,size_t n){return i2c_master_transmit_receive(imu,&reg,1,p,n,100)==ESP_OK;}
static bool write_reg(uint8_t reg,uint8_t value){uint8_t p[2]={reg,value};return i2c_master_transmit(imu,p,2,100)==ESP_OK;}
static bool configure_imu(void){
    uint8_t id;
    if(!read_reg(0,&id,1)||id!=5||!write_reg(0x60,0xb0))return false;
    vTaskDelay(pdMS_TO_TICKS(20));
    return write_reg(8,0)&&write_reg(2,0x40)&&write_reg(3,0x15)&&write_reg(4,0x55)&&write_reg(8,3);
}
bool logger_port_init(void){
    uart_config_t cfg={.baud_rate=115200,.data_bits=UART_DATA_8_BITS,.parity=UART_PARITY_DISABLE,.stop_bits=UART_STOP_BITS_1,.flow_ctrl=UART_HW_FLOWCTRL_DISABLE,.source_clk=UART_SCLK_DEFAULT};
    if(uart_driver_install(UART_NUM_1,1024,0,20,&events,0)!=ESP_OK||uart_param_config(UART_NUM_1,&cfg)!=ESP_OK||uart_set_pin(UART_NUM_1,10,11,UART_PIN_NO_CHANGE,UART_PIN_NO_CHANGE)!=ESP_OK)return false;
    i2c_master_bus_handle_t bus;
    i2c_master_bus_config_t bc={.i2c_port=I2C_NUM_0,.sda_io_num=1,.scl_io_num=2,.clk_source=I2C_CLK_SRC_DEFAULT,.glitch_ignore_cnt=7,.flags.enable_internal_pullup=true};
    if(i2c_new_master_bus(&bc,&bus)!=ESP_OK)return false;
    i2c_device_config_t dc={.dev_addr_length=I2C_ADDR_BIT_LEN_7,.device_address=0x6a,.scl_speed_hz=100000};
    if(i2c_master_bus_add_device(bus,&dc,&imu)!=ESP_OK)return false;
    /* Do not erase the partition on init errors: other users may own NVS keys. */
    nvs_ready=nvs_flash_init()==ESP_OK;
    return true;
}
bool logger_port_sample(uint16_t period,int32_t raw[6],uint8_t *mask,uint32_t *stamp){
    if(previous_period!=period){wake=xTaskGetTickCount();previous_period=period;}
    xTaskDelayUntil(&wake,pdMS_TO_TICKS(period));
    uint32_t time=logger_port_now();
    if(!imu_ready){
        if(attempted&&(int32_t)(time-retry_at)<0)return false;
        attempted=true;retry_at=time+1000;imu_ready=configure_imu();if(!imu_ready)return false;
    }
    uint8_t status,data[12];
    if(!read_reg(0x2e,&status,1)){imu_ready=false;return false;}
    if((status&3)!=3)return false;
    if(!read_reg(0x35,data,12)){imu_ready=false;return false;}
    for(unsigned i=0;i<6;i++){uint32_t v=(uint32_t)data[2*i]|((uint32_t)data[2*i+1]<<8);raw[i]=v>=32768?(int32_t)v-65536:(int32_t)v;}
    *mask=63;*stamp=logger_port_now();return true;
}
void logger_port_pause(bool pause){if(pause&&imu_ready)write_reg(8,0);imu_ready=false;attempted=false;previous_period=0;}
bool logger_port_read(uint8_t *b,bool *loss){
    *loss=false;uart_event_t event;
    while(xQueueReceive(events,&event,0)==pdTRUE){
        if(event.type==UART_FIFO_OVF||event.type==UART_BUFFER_FULL||event.type==UART_FRAME_ERR||event.type==UART_PARITY_ERR||event.type==UART_BREAK){
            uart_flush_input(UART_NUM_1);rx_pos=rx_len=0;*loss=true;
        }
    }
    if(rx_pos==rx_len){rx_len=uart_read_bytes(UART_NUM_1,rx,sizeof(rx),0);rx_pos=0;}
    if(rx_len<=0){rx_len=0;return false;}
    *b=rx[rx_pos++];return true;
}
size_t logger_port_write(void *u,const uint8_t *p,size_t n){(void)u;int sent=uart_tx_chars(UART_NUM_1,(const char*)p,n);return sent>0?(size_t)sent:0;}
bool logger_port_load(uint8_t out[128]){
    if(!nvs_ready)return false;
    nvs_handle_t h;if(nvs_open("mcu_logger",NVS_READONLY,&h)!=ESP_OK)return false;
    size_t size=128;esp_err_t err=nvs_get_blob(h,"config",out,&size);nvs_close(h);return err==ESP_OK&&size==128;
}
bool logger_port_save(const uint8_t in[128]){
    if(!nvs_ready)return false;
    nvs_handle_t h;if(nvs_open("mcu_logger",NVS_READWRITE,&h)!=ESP_OK)return false;
    esp_err_t err=nvs_set_blob(h,"config",in,128);if(err==ESP_OK)err=nvs_commit(h);
    uint8_t verify[128];size_t n=128;if(err==ESP_OK)err=nvs_get_blob(h,"config",verify,&n);
    nvs_close(h);return err==ESP_OK&&n==128&&!memcmp(in,verify,128);
}
bool logger_port_watchdog_start(void){
    esp_task_wdt_config_t c={.timeout_ms=2000,.idle_core_mask=(1U<<portNUM_PROCESSORS)-1U,.trigger_panic=true};
    esp_err_t e=esp_task_wdt_init(&c);if(e==ESP_ERR_INVALID_STATE)e=esp_task_wdt_reconfigure(&c);
    return e==ESP_OK&&esp_task_wdt_add_user("logger-health",&health_user)==ESP_OK;
}
void logger_port_watchdog_feed(void){ESP_ERROR_CHECK(esp_task_wdt_reset_user(health_user));}
void logger_port_fault(uint32_t mask){fault_record_save(&retained,mask);}
