import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
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
    if (typeof window !== 'undefined') {
      // Printing expands every folded answer; the PDF/EPUB pipelines do the
      // same, so a reader printing the site never gets truncated explanations.
      window.addEventListener('beforeprint', () => {
        document.querySelectorAll('details').forEach((item) => {
          item.open = true
        })
      })
    }
  },
} satisfies Theme