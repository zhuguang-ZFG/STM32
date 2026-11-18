// 外链巡检：把构建产物里指向站外的 http(s) 链接逐个探活。
//
// 为什么在站点外做：书稿里的外链是读者会点的承诺，构建期只校验站内锚点，
// 外链腐烂（404/410/域名迁移）不会让任何门变红。这里只读构建产物，不改正文。
//
// 用法（cwd=仓库根）：
//   node scripts/check-external-links.mjs --root docs/.vitepress/dist
//   node scripts/check-external-links.mjs --root docs/.vitepress/dist --json out.json
//
// 退出码：0 = 所有未被豁免的外链可访问；1 = 有失败或读取错误。
// 允许清单 scripts/external-links-allowlist.json 里的条目按“跳过”报告，
// 不伪造成功——每条都要写理由，且只用于对爬虫返回 401/403/429 的站点。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const OWN_HOSTS = new Set(['zhuguang-zfg.github.io'])

export function parseArgs(argv) {
  const args = {
    root: 'docs/.vitepress/dist',
    allowlist: defaultAllowlistPath(),
    json: '',
    concurrency: 8,
    timeout: 20000,
    retries: 1,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i]
    const value = argv[i + 1]
    if (key === '--root') args.root = value
    else if (key === '--allowlist') args.allowlist = value
    else if (key === '--json') args.json = value
    else if (key === '--concurrency') args.concurrency = Number(value)
    else if (key === '--timeout') args.timeout = Number(value)
    else if (key === '--retries') args.retries = Number(value)
    else throw new Error(`未知参数: ${key}`)
    i += 1
  }
  return args
}

/** 只保留 http(s) 外链；站内链接、锚点、mailto 与相对路径都不归这里管。 */
export function extractExternalUrls(html, ownHosts = OWN_HOSTS) {
  const urls = new Set()
  const href = /href\s*=\s*"([^"]+)"/gi
  let match
  while ((match = href.exec(html)) !== null) {
    const raw = match[1].replace(/&amp;/g, '&').trim()
    if (!/^https?:\/\//i.test(raw)) continue
    let parsed
    try {
      parsed = new URL(raw)
    } catch {
      continue
    }
    if (ownHosts.has(parsed.host)) continue
    parsed.hash = ''
    urls.add(parsed.toString())
  }
  return urls
}

export function walkHtml(root) {
  const files = []
  const stack = [root]
  while (stack.length) {
    const dir = stack.pop()
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) stack.push(full)
      else if (entry.name.endsWith('.html')) files.push(full)
    }
  }
  return files.sort()
}

export function loadAllowlist(file) {
  if (!file || !fs.existsSync(file)) return []
  const data = JSON.parse(fs.readFileSync(file, 'utf8'))
  if (!Array.isArray(data.entries)) throw new Error(`${file}: entries must be an array`)
  return data.entries.map((entry) => {
    if (!entry.reason || !String(entry.reason).trim()) {
      throw new Error(`${file}: every allowlist entry needs a reason (${entry.match})`)
    }
    const allowStatuses = entry.allowStatuses ?? []
    if (!Array.isArray(allowStatuses) || allowStatuses.some((s) => !Number.isInteger(s))) {
      throw new Error(`${file}: allowStatuses must be integers (${entry.match})`)
    }
    if (allowStatuses.includes(404) || allowStatuses.includes(410)) {
      throw new Error(`${file}: 404/410 是死链，不能进允许清单 (${entry.match})`)
    }
    return {
      match: new RegExp(entry.match),
      reason: entry.reason,
      allowStatuses,
      allowTransportError: entry.allowTransportError === true,
    }
  })
}

export function allowlistHit(url, allowlist) {
  for (const entry of allowlist) {
    if (entry.match.test(url)) return entry
  }
  return null
}

export function defaultAllowlistPath() {
  return path.join(path.dirname(fileURLToPath(import.meta.url)), 'external-links-allowlist.json')
}

async function probeOnce(url, timeout) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const head = await fetch(url, {
      method: 'HEAD',
      redirect: 'follow',
      signal: controller.signal,
      headers: { 'user-agent': 'stm32-book-link-check/1.0' },
    })
    if (head.status === 405 || head.status === 501) {
      const get = await fetch(url, {
        method: 'GET',
        redirect: 'follow',
        signal: controller.signal,
        headers: { 'user-agent': 'stm32-book-link-check/1.0', Range: 'bytes=0-1023' },
      })
      return get.status
    }
    return head.status
  } finally {
    clearTimeout(timer)
  }
}

// status 只在“根本没拿到 HTTP 响应”（DNS/TLS/超时）时才是 0；
// 拿到了 4xx/5xx 就必须如实返回那个状态，否则允许清单会把 404 当成传输失败吞掉。
async function probe(url, { timeout, retries }) {
  let lastError = ''
  let lastStatus = 0
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const status = await probeOnce(url, timeout)
      if (status < 400) return { status, error: '' }
      lastStatus = status
      lastError = `HTTP ${status}`
      if (status === 404 || status === 410) break
    } catch (error) {
      // 不要把已观测到的 HTTP 状态清成 0：先 500/404、重试时连接断了，
      // 不能因此把死链降级成“传输失败”而进允许清单。
      lastError = String(error?.message ?? error)
    }
  }
  return { status: lastStatus, error: lastError }
}

export async function checkExternalLinks({ root, allowlist, concurrency = 8, timeout = 20000, retries = 1, log = console.log }) {
  const files = walkHtml(root)
  if (files.length === 0) throw new Error(`${root}: no HTML files found`)
  const byUrl = new Map()
  for (const file of files) {
    for (const url of extractExternalUrls(fs.readFileSync(file, 'utf8'))) {
      if (!byUrl.has(url)) byUrl.set(url, [])
      byUrl.get(url).push(path.relative(root, file))
    }
  }
  // 每个 URL 都要探测：允许清单只豁免“探到的那一种失败”，
  // 404/410 永远不会被豁免，否则一条宽正则会把将来的死链全部藏起来。
  const urls = [...byUrl.keys()].sort()
  const skipped = []
  const failures = []
  let next = 0
  async function worker() {
    while (next < urls.length) {
      const url = urls[next]
      next += 1
      const { status, error } = await probe(url, { timeout, retries })
      if (status !== 0 && status < 400) continue
      const dead = status === 404 || status === 410
      const entry = dead ? null : allowlistHit(url, allowlist)
      const allowed =
        entry &&
        (status === 0 ? entry.allowTransportError : entry.allowStatuses.includes(status))
      if (allowed) {
        skipped.push({
          url,
          status,
          reason: entry.reason,
          pages: byUrl.get(url),
        })
        continue
      }
      failures.push({ url, status, error: error || `HTTP ${status}`, pages: byUrl.get(url) })
    }
  }
  await Promise.all(Array.from({ length: Math.max(1, concurrency) }, worker))

  const results = { checked: urls.length, skipped, failures, pages: files.length }
  log(`external links: ${urls.length} checked, ${skipped.length} allowlisted, ${failures.length} failed (${files.length} pages)`)
  for (const item of skipped) {
    const why = item.status === 0 ? 'transport failure' : `HTTP ${item.status}`
    log(`SKIP ${item.url} — ${why}: ${item.reason}`)
  }
  for (const item of failures) {
    log(`FAIL ${item.url} — ${item.error || `HTTP ${item.status}`} (${item.pages.join(', ')})`)
  }
  return results
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const args = parseArgs(process.argv.slice(2))
  const allowlistPath = args.allowlist || defaultAllowlistPath()
  const allowlist = loadAllowlist(allowlistPath)
  const results = await checkExternalLinks({ root: args.root, allowlist, concurrency: args.concurrency, timeout: args.timeout, retries: args.retries })
  if (args.json) fs.writeFileSync(args.json, JSON.stringify(results, null, 2))
  process.exit(results.failures.length ? 1 : 0)
}
