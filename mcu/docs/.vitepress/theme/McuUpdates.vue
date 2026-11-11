<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { withBase } from 'vitepress'
import updates from '../data/updates.json'

const visible = ref(false)
let observer: IntersectionObserver | null = null

const items = updates.items || []

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting) {
        visible.value = true
        observer?.disconnect()
      }
    },
    { threshold: 0.15 }
  )
  const el = document.querySelector('.mcu-updates')
  if (el) observer.observe(el)
})

onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div v-if="items.length" class="mcu-updates" :class="{ 'is-visible': visible }">
    <h2 class="mcu-updates__title">最近更新</h2>
    <p class="mcu-updates__sub">这一周，站点里哪些章节动了真格。</p>
    <ul class="mcu-updates__list">
      <li v-for="(item, i) in items" :key="item.route" class="mcu-updates__item" :style="{ '--i': i }">
        <time class="mcu-updates__date" :datetime="item.date">{{ item.date.slice(5) }}</time>
        <span class="mcu-updates__track">{{ item.track }}</span>
        <a class="mcu-updates__link" :href="withBase(item.route)">{{ item.title }}</a>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.mcu-updates {
  max-width: 800px;
  margin: 40px auto 0;
  padding: 0 24px;
}

.mcu-updates__title {
  font-size: 1.35em;
  font-weight: 700;
  margin: 0 0 4px;
  text-align: center;
  border-top: none;
  padding-top: 0;
  display: block;
}

.mcu-updates__title::after {
  content: none;
}

.mcu-updates__title::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--mcu-accent, #3eaf7c);
  margin-right: 10px;
  vertical-align: middle;
  animation: mcu-updates-pulse 2s ease-in-out infinite;
}

@keyframes mcu-updates-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.mcu-updates__sub {
  color: var(--vp-c-text-2);
  font-size: 0.9em;
  margin: 0 0 16px;
  text-align: center;
}

.mcu-updates__list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--vp-c-divider);
  border-radius: 16px;
  background: var(--vp-c-bg-soft);
  overflow: hidden;
}

.mcu-updates__item {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--vp-c-divider);
  opacity: 0;
  transform: translateY(6px);
  transition: opacity 0.4s ease, transform 0.4s ease;
  transition-delay: calc(var(--i) * 40ms);
}

.mcu-updates.is-visible .mcu-updates__item {
  opacity: 1;
  transform: none;
}

.mcu-updates__item:last-child {
  border-bottom: none;
}

.mcu-updates__date {
  flex: none;
  font-family: var(--vp-font-family-mono);
  font-size: 0.8em;
  color: var(--vp-c-text-3);
  min-width: 46px;
}

.mcu-updates__track {
  flex: none;
  font-size: 0.75em;
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--mcu-brand, #3451b2);
  background: var(--vp-c-default-soft);
  white-space: nowrap;
}

.mcu-updates__link {
  font-weight: 500;
  color: var(--vp-c-text-1);
  text-decoration: none;
  transition: color 0.2s ease;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcu-updates__link:hover {
  color: var(--mcu-brand, #3451b2);
  text-decoration: underline;
  text-underline-offset: 3px;
}

@media (max-width: 640px) {
  .mcu-updates__item {
    flex-wrap: wrap;
    gap: 6px 10px;
  }
  .mcu-updates__link {
    flex-basis: 100%;
    order: -1;
    white-space: normal;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mcu-updates__item {
    opacity: 1;
    transform: none;
    transition: none;
  }
  .mcu-updates__title::before {
    animation: none;
  }
}
</style>
