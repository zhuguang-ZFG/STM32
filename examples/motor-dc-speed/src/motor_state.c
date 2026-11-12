#include "motor_state.h"

void fsm_init(motor_fsm_t *fsm)
{
    fsm->state = MS_BOOT;
    fsm->rev_phase = RS_NONE;
    fsm->fault_bits = 0;
    fsm->fault_first = 0;
    fsm->rev_timer_ms = 0;
    fsm->last_duty = 0;
    fsm->last_target_rpm = 0.f;
    fsm->config_ok = false;
    fsm->lease_deadline_ms = 0;
    fsm->state = MS_DISABLED;  /* BOOT 自检在 ARM 侧完成后进入；主机模型直接落位 */
}

void fsm_set_config_ok(motor_fsm_t *fsm, bool ok) { fsm->config_ok = ok; }

uint32_t fsm_fault_count(uint32_t bits) { return bits ? 1u : 0u; } /* 锁存位组 */

const char *fsm_state_name(motor_state_t s)
{
    switch (s) {
    case MS_BOOT: return "BOOT";
    case MS_DISABLED: return "DISABLED";
    case MS_ARMED: return "ARMED";
    case MS_RUN_OPEN: return "RUN_OPEN";
    case MS_RUN_SPEED: return "RUN_SPEED";
    case MS_REVERSING: return "REVERSING";
    case MS_FAULT: return "FAULT";
    }
    return "?";
}

static void enter_disabled(motor_fsm_t *fsm, bridge_output_t *out)
{
    fsm->state = MS_DISABLED;
    fsm->rev_phase = RS_NONE;
    fsm->last_duty = 0;
    fsm->last_target_rpm = 0.f;
    out->mode = BRIDGE_DISABLE;
    out->duty_permille = 0;
}

static void latch_fault(motor_fsm_t *fsm, uint32_t bit)
{
    if (!fsm->fault_bits) fsm->fault_first = bit;
    fsm->fault_bits |= bit;
    fsm->state = MS_FAULT;
    fsm->rev_phase = RS_NONE;
    fsm->last_duty = 0;
    fsm->last_target_rpm = 0.f;
}

bool fsm_event(motor_fsm_t *fsm, fsm_event_t ev, uint32_t tick_ms,
               float rpm, bool has_command_lease, bridge_output_t *out)
{
    (void)tick_ms;
    if (!fsm || !out) return false;
    out->mode = BRIDGE_DISABLE;
    out->duty_permille = 0;

    /* F01 租约检查：可运行态无新鲜命令 → 锁存故障（优先级最高的事件类） */
    if (state_is_running(fsm->state) && ev != EV_STOP && !has_command_lease) {
        latch_fault(fsm, FAULT_COMMAND_TIMEOUT);
    }

    switch (fsm->state) {
    case MS_FAULT:
        if (ev == EV_CLEAR && fsm->fault_bits == 0) { enter_disabled(fsm, out); return true; }
        if (ev == EV_CLEAR) { /* 先清位，需再次 CLEAR 且条件解除才回 DISABLED（design §8） */
            fsm->fault_bits = 0; fsm->fault_first = 0; return true;
        }
        return false; /* 故障不自动恢复；运动指令一律 NACK */

    case MS_DISABLED:
        if (ev == EV_ARM) {
            if (!fsm->config_ok) { latch_fault(fsm, FAULT_INVALID_CONFIG); return false; }
            fsm->state = MS_ARMED;
            return true;
        }
        return false;

    case MS_ARMED:
    case MS_RUN_OPEN:
    case MS_RUN_SPEED:
        if (ev == EV_STOP) { enter_disabled(fsm, out); return true; }
        if (ev == EV_FAULT) { latch_fault(fsm, fsm->fault_bits ? fsm->fault_bits : FAULT_FEEDBACK_INVALID); return true; }
        if (ev == EV_SET) {
            /* 方向反转判据由控制层比较目标符号；这里只处理 RUN 保持。
               反转协议由 control_tick 驱动 REVERSING 子阶段。 */
            return true;
        }
        return false;

    case MS_REVERSING:
        if (ev == EV_STOP) { enter_disabled(fsm, out); return true; }
        if (ev == EV_FAULT) { latch_fault(fsm, FAULT_FEEDBACK_INVALID); return true; }
        return false;

    case MS_BOOT:
        return false;
    }
    return false;
}
