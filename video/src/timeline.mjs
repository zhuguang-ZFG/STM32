import { animDuration, readAnim } from '../../docs/.vitepress/anim-decorate.mjs'
import { resolveScenes } from './spec.mjs'

export const MAX_STATIC_GAP = 6
export const BEAT_FADE = 0.18

// SMIL 时长来自 anim-decorate 的同一份解析逻辑（主循环 = 最大的那个 dur=）。
// 它返回字符串，这里统一成数字；拿不到就退化成"整段静止"。
export function masterDuration(name) {
  if (!name) return 0
  const raw = readAnim(name)
  const nums = [...raw.matchAll(/dur="([\d.]+)s"/g)].map((m) => Number(m[1])).filter((n) => n > 0)
  return nums.length ? Math.max(...nums) : Number(animDuration(raw)) || 0
}

function smilAt(mode, rel, sceneDur, t0, span) {
  if (mode === 'loop') return t0 + (rel % span)
  if (mode === 'once') return Math.min(t0 + span, t0 + rel)
  return t0 + (sceneDur > 0 ? rel / sceneDur : 0) * span
}

const lineCount = (src) => (src ? String(src).replace(/\n$/, '').split('\n').length : 0)
const lineTargets = (src, prefix = 'line') => Array.from({ length: lineCount(src) }, (_, i) => `${prefix}:${i}`)

export function sceneTargets(sc) {
  const title = sc.title ? ['title'] : []
  const kicker = sc.kicker ? ['kicker'] : []
  const sub = sc.sub ? ['sub'] : []
  const note = sc.note ? ['note'] : []
  const bullets = (sc.bullets || []).map((_, i) => `bullets:${i}`)
  switch (sc.kind) {
    case 'code': return [...title, ...lineTargets(sc.code), ...lineTargets(sc.codeB, 'codeB'), ...note]
    case 'hook': return [...title, ...sub, ...lineTargets(sc.code)]
    case 'card': return [...kicker, ...title, ...bullets, ...sub]
    case 'anim': return [...title, ...bullets, ...note]
    case 'outro': return [...title, ...bullets, ...sub, 'url']
    default: return []
  }
}

export function expandTargets(sc, reveal) {
  const m = String(reveal).match(/^(line|code|codeB|bullets):(\d+)-(\d+)$/)
  if (!m) return [reveal]
  const prefix = m[1] === 'code' ? 'line' : m[1]
  const a = Number(m[2]), b = Number(m[3])
  return Array.from({ length: b - a + 1 }, (_, i) => `${prefix}:${a + i}`)
}

function groupTargets(sc, n) {
  const lead = [], body = [], tail = []
  for (const t of sceneTargets(sc)) {
    if (t === 'title' || t === 'kicker' || (sc.kind === 'hook' && t === 'sub')) lead.push(t)
    else if (t === 'sub' || t === 'url' || t === 'note') tail.push(t)
    else body.push(t)
  }
  const beats = Array.from({ length: n }, () => ({ at: 0, kind: 'content', targets: [], captionIdx: -1 }))
  beats[0].targets.push(...lead)
  const slots = Math.max(1, n - 1)
  const per = Math.ceil(body.length / slots)
  body.forEach((t, i) => beats[Math.min(n - 1, 1 + Math.floor(i / per))].targets.push(t))
  beats[n - 1].targets.push(...tail)
  return beats
}

export function deriveBeats(sc, captions) {
  const sceneStart = sc.startFrame / (sc.fps || 30)
  const starts = captions.map((c) => Math.max(0, c.start - sceneStart))
  let beats
  if (sc.beatMap?.length) {
    // beatMap 的拍由作者逐句指定；没有 content 拍的字幕补 caption 空拍用于同步。
    // 首拍（i=0）是 0s 基线；i ≥ 1 的 at 超出本场字幕数时没有落点，直接构建失败。
    beats = sc.beatMap.map((b, i) => {
      if (i > 0 && b.at > captions.length) {
        throw new Error(`beatMap[${i}].at=${b.at} 超出本场字幕数 ${captions.length}`)
      }
      return {
        at: i === 0 ? 0 : Math.max(0, (captions[b.at - 1]?.start ?? sceneStart) - sceneStart),
        kind: 'content', targets: expandTargets(sc, b.reveal), captionIdx: b.at - 1,
      }
    })
    for (const [i, at] of starts.entries()) {
      if (!beats.some((b) => Math.abs(b.at - at) <= 0.05)) beats.push({ at, kind: 'caption', targets: [], captionIdx: i })
    }
  } else {
    const n = Math.max(2, starts.length)
    beats = groupTargets(sc, n).map((b, i) => ({
      ...b, at: i === 0 ? 0 : (starts[i] ?? Math.min(sc.duration, 1.2 * i)), captionIdx: i < starts.length ? i : -1,
    }))
  }
  beats.sort((a, b) => a.at - b.at)
  if (beats.length === 1) {
    const targets = beats[0].targets
    beats[0].targets = targets.slice(0, Math.max(1, Math.ceil(targets.length / 2)))
    beats.push({ at: Math.min(Math.max(0.8, sc.duration * 0.6), Math.max(0.8, sc.duration - 0.1)), kind: 'caption', targets: targets.slice(beats[0].targets.length), captionIdx: -1 })
  }
  const shown = new Set(beats.flatMap((b) => b.targets))
  const missing = sceneTargets(sc).filter((t) => !shown.has(t))
  if (missing.length) {
    const last = [...beats].reverse().find((b) => b.kind === 'content')
    if (last) last.targets.push(...missing)
  }
  const out = []
  for (const b of beats.sort((a, b) => a.at - b.at)) {
    if (out.length && Math.abs(out[out.length - 1].at - b.at) < 0.001) {
      out[out.length - 1].targets.push(...b.targets)
      continue
    }
    out.push(b)
  }
  for (let i = 0; i < out.length; i++) {
    const b = out[i]
    const next = i + 1 < out.length ? out[i + 1].at : sc.duration
    let t = b.at + MAX_STATIC_GAP
    const pulses = []
    while (t < next - 0.05) {
      pulses.push({ at: +t.toFixed(3), kind: 'pulse', targets: [], captionIdx: -1 })
      t += MAX_STATIC_GAP
    }
    if (pulses.length) out.splice(i + 1, 0, ...pulses)
  }
  out.forEach((b, i) => { b.index = i })
  return out
}

export function beatAt(beats, rel) {
  let i = 0
  while (i + 1 < beats.length && beats[i + 1].at <= rel) i++
  const b = beats[i]
  const dt = rel - b.at
  const phase = i === 0 ? 2 : Math.min(2, Math.floor(Math.max(0, dt) / BEAT_FADE))
  return {
    index: i, at: b.at, kind: b.kind, phase,
    targets: b.targets,
    revealed: [...new Set(beats.slice(0, i + 1).flatMap((x) => x.targets))],
  }
}

export function validateBeats(plan) {
  const issues = []
  let hookSecs = 0, inHook = true, beats = 0, pulses = 0, maxGap = 0
  for (const sc of plan.scenes) {
    const list = sc.beats || []
    if (!list.length) { issues.push(`${sc.id}: 没有节拍`); continue }
    if (list.length < 2) issues.push(`${sc.id}: 节拍 ${list.length} < 2`)
    beats += list.length
    pulses += list.filter((b) => b.kind === 'pulse').length
    let last = -1
    for (const b of list) {
      if (!(b.at > last)) issues.push(`${sc.id}: 节拍时间不递增 ${b.at}`)
      last = b.at
    }
    let gap = 0
    for (let i = 0; i < list.length; i++) gap = Math.max(gap, (list[i + 1]?.at ?? sc.duration) - list[i].at)
    maxGap = Math.max(maxGap, gap)
    // 与 pulse 插入的 0.05s 判据对齐：6.00–6.05s 的贴边空档不插 pulse，也不判失败。
    if ((sc.kind === 'code' || sc.kind === 'card') && gap > MAX_STATIC_GAP + 0.05) {
      issues.push(`${sc.id}: 静止 ${gap.toFixed(1)}s > ${MAX_STATIC_GAP}s`)
    }
    const shown = new Set(list.flatMap((b) => b.targets))
    for (const t of sceneTargets(sc)) if (!shown.has(t)) issues.push(`${sc.id}: ${t} 永远不会揭示`)
    // 第 1 句字幕的首拍锚定在 0s，TTS 起播留白（实测约 0.22s）不算脱拍。
    for (const [ci, cap] of plan.captions.filter((c) => c.scene === sc.id).entries()) {
      if (ci === 0) continue
      const at = cap.start - sc.startFrame / plan.fps
      if (!list.some((b) => Math.abs(b.at - at) <= 0.05)) issues.push(`${sc.id}: 字幕 ${at.toFixed(2)}s 没有对应节拍`)
    }
    if (inHook && sc.kind === 'hook') hookSecs += sc.duration
    else inHook = false
  }
  if (hookSecs > 15.0001) issues.push(`钩子 ${hookSecs.toFixed(1)}s > 15s`)
  if (issues.length) throw new Error(`节拍审计未通过:\n${issues.map((e) => `  - ${e}`).join('\n')}`)
  return { beats, pulses, maxGap, scenes: plan.scenes.length }
}

export function buildRenderPlan(ep, platform, timeline) {
  const scenes = resolveScenes(ep, platform)
  if (scenes.length !== timeline.scenes.length) {
    throw new Error(`时间轴场景数 ${timeline.scenes.length} 与 episode 的 ${scenes.length} 不一致，请重跑音频阶段`)
  }
  const fps = timeline.fps
  const plan = { platform, fps, totalFrames: timeline.totalFrames, scenes: [], captions: timeline.captions }

  scenes.forEach((sc, i) => {
    const ts = timeline.scenes[i]
    if (ts.id !== sc.id) throw new Error(`时间轴第 ${i} 项是 ${ts.id}，episode 里是 ${sc.id}`)
    const master = masterDuration(sc.anim)
    const t0 = master ? Math.min(sc.t0 || 0, master) : 0
    const t1 = master ? Math.min(sc.t1 || master, master) : 0
    plan.scenes.push({
      ...sc,
      index: i,
      startFrame: Math.round(ts.start * fps),
      frames: ts.frames,
      duration: ts.duration,
      anim: sc.anim || null,
      master,
      smilT0: t0,
      smilSpan: Math.max(0, t1 - t0),
      smilMode: sc.smil || (sc.anim ? 'stretch' : null),
    })
  })

  for (const sc of plan.scenes) {
    if (sc.anim && !sc.master) throw new Error(`场景 ${sc.id}: 读不到 ${sc.anim} 的 SMIL 时长`)
    if (sc.anim && sc.smilSpan <= 0) throw new Error(`场景 ${sc.id}: ${sc.anim} 的 t0/t1 区间为空，动画不会动`)
  }

  plan.formatVersion = ep.formatVersion ?? 1
  if (plan.formatVersion === 2) {
    for (const sc of plan.scenes) {
      sc.fps = plan.fps
      sc.beats = deriveBeats(sc, plan.captions.filter((c) => c.scene === sc.id))
    }
    plan.beatStats = validateBeats(plan)
  }
  return plan
}

// 转场相位：每场前 4 帧 0..3，第 5 帧起撤销。v1 没有节拍，恒为 -1。
export function transitionPhase(frameInScene) {
  return frameInScene < 4 ? frameInScene : -1
}

// 逐帧状态：渲染循环按场景推进，captionIdx 用游标避免每帧二分。
export function* iterateFrames(plan) {
  let captionIdx = 0
  for (const sc of plan.scenes) {
    for (let f = 0; f < sc.frames; f++) {
      const abs = (sc.startFrame + f) / plan.fps
      while (captionIdx < plan.captions.length - 1 && plan.captions[captionIdx].end <= abs) captionIdx++
      const cap = plan.captions[captionIdx]
      yield {
        scene: sc,
        frameInScene: f,
        rel: f / plan.fps,
        abs,
        smilTime: sc.anim ? smilAt(sc.smilMode, f / plan.fps, sc.duration, sc.smilT0, sc.smilSpan) : null,
        caption: cap && cap.start <= abs && abs < cap.end ? cap : null,
        captionIdx: cap && cap.start <= abs && abs < cap.end ? captionIdx : -1,
        beat: sc.beats ? beatAt(sc.beats, f / plan.fps) : null,
        transitionPhase: sc.beats ? transitionPhase(f) : -1,
      }
    }
  }
}

export function planSummary(plan) {
  const secs = plan.totalFrames / plan.fps
  const lines = plan.scenes.map(
    (s) => `  ${String(s.startFrame / plan.fps).padStart(7)}s +${s.duration.toFixed(2).padStart(6)}s  ${s.id.padEnd(24)}${s.anim ? ` ${s.anim} [${s.smilMode}]` : ''}`,
  )
  return [`📐 ${plan.platform}: ${plan.scenes.length} 个场景，${plan.totalFrames} 帧，${secs.toFixed(2)}s`, ...lines].join('\n')
}
