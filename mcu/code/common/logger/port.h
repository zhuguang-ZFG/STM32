#ifndef LOGGER_PORT_H
#define LOGGER_PORT_H
#include "logger.h"
#include "../reliability/record.h"
/* Platform adapter. All functions run in tasks except documented ADC/DMA IRQs. */
uint8_t logger_port_platform(void);
uint8_t logger_port_sensor(void);
uint32_t logger_port_reset(void);
uint32_t logger_port_previous_fault(bool *);
uint32_t logger_port_now(void);
bool logger_port_init(void);
bool logger_port_load(uint8_t[128]);
bool logger_port_save(const uint8_t[128]);
bool logger_port_sample(uint16_t,int32_t[6],uint8_t *,uint32_t *);
void logger_port_pause(bool);
bool logger_port_read(uint8_t *,bool *);
size_t logger_port_write(void *,const uint8_t *,size_t);
bool logger_port_watchdog_start(void);
void logger_port_watchdog_feed(void);
void logger_port_fault(uint32_t);
void logger_create_tasks(void);
#endif
