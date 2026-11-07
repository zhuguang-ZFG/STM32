# B37：EPUB 阅读体验升级（位图封面 + 分节目录）与角标排查销账

日期：2026-11-07（Asia/Shanghai）。基线为已合并并通过双语 CI 的 `6ef844f`（PR #81，B36）。

## 角标排查（销 b34 挂账）

b34 审计曾记「ch05 收尾板角标 CH 06 / ch18 板 CH 19 疑似错标，留给资产批次」。
本批全量扫描 58 块 handdraw 汇总板（ch00–28 各 handdraw/mid-handdraw 2 张）+
6 块附录板：**每一块都满足「角标 = 文件章号 + 1」**，即全书**显示章号**
（docs/00 = 第 1 章）——58/58 一致，附录 A–F 同制。角标按显示章号标注是
既定约定，不是缺陷；b34 挂账就此销账。附带发现：`ch09-scan-sequence` 板内
「CH0–CH3 / CH16」为 ADC 通道号（扫描序列与内部参考通道 16），非章角标。

## EPUB 升级（本批主体）

1. **位图封面**：`render_cover_png()` 用 Chromium 对成品 HTML 的 `#cover`
   截图（1960×3124 PNG，约 130 KB），以
   `<item id="cover-image" properties="cover-image">` 入 manifest 并保留
   EPUB 2 `<meta name="cover">` 兼容。库管理 App 由此可显示封面缩略图
   （此前只声明了 meta 而没有图）。Playwright 不可用时优雅降级为无位图封面
   （EPUB 仍有效），测试不依赖它。
2. **分节级目录**：nav.xhtml 在每章/每附录条目下嵌套其 h2/h3 小节
   （锚点直跳，双语共 602 条小节链接）；NCX 同步两层（`dtb:depth=2`，
   599 个嵌套 navPoint，`<content/>` 自闭合、子 navPoint 为父内兄弟——
   首版误嵌在 `<content>` 内部，epubcheck 602 个错误后修正）。
3. 成品复核：双语 epubcheck 5.1.0 仍为 **0 错误 / 0 警告**；封面 PNG
   1960×3124 在包；nav 分节链接与 NCX 嵌套计数吻合。

## 测试

- `test_epub_build.py` 增至 **6 项**（新增：nav 嵌套分节链接与 NCX depth=2
  断言；夹具补一个带 id 的 h2）。全部通过。
- 全量 `unittest discover stm32-book/tests`：**195 项全部通过**。
- `tools/slop_lint.py` 对工具与测试无命中。

## 边界

- 封面截图使 EPUB 产物轻微依赖渲染环境（内容不依赖；无 Playwright 时降级）。
- 书稿正文、样式、资产零改动；本轮无 PDF 重建需求。
