// ch39-pi-loop: the PI loop in one glance — a ±150 rpm step, the actual
// speed curve chases the target with overshoot and settles into the ±5%
// band (整定 ≤2 s); every second play a load is dropped on the motor: the
// curve dips 10 rpm, the PI output note pops (e=−10 rpm → u=−20.05‰) and
// the speed recovers inside 2 s (扰动恢复). Numbers are the chapter's own
// hand calculation. Companion to docs/v5-motion/39-speed-closed-loop-pi.md.
// Site-only: EPUB and print keep the static plates.
// Deterministic in T; the figure stands and only drops the load.
// Load after stick.js. Use as <stick-scene scene="ch39-pi-loop" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, pill, circle, partial, arcPt, lerp, tickBadge, strokePath } = R;

  const GREEN = '#3f9d4f', GREEN_INK = '#1a7f37', RED = '#c2543f', AMBER = '#b8860b', GREY = '#8a8578';
  const CHART = { x: -226, y: -136, w: 220, h: 96 };
  const MOTOR = { cx: 132, cy: -70, r: 20 };
  const AT = 55;

  // 曲线（k 0..1 图表横轴 → rpm），全部确定性
  function curveRpm(k, settled) {
    if (!settled) {
      if (k < 0.15) return 0;
      const q = (k - 0.15) / 0.85;
      let rpm = 150 * (1 - Math.exp(-q * 4.2)) + 26 * Math.exp(-q * 9) * Math.sin(q * 7.5);
      if (q > 0.75) rpm = 150 + (rpm - 150) * (1 - (q - 0.75) / 0.25);
      return rpm;
    }
    const dip = Math.exp(-Math.pow((k - 0.42) / 0.09, 2)) * 10;
    return 150 - dip;
  }

  function chart(g, settled, drawK, dipK, fade) {
    rr(g, CHART.x, CHART.y, CHART.w, CHART.h, 5);
    inkFill(g, C.paper, 1.6);
    text(g, 'rpm', CHART.x + 10, CHART.y + 14, 8, C.muted, 'left');
    const y150 = CHART.y + CHART.h - (150 / 180) * CHART.h;
    ln(g, CHART.x + 6, y150, CHART.x + CHART.w - 6, y150, 1.3, C.muted);
    text(g, '目标 150', CHART.x + CHART.w - 10, y150 - 6, 7.5, C.muted, 'right');
    const yTop = CHART.y + CHART.h - (157.5 / 180) * CHART.h;
    const yBot = CHART.y + CHART.h - (142.5 / 180) * CHART.h;
    g.save();
    g.globalAlpha *= 0.5 * fade;
    ln(g, CHART.x + 6, yTop, CHART.x + CHART.w - 6, yTop, 1, GREEN);
    ln(g, CHART.x + 6, yBot, CHART.x + CHART.w - 6, yBot, 1, GREEN);
    g.restore();
    ln(g, CHART.x + 6, CHART.y + 1, CHART.x + 6, CHART.y + CHART.h - 1, 1.2, C.muted);
    // 实际曲线：分段画（settled 时先画整定段，再琥珀画 dip 段）
    const N = 40;
    const px = [];
    for (let i = 0; i <= N; i++) {
      const k = i / N;
      px.push([CHART.x + k * CHART.w, CHART.y + CHART.h - (curveRpm(k, settled) / 180) * CHART.h]);
    }
    g.save();
    g.globalAlpha *= fade;
    if (!settled) {
      strokePath(g, partial(px, Math.min(1, drawK)), 2.4, GREEN_INK);
      text(g, '±150 rpm 阶跃', CHART.x + 12, CHART.y + CHART.h - 10, 7.5, C.muted, 'left');
    } else {
      // 整定基线（150 平线）+ 琥珀 dip 段画到 dipK
      ln(g, px[0][0], px[0][1], px[N][0], px[N][1], 2.2, GREEN_INK);
      const dipFrom = Math.floor(0.28 * N), dipTo = Math.ceil(0.6 * N);
      const dipPts = px.slice(dipFrom, dipTo + 1);
      strokePath(g, partial(dipPts, Math.min(1, dipK)), 2.2, AMBER);
      text(g, '负载扰动', CHART.x + 12 + CHART.w * 0.3, CHART.y + CHART.h - 10, 7.5, AMBER, 'left');
    }
    g.restore();
  }

  function motor(g, fade) {
    ln(g, MOTOR.cx - 12, MOTOR.cy + MOTOR.r, MOTOR.cx - 4, 0, 2.2);
    ln(g, MOTOR.cx + 12, MOTOR.cy + MOTOR.r, MOTOR.cx + 4, 0, 2.2);
    circle(g, MOTOR.cx, MOTOR.cy, MOTOR.r);
    inkFill(g, C.paper, 1.8);
    text(g, 'M', MOTOR.cx, MOTOR.cy + 3.5, 9, C.ink, 'center');
  }

  SC['ch39-pi-loop'] = {
    dur: 5.6,
    width: 560,
    label: '给 150 rpm 阶跃，实际转速曲线带超调追上目标并进入 ±5% 带整定；负载扰动让曲线跌 10 rpm，PI 输出 −20.05‰ 拉回，2 秒内恢复。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const load = S.n % 2 === 1;
      const B = load
        ? { dropT: 1.45, noteT: 2.0, dipT: 1.6, dipEnd: 3.1, tickT: 3.5, cheerT: 3.85 }
        : { stepT: 0.25, drawEnd: 2.3, pillT: 2.4, tickT: 2.85, cheerT: 3.2 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let sx = 1;
      let drawK = 0, dipK = 0, pillK = 0, tickK = 0, dropK = 0, wtY = 0, saidK = 0, cheer = 0;
      let pillText = '', pillFill = '#dafbe1';

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
        drawK = load ? 1 : 0;
        dipK = load ? 1 : 0;
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        if (!load) {
          drawK = E.soft(seg(T, B.stepT, B.drawEnd));
          pillK = seg(T, B.pillT, B.pillT + 0.25) * (1 - seg(T, 4.4, 4.65));
          pillText = '整定 1.8 s ≤ 2 s';
          tickK = E.back(seg(T, B.tickT, B.tickT + 0.3)) * fade;
        } else {
          drawK = 1;
          dipK = seg(T, B.dipT, B.dipEnd);
          dropK = seg(T, B.dropT, B.dropT + 0.25);
          wtY = seg(T, B.dropT + 0.1, B.dropT + 0.35) * (MOTOR.cy - MOTOR.r - 96);
          pillK = seg(T, B.noteT, B.noteT + 0.25) * (1 - seg(T, 5.0, 5.25));
          pillText = 'e=−10 rpm → u=−20.05‰';
          pillFill = '#fdeecd';
          saidK = 0;
          tickK = E.back(seg(T, B.tickT, B.tickT + 0.3)) * fade;
          // bisect2: reach disabled
        }
        cheer = E.soft(seg(T, B.cheerT, B.cheerT + 0.3)) * (1 - E.soft(seg(T, B.cheerT + 0.55, B.cheerT + 0.85)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
      }

      chart(g, load, drawK, dipK, S.on ? 1 : 1);
      motor(g, S.on ? 1 : 1);
      // 负载下落
      if (dropK > 0) {
        circle(g, MOTOR.cx + 6, MOTOR.cy - MOTOR.r - 10 + wtY, 7);
        inkFill(g, GREY, 1.5, C.ink);
      }
      fig(g, pose, AT, 0, { sx, wave: S.wave, wt: S.wt });
      if (!load) chipFly(g, seg(T, B.flyT || 9e9, (B.flyT || 9e9) + 0.4));
      if (pillK > 0) {
        g.save();
        g.globalAlpha *= Math.min(1, pillK);
        pill(g, 120, -34, pillText, pillFill, C.ink, 8.5);
        g.restore();
      }
      if (tickK > 0) tickBadge(g, CHART.x + CHART.w - 14, CHART.y + CHART.h - 14, tickK, 9, '#dafbe1', GREEN_INK);
      if (cheer > 0.4) sparks(g, AT, -142, cheer, 9, 5, GREEN);

      function chipFly(k) {
        if (k <= 0 || k >= 1) return;
        const p = arcPt([CHART.x + CHART.w - 40, CHART.y + CHART.h - (150 / 180) * CHART.h], [AT - 10, -110], 36, E.soft(k));
        g.save();
        g.globalAlpha *= 1 - k * 0.25;
        circle(g, p[0], p[1], 4);
        inkFill(g, '#fde68a', 1.3, AMBER);
        g.restore();
      }
      void saidK;
    },
  };
})();
