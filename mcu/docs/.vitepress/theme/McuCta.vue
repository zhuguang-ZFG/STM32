<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { withBase } from 'vitepress'
import progress from '../data/progress.json'

const t = progress.totals
const visible = ref(false)
let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting) {
        visible.value = true
        observer?.disconnect()
      }
    },
    { threshold: 0.2 }
  )
  const el = document.querySelector('.mcu-cta')
  if (el) observer.observe(el)
})

onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div class="mcu-cta" :class="{ 'mcu-cta-visible': visible }">
    <div class="mcu-cta-glow"></div>
    <div class="mcu-cta-content">
      <h2 class="mcu-cta-title">准备好点亮第一盏灯了吗？</h2>
      <p class="mcu-cta-desc">
        {{ t.chapters }} 章体系化教程 · {{ t.animations }} 张寄存器动画 · {{ t.projects }} 个可编译工程 · {{ t.experiments }} 个硬件实验<br>
        从零到 RTOS，一条路线走到底。
      </p>
      <div class="mcu-cta-actions">
        <a :href="withBase('/guide/')" class="mcu-cta-btn mcu-cta-btn-primary">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
            <path d="M3 1h7l3 3v11H3V1z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M6 1v3h4" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M5.5 8h5M5.5 10.5h5M5.5 5.5h2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          开始学习
        </a>
        <a :href="withBase('/guide/hardware')" class="mcu-cta-btn mcu-cta-btn-ghost">
          先看装备清单
        </a>
      </div>
      <div class="mcu-cta-chips">
        <span class="mcu-cta-chip">STM32F407</span>
        <span class="mcu-cta-chip">ESP32-S3</span>
        <span class="mcu-cta-chip">FreeRTOS</span>
        <span class="mcu-cta-chip">RT-Thread</span>
        <span class="mcu-cta-chip">GD32</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mcu-cta {
  position: relative;
  max-width: 800px;
  margin: 20px auto 40px;
  padding: 0 24px;
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.mcu-cta-visible {
  opacity: 1;
  transform: none;
}

.mcu-cta-glow {
  position: absolute;
  inset: 0;
  border-radius: 20px;
  background:
    radial-gradient(ellipse at 30% 0%, rgba(52, 81, 178, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 100%, rgba(62, 175, 124, 0.05) 0%, transparent 60%);
  pointer-events: none;
}

:root.dark .mcu-cta-glow {
  background:
    radial-gradient(ellipse at 30% 0%, rgba(52, 81, 178, 0.12) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 100%, rgba(62, 175, 124, 0.08) 0%, transparent 60%);
}

.mcu-cta-content {
  position: relative;
  text-align: center;
  padding: 40px 32px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 20px;
  background: var(--vp-c-bg-soft);
  overflow: hidden;
}

.mcu-cta-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--mcu-brand), var(--mcu-accent), transparent);
  opacity: 0.6;
}

.mcu-cta-title {
  font-size: 1.6em;
  font-weight: 700;
  margin: 0 0 12px;
  background: linear-gradient(135deg, var(--mcu-brand) 30%, var(--mcu-accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.mcu-cta-desc {
  font-size: 0.95em;
  color: var(--vp-c-text-2);
  line-height: 1.7;
  margin: 0 0 28px;
}

.mcu-cta-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.mcu-cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 24px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95em;
  text-decoration: none;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.mcu-cta-btn-primary {
  background: linear-gradient(135deg, var(--mcu-brand), #4a6ad4);
  color: #fff;
  box-shadow: 0 4px 14px rgba(52, 81, 178, 0.25);
}

.mcu-cta-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(52, 81, 178, 0.35);
}

.mcu-cta-btn-primary:active {
  transform: translateY(0) scale(0.98);
}

.mcu-cta-btn-ghost {
  background: transparent;
  color: var(--vp-c-text-1);
  border: 1px solid var(--vp-c-divider);
}

.mcu-cta-btn-ghost:hover {
  border-color: var(--mcu-brand);
  color: var(--mcu-brand);
  background: rgba(52, 81, 178, 0.04);
}

.mcu-cta-chips {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.mcu-cta-chip {
  padding: 4px 12px;
  font-size: 0.78em;
  font-weight: 500;
  color: var(--vp-c-text-3);
  border: 1px solid var(--vp-c-divider);
  border-radius: 100px;
  transition: all 0.2s;
}

.mcu-cta-chip:hover {
  color: var(--mcu-brand);
  border-color: var(--mcu-brand);
  background: rgba(52, 81, 178, 0.05);
}

@media (max-width: 640px) {
  .mcu-cta-content {
    padding: 28px 20px;
  }
  .mcu-cta-title {
    font-size: 1.3em;
  }
  .mcu-cta-actions {
    flex-direction: column;
  }
  .mcu-cta-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mcu-cta {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
</style>
