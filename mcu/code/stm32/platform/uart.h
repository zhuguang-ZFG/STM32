#ifndef F407_UART_H
#define F407_UART_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "../../common/reliability/transport.h"
#define REG32(b,o) (*(volatile uint32_t *)((b)+(o)))
#define RCC_BASE_F4 0x40023800UL
#define DMA5_TE (1UL<<9)
#define DMA5_HT (1UL<<10)
#define DMA5_TC (1UL<<11)
#define RCC_RESET_OFFSET 0x74UL
static inline unsigned f407_dma_events(uint32_t flags){return ((flags&DMA5_HT)?1U:0U)|((flags&DMA5_TC)?2U:0U)|((flags&(DMA5_TE|(1UL<<8)|(1UL<<6)))?4U:0U);}
bool f407_uart_init(void);
bool f407_uart_read(uint8_t *,bool *);
size_t f407_uart_write(void *,const uint8_t *,size_t);
uint32_t f407_reset_reason(void);
uint32_t f407_lock(void);
void f407_unlock(uint32_t);
#endif
