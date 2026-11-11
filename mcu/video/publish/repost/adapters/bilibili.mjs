import {
  UnknownError,
  looksLoggedOut,
  normalizeText,
  pageBody,
  seriesName,
} from '../common.mjs'

const MANAGER = 'https://member.bilibili.com/platform/upload-manager/article'

function parseClock(text) {
  const m = String(text || '').match(/(?:^|\s)(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s|$)/)
  if (!m) return null
  return m[3] ? Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) : Number(m[1]) * 60 + Number(m[2])
}

function parsePublishedAt(text) {
  const s = String(text || '')
  const m = s.match(/(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/)
  if (m) return `${m[1]} ${m[2]}`
  const cn = s.match(/(\d{4})年(\d{2})月(\d{2})日\s+(\d{2}:\d{2})/)
  return cn ? `${cn[1]}-${cn[2]}-${cn[3]} ${cn[4]}` : ''
}

async function findRows(page, title) {
  const want = normalizeText(title)
  if (!want) return []
  const series = seriesName()
  // 稿件管理列表是虚拟滚动：旧稿不在首屏时，靠 PageDown 滚 20 轮也可能滚不到（s5 的 row 就是这样丢的）。
  // 页头有「搜索稿件」，先把列表收敛到这一条再滚。输入走原生 setter + Enter，
  // 因为 React 控件不认直接改 value。
  const searched = await page
    .evaluate((t) => {
      const vis = (e) => {
        const r = e.getBoundingClientRect()
        return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
      }
      const input = [...document.querySelectorAll('input')].find((i) => vis(i) && /搜索稿件/.test(i.placeholder || ''))
      if (!input) return false
      input.focus()
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
      setter.call(input, t)
      input.dispatchEvent(new Event('input', { bubbles: true }))
      for (const type of ['keydown', 'keyup']) {
        input.dispatchEvent(new KeyboardEvent(type, { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }))
      }
      return true
    }, want)
    .catch(() => false)
  if (searched) await page.waitForTimeout(1800)
  for (let round = 0; round < 20; round++) {
    const rows = await page.evaluate(({ t, seriesName: s }) => {
      const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
      const vis = (e) => {
        const r = e.getBoundingClientRect()
        return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
      }
      return [...document.querySelectorAll('a[href*="/video/BV"]')]
        .filter((a) => vis(a) && norm(a.innerText) === t)
        .map((a) => {
          const boxes = []
          for (let box = a; box && box !== document.body; box = box.parentElement) {
            const text = norm(box.innerText)
            if (!text.includes(t)) continue
            boxes.push(box)
            if (text.length > t.length + 320) break
          }
          // 祖先链会一路套到页头：第一个 img 变成站点头像/图标，拿它冒充封面等于假绿。
          // 稿件行是 .article-card，卡内 bfs/archive 图才是真封面。
          const picked = a.closest('.article-card') || boxes[boxes.length - 1] || a
          const rowText = norm(picked.innerText).slice(0, 800)
          const imgs = [...picked.querySelectorAll('img')]
          const img =
            imgs.find((i) => /\/bfs\/archive\//.test(i.currentSrc || i.src || '')) ||
            imgs.find((i) => {
              const s = i.currentSrc || i.src || ''
              return s && !/\/static\/|\.svg(\?|$)/i.test(s)
            })
          return {
            href: a.href,
            rowText,
            cover: img?.currentSrc || img?.src || '',
            clock: rowText,
            collectionHit: s ? rowText.includes(s) : false,
          }
        })
    }, { t: want, seriesName: series })
    if (rows.length) return rows
    await page.keyboard.press('PageDown').catch(() => {})
    await page.mouse.wheel(0, 1400).catch(() => {})
    await page
      .evaluate(() => {
        let el = document.querySelector('a[href*="/video/BV"]')
        while (el && el.scrollHeight <= el.clientHeight) el = el.parentElement
        if (el) el.scrollTop += Math.floor(el.clientHeight * 0.9)
      })
      .catch(() => {})
    await page.waitForTimeout(900)
  }
  return []
}

// 稿件管理卡片不显示合集名，回读合集只能问公开接口（只读，用浏览器上下文自带的 Cookie）。
async function readSeason(page, bvid) {
  try {
    const r = await page.context().request.get(`https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`, {
      timeout: 15000,
    })
    if (!r.ok()) return null
    const j = await r.json()
    return j?.code === 0 ? j.data?.ugc_season?.title || null : null
  } catch {
    return null
  }
}

function shape(title, hint, rows, info) {
  const id = (rows[0]?.href.match(/BV[0-9A-Za-z]{10}/) || [''])[0]
  const row = rows[0]
  return {
    id: id || (hint?.id || null),
    title,
    duration: row ? parseClock(row.clock) : null,
    cover: row?.cover || '',
    collection: row?.collectionHit ? seriesName() : null,
    publishedAt: row ? parsePublishedAt(row.rowText) || hint?.at || '' : hint?.at || '',
    evidence: row
      ? `row=${JSON.stringify(row.rowText.slice(0, 240))}; href=${row.href}`
      : `页面未出现标题精确匹配的行；${info ? `finalUrl=${info.url}; title=${info.title}` : ''}`,
    unavailable: row ? [] : ['row'],
  }
}

export default {
  managerUrl: MANAGER,

  async readOld(page, { title, hint }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) {
      return {
        id: hint?.id || null,
        title,
        duration: null,
        cover: '',
        collection: null,
        publishedAt: hint?.at || '',
        evidence: `未登录：finalUrl=${info.url}; title=${info.title}；台账线索=${hint?.source || '(无)'}`,
        unavailable: ['login', 'row'],
      }
    }
    const rows = await findRows(page, title)
    if (rows.length > 1) {
      return {
        id: hint?.id || null,
        title,
        duration: null,
        cover: rows[0]?.cover || '',
        collection: null,
        publishedAt: hint?.at || '',
        evidence: `标题精确命中 ${rows.length} 行，拒绝猜是哪一条`,
        unavailable: ['row:ambiguous'],
      }
    }
    return shape(title, hint, rows, info)
  },

  async probeOld(page, { title, hint }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) {
      return {
        login: false,
        rows: [],
        hintId: hint?.id || '',
        note: `未登录（finalUrl=${info.url}）；已发布稿的换源/删除入口仍未实测`,
      }
    }
    const rows = await findRows(page, title)
    return {
      login: true,
      rows: rows.map((r) => ({ href: r.href, text: r.rowText.slice(0, 240) })),
      hintId: hint?.id || '',
      replaceEntryVisible: null,
      deleteEntryVisible: null,
      note: 'B站已发布稿件编辑页的换源/删除入口未经登录实测，探针只读列表',
    }
  },

  async deleteOld() {
    throw new UnknownError(
      'B站删除/换源仍未实测（探针 2026-10-22 被重定向到登录页）。登录后重跑 probe-platforms.mjs，' +
        '确认已发布编辑页有无「更换视频/换源」再决定；在此之前不自动点任何入口。',
    )
  },

  async confirmManualDeleted(page, { title, old }) {
    const rows = await findRows(page, title)
    const id = old?.id || ''
    const still = rows.some((r) => (id ? r.href.includes(id) : true))
    return {
      manual: true,
      verified: !still,
      oldId: id,
      evidence: still ? `旧行仍在：${rows.map((r) => r.href).join(' / ')}` : '列表里已看不到旧行',
    }
  },

  async verifyNew(page, { title, old, replace = false }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`B站未登录，无法回读新稿（${info.url}）`)
    const rows = await findRows(page, title)
    if (rows.length !== 1) throw new UnknownError(`B站回读到 ${rows.length} 行标题精确匹配，拒绝判定`)
    const got = shape(title, null, rows, info)
    if (!got.id) throw new UnknownError('B站回读没有 BV 号')
    // 换源时 BV 本来就该相同；「仍是旧 BV」只对删除重投成立。
    if (old?.id && got.id === old.id && !replace) throw new UnknownError(`B站回读仍是旧 BV ${got.id}`)
    if (!got.collection) got.collection = await readSeason(page, got.id)
    return { ...got, oldId: old?.id || null }
  },
}
