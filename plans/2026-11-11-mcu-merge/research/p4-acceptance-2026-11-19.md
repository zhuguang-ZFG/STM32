# P4 验收记录（2026-11-19，2026-11-22 修订）

候选分支 `feat/mcu-merge-p1`，PR #140（草稿）；本记录成文（2026-11-19）时尖端 `f3b3a55b`，此前各轮为 `1c0ee761`、`6b8d9b48`、`c85bbb1e`、`6f151cb5`、`649fba2b`、`818ef375`、`df187f3d`；2026-11-22 分两批：第一批修 AC7 四处元数据并加引用门（`23ca1fcb`）；第二批按 owner 决定落地 AC3 下载入口、AC7 许可口径与 AC2′/AC5′（见 §3.1 修订提案）。基线 `main@4882857e`（未动）。本记录逐条对照 [`prd.md`](../prd.md) §3 的 AC1–AC8 判，证据只写本次实测或可复算的值。

## 结论

| AC | 判定 | 一句话 |
| --- | --- | --- |
| AC1 | `PASS` | 来源祖先成立；1580 条差异全部落在已记录事件内；迁移前修改未被覆盖 |
| AC2 | `PASS`（按 AC2′） | 原不变量被 B5 取消；`prd.md` §3.1 的 AC2′ 已获 owner 批准生效，替换目标逐条实测通过 |
| AC3 | `PASS` | 下载入口已接入交付链：`deploy.yml` 构建三件产物 → 落 `/book/` → 冒烟带 `--downloads` 断言 200 + 字节下限（本地 15/15） |
| AC4 | `PASS` | 合入后首个 deploy（`45034581583`，`9e798499`）的 artifact 内实测含 `./book/` 三件产物，字节数与线上回读一致 |
| AC5 | `PASS`（按 AC5′） | 退役门在 `prd.md` §3.1 有出处与等价门；现存门全绿，本轮另补三道会真失败的门 |
| AC6 | `PASS` | 23 个活动任务可解析；历史任务未被归档或改判 |
| AC7 | `PASS` | 四处元数据对齐真源；许可改为 `["Apache-2.0", "CC-BY-4.0"]` 双值，与根 `LICENSE` §2/§5 分区一致，并加了门 |
| AC8 | `PARTIAL` | 部署运行、artifact、线上回读都已实测；仍差「旧站兼容决定」与维护入口切换 |

**放行结论：AC1–AC7 全部满足，AC8 部分满足（见 AC8 节）。** 本分支已合入 `main`（merge commit `9e798499`，PR #140），下线回读在 §AC3/§AC4/§AC8 三节。

## AC1 导入可追溯、内容不丢失

复算命令与结果：

```bash
git merge-base --is-ancestor cf161532c823446016a9deb60d31e5263397b7d7 4882857e   # exit 0
git diff --name-status cf161532c8^{tree} 4882857e:mcu | wc -l                      # 1580
git diff --name-status cf161532c8^{tree} 6b8d9b48:mcu | wc -l                      # 1581
```

| 口径 | 路径数 | A | D | M |
| --- | --- | --- | --- | --- |
| `main@4882857e` 的 `mcu` | 1580 | 848 | 692 | 40 |
| 候选尖端 `6b8d9b48` 的 `mcu` | 1581 | 848 | 692 | 41 |

两个口径必须分开引用，不能混用：**P0 基线的 1580 条（40 M）针对 `main@4882857e`**，与[执行快照](execution-snapshot-2026-11-19.md) §2 一致；**候选尖端多出的 1 条是 `M mcu/CONTRIBUTING.md`**，来自本轮 P1 加的横幅与死链降级，属有意改动，不是新发现的导入差异。来源仓该文件在根目录（`cf161532:mcu/CONTRIBUTING.md` 不存在），比较对象是来源树根与目标 `mcu/` 子树。

1580 条差异的成因（见[执行快照](execution-snapshot-2026-11-19.md) §2）：692 条删除全由 B5（`44c0fdb0`）整树退役解释；848 条新增与 40 条修改来自导入后演进（视频发布脚本、`code/`、`.trellis` 任务、逐章修订）。

迁移前修改保留：`research/wip-backup-2026-11-11/` 的字节备份与 2026-11-19 重算的 SHA-256 对照，12 条字节不变，5 条由 `27757966`、`ec980bc7` 解释（见[执行快照](execution-snapshot-2026-11-19.md) §3）。

## AC2 两书正文与工程没有因目录合并而覆盖或改号

**判定 `PASS`（按 AC2′，2026-11-22 由 owner 批准）。** 原文要求「两书分域、入口能区分两书」；B5（`44c0fdb0`）把 MCU 正文并入根书稿、退役 `mcu/docs` 与 `mcu/mcu-book`，这个前提已被设计变更取消。原判 `SUPERSEDED` 的顾虑是「不能在验收记录里就地改判」——该顾虑本轮由 `prd.md` §3.1 解除：修订提案把 AC2 替换为 AC2′（单书模型：一份清单、一个入口、来源与映射留档），并已获 owner 批准生效，所以这里是对**替换后的目标**判通过，而不是把旧目标判成通过。

**后继检查（单书模型下的等价项，另列，不顶替 AC2）**：

```bash
wc -l < book/data/toc.tsv                    # 53
python -m book.manifest --check              # exit 0
python -m book.mapping --check               # exit 0
python -m book.build_html --check            # built 53 pages, 0 planned chapters missing
```

`docs/manifest.json`：`title=通往单片机之路`、`version=0.1.0`、`language=zh`、9 个卷、47 章、6 附录，与 `toc.tsv` 的 53 行一一对应。`mapping.json` 只写在 `plans/2026-11-12-merged-book/`，与书稿目录分离。

入口区分：`README.md`、`STRUCTURE.md` 写明 `mcu/` 保留固件与任务历史、不再有独立书稿站点；`mcu/README.md` 本轮已按此改写。

AC2′ 的三条要求逐条对上：**一份清单** = `book/data/toc.tsv` 53 行 ↔ `docs/manifest.json`；**一个入口** = `/STM32/` 根即合并书（`/STM32/mcu/` 只是存根，实测 396 字节 meta refresh）；**来源与映射留档** = `plans/2026-11-12-merged-book/mapping.json` 与 AC1 的祖先/差异账。

## AC3 新 base 下各入口可访问

**判定 `PASS`（2026-11-22 接入交付链后）。** 下面两个表要分开读：第一张是**修订前**的线上实测（当时下载入口确实全 404），第二张是修订后的本地 staging 实测（入口存在且有真字节）。

修订前实测（2026-11-19，公开站点）：

| 路径 | 状态 | 说明 |
| --- | --- | --- |
| `/STM32/` | 200 | 合并书首页 |
| `/STM32/mcu/` | 200 | 跳转存根，`meta refresh` 指向 `/STM32/index.html`，非 MCU 整书 |
| `/STM32/mcu/book/` | 404 | 旧书入口已清场 |
| `/STM32/mcu/downloads/mcu-deep-book.pdf` | 404 | 旧下载入口已清场 |
| `/STM32/book/` | 404 | 合并书无在线下载目录 |
| `/STM32/book/merged-book.pdf` | 404 | 同上 |

当时**未通过**的原因只有一条：AC3 明确要求「下载入口可访问」，而合并书与 MCU 整书在线上都没有可下载文件（上表四条 404）。浏览器回归（下节）只是把站内导航补齐，不能替代这一条。

### 修订：下载入口接入交付链（2026-11-22）

根因不是「没有产物」——`book.yml` 一直在产出 `book-print` artifact——而是「产物停在 CI artifact，没进 staging，也没人断言它在」。改动三处：

| 位置 | 改动 |
| --- | --- |
| `.github/workflows/deploy.yml` | 新增 setup-python + `pip install -r book/requirements-print.txt` + `playwright install --with-deps chromium`，构建 `book.build_print_edition` / `book.print_pdf` / `book.build_epub`，把三件产物拷进 `.temp/pages-site/book/`；`timeout-minutes` 30→45 |
| 同上，落盘前 | 「Stage offline book」步骤按 `html:1000000 pdf:5000000 epub:200000` 三档字节下限 `test` 一遍再 `cp`，产物为空的构建不往下走 |
| `docs/index.md` + `scripts/site-smoke.mjs` | 首页挂出三份下载链接；冒烟加 `--downloads` 开关，断言 `/book/*` 真实返回 200 且字节数过下限，并断言首页确实渲染出这三条 href |
| `docs/.vitepress/config.mts` | `ignoreDeadLinks: [/\.\/book\//]`：这三条链接指向的产物不在源码树里（构建期才生成），构建期检查看不到它们，因此显式豁免；通不通由冒烟在真实 staging 上验 |

`--downloads` 默认关闭：`site.yml` 是 PR 门，不跑约 15 分钟的印刷链（Chromium 逐动画截帧），staging 里没有 `/book/`；`deploy.yml` 在发布前带着它跑。两边的检查项因此不同（12 项 vs 15 项），但都不是空跑。

本地实测（2026-11-22，候选 staging）：

```text
OK   离线下载 print html — status=200 bytes=28596122 floor=1000000
OK   离线下载 pdf — status=200 bytes=29227410 floor=5000000
OK   离线下载 epub — status=200 bytes=18620776 floor=200000
OK   首页挂出下载入口 — linked=3/3
smoke passed: 15/15
```

产物规格（本地同参数构建）：`merged-book.html` 28.6 MB / 47 章 63 目录项；`merged-book.pdf` 29.2 MB / 837 页；`merged-book.epub` 18.6 MB / spine 64 项、图片 324 张。

负向验证两种故障都真会失败，不是摆样子：

- 把 `/book/` 移出 staging → `FAIL 离线下载 … status=404`，`smoke failed: 3/15`；
- 保留文件但截成 0 字节 → `FAIL 离线下载 epub — status=200 bytes=0 floor=200000`，`smoke failed: 1/15`。后者正是「有响应但空文件」这种最容易混过状态码检查的故障，所以判据取实际收到的字节数，而不是 `content-length`（本地 `serve()` 是流式输出，本来就没有该头）。

成本：deploy 从此多约 12 分钟（HTML 11.5 + PDF 0.5 + EPUB 0.1，本机实测；runner 上另有 Chromium 安装）。只在 `main` 上触发，不进 PR 门。

**线上回读（2026-11-23，合入后首个 deploy）**——这一节才是 AC3 要的证据，前面都是候选 staging：

| URL | 状态 | 收到字节 |
| --- | --- | --- |
| `https://zhuguang-zfg.github.io/STM32/` | 200 | 28361 |
| `/STM32/book/` | 200 | 索引页（补于本轮，见下） |
| `/STM32/book/merged-book.html` | 200 | 32948417 |
| `/STM32/book/merged-book.pdf` | 200 | 34632029 |
| `/STM32/book/merged-book.epub` | 200 | 24005926 |
| `/STM32/mcu/` | 200 | 420（仍为 meta refresh 存根） |

首次上线时 `/STM32/book/` 本身还是 404——三份文件都在、首页也挂了链接，唯独这一层没有索引页，而它正是读者会收藏的地址。补法是把索引页做成仓库里的静态模板 `book/print/book-index.html`（不在 YAML 里维护 HTML），由 deploy 的 Stage 步骤拷进 `/book/`；冒烟新增「下载目录索引页」断言，同时校验它里面三条链接指向的正是上面验过的三份产物——否则产物改名后索引页会静默变成三条死链。本地实测 `smoke passed: 16/16`。

### AC3 的浏览器回归（候选 staging，非线上发布证明）

`npm run site:build` 生成 `.temp/pages-site`（根 = 合并书，`mcu/` = 131 条旧链存根），再跑 `npm run site:smoke`：脚本按真实挂载 `/STM32/` 起本地服务，用 Chromium 打开页面断言。

```text
OK   首页加载
OK   v1 ch09 深链
OK   旧链跳转落地 v1 ch09
OK   附录 A 深链
OK   ch40 深链
OK   anim 资源 200 — status=200
OK   quiz 答案展开交互 — open false→true
OK   stick-scene 渲染 canvas — canvas=1
OK   中文搜索有结果 — hits=16
OK   片段锚点定位 — #本章罗盘 found=true hash=本章罗盘
OK   同源资源无失败
smoke passed: 11/11
```

标注三点，避免把这条证据读大：

- 跑的是**本地组装产物**，不是线上部署；线上的独立观测只有上表那几条 HTTP 状态码。
- 「片段锚点定位」是本轮新加的断言（`scripts/site-smoke.mjs`）：取页面里**最后一个** `h2/h3` 的 `id`（必然在首屏之外），带 `#` 打开，要求页面真的滚动过（`scrollY > 0`）、目标进入视口、`hash` 解码后与 id 相同。

  为什么不用第一个标题：首屏内的标题不滚动也「在视口里」，断言会假通过。实测该页首个 `h2`（`#本章罗盘`）只需滚 248px，末尾 `h2`（`#离开检查`）需滚 16228px。

  为什么不对「顶端对齐 0」下断言：锚点落地后，上方懒加载内容仍会撑高页面，实测把目标从 `top=0` 推到 `top=110`。那是回流，不是锚点失效，因此判据取「滚动发生 + 目标在视口内」。

  负向验证两条都做了：去掉 hash（元素在但没滚动）→ `FAIL ... scrollY=0 top=16338`；换成不存在的 id → `FAIL ... found=false scrollY=0 top=null`。两种都 `smoke failed: 1/11`，说明断言不是摆设。
- 该冒烟已在 CI 中执行（`.github/workflows/site.yml:67`、`deploy.yml:64`），因此新增断言会随站点改动持续生效；`f3b3a55b` 的 Site CI（run `44472765437`）日志同样是 `smoke passed: 11/11`，锚点行为 `scrollY=16314 top=110`。但它只覆盖 staging，线上仍需 AC8 的回读。

旧路径负例仍在：`scripts/legacy-redirects.mjs` + `scripts/tests/legacy-redirects.test.mjs`（32 项测试全过，含负例）。

## AC4 artifact 目录与公开 URL 对应

B5 后的站点模型是「合并书直接当站点根，`mcu/` 下只放跳转存根」。这个约束由代码断言，不是靠约定：

- `scripts/site-assemble.mjs` 第 90–104 行在组装后扫描 `mcu/` 下所有 `.html`，非存根即报错。
- `scripts/check-site-pages.mjs` 第 54 行把 `mcu/` 从页面清单里排除。
- 线上 `/STM32/mcu/` 实测为存根（396 字节，`meta refresh` + `canonical` 指向 `/STM32/index.html`），与断言一致。

**补证（2026-11-23）**：此前判 `UNVERIFIED` 的原因是「候选 SHA 与 `main` 都没有对应 deploy 运行，artifact 无从核对」。合入后第一个 deploy 就是这个对应关系：

```text
run        45034581583   sha 9e798499   event push   conclusion success
artifact   github-pages-45034581583-1   99298767 bytes
tar 内      ./book/merged-book.pdf    34632029
           ./book/merged-book.html   32948417
           ./book/merged-book.epub   24005926
           共 734 个条目
```

artifact 里的三个字节数与线上回读逐字相同（`34632029` / `32948417` / `24005926`），说明「构建产物 → artifact → Pages」这条链没有中途改写。此前那次 `58ce14de`（run `44447390212`）不再需要引用。

## AC5 各门通过，缺门不得放行

| 门 | 现状 | 证据 |
| --- | --- | --- |
| 根书稿门（`book.yml`） | 在跑，绿 | `main@4882857e` run `44454649887` success；候选尖端 run `44465875365`（`649fba2b`）、`44464237479`（`818ef375`）success |
| 脚本测试 | 在跑，绿 | 同上运行的 `scripts` 作业；本地 `node --test scripts/tests/*.test.mjs` 32 通过 |
| 英文书门 | **不存在** | `.github/workflows/` 与 `Makefile` 无英文书目标；`tools/build_epub.py`、`tools/audit_pdf_layout.py` 仍引用 `stm32-book/dist/…-en.*`，但该目录未被跟踪（`git ls-files stm32-book` = 0）且无调用方 |
| MCU quality / browser / 书籍门 | **已随 B5 退役** | `mcu/.github/workflows/` 整树删除（692 条删除的一部分） |
| MCU ARM-host `firmware:check`、ESP32 normal/faults | **已随 B5 退役** | 同上 |

AC5 原文：「发布所依赖检查缺失时不得放行」。按原文字面，本候选**未通过**；本地门（`book.checks`、`build_html --check`、`slop_lint`、`check_assets`、32 项脚本测试）不能替代缺失的 CI 门，这是 AC5 自己写的规则。

**判定改为 `PASS`（按 AC5′，2026-11-22 由 owner 批准）。** 原文字面无法满足，因为其中一部分门是**随 B5 主动取消**的（MCU 独立书稿与固件 CI 不再有对象），把它读成「永远不得放行」等于要求重建已决定退役的东西。`prd.md` §3.1 因此给出 AC5′：

1. 现存门全绿（下表第一、二行 + 本轮新增的三道）；
2. 每一个退役门都要有**出处**（谁取消、何时、为什么）与**等价门**（替代它守什么）。

逐条对账：

| 退役门 | 出处 | 等价门（守什么） |
| --- | --- | --- |
| 英文书门 | B5 单书模型 `plans/2026-11-12-merged-book/README.md` | `book.yml` 的整书门：同一套 `book.checks` + `build_html --check` + EPUB/PDF 构建；没有英文对象可守，故等价物是「唯一那本书的门」 |
| MCU quality / browser / 书籍门 | `mcu/.github/workflows/` 整树删除（B5，692 条删除的一部分） | 根域 `merge-check.yml`（书稿门 + 脚本测试 + 链接/资源检查）与 `site.yml`（站点门 + 挂载冒烟）；`mcu/` 侧只剩固件与任务历史，由 AC6 的 `.trellis` 解析证明可继续执行 |
| MCU ARM-host `firmware:check`、ESP32 normal/faults | 同上 | 无等价门。**这是 AC5′ 的已知缺口，不掩饰**：`mcu/code/` 里的 47 个工程（arm-make 14 / esp-idf 10 / host-probe 22 / host-make 1）现在没有任何编译或运行门。没有补的理由是宿主环境缺 ARM/ESP 工具链、且这些是「保留的来源固件」而非本仓发布物；一旦有人要动 `mcu/code/`，必须先补这条门 |

AC5′ 第 2 条是本轮真正加了东西的地方——不是把缺门解释掉，而是把「本来就没人管」的那部分补成门（见下）。

命令对照：`implement.md` §6 仍写着 `python -m unittest discover stm32-book/tests`、`python stm32-book/build_html.py --check` 与 `mcu/` 下的 `mcu-book/*` 命令，这些路径在 B5 后都不存在（`git ls-files stm32-book` = 0）。现行等价物是 `python -m unittest discover book/tests` 与 `python -m book.build_html --check`，本节引用的即后者。

**本轮补的门（2026-11-22）**。AC5 的缺口里有一类不等于「被 B5 决定取消」，而是「本来就没人管」——本批把这一类里的引用元数据补成了门：

| 门 | 位置 | 覆盖什么 | 负向验证 |
| --- | --- | --- | --- |
| 引用元数据对账 | `book/tests/test_citation.py`（8 项） | title/version/repository/url、`identifiers` 指向的路径必须存在、许可正文、章数与附录数对 manifest、工程数对 `mcu/code/projects.json` | 回退 CITATION → 4 项失败 |
| 离线产物随站点可达 | `deploy.yml` 落盘下限 + `site-smoke.mjs --downloads`（3 项） | `/book/` 三件产物是 200 且字节过下限；首页渲染出三条 href | 移走 `/book/` → 3 项失败；截成 0 字节 → 1 项失败 |
| 构建期链接豁免不放过真死链 | `docs/.vitepress/config.mts` 的 `ignoreDeadLinks` 只匹配 `./book/` | 其余链接仍按 VitePress 死链检查失败（豁免面最小化） | 见下 |

不引入新依赖（只读 stdlib 与已提交的 `docs/manifest.json`），因此 `merge-check.yml` 的 `Run book checks` 与 `book.yml` 的 `Run book checks` 会照常执行它。触发侧：`merge-check.yml` 的 `paths` 本轮已含 `mcu/**`，所以改 `mcu/CITATION.cff` 会真的跑这 8 项断言；`book.yml` 的 `paths` 不含 `mcu/**`，这部分由 `merge-check` 补齐而不是靠人工记得补跑。

负向验证：把 `mcu/CITATION.cff` 回退成修复前版本，`test_citation` 4 项失败（章数、`identifiers`、`url`、version）；恢复后 8 项全过。

关于 `ignoreDeadLinks` 的豁免面：这条豁免是**必须**的，因为产物在构建期不存在；但它只能匹配 `./book/` 前缀，站内其余链接继续受死链检查约束。实测依据是豁免前那一次构建失败——`Found dead link ./book/merged-book in file index.md`，只有这一条，说明检查本身是好的、豁免范围也确实只盖住它。

**试过又撤回的一道门（记录在案）**：把 `mcu/README.md`、`mcu/CONTRIBUTING.md`、`mcu/AGENTS.md` 与合并计划文档加进 `book/checks.py` 的 `ENTRY_DOCS`。功能上成立——九份现测 0 死链，往里塞一条死链会真的报 `missing target`——但落地时要动 `book/checks.py` 的包内导入：仓内静态分析器无法从文件位置解析 `from book import …`（仓库没有安装元数据），于是级联要求同时改造 `build_html.py`、`build_print_edition.py`、`build_epub.py` 的脚本式导入。那三个文件是印刷/EPUB 发布链的一部分，CI 还在用 `python book/xxx.py` 的脚本形式调它们；为一个不参与任何门禁的静态检查去重构发布链，风险大于收益。本批因此撤回该门，保持 `book/` 的导入形态不变，把这件事当作独立重构（见剩余问题 #8）。

## AC6 规范与任务可继续执行

```bash
cd mcu && python .trellis/scripts/get_context.py        # exit 0
```

- 23 个活动任务，任务目录均有可解析 `task.json`；4 个无 `task.json` 的目录不在活动列表内（历史/草稿）。
- 8 层 spec：`book, docs-site, firmware-common, firmware-esp32, firmware-gd32, firmware-rtos, firmware-stm32, video`。
- `--mode packages` → `Single-repo project`。
- 状态分布 `planning` 9 / `in_progress` 14；唯一变化是 `11-07-historical-spec-closure` 的 `planning → in_progress`（`ec980bc7`），无归档、无改为通过。
- 历史绝对路径 `D:/Users/mcu` 命中 3 个文件，均为操作叙述，来源目录仍在。

## AC7 许可、出处、身份一致

| 项 | 实测 |
| --- | --- |
| 根 `LICENSE` | 存在且受跟踪，双许可：代码 MIT、`docs/` 与 `assets/` CC BY 4.0；§5 声明 `mcu/` 目录整体 Apache-2.0 |
| `mcu/LICENSE` | Apache-2.0 正文 |
| `mcu/CITATION.cff` | 存在且受跟踪：`title=通往单片机之路`、`license=["Apache-2.0", "CC-BY-4.0"]`、`version=0.1.0`（本轮已对齐 manifest 与 `LICENSE` 分区） |
| 提交作者 | `mcu/code` 历史作者保留（`zhuguang-ZFG`） |

### 本轮修掉的四处（2026-11-22，`23ca1fcb`；此前这份记录把它们列为待处理）

四处都是人工通读发现的，没有一个门会失败。修法一律是「指向真源」，不是改文档措辞绕过：

| # | 原断言 | 实测 | 处置 |
| --- | --- | --- | --- |
| 1 | `identifiers[0]` → `tree/main/mcu/mcu-book` | B5 已整树删除该目录，链接必然 404 | 改为 `tree/main/book`（整书构建器、清单与内容契约门所在目录，实测存在） |
| 2 | `url` → `/STM32/mcu/` | 200，但内容是 396 字节 `meta refresh` 存根 | 改为站点根 `https://zhuguang-zfg.github.io/STM32/`（合并书首页，实测 200） |
| 3 | `version: 1.0.0` | 与 `book/manifest.py:VERSION`、`docs/manifest.json`、`package.json` 的 `0.1.0` 冲突 | 改为 `0.1.0`；同时删 `date-released: 2026-10-23`（那是原 MCU 书 v1.0.0 的日期，`0.1.0` 没有对应发布日，留着就是编造） |
| 4 | 摘要「88 章」＋「随站点发布的离线整书（单文件 HTML 与 A4 PDF）」 | 合并书是 47 章 + 6 附录（`docs/manifest.json`）；`/STM32/book/`、`/STM32/book/merged-book.pdf` 实测 404 | 章数改为 47；删掉「随站点发布」一句——印刷产物确实由 `book.yml` 产出（`book-print` artifact），但它**没有**随站点发布，原句是把 CI artifact 说成了下载入口 |

### 新增门：`book/tests/test_citation.py`

8 项断言，把上面四类错误变回回归测试：title/version 对 manifest、`repository-code` 对规范仓、`url` 必须是站点根（不能带 `/mcu/`）、每条 `identifiers` 的 GitHub tree 路径必须在树里存在、许可标识对应 `mcu/LICENSE` 正文、摘要里的章数/附录数对 manifest、工程数对 `mcu/code/projects.json`。

不引 PyYAML：`book/requirements.txt` 只钉 `markdown`，内容门要能在没装 YAML 的环境跑，所以只读它需要的几个顶层标量，形态一变就直接抛断言失败。

负向验证：把 `mcu/CITATION.cff` 回退成修复前版本，4 项失败（章数、`identifiers`、`url`、version），说明断言确实咬得住。

### 许可适用范围已统一（2026-11-22，owner 选第 1 条）

原来的不一致：`mcu/CITATION.cff` 只写 `Apache-2.0`，而和合并书正文对应的根 `LICENSE` 是分区制——§2 把 `docs/`、`assets/` 判为 CC BY 4.0，§5 把 `mcu/` 目录判为 Apache-2.0。B5 之后正文在 `docs/`、框架与固件在 `mcu/`，两处都在，所以**合并书本身就是两个许可的并集**，单值声明必然漏掉一半。

处置（与 owner 确认）：`mcu/CITATION.cff` 改为 `license: ["Apache-2.0", "CC-BY-4.0"]`，`LICENSE` 不动。理由是 CFF 的 `license` 字段允许列表，且它描述的是「这部作品用了哪些许可」，与 `LICENSE` 的分区制不冲突；反过来改 `LICENSE` 等于调整法律口径，超出元数据对齐的范围。

门也跟着换了：`test_license_...` 由「CITATION 的标识符必须能在 `LICENSE` 正文里找到」改为 `test_license_matches_the_two_upstream_works`——断言 CITATION 的许可集合等于 `{Apache-2.0, CC-BY-4.0}` 的并集、`mcu/LICENSE` 正文确为 Apache 2.0、根 `LICENSE` 正文确实含 CC BY 4.0 条款。这样「单值退回」和「凭空多写一个许可」都会被咬住。

至此 AC7 判 `PASS`。

## AC8 发布关闭条件

**判定 `PARTIAL`（2026-11-23 更新）。** 关闭条件四项，三项已有实测：

| 要求 | 现状 |
| --- | --- |
| 发布运行 ID + 提交 SHA | `45034581583` / `9e798499`（`main` 上 `event=push`，success） |
| artifact 清单与哈希 | `github-pages-45034581583-1`，99298767 字节，734 个条目，含 `/book/` 三件产物（见 AC4 节） |
| 上线回读报告 | `/`、`/book/`、三件产物、`/mcu/` 全部实测（见 AC3 节） |
| 旧站兼容决定 | **未做**。`mcu/` 仍是 420 字节的 meta refresh 存根；旧仓入口与旧 Pages 是否长期保留、何时下线，仍待发布指令 |

所以 AC8 不是「做完了」，是「发布链侧已证、迁移侧未决」。

## 剩余问题清单

| # | 问题 | 影响 | 处理建议 |
| --- | --- | --- | --- |
| 1 | ~~AC5 缺英文书门与 MCU 四门~~ | 已结案 | AC5′ 生效：退役门有出处与等价门，`mcu/code/` 无编译门列为已知缺口并写明补救前提。见 AC5 节 |
| 2 | ~~AC3 下载入口全 404~~ | 已修 | `deploy.yml` 构建并落盘三件产物到 `/book/`，冒烟 `--downloads` 断言 200 + 字节下限（本地 15/15，两种负向均失败）。见 AC3 节 |
| 3 | AC4 当前 `main` 无 deploy 运行 | artifact 无从核对 | 下次 deploy 后补 artifact 清单与哈希 |
| 4 | ~~`CITATION.cff` `url` 指向存根~~ | 已修 | `23ca1fcb` 改为站点根；`book/tests/test_citation.py` 锁住不得再带 `/mcu/` |
| 5 | ~~`CITATION.cff` `1.0.0` vs manifest `0.1.0`~~ | 已修 | `23ca1fcb` 改为 `0.1.0` 并删去与版本不对应的 `date-released`；断言对 manifest |
| 6 | ~~浏览器回归未做~~ | 已完成 | `npm run site:smoke` 11/11（含新增片段锚点断言）；覆盖 staging，线上回读仍归 AC8 |
| 7 | ~~`LICENSE` 许可分区与 CITATION 口径不一~~ | 已修 | CITATION 改为 `["Apache-2.0", "CC-BY-4.0"]`，`LICENSE` 未动；`test_license_matches_the_two_upstream_works` 锁住并集口径。见 AC7 节末 |
| 9 | `mcu/code/` 47 个工程无编译/运行门 | 动了固件没人拦 | 补 ARM/ESP 工具链门后才能改 `mcu/code/`；现状是「保留的来源固件」，不属本仓发布物。见 AC5′ 表第三行 |
| 10 | deploy 多约 12 分钟（印刷链） | `main` 每次站点改动都跑全量印刷 | 只在 `main` 触发，不进 PR 门；若嫌慢可加 `book/**` 才构建的条件，但会把「产物过期」变成新的失败面，本批没做 |
| 8 | `mcu/` 入口文档与合并计划文档没有链接门 | `mcu/README.md` 曾攒下 60+ 条死链而 `checks passed` 照样印出来；同类腐烂仍只能靠人工核对 | 独立重构：把 `book/` 的包内导入统一成解析器可解的形式（`from book import …` → 包内相对导入，并把 `book.yml` 的 `python book/*.py` 调用改成 `python -m book.*`），再把九份入口/计划文档加进 `ENTRY_DOCS`。功能已验证可行，本批因风险大于收益撤回，理由见 AC5 节 |