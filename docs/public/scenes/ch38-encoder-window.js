// ch38-encoder-window: a figure pushes the encoder wheel; each slot past the
// photogate blinks and one count flies into the Δ counter; when the 10 ms
// window closes a ticket stamps the rpm. Fast push: Δ=11 → 150 rpm. Slow
// push (every second play): Δ=1 → 13.6 rpm, the quantisation floor.
// Companion to docs/v5-motion/38-encoder-speed-measurement.md (the formula
// and the P/PPR/G/CPR table live on the chapter's static plates). Site-only:
// EPUB and print keep the static hand-drawn plates.
// All state the viewer reads is deterministic in T; only the wheel angle
// integrates. Load after stick.js.
// Use as <stick-scene scene="ch38-encoder-window" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, pill, arrow, circle, words, tickBadge, arcPt, lerp } = R;

  const GREEN = '#3f9d4f', AMBER = '#b8860b', GREY = '#8a8578';
  const WHEEL = { cx: -150, cy: -80, r: 30 };
  const GATE = { x: -112, y: -80 };
  const CNT = { x: 40, y: -132, w: 108, h: 76 };
  const PILL = { x: 94, y: -34 };
  const FORM = { x: 94, y: -50 };
  const HOME = -235, AT = -200;
  const PUSH = [WHEEL.cx - 21, WHEEL.cy - 21];   // upper-left rim point

  function beats(forget) {
    // slow = forget-named second play: ONE count → the quantisation floor
    return forget
      ? { pushT: 1.5, blinks: [1.6], delta: 1, homeT: 3.5 }
      : { pushT: 1.1, blinks: Array.from({ length: 11 }, (_, i) => 1.2 + i * 0.15), delta: 11, homeT: 3.8 };
  }

  function wheel(g, ang, fade) {
    ln(g, WHEEL.cx - 10, WHEEL.cy + WHEEL.r, WHEEL.cx - 20, 0, 2.2);
    ln(g, WHEEL.cx + 10, WHEEL.cy + WHEEL.r, WHEEL.cx + 20, 0, 2.2);
    circle(g, WHEEL.cx, WHEEL.cy, WHEEL.r);
    inkFill(g, C.paper, 1.8);
    // 12 slots on the rim
    for (let i = 0; i < 12; i++) {
      const a = ang + (i * Math.PI * 2) / 12;
      circle(g, WHEEL.cx + Math.cos(a) * (WHEEL.r - 6), WHEEL.cy + Math.sin(a) * (WHEEL.r - 6), 1.8);
      inkFill(g, C.ink, 1, C.ink);
    }
    // hub + crank handle
    circle(g, WHEEL.cx, WHEEL.cy, 3);
    inkFill(g, C.ink, 1.2);
    ln(g, WHEEL.cx, WHEEL.cy, WHEEL.cx + Math.cos(ang + 2.2) * (WHEEL.r - 10), WHEEL.cy + Math.sin(ang + 2.2) * (WHEEL.r - 10), 2, C.ink);
    text(g, 'PPR=110', WHEEL.cx, WHEEL.cy + WHEEL.r + 14, 7.5, C.muted, 'center');
  }

  function gate(g, blinkK, fade) {
    // photogate bracket hugging the rim
    arcBracket(g, GATE.x, GATE.y, 9, blinkK > 0 ? GREEN : C.muted, fade);
    if (blinkK > 0) {
      circle(g, GATE.x - 2, GATE.y - 2, 2.5);
      inkFill(g, GREEN, 1.2, GREEN);
    }
    text(g, '光栅', GATE.x + 4, GATE.y + 22, 7.5, C.muted, 'left');
  }

  function arcBracket(g, x, y, r, col, fade) {
    g.save();
    g.globalAlpha *= fade;
    g.strokeStyle = col;
    g.lineWidth = 1.8;
    g.beginPath();
    g.arc(x, y, r, Math.PI * 0.75, Math.PI * 1.35);
    g.stroke();
    g.restore();
  }

  function counter(g, delta, fade) {
    ln(g, CNT.x + 18, CNT.y + CNT.h, CNT.x + 8, 0, 2.2);
    ln(g, CNT.x + CNT.w - 18, CNT.y + CNT.h, CNT.x + CNT.w - 8, 0, 2.2);
    rr(g, CNT.x, CNT.y, CNT.w, CNT.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, 'Δ 计数', CNT.x + 14, CNT.y + 16, 8.5, C.ink, 'left');
    text(g, '窗 10 ms', CNT.x + CNT.w - 12, CNT.y + 16, 7, C.muted, 'right');
    text(g, String(delta), CNT.x + CNT.w / 2, CNT.y + 52, 26, C.ink, 'center');
  }

  SC['ch38-encoder-window'] = {
    dur: 5.6,
    width: 520,
    label: '一个人推动编码器轮，每个槽过光栅就闪一下、一个计数飞进 Δ 框；10 毫秒窗结束，票上盖出换算的转速。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const slow = S.n % 2 === 1;
      const B = beats(slow);
      const st = (S.st = S.st || { ang: 0 });
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let sx = 1;
      let pushK = 0, reach = 0, cheer = 0;
      let delta = 0, ticketK = 0, gateBlink = 0;

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        // walks：慢起慢收（E.io），步末保持收步姿势（walkSeg 对 T>b 返回终态），
        // 立刻归零 gait 会让双脚在一步内滑回站立位（motion: skate）。
        if (T < 0.55) {
          const w = walkSeg(T, 0, 0.55, HOME, AT); x = w.x; sx = 1; gait = w;
        } else if (T >= B.homeT) {
          // 回家向左走：转身面向行走方向（sx=-1）；正脸朝右倒着走 = moonwalk skate
          const w = walkSeg(T, B.homeT, Math.min(B.homeT + 0.55, this.dur - 0.05), AT, HOME);
          x = w.x; gait = w; sx = -1;
        } else {
          x = AT;
        }
        // deterministic wheel speed: one push impulse, exponential decay
        const imp = slow ? 1.1 : 3.4;
        const tau = slow ? 1.9 : 2.6;
        const spd = imp * seg(T, B.pushT, B.pushT + 0.12) * Math.exp(-Math.max(0, T - B.pushT - 0.1) / tau) * fade;
        st.ang = (st.ang || 0) + spd * 0.12;
        // counts: one per blink time; Δ follows the blinked schedule
        const done = B.blinks.filter((b) => T >= b).length;
        delta = Math.round(lerp(0, done, 1)) * fade;
        gateBlink = B.blinks.some((b) => T >= b && T < b + 0.14) ? 1 : 0;
        // reach & push
        reach = E.soft(seg(T, B.pushT - 0.4, B.pushT)) * (1 - E.soft(seg(T, B.pushT + 0.5, B.pushT + 0.8)));
        pushK = seg(T, B.pushT, B.pushT + 0.15);
        pose = mix(pose, P({ hF: lp([PUSH[0] + pushK * 6, PUSH[1] + pushK * 14], x, 0, 1), hB: [-4, -54], head: [9, -113], chest: [4, -90] }), reach);
        // ticket after the window closes (last blink + a beat)
        const ticketT = B.blinks[B.blinks.length - 1] + 0.3;
        ticketK = E.back(seg(T, ticketT, ticketT + 0.3)) * fade;
        cheer = E.soft(seg(T, ticketT + 0.25, ticketT + 0.55)) * (1 - E.soft(seg(T, ticketT + 1.0, ticketT + 1.3)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
      }

      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });
      const lastT1 = B.homeT + 0.55;
      if (T >= lastT1 + 0.15) sx = 1;

      counter(g, delta, S.on ? 1 : 1);
      wheel(g, st.ang, S.on ? 1 : 1);
      gate(g, gateBlink, S.on ? 1 : 1);
      fig(g, pose, x, 0, { sx, wave: S.wave, wt: S.wt });
      // count dots flying gate → counter for recent blinks
      if (T >= 0) {
        for (const b of B.blinks) {
          const k = seg(T, b, b + 0.4);
          if (k > 0 && k < 1) {
            const p = arcPt([GATE.x, GATE.y - 6], [CNT.x + CNT.w / 2, CNT.y + CNT.h / 2], 36, E.soft(k));
            circle(g, p[0], p[1], 2.6);
            inkFill(g, GREEN, 1.1, GREEN);
          }
        }
      }
      if (ticketK > 0 && T >= 0) {
        const k = Math.min(1, ticketK);
        g.save();
        g.globalAlpha *= k;
        const rpm = slow ? '13.6 rpm' : '150 rpm';
        const fill = slow ? '#fdeecd' : '#dafbe1';
        pill(g, PILL.x, PILL.y + (1 - k) * 6, rpm, fill, C.ink, 10);
        text(g, slow ? 'Δ=1 · 量化下限' : 'Δ=11 · CPR=440', FORM.x, FORM.y, 7, C.muted, 'center');
        g.restore();
        if (!slow) tickBadge(g, PILL.x + 40, PILL.y - 12, ticketK, 7, '#dafbe1', '#1a7f37');
        if (!slow) sparks(g, PILL.x + 34, PILL.y - 14, ticketK * 0.8, 8, 4, GREEN);
      }
    },
  };

})();
