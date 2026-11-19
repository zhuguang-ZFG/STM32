# P4 验收记录（2026-11-19）

候选分支 `feat/mcu-merge-p1`，尖端 `6f151cb5`，基线 `main@4882857e`（未动）。本记录逐条对照 [`prd.md`](../prd.md) §3 的 AC1–AC8 判，证据只写本次实测或可复算的值。

## 结论

| AC | 判定 | 一句话 |
| --- | --- | --- |
| AC1 | `PASS` | 来源祖先成立；1580 条差异全部落在已记录事件内；迁移前修改未被覆盖 |
| AC2 | `SUPERSEDED` | 原文要求「两书并存且入口区分」，B5 已改为单书模型；后继检查另列，不计作 AC2 通过 |
| AC3 | `NOT PASSED` | 下载入口 404；搜索/锚点/动画/导读的浏览器回归未做 |
| AC4 | `UNVERIFIED` | 存根约束由组装脚本断言，但候选 SHA 与 `main` 都没有对应 deploy 运行，artifact 无从核对 |
| AC5 | `NOT PASSED` | 英文书门与 MCU 的 quality/browser/book/ARM-host/ESP32 门都已不存在；AC5 原文规定缺门不得放行 |
| AC6 | `PASS` | 23 个活动任务可解析；历史任务未被归档或改判 |
| AC7 | `PARTIAL` | 许可与作者保留；`CITATION.cff` 有一处死指针、一处指向存根、一处版号不一致 |
| AC8 | `UNVERIFIED` | 发布门，尚未开始 |

**放行结论：按 AC5 与 AC3 的现状，本候选分支不满足合并条件。** PR #140 保持草稿。

## AC1 导入可追溯、内容不丢失

复算命令与结果：

```bash
git merge-base --is-ancestor cf161532c823446016a9deb60d31e5263397b7d7 4882857e   # exit 0
git diff --name-status cf161532c8^{tree} 4882857e:mcu | wc -l                      # 1580
git diff --name-status cf161532c8^{tree} 6f151cb5:mcu | wc -l                      # 1581
```

| 口径 | 路径数 | A | D | M |
| --- | --- | --- | --- | --- |
| `main@4882857e` 的 `mcu` | 1580 | 848 | 692 | 40 |
| 候选尖端 `6f151cb5` 的 `mcu` | 1581 | 848 | 692 | 41 |

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

**未通过**的原因有两条，都不是「看起来还行」能盖过的：

1. AC3 明确要求「下载入口可访问」，而合并书与 MCU 整书在线上都没有可下载文件。
2. 搜索、锚点、动画、导读四项只做了 URL 连通性探测，没有浏览器回归。

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
| 根 `LICENSE` | 存在且受跟踪，Apache-2.0 正文 |
| `mcu/LICENSE` | Apache-2.0 |
| `mcu/CITATION.cff` | 存在且受跟踪：`title=通往单片机之路`、`license=Apache-2.0`、`version=1.0.0` |
| 提交作者 | `mcu/code` 历史作者保留（`zhuguang-ZFG`） |

三处不一致，都是实测出来的：

1. **死指针（确定失效）**：`identifiers[0].value = https://github.com/zhuguang-ZFG/STM32/tree/main/mcu/mcu-book`，描述是「整书构建器、书稿清单与出版契约门所在目录」。该目录已被 B5 整树删除（`git cat-file -e 4882857e:mcu/mcu-book` 失败），链接必然 404。
2. **`url` 指向已改义的地址**：`https://zhuguang-zfg.github.io/STM32/mcu/` 实测 200，但内容是 `meta refresh` 跳转到 `/STM32/index.html` 的存根（396 字节），不再是《通往单片机之路》的落地页。不是 404，但也不再是它自称的东西。
3. **版号不一致**：`CITATION.cff` 写 `1.0.0`，`docs/manifest.json` 写 `0.1.0`。

这三条要么改元数据，要么在合并任务里明确保留理由，不能默认过去。

## AC8 发布关闭条件

未开始。需要：旧站/根站部署状态快照、候选 artifact SHA、发布运行 ID、上线回读报告。本条在 PR 合入与 Pages 切换之前无法验证。

## 剩余问题清单

| # | 问题 | 影响 | 处理建议 |
| --- | --- | --- | --- |
| 1 | AC5 缺英文书门与 MCU 四门 | 按 AC5 不得放行 | 明确这些门是「随 B5 取消」并写进验收口径，或重建等价门 |
| 2 | AC3 下载入口全 404 | 读者拿不到离线书 | 决定是否提供在线下载，或明确 AC3 修订 |
| 3 | AC4 当前 `main` 无 deploy 运行 | artifact 无从核对 | 下次 deploy 后补 artifact 清单与哈希 |
| 4 | `CITATION.cff` `url` 指向存根 | 引用信息误导 | 改为指向合并书或明示为历史站点 |
| 5 | `CITATION.cff` `1.0.0` vs manifest `0.1.0` | 版号不可信 | 统一口径 |
| 6 | 浏览器回归未做（搜索/锚点/动画/导读） | AC3 缺口 | 用 Playwright 或人工走查补证 |