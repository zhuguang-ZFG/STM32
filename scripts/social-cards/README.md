# 书籍金句卡

`cards.json` 保存 2026-11-05 从现有三批 HTML 接收的 29 张卡面内容及文字基线。`cards.css` 统一页头、内容组和页脚；内容组内部固定间距，避免把台账推到卡底留下中部断层。主句保持章节原文，小注沿用原 spec 允许的压缩措辞。

```sh
node scripts/social-cards/render.mjs
node scripts/social-cards/render.mjs --check
```

需要根目录已安装 Playwright 和 Chromium。路径从脚本位置解析，无个人目录依赖。源码在本目录，正式资产在 `video/assets/social-cards/book/`；打开其 `index.html` 可浏览全部图片。旧任务交付件保留作历史参考。

生成先在 `.temp/skill-closeout/cards/` 测量，29 张全部通过才复制到正式目录。检查包含原文主句、接收时全卡文字、内容间距、文字列边界、页脚安全区及 30 张 PNG 哈希。竖版以 750×1000 CSS px、2 倍像素导出为 1500×2000；横版沿用现有 16:9 构图。

颜色沿用站点品牌；本轮将大字恢复为瑞士风细体，保留已有绿/橙语义标记。稀疏金句卡采用原 spec 的 A 方案，留白集中在内容组上下；没有为了填满画面增加文案。
