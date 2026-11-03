# ch03 合流硬门审计（§10.2）

对照：[`BOOK_CLASSIC_CONVERGE_SPECS.md`](../BOOK_CLASSIC_CONVERGE_SPECS.md) §10.2。  
分支：`feat/book-video-classic`。审计时点：本机改章前快照 + 本轮改动说明。

## 已完成前置

- [x] Overlay 已合入 classic（`96edfbd`）
- [x] Port A strip（`d7419d6`）
- [x] Port B Sepia/plain-voice 规则（`ae8030c`），无 handraw docs 整树合并
- [x] CONTENT_GUIDE §8 功能块合同（`bb6137e`）

## 改章前缺陷清单

| 项 | 改前状态 | 本轮处理 |
| --- | --- | --- |
| 教学合同七项+先备 | manifest 仅有 question/deliverable/boundary/sources | 中英 `chapter_guides` 补齐 prerequisites/minimum_victory/mechanism/failure_branch/memory_anchor/exit_check；保留三件套供 compass 渲染 |
| 最小胜利 vs 手册密度 | 视频后直接「原理与适用范围」+ 长表；最小胜利埋在实验/代码 | 视频后插入「最小胜利 / Minimum victory」，手册表仍在核心原理之后 |
| Handraw 引用 | `ch03-handdraw.svg` 只在短片/分镜，**章正文未引用** | 最小胜利节嵌入 Handraw 图 + SHA-256 |
| 真证轨 | 无 BluePill PC13 实拍/表计截图；Nucleo 照片与本章无关 | 硬件节显式「真证轨缺口（待补）」+ 知识轨哈希 |
| 失败分支证据 | 「常见坑与出处」五行已含现象/原因/处理/出处 | 保留；最小胜利失败时指向该表三行；未删可区分证据 |
| 旁白节拍指纹 | 改前：10 拍同构尾（口诀/实验/合上书） | **已改**：短片 7 拍 + 长片 purpose 交错；已 regen 成片与 media-report |
| 同构填料 | 「学习目标」五条清单偏目录腔 | 改写成离开检查动作/判断；标题保留以兼容既有 sample 测试 |
| Sepia 删除/回退 | 无专章记录 | 见下节 |

## Sepia 删除 / 回退检查

诊断（先列缺陷再改字）：

1. 视频后缺最小胜利 → 读者被手册墙拦住。
2. 学习目标复述目录 → 与离开检查重复且不可验收。
3. Handraw 资产存在却不进正文 → 知识轨合同缺口。
4. 真证与知识轨未分家声明 → 易把插画当测量。

删除检查：

- 未新增「本章将介绍 / 让我们 / 通过以上」类开场。
- 最小胜利四步若删掉任一步，验收条件不完整 → 保留。
- 真证缺口句若删掉，双轨合同消失 → 保留。

回退检查：

- 原理/插图/时序/坑卡/代码/BSRR 亮灭注释/LCKR 两次读/stack 单次引用等既有精确句**未改写**（避免为润色拉长）。
- 仅替换学习目标条目、插入最小胜利与真证声明、manifest 扩字段。

## 旁白 / 视频

### 短片节拍（已改 + 已 regen）

- 源：`tools/narration.py` `CHAPTERS[3].segments` → **7 段**（非邻章 10 段模板）。
- 指纹 heads：写 1，灯反而灭了？ → 先做成最小胜利 → 低电平为什么能点灯 → 驱动与空闲电平 → 照抄 PA0 会踩坑 → 三条边界带走 → 离开前做一件事。
- **明确去掉**邻章同构尾拍「口诀 / 实验… / 合上书，三问」。
- SP-05：开场 0–8s 反常识实问题（PC13 写 1 灯灭）；机制段画面走 Handraw/stack，旁白标明「不是实测电流」。
- 成片：`assets/video/ch03-gpio.mp4`（**1920×1080**，speak ≈121.4s）+ `.srt` + 海报；本轮以 `NARRATED_SCALE=2` 重生（sha256 见文末补证）。
- 中英正文 `<details>` 旁白列表已同步 7 条。

### 长片分镜（已改 + 已 regen）

- 源：`video/ch03/storyboard.json` 仍 28 场；`purpose` 计数 hook1 / mechanism15 / failure8 / experiment3 / recall1。
- 指纹不同于 ch02：开场即 `hook > mechanism > failure > …`；收尾 `experiment > recall > failure`（ch02 收尾为 `experiment > recall > recall`）。
- 成片链：`NARRATED_FONT=C:\Windows\Fonts\msyh.ttc` + `NARRATED_SCALE=2` 下 `python tools/gen_long_lesson.py --speak 03` **exit 0**。
- 产物（`final-videos/` 被 gitignore，以报告为准）：
  - `final-videos/ch03/ch03-bilibili-safe.mp4` ≈676.6s / 1920×1080 / 30fps
  - `video/ch03/media-report.json` 全绿（28_scenes、five_learning_roles、1080p、30_fps、subtitle_count、duration_*、loudness、true_peak、contact_sheet）
  - `video/ch03/contact-sheet.jpg`、`ch03.srt`、`storyboard-rendered.json` 已更新
- mp4_sha256（media-report）：`205a47dea4a49f3e179d4214a1cbad9dce9f78e52c5566eb0f860e442988b279`

### 邻章对照

| 章 | 短片段数 | 典型尾拍 |
| --- | --- | --- |
| 02 | 10 | 口诀 → 实验… → 合上书，三问 |
| **03** | **7** | 边界 → 离开前一件事（无口诀/三问） |
| 04 | 10 | 口诀 → 实验… → 合上书，三问 |

## §10.2 勾选展望（本轮目标）

改完并测试后应可勾：

- 教学合同中英登记对齐
- 功能块可选 + 最小胜利在手册密度前
- Handraw 引用 + 真证缺口声明
- 失败分支可区分证据（既有表 + 指向）
- Sepia 记录（本文）

仍开放（诚实未验证）：

- 浏览器/PDF **人工目检** / `task_verify`（absent-tool）
- 全书级 `check_assets`（ch18–ch20 960p 存量 FAIL；ch03 已回 1080p）

## 知识轨哈希（本轮引用）

| 文件 | SHA-256 |
| --- | --- |
| `assets/illustrations/ch03-handdraw.svg` | `f42797497bced104561e330c8e8293c26ef0c2142c0c6935175d70a5bf185ef0` |
| `assets/diagrams/stack-gpio-pc13-led.png` | `3677daa7780d086868437f41450664e8d2faa6c58ed07ccbadeb188c1fa960d9` |
| `assets/diagrams/sample-03-gpio-led.svg` | `35a7e6901de591eee1e61a095904be4e2a926c4c351c386d20b8bfda714a6abe` |

## §15.4 B1 三表（ch03 模板）

本节是 Overlay §15.4 计划 30 要求的三表，作为 B2–B7 的唯一模板。表内每行都能在仓库文件中核对；未新生成图的章不得照抄本表。

### 表 1 · 插图清单

| # | 文件 | 类型（§15.1） | 认知任务（互不重复） | 轨道 / 登记 | Layout | 风格 / 配色 | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `assets/illustrations/ch03-handdraw.svg` | 概念图（双态对照） | 写值 → 共阳电流方向：写 1 灯灭、写 0 灯亮 | 知识轨（Handraw）；manifest `files[chapter=03]` 已登记 | IG-004 双列多行对比 | FA-002 continuous-line；层登记 C-03 / C-10 / C-27 / C-31（页脚 Prussian Blue / Sage / Naples Yellow） | `f42797497bced104561e330c8e8293c26ef0c2142c0c6935175d70a5bf185ef0` |
| 2 | `assets/illustrations/ch03-mid-handdraw.svg` | 概念图（上拉 / 下拉双态） | 浮空引脚被按住 vs 浮空；长片分镜 `visual_source` 已用 | 知识轨（Handraw）；manifest `mid[chapter=03]` 已登记；**未入章正文** | IG-004 双列多行对比 | FA-002；同层配色 | `bd31d11c8f267c785870667472ae3fa8f8a3186ebc342294cbad0b1a1a6a33de` |
| 3 | `assets/diagrams/sample-03-gpio-led.svg` | 技术关系图 + 正误对比 | PA0 推挽点灯（正确）vs 同一接法搬上 PC13（错误） | 知识轨自绘（`tools/gen_sample_figures.py`，svgkit） | IG-004 双列多行对比 | 自绘静态；页脚标注 DS5319 Rev 20 | `ed09310282b4f0b6b6abf6bb529636b0a276d8fcb9262f06cfc8b6044e407d04` |
| 4 | `assets/diagrams/stack-gpio-pc13-led.png` | 技术关系图（分层） | 程序控制路径与电流路径分层对账 | 精确工程轨 `stack-diagram`（HTML 源含 `stack-diagram` 标记、132px 节点网格） | 节点几何规则（非 IG 图型） | 自绘；暗色版 `stack-gpio-pc13-led-dark.png` | `3677daa7780d086868437f41450664e8d2faa6c58ed07ccbadeb188c1fa960d9` |
| 5 | `assets/boards/pinout-bluepill.svg` | 技术 / 硬件图 | PA0、PA1、PC13、PA13、PA14 位置与复用边界 | 知识轨自绘（`tools/gen_pinouts.py`） | 引脚全图（非 IG 图型） | 自绘 | `35530cc647320da3e1cc809177d74f0be79c1c3b23ce32f266e92c83ab958a03` |

类型覆盖：概念图（1、2）、技术关系图（3、4、5）、排错或对比图（3 的正误双栏 + 「常见坑与出处」五行表）。任务不重复：1 讲共阳电流方向，2 讲浮空电平，3 讲电流路径与引脚能力边界，4 讲控制/电流分层，5 讲板级引脚位置。

真证轨缺口：BluePill PC13 共阳实拍 / 万用表或示波器截图仍**待补**；有则回填哈希，无则保留缺口声明。

原文请求存档：以上 1–5 均为既有资产回登记，本轮**未**新生成图片，故无新提示词存档；后续新图必须随图登记 Layout / 风格 / 配色与提示词原文。

### 表 2 · 动画清单

| # | 文件 | 覆盖要求 | 认知任务 | 可播放性 | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| 1 | `assets/animations/gpio-blink.svg` | 核心机制 ≥1 可播放演示 | GPIO 推挽输出两态驱动 LED（写 1 / 写 0 电流路径） | 5 段 CSS keyframes（`hd-pulse` / `hd-flow` 等），首帧为完整静态底图，PDF 打印可读 | `27bf3652e06a0f27092da486ea17916554593ee1b81cd1048c42ce95e22ec997` |
| 2 | `assets/gif/led-blink.gif` | 实验可见结果 | PC13 低电平点亮 → 1 Hz 闪烁 | GIF 动图（640 px 宽，8085 B） | `d5654032d7760c3fe017ddbb1f5df1ba58cfe9192ad55b833002a5964c6ae1f1` |

空转场 / 纯装饰动效：0（1 的机制变化是写值—电流方向对应，2 是实验现象）。章首视频不计入动画锚点。

### 表 3 · 官方 / 开源对照表

| 来源 | 类型 | 编号 / 版本 | 路径 / 位置 | 许可 | 可复用 / 仅对照 | 冲突裁定 |
| --- | --- | --- | --- | --- | --- | --- |
| RM0008 | ST 官方参考手册 | Rev 21（STM32F101/102/103/105/107） | §9 GPIO；§9.2.7 `GPIOx_LCKR`；§9.3.5 表 36（SWDIO=PA13、SWCLK=PA14） | ST 文档条款 | 权威依据，可引用文档号 | 与开源冲突时以 RM0008 适用条件为准 |
| DS5319 | ST 官方数据手册 | Rev 20（STM32F103x8/B） | 表 5 引脚定义；图 8；注 5（PC13–PC15：3 mA / 2 MHz / 30 pF） | ST 文档条款 | 权威依据，可引用文档号 | 3 mA / 2 MHz / 30 pF 只认 DS5319 注 5 |
| zhuguang-ZFG/STM32 | GitHub OSS | `main` | `examples/`（gpio-blink 等 14 例程） | MIT | **仅对照**：例程目标、接线、预期现象、代码可复用；不作为限值或寄存器依据 | 差异写入迁移表 / 坑表，不静默覆盖官方 |
| zhuguang-ZFG/STM32 | GitHub OSS | `main` | `docs/`（内容风格指南） | CC BY 4.0 | **仅对照**：命名与写作规则 | 与 Overlay 冲突时以 Overlay 为准 |

订货号：STM32F103C8T6，LQFP48 封装（PA0 第 10 脚、PC13 第 2 脚）。每章 ≥1 个 GitHub OSS 的要求已由 `examples/`（MIT）满足。

**冲突实例（已按 §15.3 计划 29 处理）：** PA0 的 `(3.3 − 2.0) / 0.005 = 260 Ω` 来自 MIT 例程估算，2.0 V / 5 mA **不是** DS5319 推荐值；正文与图 3 均标明「不是数据手册推荐的电流」，限值仍以 DS5319 注 5 为准。

## 本轮可复现验证（执行结果）

| 命令 | 结果 |
| --- | --- |
| `python tools/slop_lint.py` | 干净 |
| `python -m unittest discover -s stm32-book/tests` | **176 OK** |
| `python stm32-book/build_html.py --check` | PASS（zh） |
| `python stm32-book/build_html.py --lang en --check` | PASS（en） |
| `python tools/check_assets.py` | **FAIL（存量）**：仅 ch18/ch19/ch20 为 960×540；**ch03 本轮 1920×1080 ok**；海报字体 SKIP |
| `python tools/gen_long_lesson.py --check 03` / `--speak 03` | **本轮通过**：设 `NARRATED_FONT=C:\Windows\Fonts\msyh.ttc` 后 `--check` 与 `--speak` 均 exit 0；media-report 全绿 |
| `python stm32-book/build_html.py --pdf` / `--lang en --pdf` | **构建 passed**（dist 已写出）；**人工目检仍 unverified** |
| 浏览器章页目检 | **unverified**（无 GUI 目检；dist HTML 见文末） |
| `task_verify` | **unverified（absent-tool）** |

## §10.2 本轮勾选

- [x] Overlay / Port A / Port B / CONTENT_GUIDE §8（既有）
- [x] 中英教学合同字段登记对齐
- [x] 最小胜利在手册密度前；功能块可选组织
- [x] Handraw 正文引用 + 真证轨缺口声明（哈希在本清单）
- [x] 失败分支可区分证据（坑表保留）
- [x] Sepia 删除/回退记录（上文）
- [x] 短片+长片节拍指纹去同构并可再生（本轮：短片 7 拍 regen；长片 media-report 全绿）
- [x] **§15.4 三表（B1 模板）** 已写入本文件 §15.4；类型覆盖概念/技术关系/排错对比，核心机制动画 ≥1，官方（RM0008 Rev 21 / DS5319 Rev 20）+ OSS（MIT `examples/`）齐全。
- [x] 全书级 `check_assets`：**PASS**（1298/1298 链接、29 章 MP4+SRT+海报；ch16–ch20 已回 1920×1080，`hd_chapters` 同步登记）。
- [x] 窄回归 + 全量 `unittest` + `check_assets` + `slop_lint` + 双语 HTML `--check`：**全绿**（177 OK；PDF 构建与目检见文末收口轮）。
- [x] 浏览器/PDF **目检**：ch03 章首页 / Handraw 关系图 / stack 关系图 / 寄存器表 / 实验动画 / 引脚图已用真实 Chromium 渲染逐页核对（证据见文末收口轮）。
- [x] `task_verify`：工具已可调用（`xd://task_verify`）→ **unverified（project-or-git-baseline-unavailable）**；passed/failed 均无，不冒充通过。

## 建议下一步

1. ~~短片/长片节拍去同构与 regen~~ **已完成**（见上文旁白/视频）。
2. 补 BluePill PC13 真证照片/表计截图并回填本清单哈希。
3. 人工完成浏览器/PDF 目检，并处理 ch18–20 960p 或书面挂账后，再勾 §10.2 剩余项；勿开 B2。`task_verify` 仍为 absent-tool。
4. 另开任务处理 ch18–ch20 视频 960p（`check_assets` 存量 FAIL）；勿与 ch03 合流提交混装。

## 本轮验证记录

时区：America/Adak（UTC-10）。记录时刻约 2026-11-03 02:26 Adak。

### 已跑且通过
- `python -m unittest stm32-book.tests.test_converge_ch03 stm32-book.tests.test_advanced_visuals stm32-book.tests.test_book_audit -v` → 20 OK
- `python -m unittest discover -s stm32-book/tests -v` → **176 OK**（约 86s）
- `python tools/slop_lint.py docs/03-GPIO与LED.md docs/en/03-gpio-and-led.md` → 干净
- 双语 HTML 由书册测试路径生成（约 6.0 MB / 6.1 MB，29 章）；本轮未单独跑带 `--check` 标志的发布脚本之外的独立门（若仓库 HTML check 嵌在 unittest，已随 176 OK 覆盖）

### 已跑未通过（与 ch03 无关的存量）
- `python tools/check_assets.py` → **FAIL**：`ch18-faq` / `ch19-projects` / `ch20-refs` 视频流为 960×540，不是 1920×1080。ch03-gpio.mp4 本身 `[ok]`。海报字库缺失仅 SKIP。

### 未验证（诚实列出，不勾 §10.2）
- 浏览器目检（章首页 / 关系图 / 代码表 / 实验页）：**未做**（dist HTML 已生成）。
- PDF **人工**翻页目检：**未做**（zh/en PDF **构建**已 passed，见文末）。
- `task_verify`：**unverified（absent-tool）**，仓库无入口。
- 全书 `check_assets`：仍因 ch18–20 960p FAIL（与 ch03 无关）。
- BluePill PC13 共阳真板照片：仍 **待补**（正文已声明真证轨缺口）。
- 注：短片/长片节拍去同构与 ch03 短片 1080p 重生已在上文/文末记录，不再列未跑。

### Sepia 删除/回退（本轮）
- **删/削**：未发明第二套章骨架；未整支合并 handraw docs。未删事实表、公式、代码、来源锚。
- **留**：`## 学习目标` / `## Learning goals` 标题因 Book2.0/batch 契约测试锁定保留；离开检查语义落在 `chapter_guides.exit_check` 与最小胜利块。四节经典 H2（原理与适用范围等）保留。
- **加**：`## 最小胜利` / `## Minimum victory` 前置；Handraw 知识轨图 + 真证轨「待补」声明。
- **回退点**：去掉最小胜利块与 manifest 七字段即可回到 Port 前正文合同形态；勿回滚事实内容。
- **未整支合并** handraw 分支 docs。

### 建议下一手
1. 改 ch03 旁白/分镜节拍指纹，打破与 ch02/ch04 的同构 10 拍，再走短片链。
2. 在有字体与 PDF 依赖的环境跑双语 PDF check + 浏览器四页目检。
3. 另开任务修 ch18–20 960p（或降级 check_assets 规则），否则书级 `check_assets` 无法绿。
4. 补 BluePill PC13 真证照片并回填哈希。

### 旁白节拍硬门（2026-11-03 约 02:40 America/Adak（UTC-10））

已跑且通过：

- 短片 fingerprint ≠ 02/04；无「口诀/合上书」头；`gen_narrated` speak+srt 已更新 `assets/video/ch03-gpio.*`
- 长片 `gen_long_lesson.py --speak 03` exit 0；`video/ch03/media-report.json` checks 全 `true`
- 相关 unittest / `slop_lint` 见本轮提交前复跑结果

未宣称 / 仍开放：

- 全书 `check_assets`（ch18–20 960p；ch03 短片已回 1080p）
- 浏览器/PDF **人工目检**；`task_verify`（absent-tool）
- 未把 gitignored 的 `final-videos/ch03/*.mp4` 纳入版本库；以 `media-report.json` 哈希为准

### 剩余硬门补证（2026-11-03 02:58 America/Adak (UTC-10)）

本轮只补证据与 ch03 相关阻塞，不把未目检项写成通过。

#### 1) `task_verify`

| 分列 | 结果 |
| --- | --- |
| passed | （无） |
| failed | （无） |
| unverified | **工具/脚本在仓库中不存在** |

检索范围：`tools/`、`stm32-book/`、`.claude/skills/`、根目录脚本与文档引用。命中仅为 Spec/审计叙述与 `audits/ch03-l1-tdd.md` 历史句（`unverified（project-or-git-baseline-unavailable）`）。**无**可执行的 `task_verify` CLI/入口。因此本项记 **unverified（absent-tool）**，不冒充通过，也不勾 §10.2 对应框。

#### 2) 双语书册自动检查

| 命令 | 结果 | 备注 |
| --- | --- | --- |
| `python stm32-book/build_html.py --check` | **passed** | zh HTML contract；约 6.0 MB / 29 章 |
| `python stm32-book/build_html.py --lang en --check` | **passed** | en HTML contract；约 6.1 MB / 29 章 |
| `python stm32-book/build_html.py --pdf` | **passed（构建）** | `stm32-book/dist/stm32-practical-book.pdf`（约 13.5 MB） |
| `python stm32-book/build_html.py --lang en --pdf` | **passed（构建）** | `stm32-book/dist/stm32-practical-book-en.pdf`（约 13.8 MB） |

说明：PDF 两项是 Playwright 打印**构建成功**，**不是**人工 PDF 目检。

#### 3) 浏览器 / PDF 目检

| 项 | 结果 |
| --- | --- |
| 浏览器章首页 / 关系图页 / 代码或表页 / 实验页 | **unverified**（未做可靠 GUI 浏览器目检；**不勾** §10.2 目检框） |
| PDF 人工翻页目检 | **unverified**（已生成文件，待人眼） |

供人工目检的本机路径：

- `D:\Users\STM32\stm32-book\dist\stm32-practical-book.html`
- `D:\Users\STM32\stm32-book\dist\stm32-practical-book-en.html`
- `D:\Users\STM32\stm32-book\dist\stm32-practical-book.pdf`
- `D:\Users\STM32\stm32-book\dist\stm32-practical-book-en.pdf`

#### 4) `check_assets`（清洁环境：未设置 `NARRATED_SCALE` / `NARRATED_FONT`）

| 项 | 结果 |
| --- | --- |
| 命令 | `python tools/check_assets.py` → **failed**（exit 1） |
| ch03-gpio | **ok**：视频流 **1920×1080** H.264；121s；字幕 7 条（本轮 `NARRATED_SCALE=2` + `NARRATED_FONT=C:\Windows\Fonts\msyh.ttc` 重生） |
| ch03 mp4 sha256 | `97fc7f0d0ca868c625a82765fd027e13a0f35f9f4794a302d250813c1544b6f1` |
| 海报逐像素 | **SKIP**（默认字体 `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc` 本机不存在） |
| 存量 FAIL | **ch18-faq / ch19-projects / ch20-refs** 均为 `('h264', 960, 540)`，期望 1920×1080 |

**最小修复选项（仅文档建议；本轮未改策略、未整批重生 18–20）：**

1. **优选**：`NARRATED_SCALE=2` + `NARRATED_FONT=C:\Windows\Fonts\msyh.ttc` 后执行 `python tools/gen_narrated.py --speak 18 19 20`，再在清洁环境复跑 `check_assets`。
2. **临时例外**：审计挂账「L4 批次 B5 前允许 960p」；**不**改 `hd_chapters`，除非另开策略 PR。仓库内**无**现成一行 allowlist。
3. **禁止本轮**：为绿灯删断言、扩大 allowlist、或无关章节大清洗。

注意：若 shell 仍导出 `NARRATED_SCALE=2`，`check_assets` 会误伤海报比对；验证前必须清除。

#### 5) §10.2 勾选纪律（本轮）

- 已勾选的合同/结构/Handraw/真证/节拍/Sepia 项：不回退。
- **仍不勾**：
  - 复合自动检查门（全书 `check_assets` 仍因 ch18–20 FAIL）。
  - 浏览器/PDF 人工目检。
  - `task_verify`（absent-tool → unverified）。
- 双语 HTML `--check` 与双语 PDF **构建**已 passed，只记证据，不单独把复合门改成勾选。

#### 6) 仍需用户侧完成

1. BluePill PC13 共阳真板照片 / 表计截图，回填真证轨哈希。
2. 打开上列 dist HTML/PDF，完成章首页、关系图、代码/表、实验页目检。
3. 决定 ch18–20：重生 1080p，或书面批准挂账到 B5。
4. 若团队另有外部 `task_verify` 入口，提供路径后再跑并分列记账。

## 收口轮（2026-11-03 晚，America/Adak）

### §15.4 三表（B1 模板）

已写入上文「§15.4 B1 三表」：插图清单 5 行、动画清单 2 行、官方/开源对照 4 行。官方 RM0008 Rev 21 / DS5319 Rev 20；OSS `zhuguang-ZFG/STM32` `examples/` MIT（仅对照）。B2–B7 强制同模。

### 自动检查（全部重跑）

| 检查 | 结果 |
| --- | --- |
| `python -m unittest discover stm32-book/tests` | **177 OK**（75s；较上轮 +1：`test_classic_l5` 4 用例） |
| `python tools/check_assets.py` | **PASS**（1298/1298 链接，29 章 MP4+SRT+海报） |
| `python tools/slop_lint.py` | 干净 |
| `build_html.py --check`（zh/en） | PASS（6010483 / 6060965 bytes，29 章） |
| `python tools/audit_book.py` | 中文 PDF 视觉锚点 140，低于目标章节 0 |
| `git diff --check` | exit 0 |
| ch16–ch20 五个短片全解码（`ffmpeg -v error -map 0 -f null -`） | exit 0，stderr 0 字节 |
| `xd://task_verify`（action=run，提交前后各一次） | **unverified（project-or-git-baseline-unavailable）**，checks=[]；不冒充通过 |

提交链（本收口轮共 4 个提交，`git log --oneline -4` 可复核）：页眉字体修复 → 审计/spec 收口 → ch16–20 回 1080p → ch16–20 分镜源与 L5 契约测试。工作树在收口后仅剩 gitignored 的 `dist/`、`.temp/`。

### ch16–ch20 短片回 1080p 与合同对齐

- 工作树中 ch16–ch20 已重生成 1920×1080；`tools/check_assets.py` `hd_chapters` 原缺 16/17 致反向 FAIL，补齐为 `{00..20}`。
- 配套：`tools/narration.py` ch18 第 5 拍改 4 条、ch16–17 SRT 同步、`docs/20` 一处文字。

### 浏览器目检（真实 Chromium，1600×1125 ×7 图）

p1 章首页 / p2 Handraw 双态 / p3 stack 关系图 / p4 寄存器表 / p5 实验 GIF / p6 动手实验 / p7 引脚图。视觉核对：图全渲染，无缺图/断图；`ch03-handdraw.svg` 页脚 "CH 04" 系显示编号（源 03 → 显示 04），非缺陷；`gpio-blink.svg` 标注「外接 LED：高电平点亮（BluePill 板载灯是 PC13，低电平才亮）」为诚实通用示例。

### PDF 目检（PyMuPDF 光栅 + 视觉核对）

zh p44/46/48/50、en p47/48/50/54/58：中文完好、表格/代码/插图无溢出，动画首帧印刷可读。

### PDF 页眉乱码根因与修复（用户报「书籍乱码」）

- **根因**：`build_html.py` 页眉用 `china-s` 别名 → PDF 仅写 `/BaseFont/Heiti` 引用、零嵌入（`extract_font` = 0 字节）。MuPDF 自带回退故光栅目检全绿；Adobe/浏览器/手机阅读器无此字体 → **每页页眉乱码**。正文 28 字体中 17 个 Type3 由 Chromium 自嵌（`AAAAAA+` 前缀），不受影响。
- **修复**：`build_html.py` `_header_font_buffer()` 取 `fitz.Font("cjk")` buffer，`insert_font(fontbuffer=...)` 真嵌入 Droid Sans Fallback；宽度测量改 `Font.text_length`。回归：stamping 契约 4 测试 OK；嵌入断言 3556308 字节；even/odd 页眉与省略号路径实测。
- 乱码面普查：全库 1074 文本文件严格 UTF-8 扫描 → 干净（仅 `.claude/settings.local.json` 权限串 1 个 U+FFFD，非书籍内容）；git 中文文件名八进制转义系 `core.quotepath`，已设 false。

### 遗留

1. BluePill PC13 真证照片仍缺（上文 §6.1）。
2. B2–B7 未动（B1 模板已就绪）。
