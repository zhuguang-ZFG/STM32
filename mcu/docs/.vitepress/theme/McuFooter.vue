<script setup lang="ts">
import { withBase } from 'vitepress'

const GH = 'https://github.com/zhuguang-ZFG/mcu'

const columns = [
  {
    title: '学习路线',
    links: [
      { text: 'STM32F407 寄存器主线', href: '/stm32/' },
      { text: 'ESP32-S3 + ESP-IDF', href: '/esp32/' },
      { text: 'C 语言精髓', href: '/c/' },
      { text: '构建与运行全过程', href: '/build/' },
      { text: 'RTOS 双精讲', href: '/rtos/' },
      { text: 'GD32 双系对照', href: '/gd32/' },
    ],
  },
  {
    title: '动手实践',
    links: [
      { text: '实物实验中心', href: '/lab/' },
      { text: '双板综合项目', href: '/projects/' },
      { text: '动画展', href: '/animations' },
      { text: '硬件装备清单', href: '/guide/hardware' },
      { text: '学习路径', href: '/learning-path' },
    ],
  },
  {
    title: '速查与参考',
    links: [
      { text: '术语速查', href: '/reference/glossary' },
      { text: '常见问题 FAQ', href: '/reference/faq' },
      { text: '参考文献', href: '/reference/bibliography' },
      { text: '更新日志', href: '/reference/changelog' },
      { text: '关于我们与致谢', href: '/reference/about' },
    ],
  },
  {
    title: '社区与协作',
    links: [
      { text: 'GitHub 仓库', href: GH },
      { text: '提 Issue / 报错', href: `${GH}/issues` },
      { text: '贡献指南', href: `${GH}/blob/main/CONTRIBUTING.md` },
    ],
  },
]
</script>

<template>
  <footer class="mcu-footer">
    <div class="mcu-footer__inner">
      <div class="mcu-footer__grid">
        <div v-for="col in columns" :key="col.title" class="mcu-footer__col">
          <h3 class="mcu-footer__heading">{{ col.title }}</h3>
          <ul class="mcu-footer__list">
            <li v-for="link in col.links" :key="link.text">
              <a
                class="mcu-footer__link"
                :href="link.href.startsWith('http') ? link.href : withBase(link.href)"
                :target="link.href.startsWith('http') ? '_blank' : undefined"
                :rel="link.href.startsWith('http') ? 'noopener noreferrer' : undefined"
              >{{ link.text }}</a>
            </li>
          </ul>
        </div>
      </div>
      <div class="mcu-footer__bottom">
        <p class="mcu-footer__brand">
          <a :href="withBase('/')" class="mcu-footer__logo">通往单片机之路</a>
          <span class="mcu-footer__slogan">把一颗芯片讲透</span>
        </p>
        <p class="mcu-footer__legal">
          内容以
          <a :href="`${GH}/blob/main/LICENSE`" target="_blank" rel="noopener noreferrer">Apache-2.0</a>
          发布 · 标注"待核验 / 待实测"的结论尚未上板闭环，引用前请自行核对
        </p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.mcu-footer {
  border-top: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  padding: 48px 24px 32px;
  font-size: 0.9em;
}

.mcu-footer__inner {
  max-width: 1152px;
  margin: 0 auto;
}

.mcu-footer__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  margin-bottom: 40px;
}

.mcu-footer__heading {
  font-size: 0.95em;
  font-weight: 700;
  margin: 0 0 14px;
  padding: 0;
  border: none;
  color: var(--vp-c-text-1);
}

.mcu-footer__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mcu-footer__link {
  color: var(--vp-c-text-2);
  text-decoration: none;
  transition: color 0.2s ease;
}

.mcu-footer__link:hover {
  color: var(--mcu-brand, #3451b2);
}

.mcu-footer__bottom {
  border-top: 1px solid var(--vp-c-divider);
  padding-top: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.mcu-footer__brand {
  margin: 0;
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.mcu-footer__logo {
  font-weight: 700;
  font-size: 1.05em;
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.mcu-footer__logo:hover {
  color: var(--mcu-brand, #3451b2);
}

.mcu-footer__slogan {
  color: var(--vp-c-text-3);
  font-size: 0.9em;
}

.mcu-footer__legal {
  margin: 0;
  color: var(--vp-c-text-3);
  font-size: 0.85em;
}

.mcu-footer__legal a {
  color: var(--vp-c-text-3);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.mcu-footer__legal a:hover {
  color: var(--mcu-brand, #3451b2);
}

@media (max-width: 768px) {
  .mcu-footer__grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
  }
  .mcu-footer__bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .mcu-footer__grid {
    grid-template-columns: 1fr;
  }
}
</style>
