<script setup lang="ts">
import { useData, withBase } from 'vitepress'
const { frontmatter: fm } = useData()
</script>

<template>
  <table class="mcu-lab-status">
    <tbody>
      <tr><th scope="row">时长</th><td>约 {{ fm.minutes }} 分钟</td></tr>
      <tr><th scope="row">难度</th><td>{{ '★'.repeat(fm.difficulty) }}</td></tr>
      <tr><th scope="row">配套代码</th><td>{{ fm.code_status === 'ready' ? '工程已提供' : '工程建设中' }} · {{ fm.code_note }}</td></tr>
      <tr><th scope="row">上板验证</th><td><a v-if="fm.hardware_status === 'verified'" :href="withBase('/' + fm.evidence.replace(/\.md$/, '.html'))">查看实测记录</a><template v-else>待上板实测；下文为预期现象，空白记录不表示验证通过</template></td></tr>
    </tbody>
  </table>
</template>
