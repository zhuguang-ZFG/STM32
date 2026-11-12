/* 状态机（design §8，H05/H10）。
 * BOOT→DISABLED→ARMED→RUN_*→REVERSING；STOP→DISABLED；故障锁存→FAULT；CLEAR→DISABLED。
 * 事件优先级：硬件关断 > 软件故障 > STOP > 参数与运动指令。
 * 状态机只决定 bridge_output 与故障位；不直接触碰硬件。
 */
#ifndef MOTOR_STATE_H
#define MOTOR_STATE_H

#include <stdint.h>
#include <stdbool.h>
#include "control_types.h"

typedef struct {
    motor_state_t state;
    reversing_phase_t rev_phase;
    uint32_t fault_bits;        /* 锁存；首因=最低置位位 */
    uint32_t fault_first;       /* 首因 ID */
    uint32_t rev_timer_ms;      /* REVERSING 子阶段计时 */
    int16_t  last_duty;         /* 当前输出（千分数），用于 REVERSING 斜坡降 */
    float    last_target_rpm;   /* RUN_SPEED 目标；STOP/FAULT 清零 */
    bool     config_ok;         /* F06：CPR/参数已标定合法才允许 ARM */
    uint32_t lease_deadline_ms; /* F01：单调时钟口径，回绕由调用方处理 */
} motor_fsm_t;

typedef enum {
    EV_NONE = 0, EV_ARM, EV_SET, EV_STOP, EV_FAULT, EV_CLEAR, EV_TICK
} fsm_event_t;

void     fsm_init(motor_fsm_t *fsm);
void     fsm_set_config_ok(motor_fsm_t *fsm, bool ok);

/* 事件驱动。tick_ms=当前单调时间；rpm=当前滤波转速（FAULT 判定/停稳确认输入）。
 * has_command_lease=本周期收到过新鲜合法命令或心跳（F01）。
 * out=本周期桥输出（始终写入，停机为高阻 DISABLE）。
 * 返回 true=事件被接受（调用方据此 NACK/ACK）。 */
bool     fsm_event(motor_fsm_t *fsm, fsm_event_t ev, uint32_t tick_ms,
                   float rpm, bool has_command_lease, bridge_output_t *out);

uint32_t fsm_fault_count(uint32_t bits);
const char *fsm_state_name(motor_state_t s);

#endif
