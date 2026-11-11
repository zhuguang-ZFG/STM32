<script setup>
import { onMounted, onUnmounted, ref, nextTick } from 'vue'

// SVG 由 config.mts 的 markdown 规则在构建期内联进来，以字符串 prop 交给 v-html 渲染
// （静态内容，不让 Vue 去 diff 整棵 SVG 子树）；本组件只负责控件：
// 暂停/播放、进度条、放大查看、尊重系统的"减少动效"偏好。
// 配色靠 custom.css 里的 .a-* / .s-* 类（同一处规则完成深浅两套主题）。

const props = defineProps({
  name: { type: String, required: true },
  caption: { type: String, default: '' },
  dur: { type: [String, Number], default: '' },
  markup: { type: String, default: '' },
})

const stage = ref(null)
const lightboxStage = ref(null)
const paused = ref(false)      // 用户意图：按了「暂停」
const offscreen = ref(false)   // 视口外自动停：用户看不见的图不该烧 CPU（SSR/无 JS 时不标，进度条照常走）
const reducedMotion = ref(false)
const lightbox = ref(false)

// SMIL 跑在主线程上。演示中心一页 69 张图同时跑，慢机器/手机的帧率会掉到个位数，
// 连滚动都卡；所以离开视口（含 200px 预载带）就 pauseAnimations()，回来再续。
// 续播从停下的那一刻接着走，读者感知不到——按钮只反映用户意图，不反映这个自动停。
// 水合之前由 config.mts 里 <head> 的那段内联脚本先按同一口径停一遍（SMIL 在 load 就开跑，等不到这里）。
function applyPlayState() {
  const svg = stage.value?.querySelector('svg')
  if (!svg || typeof svg.pauseAnimations !== 'function') return
  if (paused.value || offscreen.value) svg.pauseAnimations()
  else svg.unpauseAnimations()
}

function toggle() {
  paused.value = !paused.value
  applyPlayState()
  if (lightbox.value) syncLightbox()
}

// 全屏副本不复制 DOM：用同一份 markup 再渲染一份。SMIL 各自跑，
// 打开时把当前时刻与暂停状态同步过去，保证"减少动效"用户看到的是静止帧。
function openLightbox() {
  lastFocus = document.activeElement
  lightbox.value = true
  // 对话框打开后背景不该还能滚：滚轮会穿透到页面，手机上尤其明显。
  document.body.style.overflow = 'hidden'
  nextTick(() => {
    syncLightbox()
    // 焦点必须进到对话框里，否则键盘用户仍停在后面正文的第一个控件上。
    lightboxStage.value?.closest('.anim-lightbox__card')?.querySelector('.anim-lightbox__close')?.focus()
  })
}

function syncLightbox() {
  const src = stage.value?.querySelector('svg')
  const dst = lightboxStage.value?.querySelector('svg')
  if (!src || !dst || typeof src.getCurrentTime !== 'function') return
  try { dst.setCurrentTime(src.getCurrentTime()) } catch { /* 无碍 */ }
  if (typeof dst.pauseAnimations === 'function') {
    if (paused.value) dst.pauseAnimations()
    else dst.unpauseAnimations()
  }
}

function closeLightbox() {
  if (!lightbox.value) return
  lightbox.value = false
  document.body.style.overflow = ''
  // 回到触发它的"放大"按钮，键盘阅读的位置不丢。
  lastFocus?.focus?.()
  lastFocus = null
}

function onKey(e) {
  if (!lightbox.value) return
  if (e.key === 'Escape') {
    closeLightbox()
    return
  }
  if (e.key !== 'Tab') return
  // 焦点圈在对话框内：出得去的对话框等于把键盘用户丢回正文。
  const card = lightboxStage.value?.closest('.anim-lightbox__card')
  const items = card
    ? [...card.querySelectorAll('button, [href], [tabindex]:not([tabindex="-1"])')].filter((el) => !el.disabled)
    : []
  if (!items.length) return
  const first = items[0]
  const last = items[items.length - 1]
  const active = document.activeElement
  if (e.shiftKey && (active === first || !card.contains(active))) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && (active === last || !card.contains(active))) {
    e.preventDefault()
    first.focus()
  }
}

let observer = null
let lastFocus = null

onMounted(() => {
  // 尊重系统偏好但不替用户做决定：默认停在静止帧，点「播放」即可跑起来。
  reducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const svg = stage.value?.querySelector('svg')
  if (reducedMotion.value) {
    // 静止帧不能停在 t=0：爬线一笔没画、生长箭头一寸没长，那是一张缺零件的图。
    // 停在末尾——底色、结论字幕都在，波形也已经整条画完了。
    const d = Number(props.dur)
    if (svg && d) svg.setCurrentTime(d * 0.9)
    paused.value = true
  }
  // 先按"看不见"停住（SPA 内跳转到演示中心时没有看门人，v-html 一插入 SMIL 就开跑），
  // observer 的首次回调随即按真实可见性续播；暂停/续播不丢时间轴，视觉上只是少走一帧。
  offscreen.value = true
  applyPlayState()
  if (typeof IntersectionObserver === 'function' && stage.value) {
    observer = new IntersectionObserver((entries) => {
      offscreen.value = !entries.some((e) => e.isIntersecting)
      applyPlayState()
    }, { rootMargin: '200px 0px' })
    observer.observe(stage.value)
  } else {
    offscreen.value = false
    applyPlayState()
  }
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  observer?.disconnect()
  window.removeEventListener('keydown', onKey)
  // 组件在对话框打开期间被卸载（路由切走）时别把页面永久锁死。
  if (lightbox.value) document.body.style.overflow = ''
})
</script>

<template>
  <figure class="anim-figure" :data-anim="name" :class="{ 'is-paused': paused, 'is-offscreen': offscreen }">
    <div ref="stage" class="anim-figure__stage" v-html="markup" />
    <div class="anim-figure__bar">
      <button
        v-if="dur"
        class="anim-figure__btn"
        type="button"
        :aria-pressed="paused ? 'true' : 'false'"
        @click="toggle"
      >
        {{ paused ? '播放' : '暂停' }}
      </button>
      <span v-if="dur" class="anim-figure__progress" aria-hidden="true">
        <i :style="{ animationDuration: dur + 's' }" />
      </span>
      <span class="anim-figure__meta">
        <template v-if="dur">{{ dur }}s 一轮</template>
        <template v-if="reducedMotion && paused"> · 系统偏好减少动效，已停在静止帧</template>
      </span>
      <button
        v-if="markup"
        class="anim-figure__zoom"
        type="button"
        aria-label="放大查看动画"
        title="放大查看"
        @click="openLightbox"
      >
        放大
      </button>
    </div>
    <figcaption v-if="caption" class="anim-figure__caption">{{ caption }}</figcaption>

    <Teleport to="body">
      <div
        v-if="lightbox"
        class="anim-lightbox"
        role="dialog"
        aria-modal="true"
        aria-label="动画放大查看"
        @click.self="closeLightbox"
      >
        <div class="anim-lightbox__card">
          <button class="anim-lightbox__close" type="button" aria-label="关闭" @click="closeLightbox">✕</button>
          <div ref="lightboxStage" class="anim-figure__stage anim-lightbox__stage" v-html="markup" />
          <div class="anim-figure__bar">
            <button
              v-if="dur"
              class="anim-figure__btn"
              type="button"
              :aria-pressed="paused ? 'true' : 'false'"
              @click="toggle"
            >
              {{ paused ? '播放' : '暂停' }}
            </button>
            <span v-if="dur" class="anim-figure__progress" aria-hidden="true">
              <i :style="{ animationDuration: dur + 's' }" />
            </span>
            <span class="anim-figure__meta">{{ dur }}s 一轮 · Esc 关闭</span>
          </div>
        </div>
      </div>
    </Teleport>
  </figure>
</template>