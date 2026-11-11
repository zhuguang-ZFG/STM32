import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { readAnim } from '../../docs/.vitepress/anim-decorate.mjs'
import { animMarkup, pageHtml, setAnimSourceReader } from '../src/layout.mjs'
import { platformConfig, resolveScenes } from '../src/spec.mjs'

setAnimSourceReader(readAnim)

test('S5 v1 双平台 pageHtml 与金样例逐字节相同', () => {
  // 金样例必须配冻结输入：S5 已在 Task 11 转为 v2，实时 episode 会改掉 v1 布局的输入。
  const ep = JSON.parse(readFileSync('video/tests/fixtures/episode-v1-s5.json', 'utf8'))
  for (const p of ['bilibili', 'douyin']) {
    const cfg = platformConfig(ep, p)
    const scenes = resolveScenes(ep, p)
    const anims = {}
    scenes.forEach((sc, i) => { if (sc.anim) anims[`${p}-${i}`] = animMarkup(sc.anim, `${p}-${i}`) })
    const html = pageHtml({ platform: p, size: cfg.size, safe: cfg.safe, scenes, anims,
      kicker: ep.cover?.kicker || '通往单片机之路', badge: ep.badge || 'S5', sections: cfg.sections })
    assert.equal(html, readFileSync(`video/tests/fixtures/page-v1-s5-${p}.html`, 'utf8'), p)
  }
})
