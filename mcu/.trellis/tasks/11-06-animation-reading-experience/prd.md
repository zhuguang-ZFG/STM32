# 动画阅读体验：移动端、深色与减少动态效果

## Goal

修复书稿 SVG 动画在实际阅读中已复现的体验缺陷，使控件、标签与静止帧与图本身的时间轴一致，移动端"放大"真正放大。

## Confirmed Defects

| ID | 现象（实测） | 根因锚点 |
|---|---|---|
| D1 | `/c/03-volatile` 元信息显示 `1.5s 一轮`，实际主时间轴 12s；减少动效静止帧停在 `t=1.35`（第 ① 阶段），而代码注释要求停在末尾。全库 **30/111** 张首值≠主值，最大偏差 16 倍。 | `docs/.vitepress/anim-decorate.mjs:89-92` 取首个 `dur=`；`scripts/anim-lint.mjs:78` 用 `Math.max` |
| D2 | `/build/00-toolchain`、`/build/06-flash-debug`、`/c/00-c-in-mcu` 三页 `.anim-figure` 无 SVG、无按钮（空舞台）。 | 三份 md 用 `<AnimFigure src>`；站点规则只认 `![…](/anim/x.svg)`（`config.mts` `anim-figure-block`）；`mcu-book/build_html.py:63` 的 `ANIM_TAG` 认 `src` 形式 |
| D3 | 375px 视口：行内 SVG 284px，"放大"后仅 273.4px（比值 0.963），标签有效字号 6.71px→6.46px。 | `custom.css:591-599` card `width:min(94vw,900px)` + `padding:16px 18px` |
| D4 | 打开放大视图后焦点仍在 `BODY`；背景可继续滚动。 | `AnimFigure.vue:42-60` 无焦点管理与滚动锁定 |

**已否证**：深色模式下 SMIL 动画 `fill` 漏浅色——实测计算值为深色令牌（`rgb(241,245,249)`、`rgb(148,163,184)`），CSS 类规则胜出。

## Requirements

- R1：每项修复先有可复现证据（预期 vs 实际），修复后再取同口径证据对照。
- R2：只改站点渲染层（`docs/.vitepress/`）；不动 `docs/public/anim/*.svg` 源图、不动 `docs/*.md` 正文、不动 `mcu-book/`。
- R3：不新增门禁规则，不改既有测试断言，不弱化验证；不碰 11-02 未提交改动。
- R4：不提交、不推送、不合并，交由用户决定。

## Acceptance Criteria

- [ ] D1：构建后 `/c/03-volatile` 元信息为 `12s 一轮`；减少动效下 `getCurrentTime()` ≈ 10.8 且画面出现结论字幕。
- [ ] D2：三页 `.anim-figure` 均有 `svg`、播放按钮与 `data-anim`；`npm run book:check` 仍通过且 `mcu-book/` 无改动。
- [ ] D3：375px 下放大视图 SVG 宽 > 行内 284px，标签有效字号大于行内。
- [ ] D4：打开后焦点在对话框内，关闭后回到"放大"按钮，背景不滚动。
- [ ] `docs:build`、`anim:lint`、`book:check`、`a11y:check`、`test:browser` 结果按通过/失败/未验证分别报告。
- [ ] `task_verify` 若仍为 `unverified`，如实标注，不当作通过。

## Out of Scope

- 减少动效下进度条恒 `animation:none`（F8）：视为有意的降动设计，不追。
- 全站重设计、整本 PDF 重建、语言精修、静态题图继续微调。
- 新增边距/时长门禁规则。

## Technical Notes

- 30 张首值≠主值的清单已枚举；规范 §3 要求连续动画 `dur` 整除主 `dur`，故 `Math.max` 即主时长，与 `anim-lint` 口径一致。
- D2 若改 md 正文会改变印前 `<figure><img class="anim">` 结构，故选择在渲染层兜住。
- GitNexus 仅索引无关的 clideck；本项目按源码与构建产物取证，未使用图谱结论。
