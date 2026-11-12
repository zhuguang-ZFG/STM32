/* 命令协议 v1（design §9，H07/H08；MC-104 冻结版）。
 * ASCII 行，≤96 字节（含 \n）；超限丢弃到换行。
 * 语法：  HELLO\n
 *         <sess:8hex> <seq:dec u32> <CMD> [args]\n
 * CMD：ARM / SET_DUTY <±permille> / SET_RPM <±rpm> / HEARTBEAT / STOP / CLEAR / CONFIG k=v / STATUS
 * 除 HELLO/STOP/STATUS 外必须带本会话 sess 且 seq 严格递增；
 * 重复/倒序/未知/非法参数 → NACK 且不刷新租约。STOP 始终有效（会话不匹配也执行）。
 * 响应：+OK <text> | -NACK <code>；HELLO 响应携带新会话 ID。
 */
#ifndef MOTOR_COMMAND_H
#define MOTOR_COMMAND_H

#include <stdint.h>
#include <stdbool.h>
#include "control_types.h"

#define CMD_LINE_MAX   96u
#define CMD_ARG_MAX    48u

typedef enum {
    CMD_HELLO = 0, CMD_ARM, CMD_SET_DUTY, CMD_SET_RPM,
    CMD_HEARTBEAT, CMD_STOP, CMD_CLEAR, CMD_CONFIG, CMD_STATUS, CMD_UNKNOWN
} cmd_type_t;

typedef struct {
    cmd_type_t  type;
    uint32_t    session;
    uint32_t    seq;
    int32_t     arg_int;       /* SET_DUTY/SET_RPM 的数值 */
    char        arg_str[CMD_ARG_MAX]; /* CONFIG 的 k=v */
    bool        has_session;
} cmd_t;

typedef struct {
    uint32_t session;          /* 0=未协商 */
    uint32_t last_seq;
    bool     session_open;
} cmd_lease_t;

void cmd_lease_init(cmd_lease_t *le);
void cmd_lease_reset(cmd_lease_t *le);      /* 复位/断开：清空旧邮箱（旧命令不复活） */
uint32_t cmd_lease_open(cmd_lease_t *le);   /* HELLO：返回新会话 ID（8 hex 风格非零值） */

/* 解析一行（不含 \n，len<96）。写入 out。
 * fresh=该命令是否刷新租约（合法且顺序正确且带本会话）。
 * 返回 false=解析/会话/seq 失败（调用方发 NACK；STOP 例外仍执行）。 */
bool cmd_parse(cmd_lease_t *le, const char *line, uint32_t len, cmd_t *out, bool *fresh);

#endif
