<script setup lang="ts">
import { withBase } from 'vitepress'
import manifest from '../../../manifest.json'

const parts = (manifest.parts as Array<{ id: string; title: string; goal?: string; chapters: Array<{ id: string; title: string; file: string }> }>)
  .filter((part) => part.chapters.length > 0)
const appendices = (manifest.appendices ?? []) as Array<{ id: string; title: string; file: string }>

function link(file: string): string {
  return withBase(`/${file.replace(/\.md$/, '')}.html`)
}
</script>

<template>
  <div class="book-index">
    <header class="book-index-head">
      <h1>{{ manifest.title }}</h1>
      <p class="book-subtitle">{{ manifest.subtitle }}</p>
      <p class="book-version">版本 {{ manifest.version }}</p>
    </header>
    <section v-for="part in parts" :key="part.id" class="book-index-part">
      <h2>{{ part.title }}</h2>
      <p v-if="part.goal">{{ part.goal }}</p>
      <ol>
        <li v-for="chapter in part.chapters" :key="chapter.id">
          <a :href="link(chapter.file)">{{ chapter.title }}</a>
        </li>
      </ol>
    </section>
    <section v-if="appendices.length" class="book-index-part">
      <h2>附录</h2>
      <ol>
        <li v-for="entry in appendices" :key="entry.id">
          <a :href="link(entry.file)">{{ entry.title }}</a>
        </li>
      </ol>
    </section>
  </div>
</template>