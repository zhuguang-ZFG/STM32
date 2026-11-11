#include "service.h"
/* Stable INFO/STATUS prefixes are shared by basic examples and the logger. */
bool device_service_query(const device_service_t *s,const frame_t *q,frame_t *r,uint32_t now){
    if(q->type!=1&&q->type!=2)return false;
    *r=(frame_t){.type=(uint8_t)(q->type|0x80),.sequence=q->sequence,.length=1};
    if(q->length){r->payload[0]=2;return true;}
    if(q->type==1){r->length=5;r->payload[1]=1;r->payload[2]=s->platform;write_le16(r->payload+3,(uint16_t)(1U|(s->health?2U:0U)|(s->fault?4U:0U)));}
    else{
        r->length=25;r->payload[1]=1;write_le32(r->payload+2,now);write_le32(r->payload+6,s->reset_reason);
        r->payload[10]=s->required;r->payload[11]=s->overdue;r->payload[12]=s->flags;
        write_le32(r->payload+13,s->rx.stats.ok);write_le32(r->payload+17,protocol_errors(&s->rx.stats));write_le32(r->payload+21,s->tx.dropped);
    }
    return true;
}
