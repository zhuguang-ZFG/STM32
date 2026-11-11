/*
 * main_host.c —— 把超级循环套进量具里跑
 *
 *   ./build/f0.exe block       ← 第二节：uart_echo 死等 RXNE
 *   ./build/f0.exe poll        ← 第三节：uart_echo 换成非阻塞 uart_poll
 *   ./build/f0.exe burn-head   ← 第三节收尾：加一个 2 ms 的批量采样，摆在最前
 *   ./build/f0.exe burn-tail   ← 同一份活，只把它挪到最后一行
 *
 * 第二个参数是连跑几局（默认 1，最多 HOST_REPS_MAX）。宿主机不是真板，
 * 宿主 OS 随时能把一局抢走十几毫秒，单局的"最坏迟到"能差一个数量级；
 * 所以章里和屏幕上引用的都是跨局中位数，逐局报告只当"其中一例"看。
 *
 * 循环体就是章里那三行（superloop_block / superloop_poll 的本体一字不差），
 * 只是在外面套了两只表笔：一圈开始、一圈结束。
 * burn-* 两档的总工作量完全相同，差别只有那一行摆在哪——这就是"用行序当优先级"的价目表。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "superloop.h"
#include "board_host.h"

#define BURN_US 2000u
#define REPS_DEFAULT 5

enum { M_BLOCK, M_POLL, M_BURN_HEAD, M_BURN_TAIL };

int main(int argc, char **argv)
{
    int mode = M_BLOCK;
    const char *mode_name = "阻塞版：led_tick / key_scan / uart_echo（死等 RXNE）";
    int reps = REPS_DEFAULT;

    if (argc > 1) {
        if (strcmp(argv[1], "block") == 0) {
            ;
        } else if (strcmp(argv[1], "poll") == 0) {
            mode = M_POLL;
            mode_name = "改良版：led_tick / key_scan / uart_poll（查一眼就走）";
        } else if (strcmp(argv[1], "burn-head") == 0) {
            mode = M_BURN_HEAD;
            mode_name = "改良版 + 2 ms 批量采样摆在第一行：sensor / led_tick / key_scan / uart_poll";
        } else if (strcmp(argv[1], "burn-tail") == 0) {
            mode = M_BURN_TAIL;
            mode_name = "改良版 + 同样 2 ms 摆到最后一行：led_tick / key_scan / uart_poll / sensor";
        } else {
            fprintf(stderr, "用法：f0 [block|poll|burn-head|burn-tail] [局数 1..%d]\n", HOST_REPS_MAX);
            return 2;
        }
    }
    if (argc > 2) {
        reps = atoi(argv[2]);
        if (reps < 1 || reps > HOST_REPS_MAX) {
            fprintf(stderr, "局数得在 1..%d 之间\n", HOST_REPS_MAX);
            return 2;
        }
    }

    host_init();
    host_print_script();
    printf("本档连跑 %d 局；剧情表只读，所以每局的事件时刻完全一致，"
           "只有真实耗时各局不同。\n\n", reps);

    for (int rep = 1; rep <= reps; rep++) {
        host_run_begin();
        while (!host_done()) {
            host_pass_begin();
            if (mode == M_BURN_HEAD) {
                host_burn_us(BURN_US);
            }
            led_tick();
            key_scan();
            if (mode == M_BLOCK) {
                uart_echo();
            } else {
                uart_poll();
                if (mode == M_BURN_TAIL) {
                    host_burn_us(BURN_US);
                }
            }
            host_pass_end();
        }
        host_measure();
        if (rep == reps) {
            host_report(mode_name);       /* 只有最后一局展开打印，避免日志淹没 */
        }
    }
    if (reps > 1) {
        host_summary(mode_name);
    }
    return 0;
}

