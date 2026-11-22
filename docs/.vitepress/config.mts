import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import {
  BASE,
  SITE_URL,
  buildNav,
  buildSidebar,
  cjkTokenize,
  docsRoot,
  manifest,
  slugify,
} from './book.mts'
import { bookMarkdown } from './plugins/book-markdown.mts'

const scenes = JSON.parse(
  fs.readFileSync(path.join(docsRoot, '.vitepress', 'data', 'scenes.json'), 'utf8'),
)

export default defineConfig({
  lang: 'zh-CN',
  title: manifest.title,
  description: `${manifest.title}：${manifest.subtitle ?? ''}`,
  base: BASE,
  cleanUrls: false,
  srcExclude: ['superpowers/**', 'README.md', 'CONTENT_GUIDE.md'],
  // 离线整书（`/book/*.pdf|html|epub`）不在源码树里：它们是 deploy 时由 Book CI
  // 构建后写进 staging 的产物，所以 VitePress 把这几条当作“指向不存在的页面”报死链。
  // 这里只豁免这条路径；链接到底通不通由 `site:smoke` 的「离线下载」断言在真实
  // staging 上验（200 + 字节下限），不靠构建期猜测。
  ignoreDeadLinks: [/\.\/book\//],
  sitemap: { hostname: SITE_URL },
  head: [['meta', { name: 'theme-color', content: '#fdf8ea' }]],
  markdown: {
    html: true,
    linkify: true,
    // Technical prose uses literal braces (`push {r4, lr}`); markdown-it-attrs
    // would eat them as boolean attributes and truncate headings.
    attrs: { disable: true },
    anchor: {
      // Python-Markdown's toc dedupes repeats as `机制_1`; keep the same suffix
      // so deep links written against the pre-VitePress site still resolve.
      slugifyWithState: (text: string, state: any) => {
        const base = slugify(text)
        const counts: Map<string, number> = (state.__bookAnchorCounts ??= new Map())
        const seen = counts.get(base) ?? 0
        counts.set(base, seen + 1)
        return seen === 0 ? base : `${base}_${seen}`
      },
    },
    config: (md) => bookMarkdown(md, { base: BASE, docsRoot, scenes }),
  },
  vue: {
    template: {
      compilerOptions: {
        isCustomElement: (tag: string) => tag === 'stick-scene',
      },
    },
  },
  transformHead({ pageData }) {
    // 404 不是可索引内容：不加 canonical，明确 noindex（VitePress 默认不带）。
    if (pageData.isNotFound) {
      return [['meta', { name: 'robots', content: 'noindex' }]]
    }
    const relative = pageData.relativePath.replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '.html')
    const url = `${SITE_URL}${relative}`
    const title = pageData.frontmatter.title
      ? `${pageData.frontmatter.title} · ${manifest.title}`
      : `${manifest.title}：${manifest.subtitle ?? ''}`
    return [
      ['link', { rel: 'canonical', href: url }],
      ['meta', { property: 'og:type', content: 'article' }],
      ['meta', { property: 'og:site_name', content: manifest.title }],
      ['meta', { property: 'og:title', content: title }],
      ['meta', { property: 'og:url', content: url }],
      ['meta', { name: 'twitter:card', content: 'summary' }],
    ]
  },
  themeConfig: {
    nav: buildNav(),
    sidebar: buildSidebar(),
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一章', next: '下一章' },
    darkModeSwitchLabel: '外观',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    lastUpdated: false,
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '没有找到结果',
            resetButtonTitle: '清除',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
        miniSearch: {
          options: {
            tokenize: cjkTokenize,
            processTerm: (term: string) => term.toLowerCase(),
          },
          searchOptions: {
            fuzzy: 0.2,
            prefix: true,
            boost: { title: 4, text: 2, headings: 3 },
          },
        },
      },
    },
  },
})