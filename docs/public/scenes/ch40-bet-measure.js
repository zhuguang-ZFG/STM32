// ch40-bet-measure: the lab method in one loop — write the bet on the
// record board first (10 blinks ≈ 8 s), step right to the LED rig and
// measure with the stopwatch, step back to the 实测 column and write what
// the meter actually said, then reconcile. Every second play bets 6 s and
// measures 9.2 s — the mismatch is not a failure: the delta gets its own
// note, because a wrong bet focuses attention (the chapter's own words).
// Companion to docs/v6-labs-projects/40-lab-method-instruments.md.
// Site-only: EPUB and print keep the static plates.
// Deterministic in T; walks ≥110 u/s; the figure faces what it works on.
// Load after stick.js. Use as <stick-scene scene="ch40-bet-measure" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, circle, tickBadge } = R;

  const GREEN = '#3f9d4f', GREEN_INK = '#1a7f37', AMBER = '#b8860b', RED = '#c2543f';
  const BOARD = { x: -210, y: -140, w: 180, h: 86 };
  const BET = { cx: -170, y: -104 };
  const ACT = { cx: -110, y: -100 };
  const LED = { cx: -58, cy: -96 };
  const WATCH = { cx: -28, cy: -94, r: 22 };
  const A1 = -175, A2 = -85;                                // idle 即 A1

  // 时间线（秒）：bet 写押注 → 走到 LED 按按钮（灯闪/秒表扫）→ 转身写实测
  // → 走回 A1 对账（tick/差值/cheer）。
  function beats(wrong) {
    return wrong
      ? { betT: 0.15, flyBet: 0.5, walkT: 0.9, pressT: 1.75, blinkT: 1.9, sweepT: 1.9, showT: 3.15,
          actT: 3.3, flyAct: 3.65, walkBackT: 3.8, tickT: 4.15, deltaT: 4.2, sayT: 4.25, cheerT: 4.4 }
      : { betT: 0.15, flyBet: 0.5, walkT: 0.9, pressT: 1.75, blinkT: 1.9, sweepT: 1.9, showT: 3.15,
          actT: 3.3, flyAct: 3.65, walkBackT: 3.8, tickT: 4.15, cheerT: 4.3 };
  }

  function boardFace(g, betText, betK, actK, actText, wrong, fade) {
    ln(g, BOARD.x + 24, BOARD.y + BOARD.h, BOARD.x + 12, 0, 2.2);
    ln(g, BOARD.x + BOARD.w - 24, BOARD.y + BOARD.h, BOARD.x + BOARD.w - 12, 0, 2.2);
    rr(g, BOARD.x, BOARD.y, BOARD.w, BOARD.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, '押注', BET.cx - 26, BOARD.y + 16, 8.5, C.ink, 'left');
    text(g, '实测', ACT.cx - 22, BOARD.y + 16, 8.5, C.ink, 'left');
    ln(g, BOARD.x + 10, BOARD.y + 24, BOARD.x + BOARD.w - 10, BOARD.y + 24, 1.2, C.muted);
    rr(g, BET.cx - 22, BET.y - 13, 44, 26, 3);
    g.save();
    g.globalAlpha *= betK * fade;
    inkFill(g, '#fde68a', 1.4, AMBER);
    text(g, betText, BET.cx, BET.y + 4, 8, C.ink, 'center');
    g.restore();
    if (actK > 0) {
      g.save();
      g.globalAlpha *= Math.min(1, actK) * fade;
      text(g, actText, ACT.cx, ACT.y + 4, 9, GREEN_INK, 'center');
      ln(g, ACT.cx - 20, ACT.y + 14, ACT.cx + 20, ACT.y + 14, 1.2, GREEN);
      g.restore();
    }
    if (wrong && actK > 0.5) {
      g.save();
      g.globalAlpha *= Math.min(1, actK) * fade;
      text(g, '差 3.2 s', ACT.cx, ACT.y + 26, 7.5, AMBER, 'center');
      g.restore();
    }
  }

  function ledRig(g, blinkK, pressK, fade) {
    circle(g, LED.cx, LED.cy, 9);
    inkFill(g, blinkK > 0 ? '#dafbe1' : C.paper, 1.5, blinkK > 0 ? GREEN_INK : C.muted);
    text(g, 'LED ×10', LED.cx, LED.cy - 16, 8, C.ink, 'center');
    rr(g, LED.cx - 14, LED.cy + 16, 28, 14, 3);
    inkFill(g, pressK > 0 ? '#dafbe1' : C.paper, 1.3, pressK > 0 ? GREEN_INK : C.muted);
    text(g, '按钮', LED.cx, LED.cy + 25, 7, C.muted, 'center');
  }

  function stopwatch(g, sweepK, showT, fade) {
    circle(g, WATCH.cx, WATCH.cy, WATCH.r);
    inkFill(g, C.paper, 1.8);
    for (let i = 0; i < 12; i++) {
      const a = (i * Math.PI * 2) / 12;
      ln(g, WATCH.cx + Math.cos(a) * (WATCH.r - 5), WATCH.cy + Math.sin(a) * (WATCH.r - 5),
        WATCH.cx + Math.cos(a) * (WATCH.r - 9), WATCH.cy + Math.sin(a) * (WATCH.r - 9), 1.2, C.muted);
    }
    const a = -Math.PI / 2 + sweepK * Math.PI * 2;
    ln(g, WATCH.cx, WATCH.cy, WATCH.cx + Math.cos(a) * (WATCH.r - 12), WATCH.cy + Math.sin(a) * (WATCH.r - 12), 2.2, RED);
    if (showT > 0) {
      g.save();
      g.globalAlpha *= Math.min(1, showT) * fade;
      text(g, '9.2 s', WATCH.cx, WATCH.cy - WATCH.r - 8, 9.5, C.ink, 'center');
      g.restore();
    }
    text(g, '秒表', WATCH.cx, WATCH.cy + WATCH.r + 12, 7.5, C.muted, 'center');
  }

  SC['ch40-bet-measure'] = {
    dur: 6.0,
    width: 560,
    label: '先在记录板押注栏写下猜测，右侧 LED 台按按钮用秒表实测，回到实测栏写下读数对账——押错了就另标差值，押错最好。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const wrong = S.n % 2 === 1;
      const betText = wrong ? '10 次 ≈ 6 s' : '10 次 ≈ 8 s';
      const B = beats(wrong);
      let x = A1, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let sx = 1;
      let betK = 0, actK = 0, blinkK = 0, sweepK = 0, showT = 0, deltaK = 0, saidK = 0, cheer = 0;
      let press = 0;

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        // walks：A1→A2（去测量）与 A2→A1（回写实测），均 ≥110 u/s
        const w2 = walkSeg(T, B.walkT, B.walkT + 0.8, A1, A2);
        const w3 = walkSeg(T, B.walkBackT, B.walkBackT + 0.8, A2, A1);
        if (T >= B.walkT && T < B.walkT + 0.8) { x = w2.x; sx = 1; gait = w2; }
        else if (T >= B.walkBackT && T < B.walkBackT + 0.8) { x = w3.x; sx = -1; gait = w3; }
        else if (T >= B.walkT + 0.8 && T < B.walkBackT) { x = A2; sx = 1; }
        else { x = A1; sx = T >= B.actT && T < B.walkBackT ? -1 : 1; }
        // beats
        betK = E.back(seg(T, B.betT, B.betT + 0.3));
        press = E.soft(seg(T, B.pressT, B.pressT + 0.2)) * (1 - E.soft(seg(T, B.pressT + 0.5, B.pressT + 0.75)));
        blinkK = (T >= B.blinkT && T < B.blinkT + 1.4 && Math.sin((T - B.blinkT) * Math.PI * 2 / 0.16) > 0) ? 1 : 0;
        sweepK = E.io(seg(T, B.sweepT, B.sweepT + 1.25));
        showT = seg(T, B.showT, B.showT + 0.25) * (1 - seg(T, B.flyAct + 0.3, B.flyAct + 0.6));
        actK = seg(T, B.actT + 0.15, B.actT + 0.45);
        deltaK = wrong ? seg(T, B.deltaT, B.deltaT + 0.25) * (1 - seg(T, B.walkBackT - 0.1, B.walkBackT + 0.15)) : 0;
        saidK = wrong ? seg(T, B.sayT, B.sayT + 0.2) * (1 - seg(T, B.sayT + 0.55, B.sayT + 0.8)) : 0;
        cheer = E.soft(seg(T, B.cheerT, B.cheerT + 0.3)) * (1 - E.soft(seg(T, B.cheerT + 0.55, B.cheerT + 0.85)));
        // 写押注（面向右，dx 5）与写实测（面向左，dx 25）；按按钮（面向右，dx 27）
        const writeBet = E.soft(seg(T, B.betT, B.betT + 0.3)) * (1 - E.soft(seg(T, B.flyBet, B.flyBet + 0.25)));
        const writeAct = E.soft(seg(T, B.actT, B.actT + 0.3)) * (1 - E.soft(seg(T, B.flyAct, B.flyAct + 0.25)));
        const pressReach = E.soft(seg(T, B.pressT - 0.25, B.pressT)) * (1 - E.soft(seg(T, B.pressT + 0.25, B.pressT + 0.5)));
        pose = mix(pose, P({ hF: lp([BET.cx, BET.y], x, 0, sxWrite(BET.cx, x)), hB: [-4, -54], head: [8, -113], chest: [4, -90] }), writeBet);
        pose = mix(pose, P({ hF: lp([ACT.cx, ACT.y], x, 0, sxWrite(ACT.cx, x)), hB: [-4, -54], head: [8, -113], chest: [4, -90] }), writeAct);
        pose = mix(pose, P({ hF: lp([LED.cx, LED.cy + 6], x, 0, sxWrite(LED.cx, x)), hB: [-4, -54], head: [8, -113] }), pressReach);
        // 本帧面向：与正在进行的动作一致（写哪边面向哪边）
        if (writeAct > 0.05) sx = ACT.cx < x ? -1 : 1;
        else if (writeBet > 0.05) sx = BET.cx < x ? -1 : 1;
        else if (pressReach > 0.05) sx = LED.cx < x ? -1 : 1;
        else if (T >= B.walkBackT + 0.8 + 0.15) sx = 1;   // 到家转回正面
      }

      boardFace(g, betText, betK, actK, '9.2 s', wrong, S.on ? 1 : 1);
      ledRig(g, blinkK, press, S.on ? 1 : 1);
      stopwatch(g, sweepK, showT, S.on ? 1 : 1);
      fig(g, pose, x, 0, { sx, wave: S.wave, wt: S.wt });
      if (saidK > 0) bubble(g, x + 14 * (sx >= 0 ? 1 : -1), -142, '押错最好', saidK, { tail: 14, size: 9 });
      if (actK > 0.5 && T >= 0) tickBadge(g, ACT.cx + 34, ACT.y + 4, Math.min(1, actK * 1.4), 8, wrong ? '#fdeecd' : '#dafbe1', wrong ? AMBER : GREEN_INK);
      if (cheer > 0.4 && T >= 0) sparks(g, x, -140, cheer, 9, 5, GREEN);

      // 本帧面向：与正在进行的动作一致（写哪边面向哪边）
      function sxWrite(targetX, figX) { return targetX >= figX ? 1 : -1; }
    },
  };
})();
