# 极其精品：实施记录

## 批次 A — 传播力（feat(seo) 368bd76）

- config.mts：sitemap（hostname 含 base + 尾斜杠，防丢 /mcu/ 前缀）、transformHead 注入每页 og/twitter/canonical、站点级 og:image(1200x630)/theme-color
- docs/public/robots.txt + og-cover.png
- scripts/gen-og-cover.py：确定性 Pillow 生成（非 AI 生图，中文不乱码）
- scripts/seo-check.mjs + tests/seo.test.mjs（7 例，含丢 base 反例）
- package.json + quality-contract.md 登记

## 批次 B — 可证性能（feat(perf) 209068a）

- scripts/perf-budget.mjs + tests/perf.test.mjs（6 例）
- 预算：首屏外壳+CSS br≤110KB、CSS br≤35KB、最大单块 br≤460KB、搜索索引 raw≤2600KB
- 当前基线全绿（首屏 79.7KB、CSS 19.0KB、最大块 391.7KB、索引 2047KB）
- package.json + quality-contract.md 登记

## 批次 C — 无障碍（feat(a11y) 0b99702）

- Layout.vue 注入 skip-link（跳到 #VPContent）
- custom.css 强化 :focus-visible（品牌色 outline，深浅主题自适应）
- scripts/a11y-check.mjs + tests/a11y.test.mjs（6 例）：lang、img alt、button/link name、h1、landmark；VPSwitchAppearance 白名单
- package.json + quality-contract.md 登记

## 批次 D — 可信度（feat(trust) f122206）

- docs/guide/verify-on-hardware.md：四步验证流程 + 证据模板 + 回填说明 + 常见疑问
- LabOverview.vue：「X / N 已实测」进度 + 指南入口；custom.css 加 .mcu-verify-summary
- config.mts：guide 侧边栏登记；nav:check 保护
- K5 收口：sidebar 全量补齐（批次 A 已完成），导览页无旧任务目录引用

## 关键决策

- **不伪造验证**：所有 hardware_status 保持 pending，只建机制（指南 + 总览入口）。
- **不重复接线 site:measure**：行为侧（延迟索引、减少动效）已由 test:browser 覆盖，perf:budget 只补体积维度。
- **config.mts 外科式提交**：每批提交前备份 → 摘除并行会话的 /projects/ 导航 → 提交 → 还原，避免把未跟踪的 docs/projects/ 死链带进提交态。
