# 参考项目调研：御舆书（D:/Users/claude/claude-code-book-main）vs 现行手绘风

用户 2026-10-26 追加参考项目。结论记录供风格拍板。

## 御舆的做法（yuyu-book/yuyu_book/）

1. **题图 = 64×64 极简徽记**（ch01–ch15.svg）：每章一枚小图，viewBox 64×64、stroke-width 2.1、`currentColor` 全程、**零滤镜、零 id、零 href**。手绘感来自 path 曲线本身（全书 143 条 path：M 270 / C 139 / L 123——贝塞尔曲线占比高），不靠噪声滤镜。
2. **`art.py` 76 行的准入审计**：`_BANNED` 列表硬拒 `<script>/<style>/<iframe>/id=/href=/url()`——20 枚同页内联不会撞 id、不会有外部引用；每枚 6KB 预算、封面 20KB。
3. **印前明确无滤镜**：`style.py:801` 注释原话——"no filter: the print engine rasterises a filtered subtree, which would turn every plate's labels into outlines — unsearchable, and most of a 31MB PDF"。即：**御舆用纯几何线稿正是为了绕开我们踩过的光栅化坑**。
4. 封面是 1000×470 大图（插画感的"板画"），但同样零滤镜——手绘感来自粗细分级（1.8/3.4/5）+ opacity 分层（.45/.8/1）的双描+淡影，与我在 mcu art.py 里做的 defs 双描同构，但人家不依赖 filter 实现。

## 与现行 mcu 方案的差异

| 维度 | 御舆 | mcu 现行 |
|---|---|---|
| 手绘感来源 | path 曲线+笔压分级+透明度分层 | feTurbulence+feDisplacementMap 滤镜 |
| 印前 PDF | 纯矢量，文字可搜索 | 分部图被 Chromium 光栅化（≈190-300dpi） |
| 同页内联安全 | 无 id 零冲突审计 | 每枚独立 filter id（需 guard 防重名） |
| 画面复杂度 | 极简徽记（3-6 笔） | 叙事性场景（5-15 元素+中文标签） |
| 中文字标签 | 无（纯图形） | 有（font-size≥7 的丝印字） |

## 待拍板

A. **保持现行**：滤镜路线已过 12 门（光栅化在 200dpi 下目检可接受），叙事性题图信息量高。
B. **转御舆路线**：题图去滤镜改曲线手绘（重画 3 枚试点），印前全矢量；文字标签保留但移出滤镜组（已是现状）；分部图/封面同样去滤镜改双描线+透明度分层。
C. **混合**：题图（320×88 横幅、带标签）保持滤镜；封面与分部图去滤镜改御舆式笔压分层——印前光栅化只发生在章首，正文搜索性不受影响。
