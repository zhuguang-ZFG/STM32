// ch42-delivery-pack: the delivery crate in one loop — five pieces sit on
// the packing bench (重建脚本 / ELF+map / 配置 / 接线记录 / 已知限制),
// the figure walks the bench and flies each one into the crate, the lid
// closes, the 验收 stamp lands. Every second play the shelf only has four
// pieces — the fifth (已知限制) is missing and fetched before the stamp can
// land: the "not done" list is half of what delivery means. Companion to
// docs/v6-labs-projects/42-project-delivery-acceptance.md (the five-piece
// union list lives in the chapter). Site-only: EPUB and print keep the
// static plate.
// Deterministic in T; walks ≥110 u/s; the figure faces what it picks.
// Load after stick.js. Use as <stick-scene scene="ch42-delivery-pack" play="view" no-font>.
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, bubble, circle, tickBadge, arcPt } = R;

  const GREEN = '#3f9d4f', GREEN_INK = '#1a7f37', AMBER = '#b8860b', RED = '#c2543f', WOOD = '#ecdfc8';
  const BENCH = { x: -240, y: -60, w: 180, h: 8 };
  const ITEMS = [
    { cx: -218, label: '重建脚本' },
    { cx: -184, label: 'ELF+map' },
    { cx: -150, label: '配置' },
    { cx: -116, label: '接线记录' },
    { cx: -82, label: '已知限制' },
  ];
  const CRATE = { x: -30, y: -88, w: 92, h: 52 };
  const CRATE_IN = [-10, -62];
  const S1 = -201, S2 = -167, S3 = -133, S4 = -99;   // 每个站位服务一件（物品都在面前）
  const HOME = S1;

  // 调度表：拾取 pickT（站位 i）、飞行 pickT+0.3→+0.7、落箱 tick。
  // 缺件变体：第五件 popT 弹回台上、拾取顺延；盖/章/欢呼顺延。
  function schedule(missing) {
    return {
      pickT: missing ? [0.15, 0.8, 1.5, 2.2, 4.7] : [0.15, 0.8, 1.5, 2.2, 2.9],
      flyT: missing ? [0.45, 1.2, 1.95, 2.7, 4.95] : [0.45, 1.2, 1.95, 2.7, 3.3],
      popT: missing ? 3.95 : 9e9,
      lidT: missing ? 5.5 : 3.35,
      stampT: missing ? 6.0 : 3.7,
      cheerT: missing ? 6.5 : 4.8,
      homeT: missing ? 6.6 : 4.9,
    };
  }

  function bench(g, presentK, fade) {
    rr(g, BENCH.x, BENCH.y, BENCH.w, BENCH.h, 3);
    inkFill(g, WOOD, 1.7);
    ln(g, BENCH.x + 12, BENCH.y + BENCH.h, BENCH.x + 6, 0, 2.2);
    ln(g, BENCH.x + BENCH.w - 12, BENCH.y + BENCH.h, BENCH.x + BENCH.w - 6, 0, 2.2);
    ITEMS.forEach((it, i) => {
      const k = presentK[i];
      if (k <= 0) return;
      g.save();
      g.globalAlpha *= Math.min(1, k) * fade;
      rr(g, it.cx - 16, BENCH.y - 20, 32, 18, 3);
      inkFill(g, C.paper, 1.3, C.muted);
      text(g, it.label, it.cx, BENCH.y - 26, 6.5, C.ink, 'center');
      g.restore();
    });
  }

  function crate(g, lidK, fade) {
    ln(g, CRATE.x + 14, CRATE.y + CRATE.h, CRATE.x + 8, 0, 2.2);
    ln(g, CRATE.x + CRATE.w - 14, CRATE.y + CRATE.h, CRATE.x + CRATE.w - 8, 0, 2.2);
    rr(g, CRATE.x, CRATE.y, CRATE.w, CRATE.h, 4);
    inkFill(g, WOOD, 1.8);
    text(g, '交付包', CRATE.x + CRATE.w / 2, CRATE.y + CRATE.h - 12, 9, C.ink, 'center');
    g.save();
    g.translate(CRATE.x + 6, CRATE.y);
    g.rotate(-1.15 * lidK);
    rr(g, 0, -10, CRATE.w - 12, 10, 3);
    inkFill(g, WOOD, 1.6);
    g.restore();
  }

  SC['ch42-delivery-pack'] = {
    dur: 8.0,
    width: 560,
    label: '五件交付物逐件飞进交付箱，盖子合上，验收章落下；缺一件（已知限制）就去取回来再盖章。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      const missing = S.n % 2 === 1;
      const B = schedule(missing);
      const st = (S.st = S.st || {});
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let sx = 1;
      let saidK = 0, chin = 0, cheer = 0;

      // 每件可见度：起飞前在台上；缺件变体第五件 popT 后弹回、飞走后消失
      const presentK = ITEMS.map((_, i) => {
        const f = B.flyT[i];
        if (missing && i === 4) {
          if (T < B.popT) return 0;
          if (T < B.popT + 0.25) return E.back(seg(T, B.popT, B.popT + 0.25));
          return 1 - seg(T, f, f + 0.4);
        }
        return 1 - seg(T, f, f + 0.4);
      });

      // 走位段（sx 永远面向行走方向；起点与终点都是 HOME）
      const segs = missing
        ? [[1.25, 1.9, S1, S2], [2.75, 3.1, S2, S3], [B.homeT, Math.min(B.homeT + 1.25, this.dur - 0.05), S3, S1]]
        : [[0.6, 1.25, S1, S2], [2.0, 2.35, S2, S3], [2.85, 3.2, S3, S4],
           [B.homeT, Math.min(B.homeT + 1.2, this.dur - 0.05), S4, S1]];

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116] }), pulse(t, 5.6, 2.1, 2.2));
      } else {
        const fade = 1 - seg(T, this.dur - 0.45, this.dur);
        for (const [t0, t1, x0, x1] of segs) {
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
        if (T >= (missing ? 6.7 : 5.0) + 0.15) sx = 1;   // 到家转回正面（idle 朝向）
        // 拾取 reach：每件都在站位面前（dx ≤ 20）
        for (let i = 0; i < 5; i++) {
          const t0 = B.pickT[i];
          const near = Math.abs(ITEMS[i].cx - x) < 40 && T >= t0 - 0.3 && T < t0 + 0.12;
          if (!near) continue;
          const rk = E.soft(seg(T, t0 - 0.3, t0)) * (1 - E.soft(seg(T, t0 + 0.12, t0 + 0.4)));
          const psx = ITEMS[i].cx < x ? -1 : 1;   // 拾取面向物品
          pose = mix(pose, P({ hF: lp([ITEMS[i].cx, BENCH.y - 10], x, 0, psx), hB: [-4, -54], head: [8, -113], chest: [4, -90] }), rk);
          if (T >= t0 - 0.05 && T < t0 + 0.12) sx = psx;
        }
        // 缺件困惑（站到第五件的位置发现它不在）
        chin = missing ? seg(T, B.sayT - 0.05, B.sayT + 0.15) * (1 - seg(T, B.sayT + 0.5, B.sayT + 0.75)) : 0;
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] }), chin);
        saidK = missing ? seg(T, B.sayT, B.sayT + 0.2) * (1 - seg(T, B.sayT + 0.5, B.sayT + 0.75)) : 0;
        cheer = E.soft(seg(T, B.cheerT, B.cheerT + 0.3)) * (1 - E.soft(seg(T, B.cheerT + 0.55, B.cheerT + 0.85)));
        pose = mix(pose, P({ hF: [14, -132], hB: [-10, -130], head: [3, -118] }), cheer);
      }
      // walking gait applied after every mix (feet plant per stride)
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });

      bench(g, presentK, S.on ? 1 : 1);
      crate(g, 1 - seg(T, B.lidT, B.lidT + 0.35), S.on ? 1 : 1);
      // 逐件飞行（台面 → 箱内）
      if (T >= 0) {
        ITEMS.forEach((it, i) => {
          const f = B.flyT[i];
          if (missing && i === 4 && T < B.popT + 0.3) return;
          const k = seg(T, f, f + 0.4);
          if (k > 0 && k < 1) {
            const p = arcPt([it.cx, BENCH.y - 12], CRATE_IN, 42, E.soft(k));
            g.save();
            g.globalAlpha *= 1 - k * 0.2;
            rr(g, p[0] - 14, p[1] - 8, 28, 14, 3);
            inkFill(g, '#fde68a', 1.2, AMBER);
            g.restore();
          }
        });
      }
      fig(g, pose, x, 0, { sx, wave: S.wave, wt: S.wt });
      // 计数 ticks 落在箱沿
      if (T >= 0) {
        ITEMS.forEach((_, i) => {
          const f = B.flyT[i];
          if (missing && i === 4 && T < B.popT + 0.8) return;
          if (T >= f + 0.4) {
            tickBadge(g, CRATE.x + 10 + i * 15, CRATE.y - 6, seg(T, f + 0.4, f + 0.6), 6.5, '#dafbe1', GREEN_INK);
          }
        });
      }
      if (saidK > 0) bubble(g, x + 14, -142, '缺一件', saidK, { tail: 14, size: 9 });
      const stampK = E.in(seg(T, B.stampT, B.stampT + 0.22)) * (1 - E.soft(seg(T, B.stampT + 0.9, B.stampT + 1.2)));
      if (stampK > 0 && T >= 0) {
        g.save();
        g.globalAlpha *= Math.min(1, stampK);
        g.translate(CRATE.x + CRATE.w / 2, CRATE.y + 14);
        g.rotate(-0.16);
        const sc = 1 + 0.9 * (1 - stampK);
        g.scale(sc, sc);
        rr(g, -34, -14, 68, 28, 4);
        inkFill(g, '#ffebe9', 2, RED);
        text(g, '验收', 0, 5, 14, RED, 'center');
        g.restore();
        if (stampK > 0.85) sparks(g, CRATE.x + CRATE.w / 2, CRATE.y + 4, seg(T, B.stampT + 0.2, B.stampT + 0.7), 10, 6, RED);
      }
      if (cheer > 0.4 && T >= 0) sparks(g, x, -140, cheer, 8, 5, GREEN);
    },
  };
})();
