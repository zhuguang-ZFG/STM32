#ifndef MCU_CAPTURE_H
#define MCU_CAPTURE_H
#include <stdint.h>
#include <stdbool.h>
typedef struct { uint32_t previous, frequency, lost; bool seen; } capture_t;
/* 32-bit free-running 1MHz counter, accepted periods 100us..500ms. */
static inline void capture_edge(capture_t *s, uint32_t now, bool overcapture)
{
    uint32_t delta = now - s->previous;
    s->frequency = 0;
    if (overcapture) { s->lost++; s->seen = false; return; }
    if (s->seen && delta >= 100U && delta <= 500000U) s->frequency = 1000000U / delta;
    s->previous = now; s->seen = true;
}
static inline void capture_expire(capture_t *s, uint32_t now)
{
    if (s->seen && now - s->previous > 1000000U) { s->seen=false; s->frequency=0; }
}
static inline uint32_t apb_div(uint32_t field) {
    static const uint8_t divs[8] = {1,1,1,1,2,4,8,16};
    return divs[field & 7U];
}
#endif
