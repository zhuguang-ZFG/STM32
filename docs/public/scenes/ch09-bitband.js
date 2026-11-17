// ch09-bitband: a figure flips one switch on the bit-band alias wall; the
// write travels down the wire and ONE bit of the peripheral register flips —
// the read-modify-write done atomically by the hardware, in one step.
// Companion to docs/v1-drivers/09-gpio.md (数据寄存器/位带); the alias formula
// itself lives on the chapter's static plate. Site-only: EPUB and print keep
// the static hand-drawn plate.
// Load after stick.js. Use as <stick-scene scene="ch09-bitband" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, tickBadge, wline, arcPt, circle, words } = R;

  const GREEN_ON = '#4caf50', ON_INK = '#1a7f37';
  // Fixed layout, world units: ground y = 0, up is negative, x = 0 centre.
  const PANEL = { x: -90, y: -110, w: 100, h: 80 };      // alias wall
  const SW_Y = -88;                                       // switch row height
  const SW = [0, 1, 2, 3, 4, 5, 6, 7].map((i) => PANEL.x + 8 + i * 11); // switch x centres
  const FLIP = 0;                                         // the switch we throw
  const ODR = { x: 92, y: -122, w: 92, h: 84 };           // peripheral register
  const CELL_W = 9.4, CELL_Y = -100, CELL_H = 16;
  const WIRE_A = [SW[FLIP] - 1, SW_Y - 10], WIRE_B = [ODR.x + 6, CELL_Y + CELL_H / 2], WIRE_H = 42;
  const HOME = -150, AT = -106;

  function machine(g, flipK, wireK, bitK, fade) {
    // alias wall with eight single-throw switches
    ln(g, PANEL.x + 22, PANEL.y + PANEL.h, PANEL.x + 10, 0, 2.2);
    ln(g, PANEL.x + PANEL.w - 22, PANEL.y + PANEL.h, PANEL.x + PANEL.w - 10, 0, 2.2);
    rr(g, PANEL.x, PANEL.y, PANEL.w, PANEL.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, '别名区', PANEL.x + 14, PANEL.y + 14, 8.5, C.ink, 'left');
    text(g, '0x4200_0000', PANEL.x + PANEL.w - 12, PANEL.y + 14, 7.5, C.muted, 'right');
    // one faint address line + the switch row
    words(g, PANEL.x + 12, PANEL.y + 30, PANEL.w - 26, 5);
    SW.forEach((x, i) => {
      const on = i === FLIP ? flipK : 0;
      rr(g, x - 4, SW_Y + 2, 8, 12, 2);
      inkFill(g, C.paper, 1.2);
      ln(g, x, SW_Y + 4, x + (on ? 5 : -5), SW_Y - 5 + on * 6, 2, C.ink);
    });
    // peripheral register board, eight bit cells
    ln(g, ODR.x + 22, ODR.y + ODR.h, ODR.x + 10, 0, 2.2);
    ln(g, ODR.x + ODR.w - 22, ODR.y + ODR.h, ODR.x + ODR.w - 10, 0, 2.2);
    rr(g, ODR.x, ODR.y, ODR.w, ODR.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, 'ODR', ODR.x + 14, ODR.y + 14, 8.5, C.ink, 'left');
    for (let i = 0; i < 8; i++) {
      const x = ODR.x + 5 + i * (CELL_W + 1.2);
      rr(g, x, CELL_Y, CELL_W, CELL_H, 2);
      const lit = i === FLIP ? bitK : 0;
      inkFill(g, lit > 0 ? GREEN_ON : C.paper, 1.3, lit > 0 ? ON_INK : C.muted);
    }
    text(g, '0 1 2 3 4 5 6 7', ODR.x + ODR.w / 2, CELL_Y - 5, 6.5, C.muted, 'center');
    // the one alias wire: dim until the write travels
    if (wireK > 0) {
      g.save();
      g.globalAlpha *= Math.min(1, wireK * 2) * fade;
      const pts = [];
      for (let i = 0; i <= 16; i++) pts.push(arcPt(WIRE_A, WIRE_B, WIRE_H, i / 16));
      wline(g, pts.map((p) => [p[0], p[1]]), 1.8, ON_INK);
      g.restore();
    }
  }

  SC['ch09-bitband'] = {
    dur: 5.0,
    width: 390,
    label: '一个人拨下位带别名区的开关，一个写沿导线飞进外设寄存器，对应的那一位被原子地翻转。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let flipK = 0, wireK = 0, bitK = 0, saidK = 0;
      const chin = P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] });
      if (T < 0) {
        pose = mix(pose, chin, pulse(t, 5.5, 2, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        const ws = T < 3.2 ? walkSeg(T, 0, 0.6, HOME, AT) : walkSeg(T, 3.2, 3.9, AT, HOME);
        x = ws.x;
        gait = T >= 3.2 ? { ph: -ws.ph, amp: ws.amp, stride: ws.stride } : ws;
        const reach = E.soft(seg(T, 0.6, 1.0)) * (1 - E.soft(seg(T, 1.5, 1.8)));
        const cheer = E.back(seg(T, 1.9, 2.3)) * (1 - E.soft(seg(T, 2.8, 3.1)));
        pose = mix(pose, P({ hF: lp([SW[FLIP], SW_Y], x, 0, 1), hB: [-4, -54], head: [9, -114], chest: [3, -90] }), reach);
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
        flipK = E.soft(seg(T, 0.75, 1.0)) * fade;
        wireK = seg(T, 1.1, 1.7) * fade;
        bitK = E.back(seg(T, 1.7, 2.0)) * fade;
        saidK = seg(T, 2.0, 2.2) * (1 - seg(T, 3.0, 3.2));
      }
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });

      machine(g, flipK, wireK, bitK, S.on ? 1 : 1);
      fig(g, pose, x, 0, { wave: S.wave, wt: S.wt });
      // the write travels down the wire as a dot
      const flyK = seg(T, 1.1, 1.7);
      if (flyK > 0 && flyK < 1) {
        const p = arcPt(WIRE_A, WIRE_B, WIRE_H, E.soft(flyK));
        circle(g, p[0], p[1], 3.5);
        inkFill(g, GREEN_ON, 1.2, ON_INK);
      }
      sparks(g, ODR.x + 6 + CELL_W / 2, CELL_Y - 4, seg(T, 1.7, 2.3), 10, 5, ON_INK);
      bubble(g, x - 10, -130, '原子改一位', saidK, { tail: 16, size: 9 });
    },
  };
})();
