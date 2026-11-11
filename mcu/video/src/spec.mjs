import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { ANIM_DIR, EPISODES_DIR } from './util.mjs'

export const KINDS = ['hook', 'anim', 'code', 'card', 'outro']
export const SMIL_MODES = ['stretch', 'loop', 'once']
export const FORMAT_VERSIONS = [1, 2]
export const V2_VOICES = ['zh-CN-YunyangNeural']
const V2_SECTION_RANGE = [3, 6]
const REVEAL_RE = /^(title|sub|note|kicker|url|code:\d+-\d+|codeB:\d+-\d+|bullets:\d+-\d+|line:\d+-\d+)$/

// 旁白时长估算：每字秒数 + 每场固定留白，见下面 validateEpisode 里的回归出处
export const SEC_PER_CHAR = {
  bilibili: { char: 0.1955, perScene: 0 },
  douyin: { char: 0.1946, perScene: 1.091 },
}

export const PLATFORM_DEFAULTS = {
  bilibili: { size: [1920, 1080], fps: 30, safe: { top: 60, right: 60, bottom: 150, left: 60 } },
  douyin: { size: [1080, 1920], fps: 30, safe: { top: 200, right: 160, bottom: 300, left: 100 } },
}

export function episodePath(id) {
  return join(EPISODES_DIR, id, 'episode.json')
}

// 抖音短版常只改旁白（要 60 秒讲完），画面复用 B 站长版，避免两处维护同一批 scene。
// pick 给定时按这个顺序挑，是"同素材重排的短版"而不是把长版调快。
export function resolveScenes(ep, platform) {
  const cfg = ep.platforms[platform]
  if (!cfg) throw new Error(`episode 里没有平台 ${platform}`)
  if (cfg.scenes) return cfg.scenes
  if (cfg.reuseFrom) {
    const src = ep.platforms[cfg.reuseFrom]
    if (src?.scenes) {
      const overrides = cfg.narration || {}
      const sets = cfg.set || {}
      const byId = new Map(src.scenes.map((sc) => [sc.id, sc]))
      const list = cfg.pick ? cfg.pick.map((sid) => byId.get(sid) ?? { id: sid, __missing: true }) : src.scenes
      // set 按字段覆盖任意一项。竖屏放不下横版那条 120 字符的取证输出、也放不下
      // 不断行的 19 字大标题，只能让抖音带一份自己的 code/title——
      // 而不是把 scene 整份复制出来两处维护。
      return list.map((sc) => {
        const out = { ...sc }
        if (overrides[sc.id]) {
          // 旁白换了，源 scene 的 ttsText 是照着旧旁白写的发音文，留着会让耳朵和字幕对不上：
          // 删掉后由 narrationJobs 从新旁白展开（或由下面的 set 显式给平台自己的 ttsText）。
          delete out.ttsText
          out.narration = overrides[sc.id]
        }
        return sets[sc.id] ? { ...out, ...sets[sc.id] } : out
      })
    }
    throw new Error(`平台 ${platform}: reuseFrom="${cfg.reuseFrom}" 没有 scenes`)
  }
  throw new Error(`平台 ${platform}: 既没有 scenes 也没有可用的 reuseFrom`)
}

function check(cond, msg, errs) {
  if (!cond) errs.push(msg)
}

// 页头「第 i/n 节 · title」的数据源。platforms[p].sections 声明分节边界，
// `at` 是该场第一幕的 scene id，一节管到下一节开始为止。
// 缺省返回全 null——旧稿没有这个字段时，页头必须与改版前逐字节相同（回归口径）。
// 首节之前的场次（比如没归进任何一节的片头）也是 null，页头保持旧文案。
export function sceneSections(scenes, sections) {
  if (!sections?.length) return scenes.map(() => null)
  const byScene = new Map(sections.map((s, j) => [s.at, j]))
  const n = sections.length
  let k = -1
  return scenes.map((sc) => {
    const j = byScene.get(sc.id)
    if (j !== undefined) k = j
    return k < 0 ? null : { i: k + 1, n, title: sections[k].title }
  })
}

// 12 字是页头字号（1.7u≈18.4px）下竖版 860px 可用宽的实测上限，不是拍脑袋：
// 改版后 fill-probe 会量出真实占宽，宽度不够就先减字、不是先缩字号——
// 页头一缩字号就撞审计的 16px 地板。
export const SECTION_TITLE_MAX = 12

function validateSections(sections, scenes, name, errs) {
  if (!sections?.length) return
  const seenAt = new Set()
  let lastIdx = -1
  for (const [j, s] of sections.entries()) {
    const at = `${name}.sections[${j}]`
    const idx = scenes.findIndex((sc) => sc.id === s.at)
    // 命不中真实 id、顺序乱是写错稿。静默退回旧页头会把错误一路带到成片里，
    // 而页头文本每帧都在画面中，错了没有第二处能看出来。
    check(idx >= 0, `${at}: at="${s.at}" 不是平台 ${name} 里的真实 scene id`, errs)
    check(!seenAt.has(s.at), `${at}: at="${s.at}" 与其它节重复`, errs)
    seenAt.add(s.at)
    check(s.title?.trim(), `${at}: 缺 title`, errs)
    const len = s.title?.trim().length || 0
    check(len <= SECTION_TITLE_MAX, `${at}: title ${len} 字，超过页头宽度上限 ${SECTION_TITLE_MAX} 字（先减字，别指望 fitAll 缩字号）`, errs)
    if (idx >= 0) {
      check(idx > lastIdx, `${at}: at="${s.at}" 在 scenes 里是第 ${idx} 场，不大于上一节的 ${lastIdx}（分节必须按场次递增）`, errs)
      lastIdx = idx
    }
  }
}

function lineCount(src) {
  return src ? String(src).replace(/\n$/, '').split('\n').length : 0
}

function rangeOf(spec) {
  const m = String(spec).match(/:(\d+)-(\d+)$/)
  return m ? [Number(m[1]), Number(m[2])] : null
}

function validateBeatMap(sc, at, errs) {
  if (sc.beatMap === undefined) return
  if (!Array.isArray(sc.beatMap) || !sc.beatMap.length) {
    errs.push(`${at}: beatMap 必须是非空数组`)
    return
  }
  let last = 0
  for (const [i, b] of sc.beatMap.entries()) {
    const p = `${at}.beatMap[${i}]`
    // 单项写坏（null、字符串、数组）只报这一项，不能把整份 episode 的校验抛崩。
    if (!b || typeof b !== 'object' || Array.isArray(b)) {
      errs.push(`${p}: beatMap 项必须是对象`)
      continue
    }
    // 首拍锚定 scene 起点（caption 1 / 0 s）：at > 1 会被 Task 3 的
    // captions[at-1] 错位或静默退回场首，必须在这里拦下。
    if (i === 0 && Number.isInteger(b.at) && b.at !== 1) {
      errs.push(`${p}: 第一拍 at 必须是 1（场景基线）`)
    }
    if (!Number.isInteger(b.at) || b.at < 1) errs.push(`${p}: at 必须是 ≥1 的整数（1-based 字幕序号）`)
    else if (b.at <= last) errs.push(`${p}: at=${b.at} 必须大于上一拍 ${last}`)
    else last = b.at
    if (typeof b.reveal !== 'string' || !REVEAL_RE.test(b.reveal)) {
      errs.push(`${p}: reveal="${b.reveal}" 不在允许形状内`)
      continue
    }
    const range = rangeOf(b.reveal)
    if (!range) continue
    const [a, c] = range
    if (a > c) errs.push(`${p}: ${b.reveal} 起止倒置`)
    const kind = b.reveal.split(':')[0]
    const max = kind === 'bullets' ? (sc.bullets?.length || 0)
      : kind === 'codeB' ? lineCount(sc.codeB)
        : lineCount(sc.code)
    if (c >= max) errs.push(`${p}: ${b.reveal} 越界（共 ${max} 行/条）`)
  }
}

function validateEmphasis(sc, at, errs) {
  if (sc.emphasis === undefined) return
  if (!Array.isArray(sc.emphasis)) { errs.push(`${at}: emphasis 必须是数组`); return }
  const hay = [sc.title, sc.sub, sc.note, sc.kicker, sc.code, sc.codeB, ...(sc.bullets || [])].filter(Boolean).join('\n')
  for (const e of sc.emphasis) {
    if (typeof e !== 'string' || !e.trim()) errs.push(`${at}: emphasis 里有空值`)
    else if (!hay.includes(e)) errs.push(`${at}: emphasis "${e}" 不在这一场的上屏文本里`)
  }
}

function validateLexicon(lex, errs) {
  if (lex === undefined) return
  if (!lex || typeof lex !== 'object' || Array.isArray(lex)) { errs.push('ttsLexicon 必须是对象'); return }
  for (const [k, v] of Object.entries(lex)) {
    if (k.length < 2) errs.push(`ttsLexicon["${k}"] 的键至少 2 字符`)
    if (typeof v !== 'string' || !v.trim()) errs.push(`ttsLexicon["${k}"] 的值必须是非空字符串`)
  }
}

export function validateEpisode(ep, id) {
  const errs = []
  const warns = []
  check(ep.id === id, `episode.json 的 id="${ep.id}" 与目录名 "${id}" 不一致`, errs)
  check(ep.title?.trim(), '缺 title', errs)
  check(ep.voice?.trim(), '缺 voice（edge-tts 音色名）', errs)
  check(Array.isArray(ep.platforms) === false && ep.platforms, '缺 platforms', errs)

  const fv = ep.formatVersion ?? 1
  check(FORMAT_VERSIONS.includes(fv), `formatVersion=${ep.formatVersion} 不在 1/2`, errs)
  if (fv === 2) {
    check(V2_VOICES.includes(ep.voice), `v2 音色必须是 ${V2_VOICES.join('/')}，当前 "${ep.voice}"`, errs)
    validateLexicon(ep.ttsLexicon, errs)
  }

  const seenAnims = new Set()
  for (const [name, cfg] of Object.entries(ep.platforms || {})) {
    if (!PLATFORM_DEFAULTS[name]) warns.push(`未知平台 "${name}"，将套用默认布局字段`)
    let scenes
    try {
      scenes = resolveScenes(ep, name)
    } catch (e) {
      errs.push(e.message)
      continue
    }
    const [w, h] = cfg.size || PLATFORM_DEFAULTS[name]?.size || []
    check(w && h, `平台 ${name}: size 缺失`, errs)

    const ids = new Set()
    let narrationChars = 0
    for (const [i, sc] of scenes.entries()) {
      const at = `${name}.scenes[${i}]${sc.id ? `(${sc.id})` : ''}`
      check(!sc.__missing, `${at}: pick 里的场景在 ${cfg.reuseFrom} 里不存在`, errs)
      check(sc.id?.trim(), `${at}: 缺 id`, errs)
      check(!ids.has(sc.id), `${at}: id 重复`, errs)
      ids.add(sc.id)
      check(KINDS.includes(sc.kind), `${at}: kind="${sc.kind}" 不在 ${KINDS.join('/')}`, errs)
      const text = sc.narration?.trim()
      check(text, `${at}: 缺 narration`, errs)
      narrationChars += text?.length || 0
      if (sc.anim) {
        check(existsSync(join(ANIM_DIR, `${sc.anim}.svg`)), `${at}: 动画 docs/public/anim/${sc.anim}.svg 不存在`, errs)
        seenAnims.add(sc.anim)
        check(
          !sc.t1 || !sc.t0 || sc.t1 > sc.t0,
          `${at}: t1(${sc.t1}) 必须大于 t0(${sc.t0})`,
          errs,
        )
      } else {
        check(!sc.t0 && !sc.t1, `${at}: 没绑 anim 却给了 t0/t1`, errs)
      }
      if (sc.smil) check(SMIL_MODES.includes(sc.smil), `${at}: smil="${sc.smil}" 不在 ${SMIL_MODES.join('/')}`, errs)
      if (sc.kind === 'anim') check(sc.anim, `${at}: kind=anim 但没绑 anim`, errs)
      if (sc.kind === 'code') check(sc.code?.trim(), `${at}: kind=code 但没给 code`, errs)
      if (sc.kind === 'card') check(sc.title?.trim(), `${at}: kind=card 但没给 title`, errs)
      check(sc.tail === undefined || (sc.tail >= 0 && sc.tail <= 3), `${at}: tail 必须在 0..3`, errs)
      // revealFrames 是"这一场开头淡入几帧"，0 = 首帧即全亮；非负整数以外没有意义
      check(
        sc.revealFrames === undefined || (Number.isInteger(sc.revealFrames) && sc.revealFrames >= 0),
        `${at}: revealFrames 必须是非负整数`,
        errs,
      )

      if (h && w) {
        const maxLines = Math.max(6, Math.floor((h * 0.5) / (h * 0.038)))
        const lines = (sc.code || '').split('\n').length
        check(lines <= maxLines + 6, `${at}: 代码 ${lines} 行，超出 ${name} 可显示上限，请拆场`, warns)
      }

      if (fv === 2) {
        validateBeatMap(sc, at, errs)
        validateEmphasis(sc, at, errs)
        if (sc.ttsText !== undefined) check(typeof sc.ttsText === 'string' && sc.ttsText.trim(), `${at}: ttsText 必须是非空字符串`, errs)
      }
    }
    validateSections(cfg.sections, scenes, name, errs)
    if (fv === 2) {
      const n = cfg.sections?.length || 0
      check(n >= V2_SECTION_RANGE[0] && n <= V2_SECTION_RANGE[1], `平台 ${name}: v2 需要 3–6 节，当前 ${n} 节`, errs)
    }
    const [lo, hi] = cfg.targetSec || []
    if (lo && hi) {
      // 口径来自 11 集成片的实测回归（拿 narration.srt 末句时间当分母，最小二乘拟合）：
      //   bilibili  0.1955 s/字，场次系数 −0.09 ≈ 0        → MAE 10.3 s
      //   douyin    0.1946 s/字 + 1.091 s/场（短旁白下句间留白才显形）→ MAE 1.3 s
      // 同一音色同一 rate 每字耗时一致，差的是固定留白在长短旁白里的占比。
      const rate = SEC_PER_CHAR[name] || SEC_PER_CHAR.bilibili
      const est = narrationChars * rate.char + scenes.length * rate.perScene
      check(
        est >= lo * 0.85 && est <= hi * 1.12,
        `平台 ${name}: 旁白 ${narrationChars} 字 / ${scenes.length} 场 ≈ ${Math.round(est)}s，偏离目标 ${lo}-${hi}s 太多`,
        errs,
      )
    }
  }
  return { errs, warns, anims: [...seenAnims] }
}

export function loadEpisode(id) {
  const p = episodePath(id)
  if (!existsSync(p)) throw new Error(`找不到 ${p}`)
  const ep = JSON.parse(readFileSync(p, 'utf8'))
  const { errs, warns, anims } = validateEpisode(ep, id)
  for (const w of warns) console.warn(`⚠️  ${w}`)
  if (errs.length) {
    throw new Error(`episode.json 校验未通过:\n${errs.map((e) => `  - ${e}`).join('\n')}`)
  }
  return ep
}

export function platformConfig(ep, platform) {
  const base = PLATFORM_DEFAULTS[platform] || { size: [1920, 1080], fps: 30, safe: { top: 40, right: 40, bottom: 40, left: 40 } }
  const cfg = ep.platforms[platform]
  if (!cfg) throw new Error(`episode 里没有平台 ${platform}`)
  return {
    ...base,
    ...cfg,
    size: cfg.size || base.size,
    fps: cfg.fps || ep.fps || base.fps,
    safe: { ...base.safe, ...(cfg.safe || {}) },
  }
}
