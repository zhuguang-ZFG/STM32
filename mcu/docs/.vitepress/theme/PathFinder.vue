<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { withBase } from 'vitepress'

const paths = [
  {
    emoji: '🌱',
    who: '零基础，板子刚到手',
    color: '#3eaf7c',
    steps: [
      { label: 'S0 环境搭建', link: '/stm32/00-env.md', desc: '点亮第一盏灯' },
      { label: '实验 E01', link: '/lab/e01-blink.md', desc: 'RGB 红灯闪烁' },
      { label: 'C1 内存模型', link: '/c/01-memory-model.md', desc: '理解变量住哪' },
    ],
    then: '按 C 篇 → B 篇 → S 篇顺序补地基',
  },
  {
    emoji: '🔨',
    who: '会 C、玩过 Arduino',
    color: '#3451b2',
    steps: [
      { label: 'B1 四步构建', link: '/build/01-four-steps.md', desc: '预处理到链接' },
      { label: 'B4 启动过程', link: '/build/04-startup.md', desc: '上电到 main' },
      { label: 'S3 GPIO', link: '/stm32/03-gpio.md', desc: '七个寄存器' },
    ],
    then: '补上"构建/链接/启动"这块最常被跳过的地基',
  },
  {
    emoji: '⚡',
    who: '硬件出身，代码薄',
    color: '#d97706',
    steps: [
      { label: 'C2 指针', link: '/c/02-pointer.md', desc: '嵌入式指针' },
      { label: 'C3 volatile', link: '/c/03-volatile.md', desc: '编译器别动' },
      { label: 'S2 时钟树', link: '/stm32/02-rcc-clock.md', desc: 'RCC 全解' },
    ],
    then: '每章配实验中心的观测点，眼见为实',
  },
  {
    emoji: '🚀',
    who: '想做 AIoT / 语音产品',
    color: '#dc2626',
    steps: [
      { label: 'P0 ESP-IDF', link: '/esp32/00-env.md', desc: '环境搭建' },
      { label: 'P2 GPIO 矩阵', link: '/esp32/02-gpio-matrix.md', desc: '引脚任意映射' },
      { label: 'P5 UART 驱动', link: '/esp32/05-uart-driver.md', desc: '驱动解析' },
    ],
    then: '直上 E07 姿态传感器、E08 音频放音',
  },
  {
    emoji: '🧵',
    who: '被 RTOS 面试/项目卡住',
    color: '#7c3aed',
    steps: [
      { label: 'F1 任务与 TCB', link: '/rtos/freertos/01-task-tcb.md', desc: '任务结构体' },
      { label: 'F2 上下文切换', link: '/rtos/freertos/02-context-switch.md', desc: '动画演示' },
      { label: 'E04 优先级反转', link: '/lab/e04-priority-inversion.md', desc: '复现实验' },
    ],
    then: '回看双 OS 对照做选型',
  },
]

const visible = ref(false)
const activeCard = ref(-1)
let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting) {
        visible.value = true
        observer?.disconnect()
      }
    },
    { threshold: 0.08 }
  )
  const el = document.querySelector('.mcu-pathfinder')
  if (el) observer.observe(el)
})

onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div class="mcu-pathfinder" :class="{ 'mcu-pathfinder-visible': visible }">
    <div
      v-for="(p, i) in paths"
      :key="i"
      class="mcu-path-card"
      :class="{ 'mcu-path-active': activeCard === i }"
      :style="{
        '--path-color': p.color,
        '--card-delay': `${i * 0.1}s`,
      }"
      @mouseenter="activeCard = i"
      @mouseleave="activeCard = -1"
    >
      <div class="mcu-path-header">
        <span class="mcu-path-emoji">{{ p.emoji }}</span>
        <span class="mcu-path-who">{{ p.who }}</span>
      </div>

      <div class="mcu-path-steps">
        <div
          v-for="(s, j) in p.steps"
          :key="j"
          class="mcu-path-step"
          :style="{ '--step-i': j }"
        >
          <span class="mcu-path-dot" :style="{ background: p.color }"></span>
          <a :href="withBase(s.link.replace(/\.md$/, '.html'))" class="mcu-path-step-link">
            <span class="mcu-path-step-label">{{ s.label }}</span>
            <span class="mcu-path-step-desc">{{ s.desc }}</span>
          </a>
          <span v-if="j < p.steps.length - 1" class="mcu-path-connector"></span>
        </div>
      </div>

      <div class="mcu-path-then">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
          <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ p.then }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mcu-pathfinder {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  padding: 0 0 32px;
  max-width: 1100px;
  margin: 0 auto;
}

.mcu-path-card {
  position: relative;
  padding: 20px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  overflow: hidden;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.35s ease,
              border-color 0.35s ease;

  opacity: 0;
  transform: translateY(14px);
}

.mcu-pathfinder-visible .mcu-path-card {
  opacity: 1;
  transform: none;
  transition: opacity 0.45s cubic-bezier(0.16, 1, 0.3, 1) var(--card-delay),
              transform 0.45s cubic-bezier(0.16, 1, 0.3, 1) var(--card-delay),
              box-shadow 0.35s ease,
              border-color 0.35s ease;
}

.mcu-path-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--path-color);
  opacity: 0;
  transition: opacity 0.3s;
}

.mcu-path-card:hover::before,
.mcu-path-active::before {
  opacity: 1;
}

.mcu-path-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--path-color) 30%, transparent);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
}

:root.dark .mcu-path-card:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25);
}

.mcu-path-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.mcu-path-emoji {
  font-size: 1.6em;
  line-height: 1;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.mcu-path-card:hover .mcu-path-emoji {
  transform: scale(1.15) rotate(-5deg);
}

.mcu-path-who {
  font-weight: 600;
  font-size: 0.95em;
  color: var(--vp-c-text-1);
  line-height: 1.3;
}

.mcu-path-steps {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 14px;
}

.mcu-path-step {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  padding-bottom: 10px;
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.35s ease calc(var(--card-delay) + var(--step-i, 0) * 0.06s + 0.15s),
              transform 0.35s cubic-bezier(0.16, 1, 0.3, 1) calc(var(--card-delay) + var(--step-i, 0) * 0.06s + 0.15s);
}

.mcu-pathfinder-visible .mcu-path-step {
  opacity: 1;
  transform: none;
}

.mcu-path-step:last-child {
  padding-bottom: 0;
}

.mcu-path-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  box-shadow: 0 0 0 3px var(--vp-c-bg-soft);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1) calc(var(--step-i, 0) * 0.08s),
              box-shadow 0.25s ease calc(var(--step-i, 0) * 0.08s);
}

.mcu-path-card:hover .mcu-path-dot {
  transform: scale(1.3);
  box-shadow: 0 0 0 3px var(--vp-c-bg-soft), 0 0 8px var(--path-color);
}

.mcu-path-connector {
  position: absolute;
  left: 3.5px;
  top: 15px;
  bottom: 0;
  width: 1px;
  background: var(--vp-c-divider);
  transform-origin: top;
  transition: background 0.3s;
}

.mcu-path-card:hover .mcu-path-connector {
  background: color-mix(in srgb, var(--path-color) 50%, transparent);
  animation: mcu-conn-grow 0.4s ease calc(var(--step-i, 0) * 0.08s) both;
}

@keyframes mcu-conn-grow {
  from { transform: scaleY(0); }
  to   { transform: scaleY(1); }
}

.mcu-path-step-link {
  display: flex;
  flex-direction: column;
  gap: 1px;
  text-decoration: none;
  transition: transform 0.2s;
}

.mcu-path-step-link:hover {
  transform: translateX(3px);
}

.mcu-path-step-label {
  font-size: 0.88em;
  font-weight: 600;
  color: var(--vp-c-text-1);
  line-height: 1.3;
}

.mcu-path-step-link:hover .mcu-path-step-label {
  color: var(--path-color);
}

.mcu-path-step-desc {
  font-size: 0.78em;
  color: var(--vp-c-text-3);
  line-height: 1.3;
}

.mcu-path-then {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 12px;
  border-top: 1px dashed var(--vp-c-divider);
  font-size: 0.8em;
  color: var(--vp-c-text-3);
  line-height: 1.4;
  transition: color 0.2s;
}

.mcu-path-card:hover .mcu-path-then {
  color: var(--vp-c-text-2);
}

.mcu-path-then svg {
  flex-shrink: 0;
  opacity: 0.5;
  transition: opacity 0.2s, transform 0.2s;
}

.mcu-path-card:hover .mcu-path-then svg {
  opacity: 1;
  transform: translateX(3px);
  color: var(--path-color);
}

@media (max-width: 640px) {
  .mcu-pathfinder {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mcu-path-card {
    opacity: 1;
    transform: none;
    transition: box-shadow 0.35s, border-color 0.35s;
  }
  .mcu-path-card:hover {
    transform: none;
  }
  .mcu-path-card:hover .mcu-path-emoji {
    transform: none;
  }
  .mcu-path-step {
    opacity: 1;
    transform: none;
    transition: none;
  }
  .mcu-path-dot {
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .mcu-path-card:hover .mcu-path-connector {
    animation: none;
  }
}
</style>
