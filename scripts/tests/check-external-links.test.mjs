import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import {
  allowlistHit,
  checkExternalLinks,
  extractExternalUrls,
  loadAllowlist,
} from '../check-external-links.mjs'

test('extractExternalUrls keeps off-site links and drops own host', () => {
  const html = `
    <a href="https://example.org/a#frag">a</a>
    <a href="https://zhuguang-zfg.github.io/STM32/x.html">own</a>
    <a href="/local/path.html">rel</a>
    <a href="mailto:x@example.org">mail</a>
  `
  const urls = [...extractExternalUrls(html)]
  assert.deepEqual(urls, ['https://example.org/a'])
})

async function withAllowlist(content, fn) {
  const dir = await mkdtemp(join(tmpdir(), 'link-allow-'))
  try {
    const file = join(dir, 'allowlist.json')
    await writeFile(file, JSON.stringify(content), 'utf8')
    return await fn(file)
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}

test('allowlist requires a reason for every entry', async () => {
  await withAllowlist({ entries: [{ match: '^https://a\\.org/' }] }, async (file) => {
    assert.throws(() => loadAllowlist(file), /needs a reason/)
  })
})

test('allowlist refuses to whitelist 404 or 410', async () => {
  await withAllowlist(
    { entries: [{ match: '^https://a\\.org/', reason: 'x', allowStatuses: [404] }] },
    async (file) => {
      assert.throws(() => loadAllowlist(file), /404\/410/)
    },
  )
})

test('allowlistHit matches by regex', async () => {
  await withAllowlist(
    { entries: [{ match: '^https://a\\.org/x$', reason: 'x', allowStatuses: [403] }] },
    async (file) => {
      const allowlist = loadAllowlist(file)
      assert.equal(allowlistHit('https://a.org/x', allowlist)?.reason, 'x')
      assert.equal(allowlistHit('https://a.org/y', allowlist), null)
    },
  )
})

/**
 * 用假的 fetch 复现探活语义：
 * - 条目声称豁免传输失败，但站点真的返回 404 时仍必须 FAIL；
 * - 条目豁免 403 时，403 只记 SKIP；
 * - 真正拿不到响应（fetch 抛错）才走 allowTransportError。
 */
async function runChecker({ status, throwOnFetch, seq, entries, retries = 0 }) {
  const root = await mkdtemp(join(tmpdir(), 'link-dist-'))
  const originalFetch = globalThis.fetch
  const allowlistFile = await mkdtemp(join(tmpdir(), 'link-allow-'))
  try {
    await writeFile(
      join(root, 'page.html'),
      '<a href="https://a.org/x">x</a>',
      'utf8',
    )
    await writeFile(
      join(allowlistFile, 'allowlist.json'),
      JSON.stringify({ entries }),
      'utf8',
    )
    const steps = seq ?? [{ status, throw: throwOnFetch }]
    let attempt = 0
    globalThis.fetch = async () => {
      const step = steps[Math.min(attempt, steps.length - 1)]
      attempt += 1
      if (step.throw) throw new Error('getaddrinfo ENOTFOUND')
      return new Response(null, { status: step.status, headers: {} })
    }
    const results = await checkExternalLinks({
      root,
      allowlist: loadAllowlist(join(allowlistFile, 'allowlist.json')),
      concurrency: 1,
      timeout: 1000,
      retries,
      log: () => {},
    })
    return results
  } finally {
    globalThis.fetch = originalFetch
    await rm(root, { recursive: true, force: true })
    await rm(allowlistFile, { recursive: true, force: true })
  }
}

test('transport allowance never hides a real 404', async () => {
  const results = await runChecker({
    status: 404,
    entries: [{ match: '^https://a\\.org/x$', reason: 'dns blocked', allowTransportError: true }],
  })
  assert.equal(results.skipped.length, 0)
  assert.equal(results.failures.length, 1)
  assert.equal(results.failures[0].status, 404)
})

test('transport allowance covers only fetch exceptions', async () => {
  const results = await runChecker({
    throwOnFetch: true,
    entries: [{ match: '^https://a\\.org/x$', reason: 'dns blocked', allowTransportError: true }],
  })
  assert.equal(results.failures.length, 0)
  assert.equal(results.skipped.length, 1)
  assert.equal(results.skipped[0].status, 0)
})

test('a 5xx followed by a transport error still fails as HTTP', async () => {
  // 先 500、重试时断连：不能把已观测到的状态改写成“传输失败”，
  // 否则 allowTransportError 会把它错误豁免。
  const results = await runChecker({
    seq: [{ status: 500 }, { throw: true }],
    retries: 1,
    entries: [{ match: '^https://a\\.org/x$', reason: 'dns flaky', allowTransportError: true }],
  })
  assert.equal(results.skipped.length, 0)
  assert.equal(results.failures[0].status, 500)
})

test('status allowance covers exactly the listed status', async () => {
  const allowed = await runChecker({
    status: 403,
    entries: [{ match: '^https://a\\.org/x$', reason: 'bot block', allowStatuses: [403] }],
  })
  assert.equal(allowed.failures.length, 0)
  assert.equal(allowed.skipped[0].status, 403)

  const denied = await runChecker({
    status: 500,
    entries: [{ match: '^https://a\\.org/x$', reason: 'bot block', allowStatuses: [403] }],
  })
  assert.equal(denied.skipped.length, 0)
  assert.equal(denied.failures[0].status, 500)
})
