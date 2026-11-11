import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { loadProjects } from '../scripts/project-catalog.mjs'

function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mcu-catalog-'))
  t.after(() => {
    assert.ok(path.resolve(dir).startsWith(path.resolve(os.tmpdir()) + path.sep))
    fs.rmSync(dir, { recursive: true })
  })
  fs.mkdirSync(path.join(dir, 'code/esp32/example'), { recursive: true })
  fs.writeFileSync(path.join(dir, 'code/esp32/example/CMakeLists.txt'), 'project(example)')
  const entries = [{ id: 'example', path: 'code/esp32/example', kind: 'esp-idf', entry: 'CMakeLists.txt', target: 'esp32s3' }]
  const write = data => fs.writeFileSync(path.join(dir, 'code/projects.json'), JSON.stringify(data))
  write(entries)
  return { dir, entries, write }
}
test('an empty directory does not increase project count', t => {
  const { dir } = fixture(t)
  fs.mkdirSync(path.join(dir, 'code/esp32/empty'))
  assert.equal(loadProjects(dir).length, 1)
})
test('unregistered build entry fails', t => {
  const { dir } = fixture(t)
  fs.mkdirSync(path.join(dir, 'code/esp32/another'))
  fs.writeFileSync(path.join(dir, 'code/esp32/another/Makefile'), '')
  assert.throws(() => loadProjects(dir), /未登记/)
})
test('missing entry fails', t => {
  const { dir } = fixture(t)
  fs.unlinkSync(path.join(dir, 'code/esp32/example/CMakeLists.txt'))
  assert.throws(() => loadProjects(dir), /入口/)
})
test('duplicates and traversal fail', t => {
  const { dir, entries, write } = fixture(t)
  write([...entries, ...entries])
  assert.throws(() => loadProjects(dir), /重复/)
  write([{ ...entries[0], path: '../escape' }])
  assert.throws(() => loadProjects(dir), /路径/)
})
test('classic ESP32 target cannot silently pass', t => {
  const { dir, entries, write } = fixture(t)
  write([{ ...entries[0], target: 'esp32' }])
  assert.throws(() => loadProjects(dir), /esp32s3/)
})
test('probe hook is opt-in, arm-make only, and must point at a real file', t => {
  const { dir, entries, write } = fixture(t)
  fs.mkdirSync(path.join(dir, 'code/stm32/board'), { recursive: true })
  fs.writeFileSync(path.join(dir, 'code/stm32/board/Makefile'), '')
  const arm = { id: 'board', path: 'code/stm32/board', kind: 'arm-make', entry: 'Makefile' }
  write([...entries, { ...arm, probe: 'probe.sh' }])
  assert.throws(() => loadProjects(dir), /probe 钩子/)
  fs.writeFileSync(path.join(dir, 'code/stm32/board/probe.sh'), '#!/bin/sh\n')
  assert.equal(loadProjects(dir).length, 2)
  write([{ ...entries[0], probe: 'probe.sh' }])
  assert.throws(() => loadProjects(dir), /probe 钩子/)
})
