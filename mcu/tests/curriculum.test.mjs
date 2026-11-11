import {test} from 'node:test'
import assert from 'node:assert/strict'
import {validateCurriculum} from '../scripts/curriculum.mjs'
const entry=(id,must=[],parallel=[])=>({id,must,parallel,path:null})
test('parallel references allow mutual reading, hard cycles fail',()=>{
 assert.equal(validateCurriculum([entry('A',[],['B']),entry('B',[],['A'])]).length,2)
 assert.throws(()=>validateCurriculum([entry('A',['B']),entry('B',['A'])]),/环/)
 assert.throws(()=>validateCurriculum([entry('A',['missing'])]),/未知/)
})
test('duplicate IDs and paths cannot change planned totals silently',()=>{
 assert.throws(()=>validateCurriculum([entry('A'),entry('A')]),/重复/)
 assert.throws(()=>validateCurriculum([{...entry('A'),path:'../x.md'}]),/路径/)
})
