#!/usr/bin/env node
/**
 * 从 mapping.json 生成旧 /mcu/** 路径的跳转存根。
 * 约定：每个源文件的主目标 = targets[0]；旧 URL 保留 mcu 前缀与 .html 后缀。
 * B5 扩展：mapping 之外的 37 个 mcu/docs 旧页（guide/reference/lab/各分区 index
 * /404 等）按 best-fit 目标表补齐——全书旧页覆盖率 100%（131 = 94 + 37）。
 * 附录目标使用 .md 后缀：站点由 VitePress/static 构建时会输出对应 html，
 * meta-refresh 对 .md 路径由目标站的 cleanUrls/服务器重写兜底——这里统一
 * 发到合并书附录的 .html 形态（build 产物路径）。
 */
import fs from 'node:fs'
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HOST = 'https://zhuguang-zfg.github.io'
const NEW_BASE = '/STM32/'
const OLD_BASE = '/mcu/'

export function oldUrlFor(source) {
  if (!source.startsWith('mcu/docs/')) {
    throw new Error(`not an mcu docs source: ${source}`)
  }
  return OLD_BASE + source.slice('mcu/docs/'.length).replace(/\.md$/, '.html')
}

export function targetUrlFor(file) {
  if (file.endsWith('.md')) {
    // 附录/书稿源文件：给出站点 html 形态（构建器按 .md 路径输出 .html）
    return NEW_BASE + file.replace(/\.md$/, '.html')
  }
  return NEW_BASE + file
}

// mapping 之外的 mcu/docs 旧页 → 合并书 best-fit 目标（B5 补齐表）。
// 键为 mcu/docs/ 相对路径；值为目标章文件（相对 docs/，含 .md）。
export const SUPPLEMENTARY_TARGETS = {
  'mcu/docs/index.md': 'index.md',
  'mcu/docs/404.md': 'index.md',
  'mcu/docs/animations.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/learning-path.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/hardware-test-plan.md': 'v6-labs-projects/42-project-delivery-acceptance.md',
  'mcu/docs/visual-enhancements.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/guide/index.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/guide/hardware.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/guide/manuals.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/guide/verify-on-hardware.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/reference/about.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/reference/bibliography.md': 'appendix/E-sources-version-license.md',
  'mcu/docs/reference/book.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/reference/changelog.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/reference/faq.md': 'v7-delivery/45-troubleshooting-handbook.md',
  'mcu/docs/reference/glossary.md': 'appendix/D-glossary.md',
  'mcu/docs/lab/index.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/lab/template.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/lab/reports/README.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/lab/reports/e01-test-report.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/lab/reports/equipment-checklist.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/lab/reports/first-round-test-report.md': 'v6-labs-projects/40-lab-method-instruments.md',
  'mcu/docs/lab/reports/gdb-cheat-sheet.md': 'v2-reliability/20-debug-performance.md',
  'mcu/docs/lab/reports/gdb-screenshot-guide.md': 'v2-reliability/20-debug-performance.md',
  'mcu/docs/lab/reports/j1-test-report.md': 'v6-labs-projects/41-dual-board-logger-project.md',
  'mcu/docs/c/index.md': 'v0-foundations/01-c-memory-model.md',
  'mcu/docs/build/index.md': 'v0-foundations/05-toolchain-four-steps.md',
  'mcu/docs/stm32/index.md': 'v1-drivers/08-architecture-memory-clock.md',
  'mcu/docs/rtos/index.md': 'v3-rtos/21-why-rtos.md',
  'mcu/docs/esp32/index.md': 'v4-platforms/30-esp32s3-architecture-boot.md',
  'mcu/docs/gd32/index.md': 'v4-platforms/29-gd32-arm-riscv.md',
  'mcu/docs/projects/index.md': 'v6-labs-projects/41-dual-board-logger-project.md',
  'mcu/docs/ai/index.md': 'v7-delivery/43-ai-pair-programming.md',
  'mcu/docs/reference/releases/2026-10-10-2.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/reference/releases/2026-10-10.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/video/c2-pointer-storyboard.md': 'v0-foundations/01-c-memory-model.md',
  'mcu/docs/video/f3-scheduler-storyboard.md': 'v3-rtos/22-tasks-tcb-scheduler.md',
  'mcu/docs/video/index.md': 'v7-delivery/46-resources-roadmap-open-source.md',
  'mcu/docs/video/hardware-freeze.md': 'v7-delivery/46-resources-roadmap-open-source.md',
}

function stub(target) {
  const canonical = HOST + target
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>页面已迁移</title>
<link rel="canonical" href="${canonical}">
<meta http-equiv="refresh" content="0; url=${target}">
</head>
<body>
<p>本页已迁移到 <a href="${target}">${target}</a>。</p>
<script>location.replace(${JSON.stringify(target)} + location.hash);</script>
</body>
</html>
`
}

async function listSourcePages(docsDir) {
  const frozen = JSON.parse(
    await readFile(join(dirname(fileURLToPath(import.meta.url)), '..', 'book', 'data', 'legacy-pages.json'), 'utf8'),
  )
  const pages = frozen.pages
  if (docsDir && fs.existsSync(docsDir)) {
    // 现场目录存在时做双向核对：冻结清单 ⇔ 实际 md 文件。
    const actual = []
    async function walk(dir) {
      for (const entry of await readdir(dir, { withFileTypes: true })) {
        const full = join(dir, entry.name)
        if (entry.isDirectory()) {
          if (entry.name === '.vitepress' || entry.name === 'public') continue
          await walk(full)
        } else if (entry.name.endsWith('.md')) {
          actual.push(full.split(path.sep).join('/'))
        }
      }
    }
    await walk(docsDir)
    const frozenSet = new Set(pages)
    const drift = actual.filter((f) => !frozenSet.has(f))
    if (drift.length > 0) throw new Error(`legacy pages drift (not in frozen list): ${drift.join(', ')}`)
  }
  return pages
}

export async function generate({ mappingPath, manifestPath, outDir, docsDir }) {
  const mapping = JSON.parse(await readFile(mappingPath, 'utf8'))
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
  const files = new Map()
  for (const part of manifest.parts) {
    for (const chapter of part.chapters) {
      files.set(chapter.id, chapter.file)
    }
  }
  for (const appendix of manifest.appendices ?? []) {
    files.set(appendix.id, appendix.file)
  }
  let count = 0
  const covered = new Set()
  for (const row of mapping.sources) {
    if (row.book !== 'mcu' || !row.source.startsWith('mcu/docs/')) continue
    const target = files.get(row.targets[0])
    if (!target) {
      throw new Error(`unknown target ${row.targets[0]} for ${row.source}`)
    }
    const outPath = join(outDir, oldUrlFor(row.source).slice(1))
    await mkdir(dirname(outPath), { recursive: true })
    await writeFile(outPath, stub(targetUrlFor(target)), 'utf8')
    covered.add(row.source)
    count += 1
  }
  {
    // B5 全量覆盖：mapping 之外的每个旧页都拿到 best-fit 存根
    // （docsDir 存在时与现场目录双向核对，不存在时用冻结清单）。
    const all = await listSourcePages(docsDir)
    const missed = all.filter((f) => !covered.has(f))
    for (const source of missed) {
      const targetRel = SUPPLEMENTARY_TARGETS[source]
      if (!targetRel) {
        throw new Error(`unmapped legacy page without best-fit target: ${source}`)
      }
      const oldUrl = OLD_BASE + source.slice('mcu/docs/'.length).replace(/\.md$/, '.html')
      const outPath = join(outDir, oldUrl.slice(1))
      await mkdir(dirname(outPath), { recursive: true })
      await writeFile(outPath, stub(targetUrlFor(targetRel)), 'utf8')
      covered.add(source)
      count += 1
    }
    const stillMissing = all.filter((f) => !covered.has(f))
    if (stillMissing.length > 0) {
      throw new Error(`legacy coverage gap: ${stillMissing.join(', ')}`)
    }
  }
  return count
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]
if (isMain) {
  const args = new Map()
  for (let index = 2; index < process.argv.length; index += 2) {
    args.set(process.argv[index], process.argv[index + 1])
  }
  const count = await generate({
    mappingPath: args.get('--mapping'),
    manifestPath: args.get('--manifest'),
    outDir: args.get('--out'),
    docsDir: args.get('--docs'),
  })
  console.log(`generated ${count} legacy redirect stubs`)
}
