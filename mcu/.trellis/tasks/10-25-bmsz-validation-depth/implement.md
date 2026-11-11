# 执行计划：验证纵深

约定：每期一个提交（`git add` 只列本任务路径）；每期结束跑该期的"验证命令"并把原文粘进本期收口记录；任何 FAIL 先修再进下一期。

---

## P0 · 前置：测试与策略改动清单（**需复核**）

本任务会新增/修改测试与 CI 策略，按仓库约定**先行列出**，复核通过后才进入 P1。

| 文件 | 动作 | 理由 | 是否放宽断言 |
|---|---|---|---|
| `tests/docs-check.test.mjs` | 新增 | 覆盖 slugify、链接/锚点、卫生、CLAIMS 对账的正反例 | 否（纯新增） |
| `tests/pages-check.test.mjs` | 新增 | dist 锚点对账正反例（临时目录夹具） | 否 |
| `tests/search-check.test.mjs` | 新增 | 术语抽取 + 索引命中正反例 | 否 |
| `mcu-book/tests/test_check_pdf.py` | 新增 | 合成 PDF 夹具：完整契约 + 缺页脚/多页眉/大纲缺失/元数据不符 | 否 |
| `mcu-book/tests/test_publish_downloads.py` | 新增 | 产物齐备、SHA256SUMS 正确、输入缺失保留旧包、升版不残留 | 否 |
| `tests/workflow.test.mjs` | **修改** | workflow 新增 `lint` job、新增步骤、runner 钉 `ubuntu-24.04`；`links.yml` 加入同一断言集 | 否——只把"现有的严格性"外推到新 job；不删任何既有断言 |
| `scripts/links-check.mjs` | **修改** | 锚点算法与 `docs-check.mjs` 统一为 GitHub 规则（现算法折叠连续空白，与 GitHub 不符） | 收紧，不放宽 |

复核门（人工确认后才 `task.py start`）：以上六项是否允许；`tests/workflow.test.mjs` 的具体改动 diff 是否只是"外推严格性"。

**回滚点**：本任务尚未产生任何代码改动，回滚即丢弃任务目录。

---

## P1 · 门禁骨架与环境钉死（R1/R7/R8-钉死）

1. `ruff.toml`：`select = ["E4","E7","E9","F","B","UP","W605"]`，顶部注释写明不做格式化/行长规则的两条理由（中文按字符计长失真；`ruff format` 会打散对齐注释表）。
2. `scripts/local-gates.ps1`（UTF-8 with BOM）+ `scripts/local-gates.sh`，按 design §3.1 的 12 项实现；解释器探测、`FAIL/SKIP`、汇总、`-Only/--only`。
3. `package.json` 新增脚本：`docs:check`、`pages:check`、`search:check`（P2/P6 落地后生效；此处先占位实现最小可用版本，避免门槛期悬空——**决定：等 P2/P6 实现后再加这两行，P1 只加 `gates` 文档段落，不留悬空脚本**）。替换为：P1 只加 `docs:check` 的 npm 行（P2 同步实现）。
4. 三个 workflow：`ubuntu-latest` → `ubuntu-24.04`；`.gitattributes` 与 `scripts/anim-audit.mjs` 中引用 `ubuntu-latest` 的注释同步更新。
5. `quality.yml` 新增独立 `lint` job（`astral-sh/ruff-action@v4.1.0`，`version: "0.15.21"`，`args: check`）。
6. 同步改 `tests/workflow.test.mjs`（job 集合、runner、lint job 断言）。

**验证命令**
```bash
python -m ruff check .
pwsh -File scripts/local-gates.ps1 -Only ruff      # 期望 PASS；把 ruff 卸载/改名后期望 SKIP
bash scripts/local-gates.sh --only node
node --test tests/workflow.test.mjs
python ./.trellis/scripts/../scripts/../.trellis/scripts/get_context.py >/dev/null 2>&1 || true
```
**回滚点**：revert 本期提交；`local-gates` 是纯新增，删除即回到原状。

---

## P2 · 文档一致性门（R2）

1. `scripts/docs-check.mjs`：按 design §3.2 实现 `slugify`/`checkLinks`/`checkHygiene`/`checkSelfBlobLinks`/`checkNumberClaims`/`CLAIMS`。
2. **先实测再写死 CLAIMS**：
   ```bash
   grep -rn "88 章\|附录\|张动画\|组自测\|个工程\|个契约" docs README.md CONTRIBUTING.md mcu-book/README.md | head -50
   ```
   把真实存在的表述登记进 `CLAIMS`，每条 `minMatches >= 1`。
3. 把 links-check 的锚点算法切到 `slugify`（import），修掉暴露的真实坏锚点。
4. `package.json` 加 `docs:check`；`quality` 链加入 `&& npm run docs:check` 的合适位置（`docs:build` 之后，因为需要构建产物时才需要 dist——实测确认 docs-check 只读源文件，则放最前）。
5. `tests/docs-check.test.mjs`：slugify（含 `A + B` → `a--b` 的多空格用例）、锚点命中/未命中、真 TAB 与 `\(` 检出、CLAIMS 值不符与命中数不足两种红。

**验证命令**
```bash
npm run docs:check
node --test tests/docs-check.test.mjs
npm run links:check && npm run readme:check
```
**故意失败样例（4 条，逐条记录报错原文）**：改一个锚点、塞一个真 TAB、把某处"88 章"改成"89 章"、把一条自链指向不存在的文件。

---

## P3 · PDF 出版契约门（R3）

1. `mcu-book/build_html.py`：提取 `running_header_map(manifest)`、`header_skip_pages(manifest)` 纯函数，原调用点改用它们（行为不变）。
2. `mcu-book/check_pdf.py`：按 design §3.5 实现 7 项校验，复用上述纯函数与 `load_manifest()`。
3. `mcu-book/tests/test_check_pdf.py`：合成 PDF 夹具（PyMuPDF 现场造页）+ 4 个反向用例。
4. `package.json` 加 `book:pdfcheck`；`book.yml` 与 `quality.yml` 在 `--pdf` 之后调用。

**验证命令**
```bash
npm run book:pdf && python mcu-book/check_pdf.py
python -m unittest discover mcu-book/tests -v
```
**故意失败样例**：改 `check_pdf.py` 断言所依赖的 PDF 元数据（或人为删一页页脚）→ 必须点名。

---

## P4 · 下载打包器（R4）

1. `mcu-book/publish_downloads.py`：按 design §3.6 实现；`--out-dir` 必填、staging→replace、输入缺失保留旧包。
2. `mcu-book/tests/test_publish_downloads.py`：产物齐备/SHA256SUMS 正确/输入缺失保留旧包/升版不残留。
3. `quality.yml`：`--out-dir docs/.vitepress/dist/downloads`；`book.yml`：同样产物进 artifact。
4. 站点入口：`docs/.vitepress/config.mts` 加"下载"导航（指向 `/mcu/downloads/`），并确认 `pages-check` 通过。

**验证命令**
```bash
python mcu-book/publish_downloads.py --out-dir .temp/book-downloads
cd .temp/book-downloads && sha256sum -c SHA256SUMS.txt && ls -1
python -m unittest discover mcu-book/tests -v
```
**回滚点**：删除产物目录与本期提交；站点入口还原。

---

## P5 · 外链巡检（R5）

1. `.lychee.toml`：`accept`/`timeout`/`max_retries`/`max_concurrency` 按 BMS-Z 口径；`exclude` 从**本仓库实际超时/反爬域名**实测得来，逐条配注释。
2. `.github/workflows/links.yml`：两轮制 + `schedule`。
3. `tests/workflow.test.mjs` 增补 `links.yml` 断言（两轮存在、`fail: true`、schedule 存在）。

**验证命令**
```bash
gh workflow run links.yml   # 或本地 npx lychee --config .lychee.toml ./**/*.md（若本机有 lychee）
node --test tests/workflow.test.mjs
```

---

## P6 · dist 侧对账（R6）

1. `scripts/pages-check.mjs`（`--dist`，默认 `docs/.vitepress/dist`）：复用 `collectHtmlPages`。
2. `scripts/search-check.mjs`（`--dist`，默认同上）：复用 `loadSearchIndex`。
3. `package.json` 加 `pages:check`、`search:check`；`quality.yml` 在 `docs:build` 后调用。
4. `deploy.yml`：`configure-pages` 前插入 `npm ci` + 两个脚本（`--dist site`）。
5. `tests/pages-check.test.mjs`、`tests/search-check.test.mjs`。

**验证命令**
```bash
npm run docs:build && npm run pages:check && npm run search:check
node --test tests/pages-check.test.mjs tests/search-check.test.mjs
grep -n "pages:check" .github/workflows/deploy.yml   # 必须出现在 upload-pages-artifact 之前
```
**故意失败样例**：改一个站内链接的 fragment → 报错；把 `miniSearch.options.tokenize` 注释掉 → `search:check` 报错。

---

## P7 · 元文件（R8-元文件）

1. `CITATION.cff`（取自 manifest）、`SECURITY.md`、`CODE_OF_CONDUCT.md`、根 `CHANGELOG.md`（版本节，v1.0.0 起）。
2. `docs-check.mjs` 增补两条对账：CITATION ↔ manifest、CHANGELOG 版本 ↔ 站内更新日志 + 最新版 == manifest.version。
3. 对应测试用例加入 `tests/docs-check.test.mjs`。

**验证命令**
```bash
npm run docs:check
node --test tests/docs-check.test.mjs
```

---

## 收口（P8）

1. `.trellis/spec/docs-site/quality-contract.md`：收录全部新门的签名、契约、错误矩阵、必测项（这条是 Phase 3.3 spec 更新的正文）。
2. `CONTRIBUTING.md`：门清单与"提交前自查"段更新为 `scripts/local-gates.*`。
3. 全量验证：
   ```bash
   npm run quality && npm run test:browser && npm run anim:audit
   npm run firmware:check            # 需 arm 工具链，否则记录未验证
   python -m unittest discover mcu-book/tests -v
   python -m ruff check .
   ```
4. `task_verify`：报告 passed / failed / unverified 三分，未跑到的项逐条列名。
5. 每期故意失败样例的报错原文汇总进 `.trellis/tasks/10-25-bmsz-validation-depth/` 的收口记录。
6. 提交时只 `git add` 本任务路径；video 在途改动保持未提交、不动。

## 复核门一览

| 门 | 位置 | 需要人工确认的内容 |
|---|---|---|
| G1 | P0 结束 | 新增/修改测试清单（尤以 `tests/workflow.test.mjs` 的 diff）是否只是外推严格性 |
| G2 | P2 结束 | CLAIMS 登记的真实表述与数值来源；锚点算法收紧后修掉的内容改动是否只改错处 |
| G3 | P4/P6 结束 | 站点新增下载入口与 deploy 侧检查位置 |
| G4 | 收口 | `task_verify` 三分报告 + spec 更新 + 是否合入 main |