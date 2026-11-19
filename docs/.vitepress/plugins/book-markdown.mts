// Markdown extensions that keep the VitePress output equal to the site the
// book was designed against (captioned figures, scrollable register tables,
// image dimensions, stick-scene slots, base-prefixed raw HTML).
//
// The print/EPUB pipeline still renders Markdown with book/build_html.py; that
// module owns the same rules in Python. Content stays in one place: the
// Markdown files plus docs/.vitepress/data/*.json.
import fs from 'node:fs'
import path from 'node:path'

const SCENE_RE = /^\s*<!--\s*stick-scene:\s*([a-z0-9-]+)\s*-->\s*$/
const IMG_TAG_RE = /<img\b([^>]*)>/i

/** Decode off the main thread and defer offscreen bitmaps; never double-add. */
function addLazyAttrs(tag: string, attrs: string): string {
  if (/loading=/.test(attrs)) return tag
  const plus = `${/decoding=/.test(attrs) ? '' : ' decoding="async"'}`
  return `<img loading="lazy"${plus}${attrs}>`
}

function attrValue(attrs: string, name: string): string | null {
  const match = attrs.match(new RegExp(`\\b${name}="([^"]*)"`, 'i'))
  return match ? match[1] : null
}

/**
 * Raw-HTML images: 正文只写 width 时按原图比例补高度，再补懒加载属性。
 * 尺寸读不到就原样返回（宁可没尺寸，也不要写错比例）。
 */
function normalizeRawImg(tag: string, attrs: string, docsRoot: string): string {
  let width = attrValue(attrs, 'width')
  let height = attrValue(attrs, 'height')
  const src = attrValue(attrs, 'src')
  if ((!width || !height) && src) {
    const size = imageSize(src, docsRoot)
    if (size) {
      if (!width && !height) {
        width = String(size[0])
        height = String(size[1])
      } else if (width) {
        height = String(Math.round((size[1] * Number.parseFloat(width)) / size[0]))
      } else {
        width = String(Math.round((size[0] * Number.parseFloat(height as string)) / size[1]))
      }
    }
  }
  if (width && height) {
    const rest = attrs.replace(/\s(?:width|height)="[^"]*"/g, '')
    tag = `<img width="${width}" height="${height}"${rest}>`
  }
  return addLazyAttrs(tag, tag.replace(/^<img\b/i, '').replace(/>$/, ''))
}

export interface BookMarkdownOptions {
  base: string
  docsRoot: string
  scenes: Record<string, { label: string; caption: string; fallback: string }>
}

function basePath(base: string, url: string): string {
  if (!url.startsWith('/') || url.startsWith('//')) return url
  return `${base.replace(/\/$/, '')}${url}`
}

function svgSize(text: string): [number, number] | null {
  const root = text.match(/<svg\b([^>]*)>/i)
  if (!root) return null
  const attrs = root[1]
  const width = attrs.match(/\bwidth="([0-9.]+)(?:px)?"/i)
  const height = attrs.match(/\bheight="([0-9.]+)(?:px)?"/i)
  if (width && height) return [Math.round(Number(width[1])), Math.round(Number(height[1]))]
  const viewBox = attrs.match(/\bviewBox="([^"]+)"/i)
  if (!viewBox) return null
  const parts = viewBox[1].trim().split(/[\s,]+/).map(Number)
  if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
    return [Math.round(parts[2]), Math.round(parts[3])]
  }
  return null
}

function pngSize(data: Buffer): [number, number] | null {
  if (data.length < 24 || data.readUInt32BE(0) !== 0x89504e47) return null
  return [data.readUInt32BE(16), data.readUInt32BE(20)]
}

function jpegSize(data: Buffer): [number, number] | null {
  if (data.length < 4 || data[0] !== 0xff || data[1] !== 0xd8) return null
  let offset = 2
  while (offset + 9 < data.length) {
    if (data[offset] !== 0xff) {
      offset += 1
      continue
    }
    const marker = data[offset + 1]
    if (marker === 0xd8 || marker === 0xd9) {
      offset += 2
      continue
    }
    const length = data.readUInt16BE(offset + 2)
    if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
      return [data.readUInt16BE(offset + 7), data.readUInt16BE(offset + 5)]
    }
    offset += 2 + length
  }
  return null
}

function imageSize(src: string, docsRoot: string): [number, number] | null {
  if (!src.startsWith('/') || src.startsWith('//')) return null
  const file = path.join(docsRoot, 'public', src)
  try {
    const stat = fs.statSync(file)
    if (!stat.isFile() || stat.size > 64 * 1024 * 1024) return null
    const ext = path.extname(file).toLowerCase()
    if (ext === '.svg') return svgSize(fs.readFileSync(file, 'utf8'))
    const head = Buffer.alloc(Math.min(stat.size, 256 * 1024))
    const fd = fs.openSync(file, 'r')
    try {
      fs.readSync(fd, head, 0, head.length, 0)
    } finally {
      fs.closeSync(fd)
    }
    if (ext === '.png') return pngSize(head)
    if (ext === '.jpg' || ext === '.jpeg') return jpegSize(head)
  } catch {
    return null
  }
  return null
}

export function bookMarkdown(md: any, options: BookMarkdownOptions): void {
  const { base, docsRoot, scenes } = options
  const sceneIds = new Set(Object.keys(scenes))

  // 1. `<!-- stick-scene: id -->` → <StickScene scene="id" /> (Vue component).
  md.core.ruler.push('book_stick_scenes', (state: any) => {
    for (const token of state.tokens) {
      if (token.type !== 'html_block') continue
      const match = token.content.match(SCENE_RE)
      if (!match) continue
      if (!sceneIds.has(match[1])) {
        throw new Error(`unknown stick-scene id: ${match[1]} (${state.env?.relativePath ?? '?'})`)
      }
      token.content = `<StickScene scene="${match[1]}" />`
    }
  })

  // 2. A paragraph holding exactly one captioned image becomes a <figure>.
  md.core.ruler.push('book_figures', (state: any) => {
    const tokens = state.tokens
    for (let i = 0; i + 2 < tokens.length; i += 1) {
      if (tokens[i].type !== 'paragraph_open') continue
      if (tokens[i + 1].type !== 'inline' || tokens[i + 2].type !== 'paragraph_close') continue
      const children = tokens[i + 1].children ?? []
      if (children.length !== 1 || children[0].type !== 'image') continue
      const alt = String(children[0].content ?? '').trim()
      const src = children[0].attrGet('src') ?? ''
      if (!alt || !src || src.startsWith('data:')) continue
      const meta = { bookFigure: true, alt, src }
      tokens[i].meta = meta
      tokens[i + 2].meta = meta
    }
  })

  const paragraphOpen = md.renderer.rules.paragraph_open
  md.renderer.rules.paragraph_open = (tokens: any[], idx: number, opts: any, env: any, self: any) => {
    const meta = tokens[idx].meta
    if (meta?.bookFigure) {
      const href = md.utils.escapeHtml(basePath(base, meta.src))
      return `<figure class="book-figure"><a class="figure-zoom" href="${href}" target="_blank" rel="noopener">`
    }
    return paragraphOpen ? paragraphOpen(tokens, idx, opts, env, self) : '<p>'
  }

  const paragraphClose = md.renderer.rules.paragraph_close
  md.renderer.rules.paragraph_close = (tokens: any[], idx: number, opts: any, env: any, self: any) => {
    const meta = tokens[idx].meta
    if (meta?.bookFigure) {
      return `</a><figcaption>${md.utils.escapeHtml(meta.alt)}</figcaption></figure>`
    }
    return paragraphClose ? paragraphClose(tokens, idx, opts, env, self) : '</p>'
  }

  // 3. Wide register tables scroll instead of pushing the page sideways.
  md.renderer.rules.table_open = () => '<div class="table-scroll"><table>'
  md.renderer.rules.table_close = () => '</table></div>'

  // 4. Reserve layout space for images before they load, and keep offscreen
  //    bitmaps (0.5–1 MB PNGs here) out of the initial fetch burst.
  const image = md.renderer.rules.image
  if (image) {
    md.renderer.rules.image = (tokens: any[], idx: number, opts: any, env: any, self: any) => {
      const token = tokens[idx]
      let width = token.attrGet('width')
      let height = token.attrGet('height')
      if (!width || !height) {
        // 正文常只写 width（`<img width="760">`）：按原图比例补出缺失的一维，
        // 否则窄屏上仍会跳版。
        const size = imageSize(token.attrGet('src') ?? '', docsRoot)
        if (size) {
          if (!width && !height) {
            width = String(size[0])
            height = String(size[1])
          } else if (width) {
            height = String(Math.round((size[1] * Number.parseFloat(width)) / size[0]))
          } else {
            width = String(Math.round((size[0] * Number.parseFloat(height)) / size[1]))
          }
        }
      }
      let out: string = image(tokens, idx, opts, env, self)
      if (width && height) {
        out = out.replace(IMG_TAG_RE, (tag: string, attrs: string) =>
          `<img width="${width}" height="${height}"${attrs.replace(/\s(?:width|height)="[^"]*"/g, '')}>`,
        )
      }
      return out.replace(IMG_TAG_RE, (tag: string, attrs: string) => addLazyAttrs(tag, attrs))
    }
  }

  // 4b. Raw-HTML images (appendix C, generated pages) bypass the rule above.
  for (const type of ['html_block', 'html_inline']) {
    const inner = md.renderer.rules[type]
    md.renderer.rules[type] = (tokens: any[], idx: number, opts: any, env: any, self: any) => {
      const content: string = inner
        ? inner(tokens, idx, opts, env, self)
        : tokens[idx].content
      return content.replace(new RegExp(`<img\\b([^>]*)>`, 'gi'), (tag: string, attrs: string) =>
        normalizeRawImg(tag, attrs, docsRoot),
      )
    }
  }
}
