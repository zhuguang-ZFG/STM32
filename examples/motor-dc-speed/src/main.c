/* ARM 侧入口（薄切片：可编译、逻辑完整，**未上板验证**，全部标 CANDIDATE）。
 * 数据流 per design §4：串口接收 → 主循环校验 → 有界邮箱 → TIM4 ISR 取快照
 * → 编码器/估速 → 状态机/PI → 桥 → 遥测；主循环只负责收发，不直接改桥。
 */
#include "main.h"
#include "board_config.h"
#include "control_tick.h"
#include "motor_bridge.h"
#include "telemetry.h"
#include <string.h>

static control_t g_control;
static control_params_t g_params = {
    .kp = 2.0f, .ki = 0.5f, .i_limit = 500.f, .duty_limit = 900.f,
    .target_limit_rpm = 300.f, .ramp_rpm_per_s = 600.f, .alpha = 1.f,
    .reverse_zero_rpm = 5.f, .reverse_hold_ms = 100, .reverse_timeout_ms = 3000,
    .command_lease_ms = 500, .startup_grace_ms = 300, .no_feedback_ms = 500,
    .rpm_min = 20.f, .rpm_max = 400.f,
};
/* CPR=0：未标定 → fsm config_ok=false → ARM 被 F06 拒绝（安全默认） */
#define BOARD_ENC_CPR_RUNTIME  0u

/* ---- 有界行缓冲（H08：超长丢弃到换行；半帧不刷新租约） ---- */
static char rx_line[BOARD_UART_RX_LINE_MAX];
static uint32_t rx_len;
static volatile bool rx_line_ready;

void board_uart_rx_byte(uint8_t b)
{
    if (b == '\n') {
        if (rx_len > 0 && rx_len < BOARD_UART_RX_LINE_MAX - 1) {
            rx_line[rx_len] = '\0';
            rx_line_ready = true;
        }
        rx_len = 0;
    } else if (rx_len < BOARD_UART_RX_LINE_MAX - 1) {
        rx_line[rx_len++] = (char)b;
    } else {
        rx_len = BOARD_UART_RX_LINE_MAX - 1;  /* 有界：等换行整行丢弃 */
    }
}

/* TIM4 控制 ISR：读编码器快照 → control_tick → 写桥（不读阻塞总线/不打印/不分配） */
void board_control_isr(void)
{
    HAL_GPIO_WritePin(BOARD_PIN_MEAS_PORT, BOARD_PIN_MEAS_PIN, GPIO_PIN_SET);

    const uint32_t enc = (uint32_t)__HAL_TIM_GET_COUNTER(&htim2);
    tl_sample_t sample;
    control_tick(&g_control, HAL_GetTick(), enc, 0u, &sample);

    bridge_output_t out = { BRIDGE_DISABLE, 0 };
    if (g_control.fsm.state == MS_RUN_OPEN || g_control.fsm.state == MS_RUN_SPEED ||
        g_control.fsm.state == MS_REVERSING) {
        out.duty_permille = g_control.cur_duty;
        out.mode = (g_control.cur_duty >= 0) ? BRIDGE_DRIVE_FORWARD : BRIDGE_DRIVE_REVERSE;
        if (g_control.cur_duty == 0 &&
            (g_control.fsm.rev_phase == RS_WAIT_ZERO || g_control.fsm.rev_phase == RS_HOLD)) {
            out.mode = BRIDGE_DISABLE;   /* 停稳期撤销驱动 */
        }
    }

    bridge_pins_t pins;
    if (bridge_map(out, BOARD_PWM_ARR, &pins)) {
        HAL_GPIO_WritePin(BOARD_PIN_STBY_PORT, BOARD_PIN_STBY_PIN,
                          pins.stby ? GPIO_PIN_SET : GPIO_PIN_RESET);
        HAL_GPIO_WritePin(BOARD_PIN_AIN1_PORT, BOARD_PIN_AIN1_PIN,
                          pins.ain1 ? GPIO_PIN_SET : GPIO_PIN_RESET);
        HAL_GPIO_WritePin(BOARD_PIN_AIN2_PORT, BOARD_PIN_AIN2_PIN,
                          pins.ain2 ? GPIO_PIN_SET : GPIO_PIN_RESET);
        __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, pins.pwm_ccr);
    }

    HAL_GPIO_WritePin(BOARD_PIN_MEAS_PORT, BOARD_PIN_MEAS_PIN, GPIO_PIN_RESET);
}

int main(void)
{
    HAL_Init();
    board_clock_init();         /* 72 MHz 候选（CANDIDATE，P2 核验） */
    board_gpio_init();
    board_tim_init();
    board_uart_init();

    control_init(&g_control, &g_params, BOARD_ENC_CPR_RUNTIME, 600.f, 50u);

    for (;;) {
        if (rx_line_ready) {
            rx_line_ready = false;
            cmd_t cmd; bool fresh = false;
            const bool ok = cmd_parse(&g_control.lease, rx_line, strlen(rx_line), &cmd, &fresh);
            if (ok) {
                if (cmd.type == CMD_HEARTBEAT || fresh) {
                    g_control.last_fresh_cmd_ms = HAL_GetTick();
                }
                char reply[48];
                control_command(&g_control, &cmd, reply, sizeof(reply));
                HAL_UART_Transmit(&huart1, (uint8_t *)reply, (uint16_t)strlen(reply), 10);
                HAL_UART_Transmit(&huart1, (uint8_t *)"\n", 1, 1);
            } else {
                HAL_UART_Transmit(&huart1, (uint8_t *)"-NACK\n", 6, 1);
            }
        }
        /* IWDG：P2 冻结后按「控制心跳+主循环健康」喂狗（design §4），当前不启用 */
        HAL_Delay(1);
    }
}
