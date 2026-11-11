# 验证记录（2026-10-25 实测，逐条可复跑）

本文件是 P8 的收口证据：每条给命令与真实输出摘要；故意失败样例逐条保留报错原文。

## 0. 端到端：本地门禁全量

```
$ powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-gates.ps1
[PASS] node / test / projects:check / docs:build(38s) / anim:lint / readme:check / reading:check
       links:check / docs:check / nav:check / seo:check / perf:budget(24s) / a11y:check
       pages:check / search:check / anim:audit / test:browser(34s) / firmware:check(331s)
       book:check / book:unittest / book:pack / book:pack-verify / book:pdfcheck / ruff
共 24 pass / 0 fail / 0 skip（457s）
```

`sh scripts/local-gates.sh --only node` → `[PASS] node —— v24.14.0`，`exit=0`。
注意：本机 `bash` 指向未安装的 WSL（`C:\Windows\system32\bash.exe`），Git Bash 侧要用 `sh` 调用。

## 1. P1 门禁与环境钉死

- `python -m ruff check .` → `All checks passed!`（exit 0）。
- 本机 ruff 版本与 CI 对齐：`ruff 0.15.21`（`pip install ruff==0.15.21`）。
- 故意失败样例（未定义名必须被抓）：
  ```
  $ printf 'def f():\n    return undefined_name_xyz\n' > .temp/ruff-probe.py && python -m ruff check .temp/ruff-probe.py
  F821 Undefined name `undefined_name_xyz` … Found 1 error.
  ```
- `.ps1` BOM 复验：前 3 字节 `ef bb bf`。
- 三个 workflow + links.yml 的 runner：`tests/workflow.test.mjs` 断言全为 `ubuntu-24.04`。
- **lint 抓到的真 bug**：`mcu-book/build_html.py:319` 原为
  `kind, video_id, title = match.group(1), match.group(2), match.group(3) or video_id`
  —— 把自己赋给自己，`<VideoEmbed>` 缺 title 时会 NameError；已改为 `or match.group(2)`。
- 修 lint 后行为未变：`python scripts/device-console.py self-test --timeout 1` → 通过。

## 2. P2 文档一致性门

- `node scripts/docs-check.mjs` → `✓ 全站文档一致性检查通过：扫描 130 个 Markdown 文件，5 类检查（其中数字声明 27 条）`，exit 0。
- 故意失败样例（4 条，改后均已还原）：
  - 坏锚点：`docs/stm32/03-gpio.md:184 … 锚点 #不存在的锚点 在 ../c/02-pointer.md 里找不到对应标题`
  - 真 TAB：`docs/stm32/03-gpio.md:184 正文里出现真 TAB 控制字符`
  - 数字写错：`README.md:12 → 「章节数」写的 89（=89）与实际 88 不符`
  - 自链不存在：`docs/reference/about.md:68 自链 …/LICENSE.txt 指向工作树里不存在的 LICENSE.txt`
- 新增两条对账的样例（单测覆盖）：CITATION 字段漂移两条点名；CHANGELOG 三种漂移（站点无提法 / 与 manifest 版本不符 / 无版本节）。
- 锚点语义实测：`vitePressSlug('第五步：接线（SWD 四线）')` = `第五步-接线-swd-四线`，与产物 `id="第五步-接线-swd-四线"` 逐字一致。

## 3. P3 PDF 出版契约门（真实产物）

```
$ python mcu-book/build_html.py --pdf        # 7m53s，html 6,015,010 B / pdf 24,495,763 B
$ python mcu-book/check_pdf.py
✓ 元数据与 manifest 一致（title/author/subject 逐项相等）
✓ 大纲条目数与章节+附录+分部一致（共 1889 条大纲）
✓ 封面无页脚页码（第 1 页页脚带无 N / total）
✓ 除封面每页页脚为 N / total（逐页核对 712 页）
✓ 结构页（前言/目录/分部隔页）无页眉（跳过集合 12 页）
✓ 逐页页眉与映射一致（逐页核对 700 页）
✓ total 自洽（total = 712，全书 713 页）
check_pdf: PASS
```
- 反向用例见 `mcu-book/tests/test_check_pdf.py`（元数据不符 / 缺页脚 / 章首页多页眉 / 大纲少一条 / 缺文件）。

## 4. P4 下载打包

```
$ python mcu-book/publish_downloads.py --out-dir .temp/book-downloads
✓ 下载包已发布（7 个文件：SHA256SUMS.txt、book-downloads.json、index.html、
  mcu-deep-book-v1.0.0.html/.pdf、mcu-deep-book.html/.pdf）
$ python mcu-book/publish_downloads.py --verify .temp/book-downloads
✓ 下载包校验通过：4 个文件与 SHA256SUMS.txt 一致
```
- 故意失败样例（篡改 PDF）：
  ```
  ✗ 下载包校验失败 1 处：
    - mcu-deep-book.pdf: 实际 195edf56… ≠ 记录 78daa553…
  ```
- **平台差异实测（写进代码注释与 spec 的事实）**：
  - `python -c hashlib` 真值 = `78daa553…`；`sha256sum mcu-deep-book.pdf` 单跑也是 `78daa553…`；
  - 但 `sha256sum -c SHA256SUMS.txt`（Git for Windows 0.8.0）对两个 PDF 判 FAILED、HTML 判 OK；
    实测原因：该实现**忽略 `*` 二进制标记、一律按文本模式读**（把 CRLF 换成 LF 后的摘要是 `19f653f5…`，用它做清单才能过）。
  - 结论：清单按 GNU 口径写、CI 用 Linux 的 GNU `sha256sum -c` 作权威判定，本机自证用 `--verify`（hashlib）。
    两个口径都已进 CI（book.yml 与 quality.yml 各一步）。

## 5. P5 外链巡检

本机装 lychee 0.24.2（`gh release download -R lycheeverse/lychee`，放 `.temp/`，不入库）按 CI 口径预演：

```
$ lychee --config .lychee.toml -m 5 --no-progress './docs/**/*.md' './README.md' './CONTRIBUTING.md' './mcu-book/**/*.md' './code/**/*.md'
🔍 2301 Total · 🔗 466 Unique · ✅ 177 OK · 🚫 5 Errors · 👻 2119 Excluded
```
- 收敛过程（都是实测，不是猜）：
  - 不给 `root_dir` → 642 条 "Cannot resolve root-relative link"（VitePress 站内绝对路径）；给 `root_dir = "docs"` 后消失。
  - `exclude` 过滤不了解析期错误；`exclude_path` 是**正则不是 glob**，且 Windows 路径是反斜杠 → 用裸目录名 `managed_components` 才匹配。
- 死链判红能力验证：临时往 README.md 追加一条站内 404 链接 → lychee 报错且非零退出（README 已还原，`git diff` 为 0）。
- 两条真失败已分别处置（都写进 `.lychee.toml` 的理由注释）：
  - `code/esp32/05-audio-play/managed_components/**/CHANGELOG.md` 里的 datasheetspdf → 第三方组件源码，用 `exclude_path` 排除；
  - `docs/guide/hardware.md:15` 的 lcdwiki → 证书链不全（openssl 复测 leaf 有效 2026-09-06→2026-12-05，`--insecure` 返回 200，浏览器走 AIA 可开），按"放行 + 理由 + 月度复查"处理。

## 6. P6 dist 侧对账

- `node scripts/pages-check.mjs` → 首跑抓到 1 条真坏锚点：
  ```
  ✗ 1/2627 条站内锚点链接对不上：
    - lab/e01-blink.html:39 → href "./../stm32/00-env.html#第五步接线swd-四线" 期望 stm32/00-env.html 含 id="第五步接线swd-四线"，实际不存在
  ```
  修完源码锚点后：`✓ 124 个页面、2627 条带锚点链接全部命中目标 id`。
- `node scripts/search-check.mjs` → `✓ 2147 个章节/小节标题都能被站内搜索翻到自己那一页（55164 个 term）`。
- **口径推翻与重建（重要）**：最初按"术语表成员"判，报 20/1034 缺失；实测否证——索引里确实没有 `位艺`
  这类跨词边界二元组（`移位艺术` → 有 `移位`/`艺术`，没有 `位艺`），但用它真查一次能翻到 `stm32/12-spi.html`。
  重建站点后现象可复现（不是索引陈旧），于是改成按用户可见承诺判：真查一次、要求命中该页。
  期间还修掉两个实现错：index 页 URL 是目录式（`build/index.md` → `/mcu/build/#…`），根页只能认 `/mcu/#`。
- 故意失败样例（摘掉分词器重建）：
  ```
  $ (临时把 config.mts 的 tokenize 注释掉) npx vitepress build docs && node scripts/search-check.mjs
  ✗ 770/2147 个标题在自己的页面里搜不到： … 检索返回 0 条，其中没有这一页
  ```
  恢复 config.mts 后重建 → 全绿；`git diff docs/.vitepress/config.mts` 为空。

## 7. P7 元文件与发布口径

- `docs:check` 已含 `checkCitation` / `checkChangelog`，真实仓库零报错（v1.0.0 与 manifest/站点一致）。
- 单测覆盖：CITATION 字段漂移 2 条点名、文件缺失报错；CHANGELOG 站点无提法 / 版本不符 / 无版本节三种。
- 锁文件同步（阻断项已修）：`minisearch` 已进 `package-lock.json` 的根 devDependencies；
  `npm ci --dry-run` → `up to date`，不再会在 CI 装依赖那步炸。

## 8. 测试与回归总量

- `node --test tests/*.test.mjs` → 109 pass / 0 fail。
- `python -m unittest discover mcu-book/tests -v` → 24 tests OK（含既有 test_build 的 88 章契约）。
- `npm run firmware:check` → 通过（331s，ARM 全工程 + 场景切换 + SP/Reset 校验）。
- `npm run test:browser` → 通过（34s）。
- `task_verify`：本仓库无配置基线 → 返回 `unverified (project-or-git-baseline-unavailable)`，非"通过"。

## 9. 未验证项（如实列出）

1. **CI 侧尚未跑**：三个 workflow 与 links.yml 的改动只在本机按等价口径预演（YAML 结构、命令、runner、位置由 `tests/workflow.test.mjs` 断言），真正的 GitHub Actions 运行要等 push 之后。
2. **lychee 的 CI 实现版本**：本机用 lychee 0.24.2 预演，CI 用 `lycheeverse/lychee-action@v2` 自带的版本，可能有细微差异（排除清单已按实测收敛，若 CI 出现新的假红按同一套理由处置）。
3. **`anim:audit` 在 ubuntu-24.04 的字体度量**：本地为 Windows 雅黑；CI 换钉板后需要一次真实运行确认（`--font-scale` 机制已存在）。
4. **`.ps1` 在 PowerShell 7（pwsh）下**：本机只有 Windows PowerShell 5.1，按 5.1 兼容写的；pwsh 未验证。