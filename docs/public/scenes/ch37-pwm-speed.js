// ch37-pwm-speed: open-loop speed in one glance — the figure pushes the
// duty slider (CCR 900 → 2700, 25% → 75%) and the motor fan visibly speeds
// up; pulls it back and it slows. Every second play pushes to the top:
// CCR=ARR is 99.97%, one tick short of full voltage (the 差一格 semantics).
// Companion to docs/v5-motion/37-dc-motor-openloop.md (the PWM four-number
// recomputation and endpoint semantics live in the chapter). Site-only:
// EPUB and print keep the static plate.
// Deterministic in T; one stand, zero walks. Load after stick.js.
// Use as <stick-scene scene="ch37-pwm-speed" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, pill, circle } = R;

  const GREEN = '#3f9d4f', GREEN_INK = '#1a7f37', AMBER = '#b8860b';
  const BOARD = { x: -214, y: -132, w: 148, h: 96 };
  const SLIDER = { x: -100, y: -118, h: 66 };
  const MOTOR = { cx: 112, cy: -74, r: 22 };
  const AT = -145;

  function board(g, duty, topK, fade) {
    const dutyK = (duty - 0.25) / 0.75;   // 滑块行程 25%→100%
    ln(g, BOARD.x + 22, BOARD.y + BOARD.h, BOARD.x + 10, 0, 2.2);
    ln(g, BOARD.x + BOARD.w - 22, BOARD.y + BOARD.h, BOARD.x + BOARD.w - 10, 0, 2.2);
    rr(g, BOARD.x, BOARD.y, BOARD.w, BOARD.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, 'PWM', BOARD.x + 14, BOARD.y + 14, 9, C.ink, 'left');
    text(g, 'ARR 3599 · 20 kHz', BOARD.x + BOARD.w - 12, BOARD.y + 14, 7, C.muted, 'right');
    const span = SLIDER.h - 14;
    ln(g, SLIDER.x, SLIDER.y, SLIDER.x, SLIDER.y + SLIDER.h, 1.6, C.muted);
    const cy = SLIDER.y + 7 + dutyK * span;
    ln(g, SLIDER.x - 9, cy, SLIDER.x + 9, cy, 2.4, dutyK > 0.97 ? AMBER : GREEN);
    circle(g, SLIDER.x, cy, 5);
    inkFill(g, C.paper, 1.4, C.ink);
    for (const [k, s] of [[0.25, '25%'], [0.75, '75%'], [1, '100%']]) {
      ln(g, SLIDER.x - 4, SLIDER.y + 7 + k * span, SLIDER.x + 4, SLIDER.y + 7 + k * span, 1.2, C.muted);
      text(g, s, SLIDER.x - 12, SLIDER.y + 10 + k * span, 6.5, C.muted, 'right');
    }
    const ccr = Math.round(3600 * duty);   // CCR = ARR × duty（25% → 900）
    text(g, 'CCR ' + ccr, BOARD.x + 26, BOARD.y + 64, 8.5, C.ink, 'left');
    text(g, 'duty ' + Math.round(duty * 100) + '%', BOARD.x + 26, BOARD.y + 80, 8.5, duty > 0.997 ? AMBER : GREEN, 'left');
    if (topK > 0) {
      g.save();
      g.globalAlpha *= Math.min(1, topK) * fade;
      pill(g, BOARD.x + BOARD.w / 2, BOARD.y - 12, 'CCR=ARR · 99.97%', topK, '#fdeecd', C.ink, 8);
      g.restore();
    }
  }

  function motor(g, spd, ang, fade) {
    ln(g, MOTOR.cx - 14, MOTOR.cy + MOTOR.r, MOTOR.cx - 4, 0, 2.2);
    ln(g, MOTOR.cx + 14, MOTOR.cy + MOTOR.r, MOTOR.cx + 4, 0, 2.2);
    circle(g, MOTOR.cx, MOTOR.cy, MOTOR.r);
    inkFill(g, C.paper, 1.8);
    text(g, 'M', MOTOR.cx, MOTOR.cy + 3.5, 9, C.ink, 'center');
    g.save();
    g.translate(MOTOR.cx, MOTOR.cy);
    g.rotate(ang);
    for (let i = 0; i < 3; i++) {
      const a = (i * Math.PI * 2) / 3;
      ln(g, 0, 0, Math.cos(a) * (MOTOR.r - 7), Math.sin(a) * (MOTOR.r - 7), 2, C.muted);
    }
    g.restore();
    if (spd > 0.15) {
      g.save();
      g.globalAlpha *= Math.min(1, spd / 1.2) * fade;
      const w = 16 + spd * 12;
      for (const s of [-1, 1]) {
        ln(g, MOTOR.cx + MOTOR.r + 6, ARROW_Y + s * 5, MOTOR.cx + MOTOR.r + 6 + w, ARROW_Y + s * 5, 1.6, C.muted);
      }
      g.restore();
    }
  }

  const ARROW_Y = -26;

  SC['ch37-pwm-speed'] = {
    dur: 6.0,
    width: 540,
    label: '一个人推动占空比滑杆，从 25% 到 75%，电机风扇明显变快；顶格播放里 CCR=ARR 只到 99.97%，差一格才满压。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const top = S.n % 2 === 1;
      const st = (S.st = S.st || { ang: 0 });
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let duty = 0.25, pushK = 0, saidK = 0, cheer = 0, topK = 0, spd = 0;

      if (T < 0) {
        // idle 也是「站在面板前」的姿态（与动作首尾一致，无 start/end pop）
        const cy0 = SLIDER.y + 7 + 0.25 * (SLIDER.h - 14);
        pose = mix(pose, P({ hF: lp([SLIDER.x - 9, cy0], AT, 0, 1), hB: [-4, -54], head: [9, -113], chest: [3, -90] }), 0.35);
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        if (top) {
          duty = 0.25 + 0.5 * E.soft(seg(T, 0.7, 1.1)) + 0.25 * E.soft(seg(T, 1.3, 1.7))
            - 0.75 * E.soft(seg(T, 4.4, 4.9));
          topK = seg(T, 1.8, 2.0) * (1 - seg(T, 4.1, 4.35)) * fade;
          saidK = seg(T, 1.85, 2.05) * (1 - seg(T, 3.7, 3.95));
        } else {
          duty = 0.25 + 0.5 * E.soft(seg(T, 0.7, 1.1)) - 0.35 * E.soft(seg(T, 2.6, 3.0));
          cheer = E.soft(seg(T, 3.5, 3.8)) * (1 - E.soft(seg(T, 4.4, 4.7)));
        }
        duty = Math.max(0, Math.min(1, duty));
        spd = 2.4 * duty * fade;
        pushK = E.soft(seg(T, 0.6, 0.95)) * (1 - E.soft(seg(T, 3.6, 3.85)));
        const cy = SLIDER.y + 7 + duty * (SLIDER.h - 14);
        const pose2 = P({ hF: lp([SLIDER.x - 9, cy], AT, 0, 1), hB: [-4, -54], head: [9, -113], chest: [3, -90] });
        pose = mix(pose, pose2, Math.max(pushK, 0.35));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
        saidK = saidK * fade;
        topK = topK;
      }
      st.ang = (st.ang || 0) + spd * 0.1;
      board(g, duty, topK, S.on ? 1 : 1);
      motor(g, spd, st.ang, S.on ? 1 : 1);
      fig(g, pose, AT, 0, { sx: 1, wave: S.wave, wt: S.wt });
      if (saidK > 0) bubble(g, AT + 16, -140, '差一格才满压', saidK, { tail: 14, size: 9 });
      if (cheer > 0.4 && T >= 0) sparks(g, MOTOR.cx, MOTOR.cy - 32, cheer, 9, 5, GREEN);
    },
  };
})();
