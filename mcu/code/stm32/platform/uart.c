/* ST CMSIS stm32f407xx.h: DMA2 Stream5 HISR TE=9, HT=10, TC=11;
 * RCC_CSR offset 0x74. PA9/PA10 AF7. Reset HSI16 required. */
#include "uart.h"
#include "../../common/behavior/circular.h"
#define RCC RCC_BASE_F4
#define DMA 0x40026400UL
#define S5 0x40026488UL
#define UART 0x40011000UL
static volatile uint8_t ring[256];
static byte_queue_t queue;
static dma_cursor_t cursor;
static volatile bool restart_dma;
uint32_t f407_lock(void){uint32_t m;__asm__ volatile("mrs %0, primask\ncpsid i":"=r"(m)::"memory");return m;}
void f407_unlock(uint32_t m){__asm__ volatile("msr primask, %0"::"r"(m):"memory");}
uint32_t f407_reset_reason(void){uint32_t flags=REG32(RCC,RCC_RESET_OFFSET)&0xfe000000UL;REG32(RCC,RCC_RESET_OFFSET)|=1UL<<24;return flags;}
static bool dma_start(void){
    REG32(S5,0UL)=0;
    unsigned limit=10000;while((REG32(S5,0UL)&1U)&&--limit){}
    if(!limit)return false;
    REG32(DMA,0xcUL)=0xf40UL; /* all Stream5 status bits, including FE/DME */
    cursor.read=0;REG32(S5,8UL)=UART+4UL;REG32(S5,0xcUL)=(uint32_t)(uintptr_t)ring;
    REG32(S5,4UL)=256;REG32(S5,0x14UL)=0;
    REG32(S5,0UL)=(4UL<<25)|(1UL<<10)|(1UL<<8)|(1UL<<4)|(1UL<<3)|(1UL<<2)|(1UL<<1)|1UL;
    return true;
}
bool f407_uart_init(void){
    if((REG32(RCC,8UL)&((3UL<<2)|(15UL<<4)|(7UL<<10)|(7UL<<13)))!=0)return false;
    REG32(RCC,0x30UL)|=(1UL<<22)|1UL;REG32(RCC,0x44UL)|=1UL<<4;(void)REG32(RCC,0x44UL);
    REG32(0x40020000UL,0UL)=(REG32(0x40020000UL,0UL)&~(15UL<<18))|(10UL<<18);
    REG32(0x40020000UL,0x24UL)=(REG32(0x40020000UL,0x24UL)&~0xff0UL)|0x770UL;
    REG32(UART,0xcUL)=0;REG32(UART,0x10UL)=0;REG32(UART,8UL)=139;
    REG32(UART,0x14UL)=1UL<<6;
    REG32(UART,0xcUL)=(1UL<<13)|(1UL<<4)|(1UL<<3)|(1UL<<2);
    if(!dma_start())return false;
    ((volatile uint8_t *)0xe000e400UL)[37]=0x60;
    ((volatile uint8_t *)0xe000e400UL)[68]=0x60;
    REG32(0xe000e100UL,4UL)=1UL<<5;REG32(0xe000e100UL,8UL)=1UL<<4;
    return true;
}
static void receive(void){
    uint32_t flags=REG32(DMA,4UL), pos=(256U-REG32(S5,4UL))%256U;
    flags|=REG32(DMA,4UL);REG32(DMA,0xcUL)=flags&0xf40UL;
    unsigned events=f407_dma_events(flags);
    dma_span_t span=dma_consume(&cursor,pos,256,events);
    if(events&4U)restart_dma=true;
    if(span.dropped){byte_queue_loss(&queue);return;}
    for(uint32_t i=0;i<span.count;i++)if(!byte_queue_push(&queue,ring[(span.start+i)%256U]))break;
}
void DMA2_Stream5_IRQHandler(void){receive();}
void USART1_IRQHandler(void){
    uint32_t sr=REG32(UART,0UL);
    if(sr&0x1fU){(void)REG32(UART,4UL);if(sr&0xfU)byte_queue_loss(&queue);receive();}
}
bool f407_uart_read(uint8_t *b,bool *loss){
    uint32_t m=f407_lock();
    if(restart_dma){byte_queue_loss(&queue);restart_dma=!dma_start();}
    bool got=byte_queue_pop(&queue,b,loss);
    f407_unlock(m);return got;
}
size_t f407_uart_write(void *u,const uint8_t *p,size_t n){
    (void)u;size_t sent=0;
    while(sent<n&&(REG32(UART,0UL)&(1UL<<7)))REG32(UART,4UL)=p[sent++];
    return sent;
}
