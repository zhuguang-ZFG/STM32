import { test } from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
test('host decodes logger payload, TLVs and refuses invalid settings without touching serial',()=>{
 const code=`import importlib.util,struct
s=importlib.util.spec_from_file_location('device','scripts/device-console.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=struct.pack('<IIIBBH6i6i',7,100,2,2,63,0,*([-32768,0,32767,1,2,3]*2))
d=m.parse_sample(p);assert d['sequence']==7 and d['raw'][0]==-32768 and d['filtered'][2]==32767
assert m.parse_tlvs(bytes([99,2,1,2]),0)=={99:bytes([1,2])}
try:m.parse_tlvs(bytes([1,3,0]),0);raise AssertionError('accepted truncated TLV')
except m.FrameError:pass
assert m.main(['configure','--period','99','--port','DO_NOT_OPEN'])==1
`
 const r=spawnSync('python3',['-c',code],{encoding:'utf8'})
 assert.equal(r.status,0,r.stdout+r.stderr)
})
