#ifndef MCU_TRANSPORT_H
#define MCU_TRANSPORT_H
#include "protocol.h"
typedef size_t (*tx_write_fn)(void *, const uint8_t *, size_t);
typedef struct {
    uint8_t wire[4][PROTOCOL_WIRE_MAX], length[4], head, count, offset;
    bool active, sync;
    uint32_t start_ms, dropped;
} protocol_tx_t;
void protocol_tx_init(protocol_tx_t *);
bool protocol_tx_enqueue(protocol_tx_t *, const frame_t *);
void protocol_tx_step(protocol_tx_t *, uint32_t, tx_write_fn, void *);
/* A bounded RX queue shared by ISR/task only under the platform's short lock.
 * On overflow discard the entire uncertain segment; loss is delivered before fresh bytes. */
typedef struct { uint8_t bytes[512]; uint16_t head, count; bool loss; uint32_t dropped; } byte_queue_t;
void byte_queue_loss(byte_queue_t *);
bool byte_queue_push(byte_queue_t *, uint8_t);
bool byte_queue_pop(byte_queue_t *, uint8_t *, bool *);
#endif
