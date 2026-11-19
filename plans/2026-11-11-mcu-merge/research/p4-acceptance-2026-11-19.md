# P4 验收记录（2026-11-19）

候选分支 `feat/mcu-merge-p1`，尖端 `6f151cb5`，基线 `main@4882857e`（未动）。本记录逐条对照 [`prd.md`](../prd.md) §3 的 AC1–AC8 判，证据只写本次实测或可复算的值。

## 结论

| AC | 判定 | 一句话 |
| --- | --- | --- |
| AC1 | 通过 | 来源祖先成立；1580 条差异全部落在已记录事件内；迁移前修改未被覆盖 |
| AC2 | 通过（口径按单书模型修订） | 章号未改；47 章 + 6 附录 = 53 页，构建与清单一致 |
| AC3 | **未通过** | 下载入口 404；搜索/锚点/动画/导读的浏览器回归未做 |
| AC4 | 部分 | 「`mcu/` 下只有存根」由 CI 断言且线上实测吻合；但当前 `main` SHA 没有 deploy 运行，artifact 清单无从核对 |
| AC5 | **未通过** | 英文书门与 MCU 的 quality/browser/book/ARM-host/ESP32 门都已不存在；AC5 原文规定缺门不得放行 |
| AC6 | 通过 | 23 个活动任务可解析；历史任务未被归档或改判 |
| AC7 | 部分 | 许可与作者保留；`CITATION.cff` 的 `url` 指向存根页，版号与 manifest 不一致 |
| AC8 | 未验证 | 发布门，尚未开始 |

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

尖端比 `main` 多的一条是 `mcu/CONTRIBUTING.md`：来源仓该文件在根目录，本轮加了「写作标准降为历史参考」横幅与死链降级，因此与来源不再字节相同。这是有意改动，不是导入遗漏。

1580 条差异的成因（见[执行快照](execution-snapshot-2026-11-19.md) §2）：692 条删除全由 B5（`44c0fdb0`）整树退役解释；848 条新增与 40 条修改来自导入后演进（视频发布脚本、`code/`、`.trellis` 任务、逐章修订）。

迁移前修改保留：`research/wip-backup-2026-11-11/` 的字节备份与 2026-11-19 重算的 SHA-256 对照，12 条字节不变，5 条由 `27757966`、`ec980bc7` 解释（见[执行快照](execution-snapshot-2026-11-19.md) §3）。

## AC2 两书正文与工程没有因目录合并而覆盖或改号

AC 原文假设「两书分域、入口区分两书」。B5 把这个前提换成了单书模型（MCU 正文并入根书稿），因此本节判的是该 AC 仍可观察的部分：**章号没有被合并改掉、构建与清单自洽**。

```bash
wc -l < book/data/toc.tsv                    # 53
python -m book.manifest --check              # exit 0
python -m book.mapping --check               # exit 0
python -m book.build_html --check            # built 53 pages, 0 planned chapters missing
```

`docs/manifest.json`：`title=通往单片机之路`、`version=0.1.0`、`language=zh`、9 个卷、47 章、6 附录，与 `toc.tsv` 的 53 行一一对应。`mapping.json` 只写在 `plans/2026-11-12-merged-book/`，与书稿目录分离。

入口区分：`README.md`、`STRUCTURE.md` 写明 `mcu/` 保留固件与任务历史、不再有独立书稿站点；`mcu/README.md` 本轮已按此改写。

未覆盖：AC 原文里「两书入口并存」已不存在，这是设计变更（B5），不是本次缺陷。

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

缺口：`gh api .../actions/runs?head_sha=4882857e` 返回空，即当前 `main` 没有 deploy 运行，最近一次 deploy 成功是 `58ce14de`（run `44447390212`）。**没有可核对的、对应当前 `main` 的 artifact 清单**，所以本条只能是「部分」。

## AC5 各门通过，缺门不得放行

| 门 | 现状 | 证据 |
| --- | --- | --- |
| 根书稿门（`book.yml`） | 在跑，绿 | `main@4882857e` run `44454649887` success；候选尖端 run `44465875365`（`649fba2b`）、`44464237479`（`818ef375`）success |
| 脚本测试 | 在跑，绿 | 同上运行的 `scripts` 作业；本地 `node --test scripts/tests/*.test.mjs` 32 通过 |
| 英文书门 | **不存在** | `.github/workflows/` 与 `Makefile` 无英文书目标；`tools/build_epub.py`、`tools/audit_pdf_layout.py` 仍引用 `stm32-book/dist/…-en.*`，但该目录未被跟踪（`git ls-files stm32-book` = 0）且无调用方 |
| MCU quality / browser / 书籍门 | **已随 B5 退役** | `mcu/.github/workflows/` 整树删除（692 条删除的一部分） |
| MCU ARM-host `firmware:check`、ESP32 normal/faults | **已随 B5 退役** | 同上 |

AC5 原文：「发布所依赖检查缺失时不得放行」。按此，本候选**未通过**。本地门（`book.checks`、`build_html --check`、`slop_lint`、`check_assets`、32 项脚本测试）不能替代缺失的 CI 门，这是 AC5 自己写的规则。

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

两处不一致，都是实测出来的：

1. **`CITATION.cff` 的 `url` 指向 `https://zhuguang-zfg.github.io/STM32/mcu/`**，该地址现在是跳转到合并书首页的存根（实测 200 + `meta refresh`），不是《通往单片机之路》。
2. **版号不一致**：`CITATION.cff` 写 `1.0.0`，`docs/manifest.json` 写 `0.1.0`。

这两条要么改元数据，要么在合并任务里明确保留理由，不能默认过去。

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