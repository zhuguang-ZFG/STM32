import { chromium } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { gzipSync, brotliCompressSync } from 'node:zlib'
import { spawn } from 'node:child_process'
import assert from 'node:assert/strict'
import net from 'node:net'

const stage = process.argv[2] || 'current'
const out = process.argv[3] || 'test-results/performance'
fs.mkdirSync(out, { recursive: true })
const assets = fs.readdirSync('docs/.vitepress/dist', { recursive: true }).filter(f => /\.(js|css)$/.test(f)).map(file => {
  const data = fs.readFileSync(path.join('docs/.vitepress/dist', file))
  return { file, bytes: data.length, gzip: gzipSync(data).length, brotli: brotliCompressSync(data).length }
}).sort((a,b) => b.bytes-a.bytes)
const reservation=net.createServer()
await new Promise(resolve=>reservation.listen(0, '127.0.0.1', resolve))
const port=reservation.address().port
await new Promise(resolve=>reservation.close(resolve))
const origin='http://127.0.0.1:'+port
const server = spawn(process.execPath, ['node_modules/vitepress/bin/vitepress.js', 'preview', 'docs', '--host', '127.0.0.1', '--port', String(port)], { stdio: 'ignore' })
let browser
try {
  for (let i=0;i<60;i++) {
    try { if ((await fetch(origin+'/mcu/')).ok) break } catch {}
    await new Promise(r => setTimeout(r, 250))
  }
  browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || undefined, headless: true })
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } })
  const errors=[]
  page.on('pageerror', e=>errors.push(e.message))
  await page.goto(origin+'/mcu/', { waitUntil: 'networkidle' })
  const initial = await page.evaluate(() => performance.getEntriesByType('resource').map(r => ({name:r.name, bytes:r.transferSize})))
  await page.locator('.VPNavBarSearch button').click()
  try { await page.locator('#localsearch-input').fill('I2C', {timeout:10000}) }
  catch(e) { await page.screenshot({path:`${out}/${stage}-error.png`}); throw e }
  await page.locator('#localsearch-list [role=option]').first().waitFor({timeout:15000})
  const searched = await page.evaluate(() => performance.getEntriesByType('resource').map(r => ({name:r.name, bytes:r.transferSize})))
  const results = await page.locator('.VPLocalSearchBox .result').count()
  await page.screenshot({ path: `${out}/${stage}-search.png` })
  await page.keyboard.press('Escape')
  await page.goto(origin+'/mcu/stm32/02-rcc-clock.html', { waitUntil: 'networkidle' })
  const animationCount=await page.locator('.anim-figure').count()
  await page.locator('.anim-figure__btn').first().click()
  const paused=await page.locator('.anim-figure').first().evaluate(el=>el.querySelector('svg').animationsPaused())
  await page.locator('.anim-figure__btn').first().click()
  const playing=await page.locator('.anim-figure').first().evaluate(el=>!el.querySelector('svg').animationsPaused())
  await page.emulateMedia({ reducedMotion:'reduce',colorScheme:'dark' })
  await page.reload({waitUntil:'networkidle'})
  const reduced=await page.locator('.anim-figure').first().evaluate(el=>el.querySelector('svg').animationsPaused())
  await page.setViewportSize({width:390,height:844})
  await page.screenshot({path: `${out}/${stage}-mobile.png`})
  const metrics={stage,assets:assets.slice(0,12),initial,searched,results,animationCount,paused,playing,reduced,errors}
  fs.writeFileSync(`${out}/${stage}-performance.json`,JSON.stringify(metrics,null,2)+'\n')
  assert.deepEqual(errors, [])
  assert.ok(results > 0 && paused && playing && reduced)
  console.log(JSON.stringify({stage,largest:assets[0],initialSearch:initial.filter(r=>r.name.includes('localSearchIndex')).length,loadedSearch:searched.filter(r=>r.name.includes('localSearchIndex')).length,results,animationCount,paused,playing,reduced,errors}))
} finally { if(browser) await browser.close(); server.kill() }
