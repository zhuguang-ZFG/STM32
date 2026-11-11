import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readMetadata, readLabMetadata } from '../scripts/content-metadata.mjs'
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

const valid = '---\ntitle: Example\nstatus: done\ndifficulty: 2\nminutes: 30\n---\n# Example'
test('valid metadata remains typed', () => {
  assert.equal(readMetadata(valid).minutes, 30)
  assert.equal(readMetadata(valid.replace('done', 'building')).status, 'building')
})
for (const [field, value] of [['title', '""'], ['status', 'finished'], ['difficulty', '4'], ['difficulty', '"2"'], ['minutes', '0'], ['minutes', '-1'], ['minutes', '2.5'], ['minutes', 'abc']]) {
  test(`reject invalid ${field}=${value}`, () => assert.throws(() => readMetadata(valid.replace(new RegExp(`^${field}:.*$`, 'm'), `${field}: ${value}`))))
}
for (const field of ['title', 'status', 'difficulty', 'minutes']) {
  test(`reject missing ${field}`, () => assert.throws(() => readMetadata(valid.replace(new RegExp(`^${field}:.*\\n`, 'm'), ''))))
}
test('reject duplicate YAML fields', () => assert.throws(() => readMetadata(valid.replace('minutes: 30', 'minutes: 30\nminutes: 20'))))

const lab = { code_status:'ready', hardware_status:'pending', code_note:'独立工程', projects:['demo'] }
test('ready labs require a registered project', () => {
  assert.equal(readLabMetadata(lab, [{id:'demo'}], 'docs').hardwareStatus, 'pending')
  assert.throws(()=>readLabMetadata({...lab,projects:[]}, [], 'docs'), /ready/)
  assert.throws(()=>readLabMetadata({...lab,projects:0}, [], 'docs'), /工程/)
  assert.throws(()=>readLabMetadata(lab, [], 'docs'), /工程/)
})
test('verified labs require an actual evidence file within docs', t => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'mcu-evidence-'))
  t.after(()=>fs.rmSync(dir,{recursive:true}))
  const verified={...lab,hardware_status:'verified'}
  assert.throws(()=>readLabMetadata(verified,[{id:'demo'}],dir), /证据/)
  assert.throws(()=>readLabMetadata({...verified,evidence:'.'},[{id:'demo'}],dir), /证据/)
  assert.throws(()=>readLabMetadata({...verified,evidence:'../other.md'},[{id:'demo'}],dir), /证据/)
  fs.writeFileSync(path.join(dir,'record.md'),'fixture measurement')
  assert.equal(readLabMetadata({...verified,evidence:'record.md'},[{id:'demo'}],dir).hardwareStatus,'verified')
})
