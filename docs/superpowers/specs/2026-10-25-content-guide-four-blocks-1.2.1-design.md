# CONTENT_GUIDE 四块规范对齐 1.2.1 设计

日期：2026-10-25  
状态：已批准，待 CONTENT_GUIDE 实施  
基线：`main` 上的整书 **v1.2.0**（`4cbb4b5624c0914f872bed615477ba55678b4748`，PR #27，2026-10-25）  
上一份设计：[2026-10-25-book-visual-polish-1.2.0-design.md](2026-10-25-book-visual-polish-1.2.0-design.md)（PR #25）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。  
本文件只记录设计。它不改 `docs/CONTENT_GUIDE.md`，不改 `docs/en/CONTENT_GUIDE.md`，不改正文，不升版本号，不打 tag，不发布 Release。

## 背景

观感抛光已经在 `main` 上标成 1.2.0。上一份设计把下一刀点名为 CONTENT_GUIDE 规范对齐，再往后才是 Batch3。本文件只覆盖这一刀：让两份贡献指南的固定骨架承认大典四块。

对照 v1.2.0 核对过的事实：

1. **四块只在四章里，而且位置已经固定。** 中文 `docs/00-如何学习STM32.md`、`docs/03-GPIO与LED.md`、`docs/04-中断与NVIC.md`、`docs/06-串口UART.md`，以及英文 `docs/en/00-how-to-learn-stm32.md`、`docs/en/03-gpio-and-led.md`、`docs/en/04-interrupts-nvic.md`、`docs/en/06-uart.md`，都在 `<!-- /video: -->` 之后、`## 📌 学习目标` 或 `## 📌 Learning goals` 之前，各有一次 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。这四个标题没有表情符号。其余章仍从学习目标写起。
2. **中文指南的骨架还是旧的。** `docs/CONTENT_GUIDE.md` 第 2 节「每篇文章的固定骨架」在居中动画段之后直接是 `## 📌 学习目标`，然后是核心原理、硬件与接线、代码实现、`## ⚠️ 常见坑与排查`、动手实验、相关资源。四块标题一次都没有出现。
3. **英文指南的旧坑标题和章内用词不是同一串。** `docs/en/CONTENT_GUIDE.md` 第 2 节骨架里的坑标题是 `## ⚠️ Common traps and how to check them`。未加厚的英文章多用 `## ⚠️ Pitfalls and troubleshooting`。已经加厚的 00、03、04、06 章删掉了后一个标题，没有留下空节。
4. **`#source-` 已经能点到附录 E。** 第 00 章坑表的出处列是 Markdown 链接，例如 `[RM0008 表 9](#source-rm0008-boot)`。`stm32-book/build_html.py` 把两份 manifest 的 `sources` 渲染成 `<article class="source-card" id="source-{id}">`。构建检查要求页内 `#fragment` 都有目标。指南里还没有写下这条链。
5. **版本字面量锁在 1.2.0。** `revisions.json` 第一条是 `1.2.0`（2026-10-25），中英各两句，只讲样式。`manifest.json` 与 `manifest-en.json` 的 `version` 是 `1.2.0`，`date` 是 `2026-10-25`。`stm32-book/README.md` 当前版本句是 **v1.2.0 · 2026-10-25**。发布节写「版本号已经是 1.2.0」，tag 名是 `v1.2.0`，误标句子收到「也不要把 1.1.1 的产物标成 1.2.0」。`stm32-book/tests/test_build.py` 在 `assert_version_history_and_index`、`test_revision_file_lists_1_0_0_through_manifest_version`、`test_build_produces_one_complete_offline_book`、`test_english_book_is_a_separate_offline_edition` 和 `test_visual_polish_version_is_1_2_0` 里把当前版本断言为 `1.2.0`。
6. **Book CI 不扫描四块。** 工作流是 `.github/workflows/book.yml`，名称是 Book CI。它构建整书并跑现有测试，不读取两份 `CONTENT_GUIDE.md` 的骨架标题，也不扫描 29 章是否已经有四块。

## 目标与非目标

### 目标

- 只改 `docs/CONTENT_GUIDE.md` 与 `docs/en/CONTENT_GUIDE.md` 的第 2 节。在「每篇文章的固定骨架」里把大典四块写成必选。中文标题是原理与边界、关键插图、时序或状态、坑与出处卡。英文标题是 Principle and boundary、Key figures、Timing or state、Pitfalls and source cards。位置在视频块之后、学习目标之前。
- 写明旧「常见坑与排查 / Pitfalls and troubleshooting」迁入「坑与出处卡」。坑行用 `#source-` 链到附录 E。英文骨架里现在的 `Common traps and how to check them` 在同一次编辑里删掉，不留成第二套坑标题。
- 实施 PR 把整书标成 **1.2.1 · 2026-10-25**。中英文共用这个版本号。改两份 manifest 的 `version` 和 `date`、`revisions.json` 的新第一条、`stm32-book/README.md` 的版本句和发布节，以及 `test_build.py` 里已经把当前版本锁成 1.2.0 的断言。
- 实施 PR 在 Book CI 变绿之后自动 squash 合入 `main`。

### 非目标

- 不改 `docs/00`–`28` 与 `docs/en/` 的章节正文，含已经有四块的 00、03、04、06。不把其余章补到新骨架上。
- 不改两份指南的第 1、3、4、5 节，不改指南开头的定位段。
- 不写样图或 GIF 的细则：不规定张数、静态或动画、体积、`svgkit`、`gen_sample_figures.py`、`gen_gifs.py`。这些仍只活在既有加厚设计里。
- 不加图目录或表目录。出版书签仍是现在的条数。
- 不加扫描各章四块的测试，不改 `.github/workflows/book.yml`，不加 scan CI。
- 不改 `stm32-book/build_html.py`，不改附录 E 的字段，不改两份 manifest 里除 `version` 和 `date` 以外的字段，不改 `CREDITS.md`。
- 不打 tag，不创建 GitHub Release。README 的发布节只改版本句、tag 名和一句「不要把上一版产物标成这一版」，不在实施 PR 里执行发布步骤。
- 不实现 Batch3，不预选下一次加厚的章号。不回写观感设计文件。

## 骨架

四块只加在第 2 节的骨架代码块里。中文代码块保持 `../assets/...`。英文代码块保持 `../../assets/...`。四个新标题不加表情符号。学习目标继续带 `📌`。

代码块里，四块紧接现有居中动画段的 `</p>` 之后、学习目标之前。指南骨架现在没有 `<!-- video: -->` 注释；实施时不把旁白稿或这条注释写进指南。给贡献者的一句位置说明写在代码块下面：章内若有 `<!-- video: -->` … `<!-- /video: -->`，四块仍写在该注释结束之后、学习目标之前，与第 00、03、04、06 章相同。

| 块 | 中文标题 | 英文标题 | 标题下写进代码块的一句 |
| --- | --- | --- | --- |
| 1 | `## 原理与边界` | `## Principle and boundary` | 结论钉在哪颗订货号、哪路时钟、哪一版手册；换系列时哪一句作废 |
| 2 | `## 关键插图` | `## Key figures` | 这一节放关键插图 |
| 3 | `## 时序或状态` | `## Timing or state` | 一张能算回去的时序表或状态表。没有电气时序就写状态迁移，不留空标题 |
| 4 | `## 坑与出处卡` | `## Pitfalls and source cards` | 不写句子，只放下面的表头 |

中文第四块的表头沿用第 00 章：`现象`、`原因`、`处理`、`出处`、`该来源允许支持的主张`。英文表头沿用 `docs/en/00-how-to-learn-stm32.md`：`Symptom`、`Cause`、`What to do`、`Source`、`Claim this source may support`。代码块里只放表头，不放第 00 章的例子行。

从代码块里删掉的旧标题：

- 中文：`## ⚠️ 常见坑与排查`，以及它现在的三列表（现象、原因、解决）。
- 英文：`## ⚠️ Common traps and how to check them`，以及它现在的三列表（Symptom、Cause、Fix）。

代码块下面、仍在第 2 节，用贡献者能照做的话写迁入规则。这段不放进骨架代码块，避免被抄进各章正文：

- 旧「常见坑与排查 / Pitfalls and troubleshooting」不再作为骨架标题。原先写在那一节的坑迁入「坑与出处卡 / Pitfalls and source cards」，不保留两套说法，不留空标题。
- 每一行只有一个主张。出处列写成指向 `#source-{id}` 的链接。`{id}` 是两份 manifest 的 `sources` 里已有的 id。构建后的目标是附录 E 卡片上的 `id="source-{id}"`。
- 指南不新开第二份出处表。新 id 仍按既有加厚设计追加进 `sources`；这一刀的实施不追加 id。

学习目标、核心原理、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题，留在四块之后，顺序不变。代码仍按第 3 节现有约定：HAL，参数用宏。

## 版本与修订文案

实施 PR 把整书标成 **1.2.1**，日期 **2026-10-25**。`validate_revisions` 仍要求修订第一条的版本等于两份 manifest 的 `version`。日期用这个写死的日子，不用合并当天另换。

`revisions.json` 在条目最前新增：

- `version`: `1.2.1`
- `date`: `2026-10-25`
- `zh`:
  - 贡献指南把大典四块写成每章必选，放在视频块之后、学习目标之前。
  - 旧的常见坑与排查迁入坑与出处卡，并用 `#source-` 链到附录 E。这一版不改正文章。
- `en`:
  - The contributor guide requires the four compendium sections after the video block and before the learning goals.
  - The old pitfalls section moves into Pitfalls and source cards, with `#source-` links to Appendix E. This edition does not rewrite chapter prose.

不在修订说明里写 Batch3，不写观感。保留 1.2.0 及更早条目，含 1.2.0 那两句样式说明。

`manifest.json` 与 `manifest-en.json` 的 `version` 改为 `1.2.1`，`date` 改为 `2026-10-25`。其他字段不动。

`stm32-book/README.md`：

- 当前版本句改为 **v1.2.1 · 2026-10-25**。中英文整书仍共用这一版号。Release 仍等提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
- 发布节的版本句改为已经是 1.2.1。tag 名改为 `v1.2.1`。在现有「也不要把 1.1.1 的产物标成 1.2.0」之后加上「也不要把 1.2.0 的产物标成 1.2.1」。
- 这一步仍不创建 tag，也不创建 Release。

`stm32-book/tests/test_build.py` 只改已经把当前版本锁成 1.2.0 的断言，使 Book CI 能在 1.2.1 上变绿：

- `assert_version_history_and_index` 的版本元组在 `1.2.0` 之前加上 `1.2.1`，并断言 `1.2.1` 出现在 `1.2.0` 之前。
- `test_revision_file_lists_1_0_0_through_manifest_version` 的列表以 `1.2.1` 起头，其后仍是 `1.2.0` 直到 `1.0.0`。
- `test_build_produces_one_complete_offline_book` 与 `test_english_book_is_a_separate_offline_edition` 里的 `<strong>v1.2.0</strong>` 改为 `<strong>v1.2.1</strong>`。英文 manifest 的 `version` 断言改为 `1.2.1`。
- `test_visual_polish_version_is_1_2_0` 改为核对当前条目是 1.2.1，日期是 2026-10-25，中英修订是上面四句。1.2.0 那四句样式说明改去核对 `entries[1]`。README 断言改为当前版本句 **v1.2.1 · 2026-10-25**、`版本号已经是 1.2.1。`、`也不要把 1.2.0 的产物标成 1.2.1。`，以及打 tag 的那一行使用 `v1.2.1`。不再把 `v1.2.0` 当成当前版本句或当前要打的 tag。

不新增读取 `CONTENT_GUIDE.md` 的测试。不删 `0x271`、`167 ns`、出版书签、样本章和 batch2 的断言。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增本文件。不改 `docs/CONTENT_GUIDE.md`、`docs/en/CONTENT_GUIDE.md`、章节正文、`stm32-book/`、`assets/`、`tools/`、`.github/`。不升版本，不打 tag，不发 Release。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **指南。** 按上一节改两份 `CONTENT_GUIDE.md` 的第 2 节。其他节不动。
2. **版本与测试锁。** 同一 PR 内改 `revisions.json`、两份 manifest、`stm32-book/README.md`，以及上一节点名的 `test_build.py` 断言。修订说明只用上一节的四句。
3. **验证。** 下面三条通过之后再请求合入：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

4. **合入。** Book CI 变绿之后，把实施 PR 自动 squash 合入 `main`。不打 `v1.2.1` tag，不创建 Release。

实施 PR 的 diff 可以碰：`docs/CONTENT_GUIDE.md`、`docs/en/CONTENT_GUIDE.md`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`、`stm32-book/tests/test_build.py` 里上一节点名的版本断言。不碰章节正文，不碰 `build_html.py`，不碰 `.github/workflows/book.yml`。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-content-guide-four-blocks-1.2.1-design.md`。
- 两份 `CONTENT_GUIDE.md`、`docs/` 章节、`docs/en/` 章节、`stm32-book/` 与基线 `4cbb4b5` 相同。
- 版本号仍是 1.2.0。没有 tag，没有 Release。

### 实施 PR

- 中文指南第 2 节的骨架代码块在学习目标之前各有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次，且在 `## 📌 Learning goals` 之前。
- 两份骨架代码块都不再有 `## ⚠️ 常见坑与排查`、`## ⚠️ Pitfalls and troubleshooting`、`## ⚠️ Common traps and how to check them`。
- 第 2 节、代码块之外写明：旧坑节迁入第四块，出处列用 `#source-{id}` 链到附录 E。
- `docs/00`–`28` 与 `docs/en/` 章节正文的 diff 为空。`build_html.py` 与 `.github/workflows/book.yml` 的 diff 为空。
- 两份 manifest 的 `version` 是 `1.2.1`，`date` 是 `2026-10-25`。`revisions.json` 第一条是上一节的四句，第二条仍是 1.2.0 的样式说明。README 当前版本句是 **v1.2.1 · 2026-10-25**。
- 上一节的三条命令通过。Book CI 变绿后实施 PR 已设置为自动 squash。
- 没有新的扫描测试，没有图目录，没有 tag，没有 Release。

## 后续

只点名，不在本文件里设计细节，也不进入 1.2.1 的 diff。

**Batch3 加厚。** 观感设计里已经把这一刀排在 CONTENT_GUIDE 之后。章号到那时的设计里再锁。本刀先让指南承认四块，不代替那次加厚。

## 未决问题

没有会挡住 CONTENT_GUIDE 实施的未决项。下面几项按此处的默认执行，复审规格时可以改口，不需要再写一版设计才改指南：

1. **英文旧标题的用词。** 骨架里删掉的是现在印着的 `Common traps and how to check them`。迁入说明使用章内旧标题 Pitfalls and troubleshooting。不两套并存。
2. **表情符号。** 四块标题不加。学习目标的 `📌` 保留。
3. **尚未加厚的章。** 继续留着旧坑标题，直到后面的加厚批次。1.2.1 不改正文去追平指南。
4. **样图、GIF、图目录、扫描 CI、Release。** 这一刀都不做。

## 英文提要

On v1.2.0 (`4cbb4b5`, PR #27), edit only the fixed-skeleton section of `docs/CONTENT_GUIDE.md` and `docs/en/CONTENT_GUIDE.md`. Require four sections after the video block and before the learning goals: 原理与边界 / Principle and boundary, 关键插图 / Key figures, 时序或状态 / Timing or state, 坑与出处卡 / Pitfalls and source cards. Move the old 常见坑与排查 / Pitfalls and troubleshooting section into the fourth block, and say that each row links `#source-{id}` to the Appendix E card the book builder already emits. Drop the English skeleton's current heading, Common traps and how to check them, in that same edit. Do not rewrite chapter prose, do not add figure or GIF rules, do not add a list of figures, do not add a scan CI job, and do not tag or release. The implementation PR bumps the book to 1.2.1 dated 2026-10-25 in both manifests, `revisions.json`, the README, and the existing version assertions in `test_build.py`, then auto-squash-merges after Book CI is green. This design PR only adds this file and waits for human review.
