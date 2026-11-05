import { spawn } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, existsSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { CACHE_DIR, FFMPEG, ensureDir, log } from './util.mjs'
import { resolveScenes } from './spec.mjs'

const PYTHON = process.env.PYTHON || 'python'
const ASSEMBLE = join(import.meta.dirname, 'audio', 'assemble.py')

export function timelinePath(outDir) {
  return join(outDir, 'timeline.json')
}

// 场景间隔：句子之间留一点呼吸，但片头/金句要更重的停顿
const TAIL = { hook: 0.5, anim: 0.45, code: 0.5, card: 0.7, outro: 0.8 }
const MIN_SEC = { hook: 2.2, anim: 2.4, code: 2.8, card: 2.4, outro: 2.6 }

// 发音表只作用于送进 TTS 的文本，字幕/时间轴仍用 narration 原文：
// 屏幕上写 0x40021418，耳朵里听到"零 x 四零零二一四一八"。
// 长键先替换，避免 "0x" 抢在 "0x40021418" 前面把地址拆碎；实现是纯 split/join，
// 不碰正则，所以 emoji 与组合字符（e + U+0301）不会被拆散。
export function applyLexicon(text, lexicon) {
  if (!lexicon) return text
  let out = String(text)
  for (const k of Object.keys(lexicon).sort((a, b) => b.length - a.length)) {
    out = out.split(k).join(lexicon[k])
  }
  return out
}

export function narrationJobs(ep, platform) {
  return resolveScenes(ep, platform).map((sc) => ({
    id: sc.id,
    narration: sc.narration.trim(),
    ttsText: applyLexicon((sc.ttsText || sc.narration).trim(), ep.ttsLexicon),
    head: sc.head ?? 0.22,
    tail: sc.tail ?? TAIL[sc.kind] ?? 0.45,
    minSec: sc.minSec ?? MIN_SEC[sc.kind] ?? 2,
  }))
}

export async function buildAudio(ep, platform, outDir, { force = false } = {}) {
  const timeline = timelinePath(outDir)
  const stampFile = join(outDir, 'audio-stamp')
  const manifest = {
    ffmpeg: FFMPEG,
    cacheDir: join(CACHE_DIR, 'tts'),
    outDir,
    platform,
    voice: ep.voice,
    rate: ep.rate || '+4%',
    fps: ep.fps,
    sampleRate: ep.sampleRate || 44100,
    channels: ep.channels ?? 2,
    scenes: narrationJobs(ep, platform),
  }
  // 缓存键必须是"会影响声音的一切"，不能只看 timeline.json 在不在：
  // 改了旁白却复用旧 timeline，画面会拿新分镜配旧配音，而且没人会察觉。
  const stamp = audioStamp(manifest)
  if (!force && existsSync(timeline) && existsSync(stampFile) && readFileSync(stampFile, 'utf8').trim() === stamp) {
    const cached = readJson(timeline)
    if (cached?.platform === platform && cached.scenes?.length) {
      log(`🎙️  旁白未改动，沿用 ${platform} 时间轴（${cached.scenes.length} 个场景）`)
      return cached
    }
  } else if (existsSync(timeline)) {
    log('🎙️  检测到旁白/配音参数改动，重跑音频阶段（逐句内容哈希缓存，只补真改动的句子）')
  }

  ensureDir(outDir)
  if (existsSync(timeline)) log('🎙️  旁白有改动，重跑音频阶段（逐句内容哈希缓存，只补真改动的那几句）')
  const manifestPath = join(outDir, 'audio-manifest.json')
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 1))

  await new Promise((res, rej) => {
    const p = spawn(PYTHON, [ASSEMBLE, manifestPath], { stdio: 'inherit' })
    p.on('error', rej)
    p.on('exit', (code) => (code === 0 ? res() : rej(new Error(`assemble.py 退出码 ${code}`))))
  })
  const built = readJson(timeline)
  writeFileSync(stampFile, stamp)
  return built
}

// 只哈希语义输入，不哈希 outDir/ffmpeg 路径——换台机器重跑不该让整集配音重来。
function audioStamp(m) {
  return createHash('sha1')
    .update(JSON.stringify({ platform: m.platform, voice: m.voice, rate: m.rate, fps: m.fps, sampleRate: m.sampleRate, channels: m.channels, scenes: m.scenes }))
    .digest('hex')
}

function readJson(p) {
  try {
    return JSON.parse(readFileSync(p, 'utf8'))
  } catch {
    return null
  }
}
