#ifndef MCU_CIRCULAR_H
#define MCU_CIRCULAR_H
#include <stdint.h>
#include <stdbool.h>
/* Event bits are logical HT=1 TC=2 ERROR=4, not peripheral register bits.
 * Service before both boundaries accumulate. Uncertain data is discarded. */
typedef struct { uint32_t read, lost; } dma_cursor_t;
typedef struct { uint32_t start, count; bool dropped; } dma_span_t;
static inline dma_span_t dma_consume(dma_cursor_t *s, uint32_t position, uint32_t size, unsigned events)
{
    dma_span_t out = {s->read, 0, false};
    if (!size || position >= size || s->read >= size ||
        (events & 4U) || (events & 3U) == 3U ||
        (position == s->read && (events & 2U))) {
        s->lost++; s->read = size ? position % size : 0;
        out.dropped = true;
        return out;
    }
    out.count = (position + size - s->read) % size;
    s->read = position;
    return out;
}
#endif
