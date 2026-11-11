import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import assert from 'node:assert/strict'
import { loadProjects, root } from './project-catalog.mjs'

const make = process.env.MAKE || (process.platform === 'win32' ? 'mingw32-make' : 'make')
function run(command, args, cwd) {
  console.log(`> ${command} ${args.join(' ')} (${path.relative(root, cwd)})`)
  const result = spawnSync(command, args, { cwd, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 })
  process.stdout.write(result.stdout || '')
  process.stderr.write(result.stderr || '')
  if (result.error || result.status !== 0) throw result.error || new Error(`${command} failed: ${result.status}`)
  return result.stdout
}
const projects = loadProjects()
for (const p of projects.filter(p => p.kind !== 'esp-idf')) {
  const cwd = path.join(root, p.path)
  if (p.kind === 'host-probe') run('sh', [p.entry], cwd)
  if (p.kind === 'host-make') run(make, ['-B', 'run', 'asm-arm'], cwd)
  if (p.kind === 'arm-make') {
    if(p.variants) { for(const v of p.variants) run(make,['-B',...v.args],cwd) }
    else for (const scene of p.scenes || [null]) run(make, ['-B', ...(scene ? [`DEMO_SCENE=${scene}`] : [])], cwd)
    const builds = p.variants ? p.variants.map(v=>v.dir) : p.scenes ? p.scenes.map(n => `build/scene-${n}`) : ['build']
    for (const dir of builds) {
      const elf = fs.readdirSync(path.join(cwd, dir)).find(f => f.endsWith('.elf'))
      assert.ok(elf, `${p.id}: missing ELF`)
      const symbols = run('arm-none-eabi-nm', ['-n', `${dir}/${elf}`], cwd)
      const sections = run('arm-none-eabi-objdump', ['-h', `${dir}/${elf}`], cwd)
      assert.match(sections, /\.(?:isr_vector|text)\s+\w+\s+08000000/i, `${p.id}: flash start`)
      const reset = symbols.match(/^([a-f0-9]+)\s+\w\s+Reset_Handler$/m)
      const stack = symbols.match(/^([a-f0-9]+)\s+\w\s+(?:_estack|__StackTop)$/m)
      assert.ok(reset && stack, `${p.id}: startup symbols`)
      const bin = fs.readFileSync(path.join(cwd, dir, elf.replace(/\.elf$/, '.bin')))
      assert.equal(bin.readUInt32LE(0), parseInt(stack[1], 16), `${p.id}: initial SP`)
      assert.equal(bin.readUInt32LE(4), parseInt(reset[1], 16) | 1, `${p.id}: reset vector`)
    }
if (p.scenes && p.scenes.length >= 2) {
      // 场景独立性：不同 DEMO_SCENE 产物必须不同；切回首个场景须可复现。
      const binName = n => fs.readdirSync(path.join(cwd, `build/scene-${n}`)).find(f => f.endsWith('.bin'))
      const hash = n => createHash('sha256').update(fs.readFileSync(path.join(cwd, `build/scene-${n}`, binName(n)))).digest('hex')
      const first = hash(p.scenes[0]), second = hash(p.scenes[1])
      assert.notEqual(first, second, 'scene variants must differ')
      for (const scene of [p.scenes[0], p.scenes[1], p.scenes[0]]) run(make, [`DEMO_SCENE=${scene}`], cwd)
      assert.equal(hash(p.scenes[0]), first)
      assert.equal(hash(p.scenes[1]), second)
      const elfName = binName(p.scenes[1]).replace(/\.bin$/, '.elf')
      assert.match(run(make, ['-n', `DEMO_SCENE=${p.scenes[1]}`, 'flash'], cwd), new RegExp(`program build\\/scene-${p.scenes[1]}\\/${elfName}`))
      const bad = spawnSync(make, ['-n', `DEMO_SCENE=${p.scenes[p.scenes.length - 1] + 1}`, 'flash'], { cwd, encoding: 'utf8' })
      assert.notEqual(bad.status, 0, 'invalid scene must fail')
    }
    if(p.variants){
      const digest=v=>{const dir=path.join(cwd,v.dir);const file=fs.readdirSync(dir).find(f=>f.endsWith('.bin'));return createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex')}
      const first=digest(p.variants[0]);
      assert.notEqual(first,digest(p.variants[1]),'normal/fault builds must differ');
      run(make,p.variants[0].args,cwd);assert.equal(digest(p.variants[0]),first);
      assert.notEqual(spawnSync(make,['MODE=99'],{cwd}).status,0);
    }
    // 无板取证脚本：只有清单里显式声明 probe 的 arm-make 工程才跑（它要交叉链与 CMSIS 头文件两样东西）。
    if (p.probe) run('sh', [p.probe], cwd)
  }
}
console.log('All ARM/host projects passed; hardware observations remain separate.')
