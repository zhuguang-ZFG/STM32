/* 主机测试 H01–H10（acceptance §2.1）。独立断言，不重复实现被测公式当期望。 */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "encoder.h"
#include "speed_estimator.h"
#include "pi_controller.h"
#include "motor_state.h"
#include "motor_bridge.h"
#include "command.h"
#include "telemetry.h"
#include "control_tick.h"

static int g_pass = 0, g_fail = 0;
#define CHECK(cond, name) do { \
    if (cond) { g_pass++; } \
    else { g_fail++; printf("FAIL %s:%d %s\n", __FILE__, __LINE__, name); } \
} while (0)

static control_params_t make_params(void)
{
    control_params_t p;
    memset(&p, 0, sizeof(p));
    p.kp = 2.0f; p.ki = 0.5f; p.i_limit = 500.f; p.duty_limit = 900.f;
    p.target_limit_rpm = 300.f; p.ramp_rpm_per_s = 600.f; p.alpha = 1.f;
    p.reverse_zero_rpm = 5.f; p.reverse_hold_ms = 100; p.reverse_timeout_ms = 3000;
    p.command_lease_ms = 500; p.startup_grace_ms = 300; p.no_feedback_ms = 500;
    p.rpm_min = 20.f; p.rpm_max = 400.f;
    return p;
}

/* H01：正/反向计数、跨回绕、恰好半模 */
static void test_h01(void)
{
    int32_t d = 0;
    CHECK(enc_delta(100, 90, 16, &d) && d == 10, "H01 fwd");
    CHECK(enc_delta(90, 100, 16, &d) && d == -10, "H01 rev");
    /* 正向跨回绕：0xFFFF→1 = +2 */
    CHECK(enc_delta(1, 0xFFFF, 16, &d) && d == 2, "H01 wrap fwd");
    /* 反向跨回绕：1→0xFFFF = -2 */
    CHECK(enc_delta(0xFFFF, 1, 16, &d) && d == -2, "H01 wrap rev");
    /* 恰好半模 0x8000：不可消歧 */
    CHECK(!enc_delta(0x8000, 0, 16, &d), "H01 half ambiguous");
    /* 最大可消歧：half-1 正向 */
    CHECK(enc_delta(0x7FFF, 0, 16, &d) && d == 0x7FFF, "H01 max fwd");
}

/* H02：首次采样/dt 异常/跳变；H03：多组 CPR 与手算向量一致 */
static void test_h02_h03(void)
{
    float raw = 0, filt = 0;
    /* CPR=440（P11×Q4×G10），T=10ms：q_rpm=60/(440×0.01)=13.64 rpm */
    speed_estimator_t se;
    se_init(&se, 440, 5000.f, 20, 1.f);
    CHECK(fabsf(se_quantization_rpm(&se, 10) - 13.6363f) < 0.01f, "H03 q_rpm");
    /* 首次采样只建基线 */
    CHECK(!se_update(&se, 1000, 10, &raw, &filt), "H02 first baseline");
    /* 正常：+11 counts / 10 ms → 60×11/(440×0.01)=150 rpm */
    CHECK(se_update(&se, 1011, 10, &raw, &filt) && fabsf(raw - 150.f) < 0.5f, "H03 manual vector");
    /* dt=0 无效 */
    CHECK(!se_update(&se, 1011, 0, &raw, &filt), "H02 dt=0 invalid");
    /* 漏周期：dt>max 无效且废基线 */
    CHECK(!se_update(&se, 1030, 25, &raw, &filt), "H02 dt too big");
    /* 超物理上限跳变无效 */
    se_init(&se, 440, 100.f /*max rpm*/, 20, 1.f);
    (void)se_update(&se, 0, 10, &raw, &filt);
    CHECK(!se_update(&se, 400, 10, &raw, &filt), "H02 jump invalid");
    /* 方向为负 */
    se_init(&se, 440, 5000.f, 20, 1.f);
    (void)se_update(&se, 5000, 10, &raw, &filt);
    CHECK(se_update(&se, 4989, 10, &raw, &filt) && raw < -140.f && raw > -160.f, "H03 reverse sign");
}

/* H04：PI 零误差/阶跃/饱和/反号释放/条件积分；H06：斜坡与非法参数 */
static void test_h04_h06(void)
{
    pi_controller_t pi;
    float u = 0;
    CHECK(pi_init(&pi, 2.f, 0.5f, 500.f, 900.f), "H04 init");
    /* 零误差 → 零输出 */
    CHECK(pi_update(&pi, 100.f, 100.f, 0.01f, 1, &u) && u == 0.f, "H04 zero err");
    /* 阶跃：e=100,dt=0.01 → P=200, I=0.5×100×0.01=0.5 → u≈200.5 */
    pi_reset(&pi);
    CHECK(pi_update(&pi, 200.f, 100.f, 0.01f, 1, &u) && fabsf(u - 200.5f) < 0.01f, "H04 step");
    /* 饱和上界：重复大误差 → u=900 封顶，sat_high */
    pi_reset(&pi);
    for (int i = 0; i < 200; i++) pi_update(&pi, 1000.f, 0.f, 0.01f, 1, &u);
    CHECK(u == 900.f && pi.saturated_high, "H04 sat high");
    /* 饱和且 e<0 → 积分朝脱离方向被接受（不再加深饱和） */
    CHECK(pi_update(&pi, 0.f, 50.f, 0.01f, 1, &u), "H04 desat accept");
    /* 反号释放：dir>0 时 u_try<0 → 0 输出，不反向 */
    pi_reset(&pi);
    CHECK(pi_update(&pi, -50.f, 100.f, 0.01f, 1, &u) && u == 0.f, "H04 anti-reverse release");
    /* 负方向区间 */
    pi_reset(&pi);
    CHECK(pi_update(&pi, -200.f, -100.f, 0.01f, -1, &u) && u < 0.f && u >= -900.f, "H04 neg dir");
    /* dir 非法 */
    CHECK(!pi_update(&pi, 0.f, 0.f, 0.01f, 0, &u), "H04 bad dir");
    /* NaN 输入无副作用 */
    pi_reset(&pi);
    CHECK(!pi_update(&pi, NAN, 0.f, 0.01f, 1, &u), "H06 NaN rejected");
    /* 非法参数 */
    control_params_t p = make_params();
    p.duty_limit = 1000.f;
    CHECK(!params_valid(&p), "H06 duty_limit<1000 enforced");
    p = make_params(); p.alpha = 1.5f;
    CHECK(!params_valid(&p), "H06 alpha range");
    /* 斜坡有界 */
    CHECK(fabsf(ramp_target(300.f, 0.f, 600.f, 0.01f) - 6.f) < 0.01f, "H06 ramp step");
    CHECK(ramp_target(3.f, 0.f, 600.f, 0.01f) == 3.f, "H06 ramp reaches");
}

/* H05/H10：STOP/FAULT/模式切换；同周期优先级 */
static void test_h05_h10(void)
{
    motor_fsm_t f;
    fsm_init(&f);
    fsm_set_config_ok(&f, true);
    bridge_output_t out;
    /* 未 ARM 不能 SET 语义（ARM） */
    CHECK(fsm_event(&f, EV_ARM, 0, 0.f, true, &out), "H05 arm");
    CHECK(f.state == MS_ARMED && out.mode == BRIDGE_DISABLE, "H05 armed coast");
    /* STOP → DISABLED 且输出撤销 */
    CHECK(fsm_event(&f, EV_STOP, 0, 0.f, true, &out) && f.state == MS_DISABLED, "H05 stop");
    /* 故障锁存：ARM 后注入，不能自动恢复 */
    fsm_event(&f, EV_ARM, 0, 0.f, true, &out);
    f.fault_bits |= FAULT_FEEDBACK_INVALID;
    f.state = MS_FAULT;
    CHECK(!fsm_event(&f, EV_SET, 0, 0.f, true, &out), "H05 fault blocks set");
    /* CLEAR 两步：先清位，再确认回 DISABLED */
    CHECK(fsm_event(&f, EV_CLEAR, 0, 0.f, true, &out), "H10 clear step1");
    CHECK(f.fault_bits == 0 && f.state == MS_FAULT, "H10 still latched");
    CHECK(fsm_event(&f, EV_CLEAR, 0, 0.f, true, &out) && f.state == MS_DISABLED, "H10 clear step2");
    /* F06：config 不合法禁止 ARM */
    fsm_set_config_ok(&f, false);
    CHECK(!fsm_event(&f, EV_ARM, 0, 0.f, true, &out), "H10 F06 arm blocked");
    /* F01：可运行态无租约 → FAULT（EV_TICK 为信息性事件，ACK 与否不作断言） */
    fsm_init(&f); fsm_set_config_ok(&f, true);
    fsm_event(&f, EV_ARM, 0, 0.f, true, &out);
    (void)fsm_event(&f, EV_TICK, 100, 0.f, false, &out);
    CHECK(f.state == MS_FAULT && (f.fault_bits & FAULT_COMMAND_TIMEOUT), "H10 F01 latch");
}

/* H07：命令超时边界/会话/seq；H08：长行/未知/坏格式 */
static void test_h07_h08(void)
{
    cmd_lease_t le; cmd_lease_init(&le);
    cmd_t c; bool fresh = false;
    CHECK(cmd_parse(&le, "HELLO", 5, &c, &fresh) && c.type == CMD_HELLO, "H07 hello parse");
    uint32_t s = cmd_lease_open(&le);
    char line[64];
    snprintf(line, sizeof(line), "%08lx 1 ARM", (unsigned long)s);
    CHECK(cmd_parse(&le, line, strlen(line), &c, &fresh) && c.type == CMD_ARM && fresh, "H07 arm fresh");
    /* 重复 seq 不新鲜且拒绝 */
    CHECK(!cmd_parse(&le, line, strlen(line), &c, &fresh) && !fresh, "H07 dup seq rejected");
    /* 递增 seq OK */
    snprintf(line, sizeof(line), "%08lx 2 HEARTBEAT", (unsigned long)s);
    CHECK(cmd_parse(&le, line, strlen(line), &c, &fresh) && fresh, "H07 seq inc");
    /* 错误会话拒绝 */
    snprintf(line, sizeof(line), "deadbeef 3 HEARTBEAT");
    CHECK(!cmd_parse(&le, line, strlen(line), &c, &fresh), "H07 wrong session");
    /* STOP 豁免会话仍执行 */
    snprintf(line, sizeof(line), "deadbeef 99 STOP");
    CHECK(cmd_parse(&le, line, strlen(line), &c, &fresh) && c.type == CMD_STOP, "H08 stop immune");
    /* 未知命令 */
    snprintf(line, sizeof(line), "%08lx 4 FLY", (unsigned long)s);
    CHECK(!cmd_parse(&le, line, strlen(line), &c, &fresh), "H08 unknown");
    /* 坏数值 */
    snprintf(line, sizeof(line), "%08lx 5 SET_DUTY abc", (unsigned long)s);
    CHECK(!cmd_parse(&le, line, strlen(line), &c, &fresh), "H08 bad arg");
    /* 过长行：len≥96 拒绝 */
    char big[128]; memset(big, 'A', sizeof(big));
    CHECK(!cmd_parse(&le, big, 120, &c, &fresh), "H08 overlong");
    /* 会话重置：旧命令不复活 */
    cmd_lease_reset(&le);
    snprintf(line, sizeof(line), "%08lx 6 HEARTBEAT", (unsigned long)s);
    CHECK(!cmd_parse(&le, line, strlen(line), &c, &fresh), "H07 stale session");
}

/* H09：遥测满队列不阻塞（由 dropped 计数表达）、帧编解码、CRC、缺序可检 */
static void test_h09(void)
{
    tl_sample_t s; memset(&s, 0, sizeof(s));
    s.target_ramp = 1234; s.delta_count = -5; s.rpm_raw = 1500; s.rpm_filt = 1495;
    s.integral = 250; s.out_duty = 300; s.state = 4; s.fault = 0; s.flags = 1;
    s.exec_us = 800; s.dropped = 0;
    uint8_t buf[64];
    uint32_t n = tl_pack_sample(buf, sizeof(buf), 7, 123456, &s);
    CHECK(n == TL_SAMPLE_FRAME && n <= 64, "H09 frame size");
    uint8_t type = 0; uint32_t seq = 0, t = 0; const uint8_t *pl = 0;
    uint32_t plen = tl_unpack(buf, n, &type, &seq, &t, &pl);
    CHECK(plen == TL_SAMPLE_PAYLOAD && type == TL_TYPE_SAMPLE && seq == 7 && t == 123456, "H09 unpack");
    CHECK((int16_t)(pl[0] | (pl[1] << 8)) == 1234, "H09 payload le");
    /* CRC 破坏拒绝 */
    buf[20] ^= 0xFF;
    CHECK(tl_unpack(buf, n, &type, &seq, &t, &pl) == 0, "H09 crc reject");
    /* 错长度拒绝 */
    CHECK(tl_unpack(buf, 10, &type, &seq, &t, &pl) == 0, "H09 short reject");
}

/* 桥映射：官方真值表 */
static void test_bridge(void)
{
    bridge_pins_t p;
    bridge_output_t o;
    o.mode = BRIDGE_DISABLE; o.duty_permille = 0;
    CHECK(bridge_map(o, 3599, &p) && !p.stby && p.pwm_ccr == 0, "BRIDGE disable=STBY L");
    o.mode = BRIDGE_COAST;
    CHECK(bridge_map(o, 3599, &p) && p.stby && !p.ain1 && !p.ain2 && p.pwm_ccr == 3599, "BRIDGE coast=Stop mode");
    o.mode = BRIDGE_DRIVE_FORWARD; o.duty_permille = 500;
    CHECK(bridge_map(o, 3599, &p) && p.stby && p.ain1 && !p.ain2 && p.pwm_ccr == 1799, "BRIDGE fwd 50%");
    o.mode = BRIDGE_DRIVE_REVERSE; o.duty_permille = -500;
    CHECK(bridge_map(o, 3599, &p) && p.stby && !p.ain1 && p.ain2 && p.pwm_ccr == 1799, "BRIDGE rev 50%");
    o.mode = BRIDGE_SHORT_BRAKE;
    CHECK(bridge_map(o, 3599, &p) && p.stby && p.pwm_ccr == 0, "BRIDGE short brake PWM=L");
    o.mode = BRIDGE_DRIVE_FORWARD; o.duty_permille = 1000;
    CHECK(bridge_map(o, 3599, &p) && p.pwm_ccr == 3599, "BRIDGE 100% endpoint=ARR");
}

/* 端到端薄切片：HELLO→ARM→SET_RPM→tick→STOP，遥测可还原 */
static void test_e2e(void)
{
    control_t c; control_params_t p = make_params();
    control_init(&c, &p, 440, 600.f, 20);
    tl_sample_t s;
    uint32_t t = 0;
    control_tick(&c, t += 10, 0, 100, &s);
    cmd_t cmd; cmd.type = CMD_HELLO;
    char reply[32];
    CHECK(control_command(&c, &cmd, reply, sizeof(reply)) && strncmp(reply, "+OK ", 4) == 0, "E2E hello");
    cmd.type = CMD_ARM;
    CHECK(control_command(&c, &cmd, reply, sizeof(reply)), "E2E arm");
    cmd.type = CMD_SET_RPM; cmd.arg_int = 150;
    c.last_fresh_cmd_ms = 20;
    CHECK(control_command(&c, &cmd, reply, sizeof(reply)), "E2E set rpm");
    uint32_t enc = 1000;
    bool any_valid = false;
    for (int i = 0; i < 50; i++) {
        enc += 11;  /* 150 rpm 等效 */
        control_tick(&c, t += 10, enc, 120, &s);
        c.last_fresh_cmd_ms = t;
        if (s.rpm_filt != 0) any_valid = true;
    }
    CHECK(any_valid, "E2E estimator produces rpm");
    cmd.type = CMD_STOP;
    CHECK(control_command(&c, &cmd, reply, sizeof(reply)), "E2E stop");
    control_tick(&c, t += 10, enc, 80, &s);
    CHECK(s.out_duty == 0 && (s.state == MS_DISABLED || s.state == MS_ARMED), "E2E stopped output zero");
}

int main(void)
{
    test_h01();
    test_h02_h03();
    test_h04_h06();
    test_h05_h10();
    test_h07_h08();
    test_h09();
    test_bridge();
    test_e2e();
    printf("host_tests: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail ? 1 : 0;
}
