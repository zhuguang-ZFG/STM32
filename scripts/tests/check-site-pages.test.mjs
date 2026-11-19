import test from 'node:test'
import assert from 'node:assert/strict'

import { actualPages, comparePages, expectedPages } from '../check-site-pages.mjs'

const manifest = {
  parts: [
    { chapters: [{ file: 'v0/01-a.md' }, { file: 'v0/02-b.md' }] },
  ],
  appendices: [{ file: 'appendix/A-deep.md' }],
}

test('expectedPages covers index, chapters and appendices', () => {
  assert.deepEqual([...expectedPages(manifest)].sort(), [
    'appendix/A-deep.html',
    'index.html',
    'v0/01-a.html',
    'v0/02-b.html',
  ])
})

test('comparePages reports renames as one miss plus one extra', () => {
  const result = comparePages({
    expected: new Set(['index.html', 'v0/01-a.html']),
    actual: new Set(['index.html', 'v0/01-renamed.html']),
  })
  assert.equal(result.ok, false)
  assert.deepEqual(result.missing, ['v0/01-a.html'])
  assert.deepEqual(result.extra, ['v0/01-renamed.html'])
})

test('comparePages accepts identical sets', () => {
  const same = new Set(['index.html', 'v0/01-a.html'])
  assert.equal(comparePages({ expected: same, actual: new Set(same) }).ok, true)
})

test('actualPages includes nested pages of a real tree', async () => {
  const { mkdtemp, mkdir, writeFile, rm } = await import('node:fs/promises')
  const { tmpdir } = await import('node:os')
  const { join } = await import('node:path')
  const dist = await mkdtemp(join(tmpdir(), 'site-pages-'))
  try {
    await mkdir(join(dist, 'v0'), { recursive: true })
    await writeFile(join(dist, 'index.html'), '<html></html>')
    await writeFile(join(dist, 'v0/01-a.html'), '<html></html>')
    await writeFile(join(dist, '404.html'), '<html></html>')
    assert.deepEqual([...actualPages(dist)].sort(), ['index.html', 'v0/01-a.html'])
  } finally {
    await rm(dist, { recursive: true, force: true })
  }
})

test('checkCrawlability requires 404 noindex and a sitemap robots.txt', async () => {
  const { mkdtemp, writeFile, rm } = await import('node:fs/promises')
  const { tmpdir } = await import('node:os')
  const { join } = await import('node:path')
  const { checkCrawlability } = await import('../check-site-pages.mjs')
  const dist = await mkdtemp(join(tmpdir(), 'crawl-'))
  try {
    // 缺 404 与 robots.txt：两条都要报出来，不能只报第一条就短路
    assert.equal(checkCrawlability(dist).ok, false)
    assert.equal(checkCrawlability(dist).problems.length, 2)

    // 404 可索引（VitePress 默认形态）：必须失败
    await writeFile(join(dist, '404.html'), '<html><head></head></html>')
    await writeFile(join(dist, 'robots.txt'), 'User-agent: *\nAllow: /\nSitemap: https://x/STM32/sitemap.xml\n')
    const indexable = checkCrawlability(dist)
    assert.equal(indexable.ok, false)
    assert.match(indexable.problems[0], /404\.html/)

    // 两处都补齐后才通过
    await writeFile(join(dist, '404.html'), '<html><head><meta name="robots" content="noindex"></head></html>')
    assert.deepEqual(checkCrawlability(dist), { ok: true, problems: [] })

    // 相对 Sitemap 行同样算失败：爬虫要求绝对 URL
    await writeFile(join(dist, 'robots.txt'), 'User-agent: *\nSitemap: sitemap.xml\n')
    assert.equal(checkCrawlability(dist).ok, false)
  } finally {
    await rm(dist, { recursive: true, force: true })
  }
})
