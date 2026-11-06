# 实施计划：动画阅读体验修复

## 顺序（每条独立可验证）

### 1. D1 时长取主值
- 改 `docs/.vitepress/anim-decorate.mjs:89-92`：`animDuration` 取所有 `dur="<数字>s"` 的 `Math.max`。
- 验证：`npm run docs:build` 后，`/c/03-volatile.html` 的元信息应为 `12s 一轮`；在 `prefers-reduced-motion: reduce` 下 `svg.getCurrentTime()` 应 ≈ 10.8（第 ④ 阶段），画面出现结论字幕与完整波形。
- 回归风险：仅影响 `<figcaption>` 元信息文本、进度条 CSS 周期与静止帧时刻；不影响 SMIL 本体。

### 2. D2 组件标签渲染
- 改 `docs/.vitepress/config.mts` 的 markdown core rule：把 `<AnimFigure src="/anim/<name>.svg"[ caption="…"] />` 的 `html_block` 改写为现有 `emit(name, caption)` 输出。
- 验证：`/build/00-toolchain.html`、`/build/06-flash-debug.html`、`/c/00-c-in-mcu.html` 三页 `svg>0`、播放按钮存在、`data-anim` 正确。
- 印前回归：`npm run book:check` 必须通过，且 `mcu-book/` 无改动。

### 3. D3 手机端放大
- 改 `docs/.vitepress/theme/custom.css`：窄屏（`max-width: 768px`）下把 lightbox 的 `padding` 收窄、`card` 宽度放到接近满宽。
- 验证：375px 视口下 lightbox 内 SVG 宽 > 行内 284px，标签有效字号大于行内。

### 4. D4 放大视图可达性
- 改 `docs/.vitepress/theme/AnimFigure.vue`：`openLightbox` 后聚焦关闭按钮并锁 `body` 滚动；`closeLightbox` 还原焦点与滚动。
- 验证：打开后 `document.activeElement` 在对话框内；关闭后回到"放大"按钮；背景不再滚动。

## 验证命令

```bash
npm run docs:build          # 零死链
npm run anim:lint           # 源图未改，应保持通过
npm run book:check          # 印前链路零改动
npm run a11y:check          # 放大视图可达性改动
npm run test:browser        # 既有动画控件回归
```

另需真实浏览器取证：375px 视口 + 明暗两主题 + `prefers-reduced-motion` 开/关，逐条截图对照。

## 审查门

- `task_verify`：当前返回 `unverified`（`verification-baseline-unavailable`），必须如实报告，不能当作通过。
- 不新增门禁规则、不改既有测试断言；如需回归测试，单列为待评审项。
- 不提交、不推送、不合并——交由用户决定。
