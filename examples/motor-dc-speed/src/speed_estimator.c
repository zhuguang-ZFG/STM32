#include "speed_estimator.h"
#include "encoder.h"
#include <math.h>

void se_init(speed_estimator_t *se, uint32_t cpr, float max_abs_rpm,
             uint32_t max_dt_ms, float alpha)
{
    if (!se) return;
    se->counts_per_output_rev = cpr;
    se->max_abs_rpm = max_abs_rpm;
    se->max_dt_ms = max_dt_ms;
    se->alpha = (alpha < 0.f) ? 0.f : (alpha > 1.f) ? 1.f : alpha;
    se_reset(se);
}

void se_reset(speed_estimator_t *se)
{
    se->baseline_valid = false;
    se->prev_count = 0;
    se->rpm_filtered = 0.f;
}

float se_quantization_rpm(const speed_estimator_t *se, uint32_t nominal_period_ms)
{
    if (!se || se->counts_per_output_rev == 0u || nominal_period_ms == 0u) return 0.f;
    return 60.f / ((float)se->counts_per_output_rev * ((float)nominal_period_ms / 1000.f));
}

bool se_update(speed_estimator_t *se, uint32_t now, uint32_t dt_ms,
               float *rpm_raw, float *rpm_filt)
{
    if (!se || se->counts_per_output_rev == 0u) return false;
    if (dt_ms == 0u || dt_ms > se->max_dt_ms) { se->baseline_valid = false; return false; }

    if (!se->baseline_valid) {
        /* 首次采样仅建立基线（H02），不产生速度。 */
        se->prev_count = now;
        se->baseline_valid = true;
        se->rpm_filtered = 0.f;
        return false;
    }

    int32_t delta = 0;
    if (!enc_delta(now, se->prev_count, 16u, &delta)) {
        se->baseline_valid = false;   /* 不可消歧：废基线，下周期重建 */
        return false;
    }
    se->prev_count = now;

    const float dt_s = (float)dt_ms / 1000.f;
    const float raw = 60.f * (float)delta / ((float)se->counts_per_output_rev * dt_s);

    if (!isfinite(raw) || fabsf(raw) > se->max_abs_rpm) {
        return false;                 /* 异常跳变：反馈无效（F02），不送 PI */
    }

    se->rpm_filtered += se->alpha * (raw - se->rpm_filtered);
    if (rpm_raw)  *rpm_raw  = raw;
    if (rpm_filt) *rpm_filt = se->rpm_filtered;
    return true;
}
