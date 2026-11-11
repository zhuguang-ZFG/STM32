#ifndef MCU_PROTOCOL_H
#define MCU_PROTOCOL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
enum { PROTOCOL_PAYLOAD_MAX=64, PROTOCOL_RAW_MAX=72, PROTOCOL_ENCODED_MAX=73, PROTOCOL_WIRE_MAX=74 };
typedef struct { uint8_t type; uint16_t sequence, length; uint8_t payload[64]; } frame_t;
typedef enum { PROTO_OK, PROTO_COBS, PROTO_VERSION, PROTO_LENGTH, PROTO_CRC } protocol_error_t;
typedef enum { RX_EMPTY, RX_COLLECT, RX_DISCARD } rx_state_t;
typedef struct {
    uint32_t ok, cobs, version, length, crc, oversize, timeout, transport_loss;
} protocol_stats_t;
typedef struct {
    uint8_t encoded[PROTOCOL_ENCODED_MAX];
    size_t used;
    uint32_t timeout_ms, last_ms;
    rx_state_t state;
    protocol_stats_t stats;
    bool valid;
} protocol_rx_t;
uint16_t protocol_crc(const uint8_t *data, size_t length);
size_t protocol_cobs_encode(const uint8_t *src, size_t n, uint8_t *dst, size_t capacity);
size_t protocol_cobs_decode(const uint8_t *src, size_t n, uint8_t *dst, size_t capacity);
size_t protocol_encode(const frame_t *frame, uint8_t *wire, size_t capacity);
protocol_error_t protocol_decode(const uint8_t *encoded, size_t n, frame_t *frame);
bool protocol_rx_init(protocol_rx_t *rx, uint32_t timeout_ms);
void protocol_rx_poll(protocol_rx_t *rx, uint32_t now);
void protocol_rx_loss(protocol_rx_t *rx);
bool protocol_rx_feed(protocol_rx_t *rx, uint8_t byte, uint32_t now, frame_t *frame);
uint32_t protocol_errors(const protocol_stats_t *stats);
uint32_t sat_add(uint32_t a, uint32_t b);
uint16_t read_le16(const uint8_t *p);
uint32_t read_le32(const uint8_t *p);
void write_le16(uint8_t *p, uint16_t v);
void write_le32(uint8_t *p, uint32_t v);
#endif
