# 附录 G（开源地图）接入记录

2026-10-26。用户要求在书里补充 GitHub 开源项目与社区的影响。

## 做了什么

1. **新增手写附录 G**：`mcu-book/book/G-开源地图.md`，manifest 增 `appendix-oss-map`。
   - 仓库地图：30 个仓库（星标/许可/先读路径/对应章节），星标与 `archived` 均按 GitHub API 当日复核。
   - 六个知识点：每条「原理一句话 + 机制 + 踩坑现场 + 自己验」，按用户要求改成形象化讲解。
   - 社区提问五件事、复刻清单、许可边界表、证据口径。
2. **术语索引顺延**：自动生成的术语索引从附录 G 改为附录 H
   （`build_print.py` 的目录字面量 + `print/index.py` 的页眉字面量）。否则纸上顺序会变成 A–F、H、G。
3. **契约同步**：`tests/test_build.py` 的附录集合加入 `appendix-oss-map`；附录小节数改为按 manifest 推导。

## 两次真实踩坑（都已修）

### 字体子集必须重出

新增正文引入「栋 / 屋 / 汤 / 炖」等字，旧子集没有 → Chromium 回退到
`JAAAAA+SimSun`（p845）与 `KAAAAA+MicrosoftYaHei-Bold`（p1051），印前字体门直接红。
重出九族子集后复查：四个新字全部落在 serif/sans 四体里；`筛 ↗ 🧮 ★ ÷` 也齐。

**命令要点**：`subset_fonts.py` 的 `--chars-from` 是**替换**默认根，不是追加。
默认根包含 `docs`、`docs/public`、`mcu-book/book`、`manifest.json`、`build_html.py`——
少一个就会把构建器注入的字面量（🧮 计算器、↗ 箭头）漏掉，历史上前一次就是这么回退到雅黑的。
**正确姿势：不带 `--chars-from`**。

### 路径必须指到文件，不能凭印象

初稿写了 `include/libopencm3/stm32/f4/memorymap/`（目录）与 `Core/Include/core_cm4.h`。
实测：libopencm3 的 f4 目录下是**单个** `memorymap.h`（7755 B），没有 memorymap 子目录；
CMSIS_6 的路径是 `CMSIS/Core/Include/core_cm4.h`。两处已改。

## 验证

- `art_guard --yuyu --dir`：88 枚 0 违规（附录不带题图）。
- `build_html.py`：88 章 + 7 附录，附录 G 在目录里。
- `check_pdf.py`：12 门（字体门在新子集上通过后）。
- `pytest`：51 passed（含新增 `test_art_guard.py` 四条）。
