<script setup>
import { ref, computed, watch } from 'vue'
import gpiofModer from '../data/registers/gpiof-moder.json'

const props = defineProps({
  reg: { type: String, default: 'gpiof-moder' },
  highlight: { type: String, default: '' },
})

const regMap = {
  'gpiof-moder': () => import('../data/registers/gpiof-moder.json'),
  'rcc-pllcfg': () => import('../data/registers/rcc-pllcfg.json'),
}

const reg = ref(null)
const selectedField = ref(null)
const editValues = ref({})

async function loadReg(name) {
  const loader = regMap[name]
  if (loader) {
    const mod = await loader()
    reg.value = mod.default
    editValues.value = {}
    reg.value.fields.forEach(f => {
      const raw = f.reset
      if (raw.startsWith('0b')) {
        editValues.value[f.name] = parseInt(raw.slice(2), 2) || 0
      } else if (raw.startsWith('0x')) {
        editValues.value[f.name] = parseInt(raw.slice(2), 16) || 0
      } else {
        editValues.value[f.name] = parseInt(raw) || 0
      }
    })
  }
}

watch(() => props.reg, loadReg, { immediate: true })

const bitColors = ['#3451b2', '#3eaf7c', '#d97706', '#dc2626', '#666', '#1a7f56', '#92400e', '#94a3b8']

function fieldColor(idx) {
  return bitColors[idx % bitColors.length]
}

function bitWidth(f) {
  return Array.isArray(f.bits) ? f.bits[0] - f.bits[1] + 1 : 1
}

function bitStart(f) {
  return Array.isArray(f.bits) ? f.bits[1] : f.bits
}

const hexValue = computed(() => {
  if (!reg.value) return '0x00000000'
  let val = 0
  reg.value.fields.forEach(f => {
    const v = editValues.value[f.name] || 0
    const shift = bitStart(f)
    const mask = (1 << bitWidth(f)) - 1
    val |= (v & mask) << shift
  })
  return '0x' + (val >>> 0).toString(16).toUpperCase().padStart(8, '0')
})

function selectField(f) {
  selectedField.value = selectedField.value?.name === f.name ? null : f
}
</script>

<template>
  <div v-if="reg" class="reg-explorer">
    <div class="reg-header">
      <div class="reg-title-row">
        <span class="reg-name">{{ reg.name }}</span>
        <span class="reg-addr">{{ reg.address }}</span>
        <span class="reg-rm">{{ reg.rmRef }}</span>
      </div>
      <div class="reg-full-name">{{ reg.fullName }}</div>
      <div class="reg-hex">
        <span class="reg-hex-label">当前值</span>
        <span class="reg-hex-value">{{ hexValue }}</span>
        <span class="reg-reset">复位值: {{ reg.resetValue }}</span>
      </div>
    </div>

    <div class="reg-bitfield">
      <div class="bit-numbers">
        <span v-for="i in 32" :key="i" class="bit-num">{{ 32 - i }}</span>
      </div>
      <div class="bit-fields">
        <div
          v-for="(f, idx) in reg.fields"
          :key="f.name"
          class="field"
          :class="{ 'field-selected': selectedField?.name === f.name, 'field-highlight': highlight && f.name.toLowerCase().includes(highlight.toLowerCase()) }"
          :style="{
            flex: bitWidth(f),
            backgroundColor: selectedField?.name === f.name ? fieldColor(idx) + '22' : undefined,
            borderColor: fieldColor(idx),
          }"
          @click="selectField(f)"
        >
          <span class="field-name">{{ f.name }}</span>
          <span class="field-bits">[{{ Array.isArray(f.bits) ? f.bits[0] + ':' + f.bits[1] : f.bits }}]</span>
        </div>
      </div>
    </div>

    <div v-if="selectedField" class="reg-detail">
      <div class="detail-row">
        <span class="detail-label">字段</span>
        <span class="detail-value">{{ selectedField.name }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">位</span>
        <span class="detail-value">[{{ Array.isArray(selectedField.bits) ? selectedField.bits[0] + ':' + selectedField.bits[1] : selectedField.bits }}] ({{ bitWidth(selectedField) }} bit)</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">复位值</span>
        <span class="detail-value">{{ selectedField.reset }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">访问</span>
        <span class="detail-value">{{ selectedField.access }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">说明</span>
        <span class="detail-value detail-desc">{{ selectedField.desc }}</span>
      </div>
      <div v-if="bitWidth(selectedField) <= 4" class="detail-row">
        <span class="detail-label">设值</span>
        <div class="detail-input-group">
          <input
            type="range"
            :min="0"
            :max="(1 << bitWidth(selectedField)) - 1"
            :value="editValues[selectedField.name] || 0"
            @input="editValues[selectedField.name] = +$event.target.value"
            class="detail-slider"
          />
          <span class="detail-input-val">{{ (editValues[selectedField.name] || 0).toString(2).padStart(bitWidth(selectedField), '0') }} ({{ editValues[selectedField.name] || 0 }})</span>
        </div>
      </div>
    </div>

    <div v-else class="reg-hint">点击位域查看详细说明</div>
  </div>
</template>

<style scoped>
.reg-explorer {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--mcu-anim-bg);
  padding: 16px;
  margin: 16px 0;
  font-size: 0.88rem;
}
.reg-header {
  margin-bottom: 12px;
}
.reg-title-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.reg-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--mcu-anim-brand);
  font-family: var(--vp-font-family-mono);
}
.reg-addr {
  font-family: var(--vp-font-family-mono);
  font-size: 0.82rem;
  color: var(--mcu-anim-sub);
}
.reg-rm {
  font-size: 0.78rem;
  color: var(--mcu-anim-muted);
}
.reg-full-name {
  font-size: 0.82rem;
  color: var(--mcu-anim-sub);
  margin-top: 2px;
}
.reg-hex {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 6px 10px;
  background: var(--mcu-anim-card);
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
}
.reg-hex-label {
  font-size: 0.78rem;
  color: var(--mcu-anim-muted);
}
.reg-hex-value {
  font-family: var(--vp-font-family-mono);
  font-weight: 600;
  color: var(--mcu-anim-brand);
  font-size: 1rem;
}
.reg-reset {
  margin-left: auto;
  font-size: 0.78rem;
  color: var(--mcu-anim-muted);
  font-family: var(--vp-font-family-mono);
}
.reg-bitfield {
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  overflow: hidden;
  background: var(--mcu-anim-card);
}
.bit-numbers {
  display: flex;
  border-bottom: 1px solid var(--vp-c-divider);
  background: var(--mcu-anim-panel);
}
.bit-num {
  flex: 1;
  text-align: center;
  font-size: 0.65rem;
  font-family: var(--vp-font-family-mono);
  color: var(--mcu-anim-muted);
  padding: 2px 0;
}
.bit-fields {
  display: flex;
  min-height: 48px;
}
.field {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px 2px;
  border-right: 2px solid;
  cursor: pointer;
  transition: background-color 0.15s ease;
  min-width: 0;
  overflow: hidden;
}
.field:last-child {
  border-right: none;
}
.field:hover {
  filter: brightness(0.96);
}
.field-selected {
  box-shadow: inset 0 0 0 2px currentColor;
}
.field-highlight {
  background: var(--mcu-anim-wash-amber);
}
.field-name {
  font-size: 0.7rem;
  font-weight: 600;
  font-family: var(--vp-font-family-mono);
  color: var(--mcu-anim-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.field-bits {
  font-size: 0.6rem;
  color: var(--mcu-anim-muted);
  font-family: var(--vp-font-family-mono);
}
.reg-detail {
  margin-top: 12px;
  padding: 12px;
  background: var(--mcu-anim-card);
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
}
.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 4px 0;
}
.detail-row + .detail-row {
  border-top: 1px solid var(--vp-c-divider);
}
.detail-label {
  font-size: 0.78rem;
  color: var(--mcu-anim-muted);
  min-width: 48px;
  flex-shrink: 0;
}
.detail-value {
  font-family: var(--vp-font-family-mono);
  font-size: 0.85rem;
  color: var(--mcu-anim-ink);
}
.detail-desc {
  font-family: inherit;
  color: var(--mcu-anim-sub);
  line-height: 1.5;
}
.detail-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.detail-slider {
  flex: 1;
  accent-color: var(--mcu-anim-brand);
}
.detail-input-val {
  font-family: var(--vp-font-family-mono);
  font-size: 0.82rem;
  color: var(--mcu-anim-brand);
  min-width: 80px;
}
.reg-hint {
  margin-top: 8px;
  text-align: center;
  font-size: 0.78rem;
  color: var(--mcu-anim-muted);
}
</style>
