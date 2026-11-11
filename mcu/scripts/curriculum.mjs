import fs from 'node:fs'
import path from 'node:path'
export function validateCurriculum(entries) {
  const ids=new Map(),paths=new Set()
  for(const e of entries){
    if(!e.id||ids.has(e.id))throw Error(`重复课程 ID: ${e.id}`)
    if(!Array.isArray(e.must)||!Array.isArray(e.parallel))throw Error(`缺先修分类: ${e.id}`)
    if(e.path && (paths.has(e.path)||!/^docs\/[\w/-]+\.md$/.test(e.path)))throw Error(`非法/重复课程路径: ${e.path}`)
    ids.set(e.id,e);if(e.path)paths.add(e.path)
  }
  for(const e of entries)for(const id of [...e.must,...e.parallel])if(!ids.has(id))throw Error(`未知先修: ${e.id} -> ${id}`)
  const visiting=new Set(),done=new Set()
  function visit(id){if(visiting.has(id))throw Error(`硬前置形成环: ${id}`);if(done.has(id))return;visiting.add(id);for(const next of ids.get(id).must)visit(next);visiting.delete(id);done.add(id)}
  for(const id of ids.keys())visit(id)
  return entries
}
export function loadCurriculum(root){
  const entries=validateCurriculum(JSON.parse(fs.readFileSync(path.join(root,'docs/curriculum.json'),'utf8')))
  for(const e of entries)if(e.path&&!fs.existsSync(path.join(root,e.path)))throw Error(`已建档课程不存在: ${e.path}`)
  return entries
}
