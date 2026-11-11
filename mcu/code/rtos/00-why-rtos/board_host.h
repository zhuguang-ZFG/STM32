/*
 * board_host.h —— 宿主机侧的时钟、事件脚本与统计口径
 *
 * 不用线程、不用真实串口：字节到达时刻与按键按下/松开时刻全由一张脚本表决定，
 * 所以两个模式跑的是同一条"剧情"，数字可以直接并排比。
 *
 * 一局 = 一遍完整剧情。宿主机不是真板：宿主 OS 会随时把这一局抢走十几毫秒，
 * 所以单局的"最坏迟到"能差一个数量级。同一档跑多局（host_run_begin / host_measure），
 * 章里和屏幕上只引用跨局中位数，单局报告当成"其中一例"看。
 */
#ifndef F0_BOARD_HOST_H
#define F0_BOARD_HOST_H

#include <stdint.h>

#define HOST_REPS_MAX 8          /* 一档最多连跑几局 */

void host_init(void);            /* 时钟频率 + 剧情表：整个程序一次 */
void host_run_begin(void);       /* 开一局：时钟起点与所有计数器归零 */
int  host_done(void);            /* 事件脚本跑到终止符了吗 */
void host_pass_begin(void);      /* 超级循环单圈计时 */
void host_pass_end(void);
void host_burn_us(uint32_t us);  /* 顶替一段跑不掉的活：批量采样 / SPI 一帧 */
void host_print_script(void);
void host_measure(void);         /* 结算本局并存档，供跨局统计 */
void host_report(const char *mode_name);   /* 打印最近一局的全量报告 */
void host_summary(const char *mode_name);  /* 打印跨局 min / 中位 / max */

#endif /* F0_BOARD_HOST_H */
