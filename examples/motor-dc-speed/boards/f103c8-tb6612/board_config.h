/* Board configuration — f103c8-tb6612 (候选 v1.2, P0 采购冻结版).
 * 引脚复用依据 DS5319 Rev 20 p.29；真值表依据 Toshiba TB6612FNG 官方手册
 * 2026-05-13 版 p.4（见 plans/2026-11-11-motor-control/research/hardware-freeze.md）。
 * 凡标注 CANDIDATE 的数值在 P2 测量前不得视为已核验事实。
 */
#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

#include <stdint.h>

/* ---- 时钟：候选。APB1 分频影响定时器时钟，P2 必须用时钟树+测量确认 ---- */
#define BOARD_SYSCLK_HZ        72000000u   /* CANDIDATE */
#define BOARD_TIM3_CLK_HZ      72000000u   /* CANDIDATE: APB1 PSC=1 时 TIMxCLK=72M */
#define BOARD_TIM4_CLK_HZ      72000000u   /* CANDIDATE */

/* ---- PWM：TIM3_CH1 = PA6，20 kHz 起点 ----
 * 边沿对齐、PSC=0 时 ARR = 72MHz/20kHz - 1 = 3599。100% 端点按模式实现并测试（B02）。
 */
#define BOARD_PWM_HZ           20000u      /* CANDIDATE, design §4 起点 */
#define BOARD_PWM_ARR          (BOARD_TIM3_CLK_HZ / BOARD_PWM_HZ - 1u)  /* =3599 @候选时钟 */
#define BOARD_PWM_CH           1

/* ---- 控制周期：TIM4 更新中断，10 ms 起点（16 位定时器：PSC=7199 → 10 kHz，ARR=99 → 100 Hz） ---- */
#define BOARD_CONTROL_HZ       100u        /* CANDIDATE */
#define BOARD_CONTROL_PERIOD_MS (1000u / BOARD_CONTROL_HZ)               /* 10 ms */
#define BOARD_CONTROL_DEADLINE_US 2000u   /* 目标执行时间预算，design §4 */
#define BOARD_TIM4_PSC         7199u                            /* 72 MHz/7200 = 10 kHz */
#define BOARD_TIM4_ARR         (10000u / BOARD_CONTROL_HZ - 1u) /* =99 → 10 ms */

/* ---- 编码器：TIM2 编码器模式 3（SMS=011，RM0008 Rev21 p.329/392），16 位计数 ---- */
#define BOARD_ENC_TIMER_BITS   16u
#define BOARD_ENC_CPR_DEFAULT  0u          /* 禁止：CPR 未标定前不得使能闭环（F06） */

/* ---- 驱动引脚（全部 GPIO 输出，复位默认下拉/浮空安全态由硬件保证）---- */
#define BOARD_PIN_PWM_PORT     GPIOA
#define BOARD_PIN_PWM_PIN      6           /* PA6 TIM3_CH1 */
#define BOARD_PIN_AIN1_PORT    GPIOB
#define BOARD_PIN_AIN1_PIN     0           /* PB0 CANDIDATE（design §2 表） */
#define BOARD_PIN_AIN2_PORT    GPIOB
#define BOARD_PIN_AIN2_PIN     1           /* PB1 CANDIDATE */
#define BOARD_PIN_STBY_PORT    GPIOB
#define BOARD_PIN_STBY_PIN     10          /* PB10 CANDIDATE + 外部默认关闭电路 */
#define BOARD_PIN_MEAS_PORT    GPIOB
#define BOARD_PIN_MEAS_PIN     12          /* PB12 控制耗时测量 GPIO */

/* ---- UART1：PA9/PA10，115200 8N1 起点 ---- */
#define BOARD_UART_BAUD        115200u     /* CANDIDATE, design §9 */
#define BOARD_UART_RX_LINE_MAX 96u         /* 有界行缓冲，design §9 */

/* ---- 看门狗：IWDG 超时初值，按 LSI 范围 P2 核验 ---- */
#define BOARD_IWDG_TIMEOUT_MS  500u        /* CANDIDATE */

#endif /* BOARD_CONFIG_H */
