// ch45-triage: the symptom-to-chapter hand-off in one glance — the figure
// holds a symptom card (「乱码/丢字节」), steps to the triage rack, slots it
// into the 串口 row and the row's chapter tag pops (ch13); the second card
// (「HSE 不起振」) goes to the 时钟启动 row (ch08). The rack rows and chapter
// tags are the chapter's own 8 现象域 table. Companion to
// docs/v7-delivery/45-troubleshooting-handbook.md. Site-only: EPUB and
// print keep the static plates.
// Deterministic in T; one stand at the rack (rows within vertical reach).
// Load after stick.js. Use as <stick-scene scene="ch45-triage" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, pill, circle, tickBadge, arcPt } = R;

  const GREEN = '#3f9d4f', GREEN_INK = '#1a7f37', AMBER = '#b8860b';
  const RACK = { x: -180, y: -140, w: 200, h: 100 };
  // 8 现象域行：y 位置 + 现象域名 + 指向章
  const ROWS = [
    ['供电复位', 'ch18'],
    ['下载调试', 'ch10'],
    ['时钟启动', 'ch08'],
    ['串口', 'ch13'],
    ['总线', 'ch16'],
    ['RTOS', 'ch22'],
    ['运动', 'ch36'],
    ['网络无线', 'ch32'],
  ];
  const ROW_H = 11, ROW_Y0 = RACK.y + 13;
  const CARDS = [
    { text: '乱码/丢字节', row: 3 },     // 串口
    { text: 'HSE 不起振', row: 2 },      // 时钟启动
  ];
  const AT = -172;   // idle 即架前

  function rowY(i) { return ROW_Y0 + i * ROW_H + ROW_H / 2; }

  function rack(g, hiRow, hiK, tagK, fade) {
    rr(g, RACK.x, RACK.y, RACK.w, RACK.h, 5);
    inkFill(g, C.paper, 1.7);
    text(g, '分诊表 · 8 现象域', RACK.x + 14, RACK.y + 11, 8, C.ink, 'left');
    ROWS.forEach(([name, chap], i) => {
      const y = rowY(i);
      const hi = i === hiRow ? hiK : 0;
      if (hi > 0) {
        g.save();
        g.globalAlpha *= 0.35 * hi * fade;
        rr(g, RACK.x + 8, y - ROW_H / 2 + 1, RACK.w - 16, ROW_H - 2, 2);
        inkFill(g, '#fde68a', 1, AMBER);
        g.restore();
      }
      text(g, name, RACK.x + 14, y + 3, 7.5, hi > 0.5 ? AMBER : C.ink, 'left');
      // 指向章 chip
      if (hi > 0.4) {
        g.save();
        g.globalAlpha *= Math.min(1, hi) * fade;
        pill(g, RACK.x + RACK.w - 34, y, chap, hi, '#dafbe1', C.ink, 7.5);
        g.restore();
      } else {
        text(g, chap, RACK.x + RACK.w - 34, y + 3, 7, C.muted, 'center');
      }
    });
  }

  SC['ch45-triage'] = {
    dur: 6.4,
    width: 540,
    label: '拿着症状卡走到分诊表：乱码/丢字节插进串口行，指向 ch13；HSE 不起振插进时钟启动行，指向 ch08——先对现象，再查第一处边界。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const st = (S.st = S.st || { card: 0 });
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let sx = 1;
      let hiRow = -1, hiK = 0, tagK = 0, saidK = 0, cheer = 0, cardInHand = 0, cardAt = 0;

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        // 卡 1（串口）飞行 0.5–0.9、tag 0.95；卡 2（时钟）飞行 1.9–2.3、tag 2.35
        const fly1 = seg(T, 0.5, 0.9);
        const fly2 = seg(T, 1.9, 2.3);
        const tag1 = seg(T, 0.95, 1.2) * (1 - seg(T, 2.6, 2.85));
        const tag2 = seg(T, 2.35, 2.6) * fade;
        hiRow = fly1 > 0 ? 3 : fly2 > 0 ? 2 : -1;
        hiK = Math.max(fly1 > 0 ? 1 : 0, fly2 > 0 ? 1 : 0, tag1 > 0 ? 1 : 0, tag2 > 0 ? 1 : 0) * fade;
        tagK = 0;
        saidK = seg(T, 3.0, 3.2) * (1 - seg(T, 3.7, 3.95));
        cheer = E.soft(seg(T, 3.1, 3.4)) * (1 - E.soft(seg(T, 3.75, 4.05)));
        // 掷卡姿态：手向前伸（面向右，架子在前）
        const throwK = Math.max(E.soft(seg(T, 0.4, 0.6)) * (1 - E.soft(seg(T, 0.9, 1.15))),
                                E.soft(seg(T, 1.8, 2.0)) * (1 - E.soft(seg(T, 2.3, 2.55))));
        const throwRow = (T < 1.6) ? 3 : 2;
        pose = mix(pose, P({ hF: lp([RACK.x + 40, rowY(throwRow)], AT, 0, 1), hB: [-4, -54], head: [8, -113], chest: [3, -90] }), throwK);
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
        // 卡 1/卡 2 沿弧线飞入行
        if (fly1 > 0 && fly1 < 1) {
          const p = arcPt([AT + 20, -100], [RACK.x + 52, rowY(3)], 34, E.soft(fly1));
          g.save();
          g.globalAlpha *= 1 - fly1 * 0.15;
          rr(g, p[0] - 18, p[1] - 8, 36, 15, 3);
          inkFill(g, '#fde68a', 1.3, AMBER);
          text(g, CARDS[0].text, p[0], p[1] + 3, 6.5, C.ink, 'center');
          g.restore();
        }
        if (fly2 > 0 && fly2 < 1) {
          const p = arcPt([AT + 20, -100], [RACK.x + 52, rowY(2)], 34, E.soft(fly2));
          g.save();
          g.globalAlpha *= 1 - fly2 * 0.15;
          rr(g, p[0] - 18, p[1] - 8, 36, 15, 3);
          inkFill(g, '#fde68a', 1.3, AMBER);
          text(g, CARDS[1].text, p[0], p[1] + 3, 6.5, C.ink, 'center');
          g.restore();
        }
      }
      // walking gait applied after every mix（本场景无步行，保持站立呼吸）
      pose = breathe(pose, t);
      rack(g, hiRow, hiK, tagK, S.on ? 1 : 1);
      // 手里的卡（第一段：走向架子前拿着第一张）
      if (T >= 0 && cardInHand > 0 && hiRow >= 0) {
        const ctext = CARDS[hiRow === 3 ? 0 : 1].text;
        g.save();
        g.globalAlpha *= S.on ? 1 : 1;
        rr(g, AT + 14, -96, 40, 18, 3);
        inkFill(g, '#fde68a', 1.4, AMBER);
        text(g, ctext, AT + 34, -83, 7, C.ink, 'center');
        g.restore();
      }
      // 已插入的卡贴在行上
      fig(g, pose, AT, 0, { sx, wave: S.wave, wt: S.wt });
      if (saidK > 0) bubble(g, AT + 16, -140, '一次只改一处', saidK, { tail: 14, size: 9 });
      if (cheer > 0.4 && T >= 0) sparks(g, AT, -142, cheer, 9, 5, GREEN);
    },
  };
})();
