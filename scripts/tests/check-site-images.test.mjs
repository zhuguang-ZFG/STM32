// 图片属性门：懒加载与异步解码分属 Markdown 规则与 Vue 组件两条产出路径，
// 只有构建产物能证明两条都覆盖到。
import test from 'node:test'
import assert from 'node:assert/strict'

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
