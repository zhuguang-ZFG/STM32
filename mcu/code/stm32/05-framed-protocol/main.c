/* USART1 binary protocol; actual transport reused by the watchdog/recorder.
 * PA9 TX, PA10 RX, USB-TTL 3.3V + GND. No printf on this UART. */
#include "../platform/uart.h"
#include "../../common/reliability/service.h"
static volatile uint32_t ms;
void SysTick_Handler(void){++ms;}
int main(void){
    uint32_t reason=f407_reset_reason();
    if(!f407_uart_init())for(;;){}
    REG32(0xe000e010UL,4UL)=15999;REG32(0xe000e010UL,8UL)=0;REG32(0xe000e010UL,0UL)=7;
    device_service_t service;device_service_init(&service,1,reason,false,0,0);
    for(;;){
        for(unsigned i=0;i<512;i++){uint8_t b;bool loss;bool got=f407_uart_read(&b,&loss);if(loss)protocol_rx_loss(&service.rx);if(!got)break;device_service_feed(&service,b,ms);}
        protocol_rx_poll(&service.rx,ms);
        protocol_tx_step(&service.tx,ms,f407_uart_write,0);
    }
}
