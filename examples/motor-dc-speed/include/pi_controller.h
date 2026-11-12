/* PI（design §7，H04/H06）。浮点；误差 rpm，输出归一化占空比。
 * 条件积分：不饱和→接受 I_try；触及方向区间上界且 e<0、或下界且 e>0→允许朝脱离方向；
 * 其余冻结。积分自身有限界。抗饱和使用最终执行区间（含零端约束）。
 */
#ifndef PI_CONTROLLER_H
#define PI_CONTROLLER_H

#include <stdbool.h>
#include "control_types.h"

typedef struct {
    float kp, ki, i_limit, duty_limit;  /* duty_limit<1000 */
    float integral;
    float u;                            /* 上次输出（限幅后） */
    bool  saturated_high, saturated_low;
} pi_controller_t;

bool pi_init(pi_controller_t *pi, float kp, float ki, float i_limit, float duty_limit);
void pi_reset(pi_controller_t *pi);   /* 清积分与限幅记忆；STOP/FAULT/切换时调用 */

/* dir: +1 输出区间 [0,+duty_limit]；-1 区间 [-duty_limit,0]；其余返回 false。
 * dt_s>0 且有限。超调产生反号请求时执行零输出（释放策略），不反向驱动。 */
bool pi_update(pi_controller_t *pi, float target_rpm, float measured_rpm,
               float dt_s, int dir, float *out_duty);

/* 目标斜坡：每步变化有界（H06）。step 返回本步斜坡目标。 */
float ramp_target(float target, float current, float ramp_rpm_per_s, float dt_s);

bool params_valid(const control_params_t *p); /* NaN/Inf/范围校验（H06） */

#endif
