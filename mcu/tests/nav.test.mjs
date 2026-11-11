import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { extractLinks, collectPages, findUnreachable } from '../scripts/nav-check.mjs'

test('extractLinks strips anchors/query/trailing slash and skips external', () => {
  const links = extractLinks(`
    nav: [{ link: '/guide/' }, { link: '/guide/#全景路线图' }],
    social: { link: 'https://github.com/x/y' },
    edit: { link: '/animations' },
  `)
  assert.deepEqual([...links].sort(), ['/animations', '/guide'])
})

test('collectPages normalizes index pages and skips .vitepress', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nav-'))
  fs.mkdirSync(path.join(dir, 'a', 'b'), { recursive: true })
  fs.mkdirSync(path.join(dir, '.vitepress'), { recursive: true })
  fs.writeFileSync(path.join(dir, 'index.md'), '# home')
  fs.writeFileSync(path.join(dir, 'a', 'index.md'), '# a')
  fs.writeFileSync(path.join(dir, 'a', 'b', 'c.md'), '# c')
  fs.writeFileSync(path.join(dir, '.vitepress', 'config.mts'), '')
  try {
    assert.deepEqual(collectPages(dir).sort(), ['/', '/a', '/a/b/c'])
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
})

/** 造一个最小站点：index + a/b.md，sidebar 只登记 links 里给的链接。 */
function fixture(links) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nav-'))
  fs.mkdirSync(path.join(dir, '.vitepress'), { recursive: true })
  fs.mkdirSync(path.join(dir, 'a'), { recursive: true })
  fs.writeFileSync(path.join(dir, 'index.md'), '# home')
  fs.writeFileSync(path.join(dir, 'a', 'b.md'), '# b')
  fs.writeFileSync(
    path.join(dir, '.vitepress', 'config.mts'),
    `export default { themeConfig: { sidebar: { '/a/': [{ items: [${links}] }] } } }`,
  )
  return dir
}

const cfgOf = (dir) => path.join(dir, '.vitepress', 'config.mts')

test('a chapter registered in the sidebar is reachable', () => {
  const dir = fixture(`{ link: '/a/b' }`)
  try {
    const { missing, all } = findUnreachable({ docsDir: dir, configFile: cfgOf(dir) })
    assert.deepEqual(missing, [])
    assert.equal(all.length, 2)
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
})

test('a chapter missing from the sidebar is flagged (the GD32 regression)', () => {
  const dir = fixture(`{ link: '/somewhere/else' }`)
  try {
    const { missing } = findUnreachable({ docsDir: dir, configFile: cfgOf(dir) })
    assert.deepEqual(missing, ['/a/b'])
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
})

test('a trailing-slash sidebar link still counts as reachable', () => {
  const dir = fixture(`{ link: '/a/b/' }`)
  try {
    const { missing } = findUnreachable({ docsDir: dir, configFile: cfgOf(dir) })
    assert.deepEqual(missing, [])
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
})
