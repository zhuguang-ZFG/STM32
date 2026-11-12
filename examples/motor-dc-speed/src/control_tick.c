#include "control_tick.h"
#include <string.h>
#include <stdio.h>
#include <math.h>

void control_init(control_t *c, const control_params_t *p, uint32_t cpr,
                  float max_abs_rpm, uint32_t max_dt_ms)
{
    memset(c, 0, sizeof(*c));
    fsm_init(&c->fsm);
    se_init(&c->se, cpr, max_abs_rpm, max_dt_ms, p ? p->alpha : 1.f);
    pi_init(&c->pi, p ? p->kp : 0.f, p ? p->ki : 0.f, p ? p->i_limit : 0.f,
            p ? p->duty_limit : 0.f);
    if (p) c->params = *p;
    cmd_lease_init(&c->lease);
    c->se.alpha = p ? p->alpha : 1.f;
    fsm_set_config_ok(&c->fsm, cpr != 0u && params_valid(p));
}

bool control_apply_config(control_t *c, const control_params_t *p, uint32_t cpr)
{
    if (c->fsm.state != MS_DISABLED) return false;      /* 仅 DISABLED 可改参数 */
    if (!params_valid(p) || cpr == 0u) return false;
    c->params = *p;
    se_init(&c->se, cpr, p->rpm_max * 1.25f + 1.f, 50u /*max_dt_ms 由板层给*/, p->alpha);
    pi_init(&c->pi, p->kp, p->ki, p->i_limit, p->duty_limit);
    fsm_set_config_ok(&c->fsm, true);
    return true;
}

bool control_hello(control_t *c, uint32_t *new_session)
{
    uint32_t s = cmd_lease_open(&c->lease);
    if (new_session) *new_session = s;
    return true;
}

bool control_command(control_t *c, const cmd_t *cmd, char *reply, uint32_t cap)
{
    if (!c || !cmd) return false;
    const char *ok = "+OK", *nack = "-NACK";

    switch (cmd->type) {
    case CMD_HELLO: {
        uint32_t s; control_hello(c, &s);
        if (reply && cap > 12) snprintf(reply, cap, "+OK %08lx", (unsigned long)s);
        return true;
    }
    case CMD_STOP:
        fsm_event(&c->fsm, EV_STOP, c->tick_ms, 0.f, true, &(bridge_output_t){0});
        pi_reset(&c->pi);
        c->target_rpm = 0.f; c->target_duty = 0; c->ramped_rpm = 0.f; c->cur_duty = 0;
        if (reply && cap > 4) memcpy(reply, ok, 4);
        return true;
    case CMD_CLEAR:
        fsm_event(&c->fsm, EV_CLEAR, c->tick_ms, 0.f, true, &(bridge_output_t){0});
        if (reply && cap > 4) memcpy(reply, ok, 4);
        return true;
    case CMD_ARM: {
        bridge_output_t out;
        bool acc = fsm_event(&c->fsm, EV_ARM, c->tick_ms, 0.f, true, &out);
        if (reply && cap > 6) memcpy(reply, acc ? ok : nack, acc ? 4 : 5);
        return acc;
    }
    case CMD_SET_DUTY:
        if (c->fsm.state != MS_ARMED && c->fsm.state != MS_RUN_OPEN) {
            if (reply && cap > 6) memcpy(reply, nack, 5);
            return false;
        }
        c->speed_mode = false;
        c->target_duty = (int16_t)cmd->arg_int;
        if (c->fsm.state == MS_ARMED) c->fsm.state = MS_RUN_OPEN;
        if (reply && cap > 4) memcpy(reply, ok, 4);
        return true;
    case CMD_SET_RPM:
        if (c->fsm.state != MS_ARMED && c->fsm.state != MS_RUN_SPEED) {
            if (reply && cap > 6) memcpy(reply, nack, 5);
            return false;
        }
        if (fabsf((float)cmd->arg_int) > c->params.target_limit_rpm) {
            if (reply && cap > 6) memcpy(reply, nack, 5);
            return false;
        }
        c->speed_mode = true;
        c->target_rpm = (float)cmd->arg_int;
        if (c->fsm.state == MS_ARMED) c->fsm.state = MS_RUN_SPEED;
        if (reply && cap > 4) memcpy(reply, ok, 4);
        return true;
    case CMD_CONFIG: {
        /* 语法已解析为 k=v 字符串；数值解析留给主机/板层（P1 薄切片：透传记录） */
        if (c->fsm.state != MS_DISABLED) { if (reply && cap > 6) memcpy(reply, nack, 5); return false; }
        if (reply && cap > 4) memcpy(reply, ok, 4);
        return true;
    }
    case CMD_STATUS:
    case CMD_HEARTBEAT:
        if (reply && cap > 4) memcpy(reply, ok, 4);
        return true;
    default:
        if (reply && cap > 6) memcpy(reply, nack, 5);
        return false;
    }
}

bool control_tick(control_t *c, uint32_t now_ms, uint32_t enc_count,
                  uint32_t exec_us, tl_sample_t *sample)
{
    if (!c) return false;
    const uint32_t dt_ms = (c->tick_ms == 0u) ? 10u : (now_ms - c->tick_ms);
    c->tick_ms = now_ms;

    float rpm_raw = 0.f, rpm_filt = 0.f;
    bool fb_ok = se_update(&c->se, enc_count, dt_ms, &rpm_raw, &rpm_filt);

    /* 租约新鲜度（F01）：由命令层在收到合法命令时刷新 last_fresh_cmd_ms */
    const bool lease_fresh = (now_ms - c->last_fresh_cmd_ms) <= c->params.command_lease_ms;

    bridge_output_t out = { BRIDGE_DISABLE, 0 };
    int16_t duty = 0;
    bool feedback_invalid = false;

    switch (c->fsm.state) {
    case MS_RUN_OPEN:
        duty = c->target_duty;
        break;
    case MS_RUN_SPEED: {
        /* 反转检测 → 进入 REVERSING */
        const float e_sign = (c->target_rpm >= 0.f) ? 1.f : -1.f;
        const float cur_sign = (rpm_filt >= 0.f) ? 1.f : -1.f;
        if (fabsf(c->target_rpm) > 0.f && fabsf(rpm_filt) > c->params.reverse_zero_rpm &&
            e_sign != cur_sign) {
            c->fsm.state = MS_REVERSING;
            c->fsm.rev_phase = RS_RAMP_DOWN;
            c->fsm.rev_timer_ms = now_ms;
        } else {
            c->ramped_rpm = ramp_target(c->target_rpm, c->ramped_rpm,
                                        c->params.ramp_rpm_per_s, (float)dt_ms / 1000.f);
            if (fb_ok) {
                int dir = (c->ramped_rpm >= 0.f) ? 1 : -1;
                float u = 0.f;
                pi_update(&c->pi, fabsf(c->ramped_rpm), fabsf(rpm_filt),
                          (float)dt_ms / 1000.f, dir, &u);
                duty = (int16_t)u;
            } else {
                feedback_invalid = true;
            }
        }
        break;
    }
    case MS_REVERSING: {
        const uint32_t el = now_ms - c->fsm.rev_timer_ms;
        if (el > c->params.reverse_timeout_ms) {
            c->fsm.fault_bits |= FAULT_REVERSAL_TIMEOUT;
            c->fsm.fault_first = FAULT_REVERSAL_TIMEOUT;
            c->fsm.state = MS_FAULT;
            break;
        }
        switch (c->fsm.rev_phase) {
        case RS_RAMP_DOWN: {
            /* 保持原方向输出斜坡降至 0（简化线性：每周期降 50‰） */
            int16_t d = c->cur_duty;
            const int16_t step = 50;
            if (d > step) d = (int16_t)(d - step);
            else if (d < -step) d = (int16_t)(d + step);
            else d = 0;
            duty = d;
            c->cur_duty = d;
            if (d == 0) { c->fsm.rev_phase = RS_WAIT_ZERO; }
            break;
        }
        case RS_WAIT_ZERO:
            duty = 0;   /* 撤销驱动 */
            if (fabsf(rpm_filt) <= c->params.reverse_zero_rpm) {
                c->fsm.rev_phase = RS_HOLD;
                c->fsm.rev_timer_ms = now_ms;
            }
            break;
        case RS_HOLD:
            duty = 0;
            if (now_ms - c->fsm.rev_timer_ms >= c->params.reverse_hold_ms) {
                c->ramped_rpm = 0.f;
                pi_reset(&c->pi);
                c->fsm.rev_phase = RS_RAMP_UP;
                c->fsm.state = MS_RUN_SPEED;   /* 换向完成，从零升速 */
                c->fsm.rev_phase = RS_NONE;
            }
            break;
        default: break;
        }
        break;
    }
    default: break;
    }

    /* F01：可运行态租约失效 → 锁存并停机 */
    if (state_is_running(c->fsm.state) && !lease_fresh) {
        c->fsm.fault_bits |= FAULT_COMMAND_TIMEOUT;
        if (!c->fsm.fault_first) c->fsm.fault_first = FAULT_COMMAND_TIMEOUT;
        c->fsm.state = MS_FAULT;
    }
    if (feedback_invalid && c->fsm.state == MS_RUN_SPEED) {
        /* 失效速度不送 PI；持续由 F02/F03 策略处理（P3 细化窗口） */
    }

    /* 桥输出 */
    if (c->fsm.state == MS_FAULT || c->fsm.state == MS_DISABLED || c->fsm.state == MS_ARMED) {
        out.mode = BRIDGE_DISABLE; out.duty_permille = 0;
    } else if (c->fsm.rev_phase == RS_WAIT_ZERO || c->fsm.rev_phase == RS_HOLD) {
        out.mode = BRIDGE_DISABLE; out.duty_permille = 0;   /* 停稳期撤销驱动 */
    } else {
        out.duty_permille = duty;
        out.mode = (duty >= 0) ? BRIDGE_DRIVE_FORWARD : BRIDGE_DRIVE_REVERSE;
        if (duty == 0 && c->fsm.state == MS_RUN_OPEN) out.mode = BRIDGE_DISABLE;
    }
    c->cur_duty = duty;

    if (sample) {
        memset(sample, 0, sizeof(*sample));
        sample->target_ramp = (int16_t)(c->ramped_rpm * 10.f);
        sample->rpm_raw = (int16_t)(rpm_raw * 10.f);
        sample->rpm_filt = (int16_t)(rpm_filt * 10.f);
        sample->integral = (int16_t)(c->pi.integral * 10.f);
        sample->out_duty = duty;
        sample->state = (uint8_t)c->fsm.state;
        sample->fault = (uint8_t)(c->fsm.fault_bits & 0xFFu);
        sample->flags = (uint8_t)((c->pi.saturated_high ? 1u : 0u) |
                                  (c->pi.saturated_low ? 2u : 0u) |
                                  (feedback_invalid ? 4u : 0u));
        sample->exec_us = (uint16_t)(exec_us > 65535u ? 65535u : exec_us);
        sample->dropped = 0;
    }
    c->sample_seq++;
    return true;
}
