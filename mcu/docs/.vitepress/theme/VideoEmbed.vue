<script setup lang="ts">
// 视频嵌入：B 站 / 油管 统一卡片
// 用法：<VideoEmbed type="bilibili" id="BV1Jx411X7NS" title="野火 FreeRTOS 内核实战" />
//       <VideoEmbed type="youtube"  id="gOW-B2KHvHU" title="TCP 3-Way Handshake" />
// 纪律：id 必须真实存在（嵌入前先验证），禁止占位。
const props = defineProps<{
  type: 'bilibili' | 'youtube'
  id: string
  title?: string
}>()

const src = props.type === 'bilibili'
  ? `https://player.bilibili.com/player.html?bvid=${props.id}&autoplay=0&high_quality=1`
  : `https://www.youtube-nocookie.com/embed/${props.id}`

const siteName = props.type === 'bilibili' ? '哔哩哔哩' : 'YouTube'
const pageUrl = props.type === 'bilibili'
  ? `https://www.bilibili.com/video/${props.id}`
  : `https://youtu.be/${props.id}`
</script>

<template>
  <div class="video-embed">
    <div class="video-frame">
      <iframe
        :src="src"
        :title="title || id"
        scrolling="no"
        frameborder="0"
        allowfullscreen
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      />
    </div>
    <div class="video-caption">
      🎬 {{ title || id }} <span class="video-site">@ {{ siteName }}</span>
      · <a :href="pageUrl" target="_blank" rel="noopener">打不开？去{{ siteName }}看 ↗</a>
    </div>
  </div>
</template>

<style scoped>
.video-embed {
  margin: 1.2em 0;
}
.video-frame {
  position: relative;
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  aspect-ratio: 16 / 9;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
}
.video-frame iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.video-caption {
  text-align: center;
  font-size: 13px;
  color: var(--vp-c-text-2);
  margin-top: 6px;
}
.video-site {
  opacity: 0.7;
}
</style>
