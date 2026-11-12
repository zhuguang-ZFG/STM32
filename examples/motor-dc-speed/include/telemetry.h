/* 遥测帧 v1（design §9，H09；MC-104 冻结版）。
 * 字节序：全部小端。浮点不出帧——转速等以定点（0.1 rpm），占空比为千分数。
 * 帧布局（≤64 B）：
 *   [0]=0xAA [1]=0x55 [2]=ver(1) [3]=type [4:6]=len(LE, 含头不含 CRC)
 *   [6:10]=seq(LE u32) [10:14]=t_ms(LE u32) [14..14+payload)=payload [末]=CRC8
 * type 1=SAMPLE，payload 28 B：
 *   target_ramp(i16,0.1rpm) delta_count(i16) rpm_raw(i16,0.1rpm) rpm_filt(i16,0.1rpm)
 *   integral(i16,0.1%o) out_duty(i16,%o) state(u8) fault(u8) flags(u8)
 *   exec_us(u16) dropped(u8) pad(u8)
 */
#ifndef MOTOR_TELEMETRY_H
#define MOTOR_TELEMETRY_H

#include <stdint.h>
#include <stdbool.h>

#define TL_MAGIC0      0xAAu
#define TL_MAGIC1      0x55u
#define TL_VERSION     1u
#define TL_FRAME_MAX   64u
#define TL_TYPE_SAMPLE 1u
#define TL_SAMPLE_PAYLOAD 28u
#define TL_SAMPLE_FRAME   (14u + TL_SAMPLE_PAYLOAD + 1u)   /* =43 */

typedef struct {
    int16_t  target_ramp;   /* 0.1 rpm */
    int16_t  delta_count;
    int16_t  rpm_raw;       /* 0.1 rpm */
    int16_t  rpm_filt;      /* 0.1 rpm */
    int16_t  integral;      /* 0.1 ‰ */
    int16_t  out_duty;      /* ‰ */
    uint8_t  state;
    uint8_t  fault;
    uint8_t  flags;         /* bit0=饱和高 bit1=饱和低 bit2=反馈无效 bit3=丢样 */
    uint16_t exec_us;
    uint8_t  dropped;
} tl_sample_t;

uint8_t tl_crc8(const uint8_t *data, uint32_t len);  /* poly 0x07, init 0x00 */

uint32_t tl_pack_sample(uint8_t *buf, uint32_t cap, uint32_t seq, uint32_t t_ms,
                        const tl_sample_t *s);

/* 解包：校验魔数/版本/长度/CRC。返回 payload 长度；失败返回 0。 */
uint32_t tl_unpack(const uint8_t *buf, uint32_t len, uint8_t *type,
                   uint32_t *seq, uint32_t *t_ms, const uint8_t **payload);

#endif
