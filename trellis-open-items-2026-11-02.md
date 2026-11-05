# Trellis 未解决事项清单（2026-11-02 盘点）

## 结论

书稿侧三条主线（去 AI 味、趣味性、AI 部加深）**实质工作已全部完成并通过印前 13 门**，卡在"用户验收 + 归档"这一步；封面与 88 章题图也已落地。真正还在动的是两条：**视频 v2 重制 Wave C**（五集已渲染、未发布换新）和**书的 EPUB3**（完全未做）。另有三个真空缺：E04 上板实测（缺硬件执行）、开源项目地图（只有调研没落地）、抖音 19 条手工置顶（只能用户在 App 点）。另有一批任务状态机停在 planning/in_progress 与实物不符，需顺手归档或推进。

## 任务清单

| 任务 | 目标 | 当前状态 | 证据 | 还缺什么 |
|---|---|---|---|---|
| 10-26-de-ai-polish | 去 AI 味精修：文字/图片/封面（父任务） | 已完成（待归档） | task.json 仍 planning；子任务 prose-polish / cover-art 均实质完成；印前 13 门全过（journal Session 32） | 走 `task.py start/finish/archive`；Open Decisions 三项未见正式关闭记录（实际已执行） |
| 10-26-prose-polish | 88 章+6 附录逐章精修 | 已完成（待验收归档） | `research/batch-reports/B9-B10-final.md`：94/94 章收官，破折号 2002+359→约 45；`mcu-book/tools/prose_guard.py` 在；pytest 72 passed、13 门全过（Session 32） | implement.md 里 B6/B6b/B8/M 行仍标"进行中/待派"（与报告矛盾，需刷新）；用户终验 + 归档 |
| 10-26-cover-art | 封面定制线稿插画 | 已完成（印前/站点侧） | 两版配色候选在 `research/cover/`；用户 10-26 拍板米白墨线（见 10-26-chapter-art/prd.md）；`mcu-book/print/art.py:78` `cover_art()` 已接入 `mcu-book/build_html.py:1330` | EPUB 封面同步（EPUB 本体未做，见 10-25-book-production）；状态机推进 + 归档 |
| 10-26-chapter-art | 88 章手绘题图 | 已完成（未归档） | `mcu-book/book/assets/chapter-art/` 100 枚 SVG；`mcu-book/tools/art_guard.py` 全绿（100 枚 0 违规）；`build_html.py:788` 内联 + 纯矢量硬门；站点接入（Session 22）、10 枚薄弱题花重绘闭环（Session 23） | 目录连 task.json 都没有，流程从未走；归档 |
| 10-27-book-interest-polish | 书级趣味性（叙事/互动/记忆点） | 已完成（待验收归档） | Session 32：批 1–10 全部闭环，「先猜」装置全书覆盖，13 门全过 | 用户验收批 10；归档 |
| 10-27-ai-dev-deepen | AI 辅助开发第六部 6 章 | 已完成（待 Phase 7 验收） | `docs/ai/00–05` 六章成稿；implement.md Phase 6 电池全 [x]；文字 R1–R4 + 题花 R5/R5b 维护轮全绿（implement.md 实施实录、Session 13–17） | Phase 7 用户过目（插图生动度 + 文字详细度）；归档 |
| 10-25-book-production | 16 开印前 PDF + EPUB3 | 进行中 | 印前 PDF 完成：`mcu-book/dist/mcu-deep-book-print.pdf` 1174 页、13 门全过（Session 32） | **EPUB3 整体未做**（无 `mcu-book/build_epub.py`、dist 无 .epub）；A4 旧版未退役（`dist/mcu-deep-book.pdf` 仍在）；P7 收口（文档口径、spec 落契、G5 复核门） |
| 10-25-bmsz-validation-depth | BMS-Z 验证纵深 | 已完成（待归档） | `research/verification-log.md` 标"P8 收口证据"；24 项本地门禁全 pass（Session 12） | 归档 |
| 10-22-video-v2-remaster | 视频 v2 重制 + 全平台换新 | 进行中 | Wave A/B 完成；Wave C 五集（s14/s16/s2/s4/s7）已渲染：`video/out/<ep>/` 均有 bilibili.mp4 + douyin.mp4 + 四平台封面 + 发布文案；Session 32 明确"转入 Wave C，首集 s2-rcc" | Wave C 双平台 check 抽检；17 集全平台换新发布（B站换源/抖音删除重投等 Phase 0 决策的执行面）；implement.md 复选框全空需刷新 |
| 10-28-social-video-ai-tools | AI 视频工具清单社媒成片 | 进行中（近完成） | `video/out/ai4fw/` 已有 bilibili/douyin/wx 三条成片 + 封面；`video/publish/copy-ai4fw.md` 文案在 | 小红书封面/笔记文案缺（out 里只有 发布-douyin.md）；doctor→finalize 全绿记录未见；发布（PRD 约定不自动发布，等用户） |
| 10-26-oss-influence | 开源项目地图补全书项目层 | 未开始 | 仅 `research/verified-oss-projects.md` 调研；`docs/` 全站无"开源项目地图"内容 | P1 附录 B 落地及后续 P2–P4；prd 两个开放问题未拍板 |
| 10-16-e04-board-measurement | E04 优先级反转上板实测填表 | 未开始（阻塞：需硬件） | `docs/lab/e04-priority-inversion.md:101-108` 实测记录表四行仍全空 | 四臂上板跑 scene 6、串口取数回填；顺手修 `code/rtos/01-freertos-lab/main.c:2` 过期注释 |
| 10-16-bili-season-after-unlock | B站合集建集挂载 | 已完成（剩用户手工项） | Session 31：新合集 9435811 建成、18 条挂载、公共端逐条回显通过 | 用户在抖音 App 手工置顶 19 条（清单 `.temp/douyin-run/待置顶清单.md`，工具无法代点）；归档 |
| 10-06-b3-linker-script | 链接脚本章 | 已完成（未归档） | `docs/build/03-linker-script.md` 成稿在册 | 无 task.json/prd，补归档或直接删目录 |
| 10-06-gd32-tracks | GD32 双系路线 | 已完成（未归档） | `docs/gd32/00–09` 十章 + index 成稿，G/V 两线齐 | 同上：无 task.json，补归档或清理 |

## 建议的处理顺序

1. **先清"已完成待归档"的一串**（de-ai-polish 父子三个、chapter-art、book-interest-polish、bmsz、bili-season、b3-linker-script、gd32-tracks）：实物验收早就全绿，只差用户点头和 `task.py archive`。不清掉，任务列表会持续虚报"在途"，干扰后续判断。
2. **video-v2-remaster Wave C 收尾**：五集成片已在盘上，离"全平台换新"只差 check 抽检和发布执行，是当前唯一有明确下一步动作的在途任务，Session 32 已点名接续。
3. **ai4fw 补小红书件后交付验收**：渲染大头已完成，补一条竖版笔记文案 + 封面即可关单。
4. **book-production 的 EPUB3**：书侧唯一真空缺，且 cover-art 的"EPUB 封面同步"验收挂在它上面；印前 PDF 的工艺（字体子集、paged.js 管线）都已成熟，EPUB 是独立新增工作，适合单开一轮。
5. **E04 上板实测**排在有整块时间 + 板子在手时做，纯硬件活，不挡别的线。
6. **oss-influence** 优先级最低：属增量增强，且 P3 放哪一部、中文社区是否纳入两个开放问题需要先拍板，建议在 EPUB 之后再启动。
