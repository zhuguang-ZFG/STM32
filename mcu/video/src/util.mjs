import { createHash } from 'node:crypto'
import { execFile, spawn } from 'node:child_process'
import { readFileSync, existsSync, mkdirSync, statSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { promisify } from 'node:util'

const execFileP = promisify(execFile)

export const VIDEO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
export const REPO_ROOT = resolve(VIDEO_ROOT, '..')
export const OUT_DIR = join(VIDEO_ROOT, 'out')
export const CACHE_DIR = join(VIDEO_ROOT, '.cache')
export const EPISODES_DIR = join(VIDEO_ROOT, 'episodes')
export const ANIM_DIR = join(REPO_ROOT, 'docs', 'public', 'anim')

export const FFMPEG = resolve(REPO_ROOT, 'node_modules', 'ffmpeg-static', 'ffmpeg.exe')

export function ensureDir(p) {
  mkdirSync(p, { recursive: true })
  return p
}

export function sha1(buf) {
  return createHash('sha1').update(buf).digest('hex')
}

export function readFileSafe(p) {
  return existsSync(p) ? readFileSync(p, 'utf8') : null
}

export function exists(p) {
  return existsSync(p)
}

export function mtime(p) {
  try {
    return statSync(p).mtimeMs
  } catch {
    return 0
  }
}

// ffmpeg-static 不带 ffprobe，只能拿 ffmpeg 本体的 `-i` 输出去解析。
// 注意这里不解码：`ffmpeg -i f` 会打印流信息后立刻以错误退出，几毫秒返回；
// 解码到 null 探时长只对无 Xing 头的 mp3 有必要（在 python 侧逐句探时长时用）。
export async function probeStreams(file) {
  const r = await execFileP(FFMPEG, ['-hide_banner', '-i', file], { maxBuffer: 8 << 20 }).catch((err) => {
    if (!err.stderr) throw err
    return { stderr: err.stderr }
  })
  const stderr = String(r.stderr || '')
  const dur = stderr.match(/Duration:\s*(\d+):(\d+):([\d.]+)/)
  const streams = [...stderr.matchAll(/Stream #\d+:(\d+)[^\n]*/g)].map((m) => m[0])
  const pick = (kind) => streams.find((s) => s.includes(`: ${kind}:`)) || null
  const audio = pick('Audio')
  const audioInfo = audio
    ? {
        line: audio,
        codec: (audio.match(/Audio:\s*([a-z0-9_]+)/) || [])[1] || '',
        sampleRate: Number((audio.match(/(\d+)\s*Hz/) || [])[1]) || 0,
        channels: /stereo/.test(audio) ? 2 : /mono/.test(audio) ? 1 : 0,
      }
    : null
  return {
    duration: dur ? Number(dur[1]) * 3600 + Number(dur[2]) * 60 + Number(dur[3]) : 0,
    video: pick('Video'),
    audio: audioInfo,
    raw: stderr,
  }
}

export async function probeDuration(file) {
  const { duration } = await probeStreams(file)
  if (!duration) throw new Error(`探测不到时长: ${file}`)
  return duration
}

export async function run(cmd, args, { quiet = true } = {}) {
  try {
    const r = await execFileP(cmd, args, { maxBuffer: 64 << 20 })
    return r
  } catch (err) {
    const stderr = quiet ? String(err.stderr || '').split('\n').slice(-14).join('\n') : String(err.stderr || '')
    throw new Error(`${cmd} 失败 (exit ${err.code}):\n${stderr}`)
  }
}

export function fmtSec(n) {
  return `${(Math.round(n * 100) / 100).toFixed(2)}s`
}

export function fmtClock(sec) {
  const s = Math.floor(sec)
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

export function clamp(v, lo, hi) {
  return Math.min(hi, Math.max(lo, v))
}

// 把 PNG 解码成 RGBA 原始像素（只为自检比较两帧，不落盘、不引依赖）
export function decodeRgba(pngBuf) {
  return new Promise((resolveP, rejectP) => {
    const child = spawn(
      FFMPEG,
      ['-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-i', 'pipe:', '-f', 'rawvideo', '-pix_fmt', 'rgba', 'pipe:1'],
      { stdio: ['pipe', 'pipe', 'pipe'] },
    )
    const chunks = []
    let err = ''
    child.stdout.on('data', (d) => chunks.push(d))
    child.stderr.on('data', (d) => {
      err += d
    })
    child.stdin.on('error', () => {})
    child.on('error', rejectP)
    child.on('close', (code) =>
      code === 0 ? resolveP(Buffer.concat(chunks)) : rejectP(new Error(`PNG 解码失败 ${code}：${err.slice(-500)}`)),
    )
    child.stdin.end(pngBuf)
  })
}

// "强差异像素"的门限：Δ≥32 才算。抗锯齿重排一般停在个位数到 30 出头，
// 而笔画/字形真的换相位是 100+ 起步——32 是实测两堆之间的空档。
export const STRONG_DELTA = 32

export function diffRgba(a, b) {
  const n = Math.min(a.length, b.length)
  let changed = 0
  let strong = 0
  let maxDelta = 0
  for (let i = 0; i < n; i += 4) {
    let hit = false
    let d = 0
    for (let k = 0; k < 3; k++) {
      const t = Math.abs(a[i + k] - b[i + k])
      if (t) {
        hit = true
        if (t > d) d = t
      }
    }
    if (hit) changed++
    if (d >= STRONG_DELTA) strong++
    if (d > maxDelta) maxDelta = d
  }
  const pixels = n / 4
  return { changedPx: changed, strong, pixels, ratio: changed / pixels, maxDelta }
}

export function log(...args) {
  console.log(...args)
}
