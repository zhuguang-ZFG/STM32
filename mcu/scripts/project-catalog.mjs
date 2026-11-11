import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const kinds = new Set(['arm-make', 'esp-idf', 'host-probe', 'host-make'])

export function loadProjects(repo = root) {
  const projects = JSON.parse(fs.readFileSync(path.join(repo, 'code/projects.json'), 'utf8'))
  if (!Array.isArray(projects) || !projects.length) throw new Error('工程清单必须是非空数组')
  const ids = new Set(), paths = new Set()
  for (const p of projects) {
    if (typeof p.id !== 'string' || !/^[a-z0-9-]+$/.test(p.id) || ids.has(p.id) || paths.has(p.path)) throw new Error(`重复或非法工程: ${p.id}`)
    ids.add(p.id); paths.add(p.path)
    if (!/^code\/[a-z0-9-]+\/[a-z0-9-]+$/.test(p.path) || !kinds.has(p.kind)) throw new Error(`非法工程路径/类型: ${p.id}`)
    const entry = { 'arm-make': 'Makefile', 'esp-idf': 'CMakeLists.txt', 'host-probe': 'probe.sh', 'host-make': 'Makefile' }[p.kind]
    if (p.entry !== entry || !fs.statSync(path.join(repo, p.path, entry), { throwIfNoEntry: false })?.isFile()) throw new Error(`构建入口不存在: ${p.id}`)
    if (p.kind === 'esp-idf' && p.target !== 'esp32s3') throw new Error(`目标必须为 esp32s3: ${p.id}`)
    // probe 是 arm-make 工程的可选取证钩子：值固定、文件必须真实存在，否则登记了就跑不起来。
    if (p.probe !== undefined && (p.kind !== 'arm-make' || p.probe !== 'probe.sh' || !fs.statSync(path.join(repo, p.path, p.probe), { throwIfNoEntry: false })?.isFile())) throw new Error(`probe 钩子非法: ${p.id}`)
    if (p.variants && (p.kind !== 'arm-make' || !Array.isArray(p.variants) || !p.variants.length || p.variants.some(v=>!/^build\/[a-z0-9-]+$/.test(v.dir)||!Array.isArray(v.args)||!v.args.length||v.args.some(a=>!/^(MODE=[0-3]|FAULTS=[01])$/.test(a))))) throw new Error(`非法构建变体: ${p.id}`)
    if (p.scenes && (p.kind !== 'arm-make' || !['[1,2,3,4,5]','[1,2,3,4,5,6]','[1,6]'].includes(JSON.stringify(p.scenes)))) throw new Error(`非法场景列表: ${p.id}`)
  }
  // 忽略空目录；有真实构建入口却未登记的工程必须补入清单。
  for (const board of fs.readdirSync(path.join(repo, 'code'), { withFileTypes: true }).filter(d => d.isDirectory())) {
    for (const dir of fs.readdirSync(path.join(repo, 'code', board.name), { withFileTypes: true }).filter(d => d.isDirectory())) {
      const rel = `code/${board.name}/${dir.name}`
      if (['Makefile', 'CMakeLists.txt', 'probe.sh'].some(f => fs.existsSync(path.join(repo, rel, f))) && !paths.has(rel)) throw new Error(`工程未登记: ${rel}`)
    }
  }
  return projects
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const projects = loadProjects()
  if (process.argv.includes('--matrix')) {
    console.log(JSON.stringify({ include: projects.filter(p => p.kind === 'esp-idf').flatMap(p => (p.faults ? ['normal','faults'] : ['normal']).map(variant => ({ path:p.path, target:p.target, variant, defaults:variant === 'faults' ? 'sdkconfig.defaults;sdkconfig.defaults.faults' : 'sdkconfig.defaults' }))) }))
  } else console.log(`工程清单通过：${projects.length} 个示例工程（不等同于上板验证）`)
}
