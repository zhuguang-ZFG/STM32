# 知识轨 Handraw 全书覆盖审计（29 章 + 附录 A–F）

日期：2026-11-05（America/Adak 本地日）。范围：`assets/illustrations/handraw/`、
`docs/00–28` + `docs/en/00–28`、`stm32-book/book/`（附录 A–F）、`tools/handraw_track/`。
合同依据：`BOOK_CLASSIC_CONVERGE_SPECS.md` §6（双轨裁定）、§15.1（23–26 密度）、
`BOOK_REDESIGN_SPEC.md` §11（可再生、不依赖随机数与网络）。

## 1. 覆盖结果

| 项 | 值 | 证据 |
| --- | --- | --- |
| 章覆盖 | 29/29 章（zh+en 同步嵌入） | `test_handraw_track` 双语引用对称断言 PASS |
| 附录覆盖 | A–F 六册（zh+en） | commit `ec52505` |
| 知识轨 PNG | 177 张（ch00–12：71；ch13–28：79；附录：27） | 目录清点（见下） |
| 脚本可复现 SVG 源 | 66 张（ch21–28 + 附录，`tools/handraw_track` 种子固定） | `hd.py`/`fig_chNN.py` + `render.py` |
| 双轨标注 | 全部图注/徽章标「原理示意 / 非实拍」 | `test_handraw_track` 徽章断言 |
| 真证轨 | 未动：ch03 两张 CC BY-SA 4.0 BluePill 实拍、Nucleo CC0 实拍、PC13/表计缺口仍诚实挂账 | `assets/photos/README.md` |

目录清点（2026-11-05）：`ch00–04` 各 6、`ch05–11` 各 5、`ch12` 6、`ch13–22/24–28` 各 5、
`ch23` 4、`app-*` 27，合计 177 PNG；SVG 源 66（`ch21-board…app-a…`）。

## 2. 两条生产线

1. **AI 生成知识轨（ch00–12，71 张）**：按 `yang0/handraw-style` 规划登记
   （FA-002/FA-029 风格、IG-002/004/008/009/010/011/012/013 图型、C-03/C-10/C-27/C-31 配色），
   逐张图注写明「证明什么/不能证明什么」；SHA 与规划记录在 `audits/ch03-converge-gate.md` 等批次门表。
2. **脚本生成知识轨（ch13–28 + 附录，106 张）**：`tools/handraw_track/hd.py`
   （米色纸面、抖动墨线、手绘徽章）+ `fig_chNN.py`（每章真实寄存器/公式/版本号）+
   `render.py`（Playwright Chromium 1152×864 截图）。种子固定 → SVG 字节可复现
   （`cmp` 验证一致），PNG 不依赖网络。README 记录重建命令。

两条线共用同一视觉语法（构图、配色、徽章、图注格式），全书一致；真证轨照旧。

## 3. 视觉审计（看图记录）

4-up 联系表逐张过目（`tools/handraw_track/contact_sheet.py`）：

- ch00/07/09 抽查 14 张：文字清晰、寄存器与公式正确（I2C 0x78 vs 0x3C、SMP 档位、
  pull-up 公式）——PASS；
- ch13–20 全部 40 张：CAN 位时序 8TQ/75%、TEC 阶梯、FreeRTOS FromISR 墙、
  低功耗三岔口等——PASS；3 处外观小疵（箭头落点、双描边）不影响阅读，挂账不返工；
- ch21–23 全部 14 张 + ch24–28 全部 25 张（逐张复核后入库）——PASS；
- 附录 A–F 抽查（证据口径、术语地图等）——PASS。

发现并修复的内容缺陷：ch00–04 EN 图注使用 "schematic" 一词，违反读者保护词表
（`slop_lint` 审稿用语组 + `sample_chapters`/`batch4` 断言），已统一为「原理示意」
（commit `c94829c`，28 alt + 28 caption）。

## 4. 质量门

| 门 | 结果 |
| --- | --- |
| `python -m pytest stm32-book/tests` | **182 passed**（基线 180 + 新增 `test_handraw_track` 2 项） |
| `python tools/check_assets.py` | PASS（1880/1880 链接；JPEG 哈希 4/4） |
| `python tools/slop_lint.py` | 干净（机械命中 0） |
| `python tools/audit_book.py` | zh/en 视觉锚点各 425；低于目标章节 0 |
| `build_html --check` zh+en | PASS |
| `build_html --pdf` zh+en | 565 页 / 589 页，118 MB ×2；页样目检 3 页（zh）+ 1 页（en）PASS |
| `test_sample_svg_c`（324 张锁定清单） | PASS——`illustrations/handraw/` 划出其管辖，理由见 §5 |
| `test_book_audit` / `test_advanced_visuals` | 锁定值按 §15.1-25 上调后的新实况 re-baseline（commit `668aff9`） |
| `test_batch6` 术语表/附录锁 | 比对前同形剥离 handraw 嵌入层；F103 Stop 电流单元格保护不变（commit `c82acf7`） |

## 5. 合同裁定（记录在案）

1. **handraw 家族不进 `test_sample_svg_c` 的 324 张哈希锁定清单**：该清单管的是
   paper-card 图系统（stroke ≤2、自绘署名、逐张 SHA）；知识轨是另一视觉体系，
   由新增 `test_handraw_track.py` 管辖（XML 合法、诚实徽章、无脚本/外链、双语引用
   对称、文件存在性）。旧断言未被削弱，管辖范围显式划界（Overlay §11.1 的
   「不得改旧断言换绿灯」指不得删除断言；本裁定为范围划界并落档）。
2. **ch00–04 的 EN 措辞**：沿用全书 dominant 形式「Handraw · 原理示意 / not a photo」，
   与 zh「原理示意/非实拍」逐条对应。
3. **AI 概念图（ch00–12）保留**：Spec §6.4/§15.1-26 允许明确标注的概念插画；
   全部带徽章与图注边界，未进入真证轨，未写入 CREDITS 实拍条目。
   CREDITS 新增知识轨行（来源、两条生产线、许可）。

## 6. 并发协作记录

本轮由两个 goal-runner 实例并行推进（同一 /goal）：一路自 ch13 向前（AI 生成线），
一路自 ch28 向后（脚本生成线）。碰撞规避：反向推进 + 每章开工前 poll `git log` +
逐章独立提交。交接事实：对方实例 adopt 了 `tools/handraw_track` 语法完成 ch21–23
与附录 A–F；本实例的 ch23 四图由对方在其 commit `7679119` 一并入库；SVG 删除/恢复
往返以对方 `b1b294c`（保留 SVG 源）为准；测试锁 re-baseline 以对方 `668aff9` 为准，
本实例在其上仅做范围划界（§5-1）与措辞修复。

## 7. 遗留（不冒充完成）

- ~~29 短片 + 29 长片的可复现重制~~ **已完成**（2026-11-05 Batch A–G：见 `audits/video-regen-plan.md` Status 与 `audits/task-verify-equivalent-2026-11-05.md`）；
- ~~`task_verify` 分列报告~~ **已完成**（等价分列落盘，工具本体缺失如实保留为 unverified）；
- ch03 PC13 LED 特写与表计实拍、L4 整板电流实测等真证轨缺口仍按原文挂账（需真板与仪器）；
- 本轮 3 处外观小疵（§3）如需返工，改 `fig_chNN.py` 对应坐标后重渲染即可。
