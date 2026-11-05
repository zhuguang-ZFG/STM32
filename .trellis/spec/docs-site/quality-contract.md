# 质量与复现契约

## 1. Scope / Trigger

修改工程、章节元数据、实验状态、部署流程或搜索/语法高亮时，适用本合同。

## 2. Signatures

- `npm run quality`：单元回归、工程清单、站点构建、动画、README、链接、导航可达性、分享/收录元数据、性能预算、无障碍基线。
- `npm run nav:check`：扫描全部页面，检查每个页面都能从 `config.mts` 的 nav/sidebar 到达（页面→入口方向，正是死链检查的反面）。
- `npm run seo:check`：检查构建产物含 sitemap.xml（每条 `<loc>` 必须带 `host+base` 前缀）、robots.txt、og-cover.png，每页都有 og/twitter 分享卡与 canonical，**且本地搜索索引含足量中文二元组**。需先构建。
- `npm run perf:budget`：纯静态体积预算（zlib，无浏览器）——首屏外壳+CSS、渲染阻塞 CSS、最大单块、搜索索引原文。需先构建。行为侧（延迟索引、减少动效）仍由 `test:browser` 覆盖，两者分工不重叠。
- `npm run a11y:check`：无障碍静态审计——每页 html[lang]、img alt、button/链接可访问名、h1、地标（main/VPContent）。需先构建。
- `npm run firmware:check`：ARM/host 全工程、五场景切换、初始 SP 与 Thumb 复位向量验证。登记了 `probe` 的 arm-make 工程，建完 ELF 还会跑一遍 `probe.sh`（无板取证：宿主断言 → 与 CMSIS/正文对账 → 交叉反汇编）。
- `npm run test:browser`：构建后运行；先 `npx playwright install chromium`。本机可 `PLAYWRIGHT_CHANNEL=msedge`。
- `npm run site:measure -- current [output-directory]`：测量产物与搜索延迟加载，默认输出 test-results/performance。
- `node scripts/project-catalog.mjs --matrix`：仅向 stdout 输出 JSON `{include:[{path,target}]}`，供 CI 消费。
- `npm run docs:check`：全站文档一致性门（`scripts/docs-check.mjs`）——相对链接与锚点、Markdown 卫生（控制字符、`\(\)`）、仓库自链按工作树核对、**手写数字声明对账**、CITATION/CHANGELOG 与 manifest 口径对账。只读源文件，不需构建。
- `npm run pages:check`：产物锚点门（`scripts/pages-check.mjs`）——扫 `docs/.vitepress/dist` 每个页面的 `#fragment` 链接，要求目标页真有那个 `id`。需先构建；支持 `--dist <dir>`（部署侧对 artifact 用 `--dist site`）。
- 产物锚点门先清空 `script/style` 原始文本再提取 href，保留行号；JS 中的 CSS 选择器不是实际链接。独立 HTML 导读的过期门与入口检查见 [presentation-assets.md](presentation-assets.md)。
- `npm run search:check`：搜索可达性门（`scripts/search-check.mjs`）——用站内同一套 tokenizer 载入产物索引，逐个章节/小节标题**真查一次**，要求命中该标题所在页面。需先构建。
- `npm run book:pdfcheck`：PDF 出版契约门（`mcu-book/check_pdf.py`）——元数据、大纲条数、封面无页码、逐页 `N / total`、结构页无页眉、逐页页眉与映射一致。
- `npm run book:pack` / `publish_downloads.py --verify <dir>`：下载打包（稳定名 + `-vX.Y.Z` 版本名 + `SHA256SUMS.txt` + `book-downloads.json` + 落地页，staging→整体替换）；`--verify` 用 hashlib 逐条核对既有包。
- `bash scripts/local-gates.sh [--only <label>]` / `powershell -File scripts/local-gates.ps1 [-Only <label>]`：本地逐项复跑上面这些门（FAIL 非零退出，工具缺失记 SKIP），与 CI 同集合。

## 3. Contracts

- `code/projects.json` 数组：`id` 唯一；`path` 为 `code/<board>/<project>`；`kind` 为 arm-make/esp-idf/host-probe/host-make；`entry` 必须存在且与类型一致。ESP 的 `target` 必须是 esp32s3，RTOS `scenes=[1,2,3,4,5]`。可选 `probe`：只允许 arm-make，值必须是 `probe.sh` 且文件真实存在——它是"板级固件 + 无板取证"同目录共存的唯一登记方式（`host-probe` 那一类是纯取证工程，有自己的目录与 entry）。CI 侧 `arm-host` job 会把 `.trellis/ref/cmsis` 固定到 cmsis-device-f4 `v2.6.11` + CMSIS_5 `5.9.0` 并校验 sha256，取证脚本的头文件对账因此在 CI 上有第二来源；交叉反汇编那一步只在本机钉住的工具链版本上判定，别的版本打印跳过。
- 章节：title 非空字符串，status=done/building，difficulty=1/2/3，minutes 正整数。非法值使生成进程非零退出，不能降级为告警再产出数据。
- 实验额外字段：code_status=ready/planned、hardware_status=pending/verified、code_note 非空、projects 为工程 ID 数组。ready 必须引用工程；verified 必须有 docs/ 下的 evidence 文件。
- status 只表示文稿；LabStatus/LabOverview 从元数据与 progress.json 显示时长、难度、代码状态和实测状态。禁止将成稿数说成实测数。
- 部署调用本地 reusable quality workflow；deploy 必须依赖其全部 jobs 成功，且目标为 main。PR 只读权限，不得 continue-on-error 放行必需检查。
- 搜索索引只在打开搜索时加载；索引正文/行内标识符，完整代码块从索引中剔除。ld/gdb 由 code-languages.mjs 的 TextMate 规则渲染。
- **锚点有两套 slug，必须按两边取并集判**：站点侧 VitePress 把全角标点折成 `-`（`第五步：接线（SWD 四线）` → `第五步-接线-swd-四线`），GitHub 直接丢标点（→ `第五步接线swd-四线`），书籍构建器与 GitHub 同款。所以：源码里的锚点由 `docs:check` 按并集接受，站点那侧的真值由 `pages:check` 对 dist 产物核对，书籍那侧由 `build_html.py` 的 `fragment_key`（去分隔符比较）解析——**三处不许各写一套规则**。
- **`SHA256SUMS.txt` 用 GNU 口径（`<sha> *<name>`）**：GNU coreutils 下 `sha256sum -c` 全 OK；Git for Windows 的 `sha256sum -c` 实测忽略 `*`、一律按文本模式读，PDF 会误报 FAILED。所以本机自证走 `publish_downloads.py --verify`（hashlib），CI 用 GNU `sha256sum -c` + `--verify` 双口径。
- **Python lint 范围**：根 `ruff.toml` 只启用「能抓真错误」的规则集（E4/E7/E9/F/B/UP/W605），`extend-exclude = [".trellis", "video"]`（框架托管目录与在途的视频任务不纳入），版本在 CI 里钉 `0.15.21`。
- **runner 钉 `ubuntu-24.04`**（三个 workflow 与 links.yml 一致）：`ubuntu-latest` 会让字体度量与工具链版本在无声中漂移，`anim:audit` 的判定依赖字体度量。
- **`CITATION.cff` 与根 `CHANGELOG.md` 必须与 manifest/站点同源**：CITATION 的 title/version/repository-code/url/authors[0] 对 manifest 与站点 host；`CHANGELOG.md` 的每个 `## vX.Y.Z` 都要能在 `docs/reference/changelog.md` 找到提法，最新版本号必须等于 `mcu-book/manifest.json` 的 `version`。

## 4. Validation & Error Matrix

| 输入/事件 | 结果 |
|---|---|
| 空目录 | 不计工程 |
| 有构建入口但未登记 / 路径失效 / 重复 ID | 报错 |
| minutes=0、difficulty=4、status=finished | 报错 |
| 实测 verified 但无证据 | 报错 |
| 任一 CI job 失败/取消/跳过 | 不部署 |
| 搜索产物 raw >500 kB | 保留告警，记录 gzip/Brotli/首屏请求，不能单纯调阈值 |
| 首屏外壳+CSS、CSS、最大单块或搜索索引超出 perf:budget | 报错；确属合理增长再上调 BUDGETS 并说明原因 |
| 搜索索引缺少中文二元组（seo:check） | 报错；说明 `themeConfig.search.options.miniSearch.options.tokenize` 被误删，中文搜索会静默失效 |
| 改动搜索分词器 | 构建端与浏览器端必须共用同一函数（VitePress 两端都读 `miniSearch.options`），否则索引与查询口径不一致、搜索整体失效 |
| 页面缺 lang、img alt、button/链接可访问名、h1 或地标 | 报错；框架级组件（如 VPSwitch）可列入白名单，但须注明理由 |
| 站内链接的 `#fragment` 在目标页不存在（pages:check 对 dist 核对） | 报错并点名 `文件 → href → 期望 id vs 实际`；不许改成"只查文件存在" |
| 章节标题用站内搜索查不到自己那一页（search:check） | 报错；多半是 `miniSearch.options.tokenize` 被删回默认分词，索引与查询口径不一致 |
| 正文手写的"N 章 / N 张动画 / N 个契约"与真源不符，**或正则一处都没命中** | 两类都报错：值不符要改文案；命中数为 0 说明写法漂移，门不许静默变绿（同步更新 `CLAIMS`） |
| `CITATION.cff` / 根 `CHANGELOG.md` 与 manifest 或站点更新日志漂移 | 报错；引用格式被外人直接抄走，过期版本必须当场拦住 |
| 下载包 `SHA256SUMS.txt` 与实际字节不符（`--verify` 或 GNU `sha256sum -c`） | 报错并点名文件与两个摘要；打包失败时不许留下半个包（staging→整体替换） |
| `ruff check .` 有任一命中（含 F821 未定义名） | 报错；`extend-exclude` 之外的任何"排除"都必须在 ruff.toml 里写出理由 |

## 5. Good / Base / Bad Cases

- Good：E07 文稿 done、代码 ready、硬件 pending，有独立工程和精确接线。
- Base：E04 文稿 building、代码 planned、硬件 pending，明确这是实验方案。
- Bad：八篇实验都 done 因而写“八项已实测”；给未构建目录冠以“可构建”标签。

## 6. Tests Required

- tests/catalog.test.mjs：空目录、失效入口、未登记工程、重复与目标错配。
- tests/nav.test.mjs：sidebar 全量（正例）、漏登记被拦截（反例，GD32 回归）、锚点/尾斜杠归一。
- tests/seo.test.mjs：meta 抽取与空值、单页分享卡齐全、og:image/url 必须绝对 URL、sitemap 丢 base 前缀被拦截（反例）、robots 缺项。
- tests/perf.test.mjs：压缩体积计算、首屏资源抽取去重、预算内通过、超预算逐项点名、搜索索引单独设限。
- tests/a11y.test.mjs：属性抽取、文本清洗、完整页面通过、缺 lang/img alt/button name/link text/h1/landmark 被点名、VPSwitchAppearance 白名单。
- tests/metadata.test.mjs：缺项、非法数值/枚举、重复 YAML 字段。
- tests/workflow.test.mjs：同提交依赖关系、PR 权限与失败传播。
- tests/search.test.mjs、tests/browser/site.spec.mjs：高亮实际 token、保留正文、搜索结果、延迟索引、暂停/减少动效、移动端实验卡。
- scripts/check-firmware.mjs：场景 1→2→1 的真实二进制、flash 路径、非法场景拒绝；二进制开头 SP/Reset 与 ELF 符号对应。GD32 可将向量表并入 .text，不能仅依赖输出节名。
- tests/docs-check.test.mjs：slugify 多空格/中文/组合记音、vitePressSlug 三例与产物 id 对拍、链接与锚点命中/未命中、`{#id}` 自定义锚点、围栏内的 TAB 放行而正文 TAB 点名、CLAIMS 值不符与命中数为 0 两类反例、checkCitation 字段漂移与文件缺失、checkChangelog 的三种漂移。
- tests/pages-check.test.mjs：resolveHref 的外链/协议相对/纯 `#`/空锚点/非 html 资产不查；同页、跨页、base、目录、query 全过；缺 id 与缺文件逐条点名。
- tests/search-check.test.mjs：pageHrefPrefixes 的目录式 URL 与根页 `#` 特例；harvestEntries 跳过围栏/四级/空子树/`search: false`；**索引被默认分词建过时必须判红**（口径不一致的回归）。
- mcu-book/tests/test_check_pdf.py：合成 PDF 夹具的完整契约 + 缺页脚/多页眉/大纲少一条/元数据不符。
- mcu-book/tests/test_publish_downloads.py：产物齐备、`sha256sum` 行与 hashlib 一致、`--verify` 通过与被篡改点名、缺输入保留旧包、升版不残留、既无 `--out-dir` 也无 `--verify` 判用法错误。
- tests/workflow.test.mjs：除既有的依赖/权限/容器断线外，还要断言 runner 钉 `ubuntu-24.04`、`lint` job 与 ruff 版本、整书产物之后必须跑契约门与打包、部署前 dist 侧两门位于 `upload-pages-artifact` 之前、links.yml 两轮制与月度 schedule。

## 7. Wrong vs Correct

- Wrong：改 `-DDEMO_SCENE` 却共用 build/main.o。Correct：build/scene-N 隔离，Makefile/头文件更新重建。
- Wrong：汇编只写 `.thumb` 就认为向量里的地址带 Thumb 位。Correct：Reset_Handler 标记 `.thumb_func`/function 类型，并核验 bin 第 4 字节起的复位字最低位为 1。
- Wrong：往 N16R8 GPIO35 输出 PWM 证明它被占用。Correct：以模组资料核对；示例只在 GPIO10/11 路由，并先 gpio_reset_pin 断开旧输出。
- Wrong：正文里写 `[第五步](../stm32/00-env.md#第五步接线swd-四线)` 就以为跨渲染都可点。Correct：全角标点让站点 id 变成 `第五步-接线-swd-四线`；源码锚点按两套 slug 的**并集**判定（docs-check），站点那侧由 pages-check 对 dist 核对，书籍那侧由 `fragment_key` 去分隔符解析。
- Wrong：拿 Git for Windows 的 `sha256sum -c` 红了就断定下载包坏了（它按文本模式读，PDF 必误报）。Correct：本机用 `publish_downloads.py --verify`，权威判定交给 Linux 上的 GNU `sha256sum -c`，两者都进 CI。
- Wrong：为了让 `ruff check .` 变绿就 `--add-noqa` 或把规则从 `select` 里删掉。Correct：修代码；确要排除某目录，必须在 `ruff.toml` 里写出"为什么它不属于维护面对"。本门已经抓到过一个真 bug：`mcu-book/build_html.py` 里 `match.group(3) or video_id`（自己赋给自己）。
