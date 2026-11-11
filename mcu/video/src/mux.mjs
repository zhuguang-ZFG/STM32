import { execFile } from 'node:child_process'
import { copyFileSync, existsSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import { promisify } from 'node:util'
import { FFMPEG, VIDEO_ROOT, ensureDir, fmtSec, log, probeStreams, run } from './util.mjs'

const execFileP = promisify(execFile)

export const BGM_PATH = join(VIDEO_ROOT, 'assets', 'ambient-pad.m4a')
// v2 的 A/B 候选：与 ambient-pad 同位置，未获用户选听前不算正式资产（Task 11 决定去留）。
export const LAB_BGM_PATH = join(VIDEO_ROOT, 'assets', 'lab-ambient.m4a')

// 旁白是主角：BGM 先压到很低的底，再用 sidechaincompress 让旁白一开口就把它压下去，
// 旁白停顿的间隙它自己抬回来（makeup 不做，避免呼吸感太明显）。
// 最后 loudnorm 到 -14 LUFS——B站/抖音的通行响度，也是手机外放不难听的下限。
// loudnorm 内部会把采样率顶到 192k，尾巴上必须补一道 aresample。
// sfx === false 时逐字返回 v1 的三条滤镜串（bgm × duck 四种组合里，
// 无 BGM 的两种同串）——已被 37 集母版钉死，改一个字都要重验。
// 有 SFX 时按实际 -i 顺序取输入：video(0)、narration(1)、[bgm(2)]、sfx(2 或 3)。
// v2 用两遍 loudnorm：第一遍只测 I/TP/LRA/thresh，第二遍按实测值线性校正；
// 单遍 loudnorm 在真实语音上可能落在 -15.8 LUFS，不能当 -14±1 的硬门。
const V1_NORMALIZE = 'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]'
const V2_TARGET = 'loudnorm=I=-14:TP=-1.5:LRA=11'

function mixChains({ bgm, duck, sfx = false, sfxIdx }) {
  if (!sfx) {
    if (!bgm) return []
    // sidechaincompress 会吃掉它的两个输入，只吐一路"被压过的 BGM"。
    // 旁白要同时当触发源和主声，必须先 asplit 成两路，否则 amix 拿到的标签已被消费，
    // ffmpeg 直接报 "Stream matching for 'narr' has no matches"。
    return duck
      ? [
          '[1:a]aresample=44100,asplit=2[narr][narrSC]',
          '[2:a]aresample=44100,volume=-16dB[bg]',
          '[bg][narrSC]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=350[ducked]',
          '[narr][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix]',
        ]
      : [
          '[1:a]aresample=44100[narr]',
          '[2:a]aresample=44100,volume=-16dB[bg]',
          '[narr][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix]',
        ]
  }
  if (!Number.isInteger(sfxIdx)) throw new Error('audioFilter: sfx=true 时必须给 sfxIdx（实际 -i 顺序）')
  const sfxLine = `[${sfxIdx}:a]aresample=44100,volume=-24dB[sfx]`
  if (!bgm) {
    return [
      '[1:a]aresample=44100[narr]',
      sfxLine,
      '[narr][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix]',
    ]
  }
  return duck
    ? [
        '[1:a]aresample=44100,asplit=2[narr][narrSC]',
        '[2:a]aresample=44100,volume=-16dB[bg]',
        sfxLine,
        '[bg][narrSC]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=350[ducked]',
        '[narr][ducked][sfx]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix]',
      ]
    : [
        '[1:a]aresample=44100[narr]',
        '[2:a]aresample=44100,volume=-16dB[bg]',
        sfxLine,
        '[narr][bg][sfx]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix]',
      ]
}

export function audioFilter({ bgm, duck, sfx = false, sfxIdx, measured = null }) {
  const chains = mixChains({ bgm, duck, sfx, sfxIdx })
  if (!sfx) return chains.length ? [...chains, `[mix]${V1_NORMALIZE}`].join(';') : V1_NORMALIZE
  return [...chains, measured ? loudnormSecondPass(measured) : `[mix]${V2_TARGET},aresample=44100[out]`].join(';')
}

// 第一遍：同样的混音链，只把 loudnorm 的 JSON 报告打到 stderr。
export function loudnessProbeFilter({ bgm, duck, sfx = true, sfxIdx }) {
  return [...mixChains({ bgm, duck, sfx, sfxIdx }), `[mix]${V2_TARGET}:print_format=json[out]`].join(';')
}

function finiteField(measured, key) {
  const v = Number(measured?.[key])
  if (!Number.isFinite(v)) throw new Error(`loudnorm 第一遍缺少有效的 ${key}：${measured?.[key]}`)
  return v
}

export function loudnormSecondPass(measured) {
  const i = finiteField(measured, 'input_i')
  const tp = finiteField(measured, 'input_tp')
  const lra = finiteField(measured, 'input_lra')
  const thresh = finiteField(measured, 'input_thresh')
  const offset = finiteField(measured, 'target_offset')
  return (
    `[mix]loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=${i}:measured_TP=${tp}` +
    `:measured_LRA=${lra}:measured_thresh=${thresh}:offset=${offset}:linear=true:print_format=summary` +
    ',aresample=44100[out]'
  )
}

// loudnorm 的 JSON 是 stderr 里最后一个花括号块；解析失败就退回单遍，
// 后面的响度硬门会决定能不能放行。
export function parseLoudnormJson(stderr) {
  const s = String(stderr || '')
  const start = s.lastIndexOf('{')
  const end = s.lastIndexOf('}')
  if (start < 0 || end <= start) throw new Error('loudnorm 没有输出 JSON 报告')
  return JSON.parse(s.slice(start, end + 1))
}

// ebur128 的 Summary 在 stderr；只认 Integrated 那一行。
export async function probeLoudness(file) {
  // -vn：响度只关心音轨，别为了探一次响度把整条视频流也解一遍。
  const r = await execFileP(FFMPEG, ['-hide_banner', '-i', file, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'], {
    maxBuffer: 16 << 20,
  }).catch((e) => ({ stderr: e.stderr }))
  const tail = String(r.stderr || '').split('Summary:').pop()
  const m = tail.match(/I:\s*(-?\d+(?:\.\d+)?)\s*LUFS/)
  if (!m) throw new Error(`读不到响度：${file}`)
  return Number(m[1])
}

function audioInputArgs({ videoPath, narrationPath, bgm, sfxPath, loglevel = 'error' }) {
  const args = ['-hide_banner', '-loglevel', loglevel, '-y', '-i', videoPath, '-i', narrationPath]
  if (bgm) args.push('-stream_loop', '-1', '-i', bgm)
  if (sfxPath) args.push('-i', sfxPath)
  return args
}

// 第一遍只走音频：视频流照样 -i 进去占住 0 号，保证 [1:a]/[2:a]/[3:a] 与成片一致。
async function measureLoudnorm({ videoPath, narrationPath, bgm, duck, sfxPath, sfxIdx, duration }) {
  const args = audioInputArgs({ videoPath, narrationPath, bgm, sfxPath, loglevel: 'info' })
  args.push(
    '-filter_complex',
    loudnessProbeFilter({ bgm, duck, sfx: true, sfxIdx }),
    '-map',
    '[out]',
    '-t',
    duration.toFixed(6),
    '-f',
    'null',
    '-',
  )
  let stderr = ''
  try {
    stderr = (await execFileP(FFMPEG, args, { maxBuffer: 16 << 20 })).stderr
  } catch (e) {
    stderr = String(e.stderr || '')
    if (!stderr.includes('input_i')) throw new Error(`loudnorm 第一遍失败：${e.message}`)
  }
  return parseLoudnormJson(stderr)
}

// 视频流是 -c:v copy 直接搬过去：逐帧渲染阶段已经把时长钉死在 totalFrames/fps，
// 这里再断言一次成片两条流的时长差，音画对位到此有证据。
export async function mux({
  videoPath,
  narrationPath,
  outPath,
  duration,
  bgm = BGM_PATH,
  duck = true,
  sfxPath = null,
  assertLoudness = false,
}) {
  const useBgm = bgm && existsSync(bgm)
  // v2 计划了 SFX 就不能静默出无声版：缺文件直接失败。BGM 缺了仍是 v1 的静音降级。
  const useSfx = sfxPath !== null && sfxPath !== undefined
  if (useSfx && !existsSync(sfxPath)) throw new Error(`SFX 文件不存在：${sfxPath}`)
  ensureDir(outPath.replace(/[\\/][^\\/]+$/, ''))
  const sfxIdx = useSfx ? (useBgm ? 3 : 2) : undefined
  let measured = null
  if (useSfx) {
    measured = await measureLoudnorm({
      videoPath,
      narrationPath,
      bgm: useBgm ? bgm : null,
      duck,
      sfxPath,
      sfxIdx,
      duration,
    })
    log(`  🔊 两遍响度：第一遍测到 ${Number(measured.input_i).toFixed(1)} LUFS，第二遍线性校正`)
  }
  const args = audioInputArgs({ videoPath, narrationPath, bgm: useBgm ? bgm : null, sfxPath })
  args.push(
    '-filter_complex',
    audioFilter({ bgm: useBgm, duck, sfx: useSfx, sfxIdx, measured }),
    '-map',
    '0:v:0',
    '-map',
    '[out]',
    '-c:v',
    'copy',
    '-c:a',
    'aac',
    '-b:a',
    '192k',
    '-ar',
    '44100',
    '-ac',
    '2',
    '-t',
    duration.toFixed(6),
    '-shortest',
    '-movflags',
    '+faststart',
    outPath,
  )
  await run(FFMPEG, args)

  let info = await probeStreams(outPath)
  const drift = Math.abs(info.duration - duration)
  if (drift > 0.15) throw new Error(`${outPath} 成片时长 ${info.duration.toFixed(3)}s 与计划 ${duration.toFixed(3)}s 差 ${drift.toFixed(3)}s`)
  if (!info.video) throw new Error(`${outPath} 里没有视频流`)
  if (info.audio?.codec !== 'aac' || info.audio?.sampleRate !== 44100 || info.audio?.channels !== 2) {
    throw new Error(`${outPath} 音轨不是 aac 44.1kHz 立体声：${info.audio?.line}`)
  }
  log(
    `  🔊 成片 ${fmtSec(info.duration)}｜${useBgm ? 'BGM ducking' : '纯旁白'}｜` +
      `视频 ${info.video.replace(/^\s*/, '')}｜音频 ${info.audio.codec}/${info.audio.sampleRate}Hz/${info.audio.channels}ch`,
  )
  // 响度每次都探、每次都打；只有 v2 才把 -14 LUFS 当硬门。v1 探测失败也不能让老集重渲失败。
  let lufs = null
  try {
    lufs = await probeLoudness(outPath)
    log(`  🔊 响度 ${lufs.toFixed(1)} LUFS（目标 -14 ±1）`)
  } catch (err) {
    if (assertLoudness) throw err
    log(`  ⚠️  响度探测失败：${err.message}`)
  }
  if (assertLoudness) {
    // loudnorm 在 TP 约束下会停在比 -14 更低的位置（c3 抖音实测 -15.1）；
    // 限幅器换回响度，视频流 copy，不重渲帧。
    for (let attempt = 0; lufs !== null && Math.abs(lufs + 14) > 1 && attempt < 2; attempt++) {
      const delta = -14 - lufs
      const fixed = `${outPath}.loudfix.mp4`
      log(`  🔊 响度 ${lufs.toFixed(1)} LUFS 超出 -14 ±1：${delta >= 0 ? '+' : ''}${delta.toFixed(2)} dB 重封音轨`)
      await run(FFMPEG, [
        '-hide_banner',
        '-loglevel',
        'error',
        '-y',
        '-i',
        outPath,
        '-c:v',
        'copy',
        '-af',
        `volume=${delta.toFixed(2)}dB,alimiter=limit=0.75:level=false:attack=5:release=50,aresample=44100`,
        '-c:a',
        'aac',
        '-b:a',
        '192k',
        '-ar',
        '44100',
        '-ac',
        '2',
        '-t',
        duration.toFixed(6),
        '-shortest',
        '-movflags',
        '+faststart',
        fixed,
      ])
      copyFileSync(fixed, outPath)
      rmSync(fixed)
      const fixedInfo = await probeStreams(outPath)
      if (Math.abs(fixedInfo.duration - duration) > 0.15) {
        throw new Error(`${outPath} 修正后成片时长 ${fixedInfo.duration.toFixed(3)}s 与计划 ${duration.toFixed(3)}s 差超过 0.15s`)
      }
      if (!fixedInfo.video) throw new Error(`${outPath} 修正后没有视频流`)
      if (fixedInfo.audio?.codec !== 'aac' || fixedInfo.audio?.sampleRate !== 44100 || fixedInfo.audio?.channels !== 2) {
        throw new Error(`${outPath} 修正后音轨不是 aac 44.1kHz 立体声：${fixedInfo.audio?.line}`)
      }
      info = fixedInfo
      lufs = await probeLoudness(outPath)
      log(`  🔊 修正后响度 ${lufs.toFixed(1)} LUFS（目标 -14 ±1）`)
    }
    if (lufs === null) throw new Error(`${outPath} 读不到响度，无法断言 -14 LUFS`)
    if (Math.abs(lufs + 14) > 1) throw new Error(`${outPath} 响度 ${lufs.toFixed(1)} LUFS 偏离 -14 ±1`)
  }
  return info
}
