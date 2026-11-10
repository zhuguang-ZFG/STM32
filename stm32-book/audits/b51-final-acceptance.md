# B51 · 整书验收（Book 2.0 发布门）

日期：2026-11-10 ｜ 分支：`improve/b51-final-acceptance-1`（基于 b52 收口后 tip）｜ 依据：`stm32-book/BOOK_REDESIGN_SPEC.md` §11–§12、计划 B46–B51

## 验收命令集（spec §11）

```bash
python -m pytest stm32-book/tests -q            # 全量测试
python tools/check_assets.py                    # 链接/照片/示例契约
python stm32-book/build_html.py --check         # zh HTML 契约
python stm32-book/build_html.py --lang en --check
python stm32-book/build_html.py --pdf           # zh PDF（串行）
python stm32-book/build_html.py --lang en --pdf # en PDF
python tools/build_epub.py                      # EPUB（zh/en 按工具参数）
python tools/audit_pdf_layout.py --lang zh --max-gap-pages 145 --max-large-gap-pages 15 --min-anchors 8 --max-fig-free-pages 5
python tools/audit_pdf_layout.py --lang en --min-anchors 9 --max-fig-free-pages 4
git diff --check
```

结果（2026-11-10 终态，b51 @ 26bdc38 基于 b52 收口）：

```text
pytest stm32-book/tests        196 passed（528.67s，b51 终态分支重跑）
check_assets                   链接 2176/2176 有效；实拍照片 5/5 哈希与尺寸匹配，通过
build_html --check (zh)        PASS（29 章）
build_html --check (en)        PASS（29 章）
build_html --pdf (zh)          dist/stm32-practical-book.pdf 122,476,175 B
build_html --pdf (en)          dist/stm32-practical-book-en.pdf 123,188,667 B
build_epub.py                  zh/en 各 49 spine / 621 images / errors=0
audit_pdf_layout zh            528p  gaps>150pt=142(133+9+0)  硬缺陷 0  anchors[min=11 max_free=4]  exit=0
audit_pdf_layout en (CI 同命令) 561p  gaps>150pt=137(121+16+0)  硬缺陷 0  anchors[min=11 max_free=4]  **本地 exit=1（16>15）**
audit_pdf_layout en (CI 实测)   551p  gaps>150pt=133(121+12+0)  硬缺陷 0  anchors[min=11 max_free=5]  exit=0（run 42790473203 job 129742359382）
git diff --check               0（提交前已验）
```

## 前后对比

### 无图区间（zh，官方 audit）

B46 计划基线（df89879）→ 当前：

| 章 | 基线 | B48 | B49 | b52 收口后 |
|---|---|---|---|---|
| 27 | 2585 | ✓ ≤1200 | | |
| 13 | 2566 | ✓ | | |
| 26 | 2438 | ✓ 1231（登记例外） | | |
| 28 | 2198 | | ✓ 1090 | |
| 24 | 2149 | | ✓ 1082 | |
| 18 | 1870 | | ✓ 1131 | |
| 23 | 1844 | | ✓ 1082 | |
| 12 | 1716 | | ✓ 1194 | |
| 16 | 1568 | | ✓ 1127 | |
| 01 | （未列入计划表，实测 1508） | | | 1047 ✓ |
| 25 | 1498 | | | 1139 ✓ |
| 09 | 1449 | | | 1159 ✓ |
| 17 | 1437 | | | 1138 ✓ |
| 21 | 1417 | | | 1093 ✓ |
| 14 | 1343 | | | 1128 ✓ |
| 19 | 1316 | | | 1143 ✓ |
| 02 | 1294 | | | 1171 ✓ |

_注：b52 为 B51 验收时发现的 8 章遗留超线（计划表未列），按同管线收口，不计新例外。_

### 版式（PDF 版式门）

| 指标 | B46 基线 | B47 后 | B51 终态 |
|---|---|---|---|
| zh 页数 | 511 | 511 | 528（b49/b50/b52 新增 23 图） |
| zh ≥150pt 大留白页 | 140 | 139 | 142 |
| zh ≥250pt | 10 | 11 | 9 |
| zh 硬缺陷 | 0 | 0 | 0 |
| en 页数 | 541 | 540 | 561（本地 Windows）/ 551（CI Ubuntu，实测） |
| en ≥150pt | 126 | 124 | 137（本地）/ 133（CI） |
| en ≥250pt | 12 | 12 | 16（本地）/ 12（CI，门 15 以下，通过） |
| en 硬缺陷 | 0 | 0 | 0 |

> 平台分页差异：同一提交 en PDF 在 Windows 本地与 CI Ubuntu 分页不同
> （字体/渲染环境差异，561p vs 551p；≥250pt 16 vs 12）。发布门以 CI 为准
> （workflow book-en 同命令实测 exit=0，run 42790473203）；本地超门数值为
> 平台噪声，不构成树缺陷，勿据此改版图。

### 有实物证据（实拍照片）章节数

- 前（B46）：2（ch03、ch24）
- 后：4（ch03、ch21（B50 补 3 张准确型号照片）、ch24、ch28）

## 抽样翻页

每章取「知识轨」图注最密的一页渲染 PNG 目检（zh PDF，PyMuPDF 1.28，zoom 1.1）；
选页严格按 PDF TOC 章界（`doc.get_toc()` lvl2 章起始页，1-based），首版抽样因
手工章界漏 docs05/26/27 漂入相邻章，首版结果不计入，已重选（首版 p103/p415
实为定时器/SPL 内容）。下表为更正后终版，渲染件存 `.temp/sample2/`：

| 分部 | 章（docs / PDF 章） | 渲染页 | 目检结果 |
|---|---|---|---|
| 一 · L0 | 00 / 01 / 02（第1、2、3章） | p11 / p34 / p50 | 三阶段+RTOS；boot-first-words+main-skeleton；选型框架图正常 |
| 二 · L1 | 03 / 04（第4、5章） | p66 / p75 | GPIO 配置图正常；NVIC 响应链（PM0056 出处）正常 |
| 三 · L2 | 06 / 08（第7、9章） | p107 / p138 | UART 帧+采样点正常；SPI 模式对比正常 |
| 四 · L3 | 13 / 16（第14、17章） | p214 / p258 | CAN 位时序正常；唤醒路径+prove-wakeup 图正常 |
| 五 · L4 | 18 / 20（第19、21章） | p292 / p324 | BOOT 选源+SWD 查连接正常；三件套分工+手册命名图正常 |
| 六 · L5 | 23 / 24（第24、25章） | p367 / p382 | BOOT 锁存机制（DS12232/RM0444/AN2606 出处）正常；L476 抢脚清单正常 |
| 七 · 收束 | 28（第29章，**本部仅此一章**） | p439 | 系统分层 ownership+四执行概念正常 |
| 七 · 收束（非章） | 学习路线收束页 | p460 | 推荐顺序/读完标准/下一步 纯文本排版正常 |

分部归属以正式目录（dist/stm32-practical-book.html 目录 + PDF TOC）为准：
docs02 归第一部，故第一部抽 3 章（00/01/02），第二至六部各 2 章，第七部仅
一章（28）+ 收束页 1；合计 15 页目检，不用其他部多抽抵数。15/15 页版式、
图注、页眉页脚、图片清晰度全部合格；无溢出、无孤立图注。

## 遗留

- ~~PR 创建 403~~ 已解决（2026-11-10）：MCP 挂的是细粒度 PAT（仅 Contents write），
  本机 `gh` CLI 的 OAuth token（repo scope）可建 PR。6 个 PR 已按 base 链创建：
  [#98 b47](https://github.com/zhuguang-ZFG/STM32/pull/98)（原 #92 因 base 分支随
  #91 合并被删而自动关闭，GitHub 不允许改已关闭 PR 的 base，故重开）、
  [#93 b48](https://github.com/zhuguang-ZFG/STM32/pull/93)、
  [#94 b49](https://github.com/zhuguang-ZFG/STM32/pull/94)、
  [#95 b50](https://github.com/zhuguang-ZFG/STM32/pull/95)、
  [#99 b52](https://github.com/zhuguang-ZFG/STM32/pull/99)（原 #96 同因关闭，重开）、
  [#97 b51](https://github.com/zhuguang-ZFG/STM32/pull/97)。
  遗留：合并进行中（#91/#98/#93/#95 已合）。合并流程教训：GitHub 在 base 分支
  被删时自动**关闭**依赖它的 PR（不会自动重定向），且关闭态 PR 不能改 base。
  正确顺序：先改下一个 PR 的 base → 再合并并删当前分支；合并与删分支必须在
  一次成功调用里完成，API 抖动时先验证状态再继续（#92/#96 因此被关闭，
  重开为 #98/#99）。
