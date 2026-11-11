import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

test('tutorial Markdown retains Unicode instead of shell-encoding replacements', () => {
  const files = fs.readdirSync('docs', { recursive:true }).filter(f => f.endsWith('.md') && !f.startsWith('.vitepress'))
  for (const f of files) {
    const text = fs.readFileSync(path.join('docs',f),'utf8')
    assert.doesNotMatch(text, /\?{3,}|\uFFFD/, f)
  }
})
