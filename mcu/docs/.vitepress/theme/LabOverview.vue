<script setup lang="ts">
import { withBase } from 'vitepress'
import data from '../data/progress.json'
const labs = data.tracks.find(t => t.key === 'lab')!.chapters
const verifiedCount = labs.filter(l => l.hardwareStatus === 'verified').length
</script>
<template>
  <p class="mcu-verify-summary">
    上板验证进度：<strong>{{ verifiedCount }} / {{ labs.length }}</strong> 个实验已实测。
    <a :href="withBase('/guide/verify-on-hardware')">了解如何验证并回填 →</a>
  </p>
  <table>
    <thead><tr><th>实验</th><th>文稿</th><th>配套代码</th><th>上板验证</th><th>时长 / 难度</th></tr></thead>
    <tbody>
      <tr v-for="lab in labs" :key="lab.route">
        <td><a :href="withBase(lab.route)">{{ lab.title }}</a></td>
        <td>{{ lab.status === 'done' ? '成稿' : '建设中' }}</td>
        <td :title="lab.codeNote">{{ lab.codeStatus === 'ready' ? '工程已提供' : '建设中' }}</td>
        <td>{{ lab.hardwareStatus === 'verified' ? '有记录' : '待实测' }}</td>
        <td>{{ lab.minutes }} 分钟 / {{ '★'.repeat(lab.difficulty) }}</td>
      </tr>
    </tbody>
  </table>
</template>
