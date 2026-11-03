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
- 成片：`assets/video/ch03-gpio.mp4`（960×540，speak ≈121.4s）+ `.srt`；海报 `ch03-gpio.png` 以 `NARRATED_SCALE=2` 出 1920×1080。
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

- 双语 PDF 目检 / 浏览器目检 / `task_verify`
- 全书级 `check_assets`（ch18–ch20 960p 存量 FAIL，与 ch03 无关）

## 知识轨哈希（本轮引用）

| 文件 | SHA-256 |
| --- | --- |
| `assets/illustrations/ch03-handdraw.svg` | `f42797497bced104561e330c8e8293c26ef0c2142c0c6935175d70a5bf185ef0` |
| `assets/diagrams/stack-gpio-pc13-led.png` | `3677daa7780d086868437f41450664e8d2faa6c58ed07ccbadeb188c1fa960d9` |
| `assets/diagrams/sample-03-gpio-led.svg` | `35a7e6901de591eee1e61a095904be4e2a926c4c351c386d20b8bfda714a6abe` |

## 本轮可复现验证（执行结果）

| 命令 | 结果 |
| --- | --- |
| `python tools/slop_lint.py` | 干净 |
| `python -m unittest discover -s stm32-book/tests` | **176 OK** |
| `python stm32-book/build_html.py --check` | PASS（zh） |
| `python stm32-book/build_html.py --lang en --check` | PASS（en） |
| `python tools/check_assets.py` | **FAIL（既有）**：ch18/ch19/ch20 视频流非 1920×1080；ch03 本身 ok；海报字体 SKIP |
| `python tools/gen_long_lesson.py --check 03` / `--speak 03` | **本轮通过**：设 `NARRATED_FONT=C:\Windows\Fonts\msyh.ttc` 后 `--check` 与 `--speak` 均 exit 0；media-report 全绿 |
| `python stm32-book/build_html.py --pdf` | **未验证**：本机启动后 PDF 长时间 0 B，已中止；不做绿灯 |
| 浏览器章页目检 / `task_verify` | **未跑** |

## §10.2 本轮勾选

- [x] Overlay / Port A / Port B / CONTENT_GUIDE §8（既有）
- [x] 中英教学合同字段登记对齐
- [x] 最小胜利在手册密度前；功能块可选组织
- [x] Handraw 正文引用 + 真证轨缺口声明（哈希在本清单）
- [x] 失败分支可区分证据（坑表保留）
- [x] Sepia 删除/回退记录（上文）
- [x] 短片+长片节拍指纹去同构并可再生（本轮：短片 7 拍 regen；长片 media-report 全绿）
- [ ] 窄回归之外：`check_assets` 全书级既有 FAIL 需另开
- [ ] 双语 PDF 目检 / 浏览器目检 / `task_verify` 分列

## 建议下一步

1. ~~短片/长片节拍去同构与 regen~~ **已完成**（见上文旁白/视频）。
2. 补 BluePill PC13 真证照片/表计截图并回填本清单哈希。
3. 双语 PDF 目检 / 浏览器章页目检 / `task_verify` 通过后再勾 §10.2 剩余项，勿开 B2。
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
- 短片/长片按 SP-05/06 重生：未跑。旁白仍与相邻章同构 10 拍风险，见上文节拍指纹。
- 双语 PDF `--check` / 实产 PDF：本机曾出现 0B 产物风险，本轮中止，**未验证**。
- 浏览器目检（章首页 / 关系图 / 代码表 / 实验页）：**未做**。
- `task_verify` 分列报告：**未跑**。
- BluePill PC13 共阳真板照片：仍 **待补**（正文已声明真证轨缺口）。

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

- 全书 `check_assets`（ch18–20 960p）
- 双语 PDF 浏览器目检 / `task_verify`
- 未把 gitignored 的 `final-videos/ch03/*.mp4` 纳入版本库；以 `media-report.json` 哈希为准

