// 程序化 SFX：不读外部资产、不带上屏文案，只按 v2 的节拍表合成一条 WAV。
// 每个节拍恰好一个音效；同一条事件表每次合成逐样本相同（PRNG 固定种子），
// 这样母版重渲和像素级回归一样能对得上。
import { writeFileSync } from 'node:fs'

const RATE = 44100

// mulberry32：短、无依赖、跨 Node 版本输出稳定。
function mulberry32(a) {
  return function () {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function tone(kind, n, sr, rnd) {
  const out = new Float32Array(n)
  let phase = 0
  for (let i = 0; i < n; i++) {
    const t = i / sr
    if (kind === 'click') {
      out[i] = Math.sin(2 * Math.PI * 1000 * t) * Math.exp(-t / 0.02) * 0.7 + (rnd() * 2 - 1) * Math.exp(-t / 0.004) * 0.25
    } else if (kind === 'whoosh') {
      const f = 400 + 1600 * (i / n)
      phase += (2 * Math.PI * f) / sr
      out[i] = (Math.sin(phase) * 0.35 + (rnd() * 2 - 1) * 0.15) * Math.sin((Math.PI * i) / n)
    } else if (kind === 'relay') {
      out[i] = Math.sign(Math.sin(2 * Math.PI * 180 * t)) * 0.35 * Math.exp(-t / 0.01) + (rnd() * 2 - 1) * 0.1 * Math.exp(-t / 0.01)
    } else {
      const a = Math.min(1, i / (n * 0.02))
      out[i] = (Math.sin(2 * Math.PI * 660 * t) * 0.5 + Math.sin(2 * Math.PI * 990 * t) * 0.3) * Math.exp(-t / 0.35) * a
    }
  }
  return out
}

const LEN = { click: 0.08, whoosh: 0.18, relay: 0.03, sting: 1.2 }
const GAIN = { click: 0.35, whoosh: 0.25, relay: 0.3, sting: 0.4 }

// 一场一拍：pulse → relay（走带计数），动画场 → whoosh，代码/卡片 → click，
// 其余场第一拍 → sting、后续拍 → whoosh。scene 与 beat 只用于对账，不进音频。
export function buildSfxEvents(plan) {
  const out = []
  for (const sc of plan.scenes) {
    const start = sc.startFrame / plan.fps
    for (const b of sc.beats || []) {
      const kind = b.kind === 'pulse' ? 'relay'
        : sc.kind === 'anim' ? 'whoosh'
        : sc.kind === 'code' || sc.kind === 'card' ? 'click'
        : b.index === 0 ? 'sting' : 'whoosh'
      out.push({ t: +(start + b.at).toFixed(3), kind, scene: sc.id, beat: b.index })
    }
  }
  return out.sort((a, b) => a.t - b.t)
}

export function renderSfxBuffer(events, { duration, sampleRate = RATE, channels = 2 }) {
  const frames = Math.max(0, Math.round(duration * sampleRate))
  const pcm = new Float32Array(frames * channels)
  const rnd = mulberry32(0x5f3759df)
  for (const ev of events) {
    if (!Number.isFinite(ev.t) || ev.t < 0) continue
    const at = Math.round(ev.t * sampleRate)
    // 尾巴越界就截到片尾；起点已在片尾之后则整条丢弃。
    const n = Math.min(Math.round((LEN[ev.kind] || 0.1) * sampleRate), frames - at)
    if (n <= 0) continue
    const sig = tone(ev.kind, n, sampleRate, rnd)
    for (let i = 0; i < n; i++) {
      const v = sig[i] * (GAIN[ev.kind] || 0.3)
      for (let c = 0; c < channels; c++) pcm[(at + i) * channels + c] += v
    }
  }
  // 多事件叠在一起也不许越界：16-bit PCM 之前统一夹到 [-1, 1]。
  for (let i = 0; i < pcm.length; i++) pcm[i] = Math.max(-1, Math.min(1, pcm[i]))
  return { pcm, sampleRate, channels }
}

export function wavFromBuffer({ pcm, sampleRate, channels }) {
  const data = Buffer.alloc(44 + pcm.length * 2)
  data.write('RIFF', 0)
  data.writeUInt32LE(36 + pcm.length * 2, 4)
  data.write('WAVE', 8)
  data.write('fmt ', 12)
  data.writeUInt32LE(16, 16)
  data.writeUInt16LE(1, 20)
  data.writeUInt16LE(channels, 22)
  data.writeUInt32LE(sampleRate, 24)
  data.writeUInt32LE(sampleRate * channels * 2, 28)
  data.writeUInt16LE(channels * 2, 32)
  data.writeUInt16LE(16, 34)
  data.write('data', 36)
  data.writeUInt32LE(pcm.length * 2, 40)
  for (let i = 0; i < pcm.length; i++) data.writeInt16LE(Math.round(pcm[i] * 32767), 44 + i * 2)
  return data
}

export function renderSfx(events, { duration, outPath, sampleRate = RATE, channels = 2 }) {
  if (!outPath) throw new Error('renderSfx 需要 outPath')
  writeFileSync(outPath, wavFromBuffer(renderSfxBuffer(events, { duration, sampleRate, channels })))
  return { path: outPath, events }
}
