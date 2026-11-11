# 研究：BMS-Z → mcu 工程化差距取证（2026-10-25）

来源：两个只读侦察（`agent://BmszInfraAudit`、`agent://McuInfraAudit`，各 2.5–3.2 分钟，全文件级读证）。
本文件只归档**已读到的原文事实**，结论见 `prd.md` / `design.md`。

## 1. mcu 现状（实测）

### 工作流

| 文件 | 触发 | jobs | 阻断 |
|---|---|---|---|
| `quality.yml` | `pull_request` / `workflow_dispatch` / `workflow_call` | `checks`、`arm-host`、`esp32`(needs: checks) | 是，无 `continue-on-error` |
| `book.yml` | push main / PR / dispatch | `book` | 是，`if-no-files-found: error` |
| `deploy.yml` | push main / dispatch | `quality`(uses:) → `deploy`(needs + `refs/heads/main` + `result == 'success'`) | 是 |

- `checks` job 顺序：`npm ci` → `npm run quality` → `npx playwright install --with-deps chromium && npm run test:browser` → `npm run anim:audit` → `node scripts/project-catalog.mjs --matrix` → 装 Python 3.13 → `python mcu-book/build_html.py --pdf` → `cp mcu-book/dist/*.{html,pdf} docs/.vitepress/dist/book/` → upload `docs-site`。
- `arm-host`：apt 装 `gcc-arm-none-eabi`；FreeRTOS-Kernel `V11.1.0`；RT-Thread 稀疏检出；CMSIS 两个头文件 curl + `sha256sum --check --strict`；`npm run firmware:check`。
- `esp32`：`container: espressif/idf:v5.5.2`，matrix 来自 `checks` 输出，`idf.py set-target/build size`，末尾断言 `project_description.json` 的 `target == "esp32s3"`。
- 三个 workflow 全部 `runs-on: ubuntu-latest`；action 已按 SHA 固定（`book.yml`）或按 major 标签（`quality.yml`/`deploy.yml` 用 `@v7`/`@v6`/`@v4`/`@v5`）。
- `deploy.yml` 只搬运 `checks` 上传的 `docs-site` artifact；**部署前不再对 dist 做任何检查**。

### `package.json`（`name: mcu-road`，`version: 0.1.0`）

`quality` = `test && projects:check && docs:build && anim:lint && readme:check && reading:check && links:check && nav:check && seo:check && perf:budget && a11y:check`（`&&` 链，首个失败即停）。
其余脚本：`video:*` 8 个、`book:check|html|pdf`、`firmware:check`、`test:browser`、`site:measure`、`docs:gen|dev|build|preview`、`readme:sync|check`、`anim:lint|audit`。
`devDependencies`：`@playwright/test ^1.63.0`、`ffmpeg-static ^5.3.0`、`puppeteer ^25.13.0`、`vitepress ^1.6.3`、`yaml ^2.8.3`（全部 caret，非钉死）。

### `scripts/`（24 项）与测试对应

已有测试：`perf-budget`→`tests/perf.test.mjs`、`project-catalog`→`catalog`、`reading-time`→`reading-time`、`search-tokenize`/`search-render`→`search`、`seo-check`→`seo`、`a11y-check`→`a11y`、`nav-check`→`nav`、`curriculum`→`curriculum`、`content-metadata`→`metadata`、`device-console.py`→`logger-cli`+`device-cli`。
无独立测试：`check-firmware.mjs`、`anim-audit.mjs`、`anim-lint.mjs`、`gen-progress.mjs`、`links-check.mjs`、`measure-site.mjs`、`gen-og-cover.py`。
`tests/`：13 个 `.test.mjs` + `tests/browser/site.spec.mjs`（Playwright：源码暴露/待实测状态、搜索按需加载、动画控件、减少动效、移动端无横向溢出）。

`tests/workflow.test.mjs` 现有断言：`deploy.yml` 复用 `quality.yml`、部署依赖 quality 成功且为 main；`quality.yml` 含 `workflow_call`/`pull_request`、jobs 为 `checks/arm-host/esp32`、无 `continue-on-error`、ESP32 容器为 `espressif/idf:v5.5.2`。
→ **改动 workflow 的 job 集合或容器/runner 会直接命中这个测试**，必须同步（属"测试改动需复核"范畴）。

### `mcu-book/`

- `build_html.py`（70.9KB，1550 行）：`validate_manifest`、`convert_containers`、`substitute_components`、`audit_html`、`build_pdf`、`_stamp_page_numbers`（PyMuPDF 写页眉/页码/大纲/元数据）、CLI `--out-dir|--pdf|--browser|--check`。
- `manifest.json`（102KB）：`title/subtitle/version/date/language/author/repository/license`、10 个 `parts`、`chapter_guides`（question/deliverable/boundary/sources）、6 个 `appendices`、`sources` 注册表。
- `tests/test_build.py`：88 章覆盖、单文件离线书断言（88 罗盘、6 附录、13 测验组、≥90 data URI、锚点无缺失）、页眉映射、以及 6 个破坏性用例。
- `requirements.txt`：`markdown>=3.7`、`playwright>=1.40`、`PyMuPDF>=1.24`。
- **无** `check_pdf.py`、**无** 产物打包/校验和/landing。

### 缺失清单（对照物为 BMS-Z）

根 `CHANGELOG.md`、`CITATION.cff`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`.lychee.toml`、`scripts/local-gates.{ps1,sh}`、`.github/workflows/links.yml`、`ruff.toml` + Python lint job、独立 PDF 契约门、下载打包器、dist 侧锚点/搜索对账。

## 2. BMS-Z 机制原文（可移植部分）

### `scripts/local-gates.ps1` / `.sh`

头注释语义：`FAIL 使退出码非零；工具缺失记 SKIP（附安装提示）但不算失败，因为 CI 才是真门禁`。
`.ps1` 必须 **UTF-8 with BOM**（PS 5.1 否则按 ANSI 误读中文）；解释器探测链 `python` → scoop 路径 → `py`；`.sh` 为 `python3` → `python`。
临时目录安全清理拒绝非 `bmsz-(regen|card)-` 前缀。
检查项按序：解释器、`check_docs.py`、`ruff`、`pytest soc`、`compare.py` 冒烟、`pytest protocol`、`pytest 擂台基线`、固件 `gcc+run`、`hil_replay`、生成图对账、社交卡对账、`--release-truth`、`--categories-truth`、`--about-truth`。

### `.github/scripts/check_docs.py`（657 行报告节选）

强制的规则（原文摘录）：
1. **GitHub 锚点算法**：`_KEEP = re.compile(r"[^\w\s\-\u4e00-\u9fff\u0300-\u036f]", re.UNICODE)`；`slugify` = NFC → strip → lower → 去标点 → **每个空格换一个 `-`**（不折叠），故 `AFE + MCU` → `afe--mcu`。
2. **SVG 数量只设下界**（`MIN_SVGS = 150`）：新增不该红，掉下来才红。
3. **SVG 硬约定**：中文 `<title>`、含 `<animate`、`prefers-color-scheme: dark`、根节点 `role="img"`。
4. **SMIL 规范**：`keyTimes` 以 0 开头、非 discrete 时以 1 结尾、单调不减、与 `values`/`keyPoints` 等长；`animateMotion` 延迟启动时宿主必须有坐标。
5. **画风**：未定义 class、内联 paint、字号 <12px、缺 `<desc>` 或复读 title、缺 `role="img"`、`viewBox` 宽非 800。
6. **Markdown 卫生**：拦控制字符（`\times` 里的真 TAB）与 `\( \)` 定界符。
7–9. README 阶段表动画张数、全库 25 处手写数字声明、动画索引与 `assets/` 双向一致；正则没捞到预期句数**直接报红**（防"写法改了门就静默通过"）。
10. `.lychee.toml` 排除清单与文档里写的域名数量逐条对账。
11. 本仓库 blob 自链改为**按仓库树逐条验存在**。
12–14. 发布记录表列数/格式对账、表格列数对账、本地门清单"脚本输出 ↔ 头注释 ↔ CONTRIBUTING ↔ 步数"四处一致。
15. 相对链接与锚点存在性（`.md` 用 slugify、`.html` 用 `id`），拒绝路径尾部 `.`/空格。
17–18. 口诀索引同步、更新动态分组、门面最新发布、Unreleased 迁移、CHANGELOG 条数对账。

### `links.yml` + `.lychee.toml`

两轮制：第 1 轮 `continue-on-error: true`；红则等 180 秒、把报告挪成 `.lychee-report-1.md`（避免第 2 轮自扫描），再跑第 2 轮；两轮都红才判红。触发含 `schedule: cron "23 3 5 * *"`。
`accept = ["200..=299","401","403","412","418","429","440"]`；`timeout = 20`、`max_retries = 3`、`max_concurrency = 8`；`exclude` 逐条列域名。

### `ruff.toml`

`select = ["E4","E7","E9","F","B","UP","W605"]`；顶部注释说明**不启用**格式化与行长规则的两个理由（中文按字符计长失真；`ruff format` 会打散 CRC 校验值对齐注释表）。

### `bms-book/check_pdf.py`

校验：PDF 元数据与 manifest 一致；书签数 == 预期文件数；封面无页脚页码；除封面每页页脚含 `页码 / 总页数`；章首页/分部页无页眉；奇偶页眉（偶页书名/奇页当前章名）；目录覆盖全部章节且目录条目右侧有页码；`SOURCE ANCHORS` 出现次数 == `chapter_sources` 登记数。

### `bms-book/publish_downloads.py`

校验 manifest `title` 与 `version =~ \d+\.\d+\.\d+`；要求源目录**同时**存在 html 与 pdf；产出稳定名 + `-vX.Y.Z` 版本名、`SHA256SUMS.txt`、`book-downloads.json`、响应式 `index.html`；staging → replace 原子更新；输入缺失时保留上一份完整包；升版不留旧版本文件。

### `bms-book/tests/`

`test_check_pdf.py`（合成 PDF 夹具：完整合同、缺页脚、缺目录页码、大纲标题带零宽字符、目录续页只剩一条目）、`test_publish_downloads.py`（稳定/版本化产物、SHA256SUMS、JSON、landing、输入缺失保留旧包、升版不残留）、`test_build.py`（真跑构建 + 破坏性用例）。

### `CHANGELOG.md`

手工维护、按版本分节（`## v0.6.1 · 2026-10-24`），每条一个 bullet；但 `check_docs.py` 强制与发布记录表、compare 落款、日期、条数对账。

## 3. 侦察给出的"可移植机制"清单（原文）

钉死 CI 运行环境与工具版本；本地一键复跑 CI；本地-only 真值门；两轮制外链；排除清单与文档对账；自链改树校验；发布产物原子打包 + SHA-256；PDF 出版契约门；部署前检查最终 dist；来源锚点登记体系；manifest 驱动构建；生成图与入库版逐字节对账；门清单四处一致；Markdown 卫生；章节结构契约；demo 与正文数字钉死。