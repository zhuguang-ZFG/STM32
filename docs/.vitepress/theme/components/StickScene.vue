<script setup lang="ts">
import { computed } from 'vue'
import scenes from '../../data/scenes.json'

const props = defineProps<{ scene: string }>()
const meta = (scenes as Record<string, { label: string; caption: string; fallback: string }>)[props.scene]
if (!meta) throw new Error(`unknown stick-scene id: ${props.scene}`)

const base = import.meta.env.BASE_URL

function escapeAttr(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
}

// The canvas widget is a native custom element (docs/public/scenes/stick.js).
// Injecting it through v-html keeps the exact DOM the print/EPUB parity tests
// know, including the <noscript> fallback plate.
const inner = computed(
  () =>
    `<stick-scene scene="${props.scene}" play="view" no-font aria-label="${escapeAttr(meta.label)}" style="height:240px;max-width:560px"></stick-scene>` +
    `<noscript><img src="${base}${meta.fallback.replace(/^\//, '')}" alt="${escapeAttr(meta.caption)}" loading="lazy" decoding="async"></noscript>` +
    `<figcaption>${escapeAttr(meta.caption)}</figcaption>`,
)

const loaded = new Set<string>()
let runtime: Promise<void> | null = null

function addScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = src
    script.async = false
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`failed to load ${src}`))
    document.body.appendChild(script)
  })
}

async function loadScene(id: string) {
  if (typeof window === 'undefined') return
  if (!runtime) runtime = addScript(`${base}scenes/stick.js`)
  await runtime
  if (loaded.has(id)) return
  loaded.add(id)
  await addScript(`${base}scenes/${id}.js`)
}

loadScene(props.scene).catch((error) => console.error(error))
</script>

<template>
  <figure class="book-figure book-scene" v-html="inner" />
</template>