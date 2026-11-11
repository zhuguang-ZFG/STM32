<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  chapter: { type: String, required: true },
})

const quizMap = {
  's02-rcc-clock': () => import('../data/quizzes/s02-rcc-clock.json'),
  's03-gpio': () => import('../data/quizzes/s03-gpio.json'),
  's04-nvic': () => import('../data/quizzes/s04-nvic.json'),
  's06-tim': () => import('../data/quizzes/s06-tim.json'),
  's07-usart': () => import('../data/quizzes/s07-usart.json'),
  's08-dma': () => import('../data/quizzes/s08-dma.json'),
  's09-adc': () => import('../data/quizzes/s09-adc.json'),
  's11-i2c': () => import('../data/quizzes/s11-i2c.json'),
  's12-spi': () => import('../data/quizzes/s12-spi.json'),
  's14-pwr': () => import('../data/quizzes/s14-pwr.json'),
  'f4-queue': () => import('../data/quizzes/f4-queue.json'),
  'f7-heap': () => import('../data/quizzes/f7-heap.json'),
  'c03-volatile': () => import('../data/quizzes/c03-volatile.json'),
}

const loaded = ref(null)
const error = ref(false)

if (quizMap[props.chapter]) {
  quizMap[props.chapter]().then(m => {
    loaded.value = m.default || m
  }).catch(() => {
    error.value = true
  })
} else {
  error.value = true
}

const questions = computed(() => loaded.value?.questions || [])
const title = computed(() => loaded.value?.title || '短自测')

const revealed = ref(new Set())
const score = ref(0)
const attempted = ref(new Set())

function toggle(idx) {
  if (revealed.value.has(idx)) {
    revealed.value.delete(idx)
  } else {
    revealed.value.add(idx)
  }
}

function markAttempted(idx, correct) {
  if (!attempted.value.has(idx)) {
    attempted.value.add(idx)
    if (correct) score.value++
  }
}

const progress = computed(() => {
  const total = questions.value.length
  const done = revealed.value.size
  return { total, done, pct: total ? Math.round(done / total * 100) : 0 }
})

function reset() {
  revealed.value.clear()
  attempted.value.clear()
  score.value = 0
}
</script>

<template>
  <div class="quiz-bank" v-if="questions.length">
    <div class="qb-header">
      <span class="qb-title">{{ title }}</span>
      <span class="qb-progress">{{ progress.done }}/{{ progress.total }}</span>
      <button class="qb-reset" @click="reset" v-if="progress.done > 0">重置</button>
    </div>

    <div class="qb-list">
      <div
        v-for="(q, i) in questions" :key="i"
        :class="['qb-item', { revealed: revealed.has(i) }]"
      >
        <div class="qb-q">
          <span class="qb-num">{{ i + 1 }}</span>
          <span class="qb-text">{{ q.q }}</span>
        </div>

        <div class="qb-options" v-if="q.options">
          <button
            v-for="(opt, oi) in q.options" :key="oi"
            :class="['qb-opt', {
              selected: q.answer === oi,
              wrong: attempted.has(i) && q._selected === oi && q.answer !== oi,
              correct: revealed.has(i) && q.answer === oi,
            }]"
            @click="q._selected = oi"
            :disabled="revealed.has(i)"
          >{{ opt }}</button>
        </div>

        <button
          class="qb-reveal"
          @click="markAttempted(i, q._selected === q.answer); toggle(i)"
        >
          {{ revealed.has(i) ? '收起答案' : '查看答案' }}
        </button>

        <div class="qb-answer" v-if="revealed.has(i)">
          <div class="qb-answer-label">
            <template v-if="q.options">
              <span v-if="q._selected === q.answer" class="qb-correct">✓ 正确</span>
              <span v-else class="qb-wrong">✗ 正确答案：{{ q.options[q.answer] }}</span>
            </template>
          </div>
          <p class="qb-explain">{{ q.a }}</p>
        </div>
      </div>
    </div>

    <div class="qb-score" v-if="progress.done === progress.total && progress.total > 0">
      <span>得分：{{ score }}/{{ progress.total }}</span>
      <span v-if="score === progress.total" class="qb-perfect">全部正确！</span>
    </div>
  </div>

  <div class="quiz-bank qb-error" v-else-if="error">
    <p>暂无自测题数据（{{ props.chapter }}）</p>
  </div>
</template>

<style scoped>
.quiz-bank {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 16px 20px;
  background: var(--vp-c-bg-soft);
  margin: 1.5em 0;
}
.qb-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--vp-c-divider);
}
.qb-title {
  font-weight: 700;
  font-size: 1em;
  color: var(--vp-c-brand-1);
}
.qb-progress {
  font-size: 0.8em;
  color: var(--vp-c-text-2);
  margin-left: auto;
}
.qb-reset {
  font-size: 0.75em;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  cursor: pointer;
  color: var(--vp-c-text-2);
}
.qb-reset:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}
.qb-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.qb-item {
  padding: 12px;
  border-radius: 8px;
  background: var(--vp-c-bg);
  border: 1px solid transparent;
  transition: border-color 0.2s;
}
.qb-item.revealed {
  border-color: var(--vp-c-brand-soft);
}
.qb-q {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.qb-num {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--vp-c-brand-1);
  color: #fff;
  font-size: 0.75em;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.qb-text {
  font-size: 0.9em;
  line-height: 1.5;
  padding-top: 2px;
}
.qb-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}
.qb-opt {
  text-align: left;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  cursor: pointer;
  font-size: 0.85em;
  transition: all 0.15s;
}
.qb-opt:hover:not(:disabled) {
  border-color: var(--vp-c-brand-1);
}
.qb-opt.selected {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
}
.qb-opt.correct {
  border-color: #1a7f37;
  background: #dafbe1;
}
.qb-opt.wrong {
  border-color: #cf222e;
  background: #ffebe9;
}
:root.dark .qb-opt.correct {
  border-color: #3fb950;
  background: #0d1117;
}
:root.dark .qb-opt.wrong {
  border-color: #f85149;
  background: #1c1206;
}
.qb-opt:disabled {
  cursor: default;
}
.qb-reveal {
  font-size: 0.8em;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid var(--vp-c-brand-1);
  background: transparent;
  color: var(--vp-c-brand-1);
  cursor: pointer;
  transition: all 0.15s;
}
.qb-reveal:hover {
  background: var(--vp-c-brand-1);
  color: #fff;
}
.qb-answer {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--vp-c-brand-soft);
  font-size: 0.85em;
  line-height: 1.6;
}
.qb-answer-label {
  margin-bottom: 4px;
}
.qb-correct {
  color: #1a7f37;
  font-weight: 600;
}
.qb-wrong {
  color: #cf222e;
  font-weight: 600;
}
:root.dark .qb-correct { color: #3fb950; }
:root.dark .qb-wrong { color: #f85149; }
.qb-explain {
  margin: 0;
  color: var(--vp-c-text-1);
}
.qb-score {
  margin-top: 12px;
  padding: 10px;
  text-align: center;
  font-weight: 700;
  font-size: 1em;
  color: var(--vp-c-brand-1);
  border-top: 1px solid var(--vp-c-divider);
}
.qb-perfect {
  margin-left: 8px;
  color: #1a7f37;
}
:root.dark .qb-perfect { color: #3fb950; }
.qb-error {
  text-align: center;
  color: var(--vp-c-text-3);
  font-size: 0.85em;
}
</style>
