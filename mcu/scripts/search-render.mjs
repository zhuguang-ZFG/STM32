// 搜索正文、标题、行内标识符和图注；完整源码已可在章节内查阅，
// 不重复索引大量导入代码与 SVG 序列化数据。
export function renderSearch(src, env, md) {
  const html = md.render(src, env)
  if (env.frontmatter?.search === false) return ''
  return html
    // 章首题花是构建期注入的原生 SVG（与 anim 的转义属性形态不同），
    // 不剥会把 <text> 标签连内容一起索引进正文（实测 CCR+CNT 熔成 ccrcnt）。
    .replace(/<div class="chapter-art">[\s\S]*?<\/div>/gi, '')
    .replace(/<pre\b[^>]*>[\s\S]*?<\/pre>/gi, '')
}
