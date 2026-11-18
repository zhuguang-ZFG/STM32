<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ chapter: string }>()

const quizzes = import.meta.glob('../../data/quizzes/*.json', { eager: true }) as Record<
  string,
  { default?: unknown }
>

const data = computed(() => {
  const entry = Object.entries(quizzes).find(([file]) => file.endsWith(`/${props.chapter}.json`))
  if (!entry) throw new Error(`unknown quiz: ${props.chapter}`)
  const value = entry[1] as { default?: Record<string, unknown> }
  return (value.default ?? value) as {
    title: string
    questions: Array<{ q: string; options: string[]; answer: number; a: string }>
  }
})
</script>

<template>
  <section class="quiz">
    <h3>{{ data.title }}</h3>
    <template v-for="(item, index) in data.questions" :key="index">
      <p class="quiz-q"><strong>Q{{ index + 1 }}.</strong> {{ item.q }}</p>
      <ol class="quiz-options">
        <li v-for="(option, optionIndex) in item.options" :key="optionIndex">{{ option }}</li>
      </ol>
      <details class="quiz-answer">
        <summary>答案与解析</summary>
        <p>{{ item.a }}</p>
      </details>
    </template>
  </section>
</template>