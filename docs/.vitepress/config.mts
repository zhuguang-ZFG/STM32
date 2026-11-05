import { defineConfig } from 'vitepress'
import { animDuration, decorateAnim, readAnim } from './anim-decorate.mjs'
import { codeLanguages } from './code-languages.mjs'
import { renderSearch } from '../../scripts/search-render.mjs'
import { tokenizeForSearch } from '../../scripts/search-tokenize.mjs'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HOST = 'https://zhuguang-zfg.github.io'
const BASE = '/mcu/'
const SITE_DESC = '寄存器级 STM32F407 × ESP32-S3 深度教学：C 语言精髓 · RTOS 双精讲 · 全程实物实验'
const OG_IMAGE = `${HOST}${BASE}og-cover.png`

// 页面相对路径 → 规范 URL：index 归一为目录，与 VitePress 产物路径一致。
const pageUrl = (page: string) => {
  let p = page.replace(/\.md$/, '.html')
  if (p === 'index.html') p = ''
  else p = p.replace(/\/index\.html$/, '/')
  return `${HOST}${BASE}${p}`
}
const ART_DIR = join(
  dirname(fileURLToPath(import.meta.url)), '..', '..',
  'mcu-book', 'book', 'assets', 'chapter-art',
)

// 章首题花上网：与印前 build_html.py chapter_art_html 同一资产、同一约定——
// 相对路径 slug（stm32/06-tim.md → stm32-06-tim）存在即内联、缺失静默跳过、
// 滤镜硬门（feTurbulence/<filter 是印前光栅化源头，web 同口径拒绝）。
// 内联而非 <img>：SVG 里的 var(--cover-ink) 墨色令牌要能吃深浅两套主题。
const chapterArt = (rel?: string): string => {
  if (!rel) return ''
  const slug = rel.replace(/\.md$/, '').replace(/\//g, '-')
  let svg: string
  try {
    svg = readFileSync(join(ART_DIR, `${slug}.svg`), 'utf-8')
  } catch {
    return ''
  }
  if (svg.includes('feTurbulence') || svg.includes('<filter')) {
    throw new Error(`章首题图必须纯矢量（含滤镜）：${slug}.svg`)
  }
  return `<div class="chapter-art">${svg}</div>\n`
}

export default defineConfig({
  base: BASE,
  title: '通往单片机之路',
  description: SITE_DESC,
  lang: 'zh-CN',
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: `${BASE}favicon.svg` }],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { property: 'og:site_name', content: '通往单片机之路' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }],
    ['meta', { property: 'og:image', content: OG_IMAGE }],
    ['meta', { property: 'og:image:width', content: '1200' }],
    ['meta', { property: 'og:image:height', content: '630' }],
    ['meta', { property: 'og:image:alt', content: '通往单片机之路：寄存器级 STM32F407 × ESP32-S3 深度教学' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:image', content: OG_IMAGE }],
    // 水合前的看门人：SVG 是 SSR 直出的，SMIL 在 document load 一到就全体开跑，
    // 比 Vue 接管（AnimFigure 的 IntersectionObserver）早得多。演示中心 69 张一起跑，
    // 慢机器上水合本身都要排队等帧。这里在 DOMContentLoaded（早于 load）先把
    // 视口外（含 200px 预载带，与组件同一口径）的图停住，组件接管后按可见性续播。
    ['script', {}, `document.addEventListener('DOMContentLoaded',function(){var m=200,h=innerHeight;document.querySelectorAll('.anim-figure__stage svg').forEach(function(s){var r=s.getBoundingClientRect();if((r.bottom<-m||r.top>h+m)&&s.pauseAnimations)s.pauseAnimations()})})`],
  ],
  // hostname 必须含 base 且以 / 结尾：VitePress 生成的是相对路径，靠它做相对解析。
  sitemap: { hostname: `${HOST}${BASE}` },
  // 每页分享卡与规范链接：链接被分享/收录时给出标题、描述与配图，而不是一张白板。
  transformHead({ page, title, description }) {
    const url = pageUrl(page)
    const desc = description || SITE_DESC
    return [
      ['link', { rel: 'canonical', href: url }],
      ['meta', { property: 'og:type', content: page === 'index.md' ? 'website' : 'article' }],
      ['meta', { property: 'og:title', content: title }],
      ['meta', { property: 'og:description', content: desc }],
      ['meta', { property: 'og:url', content: url }],
      ['meta', { name: 'twitter:title', content: title }],
      ['meta', { name: 'twitter:description', content: desc }],
    ]
  },
  ignoreDeadLinks: false,
  markdown: {
    languages: codeLanguages,
    // 作者照旧写 ![图注](/anim/x.svg)；这里把 SVG 原文内联进页面 chunk，
    // 交给 AnimFigure 上图注、播放控件与深浅主题配色（细节见 anim-decorate.mjs）。
    config(md: any) {
      const emit = (name: string, caption: string) => {
        const raw = readAnim(name)
        const dur = animDuration(raw)
        // 转义成属性字符串交给 v-html：让 Vue 去 diff 整棵 SVG 子树只会带来 hydration 抖动，
        // 而这些图是构建期定死的静态内容。
        const markup = decorateAnim(raw, name)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
        const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;')
        const attrs = [caption && `caption="${esc(caption)}"`, dur && `dur="${dur}"`, `markup="${markup}"`]
        return `<AnimFigure name="${name}" ${attrs.filter(Boolean).join(' ')} />`
      }

      // 独占一行的动画图必须从 <p> 里拿出来：figure/button 待在段落里会被浏览器
      // 解析器挪出去，SSR 与客户端结构对不上，Vue 就报 hydration mismatch。
      md.core.ruler.after('inline', 'anim-figure-block', (state: any) => {
        const tokens = state.tokens
        for (let i = 0; i < tokens.length - 2; i++) {
          if (tokens[i].type !== 'paragraph_open' || tokens[i + 2].type !== 'paragraph_close') continue
          const inline = tokens[i + 1]
          if (inline.type !== 'inline' || inline.children?.length !== 1) continue
          const child = inline.children[0]
          if (child.type !== 'image') continue
          const match = /^\/anim\/([\w-]+)\.svg$/.exec(child.attrGet('src') || '')
          if (!match) continue
          const block = new state.Token('html_block', '', 0)
          block.content = emit(match[1], child.content || child.attrGet('alt') || '') + '\n'
          block.map = tokens[i].map
          tokens.splice(i, 3, block)
          i--
        }
      })
      // 章首题花：插在 H1 之后，镜像印前「章号/标题 → 题花」的相邻关系
      // （web 端罗盘住在 doc-before 槽、位于标题上方，属既有布局，不在此动）。
      md.core.ruler.after('anim-figure-block', 'chapter-art', (state: any) => {
        const rel = state.env?.relativePath || state.env?.path
        const html = chapterArt(typeof rel === 'string' ? rel : '')
        if (!html) return
        const block = new state.Token('html_block', '', 0)
        block.content = html
        const h1Close = state.tokens.findIndex(
          (t: any) => t.type === 'heading_close' && t.tag === 'h1',
        )
        state.tokens.splice(h1Close >= 0 ? h1Close + 1 : 0, 0, block)
      })
    },
  },
  themeConfig: {
    search: {
      provider: 'local',
      options: {
        _render: renderSearch,
        // 中文分词：默认分词器把整段中文当 1 个 token，只有段首词能被 prefix 命中
        // （实测搜「寄存器」「总线」「外设」全部 0 结果）。两端必须共用同一函数。
        miniSearch: { options: { tokenize: tokenizeForSearch } },
        translations: {
          button: { buttonText: '搜索', resetButtonTitle: '清空搜索' },
          noResultsText: '没有找到相关段落——换个说法再试，名词类问题去「术语速查」页查。',
        },
      },
    },
    nav: [
      { text: '导读', link: '/guide/' },
      { text: 'C 精髓', link: '/c/' },
      { text: '构建运行', link: '/build/' },
      { text: 'STM32', link: '/stm32/' },
      { text: 'RTOS', link: '/rtos/' },
      { text: 'ESP32', link: '/esp32/' },
      { text: 'GD32', link: '/gd32/' },
      { text: '实验', link: '/lab/' },
      { text: '综合项目', link: '/projects/' },
      { text: 'AI 辅助', link: '/ai/' },
      { text: '动画', link: '/animations' },
      { text: '学习路径', link: '/learning-path' },
      {
        text: '资料',
        items: [
          { text: '术语速查', link: '/reference/glossary' },
          { text: '常见问题 FAQ', link: '/reference/faq' },
          { text: '参考文献', link: '/reference/bibliography' },
          { text: '整书离线版', link: '/reference/book' },
          { text: '更新日志', link: '/reference/changelog' },
          { text: '关于我们与致谢', link: '/reference/about' },
          { text: '视觉增强示例', link: '/visual-enhancements' },
          { text: '视频资源', link: '/video/c2-pointer-storyboard' },
          { text: '硬件实测计划', link: '/hardware-test-plan' },
        ],
      },
    ],
    sidebar: {
      '/projects/': [{ text:'综合项目', items:[{text:'导览',link:'/projects/'},{text:'J1 F407记录器',link:'/projects/01-f407-logger'},{text:'J2 S3记录器',link:'/projects/02-s3-logger'}] }],
      '/ai/': [{ text:'AI 辅助开发', items:[{text:'导览',link:'/ai/'},{text:'A0 结对工程师',link:'/ai/00-pair-not-ghost'},{text:'A1 提示词模式',link:'/ai/01-prompt-patterns'},{text:'A2 手册对账',link:'/ai/02-manual-reconciliation'},{text:'A3 工具流',link:'/ai/03-toolflow-mcp'},{text:'A4 幻觉防御',link:'/ai/04-hallucination-defense'},{text:'A5 生产线自证',link:'/ai/05-this-book-pipeline'}] }],
      '/guide/': [
        {
          text: '导读',
          items: [
            { text: '这条路怎么走', link: '/guide/' },
            { text: '实物装备清单', link: '/guide/hardware' },
            { text: '手册地图', link: '/guide/manuals' },
            { text: '上板验证与回填指南', link: '/guide/verify-on-hardware' },
          ],
        },
      ],
      '/c/': [
        { text: 'C8 串口协议：从字节流到可恢复的消息', link: '/c/08-framed-protocol' },
        {
          text: 'C 语言精髓',
          items: [
            { text: '导览', link: '/c/' },
            { text: 'C0 为什么嵌入式 C 是另一种 C', link: '/c/00-c-in-mcu' },
            { text: 'C1 内存模型', link: '/c/01-memory-model' },
            { text: 'C2 指针', link: '/c/02-pointer' },
            { text: 'C3 volatile', link: '/c/03-volatile' },
            { text: 'C4 结构体与 ABI', link: '/c/04-struct-abi' },
            { text: 'C5 函数指针与状态机', link: '/c/05-func-pointer' },
            { text: 'C6 调用约定与栈帧', link: '/c/06-abi-stack' },
            { text: 'C7 UB 与 MISRA-C', link: '/c/07-ub-misra' },
          ],
        },
      ],
      '/build/': [
        {
          text: '构建与运行全过程',
          items: [
            { text: '导览', link: '/build/' },
            { text: 'B0 工具链全景', link: '/build/00-toolchain' },
            { text: 'B1 四步构建', link: '/build/01-four-steps' },
            { text: 'B2 ELF 解剖', link: '/build/02-elf' },
            { text: 'B3 链接脚本', link: '/build/03-linker-script' },
            { text: 'B4 启动过程', link: '/build/04-startup' },
            { text: 'B5 map 与体积', link: '/build/05-map-size' },
            { text: 'B6 烧录与调试', link: '/build/06-flash-debug' },
            { text: 'B7 构建系统', link: '/build/07-build-system' },
          ],
        },
      ],
      '/stm32/': [
        { text: 'S17 看门狗：任务失去进展之后', link: '/stm32/17-watchdog-reset' },
        {
          text: 'STM32F407 寄存器主线',
          items: [
            { text: '导览', link: '/stm32/' },
            { text: 'S0 环境搭建', link: '/stm32/00-env' },
            { text: 'S1 架构总览', link: '/stm32/01-arch' },
            { text: 'S2 RCC 时钟树', link: '/stm32/02-rcc-clock' },
            { text: 'S3 GPIO', link: '/stm32/03-gpio' },
            { text: 'S4 NVIC 与 EXTI', link: '/stm32/04-nvic-exti' },
            { text: 'S5 SysTick', link: '/stm32/05-systick' },
            { text: 'S6 定时器 TIM', link: '/stm32/06-tim' },
            { text: 'S7 USART', link: '/stm32/07-usart' },
            { text: 'S8 DMA', link: '/stm32/08-dma' },
            { text: 'S9 ADC', link: '/stm32/09-adc' },
            { text: 'S10 DAC', link: '/stm32/10-dac' },
            { text: 'S11 I2C', link: '/stm32/11-i2c' },
            { text: 'S12 SPI', link: '/stm32/12-spi' },
            { text: 'S13 内部 Flash 与 IAP', link: '/stm32/13-flash-iap' },
            { text: 'S14 低功耗', link: '/stm32/14-pwr' },
            { text: 'S15 SPL 库解剖', link: '/stm32/15-spl-anatomy' },
            { text: 'S16 HardFault 与排错', link: '/stm32/16-debug-hardfault' },
          ],
        },
      ],
      '/rtos/': [
        {
          text: 'RTOS 双精讲',
          items: [
            { text: '导览', link: '/rtos/' },
          ],
        },
        {
          text: 'FreeRTOS 精讲',
          collapsed: false,
          items: [
            { text: 'F0 为什么需要 RTOS', link: '/rtos/freertos/00-why-rtos' },
            { text: 'F1 任务与 TCB', link: '/rtos/freertos/01-task-tcb' },
            { text: 'F2 上下文切换', link: '/rtos/freertos/02-context-switch' },
            { text: 'F3 调度器', link: '/rtos/freertos/03-scheduler' },
            { text: 'F4 队列', link: '/rtos/freertos/04-queue' },
            { text: 'F5 信号量与互斥量', link: '/rtos/freertos/05-sem-mutex' },
            { text: 'F6 通知/事件/软件定时器', link: '/rtos/freertos/06-notify-event-timer' },
            { text: 'F7 内存管理', link: '/rtos/freertos/07-heap' },
            { text: 'F8 移植到霸天虎', link: '/rtos/freertos/08-port-f407' },
          ],
        },
        {
          text: 'RT-Thread 精讲',
          collapsed: false,
          items: [
            { text: 'R0 架构与对象模型', link: '/rtos/rtthread/00-arch' },
            { text: 'R1 线程与调度', link: '/rtos/rtthread/01-thread-sched' },
            { text: 'R2 IPC 全家桶', link: '/rtos/rtthread/02-ipc' },
            { text: 'R3 内存管理', link: '/rtos/rtthread/03-mem' },
            { text: 'R4 设备框架', link: '/rtos/rtthread/04-device' },
            { text: 'R5 finsh 控制台', link: '/rtos/rtthread/05-finsh' },
            { text: 'R6 Env 与 menuconfig', link: '/rtos/rtthread/06-env-menuconfig' },
            { text: 'R7 移植到霸天虎', link: '/rtos/rtthread/07-port-f407' },
          ],
        },
        {
          text: '对照与选型',
          items: [
            { text: '对比 0 双实现对照', link: '/rtos/compare/00-side-by-side' },
            { text: '对比 1 选型决策树', link: '/rtos/compare/01-choose' },
          ],
        },
      ],
      '/esp32/': [
        { text: 'P13 看门狗与健康监督：不要喂反了', link: '/esp32/13-watchdog-health' },
        {
          text: 'ESP32-S3 + ESP-IDF',
          items: [
            { text: '导览', link: '/esp32/' },
            { text: 'P0 环境搭建', link: '/esp32/00-env' },
            { text: 'P1 架构与启动', link: '/esp32/01-arch-boot' },
            { text: 'P2 GPIO 与引脚矩阵', link: '/esp32/02-gpio-matrix' },
            { text: 'P3 IDF 工程解剖', link: '/esp32/03-idf-anatomy' },
            { text: 'P4 中断与双核', link: '/esp32/04-irq-dualcore' },
            { text: 'P5 UART 驱动解析', link: '/esp32/05-uart-driver' },
            { text: 'P6 SPI/I2C 驱动框架', link: '/esp32/06-spi-i2c-driver' },
            { text: 'P7 定时器与 LEDC', link: '/esp32/07-timer-ledc' },
            { text: 'P8 Wi-Fi 精髓', link: '/esp32/08-wifi' },
            { text: 'P9 蓝牙与 ESP-NOW', link: '/esp32/09-bt-espnow' },
            { text: 'P10 Flash/分区/OTA', link: '/esp32/10-flash-nvs-ota' },
            { text: 'P11 低功耗', link: '/esp32/11-lowpower' },
            { text: 'P12 音频链路', link: '/esp32/12-audio-path' },
          ],
        },
      ],
      '/gd32/': [
        {
          text: 'GD32 双系路线',
          items: [
            { text: '导览（G 篇 ARM / V 篇 RISC-V）', link: '/gd32/' },
          ],
        },
        {
          text: 'G 篇 GD32F4xx（Cortex-M4）',
          collapsed: false,
          items: [
            { text: 'G0 环境与工具链', link: '/gd32/00-env' },
            { text: 'G1 RCU 时钟树', link: '/gd32/01-rcu-clock' },
            { text: 'G2 GPIO 与 AF 复用', link: '/gd32/02-gpio-af' },
            { text: 'G3 USART 增强点', link: '/gd32/03-usart' },
            { text: 'G4 外设差异', link: '/gd32/04-periph-diff' },
          ],
        },
        {
          text: 'V 篇 GD32VF103（RISC-V）',
          collapsed: false,
          items: [
            { text: 'V0 RISC-V 工具链与启动', link: '/gd32/05-riscv-toolchain' },
            { text: 'V1 Bumblebee 内核与 CLIC', link: '/gd32/06-clic-irq' },
            { text: 'V2 RCU 与 108MHz', link: '/gd32/07-rcu-108m' },
            { text: 'V3 MTIME 与裸机延时', link: '/gd32/08-mtime-delay' },
            { text: 'V4 GPIO 最小系统', link: '/gd32/09-gpio-minimal' },
          ],
        },
      ],
      '/lab/': [
        {
          text: '实物实验中心',
          items: [
            { text: '实验总览', link: '/lab/' },
            { text: '实验模板', link: '/lab/template' },
            { text: 'E01 点亮 RGB 红灯', link: '/lab/e01-blink' },
            { text: 'E02 抓 UART 帧', link: '/lab/e02-logic-uart' },
            { text: 'E03 示波器看 PWM', link: '/lab/e03-scope-pwm' },
            { text: 'E04 优先级反转复现', link: '/lab/e04-priority-inversion' },
            { text: 'E05 I2C 抓包读 EEPROM', link: '/lab/e05-i2c-eeprom' },
            { text: 'E06 低功耗电流实测', link: '/lab/e06-lowpower-current' },
            { text: 'E07 S3 姿态传感器', link: '/lab/e07-qmi8658' },
            { text: 'E08 S3 音频放音', link: '/lab/e08-audio-play' },
          ],
        },
      ],
      '/reference/': [
        {
          text: '资料',
          items: [
            { text: '术语速查', link: '/reference/glossary' },
            { text: '常见问题 FAQ', link: '/reference/faq' },
            { text: '参考文献', link: '/reference/bibliography' },
            { text: '整书离线版', link: '/reference/book' },
            { text: '更新日志', link: '/reference/changelog' },
            { text: '发布摘要 · 2026-10-10', link: '/reference/releases/2026-10-10' },
            { text: '发布摘要 · 2026-10-10（第二次）', link: '/reference/releases/2026-10-10-2' },
            { text: '关于我们与致谢', link: '/reference/about' },
          ],
        },
      ],
      '/video/': [
        {
          text: '视频资源',
          items: [
            { text: 'C2 指针分镜脚本', link: '/video/c2-pointer-storyboard' },
            { text: 'F3 调度器分镜脚本', link: '/video/f3-scheduler-storyboard' },
          ],
        },
      ],
      '/hardware-test-plan.md': [
        {
          text: '硬件实测计划',
          items: [
            { text: '10 项 pending 验证与实测流程', link: '/hardware-test-plan' },
          ],
        },
      ],
      '/lab/reports/': [
        {
          text: '硬件实测报告',
          items: [
            { text: '报告目录与使用指南', link: '/lab/reports/README' },
            { text: '装备清单与采购指南', link: '/lab/reports/equipment-checklist' },
            { text: 'GDB 调试速查表', link: '/lab/reports/gdb-cheat-sheet' },
            { text: 'GDB 截图采集指南', link: '/lab/reports/gdb-screenshot-guide' },
            { text: 'E01 实测报告模板', link: '/lab/reports/e01-test-report' },
            { text: 'J1 实测报告模板', link: '/lab/reports/j1-test-report' },
            { text: '首轮实测报告模板', link: '/lab/reports/first-round-test-report' },
          ],
        },
      ],
    },
    socialLinks: [{ icon: 'github', link: 'https://github.com/zhuguang-ZFG/mcu' }],
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    editLink: { pattern: 'https://github.com/zhuguang-ZFG/mcu/edit/main/docs/:path', text: '在 GitHub 上编辑此页' },
    lastUpdated: { text: '最后更新' },
  },
})
