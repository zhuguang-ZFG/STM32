# 架构图层规范（stack-diagram 路线）

> 2026-11-03 随 11-02-skill-remaster 任务建立。第一批 4 张：`toolchain-pipeline`（B0）、`idf-anatomy`（P3）、`wifi-stack`（P8）、`rtos-side-by-side`（对比 0）。

## 1. 三种图各管什么（分工不许混）

| 图层 | 管什么 | 技术 | 目录 |
|---|---|---|---|
| **动画** | 动态因果——"它怎么动" | SVG+SMIL 四武器（爬线/生长箭头/节拍脉冲/接力流转） | `docs/public/anim/` |
| **架构图** | 静态结构——"谁连谁、数据去哪" | stack-diagram（白底瓷砖+官方 logo+正交连线） | `docs/public/arch/` |
| **题图** | 情绪——"这一章的气质" | 手工 SVG 线稿（纯矢量路线） | `mcu-book/` art 体系 |

判断口诀：**动的是因果→动画；不动只看连接→架构图；不解释机制→题图。**同一主题可以三图并存（如 B0：架构图给全景、动画演接力）。

## 2. 产图工作流（skill：caru-ini/stack-diagram，装于 `~/.agents/skills/stack-diagram`）

1. **定内容**（nodes/groups/edges），全部事实对账章节原文与已核事实（RM0090/CMSIS），未核对的写"以手册为准"；
2. **取图标**：`python <skill>/scripts/fetch_icons.py <icons-dir> name…`——svgl→devicon→gilbarbara 自动链；品牌缺失用 `name=官方URL`（ST/Espressif/FreeRTOS/RT-Thread 均如此取到）；抽象概念用 `name:lucide/<icon>`；**不许 simple-icons、不许重涂 logo**；手动补的图标要登记进 `manifest.json`；
3. **手写源 HTML**：以 skill 的 `assets/template.html` 为底，坐标按 `references/geometry.md`（节点 132×100、行距 ≥140、组框外扩 24/60/150、竖边走 box-bottom→tile-top、肘形边走空带走廊）——**先列每条竖/肘段的 x 走廊，确认不穿任何节点框再写**；组框标签固定在左上角（起点 = 组左 + 12px），**任何竖边都不许从标签横带里走过**：多行分组若把行间距留在标签下方，拆成上下两个组框必被第一列竖边穿字，改用「一整块高框（标签在最上、竖边全在其下方）+ 每行行首身份砖」表达归属；
4. **构建与渲染**：
   ```bash
   python <skill>/scripts/build.py 源.html icons/ 产物.out.html --fonts <skill>/assets/fonts
   python <skill>/scripts/render_png.py 产物.out.html 图.png --selector .canvas --scale 2 --single
   ```
   自包含 out.html 是事实源；PNG @2x（2440px 级）进 `docs/public/arch/`；逐项目检：无穿线、无白底白 logo、组标签不压节点、组标签横带无竖边穿过、无画布裁切；
5. **入章节**：图放对应小节开头，引导句一句（非模板腔、破折号 ≤1）、alt 写"表达结构一句话"；
6. **过门**：`docs:check`（注意「成书插图数」CLAIMS 会因新增独立行图片变化——同步 `docs/reference/book.md`、`docs/reference/changelog.md`、`mcu-book/README.md` 三处与 `scripts/docs-check.mjs` 的正则口径）→ `reading:check` → `docs:build` → `book:pdf` + `book:pdfcheck`。

## 3. 契约

- 源 HTML 与图标清单存 `scripts/arch-diagrams/`（icons/ 共享目录 + manifest.json），**PNG 不许直接手改**——改源重渲；
- 中文字体栈：模板 font token 已追加 `Microsoft YaHei / PingFang SC / Noto Sans CJK SC`，`lang="zh-CN"`；
- 印刷兼容：PNG @2x 由 `build_html.py` 的 `_resolve_asset_target` 从 `docs/public/` 自动内嵌 data URI，PDF 端无需额外处理；
- 图内事实纪律与正文同级：地址/引脚/组件名必须二源核对；
- 新图必须被至少一个章节页引用（孤儿图不算交付）。
