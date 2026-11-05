import { UnknownError, looksLoggedOut, normalizeText, pageBody, seriesName } from '../common.mjs'

const MANAGER = 'https://creator.douyin.com/creator-micro/content/manage'
const DETAIL_ID = /work-detail\/(\d{15,25})/

function parseClock(text) {
  const m = String(text || '').match(/(?:^|\s)(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s|$)/)
  if (!m) return null
  return m[3] ? Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) : Number(m[1]) * 60 + Number(m[2])
}

function parsePublishedAt(text) {
  const pad = (n) => String(n).padStart(2, '0')
  const zh = String(text || '').match(/(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})/)
  if (zh) return `${zh[1]}-${pad(zh[2])}-${pad(zh[3])}T${pad(zh[4])}:${zh[5]}+08:00`
  const m = String(text || '').match(/(\d{4}[-/]\d{2}[-/]\d{2})[ T]?(\d{2}:\d{2})?/)
  return m ? `${m[1].replace(/\//g, '-')} ${m[2] || ''}`.trim() : ''
}

// 作品卡片没有 /video/ 链接，也没有 id 属性；标题与文案同在一个文本块里，
// 只能按卡片文本前缀匹配，命中后必须唯一。列表在 .list-scroll-* 里滚动加载。
async function locateCard(page, title, { maxRounds = 140, waitMs = 800 } = {}) {
  const want = normalizeText(title)
  if (!want) return { rows: [], exhausted: false, reason: 'empty-title' }

  let lastSh = 0
  let stuck = 0
  for (let round = 0; round < maxRounds; round++) {
    const res = await page.evaluate(
      ({ t }) => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        const vis = (e) => {
          const r = e.getBoundingClientRect()
          return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
        }
        const infos = [...document.querySelectorAll('[class*="video-card-info"]')]
          .filter((e) => vis(e) && norm(e.innerText).startsWith(t))
        if (infos.length) {
          const token = `repost-${Date.now()}-${Math.random().toString(16).slice(2)}`
          const rows = []
          const seen = new Set()
          for (const info of infos) {
            let card = info
            for (let k = 0; k < 8 && card; k++) {
              if (String(card.className || '').includes('video-card-content')) break
              card = card.parentElement
            }
            if (!card || seen.has(card)) continue
            seen.add(card)
            const key = `${token}-${rows.length}`
            card.setAttribute('data-repost-card', key)
            const text = norm(card.innerText).slice(0, 1200)
            const coverEl = card.querySelector('[class*="video-card-cover"]')
            const bg = coverEl ? getComputedStyle(coverEl).backgroundImage : ''
            const cover = (bg.match(/url\("?([^")]+)"?\)/) || [])[1] || ''
            rows.push({ key, text, cover, hasDelete: text.includes('删除作品') })
            if (rows.length >= 5) break
          }
          return { rows, done: true }
        }
        const box = document.querySelector('[class*="list-scroll"]')
        if (!box) return { rows: [], done: true, reason: 'no-list' }
        box.scrollTop = box.scrollHeight
        return {
          rows: [],
          done: false,
          atEnd: /没有更多作品/.test(document.body.innerText || ''),
          sh: box.scrollHeight,
          top: Math.round(box.scrollTop),
        }
      },
      { t: want },
    )
    if (res.rows?.length) {
      const series = seriesName()
      for (const r of res.rows) {
        r.collectionHit = !!series && normalizeText(r.text).includes(normalizeText(series))
      }
      return { rows: res.rows, exhausted: false }
    }
    if (res.done || res.atEnd) return { rows: [], exhausted: true, reason: res.reason || 'end' }
    // 列表是异步加载的：滚动动作本身不会立刻改变 scrollHeight，连续几轮不增长才算到底。
    if (res.sh === lastSh) stuck += 1
    else stuck = 0
    lastSh = res.sh
    if (stuck >= 4) return { rows: [], exhausted: true, reason: 'no-growth' }
    await page.waitForTimeout(waitMs)
  }
  return { rows: [], exhausted: false, reason: 'rounds' }
}

// 点标题会新开一个只读的作品详情页，URL 里带 aweme id；读完立即关掉这个弹窗。
async function readDetailId(page, key) {
  const card = page.locator(`[data-repost-card="${key}"]`).first()
  const titleEl = card.locator('[class*="info-title-text"]').first()
  const before = page.url()
  const popupPromise = page.waitForEvent('popup', { timeout: 8000 }).catch(() => null)
  await titleEl.scrollIntoViewIfNeeded({ timeout: 5000 }).catch(() => {})
  await titleEl.click({ timeout: 8000 }).catch(() => {})
  const popup = await popupPromise
  if (popup) {
    // 弹层先以 about:blank 出现、随后才导航到 work-detail；只等 domcontentloaded 会读到空 URL。
    await popup.waitForURL(DETAIL_ID, { timeout: 15_000 }).catch(() => {})
    await popup.waitForLoadState('domcontentloaded').catch(() => {})
    const url = popup.url()
    const id = (url.match(DETAIL_ID) || [''])[1] || ''
    await popup.close().catch(() => {})
    return { id, note: url }
  }
  if (page.url() !== before) {
    const url = page.url()
    const id = (url.match(DETAIL_ID) || [''])[1] || ''
    await page.goto(MANAGER, { waitUntil: 'domcontentloaded', timeout: 60_000 }).catch(() => {})
    return { id, note: `${url}（详情页在本页打开，已返回管理页）` }
  }
  return { id: '', note: '点击标题没有打开作品详情页' }
}

function emptyFrom(title, hint, info, unavailable, evidence) {
  return {
    id: hint?.id || null,
    title,
    duration: null,
    cover: '',
    collection: null,
    publishedAt: hint?.at || '',
    evidence,
    unavailable,
  }
}

export default {
  managerUrl: MANAGER,

  async readOld(page, { title, hint }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) {
      return emptyFrom(
        title,
        hint,
        info,
        ['login', 'row'],
        `未登录：finalUrl=${info.url}; title=${info.title}；台账线索=${hint?.source || '(无)'}`,
      )
    }
    const located = await locateCard(page, title)
    if (located.rows.length === 0) {
      return emptyFrom(
        title,
        hint,
        info,
        ['row'],
        `滚到底未出现标题精确匹配的作品卡（${located.reason || 'not-found'}）；finalUrl=${info.url}; title=${info.title}`,
      )
    }
    if (located.rows.length > 1) {
      return emptyFrom(
        title,
        hint,
        info,
        ['row:ambiguous'],
        `标题精确命中 ${located.rows.length} 个作品卡片，拒绝猜是哪一条`,
      )
    }
    const row = located.rows[0]
    const detail = row.hasDelete ? await readDetailId(page, row.key) : { id: '', note: '卡片内没有删除入口，未点标题' }
    const id = detail.id || hint?.id || ''
    const publishedAt = parsePublishedAt(row.text) || hint?.at || ''
    return {
      id: id || null,
      title,
      duration: parseClock(row.text),
      cover: row.cover,
      collection: row.collectionHit ? seriesName() : null,
      publishedAt,
      evidence: `row=${JSON.stringify(row.text.slice(0, 300))}; detail=${detail.note}; cover=${row.cover ? 'yes' : 'no'}`,
      unavailable: id ? [] : ['id'],
    }
  },

  async probeOld(page, { title, hint }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) {
      return { login: false, rows: [], hintId: hint?.id || '', note: `未登录（${info.url}）` }
    }
    const located = await locateCard(page, title)
    const rows = []
    for (const r of located.rows.slice(0, 2)) {
      const detail = r.hasDelete ? await readDetailId(page, r.key) : { id: '', note: '无删除入口' }
      rows.push({
        key: r.key,
        id: detail.id || '',
        text: r.text.slice(0, 260),
        cover: r.cover,
        publishedAt: parsePublishedAt(r.text),
        hasDelete: r.hasDelete,
      })
    }
    return {
      login: true,
      rows,
      exhausted: located.exhausted,
      hintId: hint?.id || '',
      note: '只读探针：已按标题定位作品卡并读取详情 id，未点击删除作品',
    }
  },

  async deleteOld(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`抖音未登录，不能删除（${info.url}）`)
    const located = await locateCard(page, title)
    if (located.rows.length !== 1) {
      throw new UnknownError(`抖音标题精确命中 ${located.rows.length} 行（${located.reason || 'ok'}），拒绝删除`)
    }
    const row = located.rows[0]
    if (!row.hasDelete) throw new UnknownError('抖音目标行内没有「删除作品」，不猜入口')
    const oldId = old?.id || ''
    if (oldId) {
      const detail = await readDetailId(page, row.key)
      if (!detail.id) throw new UnknownError(`读不到目标卡片的详情 id，无法与 old.json ${oldId} 对上，停手`)
      if (detail.id !== oldId) throw new UnknownError(`详情 id=${detail.id} 与 old.json=${oldId} 不一致，停手`)
    }
    const oldDate = String(old?.publishedAt || '').slice(0, 10)
    if (oldDate) {
      const zh = oldDate.match(/^(\d{4})-(\d{2})-(\d{2})$/)
      const want = zh ? `${zh[1]}年${Number(zh[2])}月${Number(zh[3])}日` : ''
      if (want && !row.text.includes(want)) {
        throw new UnknownError(`卡片日期与 old.json ${oldDate} 对不上，拒绝删除`)
      }
    }

    const del = await page.evaluate(
      ({ key }) => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        const vis = (e) => {
          const r = e.getBoundingClientRect()
          return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
        }
        const row = document.querySelector(`[data-repost-card="${key}"]`)
        if (!row) return { count: -1 }
        const hits = [...row.querySelectorAll('button,div,span,a')].filter(
          (e) => vis(e) && norm(e.innerText) === '删除作品',
        )
        // 外层容器与里层文字会同时命中；只留最内层，避免把同一个入口数成两个。
        const inner = hits.filter((e) => !hits.some((o) => o !== e && e.contains(o)))
        if (inner.length !== 1) return { count: inner.length }
        const k = `del-${Date.now()}`
        inner[0].setAttribute('data-repost-del', k)
        const r = inner[0].getBoundingClientRect()
        const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2)
        if (top !== inner[0] && !inner[0].contains(top)) return { count: 1, centerMiss: true }
        return { count: 1, key: k }
      },
      { key: row.key },
    )
    if (del.count !== 1) throw new UnknownError(`目标行内「删除作品」命中 ${del.count} 个，不敢点`)
    if (del.centerMiss) throw new UnknownError('「删除作品」中心点没有命中原元素，不敢点')

    // 原生 confirm 由 Playwright 自动 dismiss，DOM 里什么都看不到；先挂监听，只接受含「删除」的确认。
    let nativeMsg = ''
    const onDialog = async (d) => {
      nativeMsg = d.message()
      if (/删除/.test(d.message())) await d.accept().catch(() => {})
      else await d.dismiss().catch(() => {})
    }
    page.on('dialog', onDialog)
    try {
      await page.locator(`[data-repost-del="${del.key}"]`).click({ timeout: 10_000 })

      const scan = () => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        const vis = (e) => {
          const r = e.getBoundingClientRect()
          return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
        }
        const BTN = 'button,[role="button"],[class*="btn"],[class*="Btn"]'
        const btnOf = (root) => [...root.querySelectorAll(BTN)].filter(vis)
        const leaves = (arr) => arr.filter((e) => !arr.some((o) => o !== e && o.contains(e)))
        const rankOf = (t) => {
          if (t === '确认删除' || t === '确定删除') return 0
          if (t === '删除') return 1
          if (/删除/.test(t) && !/取消/.test(t) && !/删除作品/.test(t) && t.length <= 6) return 2
          if (t === '确定' || t === '确认') return 3
          return 9
        }
        // 抖音弹窗容器类名不含 modal/dialog，且按钮外层有带 btn 的包裹层，
        // 全页「只留最内层」会把弹窗按钮一起筛掉；改用页面上唯一的「取消」当锚点。
        const cancels = leaves(btnOf(document)).filter((e) => norm(e.innerText) === '取消')
        if (cancels.length !== 1) return { found: false, cancelCount: cancels.length }
        let node = cancels[0]
        let footer = null
        let modal = null
        for (let i = 0; i < 12 && node.parentElement && node.parentElement !== document.body; i++) {
          node = node.parentElement
          if (!footer && btnOf(node).some((b) => rankOf(norm(b.innerText)) < 9)) footer = node
          if (footer && /删除/.test(norm(node.innerText))) {
            modal = node
            break
          }
        }
        if (!footer) return { found: false, cancelCount: 1, why: 'no-footer' }
        const cands = leaves(btnOf(footer)).filter(
          (b) => norm(b.innerText) !== '取消' && rankOf(norm(b.innerText)) < 9,
        )
        const text = norm((modal || footer).innerText).slice(0, 300)
        if (!cands.length) {
          return { found: false, cancelCount: 1, why: 'no-confirm', footerText: norm(footer.innerText).slice(0, 200) }
        }
        const best = Math.min(...cands.map((b) => rankOf(norm(b.innerText))))
        const top = cands.filter((b) => rankOf(norm(b.innerText)) === best)
        if (top.length !== 1) {
          return { found: true, text, confirmCount: top.length, clickable: top.map((b) => norm(b.innerText)) }
        }
        const k = `confirm-${Date.now()}`
        top[0].setAttribute('data-repost-confirm', k)
        return { found: true, text, confirmCount: 1, key: k, label: norm(top[0].innerText) }
      }

      let confirm = { found: false }
      let confirmFrame = page.mainFrame()
      for (let i = 0; i < 12 && !confirm.found; i++) {
        await page.waitForTimeout(500)
        for (const f of page.frames()) {
          const r = await f.evaluate(scan).catch(() => null)
          if (r?.found) {
            confirm = r
            confirmFrame = f
            break
          }
        }
      }
      if (!confirm.found && nativeMsg) {
        if (!/删除/.test(nativeMsg)) throw new UnknownError(`原生对话框未见「删除」，已忽略：${nativeMsg}`)
        await page.waitForTimeout(4000)
        const afterNative = await locateCard(page, title)
        if (afterNative.rows.length > 0) throw new UnknownError('原生确认后列表里仍能看到旧作品，按删除失败对待')
        return { deleted: true, oldId, nativeConfirm: nativeMsg, evidence: '原生确认后列表回读旧卡已消失' }
      }
      if (!confirm.found) {
        const visible = await page.evaluate(() => {
          const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
          const vis = (e) => {
            const r = e.getBoundingClientRect()
            return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'
          }
          return [...document.querySelectorAll('button,[role="button"],[class*="btn"],[class*="Btn"]')]
            .filter((e) => vis(e) && ['确定', '确认', '取消', '删除', '确认删除', '删除作品'].includes(norm(e.innerText)))
            .map((e) => ({ tag: e.tagName, cls: String(e.className || '').slice(0, 60), text: norm(e.innerText) }))
        })
        throw new UnknownError(
          `点了「删除作品」但没有出现含「删除」的二次确认，停手；native=${JSON.stringify(nativeMsg)}；scan=${JSON.stringify(confirm)}；可见确认类按钮=${JSON.stringify(visible)}`,
        )
      }
      if (!confirm.key) {
        const detail = confirm.clickable?.length
          ? `；可点元素=${JSON.stringify(confirm.clickable)}`
          : `；可点元素为空；html=${confirm.html || ''}`
        throw new UnknownError(`二次确认里没有唯一的确认按钮（${confirm.confirmCount} 个），停手：${confirm.text}${detail}`)
      }
      await confirmFrame.locator(`[data-repost-confirm="${confirm.key}"]`).click({ timeout: 10_000 })
      await page.waitForTimeout(4000)

      const after = await locateCard(page, title)
      if (after.rows.length > 0) throw new UnknownError('点了确认后列表里仍能看到旧作品，按删除失败对待')
      return { deleted: true, oldId, confirmText: confirm.text, confirmLabel: confirm.label, evidence: '列表回读旧卡已消失' }
    } finally {
      page.off('dialog', onDialog)
    }
  },

  async confirmManualDeleted(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`抖音未登录，无法核对（${info.url}）`)
    const located = await locateCard(page, title)
    const still = located.rows.length > 0
    return {
      manual: true,
      verified: !still,
      oldId: old?.id || '',
      evidence: still
        ? `旧卡仍在：${located.rows.map((r) => r.text.slice(0, 80)).join(' / ')}`
        : '列表里已看不到旧卡',
    }
  },

  async verifyNew(page, { title, old }) {
    const info = await pageBody(page)
    if (looksLoggedOut(info)) throw new UnknownError(`抖音未登录，无法回读新稿（${info.url}）`)
    const located = await locateCard(page, title)
    if (located.rows.length !== 1) throw new UnknownError(`抖音回读到 ${located.rows.length} 张标题匹配卡片，拒绝判定`)
    const row = located.rows[0]
    const detail = await readDetailId(page, row.key)
    if (!detail.id) throw new UnknownError('抖音回读没有作品 id')
    if (old?.id && detail.id === old.id) throw new UnknownError(`抖音回读仍是旧作品 ${detail.id}`)
    return {
      id: detail.id,
      title,
      duration: parseClock(row.text),
      cover: row.cover,
      collection: row.collectionHit ? seriesName() : null,
      publishedAt: parsePublishedAt(row.text),
      evidence: `row=${JSON.stringify(row.text.slice(0, 300))}; detail=${detail.note}`,
      unavailable: [],
      oldId: old?.id || null,
    }
  },
}
