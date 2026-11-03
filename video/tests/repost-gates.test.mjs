import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { requireGate, GateError, consumeGate, parseArgs } from '../publish/repost/common.mjs'

test('无闸门 exit 3', () => {
  const dir = mkdtempSync(join(tmpdir(), 'gate-'))
  assert.throws(
    () => requireGate('delete', 'ep', dir),
    (e) => e instanceof GateError && e.exitCode === 3,
  )
})

test('闸门内容原样返回，消费后不可复用', () => {
  const dir = mkdtempSync(join(tmpdir(), 'gate-'))
  writeFileSync(join(dir, 'I_HAVE_USER_OK_DELETE_ep'), '我确认删除这一集的旧稿\n')
  assert.equal(requireGate('delete', 'ep', dir), '我确认删除这一集的旧稿')
  consumeGate('delete', 'ep', dir)
  assert.throws(() => requireGate('delete', 'ep', dir))
})

test('parseArgs 拒绝批量 --all', () => {
  assert.throws(() => parseArgs(['--all']), /禁止批量/)
  assert.throws(() => parseArgs(['--ep', 's5-systick', '--platform', 'bilibili', '--all']), /禁止批量/)
})

test('parseArgs 接受 --ep=x 与空格两种写法', () => {
  assert.equal(parseArgs(['--ep=s5-systick', '--platform=douyin']).ep, 's5-systick')
  assert.equal(parseArgs(['--ep', 's5-systick', '--platform', 'douyin']).platform, 'douyin')
})

test('parseArgs 拒绝缺集号与多集列表', () => {
  assert.throws(() => parseArgs(['--platform', 'bilibili']), /--ep/)
  assert.throws(() => parseArgs(['--ep', 's5-systick,c2-pointer']), /一次只处理一集/)
})
