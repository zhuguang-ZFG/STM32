# P4 验收记录（2026-11-19，2026-11-22 修订）

候选分支 `feat/mcu-merge-p1`，PR #140（草稿）；本记录成文（2026-11-19）时尖端 `f3b3a55b`，此前各轮为 `1c0ee761`、`6b8d9b48`、`c85bbb1e`、`6f151cb5`、`649fba2b`、`818ef375`、`df187f3d`；2026-11-22 追加 AC7 修复与两道新门（`23ca1fcb`，本文件同步更新）。基线 `main@4882857e`（未动）。本记录逐条对照 [`prd.md`](../prd.md) §3 的 AC1–AC8 判，证据只写本次实测或可复算的值。

## 结论

| AC | 判定 | 一句话 |
| --- | --- | --- |
| AC1 | `PASS` | 来源祖先成立；1580 条差异全部落在已记录事件内；迁移前修改未被覆盖 |
| AC2 | `SUPERSEDED` | 原文要求「两书并存且入口区分」，B5 已改为单书模型；后继检查另列，不计作 AC2 通过 |
| AC3 | `NOT PASSED` | 下载入口四条 404；站内导航（深链、旧链、锚点、动画、搜索、交互）已由 staging 冒烟覆盖 |
| AC4 | `UNVERIFIED` | 存根约束由组装脚本断言，但候选 SHA 与 `main` 都没有对应 deploy 运行，artifact 无从核对 |
| AC5 | `NOT PASSED` | 英文书门与 MCU 的 quality/browser/book/ARM-host/ESP32 门都已不存在；AC5 原文规定缺门不得放行 |
| AC6 | `PASS` | 23 个活动任务可解析；历史任务未被归档或改判 |
| AC7 | `PARTIAL` | 许可与作者保留；`CITATION.cff` 四处元数据已按真源修正并加了门，许可适用范围仍待 owner 决定 |
| AC8 | `UNVERIFIED` | 发布门，尚未开始 |

**放行结论：按 AC5 与 AC3 的现状，本候选分支不满足合并条件。** PR #140 保持草稿。

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

**判定 `SUPERSEDED`。** 原文要求「两书分域、入口能区分两书」；B5（`44c0fdb0`）把 MCU 正文并入根书稿、退役 `mcu/docs` 与 `mcu/mcu-book`，这个前提已被设计变更取消。把它判成「通过」会把替换后的目标冒充成原目标，所以不计通过。

**后继检查（单书模型下的等价项，另列，不顶替 AC2）**：

```bash
wc -l < book/data/toc.tsv                    # 53
python -m book.manifest --check              # exit 0
python -m book.mapping --check               # exit 0
python -m book.build_html --check            # built 53 pages, 0 planned chapters missing
```

`docs/manifest.json`：`title=通往单片机之路`、`version=0.1.0`、`language=zh`、9 个卷、47 章、6 附录，与 `toc.tsv` 的 53 行一一对应。`mapping.json` 只写在 `plans/2026-11-12-merged-book/`，与书稿目录分离。

入口区分：`README.md`、`STRUCTURE.md` 写明 `mcu/` 保留固件与任务历史、不再有独立书稿站点；`mcu/README.md` 本轮已按此改写。

复查要点：AC2 的原始不变量（两本书各自可独立维护、入口区分）在单书模型里没有对应物。若合并任务要关掉 AC2，需要在 PRD 层面写明「由 AC2′ 取代」，而不是在验收记录里就地改判。

## AC3 新 base 下各入口可访问

实测（2026-11-19，公开站点）：

| 路径 | 状态 | 说明 |
| --- | --- | --- |
| `/STM32/` | 200 | 合并书首页 |
| `/STM32/mcu/` | 200 | 跳转存根，`meta refresh` 指向 `/STM32/index.html`，非 MCU 整书 |
| `/STM32/mcu/book/` | 404 | 旧书入口已清场 |
| `/STM32/mcu/downloads/mcu-deep-book.pdf` | 404 | 旧下载入口已清场 |
| `/STM32/book/` | 404 | 合并书无在线下载目录 |
| `/STM32/book/merged-book.pdf` | 404 | 同上 |

**未通过**的原因是下载入口缺失，与浏览器回归无关——后者本轮已补：

1. AC3 明确要求「下载入口可访问」，而合并书与 MCU 整书在线上都没有可下载文件（上表四条 404）。
2. 浏览器回归已完成，见下节；它的结论是「站内导航正常」，不能替代第 1 条。

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

缺口（因此判 `UNVERIFIED`，不是「部分通过」）：`gh api .../actions/runs?head_sha=4882857e` 返回空，即当前 `main` 没有 deploy 运行；最近一次 deploy 成功是 `58ce14de`（run `44447390212`），既不是候选 SHA 也不是 `main` 当前 SHA。**没有对应当前代码的 artifact 清单与哈希**。组装脚本的存根断言和线上首页 200 都不能替代「候选 artifact 内的目录与挂载深链实测」。

## AC5 各门通过，缺门不得放行

| 门 | 现状 | 证据 |
| --- | --- | --- |
| 根书稿门（`book.yml`） | 在跑，绿 | `main@4882857e` run `44454649887` success；候选尖端 run `44465875365`（`649fba2b`）、`44464237479`（`818ef375`）success |
| 脚本测试 | 在跑，绿 | 同上运行的 `scripts` 作业；本地 `node --test scripts/tests/*.test.mjs` 32 通过 |
| 英文书门 | **不存在** | `.github/workflows/` 与 `Makefile` 无英文书目标；`tools/build_epub.py`、`tools/audit_pdf_layout.py` 仍引用 `stm32-book/dist/…-en.*`，但该目录未被跟踪（`git ls-files stm32-book` = 0）且无调用方 |
| MCU quality / browser / 书籍门 | **已随 B5 退役** | `mcu/.github/workflows/` 整树删除（692 条删除的一部分） |
| MCU ARM-host `firmware:check`、ESP32 normal/faults | **已随 B5 退役** | 同上 |

AC5 原文：「发布所依赖检查缺失时不得放行」。按此，本候选**未通过**。本地门（`book.checks`、`build_html --check`、`slop_lint`、`check_assets`、32 项脚本测试）不能替代缺失的 CI 门，这是 AC5 自己写的规则。

命令对照：`implement.md` §6 仍写着 `python -m unittest discover stm32-book/tests`、`python stm32-book/build_html.py --check` 与 `mcu/` 下的 `mcu-book/*` 命令，这些路径在 B5 后都不存在（`git ls-files stm32-book` = 0）。现行等价物是 `python -m unittest discover book/tests` 与 `python -m book.build_html --check`，本节引用的即后者。

**本轮补的两道门（2026-11-22，`23ca1fcb`）**。AC5 的缺口里有一类不等于「被 B5 决定取消」，而是「本来就没人管」——本批把这类补成了门：

| 门 | 位置 | 覆盖什么 |
| --- | --- | --- |
| `mcu/` 入口文档与合并计划文档的链接扫描 | `book/checks.py` 的 `ENTRY_DOCS` 新增 `mcu/README.md`、`mcu/CONTRIBUTING.md`、`mcu/AGENTS.md`，以及 `plans/2026-11-11-mcu-merge/{prd,design,implement}.md`、`research/execution-snapshot-2026-11-19.md`、`research/p4-acceptance-2026-11-19.md`、`plans/2026-11-12-merged-book/README.md` | 本批重写 `mcu/README.md` 的原因就是它有 60+ 条链接指向已删除的树，而当时没有任何门会失败。计划文档同理：`implement.md` 指向 `research/*`，验收记录又指向 `prd.md` 与快照，断一条就是证据链断一条。九份现测 0 死链，加进去之后同类腐烂会被 `book.checks --check` 报出来 |
| 引用元数据对账 | `book/tests/test_citation.py`（8 项） | title/version/repository/url、`identifiers` 指向的路径必须存在、许可正文、章数与附录数对 manifest、工程数对 `mcu/code/projects.json` |

两者都不引入新依赖（只读 `markdown` 那套），因此 `merge-check.yml` 的 `Run book checks` 与 `book.yml` 的 `Run book checks` 会照常执行它们。触发侧要说清：`merge-check.yml` 的 `paths` 本轮已含 `mcu/**`，所以改 `mcu/CITATION.cff` 或 `mcu/README.md` 会真的跑这两道断言；`book.yml` 的 `paths` 不含 `mcu/**`，这部分由 `merge-check` 补齐而不是靠人工记得补跑。

负向验证（两道门都验过会失败，不是摆设）：把 `mcu/CITATION.cff` 回退成修复前版本，`test_citation` 4 项失败（章数、`identifiers`、`url`、version）；往 `mcu/README.md` 塞一条指向不存在文件的链接，`ShippedEntryDocsTest` 报 `AssertionError: ['mcu/README.md:103: missing target: ../docs/retired-dir.md']`；往 `implement.md` 塞一条 `../research/not-there.md`，同一测试报 `plans/2026-11-11-mcu-merge/implement.md:192: missing target`。两处恢复后均回到 OK。

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
| `mcu/CITATION.cff` | 存在且受跟踪：`title=通往单片机之路`、`license=Apache-2.0`、`version=0.1.0`（本轮已对齐 manifest） |
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

### 仍不一致：许可适用范围（需 owner 决定，因此 AC7 仍判 `PARTIAL`）

B5 把 MCU 正文搬进了根 `docs/`，而根 `LICENSE` 的许可分区没跟着搬：

- §2 写「`docs/`、`assets/` … CC BY 4.0」——合并书正文现在就在 `docs/`；
- §5 写「`mcu/` 目录（《通往单片机之路》）整体适用 Apache-2.0」——但该书正文已不在 `mcu/`。

而 `mcu/CITATION.cff` 只声明 `Apache-2.0`。合并书的正文来自两本上游作品，两者许可都允许再分发，所以这不是侵权风险，是**声明与实际不一致**：读者按 CITATION 引用时，被告知的是与 `LICENSE` 不同的口径。

两条路都行，但得选一条并写进 `LICENSE` 或 CITATION，不能两边并存：

1. CITATION 改为 `license: ["Apache-2.0", "CC-BY-4.0"]`（CFF 允许列表），`LICENSE` 不动；
2. 在 `LICENSE` §2/§5 里给合并书正文单列一条（例如「`docs/` 中源自《通往单片机之路》的章节适用 Apache-2.0」），CITATION 保持单值。

本轮没有替 owner 做这个选择：改许可声明是法律口径，不是元数据对齐。

## AC8 发布关闭条件

未开始。需要：旧站/根站部署状态快照、候选 artifact SHA、发布运行 ID、上线回读报告。本条在 PR 合入与 Pages 切换之前无法验证。

## 剩余问题清单

| # | 问题 | 影响 | 处理建议 |
| --- | --- | --- | --- |
| 1 | AC5 缺英文书门与 MCU 四门 | 按 AC5 不得放行 | 明确这些门是「随 B5 取消」并写进验收口径，或重建等价门。**B5 取消的部分已由已记录的 B5 决定解释（`plans/2026-11-12-merged-book/README.md`）；本批另补了两道真正缺的门（`mcu/` 入口链接、引用元数据），见 AC5 节** |
| 2 | AC3 下载入口全 404 | 读者拿不到离线书 | 决定是否提供在线下载（`book.yml` 已产出 `book-print` artifact，缺的是把它放进 staging 并写进冒烟），或明确 AC3 修订。**本批只删掉 CITATION 里那句不成立的「随站点发布」，没改交付链** |
| 3 | AC4 当前 `main` 无 deploy 运行 | artifact 无从核对 | 下次 deploy 后补 artifact 清单与哈希 |
| 4 | ~~`CITATION.cff` `url` 指向存根~~ | 已修 | `23ca1fcb` 改为站点根；`book/tests/test_citation.py` 锁住不得再带 `/mcu/` |
| 5 | ~~`CITATION.cff` `1.0.0` vs manifest `0.1.0`~~ | 已修 | `23ca1fcb` 改为 `0.1.0` 并删去与版本不对应的 `date-released`；断言对 manifest |
| 6 | ~~浏览器回归未做~~ | 已完成 | `npm run site:smoke` 11/11（含新增片段锚点断言）；覆盖 staging，线上回读仍归 AC8 |
| 7 | `LICENSE` 许可分区与 CITATION 口径不一 | AC7 仍 `PARTIAL`；读者按 CITATION 引用会被告知与 `LICENSE` 不同的口径 | owner 二选一：CITATION 改为 `["Apache-2.0", "CC-BY-4.0"]`，或在 `LICENSE` §2/§5 给合并书正文单列一条。见 AC7 节末 |