#!/usr/bin/env node
// 四平台只读能力探针：只回答“管理页上现在能看到哪些删/换入口”，不做任何删除或替换。
//
// 纪律（与 video-release skill §1/§6 同一条）：
// - 只 connectOverCDP 到常驻浏览器 9223；不 launch，不 browser.close()（close 会把人的登录窗口带走）。
// - 每平台自己 ctx.newPage()，收尾只 close 自己开的页；小红书常驻页永不碰。
// - 只有可见文案精确等于「更多」或省略号字形（aria-label/title 只作无文案回退且只认「更多」）的展开控件可以点；中心点必须命中原元素，候选自身/后代不得含动作词。
// - 不登录、不重试登录、不启动新浏览器；CDP 不通就整份报告记 not-logged-in + blocked=true。
//
// 输出：
//   .temp/v2-probe/report.json   （Task 16 的入口契约；status 只有 yes / no / not-logged-in）
//   stdout                       （由调用方重定向到 .temp/v2-probe/report.txt）
//   .temp/v2-probe/<platform>.png（可选证据截图，失败不影响结果）
//
// 用法：node video/publish/repost/probe-platforms.mjs
// 可选环境变量：PROBE_CDP / PROBE_WAIT_MS / PROBE_CONNECT_TIMEOUT_MS

import { chromium } from 'playwright'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

const CDP = process.env.PROBE_CDP || 'http://127.0.0.1:9223'
const OUT = resolve(process.cwd(), '.temp', 'v2-probe')
const WAIT_MS = Number(process.env.PROBE_WAIT_MS || 6000)
const CONNECT_TIMEOUT_MS = Number(process.env.PROBE_CONNECT_TIMEOUT_MS || 15000)

const TARGETS = {
  bilibili: 'https://member.bilibili.com/platform/upload-manager/article',
  douyin: 'https://creator.douyin.com/creator-micro/content/manage',
  zhihu: 'https://www.zhihu.com/creator/manage/creation/zvideo',
  xiaohongshu: 'https://creator.xiaohongshu.com/new/note-manager',
}

// 知乎的草稿箱路由是从页面 <a> 里实测拿到的（zhihu-plan.md），不是拼出来的。
const ZHIHU_DRAFT = 'https://www.zhihu.com/creator/manage/creation/draft?type=zvideo'

const RISK = {
  bilibili:
    '删除稿件会连带清空评论/弹幕/收藏与 BV 号；换源若重新转码会改变 cid，播放页、外链与合集归属都要复核。',
  douyin:
    '删除作品会清空评论、点赞与播放数据，作品 ID 不可复用；重发要重新过审并重新冷启动。',
  zhihu:
    '删除不可恢复；已发布页与草稿箱是两个入口，误删草稿会丢失续传；重发受账号级频率窗口限制（code=10000）。',
  xiaohongshu:
    '删除是行内图标按钮，hover 即显形，按坐标或“第一张卡片”点击容易误删；删除不可恢复，重发的笔记 ID 会变，原点/赞/评/藏都不迁移。',
}

const FORBIDDEN = /删除|确认|发布|提交|更换视频|重新上传/

const log = (...a) => console.log(...a)

function emptyResult(platform) {
  return { status: 'not-logged-in', entries: [], evidence: '', risk: RISK[platform] }
}

// 简报给定的扫描器：只读可见文本，原文长度 < 80，最多 30 条。
async function scan(page) {
  return page.evaluate(() => {
    const vis = (e) => {
      const r = e.getBoundingClientRect()
      return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
    }
    // 知乎的「更多」按钮 innerText 前面带 U+200B，必须剥掉，否则永远点不到展开。
    const T = (e) => (e.innerText || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
    return [...document.querySelectorAll('button,a,[role=menuitem],li,span,div')]
      .filter((e) => vis(e) && T(e).length < 80 && /删除|更换视频|换源|重新上传/.test(T(e)))
      .map((e) => ({ tag: e.tagName, text: T(e), cls: String(e.className || '').slice(0, 80), href: e.href || '' }))
      .slice(0, 30)
  })
}

function dedupe(entries) {
  const seen = new Set()
  const out = []
  for (const e of entries) {
    const k = `${e.tag}\u0000${e.text}\u0000${e.href}`
    if (seen.has(k)) continue
    seen.add(k)
    out.push(e)
  }
  return out.slice(0, 30)
}

async function pageInfo(page) {
  return page.evaluate(() => {
    const body = (document.body?.innerText || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
    return { url: location.href, title: document.title, body: body.slice(0, 1600), bodyLen: body.length }
  })
}

const LOGIN_MARKER = {
  bilibili: /稿件管理|稿件列表|视频管理|内容管理|数据中心/,
  douyin: /作品管理|内容管理|全部作品|作品列表|数据看板/,
  zhihu: /创作中心|已发布|草稿箱|我的创作/,
  xiaohongshu: /笔记管理|已发布|草稿箱|笔记列表/,
}
const LOGIN_WALL = /扫码登录|手机号登录|密码登录|验证码登录|请先登录|登录后(?:查看|使用|继续)|登录\/注册|立即登录/
const ERROR_PAGE = /页面不见了|你访问的页面不存在|页面不存在|访问异常|系统繁忙|出错了|404 Not Found/i

function assessLogin(platform, info) {
  const urlLogin = /passport\.bilibili\.com|\/login|\/signin|\/sso/i.test(info.url)
  const hasMarker = LOGIN_MARKER[platform].test(info.body)
  const hasWall = LOGIN_WALL.test(info.body)
  const errorPage = ERROR_PAGE.test(info.body) && info.bodyLen < 2000
  const loggedIn = !urlLogin && !errorPage && (hasMarker || (!hasWall && info.bodyLen > 200))
  return { loggedIn, urlLogin, hasMarker, hasWall, errorPage }
}

// 只找“更多 / ⋯”这类展开控件；不按 class 猜、不点任何动作词。
async function expandOnce(page) {
  const candidates = await page.evaluate(() => {
    const FORBIDDEN_TEXT = /删除|确认|发布|提交|更换视频|重新上传/
    const vis = (e) => {
      const r = e.getBoundingClientRect()
      return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
    }
    const T = (e) => (e.innerText || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
    const hasForbidden = (el) => {
      if (FORBIDDEN_TEXT.test(el.innerText || '')) return true
      if (FORBIDDEN_TEXT.test(el.getAttribute('aria-label') || '')) return true
      if (FORBIDDEN_TEXT.test(el.getAttribute('title') || '')) return true
      return [...el.querySelectorAll('*')].some((d) => {
        if (FORBIDDEN_TEXT.test(d.innerText || '')) return true
        if (FORBIDDEN_TEXT.test(d.getAttribute('aria-label') || '')) return true
        return FORBIDDEN_TEXT.test(d.getAttribute('title') || '')
      })
    }
    const out = []
    const token = String(Date.now())
    for (const e of document.querySelectorAll('button,[role="button"],a,span,div,svg')) {
      if (!vis(e)) continue
      const t = T(e)
      const aria = (e.getAttribute('aria-label') || '').trim()
      const title = (e.getAttribute('title') || '').trim()
      // 可见文案必须精确命中；aria-label/title 只作无可见文案时的回退，且只接受「更多」。
      const exact = t === '更多' || /^(⋯|…|···|\.\.\.|•••)$/.test(t) || (t === '' && (aria === '更多' || title === '更多'))
      if (!exact) continue
      // 候选自身或任一后代带动作词就放弃，避免把删除/提交控件当成展开控件。
      if (hasForbidden(e)) continue
      const r = e.getBoundingClientRect()
      if (r.width < 4 || r.height < 4) continue
      const cx = r.x + r.width / 2
      const cy = r.y + r.height / 2
      const top = document.elementFromPoint(cx, cy)
      // 必须命中的就是候选元素本身：若中心点落在后代图标上，点击可能点到嵌套的删除图标。
      if (!top || top !== e) continue
      const key = `probe-more-${token}-${out.length}`
      e.setAttribute('data-probe-more', key)
      out.push({ key, text: t || aria || title, x: Math.round(cx), y: Math.round(cy) })
      if (out.length >= 8) break
    }
    return out
  })

  for (const c of candidates) {
    const el = page.locator(`[data-probe-more="${c.key}"]`).first()
    const txt = (await el.innerText().catch(() => '')).replace(/\s+/g, ' ').trim()
    const label = txt || c.text || ''
    // 双保险：展开控件自身绝不允许带动作词。
    if (FORBIDDEN.test(label)) continue
    try {
      await el.click({ timeout: 4000 })
      await page.waitForTimeout(1200)
      return { clicked: c.text || label || '(glyph)', at: { x: c.x, y: c.y } }
    } catch (e) {
      log(`  [展开] 点不动「${c.text || '⋯'}」：${e.message.split('\n')[0]}`)
    }
  }
  return null
}

async function menuTexts(page) {
  return page.evaluate(() => {
    const vis = (e) => {
      const r = e.getBoundingClientRect()
      return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
    }
    const T = (e) => (e.innerText || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
    const sels = '[role="menuitem"],[role="menu"] li,[class*="dropdown"] li,[class*="popover"] li,[class*="menu-item"],[class*="semi-dropdown"] *'
    const out = []
    for (const e of document.querySelectorAll(sels)) {
      if (!vis(e)) continue
      const t = T(e)
      if (!t || t.length > 30) continue
      if (!out.includes(t)) out.push(t)
      if (out.length >= 60) break
    }
    return out
  })
}

async function shot(page, name) {
  try {
    await page.screenshot({ path: join(OUT, `${name}.png`), fullPage: false })
  } catch {
    /* 截图只是旁证，失败不影响判据 */
  }
}

async function biliExtras(page) {
  return page.evaluate(() => {
    const T = (e) => (e.innerText || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
    const links = [...document.querySelectorAll('a[href]')]
      .map((a) => ({ href: a.href, text: T(a) }))
      // 只记录稿件管理页的编辑入口；登录页上的公开视频链接不是编辑入口。
      .filter((l) => {
        try {
          const u = new URL(l.href)
          return u.hostname === 'member.bilibili.com' && u.pathname.includes('upload-manager')
        } catch {
          return false
        }
      })
    const seen = new Set()
    const deduped = []
    for (const l of links) {
      const k = `${l.href}\u0000${l.text}`
      if (seen.has(k)) continue
      seen.add(k)
      deduped.push(l)
      if (deduped.length >= 10) break
    }
    const stripQuery = (u) => {
      try {
        const url = new URL(u)
        return `${url.protocol}//${url.host}${url.pathname}`
      } catch {
        return u.split(/[?#]/)[0]
      }
    }
    const net = [
      ...new Set(
        performance.getEntriesByType('resource')
          .map((e) => e.name)
          .filter((u) => /replace|source|upload/i.test(u))
          .map((u) => stripQuery(u)),
      ),
    ].slice(0, 40)
    return { editLinks: deduped, networkEntries: net }
  })
}

async function xhsExtras(page) {
  // 小红书行内动作默认 opacity:0，hover 笔记卡片才显形；只 hover，不点。
  await page.locator('.note-card').first().hover({ timeout: 3000 }).catch(() => {})
  await page.waitForTimeout(600)
  return page.evaluate(() => {
    const links = [...document.querySelectorAll('a[href*="/publish/update"]')].map((a) => ({
      href: a.href,
      text: (a.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
    }))
    const noteCards = [...document.querySelectorAll('.note-card')]
    const noteIds = noteCards
      .map((c) => (c.getAttribute('data-impression') || '').match(/"noteId":"([^"]+)"/)?.[1])
      .filter(Boolean)
    const delBtns = [...document.querySelectorAll('.note-card__action-btn--del')]
    const editBtns = [...document.querySelectorAll('.note-card__action-btn:not(.note-card__action-btn--del)')]
    return {
      editLinks: links.slice(0, 10),
      editLinkHasId: links.some((l) => /[?&]id=/.test(l.href)),
      noteCardCount: noteCards.length,
      noteIds: noteIds.slice(0, 5),
      // 删除是图标按钮（垃圾桶），没有文字/aria，只能靠类名识别；本次探针不点它。
      deleteControlCount: delBtns.length,
      deleteControlPresent: delBtns.length > 0,
      deleteControlClass: delBtns[0] ? String(delBtns[0].className || '') : '',
      editControlCount: editBtns.length,
    }
  })
}

async function probeSingle(platform, page) {
  const target = TARGETS[platform]
  const out = emptyResult(platform)
  const extra = {}
  log(`\n▶ ${platform}: ${target}`)

  try {
    await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(WAIT_MS)
    const info = await pageInfo(page)
    const login = assessLogin(platform, info)
    log(`  最终 URL: ${info.url}`)
    log(`  title: ${info.title}`)
    log(`  登录判定: ${login.loggedIn ? '已登录（有创作者中心标记）' : login.errorPage ? '页面异常，无法观测' : '未登录/无法确认'}`)

    let entries = dedupe(await scan(page))
    extra.expansions = []
    extra.menuTexts = []
    if (entries.length === 0 && login.loggedIn) {
      const exp = await expandOnce(page)
      if (exp) {
        extra.expansions.push(exp)
        extra.menuTexts = await menuTexts(page)
        entries = dedupe([...entries, ...(await scan(page))])
        log(`  [展开] 点了「${exp.clicked}」，菜单文字: ${extra.menuTexts.slice(0, 20).join(' | ') || '（无）'}`)
      } else {
        log('  [展开] 没有找到可见的「更多/⋯」展开控件')
      }
    }

    if (platform === 'bilibili') {
      Object.assign(extra, await biliExtras(page))
      extra.replaceEntryVisible = entries.some((e) => /更换视频|换源/.test(e.text))
      extra.deleteEntryVisible = entries.some((e) => /删除/.test(e.text))
    }
    if (platform === 'douyin') {
      extra.singleWorkMenuHasDelete = entries.some((e) => /删除/.test(e.text)) || extra.menuTexts.some((t) => /删除/.test(t))
    }
    if (platform === 'xiaohongshu') {
      Object.assign(extra, await xhsExtras(page))
      // 小红书的删除是行内垃圾桶图标（无文字、默认 opacity:0），只能靠类名判定。
      extra.deleteInlineAction =
        entries.some((e) => /删除/.test(e.text)) ||
        extra.menuTexts.some((t) => /删除/.test(t)) ||
        extra.deleteControlPresent === true
    }

    await shot(page, platform)
    const finalUrl = page.url()
    const finalTitle = await page.title().catch(() => info.title)

    let capabilityHit = entries.length > 0
    if (platform === 'xiaohongshu' && extra.deleteControlPresent) capabilityHit = true

    if (!login.loggedIn) {
      out.status = 'not-logged-in'
    } else if (capabilityHit) {
      out.status = 'yes'
    } else {
      out.status = 'no'
    }

    out.entries = entries
    let evidence = [
      `finalUrl=${finalUrl}`,
      `title=${finalTitle}`,
      `entries=${JSON.stringify(entries)}`,
      `expanded=${JSON.stringify(extra.expansions.map((e) => e.clicked))}`,
      `menuTexts=${JSON.stringify(extra.menuTexts.slice(0, 30))}`,
    ].join('; ')
    if (platform === 'xiaohongshu') {
      evidence += `; noteCards=${extra.noteCardCount}; deleteControl=${extra.deleteControlPresent} count=${extra.deleteControlCount} cls=${JSON.stringify(extra.deleteControlClass)}; editAnchors=${extra.editLinks.length} editAnchorHasId=${extra.editLinkHasId}; noteIds=${JSON.stringify(extra.noteIds)}`
    }
    out.evidence = evidence
    out.extra = extra
    log(`  命中 ${entries.length} 条：`)
    for (const e of entries) log(`    [${e.tag}] ${JSON.stringify(e.text)} href=${e.href || ''}`)
    log(`  status = ${out.status}`)
    return out
  } catch (e) {
    out.status = 'not-logged-in'
    out.evidence = `navigation/probe failed at ${target}: ${e.message.split('\n')[0]}; page not observable`
    out.extra = extra
    log(`  ✗ 失败: ${out.evidence}`)
    return out
  }
}

async function probeZhihu(page) {
  const out = emptyResult('zhihu')
  const parts = []
  const extra = { published: null, draft: null }

  for (const [kind, url] of [
    ['published', TARGETS.zhihu],
    ['draft', ZHIHU_DRAFT],
  ]) {
    log(`\n▶ zhihu/${kind}: ${url}`)
    const part = { kind, url, finalUrl: '', title: '', result: 'not-logged-in', entries: [], expansions: [], menuTexts: [] }
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
      await page.waitForTimeout(WAIT_MS)
      const info = await pageInfo(page)
      part.finalUrl = info.url
      part.title = info.title
      const login = assessLogin('zhihu', info)
      log(`  最终 URL: ${info.url}`)
      log(`  title: ${info.title}`)
      log(`  登录判定: ${login.loggedIn ? '已登录' : login.errorPage ? '页面异常，无法观测' : '未登录/无法确认'}`)
      let entries = dedupe(await scan(page))
      if (entries.length === 0 && login.loggedIn) {
        const exp = await expandOnce(page)
        if (exp) {
          part.expansions.push(exp)
          part.menuTexts = await menuTexts(page)
          entries = dedupe([...entries, ...(await scan(page))])
          log(`  [展开] 点了「${exp.clicked}」，菜单文字: ${part.menuTexts.slice(0, 20).join(' | ') || '（无）'}`)
        }
      }
      await shot(page, `zhihu-${kind}`)
      part.finalUrl = page.url()
      part.title = await page.title().catch(() => info.title)
      part.entries = entries
      part.loggedIn = login.loggedIn
      part.result = !login.loggedIn ? 'not-logged-in' : entries.length ? 'yes' : 'no'
      log(`  命中 ${entries.length} 条，result = ${part.result}`)
      for (const e of entries) log(`    [${e.tag}] ${JSON.stringify(e.text)} href=${e.href || ''}`)
    } catch (e) {
      part.error = e.message.split('\n')[0]
      log(`  ✗ 失败: ${part.error}`)
    }
    extra[kind] = part
    parts.push(part)
  }

  const published = extra.published
  const draft = extra.draft
  const entries = [...(published?.entries || []), ...(draft?.entries || [])]
  const loggedIn = published?.loggedIn || draft?.loggedIn
  out.status = !loggedIn ? 'not-logged-in' : entries.length ? 'yes' : 'no'
  out.entries = entries
  out.evidence = [
    `published.finalUrl=${published?.finalUrl || ''}`,
    `published.title=${published?.title || ''}`,
    `published.entries=${JSON.stringify(published?.entries || [])}`,
    `draft.finalUrl=${draft?.finalUrl || ''}`,
    `draft.title=${draft?.title || ''}`,
    `draft.entries=${JSON.stringify(draft?.entries || [])}`,
  ].join('; ')
  out.extra = extra
  log(`\n  zhihu status = ${out.status}（已发布 ${published?.result || '?'} / 草稿 ${draft?.result || '?'}）`)
  return out
}

function writeReport(report) {
  mkdirSync(OUT, { recursive: true })
  const file = join(OUT, 'report.json')
  writeFileSync(file, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  return file
}

async function main() {
  mkdirSync(OUT, { recursive: true })
  const report = {
    at: new Date().toISOString(),
    cdp: CDP,
    blocked: false,
    blockedReason: null,
    platforms: {},
  }

  let browser
  try {
    browser = await chromium.connectOverCDP(CDP, { timeout: CONNECT_TIMEOUT_MS })
  } catch (e) {
    report.blocked = true
    report.blockedReason = `CDP unreachable at ${CDP}: ${e.message.split('\n')[0]}`
    for (const p of Object.keys(TARGETS)) {
      const r = emptyResult(p)
      r.evidence = `CDP unreachable at ${CDP}: ${e.message.split('\n')[0]}; no page opened; login state unknown; BLOCKED`
      report.platforms[p] = r
    }
    const file = writeReport(report)
    log(`\n✗ BLOCKED: ${report.blockedReason}`)
    log('  按纪律没有启动新浏览器、没有尝试登录；四平台均记为 not-logged-in（无法观测）。')
    log(`  已写 ${file}`)
    await new Promise((r) => process.stdout.write('', r))
    process.exit(2)
  }

  const contexts = browser.contexts()
  if (!contexts.length) {
    report.blocked = true
    report.blockedReason = 'CDP connected but no browser context (no logged-in window)'
    for (const p of Object.keys(TARGETS)) {
      const r = emptyResult(p)
      r.evidence = `${report.blockedReason}; no page opened; BLOCKED`
      report.platforms[p] = r
    }
    const file = writeReport(report)
    log(`\n✗ BLOCKED: ${report.blockedReason}`)
    log(`  已写 ${file}`)
    await new Promise((r) => process.stdout.write('', r))
    process.exit(2)
  }

  const ctx = contexts[0]
  log(`✓ 已连接 CDP ${CDP}；contexts=${contexts.length}，现有页面=${ctx.pages().length}（只读，不关任何既有页）`)

  for (const platform of Object.keys(TARGETS)) {
    let page
    try {
      page = await ctx.newPage()
      page.setDefaultTimeout(45_000)
      page.setDefaultNavigationTimeout(60_000)
      page.on('dialog', (d) => d.dismiss().catch(() => {}))
      const r = platform === 'zhihu' ? await probeZhihu(page) : await probeSingle(platform, page)
      report.platforms[platform] = r
    } catch (e) {
      // 开页/探针本身失败也要落报告：这一平台记为无法观测，其余平台继续。
      const r = emptyResult(platform)
      r.evidence = `newPage/probe failed for ${platform}: ${e.message.split('\n')[0]}; page not observable`
      report.platforms[platform] = r
      log(`\n✗ ${platform}: ${r.evidence}`)
    } finally {
      // 只关自己开的页；绝不 browser.close()。
      if (page) await page.close().catch(() => {})
    }
  }

  const file = writeReport(report)
  log('\n===== 汇总 =====')
  for (const [p, r] of Object.entries(report.platforms)) log(`${p.padEnd(12)} ${r.status}`)
  log(`已写 ${file}`)

  const statuses = Object.values(report.platforms).map((r) => r.status)
  const code = statuses.every((s) => s === 'yes' || s === 'no') ? 0 : 3
  await new Promise((r) => process.stdout.write('', r))
  process.exit(code)
}

await main()
