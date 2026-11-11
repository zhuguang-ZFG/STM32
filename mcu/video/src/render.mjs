import { spawn } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { FFMPEG, log } from './util.mjs'
import { iterateFrames, transitionPhase } from './timeline.mjs'

// Task 5 的公开接口仍在 render.mjs 上；实现唯一来源是 timeline.mjs。
export { transitionPhase }

// PNG 直接喂 ffmpeg 的 stdin（image2pipe），中间不落一万张 PNG。
// 关键优化不是编码而是"少截图"：一次 1080p 截图 20~40 ms，而一集里大量帧的
// 画面其实一模一样（金句卡、代码页、once 动画放完之后的静止段）。
// 用"状态键"判等比哈希便宜得多：场景 + SMIL 时刻 + 字幕序号 + 字幕不透明度
// 四元组相同 ⇒ 画面必然相同，于是把上一帧的 PNG 原样再写一遍，跳过浏览器。
// 注意写的是上一帧的字节、不是让 ffmpeg 复制帧，这样 pipe 里帧数恒等于 totalFrames，
// 视频时长 = totalFrames/fps，和旁白时长在构造上对齐。

const FADE_IN = 4
const FADE_OUT = 3
const REVEAL = 8 // 每场开头的淡入帧数（0.27s @30fps）
const QUANT = 60 // SMIL 时刻量化到 1/60 s，再细的差别肉眼看不出来，但会让去重失效

export function captionOpacity(cap, abs, fps) {
  if (!cap) return 1
  const span = Math.max(1e-6, cap.end - cap.start)
  const inF = Math.min(1, ((abs - cap.start) * fps) / FADE_IN)
  const outF = Math.min(1, ((cap.end - abs) * fps) / FADE_OUT)
  return Math.max(0, Math.min(1, inF, outF))
}

// 内容淡入：ease-out，前 8 帧从 0.12 走到 1。淡入不到 0，否则整屏黑帧会被
// 静止帧去重当成"和下一帧一样"而吃掉。
// revealFrames 由场景自己定：0 = 首帧就全亮。开场场若留着 8 帧淡入，前两秒是一层
// 半透明的图，"结果先行"就白做了；但只有被点名的场景才改，其余仍走默认。
export function revealOpacity(frameInScene, revealFrames = REVEAL) {
  if (revealFrames <= 0) return 1
  if (frameInScene >= revealFrames) return 1
  const p = frameInScene / revealFrames
  return Math.round((0.12 + 0.88 * (1 - (1 - p) ** 2)) * 100) / 100
}

export function stateKey(frame, opacity, reveal, beat = null, transition = -1) {
  const smil = frame.smilTime === null ? '-' : (Math.round(frame.smilTime * QUANT) / QUANT).toFixed(4)
  const op = Math.round(opacity * 100) / 100
  const base = `${frame.scene.index}|${smil}|${frame.captionIdx}|${op}|${reveal}`
  if (!beat && transition < 0) return base
  const b = beat ? `${beat.index}:${beat.phase}` : '-'
  return `${base}|b${b}|t${transition < 0 ? '-' : transition}`
}

function spawnEncoder({ ffmpeg, fps, outPath }) {
  const args = [
    '-hide_banner',
    '-loglevel',
    'error',
    '-y',
    '-nostdin',
    '-f',
    'image2pipe',
    '-framerate',
    String(fps),
    '-i',
    'pipe:',
    '-an',
    '-c:v',
    'libx264',
    '-preset',
    'veryfast',
    '-crf',
    '17',
    '-pix_fmt',
    'yuv420p',
    '-g',
    String(fps * 4),
    outPath,
  ]
  const child = spawn(ffmpeg, args, { stdio: ['pipe', 'ignore', 'pipe'] })
  let stderr = ''
  child.stderr.on('data', (d) => {
    stderr += d
  })
  const done = new Promise((resolve, reject) => {
    child.on('error', reject)
    child.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg 编码失败 ${code}：${stderr.slice(-2000)}`))))
  })
  return {
    async write(buf) {
      if (child.stdin.write(buf)) return
      await new Promise((res, rej) => {
        const onDrain = () => {
          child.stdin.off('error', onError)
          res()
        }
        const onError = (e) => {
          child.stdin.off('drain', onDrain)
          rej(e)
        }
        child.stdin.once('drain', onDrain)
        child.stdin.once('error', onError)
      })
    },
    async end() {
      child.stdin.end()
      await done
      if (stderr.trim()) log(`  ffmpeg: ${stderr.trim().slice(0, 500)}`)
    },
  }
}

export async function renderFrames(plan, stage, { outPath, ffmpeg, onFrame }) {
  // 捕获起点单独落一枚戳。成片 mtime 拦不住"文本改在捕获中间"——mux 在捕获之后才写 mp4，
  // 于是 mtime 必然比改动晚，比对会假绿；NTFS 的 birthtime 在覆盖写时也不刷新。只有当场记时间才留得下证据。
  writeFileSync(join(dirname(outPath), 'capture-stamp'), `${new Date().toISOString()} ${outPath}\n`)
  const enc = spawnEncoder({ ffmpeg, fps: plan.fps, outPath })
  let lastKey = null
  let lastBuf = null
  let shot = 0
  let reused = 0
  let done = 0
  const t0 = Date.now()
  try {
    for (const frame of iterateFrames(plan)) {
      const opacity = captionOpacity(frame.caption, frame.abs, plan.fps)
      const reveal = revealOpacity(frame.frameInScene, frame.scene.revealFrames)
      const beat = frame.beat || null
      const tp = frame.transitionPhase ?? -1
      const key = stateKey(frame, opacity, reveal, beat, tp)
      if (key !== lastKey || !lastBuf) {
        lastBuf = await stage.capture(frame.scene.index, frame.smilTime, frame.caption?.text ?? null, opacity, reveal, beat, tp)
        lastKey = key
        shot++
      } else {
        reused++
      }
      await enc.write(lastBuf)
      done++
      onFrame?.({ done, total: plan.totalFrames, shot, reused, frame })
    }
  } finally {
    await enc.end()
  }
  const secs = (Date.now() - t0) / 1000
  if (done !== plan.totalFrames) throw new Error(`只写了 ${done} 帧，计划 ${plan.totalFrames} 帧`)
  log(
    `  截图 ${shot} 帧 / 复用 ${reused} 帧（省 ${(reused / Math.max(1, done) * 100).toFixed(0)}% 次截图），` +
      `${done} 帧 ${(done / Math.max(1, secs)).toFixed(1)} fps，用时 ${secs.toFixed(1)}s`,
  )
  return { frames: done, shot, reused, seconds: secs }
}

// 给定绝对秒数，取覆盖它的那一帧状态（人检抽帧用，不开浏览器也能算）
export function statesAt(plan, times) {
  const targets = [...times].sort((a, b) => a - b)
  const out = new Map()
  let ti = 0
  for (const frame of iterateFrames(plan)) {
    while (ti < targets.length && targets[ti] <= frame.abs) {
      out.set(targets[ti++], frame)
    }
    if (ti >= targets.length) break
  }
  for (; ti < targets.length; ti++) out.set(targets[ti], null)
  return targets.map((t) => ({ t, frame: out.get(t) }))
}

export async function captureStills(plan, stage, times, save) {
  const picked = statesAt(plan, times)
  const results = []
  for (const { t, frame } of picked) {
    if (!frame) {
      results.push({ t, error: '超出视频时长' })
      continue
    }
    const opacity = captionOpacity(frame.caption, frame.abs, plan.fps)
    // 抽帧必须和正式编码用同一个 reveal：硬传 1 会把"暗首帧"抽成亮帧，
    // 人检看过了成片却仍然是暗的——检查就等于没做。
    const reveal = revealOpacity(frame.frameInScene, frame.scene.revealFrames)
    const buf = await stage.capture(
      frame.scene.index,
      frame.smilTime,
      frame.caption?.text ?? null,
      opacity,
      reveal,
      frame.beat ?? null,
      frame.transitionPhase ?? -1,
    )
    const name = `${String(Math.round(t * 1000)).padStart(8, '0')}ms_f${frame.scene.id}`
    await save(name, buf)
    results.push({ t: frame.abs, scene: frame.scene.id, smil: frame.smilTime, caption: frame.caption?.text ?? null })
  }
  return results
}
