import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  slugify,
  vitePressSlug,
  collectMarkdown,
  checkLinks,
  checkHygiene,
  checkSelfBlobLinks,
  checkNumberClaims,
  checkCitation,
  checkChangelog,
  CLAIMS,
} from '../scripts/docs-check.mjs'

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

/** 造一个迷你仓库：docs/ 目录 + 根 README，临时目录用完即弃。 */
function fixture(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'docs-check-'))
  for (const [rel, text] of Object.entries(files)) {
    const p = path.join(dir, rel)
    fs.mkdirSync(path.dirname(p), { recursive: true })
    fs.writeFileSync(p, text)
  }
  return dir
}

/* ---------------- slugify：GitHub 锚点算法 ---------------- */

test('slugify：A + B 必须得到 a--b（每个空格各换一个 -，不折叠）', () => {
  assert.equal(slugify('A + B'), 'a--b')
  assert.equal(slugify('a  b'), 'a--b') // 双空格 → 双连字符
})

test('slugify：小写、去标点、保汉字', () => {
  assert.equal(slugify('Hello World'), 'hello-world')
  assert.equal(slugify('第五步：接线（SWD 四线）'), '第五步接线swd-四线')
  assert.equal(slugify('C++ 与 C#'), 'c-与-c')
})

test('slugify：NFC 归一——组合记音序列与预组合字符同锚点', () => {
  assert.equal(slugify('Café'), slugify('Café'))
})

/* ---------------- collectMarkdown：扫描范围 ---------------- */

test('collectMarkdown：docs 递归 + 根 *.md，排除 dist/node_modules/mcu-book', () => {
  const dir = fixture({
    'docs/a.md': '# a',
    'docs/sub/b.md': '# b',
    'README.md': '# r',
    'docs/.vitepress/dist/x.md': '# 构建产物',
    'docs/node_modules/y.md': '# 依赖',
    'mcu-book/book/A.md': '# 书籍附录（不扫）',
    'mcu-book/README.md': '# 书籍说明（不在默认扫描集）',
  })
  const files = collectMarkdown(dir)
  assert.deepEqual(files, ['README.md', 'docs/a.md', 'docs/sub/b.md'])
})

/* ---------------- checkLinks：正反例 ---------------- */

test('checkLinks：相对链接存在 + .md 锚点命中 → 零报错', () => {
  const dir = fixture({
    'README.md': '[去看 b](docs/b.md#真标题)',
    'docs/a.md': '# a\n\n[回 b](b.md#真标题)',
    'docs/b.md': '# B\n\n## 真标题\n\n内容',
  })
  assert.deepEqual(checkLinks(dir), [])
})

test('checkLinks：.md 锚点未命中 → 点名 文件:行 与锚点', () => {
  const dir = fixture({
    'docs/a.md': '[坏链](b.md#不存在的标题)',
    'docs/b.md': '## 真标题',
  })
  const problems = checkLinks(dir)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /docs\/a\.md:1/)
  assert.match(problems[0], /#不存在的标题/)
  assert.match(problems[0], /找不到对应标题/)
})

test('checkLinks：相对链接指向不存在文件 → 点名', () => {
  const dir = fixture({ 'docs/a.md': '[没有](ghost.md)' })
  const problems = checkLinks(dir)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /docs\/a\.md:1/)
  assert.match(problems[0], /不存在/)
})

test('checkLinks：VitePress 自定义锚点 {#id} 可解析', () => {
  const dir = fixture({
    'docs/a.md': '[去](b.md#refs)',
    'docs/b.md': '## 参考文献 {#refs}',
  })
  assert.deepEqual(checkLinks(dir), [])
})

test('checkLinks：.html 锚点按 id 解析（命中与未命中）', () => {
  const dir = fixture({
    'docs/a.md': '[好](assets/x.html#sec-2) [坏](assets/x.html#sec-9)',
    'docs/assets/x.html': '<html><section id="sec-2"></section></html>',
  })
  const problems = checkLinks(dir)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /#sec-9/)
  assert.match(problems[0], /id="sec-9"/)
})

test('checkLinks：/mcu/ 站内绝对路径视为错误', () => {
  const dir = fixture({ 'docs/a.md': '[错](/mcu/stm32/03-gpio)' })
  const problems = checkLinks(dir)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /站内绝对路径/)
})

test('checkLinks：路径末尾带 . 或空白 → 拒绝', () => {
  const dir = fixture({ 'docs/a.md': '[点](b.md.) [空](b.md%20)', 'docs/b.md': '# b' })
  const problems = checkLinks(dir)
  assert.equal(problems.length, 2)
  problems.forEach((p) => assert.match(p, /末尾带/))
})

test('checkLinks：站点根 / 起头路径按 docs 与 docs/public 解析', () => {
  const dir = fixture({
    'docs/a.md': '[页](/sub/b.md) [资源](/anim/x.svg)',
    'docs/sub/b.md': '# b',
    'docs/public/anim/x.svg': '<svg/>',
  })
  assert.deepEqual(checkLinks(dir), [])
})

test('checkLinks：代码围栏里的示例链接不检查', () => {
  const dir = fixture({ 'docs/a.md': '```\n[示例](ghost.md#x)\n```' })
  assert.deepEqual(checkLinks(dir), [])
})

/* ---------------- checkHygiene：正反例 ---------------- */

test('checkHygiene：正文里的真 TAB 被点名（文件:行）', () => {
  const dir = fixture({ 'docs/a.md': '段落里塞了\t一个真 TAB' })
  const problems = checkHygiene(dir)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /docs\/a\.md:1/)
  assert.match(problems[0], /TAB/)
})

test('checkHygiene：代码围栏里的真 TAB 放行（Makefile/C 示例需要它）', () => {
  const dir = fixture({ 'docs/a.md': '```makefile\nall:\n\tgcc main.c\n```' })
  assert.deepEqual(checkHygiene(dir), [])
})

test('checkHygiene：\\( 与 \\) 行内公式定界符被点名', () => {
  const dir = fixture({ 'docs/a.md': '公式 \\(a+b\\) 会原样漏出' })
  const problems = checkHygiene(dir)
  assert.ok(problems.length >= 1)
  assert.match(problems[0], /公式定界符/)
})

test('checkHygiene：其余控制字符（如 BEL）被点名', () => {
  const dir = fixture({ 'docs/a.md': '响\x07了一下' })
  const problems = checkHygiene(dir)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /U\+0007/)
})

/* ---------------- checkSelfBlobLinks：正反例 ---------------- */

test('checkSelfBlobLinks：指向工作树存在路径 → 通过；不存在 → 点名', () => {
  const dir = fixture({
    'code/x/main.c': 'int main(){}',
    'docs/a.md':
      '[好](https://github.com/zhuguang-ZFG/mcu/blob/main/code/x/main.c) ' +
      '[坏](https://github.com/zhuguang-ZFG/mcu/blob/main/code/x/ghost.c)',
  })
  const problems = checkSelfBlobLinks(dir)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /docs\/a\.md:1/)
  assert.match(problems[0], /code\/x\/ghost\.c/)
})

/* ---------------- checkNumberClaims：正反例 ---------------- */

const claimOn = (file, pattern, expected, minMatches = 1) => [
  { label: '测试数', file, pattern, expected: () => expected, minMatches },
]

test('checkNumberClaims：捕获值与期望一致且命中数达标 → 通过', () => {
  const dir = fixture({ 'README.md': '全书 88 章，装订成 10 个分部。' })
  assert.deepEqual(checkNumberClaims(dir, claimOn('README.md', /(\d+) 章/g, 88)), [])
})

test('checkNumberClaims：捕获值与期望不符 → 点名实际 vs 期望', () => {
  const dir = fixture({ 'README.md': '全书 89 章。' })
  const problems = checkNumberClaims(dir, claimOn('README.md', /(\d+) 章/g, 88))
  assert.equal(problems.length, 1)
  assert.match(problems[0], /README\.md:1/)
  assert.match(problems[0], /89（=89）与实际 88 不符/)
})

test('checkNumberClaims：正则捞不到预期句数 → 红（防写法改了门静默变绿）', () => {
  const dir = fixture({ 'README.md': '全书八十八章。' })
  const problems = checkNumberClaims(dir, claimOn('README.md', /(\d+) 章/g, 88, 1))
  assert.equal(problems.length, 1)
  assert.match(problems[0], /只命中 0 处/)
  assert.match(problems[0], /不许静默变绿/)
})

test('checkNumberClaims：中文数字可解析（五 = 5）', () => {
  const dir = fixture({ 'README.md': '接收链路的五个契约。' })
  assert.deepEqual(checkNumberClaims(dir, claimOn('README.md', /([一二三四五六七八九十]+)个契约/g, 5)), [])
})

/* ---------------- vitePressSlug：站点侧锚点算法 ---------------- */

test('vitePressSlug：全角标点折成 "-"（与产物 id 实测一致）', () => {
  // 这三条都是与 docs/.vitepress/dist 里真实 id 对拍过的事实，改算法必须先来这里对
  assert.equal(vitePressSlug('第五步：接线（SWD 四线）'), '第五步-接线-swd-四线')
  assert.equal(vitePressSlug('一、移位环：发即是收，收即是发'), '一、移位环-发即是收-收即是发')
  assert.equal(vitePressSlug('S12 SPI：四根线的全双工移位'), 's12-spi-四根线的全双工移位')
})

test('checkLinks：站点风格锚点（VitePress 折行）也认，两端取并集', () => {
  const dir = fixture({
    'docs/a.md': '# 起点\n\n## 第五步：接线（SWD 四线）\n\n正文\n',
    'docs/b.md': '# 目标\n\n见 [A 第五步](./a.md#第五步-接线-swd-四线)。\n',
  })
  assert.deepEqual(checkLinks(path.join(dir, 'docs')), [])
  assert.deepEqual(checkLinks(dir), [], '站点风格锚点必须被接受（书里/站点上它才是对的那条）')
  fs.rmSync(dir, { recursive: true, force: true })
})

/* ---------------- 元文件与发布口径 ---------------- */

function metaFixture({ citation, changelog, siteChangelog, version = '1.0.0' } = {}) {
  const manifest = {
    title: '合成样书',
    version,
    author: '某人与贡献者',
    repository: 'https://github.com/zhuguang-ZFG/mcu',
  }
  return fixture({
    'mcu-book/manifest.json': JSON.stringify(manifest),
    'docs/reference/changelog.md': siteChangelog ?? '## 2026-10-25 · 整书离线版 v1.0.0 发布\n',
    'CITATION.cff':
      citation ??
      [
        'cff-version: 1.2.0',
        'title: "合成样书"',
        'version: 1.0.0',
        'repository-code: "https://github.com/zhuguang-ZFG/mcu"',
        'url: "https://zhuguang-zfg.github.io/mcu/"',
        'authors:',
        '  - name: "某人与贡献者"',
      ].join('\n'),
    'CHANGELOG.md': changelog ?? '# 更新日志\n\n## v1.0.0 · 2026-10-25\n\n- 首个版本。\n',
  })
}

const BASE_URL = 'https://zhuguang-zfg.github.io/mcu/'

test('checkCitation：与 manifest/站点口径一致 → 通过；字段漂移 → 逐条点名', () => {
  const ok = metaFixture()
  assert.deepEqual(checkCitation(ok), [])
  fs.rmSync(ok, { recursive: true, force: true })

  const drifted = metaFixture({
    citation: [
      'cff-version: 1.2.0',
      'title: "合成样书"',
      'version: 0.9.9', // 与 manifest 漂移
      'repository-code: "https://github.com/zhuguang-ZFG/mcu"',
      `url: "${BASE_URL}"`,
      'authors:',
      '  - name: "另一个人"', // 与 manifest.author 漂移
    ].join('\n'),
  })
  const problems = checkCitation(drifted)
  assert.equal(problems.length, 2)
  assert.ok(problems.some((p) => p.includes('version')))
  assert.ok(problems.some((p) => p.includes('authors[0].name')))
  fs.rmSync(drifted, { recursive: true, force: true })
})

test('checkCitation：文件缺失要报错（不许静默）', () => {
  const dir = fixture({ 'mcu-book/manifest.json': '{"title":"t","version":"1.0.0","author":"a","repository":"r"}' })
  assert.equal(checkCitation(dir).length, 1)
  fs.rmSync(dir, { recursive: true, force: true })
})

test('checkChangelog：版本号三方对账（根 CHANGELOG ↔ 站点日志 ↔ manifest.version）', () => {
  const ok = metaFixture()
  assert.deepEqual(checkChangelog(ok), [])
  fs.rmSync(ok, { recursive: true, force: true })

  const missingInSite = metaFixture({ siteChangelog: '## 2026-10-25 · 一些别的改动\n' })
  assert.ok(checkChangelog(missingInSite).some((p) => p.includes('找不到对应提法')))
  fs.rmSync(missingInSite, { recursive: true, force: true })

  const staleVersion = metaFixture({ changelog: '# 更新日志\n\n## v0.9.0 · 2026-01-01\n\n- 旧版。\n' })
  assert.ok(checkChangelog(staleVersion).some((p) => p.includes('manifest.version')))
  fs.rmSync(staleVersion, { recursive: true, force: true })

  const noSections = metaFixture({ changelog: '# 更新日志\n\n什么版本节都没有。\n' })
  assert.ok(checkChangelog(noSections).some((p) => p.includes('没有任何')))
  fs.rmSync(noSections, { recursive: true, force: true })
})

/* ---------------- 真实仓库集成：当前仓库必须零报错 ---------------- */

test('真实仓库：五类检查对当前工作树全部通过（CLAIMS 已登记）', () => {
  assert.ok(CLAIMS.length >= 20, `CLAIMS 只登记了 ${CLAIMS.length} 条，覆盖率存疑`)
  assert.deepEqual(checkLinks(REPO), [])
  assert.deepEqual(checkHygiene(REPO), [])
  assert.deepEqual(checkSelfBlobLinks(REPO), [])
  assert.deepEqual(checkNumberClaims(REPO), [])
  assert.deepEqual(checkCitation(REPO), [])
  assert.deepEqual(checkChangelog(REPO), [])
})
