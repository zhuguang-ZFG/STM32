# 精品书的标准与社区做法（2026-10-25 调研，附来源）

「精品/经典大典」不能是形容词，所以这份调研只收**可以变成验收条目**的东西：规范里写死的数字、社区项目实际在做的事、以及它们踩过的坑。

## 1. 中文排版的权威规范：W3C clreq

- 来源：*Requirements for Chinese Text Layout 中文排版需求*（W3C Working Draft，持续更新）<https://www.w3.org/TR/clreq>
- 可验收条目：
  - **行首行尾禁则**：行尾不得置收尾类标点（。，、；：）」』等），行首不得置起首类标点（「『（等）；遇到冲突时用均排把空白摊到该行各字之间。→ 我们的契约门可以对 PDF **逐行文本**检查行首/行尾字符集合。
  - **标点挤压**：中文标点占全宽的一半或半宽按体裁约定。Chromium 不实现 `text-spacing`/`text-autospace`——这条要在 PRD 里**明说做不到**（不假装达标），改为"仅做禁则与间距下限"。
  - 行首行尾对齐（两端对齐排法）在中文书是重要规则 → 我们已用 `text-align: justify`。

## 2. 开本与版心：中文图书出版惯例

- 来源：
  - 《图书出版印刷常用的开本成品尺寸以及常用术语》<https://m.douban.com/group/topic/34460755>：**787×1092 1/16（正 16 开）= 185×260 mm**，常见 40 行 × 41 字 ≈ 1640 字/面。
  - 四川大学学报《图书版式基本要求》PDF：**订口一边留白宜大于 20 mm**，天头/地脚/切口留白各有下限。
  - 出版之家《图书的版式设计》：标准 16 开 版心 140×220 mm、38 字×39 行，适用范围"教材（计算机、理工类）"。
  - 许昌学院学报《版面设计基本资料》：横排**行长 80–120 mm** 较合适，超过 120 mm 阅读速度下降；16 开五号字每行 39–40 字、行长 143–147 mm 已偏长。
- 可验收条目：
  - 开本 185×260 mm ✓（已定）。
  - **订口（内白边）> 20 mm** → 现在是 20 mm，要抬到 22 mm 才叫"大于"。
  - **每行字数 34–42 字、行长 ≤ 150 mm**：现在版心宽 = 185 − 20 − 16 = **149 mm**（按许昌学院那条 143–147 mm 的实测口径，已在偏长一侧）。P2 定案：把正文降到 9.5–10 pt 并收窄版心（或改双栏），由门测"每行字数"与"行长"。

## 3. 社区项目怎么做的（GitHub 实例）

- **Pro Git 2nd（`progit/progit2`、`progit/progit2-zh`）** <https://github.com/progit/progit2>
  - 做法：AsciiDoc 源 → `rake book:build` 同时出 HTML / EPUB / MOBI / PDF；中文分支额外装 `asciidoctor-pdf-cjk-kai_gen_gothic`。
  - 借鉴：**"中文 PDF 的字体必须专门解决"是社区十年前就撞到的坑**（与我们实测的 Type3 位图同一类问题）；一条源出多产物（HTML/PDF/EPUB）也是我们要的形态。
- **thematters/cjk-book-builder** — `docs/chinese-typography.md` <https://github.com/thematters/cjk-book-builder/blob/main/docs/chinese-typography.md>
  - 做法：CSS `@page { size: … }` 定开本；明确"中文书通常比西文书留更多天头地脚"，**天头 18 mm、订口（inner）留宽**，天头放小章节名。
  - 借鉴：与我们的 `@page` 版心 + 页眉方案同构；它的参数可直接作为对照表。
- **paged.js** <https://github.com/pagedjs/pagedjs>：CSS Paged Media 的浏览器 polyfill（我们 P1 已用，0.4.3 钉版）。
- 其它可对照的多产物工具链：`asciidoctor/asciidoctor`（DocBook/PDF/EPUB）、`crowdagger/crowbook`（Markdown → HTML/LaTeX PDF/EPUB）、`mdbook-pandoc`。

## 4. 印前（按需印刷）的硬数字

- 来源：Amazon KDP *Paperback Submission Guidelines* / *Set Trim Size, Bleed, and Margins* <https://kdp.amazon.com/help/topic/G201857950>
- 可验收条目：**不要出血时页面尺寸就是裁切尺寸**；要出血时每边加 0.125 in（3.2 mm）并从裁切线外延伸图元。→ 我们的 `--bleed 3` 默认关，与 KDP 的"无出血"口径一致；有出血时必须真的加 3.2 mm（不是 3 mm），这一条写进门里。

## 5. EPUB 的规范面

- 来源：*EPUB 3.3* <https://www.w3.org/TR/epub-33/>；EPUB Accessibility 1.1（W3C）；`epubcheck` 作权威校验器。
- 可验收条目：EPUB 3.3 结构（`mimetype` 存储、OPF、nav 两级、`dc:` 元数据）+ **无障碍元数据**（`schema:accessMode`、`accessibilityFeature`、`accessibilitySummary`）+ `epubcheck` 0 error。作为"精品"的电子书形态，无障碍元数据是社区公认的及格线。

## 6. 由此新增的"精品"验收条目（并入 PRD）

| # | 条目 | 判定方式 |
|---|---|---|
| Q1 | 订口 > 20 mm（取 22 mm） | 契约门测版心左右边界 |
| Q2 | 每行字数 34–42、行长 ≤ 150 mm；16 开单栏或双栏在 P2 定案 | 契约门对正文行做统计 |
| Q3 | 行首/行尾禁则：逐行检查收尾类/起首类标点 | 契约门扫 PDF 文本行 |
| Q4 | 标点挤压/中西文间距：**明说不做**（引擎不支持），只在文档里写清 | 文档陈述，不装达标 |
| Q5 | 图/表编号与图题统一（图 1-1 式），正文可引用 | 契约门抽查 + 目录/索引一致 |
| Q6 | 索引带页码、按统一序（码位序，见 design） | 契约门抽查 |
| Q7 | EPUB 3.3 + 无障碍元数据 + epubcheck 0 error | `check_epub` + epubcheck |
| Q8 | 出血版按 3.2 mm（KDP 口径）；无出血版=精确裁切尺寸 | 契约门测 MediaBox |
| Q9 | 有勘误页与贡献者页（社区参与入口） | 结构清单 |