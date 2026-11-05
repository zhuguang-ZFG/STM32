import { spawnSync } from 'node:child_process'
import {
  appendFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs'
import { dirname, join } from 'node:path'
import { chromium } from 'playwright'
import { REPO_ROOT } from '../../src/util.mjs'

export const CDP = process.env.REPOST_CDP || 'http://127.0.0.1:9223'
export const RUN_ROOT = join(REPO_ROOT, '.temp', 'repost')
export const PLATFORMS = ['bilibili', 'douyin', 'zhihu', 'xiaohongshu']

const EP_RE = /^[a-z0-9][a-z0-9-]*$/
const BOOL_FLAGS = new Set(['go', 'run', 'manual', 'before', 'after', 'replace', 'help'])
const VALUE_FLAGS = new Set(['ep', 'platform', 'date', 'decl', 'title'])

export class GateError extends Error {
  constructor(message) {
    super(message)
    this.exitCode = 3
  }
}

export class UnknownError extends Error {
  constructor(message) {
    super(message)
    this.exitCode = 4
  }
}

export function today(date = new Date()) {
  return date.toISOString().slice(0, 10)
}

export function dayDir(ep, date = today()) {
  const d = join(RUN_ROOT, date, ep)
  mkdirSync(d, { recursive: true })
  return d
}

// 归档和删除可能不在同一天：按 old.json / 事件文件倒序找最近一次运行目录。
export function findRunDir(ep, file = 'old.json') {
  if (!existsSync(RUN_ROOT)) return null
  const dates = readdirSync(RUN_ROOT)
    .filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d))
    .sort()
    .reverse()
  for (const date of dates) {
    const dir = join(RUN_ROOT, date, ep)
    if (existsSync(join(dir, file))) return { dir, date }
  }
  return null
}

export function runDirFor(ep, date) {
  if (date) return dayDir(ep, date)
  return findRunDir(ep)?.dir || dayDir(ep)
}

export function gateName(kind, ep) {
  return kind === 'delete' ? `I_HAVE_USER_OK_DELETE_${ep}` : `I_HAVE_USER_OK_PUBLISH_${ep}`
}

export function requireGate(kind, ep, dir = dayDir(ep)) {
  const p = join(dir, gateName(kind, ep))
  if (!existsSync(p)) {
    throw new GateError(`没有闸门 ${p}——这一步只能在对话里拿到这一集的明确点头后创建`)
  }
  return readFileSync(p, 'utf8').trim()
}

export function consumeGate(kind, ep, dir = dayDir(ep)) {
  unlinkSync(join(dir, gateName(kind, ep)))
}

export function writeJson(p, obj) {
  mkdirSync(dirname(p), { recursive: true })
  writeFileSync(p, `${JSON.stringify(obj, null, 2)}\n`)
}

export function readJson(p) {
  if (!existsSync(p)) return null
  return JSON.parse(readFileSync(p, 'utf8'))
}

export function appendEvent(dir, ev) {
  mkdirSync(dir, { recursive: true })
  appendFileSync(join(dir, 'events.jsonl'), `${JSON.stringify({ at: new Date().toISOString(), ...ev })}\n`)
}

// 一次只处理一集、一个平台；--all 是明确禁止的，不做“顺手批量”。
export function parseArgs(argv = process.argv.slice(2)) {
  const out = {}
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--all') throw new Error('禁止批量：一次只处理一集')
    if (!a.startsWith('--')) throw new Error(`不认识的参数 "${a}"`)
    const body = a.slice(2)
    const eq = body.indexOf('=')
    const key = eq >= 0 ? body.slice(0, eq) : body
    if (BOOL_FLAGS.has(key)) {
      if (eq >= 0) throw new Error(`--${key} 是开关，不接受值`)
      out[key] = true
      continue
    }
    if (!VALUE_FLAGS.has(key)) throw new Error(`不认识的参数 "--${key}"`)
    const value = eq >= 0 ? body.slice(eq + 1) : argv[++i]
    if (value === undefined || value === '' || value.startsWith('--')) {
      throw new Error(`--${key} 后面缺值`)
    }
    out[key] = value
  }
  if (out.ep === undefined && !out.help) throw new Error('必须给 --ep <episode-id>；一次只处理一集')
  if (out.ep !== undefined) {
    if (!EP_RE.test(out.ep)) throw new Error(`--ep "${out.ep}" 不是单集 id（一次只处理一集）`)
    if (out.ep.includes(',')) throw new Error('一次只处理一集，不接受逗号列表')
  }
  if (out.platform !== undefined && !PLATFORMS.includes(out.platform)) {
    throw new Error(`--platform 只能是 ${PLATFORMS.join(' / ')}`)
  }
  if (out.date !== undefined && !/^\d{4}-\d{2}-\d{2}$/.test(out.date)) {
    throw new Error('--date 必须是 YYYY-MM-DD')
  }
  return out
}

export function requireEp(args) {
  if (!args.ep) throw new Error('必须给 --ep <episode-id>；一次只处理一集')
  return args.ep
}

export function requirePlatform(args) {
  if (!args.platform) throw new Error(`必须给 --platform <${PLATFORMS.join('|')}>`)
  return args.platform
}

// 只连常驻浏览器：不 launch、不 browser.close()。每次只关自己开的页。
export async function withPage(fn, { url = null, waitMs = 6000 } = {}) {
  let browser
  try {
    browser = await chromium.connectOverCDP(CDP, { timeout: 15_000 })
  } catch (e) {
    throw new UnknownError(`CDP 连不上 ${CDP}：${e.message.split('\n')[0]}——没有启动新浏览器`)
  }
  const contexts = browser.contexts()
  if (!contexts.length) throw new UnknownError('CDP 已连上，但没有浏览器上下文（登录窗口不在）')
  const page = await contexts[0].newPage()
  page.setDefaultTimeout(45_000)
  page.setDefaultNavigationTimeout(60_000)
  try {
    if (url) {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60_000 })
      await page.waitForTimeout(waitMs)
    }
    return await fn(page)
  } finally {
    await page.close().catch(() => {})
  }
}

export function pngSize(file) {
  const b = readFileSync(file)
  if (b.length < 24 || b.toString('ascii', 1, 4) !== 'PNG') throw new Error(`${file} 不是 PNG`)
  return { width: b.readUInt32BE(16), height: b.readUInt32BE(20) }
}

export function normalizeText(s) {
  return String(s || '')
    .replace(/[\u200B-\u200D\uFEFF]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export async function pageBody(page, limit = 3000) {
  return page.evaluate((n) => {
    const t = (document.body?.innerText || '')
      .replace(/[\u200B-\u200D\uFEFF]/g, '')
      .replace(/\s+/g, ' ')
      .trim()
    return { url: location.href, title: document.title, body: t.slice(0, n), len: t.length }
  }, limit)
}

const LOGIN_WALL =
  /扫码登录|手机号登录|密码登录|验证码登录|请先登录|登录后(?:查看|使用|继续)|登录\/注册|立即登录/

export function looksLoggedOut(info) {
  const urlLogin = /passport\.bilibili\.com|\/login|\/signin|\/sso/i.test(info.url)
  return urlLogin || (LOGIN_WALL.test(info.body) && !/创作中心|内容管理|作品管理|笔记管理|稿件管理/.test(info.body))
}

export function platformGatePath(platform, ep) {
  const dir = {
    bilibili: '.temp/bili-web-run',
    douyin: '.temp/douyin-run',
    zhihu: '.temp/zh-run',
    xiaohongshu: '.temp/xhs-run',
  }[platform]
  return join(REPO_ROOT, dir, `I_HAVE_USER_OK=${ep}`)
}

export function requirePlatformGate(platform, ep, want) {
  const p = platformGatePath(platform, ep)
  if (!existsSync(p)) throw new GateError(`缺平台闸门 ${p}`)
  const got = readFileSync(p, 'utf8').trim()
  if (got !== want) {
    throw new GateError(`平台闸门内容与 repost 闸门不一致：${p}\n  repost=${JSON.stringify(want)}\n  platform=${JSON.stringify(got)}`)
  }
  return p
}

export function seriesName() {
  try {
    return JSON.parse(readFileSync(join(REPO_ROOT, 'video', 'series.json'), 'utf8')).series || ''
  } catch {
    return ''
  }
}

export function runNode(script, args = []) {
  const p = join(REPO_ROOT, 'video', 'publish', script)
  const r = spawnSync(process.execPath, [p, ...args], { stdio: 'inherit', cwd: REPO_ROOT })
  return r.status ?? 1
}

export function runVideoCli(args = []) {
  const p = join(REPO_ROOT, 'video', 'src', 'cli.mjs')
  const r = spawnSync(process.execPath, [p, ...args], { stdio: 'inherit', cwd: REPO_ROOT })
  return r.status ?? 1
}

// connectOverCDP 的 websocket 会吊住事件循环；阶段跑完主动退出，和 probe-platforms 同一做法。
export async function exitAfterFlush(code = 0) {
  await new Promise((r) => process.stdout.write('', r))
  process.exit(code)
}
