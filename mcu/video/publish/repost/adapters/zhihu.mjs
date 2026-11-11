import { UnknownError, looksLoggedOut, normalizeText, pageBody, seriesName } from '../common.mjs'

const MANAGER = 'https://www.zhihu.com/creator/manage/creation/zvideo'

function parseClock(text) {
  const m = String(text || '').match(/(?:^|\s)(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s|$)/)
  if (!m) return null
  return m[3] ? Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) : Number(m[1]) * 60 + Number(m[2])
}

function parsePublishedAt(text) {
  const m = String(text || '').match(/(\d{4}[-/]\d{2}[-/]\d{2})(?:[ T](\d{2}:\d{2}))?/)
  return m ? `${m[1].replace(/\//g, '-')} ${m[2] || ''}`.trim() : ''
}

async function tagRows(page, title) {
  const want = normalizeText(title)
  if (!want) return []
  const series = seriesName()
  for (let round = 0; round < 20; round++) {
    const rows = await page.evaluate(
      ({ t, s }) => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        const vis = (e) => {
          const r = e.getBoundingClientRect()
          return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
        }
        const token = `zh-${Date.now()}-${Math.random().toString(16).slice(2)}`
        const leaves = [...document.querySelectorAll('div,span,p,h1,h2,h3,a')].filter(
          (e) => vis(e) && norm(e.innerText) === t,
        )
        const seen = new Set()
        const out = []
        for (const leaf of leaves) {
          let picked = null
          for (let box = leaf; box && box !== document.body; box = box.parentElement) {
            const text = norm(box.innerText)
            if (!text.includes(t)) continue
            picked = box
            if (norm(box.innerText).includes('更多') || box.querySelector('a[href*="/zvideo/"],a[href*="/pin/"]')) break
            if (text.length > t.length + 320) break
          }
          if (!picked || seen.has(picked)) continue
          seen.add(picked)
          const key = `${token}-${out.length}`
          picked.setAttribute('data-repost-row', key)
          const text = norm(picked.innerText).slice(0, 900)
          const link = picked.querySelector('a[href*="/zvideo/"],a[href*="/pin/"]')
          const img = picked.querySelector('img')
          out.push({
            key,
            href: link?.href || '',
            text,
            cover: img?.currentSrc || img?.src || '',
            collectionHit: s ? text.includes(s) : false,
            hasMore: text.includes('更多'),
          })
          if (out.length >= 5) break
        }
        return out
      },
      { t: want, s: series },
    )
    if (rows.length) return rows
    await page.keyboard.press('PageDown').catch(() => {})
    await page.mouse.wheel(0, 1400).catch(() => {})
    await page.waitForTimeout(900)
  }
  return []
}

function shape(title, hint, rows, info) {
  const row = rows[0]
  const id = row ? ((row.href.match(/(?:zvideo|pin)\/(\d{10,25})/) || [''])[1] || '') : ''
  return {
    id: id || hint?.id || null,
    title,
    duration: row ? parseClock(row.text) : null,
    cover: row?.cover || '',
    collection: row?.collectionHit ? seriesName() : null,
    publishedAt: row ? parsePublishedAt(row.text) || hint?.at || '' : hint?.at || '',
    evidence: row
      ? `row=${JSON.stringify(row.text.slice(0, 260))}; href=${row.href}`
      : `页面未出现标题精确匹配的视频行；${info ? `finalUrl=${info.url}; title=${info.title}` : ''}`,
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
    const rows = await tagRows(page, title)
    if (rows.length > 1) {
      return {
        id: hint?.id || null,
        title,
        duration: null,
        cover: rows[0].cover,
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
      return { login: false, rows: [], hintId: hint?.id || '', note: `未登录（${info.url}）` }
    }
    const rows = await tagRows(page, title)
    return {
      login: true,
      rows: rows.map((r) => ({ key: r.key, href: r.href, text: r.text.slice(0, 240), hasMore: r.hasMore })),
      hintId: hint?.id || '',
      note: '只读探针：已按标题锁行，未展开「更多」、未点删除',
    }
  },

  async deleteOld(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`知乎未登录，不能删除（${info.url}）`)
    const rows = await tagRows(page, title)
    if (rows.length !== 1) throw new UnknownError(`知乎标题精确命中 ${rows.length} 行，拒绝删除`)
    const oldId = old?.id || ''
    const rowId = (rows[0].href.match(/(?:zvideo|pin)\/(\d{10,25})/) || [''])[1]
    if (oldId && rowId && oldId !== rowId) {
      throw new UnknownError(`知乎行内 id=${rowId} 与 old.json=${oldId} 不一致，停手`)
    }
    const row = page.locator(`[data-repost-row="${rows[0].key}"]`).first()

    const more = await row.evaluate((el) => {
      const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
      const vis = (e) => {
        const r = e.getBoundingClientRect()
        return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
      }
      const hits = [...el.querySelectorAll('button,a,span,div')].filter((e) => {
        if (!vis(e)) return false
        const t = norm(e.innerText)
        return t === '更多' || (t === '' && /更多/.test(e.getAttribute('aria-label') || e.getAttribute('title') || ''))
      })
      if (hits.length !== 1) return { count: hits.length }
      const key = `more-${Date.now()}`
      hits[0].setAttribute('data-repost-more', key)
      return { count: 1, key }
    })
    if (more.count !== 1) throw new UnknownError(`知乎目标行内「更多」命中 ${more.count} 个，停手`)
    await page.locator(`[data-repost-more="${more.key}"]`).click({ timeout: 10_000 })
    await page.waitForTimeout(1200)

    const del = await page.evaluate(() => {
      const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
      const vis = (e) => {
        const r = e.getBoundingClientRect()
        return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
      }
      const hits = [...document.querySelectorAll('[role="menuitem"],button,li,div,span')].filter(
        (e) => vis(e) && norm(e.innerText) === '删除',
      )
      if (hits.length !== 1) return { count: hits.length }
      const key = `del-${Date.now()}`
      hits[0].setAttribute('data-repost-del', key)
      return { count: 1, key }
    })
    if (del.count !== 1) throw new UnknownError(`展开「更多」后「删除」命中 ${del.count} 个，停手`)
    await page.locator(`[data-repost-del="${del.key}"]`).click({ timeout: 10_000 })
    await page.waitForTimeout(1500)

    const confirm = await page.evaluate(() => {
      const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
      const vis = (e) => {
        const r = e.getBoundingClientRect()
        return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
      }
      const dialogs = [...document.querySelectorAll('[role="dialog"],[class*="Modal"],[class*="modal"]')]
        .filter(vis)
        .filter((d) => /删除/.test(norm(d.innerText)))
      if (!dialogs.length) return { found: false }
      const d = dialogs[dialogs.length - 1]
      const text = norm(d.innerText).slice(0, 300)
      const buttons = [...d.querySelectorAll('button,[role="button"],div,span')].filter((b) => {
        const t = norm(b.innerText)
        return vis(b) && ['确认', '确定', '删除'].includes(t)
      })
      if (!buttons.length) return { found: true, text, confirmCount: 0 }
      const key = `confirm-${Date.now()}`
      buttons[0].setAttribute('data-repost-confirm', key)
      return { found: true, text, confirmCount: buttons.length, key }
    })
    if (confirm.found && !confirm.key) {
      throw new UnknownError(`知乎二次确认里没有唯一按钮（${confirm.confirmCount} 个），停手：${confirm.text}`)
    }
    if (confirm.key) {
      await page.locator(`[data-repost-confirm="${confirm.key}"]`).click({ timeout: 10_000 })
      await page.waitForTimeout(4000)
    } else {
      await page.waitForTimeout(3000)
    }

    const after = await tagRows(page, title)
    const still = after.some((r) => (oldId ? r.href.includes(oldId) : true))
    if (still) throw new UnknownError('知乎删除后列表里仍能看到旧视频，按删除失败对待')
    return {
      deleted: true,
      oldId,
      confirmText: confirm.text || '',
      evidence: confirm.found ? '二次确认后旧行消失' : '点击删除后无二次确认，但旧行已消失',
    }
  },

  async confirmManualDeleted(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`知乎未登录，无法核对（${info.url}）`)
    const rows = await tagRows(page, title)
    const oldId = old?.id || ''
    const still = rows.some((r) => (oldId ? r.href.includes(oldId) : true))
    return {
      manual: true,
      verified: !still,
      oldId,
      evidence: still ? `旧行仍在：${rows.map((r) => r.href).join(' / ')}` : '列表里已看不到旧行',
    }
  },

  async verifyNew(page, { title, old, expectId, intro }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`知乎未登录，无法回读新稿（${info.url}）`)
    // 管理页作品卡显示的是介绍正文，不是标题（2026-10-29 实测：标题只出现在公开 pin 页的 document.title）。
    // 所以锁行只认 pin id；没有 id 就停手，别拿标题去匹配一张不显示标题的卡。
    if (!expectId) throw new UnknownError('没有 pin id（缺 .temp/zh-run/<ep>-published.txt），管理页无法锁行，拒绝判定')
    const card = await page.evaluate(
      ({ id, intro }) => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        const vis = (e) => {
          const r = e.getBoundingClientRect()
          return r.width > 1 && r.height > 1
        }
        const want = norm(intro).slice(0, 24)
        const anchors = [...document.querySelectorAll(`a[href*="/pin/${id}"]`)].filter(vis)
        if (!anchors.length) return { rows: 0 }
        let box = anchors[0]
        for (let i = 0; i < 12 && box.parentElement && box.parentElement !== document.body; i++) {
          box = box.parentElement
          const t = norm(box.innerText)
          if (want && t.includes(want) && /审核|已发布|发布于|编辑|更多/.test(t)) break
        }
        const text = norm(box.innerText).slice(0, 900)
        return { rows: 1, text, introHit: !want || text.includes(want) }
      },
      { id: expectId, intro: intro || '' },
    )
    if (!card.rows) throw new UnknownError(`知乎管理页里没找到 pin/${expectId} 的卡片，拒绝判定`)
    if (!card.introHit) throw new UnknownError(`pin/${expectId} 的卡片里没有本集介绍前缀，可能锁错行，停手`)

    const pinUrl = `https://www.zhihu.com/pin/${expectId}`
    let pin = { title: '', cover: '', coverSize: '', publishedAt: '' }
    const p2 = await page.context().newPage()
    try {
      await p2.goto(pinUrl, { waitUntil: 'domcontentloaded', timeout: 60_000 })
      await p2.waitForTimeout(6000)
      pin = await p2.evaluate(() => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        const m = (document.title || '').match(/的想法[:：]\s*(.*?)\s*\|/)
        const at = norm(document.body.innerText).match(/发布于\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})/)
        const imgs = [...document.querySelectorAll('img')]
          .map((i) => ({ src: i.currentSrc || i.src || '', w: i.naturalWidth, h: i.naturalHeight }))
          .filter((x) => x.w >= 1200)
        return {
          title: m ? m[1].trim() : '',
          cover: imgs[0]?.src || '',
          coverSize: imgs[0] ? `${imgs[0].w}×${imgs[0].h}` : '',
          publishedAt: at ? `${at[1]} ${at[2]}` : '',
        }
      })
    } finally {
      await p2.close().catch(() => {})
    }

    if (old?.id && expectId === old.id) throw new UnknownError(`知乎回读仍是旧 id ${expectId}`)
    return {
      id: expectId,
      title: pin.title,
      // 卡片「发布于刚刚 10:54」里的钟点是视频时长，不是时刻；只对刚发布的卡取第一个钟点。
      duration: parseClock(card.text),
      cover: pin.cover,
      collection: null,
      publishedAt: pin.publishedAt,
      evidence: `card=${JSON.stringify(card.text.slice(0, 260))}; pin=${pinUrl}; cover=${pin.coverSize || '(未读到)'}`,
      unavailable: [],
      oldId: old?.id || null,
    }
  },
}
