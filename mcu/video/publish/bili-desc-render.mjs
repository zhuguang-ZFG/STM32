// 只读：看 B站 视频页上「简介」这一块的真实渲染——反引号是变代码块，还是原样露出来。
import { chromium } from 'playwright'
const b = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = b.contexts()[0]
const p = await ctx.newPage()
try {
  await p.goto('https://www.bilibili.com/video/BV1JsJt6bEFH', { waitUntil: 'domcontentloaded', timeout: 60000 })
  await p.waitForTimeout(9000)
  // 简介默认是折叠的，折叠时 ``` 那几行根本不在可见 DOM 里，不点开就会误判成「没渲染」。
  for (const t of ['显示全部', '展开全部']) {
    await p.getByText(t, { exact: false }).first().click({ timeout: 4000 }).catch(() => {})
  }
  await p.waitForTimeout(2000)
  await p.evaluate(() => window.scrollTo(0, 420))
  await p.waitForTimeout(1500)
  const r = await p.evaluate(() => {
    const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
    // 简介区：找含 ``` 或时间轴文本的容器，看它的标签与计算样式
    const all = [...document.querySelectorAll('body *')].filter((e) => vis(e) && !e.children.length && /```/.test(e.textContent))
    const box = all.map((e) => {
      let n = e, chain = []
      for (let i = 0; i < 5 && n; i++) { chain.push(`${n.tagName.toLowerCase()}.${(n.className || '').toString().split(' ')[0]}`); n = n.parentElement }
      const cs = getComputedStyle(e)
      return { 链: chain.join(' < '), 白底: cs.whiteSpace, 字体: cs.fontFamily.slice(0, 24), 片段: e.textContent.replace(/\s+/g, ' ').slice(0, 70) }
    })
    const hasPre = [...document.querySelectorAll('pre,code')].filter(vis).length
    const descEl = document.querySelector('.basic-info-desc, .desc-msg, [class*=desc-open], [class*=VideoDescription]')
    // 类名换了就退化成「未找到」，所以再用内容兜底定位一次：简介里一定有这几个字。
    const byText = descEl ? null : [...document.querySelectorAll('body *')]
      .filter((e) => vis(e) && e.textContent.includes('本机') && e.textContent.includes('信号量') && e.textContent.length < 4000)
      .sort((a, b) => a.textContent.length - b.textContent.length)[0]
    const target = descEl || byText
    return {
      命中反引号节点数: all.length,
      命中反引号节点: box.slice(0, 3),
      pre或code元素数: hasPre,
      简介容器: target ? `${target.tagName.toLowerCase()}.${(target.className || '').toString().split(' ')[0]}` : '(未找到)',
      '简介前160字': (target?.innerText || '').replace(/\s+/g, ' ').slice(0, 160),
      简介含反引号: (target?.innerText || '').includes('`'),
      简介原文HTML片段: (target?.innerHTML || '').slice(0, 300),
    }
  })
  console.log(JSON.stringify(r, null, 1))
  await p.screenshot({ path: '.temp/bili-desc-render.png', clip: { x: 0, y: 300, width: 1200, height: 700 }, timeout: 20000 }).catch(() => {})
} finally {
  await p.close().catch(() => {})
}
