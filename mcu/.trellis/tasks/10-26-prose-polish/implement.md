# 实施清单：逐章精修

## 0. 前置（已完成）

- [x] 基线统计：破折号 2002 / 一句话 120 / 记住 135 / 下一站 63（90 文件）
- [x] `mcu-book/tools/prose_guard.py`：不可动清单断言 + 口癖计数（ruff 干净）
- [x] 试点章 `gd32/08-mtime-delay` 精修稿：`research/pilot-08-mtime-delay.md`，破折号 52→3，清单全过
- [ ] **评审门**：你逐段评审试点章 + 确认 design.md §3 的三个决定 → `task.py start 10-26-prose-polish`

## 1. 分批精修（批次按分部；实测余量 2026-10-26 15:20）

| 批 | 范围 | 章数 | 状态 |
|---|---|---|---|
| B1 | 第一部分 语法地基（C0-C6 + B 系列） | ~10 | ✅ 落盘 |
| B2 | 第二部分 STM32 裸机 S0-S9 | ~10 | ✅ 落盘 |
| B3 | 第三部分 STM32 S10-S17 | ~8 | ✅ 落盘 |
| B4 | 第四部分 GD32/RISC-V V0-V9 | ~10 | ✅ 并行线完成，HEAD 基线审计 10/10 绿 |
| B6 | 第六部分 FreeRTOS F0-F8 | 9 | 🔄 进行中 |
| B6b | RT-Thread R0-R7 + 对照 2 章 | 10 | 待派 |
| B8 | 实验篇 lab E01-E08 + projects 2 章 | 9 | 待派（3-5 处/章，轻量） |
| M | manifest.json 印书 prose（罗盘 question 30/boundary 11/deliverable 1 + 分部 goal 4/intro 9） | 55 处 | 🔄 进行中（PolManifest） |

站点-only 文档（guide/、reference/faq、bibliography 等，book 章节之外）排在全书章节之后；`reference/changelog.md`（——94）与 `releases/*` 是历史记录，**不改**（变更日志的破折号是行文惯例不是口癖）。

## 2. 每批验收命令

```bash
python mcu-book/tools/prose_guard.py --batch .temp/polish/batch-N.tsv
ruff check mcu-book/tools/
```

**落盘验证必须对 `git HEAD` 做**（B3 事故教训：代理曾绕过 .temp 直接写 docs/，docs↔.temp 互验变空转；且有代理改围栏注释+数字事实被对 HEAD 复验抓获）。每批落盘前后各跑一次 HEAD 对照。字节对照基线一律 `write_bytes`（B5 事故：write_text 在 Windows text-mode 加 CR，制造过 8 章假差异）。HEAD blob 是 LF（.gitattributes eol=lf）。

**代理提示词模板追加三条**（B3/B4/B5/B8 连续踩坑）：
- guard 输出重定向到文件再读：`python mcu-book/tools/prose_guard.py … > .temp/guard-<章>.txt 2>&1`（工具输出会被压成图，代理读不到）
- 报告开头**显式列出领取的文件清单**；分派时给出基于 `ls` 的实名单，不许按序号猜章数（B5 因猜名漏了 01-rcu-clock、撞了 06）
- **docs/** 全目录对代理只读**（B8 实锤有代理直写 docs/07-port-f407.md）；落盘防线：主代理落盘时"受保护行（表格/标题/围栏）以 git HEAD 字节为准"逐行还原，散文改动取 .temp 稿

## 3. 收口

- [ ] 全部批次落盘后：全书口癖总表 vs 阈值（design.md §3.3）
- [ ] **字体子集重生成**：`python mcu-book/subset_fonts.py --font …（9 条配方见 print/fonts/provenance.json）--out-dir mcu-book/print/fonts`——正文新增任何一个生僻字，过期子集都会让印前 PDF 静默回退系统宋体（check_pdf「字体」门会红）。精修每批都可能引入新字，这是收口的固定步骤。
- [ ] 重建 `book-final5`：`check_pdf.py` 11 门全过 + 前后页数记录
- [ ] `pytest mcu-book/tests/ -q` 全绿；prose_guard 接入本地门禁（tests/ 加单测：构造违规样本必点名）
- [ ] 站点版重建（同源 docs/**，构建逻辑不动）
- [ ] 归档：批次报告存 `research/batch-reports/`

## 回滚点

- 每批落盘前 `git stash`/分支快照；单批可整批回退。
- 试点章若评审否决：只丢 research/ 下的稿子，docs/** 未动。
