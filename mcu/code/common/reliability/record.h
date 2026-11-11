#ifndef MCU_FAULT_RECORD_H
#define MCU_FAULT_RECORD_H
#include "protocol.h"
/* Byte layout avoids ABI padding and survives a same-image warm reset only. */
typedef struct { uint8_t bytes[12]; } fault_record_t;
void fault_record_save(volatile fault_record_t *, uint32_t);
bool fault_record_read(const volatile fault_record_t *, bool, uint32_t *);
bool fault_record_take(volatile fault_record_t *, bool, uint32_t *);
#endif
