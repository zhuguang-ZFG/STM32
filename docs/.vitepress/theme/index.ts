import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { useRoute } from 'vitepress'
import { nextTick, onMounted, watch } from 'vue'
import './style.css'
import QuizBank from './components/QuizBank.vue'
import StickScene from './components/StickScene.vue'
import BookIndex from './components/BookIndex.vue'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('QuizBank', QuizBank)
    app.component('StickScene', StickScene)
    app.component('BookIndex', BookIndex)
  },
  setup() {
    const route = useRoute()
    if (typeof window !== 'undefined') {
      const enhanceReferenceTables = () => {
        document.querySelectorAll<HTMLElement>('.reference-index .table-scroll').forEach((table) => {
          // A wide reference table is a deliberate horizontal viewport. Making
          // it a focusable region gives keyboard readers the same affordance as
          // a touch reader swiping the table.
          table.tabIndex = 0
          table.setAttribute('role', 'region')
          if (!table.getAttribute('aria-label')) {
            const heading = table.previousElementSibling
            const label = heading?.matches('h2,h3,h4,h5,h6')
              ? heading.textContent?.replace(/#$/, '').trim()
              : ''
            table.setAttribute('aria-label', `${label ? `${label}：` : ''}参考表，可横向滚动`)
          }
        })
      }

      onMounted(enhanceReferenceTables)
      watch(() => route.path, () => nextTick(enhanceReferenceTables), { flush: 'post' })

      let printDetailsState: Map<HTMLDetailsElement, boolean> | null = null
      // Printing expands every folded answer; the PDF/EPUB pipelines do the
      // same, so a reader printing the site never gets truncated explanations.
      window.addEventListener('beforeprint', () => {
        if (printDetailsState) return
        printDetailsState = new Map()
        document.querySelectorAll<HTMLDetailsElement>('details').forEach((item) => {
          printDetailsState?.set(item, item.open)
          item.open = true
        })
      })
      window.addEventListener('afterprint', () => {
        if (!printDetailsState) return
        printDetailsState.forEach((open, item) => { item.open = open })
        printDetailsState = null
      })
    }
  },
} satisfies Theme
