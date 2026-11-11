<script setup lang="ts">
import { withBase } from 'vitepress'
</script>

<!-- 全站统一的 AI 生成声明：替代此前 65 页各自手写、另一半页面漏写的 `> AI生成`。
     放在 Layout 的 #doc-after 插槽里，只在文档页出现（首页 layout: home 不走这个插槽）。 -->
<template>
  <aside class="mcu-ai-notice" aria-label="内容来源说明">
    <p>
      本页由 AI 生成。寄存器、引脚与行号以手册和固定版本的源码为准，依据见
      <a :href="withBase('/reference/about.html#事实从哪来')">事实从哪来</a>；发现错误欢迎编辑此页或提 issue。
    </p>
  </aside>
</template>
