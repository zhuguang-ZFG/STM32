#include "pi_controller.h"
#include <math.h>

static bool finite4(float a, float b, float c, float d) {
    return isfinite(a) && isfinite(b) && isfinite(c) && isfinite(d);
}

bool params_valid(const control_params_t *p)
{
    if (!p) return false;
    if (!finite4(p->kp, p->ki, p->i_limit, p->duty_limit)) return false;
    if (!isfinite(p->ramp_rpm_per_s) || !isfinite(p->alpha)) return false;
    if (p->duty_limit < 0.f || p->duty_limit >= 1000.f) return false;
    if (p->i_limit < 0.f) return false;
    if (p->alpha < 0.f || p->alpha > 1.f) return false;
    if (p->ramp_rpm_per_s < 0.f) return false;
    if (!(p->rpm_min < p->rpm_max)) return false;
    return true;
}

bool pi_init(pi_controller_t *pi, float kp, float ki, float i_limit, float duty_limit)
{
    if (!pi) return false;
    if (!finite4(kp, ki, i_limit, duty_limit)) return false;
    if (duty_limit < 0.f || duty_limit >= 1000.f || i_limit < 0.f) return false;
    pi->kp = kp; pi->ki = ki; pi->i_limit = i_limit; pi->duty_limit = duty_limit;
    pi_reset(pi);
    return true;
}

void pi_reset(pi_controller_t *pi)
{
    pi->integral = 0.f;
    pi->u = 0.f;
    pi->saturated_high = pi->saturated_low = false;
}

float ramp_target(float target, float current, float ramp_rpm_per_s, float dt_s)
{
    if (!isfinite(target) || !isfinite(current) || !isfinite(ramp_rpm_per_s) || !(dt_s > 0.f))
        return current;
    const float step = ramp_rpm_per_s * dt_s;
    if (target > current) return (target - current <= step) ? target : current + step;
    if (target < current) return (current - target <= step) ? target : current - step;
    return target;
}

bool pi_update(pi_controller_t *pi, float target_rpm, float measured_rpm,
               float dt_s, int dir, float *out_duty)
{
    if (!pi || !out_duty) return false;
    if (!(dir == 1 || dir == -1)) return false;
    if (!isfinite(target_rpm) || !isfinite(measured_rpm) || !(dt_s > 0.f) || !isfinite(dt_s)) {
        return false;  /* 非法输入：无副作用，不刷新输出 */
    }

    const float e = target_rpm - measured_rpm;
    float i_try = pi->integral + pi->ki * e * dt_s;

    /* 积分自身限界 */
    if (i_try >  pi->i_limit) i_try =  pi->i_limit;
    if (i_try < -pi->i_limit) i_try = -pi->i_limit;

    float u_try = pi->kp * e + i_try;

    /* 方向区间 [lo,hi]：含零端约束 */
    const float hi = (dir > 0) ? pi->duty_limit : 0.f;
    const float lo = (dir > 0) ? 0.f : -pi->duty_limit;

    /* 超调反号 → 零输出释放策略，不反向驱动 */
    if (dir > 0 && u_try < 0.f) u_try = 0.f;
    if (dir < 0 && u_try > 0.f) u_try = 0.f;

    float u = u_try;
    bool sat_h = false, sat_l = false;
    if (u > hi) { u = hi; sat_h = true; }
    if (u < lo) { u = lo; sat_l = true; }

    /* 条件积分（design §7） */
    bool accept = false;
    if (!sat_h && !sat_l) {
        accept = true;
    } else if (sat_h && e < 0.f) {
        accept = true;   /* 上界饱和且误差要求下降：允许朝脱离方向积分 */
    } else if (sat_l && e > 0.f) {
        accept = true;
    }
    if (accept) pi->integral = i_try;

    pi->u = u;
    pi->saturated_high = sat_h;
    pi->saturated_low = sat_l;
    *out_duty = u;
    return true;
}
