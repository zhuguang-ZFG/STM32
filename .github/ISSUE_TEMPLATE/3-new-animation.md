---
name: 新增动画 / 实物图
about: 提交一个新的 SVG 动画或板卡结构图
title: "[动画] "
labels: animation
---

## 想演示什么

（一句话说清这张图要讲明白的原理）

## 归属

- 关联章节：
- 输出文件名（kebab-case，例如 `can-arbitration.svg`）：

## 实现方式

- [ ] 用 `tools/svgkit.py` 写生成脚本（推荐，可复现）
- [ ] 手工编辑 SVG（请说明为什么脚本不方便）

## 自检清单

- [ ] 自包含：无 `<script>`、无外链资源、无外部字体
- [ ] 动画用 CSS `@keyframes` 或 SMIL，`<img>` 引用即可播放
- [ ] 有标题栏、图例/标注、页脚结论
- [ ] 元素未超出画布（`python3 tools/check_assets.py` 无 WARN）
- [ ] 已在 `assets/README.md` 清单中登记
- [ ] 已在对应文档与 README 中引用
