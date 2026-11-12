/* 控制节拍编排（design §4 数据流；HAL 无关，主机可测）。
 * 每控制周期：取命令快照 → 编码器/估速 → 状态机/PI → 桥输出 → 遥测样本。
 * REVERSING 子阶段：RAMP_DOWN（原方向输出斜坡降至 0）→ WAIT_ZERO（撤销驱动，
 * 连续 abs(rpm)≤reverse_zero_rpm 且持续 reverse_hold_ms）→ RAMP_UP 换向。
 * 超时进 FAULT_REVERSAL_TIMEOUT；STOP/FAULT 随时抢占。
 */
#ifndef CONTROL_TICK_H
#define CONTROL_TICK_H

#include <stdint.h>
#include "control_types.h"
#include "motor_state.h"
#include "speed_estimator.h"
#include "pi_controller.h"
#include "command.h"
#include "telemetry.h"

typedef struct {
    motor_fsm_t       fsm;
    speed_estimator_t se;
    pi_controller_t   pi;
    control_params_t  params;
    cmd_lease_t       lease;

    float    target_rpm;        /* 用户最新目标（SET_RPM） */
    int16_t  target_duty;       /* 用户最新目标（SET_DUTY，开环） */
    bool     speed_mode;        /* RUN_SPEED vs RUN_OPEN */
    float    ramped_rpm;
    int16_t  cur_duty;
    uint32_t tick_ms;
    uint32_t sample_seq;
    uint32_t dropped;           /* 遥测丢帧计数（验收运行须为 0） */
    uint32_t last_fresh_cmd_ms; /* 租约时钟 */
} control_t;

void     control_init(control_t *c, const control_params_t *p, uint32_t cpr,
                       float max_abs_rpm, uint32_t max_dt_ms);
bool     control_apply_config(control_t *c, const control_params_t *p, uint32_t cpr);
bool     control_hello(control_t *c, uint32_t *new_session);
bool     control_command(control_t *c, const cmd_t *cmd, char *reply, uint32_t cap);
bool     control_tick(control_t *c, uint32_t now_ms, uint32_t enc_count,
                      uint32_t exec_us, tl_sample_t *sample);

#endif
