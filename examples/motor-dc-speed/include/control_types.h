/* 控制核心公共类型（HAL 无关，主机可测）。单位约定见 design.md §4/§7。 */
#ifndef MOTOR_CONTROL_TYPES_H
#define MOTOR_CONTROL_TYPES_H

#include <stdint.h>
#include <stdbool.h>

typedef enum {
    MS_BOOT = 0,
    MS_DISABLED,
    MS_ARMED,
    MS_RUN_OPEN,
    MS_RUN_SPEED,
    MS_REVERSING,
    MS_FAULT
} motor_state_t;

typedef enum {
    RS_NONE = 0,
    RS_RAMP_DOWN,   /* 保持原方向，输出按斜坡降至零 */
    RS_WAIT_ZERO,   /* 撤销驱动，等待停稳 */
    RS_HOLD,        /* 停稳保持 reverse_hold_ms */
    RS_RAMP_UP      /* 改变方向后从零升速（日志可区分） */
} reversing_phase_t;

/* 故障位：design §8。锁存，首因可查。 */
#define FAULT_COMMAND_TIMEOUT   (1u << 0)   /* F01 */
#define FAULT_FEEDBACK_INVALID  (1u << 1)   /* F02 */
#define FAULT_NO_FEEDBACK       (1u << 2)   /* F03 */
#define FAULT_CONTROL_DEADLINE  (1u << 3)   /* F04 */
#define FAULT_REVERSAL_TIMEOUT  (1u << 4)   /* F05 */
#define FAULT_INVALID_CONFIG    (1u << 5)   /* F06 */

/* 桥输出合同（design §5）：桥层再把模式映射到 STBY/AIN1/AIN2/PWMA。
 * 模式经官方真值表核验（TB6612FNG 2026-05-13 p.4）：
 * 高阻释放 = STBY=L（Standby）或 IN1=IN2=L&PWM=H（Stop）；
 * 方向有效 + PWM=L = 短接制动（显式选项）。
 */
typedef enum {
    BRIDGE_DISABLE = 0,     /* STBY=L（默认停止/故障态，高阻+节电） */
    BRIDGE_DRIVE_FORWARD,   /* IN1=H IN2=L PWM=占空比 */
    BRIDGE_DRIVE_REVERSE,   /* IN1=L IN2=H PWM=占空比 */
    BRIDGE_COAST,           /* STBY=H, IN1=IN2=L, PWM=H（Stop 模式，高阻） */
    BRIDGE_SHORT_BRAKE      /* STBY=H, 方向保持, PWM=L（显式，V1 默认不开） */
} bridge_mode_t;

typedef struct {
    bridge_mode_t mode;
    int16_t duty_permille;  /* 带符号千分数 [-1000,1000]；符号须与 mode 方向一致 */
} bridge_output_t;

/* 控制参数（design §7；仅 DISABLED 可更新，拒绝 NaN/Inf）。 */
typedef struct {
    float kp;                 /* 占空比/rpm */
    float ki;                 /* 占空比/(rpm·s) */
    float i_limit;            /* 积分限幅（占空比） */
    float duty_limit;         /* 输出限幅 |u| ≤ duty_limit < 1000 */
    float target_limit_rpm;   /* 目标绝对值上限 */
    float ramp_rpm_per_s;     /* 目标斜坡 */
    float alpha;              /* 速度滤波 [0,1]；1=不过滤 */
    float reverse_zero_rpm;   /* 停稳判据 |rpm| ≤ 该值 */
    uint32_t reverse_hold_ms;
    uint32_t reverse_timeout_ms;
    uint32_t command_lease_ms;/* F01 租约，初值 500 ms */
    uint32_t startup_grace_ms;/* F03 启动宽限 */
    uint32_t no_feedback_ms;  /* F03 无进展窗口 */
    float rpm_min, rpm_max;   /* 可运行区间（P2 冻结） */
} control_params_t;

static inline bool state_is_running(motor_state_t s) {
    return s == MS_ARMED || s == MS_RUN_OPEN || s == MS_RUN_SPEED || s == MS_REVERSING;
}

#endif
