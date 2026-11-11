<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { withBase } from 'vitepress'
import data from '../data/progress.json'

// 数字来自 scripts/gen-progress.mjs（扫 docs/** 的 frontmatter）。
const totals = data.totals
const tracks = data.tracks
const readTime = Math.round(totals.minutes / 60)

// 入场动效：统计数字递增 + 轨道/章节卡片逐条淡入 + 进度条过渡。
// 尊重系统的"减少动效"偏好——命中时不做任何动画，直接停在最终态。
const reducedMotion = ref(false)
const started = ref(false)
const anim = reactive({
  chaptersDone: totals.chaptersDone,
  experimentsDone: totals.experimentsDone,
  animations: totals.animations,
  projects: totals.projects,
  hours: readTime,
})

const difficultyLabel = (level: number) => (level === 1 ? '入门' : level === 2 ? '进阶' : '硬核')
const landing = (track) => withBase(track.landing || `/${track.dir}/index.html`)

function runCountUp(dur = 800) {
  const targets = {
    chaptersDone: totals.chaptersDone,
    experimentsDone: totals.experimentsDone,
    animations: totals.animations,
    projects: totals.projects,
    hours: readTime,
  }
  const t0 = performance.now()
  const ease = (p: number) => 1 - Math.pow(1 - p, 3) // easeOutCubic
  const step = (t: number) => {
    const p = Math.min(1, (t - t0) / dur)
    const e = ease(p)
    for (const k of Object.keys(targets)) anim[k] = Math.round(targets[k] * e)
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

onMounted(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion.value = reduce.matches
  if (reduce.matches) {
    // 静止、不动画：直接落在最终态，别让数字"跑"。
    started.value = true
    return
  }
  // 地图出现在首屏下方，滚到可见区才播放一遍，而不是一进页面就闪。
  const el = document.querySelector('.mcu-map')
  if (!el) { started.value = true; runCountUp(); return }
  const io = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !started.value) {
      started.value = true
      runCount()
      io.disconnect()
    }
  }, { threshold: 0.15 })
  io.observe(el)
})
</script>

<template>
  <div class="mcu-map" :class="{ 'is-visible': started, 'is-reduced': reducedMotion }">
    <div class="mcu-map__stats">
      <div class="mcu-stat">
        <b>{{ anim.chaptersDone }}<i>/{{ totals.chapters }}</i></b>
        <span>成稿章节</span>
      </div>
      <div class="mcu-stat">
        <b>{{ anim.experimentsDone }}<i>/{{ totals.experiments }}</i></b>
        <span>实验文稿（非实测数）</span>
      </div>
      <div class="mcu-stat">
        <b>{{ anim.animations }}</b>
        <span>机制动画</span>
      </div>
      <div class="mcu-stat">
        <b>{{ anim.projects }}</b>
        <span>示例工程</span>
      </div>
      <div class="mcu-stat">
        <b>{{ anim.hours }}<i> 小时</i></b>
        <span>成稿内容通读</span>
      </div>
    </div>

    <div v-for="(track, ti) in tracks" :key="track.key" class="mcu-track" :style="{ '--d': ti * 0.06 + 's' }">
      <div class="mcu-track__head">
        <a class="mcu-track__name" :href="landing(track)">{{ track.name }}</a>
        <span class="mcu-track__count">{{ track.done }}/{{ track.total }} 成稿 · {{ track.built }} 已建档</span>
        <span class="mcu-track__bar">
          <i :style="{ width: (started ? (track.total ? (track.done / track.total) * 100 : 0) : 0) + '%' }" />
        </span>
      </div>
      <ul class="mcu-chips">
        <li v-for="(ch, ci) in track.chapters" :key="ch.id" :style="{ '--d': (ci * 0.035 + 0.02) + 's' }">
          <component :is="ch.route ? 'a' : 'span'"
            class="mcu-chip"
            :class="ch.status === 'done' ? 'is-done' : 'is-building'"
            :href="ch.route ? withBase(ch.route) : undefined"
            :title="
              ch.status === 'done'
                ? `${difficultyLabel(ch.difficulty)} · 约 ${ch.minutes} 分钟`
                : '骨架页：结构与目标已定，正文待成稿'
            "
          >
            {{ ch.title }}
            <em v-if="ch.status === 'done'">{{ difficultyLabel(ch.difficulty) }} {{ ch.minutes }}′</em>
            <em v-else>{{ ch.route ? '建设中' : '规划中' }}</em>
          </component>
        </li>
      </ul>
    </div>
  </div>
</template>