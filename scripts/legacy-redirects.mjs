#!/usr/bin/env node
/**
 * 从 mapping.json 生成旧 /mcu/** 路径的跳转存根。
 * 约定：每个源文件的主目标 = targets[0]；旧 URL 保留 mcu 前缀与 .html 后缀。
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
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
  return NEW_BASE + file.replace(/\.md$/, '.html')
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

export async function generate({ mappingPath, manifestPath, outDir }) {
  const mapping = JSON.parse(await readFile(mappingPath, 'utf8'))
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
  const files = new Map()
  for (const part of manifest.parts) {
    for (const chapter of part.chapters) {
      files.set(chapter.id, chapter.file)
    }
  }
  let count = 0
  for (const row of mapping.sources) {
    if (row.book !== 'mcu' || !row.source.startsWith('mcu/docs/')) continue
    const target = files.get(row.targets[0])
    if (!target) {
      throw new Error(`unknown target ${row.targets[0]} for ${row.source}`)
    }
    const outPath = join(outDir, oldUrlFor(row.source).slice(1))
    await mkdir(dirname(outPath), { recursive: true })
    await writeFile(outPath, stub(targetUrlFor(target)), 'utf8')
    count += 1
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
  })
  console.log(`generated ${count} legacy redirect stubs`)
}
