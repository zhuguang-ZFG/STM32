#include "telemetry.h"
#include <string.h>

uint8_t tl_crc8(const uint8_t *d, uint32_t n)
{
    uint8_t crc = 0x00;
    for (uint32_t i = 0; i < n; i++) {
        crc ^= d[i];
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
    }
    return crc;
}

static void put_u16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put_u32(uint8_t *p, uint32_t v) { put_u16(p, (uint16_t)v); put_u16(p + 2, (uint16_t)(v >> 16)); }
static uint16_t get_u16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static uint32_t get_u32(const uint8_t *p) { return (uint32_t)get_u16(p) | ((uint32_t)get_u16(p + 2) << 16); }

uint32_t tl_pack_sample(uint8_t *buf, uint32_t cap, uint32_t seq, uint32_t t_ms,
                        const tl_sample_t *s)
{
    if (!buf || !s || cap < TL_SAMPLE_FRAME) return 0;
    const uint16_t len_field = (uint16_t)(14u + TL_SAMPLE_PAYLOAD);
    buf[0] = TL_MAGIC0; buf[1] = TL_MAGIC1; buf[2] = TL_VERSION; buf[3] = TL_TYPE_SAMPLE;
    put_u16(buf + 4, len_field);
    put_u32(buf + 6, seq);
    put_u32(buf + 10, t_ms);
    uint8_t *p = buf + 14;
    put_u16(p + 0,  (uint16_t)s->target_ramp);
    put_u16(p + 2,  (uint16_t)s->delta_count);
    put_u16(p + 4,  (uint16_t)s->rpm_raw);
    put_u16(p + 6,  (uint16_t)s->rpm_filt);
    put_u16(p + 8,  (uint16_t)s->integral);
    put_u16(p + 10, (uint16_t)s->out_duty);
    p[12] = s->state; p[13] = s->fault; p[14] = s->flags;
    put_u16(p + 15, s->exec_us);
    p[17] = s->dropped;
    p[18] = 0;  /* pad */
    p[19] = 0;  /* pad: payload=28 → 20..27? 见下 */
    /* payload 实为 28 B：20B 已定，补 8B 保留为 0（版本 1 不用，但帧长固定） */
    memset(p + 20, 0, 8);
    buf[14 + TL_SAMPLE_PAYLOAD] = tl_crc8(buf, 14 + TL_SAMPLE_PAYLOAD);
    return TL_SAMPLE_FRAME;
}

uint32_t tl_unpack(const uint8_t *buf, uint32_t len, uint8_t *type,
                   uint32_t *seq, uint32_t *t_ms, const uint8_t **payload)
{
    if (!buf || len < 15) return 0;
    if (buf[0] != TL_MAGIC0 || buf[1] != TL_MAGIC1 || buf[2] != TL_VERSION) return 0;
    const uint16_t len_field = get_u16(buf + 4);
    if (len_field < 15 || len_field > TL_FRAME_MAX - 1 || len < (uint32_t)len_field + 1) return 0;
    if (tl_crc8(buf, len_field) != buf[len_field]) return 0;
    if (type) *type = buf[3];
    if (seq) *seq = get_u32(buf + 6);
    if (t_ms) *t_ms = get_u32(buf + 10);
    if (payload) *payload = buf + 14;
    return (uint32_t)len_field - 14u;
}
