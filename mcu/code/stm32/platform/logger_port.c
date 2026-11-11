/* F407 real ADC1/TIM2/DMA2 + AT24C02 adapter; HSI16 reset clock.
 * ADC trigger EXTSEL=6: ST HAL ADC_EXTERNALTRIGCONV_T2_TRGO.
 * ADC1 DMA2 Stream0 Ch0 IRQ56; UART Stream5 is separate.
 */
#include "../../common/logger/port.h"
#include "uart.h"
#include "watchdog.h"
#include "FreeRTOS.h"
#include "task.h"
#include <string.h>
static volatile fault_record_t retained __attribute__((section(".noinit")));
static TaskHandle_t sample_task;
static volatile uint16_t adc_data[2],adc_latest;
static volatile uint32_t adc_stamp,adc_errors;
static uint16_t adc_period;
static bool adc_active;
static uint32_t previous_reset;
uint8_t logger_port_platform(void){return 1;}
uint8_t logger_port_sensor(void){return 1;}
uint32_t logger_port_now(void){return (uint32_t)xTaskGetTickCount();}
uint32_t logger_port_reset(void){previous_reset=f407_reset_reason();return previous_reset;}
uint32_t logger_port_previous_fault(bool *valid){uint32_t mask=0;*valid=fault_record_take(&retained,(previous_reset&((1UL<<29)|(1UL<<30)))!=0,&mask);return mask;}
bool logger_port_read(uint8_t *b,bool *loss){return f407_uart_read(b,loss);}
size_t logger_port_write(void *u,const uint8_t *b,size_t n){return f407_uart_write(u,b,n);}
bool logger_port_watchdog_start(void){return f407_iwdg_start();}
void logger_port_watchdog_feed(void){f407_iwdg_feed();}
void logger_port_fault(uint32_t mask){fault_record_save(&retained,mask);}
void DMA2_Stream0_IRQHandler(void){
    uint32_t flags=REG32(0x40026400UL,0UL);REG32(0x40026400UL,8UL)=flags&0x3dU;
    if((flags&0x30U)==0x30U || (flags&0xdU))adc_errors++;
    if(flags&0x30U){
        adc_latest=adc_data[(flags&0x20U)?1:0];adc_stamp=(uint32_t)xTaskGetTickCountFromISR();
        if(sample_task){BaseType_t wake=pdFALSE;vTaskNotifyGiveFromISR(sample_task,&wake);portYIELD_FROM_ISR(wake);}
    }
}
static bool adc_start(uint16_t period){
    REG32(RCC_BASE_F4,0x30UL)|=(1UL<<22)|1UL;REG32(RCC_BASE_F4,0x44UL)|=1UL<<8;
    REG32(RCC_BASE_F4,0x40UL)|=1UL;(void)REG32(RCC_BASE_F4,0x44UL);
    REG32(0x40020000UL,0UL)|=3UL;REG32(0x40020000UL,0xcUL)&=~3UL;
    REG32(0x40000000UL,0UL)=0;REG32(0x40000000UL,4UL)=0;
    REG32(0x40012000UL,8UL)=0;REG32(0x40012000UL,0UL)=0;
    REG32(0x40026410UL,0UL)=0;unsigned limit=10000;
    while((REG32(0x40026410UL,0UL)&1U)&&--limit){}if(!limit)return false;
    REG32(0x40026400UL,8UL)=0x3dU;REG32(0x40026410UL,4UL)=2;
    REG32(0x40026410UL,8UL)=0x4001204cUL;REG32(0x40026410UL,0xcUL)=(uint32_t)(uintptr_t)adc_data;
    REG32(0x40026410UL,0x14UL)=0;REG32(0x40026410UL,0UL)=(1UL<<13)|(1UL<<11)|(1UL<<10)|(1UL<<8)|0x1dU;
    REG32(0x40012300UL,4UL)=(REG32(0x40012300UL,4UL)&~(3UL<<16))|(1UL<<16); /* APB2 /4 */
    REG32(0x40012000UL,4UL)=0;REG32(0x40012000UL,0x10UL)=7; /* 480 cycle sample */
    REG32(0x40012000UL,0x2cUL)=0;REG32(0x40012000UL,0x34UL)=0;
    REG32(0x40012000UL,8UL)=1UL|(1UL<<8)|(1UL<<14)|(6UL<<24)|(1UL<<28);
    vTaskDelay(pdMS_TO_TICKS(1)); /* ADON stabilization */
    sample_task=xTaskGetCurrentTaskHandle();
    ulTaskNotifyTake(pdTRUE,0);
    ((volatile uint8_t *)0xe000e400UL)[56]=0x60;REG32(0xe000e100UL,4UL)=1UL<<24;
    REG32(0x40000000UL,0x28UL)=15999;REG32(0x40000000UL,0x2cUL)=period-1U;
    REG32(0x40000000UL,0x14UL)=1;REG32(0x40000000UL,0x10UL)=0;
    REG32(0x40000000UL,4UL)=2UL<<4;REG32(0x40000000UL,0UL)=1;
    adc_period=period;return true;
}
bool logger_port_sample(uint16_t period,int32_t raw[6],uint8_t *mask,uint32_t *stamp){
    if(!adc_active||period!=adc_period)adc_active=adc_start(period);
    if(!adc_active){vTaskDelay(pdMS_TO_TICKS(period));return false;}
    uint32_t count=ulTaskNotifyTake(pdTRUE,pdMS_TO_TICKS(period+50U));
    if(!count){adc_active=false;return false;}
    uint32_t m=f407_lock();raw[0]=adc_latest;*stamp=adc_stamp;bool good=adc_errors==0&&count==1;adc_errors=0;f407_unlock(m);
    *mask=good?1:0;return good;
}
void logger_port_pause(bool pause){if(pause)REG32(0x40000000UL,0UL)=0;adc_active=false;ulTaskNotifyTake(pdTRUE,0);}
#define I2C 0x40005400UL
#define CR1 REG32(I2C,0UL)
#define SR1 REG32(I2C,0x14UL)
#define SR2 REG32(I2C,0x18UL)
#define DR REG32(I2C,0x10UL)
#define ACK (1UL<<10)
#define STOP (1UL<<9)
#define ERRORS 0xf00UL
static bool wait_bit(uint32_t bit){
    uint32_t begin=logger_port_now();
    while(!(SR1&bit)){if((SR1&ERRORS)||logger_port_now()-begin>=20U)return false;}
    return !(SR1&ERRORS);
}
static bool idle(void){uint32_t begin=logger_port_now();while(SR2&2U)if(logger_port_now()-begin>=20U)return false;return true;}
static void clear_addr(void){(void)SR1;(void)SR2;}
static void abort_i2c(void){if(!(SR1&(1UL<<9)))CR1|=STOP;SR1&=~ERRORS;CR1|=ACK;}
static bool addr(bool read){CR1|=1UL<<8;if(!wait_bit(1))return false;DR=0xa0U|(read?1U:0U);return wait_bit(2);}
static bool put(uint8_t b){if(!wait_bit(1UL<<7))return false;DR=b;return wait_bit(1UL<<2);}
static bool poll_ready(void){
    for(unsigned i=0;i<20;i++){
        if(!idle())return false;
        if(addr(false)){clear_addr();CR1|=STOP;return true;}
        bool nack=(SR1&ERRORS)==ACK;abort_i2c();if(!nack)return false;vTaskDelay(1);
    }
    return false;
}
static bool read_byte(uint8_t address,uint8_t *out){
    if(!idle()||!addr(false))return false;
    clear_addr();
    if(!put(address)||!addr(true))return false;
    uint32_t m=f407_lock();CR1&=~(ACK|(1UL<<11));clear_addr();CR1|=STOP;f407_unlock(m);
    if(!wait_bit(1UL<<6))return false;
    *out=(uint8_t)DR;CR1|=ACK;return idle();
}
static bool ee_read(void *u,uint16_t at,uint8_t *out,size_t n){
    (void)u;if(at+n>256)return false;
    for(size_t i=0;i<n;i++)if(!read_byte((uint8_t)(at+i),out+i)){abort_i2c();return false;}
    return true;
}
static bool ee_write(void *u,uint16_t at,const uint8_t *p,size_t n){
    (void)u;if(!n||at+n>256||at/8!=(at+n-1)/8)return false;
    bool ok=idle()&&addr(false);
    if(ok){clear_addr();ok=put((uint8_t)at);}
    for(size_t i=0;ok&&i<n;i++)ok=put(p[i]);
    CR1|=STOP;if(ok)ok=poll_ready();if(!ok)abort_i2c();return ok;
}
bool logger_port_init(void){
    if(!f407_uart_init())return false;
    REG32(RCC_BASE_F4,0x30UL)|=2;REG32(RCC_BASE_F4,0x40UL)|=1UL<<21;
    REG32(0x40020400UL,0UL)=(REG32(0x40020400UL,0UL)&~(15UL<<12))|(10UL<<12);
    REG32(0x40020400UL,4UL)|=(1UL<<6)|(1UL<<7);
    REG32(0x40020400UL,8UL)|=15UL<<12;
    REG32(0x40020400UL,0x20UL)=(REG32(0x40020400UL,0x20UL)&0x00ffffffUL)|0x44000000UL;
    CR1=1UL<<15;CR1=0;REG32(I2C,4UL)=16;REG32(I2C,0x1cUL)=80;REG32(I2C,0x20UL)=17;CR1=ACK|1;
    return true;
}
bool logger_port_load(uint8_t out[128]){return config_slots_load(ee_read,NULL,out);}
bool logger_port_save(const uint8_t in[128]){return config_slots_save(ee_read,ee_write,NULL,in);}
