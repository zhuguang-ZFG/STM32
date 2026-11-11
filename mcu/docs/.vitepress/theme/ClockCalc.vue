<script setup>
import { ref, computed, watch } from 'vue'

const families = {
  stm32f4: {
    label: 'STM32F407',
    maxSysclk: 168,
    vcoInMin: 1, vcoInMax: 2,
    vcoOutMin: 100, vcoOutMax: 432,
    pllM: [2, 63], pllN: [50, 432], pllP: [2, 4], pllQ: [2, 15],
    hseRange: [4, 26], hseDefault: 8,
    apb1Max: 42, apb2Max: 84,
    flashWs: [
      { ws: 0, max: 30 }, { ws: 1, max: 60 }, { ws: 2, max: 90 },
      { ws: 3, max: 120 }, { ws: 4, max: 150 }, { ws: 5, max: 168 },
    ],
    note: 'PLLP 仅 /2 或 /4；VCO/PLLQ 须 = 48 MHz（USB OTG FS）',
  },
  gd32f4: {
    label: 'GD32F450',
    maxSysclk: 200,
    vcoInMin: 1, vcoInMax: 2,
    vcoOutMin: 100, vcoOutMax: 432,
    pllM: [2, 63], pllN: [50, 432], pllP: [2, 4], pllQ: [2, 15],
    hseRange: [4, 32], hseDefault: 25,
    apb1Max: 50, apb2Max: 100,
    flashWs: [
      { ws: 0, max: 30 }, { ws: 1, max: 60 }, { ws: 2, max: 90 },
      { ws: 3, max: 120 }, { ws: 4, max: 150 }, { ws: 5, max: 180 },
      { ws: 6, max: 200 },
    ],
    note: 'CK48M 可切 IRC48M（片内 48 MHz RC），PLLQ 不必精确 48 MHz',
  },
  gd32vf: {
    label: 'GD32VF103',
    maxSysclk: 108,
    predv0: [1, 16],
    pllmf: [2, 32],
    hseRange: [4, 32], hseDefault: 8,
    note: '无 VCO 概念；PLLMF 含 ×6.5 特例；PLL1/PLL2 仅供 USB/I2S',
    special: true,
  },
}

const family = ref('stm32f4')
const hseFreq = ref(8)

const M = ref(4)
const N = ref(168)
const P = ref(2)
const Q = ref(7)

const PREDV0 = ref(2)
const PLLMF = ref(27)

const ahbDiv = ref(1)
const apb1Div = ref(4)
const apb2Div = ref(2)

watch(family, (f) => {
  const cfg = families[f]
  hseFreq.value = cfg.hseDefault
  if (f === 'gd32vf') {
    PREDV0.value = 2
    PLLMF.value = 27
  } else {
    M.value = f === 'gd32f4' ? 25 : 4
    N.value = f === 'gd32f4' ? 400 : 336
    P.value = 2
    Q.value = f === 'gd32f4' ? 9 : 7
  }
  ahbDiv.value = 1
  apb1Div.value = f === 'gd32f4' ? 4 : 4
  apb2Div.value = 2
})

const cfg = computed(() => families[family.value])

const isVF = computed(() => family.value === 'gd32vf')

const vcoIn = computed(() => {
  if (isVF.value) return null
  return hseFreq.value / M.value
})

const vcoOut = computed(() => {
  if (isVF.value) return null
  return vcoIn.value * N.value
})

const sysclk = computed(() => {
  if (isVF.value) {
    const inputAfterPredv = hseFreq.value / PREDV0.value
    return inputAfterPredv * PLLMF.value
  }
  return vcoOut.value / P.value
})

const usbFreq = computed(() => {
  if (isVF.value) return null
  return vcoOut.value / Q.value
})

const hclk = computed(() => sysclk.value / ahbDiv.value)
const pclk1 = computed(() => hclk.value / apb1Div.value)
const pclk2 = computed(() => hclk.value / apb2Div.value)

const timClk1 = computed(() => apb1Div.value === 1 ? pclk1.value : pclk1.value * 2)
const timClk2 = computed(() => apb2Div.value === 1 ? pclk2.value : pclk2.value * 2)

const vcoInOk = computed(() => {
  if (isVF.value) return true
  const v = vcoIn.value
  return v >= cfg.value.vcoInMin && v <= cfg.value.vcoInMax
})

const vcoOutOk = computed(() => {
  if (isVF.value) return true
  const v = vcoOut.value
  return v >= cfg.value.vcoOutMin && v <= cfg.value.vcoOutMax
})

const sysclkOk = computed(() => sysclk.value <= cfg.value.maxSysclk && sysclk.value > 0)

const usbOk = computed(() => {
  if (isVF.value) return true
  return Math.abs(usbFreq.value - 48) <= 0.5
})

const flashWs = computed(() => {
  const table = cfg.value.flashWs
  if (!table) return null
  for (const row of table) {
    if (sysclk.value <= row.max) return row.ws
  }
  return table[table.length - 1].ws + 1
})

const hseOk = computed(() => {
  const r = cfg.value.hseRange
  return hseFreq.value >= r[0] && hseFreq.value <= r[1]
})

function fmt(n) {
  if (n == null) return '—'
  return Number.isInteger(n) ? n.toString() : n.toFixed(2)
}

function fmtMhz(n) {
  if (n == null) return '—'
  return n.toFixed(3) + ' MHz'
}

function pillClass(ok) {
  return ok ? 'pill ok' : 'pill err'
}

const vfPllmfOptions = computed(() => {
  const opts = []
  for (let i = 2; i <= 32; i++) opts.push(i)
  opts.push(6.5)
  opts.sort((a, b) => a - b)
  return opts
})
</script>

<template>
  <div class="clock-calc">
    <div class="cc-header">
      <span class="cc-title">PLL 时钟计算器</span>
      <div class="cc-family-tabs">
        <button
          v-for="(f, key) in families" :key="key"
          :class="['cc-tab', { active: family === key }]"
          @click="family = key"
        >{{ f.label }}</button>
      </div>
    </div>

    <div class="cc-grid">
      <div class="cc-panel">
        <h4>时钟源</h4>
        <label class="cc-row">
          <span>HSE 晶振</span>
          <input type="number" v-model.number="hseFreq" :min="cfg.hseRange[0]" :max="cfg.hseRange[1]" step="1" />
          <span class="cc-unit">MHz</span>
        </label>
        <span :class="pillClass(hseOk)" v-if="!hseOk">
          HSE 超出范围 ({{ cfg.hseRange[0] }}–{{ cfg.hseRange[1] }} MHz)
        </span>

        <template v-if="!isVF">
          <h4>PLL 参数</h4>
          <label class="cc-row">
            <span>PLLM (÷M)</span>
            <input type="range" v-model.number="M" :min="cfg.pllM[0]" :max="cfg.pllM[1]" />
            <span class="cc-val">{{ M }}</span>
          </label>
          <label class="cc-row">
            <span>PLLN (×N)</span>
            <input type="range" v-model.number="N" :min="cfg.pllN[0]" :max="cfg.pllN[1]" />
            <span class="cc-val">{{ N }}</span>
          </label>
          <label class="cc-row">
            <span>PLLP (÷P)</span>
            <select v-model.number="P">
              <option :value="2">/2</option>
              <option :value="4">/4</option>
            </select>
          </label>
          <label class="cc-row">
            <span>PLLQ (÷Q)</span>
            <input type="range" v-model.number="Q" :min="cfg.pllQ[0]" :max="cfg.pllQ[1]" />
            <span class="cc-val">{{ Q }}</span>
          </label>
        </template>

        <template v-else>
          <h4>PLL 参数</h4>
          <label class="cc-row">
            <span>PREDV0 (÷)</span>
            <input type="range" v-model.number="PREDV0" :min="cfg.predv0[0]" :max="cfg.predv0[1]" />
            <span class="cc-val">{{ PREDV0 }}</span>
          </label>
          <label class="cc-row">
            <span>PLLMF (×)</span>
            <select v-model.number="PLLMF">
              <option v-for="v in vfPllmfOptions" :key="v" :value="v">×{{ v }}</option>
            </select>
          </label>
        </template>

        <h4>总线分频</h4>
        <label class="cc-row">
          <span>AHB (÷)</span>
          <select v-model.number="ahbDiv">
            <option v-for="d in [1,2,4,8,16,64,128,256,512]" :key="d" :value="d">/{{ d }}</option>
          </select>
        </label>
        <label class="cc-row">
          <span>APB1 (÷)</span>
          <select v-model.number="apb1Div">
            <option v-for="d in [1,2,4,8,16]" :key="d" :value="d">/{{ d }}</option>
          </select>
        </label>
        <label class="cc-row">
          <span>APB2 (÷)</span>
          <select v-model.number="apb2Div">
            <option v-for="d in [1,2,4,8,16]" :key="d" :value="d">/{{ d }}</option>
          </select>
        </label>
      </div>

      <div class="cc-panel cc-results">
        <h4>计算结果</h4>
        <template v-if="!isVF">
          <div class="cc-result-row">
            <span class="cc-label">VCO 输入</span>
            <span class="cc-freq">{{ fmtMhz(vcoIn) }}</span>
            <span :class="pillClass(vcoInOk)">{{ vcoInOk ? '✓' : '✗' }} {{ cfg.vcoInMin }}–{{ cfg.vcoInMax }} MHz</span>
          </div>
          <div class="cc-result-row">
            <span class="cc-label">VCO 输出</span>
            <span class="cc-freq">{{ fmtMhz(vcoOut) }}</span>
            <span :class="pillClass(vcoOutOk)">{{ vcoOutOk ? '✓' : '✗' }} {{ cfg.vcoOutMin }}–{{ cfg.vcoOutMax }} MHz</span>
          </div>
        </template>
        <div class="cc-result-row cc-highlight">
          <span class="cc-label">SYSCLK</span>
          <span class="cc-freq cc-big">{{ fmtMhz(sysclk) }}</span>
          <span :class="pillClass(sysclkOk)">{{ sysclkOk ? '✓' : '✗' }} ≤ {{ cfg.maxSysclk }} MHz</span>
        </div>
        <div class="cc-result-row" v-if="!isVF">
          <span class="cc-label">USB (VCO/Q)</span>
          <span class="cc-freq">{{ fmtMhz(usbFreq) }}</span>
          <span :class="pillClass(usbOk)">{{ usbOk ? '✓ 48 MHz' : '✗ ≠ 48 MHz' }}</span>
        </div>

        <h4>总线时钟</h4>
        <div class="cc-bus-grid">
          <div class="cc-bus-item">
            <span class="cc-bus-name">HCLK (AHB)</span>
            <span class="cc-bus-val">{{ fmtMhz(hclk) }}</span>
          </div>
          <div class="cc-bus-item">
            <span class="cc-bus-name">PCLK1 (APB1)</span>
            <span class="cc-bus-val">{{ fmtMhz(pclk1) }}</span>
          </div>
          <div class="cc-bus-item">
            <span class="cc-bus-name">PCLK2 (APB2)</span>
            <span class="cc-bus-val">{{ fmtMhz(pclk2) }}</span>
          </div>
          <div class="cc-bus-item">
            <span class="cc-bus-name">TIM 时钟 (APB1)</span>
            <span class="cc-bus-val">{{ fmtMhz(timClk1) }}</span>
            <span class="cc-bus-note" v-if="apb1Div !== 1">×2</span>
          </div>
          <div class="cc-bus-item">
            <span class="cc-bus-name">TIM 时钟 (APB2)</span>
            <span class="cc-bus-val">{{ fmtMhz(timClk2) }}</span>
            <span class="cc-bus-note" v-if="apb2Div !== 1">×2</span>
          </div>
        </div>

        <div v-if="flashWs != null" class="cc-flash">
          <span class="cc-label">Flash 等待周期</span>
          <span class="cc-freq">{{ flashWs }} WS</span>
        </div>

        <p class="cc-note">{{ cfg.note }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.clock-calc {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 20px;
  background: var(--vp-c-bg-soft);
  font-family: system-ui, sans-serif;
}
.cc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.cc-title {
  font-size: 1.1em;
  font-weight: 700;
  color: var(--vp-c-brand-1);
}
.cc-family-tabs {
  display: flex;
  gap: 6px;
}
.cc-tab {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  cursor: pointer;
  font-size: 0.85em;
  transition: all 0.15s;
}
.cc-tab.active {
  background: var(--vp-c-brand-1);
  color: #fff;
  border-color: var(--vp-c-brand-1);
}
.cc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 640px) {
  .cc-grid { grid-template-columns: 1fr; }
}
.cc-panel h4 {
  font-size: 0.85em;
  color: var(--vp-c-text-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 12px 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--vp-c-divider);
}
.cc-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 0.9em;
}
.cc-row span:first-child {
  min-width: 80px;
  color: var(--vp-c-text-2);
}
.cc-row input[type="range"] {
  flex: 1;
  accent-color: var(--vp-c-brand-1);
}
.cc-row input[type="number"],
.cc-row select {
  width: 70px;
  padding: 2px 6px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 4px;
  background: var(--vp-c-bg);
  font-size: 0.9em;
}
.cc-unit {
  color: var(--vp-c-text-3);
  font-size: 0.8em;
}
.cc-val {
  min-width: 32px;
  text-align: right;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--vp-c-brand-1);
}
.cc-result-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 0.9em;
}
.cc-highlight {
  background: var(--vp-c-brand-soft);
  border-radius: 6px;
  padding: 6px 10px;
  margin: 8px 0;
}
.cc-label {
  min-width: 90px;
  color: var(--vp-c-text-2);
}
.cc-freq {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.cc-big {
  font-size: 1.15em;
  color: var(--vp-c-brand-1);
}
.pill {
  font-size: 0.75em;
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: auto;
}
.pill.ok {
  color: #1a7f37;
  background: #dafbe1;
}
.pill.err {
  color: #cf222e;
  background: #ffebe9;
}
:root.dark .pill.ok {
  color: #3fb950;
  background: #0d1117;
}
:root.dark .pill.err {
  color: #f85149;
  background: #1c1206;
}
.cc-bus-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 12px;
}
.cc-bus-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85em;
  padding: 3px 0;
}
.cc-bus-name {
  color: var(--vp-c-text-2);
  min-width: 100px;
}
.cc-bus-val {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.cc-bus-note {
  font-size: 0.75em;
  color: var(--vp-c-accent);
  background: var(--vp-c-brand-soft);
  padding: 0 4px;
  border-radius: 3px;
}
.cc-flash {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 6px 10px;
  background: var(--vp-c-bg);
  border-radius: 6px;
  font-size: 0.9em;
}
.cc-note {
  margin-top: 12px;
  font-size: 0.8em;
  color: var(--vp-c-text-3);
  line-height: 1.5;
}
</style>
