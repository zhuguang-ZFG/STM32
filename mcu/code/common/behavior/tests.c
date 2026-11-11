#include <assert.h>
#include <stdint.h>
#include "capture.h"
#include "circular.h"
#include "../../stm32/platform/uart.h"
int main(void) {
    assert(f407_dma_events(0x400)==1 && f407_dma_events(0x800)==2 && f407_dma_events(0x200)==4);
    assert(f407_dma_events(0xc00)==3 && f407_dma_events(1UL<<29)==0);
    assert(RCC_RESET_OFFSET==0x74);
    capture_t c={0};
    capture_edge(&c,UINT32_MAX-499,false); assert(c.frequency==0);
    capture_edge(&c,500,false); assert(c.frequency==1000);
    capture_edge(&c,1500,true); assert(c.frequency==0 && c.lost==1);
    capture_edge(&c,2500,false); assert(c.frequency==0);
    capture_edge(&c,3500,false); assert(c.frequency==1000);
    capture_expire(&c,1003501); assert(!c.seen && c.frequency==0);
    capture_edge(&c,1003501,false); capture_edge(&c,1003501,false); assert(!c.frequency);
    capture_edge(&c,2003501,false); assert(!c.frequency);
    for(unsigned i=0;i<4;i++) assert(apb_div(i)==1);
    assert(apb_div(4)==2 && apb_div(7)==16);
    dma_cursor_t d={0};
    uint8_t ring[8]={0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48};
    dma_span_t p=dma_consume(&d,1,8,0); assert(p.start==0&&p.count==1&&ring[p.start]==0x41);
    p=dma_consume(&d,3,8,0); assert(p.start==1&&p.count==2);
    p=dma_consume(&d,4,8,1); assert(p.start==3&&p.count==1);
    p=dma_consume(&d,0,8,2); assert(p.start==4&&p.count==4);
    p=dma_consume(&d,0,8,0); assert(!p.count&&!p.dropped);
    p=dma_consume(&d,2,8,3); assert(p.dropped&&!p.count&&d.lost==1&&d.read==2);
    p=dma_consume(&d,3,8,0); assert(p.count==1&&p.start==2);
    /* Long stream: HT/TC consumption visits every slot once, in order. */
    d=(dma_cursor_t){0};
    unsigned expected=0;
    for(unsigned n=1;n<=100;n++) {
        unsigned pos=n%8, ev=pos==4?1:pos==0?2:0;
        p=dma_consume(&d,pos,8,ev);
        for(unsigned i=0;i<p.count;i++) assert((p.start+i)%8==expected++%8);
    }
    assert(expected==100&&!d.lost);
    p=dma_consume(&d,4,8,4); assert(p.dropped);
    return 0;
}
