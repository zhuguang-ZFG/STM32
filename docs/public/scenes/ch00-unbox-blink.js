// ch00-unbox-blink: a figure presses flash on the build machine, the build log
// runs, the firmware flies into the BluePill and the PC13 LED blinks at 1 Hz.
// Companion to docs/onramp/00-from-box-to-blink.md (section 四); all numbers
// (1 Hz, PC13) are the chapter's frozen wording. Site-only: EPUB and print
// keep the static hand-drawn plate.
// Load after stick.js. Use as <stick-scene scene="ch00-unbox-blink" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, tickBadge, words, stand, arcPt, circle } = R;

  const ADD = '#dafbe1', ADD_INK = '#1a7f37', LED_ON = '#4caf50';
  // Fixed layout, world units: ground y = 0, up is negative, x = 0 centre.
  const M = { x: -118, y: -146, w: 148, h: 100 };        // build+flash machine
  const BTN = [M.x - 9, -84];                            // flash button, left face
  const B = { x: 112, y: -96, w: 74, h: 40 };            // BluePill on a stand
  const LED = [B.x + B.w - 14, B.y + 10];                // PC13 position
  const HOME = -172, AT = -154;

  function machine(g, rowsK, tickK, pressK) {
    ln(g, M.x + 24, M.y + M.h, M.x + 12, 0, 2.2);
    ln(g, M.x + M.w - 24, M.y + M.h, M.x + M.w - 12, 0, 2.2);
    rr(g, M.x, M.y, M.w, M.h, 6);
    inkFill(g, C.paper, 1.7);
    ln(g, M.x, M.y + 17, M.x + M.w, M.y + 17, 1.3);
    text(g, 'make', M.x + 12, M.y + 12, 8.5, C.ink, 'left');
    // three build-log rows appear one by one, then fade with the rest
    [0, 1, 2].forEach((i) => {
      const k = rowsK[i];
      if (k > 0) {
        g.save();
        g.beginPath();
        g.rect(M.x + 6, M.y + 26 + i * 18 - 9, (M.w - 12) * k, 18);
        g.clip();
        words(g, M.x + 12, M.y + 34 + i * 18, M.w - 30 - i * 14, 3 + i * 5);
        g.restore();
      }
    });
    tickBadge(g, M.x + M.w - 16, M.y + 10, tickK, 7.5, ADD, ADD_INK);
    // the flash button, depressed while the hand is on it
    g.save();
    g.translate(BTN[0] + pressK * 2.5, BTN[1]);
    rr(g, -9, -9, 18, 18, 4);
    inkFill(g, C.butter, 1.5, C.ink);
    g.restore();
  }

  function boardDraw(g, ledK, blinkOn) {
    // usb nub first (it sits behind the board edge)
    rr(g, B.x - 8, B.y + 12, 10, 14, 2);
    inkFill(g, '#dcdcdc', 1.2);
    stand(g, B.x + 16, B.x + B.w - 16, B.y + B.h, 6);
    rr(g, B.x, B.y, B.w, B.h, 4);
    inkFill(g, C.paper, 1.6);
    text(g, 'PC13', B.x + B.w / 2, -14, 8, C.muted, 'center');
    circle(g, LED[0], LED[1], 5.5);
    inkFill(g, blinkOn ? LED_ON : C.paper, 1.5, ADD_INK);
    if (blinkOn > 0) {
      g.save();
      g.globalAlpha *= 0.3 * ledK;
      circle(g, LED[0], LED[1], 10);
      inkFill(g, LED_ON, 0.8, LED_ON);
      g.restore();
    }
  }

  SC['ch00-unbox-blink'] = {
    dur: 6.4,
    width: 390,
    label: '一个人按下烧录台的按钮，构建日志逐行跑完，固件飞进开发板，板上的 PC13 灯开始按 1 Hz 闪烁。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let rowsK = [0, 0, 0], tickK = 0, pressK = 0, ledK = 0, flyK = 0, saidK = 0;
      const chin = P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] });
      if (T < 0) {
        // Idle: breathing plus a chin scratch every few seconds.
        pose = mix(pose, chin, pulse(t, 5.5, 2, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        const ws = T < 4.8 ? walkSeg(T, 0, 0.6, HOME, AT) : walkSeg(T, 4.8, 5.5, AT, HOME);
        x = ws.x;
        gait = T >= 4.8 ? { ph: -ws.ph, amp: ws.amp, stride: ws.stride } : ws;
        const reach = E.soft(seg(T, 0.6, 1.0)) * (1 - E.soft(seg(T, 1.5, 1.8)));
        const cheer = E.back(seg(T, 3.1, 3.5)) * (1 - E.soft(seg(T, 4.0, 4.3)));
        pose = mix(pose, P({ hF: lp([BTN[0] + 3, BTN[1]], x, 0, 1), hB: [-4, -54], head: [9, -114], chest: [3, -90] }), reach);
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
        pressK = E.soft(seg(T, 0.7, 0.9)) * (1 - E.soft(seg(T, 1.4, 1.6)));
        rowsK = [seg(T, 0.9, 1.15), seg(T, 1.1, 1.35), seg(T, 1.3, 1.55)].map((k) => k * fade);
        tickK = seg(T, 1.5, 1.8) * fade;
        flyK = seg(T, 2.0, 2.7);
        ledK = seg(T, 2.75, 3.05) * fade;
        saidK = seg(T, 3.3, 3.5) * (1 - seg(T, 4.5, 4.7));
      }
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });

      // 1 Hz blink: on half a second, off half a second, three cycles (3.0–6.0).
      const blinkOn = ledK > 0 && T >= 3.0 && T <= 6.0 && (T - 3.0) % 1 < 0.5 ? ledK : 0;
      machine(g, rowsK, tickK, pressK);
      boardDraw(g, ledK, blinkOn);
      fig(g, pose, x, 0, { wave: S.wave, wt: S.wt });
      // the firmware strip flies from the machine to the board
      if (flyK > 0 && flyK < 1) {
        const p = arcPt([M.x + M.w / 2, M.y - 6], [B.x + B.w / 2, B.y + 4], 36, E.soft(flyK));
        rr(g, p[0] - 13, p[1] - 4, 26, 8, 3);
        inkFill(g, ADD, 1.2, ADD_INK);
      }
      sparks(g, LED[0], LED[1] - 10, seg(T, 2.8, 3.4), 12, 5, ADD_INK);
      bubble(g, x - 8, -132, '1 Hz!', saidK, { tail: 16, size: 9 });
    },
  };
})();
