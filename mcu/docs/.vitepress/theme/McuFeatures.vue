<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import progress from '../data/progress.json'

const t = progress.totals
const features = [
  {
    icon: '📖',
    title: `${t.chapters} 章体系化教程`,
    desc: '从 C 语言精髓到 RT-Thread 移植，完整覆盖嵌入式开发技能树',
    gradient: 'linear-gradient(135deg, #3451b2 0%, #5b6abf 100%)',
    accent: '#3451b2',
  },
  {
    icon: '🎬',
    title: `${t.animations} 张 SVG 动画`,
    desc: '寄存器位操作、时钟树、调度算法……抽象概念可视化',
    gradient: 'linear-gradient(135deg, #3eaf7c 0%, #4fc08d 100%)',
    accent: '#3eaf7c',
  },
  {
    icon: '🔧',
    title: `${t.projects} 个可编译工程`,
    desc: 'STM32 / GD32 / ESP32 三平台，每章配套固件代码',
    gradient: 'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)',
    accent: '#d97706',
  },
  {
    icon: '🧪',
    title: `${t.experiments} 个硬件实验`,
    desc: '从 Blink 到示波器实测，理论动手闭环',
    gradient: 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
    accent: '#dc2626',
  },
]

const visible = ref(false)
let observer: IntersectionObserver | null = null

function handleMouseEnter(e: MouseEvent) {
  const card = e.currentTarget as HTMLElement
  card.style.setProperty('--mouse-x', `${e.offsetX}px`)
  card.style.setProperty('--mouse-y', `${e.offsetY}px`)
}

function handleMouseMove(e: MouseEvent) {
  const card = e.currentTarget as HTMLElement
  const rect = card.getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width - 0.5
  const y = (e.clientY - rect.top) / rect.height - 0.5
  card.style.transform = `translateY(-4px) perspective(600px) rotateX(${-y * 6}deg) rotateY(${x * 6}deg)`
}

function handleMouseLeave(e: MouseEvent) {
  (e.currentTarget as HTMLElement).style.transform = ''
}

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

  const el = document.querySelector('.mcu-features')
  if (el) observer.observe(el)
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<template>
  <div class="mcu-features" :class="{ 'mcu-features-visible': visible }">
    <div
      v-for="(f, i) in features"
      :key="i"
      class="mcu-feature-card"
      :style="{
        '--card-gradient': f.gradient,
        '--card-accent': f.accent,
        '--card-delay': `${i * 0.1}s`,
      }"
      @mouseenter="handleMouseEnter"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
    >
      <div class="mcu-feature-spotlight"></div>
      <div class="mcu-feature-icon">{{ f.icon }}</div>
      <h3 class="mcu-feature-title">{{ f.title }}</h3>
      <p class="mcu-feature-desc">{{ f.desc }}</p>
      <div class="mcu-feature-glow"></div>
      <div class="mcu-feature-border"></div>
    </div>
  </div>
</template>

<style scoped>
.mcu-features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  padding: 40px 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.mcu-feature-card {
  position: relative;
  padding: 28px 24px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 16px;
  overflow: hidden;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.3s ease,
              border-color 0.3s ease;
  transform-style: preserve-3d;
  will-change: transform;

  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.5s ease var(--card-delay),
              transform 0.5s cubic-bezier(0.4, 0, 0.2, 1) var(--card-delay),
              box-shadow 0.3s ease,
              border-color 0.3s ease;
}

.mcu-features-visible .mcu-feature-card {
  opacity: 1;
  transform: translateY(0);
}

.mcu-feature-card:hover {
  border-color: transparent;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

:root.dark .mcu-feature-card:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

/* Spotlight follows cursor */
.mcu-feature-spotlight {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s;
  background: radial-gradient(
    300px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(52, 81, 178, 0.06),
    transparent 60%
  );
  z-index: 0;
  pointer-events: none;
}

:root.dark .mcu-feature-spotlight {
  background: radial-gradient(
    300px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(138, 180, 255, 0.08),
    transparent 60%
  );
}

.mcu-feature-card:hover .mcu-feature-spotlight {
  opacity: 1;
}

/* Animated gradient border on hover */
.mcu-feature-border {
  position: absolute;
  inset: 0;
  border-radius: 16px;
  padding: 1px;
  background: var(--card-gradient);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.mcu-feature-card:hover .mcu-feature-border {
  opacity: 1;
}

.mcu-feature-glow {
  position: absolute;
  inset: 0;
  background: var(--card-gradient);
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 0;
}

.mcu-feature-card:hover .mcu-feature-glow {
  opacity: 0.05;
}

.mcu-feature-icon {
  position: relative;
  z-index: 1;
  font-size: 2.5em;
  margin-bottom: 16px;
  display: inline-block;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.mcu-feature-card:hover .mcu-feature-icon {
  transform: scale(1.15) translateY(-3px);
  animation: mcu-icon-bounce 1.5s ease-in-out infinite;
}

@keyframes mcu-icon-bounce {
  0%, 100% { transform: scale(1.15) translateY(-3px); }
  50% { transform: scale(1.15) translateY(-8px); }
}

.mcu-feature-title {
  position: relative;
  z-index: 1;
  font-size: 1.15em;
  font-weight: 700;
  color: var(--vp-c-text-1);
  margin: 0 0 8px;
  transition: color 0.2s;
}

.mcu-feature-card:hover .mcu-feature-title {
  background: var(--card-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.mcu-feature-desc {
  position: relative;
  z-index: 1;
  font-size: 0.9em;
  color: var(--vp-c-text-2);
  line-height: 1.6;
  margin: 0;
  transition: color 0.2s;
}

.mcu-feature-card:hover .mcu-feature-desc {
  color: var(--vp-c-text-1);
}

@media (max-width: 640px) {
  .mcu-features {
    grid-template-columns: 1fr;
    padding: 20px;
  }

  .mcu-feature-card {
    transform: none !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mcu-feature-card {
    opacity: 1;
    transform: none;
    transition: box-shadow 0.3s, border-color 0.3s;
  }
  .mcu-feature-card:hover {
    transform: none !important;
  }
  .mcu-feature-card:hover .mcu-feature-icon {
    animation: none;
    transform: scale(1.1);
  }
}
</style>
