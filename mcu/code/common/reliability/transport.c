#include "transport.h"
#include <string.h>
void protocol_tx_init(protocol_tx_t *q) { memset(q,0,sizeof(*q)); q->sync=true; }
bool protocol_tx_enqueue(protocol_tx_t *q, const frame_t *f)
{
    if (q->count==4) { q->dropped=sat_add(q->dropped,1); return false; }
    unsigned slot=(q->head+q->count)%4;
    size_t n=protocol_encode(f,q->wire[slot],PROTOCOL_WIRE_MAX);
    if (!n) { q->dropped=sat_add(q->dropped,1); return false; }
    q->length[slot]=(uint8_t)n; ++q->count;
    return true;
}
static void tx_pop(protocol_tx_t *q)
{
    q->head=(uint8_t)((q->head+1)%4); --q->count; q->offset=0; q->active=false;
}
void protocol_tx_step(protocol_tx_t *q, uint32_t now, tx_write_fn write, void *user)
{
    if (!q->count || !write) return;
    if (!q->active) { q->active=true; q->start_ms=now; }
    if ((uint32_t)(now-q->start_ms)>=100) {
        q->dropped=sat_add(q->dropped,1); tx_pop(q); q->sync=true; return;
    }
    if (q->sync) {
        const uint8_t zero=0;
        if (write(user,&zero,1)==1) q->sync=false;
        return;
    }
    size_t remain=q->length[q->head]-q->offset;
    size_t sent=write(user,q->wire[q->head]+q->offset,remain);
    /* Treat a broken transport contract as loss instead of walking out of bounds. */
    if (sent>remain) { q->dropped=sat_add(q->dropped,1); tx_pop(q); q->sync=true; return; }
    q->offset=(uint8_t)(q->offset+sent);
    if (q->offset==q->length[q->head]) tx_pop(q);
}
void byte_queue_loss(byte_queue_t *q)
{
    q->head=0; q->count=0; q->loss=true; q->dropped=sat_add(q->dropped,1);
}
bool byte_queue_push(byte_queue_t *q, uint8_t byte)
{
    if (q->count==sizeof(q->bytes)) { byte_queue_loss(q); return false; }
    q->bytes[(q->head+q->count)%sizeof(q->bytes)]=byte; ++q->count; return true;
}
bool byte_queue_pop(byte_queue_t *q, uint8_t *byte, bool *loss)
{
    *loss=q->loss; q->loss=false;
    if (!q->count) return false;
    *byte=q->bytes[q->head]; q->head=(uint16_t)((q->head+1)%sizeof(q->bytes)); --q->count;
    return true;
}
