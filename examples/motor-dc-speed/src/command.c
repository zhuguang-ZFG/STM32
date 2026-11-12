#include "command.h"
#include <string.h>
#include <stdlib.h>

void cmd_lease_init(cmd_lease_t *le) { memset(le, 0, sizeof(*le)); }
void cmd_lease_reset(cmd_lease_t *le) { le->session = 0; le->last_seq = 0; le->session_open = false; }

uint32_t cmd_lease_open(cmd_lease_t *le)
{
    /* 简单可复现的会话发生器：基于上次会话递增加一大质数偏移；非零、32 位。 */
    le->session = le->session + 0x9E3779B1u;
    if (le->session == 0u) le->session = 0x1u;
    le->last_seq = 0;
    le->session_open = true;
    return le->session;
}

static bool hex8(const char *s, uint32_t *out)
{
    uint32_t v = 0;
    for (int i = 0; i < 8; i++) {
        char c = s[i];
        v <<= 4;
        if (c >= '0' && c <= '9') v |= (uint32_t)(c - '0');
        else if (c >= 'a' && c <= 'f') v |= (uint32_t)(c - 'a' + 10);
        else if (c >= 'A' && c <= 'F') v |= (uint32_t)(c - 'A' + 10);
        else return false;
    }
    *out = v;
    return true;
}

static bool u32dec(const char *s, uint32_t len, uint32_t *out)
{
    if (len == 0) return false;
    uint32_t v = 0;
    for (uint32_t i = 0; i < len; i++) {
        if (s[i] < '0' || s[i] > '9') return false;
        v = v * 10u + (uint32_t)(s[i] - '0');
        if (v > 1000000000u) return false; /* 有界，防溢出；seq 实用范围足够 */
    }
    *out = v;
    return true;
}

static bool i32dec(const char *s, uint32_t len, int32_t *out)
{
    if (len == 0) return false;
    bool neg = false;
    uint32_t i = 0;
    if (s[0] == '-') { neg = true; i = 1; }
    if (s[0] == '+') { i = 1; }
    uint32_t v = 0;
    for (; i < len; i++) {
        if (s[i] < '0' || s[i] > '9') return false;
        v = v * 10u + (uint32_t)(s[i] - '0');
        if (v > 2000000000u) return false;
    }
    *out = neg ? -(int32_t)v : (int32_t)v;
    return true;
}

/* 取下一个 token（空格分隔）。*off 为绝对偏移（输入=起始搜索位置，输出=token 结束位置）。
 * 返回 token 长度，*tok 指向 token。 */
static uint32_t next_tok(const char *line, uint32_t len, uint32_t *off, const char **tok)
{
    uint32_t i = *off, start = 0;
    while (i < len && line[i] == ' ') i++;
    start = i;
    while (i < len && line[i] != ' ') i++;
    *off = i;
    *tok = line + start;
    return i - start;
}

bool cmd_parse(cmd_lease_t *le, const char *line, uint32_t len, cmd_t *out, bool *fresh)
{
    if (!le || !line || !out) return false;
    out->type = CMD_UNKNOWN; out->session = 0; out->seq = 0;
    out->arg_int = 0; out->arg_str[0] = '\0'; out->has_session = false;
    if (fresh) *fresh = false;
    if (len == 0 || len >= CMD_LINE_MAX) return false;

    const char *tok; uint32_t off = 0;
    uint32_t tlen = next_tok(line, len, &off, &tok);
    if (tlen == 0) return false;

    if (tlen == 5 && memcmp(tok, "HELLO", 5) == 0) { out->type = CMD_HELLO; return true; }

    /* 其余命令：sess(8hex) seq(dec) CMD ... */
    if (tlen != 8 || !hex8(tok, &out->session)) return false;
    out->has_session = true;

    tlen = next_tok(line, len, &off, &tok);
    if (!u32dec(tok, tlen, &out->seq)) return false;

    tlen = next_tok(line, len, &off, &tok);
    if (tlen == 0) return false;

    cmd_type_t type = CMD_UNKNOWN;
    if      (tlen == 3 && memcmp(tok, "ARM", 3) == 0) type = CMD_ARM;
    else if (tlen == 8 && memcmp(tok, "SET_DUTY", 8) == 0) type = CMD_SET_DUTY;
    else if (tlen == 7 && memcmp(tok, "SET_RPM", 7) == 0) type = CMD_SET_RPM;
    else if (tlen == 9 && memcmp(tok, "HEARTBEAT", 9) == 0) type = CMD_HEARTBEAT;
    else if (tlen == 4 && memcmp(tok, "STOP", 4) == 0) type = CMD_STOP;
    else if (tlen == 5 && memcmp(tok, "CLEAR", 5) == 0) type = CMD_CLEAR;
    else if (tlen == 6 && memcmp(tok, "CONFIG", 6) == 0) type = CMD_CONFIG;
    else if (tlen == 6 && memcmp(tok, "STATUS", 6) == 0) type = CMD_STATUS;
    out->type = type;
    if (type == CMD_UNKNOWN) return false;

    /* 会话与 seq 校验（STOP 豁免会话不匹配，design §9） */
    bool session_ok = le->session_open && out->session == le->session;
    bool seq_ok = out->seq > le->last_seq;
    if (type == CMD_STOP) {
        if (session_ok) { le->last_seq = out->seq; if (fresh) *fresh = true; }
        return true; /* STOP 始终执行 */
    }
    if (type == CMD_STATUS) return session_ok;
    if (!session_ok || !seq_ok) return false;
    le->last_seq = out->seq;
    if (fresh) *fresh = true;

    /* 参数 */
    if (type == CMD_SET_DUTY || type == CMD_SET_RPM) {
        tlen = next_tok(line, len, &off, &tok);
        if (!i32dec(tok, tlen, &out->arg_int)) return false;
    } else if (type == CMD_CONFIG) {
        tlen = next_tok(line, len, &off, &tok);
        if (tlen == 0 || tlen >= CMD_ARG_MAX) return false;
        memcpy(out->arg_str, tok, tlen);
        out->arg_str[tlen] = '\0';
    }
    return true;
}
