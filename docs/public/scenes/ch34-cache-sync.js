// ch34-cache-sync: a DMA robot writes a fresh value onto the memory board
// while the CPU's sticky note (its cache line) still shows the old one —
// the note is torn off (invalidate) and a fresh copy flies in from memory.
// Every second play runs the other direction: the CPU pens a new note but
// nobody cleaned it to memory — the robot reads a stale value until the
// note's copy flies over (clean). Companion to
// docs/v4-platforms/34-multicore-cache.md (TX clean / RX invalidate and the
// 32 B line rules live on the chapter's static plate). Site-only: EPUB and
// print keep the static hand-drawn plate.
//
// Both figures stand still the whole scene (no walks → no skate/pop class),
// and every value the viewer reads is deterministic in T. The copy travels
// as a chip flying along an arc — the hand-off pattern from craft.md.
// Load after stick.js. Use as <stick-scene scene="ch34-cache-sync" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, pill, circle, words, tickBadge, arcPt } = R;

  const GREEN = '#3f9d4f', GREEN_INK = '#1a7f37', RED = '#c2543f', AMBER = '#b8860b', GREY = '#8a8578';
  const WALL = { x: -226, y: -132, w: 104, h: 78 };       // CPU 的便签墙（cache 行）
  const STICKY = { x: -190, y: -104, w: 44, h: 26 };
  const MEM = { x: -6, y: -138, w: 116, h: 84 };          // 主存公告板
  const CELL = { x: 2, y: -108, w: 60, h: 26 };
  const BOT_X = -30;                                       // DMA 机器人站位（格子在手前）
  const CPU_X = -172;                                      // CPU 全程站墙前
  const CHIP_A = [CELL.x + 8, CELL.y + 13];                // 内存格 → 便签（RX 回抄）
  const CHIP_B = [STICKY.x + STICKY.w - 6, STICKY.y + 13]; // 便签 → 内存格（TX clean）

  function wallBoard(g, noteVal, tornK, fresh, fade) {
    ln(g, WALL.x + 22, WALL.y + WALL.h, WALL.x + 10, 0, 2.2);
    ln(g, WALL.x + WALL.w - 22, WALL.y + WALL.h, WALL.x + WALL.w - 10, 0, 2.2);
    rr(g, WALL.x, WALL.y, WALL.w, WALL.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, 'cache 行', WALL.x + 14, WALL.y + 14, 8.5, C.ink, 'left');
    words(g, WALL.x + 14, WALL.y + 28, 60, 5);
    // 便签：invalidate 时撕下（下滑淡出），重抄时带新值弹回
    rr(g, STICKY.x, STICKY.y - tornK * 26, STICKY.w, STICKY.h, 3);
    g.save();
    g.globalAlpha *= Math.max(0, 1 - tornK) * fade;
    inkFill(g, fresh ? '#dafbe1' : '#fde68a', 1.4, fresh ? GREEN_INK : AMBER);
    text(g, noteVal, STICKY.x + STICKY.w / 2, STICKY.y + 17, 10, C.ink, 'center');
    g.restore();
  }

  function memBoard(g, memVal, fresh, fade) {
    ln(g, MEM.x + 20, MEM.y + MEM.h, MEM.x + 8, 0, 2.2);
    ln(g, MEM.x + MEM.w - 20, MEM.y + MEM.h, MEM.x + MEM.w - 8, 0, 2.2);
    rr(g, MEM.x, MEM.y, MEM.w, MEM.h, 6);
    inkFill(g, C.paper, 1.7);
    text(g, '内存', MEM.x + 14, MEM.y + 14, 8.5, C.ink, 'left');
    words(g, MEM.x + 14, MEM.y + 28, 56, 6);
    rr(g, CELL.x, CELL.y, CELL.w, CELL.h, 3);
    g.save();
    g.globalAlpha *= fade;
    inkFill(g, fresh ? '#dafbe1' : C.paper, 1.4, fresh ? GREEN_INK : C.muted);
    text(g, memVal, CELL.x + CELL.w / 2, CELL.y + 17, 10, fresh ? GREEN_INK : C.ink, 'center');
    g.restore();
  }

  function chipFly(g, from, to, k, val, fade) {
    if (k <= 0 || k >= 1) return;
    const p = arcPt(from, to, 40, E.soft(k));
    g.save();
    g.globalAlpha *= fade;
    rr(g, p[0] - 17, p[1] - 11, 34, 20, 3);
    inkFill(g, '#fde68a', 1.3, AMBER);
    text(g, val, p[0], p[1] + 3.5, 9, C.ink, 'center');
    g.restore();
  }

  SC['ch34-cache-sync'] = {
    dur: 7.0,
    width: 580,
    label: 'DMA 机器人把新值写进内存，CPU 便签上的还是旧值——把便签撕掉重新抄一份才对；反方向则是先把便签誊回内存。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const tx = S.n % 2 === 1;                 // 第二次播放：TX（clean）方向
      const B = tx
        ? { penT: 0.85, staleT: 1.55, sayT: 1.8, flyT: 2.5, doneT: 2.9, tickT: 3.8, cheerT: 4.3 }
        : { penT: 0.85, staleT: 1.5, sayT: 1.75, peelT: 2.5, flyT: 3.0, doneT: 3.35, tickT: 3.8, cheerT: 4.3 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let noteVal = '0x55', memVal = '0x55';
      let tornK = 0, fresh = false, saidK = 0, botSaidK = 0, cheer = 0, chin = 0;
      let tagK = 0, tickK = 0, penK = 0;

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        // 两次书写的落笔与回退（fade 时回 idle 值）
        penK = seg(T, B.penT, B.penT + 0.3) * (1 - seg(T, this.dur - 0.5, this.dur));
        if (!tx) {
          // RX：机器人先写内存
          memVal = penK > 0.5 ? '0x9C' : '0x55';
          fresh = memVal === '0x9C';
          tornK = seg(T, B.peelT, B.peelT + 0.3) * (1 - E.back(seg(T, B.doneT, B.doneT + 0.3)));
          fresh = fresh || T >= B.doneT + 0.15;             // 重抄后便签带新值
          noteVal = T >= B.doneT + 0.15 && T < this.dur - 0.4 ? '0x9C' : '0x55';
          saidK = seg(T, B.sayT, B.sayT + 0.2) * (1 - seg(T, B.peelT - 0.15, B.peelT));
          tagK = seg(T, B.peelT, B.peelT + 0.25) * (1 - seg(T, B.peelT + 0.9, B.peelT + 1.15));
        } else {
          // TX：CPU 先写便签
          noteVal = penK > 0.5 ? '0x9C' : '0x55';
          botSaidK = seg(T, B.sayT, B.sayT + 0.2) * (1 - seg(T, B.flyT - 0.15, B.flyT));
          tagK = seg(T, B.flyT, B.flyT + 0.25) * (1 - seg(T, B.flyT + 0.9, B.flyT + 1.15));
          memVal = T >= B.doneT + 0.15 && T < this.dur - 0.4 ? '0x9C' : '0x55';
          fresh = memVal === '0x9C';
        }
        // CPU / 机器人姿态：读自己的那份时的前倾与托腮
        // 读便签只前倾不抬手（手到脸高度会穿脸）；撕便签够它的下缘
        const lean = seg(T, B.staleT - 0.1, B.staleT + 0.15) * (1 - seg(T, B.staleT + 0.55, B.staleT + 0.8));
        pose = mix(pose, P({ hF: [16, -64], hB: [-4, -54], head: [9, -113], chest: [4, -90] }), tx ? 0 : lean);
        const peelReach = !tx ? E.soft(seg(T, B.peelT - 0.2, B.peelT)) * (1 - E.soft(seg(T, B.peelT + 0.25, B.peelT + 0.5))) : 0;
        pose = mix(pose, P({ hF: lp([STICKY.x + STICKY.w / 2, STICKY.y + STICKY.h - 2], CPU_X, 0, 1), hB: [-4, -54] }), peelReach);
        chin = seg(T, B.staleT - 0.1, B.staleT + 0.15) * (1 - seg(T, B.staleT + 0.5, B.staleT + 0.75));
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] }), tx ? chin : 0);
        saidK = tx ? 0 : seg(T, B.sayT, B.sayT + 0.2) * (1 - seg(T, B.peelT - 0.15, B.peelT));
        botSaidK = tx ? seg(T, B.sayT, B.sayT + 0.2) * (1 - seg(T, B.flyT - 0.15, B.flyT)) : 0;
        cheer = E.soft(seg(T, B.cheerT, B.cheerT + 0.3)) * (1 - E.soft(seg(T, B.cheerT + 0.7, B.cheerT + 1.0)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
      }

      const state = !tx
        ? (tornK > 0.2 ? 'invalidate' : fresh ? '已重抄' : '待机')
        : (noteVal === '0x9C' && T < B.doneT ? 'dirty' : memVal === '0x9C' ? '已誊回' : '待机');
      wallBoard(g, noteVal, tornK, fresh && !tx ? T >= B.doneT + 0.15 : fresh, S.on ? 1 : 1);
      memBoard(g, memVal, fresh && tx ? T >= B.doneT + 0.15 : !tx && memVal === '0x9C', S.on ? 1 : 1);
      // DMA robot: reaches the memory cell to read/pen
      const botReach = !tx
        ? E.soft(seg(T, B.penT - 0.15, B.penT)) * (1 - E.soft(seg(T, B.penT + 0.3, B.penT + 0.5)))
        : E.soft(seg(T, B.staleT - 0.1, B.staleT)) * (1 - E.soft(seg(T, B.staleT + 0.35, B.staleT + 0.55)));
      const botPose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t + 1.3);
      const botP = mix(botPose, P({ hF: lp([CELL.x + 8, CELL.y + 13], BOT_X, 0, 1), hB: [-4, -54], head: [8, -114] }), botReach);
      fig(g, botP, BOT_X, 0, { sx: 1, ink: '#d97757', far: '#e8b7a3', bot: { col: '#d97757', dark: '#a8553a', glow: botReach > 0.3 ? 1 : 0.25, blink: pulse(t, 4.3, 1.2, 0.15) > 0.5, happy: tickK > 0.5 } });
      text(g, 'DMA', BOT_X, -18, 8.5, '#a8553a', 'center');
      fig(g, pose, CPU_X, 0, { sx: 1, wave: S.wave, wt: S.wt });
      // the copy flies (RX: memory → note; TX: note → memory)
      if (!tx) chipFly(g, CHIP_A, CHIP_B, seg(T, B.flyT, B.flyT + 0.5), '0x9C', S.on ? 1 : 1);
      else chipFly(g, CHIP_B, CHIP_A, seg(T, B.flyT, B.flyT + 0.5), '0x9C', S.on ? 1 : 1);
      if (tagK > 0 && T >= 0) {
        g.save();
        g.globalAlpha *= Math.min(1, tagK);
        pill(g, -70, -40, tx ? 'clean' : 'invalidate', tx ? '#dafbe1' : '#fde68a', C.ink, 9);
        g.restore();
      }
      if (saidK > 0) bubble(g, CPU_X + 14, -142, '旧值！', saidK, { tail: 14, size: 9 });
      if (botSaidK > 0) bubble(g, BOT_X + 16, -142, '旧值！', botSaidK, { tail: 14, size: 9 });
      if (tickK > 0 && T >= 0) tickBadge(g, 34, -46, tickK, 9, '#dafbe1', GREEN_INK);
      if (cheer > 0.4 && T >= 0) sparks(g, CPU_X, -142, cheer, 9, 5, GREEN);
    },
  };
})();
