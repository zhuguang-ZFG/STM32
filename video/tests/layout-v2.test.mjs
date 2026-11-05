import test from 'node:test'
import assert from 'node:assert/strict'
import { pageHtml } from '../src/layout.mjs'

const scenes = [{
  id: 'a', kind: 'card', title: '上电', kicker: 'BOOT', bullets: ['一', '二'], sub: '一秒',
  narration: 'x', emphasis: ['A'],
}, {
  id: 'b', kind: 'code', title: '代码', code: 'A\nB', narration: 'y',
}]

test('v2 生成仪器层、节拍属性和客户端方法', () => {
  const html = pageHtml({ platform: 'douyin', size: [1080, 1920], safe: {}, scenes, anims: {}, kicker: 'k', badge: 'T', sections: null, formatVersion: 2, fps: 30 })
  assert.match(html, /class="rig"/)
  assert.match(html, /MCU\.state/)
  assert.match(html, /showAll/)
  const payload = JSON.parse(html.match(/window\.PAYLOAD = (.*);\n/)[1])
  const body = payload.map((sc) => sc.html).join('')
  assert.match(body, /data-beat-target="title"/)
  assert.match(body, /data-beat-target="bullets:0"/)
  assert.match(body, /data-ln="1"/)
  assert.match(body, /data-ln="2"/)
  assert.equal((body.match(/data-ln="/g) || []).length, 2, '两行代码应正好产生两个行号')
})

test('v1 不产生任何 v2 属性', () => {
  const html = pageHtml({ platform: 'douyin', size: [1080, 1920], safe: {}, scenes, anims: {}, kicker: 'k', badge: 'T', sections: null })
  assert.doesNotMatch(html, /data-beat-target/)
  assert.doesNotMatch(html, /class="rig"/)
})
