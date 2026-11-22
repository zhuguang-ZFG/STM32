// ch36-hbridge-gates: a figure at the TB6612 driver board pulls STBY up,
// flips IN1/IN2 and the motor spins CW; swaps the pair and it spins CCW;
// pulls STBY back down and the board falls asleep (待机). Every second play
// forgets STBY first — the board stays 待机 and nothing turns until the
// lever comes up. Companion to docs/v5-motion/36-motor-driver-power.md
// (the five-row truth table lives on the chapter's static plate). Site-only:
// EPUB and print keep the static hand-drawn plate.
//
// Everything the viewer reads (speed, direction, state pill) is a
// deterministic function of T — contact-sheet freezes and motion runs must
// agree with the live animation. Only the blade angle integrates.
// Load after stick.js. Use as <stick-scene scene="ch36-hbridge-gates" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, pill, arrow, circle, words } = R;

  const GREEN = '#3f9d4f', RED = '#c2543f', GREY = '#8a8578';
  // Fixed layout, world units: ground y = 0, up is negative, x = 0 centre.
  const BOX = { x: -250, y: -130, w: 175, h: 100 };
  const LEVER = { x: -196, mid: -77 };                          // 站位一：STBY 大闸
  const IN1 = { x: -118, y: -92 };                              // 站位二：IN 对（同列）
  const IN2 = { x: -118, y: -66 };
  const MOTOR = { cx: 115, cy: -74, r: 22 };
  const ARROW_Y = -26;
  const PILL = { x: 115, y: -118 };
  const HOME = -272, A1 = -215, A2 = -150;

  // Timeline beats per variant (seconds into the action).
  function beats(forget) {
    return forget
      ? { in1T: 1.85, chinT: 2.2, sayT: 2.4, stbT: 3.9, cwIn: 4.2, cheerT: 5.0, offT: 5.6, homeT: 5.75 }
      : { stbT: 0.8, in1T: 2.15, cwIn: 2.4, revT: 3.35, cheerT: 3.9, offT: 5.35, homeT: 4.6 };
  }
  // Walk segments: [t0, t1, x0, x1] — the figure always faces its walk direction.
  function walks(forget) {
    return forget
      ? [[0, 1.8, HOME, A2], [2.9, 3.85, A2, A1], [5.75, 6.3, A1, HOME]]
      : [[0, 0.55, HOME, A1], [1.15, 2.1, A1, A2], [4.6, 6.4, A2, HOME]];
  }

  function board(g, stby, k1, k2) {
    ln(g, BOX.x + 26, BOX.y + BOX.h, BOX.x + 12, 0, 2.2);
    ln(g, BOX.x + BOX.w - 26, BOX.y + BOX.h, BOX.x + BOX.w - 12, 0, 2.2);
    rr(g, BOX.x, BOX.y, BOX.w, BOX.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, 'TB6612', BOX.x + 14, BOX.y + 16, 9, C.ink, 'left');
    words(g, BOX.x + 14, BOX.y + 30, 56, 4);
    circle(g, BOX.x + BOX.w - 16, BOX.y + 16, 4);
    inkFill(g, stby > 0.5 ? GREEN : C.paper, 1.3, stby > 0.5 ? GREEN : C.muted);
    text(g, 'STBY', LEVER.x + 12, BOX.y + 58, 8, C.ink, 'left');
    ln(g, LEVER.x, LEVER.mid + 22, LEVER.x, LEVER.mid - 2, 1.6, C.muted);
    ln(g, LEVER.x, LEVER.mid + 20, LEVER.x + (stby > 0.5 ? 5 : -5), LEVER.mid - 20, 2.6, stby > 0.5 ? GREEN : RED);
    circle(g, LEVER.x, LEVER.mid + 20, 3.5);
    inkFill(g, C.paper, 1.4, C.muted);
    toggle(g, IN1.x, IN1.y, k1, 'IN1');
    toggle(g, IN2.x, IN2.y, k2, 'IN2');
    ln(g, IN1.x, IN1.y + 14, IN2.x, IN2.y - 2, 1.2, C.muted);
  }

  function toggle(g, x, y, k, name) {
    const on = k > 0.5;
    text(g, name, x + 9, y - 6, 7.5, C.ink, 'left');
    rr(g, x - 4, y + 2, 8, 13, 2);
    inkFill(g, C.paper, 1.3);
    ln(g, x, y + 4, x - 5 + 10 * k, y + 13 - 12 * k, 2.2, on ? GREEN : C.ink);
    text(g, on ? 'H' : 'L', x - 9, y + 8, 7, on ? GREEN : C.muted, 'right');
  }

  function motor(g, ang, spd, fade) {
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
    if (Math.abs(spd) > 0.25) {
      const a = spd > 0 ? 1 : -1;
      g.save();
      g.globalAlpha *= Math.min(1, Math.abs(spd) / 1.2) * fade;
      arrow(g, [[MOTOR.cx - 26 * a, ARROW_Y], [MOTOR.cx + 26 * a, ARROW_Y]], { lw: 2, col: spd > 0 ? GREEN : RED });
      g.restore();
    }
  }

  SC['ch36-hbridge-gates'] = {
    dur: 7.4,
    width: 560,
    label: '一个人在 TB6612 驱动板上拉起 STBY、拨 IN1/IN2，电机正转；对调两个开关电机反转；拉回 STBY 板子回到待机。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const forget = S.n % 2 === 1;
      const st = (S.st = S.st || { fanA: 0 });
      const B = beats(forget);
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let stby = 0, k1 = 0, k2 = 0, saidK = 0, cheer = 0, chin = 0, spd = 0;
      let sx = 1;

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.8, 2.2, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        // 走位：永远面向行走方向（sx 跟随段方向 snap，不做 ph 翻转）
        for (const [t0, t1, x0, x1] of walks(forget)) {
          if (T >= t0 && T < t1) {
            const w = walkSeg(T, t0, t1, x0, x1);
            x = w.x;
            sx = x1 > x0 ? 1 : -1;
            gait = w;
            break;
          }
          if (T >= t1) {
            x = x1;
            sx = x1 > x0 ? 1 : -1;
          }
        }
        // inputs
        stby = seg(T, B.stbT, B.stbT + 0.3) * (1 - seg(T, B.offT, B.offT + 0.25));
        k1 = seg(T, B.in1T, B.in1T + 0.2) * (1 - seg(T, B.offT, B.offT + 0.25));
        k2 = forget ? 0 : seg(T, B.revT, B.revT + 0.2) * (1 - seg(T, B.offT, B.offT + 0.25));
        // deterministic fan speed
        const alive = forget ? seg(T, B.stbT, B.stbT + 0.3) : 1 - seg(T, B.offT, B.offT + 0.35);
        const wCW = E.soft(seg(T, B.cwIn, B.cwIn + 0.5)) * (1 - (forget ? 0 : E.soft(seg(T, B.revT, B.revT + 0.5))));
        const wCCW = forget ? 0 : E.soft(seg(T, B.revT, B.revT + 0.5)) * (1 - E.soft(seg(T, B.offT, B.offT + 0.5)));
        spd = 1.9 * (wCW - wCCW) * alive * fade;
        // reaches（全部在面朝方向的前方）
        const reachStby = E.soft(seg(T, B.stbT - 0.3, B.stbT)) * (1 - E.soft(seg(T, B.stbT + 0.3, B.stbT + 0.5)));
        const offReach = (1 - E.soft(seg(T, B.offT - 0.15, B.offT))) * E.soft(seg(T, B.offT - 0.3, B.offT - 0.1));
        const stbyReachK = Math.max(reachStby, offReach);
        const reachIn1 = E.soft(seg(T, B.in1T - 0.25, B.in1T)) * (1 - E.soft(seg(T, (B.revT || 9e9) - 0.15, B.revT || 9e9)));
        const reachIn2 = forget ? 0 : E.soft(seg(T, B.revT - 0.15, B.revT)) * (1 - E.soft(seg(T, B.revT + 0.2, B.revT + 0.45)));
        const stbyPt = [LEVER.x - 5 + 10 * stby, LEVER.mid + 20 - 40 * E.soft(stby)];
        pose = mix(pose, P({ hF: lp(stbyPt, x, 0, sx), hB: [-4, -54] }), stbyReachK);
        pose = mix(pose, P({ hF: lp([IN1.x, IN1.y + 6], x, 0, sx), hB: [-4, -54], head: [8, -114] }), reachIn1);
        pose = mix(pose, P({ hF: lp([IN2.x, IN2.y + 6], x, 0, sx), hB: [-4, -54] }), reachIn2);
        chin = forget ? seg(T, B.chinT, B.chinT + 0.25) * (1 - seg(T, B.stbT - 0.3, B.stbT)) : 0;
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] }), chin);
        saidK = forget ? seg(T, B.sayT, B.sayT + 0.2) * (1 - seg(T, B.stbT - 0.2, B.stbT)) : 0;
        cheer = E.soft(seg(T, B.cheerT, B.cheerT + 0.35)) * (1 - E.soft(seg(T, B.cheerT + 0.7, B.cheerT + 1.0)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
      }

      // walking gait applied after every mix (feet plant per stride)
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });
      // face right again once the last walk has settled (idle faces right)
      const lastT1 = walks(forget).at(-1)[1];
      if (T >= lastT1 + 0.15) sx = 1;
      // blade angle integrates the deterministic speed (visual only)
      st.fanA = (st.fanA || 0) + spd * 0.09;
      const state = spd > 0.45 ? '正转' : spd < -0.45 ? '反转' : '待机';
      const stateCol = state === '正转' ? GREEN : state === '反转' ? RED : GREY;
      const stateT = spd > 0.45 || spd < -0.45 ? (spd > 0 ? B.cwIn : B.revT) : B.stbT;
      const stateK = S.on && T >= 0 ? E.back(seg(T, stateT + 0.1, stateT + 0.35)) * (1 - seg(T, B.offT + 0.05, B.offT + 0.3)) : 0;

      board(g, stby, k1, k2);
      motor(g, st.fanA, spd, S.on ? 1 : 1);
      fig(g, pose, x, 0, { sx, wave: S.wave, wt: S.wt });
      if (stateK > 0 && T >= 0) {
        const sk = Math.min(1, stateK);
        g.save();
        g.globalAlpha *= sk;
        pill(g, PILL.x, PILL.y + (1 - sk) * 6, state, stateCol === GREY ? '#efe9db' : stateCol === GREEN ? '#dafbe1' : '#ffebe9', C.ink, 9);
        g.restore();
      }
      if (saidK > 0) bubble(g, x - 4, -138, '怎么不转？', saidK, { tail: 15, size: 9 });
      if (cheer > 0.4 && T > 0) sparks(g, MOTOR.cx, MOTOR.cy - 32, cheer, 9, 5, GREEN);
    },
  };
})();
