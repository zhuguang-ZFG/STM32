# 设计：验证纵深

## 1. 边界

**做**：新增门/产物校验器 + 把它们接进 CI + 元文件 + 环境钉死。
**不做**：站点正文改写、video 流水线、`code/` 固件工程、`build_html.py` 的行为性重构。

三处结构性错位的对策：

| 错位 | 对策 | 落点 |
|---|---|---|
| 部署物无人检查 | 把检查移到 dist 产物上，且位置在 `upload-pages-artifact` 之前 | `scripts/pages-check.mjs`、`scripts/search-check.mjs`、`deploy.yml` |
| 手工结论无人对账 | 全站锚点 + Markdown 卫生 + 手写数字声明对账 | `scripts/docs-check.mjs` |
| 发布物无凭据 | PDF 反向契约门 + 打包器（校验和/版本名/落地页） | `mcu-book/check_pdf.py`、`mcu-book/publish_downloads.py` |

## 2. 技术选型（沿用既有约定，不立第二套）

| 层 | 语言/位置 | 理由 |
|---|---|---|
| 站点侧门 | `scripts/*.mjs` + `tests/*.test.mjs`（`node --test`） | 24 个脚本与 13 个测试都在这套约定里 |
| 书籍侧门 | `mcu-book/*.py` + `mcu-book/tests/test_*.py`（`unittest`） | PyMuPDF/manifest 已在 Python 侧；`--pdf` 产物天然在此校验 |
| 本地门禁 | `scripts/local-gates.ps1` + `.sh` | 用户本机是 Windows；`.sh` 供 CI/他人 |
| 外链 | `.lychee.toml` + `.github/workflows/links.yml` | BMS-Z 已验证的两轮制；不自己写爬虫 |

## 3. 关键接口与契约

### 3.1 `scripts/local-gates.ps1` / `local-gates.sh`

```
用法：pwsh -File scripts/local-gates.ps1 [-Only <label>]     # 本机
      bash scripts/local-gates.sh [--only <label>]           # Git Bash / Linux
退出码：0 = 无 FAIL（允许有 SKIP）；1 = 至少一项 FAIL
输出：每项一行 `[PASS|FAIL|SKIP] <label> <耗时>`，末尾汇总 `n pass / n fail / n skip`
编码：.ps1 为 UTF-8 with BOM（PowerShell 5.1 中文安全）
```

检查项（逐项独立执行，失败不中断后续；与 CI 一一对应）：

| # | label | 命令 | 缺失时 |
|---|---|---|---|
| 1 | `node` | `node -v` | FAIL |
| 2 | `npm quality` 的 11 项 | 逐条 `npm run test/projects:check/docs:build/anim:lint/readme:check/reading:check/links:check/nav:check/seo:check/perf:budget/a11y:check` | FAIL |
| 3 | `docs:check` | `npm run docs:check` | FAIL |
| 4 | `pages:check` `/` `search:check` | `npm run pages:check`、`npm run search:check` | FAIL（无 dist 时先构建，见下） |
| 5 | `anim:audit` | `npm run anim:audit` | FAIL |
| 6 | `test:browser` | `npm run test:browser` | 无 `npx playwright`/浏览器 → SKIP |
| 7 | `firmware:check` | `npm run firmware:check` | 无 `arm-none-eabi-gcc` → SKIP（提示 `scripts/arm-env.sh`） |
| 8 | `book:check` | `npm run book:check` | FAIL |
| 9 | `book:pdf+contract` | `npm run book:pdf` → `python mcu-book/check_pdf.py` | FAIL |
| 10 | `book:pack` | `python mcu-book/publish_downloads.py --out-dir .temp/book-downloads` | FAIL |
| 11 | `ruff` | `python -m ruff check .` | 无 ruff → SKIP（提示 `python -m pip install ruff==0.15.21`） |
| 12 | `unittest mcu-book` | `python -m unittest discover mcu-book/tests` | FAIL |

`docs:build` 会生成 dist，故 4 依赖 2；实现上把 4 排在 2 之后。

### 3.2 `scripts/docs-check.mjs`（`npm run docs:check`）

```js
export function slugify(heading)                 // GitHub 算法：NFC→trim→lower→去标点(保留 \w \s - 汉字 组合记音)→ 每个空格换一个 "-"（不折叠）
export function collectMarkdown(root)            // docs/**/*.md + README.md + CONTRIBUTING.md + *.md（排除 node_modules/.temp/dist/mcu-book/book）
export function checkLinks(root)                 // 相对链接存在性；.md 锚点用 slugify；.html 锚点用 id；拒绝尾部 "."/空白
export function checkHygiene(root)               // 控制字符（\t 之类被存成真字符）+ `\(`…`\)` 定界符
export function checkSelfBlobLinks(root)         // github.com/zhuguang-ZFG/mcu/blob/<ref>/<path> → 按工作树路径存在性校验
export function checkNumberClaims(root)          // CLAIMS 对账（见下）
export const CLAIMS
```

`CLAIMS` 条目形如 `{ label, file, pattern: /…(\d+)…/g, expected: () => 88, minMatches: 1 }`：
- 捕获值与 `expected()` 不等 → 报错（点名 file + 实际值 + 期望值）；
- 实际命中句数 < `minMatches` → **报错**（BMS-Z 的"防静默通过"：写法变了导致正则捞不到时，门必须红而不是变绿）。

初始 `CLAIMS` 集合（实施时先实测再写死，数值来源见括号）：

| label | 实际来源 |
|---|---|
| 章节数 | `docs/**/*.md` 中 frontmatter `status` 存在的页面数 / `mcu-book/manifest.json` 的 `parts[].files` 计数 |
| 附录数 | `manifest.appendices` 长度 |
| 动画张数 | `docs/public/anim/*.svg` 计数（与 `gen-progress.mjs` 同源） |
| 测验组数 | `docs/.vitepress/data/quizzes/*.json` 计数 |
| 工程数 | `code/projects.json` 长度 |
| 契约数 | `.trellis/spec/docs-site/quality-contract.md` 里点名的契约条数（若正文有"N 个契约"表述） |

**锚点算法统一**：`scripts/links-check.mjs` 现有的 `slug()` 把连续空白折叠成单个 `-`，与 GitHub 行为不符；改为 `import { slugify } from './docs-check.mjs'`，并在同一次提交里修掉因此暴露的真实锚点错误（这是修正，不是放宽）。

### 3.3 `scripts/pages-check.mjs`（`npm run pages:check`）

```js
export function collectDistAnchors(distDir)   // 复用 seo-check.mjs 的 collectHtmlPages
export function checkDistAnchors(distDir)     // 站内 href 带 fragment → 目标 html 存在且含 id=fragment
```

范围：`docs/.vitepress/dist/**/*.html`，href 以 `BASE`(`/mcu/`) 起头或以相对路径解析；跳过 `http(s):`、`mailto:`、纯 `#`。理由：`ignoreDeadLinks: false` 只保证**链接存在**，**锚点**无人管（BMS-Z 的 `check_pages.py` 同理）。

### 3.4 `scripts/search-check.mjs`（`npm run search:check`）

```js
import { loadSearchIndex } from './seo-check.mjs'   // 现有导出，单真源
export function harvestTerms(docsDir)               // 章节 title + H2/H3 标题（去代码块、去标点）→ 术语集合
export function checkTerms(indexText, terms)        // 每个术语的 CJK 二元片段必须能在索引原文里找到
```

失败样例：从 `docs/` 随机抽一个 H2 术语，确认它在索引里；人为把 `miniSearch.options.tokenize` 换回默认后必须报错（证明该门抓的是分词器静默失效）。

### 3.5 `mcu-book/check_pdf.py`

```
用法：python mcu-book/check_pdf.py [pdf] [--manifest mcu-book/manifest.json]
默认：mcu-book/dist/mcu-deep-book.pdf
```

校验项（全部反向、产物驱动）：

1. 元数据 `title/author/subject` 与 manifest 一致；
2. 大纲条目数 == 章节数 + 附录数（+ 分部页，若 manifest 声明）；
3. 第 1 页（封面）无页脚页码；
4. 除封面每页页脚为 `N / total`（正则 + total 自洽）；
5. 章首页/分部页无页眉；
6. 正文页页眉与运行页眉映射逐页一致（抽样全部页，非抽样）。
7. 全书页数 > 0 且 total 与 `document.page_count - 1` 一致。

**单真源**：把 `build_html.py` 里当前的页眉映射与 skip 集合**提取为纯函数**（`running_header_map(manifest)`、`header_skip_pages(manifest)`），`build_html.py` 与 `check_pdf.py` 共用；行为不变，由既有 `test_build.py` 的页眉用例覆盖。除此之外不重构 `build_html.py`。

### 3.6 `mcu-book/publish_downloads.py`

```
用法：python mcu-book/publish_downloads.py --out-dir <dir> [--source-dir mcu-book/dist] [--manifest mcu-book/manifest.json]
前置校验：manifest 有 title；version 匹配 ^\d+\.\d+\.\d+$；source-dir 同时存在 book html 与 pdf（缺一即 SystemExit(1)）
产物：mcu-deep-book.html/.pdf、mcu-deep-book-v<version>.html/.pdf、SHA256SUMS.txt、book-downloads.json、index.html
写盘：staging 目录 → 整体 replace；输入缺失时**不动**已有输出（保留上一份完整包）
```

`book-downloads.json`：`{ title, version, date, files:[{name, bytes, sha256}], generatedFrom:{html,pdf} }`。
`index.html`：自包含落地页（标题/版本/日期/两格式按钮/校验和入口），样式内联、无外部依赖、跟随站点 `BASE=/mcu/` 的相对路径。

### 3.7 CI 接线

- `quality.yml.checks`：追加（在 `npm run quality` 之后、`anim:audit` 之前的合适位置）
  `npm run docs:check`、`npm run pages:check`、`npm run search:check`（后两者在 `docs:build` 之后，其 dist 已存在）；
  末尾 `python mcu-book/check_pdf.py`、`python mcu-book/publish_downloads.py --out-dir docs/.vitepress/dist/downloads`。
- `quality.yml` 新增 `python-lint` step：`astral-sh/ruff-action@v4.1.0`（`version: 0.15.21`, `args: check`）。放在 `checks` job 内（避免再起 job 拖慢），或独立 job —— **决定：独立 `lint` job**，与 BMS-Z 一致，且让 `tests/workflow.test.mjs` 的 job 集合变化显式。
- `deploy.yml.deploy`：在 `actions/configure-pages` 前插入
  `npm ci` + `npm run pages:check` + `npm run search:check`（对 `site/` 这一份 artifact；需 `--dist site` 形式参数或 `DIST_DIR` 环境变量）。
  → 为此两个脚本支持 `--dist <dir>`（默认 `docs/.vitepress/dist`）。
- `book.yml`：追加 `check_pdf.py` 与 `publish_downloads.py`，并把点击下载的自证（`SHA256SUMS.txt` 存在）纳入上传 artifact。
- 三个 workflow：`runs-on: ubuntu-latest` → `ubuntu-24.04`。

### 3.8 元文件

| 文件 | 内容 | 一致性校验 |
|---|---|---|
| `CITATION.cff` | `cff-version: 1.2.0`、title/version/repository/author/license 取自 manifest | `docs-check.mjs` 断言与 manifest 的 `title/version/repository/author` 一致 |
| `SECURITY.md` | 报告渠道、支持版本、不承诺 SLA 的说明 | 无 |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1（中文） | 无 |
| `CHANGELOG.md` | Keep a Changelog 版本节；每节 `## vX.Y.Z · YYYY-MM-DD` | `docs-check.mjs`：每个版本号必须出现在 `docs/reference/changelog.md`；最新版本 == `manifest.version` |

## 4. 失败语义

统一：`FAIL` 逐条点名 `文件:行 或 文件:符号 → 实际 vs 期望`，非零退出，与既有 `✗ / ✓` 输出风格一致；`SKIP` 只用于"工具不在本机"，必须附安装提示，且 CI 上不允许出现 SKIP（CI 里缺工具即 FAIL）。

## 5. 兼容与回滚

- 全部改动是**加法**：新文件 + workflow 追加步骤 + 一条 runner 替换。
- 每期一个提交，回滚 = revert 该提交；不引入迁移、不改数据格式、不删既有门。
- 唯一有"收紧"语义的两处：`links-check.mjs` 的锚点算法（可能暴露既有错误锚点 → 修内容而非放宽算法）、`ubuntu-24.04` 钉死（可能影响 `anim:audit` 字体度量 → 以 CI 实跑为准）。

## 6. 风险与对策

| 风险 | 对策 |
|---|---|
| `tests/workflow.test.mjs` 必然被 workflow 改动打破 | 同提交内更新，并在复核门逐条说明（见 implement.md P0） |
| 手写数字声明在正文里分布未知，正则可能捞空 | 实施第一步先**实测**（grep 全站），`CLAIMS` 只登记真实存在的表述；`minMatches` 保证捞空即红 |
| `pages-check`/`search-check` 在 deploy 侧缺 dist | 加 `--dist` 参数，deploy 侧显式传 `site` |
| 本机无 arm 工具链 → `firmware:check` 常 SKIP | SKIP 语义即为此设计；CI 的 `arm-host` job 才是真门禁 |
| `check_pdf.py` 依赖 PDF 已生成 | 本地门与 CI 都在 `book:pdf` 之后调用 |
| PDF 校验的字体/度量差异（Linux CI vs Windows 本地） | 校验只断言结构（页数/页眉文本/页码格式/大纲），不断言像素或坐标 |

## 7. 交付物清单（新增/修改）

新增：`scripts/local-gates.ps1`、`scripts/local-gates.sh`、`scripts/docs-check.mjs`、`scripts/pages-check.mjs`、`scripts/search-check.mjs`、`tests/docs-check.test.mjs`、`tests/pages-check.test.mjs`、`tests/search-check.test.mjs`、`mcu-book/check_pdf.py`、`mcu-book/publish_downloads.py`、`mcu-book/tests/test_check_pdf.py`、`mcu-book/tests/test_publish_downloads.py`、`.lychee.toml`、`.github/workflows/links.yml`、`ruff.toml`、`CITATION.cff`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`CHANGELOG.md`。

修改：`package.json`、`.github/workflows/quality.yml`、`book.yml`、`deploy.yml`、`tests/workflow.test.mjs`、`scripts/links-check.mjs`、`mcu-book/build_html.py`（仅提取两个纯函数）、`docs/.vitepress/config.mts`（下载入口）、`CONTRIBUTING.md`（门清单）、`.trellis/spec/docs-site/quality-contract.md`、必要时 `docs/reference/changelog.md` 与个别章节的坏锚点。