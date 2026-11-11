// Motion recipes for web overlay layers. Each recipe builds its DOM inside `root` (a transparent box the size of
// the overlay) and starts its animations at virtual time 0; the capture then steps the clock frame by frame.
// Libraries: anime.js (MIT), rough.js (MIT), rough-notation (MIT), canvas-confetti (ISC), d3-geo + d3-array (ISC), topojson-client (ISC),
// world-atlas land outlines (ISC; Natural Earth, public domain); for their recipes only, matter-js (MIT), Zdog (MIT) and
// MathJax (Apache-2.0) — see vendor/*.LICENSE and THIRD_PARTY_NOTICES.md.
(() => {
  const { animate, stagger, createSpring, svg, createTimeline } = anime;
  const NS = 'http://www.w3.org/2000/svg';
  const fonts = {
    hand: '"Hannotate SC", "HanziPen SC", "Noto Sans CJK SC", "PingFang SC", sans-serif',
    sans: '"PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Helvetica Neue", sans-serif',
    serif: '"Songti SC", "Noto Serif CJK SC", serif',
  };
  const family = (value) => fonts[value] || value || fonts.sans;
  const spring = (stiffness = 180, damping = 14, mass = 1) => createSpring({ stiffness, damping, mass });

  function svgLayer(root, width, height) {
    const layer = document.createElementNS(NS, 'svg');
    layer.setAttribute('width', width); layer.setAttribute('height', height);
    layer.setAttribute('viewBox', `0 0 ${width} ${height}`);
    layer.style.position = 'absolute'; layer.style.left = '0'; layer.style.top = '0'; layer.style.overflow = 'visible';
    root.appendChild(layer);
    return layer;
  }

  // Draw-on for every path of a rough.js node: stroke-dashoffset from its length to 0, one after another.
  function drawOn(node, start, duration) {
    const paths = [...node.querySelectorAll('path')];
    const lengths = paths.map((path) => path.getTotalLength());
    const total = lengths.reduce((a, b) => a + b, 0) || 1;
    let cursor = start;
    paths.forEach((path, index) => {
      const share = duration * lengths[index] / total;
      if (path.getAttribute('fill') && path.getAttribute('fill') !== 'none' && !path.getAttribute('stroke')) {
        path.animate([{ opacity: 0 }, { opacity: 1 }], { delay: cursor, duration: Math.max(60, share), fill: 'both' });
      } else {
        path.style.strokeDasharray = `${lengths[index]}`;
        path.animate([{ strokeDashoffset: lengths[index] }, { strokeDashoffset: 0 }],
                     { delay: cursor, duration: Math.max(40, share), easing: 'cubic-bezier(.45,.05,.4,1)', fill: 'both' });
      }
      cursor += share;
    });
    return cursor;
  }

  const Recipes = {};

  // Headline words arrive like a product site: blurred and low, then sharp and in place, staggered (cal.com feel).
  Recipes.kinetic_title = (root, p, ctx) => {
    const box = document.createElement('div');
    Object.assign(box.style, { position: 'absolute', inset: '0', display: 'flex', flexWrap: 'wrap', alignContent: 'center',
      justifyContent: p.align === 'left' ? 'flex-start' : 'center', gap: `0 ${0.18 * (p.size || 96)}px`,
      fontFamily: family(p.font || 'hand'), fontSize: `${p.size || 96}px`, fontWeight: p.weight || 700, color: p.color || '#1E2733',
      lineHeight: 1.15, letterSpacing: p.tracking || '0' });
    root.appendChild(box);
    const style = p.style || 'blur_up';
    // Words come segmented from Python (jieba + keyword atoms); accents are [start, end) character ranges.
    const parts = ['spring_pop', 'typewriter', 'scramble'].includes(style) ? [...p.text] : (p.words || [p.text]);
    const accented = new Set((p.accents || []).flatMap(([a, b]) => [...Array(b - a).keys()].map((k) => a + k)));
    let offset = 0;
    const spans = [];
    for (const part of parts) {
      const begin = offset;
      offset += part.length;
      if (!part.trim()) continue;
      const span = document.createElement('span');
      span.style.display = 'inline-block';
      [...part].forEach((character, index) => {
        const glyph = document.createElement('span');
        glyph.textContent = character;
        if (accented.has(begin + index)) glyph.style.color = p.accent || '#E9784E';
        span.appendChild(glyph);
      });
      box.appendChild(span);
      spans.push(span);
    }
    // Fit the line(s) inside the box at rest, before any motion: a title that overflows its box is cut off in the film.
    let size = p.size || 96;
    const overflows = () => spans.some((span) => {
      const r = span.getBoundingClientRect();
      return r.left < 1 || r.top < 1 || r.right > ctx.width - 1 || r.bottom > ctx.height - 1;
    });
    for (let i = 0; i < 16 && overflows(); i++) {
      size *= 0.92;
      box.style.fontSize = `${size}px`;
      box.style.gap = `0 ${0.18 * size}px`;
    }
    const delay = p.delay || 0;
    if (style === 'blur_up') {
      animate(spans, { opacity: [0, 1], filter: ['blur(14px)', 'blur(0px)'], translateY: ['0.45em', '0em'],
                       delay: stagger(p.stagger || 70, { start: delay }), duration: 900, ease: 'outExpo' });
    } else if (style === 'spring_pop') {
      animate(spans, { opacity: [0, 1], scale: [0.2, 1], translateY: ['0.3em', '0em'], delay: stagger(p.stagger || 45, { start: delay }),
                       ease: spring(260, 12) });
    } else if (style === 'mask_up') {
      spans.forEach((span) => { const mask = document.createElement('span'); mask.style.display = 'inline-block'; mask.style.overflow = 'hidden';
        span.replaceWith(mask); mask.appendChild(span); });
      animate(spans, { translateY: ['110%', '0%'], delay: stagger(p.stagger || 80, { start: delay }), duration: 700, ease: 'outQuart' });
    } else if (style === 'typewriter') {
      spans.forEach((span, index) => span.animate([{ opacity: 0 }, { opacity: 1 }], { delay: delay + index * (p.stagger || 60), duration: 1, fill: 'both' }));
    } else if (style === 'slam') {
      // Each word lands hard, 1.55x -> 0.94x -> 1x in under 0.3 s (the "砸入" beat), and the frame jolts as it lands.
      spans.forEach((span, index) => {
        const at = delay + index * (p.stagger || 260);
        span.animate([{ transform: 'scale(1.55)', opacity: 0 }, { transform: 'scale(0.94)', opacity: 1, offset: 0.6 }, { transform: 'scale(1)', opacity: 1 }],
                     { delay: at, duration: 290, easing: 'cubic-bezier(.2,.9,.3,1)', fill: 'both' });
        if (p.shake !== false) {
          const k = size / 24;
          box.animate([{ transform: 'translate(0,0)' }, { transform: `translate(${-k}px,${k / 2}px)` }, { transform: `translate(${k * 0.6}px,${-k / 3}px)` },
                       { transform: `translate(${-k / 4}px,${k / 6}px)` }, { transform: 'translate(0,0)' }], { delay: at + 170, duration: 240 });
        }
      });
    } else if (style === 'scramble') {
      // Glyphs flicker through look-alikes and resolve left to right into the line (decoder / terminal feel).
      const glyphs = spans.flatMap((span) => [...span.children]);
      const pool = p.pool ? [...p.pool] : [...new Set([...(p.text || '')].filter((c) => c.trim()))].concat([...'#%&*+=?<>/0123456789']);
      const each = p.stagger || 45, settle = p.duration_ms || 700;
      glyphs.forEach((glyph) => { glyph.dataset.final = glyph.textContent; glyph.dataset.color = glyph.style.color; glyph.style.opacity = 0; });
      const tick = () => {
        const t = performance.now() - delay;
        glyphs.forEach((glyph, index) => {
          if (t < index * each * 0.4) { glyph.style.opacity = 0; return; }
          glyph.style.opacity = 1;
          const done = t >= index * each + settle;
          glyph.textContent = done ? glyph.dataset.final : pool[Math.floor(Math.random() * pool.length)];
          glyph.style.color = done ? glyph.dataset.color : (p.scramble_color || '#8C96A3');
        });
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    } else if (style === 'word_by_word') {
      // One word at a time on the beat; a key word arrives big and shrinks into the line, pushing its neighbours.
      spans.forEach((span, index) => {
        const at = delay + index * (p.stagger || 240);
        span.animate([{ opacity: 0, transform: 'translateY(0.25em)' }, { opacity: 1, transform: 'translateY(0)' }],
                     { delay: at, duration: 220, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'both' });
        if ([...span.children].some((glyph) => glyph.style.color)) {
          span.animate([{ fontSize: '1.45em' }, { fontSize: '1.45em', offset: 0.45 }, { fontSize: '1em' }],
                       { delay: at, duration: 760, easing: 'cubic-bezier(.3,1.35,.5,1)', fill: 'both' });
        }
      });
    }
    if (p.underline) {
      const layer = svgLayer(root, ctx.width, ctx.height);
      const y = Math.min(ctx.height - 6, ctx.height / 2 + 0.62 * size);
      const node = rough.svg(layer).line(ctx.width * 0.12, y, ctx.width * 0.88, y + 4,
        { stroke: p.accent || '#E9784E', strokeWidth: Math.max(4, size / 14), roughness: 1.6, bowing: 2, seed: p.seed || 7 });
      layer.appendChild(node);
      drawOn(node, delay + spans.length * (p.stagger || 70) + 300, 500);
    }
  };

  // A hand-drawn annotation around the overlay box: underline, box, circle, highlight, strike-through, bracket...
  Recipes.rough_annotate = (root, p) => {
    // The mark is drawn around the target with padding and a wobbly stroke: keep the target inset so it stays in the box.
    const inset = p.inset ?? ((p.padding ?? 8) + 2 * (p.stroke_width || 5) + 10);
    const target = document.createElement('div');
    Object.assign(target.style, { position: 'absolute', left: `${inset}px`, top: `${inset}px`, right: `${inset}px`, bottom: `${inset}px` });
    root.appendChild(target);
    const annotation = RoughNotation.annotate(target, { type: p.type || 'circle', color: p.color || '#E9784E',
      strokeWidth: p.stroke_width || 5, padding: p.padding ?? 8, iterations: p.iterations || 2,
      animationDuration: p.duration_ms || 800, brackets: p.brackets || ['left', 'right'], multiline: false });
    setTimeout(() => annotation.show(), p.delay || 0);
  };

  // Sketchy shapes drawn on in order: arrows, curves, boxes, ellipses, brackets, checks, crosses, stars.
  Recipes.sketch_shapes = (root, p, ctx) => {
    const layer = svgLayer(root, ctx.width, ctx.height);
    const pen = rough.svg(layer);
    let cursor = p.delay || 0;
    const each = (p.duration_ms || 900) / Math.max(1, (p.shapes || []).length);
    (p.shapes || []).forEach((shape, index) => {
      const o = { stroke: shape.color || p.color || '#1E2733', strokeWidth: shape.width || p.width || 5, roughness: shape.roughness ?? 1.4,
                  bowing: shape.bowing ?? 1.5, seed: (p.seed || 3) + index, fill: shape.fill, fillStyle: shape.fill_style || 'hachure',
                  hachureGap: shape.hachure_gap || 10, fillWeight: shape.fill_weight || 3 };
      const [x1, y1, x2, y2] = shape.box || [0, 0, ctx.width, ctx.height];
      let node;
      const k = shape.kind;
      if (k === 'arrow' || k === 'line' || k === 'curve_arrow') {
        const [[ax, ay], [bx, by]] = shape.points;
        const bend = k === 'curve_arrow' ? (shape.bend ?? 0.25) : 0;
        const mx = (ax + bx) / 2 - (by - ay) * bend, my = (ay + by) / 2 + (bx - ax) * bend;
        node = document.createElementNS(NS, 'g');
        const shaft = bend ? pen.curve([[ax, ay], [mx, my], [bx, by]], o) : pen.line(ax, ay, bx, by, o);
        node.appendChild(shaft);
        if (k !== 'line') {
          const angle = Math.atan2(by - (bend ? my : ay), bx - (bend ? mx : ax));
          const size = shape.head || 28;
          for (const side of [-1, 1]) {
            const a = angle + Math.PI + side * 0.5;
            node.appendChild(pen.line(bx, by, bx + size * Math.cos(a), by + size * Math.sin(a), o));
          }
        }
      } else if (k === 'rect') node = pen.rectangle(x1, y1, x2 - x1, y2 - y1, o);
      else if (k === 'ellipse' || k === 'circle') node = pen.ellipse((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1, o);
      else if (k === 'polygon') node = pen.polygon(shape.points, o);
      else if (k === 'check') node = pen.linearPath([[x1, (y1 + y2) / 2], [x1 + (x2 - x1) * 0.4, y2], [x2, y1]], o);
      else if (k === 'cross') { node = document.createElementNS(NS, 'g'); node.appendChild(pen.line(x1, y1, x2, y2, o)); node.appendChild(pen.line(x2, y1, x1, y2, o)); }
      else if (k === 'bracket') node = pen.linearPath([[x1 + 20, y1], [x1, y1], [x1, y2], [x1 + 20, y2]], o);
      else if (k === 'star') {
        const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2, r = Math.min(x2 - x1, y2 - y1) / 2;
        node = pen.polygon([...Array(10)].map((_, i) => { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r;
          return [cx + rr * Math.cos(a), cy + rr * Math.sin(a)]; }), o);
      } else throw new Error('Unknown sketch shape: ' + k);
      layer.appendChild(node);
      cursor = drawOn(node, cursor, shape.duration_ms || each) + (p.gap_ms ?? 60);
      if (shape.flow) {  // marching dashes along the arrow after it is drawn: a flow, a signal, a path taken
        node.querySelectorAll('path').forEach((path) => {
          path.animate([{ strokeDasharray: '14 12', strokeDashoffset: 0 }, { strokeDasharray: '14 12', strokeDashoffset: -52 }],
                       { delay: cursor, duration: 900, iterations: Infinity, easing: 'linear' });
        });
      }
    });
  };

  // Particles: confetti, sparkle stars or hearts bursting from the box centre (deterministic: seeded Math.random).
  Recipes.burst = (root, p, ctx) => {
    const kind = p.kind || 'sparkle';
    const canvas = document.createElement('canvas');
    canvas.width = ctx.width * ctx.scale; canvas.height = ctx.height * ctx.scale;
    Object.assign(canvas.style, { position: 'absolute', inset: '0', width: `${ctx.width}px`, height: `${ctx.height}px` });
    root.appendChild(canvas);
    if (kind === 'confetti') {
      const fire = confetti.create(canvas, { resize: false, useWorker: false });
      setTimeout(() => fire({ particleCount: p.count || 90, spread: p.spread || 80, startVelocity: p.velocity || 38,
        origin: { x: p.origin_x ?? 0.5, y: p.origin_y ?? 0.6 }, colors: p.colors || ['#E9784E', '#F2C14E', '#4FA3A5', '#1E2733'],
        scalar: (p.particle_scale || 1.1) * ctx.scale, ticks: p.ticks || 220, gravity: p.gravity ?? 1, disableForReducedMotion: false }), p.delay || 0);
      return;
    }
    const g = canvas.getContext('2d');
    const count = p.count || 14;
    const colors = p.colors || ['#F2C14E', '#E9784E', '#4FA3A5'];
    const parts = [...Array(count)].map((_, i) => ({ a: (i / count) * Math.PI * 2 + Math.random() * 0.4, v: 0.6 + Math.random() * 0.6,
      s: 0.6 + Math.random() * 0.8, c: colors[i % colors.length], r: Math.random() * Math.PI }));
    const start = p.delay || 0, life = p.life_ms || 900;
    const cx = canvas.width / 2, cy = canvas.height / 2, reach = Math.min(canvas.width, canvas.height) * 0.45;
    const shape = (x, y, size, rotation) => {
      g.save(); g.translate(x, y); g.rotate(rotation); g.beginPath();
      if (kind === 'heart') { g.moveTo(0, size * 0.3); g.bezierCurveTo(size, -size * 0.6, size * 0.4, -size, 0, -size * 0.35);
        g.bezierCurveTo(-size * 0.4, -size, -size, -size * 0.6, 0, size * 0.3); }
      else { for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4, rr = i % 2 ? size * 0.25 : size; g.lineTo(rr * Math.cos(a), rr * Math.sin(a)); } }
      g.closePath(); g.fill(); g.restore();
    };
    const draw = (time) => {
      g.clearRect(0, 0, canvas.width, canvas.height);
      const t = (time - start) / life;
      if (t >= 0 && t <= 1) {
        const ease = 1 - Math.pow(1 - t, 3);
        for (const q of parts) {
          g.globalAlpha = Math.min(1, 4 * (1 - t)); g.fillStyle = q.c;
          shape(cx + Math.cos(q.a) * reach * q.v * ease, cy + Math.sin(q.a) * reach * q.v * ease,
                (p.size || 18) * ctx.scale * q.s * (t < 0.2 ? t / 0.2 : 1 - 0.5 * t), q.r + t * 2);
        }
      }
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  };

  // An odometer: each digit column rolls to its value with a spring, staggered right to left.
  Recipes.number_ticker = (root, p) => {
    const value = Number(p.to), decimals = p.decimals || 0;
    const text = `${p.prefix || ''}${value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${p.suffix || ''}`;
    const row = document.createElement('div');
    Object.assign(row.style, { position: 'absolute', inset: '0', display: 'flex', alignItems: 'center',
      justifyContent: p.align === 'left' ? 'flex-start' : 'center', fontFamily: family(p.font || 'hand'), fontSize: `${p.size || 120}px`,
      fontWeight: p.weight || 800, color: p.color || '#1E2733', fontVariantNumeric: 'tabular-nums', lineHeight: 1 });
    root.appendChild(row);
    const columns = [];
    [...text].forEach((character) => {
      const cell = document.createElement('span');
      Object.assign(cell.style, { display: 'inline-block', height: '1.1em', overflow: 'hidden', position: 'relative' });
      if (/\d/.test(character)) {
        const strip = document.createElement('span');
        Object.assign(strip.style, { display: 'flex', flexDirection: 'column' });
        const turns = p.spins ?? 1;  // full turns of the wheel before it settles
        for (let d = 0; d < 10 * (turns + 1); d++) { const digit = document.createElement('span'); digit.textContent = d % 10; digit.style.height = '1.1em'; strip.appendChild(digit); }
        cell.appendChild(strip); columns.push([strip, Number(character) + 10 * turns]);
      } else { cell.textContent = character; if (p.accent_suffix && !/[\d.,]/.test(character)) cell.style.color = p.accent || '#E9784E'; }
      row.appendChild(cell);
    });
    columns.reverse().forEach(([strip, index], order) => {
      animate(strip, { translateY: ['0em', `${-1.1 * index}em`], delay: (p.delay || 0) + order * (p.stagger || 90), ease: spring(120, 14) });
    });
  };

  // A rough speech bubble or tag that springs out of its anchor with its text.
  Recipes.callout = (root, p, ctx) => {
    const layer = svgLayer(root, ctx.width, ctx.height);
    const pad = 10, tail = p.tail || 'bottom-left';
    const w = ctx.width - 2 * pad, h = ctx.height - 2 * pad - (p.tail ? 30 : 0);
    const o = { stroke: p.stroke || '#1E2733', strokeWidth: p.stroke_width || 4, fill: p.fill || '#FFFFFF', fillStyle: 'solid', roughness: 1.2, seed: p.seed || 5 };
    const group = document.createElementNS(NS, 'g');
    group.appendChild(rough.svg(layer).rectangle(pad, pad, w, h, o));
    if (p.tail) {
      const x = tail.endsWith('right') ? pad + w * 0.75 : pad + w * 0.2;
      group.appendChild(rough.svg(layer).polygon([[x, pad + h - 2], [x + 34, pad + h - 2], [x - 6, pad + h + 30]], o));
    }
    layer.appendChild(group);
    const label = document.createElement('div');
    Object.assign(label.style, { position: 'absolute', left: `${pad}px`, top: `${pad}px`, width: `${w}px`, height: `${h}px`, display: 'flex',
      alignItems: 'center', justifyContent: 'center', textAlign: 'center', fontFamily: family(p.font || 'hand'),
      fontSize: `${p.size || 54}px`, color: p.color || '#1E2733', padding: '0 0.4em', boxSizing: 'border-box', lineHeight: 1.2 });
    label.textContent = p.text || '';
    root.appendChild(label);
    root.style.transformOrigin = tail.endsWith('right') ? '75% 100%' : '20% 100%';
    animate(root, { scale: [0.3, 1], opacity: [0, 1], rotate: [p.tilt ?? -6, 0], delay: p.delay || 0, ease: spring(220, 13) });
  };

  // A hand-drawn ring that is inked to a percentage while its number counts up (rough.js, drawn on like a pen stroke).
  Recipes.progress_ring = (root, p, ctx) => {
    const layer = svgLayer(root, ctx.width, ctx.height), pen = rough.svg(layer);
    const size = Math.min(ctx.width, ctx.height), r = size * 0.36, cx = ctx.width / 2, cy = ctx.height / 2;
    const share = Math.max(0, Math.min(1, (p.value || 0) / (p.max || 100)));
    const track = pen.circle(cx, cy, 2 * r, { stroke: p.track || '#D8D2C4', strokeWidth: size * 0.05, roughness: 1.1, seed: p.seed || 4 });
    layer.appendChild(track);
    const start = -Math.PI / 2, end = start + 2 * Math.PI * Math.max(0.001, share);
    const arc = pen.arc(cx, cy, 2 * r, 2 * r, start, end, false, { stroke: p.color || '#E9784E', strokeWidth: size * 0.075, roughness: 1.3, seed: (p.seed || 4) + 1 });
    layer.appendChild(arc);
    drawOn(track, p.delay || 0, 260);
    drawOn(arc, (p.delay || 0) + 200, p.duration_ms || 1100);
    const label = document.createElement('div');
    Object.assign(label.style, { position: 'absolute', inset: '0', display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: family(p.font || 'hand'), fontWeight: 700, fontSize: `${size * 0.22}px`, color: p.text_color || '#1E2733' });
    root.appendChild(label);
    const counter = { v: 0 };
    animate(counter, { v: p.value || 0, delay: (p.delay || 0) + 200, duration: p.duration_ms || 1100, ease: 'outCubic',
      onUpdate: () => { label.textContent = `${counter.v.toFixed(p.decimals || 0)}${p.suffix ?? '%'}`; } });
  };

  // ---------------------------------------------------------------- 2.0 recipes

  const PALETTE = ['#E9784E', '#4FA3A5', '#F2C14E', '#1E2733', '#8C6BB1', '#6BA368'];
  const ink = (p) => p.ink || '#1E2733';
  function label(root, text, x, y, size, p, align = 'center', color) {
    const node = document.createElement('div');
    node.textContent = text;
    Object.assign(node.style, { position: 'absolute', left: `${x}px`, top: `${y}px`, transform: `translate(${align === 'center' ? '-50%' : align === 'right' ? '-100%' : '0'}, -50%)`,
      fontFamily: family(p.font || 'hand'), fontSize: `${size}px`, color: color || ink(p), whiteSpace: 'nowrap', lineHeight: 1 });
    root.appendChild(node);
    return node;
  }
  const appear = (node, at, duration = 260) => node.animate([{ opacity: 0, transform: `${node.style.transform} translateY(0.3em)` }, { opacity: 1, transform: node.style.transform }],
                                                            { delay: at, duration, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'both' });
  const ease = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));

  // Outline of a shape as N points, evenly spaced along its edge and starting at its top (so shapes morph without twisting).
  function outline(shape, count) {
    const [x1, y1, x2, y2] = shape.box, w = x2 - x1, h = y2 - y1, cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
    const kind = shape.shape || 'circle';
    let d;
    if (kind === 'circle' || kind === 'dot' || kind === 'ellipse') d = `M ${cx} ${y1} A ${w / 2} ${h / 2} 0 1 1 ${cx - 0.01} ${y1} Z`;
    else if (kind === 'rect' || kind === 'card') {
      const r = Math.min(shape.radius ?? Math.min(w, h) * 0.12, w / 2, h / 2);
      d = `M ${cx} ${y1} H ${x2 - r} Q ${x2} ${y1} ${x2} ${y1 + r} V ${y2 - r} Q ${x2} ${y2} ${x2 - r} ${y2} H ${x1 + r} Q ${x1} ${y2} ${x1} ${y2 - r} V ${y1 + r} Q ${x1} ${y1} ${x1 + r} ${y1} Z`;
    } else if (kind === 'star') {
      const pts = [...Array(10)].map((_, i) => { const a = -Math.PI / 2 + i * Math.PI / 5, k = i % 2 ? 0.45 : 1; return [cx + k * w / 2 * Math.cos(a), cy + k * h / 2 * Math.sin(a)]; });
      d = 'M ' + pts.map((q) => q.join(' ')).join(' L ') + ' Z';
    } else if (kind === 'heart') {
      d = `M ${cx} ${y1 + h * 0.28} C ${cx + w * 0.1} ${y1 - h * 0.05}, ${x2 + w * 0.05} ${y1 + h * 0.1}, ${x2 - w * 0.02} ${y1 + h * 0.38} C ${x2 - w * 0.1} ${y1 + h * 0.62}, ${cx + w * 0.2} ${y1 + h * 0.8}, ${cx} ${y2} C ${cx - w * 0.2} ${y1 + h * 0.8}, ${x1 + w * 0.1} ${y1 + h * 0.62}, ${x1 + w * 0.02} ${y1 + h * 0.38} C ${x1 - w * 0.05} ${y1 + h * 0.1}, ${cx - w * 0.1} ${y1 - h * 0.05}, ${cx} ${y1 + h * 0.28} Z`;
    } else if (kind === 'triangle') d = `M ${cx} ${y1} L ${x2} ${y2} L ${x1} ${y2} Z`;
    else if (kind === 'diamond') d = `M ${cx} ${y1} L ${x2} ${cy} L ${cx} ${y2} L ${x1} ${cy} Z`;
    else if (kind === 'arrow') d = `M ${x1 + w * 0.6} ${y1} L ${x2} ${cy} L ${x1 + w * 0.6} ${y2} L ${x1 + w * 0.6} ${cy + h * 0.2} L ${x1} ${cy + h * 0.2} L ${x1} ${cy - h * 0.2} L ${x1 + w * 0.6} ${cy - h * 0.2} Z`;
    else if (kind === 'path') d = shape.d;
    else throw new Error('Unknown morph shape: ' + kind);
    const probe = document.createElementNS(NS, 'path');
    probe.setAttribute('d', d);
    const length = probe.getTotalLength();
    let points = [...Array(count)].map((_, i) => { const q = probe.getPointAtLength(length * i / count); return [q.x, q.y]; });
    const top = points.reduce((best, q, i) => (q[1] < points[best][1] - 0.5 || (Math.abs(q[1] - points[best][1]) <= 0.5 && q[0] < points[best][0]) ? i : best), 0);
    points = points.slice(top).concat(points.slice(0, top));
    // Clockwise in screen space, so every shape winds the same way.
    const area = points.reduce((sum, q, i) => { const r = points[(i + 1) % count]; return sum + q[0] * r[1] - r[0] * q[1]; }, 0);
    return area < 0 ? [points[0]].concat(points.slice(1).reverse()) : points;
  }

  // One shape becomes the next, travelling as it changes (a dot grows into a card, the card into a star...): it
  // stretches along its path first and takes the new form in the second half; colours carry across.
  // shapes: [{shape: circle|dot|rect|card|star|heart|triangle|diamond|arrow|path, box: [x1,y1,x2,y2], fill, stroke, text, hold_ms}]
  Recipes.morph = (root, p, ctx) => {
    const layer = svgLayer(root, ctx.width, ctx.height);
    const count = 120, shapes = p.shapes || [];
    if (shapes.length < 1) throw new Error('morph needs shapes');
    const forms = shapes.map((shape) => outline(shape, count));
    const centres = forms.map((points) => points.reduce((a, q) => [a[0] + q[0] / count, a[1] + q[1] / count], [0, 0]));
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('stroke-width', p.stroke_width || 5); path.setAttribute('stroke-linejoin', 'round');
    layer.appendChild(path);
    const texts = shapes.map((shape) => { if (!shape.text) return null; const [x1, y1, x2, y2] = shape.box;
      const node = label(root, shape.text, (x1 + x2) / 2, (y1 + y2) / 2, shape.text_size || Math.min(x2 - x1, y2 - y1) * 0.3, p, 'center', shape.text_color || '#FFFFFF');
      node.style.opacity = 0; return node; });
    const morphMs = p.morph_ms || 700, start = p.delay || 0;
    const plan = []; let cursor = start;
    shapes.forEach((shape, index) => { plan.push({ index, from: cursor, hold: shape.hold_ms ?? 500 }); cursor += (shape.hold_ms ?? 500) + morphMs; });
    const color = (shape, key, fallback) => shape[key] || p[key] || fallback;
    const draw = () => {
      const now = performance.now();
      let index = 0;
      while (index + 1 < plan.length && now >= plan[index + 1].from) index += 1;
      const stay = plan[index], next = Math.min(index + 1, shapes.length - 1);
      const t = index + 1 < shapes.length ? Math.max(0, Math.min(1, (now - stay.from - stay.hold) / morphMs)) : 0;
      const move = ease(t), form = ease(Math.max(0, (t - 0.3) / 0.7));
      const [ax, ay] = centres[index], [bx, by] = centres[next];
      const cx = ax + (bx - ax) * move, cy = ay + (by - ay) * move;
      const dx = bx - ax, dy = by - ay, distance = Math.hypot(dx, dy) || 1, stretch = 0.28 * Math.sin(Math.PI * t) * Math.min(1, distance / 200);
      const ux = dx / distance, uy = dy / distance;
      const points = forms[index].map((q, i) => {
        const r = forms[next][i];
        let x = (q[0] - ax) + ((r[0] - bx) - (q[0] - ax)) * form, y = (q[1] - ay) + ((r[1] - by) - (q[1] - ay)) * form;
        const along = x * ux + y * uy;
        x += ux * along * stretch; y += uy * along * stretch;
        return [cx + x, cy + y];
      });
      path.setAttribute('d', 'M ' + points.map((q) => `${q[0].toFixed(2)} ${q[1].toFixed(2)}`).join(' L ') + ' Z');
      const mix = (key, fallback) => {
        const [a, b] = [color(shapes[index], key, fallback), color(shapes[next], key, fallback)].map((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));
        return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * form)).join(',')})`;
      };
      path.setAttribute('fill', mix('fill', '#E9784E')); path.setAttribute('stroke', mix('stroke', ink(p)));
      const appearAt = now < start ? 0 : Math.min(1, (now - start) / 220);
      path.setAttribute('opacity', appearAt);
      texts.forEach((node, i) => { if (node) node.style.opacity = i === index && t === 0 && now >= stay.from + 80 ? 1 : i === next && form > 0.85 ? (form - 0.85) / 0.15 : 0; });
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  };

  // Hand-drawn charts that draw themselves: axes first, then the data, then one highlighted fact.
  // kind: bar | line | pie | dots | tally | timeline (see references/motion-catalog.md for fields).
  Recipes.rough_chart = (root, p, ctx) => {
    const layer = svgLayer(root, ctx.width, ctx.height), pen = rough.svg(layer);
    const W = ctx.width, H = ctx.height, kind = p.kind || 'bar', colors = p.colors || PALETTE, size = p.label_size || Math.max(26, Math.min(W, H) * 0.068);
    const o = (extra = {}) => ({ stroke: ink(p), strokeWidth: p.stroke_width || 4, roughness: 1.3, bowing: 1.2, seed: p.seed || 9, ...extra });
    const start = p.delay || 0;
    const left = W * 0.1, right = W * 0.96, top = H * 0.1, bottom = H * (p.labels ? 0.84 : 0.92);
    const values = p.values || [], highlight = p.highlight ?? -1;
    const fmt = (v) => `${p.prefix || ''}${Number(v).toLocaleString('en-US', { maximumFractionDigits: p.decimals || 0 })}${p.suffix || ''}`;
    const count = (node, value, at, duration) => { const c = { v: 0 }; node.textContent = fmt(0);
      animate(c, { v: value, delay: at, duration, ease: 'outCubic', onUpdate: () => { node.textContent = fmt(c.v); } }); };
    if (kind === 'bar' || kind === 'line') {
      const axes = document.createElementNS(NS, 'g');
      axes.appendChild(pen.line(left, bottom, right, bottom, o())); axes.appendChild(pen.line(left, bottom, left, top, o()));
      layer.appendChild(axes);
      let cursor = drawOn(axes, start, 500) + 80;
      const max = p.max || Math.max(...values) * 1.12 || 1, slot = (right - left) / Math.max(1, values.length);
      const yOf = (v) => bottom - (bottom - top) * v / max;
      if (kind === 'bar') {
        values.forEach((value, i) => {
          const x = left + slot * (i + 0.2), w = slot * 0.6, y = yOf(value);
          const bar = document.createElementNS(NS, 'g');
          bar.appendChild(pen.rectangle(x, y, w, bottom - y, o({ fill: colors[(i === highlight ? 0 : (highlight >= 0 ? 3 : i)) % colors.length], fillStyle: 'hachure', hachureGap: 9, fillWeight: 3 })));
          bar.style.transformBox = 'view-box'; bar.style.transformOrigin = `0px ${bottom}px`;
          layer.appendChild(bar);
          const at = cursor + i * (p.stagger || 220);
          bar.animate([{ transform: 'scaleY(0)' }, { transform: 'scaleY(1)' }], { delay: at, duration: 650, easing: 'cubic-bezier(.3,1.25,.5,1)', fill: 'both' });
          const tag = label(root, '', x + w / 2, y - size * 0.8, size, p, 'center', i === highlight ? colors[0] : ink(p));
          appear(tag, at + 200); count(tag, value, at, 800);
          if (p.labels) appear(label(root, p.labels[i], x + w / 2, bottom + size * 0.9, size * 0.9, p), at);
        });
      } else {
        const pts = values.map((value, i) => [left + slot * (i + 0.5), yOf(value)]);
        const line = pen.curve(pts, o({ stroke: colors[0], strokeWidth: (p.stroke_width || 4) * 1.4 }));
        layer.appendChild(line);
        const end = drawOn(line, cursor, p.duration_ms || 1400);
        pts.forEach(([x, y], i) => {
          const at = cursor + (end - cursor) * i / Math.max(1, pts.length - 1);
          const dot = pen.circle(x, y, size * 0.6, o({ fill: i === highlight ? colors[0] : '#FFFFFF', fillStyle: 'solid' }));
          dot.style.transformBox = 'fill-box'; dot.style.transformOrigin = 'center'; layer.appendChild(dot);
          dot.animate([{ transform: 'scale(0)' }, { transform: 'scale(1)' }], { delay: at, duration: 380, easing: 'cubic-bezier(.3,1.6,.5,1)', fill: 'both' });
          if (p.show_values !== false) appear(label(root, fmt(values[i]), x, y - size * 1.1, size * 0.85, p, 'center', i === highlight ? colors[0] : ink(p)), at + 100);
          if (p.labels) appear(label(root, p.labels[i], x, bottom + size * 0.9, size * 0.9, p), at);
        });
      }
    } else if (kind === 'pie') {
      const cx = W / 2, cy = H / 2, r = Math.min(W, H) * 0.36, total = values.reduce((a, b) => a + b, 0) || 1;
      let angle = -Math.PI / 2;
      values.forEach((value, i) => {
        const sweep = 2 * Math.PI * value / total, at = start + i * (p.stagger || 320);
        const slice = pen.arc(cx, cy, 2 * r, 2 * r, angle, angle + sweep, true, o({ fill: colors[i % colors.length], fillStyle: i === highlight ? 'solid' : 'hachure', hachureGap: 8 }));
        slice.style.transformBox = 'view-box'; slice.style.transformOrigin = `${cx}px ${cy}px`; layer.appendChild(slice);
        const pop = i === highlight ? 1.08 : 1;
        slice.animate([{ transform: 'scale(0) rotate(-20deg)' }, { transform: `scale(${pop})` }], { delay: at, duration: 600, easing: 'cubic-bezier(.3,1.3,.5,1)', fill: 'both' });
        const middle = angle + sweep / 2;
        const text = (p.labels ? p.labels[i] + ' ' : '') + (p.show_values === false ? '' : fmt(value));
        appear(label(root, text, cx + Math.cos(middle) * r * 1.28, cy + Math.sin(middle) * r * 1.22, size, p), at + 250);
        angle += sweep;
      });
    } else if (kind === 'dots') {
      const total = p.total || 100, marked = p.marked ?? 0, columns = p.columns || Math.ceil(Math.sqrt(total * W / H));
      const rows = Math.ceil(total / columns), cell = Math.min((right - left) / columns, (bottom - top) / rows), r = cell * 0.32;
      const x0 = (W - cell * columns) / 2 + cell / 2, y0 = (H - cell * rows) / 2 + cell / 2;
      for (let i = 0; i < total; i++) {
        const x = x0 + (i % columns) * cell, y = y0 + Math.floor(i / columns) * cell, on = i < marked;
        const dot = pen.circle(x, y, 2 * r, o({ strokeWidth: 2, fill: on ? colors[0] : '#D8D2C4', fillStyle: on ? 'cross-hatch' : 'solid',
                                                 hachureGap: Math.max(2.5, r * 0.45), fillWeight: Math.max(1, r * 0.18), roughness: 1.4,
                                                 stroke: on ? colors[0] : '#B9B1A1', seed: (p.seed || 9) + i }));
        dot.style.transformBox = 'fill-box'; dot.style.transformOrigin = 'center'; layer.appendChild(dot);
        const at = start + (on ? 400 + i * (p.stagger || 25) : i * 4);
        dot.animate([{ transform: 'scale(0)' }, { transform: 'scale(1)' }], { delay: at, duration: 300, easing: 'cubic-bezier(.3,1.6,.5,1)', fill: 'both' });
      }
    } else if (kind === 'tally') {
      // Counting the Chinese way: every 正 is five strokes, in stroke order (or four bars and a slash with style "bars").
      const total = p.count || 5, groups = Math.ceil(total / 5), g = Math.min((right - left) / Math.max(1, groups) * 0.8, (bottom - top) * 0.8);
      let cursor = start;
      for (let k = 0; k < groups; k++) {
        const x = left + (right - left) * (k + 0.5) / groups - g / 2, y = (H - g) / 2;
        const strokes = p.style === 'bars'
          ? [[x + g * 0.1, y, x + g * 0.1, y + g], [x + g * 0.33, y, x + g * 0.33, y + g], [x + g * 0.56, y, x + g * 0.56, y + g], [x + g * 0.79, y, x + g * 0.79, y + g], [x - g * 0.05, y + g * 0.75, x + g * 0.95, y + g * 0.25]]
          : [[x + g * 0.1, y + g * 0.05, x + g * 0.9, y + g * 0.05], [x + g * 0.5, y + g * 0.05, x + g * 0.5, y + g * 0.95], [x + g * 0.5, y + g * 0.48, x + g * 0.85, y + g * 0.48],
             [x + g * 0.22, y + g * 0.42, x + g * 0.22, y + g * 0.95], [x, y + g * 0.95, x + g, y + g * 0.95]];
        strokes.slice(0, Math.min(5, total - 5 * k)).forEach((q, i) => {
          const node = pen.line(...q, o({ strokeWidth: g * 0.07, stroke: p.color || ink(p), roughness: 0.9 }));
          layer.appendChild(node); cursor = drawOn(node, cursor, p.stroke_ms || 180) + 40;
        });
        cursor += 120;
      }
    } else if (kind === 'timeline') {
      const events = p.events || [], vertical = H > W * 1.2;
      const axis = vertical ? pen.line(W * 0.2, top, W * 0.2, bottom, o()) : pen.line(left, H / 2, right, H / 2, o());
      layer.appendChild(axis);
      let cursor = drawOn(axis, start, 600);
      events.forEach((event, i) => {
        const f = events.length > 1 ? i / (events.length - 1) : 0.5;
        const x = vertical ? W * 0.2 : left + (right - left) * (0.06 + 0.88 * f), y = vertical ? top + (bottom - top) * (0.06 + 0.88 * f) : H / 2;
        const at = cursor + i * (p.stagger || 380);
        const dot = pen.circle(x, y, size * 0.8, o({ fill: i === highlight ? colors[0] : '#FFFFFF', fillStyle: 'solid' }));
        dot.style.transformBox = 'fill-box'; dot.style.transformOrigin = 'center'; layer.appendChild(dot);
        dot.animate([{ transform: 'scale(0)' }, { transform: 'scale(1)' }], { delay: at, duration: 360, easing: 'cubic-bezier(.3,1.6,.5,1)', fill: 'both' });
        const above = i % 2 === 0;
        if (event.when) appear(label(root, event.when, vertical ? x - size * 0.9 : x, vertical ? y : y + (above ? size * 1.3 : -size * 1.3), size * 0.8, p, vertical ? 'right' : 'center', colors[0]), at + 80);
        appear(label(root, event.label || '', vertical ? x + size * 0.9 : x, vertical ? y : y + (above ? -size * 1.3 : size * 1.3), size, p, vertical ? 'left' : 'center'), at + 140);
      });
    } else throw new Error('Unknown chart kind: ' + kind);
  };

  // A route over the world drawn as it is travelled: land outlines only (no borders), a great-circle line inked up to
  // a moving marker, stops popping as the marker passes them. projection "globe" turns to follow the marker; "flat" fits
  // the route. route: [[lon, lat], ...]; stops: [{at: [lon, lat], label}].
  Recipes.map_route = (root, p, ctx) => {
    const W = ctx.width, H = ctx.height, scale = ctx.scale;
    const canvas = document.createElement('canvas');
    canvas.width = W * scale; canvas.height = H * scale;
    Object.assign(canvas.style, { position: 'absolute', inset: '0', width: `${W}px`, height: `${H}px` });
    root.appendChild(canvas);
    const g = canvas.getContext('2d'); g.scale(scale, scale);
    const land = topojson.feature(WORLD_LAND, WORLD_LAND.objects.land);
    const route = p.route || [];
    if (route.length < 2) throw new Error('map_route needs a route of at least two [lon, lat] points');
    const legs = route.slice(1).map((q, i) => ({ from: route[i], to: q, length: d3.geoDistance(route[i], q), at: d3.geoInterpolate(route[i], q) }));
    const total = legs.reduce((a, leg) => a + leg.length, 0) || 1;
    const along = (f) => { let rest = f * total; for (const leg of legs) { if (rest <= leg.length || leg === legs[legs.length - 1]) return leg.at(Math.min(1, rest / (leg.length || 1))); rest -= leg.length; } };
    const samples = (f) => { const n = Math.max(2, Math.ceil(240 * f)); return [...Array(n + 1)].map((_, i) => along(f * i / n)); };
    const globe = (p.projection || 'globe') === 'globe';
    const projection = globe ? d3.geoOrthographic().clipAngle(90).scale(Math.min(W, H) * 0.44).translate([W / 2, H / 2])
                             : d3.geoNaturalEarth1().fitExtent([[W * 0.08, H * 0.08], [W * 0.92, H * 0.92]], p.fit === 'world' ? { type: 'Sphere' } : { type: 'MultiPoint', coordinates: route });
    const path = d3.geoPath(projection, g);
    const start = p.delay || 0, intro = p.intro_ms ?? 600, travel = p.travel_ms || 2600;
    const colors = { land: p.land || '#E4D9C2', coast: p.coast || '#5C5346', sea: p.sea || '#EEF3F2', route: p.color || '#E9784E', ink: ink(p) };
    const font = family(p.font || 'hand'), size = p.label_size || Math.max(20, Math.min(W, H) * 0.045);
    const stops = (p.stops || []).map((stop) => {
      let f = 0, bestD = Infinity;
      for (let i = 0; i <= 200; i++) { const d = d3.geoDistance(along(i / 200), stop.at); if (d < bestD) { bestD = d; f = i / 200; } }
      let t = 1; for (let i = 0; i <= 400; i++) if (ease(i / 400) >= f - 1e-9) { t = i / 400; break; }  // when the marker gets there
      return { ...stop, f, t };
    });
    const draw = () => {
      const now = performance.now() - start;
      const raw = (now - intro) / travel, shown = Math.max(0, Math.min(1, now / Math.max(1, intro))), f = ease(Math.max(0, Math.min(1, raw)));
      const marker = along(f);
      if (globe) {
        const lead = along(Math.min(1, f + 0.08));
        projection.rotate([-(marker[0] * 0.6 + lead[0] * 0.4), -Math.max(-50, Math.min(50, marker[1])) * 0.55]);
      }
      g.clearRect(0, 0, W, H);
      g.globalAlpha = shown;
      if (globe) { g.beginPath(); path({ type: 'Sphere' }); g.fillStyle = colors.sea; g.fill(); g.lineWidth = 3; g.strokeStyle = colors.coast; g.stroke();
        g.beginPath(); path(d3.geoGraticule10()); g.lineWidth = 0.8; g.strokeStyle = 'rgba(92,83,70,0.18)'; g.stroke(); }
      g.beginPath(); path(land); g.fillStyle = colors.land; g.fill();
      // A sketchy coast: two passes a hair apart.
      g.lineJoin = 'round'; g.strokeStyle = colors.coast; g.lineWidth = 1.6; g.stroke();
      g.save(); g.translate(0.9, -0.6); g.globalAlpha = shown * 0.45; g.beginPath(); path(land); g.stroke(); g.restore();
      g.globalAlpha = 1;
      if (now > intro) {
        g.beginPath(); path({ type: 'LineString', coordinates: samples(f) });
        g.strokeStyle = colors.route; g.lineWidth = p.route_width || 5; g.lineCap = 'round'; g.setLineDash([]); g.stroke();
        for (const stop of stops) {
          if (stop.f > f + 1e-6) continue;
          const xy = projection(stop.at), visible = !globe || d3.geoDistance(stop.at, [-projection.rotate()[0], -projection.rotate()[1]]) < Math.PI / 2;
          if (!xy || !visible) continue;
          const pop = Math.max(0.0001, Math.min(1, (raw - stop.t) * travel / 260)), r = size * 0.32 * (1 + 0.4 * Math.sin(Math.PI * pop));
          g.beginPath(); g.arc(xy[0], xy[1], r, 0, 2 * Math.PI); g.fillStyle = '#FFFFFF'; g.fill(); g.lineWidth = 3; g.strokeStyle = colors.ink; g.stroke();
          if (stop.label) { g.globalAlpha = pop; g.font = `${size}px ${font}`; g.fillStyle = colors.ink; g.textAlign = 'center'; g.fillText(stop.label, xy[0], xy[1] - size * 0.9); g.globalAlpha = 1; }
        }
        const xy = projection(marker);
        if (xy) {
          const pulse = (now % 900) / 900;
          g.beginPath(); g.arc(xy[0], xy[1], size * (0.45 + 0.8 * pulse), 0, 2 * Math.PI); g.strokeStyle = colors.route; g.globalAlpha = 1 - pulse; g.lineWidth = 3; g.stroke(); g.globalAlpha = 1;
          g.beginPath(); g.arc(xy[0], xy[1], size * 0.42, 0, 2 * Math.PI); g.fillStyle = colors.route; g.fill(); g.lineWidth = 3; g.strokeStyle = '#FFFFFF'; g.stroke();
        }
      }
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  };

  // ---------------------------------------------------------------- 2.0.1 recipes

  // Props under real physics (matter-js): coins pour into a jar, dominoes topple, a tower is knocked over, balls bounce
  // and settle. Each body keeps one rough.js outline (a fixed seed) and turns rigidly with the body instead of boiling.
  // p: {scene: pour|topple|stack|bounce, container: jar|tray|floor|none, items: [{shape: circle|box|pill, size | w,h,
  //     fill, label, count}], gravity (1 = 1000 px/s^2), bounce (0..1), drop_ms, intro_ms, delay, ink, label_size}
  Recipes.physics = (root, p, ctx) => {
    if (!window.Matter) throw new Error('physics needs matter-js (vendor/matter.js)');
    const { Engine, Bodies, Body, Composite } = Matter;
    const W = ctx.width, H = ctx.height, scale = ctx.scale, M = 8;  // bodies stay M px inside the box
    const canvas = document.createElement('canvas');
    canvas.width = W * scale; canvas.height = H * scale;
    Object.assign(canvas.style, { position: 'absolute', inset: '0', width: `${W}px`, height: `${H}px` });
    root.appendChild(canvas);
    const g = canvas.getContext('2d'); g.scale(scale, scale);
    const rc = rough.canvas(canvas), gen = rc.generator;
    // Toppling reads best faster than the free fall of a small prop (2.5x), so dominoes run as a chain, not a slow lean.
    const engine = Engine.create({ gravity: { x: 0, y: p.gravity ?? (p.scene === 'topple' ? 2.5 : 1), scale: 0.001 } });
    engine.positionIterations = 10; engine.velocityIterations = 8;
    const scene = p.scene || 'pour', kind = p.container || (scene === 'pour' ? 'jar' : 'floor');
    const start = p.delay || 0, intro = p.intro_ms ?? (kind === 'none' ? 0 : 500), lineInk = ink(p);
    const wall = (x, y, w, h, angle = 0) => Bodies.rectangle(x, y, w, h, { isStatic: true, angle, friction: 0.6 });
    // Invisible bounds a little inside the box, so nothing settles against (and gets cut by) the overlay edge.
    const statics = [wall(W / 2, H - M + 30, W * 2, 60), wall(M - 30, H / 2, 60, H * 3), wall(W - M + 30, H / 2, 60, H * 3)];
    let outlinePath = null, floorY = H - M;
    if (kind === 'jar' || kind === 'tray') {
      const jw = Math.min(W - 2 * M - 8, kind === 'jar' ? Math.max(W * 0.55, 160) : W * 0.8), jh = kind === 'jar' ? Math.min(H * 0.62, jw * 1.25) : Math.min(H * 0.22, 90);
      const left = (W - jw) / 2, right = left + jw, bottom = H - M - 4, top = bottom - jh, t = 16, r = Math.min(26, jw * 0.12);
      statics.push(wall(left - t / 2 + 2, bottom - jh / 2, t, jh), wall(right + t / 2 - 2, bottom - jh / 2, t, jh), wall(W / 2, bottom + t / 2 - 2, jw, t));
      outlinePath = `M ${left - 6} ${top} Q ${left} ${top + 6} ${left} ${top + 18} L ${left} ${bottom - r} Q ${left} ${bottom} ${left + r} ${bottom} L ${right - r} ${bottom} Q ${right} ${bottom} ${right} ${bottom - r} L ${right} ${top + 18} Q ${right} ${top + 6} ${right + 6} ${top}`;
      floorY = bottom;
      statics.opening = [left + 10, right - 10];
    } else if (kind === 'floor') {
      outlinePath = `M ${M + 4} ${H - M - 2} L ${W - M - 4} ${H - M - 2}`;
      floorY = H - M - 4;
      statics[0] = wall(W / 2, floorY + 30, W * 2, 60);
    }
    Composite.add(engine.world, statics);
    const outline = outlinePath && gen.path(outlinePath, { stroke: lineInk, strokeWidth: 3.2, roughness: 1.1, seed: 7 });
    const items = [];
    const specs = (p.items && p.items.length ? p.items : [{ shape: 'circle', fill: '#F2C14E', label: '¥', count: 14 }]);
    for (const spec of specs) for (let i = 0; i < (spec.count || 1); i++) items.push({ ...spec });
    const size = (spec) => spec.size || Math.max(22, Math.min(W, H) * 0.085);
    const FILLS = PALETTE.filter((color) => color !== '#1E2733');  // no ink-dark bodies: they read as holes
    const make = (spec, x, y, angle = 0) => {
      const options = { restitution: spec.bounce ?? p.bounce ?? (scene === 'bounce' ? 0.62 : 0.2), friction: spec.friction ?? 0.4, frictionAir: 0.004,
                        density: spec.density || 0.002, angle };
      const s = size(spec), w = spec.w || s, h = spec.h || s;
      if ((spec.shape || 'circle') === 'circle') return Bodies.circle(x, y, s / 2, options);
      if (spec.shape === 'pill') return Bodies.rectangle(x, y, w * 1.6, h * 0.7, { ...options, chamfer: { radius: h * 0.34 } });
      return Bodies.rectangle(x, y, w, h, { ...options, chamfer: { radius: Math.min(w, h) * 0.08 } });
    };
    const drawable = (spec, index) => {
      const s = size(spec), w = spec.w || s, h = spec.h || s, fill = spec.fill || FILLS[index % FILLS.length];
      const style = { stroke: lineInk, strokeWidth: 2.4, roughness: 0.9, fill, fillStyle: 'solid', seed: 11 + index };
      if ((spec.shape || 'circle') === 'circle') return gen.circle(0, 0, s, style);
      if (spec.shape === 'pill') return gen.path(`M ${-w * 0.8 + h * 0.35} ${-h * 0.35} H ${w * 0.8 - h * 0.35} A ${h * 0.35} ${h * 0.35} 0 0 1 ${w * 0.8 - h * 0.35} ${h * 0.35} H ${-w * 0.8 + h * 0.35} A ${h * 0.35} ${h * 0.35} 0 0 1 ${-w * 0.8 + h * 0.35} ${-h * 0.35} Z`, style);
      return gen.rectangle(-w / 2, -h / 2, w, h, style);
    };
    const bodies = [];  // {body, shape, spec, at}
    const release = (spec, index, at, x, y, angle = 0, kick = null) => bodies.push({ spec, shape: drawable(spec, index), at, x, y, angle, kick, body: null });
    const dropMs = p.drop_ms ?? 1400;
    const [lo, hi] = statics.opening || [M + 20, W - M - 20];
    if (scene === 'topple' || scene === 'stack') {
      const s = size(items[0]);
      if (scene === 'topple') {
        // Dominoes a little over half their height apart: each one falls far enough to tip the next.
        const n = Math.max(3, items.length), h = Math.min(s * 2.4, (floorY - M) * 0.8), w = Math.max(8, h * 0.17), gap = Math.min(h * 0.58, (W - 2 * M - 2 * w) / n);
        const x0 = W / 2 - gap * (n - 1) / 2;
        for (let i = 0; i < n; i++) release({ ...items[i % items.length], shape: 'box', w, h, friction: 0.08 }, i, 0, x0 + i * gap, floorY - h / 2 - 1, 0, i === 0 ? { angular: 0.05 } : null);
      } else {
        // A two-wide tower and a heavy ball that rolls in and knocks it over.
        const rows = Math.max(3, Math.ceil(items.length / 2)), w = s * 1.1, h = Math.min(s * 0.8, (floorY - M - 20) / rows);
        let index = 0;
        for (let r = 0; r < rows; r++) for (let c = 0; c < 2; c++) release({ ...items[index % items.length], shape: 'box', w, h }, index++, 0,
          W * 0.62 + (c - 0.5) * (w + 1) + (r % 2 ? 3 : -3), floorY - h / 2 - r * (h + 0.5) - 1);
        release({ shape: 'circle', size: s * 1.2, fill: '#E9784E', density: 0.02, bounce: 0.1 }, index, intro + 150, M + s * 0.7, floorY - rows * h * 0.62, 0, { vx: 22 });
      }
    } else {
      items.forEach((spec, i) => {
        const x = lo + (hi - lo) * (scene === 'bounce' ? (i + 0.5) / items.length : (0.5 + 0.42 * Math.sin(i * 2.399)));
        release(spec, i, intro + dropMs * i / Math.max(1, items.length), x, -size(spec) - 4 - (scene === 'bounce' ? i * 18 : 0), Math.random() * 6.28);
      });
    }
    const step = 1000 / 120;
    let sim = 0;
    const draw = () => {
      const now = performance.now() - start;
      for (; sim + step <= now; sim += step) {
        for (const entry of bodies) {
          if (entry.body || sim < entry.at) continue;
          entry.body = make(entry.spec, entry.x, entry.y, entry.angle);
          Composite.add(engine.world, entry.body);
          if (entry.kick && entry.kick.angular) Body.setAngularVelocity(entry.body, entry.kick.angular);
          if (entry.kick && entry.kick.vx) Body.setVelocity(entry.body, { x: entry.kick.vx, y: -2 });
        }
        if (sim >= Math.min(...bodies.map((entry) => entry.at), intro)) Engine.update(engine, step);
      }
      g.clearRect(0, 0, W, H);
      if (outline) {
        // The container is drawn on first: its path revealed with a moving clip from left to right.
        const f = intro ? ease(Math.min(1, now / intro)) : 1;
        g.save(); g.beginPath(); g.rect(0, 0, W * f, H); g.clip(); rc.draw(outline); g.restore();
      }
      const font = family(p.font || 'hand');
      for (const entry of bodies) {
        const shown = entry.body || (scene !== 'pour' && scene !== 'bounce');
        if (!shown) continue;
        const x = entry.body ? entry.body.position.x : entry.x, y = entry.body ? entry.body.position.y : entry.y, a = entry.body ? entry.body.angle : entry.angle;
        g.save(); g.translate(x, y); g.rotate(a);
        if (!entry.body && intro) g.globalAlpha = ease(Math.min(1, now / intro));
        rc.draw(entry.shape);
        if (entry.spec.label) {
          const s = size(entry.spec);
          g.fillStyle = lineInk; g.font = `${Math.round(p.label_size || s * 0.55)}px ${font}`; g.textAlign = 'center'; g.textBaseline = 'middle';
          g.fillText(entry.spec.label, 0, s * 0.03);
        }
        g.restore();
      }
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  };

  // A 3D object turning in place (Zdog): flat-shaded faces inside an ink silhouette, popping in with a small overshoot.
  // p: {shape: box|coin|cylinder|cone|sphere|pyramid|gem, size, colors: [main, side, top], turns (1), spin_ms, tilt (deg),
  //     axis: y|x, appear_ms, delay, ink, outline (px)}
  Recipes.spin3d = (root, p, ctx) => {
    if (!window.Zdog) throw new Error('spin3d needs Zdog (vendor/zdog.js)');
    const W = ctx.width, H = ctx.height, TAU = Zdog.TAU;
    const shape = p.shape || 'box', s = p.size || Math.min(W, H) * 0.5, line = p.outline ?? 4, inkColor = ink(p);
    const colors = p.colors || [PALETTE[0], '#C8603A', '#F4A47F'];
    const [main, side, top] = [colors[0], colors[1] || colors[0], colors[2] || colors[0]];
    // Two canvases, one model each: an ink silhouette below (every surface in ink, strokes thickened by the outline) and
    // the colours above (Zdog clears its canvas on every render, so the passes cannot share one).
    const build = (silhouette) => {
      // Sized in CSS pixels: Zdog itself up-rezes by devicePixelRatio (the capture's board scale), so no extra zoom here.
      const canvas = document.createElement('canvas');
      canvas.width = W; canvas.height = H;
      Object.assign(canvas.style, { position: 'absolute', inset: '0', width: `${W}px`, height: `${H}px` });
      root.appendChild(canvas);
      const pen = (color) => (silhouette ? inkColor : color), grow = silhouette ? 2 * line : 0;
      const scene = new Zdog.Illustration({ element: canvas, resize: false, centered: true });
      const body = new Zdog.Anchor({ addTo: scene });
      const face = (points, color, front) => new Zdog.Shape({ addTo: body, path: points, fill: true, stroke: 2 + grow, color: pen(color), front, backface: silhouette ? pen(color) : false });
      if (shape === 'box') {
        new Zdog.Box({ addTo: body, width: s * 0.78, height: s * 0.78, depth: s * 0.78, stroke: 2 + grow, color: pen(main),
          leftFace: pen(side), rightFace: pen(side), topFace: pen(top), bottomFace: pen(side), frontFace: pen(main), rearFace: pen(main) });
      } else if (shape === 'coin' || shape === 'cylinder') {
        const coin = shape === 'coin', d = coin ? s * 0.92 : s * 0.62, length = coin ? s * 0.12 : s * 0.85;
        new Zdog.Cylinder({ addTo: body, diameter: d, length, stroke: 2 + grow, color: pen(side), frontFace: pen(main), backface: pen(main),
          rotate: coin ? {} : { x: TAU / 4 } });
        if (coin && !silhouette) for (const z of [1, -1]) new Zdog.Ellipse({ addTo: body, diameter: d * 0.7, stroke: Math.max(2, s * 0.025), color: top, translate: { z: z * (length / 2 + 0.5) } });
        // A can's label stripe shows that it turns (a plain cylinder spinning on its axis looks still).
        if (!coin && !silhouette) new Zdog.Rect({ addTo: body, width: d * 0.28, height: length * 0.86, stroke: 1, fill: true, color: top, backface: false,
                                                   translate: { z: d / 2 + 1 } });
      } else if (shape === 'cone') {
        new Zdog.Cone({ addTo: body, diameter: s * 0.8, length: s * 0.9, stroke: 2 + grow, color: pen(main), backface: pen(side), rotate: { x: TAU / 4 }, translate: { y: s * 0.38 } });
        if (!silhouette) new Zdog.Shape({ addTo: body, path: [{ y: -s * 0.5 }, { y: s * 0.38, z: s * 0.4 }], stroke: Math.max(4, s * 0.05), color: top });  // a seam that turns
      } else if (shape === 'sphere') {
        const half = (color, turn) => new Zdog.Hemisphere({ addTo: body, diameter: s * 0.9, stroke: 2 + grow, color: pen(color), backface: pen(color), rotate: { y: turn } });
        half(main, 0); half(top, TAU / 2);
      } else if (shape === 'pyramid' || shape === 'gem') {
        const r = s * 0.48, apex = { x: 0, y: -s * 0.5, z: 0 }, tip = shape === 'gem' ? { x: 0, y: s * 0.62, z: 0 } : null;
        const base = [0, 1, 2, 3].map((i) => ({ x: r * Math.cos(TAU * i / 4 + TAU / 8), y: s * 0.3, z: r * Math.sin(TAU * i / 4 + TAU / 8) }));
        const corners = [apex, ...base, ...(tip ? [tip] : [])];
        const center = ['x', 'y', 'z'].reduce((c, k) => ({ ...c, [k]: corners.reduce((sum, q) => sum + q[k], 0) / corners.length }), {});
        // Zdog hides a face when its "front" point (relative to the face origin) turns away: give it the true outward normal.
        const normal = (points) => {
          const [a, b, c] = points, u = { x: b.x - a.x, y: b.y - a.y, z: b.z - a.z }, v = { x: c.x - a.x, y: c.y - a.y, z: c.z - a.z };
          const n = { x: u.y * v.z - u.z * v.y, y: u.z * v.x - u.x * v.z, z: u.x * v.y - u.y * v.x };
          const out = ['x', 'y', 'z'].reduce((sum, k) => sum + n[k] * (points.reduce((t, q) => t + q[k], 0) / points.length - center[k]), 0);
          return out < 0 ? { x: -n.x, y: -n.y, z: -n.z } : n;
        };
        const palette = [main, side, top, side];
        base.forEach((a, i) => {
          const b = base[(i + 1) % 4];
          face([apex, a, b], palette[i], normal([apex, a, b]));
          if (tip) face([tip, b, a], palette[(i + 1) % 4], normal([tip, b, a]));
        });
        if (!tip) face(base, side, normal(base));
      } else throw new Error('spin3d shape is box, coin, cylinder, cone, sphere, pyramid or gem');
      return { scene, body };
    };
    const passes = [build(true), build(false)];
    const start = p.delay || 0, appear = p.appear_ms ?? 420, spin = p.spin_ms || Math.max(600, ctx.duration - start - appear - 200);
    const tilt = (p.tilt ?? 18) * TAU / 360, turns = p.turns ?? 1, axis = p.axis || 'y';
    const draw = () => {
      const now = performance.now() - start;
      const grow = now <= 0 ? 0 : now >= appear ? 1 : 1 - Math.cos(now / appear * Math.PI * 1.25) * Math.exp(-4 * now / appear);  // overshoot, then settle
      const turn = TAU * turns * ease(Math.max(0, Math.min(1, (now - appear) / spin))) + TAU / 10;
      passes.forEach(({ scene, body }) => {
        body.scale = Math.max(0.0001, grow);
        body.rotate = axis === 'x' ? { x: turn, y: TAU / 10 } : { x: -tilt, y: turn };
        scene.updateRenderGraph();
      });
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  };

  // A formula written by hand (MathJax TeX -> SVG glyph outlines): glyph by glyph in reading order, each outline traced
  // like a pen, then filled; fraction bars and root lines are ruled left to right. A highlight circles or underlines a
  // part afterwards. p: {tex, size (px per em; default fits the box), color, glyph_ms, delay, align: center|left,
  //     highlight: {from, to (glyph indexes), style: circle|box|underline, color, at_ms}}
  Recipes.formula = (root, p, ctx) => {
    if (!window.MathJax || !MathJax.tex2svg) throw new Error('formula needs MathJax (vendor/mathjax-tex-svg.js)');
    if (!p.tex) throw new Error('formula needs "tex"');
    const W = ctx.width, H = ctx.height;
    const holder = MathJax.tex2svg(p.tex, { display: true });
    const svgNode = holder.querySelector('svg');
    if (!svgNode) throw new Error('MathJax produced no SVG for ' + p.tex);
    const error = svgNode.querySelector('[data-mml-node="merror"]');
    if (error) throw new Error('TeX error in formula: ' + (error.getAttribute('title') || error.textContent));
    const box = svgNode.viewBox.baseVal, pad = Math.min(W, H) * 0.06;
    const em = p.size || Math.min((W - 2 * pad) / (box.width / 1000), (H - 2 * pad) / (box.height / 1000), Math.max(40, H * 0.5));
    const width = box.width / 1000 * em, height = box.height / 1000 * em;
    svgNode.setAttribute('width', width); svgNode.setAttribute('height', height);
    Object.assign(svgNode.style, { position: 'absolute', top: `${(H - height) / 2}px`, left: `${p.align === 'left' ? pad : (W - width) / 2}px`,
                                   color: p.color || ink(p), overflow: 'visible' });
    root.appendChild(svgNode);
    // Reading order as a hand writes it: a fraction's bar before its denominator, a root's sign and bar before its contents.
    for (const frac of svgNode.querySelectorAll('[data-mml-node="mfrac"]')) {
      const bar = [...frac.children].find((child) => child.tagName === 'rect');
      if (bar && frac.children.length > 2) frac.insertBefore(bar, frac.children[1]);
    }
    for (const root2 of svgNode.querySelectorAll('[data-mml-node="msqrt"], [data-mml-node="mroot"]')) {
      for (const child of [...root2.children].filter((c) => c.tagName === 'rect' || c.getAttribute('data-mml-node') === 'mo').reverse()) root2.insertBefore(child, root2.firstChild);
    }
    const marks = [...svgNode.querySelectorAll('path, rect')].filter((node) => !(node.tagName === 'rect' && node.closest('[data-mml-node="merror"]')));
    const start = p.delay || 0, slot = p.glyph_ms || Math.max(90, Math.min(240, (ctx.duration - start - 500) / Math.max(1, marks.length)));
    const color = p.color || ink(p);
    marks.forEach((node, index) => {
      const at = start + index * slot;
      if (node.tagName === 'rect') {
        node.animate([{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)' }], { delay: at, duration: slot * 1.2, easing: 'cubic-bezier(.45,.05,.4,1)', fill: 'both' });
        return;
      }
      const length = node.getTotalLength();
      Object.assign(node.style, { stroke: 'currentColor', strokeWidth: `${p.pen ?? 1.4}px`, vectorEffect: 'non-scaling-stroke', strokeLinejoin: 'round', strokeDasharray: `${length}` });
      node.animate([{ strokeDashoffset: length }, { strokeDashoffset: 0 }], { delay: at, duration: slot * 1.25, easing: 'cubic-bezier(.45,.05,.4,1)', fill: 'both' });
      node.animate([{ fillOpacity: 0 }, { fillOpacity: 1 }], { delay: at + slot * 0.75, duration: slot * 1.1, easing: 'ease-out', fill: 'both' });
    });
    const mark = p.highlight;
    if (mark) {
      const glyphs = marks.slice(mark.from ?? 0, (mark.to ?? marks.length - 1) + 1);
      const origin = root.getBoundingClientRect();
      const rects = glyphs.map((node) => node.getBoundingClientRect()).filter((r) => r.width || r.height);
      if (!rects.length) throw new Error('formula highlight covers no glyphs');
      const x1 = Math.min(...rects.map((r) => r.left)) - origin.left, y1 = Math.min(...rects.map((r) => r.top)) - origin.top;
      const x2 = Math.max(...rects.map((r) => r.right)) - origin.left, y2 = Math.max(...rects.map((r) => r.bottom)) - origin.top;
      const layer = svgLayer(root, W, H), rs = rough.svg(layer), m = em * 0.12, style = { stroke: mark.color || '#E9784E', strokeWidth: mark.width || 3.4, roughness: 1.3, seed: 5 };
      const kind = mark.style || 'circle';
      const node = kind === 'underline' ? rs.line(x1, y2 + m * 0.6, x2, y2 + m * 0.4, style)
        : kind === 'box' ? rs.rectangle(x1 - m, y1 - m, x2 - x1 + 2 * m, y2 - y1 + 2 * m, style)
        : rs.ellipse((x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1) * 1.18 + 2 * m, (y2 - y1) * 1.3 + 2 * m, style);
      layer.appendChild(node);
      drawOn(node, mark.at_ms ?? start + marks.length * slot + 250, mark.ms || 520);
    }
  };

  // Anything else: the model writes the body and a script; it must animate with anime.js, CSS or element.animate
  // (all driven by the virtual clock) and keep a transparent background.
  Recipes.custom = (root, p, ctx) => {
    if (p.css) { const style = document.createElement('style'); style.textContent = p.css; document.head.appendChild(style); }
    root.innerHTML = p.html || '';
    if (p.script) new Function('root', 'p', 'ctx', 'anime', 'rough', 'RoughNotation', 'confetti', 'd3', p.script)(root, p, ctx, anime, rough, RoughNotation, confetti, d3);
  };

  window.Recipes = Recipes;
})();
