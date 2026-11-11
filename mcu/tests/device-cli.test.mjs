import {test} from 'node:test'
import assert from 'node:assert/strict'
import {spawnSync} from 'node:child_process'
test('CLI accepts the documented common arguments after a subcommand',()=>{
 const r=spawnSync(process.platform==='win32'?'python3':'python3',['scripts/device-console.py','self-test','--timeout','1'],{encoding:'utf8'})
 assert.equal(r.status,0,r.stdout+r.stderr)
})
