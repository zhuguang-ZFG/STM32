import { createHash } from 'node:crypto'
import { checkPageHtml } from '../seo-check.mjs'
import { auditPage } from '../a11y-check.mjs'

export const sha = value => createHash('sha256').update(value).digest('hex')

export function checkGuide({ sourceHash, generatorHash, manifest, html }) {
  const errors = []
  if (manifest.sourceHash !== sourceHash || manifest.generatorHash !== generatorHash) errors.push('Book guide is stale; run npm run guide:generate')
  if (sha(html) !== manifest.htmlHash) errors.push('Book guide HTML differs from recorded output')
  errors.push(...checkPageHtml(html), ...auditPage(html))
  for (const [, href] of html.matchAll(/href="([^"]+)"/g)) {
    if (!/^(?:https?:|mailto:|#)/.test(href) && /\.md(?:#|$)/.test(href)) errors.push('unresolved Markdown link')
  }
  if (/src="https?:/.test(html) || /<link\b[^>]*href="https:\/\/fonts/.test(html)) errors.push('external image/font dependency')
  if (/contenteditable[^\n]*'true'/.test(html) || /contenteditable="(?:true)?"/.test(html)) errors.push('published content is editable')
  return errors
}
