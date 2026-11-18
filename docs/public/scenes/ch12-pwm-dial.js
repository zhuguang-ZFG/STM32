// ch12-pwm-dial: a figure turns the CCR dial; the scope's square wave duty
// slides from 25% to 75% while the frequency stays put - duty lives in CCR,
// frequency in PSC/ARR (the chapter's frozen numbers: 1 kHz, PSC=83/ARR=999).
// Companion to docs/v1-drivers/12-timers-pwm.md; the static plate carries the
// three-knob formula. Site-only: EPUB and print keep the plate.
// Load after stick.js. Use as <stick-scene scene="ch12-pwm-dial" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, tickBadge, words, arcPt, circle } = R;

  const ON_INK = '#1a7f37', GREEN_ON = '#4caf50', WAVE = '#1f4680';
  // Fixed layout, world units: ground y = 0, up is negative, x = 0 centre.
  const SCOPE = { x: -172, y: -150, w: 112, h: 78 };      // scope box
  const WV = { x0: SCOPE.x + 8, x1: SCOPE.x + SCOPE.w - 8, hi: SCOPE.y + 14, lo: SCOPE.y + 62 };
  const PANEL = { x: -12, y: -130, w: 92, h: 90 };        // dial panel
  const DIAL = { x: 34, y: -95, r: 26 };                  // CCR dial
  const HOME = -60, AT = -5;

  function scopeDraw(g, duty, pct) {
    ln(g, SCOPE.x + 20, SCOPE.y + SCOPE.h, SCOPE.x + 10, 0, 2.2);
    ln(g, SCOPE.x + SCOPE.w - 20, SCOPE.y + SCOPE.h, SCOPE.x + SCOPE.w - 10, 0, 2.2);
    rr(g, SCOPE.x, SCOPE.y, SCOPE.w, SCOPE.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, '1 kHz', SCOPE.x + 12, SCOPE.y + 14, 8.5, C.ink, 'left');
    text(g, 'CCR=' + Math.round((duty * 999)).toString(), SCOPE.x + SCOPE.w - 12, SCOPE.y + 14, 7.5, C.muted, 'right');
    // square wave, two cycles, duty slides
    const n = 48, pts = [];
    for (let i = 0; i <= n; i++) {
      const f = (i / n) % 1;
      const y = f < duty ? WV.hi : WV.lo;
      pts.push([WV.x0 + (WV.x1 - WV.x0) * i / n, y]);
    }
    for (let i = 0; i < n; i++) {
      ln(g, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 2, WAVE);
    }
    ln(g, WV.x0, WV.lo, WV.x1, WV.lo, 1, '#cfcfcf');
    text(g, Math.round(pct) + '%', SCOPE.x + SCOPE.w / 2, SCOPE.y + SCOPE.h + 2, 10, WAVE, 'center');
  }

  function panelDraw(g, angle) {
    ln(g, PANEL.x + 16, PANEL.y + PANEL.h, PANEL.x + 6, 0, 2.2);
    ln(g, PANEL.x + PANEL.w - 16, PANEL.y + PANEL.h, PANEL.x + PANEL.w - 6, 0, 2.2);
    rr(g, PANEL.x, PANEL.y, PANEL.w, PANEL.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, 'CCR', PANEL.x + 12, PANEL.y + 14, 8.5, C.ink, 'left');
    // dial: ring + ticks + pointer
    circle(g, DIAL.x, DIAL.y, DIAL.r);
    inkFill(g, C.paper, 1.6, C.ink);
    for (let i = 0; i <= 8; i++) {
      const a = (-70 + 140 * i / 8) * Math.PI / 180;
      ln(g, DIAL.x + Math.cos(a) * (DIAL.r - 5), DIAL.y - Math.sin(a) * (DIAL.r - 5),
        DIAL.x + Math.cos(a) * (DIAL.r - 1), DIAL.y - Math.sin(a) * (DIAL.r - 1), 1.4, C.muted);
    }
    const ax = DIAL.x + Math.cos(angle) * (DIAL.r - 6);
    const ay = DIAL.y - Math.sin(angle) * (DIAL.r - 6);
    ln(g, DIAL.x, DIAL.y, ax, ay, 2.6, ON_INK);
    circle(g, DIAL.x, DIAL.y, 3);
    inkFill(g, C.ink, 1, C.ink);
    text(g, '0%', DIAL.x - 20, DIAL.y + 4, 7.5, C.muted, 'center');
    text(g, '100%', DIAL.x + 21, DIAL.y + 4, 7.5, C.muted, 'center');
    text(g, 'CCR 直写：立即生效', PANEL.x + PANEL.w / 2, PANEL.y + PANEL.h - 8, 7.5, C.muted, 'center');
  }

  SC['ch12-pwm-dial'] = {
    dur: 5.2,
    width: 390,
    label: '一个人拧大 CCR 旋钮，示波器上方波的占空比从 25% 滑到 75%，频率保持在 1 kHz 不变。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let saidK = 0, tickK = 0;
      const chin = P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] });
      if (T < 0) {
        pose = mix(pose, chin, pulse(t, 5.5, 2, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        const ws = T < 3.7 ? walkSeg(T, 0, 0.6, HOME, AT) : walkSeg(T, 3.7, 4.4, AT, HOME);
        x = ws.x;
        gait = T >= 3.7 ? { ph: -ws.ph, amp: ws.amp, stride: ws.stride } : ws;
        const turn = E.soft(seg(T, 1.1, 2.6)) * (1 - E.soft(seg(T, 3.6, 3.95))) * fade;
        const cheer = E.back(seg(T, 2.8, 3.2)) * (1 - E.soft(seg(T, 3.4, 3.7)));
        pose = mix(pose, P({ hF: lp([DIAL.x - 6, DIAL.y + 10], x, 0, 1), hB: [-4, -54], head: [9, -114], chest: [3, -90] }), E.soft(seg(T, 0.7, 1.1)) * (1 - seg(T, 3.7, 3.9)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
        tickK = seg(T, 2.7, 3.0) * fade;
        saidK = seg(T, 2.9, 3.1) * (1 - seg(T, 4.0, 4.2));
      }
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });

      // duty: idle 25%, turns to 75% while the pointer sweeps, back on fade
      let k = 0;
      if (T >= 0) {
        k = E.soft(seg(T, 1.1, 2.6)) * (1 - E.soft(seg(T, 4.75, 5.2)));
      }
      const duty = 0.25 + 0.5 * k;
      const pct = 25 + 50 * k;
      const angle = (-70 + 140 * k) * Math.PI / 180;

      panelDraw(g, angle);
      scopeDraw(g, duty, pct);
      fig(g, pose, x, 0, { wave: S.wave, wt: S.wt });
      sparks(g, DIAL.x, DIAL.y - DIAL.r - 6, seg(T, 2.6, 3.2), 12, 5, ON_INK);
      tickBadge(g, DIAL.x + DIAL.r + 6, DIAL.y - DIAL.r + 2, tickK, 7, '#dafbe1', ON_INK);
      bubble(g, x - 8, -128, '25% → 75%', saidK, { tail: 16, size: 9 });
    },
  };
})();
