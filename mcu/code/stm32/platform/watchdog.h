#ifndef F407_WATCHDOG_H
#define F407_WATCHDOG_H
#include "uart.h"
/* HAL IWDG/WWDG v1.8.5 + CMSIS masks; timings below are nominal, not LSI bounds. */
static inline bool f407_iwdg_start(void){
    REG32(0x40003000UL,0UL)=0xcccc;
    REG32(0x40003000UL,0UL)=0x5555;
    REG32(0x40003000UL,4UL)=4; /* /64 */
    REG32(0x40003000UL,8UL)=999; /* 2s if LSI=32kHz */
    unsigned limit=1000000;while(REG32(0x40003000UL,0xcUL)&&--limit){}
    REG32(0x40003000UL,0UL)=0xaaaa;return limit!=0;
}
static inline void f407_iwdg_feed(void){REG32(0x40003000UL,0UL)=0xaaaa;}
static inline void f407_wwdg_start(void){
    REG32(RCC_BASE_F4,0x40UL)|=1UL<<11;
    REG32(0x40002c00UL,4UL)=(3UL<<7)|0x5f; /* PCLK1/(4096*8), window 0x5f */
    REG32(0x40002c00UL,0UL)=0xff;
}
static inline bool f407_wwdg_feed(void){
    uint32_t count=REG32(0x40002c00UL,0UL)&0x7f;
    if(count>0x3f && count<0x5f){REG32(0x40002c00UL,0UL)=0xff;return true;}
    return false; /* Do not refresh early just to keep the MCU alive. */
}
#endif
