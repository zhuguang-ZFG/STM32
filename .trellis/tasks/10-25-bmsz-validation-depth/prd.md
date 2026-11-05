# BMS-Z 对齐：验证纵深（门禁 / 契约 / 产物对账）

## Goal

以姊妹项目 `D:\Users\BMS-Z` 的工程化做法为参照，把 mcu 仓库的**验证纵深**补齐：让"提交前能自查、上线物被检查、发布物有凭据、手工写的结论被机器对账"。

差距不在 CI 有无（mcu 的三个 workflow 已是硬门禁），而在三处结构性错位：

1. **检查对象错位**：`deploy.yml` 部署的是 `checks` 上传的 `docs-site` artifact，但部署前不再对该产物做任何检查；PDF 只被生成、从不被回收验证。
2. **文档结论无人对账**：正文/README 里手写的章数、动画张数、测验组数、契约数，与实际清单之间没有任何机器校验；锚点只在根 `README`/`CONTRIBUTING` 被查（`links-check.mjs`），全站 `.md` 锚点无检查。
3. **发布物无凭据**：整书 `html/pdf` 直接 `cp` 进站点，没有校验和、没有版本化文件名、没有下载落地页。

## 现状基线（2026-10-25 实测，证据见 `research/bmsz-gap-analysis.md`）

- 工作流：`quality.yml`（`checks`/`arm-host`/`esp32`）、`book.yml`（`book`）、`deploy.yml`（`quality`→`deploy`），全部阻断式，无 `continue-on-error`。
- `quality` 脚本 = 11 项 `&&` 链，作用于**源文件与构建产物**；`docs:build` 已开启 `ignoreDeadLinks: false`（内部链接存在性已由 VitePress 兜住，**锚点不在内**）。
- `checks` job 末尾：`python mcu-book/build_html.py --pdf` → `cp mcu-book/dist/mcu-deep-book.{html,pdf} docs/.vitepress/dist/book/` → upload artifact。
- `mcu-book/`：`build_html.py --check` 做 HTML 产物审计（88 章、罗盘、附录、内链锚点、组件残留、测验答案）；`--pdf` 用 PyMuPDF 写页眉/页码/大纲/元数据；**无独立 PDF 校验、无打包器**。
- `mcu-book/tests/test_build.py` 已有 88 章覆盖与 6 个破坏性用例。
- `tests/workflow.test.mjs` 断言 job 集合、无 `continue-on-error`、容器 `espressif/idf:v5.5.2`。
- 缺失：根 `CHANGELOG.md`、`CITATION.cff`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`.lychee.toml`、`local-gates.{ps1,sh}`、`links.yml`、`ruff.toml`、Python lint job、PDF 契约门、下载打包器、dist 侧锚点/搜索对账。
- 三个 workflow 均 `runs-on: ubuntu-latest`；`devDependencies` 全部 caret 版本。

## 已确认的决定（2026-10-25 对话）

1. 建立**单任务 + 分期**（不拆父子任务）。
2. 范围取默认**全量对齐**（下表 8 项）。
3. 参照物是 BMS-Z 的**机制**，不是它的业务内容：锚点算法、门清单、契约门的设计意图照搬，具体规则按 mcu 的真实资产重写。

## Requirements

### R1 本地一键门禁 `scripts/local-gates.ps1` + `.sh`

- 逐项复跑 CI 全部门（**逐项执行而非 `&&` 链**，任一失败仍继续跑完其余项），末尾汇总。
- 语义与 BMS-Z 一致：`FAIL` 置退出码非零；工具缺失记 `SKIP` 并给安装提示，不伪绿。
- `.ps1` 存为 **UTF-8 with BOM**（PowerShell 5.1 中文安全）；解释器探测 `python` → `py`；`.sh` 用 `python3` → `python`。
- 覆盖：已有 11 项 quality 项 + `anim:audit` + `test:browser` + `firmware:check` + `book:check` + `book:pdf`+PDF 契约 + 新增三项 + `ruff`。

### R2 文档一致性门 `scripts/docs-check.mjs`（npm `docs:check`）

- 全站 `.md`：相对链接存在性；`.md` 锚点按 GitHub slug 算法解析；`.html` 锚点按 `id` 解析；拒绝路径尾部 `.`/空格。
- Markdown 卫生：拦控制字符（含被存成真 TAB 的转义）与 `\(`…`\)` 定界符。
- 本仓库 `github.com/zhuguang-ZFG/mcu/blob/<ref>/<path>` 自链改为按工作树校验。
- **手写数字声明对账**：正文/README 中声明的章数、动画张数、测验组数、工程数、契约数与实际清单一致；`CLAIMS` 正则未捞到预期句数即报红（防静默通过）。
- 注册进 `npm run quality`。

### R3 PDF 出版契约门 `mcu-book/check_pdf.py`

- 反向校验产物：元数据与 `manifest.json` 一致；大纲条目数与章节+附录一致；封面无页脚页码；除封面每页页脚为 `页码 / 总页数`；章首页/分部页无页眉；正文页页眉与 `build_html.py` 的运行页眉映射一致。
- 复用 `build_html.py` 的 manifest 加载与页眉映射（**单真源，不复制规则**）。
- 有 `mcu-book/tests/test_check_pdf.py`（合成 PDF 夹具 + 反向用例）。

### R4 下载打包器 `mcu-book/publish_downloads.py`

- 从 `manifest.json` 取 `version`（要求 `\d+\.\d+\.\d+`），产出稳定名 + `-vX.Y.Z` 版本名、`SHA256SUMS.txt`、`book-downloads.json`、落地页 `index.html`。
- staging → replace 原子更新；输入缺失时保留上一份完整包。
- 有 `mcu-book/tests/test_publish_downloads.py`。
- 接入 `checks` job（产物落到 `docs/.vitepress/dist/downloads/`）并加站点入口。

### R5 外链巡检 `.lychee.toml` + `.github/workflows/links.yml`

- 两轮制（第 1 轮失败 → 等 180s → 报告挪成隐藏文件 → 第 2 轮），`fail: true`；含月度 `schedule`。
- 排除清单逐条配注释说明"为什么放行"。

### R6 部署前 dist 侧对账

- `scripts/pages-check.mjs`：扫 `docs/.vitepress/dist/**/*.html`，校验内部链接带锚点时目标文件存在且含该 `id`。
- `scripts/search-check.mjs`：校验构建后的本地搜索索引包含各章正文里的关键术语（防分词器静默失效）。
- 两者在 `deploy.yml` 的 `upload-pages-artifact` **之前**执行（对真正要上线的 artifact，而非源文件）。

### R7 Python lint

- `ruff.toml`：`select = ["E4","E7","E9","F","B","UP","W605"]`，注释说明不做格式化/行长规则的理由（中文计长、对齐注释表会被打散）。
- `quality.yml` 增加 lint 步骤，覆盖 `mcu-book/*.py` 与 `scripts/*.py`。

### R8 环境钉死与元文件

- `runs-on: ubuntu-latest` → `ubuntu-24.04`（三个 workflow）；随附更新 `.gitattributes` 与 `anim-audit.mjs` 里提到 `ubuntu-latest` 的注释（字体度量口径）。
- 补 `CITATION.cff`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、根 `CHANGELOG.md`。
  - `CITATION.cff` 的 title/version/repository/author 必须与 `mcu-book/manifest.json` 一致（由 R2 强制）。
  - 根 `CHANGELOG.md` 每个版本号必须能在站内 `docs/reference/changelog.md` 找到同名提法，且最新版本号 == `manifest.json` 的 `version`（站内更新日志是日期分节，故做"存在性 + 最新版对齐"而不是集合相等）。

## Non-goals

- 不搬运 BMS-Z 的业务检查（SMIL 150 张下界、发布记录表、擂台基线、demo 断言表）——mcu 已有等价物或不存在对应资产。
- 不引入 Python 第一语言化：站点侧门一律 `.mjs`（沿用 `scripts/*.mjs` + `node --test` 既有约定）；Python 只留在 `mcu-book/`（PyMuPDF 已在那里）。
- 不改动站点正文内容、不改 video 流水线、不动 `code/` 固件工程。
- 不为了让门变绿而放宽任何既有断言或阈值。
- 不做 `mcu-book/build_html.py` 的行为性重构；只允许把页眉映射提取成纯函数供 `check_pdf.py` 复用（行为不变，由既有 `test_build.py` 页眉用例覆盖）。

## Acceptance Criteria

### 分期验收（每期可独立验收）

- [ ] **P1 门禁与 lint**：`pwsh ./scripts/local-gates.ps1` 在本机逐项跑完并打印 `FAIL/SKIP` 汇总；删掉 ruff 时该项记 `SKIP` 而非失败；`ruff check .` 对现有 Python 零告警；`quality.yml` 的新步骤在 PR 上跑绿。
- [ ] **P2 文档一致性门**：`npm run docs:check` 对当前仓库零报错；对 4 类故意破坏（坏锚点、真 TAB、数字声明写错 1 章、自链指向不存在文件）各自点名报错；`npm run quality` 已包含它。
- [ ] **P3 PDF 契约门**：`python mcu-book/check_pdf.py` 对 `build_html.py --pdf` 产物通过；对 4 类人为破坏（改元数据、去页脚、加页眉到章首页、删一条大纲）各自点名；`test_check_pdf.py` 全绿。
- [ ] **P4 下载打包**：`python mcu-book/publish_downloads.py --out-dir <tmp>` 产出 4 个下载文件 + `SHA256SUMS.txt` + `book-downloads.json` + `index.html`；`sha256sum -c` 通过；再跑一次且输入缺失时保留旧包；升版后旧版本文件不残留；`test_publish_downloads.py` 全绿。
- [ ] **P5 外链巡检**：`links.yml` 在 PR 上跑绿；构造一条死链能判红；排除清单每条有注释。
- [ ] **P6 dist 侧对账**：`npm run pages:check`、`npm run search:check` 对构建产物通过；构造一个缺锚点链接与一个从索引移除的词，各自被点名；两者在 `deploy.yml` 中位于 `upload-pages-artifact` 之前。
- [ ] **P7 钉死与元文件**：三个 workflow 均钉 `ubuntu-24.04`；根 `CHANGELOG.md` 的每个版本号都能在 `docs/reference/changelog.md` 找到、最新版本 == `manifest.json` 的 `version`（两处各故意改错一次都会被 R2 点名）；`CITATION.cff` 字段与 manifest 一致（改 manifest 版本而不同步 CITATION 会被 R2 点名）。

### 全局验收

- [ ] `npm run quality`、`npm run firmware:check`、`python -m unittest discover mcu-book/tests`、`npm run test:browser`、`ruff check .` 全绿。
- [ ] 每个新增门都有**一次故意的失败样例与报错原文**（沿用仓库既有约定），写入本期收口记录。
- [ ] `tests/workflow.test.mjs` 随 workflow 变化更新（job 集合、新增步骤、runner 钉死），并在复核门逐条说明改了什么、为什么不是"放宽断言"。
- [ ] `task_verify` 报告 passed/failed/unverified 三分，未跑到的项明确列出。
- [ ] `.trellis/spec/docs-site/quality-contract.md` 收录新门的签名与契约。

## Constraints

- 证据优先：任何"通过/绿"的结论必须来自本机或 CI 的实际输出，不得由推理代替。
- 不改既有断言的严格度；新增检查只允许**加**约束，不允许为了让现状通过而放宽。
- 测试变更（新增 `tests/*.test.mjs`、`mcu-book/tests/test_*.py`、修订 `tests/workflow.test.mjs`）需要在复核门单独列出并请求复核。
- 本机为 Windows（PowerShell 5.1 + Git Bash）；`.ps1` 必须 BOM 编码；`.sh` 不含 CRLF 依赖。
- 不触碰工作树里 video 任务的在途改动；提交只 `git add` 本任务路径。
- 门脚本不得读取凭证、不得联网（外链巡检除外，且只在 CI）。

## Open Decisions（复核门收口）

1. **分支策略**：当前分支 `feat/video-v2-remaster` 有 315 个在途改动。本任务提交按显式路径 `git add`，与 video 改动物理隔离；是否另开分支留给用户定。
2. **根 `CHANGELOG.md` vs 站内 `docs/reference/changelog.md`**：默认双份 + 集合一致性校验；若用户要求单真源，则改为根文件为源、站点侧引用。
3. **`ubuntu-24.04` 钉死后 `anim:audit` 的字体度量**是否与 `ubuntu-latest` 当前一致（预期一致，需 CI 一次实测佐证）。
4. **R6 搜索对账的术语来源**：默认取章节标题 + H2/H3 + 仓库既有术语表（若存在）；不引入人工维护的第二份词表。