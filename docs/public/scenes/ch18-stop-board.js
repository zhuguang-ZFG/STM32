// ch18-stop-board: a figure pulls the RCC lever - the clock bulbs go out one
// by one (Stop: clock gates close, only HSI stays dim), a wake button glows;
// pressing it relights the bulbs one by one. The chapter's wake discipline
// (HSI takes over, re-derive BRR/LOAD) stays on the static plate.
// Companion to docs/v2-reliability/18-low-power.md. Site-only: EPUB and
// print keep the static hand-drawn plate.
// Load after stick.js. Use as <stick-scene scene="ch18-stop-board" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, tickBadge, words, circle } = R;

  const ON_INK = '#1a7f37', GREEN_ON = '#4caf50', AMBER = '#e0a615';
  // Fixed layout, world units: ground y = 0, up is negative, x = 0 centre.
  const PANEL = { x: -110, y: -150, w: 140, h: 110 };     // RCC distribution board
  const BULB_Y = -122;                                     // clock bulb row
  const BULBS = ['PLL', 'HSE', 'APB'].map((s, i) => ({ x: PANEL.x + 28 + i * 34, label: s }));
  const HSI = { x: PANEL.x + 22, y: -76 };                 // the dim survivor
  const LAMP = { x: PANEL.x + PANEL.w - 30, y: -76 };      // main lamp
  const LEVER = { x: PANEL.x - 8, y: -108 };               // stop lever, upper left face
  const WAKE = { x: PANEL.x - 8, y: -68 };                 // wake button, lower left face
  const HOME = -160, AT1 = -138;

  function bulb(g, x, y, k, label) {
    circle(g, x, y, 7);
    inkFill(g, k > 0 ? AMBER : C.paper, 1.5, k > 0 ? AMBER : C.muted);
    if (k > 0) {
      g.save();
      g.globalAlpha *= 0.25 * k;
      circle(g, x, y, 12);
      inkFill(g, AMBER, 0.8, AMBER);
      g.restore();
    }
    text(g, label, x, y + 16, 7, C.muted, 'center');
  }

  function board(g, bulbKs, hsiK, leverA, wakeGlow, lampK) {
    ln(g, PANEL.x + 24, PANEL.y + PANEL.h, PANEL.x + 12, 0, 2.2);
    ln(g, PANEL.x + PANEL.w - 24, PANEL.y + PANEL.h, PANEL.x + PANEL.w - 12, 0, 2.2);
    rr(g, PANEL.x, PANEL.y, PANEL.w, PANEL.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, 'RCC', PANEL.x + 14, PANEL.y + 14, 9, C.ink, 'left');
    text(g, 'STOP', PANEL.x + PANEL.w - 14, PANEL.y + 14, 8.5, C.muted, 'right');
    BULBS.forEach((b, i) => bulb(g, b.x, BULB_Y, bulbKs[i], b.label));
    bulb(g, HSI.x, HSI.y, hsiK, 'HSI');
    bulb(g, LAMP.x, LAMP.y, lampK, '主灯');
    // stop lever on the upper left face
    g.save();
    g.translate(LEVER.x, LEVER.y);
    rr(g, -6, -10, 12, 18, 3);
    inkFill(g, C.paper, 1.4, C.ink);
    ln(g, 0, 0, Math.cos(leverA) * 15, -Math.sin(leverA) * 15, 3, C.ink);
    circle(g, 0, 0, 2.5);
    inkFill(g, C.ink, 1, C.ink);
    g.restore();
    // wake button on the lower left face
    g.save();
    g.translate(WAKE.x + wakeGlow * 2, WAKE.y);
    rr(g, -7, -8, 14, 16, 3);
    inkFill(g, wakeGlow > 0 ? '#ffe9b8' : C.paper, 1.4, C.ink);
    g.restore();
    text(g, 'EXTI', WAKE.x + 14, WAKE.y + 18, 7, C.muted, 'center');
  }

  SC['ch18-stop-board'] = {
    dur: 6.2,
    width: 390,
    label: '一个人拉下 RCC 总闸，时钟灯逐颗熄灭只剩 HSI 微亮，唤醒键亮起；按下后时钟灯逐颗复亮，主灯重新点亮。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let saidK = 0, tickK = 0, wakeGlow = 0, leverA = -0.6, fade = 1;
      const chin = P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] });
      if (T < 0) {
        pose = mix(pose, chin, pulse(t, 5.5, 2, 2.2));
      } else {
        fade = 1 - seg(T, this.dur - 0.45, this.dur);
        const ws = T < 5.1 ? walkSeg(T, 0, 0.6, HOME, AT1) : walkSeg(T, 5.1, 5.7, AT1, HOME);
        x = ws.x;
        gait = T >= 5.1 ? { ph: -ws.ph, amp: ws.amp, stride: ws.stride } : (T < 0.6 ? ws : { ph: 0, amp: 0, stride: 0 });
        const reachL = E.soft(seg(T, 0.6, 1.0)) * (1 - E.soft(seg(T, 2.6, 2.9)));
        const reachW = E.soft(seg(T, 2.9, 3.3)) * (1 - E.soft(seg(T, 4.3, 4.6)));
        pose = mix(pose, P({ hF: lp([LEVER.x + 8, LEVER.y + 8], x, 0, 1), hB: [-4, -54], head: [9, -114], chest: [3, -90] }), reachL);
        pose = mix(pose, P({ hF: lp([WAKE.x - 2, WAKE.y], x, 0, 1), hB: [-4, -54], head: [9, -114] }), reachW);
        const cheer = E.soft(seg(T, 4.75, 5.05)) * (1 - E.soft(seg(T, 5.35, 5.6)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
        leverA = (-0.6 + 1.2 * E.soft(seg(T, 1.0, 1.35))) * fade + -0.6 * (1 - fade);
        wakeGlow = pulse(T, 0.9, 0.1, 0.5) * seg(T, 2.3, 2.6) * (1 - seg(T, 4.3, 4.6));
        tickK = seg(T, 4.5, 4.8) * fade;
        saidK = seg(T, 4.7, 4.9) * (1 - seg(T, 5.6, 5.8));
      }
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });

      // bulbs: on while running, out one by one after the pull, back on after wake
      let bulbKs = [1, 1, 1], hsiK = 0, lampK = 1;
      if (T >= 0) {
        const out = [seg(T, 1.4, 1.75), seg(T, 1.75, 2.1), seg(T, 2.1, 2.45)];
        const back = seg(T, 3.9, 4.2);
        const off = out.map((o) => o * (1 - back));   // dark span per bulb
        bulbKs = off.map((o) => 1 - o);
        hsiK = seg(T, 2.0, 2.3) * (1 - seg(T, 4.0, 4.3));
        lampK = 1 - off[0] * (1 - seg(T, 4.3, 4.6));
      }

      board(g, bulbKs, hsiK, leverA, wakeGlow, lampK);
      fig(g, pose, x, 0, { wave: S.wave, wt: S.wt });
      sparks(g, LAMP.x, LAMP.y - 12, seg(T, 4.35, 4.9), 12, 5, ON_INK);
      tickBadge(g, LAMP.x + 16, LAMP.y - 8, tickK, 7, '#dafbe1', ON_INK);
      bubble(g, x - 22, -124, '时钟回来了', saidK, { tail: 16, size: 9 });
    },
  };
})();
