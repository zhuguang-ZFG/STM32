# BMS-Z 验证纵深：当前门禁 → AC 矩阵（W2 只读准备）

日期：2026-11-12（本文件只读盘点，不改测试 / 不改 workflow / 不放宽断言）
参照任务：`10-25-bmsz-validation-depth`（prd.md 的 R1–R8 与 P1–P7）

> **P2 后记（2026-11-12，本文件写就后经授权执行）**：§0/§3.1/§4/§5 是**修复前快照**，保留作基线。合并 P2 已修复其中列出的接线缺口，当前证据：`npm test` 135/135、`npm run quality` 全链 PASS、`npm run test:browser` 7/7、`python -m unittest discover mcu-book/tests` 59/59、`python mcu-book/build_html.py --check` PASS、`ruff check .` PASS；`docs:build` 在 `NODE_OPTIONS=--max-old-space-size=2048` 下成功。PDF 运行期与 CI/远程 Pages 仍为 NOT_RUN。

## 0. 结论摘要

1. BMS-Z 的 8 项要求在当前树中**全部有实现**，且多数已超出原设计（15 项 quality 链、13 项 PDF 契约、59 个 Python 测试、audit/art_guard 等新增门）。
2. **当前 `npm test` 是红的**：129 测试 / 119 pass / 10 fail。10 条全部可归因为**子树合并后的测试夹具漂移**（站点 base 由 `/mcu/` 改为 `/STM32/mcu/`、workflow 文件改名为 `mcu-*.yml`），不是门禁逻辑退化；但在这 10 条修复前，`quality` 链第一项就失败，本地门禁与 CI 都不会绿。
3. **PDF 契约已换代**：`check_pdf.py` 的校验对象从旧 A4 产物切换为 **16 开印前 PDF**（MediaBox 185×260 mm，出血版 191×266 mm），校验项从旧记录中的 6 类扩展到 **13 个 check 函数**。10-25 的 712 页实测证据对旧契约有效，**不能直接当作当前契约的通过证据**。
4. 本机没有 `docs/.vitepress/dist` 与 `mcu-book/dist/*.pdf`：dist 侧（pages/search/seo/perf/a11y）与 PDF 运行期门今天**未复跑**，只能引用历史证据；`docs:build` 在本机 OOM（已知环境上限），不能以本地失败判产品失败。
5. 另发现 4 处合并接线缺口（见 §5），均属合并 P2 范围，W2 不修，单列待复核。

## 1. 当前门禁清单（以源文件为真值）

### 1.1 `package.json` · `quality` 链（15 项，`&&` 串联）

`test` → `projects:check` → `docs:build` → `anim:lint` → `readme:check` → `reading:check` → `prose:check` → `links:check` → `docs:check` → `nav:check` → `seo:check` → `perf:budget` → `a11y:check` → `pages:check` → `search:check`

其中 `docs:build = guide:check && docs:gen && vitepress build docs`（导读生成门与进度生成已嵌套进构建）。

### 1.2 CI（根 `.github/workflows/mcu-*.yml`）

| 文件 | job / 内容 | runner |
|---|---|---|
| `mcu-quality.yml` | `checks`（quality 链、Playwright 回归、`anim:audit`、题图 audit 1.08、`art_guard.py`、整书 HTML+PDF+print 构建、`check_pdf.py`、`publish_downloads.py`、GNU `sha256sum -c` + `--verify`、上传 `docs-site`）；`arm-host`（ARM 全工程 + 场景切换）；`esp32`（IDF v5.5.2 矩阵）；`lint`（ruff-action 0.15.21，`check --config mcu/ruff.toml mcu`） | 全部 `ubuntu-24.04` |
| `mcu-deploy.yml` | `quality`（复用 mcu-quality）→ `deploy`；artifact 落地后先跑 `pages-check --dist site`、`search-check --dist site`，再 `upload-pages-artifact` | `ubuntu-24.04` |
| `mcu-book.yml` | `book`：unittest → `--check` → HTML/PDF/print → `check_pdf` → `publish_downloads` → 双口径 sha | `ubuntu-24.04` |
| `mcu-links.yml` | lychee 两轮制 + 月度 schedule | `ubuntu-24.04` |

> 注意：根 `.github/workflows/book.yml` 是 STM32 主仓自己的书流程，**不是** mcu 书的 workflow；mcu 书对应 `mcu-book.yml`。

### 1.3 本地门禁 `scripts/local-gates.{ps1,sh}`

实际集合：`test`、`projects:check`、`docs:build`、`anim:lint`、`readme:check`、`reading:check`、`links:check`、`docs:check`、`nav:check`、`seo:check`、`perf:budget`、`a11y:check`、`pages:check`、`search:check`、`anim:audit`、`test:browser`（缺 Playwright 则 SKIP）、`firmware:check`（缺 ARM 工具链则 SKIP）、`book:check`、`book:unittest`、`book:pack`、`book:pack-verify`、`book:pdfcheck`（PDF 不存在则 SKIP）、`ruff`（缺则 SKIP）。

**已漂移**：脚本注释声称"与 `npm run quality` 同集合"，但漏了 `prose:check`（quality 链有、local-gates 没有）。见 §5-③。

## 2. R1–R8 → 当前实现映射

| 原要求 | 当前实现 | 相对原设计的演进 | 当前状态（2026-11-12） |
|---|---|---|---|
| R1 本地一键门禁 | `scripts/local-gates.ps1` + `.sh`，逐项跑、FAIL 非零、SKIP 带提示 | 集合扩到 23 项左右（含 book 四项、audit、browser、firmware、ruff） | 实现存在；集合漏 `prose:check`；因 `test` 红，整跑不会绿 |
| R2 文档一致性门 | `scripts/docs-check.mjs`，在 quality 链内 | 增至 6 类检查（含 CITATION/CHANGELOG 对账），数字声明 27 条 | **PASS**：138 文件、6 类、27 条声明、298 ms |
| R3 PDF 出版契约门 | `mcu-book/check_pdf.py`，quality `checks` 与 `mcu-book` 双处调用 | **换代**：A4 → 16 开（185×260，出血 191×266）；6 类 → 13 个 check；默认校验 `mcu-deep-book-print.pdf` | 代码与反向测试在；本机无 PDF → 运行期 **NOT_RUN**；历史证据只对旧契约有效 |
| R4 下载打包器 | `mcu-book/publish_downloads.py`，CI 双口径校验 | 无关键变化 | Python 测试 **PASS**；本机打包运行期 **NOT_RUN**（无输入产物） |
| R5 外链巡检 | `.lychee.toml` + `mcu-links.yml`（两轮 + 月度） | 无关键变化 | 未复跑（本地 lychee 未保留 / CI 未运行）→ **UNVERIFIED** |
| R6 dist 侧对账 | `scripts/pages-check.mjs`、`scripts/search-check.mjs`，在 deploy artifact 阶段 | 新增 `--dist site` 口径（对真正上线物） | 测试 6 条因夹具旧 base 失败；运行期 **NOT_RUN**（无 dist） |
| R7 Python lint | 根 `ruff.toml` + `mcu-quality.yml` 的 `lint` job（0.15.21） | 无关键变化 | **PASS**（`python -m ruff check .`） |
| R8 钉死与元文件 | 4 个 `mcu-*.yml` 全 `ubuntu-24.04`；CITATION/SECURITY/CODE_OF_CONDUCT/CHANGELOG/.lychee.toml/ruff.toml 均在 | 合并后 URL 口径需再审：CITATION 的 `url` 已改 `/STM32/mcu/`，`repository-code` 仍是旧仓 URL | 钉死 **PASS**；元文件齐全；仓库 URL 有 2 处合并待办（§5-④⑤） |

## 3. P1–P7 验收矩阵（当前证据 vs 历史证据）

状态口径：**PASS** = 2026-11-12 实跑通过；**FAIL** = 2026-11-12 实跑失败；**NOT_RUN** = 缺产物/环境不可跑；**UNVERIFIED** = 只有历史证据或 CI 未跑。

| 原 AC | 验收内容 | 当前门 / 证据 | 当前状态 | 历史证据（2026-10-25）与备注 |
|---|---|---|---|---|
| P1 | 本地门禁逐项跑完、SKIP 语义正确；ruff 零告警；CI 新步骤绿 | `local-gates.*` 存在；`ruff check .` PASS；`npm test` FAIL（10 条） | **FAIL**（suite 红，非 runner 逻辑） | 历史 24 门全绿（457 s）；现 quality 链已增至 15 项，集合变化需知悉 |
| P2 | `docs:check` 零报错；4 类破坏各自点名；已进 quality | `npm run docs:check` PASS（138 文件 / 6 类 / 27 条） | **PASS**（真仓库）；反向夹具在 `tests/docs-check.test.mjs`，其中 CITATION 夹具旧 URL 导致 1 条测试红 | 历史 4 类破坏（坏锚点 / 真 TAB / 数字错 / 自链不存在）均有原文 |
| P3 | `check_pdf` 对产物通过；4 类破坏点名；单测全绿 | `test_check_pdf.py` 17 个用例在 59 个 Python 测试中 **PASS**；产物门 **NOT_RUN** | **PARTIAL**：测试 PASS / 运行期 NOT_RUN | 历史 712 页实测为旧 A4 契约（6 类），**不可直接沿用**；当前为 16 开 13 项 |
| P4 | 打包四件 + SHA256SUMS + json + 落地页；`sha256sum -c`；旧包保留；升版无残留；单测绿 | `test_publish_downloads.py` 9 个用例 **PASS**；运行期 **NOT_RUN** | **PARTIAL** | 历史 7 文件包 + 双口径；Git for Windows 文本模式陷阱已写入契约 |
| P5 | links.yml PR 绿；死链判红；排除清单有注释 | workflow 存在；未复跑 | **UNVERIFIED** | 历史 lychee 0.24.2：466 unique / 177 OK / 5 errors（2 条真失败已按理由处置） |
| P6 | pages/search 对产物通过；各构造一例被判红；位于 upload 之前 | 顺序断言在 `mcu-deploy.yml:53-58`；6 条测试因旧 base 失败；运行期 **NOT_RUN** | **FAIL（测试层）/ NOT_RUN（运行期）** | 历史：pages 124 页 2627 锚点全中；search 2147 标题可查 |
| P7 | runner 全钉 24.04；CHANGELOG 版本可对账；CITATION 与 manifest 一致 | `mcu-*.yml` 全 24.04；`docs:check` 含 CITATION/CHANGELOG 对账并通过；CITATION `repository-code` 仍旧仓 | **PARTIAL** | 历史：workflow 断言 runner；现 workflow 测试自身路径失效，见 §5-① |

### 3.1 `npm test` 当前 10 条失败（逐条归因）

| 测试文件 | 失败用例 | 归因 |
|---|---|---|
| `tests/docs-check.test.mjs` | `checkCitation` 一致用例 | 夹具 `CITATION.cff` 的 url 仍是旧 `https://zhuguang-zfg.github.io/mcu/`，代码已按站点 base 校验新值 |
| `tests/pages-check.test.mjs` | `resolveHref` ×2、`checkDistAnchors`、`pageHrefPaths` | 夹具 href / 期望值仍写 `/mcu/...`；脚本已按 `BASE=/STM32/mcu/` 判 |
| `tests/search-check.test.mjs` | `checkSearchHits` ×3、`pageHrefPaths` | 索引 id 夹具仍写 `/mcu/...`，与实际 base 不一致导致"查不到自己" |
| `tests/seo.test.mjs` | `sitemap 校验` | 合法样例仍是 `${HOST}/mcu/`，而校验要求 `${HOST}/STM32/mcu/` |
| `tests/workflow.test.mjs` | 整个文件 | 读 `mcu/.github/workflows/quality.yml` 不存在（已改名并上移根目录）→ ENOENT |

> 这些是**测试夹具滞后**，不是产品门误报：`docs:check` 对真实仓库通过，且失败信息本身正是新 base 在生效的证明。修复属于测试变更，需按任务约束单列复核（合并 P2）。

## 4. 全局 AC 现状

| 全局项 | 当前状态 | 证据 |
|---|---|---|
| `npm run quality` | **FAIL**（首项 `test` 10 条红） | `.temp/w2-npm-test.log`：129 tests / 119 pass / 10 fail |
| `npm run firmware:check` | **NOT_RUN（今日）** | 历史 2026-10-25：331 s 通过；W1 未复跑 |
| `python -m unittest discover mcu-book/tests` | **PASS** | `Ran 59 tests in 25.895s · OK` |
| `npm run test:browser` | **NOT_RUN** | 无 dist；且 `playwright.config.mjs` baseURL 仍旧 `/mcu/`（§5-④） |
| `ruff check .` | **PASS** | `All checks passed!` |
| 每个新门"故意失败样例 + 报错原文" | 历史已具备 | `verification-log.md` §2–§6；本轮未新增门 |
| `tests/workflow.test.mjs` 随 workflow 更新 | **FAIL** | 路径、`uses` 值、ruff `args` 三处均已过期（即使修路径仍会红） |
| `task_verify` | **UNVERIFIED** | 基线不可用，不能当通过 |
| quality-contract 收录新门签名 | 已收录 | `.trellis/spec/docs-site/quality-contract.md` §2/§3 |

## 5. 合并接线缺口（W2 只读发现，未修，归合并 P2）

1. **`tests/workflow.test.mjs` 与合并后 workflow 全面脱节**
   - 读 `.github/workflows/{quality,deploy,book,links}.yml` → 实际在**仓库根**且名为 `mcu-*.yml`（`mcu/.github/` 不存在）→ ENOENT。
   - 即便改路径：`deploy.jobs.quality.uses` 断言 `./.github/workflows/quality.yml`，实际 `mcu-quality.yml`；ruff `args` 断言 `'check'`，实际 `check --config mcu/ruff.toml mcu`；`book` 应读 `mcu-book.yml` 而非根 `book.yml`（后者是 STM32 主仓的书流程）。
2. **4 个测试文件的合成夹具仍用旧 base `/mcu/`**（见 §3.1），共 9 条失败。
3. **`local-gates.{ps1,sh}` 与 quality 链不同集合**：漏 `prose:check`；脚本注释仍宣称同集合。
4. **`playwright.config.mjs` 仍指 `http://127.0.0.1:24318/mcu/`**：站点 base 已为 `/STM32/mcu/`，浏览器回归即便有 dist 也会打错 URL。
5. **仓库 URL 口径**：`CITATION.cff` 的 `repository-code` 与 `docs-check.mjs` 的自链前缀仍是 `github.com/zhuguang-ZFG/mcu`；合并后主仓为 `zhuguang-ZFG/STM32`、子树路径 `mcu/`。`url` 字段已改新站点。
6. **本机缺构建产物**：无 `docs/.vitepress/dist`、无 `mcu-book/dist/*.pdf`；`docs:build` 本机 OOM（约 550 MB Node 进程上限），PDF 重建约 8 分钟。故 dist/PDF 运行期门只能等 CI 或换环境复跑。

## 6. 可下的结论与下一步（不含实施）

- **可下结论**：BMS-Z 的机制在合并后的 mcu 子树中未丢失；R2/R7 与 Python 测试当前为绿；P3/P4 的反向夹具齐备且通过。
- **不可下结论**：当前不能说"P1/P6 通过"——前者被测试夹具拖红，后者运行期未跑；也不能把 10-25 的 PDF 证据套到 16 开契约上。
- **建议顺序（需另行授权/复核）**：
  1. 合并 P2：修 `workflow.test.mjs` 路径与断言、4 个夹具的 base、playwright baseURL、local-gates 补 `prose:check`、CITATION `repository-code`；修复后重跑 `npm test`（预期 129/129）。
  2. 在 CI（Linux）跑一次 `mcu-quality` + `mcu-book`，用真实 16 开 PDF 重新取证 P3，用 dist 取证 P6。
  3. 之后才更新历史任务 10-25 的状态，而不是现在把历史 PASS 直接搬过来。

## 7. 本轮证据命令（可复跑）

```bash
npm test > .temp/w2-npm-test.log 2>&1   # exit=1; 129 tests / 119 pass / 10 fail
npm run docs:check                      # exit=0; 138 文件 / 6 类 / 27 条声明
python -m ruff check .                  # exit=0; All checks passed!
python -m unittest discover mcu-book/tests -v  # exit=0; Ran 59 tests / OK (25.895s)
node tests/workflow.test.mjs 等价入口：node --test tests/workflow.test.mjs  # ENOENT: mcu/.github/workflows/quality.yml
```
