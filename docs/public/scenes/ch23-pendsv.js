// ch23-pendsv: the PendSV clerk swaps context frames — the running task's
// frame comes off the CPU slot back to its TCB hook, the next task's frame
// goes onto the slot. Swaps direction every play (S.n), so the loop always
// ends in a state the idle can redraw exactly.
// Companion to docs/v3-rtos/23-context-switch-porting.md (六、十一条语义步骤).
// Site-only: EPUB and print keep the static hand-drawn plate.
// Load after stick.js. Use as <stick-scene scene="ch23-pendsv" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, sparks, bubble, tickBadge, words, arcPt, circle } = R;

  const GREEN_ON = '#4caf50', ON_INK = '#1a7f37', INK_D = '#1f4680';
  // Fixed layout, world units: ground y = 0, up is negative, x = 0 centre.
  const SLOT = { x: -32, y: -62, w: 64, h: 42 };          // the CPU socket
  const LAMP = [SLOT.x + SLOT.w - 12, SLOT.y - 12];
  const SHELF_Y = -124;                                    // hook board height (clears the walking head)
  const AX = -122, BX = 122;                               // hook x centres
  const FW = 46, FH = 34;                                  // context frame size
  const HOME = -166, AT = -72;

  // where a labelled frame rests: in the slot, or hanging on its hook
  const slotPos = () => [0, SLOT.y - FH / 2 - 1];
  const hookPos = (hx) => [hx, SHELF_Y - FH / 2 - 2];

  function stage(g) {
    // CPU socket with a lamp and an insertion slot
    ln(g, SLOT.x + 16, SLOT.y + SLOT.h, SLOT.x + 8, 0, 2.2);
    ln(g, SLOT.x + SLOT.w - 16, SLOT.y + SLOT.h, SLOT.x + SLOT.w - 8, 0, 2.2);
    rr(g, SLOT.x, SLOT.y, SLOT.w, SLOT.h, 5);
    inkFill(g, C.paper, 1.7);
    text(g, 'CPU', 0, SLOT.y + SLOT.h / 2 + 3, 9, C.ink, 'center');
    ln(g, SLOT.x + 8, SLOT.y, SLOT.x + SLOT.w - 8, SLOT.y, 2.4, C.ink);
    // hook boards (the TCB side)
    [AX, BX].forEach((hx) => {
      ln(g, hx - 16, SHELF_Y + 6, hx - 22, 0, 2.2);
      ln(g, hx + 16, SHELF_Y + 6, hx + 22, 0, 2.2);
      rr(g, hx - 29, SHELF_Y, 58, 6, 2);
      inkFill(g, C.wood, 1.5);
      circle(g, hx, SHELF_Y + 4, 2.5);
      inkFill(g, C.paper, 1.1, C.ink);
    });
  }

  function frame(g, pos, label) {
    g.save();
    g.translate(pos[0], pos[1]);
    rr(g, -FW / 2, -FH / 2, FW, FH, 3);
    inkFill(g, C.paper, 1.5, INK_D);
    text(g, label, -FW / 2 + 9, -FH / 2 + 13, 10, INK_D, 'center');
    words(g, -FW / 2 + 8, -FH / 2 + 24, FW - 16, label === 'A' ? 3 : 7);
    g.restore();
  }

  function lampDraw(g) {
    circle(g, LAMP[0], LAMP[1], 4.5);
    inkFill(g, GREEN_ON, 1.4, ON_INK);
    g.save();
    g.globalAlpha *= 0.25;
    circle(g, LAMP[0], LAMP[1], 9);
    inkFill(g, GREEN_ON, 0.8, GREEN_ON);
    g.restore();
  }

  SC['ch23-pendsv'] = {
    dur: 4.8,
    width: 390,
    label: '管理员把正在运行任务的现场帧从 CPU 插槽取下挂回它的挂钩，再把下一个任务的现场帧挂上 CPU——PendSV 换现场。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const running = S.n % 2 === 0 ? 'A' : 'B';          // frame in the slot at rest
      const waiting = running === 'A' ? 'B' : 'A';        // frame on its hook
      const runHook = running === 'A' ? AX : BX;          // where running goes back
      const waitHook = waiting === 'A' ? AX : BX;         // where waiting starts
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let saidK = 0, tickK = 0;
      const chin = P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] });
      if (T < 0) {
        pose = mix(pose, chin, pulse(t, 5.5, 2, 2.2));
      } else {
        const ws = T < 3.9 ? walkSeg(T, 0, 0.55, HOME, AT) : walkSeg(T, 3.9, 4.55, AT, HOME);
        x = ws.x;
        gait = T >= 3.9 ? { ph: -ws.ph, amp: ws.amp, stride: ws.stride } : ws;
        const flickL = E.soft(seg(T, 0.55, 0.9)) * (1 - E.soft(seg(T, 1.3, 1.6)));
        const flickR = E.soft(seg(T, 1.5, 1.85)) * (1 - E.soft(seg(T, 2.3, 2.6)));
        pose = mix(pose, P({ hF: [38, -102], hB: [-4, -54], head: [9, -114] }), flickL);
        pose = mix(pose, P({ hF: [40, -100], hB: [-4, -54], head: [10, -116] }), flickR);
        tickK = seg(T, 2.2, 2.5) * (1 - seg(T, 4.35, 4.65));
        saidK = seg(T, 2.3, 2.5) * (1 - seg(T, 3.4, 3.6));
      }
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });

      // frame flights: slot -> its hook, then hook -> slot
      const fly1 = seg(T, 0.6, 1.35);
      const fly2 = seg(T, 1.55, 2.3);
      const p1 = fly1 > 0 && fly1 < 1 ? arcPt(slotPos(), hookPos(runHook), 46, E.soft(fly1)) : null;
      const p2 = fly2 > 0 && fly2 < 1 ? arcPt(hookPos(waitHook), slotPos(), 46, E.soft(fly2)) : null;

      stage(g);
      lampDraw(g);
      fig(g, pose, x, 0, { wave: S.wave, wt: S.wt });
      if (p1) frame(g, p1, running);
      else {
        if (fly1 >= 1) ln(g, runHook, SHELF_Y + 4, runHook, SHELF_Y - 9, 1.6, C.ink);
        frame(g, fly1 >= 1 ? hookPos(runHook) : slotPos(), running);
      }
      if (p2) frame(g, p2, waiting);
      else {
        if (fly2 < 1) ln(g, waitHook, SHELF_Y + 4, waitHook, SHELF_Y - 9, 1.6, C.ink);
        frame(g, fly2 >= 1 ? slotPos() : hookPos(waitHook), waiting);
      }
      sparks(g, 0, SLOT.y - 12, seg(T, 2.25, 2.8), 12, 5, ON_INK);
      tickBadge(g, SLOT.x + SLOT.w - 2, SLOT.y - 16, tickK, 7, '#dafbe1', ON_INK);
      bubble(g, x + 14, -126, waiting + ' 上 CPU', saidK, { tail: 16, size: 9 });
    },
  };
})();
