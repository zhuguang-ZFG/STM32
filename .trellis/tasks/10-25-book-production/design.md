# 设计：书籍工艺层（印前 PDF + EPUB3）

## 1. 边界

```
                    ┌─ docs/**/*.md（正文，冻结）
内容源 ──┤
                    └─ mcu-book/book/*.md（附录，冻结）+ manifest.json（结构/元数据，可加字段）
                          │
        ┌─────────────────┼──────────────────┬─────────────────┐
        ▼                 ▼                  ▼                 ▼
   build_html.py      build_print.py     build_epub.py     check_*.py
   （屏幕单文件 HTML，   （印前 PDF，        （EPUB3，          （三条契约门）
    现有，保持）          16 开/可选出血）      nav+OPF+封面）
```

三条输出**共用同一份正文与元数据**，但**各自一套版式**：屏幕版继续用现有 CSS；印前用新增印刷样式；EPUB 用阅读器样式（最简，交由阅读器调）。

## 2. 目录与新增文件

| 路径 | 作用 |
|---|---|
| `mcu-book/print/book-print.css` | 印刷版式：`@page`（开本/版心/页眉页脚）、`@page :first`/命名页（封面、结构页）、章首页、正文/标题/代码字体、`target-counter()` 目录页码、`counter(page)`/`counter(pages)` |
| `mcu-book/print/book-print.js` | 分页引擎驱动（用 Playwright 打开渲染 HTML、注入引擎、等分页完成） |
| `mcu-book/print/fonts/*.woff2` + `OFL.txt` + `provenance.json` | 子集字体与许可/来源登记（SIL OFL 1.1） |
| `mcu-book/subset_fonts.py` | 用 `fontTools` 从原始字体生成子集（覆盖全书用字 + 保险集），并写 `provenance.json` |
| `mcu-book/build_print.py` | CLI：`--out-dir`、`--bleed 0|3`、`--browser`、`--sample N`（原型用 2 章）、`--check` |
| `mcu-book/build_epub.py` | CLI：`--out-dir`、`--embed-fonts`、`--check` |
| `mcu-book/check_pdf.py` | **改为**印前契约门（见 §5） |
| `mcu-book/check_epub.py` | EPUB 结构门 + `epubcheck` 包装 |
| `mcu-book/tests/test_print.py` / `test_epub.py` / `test_fidelity.py` | 单测（样式关键断言 / EPUB 结构 / 内容同一性） |
| `mcu-book/print/index.py` | 索引生成（术语抽取 → 拼音序 → 页码） |

## 3. 关键接口与契约

```
python mcu-book/subset_fonts.py --source <ttf/otf> --family "Noto Serif SC" --chars-from docs/ mcu-book/book/ --out mcu-book/print/fonts/
    → book-print-<family>-<weight>.woff2 + provenance.json（源文件 SHA256、许可、生成时间、字符覆盖数）
    → 缺字（书里出现但子集未覆盖）必须报错退出，不许静默回退系统字体

python mcu-book/build_print.py [--out-dir mcu-book/dist] [--bleed 0|3] [--sample N] [--check]
    → mcu-book/dist/mcu-deep-book-print.pdf（精确 185×260；--bleed 3 时 191×266 + 裁切标记）
    → --check：构建到临时目录并跑 check_pdf.py 的同一套断言

python mcu-book/build_epub.py [--out-dir mcu-book/dist] [--embed-fonts] [--check]
    → mcu-book/dist/mcu-deep-book.epub（EPUB3）

python mcu-book/check_epub.py [epub] [--manifest ...]        # 结构 + epubcheck
python mcu-book/check_pdf.py  [pdf] [--manifest ...]         # 印前契约（语义变更，见 §5）
```

### 版式参数（写死在样式里，由门断言，不靠"看着对"）

参数来源与自洽性验算（依据见 `research/standards-and-community.md`：正 16 开 185×260、订口回白 > 20 mm、
16 开五号字每行 39–40 字、版心 140×220 的教材惯例、行长 > 120 mm 阅读速度下降）：

| 项 | 值 | 自洽验算 | 断言方 |
|---|---|---|---|
| 开本 | 185×260 mm（出血版 +3.2 mm/边，KDP 0.125 in） | — | `check_pdf` |
| 天头 / 地脚 | 20 / 22 mm | 版心高 = 260 − 42 = **218 mm** ≈ 惯例 220 | `check_pdf` 抽页测文本边框 |
| 内白边（订口）/ 外白边 | 24 / 23 mm | 订口 **24 > 20 mm**（出版惯例下限）；内略大于外，便于装订 | `check_pdf` |
| 版心 | **138 × 218 mm** | 每行 ≈ 138 / 3.53（10 pt 汉字宽）= **39 字**（惯例 39–40）；行长 138 mm ≤ 150；每面 ≈ 218 / 5.64（行距 1.6）= **38–39 行**（惯例 38–40） | `check_pdf` 统计行宽与每行字数 |
| 正文 | Noto Serif SC 10 pt / 行距 1.6 / 两端对齐 | — | 样式单测 + `check_pdf` 字号分布 |
| 标题 | Noto Sans SC：章题 20 pt、节 13 pt | — | 同上 |
| 代码 | Cascadia Mono 8.5 pt、允许折行、不缩字号 | — | 样式单测 |
| 符号回退 | emoji（Noto Emoji）+ 符号（Noto Sans Symbols 2）+ 数学（Noto Sans Math） | 全书符号集实测需要这三支互补（☐ ✕ ⟺ 等无一族能全包） | 子集门的**并集**断言 |
| 页眉页脚 | 偶页书名 / 奇页当前章名 / 页脚居中页码 | — | `check_pdf` 逐页比对 |
| 页码 | 正文 `counter(page)` 从 1；封面与前置页不编 | 末页必须 N/N；分子不得 > 分母 | `check_pdf` |
| 中文禁则 | 行尾不收尾类标点、行首不起首类标点（`line-break: strict` + 逐行检查） | — | `check_pdf` 逐行扫 |
| 标点挤压 / 中西文自动间距 | **不做**（Chromium 无 `text-spacing`/`text-autospace`） | 文档明写做不到，不假装达标 | 文档陈述 |

## 4. 分页引擎选型（P1 原型定案）

**首选 `pagedjs`（0.4.3，钉版本）**：跑在已装的 Chromium 里，复用 Playwright 链，无需新系统依赖。

原型判据（任一不达标即换 `@vivliostyle/cli` 11.4.0）：

1. 产出 MediaBox 精确 185×260 mm（±0.5 mm），内容无整体缩放；
2. `target-counter()` 能把目录页码解析成真实页码；
3. `@page` 页眉页脚 margin box 正常渲染，奇偶页规则生效；
4. 字体嵌入不是 Type3（`page.get_fonts()` 全部为 TrueType/CFF 子集）；
5. 2 章样本分页耗时 < 30 s，线性外推到 90 章可接受（若 88 章 > 8 min 则换引擎）。

## 5. 契约门语义变更（`check_pdf.py`）

旧门判的是"Chromium 打印那份 A4 PDF"的自洽性；新门判**印前契约**：

| 断言 | 失败样例（必须各留一次报错原文） |
|---|---|
| MediaBox == 185×260（或 191×266 with bleed） | 改成 210×297 即红 |
| 无 Type3 字形（真字体嵌入） | 换回系统字体路径即红 |
| 目录页码与正文实际起始页抽检 ≥10 章一致 | 手工改一个目录页码即红 |
| 末页 N/N，且任何页分子 ≤ 分母 | 复现旧的 `713 / 712` 即红 |
| 结构页（封面/版权页/目录/分部隔页）无页眉 | 给封面加页眉即红 |
| 逐页页眉与映射一致 | 改一章标题即红 |
| 版心边界（抽 10 页测文本 bbox） | 版心参数改错即红 |

## 6. 内容同一性门（R7）

```
对每一章：
  A = 现有 HTML 产物抽出该章文本（现有 build_html.audit 已有章节边界）
  B = 印前 PDF / EPUB 抽出该章文本（按章首页锚点/文档边界切分）
  归一化：去页眉页脚与页码、折叠空白、统一连字符与全半角
  A_norm == B_norm 否则报点名差异（首处不同位置 + 上下文）
```

抽样策略：全量 88 章都跑（文本抽取很便宜），失败时报前 3 章差异。

## 7. 索引生成

- 词源：`docs/reference/glossary`（术语页）∪ 正文中的 `**术语**` 与 `` `code` `` 出现（按 manifest 的 `sources` 许可过滤）。
- 每词记录首次/全部出现页（分页引擎提供 `page` 元数据；`paged.js` 的 `afterPageLayout` 钩子可收集元素→页码映射）。
- 排序：拼音（用 `pypinyin`？—— 避免新依赖：改用 Unicode 码位序并在样式里说明；若你要严格拼音序再引入依赖）。**决策：v1 用码位序，PRD 的"拼音序"降级为实现说明中的待办**（避免为一个排序引依赖）。
- 输出：附录 G《术语索引》，两栏排版。

## 8. 兼容与回滚

- 旧路径 `build_html.py --pdf` 保留到 P4 通过：`book:pdf` 语义在 P4 后切到 `build_print.py`；切换提交单独一个，便于 revert。
- 站点页面与 README 的产物名在 P7 统一改口径。
- 任一阶段失败可只 revert 该阶段提交；样式/字体/构建器都是新增文件，不与旧链路耦合。

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| paged.js 在 713 页上慢/内存高 | P1 原型给出耗时外推；超过阈值换 vivliostyle（同 CSS 思路） |
| 字体子集漏字（正文含生僻字/emoji/箭头） | 子集以"全书用字 + 保险集（GB2312 常用 + 标点 + 箭头/框线）"生成；构建时再校验一次缺字即报错 |
| Chromium 仍产出 Type3 | 门直接断言无 Type3；若 only-workaround 是位图回退，改为强制 `@font-face` + `font-variant-ligatures: none` 并用 `page.get_fonts()` 复核 |
| 目录页码与实际不符（分页引擎差异） | 门抽检 ≥10 章；不符则改用 vivliostyle；不以"看着差不多"放过 |
| EPUB 内 SMIL 动画/交互组件保真 | 动画降级为静态首帧图（复用 `docs/public/anim/*.svg`），交互组件降级为文字说明（与现有 HTML 版同口径） |
| CI 时长与体积 | 字体子集 ≤8 MB/族、EPUB ≤15 MB、新增步骤 ≤10 min；超限则收窄子集与图片分辨率 |
| ubuntu-24.04 缺 `epubcheck` | CI 里 `apt-get install -y epubcheck`（含 JDK 依赖）；本机无 Java 时 SKIP 并给提示 |