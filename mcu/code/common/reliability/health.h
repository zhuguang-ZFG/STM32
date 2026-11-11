#ifndef MCU_HEALTH_H
#define MCU_HEALTH_H
#include <stdbool.h>
#include <stdint.h>
typedef struct {
    uint32_t required_mask, seen_mask, deadline_ms[8], last_ms[8], start_ms, grace_ms;
    bool valid, grace_active;
} health_t;
typedef struct { bool may_feed, in_grace, config_valid; uint32_t overdue_mask; } health_result_t;
typedef struct { bool restart_latched; uint32_t first_overdue; } health_supervisor_t;
bool health_init(health_t *, uint32_t, const uint32_t[8], uint32_t, uint32_t);
bool health_progress(health_t *, uint8_t, uint32_t);
health_result_t health_evaluate(health_t *, uint32_t);
bool health_supervise(health_supervisor_t *, health_result_t);
/* Caller serializes all accesses; this module owns no RTOS lock or hardware watchdog. */
#endif
