import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { parse } from 'yaml'

const read = (p) => parse(fs.readFileSync(p, 'utf8'))
const quality = read('.github/workflows/quality.yml')
const deploy = read('.github/workflows/deploy.yml')
const book = read('.github/workflows/book.yml')
const links = read('.github/workflows/links.yml')

test('deployment depends on the complete reusable gate for this commit', () => {
  assert.equal(deploy.jobs.quality.uses, './.github/workflows/quality.yml')
  assert.equal(deploy.jobs.deploy.needs, 'quality')
  assert.match(deploy.jobs.deploy.if, /needs\.quality\.result == 'success'/)
  assert.match(deploy.jobs.deploy.if, /refs\/heads\/main/)
  assert.ok('workflow_call' in quality.on)
  assert.ok('pull_request' in quality.on)
  assert.deepEqual(Object.keys(quality.jobs).sort(), ['arm-host', 'checks', 'esp32', 'lint'])
  for (const job of Object.values(quality.jobs)) {
    assert.notEqual(job['continue-on-error'], true)
    for (const step of job.steps || []) assert.notEqual(step['continue-on-error'], true)
  }
  assert.equal(quality.permissions.contents, 'read')
  assert.equal(quality.permissions.pages, undefined)
  assert.equal(quality.jobs.esp32.container, 'espressif/idf:v5.5.2')
})

test('runner 钉在 ubuntu-24.04：浮动 latest 会让字体度量与工具链版本悄悄漂移', () => {
  for (const [name, wf] of Object.entries({ quality, deploy, book, links })) {
    // 复用工作流的调用 job 没有 runs-on（它跑在被调用的 workflow 里），跳过
    const runs = Object.values(wf.jobs)
      .filter((j) => !j.uses)
      .map((j) => j['runs-on'])
    assert.ok(runs.length > 0, `${name}.yml 应当至少有一个自跑 job`)
    assert.deepEqual(runs, runs.map(() => 'ubuntu-24.04'), `${name}.yml 必须钉住 runner`)
  }
})

test('Python 静态检查作为独立 job 存在，并钉住版本', () => {
  const steps = quality.jobs.lint.steps
  const ruff = steps.find((s) => String(s.uses || '').includes('ruff-action'))
  assert.ok(ruff, 'lint job 必须调用 ruff-action')
  assert.equal(ruff.with.version, '0.15.21', 'ruff 版本要钉住，否则规则集会在上游更新时变脸')
  assert.equal(ruff.with.args, 'check')
})

test('整书产物要被回收验证：构建之后必须跑 PDF 契约门与下载打包', () => {
  const checks = quality.jobs.checks.steps
  const runs = checks.map((s) => String(s.run || ''))
  const pdf = runs.findIndex((r) => r.includes('build_html.py --pdf'))
  const contract = runs.findIndex((r) => r.includes('check_pdf.py'))
  const pack = runs.findIndex((r) => r.includes('publish_downloads.py'))
  assert.ok(pdf >= 0 && contract > pdf, 'PDF 契约门必须在产物生成之后')
  assert.ok(pack > pdf, '下载打包必须在产物生成之后')

  const bookRuns = book.jobs.book.steps.map((s) => String(s.run || ''))
  const bookPdf = bookRuns.findIndex((r) => r.includes('build_html.py --pdf'))
  assert.ok(bookRuns.findIndex((r) => r.includes('check_pdf.py')) > bookPdf)
  assert.ok(bookRuns.findIndex((r) => r.includes('publish_downloads.py')) > bookPdf)
})

test('部署前对 artifact 再对一次账，且在 upload-pages-artifact 之前', () => {
  const steps = deploy.jobs.deploy.steps
  const at = (pred) => steps.findIndex(pred)
  const checkout = at((s) => String(s.uses || '').includes('actions/checkout'))
  const download = at((s) => String(s.uses || '').includes('download-artifact'))
  const anchor = at((s) => String(s.run || '').includes('pages-check.mjs --dist site'))
  const search = at((s) => String(s.run || '').includes('search-check.mjs --dist site'))
  const upload = at((s) => String(s.uses || '').includes('upload-pages-artifact'))
  const install = at((s) => String(s.run || '').trim() === 'npm ci')
  assert.ok(install >= 0 && install < anchor, '先用 npm ci 装到 minisearch 等依赖')
  assert.ok(anchor >= 0 && search >= 0, '两个 dist 侧门都要在部署流程里')
  assert.ok(anchor < upload && search < upload, '检查必须在真正上传产物之前')
  // checkout 默认 clean=true，会 reset/clean 工作区：它排在 download-artifact 之后
  // 就会把刚下载的 site/ 当未跟踪文件清掉，后面的 --dist site 变成查空目录。
  assert.ok(checkout >= 0 && download > checkout, 'checkout 必须排在 download-artifact 之前，否则 site/ 会被清掉')
})

test('外链巡检：两轮制 + 月度复查，且只允许第 1 轮 continue-on-error', () => {
  const steps = links.jobs.lychee.steps
  const rounds = steps.filter((s) => String(s.uses || '').includes('lychee-action'))
  assert.equal(rounds.length, 2, '两轮制：第一轮探测、第二轮判定')
  assert.equal(rounds[0].id, 'round1')
  assert.equal(rounds[0].with.fail, true)
  assert.equal(rounds[1].with.fail, true)
  assert.match(String(rounds[1].if || ''), /round1\.outcome == 'failure'/)
  for (const step of steps) {
    if (step.id === 'round1') {
      assert.equal(step['continue-on-error'], true, '只有第 1 轮允许 continue-on-error')
    } else {
      assert.notEqual(step['continue-on-error'], true)
    }
  }
  assert.ok(links.on.schedule, '放行清单需要月度复查，否则会变成化石')
  assert.deepEqual(links.permissions, { contents: 'read' })
})