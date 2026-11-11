#include "protocol.h"
#include <string.h>
_Static_assert(PROTOCOL_RAW_MAX == 6+PROTOCOL_PAYLOAD_MAX+2, "wire layout");
_Static_assert(PROTOCOL_WIRE_MAX == PROTOCOL_RAW_MAX+2, "COBS overhead for raw <254");
uint32_t sat_add(uint32_t a, uint32_t b) { return UINT32_MAX-a < b ? UINT32_MAX : a+b; }
uint16_t read_le16(const uint8_t *p) { return (uint16_t)((uint16_t)p[0] | (uint16_t)p[1]<<8); }
uint32_t read_le32(const uint8_t *p) { return (uint32_t)read_le16(p) | (uint32_t)read_le16(p+2)<<16; }
void write_le16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); }
void write_le32(uint8_t *p, uint32_t v) { write_le16(p,(uint16_t)v); write_le16(p+2,(uint16_t)(v>>16)); }
uint16_t protocol_crc(const uint8_t *data, size_t n)
{
    uint16_t crc=0xffffU;
    for (size_t i=0;i<n;i++) {
        crc ^= (uint16_t)((uint16_t)data[i]<<8);
        for (unsigned bit=0;bit<8;bit++)
            crc=(uint16_t)((crc&0x8000U) ? ((uint32_t)crc<<1)^0x1021U : (uint32_t)crc<<1);
    }
    return crc;
}
/* This bounded COBS codec intentionally accepts only this protocol's <=72 raw bytes. */
size_t protocol_cobs_encode(const uint8_t *src, size_t n, uint8_t *dst, size_t capacity)
{
    if ((!src && n) || !dst || n>PROTOCOL_RAW_MAX || capacity<n+1) return 0;
    size_t code_at=0, out=1; uint8_t code=1;
    for (size_t i=0;i<n;i++) {
        if (src[i]==0) { dst[code_at]=code; code_at=out++; code=1; }
        else { dst[out++]=src[i]; ++code; }
    }
    dst[code_at]=code;
    return out;
}
size_t protocol_cobs_decode(const uint8_t *src, size_t n, uint8_t *dst, size_t capacity)
{
    if (!src || !dst || !n || n>PROTOCOL_ENCODED_MAX) return 0;
    size_t in=0, out=0;
    while (in<n) {
        uint8_t code=src[in++];
        if (!code || (size_t)(code-1)>n-in) return 0;
        for (unsigned j=1;j<code;j++) {
            if (!src[in] || out==capacity) return 0;
            dst[out++]=src[in++];
        }
        if (code!=255U && in<n) {
            if (out==capacity) return 0;
            dst[out++]=0;
        }
    }
    return out;
}
size_t protocol_encode(const frame_t *f, uint8_t *wire, size_t capacity)
{
    if (!f || !wire || f->length>64 || capacity<(size_t)f->length+10) return 0;
    uint8_t raw[PROTOCOL_RAW_MAX];
    raw[0]=1; raw[1]=f->type; write_le16(raw+2,f->sequence); write_le16(raw+4,f->length);
    memcpy(raw+6,f->payload,f->length);
    write_le16(raw+6+f->length,protocol_crc(raw,6+f->length));
    size_t n=protocol_cobs_encode(raw,8+f->length,wire,capacity-1);
    wire[n]=0;
    return n+1;
}
protocol_error_t protocol_decode(const uint8_t *encoded, size_t n, frame_t *f)
{
    uint8_t raw[PROTOCOL_RAW_MAX];
    if (!f) return PROTO_LENGTH;
    size_t count=protocol_cobs_decode(encoded,n,raw,sizeof(raw));
    if (!count) return PROTO_COBS;
    if (count<8) return PROTO_LENGTH;
    if (raw[0]!=1) return PROTO_VERSION;
    uint16_t length=read_le16(raw+4);
    if (length>64 || count!=(size_t)length+8) return PROTO_LENGTH;
    if (read_le16(raw+6+length)!=protocol_crc(raw,6+length)) return PROTO_CRC;
    /* Publish only after every check. A rejected frame leaves the caller's output untouched. */
    f->type=raw[1]; f->sequence=read_le16(raw+2); f->length=length;
    memcpy(f->payload,raw+6,length);
    return PROTO_OK;
}
bool protocol_rx_init(protocol_rx_t *rx, uint32_t timeout_ms)
{
    if (!rx) return false;
    memset(rx,0,sizeof(*rx));
    rx->valid=timeout_ms>0 && timeout_ms<0x80000000UL;
    rx->timeout_ms=timeout_ms;
    return rx->valid;
}
void protocol_rx_poll(protocol_rx_t *rx, uint32_t now)
{
    if (rx && rx->valid && rx->state==RX_COLLECT && (uint32_t)(now-rx->last_ms)>=rx->timeout_ms) {
        rx->state=RX_DISCARD; rx->used=0; rx->stats.timeout=sat_add(rx->stats.timeout,1);
    }
}
void protocol_rx_loss(protocol_rx_t *rx)
{
    if (!rx || !rx->valid) return;
    rx->state=RX_DISCARD; rx->used=0;
    rx->stats.transport_loss=sat_add(rx->stats.transport_loss,1);
}
bool protocol_rx_feed(protocol_rx_t *rx, uint8_t byte, uint32_t now, frame_t *f)
{
    if (!rx || !rx->valid || !f) return false;
    protocol_rx_poll(rx,now);
    if (byte==0) {
        bool ready=false;
        if (rx->state==RX_COLLECT) {
            protocol_error_t err=protocol_decode(rx->encoded,rx->used,f);
            uint32_t *count=&rx->stats.ok;
            switch (err) {
            case PROTO_COBS: count=&rx->stats.cobs; break;
            case PROTO_VERSION: count=&rx->stats.version; break;
            case PROTO_LENGTH: count=&rx->stats.length; break;
            case PROTO_CRC: count=&rx->stats.crc; break;
            case PROTO_OK: ready=true; break;
            }
            *count=sat_add(*count,1);
        }
        rx->state=RX_EMPTY; rx->used=0;
        return ready;
    }
    if (rx->state==RX_DISCARD) return false;
    if (rx->used==sizeof(rx->encoded)) {
        rx->state=RX_DISCARD; rx->used=0; rx->stats.oversize=sat_add(rx->stats.oversize,1);
        return false;
    }
    rx->state=RX_COLLECT; rx->last_ms=now; rx->encoded[rx->used++]=byte;
    return false;
}
uint32_t protocol_errors(const protocol_stats_t *s)
{
    uint32_t sum=0;
    const uint32_t values[]={s->cobs,s->version,s->length,s->crc,s->oversize,s->timeout,s->transport_loss};
    for (size_t i=0;i<sizeof(values)/sizeof(values[0]);i++) sum=sat_add(sum,values[i]);
    return sum;
}
