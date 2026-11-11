// Virtual clock for frame-exact capture: page time only moves when the renderer calls __advance(ms).
// performance.now, Date.now, requestAnimationFrame and timers all read this clock, and Web Animations (CSS
// animations, transitions, element.animate) are paused and seeked to it, so a recipe renders the same pixels at the
// same time on every run, however slow the capture is.
(() => {
  let now = 0;
  const epoch = 1767225600000;  // a fixed wall-clock origin; recipes must not depend on the real date
  let nextId = 1;
  const frames = new Map();
  const timers = new Map();
  const seen = new WeakMap();
  performance.now = () => now;
  const RealDate = Date;
  class VirtualDate extends RealDate {
    constructor(...args) { super(...(args.length ? args : [epoch + now])); }
    static now() { return epoch + now; }
  }
  window.Date = VirtualDate;
  window.requestAnimationFrame = (callback) => { const id = nextId++; frames.set(id, callback); return id; };
  window.cancelAnimationFrame = (id) => frames.delete(id);
  window.setTimeout = (fn, ms = 0, ...args) => { const id = nextId++; timers.set(id, { at: now + Math.max(0, ms), fn, args }); return id; };
  window.setInterval = (fn, ms = 0, ...args) => {
    const id = nextId++; timers.set(id, { at: now + Math.max(1, ms), fn, args, every: Math.max(1, ms) }); return id;
  };
  window.clearTimeout = window.clearInterval = (id) => timers.delete(id);

  function syncAnimations() {
    for (const animation of document.getAnimations()) {
      if (!seen.has(animation)) {
        seen.set(animation, now);   // born during the last step: its local time starts there
        animation.pause();
      }
      animation.currentTime = Math.max(0, now - seen.get(animation));
    }
  }

  window.__advance = (ms) => {
    const target = now + ms;
    const tick = 1000 / 60;  // libraries tuned for 60 Hz displays (frame-counting particles) get 60 steps a second
    while (now < target - 1e-6) {
      now = Math.min(target, now + tick);
      for (const [id, timer] of [...timers.entries()].sort((a, b) => a[1].at - b[1].at)) {
        if (timer.at > now) continue;
        if (timer.every) timer.at += timer.every; else timers.delete(id);
        try { timer.fn(...timer.args); } catch (error) { console.error(error); }
      }
      const due = [...frames.values()];
      frames.clear();
      for (const callback of due) { try { callback(now); } catch (error) { console.error(error); } }
      syncAnimations();
    }
    syncAnimations();
    return now;
  };
  window.__now = () => now;
  // Seeded Math.random (mulberry32): particles and rough.js jitter repeat exactly for the same seed.
  let state = 1;
  window.__seedRandom = (seed) => { state = (seed >>> 0) || 1; };
  Math.random = () => {
    state = (state + 0x6D2B79F5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
})();
