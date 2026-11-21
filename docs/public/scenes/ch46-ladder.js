// ch46-ladder: the L0–L5 ladder as evidence placement — the figure stands
// centred in front of the ladder and throws one evidence token per level;
// each token lands on its step and the step lights up green; at L5 the
// 交付 flag plants. Every second play tries to skip: the throw toward L4
// happens before L3 — the L4 step stays grey with a 「证据缺口：L3」
// bubble — then L3 lands, and L4/L5 light. Companion to
// docs/v7-delivery/46-resources-roadmap-open-source.md (the L0–L5 table
// and the static ladder plate live in the chapter). Site-only: EPUB and
// print keep the static plates.
// Deterministic in T; one stand, zero walks (no skate/reach-short class).
// Load after stick.js. Use as <stick-scene scene="ch46-ladder" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, pill, circle, tickBadge, arcPt } = R;

  const GREEN = '#3f9d4f', GREEN_INK = '#1a7f37', AMBER = '#b8860b', RED = '#c2543f', GREY = '#8a8578';
  const STEPS = [
    { lvl: 'L0', name: '起步', x: -225, ev: '构建+烧录' },
    { lvl: 'L1', name: '驱动', x: -186, ev: '波形对账' },
    { lvl: 'L2', name: '数据', x: -147, ev: '时序+缓冲' },
    { lvl: 'L3', name: '可靠', x: -108, ev: '失败复现' },
    { lvl: 'L4', name: '系统', x: -69, ev: '边界+取舍' },
    { lvl: 'L5', name: '交付', x: -30, ev: '交付五件套' },
  ];
  const STEP_W = 34, BASE_Y = -50;
  const FIG_X = -128;                       // 中心站位，全程不动

  // 调度：每次投掷的节拍（手势 rise→落，token 飞行在 rise 中段）
  // 缺件变体：L4 的投掷发生在 L3 之前（被卡），L3 补上后 L4/L5 顺延
  function schedule(skip) {
    return skip
      ? { throwT: [0.2, 0.9, 1.6, 2.3, 3.6, 4.3],   // L0 L1 L2 [L4×] L3 L4
          order: [0, 1, 2, -1, 3, 4],               // -1 = 被 L3 缺口卡住的 L4 尝试
          flagT: 5.6, cheerT: 5.8 }
      : { throwT: [0.2, 0.9, 1.6, 2.3, 3.0, 3.7],
          order: [0, 1, 2, 3, 4, 5],
          flagT: 4.2, cheerT: 4.4 };
  }

  function ladder(g, litK, fade) {
    STEPS.forEach((s, i) => {
      const h = 14 + i * 11;
      const x = s.x - STEP_W / 2;
      const lit = litK[i];
      rr(g, x, BASE_Y - h, STEP_W, h, 3);
      inkFill(g, lit > 0.5 ? '#dafbe1' : C.paper, 1.6, lit > 0.5 ? GREEN : C.muted);
      text(g, s.lvl, s.x, BASE_Y - h + 10, 9, lit > 0.5 ? GREEN_INK : C.ink, 'center');
      text(g, s.name, s.x, BASE_Y - h + 21, 7, lit > 0.5 ? GREEN_INK : C.muted, 'center');
    });
    text(g, '级别按证据划分，不按章数', -128, -16, 7.5, C.muted, 'center');
  }

  SC['ch46-ladder'] = {
    dur: 6.6,
    width: 560,
    label: '证据逐级投上台阶，L0 到 L5 逐级点亮；跳级投掷会在缺证据的那级被卡住——补上 L3 再前进。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const skip = S.n % 2 === 1;
      const B = schedule(skip);
      const st = (S.st = S.st || {});
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let sx = -1;                              // idle 面向近端台阶（左）
      let saidK = 0, cheer = 0, throwK = 0, throwDir = -1;
      let litK = [0, 0, 0, 0, 0, 0];
      let flight = null;                        // {from, to, k, si}

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
        litK[0] = 0;
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        // 每次投掷的窗口与方向
        B.throwT.forEach((t0, i) => {
          const si = B.order[i];
          const dir = si >= 0 ? (STEPS[si].x < FIG_X ? -1 : 1) : 1;   // 被卡的尝试朝 L4（右）
          const rise = E.soft(seg(T, t0, t0 + 0.25));
          const fall = 1 - E.soft(seg(T, t0 + 0.5, t0 + 0.75));
          const k = rise * fall;
          if (k > throwK) {
            throwK = k;
            throwDir = dir;
            if (si >= 0) {
              // token 在手势中段飞出
              const fk = seg(T, t0 + 0.15, t0 + 0.55);
              if (fk > 0 && fk < 1) {
                flight = { from: [FIG_X + throwDir * 22, -108], to: [STEPS[si].x, BASE_Y - (14 + si * 11) - 6], k: E.soft(fk), si };
              }
            }
          }
        });
        // 缺口卡住：skip 变体的第四次投掷（si=-1）后，L3 的投掷补上
        saidK = skip ? seg(T, B.throwT[3] + 0.3, B.throwT[3] + 0.5) * (1 - seg(T, B.throwT[4], B.throwT[4] + 0.2)) : 0;
        if (skip && saidK > 0) {
          bubble(g, FIG_X + 16 * (STEPS[3].x < FIG_X ? -1 : 1), -142, '证据缺口：L3', saidK, { tail: 14, size: 9 });
        }
        // 点亮：token 落地（fly 结束）时弹入
        B.throwT.forEach((t0, i) => {
          const si = B.order[i];
          if (si < 0) return;                    // 被卡的尝试不点亮
          const land = t0 + 0.55;
          litK[si] = Math.max(litK[si], E.back(seg(T, land, land + 0.25)));
        });
        cheer = E.soft(seg(T, B.cheerT, B.cheerT + 0.3)) * (1 - E.soft(seg(T, B.cheerT + 0.55, B.cheerT + 0.85)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
        // 投掷手势：手朝目标方向抬起
        const throwPose = P({ hF: lp([FIG_X + throwDir * 26, -112], FIG_X, 0, throwDir), hB: [-4, -54], head: [8 * throwDir, -114] }), tk = throwK;
        pose = mix(pose, throwPose, tk);
        void tk;
      }
      sx = throwK > 0.05 ? throwDir : (T >= B.cheerT ? 1 : (litK[5] > 0.5 ? 1 : sx));

      ladder(g, litK, S.on ? 1 : 1);
      if (flight) {
        const p = flight;
        g.save();
        g.globalAlpha *= 1 - p.k * 0.15;
        circle(g, p.from[0] + (p.to[0] - p.from[0]) * p.k, 0 + arcY(p.from[1], p.to[1], p.k), 4.5);
        inkFill(g, '#fde68a', 1.3, AMBER);
        g.restore();
      }

      // L5 交付旗
      if (litK[5] > 0.5) {
        const s5 = STEPS[5];
        ln(g, s5.x, BASE_Y - (14 + 5 * 11), s5.x, BASE_Y - (14 + 5 * 11) - 18, 2, C.ink);
        pill(g, s5.x + 16, BASE_Y - (14 + 5 * 11) - 14, '交付', litK[5], '#dafbe1', GREEN_INK, 8);
      }
      fig(g, pose, FIG_X, 0, { sx, wave: S.wave, wt: S.wt });
      if (cheer > 0.4 && T >= 0) sparks(g, FIG_X, -142, cheer, 9, 5, GREEN);

      function arcY(y0, y1, k) {
        const base = y0 + (y1 - y0) * k;
        return base - Math.sin(k * Math.PI) * 30;
      }
    },
  };
})();
