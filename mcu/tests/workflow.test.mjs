import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { parse } from 'yaml'

const read = (p) => parse(fs.readFileSync(p, 'utf8'))
// 合并后 MCU 的 workflows 集中在仓库根（mcu-*.yml），测试从 mcu/ 内经 ../ 读取。
const quality = read('../.github/workflows/mcu-quality.yml')
const deploy = read('../.github/workflows/mcu-deploy.yml')
const book = read('../.github/workflows/mcu-book.yml')
const links = read('../.github/workflows/mcu-links.yml')

test('deployment depends on the complete reusable gate for this commit', () => {
  assert.equal(deploy.jobs.quality.uses, './.github/workflows/mcu-quality.yml')
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
  assert.match(ruff.with.args, /^check/, 'lint 语义必须是 ruff check')
  assert.ok(ruff.with.args.includes('mcu/ruff.toml'), '合并后配置集中在 mcu/ruff.toml，仍须显式 --config')
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

test('AC4：Pages staging 由 assemble-pages 组装，终检+挂载冒烟+upload 指向 staging', () => {
  const steps = deploy.jobs.deploy.steps
  const at = (pred) => steps.findIndex(pred)
  const download = at((s) => String(s.uses || '').includes('download-artifact'))
  const asmIdx = at((s) => String(s.run || '').includes('assemble-pages.mjs'))
  assert.ok(asmIdx >= 0, 'deploy 必须调用 scripts/assemble-pages.mjs 组装 staging，不许内联散装 shell')
  const asm = steps[asmIdx]
  assert.match(asm.run, /--dist site/, '组装输入必须是下载的站点产物')
  assert.match(asm.run, /--out \.\.\/\.temp\/pages-site/, 'staging 落仓库根 .temp/pages-site（上传根含 mcu/ 子树）')
  const stagingAnchor = at((s) => String(s.run || '').includes('pages-check.mjs --dist ../.temp/pages-site/mcu'))
  const stagingSearch = at((s) => String(s.run || '').includes('search-check.mjs --dist ../.temp/pages-site/mcu'))
  assert.ok(stagingAnchor >= 0 && stagingSearch >= 0, '最终 staging/mcu 必须再过锚点与搜索两门（对真正上传的那一份）')
  const smokeIdx = at((s) => String(s.run || '').includes('mount-smoke.mjs'))
  assert.ok(smokeIdx >= 0, 'deploy 必须跑挂载冒烟（staging 按 /STM32/ 起服务，Chromium 回归）')
  assert.match(steps[smokeIdx].run, /--mount \/STM32/, '冒烟挂载点必须是 /STM32/')
  const uploadIdx = at((s) => String(s.uses || '').includes('upload-pages-artifact'))
  const upload = steps[uploadIdx]
  assert.equal(upload.with.path, '.temp/pages-site', '上传对象必须是组装后的 staging 根')
  assert.ok(download >= 0 && download < asmIdx, '组装必须在 download 之后')
  assert.ok(asmIdx < stagingAnchor && asmIdx < stagingSearch && asmIdx < smokeIdx, '组装先于终检与冒烟')
  assert.ok(stagingAnchor < uploadIdx && smokeIdx < uploadIdx, '终检与冒烟必须先于上传')
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