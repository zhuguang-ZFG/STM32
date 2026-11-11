const norm = (s) => String(s || '').replace(/\s+/g, '').trim()

export function matchPublished(cards, { title, noteId, since }) {
  if (noteId) return cards.filter((c) => String(c.id) === String(noteId))
  if (!since) throw new Error('xhs 回读必须给 noteId 或 since：只按标题会把旧笔记认成新笔记')
  const want = norm(title)
  if (!want) throw new Error('xhs 回读的标题为空：不拿 since 去捞任意一条')
  const t = Date.parse(since)
  if (Number.isNaN(t)) throw new Error(`since 不是合法时间：${since}`)
  const hits = cards.filter((c) => norm(c.title).includes(want) && Date.parse(c.createTime) >= t)
  if (hits.length > 1) throw new Error(`标题命中 ${hits.length} 条，无法判定新笔记：${hits.map((h) => h.id).join(',')}`)
  return hits
}
