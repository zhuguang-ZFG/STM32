# B44：动画/插图/双语文本质量波（三代理并行）

日期：2026-11-07（Asia/Shanghai）。基线 `adb2853`（B43 合并）。三个 PR 合并前
全量 195 项测试通过；本文件为三代理工作的总审计。

## 代理 A：动画动作质量定格审查（零修复项，结论合格）

`assets/animations/` 的 **37 个 sample-\* 动画**全部经 Playwright 定格审查
（`animation-play-state:paused` + WAAPI `currentTime` 定格在各自周期的
0% / 50% / 90%，脉冲式动画加拍峰值帧），另做渲染级 getBBox 文字几何检查：

- 37/37 首帧均为完整可读的静态构图（标题、流程盒、台账齐全，PDF 口径达标）。
- 每条动画都有分步教学语义（步进高亮 / 路径行走 / 事件脉冲），无一例空转弹跳。
- 若干「三帧全等」文件经峰值帧与 CSS 源码复核为**短脉冲序列设计**（占空比
  约 3% 恰落在采样点之间），非静画或坏动画。
- `i2c-transaction.svg`：`<style>`/`<animate>`/`@keyframes` 计数均为 0 ——
  **有意静态**，与 test_sample_svg_c 合同（577–579 行）一致，未改。
- 生成器零改动，无哈希更新。范围内勘误：sample-\* 动画实为 37 个（任务书
  误写 54，另含静态 sample-\*.png 与 diagrams 的 sample-\*，不在动画合同内）。

## 代理 B：几何机械重扫（315 个 SVG，43 处修复）

Playwright + Chromium 逐文件加载，`getBBox()` 映射回 viewBox 查文本出框、
重叠、空文本；首轮 bbox 判重叠报 59 处，逐处截图目检证实 35 处为手写字体
行框衬垫假阳性，**判据升级为 canvas measureText 真实墨迹盒**（B24 的 30%
bbox 阈值降级为 SOFT 记录）后假阳性清零。

修复 43 处（全部改生成器，未手改 SVG）：

- **空文本节点 35 个 / 13 文件**：classic-03-init-code、gpio-blink、
  iwdg-window、sample-12-boot-compare、sample-f-ask-before 及 handraw 24 个
  （`multi()` 空行占位）。修复：svgkit `code()` 空行保留行位不发 text、
  anim_sys 表格空角头跳过、hd `text()` 空串跳过、两处生成器删遗留调用。
- **文字被遮/相撞 8 处 / 4 文件**（内容实际丢失）：
  - `ch28-memory-regions`：卡内说明超出 172px 卡宽被邻卡盖住（B38 根会话
    自检漏掉、本次机械扫描抓到）→ 卡内 15px→13px + 语义换行，内容零删减。
  - `ch09-scan-sequence`：公式说明尾部被「注入组」卡盖住 → 21px→18px。
  - `sample-03-gpio-bsrr-flow`：ledpulse 圆点盖住 "active-low" 尾字母 → 移位。
  - `classic-03-open-drain`：面板标题尾被 ODR 徽章盖住 → 标题锚点左移。
- 重生成 7 个 diagrams/animations SVG + 9 个 handraw SVG/PNG（5 张字节不变，
  证实空文本删除视觉零影响）；ch24-modes / ch25-clock-math 落后于当前 hd.py
  的两份提交版重生成回归确定性输出。
- **终扫：diagrams/animations/handraw 全部 BAD 0 / ISSUES 0**。
- `test_sample_svg_c.py` 机械更新 5 行 text_hash（几何不变的文件哈希不变）。

## 代理 C：双语文本等价审计（5 处真实漂移修复）

- **29 块新板**（git diff-filter=A 实测，三波合计 29：12+9+8，含 ch05 三块）
  逐块比对 zh/en 的 alt、图注、锚句事实集合：26 块等价，**3 处漂移已修**：
  - ch20-cube-suite：en 两处丢「90%」（图注 "most scenarios"、锚句
    "most of what you will do"）→ 补回 90%。
  - ch27-tls-prereqs：en 锚句被截断为 "…negotiated"（半句）→ 按 zh 补全
    「版本/套件与对端身份」。
  - ch28-memory-regions：en 图注误用锚句的「隐藏耗尽」替换了板子结论
    「malloc 返回空数据**不是恢复策略**」→ 改回。
- **全书 alt 漂移扫描**：490 对 `<img>`（zh=en 逐章按序配对，无缺失），
  机械筛（数字集合差 + 长度比）命中 25 对，逐对核实为**实漂移 2 处**：
  - en/02 sample-02-flash-latency：alt 丢「0/1/2 等待周期」、图注缺频段主题
    与「Knowledge track」标记 → 补齐。
  - en/27 network-debug-ladder：层级列表漏 IP 层 → 补 "through IP, TCP"。
  - 其余 23 对为误报（拼写数字、en 增补有 zh 支撑、CJK 密度长度比）。
- 只改 4 个 en 文档（02/20/27/28），zh 零改动；slop_lint 无命中。

## 全量验证（合并前）

- 195 项测试通过；`build_html.py --check` 双语 PASS；`check_assets.py`
  全部通过；四份改动文档 slop_lint 无命中。
- ch28-memory-regions 修复前后由根会话 Read 复核（修复前「嵌套中断」
  「保存上下文」「复计数」确实不可见）。

## 追加：内容文档序列化形态修复（读者报障「不符合规范」）

读者打开 EPUB 报「Can not load content here. Does not meet specifications」。
根因：B36 的命名空间迁移让 lxml 把全部内容文档序列化为 **`<html:html
xmlns:html="…">` 前缀形态**——XML 合法（epubcheck 通过），但按 HTML 模式解析
内容文档的阅读器把 `html:xxx` 当未知元素，整章拒绝渲染。

修复（`_to_xhtml_document`）：以 `nsmap={None: XHTML_NS}` 的默认命名空间根
重建树（零前缀输出），内联 SVG 子树自带 `xmlns="…/2000/svg"` 默认声明
（与手写 XHTML+SVG 一致），XML 声明改双引号，`<head>` 首位补
`<meta charset="utf-8"/>`；SVG 源里自带的 `xmlns` 属性复制时过滤防重复声明。
双语重打包后：epubcheck 仍 0 错 0 警，MuPDF（真实 EPUB 引擎）打开渲染正常
（zh 1033 页 / en 1140 页合成页，648/650 条目录），`html:` 前缀残留 0。
