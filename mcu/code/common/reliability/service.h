#ifndef MCU_SERVICE_H
#define MCU_SERVICE_H
#include "transport.h"
typedef void (*fault_fn)(void *, uint8_t, uint8_t);
typedef struct {
    protocol_rx_t rx;
    protocol_tx_t tx;
    uint8_t platform, required, overdue, flags;
    bool health;
    uint32_t reset_reason;
    fault_fn fault;
    void *fault_user;
} device_service_t;
void device_service_init(device_service_t *, uint8_t, uint32_t, bool, fault_fn, void *);
void device_service_feed(device_service_t *, uint8_t, uint32_t);
bool device_service_query(const device_service_t *,const frame_t *,frame_t *,uint32_t);
#endif
