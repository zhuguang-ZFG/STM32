import { UnknownError, looksLoggedOut, normalizeText, pageBody, seriesName } from '../common.mjs'

const MANAGER = 'https://creator.xiaohongshu.com/new/note-manager'

function parsePublishedAt(text) {
  const m = String(text || '').match(/(\d{4}[-/]\d{2}[-/]\d{2})(?:[ T](\d{2}:\d{2}))?/)
  return m ? `${m[1].replace(/\//g, '-')} ${m[2] || ''}`.trim() : ''
}

async function scrollOnce(page) {
  await page.keyboard.press('PageDown').catch(() => {})
  await page.mouse.move(700, 600).catch(() => {})
  await page.mouse.wheel(0, 1400).catch(() => {})
  await page
    .evaluate(() => {
      const box = document.querySelector('.content')
      if (box && box.scrollHeight > box.clientHeight) {
        box.scrollTop = box.scrollHeight
        return
      }
      let el = document.querySelector('.note-card')
      while (el && el.scrollHeight <= el.clientHeight) el = el.parentElement
      if (el) el.scrollTop = el.scrollHeight
    })
    .catch(() => {})
  await page.waitForTimeout(1000)
}

async function tagCards(page, title) {
  const want = normalizeText(title)
  if (!want) return []
  const series = seriesName()
  for (let round = 0; round < 40; round++) {
    const cards = await page.evaluate(
      ({ t, s }) => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        const vis = (e) => {
          const r = e.getBoundingClientRect()
          return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
        }
        const token = `xhs-${Date.now()}-${Math.random().toString(16).slice(2)}`
        const out = []
        for (const card of [...document.querySelectorAll('.note-card')].filter(vis)) {
          // 标题是独立的 .note-card__title，body 文本前面还有「未通过 / 已发布」状态，不能拿 body 当前缀。
          const titleEl = card.querySelector('.note-card__title')
          const titleText = norm(titleEl?.innerText || '')
          if (titleText !== t) continue
          if (card.hasAttribute('data-repost-row')) continue
          const key = `${token}-${out.length}`
          card.setAttribute('data-repost-row', key)
          const impression = card.getAttribute('data-impression') || ''
          const noteId = (impression.match(/"noteId":"([0-9a-f]{24})"/) || [])[1] || ''
          const img = card.querySelector('.note-card__cover img')
          const bgEl = card.querySelector('.note-card__cover .inner-bg') || card.querySelector('.note-card__cover')
          const bg = bgEl ? getComputedStyle(bgEl).backgroundImage : ''
          const cover = img?.currentSrc || img?.src || (bg.match(/url\("?([^")]+)"?\)/) || [])[1] || ''
          const full = norm(card.innerText).slice(0, 900)
          out.push({
            key,
            noteId,
            text: full,
            cover,
            collectionHit: s ? full.includes(s) : false,
            status: (full.match(/已发布|审核中|未通过|仅自己可见/) || [''])[0],
          })
          if (out.length >= 5) break
        }
        return out
      },
      { t: want, s: series },
    )
    if (cards.length) return cards
    await scrollOnce(page)
  }
  return []
}

function shape(title, hint, cards, info) {
  const card = cards[0]
  return {
    id: card?.noteId || hint?.id || null,
    title,
    duration: null,
    cover: card?.cover || '',
    collection: card?.collectionHit ? seriesName() : null,
    publishedAt: card ? parsePublishedAt(card.text) || hint?.at || '' : hint?.at || '',
    evidence: card
      ? `card=${JSON.stringify(card.text.slice(0, 260))}; noteId=${card.noteId || '(空)'}; status=${card.status || '(未读)'}`
      : `页面未出现标题精确匹配的笔记卡片；${info ? `finalUrl=${info.url}; title=${info.title}` : ''}`,
    unavailable: card ? [] : ['row'],
    ...(card ? { status: card.status } : {}),
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
    const cards = await tagCards(page, title)
    if (cards.length > 1) {
      return {
        id: hint?.id || null,
        title,
        duration: null,
        cover: cards[0].cover,
        collection: null,
        publishedAt: hint?.at || '',
        evidence: `标题精确命中 ${cards.length} 张卡片，拒绝猜是哪一条`,
        unavailable: ['row:ambiguous'],
      }
    }
    return shape(title, hint, cards, info)
  },

  async probeOld(page, { title, hint }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) {
      return { login: false, rows: [], hintId: hint?.id || '', note: `未登录（${info.url}）` }
    }
    const cards = await tagCards(page, title)
    const out = []
    for (const c of cards) {
      const row = page.locator(`[data-repost-row="${c.key}"]`).first()
      await row.hover({ timeout: 3000 }).catch(() => {})
      await page.waitForTimeout(600)
      const controls = await row.evaluate((el) => {
        const vis = (e) => {
          const r = e.getBoundingClientRect()
          return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
        }
        const del = [...el.querySelectorAll('.note-card__action-btn--del')].filter(vis)
        const tips = [...document.querySelectorAll('[class*="tooltip"],[role="tooltip"],[class*="popover"]')]
          .filter(vis)
          .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
          .filter(Boolean)
        return { deleteCount: del.length, deleteClass: del[0] ? String(del[0].className || '') : '', tips }
      })
      out.push({ key: c.key, noteId: c.noteId, text: c.text.slice(0, 240), ...controls })
    }
    return {
      login: true,
      rows: out,
      hintId: hint?.id || '',
      note: '只读探针：hover 卡片读取图标与 tooltip，未点删除',
    }
  },

  async deleteOld(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`小红书未登录，不能删除（${info.url}）`)
    const cards = await tagCards(page, title)
    if (cards.length !== 1) throw new UnknownError(`小红书标题精确命中 ${cards.length} 张卡片，拒绝删除`)
    const oldId = old?.id || ''
    if (oldId && cards[0].noteId && oldId !== cards[0].noteId) {
      throw new UnknownError(`小红书卡片 noteId=${cards[0].noteId} 与 old.json=${oldId} 不一致，停手`)
    }
    const row = page.locator(`[data-repost-row="${cards[0].key}"]`).first()
    await row.hover({ timeout: 5000 })
    await page.waitForTimeout(800)

    const del = await row.evaluate((el) => {
      const vis = (e) => {
        const r = e.getBoundingClientRect()
        return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
      }
      const hits = [...el.querySelectorAll('.note-card__action-btn--del')].filter(vis)
      if (hits.length !== 1) return { count: hits.length }
      const key = `del-${Date.now()}`
      hits[0].setAttribute('data-repost-del', key)
      const r = hits[0].getBoundingClientRect()
      const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2)
      if (top !== hits[0] && !hits[0].contains(top)) return { count: 1, centerMiss: true }
      return { count: 1, key }
    })
    if (del.count !== 1) throw new UnknownError(`目标卡片上删除图标命中 ${del.count} 个，不敢点`)
    if (del.centerMiss) throw new UnknownError('删除图标中心点没有命中原元素，不敢点')
    await page.locator(`[data-repost-del="${del.key}"]`).click({ timeout: 10_000 })
    await page.waitForTimeout(1500)

    const confirm = await page.evaluate(() => {
      const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
      const vis = (e) => {
        const r = e.getBoundingClientRect()
        return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
      }
      const BTN = 'button,[role="button"],[class*="btn"],[class*="Btn"]'
      const clickableIn = (root) =>
        [...root.querySelectorAll(BTN)].filter(
          (b) => vis(b) && ![...root.querySelectorAll(BTN)].some((o) => o !== b && o.contains(b) && vis(o)),
        )
      const dialogs = [...document.querySelectorAll('[role="dialog"],[class*="modal"],[class*="Modal"],[class*="popconfirm"]')]
        .filter(vis)
        .filter((d) => /删除/.test(norm(d.innerText)))
      if (!dialogs.length) return { found: false }
      // 实测弹窗是 .d-modal-content（只有正文）+ 兄弟 footer（按钮）；从正向往上找到同时包住按钮的容器。
      let d = dialogs[dialogs.length - 1]
      for (let i = 0; i < 6 && d.parentElement && d.parentElement !== document.body; i++) {
        d = d.parentElement
        if (clickableIn(d).some((b) => /删除|确定|确认|取消/.test(norm(b.innerText)))) break
      }
      const text = norm(d.innerText).slice(0, 300)
      const rankOf = (t) => {
        if (t === '确认删除' || t === '确定删除') return 0
        if (t === '删除') return 1
        if (/删除/.test(t) && !/取消/.test(t) && t.length <= 6) return 2
        if (t === '确定' || t === '确认') return 3
        return 9
      }
      const buttons = clickableIn(d)
        .map((b) => ({ b, t: norm(b.innerText), r: rankOf(norm(b.innerText)) }))
        .filter((x) => x.r < 9)
      if (!buttons.length) {
        const clickable = clickableIn(d).map((b) => ({
          tag: b.tagName,
          cls: String(b.className || '').slice(0, 60),
          text: norm(b.innerText).slice(0, 40),
          aria: b.getAttribute('aria-label') || '',
        }))
        return { found: true, text, confirmCount: 0, clickable, html: d.outerHTML.slice(0, 1500) }
      }
      buttons.sort((a, b) => a.r - b.r)
      if (buttons.length > 1 && buttons[0].r === buttons[1].r) {
        return { found: true, text, confirmCount: buttons.filter((x) => x.r === buttons[0].r).length }
      }
      const key = `confirm-${Date.now()}`
      buttons[0].b.setAttribute('data-repost-confirm', key)
      return { found: true, text, confirmCount: 1, key, label: buttons[0].t }
    })
    if (confirm.found && !confirm.key) {
      const detail = confirm.clickable?.length
        ? `；可点元素=${JSON.stringify(confirm.clickable)}`
        : `；可点元素为空；html=${confirm.html || ''}`
      throw new UnknownError(`小红书二次确认里没有唯一按钮（${confirm.confirmCount} 个），停手：${confirm.text}${detail}`)
    }
    if (confirm.key) {
      await page.locator(`[data-repost-confirm="${confirm.key}"]`).click({ timeout: 10_000 })
      await page.waitForTimeout(4000)
    } else {
      await page.waitForTimeout(3000)
    }

    const after = await tagCards(page, title)
    const still = after.some((c) => (oldId ? c.noteId === oldId : true))
    if (still) throw new UnknownError('小红书删除后列表里仍能看到旧卡片，按删除失败对待')
    return {
      deleted: true,
      oldId,
      confirmText: confirm.text || '',
      evidence: confirm.found ? '二次确认后旧卡片消失' : '点击删除后无二次确认，但旧卡片已消失',
    }
  },

  async confirmManualDeleted(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`小红书未登录，无法核对（${info.url}）`)
    const cards = await tagCards(page, title)
    const oldId = old?.id || ''
    const still = cards.some((c) => (oldId ? c.noteId === oldId : true))
    return {
      manual: true,
      verified: !still,
      oldId,
      evidence: still ? `旧卡片仍在：${cards.map((c) => c.noteId || '(无 id)').join(' / ')}` : '列表里已看不到旧卡片',
    }
  },

  async verifyNew(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`小红书未登录，无法回读新笔记（${info.url}）`)
    const cards = await tagCards(page, title)
    if (cards.length !== 1) throw new UnknownError(`小红书回读到 ${cards.length} 张标题精确匹配的卡片，拒绝判定`)
    const got = shape(title, null, cards, info)
    if (!got.id) throw new UnknownError('小红书回读没有 noteId')
    if (old?.id && got.id === old.id) throw new UnknownError(`小红书回读仍是旧 noteId ${got.id}`)
    return { ...got, oldId: old?.id || null }
  },
}
