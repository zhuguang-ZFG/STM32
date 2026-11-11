---
title: 交互式学习路径图
description: 基于先修关系的可视化学习地图，点击节点跳转章节
---

# 交互式学习路径图

> 🎯 80 章、7 个 track、完整的先修关系图。点击节点查看详情，高亮当前学习路径。

<script setup>
import { ref, onMounted, computed } from 'vue';
import curriculum from './curriculum.json';

const selectedNode = ref(null);
const highlightedPath = ref([]);
const searchQuery = ref('');

const tracks = {
  c: { name: 'C 语言篇', color: '#3451b2', icon: '📝' },
  build: { name: '构建篇', color: '#3eaf7c', icon: '🔨' },
  stm32: { name: 'STM32 篇', color: '#d97706', icon: '🔌' },
  esp32: { name: 'ESP32 篇', color: '#9c27b0', icon: '📡' },
  rtos: { name: 'FreeRTOS 篇', color: '#dc2626', icon: '⚡' },
  rtthread: { name: 'RT-Thread 篇', color: '#00bcd4', icon: '🧵' },
  gd32: { name: 'GD32 篇', color: '#666', icon: '🎯' },
  projects: { name: '项目篇', color: '#795548', icon: '🚀' }
};

const filteredChapters = computed(() => {
  if (!searchQuery.value) return curriculum;
  const q = searchQuery.value.toLowerCase();
  return curriculum.filter(ch => 
    ch.title.toLowerCase().includes(q) || 
    ch.id.toLowerCase().includes(q)
  );
});

function getTrackColor(track) {
  return tracks[track]?.color || '#666';
}

function selectNode(chapter) {
  selectedNode.value = chapter;
  highlightedPath.value = getPrerequisitePath(chapter.id);
}

function getPrerequisitePath(id) {
  const path = [];
  const visited = new Set();
  
  function dfs(nodeId) {
    if (visited.has(nodeId)) return;
    visited.add(nodeId);
    
    const node = curriculum.find(ch => ch.id === nodeId);
    if (!node) return;
    
    path.push(nodeId);
    node.must?.forEach(prereq => dfs(prereq));
  }
  
  dfs(id);
  return path;
}

function getNodeUrl(chapter) {
  const path = chapter.path.replace('docs/', '').replace('.md', '');
  return '/' + path;
}

function isHighlighted(id) {
  return highlightedPath.value.includes(id);
}

onMounted(() => {
  // Initialize with a default selection
  if (curriculum.length > 0) {
    selectNode(curriculum[0]);
  }
});
</script>

<div class="learning-path-container">
  <div class="controls">
    <input 
      v-model="searchQuery" 
      type="text" 
      placeholder="搜索章节（ID 或标题）..." 
      class="search-input"
    />
    <div class="legend">
      <div v-for="(track, key) in tracks" :key="key" class="legend-item">
        <span class="legend-dot" :style="{ background: track.color }"></span>
        {{ track.icon }} {{ track.name }}
      </div>
    </div>
  </div>

  <div class="graph-container">
    <div class="chapter-grid">
      <div 
        v-for="chapter in filteredChapters" 
        :key="chapter.id"
        class="chapter-node"
        :class="{ highlighted: isHighlighted(chapter.id), selected: selectedNode?.id === chapter.id }"
        :style="{ borderLeftColor: getTrackColor(chapter.track) }"
        @click="selectNode(chapter)"
      >
        <div class="node-header">
          <span class="node-id">{{ chapter.id }}</span>
          <span class="node-track">{{ tracks[chapter.track]?.icon }}</span>
        </div>
        <div class="node-title">{{ chapter.title }}</div>
        <div class="node-meta" v-if="chapter.must?.length">
          先修：{{ chapter.must.slice(0, 3).join(', ') }}{{ chapter.must.length > 3 ? '...' : '' }}
        </div>
      </div>
    </div>
  </div>

  <div v-if="selectedNode" class="detail-panel">
    <h3>{{ selectedNode.title }}</h3>
    <div class="detail-meta">
      <span class="badge" :style="{ background: getTrackColor(selectedNode.track) }">
        {{ tracks[selectedNode.track]?.name }}
      </span>
      <span class="badge-id">{{ selectedNode.id }}</span>
    </div>
    
    <div class="detail-section" v-if="selectedNode.must?.length">
      <h4>📋 必修先修</h4>
      <ul>
        <li v-for="prereq in selectedNode.must" :key="prereq">
          <a @click.prevent="selectNode(curriculum.find(ch => ch.id === prereq))" href="#">
            {{ prereq }} - {{ curriculum.find(ch => ch.id === prereq)?.title }}
          </a>
        </li>
      </ul>
    </div>
    
    <div class="detail-section" v-if="selectedNode.parallel?.length">
      <h4>🔗 并行推荐</h4>
      <ul>
        <li v-for="parallel in selectedNode.parallel" :key="parallel">
          <a @click.prevent="selectNode(curriculum.find(ch => ch.id === parallel))" href="#">
            {{ parallel }} - {{ curriculum.find(ch => ch.id === parallel)?.title }}
          </a>
        </li>
      </ul>
    </div>
    
    <div class="detail-section">
      <h4>🎯 学习路径</h4>
      <div class="path-chain">
        <span v-for="(id, idx) in highlightedPath" :key="id" class="path-item">
          <a @click.prevent="selectNode(curriculum.find(ch => ch.id === id))" href="#">{{ id }}</a>
          <span v-if="idx < highlightedPath.length - 1" class="path-arrow">→</span>
        </span>
      </div>
    </div>
    
    <a :href="getNodeUrl(selectedNode)" class="read-chapter-btn">
      📖 阅读本章
    </a>
  </div>
</div>

<style scoped>
.learning-path-container {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 20px;
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.controls {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 15px;
  border: 2px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
}

.search-input:focus {
  outline: none;
  border-color: var(--vp-c-brand);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px;
  background: var(--vp-c-bg-soft);
  border-radius: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--vp-c-text-2);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.graph-container {
  overflow-y: auto;
  max-height: 70vh;
  padding-right: 10px;
}

.chapter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.chapter-node {
  padding: 12px;
  background: var(--vp-c-bg);
  border: 2px solid var(--vp-c-divider);
  border-left-width: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.chapter-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chapter-node.highlighted {
  background: var(--vp-c-brand-soft);
  border-color: var(--vp-c-brand);
}

.chapter-node.selected {
  border-width: 3px;
  box-shadow: 0 0 0 3px var(--vp-c-brand-soft);
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.node-id {
  font-weight: 700;
  font-size: 14px;
  color: var(--vp-c-brand);
}

.node-track {
  font-size: 16px;
}

.node-title {
  font-size: 13px;
  line-height: 1.4;
  color: var(--vp-c-text-1);
  margin-bottom: 6px;
}

.node-meta {
  font-size: 11px;
  color: var(--vp-c-text-3);
}

.detail-panel {
  position: sticky;
  top: 20px;
  padding: 20px;
  background: var(--vp-c-bg);
  border: 2px solid var(--vp-c-divider);
  border-radius: 12px;
  max-height: 70vh;
  overflow-y: auto;
}

.detail-panel h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: var(--vp-c-text-1);
}

.detail-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  color: white;
  font-weight: 600;
}

.badge-id {
  padding: 4px 10px;
  background: var(--vp-c-bg-soft);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--vp-c-text-2);
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--vp-c-text-2);
}

.detail-section ul {
  margin: 0;
  padding-left: 20px;
}

.detail-section li {
  margin-bottom: 6px;
  font-size: 13px;
}

.detail-section a {
  color: var(--vp-c-brand);
  text-decoration: none;
}

.detail-section a:hover {
  text-decoration: underline;
}

.path-chain {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.path-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.path-item a {
  padding: 4px 8px;
  background: var(--vp-c-bg-soft);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--vp-c-brand);
  text-decoration: none;
}

.path-item a:hover {
  background: var(--vp-c-brand-soft);
}

.path-arrow {
  color: var(--vp-c-text-3);
  font-size: 16px;
}

.read-chapter-btn {
  display: block;
  width: 100%;
  padding: 12px;
  background: var(--vp-c-brand);
  color: white;
  text-align: center;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  margin-top: 16px;
  transition: background 0.2s;
}

.read-chapter-btn:hover {
  background: var(--vp-c-brand-dark);
}

@media (max-width: 960px) {
  .learning-path-container {
    grid-template-columns: 1fr;
  }
  
  .detail-panel {
    position: static;
    max-height: none;
  }
  
  .chapter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
