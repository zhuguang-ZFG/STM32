# 执行计划：书籍工艺层

约定：每期一个提交；`git add` 只列本任务路径（video 在途改动一律不动）；每期跑该期「验证命令」并把输出摘要写进 `research/verification-log.md`；任何 FAIL 先修再进下一期。

---

## P0 · 复核门：要改的测试与策略（**需你确认后再动**）

| 文件 | 动作 | 理由 | 是否放宽断言 |
|---|---|---|---|
| `mcu-book/tests/test_print.py` | 新增 | 印刷样式关键断言（开本、版心、字号、字体族、`@page` 规则、超长代码折行） | 否（新增） |
| `mcu-book/tests/test_epub.py` | 新增 | EPUB 结构（mimetype 存储方式、OPF 元数据、nav 两级、每章一文档、封面存在） | 否 |
| `mcu-book/tests/test_fidelity.py` | 新增 | 内容同一性：逐章文本归一化后一致（含「故意改一个字即红」的反例） | 否 |
| `mcu-book/tests/test_check_pdf.py` | **改写** | 它现有断言编码的是**旧 A4 产物的契约**（页脚 `N / total`、`total = page_count - 1`、A4 尺寸）。印前门换的是**判定对象与口径**，不是把门槛降低：开本断言更严（精确 185×260）、新增无 Type3、目录页码一致、分子≤分母 | 否——旧口径作废，新口径更严 |
| `tests/workflow.test.mjs` | 修改 | CI 新增印前/EPUB 步骤与 `epubcheck` 安装；断言「两件产物都在产物生成后校验」 | 否（外推既有严格性） |
| `package.json` | 修改 | 新增 `book:print`、`book:epub`、`book:epubcheck`；`book:pdf` 语义在 P4 后切到印前构建器 | 否 |

复核门 G1：确认上述清单；`test_check_pdf.py` 的改写理由是否成立（判据：新断言集合是旧集合的超集，且旧集合中与 A4 绑定的项被"改成印前口径"而不是删除）。

**回滚点**：本任务尚未产生代码改动，回滚即丢弃任务目录。

---

## P1 · 引擎原型与选型定案（R1/R2）

1. `python mcu-book/subset_fonts.py ...`：先用 2 章样本的字符集产出一份最小子集（验证流水线，不追求覆盖）。
2. `mcu-book/print/book-print.css`：`@page`（185×260、版心、页眉页脚 margin box）、封面/结构页命名页、正文/标题/代码字体、`target-counter()` 目录页码。
3. `mcu-book/build_print.py --sample 2`：Playwright 打开渲染 HTML → 注入 `pagedjs` → 等分页完成 → `page.pdf({preferCSSPageSize: true})`。
4. 用 §4 的 5 条判据逐条量：尺寸、目录页码、页眉页脚、字体类型（`page.get_fonts()`）、耗时。

**验证命令**
```bash
npm i -D pagedjs@0.4.3                    # 版本钉住
python mcu-book/subset_fonts.py --sample 2
python mcu-book/build_print.py --sample 2 --out-dir .temp/print-proto
python - <<'PY'
import fitz; d=fitz.open('.temp/print-proto/mcu-deep-book-print.pdf')
print('尺寸', d[0].rect, '| 页数', d.page_count)
print('字体类型', {f[3] for f in d[2].get_fonts()})   # 必须非 Type3
PY
```
**判据未过** → 同一 CSS 换 `@vivliostyle/cli` 重跑，记录两组数据后定案。
**回滚点**：删除 `.temp` 样本与新增样式/脚本（纯新增）。

---

## P2 · 全量印前排版（R1/R2）

1. 字体子集改为「全书用字 + 保险集」，产出 `mcu-book/print/fonts/`（含 `OFL.txt`、`provenance.json`：源文件 SHA256、许可、生成参数、覆盖字符数）。
2. 全量渲染 88 章 + 6 附录；`--bleed 3` 走同一份样式（页面扩 6 mm + 裁切标记）。
3. 抽检 10 章：正文文本 bbox 未越出版心、代码块未横向溢出、表格未断裂到不可读。

**验证命令**
```bash
python mcu-book/build_print.py --out-dir .temp/print-full
python mcu-book/build_print.py --bleed 3 --out-dir .temp/print-bleed
python - <<'PY'
import fitz
for p in ('.temp/print-full/mcu-deep-book-print.pdf', '.temp/print-bleed/mcu-deep-book-print.pdf'):
    d=fitz.open(p); print(p, round(d[0].rect.width,1), round(d[0].rect.height,1), d.page_count)
PY
```
**回滚点**：revert 本期；旧 `build_html.py --pdf` 链路未动。

---

## P3 · 前置/后置页、目录页码与索引（R3/R4）

1. 版权页（书名/版本/日期/许可/作者/来源与冻结点摘要/构建说明）。
2. 目录：分部 → 章 → 节三级，页码由 `target-counter()` 产出。
3. 索引：`mcu-book/print/index.py` 抽取术语 → 页码映射（`paged.js` 的 `afterPageLayout` 钩子收集）→ 附录 G。
4. 样式：索引两栏；目录三级缩进；不跨页断行。

**验证命令**
```bash
python mcu-book/build_print.py --out-dir .temp/print-front
python - <<'PY'
import fitz, re
d=fitz.open('.temp/print-front/mcu-deep-book-print.pdf')
toc=[p for p in range(5, 20) if '目录' in d[p].get_text()]
print('目录页候选', toc)
print('抽一条目录行:', re.search(r'.*\.\.\..*', d[toc[0]].get_text()) is not None)
PY
```
**抽检 ≥10 章**：目录上写的页码 == 该章首页物理页（差值为前置页偏移，口径写死在门里）。

---

## P4 · 页码页眉自洽 + `book:pdf` 切到印前（R5）

1. `@page` 用 `counter(page)/counter(pages)`；封面与前置页不编号；正文从 1。
2. 奇偶页眉（偶页书名 / 奇页当前章名）、章首页与结构页无页眉 —— 全部由 CSS 声明，删掉 PyMuPDF 事后盖章那一步。
3. `package.json`：`book:pdf` → `build_print.py`（同一提交内同步 `docs/reference/book.md` 的产物名）。
4. 末页必须 N/N；门加「分子 ≤ 分母」回归。

**验证命令**
```bash
python mcu-book/build_print.py --out-dir .temp/print-final && python mcu-book/check_pdf.py .temp/print-final/mcu-deep-book-print.pdf
```
**故意失败样例**：把 `counter(pages)` 改成常数 712 → 门必须红（复现旧 `713 / 712` 的错误形态）。

---

## P5 · EPUB3（R6）

1. `mcu-book/build_epub.py`：每章一 XHTML（正文 HTML 复用现有渲染结果，链接改为文档间锚点）+ `nav.xhtml`（分部/章两级）+ OPF（标题/作者/语言/版本/封面）+ 封面图（复用 `scripts/gen-og-cover.py` 的思路另出 `cover.jpg`，1200×1600）。
2. 动画降级为静态首帧图；交互组件降级为文字说明（与 HTML 版同口径）。
3. `mimetype` 必须以存储方式作为第一个条目；zip 无多余目录项。
4. `mcu-book/check_epub.py`：结构断言 + `epubcheck` 包装（本机无 Java → SKIP + 安装提示）。

**验证命令**
```bash
python mcu-book/build_epub.py --out-dir .temp/epub
python mcu-book/check_epub.py .temp/epub/mcu-deep-book.epub
epubcheck .temp/epub/mcu-deep-book.epub 2>&1 | tail -3     # 本机 JDK 17 在，可直接跑
```

---

## P6 · 契约门与接线（R8）

1. `check_pdf.py` 重写为印前契约（§5 七条断言）；`test_check_pdf.py` 同步改写（P0 已声明）。
2. `book.yml` / `quality.yml`：产出印前 PDF 与 EPUB 并校验；`apt-get install -y epubcheck`。
3. `local-gates.{ps1,sh}`：新增 `book:print`、`book:pdfcheck`、`book:epub`、`book:epubcheck`（本机无 Java 时后者 SKIP）。
4. `tests/workflow.test.mjs` 外推断言。

**验证命令**
```bash
node --test tests/*.test.mjs
python -m unittest discover mcu-book/tests -v
python -m ruff check .
sh scripts/local-gates.sh --only book:pdfcheck
```

---

## P7 · 收口

1. `docs/reference/book.md`、`mcu-book/README.md`：改成两件产物（印前 PDF / EPUB）的口径与本地命令。
2. `.trellis/spec/docs-site/quality-contract.md`：新增书籍工艺契约（开本/版心/字体/目录页码/内容同一性/EPUB）。
3. 内容同一性对 88 章全量通过；`research/verification-log.md` 记录每期命令与故意失败样例报错原文。
4. `task_verify` 三分报告；全量 `local-gates`。
5. 若 A4 版退役：单提交删除其产物路径引用（旧构建函数保留到确认无引用的下一个提交）。

## 复核门一览

| 门 | 位置 | 需要确认 |
|---|---|---|
| G1 | P0 结束 | 上表测试/策略改动（尤其 `test_check_pdf.py` 改写理由） |
| G2 | P1 结束 | 引擎选型定案（paged.js vs vivliostyle）与实测数据 |
| G3 | P3 结束 | 版权页文本、目录/索引形态（是否要拼音序） |
| G4 | P5 结束 | EPUB 是否内嵌字体、封面图口径 |
| G5 | P7 | A4 版是否退役、是否合入 main |