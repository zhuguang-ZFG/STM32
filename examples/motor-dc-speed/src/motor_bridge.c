#include "motor_bridge.h"

bool bridge_map(bridge_output_t out, uint16_t arr, bridge_pins_t *pins)
{
    if (!pins) return false;

    int16_t d = out.duty_permille;
    if (d > 1000) d = 1000;
    if (d < -1000) d = -1000;

    switch (out.mode) {
    case BRIDGE_DISABLE:
        pins->stby = false; pins->ain1 = false; pins->ain2 = false; pins->pwm_ccr = 0;
        return true;
    case BRIDGE_COAST:
        pins->stby = true; pins->ain1 = false; pins->ain2 = false; pins->pwm_ccr = arr;
        return true;
    case BRIDGE_SHORT_BRAKE:
        pins->stby = true; pins->pwm_ccr = 0;
        pins->ain1 = true; pins->ain2 = true;   /* 方向保持语义由上层给；制动时 IN 对不影响 OUT=L */
        return true;
    case BRIDGE_DRIVE_FORWARD:
        pins->stby = true;
        pins->ain1 = true; pins->ain2 = false;
        pins->pwm_ccr = (uint16_t)(((uint32_t)(d < 0 ? -d : d) * arr) / 1000u);
        return true;
    case BRIDGE_DRIVE_REVERSE:
        pins->stby = true;
        pins->ain1 = false; pins->ain2 = true;
        pins->pwm_ccr = (uint16_t)(((uint32_t)(d < 0 ? -d : d) * arr) / 1000u);
        return true;
    }
    return false;
}
