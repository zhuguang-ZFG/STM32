<script setup lang="ts">
import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
// 与整书同源的单一事实：mcu-book/manifest.json（分部、88 章罗盘、60 项来源）。
// 站点在这里只读展示；内容维护唯一入口仍是 mcu-book/manifest.json。
import manifest from '../../../mcu-book/manifest.json'

const { page } = useData()

const guide = computed(() => {
  const path = page.value.relativePath
  if (!path) return null
  return (manifest.chapter_guides as Record<string, any>)[path] ?? null
})

const partTitle = computed(() => {
  const path = page.value.relativePath
  if (!path) return ''
  const part = (manifest.parts as any[]).find((p) => p.files.includes(path))
  return part ? part.title : ''
})

const sourceTitle = (id: string) =>
  (manifest.sources as Record<string, any>)[id]?.title ?? id

const bibliographyUrl = withBase('/reference/bibliography.html')
</script>

<template>
  <aside v-if="guide" class="chapter-compass" aria-label="本章罗盘">
    <p class="compass-kicker">本章罗盘<span v-if="partTitle" class="compass-part">· {{ partTitle }}</span></p>
    <div class="compass-grid">
      <div class="compass-item">
        <strong>问题</strong>
        <p>{{ guide.question }}</p>
      </div>
      <div class="compass-item">
        <strong>交付</strong>
        <p>{{ guide.deliverable }}</p>
      </div>
      <div class="compass-item">
        <strong>边界</strong>
        <p>{{ guide.boundary }}</p>
      </div>
    </div>
    <p class="compass-sources">
      <strong>依据锚点</strong>
      <code
        v-for="id in guide.sources"
        :key="id"
        :title="sourceTitle(id)"
      >{{ id }}</code>
      <span class="compass-note">锚点条目详见<a :href="bibliographyUrl">参考文献</a>与整书附录 E</span>
    </p>
  </aside>
</template>

<style scoped>
.chapter-compass {
  margin: 0 0 1.5rem;
  padding: 1rem 1.2rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-left: 4px solid var(--vp-c-brand-1);
  border-radius: 10px;
}
.compass-kicker {
  margin: 0 0 .7rem;
  font-weight: 700;
  color: var(--vp-c-brand-1);
  letter-spacing: .06em;
}
.compass-part {
  color: var(--vp-c-text-2);
  font-weight: 500;
  font-size: .9em;
}
.compass-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .8rem;
}
.compass-item {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: .7rem .85rem;
}
.compass-item strong {
  color: var(--vp-c-brand-1);
  font-size: .88em;
}
.compass-item p {
  margin: .3rem 0 0;
  font-size: .9rem;
  line-height: 1.65;
  color: var(--vp-c-text-1);
}
.compass-sources {
  margin: .8rem 0 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .4rem;
  font-size: .85rem;
  color: var(--vp-c-text-2);
}
.compass-sources code {
  color: var(--vp-c-brand-1);
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 5px;
  padding: .05em .4em;
  cursor: help;
}
.compass-note {
  margin-left: auto;
  font-size: .82rem;
}
@media (max-width: 768px) {
  .compass-grid { grid-template-columns: minmax(0, 1fr); }
  .compass-note { margin-left: 0; }
}
</style>
