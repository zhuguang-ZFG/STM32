/* 桥输出映射（design §5）。把 bridge_mode_t 映射为 TB6612 四路输入。
 * 官方真值表（TB6612FNG 2026-05-13 p.4）：
 *   DISABLE      = STBY=L                       → OFF（Standby 高阻+节电）
 *   DRIVE_*      = STBY=H, PWM=占空比, IN 按方向 → CW/CCW
 *   COAST        = STBY=H, IN1=L, IN2=L, PWM=H  → Stop（高阻）
 *   SHORT_BRAKE  = STBY=H, PWM=L, IN 保持        → Short brake（两输出 L）
 * V1 默认禁用 SHORT_BRAKE（显式选项，需专用指令与电源/热预算）。
 */
#ifndef MOTOR_BRIDGE_H
#define MOTOR_BRIDGE_H

#include <stdbool.h>
#include "control_types.h"

typedef struct {
    bool     stby;      /* 低有效：false=L（待机/默认停止） */
    bool     ain1;
    bool     ain2;
    uint16_t pwm_ccr;   /* 0..arr */
} bridge_pins_t;

/* duty_permille 限幅到 ±1000；mode=DRIVE_* 时符号决定 IN 对（与 mode 方向一致性由调用方保证）。 */
bool bridge_map(bridge_output_t out, uint16_t arr, bridge_pins_t *pins);

#endif
