#ifndef MCU_LOGGER_H
#define MCU_LOGGER_H
#include "../reliability/protocol.h"
enum { LOGGER_SLOTS=16, CONFIG_IMAGE_SIZE=128 };
typedef struct { uint16_t period_ms; uint8_t filter_shift; } logger_config_t;
typedef struct {
    logger_config_t config; uint32_t generation,saved_generation,sequence,dropped,sensor_errors,storage_errors;
    int32_t filtered[6]; uint8_t filter_valid,sensor_type,head,count,high_water;
    bool running; frame_t samples[LOGGER_SLOTS];
} logger_t;
bool logger_config_valid(logger_config_t);
void config_encode(uint8_t[CONFIG_IMAGE_SIZE],logger_config_t,uint32_t);
bool config_decode(const uint8_t[CONFIG_IMAGE_SIZE],logger_config_t *,uint32_t *);
bool generation_after(uint32_t,uint32_t);
void logger_init(logger_t *,uint8_t,const uint8_t *);
void logger_sample(logger_t *,const int32_t[6],uint8_t,uint32_t,uint32_t);
bool logger_pop(logger_t *,frame_t *);
bool logger_command(logger_t *,const frame_t *,frame_t *);
void logger_extend(const logger_t *,frame_t *);
typedef bool (*store_read_fn)(void *,uint16_t,uint8_t *,size_t);
typedef bool (*store_write_fn)(void *,uint16_t,const uint8_t *,size_t);
bool config_slots_load(store_read_fn,void *,uint8_t[CONFIG_IMAGE_SIZE]);
bool config_slots_save(store_read_fn,store_write_fn,void *,const uint8_t[CONFIG_IMAGE_SIZE]);
#endif
