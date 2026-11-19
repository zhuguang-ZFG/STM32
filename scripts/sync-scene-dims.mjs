// 场景回退图的尺寸必须与 PNG 头一致：`<noscript>` 里的 <img> 拿不到 CSS 尺寸，
// 缺 width/height 时无 JS 读者会看到布局跳动。
//
// 尺寸写进 docs/.vitepress/data/scenes.json（站点组件与印刷渲染器共用同一份），
// 由本脚本从 PNG 的 IHDR 直接读取，不靠手填。
//
// 用法（cwd=仓库根）：
//   node scripts/sync-scene-dims.mjs --check   # 门：与 PNG 头不一致即失败
//   node scripts/sync-scene-dims.mjs --write   # 重新生成尺寸字段
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const DEFAULT_JSON = 'docs/.vitepress/data/scenes.json'
const DEFAULT_PUBLIC = 'docs/public'

export function parseArgs(argv) {
  const args = { json: DEFAULT_JSON, publicDir: DEFAULT_PUBLIC, write: false }
  for (const key of argv) {
    if (key === '--write') args.write = true
    else if (key === '--check') args.write = false
    else if (key.startsWith('--json=')) args.json = key.slice('--json='.length)
    else if (key.startsWith('--public-dir=')) args.publicDir = key.slice('--public-dir='.length)
    else throw new Error(`未知参数: ${key}`)
  }
  return args
}

/** 只读 PNG 的 IHDR：8 字节签名 + 4 长度 + 4 类型 + 宽 4 + 高 4。 */
export function pngSize(file) {
  const buf = fs.readFileSync(file)
  if (buf.length < 24 || buf.readUInt32BE(0) !== 0x89504e47) return null
  return [buf.readUInt32BE(16), buf.readUInt32BE(20)]
}

export function collectDims(scenes, publicDir) {
  const dims = {}
  const missing = []
  for (const [id, meta] of Object.entries(scenes)) {
    const rel = String(meta.fallback ?? '').replace(/^\//, '')
    if (!rel) {
      missing.push(`${id}: 没有 fallback`)
      continue
    }
    const size = pngSize(path.join(publicDir, rel))
    if (!size) {
      missing.push(`${id}: ${rel} 不是可读 PNG`)
      continue
    }
    dims[id] = { width: size[0], height: size[1] }
  }
  return { dims, missing }
}

export function checkSceneDims({ json, publicDir }) {
  const scenes = JSON.parse(fs.readFileSync(json, 'utf8'))
  const { dims, missing } = collectDims(scenes, publicDir)
  const drift = []
  for (const [id, size] of Object.entries(dims)) {
    const meta = scenes[id]
    if (meta.width !== size.width || meta.height !== size.height) {
      drift.push(`${id}: 期望 ${size.width}x${size.height}，scenes.json 是 ${meta.width}x${meta.height}`)
    }
  }
  return { ok: missing.length === 0 && drift.length === 0, missing, drift, count: Object.keys(dims).length }
}

export function writeSceneDims({ json, publicDir }) {
  const scenes = JSON.parse(fs.readFileSync(json, 'utf8'))
  const { dims, missing } = collectDims(scenes, publicDir)
  if (missing.length) throw new Error(missing.join('; '))
  for (const [id, size] of Object.entries(dims)) {
    scenes[id] = { ...scenes[id], width: size.width, height: size.height }
  }
  fs.writeFileSync(json, `${JSON.stringify(scenes, null, 2)}\n`)
  return { count: Object.keys(dims).length }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const args = parseArgs(process.argv.slice(2))
  if (args.write) {
    const { count } = writeSceneDims(args)
    console.log(`scene dims: 写入 ${count} 个场景的尺寸`)
  } else {
    const result = checkSceneDims(args)
    for (const problem of result.missing) console.error(`MISSING ${problem}`)
    for (const problem of result.drift) console.error(`DRIFT ${problem}`)
    if (!result.ok) process.exit(1)
    console.log(`scene dims: ${result.count} 个场景与 PNG 头一致`)
  }
}