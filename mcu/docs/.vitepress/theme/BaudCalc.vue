<script setup>
import { ref, computed } from 'vue'

// UART 波特率误差计算器：按 RM0090 的 BRR 编码（DIV_Mantissa[15:4] + DIV_Fraction[3:0]，
// F1/F4 同一套布局）做分频量化，再把误差放进整帧采样漂移的预算里判定成败。
// 量化结果与 code/stm32/03-uart-dma 固件的 `round(PCLK/baud)` 逐格相同（probe.sh 第 1 步实测）。

const clockMHz = ref(16)
const oversamp = ref(16)
const targetBaud = ref(115200)

const baudPresets = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
const clockPresets = [2, 8, 16, 42, 72, 84, 168, 1.8432]

// 时钟源固有容差（两侧各贡献一份）
const sources = {
  hse: { label: 'HSE 晶振 ±50 ppm', tol: 0.005 },
  lsecs: { label: '陶瓷谐振器 ±0.5%', tol: 0.5 },
  hsi: { label: 'HSI 内部 RC ±1%', tol: 1.0 },
  lsi: { label: 'LSI / 内部低速 ±3%', tol: 3.0 },
}
const sourceKey = ref('hse')

// 帧格式决定最坏采样时刻：8N1 = 10 位，8E2 = 12 位
const frames = {
  '8N1': 10,
  '8N2': 11,
  '8E1': 11,
  '8E2': 12,
}
const frameKey = ref('8N1')

const calc = computed(() => {
  const fck = clockMHz.value * 1e6
  const baud = targetBaud.value
  if (!(fck > 0) || !(baud > 0)) return null
  const os = oversamp.value
  const div = fck / (os * baud) // USARTDIV
  let mant = Math.floor(div)
  let frac = Math.round((div - mant) * os)
  const fracMax = os === 16 ? 15 : 7
  if (frac > fracMax) { mant += 1; frac = os === 16 ? 0 : frac - 8 }
  const usartdiv = mant + frac / os
  const actual = fck / (os * usartdiv)
  const quantErr = ((actual - baud) / baud) * 100
  const brr = (mant << 4) | (frac & 0xf)
  return {
    mant, frac, actual, quantErr, brr,
    mantOk: mant >= (os === 16 ? 16 : 8) && mant <= 0xfff,
    fracOk: os === 16 || frac <= 7,
  }
})

const budget = computed(() => {
  if (!calc.value) return null
  const n = frames[frameKey.value]
  // 接收端在每位中点重采样，误差逐位累积；第 N-1 位数据的中点 = (N-1.5) 位时刻，
  // 采样点必须留在位窗口内：|总误差| × (N-1.5) < 0.5 → 总预算 = 0.5/(N-1.5)
  const total = (0.5 / (n - 1.5)) * 100
  const src = sources[sourceKey.value].tol
  const quant = Math.abs(calc.value.quantErr)
  const used = quant + 2 * src
  return { bits: n, total, src, quant, used, margin: total - used }
})

const verdict = computed(() => {
  const b = budget.value
  if (!b) return { cls: 'pill', text: '—' }
  if (!calc.value.mantOk) return { cls: 'pill err', text: '✗ 分频字段越界' }
  if (b.margin >= 1) return { cls: 'pill ok', text: '✓ 可靠' }
  if (b.margin >= 0) return { cls: 'pill warn', text: '⚠ 勉强' }
  return { cls: 'pill err', text: '✗ 超预算' }
})

function fmtBaud(n) {
  if (n == null) return '—'
  return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

// 漂移示意：每格 1 bit，三角是接收采样点，越靠边越危险
const W = 560
const cellW = computed(() => (budget.value ? (W - 20) / budget.value.bits : W))
const samples = computed(() => {
  const b = budget.value
  if (!b) return []
  // 总相对误差 = 量化 + 两侧时钟源，逐位累积成采样点平移
  const eps = b.used / 100
  const out = []
  for (let k = 0; k < b.bits; k++) {
    const t = (k + 0.5) * (1 + eps)
    const rel = (t - k) // 相对本位起点的位置，>1 就跨进下一位了
    out.push({ k, x: 10 + rel * cellW.value, danger: Math.abs(t - (k + 0.5)) / 1 })
  }
  return out
})
</script>

<template>
  <div class="baud-calc">
    <div class="bc-header">
      <span class="bc-title">波特率误差计算器</span>
      <span class="bc-sub">BRR 量化 + 整帧采样漂移预算</span>
    </div>

    <div class="bc-grid">
      <div class="bc-panel">
        <h4>外设时钟 f<sub>PCLK</sub></h4>
        <div class="bc-chips">
          <button
            v-for="c in clockPresets" :key="c"
            :class="['bc-chip', { active: clockMHz === c }]"
            @click="clockMHz = c"
          >{{ c }} MHz</button>
        </div>
        <label class="bc-row">
          <span>自定义</span>
          <input type="number" v-model.number="clockMHz" min="0.1" step="0.0001" />
          <span class="bc-unit">MHz</span>
        </label>

        <h4>过采样</h4>
        <div class="bc-chips">
          <button :class="['bc-chip', { active: oversamp === 16 }]" @click="oversamp = 16">16×（OVER8=0）</button>
          <button :class="['bc-chip', { active: oversamp === 8 }]" @click="oversamp = 8">8×（OVER8=1）</button>
        </div>

        <h4>目标波特率</h4>
        <div class="bc-chips">
          <button
            v-for="b in baudPresets" :key="b"
            :class="['bc-chip', { active: targetBaud === b }]"
            @click="targetBaud = b"
          >{{ b }}</button>
        </div>
        <label class="bc-row">
          <span>自定义</span>
          <input type="number" v-model.number="targetBaud" min="300" step="100" />
          <span class="bc-unit">bps</span>
        </label>

        <h4>时钟源容差</h4>
        <div class="bc-chips">
          <button
            v-for="(s, key) in sources" :key="key"
            :class="['bc-chip', { active: sourceKey === key }]"
            @click="sourceKey = key"
          >{{ s.label }}</button>
        </div>

        <h4>帧格式</h4>
        <div class="bc-chips">
          <button
            v-for="(n, key) in frames" :key="key"
            :class="['bc-chip', { active: frameKey === key }]"
            @click="frameKey = key"
          >{{ key }}（{{ n }} 位）</button>
        </div>
      </div>

      <div class="bc-panel bc-results">
        <h4>BRR 编码</h4>
        <template v-if="calc">
          <div class="bc-kv">
            <span>USARTDIV</span>
            <code>{{ calc.mant }} + {{ calc.frac }}/{{ oversamp }} = {{ (calc.mant + calc.frac / oversamp).toFixed(4) }}</code>
          </div>
          <div class="bc-kv bc-highlight">
            <span>BRR / BAUD</span>
            <code class="bc-big">0x{{ calc.brr.toString(16).toUpperCase().padStart(3, '0') }}</code>
            <span :class="calc.mantOk && calc.fracOk ? 'pill ok' : 'pill err'">
              {{ calc.mantOk ? (calc.fracOk ? '字段合法' : 'OVER8 小数位越界') : ' Mantissa 越界（须 16 位整数域且 ≥ ' + (oversamp === 16 ? 16 : 8) + '）' }}
            </span>
          </div>
          <div class="bc-kv">
            <span>实际波特率</span>
            <code>{{ fmtBaud(calc.actual) }}</code>
            <span class="bc-errval">量化误差 {{ calc.quantErr >= 0 ? '+' : '' }}{{ calc.quantErr.toFixed(3) }}%</span>
          </div>
        </template>

        <h4>误差预算（{{ frameKey }}，{{ frames[frameKey] }} 位）</h4>
        <template v-if="budget">
          <div class="bc-meter">
            <div class="bc-meter-track">
              <i class="m-quant" :style="{ width: Math.min(100, budget.quant / budget.total * 100) + '%' }" />
              <i class="m-src" :style="{ width: Math.min(100 - Math.min(100, budget.quant / budget.total * 100), budget.src * 2 / budget.total * 100) + '%' }" />
            </div>
            <div class="bc-meter-legend">
              <span><b class="dot d-quant" />量化 {{ budget.quant.toFixed(2) }}%</span>
              <span><b class="dot d-src" />时钟源×2 {{ (budget.src * 2).toFixed(2) }}%</span>
              <span>总预算 {{ budget.total.toFixed(2) }}%</span>
              <span :class="budget.margin >= 0 ? 'ok-text' : 'err-text'">余量 {{ (budget.margin >= 0 ? '+' : '') + budget.margin.toFixed(2) }}%</span>
            </div>
          </div>
          <p class="bc-formula">
            预算 = 0.5 ÷ ({{ frames[frameKey] }} − 1.5) = {{ budget.total.toFixed(2) }}%：
            最后一个采样点（第 {{ frames[frameKey] - 1 }} 位中点）必须落回本位窗口内，
            误差逐位累积到这里还剩半格。"±2%" 经验值就是这么来的——10 位帧总预算 ≈ 5.88%，
            扣掉两份时钟源容差再对半分，留给每边约 2%。
          </p>
        </template>

        <h4>采样漂移</h4>
        <svg class="bc-svg" :viewBox="`0 0 ${W} 88`" role="img" aria-label="接收采样点随误差累积漂移示意图">
          <g v-for="k in frames[frameKey]" :key="k">
            <rect
              :x="10 + (k - 1) * cellW" y="18" :width="cellW - 2" height="30" rx="3"
              :fill="k === 1 ? 'var(--vp-c-brand-soft)' : 'var(--vp-c-bg)'"
              stroke="var(--vp-c-divider)"
            />
            <text :x="10 + (k - 1) * cellW + cellW / 2" y="36" text-anchor="middle" class="bc-bit">
              {{ k === 1 ? 'START' : k === frames[frameKey] ? 'STOP' : 'D' + (k - 1) }}
            </text>
          </g>
          <line x1="10" y1="56" :x2="W - 10" y2="56" stroke="var(--vp-c-divider)" stroke-dasharray="3 3" />
          <g v-for="s in samples" :key="s.k">
            <polygon
              :points="`${s.x - 4},64 ${s.x + 4},64 ${s.x},56`"
              :fill="s.danger > 0.4 ? '#cf222e' : '#1a7f37'"
            />
          </g>
          <text x="10" y="82" class="bc-anno">▲ 接收采样点：误差累积到第 {{ frames[frameKey] }} 位仍须留在窗口内</text>
        </svg>

        <div class="bc-verdict">
          <span>结论</span>
          <span :class="verdict.cls">{{ verdict.text }}</span>
          <span class="bc-verdict-detail" v-if="budget">
            {{ fmtBaud(targetBaud) }} @ {{ clockMHz }} MHz / {{ oversamp }}×
            → 实际 {{ calc ? fmtBaud(calc.actual) : '—' }}，
            预算 {{ budget.total.toFixed(2) }}%，占用 {{ budget.used.toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>

    <p class="bc-note">
      试试 1.8432 MHz（0.5 VCO 参考的由来）：9600/115200 都零误差；再试 16 MHz 配 460800、
      HSI 时钟源——量化误差本身不到 1%，但 ±1% 的时钟源两份一压就顶到预算边缘。
      这就是"低时钟倍频的串口高频段不可靠"的完整因果链。
    </p>
  </div>
</template>

<style scoped>
.baud-calc {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 20px;
  background: var(--vp-c-bg-soft);
  font-family: system-ui, sans-serif;
}
.bc-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.bc-title {
  font-size: 1.1em;
  font-weight: 700;
  color: var(--vp-c-brand-1);
}
.bc-sub {
  font-size: 0.85em;
  color: var(--vp-c-text-3);
}
.bc-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 20px;
}
@media (max-width: 768px) {
  .bc-grid { grid-template-columns: 1fr; }
}
.bc-panel h4 {
  font-size: 0.85em;
  color: var(--vp-c-text-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 12px 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--vp-c-divider);
}
.bc-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.bc-chip {
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  cursor: pointer;
  font-size: 0.82em;
  transition: all 0.15s;
}
.bc-chip:hover {
  border-color: var(--vp-c-brand-1);
}
.bc-chip.active {
  background: var(--vp-c-brand-1);
  color: #fff;
  border-color: var(--vp-c-brand-1);
}
.bc-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 0.9em;
}
.bc-row span:first-child {
  min-width: 60px;
  color: var(--vp-c-text-2);
}
.bc-row input[type="number"] {
  width: 110px;
  padding: 2px 6px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 4px;
  background: var(--vp-c-bg);
}
.bc-unit {
  color: var(--vp-c-text-3);
  font-size: 0.8em;
}
.bc-kv {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 8px;
  font-size: 0.92em;
}
.bc-kv > span:first-child {
  min-width: 96px;
  color: var(--vp-c-text-2);
}
.bc-kv code {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 1em;
}
.bc-highlight {
  background: var(--vp-c-brand-soft);
  border-radius: 6px;
  padding: 6px 10px;
}
.bc-big {
  font-size: 1.15em;
  font-weight: 700;
  color: var(--vp-c-brand-1);
}
.bc-errval {
  font-variant-numeric: tabular-nums;
  color: var(--vp-c-text-2);
}
.bc-meter-track {
  display: flex;
  height: 14px;
  border-radius: 7px;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  overflow: hidden;
}
.bc-meter-track i {
  display: block;
  height: 100%;
}
.m-quant { background: var(--vp-c-brand-1); }
.m-src { background: #d97706; }
.bc-meter-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.8em;
  color: var(--vp-c-text-2);
  margin-top: 6px;
}
.dot {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-right: 4px;
}
.d-quant { background: var(--vp-c-brand-1); }
.d-src { background: #d97706; }
.ok-text { color: #1a7f37; font-weight: 600; }
.err-text { color: #cf222e; font-weight: 600; }
.dark .ok-text { color: #3fb950; }
.dark .err-text { color: #f85149; }
.bc-formula {
  font-size: 0.82em;
  line-height: 1.6;
  color: var(--vp-c-text-2);
  background: var(--vp-c-bg);
  border-radius: 8px;
  padding: 8px 12px;
  margin-top: 8px;
}
.bc-svg {
  width: 100%;
  height: auto;
  margin-top: 4px;
}
.bc-bit {
  font-size: 10px;
  fill: var(--vp-c-text-3);
  font-family: Consolas, monospace;
}
.bc-anno {
  font-size: 10px;
  fill: var(--vp-c-text-3);
}
.bc-verdict {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--vp-c-bg);
  border-radius: 8px;
  font-size: 0.9em;
}
.pill {
  font-size: 0.8em;
  padding: 1px 8px;
  border-radius: 4px;
}
.pill.ok {
  color: #1a7f37;
  background: #dafbe1;
}
.pill.warn {
  color: #92400e;
  background: #fdf0d5;
}
.pill.err {
  color: #cf222e;
  background: #ffebe9;
}
.dark .pill.ok {
  color: #3fb950;
  background: #0d1117;
}
.dark .pill.warn {
  color: #d29922;
  background: #1c1206;
}
.dark .pill.err {
  color: #f85149;
  background: #2a1212;
}
.bc-verdict-detail {
  color: var(--vp-c-text-3);
  font-size: 0.85em;
}
.bc-note {
  margin-top: 14px;
  font-size: 0.82em;
  color: var(--vp-c-text-3);
  line-height: 1.6;
}
</style>
