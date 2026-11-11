<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'
import { useData } from 'vitepress'
import { ref, onMounted, onUnmounted } from 'vue'
import AiNotice from './AiNotice.vue'
import ChapterCompass from './ChapterCompass.vue'
import McuHero from './McuHero.vue'
import McuFeatures from './McuFeatures.vue'
import McuCta from './McuCta.vue'
import McuFooter from './McuFooter.vue'

const { Layout } = DefaultTheme
const { page, isDark } = useData()
const isHome = page.value.frontmatter.layout === 'home'

const scrollProgress = ref(0)
const showTop = ref(false)

function updateScroll() {
  const h = document.documentElement
  const scrolled = h.scrollTop / (h.scrollHeight - h.clientHeight)
  scrollProgress.value = Math.min(100, Math.max(0, scrolled * 100))
  showTop.value = h.scrollTop > 480
}

function backToTop() {
  const smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  window.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' })
}

let sections: Element[] = []
let sectionObserver: IntersectionObserver | null = null

function toggleDarkWithCircle(event: MouseEvent) {
  const isAppearance = (event.target as Element)?.closest('.VPSwitchAppearance')
  if (!isAppearance) return

  const x = event.clientX
  const y = event.clientY
  const endRadius = Math.hypot(
    Math.max(x, innerWidth - x),
    Math.max(y, innerHeight - y)
  )

  if (!document.startViewTransition) {
    isDark.value = !isDark.value
    return
  }

  const transition = document.startViewTransition(() => {
    isDark.value = !isDark.value
  })

  transition.ready.then(() => {
    const clipPath = [
      `circle(0px at ${x}px ${y}px)`,
      `circle(${endRadius}px at ${x}px ${y}px)`,
    ]
    const isGoingDark = isDark.value
    document.documentElement.animate(
      { clipPath },
      {
        duration: 500,
        easing: 'ease-in-out',
        pseudoElement: isGoingDark
          ? '::view-transition-new(root)'
          : '::view-transition-old(root)',
      }
    )
  })
}

onMounted(() => {
  window.addEventListener('scroll', updateScroll, { passive: true })
  updateScroll()

  sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) e.target.classList.add('is-visible')
      })
    },
    { threshold: 0.1 }
  )

  sections = Array.from(document.querySelectorAll('.mcu-start, .mcu-map'))
  sections.forEach((s) => sectionObserver!.observe(s))

  document.addEventListener('click', toggleDarkWithCircle)
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateScroll)
  sectionObserver?.disconnect()
  document.removeEventListener('click', toggleDarkWithCircle)
})
</script>

<template>
  <Layout>
    <template #layout-top>
      <a class="mcu-skip-link" href="#VPContent">跳到正文</a>
      <div class="mcu-scroll-progress" :style="{ width: `${scrollProgress}%` }"></div>
      <Transition name="mcu-fade">
        <button
          v-if="showTop"
          class="mcu-back-top"
          type="button"
          aria-label="返回顶部"
          title="返回顶部"
          @click="backToTop"
        >↑</button>
      </Transition>
    </template>
    <template #home-hero-before v-if="isHome">
      <McuHero />
    </template>
    <template #home-features-before v-if="isHome">
      <McuFeatures />
    </template>
    <template #home-features-after v-if="isHome">
      <McuCta />
    </template>
    <template #doc-before>
      <ChapterCompass />
    </template>
    <template #doc-after>
      <AiNotice />
    </template>
    <template #layout-bottom>
      <McuFooter />
    </template>
  </Layout>
</template>

<style>
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}

::view-transition-old(root) {
  z-index: 1;
}

::view-transition-new(root) {
  z-index: 9999;
}

.dark::view-transition-old(root) {
  z-index: 9999;
}

.dark::view-transition-new(root) {
  z-index: 1;
}
</style>
