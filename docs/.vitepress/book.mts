// Single source for the site's identity, navigation and anchors.
// Everything here is derived from docs/manifest.json (generated from
// book/data/toc.tsv); nothing is hand-listed, so a new chapter shows up in the
// nav, sidebar and sitemap as soon as the manifest is regenerated.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const BASE = '/STM32/'
export const SITE_ORIGIN = 'https://zhuguang-zfg.github.io'
export const SITE_URL = `${SITE_ORIGIN}${BASE}`

const here = path.dirname(fileURLToPath(import.meta.url))
export const docsRoot = path.resolve(here, '..')

export interface ChapterEntry {
  id: string
  title: string
  file: string
  status?: string
  platforms?: string[]
}

export interface PartEntry {
  id: string
  title: string
  goal?: string
  chapters: ChapterEntry[]
}

export interface BookManifest {
  title: string
  subtitle?: string
  version?: string
  language?: string
  parts: PartEntry[]
  appendices?: ChapterEntry[]
}

export const manifest: BookManifest = JSON.parse(
  fs.readFileSync(path.join(docsRoot, 'manifest.json'), 'utf8'),
)

/** Chapter file (`v1-drivers/09-gpio.md`) → VitePress route (`/v1-drivers/09-gpio`). */
export function chapterLink(file: string): string {
  return `/${file.replace(/\.md$/, '')}`
}

export function buildSidebar() {
  const groups = manifest.parts.map((part) => ({
    text: part.title,
    collapsed: false,
    items: part.chapters.map((chapter) => ({
      text: chapter.title,
      link: chapterLink(chapter.file),
    })),
  }))
  const appendices = manifest.appendices ?? []
  if (appendices.length) {
    groups.push({
      text: '附录',
      collapsed: false,
      items: appendices.map((entry) => ({
        text: entry.title,
        link: chapterLink(entry.file),
      })),
    })
  }
  return groups
}

export function buildNav() {
  const parts = manifest.parts
    .filter((part) => part.chapters.length)
    .map((part) => ({
      text: part.title,
      link: chapterLink(part.chapters[0].file),
    }))
  const nav: Array<Record<string, unknown>> = [
    { text: '首页', link: '/' },
    { text: '卷册', items: parts },
  ]
  const appendices = manifest.appendices ?? []
  if (appendices.length) {
    nav.push({ text: '附录', link: chapterLink(appendices[0].file) })
  }
  nav.push({ text: 'GitHub', link: 'https://github.com/zhuguang-ZFG/STM32' })
  return nav
}

/**
 * Same slug rule as book/checks.py:cjk_slugify — anchors are validated against
 * that function, so the site must not invent its own.
 *   re.sub(r"[^\w\s-]", "", value).strip().lower(); re.sub(r"[\s-]+", "-", value)
 */
export function slugify(value: string): string {
  const cleaned = value
    .replace(/[^\p{L}\p{N}_\s-]/gu, '')
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '-')
  return cleaned || 'section'
}

/** MiniSearch tokenizer that keeps CJK searchable (one token per Han character). */
export function cjkTokenize(text: string): string[] {
  const parts = text.split(/[\s\-_/.,;:!?()[\]{}"'`~@#$%^&*+=|\\<>]+/u)
  const tokens: string[] = []
  for (const part of parts) {
    if (!part) continue
    if (/[\u3400-\u9fff\uf900-\ufaff]/.test(part)) {
      tokens.push(...(part.match(/[\u3400-\u9fff\uf900-\ufaff]|[a-zA-Z0-9_]+/gu) ?? []))
    } else {
      tokens.push(part)
    }
  }
  return tokens
}
