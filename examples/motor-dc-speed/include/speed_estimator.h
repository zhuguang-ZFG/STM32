/* 估速器（design §6，H02/H03）。
 * rpm_raw = 60 * delta_count / (CPR * dt_s)；一阶 IIR 滤波（alpha=1 即不过滤）。
 * 首次采样只建基线；dt=0/过大/超物理跳变/不可消歧回绕 → 反馈无效（不送 PI，F02）。
 */
#ifndef SPEED_ESTIMATOR_H
#define SPEED_ESTIMATOR_H

#include <stdint.h>
#include <stdbool.h>
#include "control_types.h"

typedef struct {
    uint32_t counts_per_output_rev; /* N=P×Q×G，标定后写入；0=未标定 */
    float    max_abs_rpm;           /* 物理上限，超限判无效 */
    uint32_t max_dt_ms;             /* dt 上限（漏周期判据） */
    float    alpha;                 /* 滤波系数 [0,1] */
    bool     baseline_valid;
    uint32_t prev_count;
    float    rpm_filtered;
} speed_estimator_t;

void  se_init(speed_estimator_t *se, uint32_t cpr, float max_abs_rpm, uint32_t max_dt_ms, float alpha);

/* 每控制周期调用。now=当前计数，t_ms=单调时钟（可回绕，由调用方保证 dt>0 语义）。
 * 返回 false=本周期反馈无效（reason 位可选记录）；有效时 *rpm_raw/*rpm_filt 输出。
 */
bool  se_update(speed_estimator_t *se, uint32_t now, uint32_t dt_ms,
                float *rpm_raw, float *rpm_filt);

/* 量化步进 q_rpm = 60/(CPR × T_s)：闭环最低转速须 ≥ 50×q_rpm（design §6 要求 q≤2%）。 */
float se_quantization_rpm(const speed_estimator_t *se, uint32_t nominal_period_ms);

void  se_reset(speed_estimator_t *se); /* 清基线与滤波历史；旧基线不可直接生成速度 */

#endif
