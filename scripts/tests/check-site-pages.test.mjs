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

test('checkNotFoundIndexing flags a missing or indexable 404', async () => {
  const { mkdtemp, writeFile, rm } = await import('node:fs/promises')
  const { tmpdir } = await import('node:os')
  const { join } = await import('node:path')
  const { checkNotFoundIndexing } = await import('../check-site-pages.mjs')
  const dist = await mkdtemp(join(tmpdir(), 'indexing-'))
  try {
    // 没有 404.html：报缺文件
    assert.equal(checkNotFoundIndexing(dist).ok, false)
    assert.match(checkNotFoundIndexing(dist).problems[0], /不存在/)

    // VitePress 默认形态（可索引）：必须失败
    await writeFile(join(dist, '404.html'), '<html><head></head></html>')
    assert.equal(checkNotFoundIndexing(dist).ok, false)
    assert.match(checkNotFoundIndexing(dist).problems[0], /noindex/)

    // transformHead 产出的精确标签才通过
    await writeFile(join(dist, '404.html'), '<html><head><meta name="robots" content="noindex"></head></html>')
    assert.deepEqual(checkNotFoundIndexing(dist), { ok: true, problems: [] })
  } finally {
    await rm(dist, { recursive: true, force: true })
  }
})

test('checkImages flags images without lazy loading or async decoding', async () => {
  const { mkdtemp, mkdir, writeFile, rm } = await import('node:fs/promises')
  const { tmpdir } = await import('node:os')
  const { join } = await import('node:path')
  const { checkImages } = await import('../check-site-images.mjs')
  const dist = await mkdtemp(join(tmpdir(), 'images-'))
  try {
    await mkdir(join(dist, 'v0'), { recursive: true })
    await writeFile(
      join(dist, 'v0/01-a.html'),
      '<img src="a.png"><img src="b.png" loading="lazy" decoding="async"><img src="c.png" loading="lazy">',
    )
    const result = checkImages(dist)
    assert.equal(result.total, 3)
    assert.deepEqual(result.notLazy.map((i) => i.tag), ['<img src="a.png">'])
    assert.deepEqual(result.notAsync.map((i) => i.tag), ['<img src="a.png">', '<img src="c.png" loading="lazy">'])
    assert.equal(result.ok, false)

    // 全部补齐后通过；嵌套目录同样计入
    await mkdir(join(dist, 'appendix'), { recursive: true })
    await writeFile(join(dist, 'v0/01-a.html'), '<img src="a.png" loading="lazy" decoding="async">')
    await writeFile(join(dist, 'appendix/A.html'), '<img src="d.png" loading="lazy" decoding="async">')
    assert.deepEqual(checkImages(dist), { total: 2, notLazy: [], notAsync: [], ok: true })

    // 旧链存根目录不参与统计
    await mkdir(join(dist, 'mcu'), { recursive: true })
    await writeFile(join(dist, 'mcu/legacy.html'), '<img src="old.png">')
    assert.equal(checkImages(dist).total, 2)
  } finally {
    await rm(dist, { recursive: true, force: true })
  }
})
