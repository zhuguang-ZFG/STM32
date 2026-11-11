# P4 集成验收记录（AC1–AC7）

日期：2026-11-11 · 候选仓库 `D:\Users\STM32-mcu-merge-p1` · 分支 `feat/mcu-merge-p1` · 候选提交 **`f6b039b6`**（P1 `2e965db4` + P2 `27757966` + P3 `f6b039b6`，PR #106）

环境：Windows 10.0.26200 · node v24.14.0 / npm 11.9.0 · Python 3.13.14 · ruff 0.15.21 · arm-none-eabi-gcc 10.3.1（=CI 10.3-2021.10）· Chromium（Playwright 1.63）

## AC 状态总表

| AC | 状态 | 证据 |
|---|---|---|
| AC1 基线与祖先 | 通过 | p0-gate.md：`merge-base --is-ancestor cf16153 HEAD` RC0；baseline.json 快照；目标 92fc917 → 候选 f6b039b6 |
| AC2 双书维护入口 | 通过 | P1 提交：STRUCTURE/AGENTS/README；p1-evidence.md |
| AC3 站点身份单源 | 通过 | P2 提交：site-config.mjs + 9 消费方；npm test 137；p2-evidence.md |
| AC4 Pages 组装 | 通过 | P3 提交：assemble-pages + mount-smoke；真实产物 staging 655 文件/10015 引用；冒烟 12/12；p3-evidence.md |
| AC5 两侧全部门 | 本地通过 / CI 待跑 | 下表全绿；ESP32 矩阵 + 双语 PDF 版式审计记 CI-pending（PR 合入后 run 留证） |
| AC6 任务上下文可解析 | 通过 | p1-evidence.md：23 活动任务/256 file 条目 MCU 根可解析；skills 832 文件受控纳入 |
| AC7 字符串分类纪律 | 通过 | p2-string-classification.md：A/B/C/D 四类全量处置；`.trellis` 零改写 |
| AC8 发布关闭 | 待 P5 | 前置项见下「P5 发布前置」 |

## 门禁明细（全部在候选提交 f6b039b6 工作树执行）

### STM32 书（cwd=仓库根）

| 命令 | 结果 | 退出码 |
|---|---|---|
| `python tools/slop_lint.py` | 干净，无机械命中 | 0 |
| `python tools/check_assets.py` | SVG 566/566、GIF 23、MP4+SRT 29 章、Wokwi 6、Renode 2、引脚图 3、示例工程、照片 5/5；**链接 2331/2331**（mcu/ 归 MCU 门禁管辖，见下「工具域调整」） | 0 |
| `python -m pytest stm32-book/tests -q` | **197 passed**（8m41s；含 slop/AI 味门——修了自家计划文档 2 处 `结论：` 标签） | 0 |
| `python stm32-book/build_html.py --check` | 整书契约 PASS（zh，29 章 158.8 MB） | 0 |
| `python stm32-book/build_html.py --lang en --check` | 整书契约 PASS（en，29 章 159.0 MB） | 0 |

说明：`stm32-book/` 与 `tools/` 自上次全验证提交 `b02cf3c` 以来仅 `slop_lint.py` 差分（按合并计划将 `mcu/` 纳入其跳过表），该工具本轮重跑通过；中英 PDF 生成与版式审计（`audit_pdf_layout`）为 CI 侧（book.yml），记 CI-pending。

### MCU（cwd=mcu/）

| 命令 | 结果 | 退出码 |
|---|---|---|
| `npm ci` / `npm test` | 137/137 | 0 |
| `npm run quality`（15 段） | 全链绿（含 vitepress build、seo、perf、a11y、pages、search、links、docs、nav、prose、reading、readme、anim:lint、projects） | 0 |
| `npm run test:browser` | 7 passed | 0 |
| `npm run anim:audit` | 111 张动画版式审计通过 | 0 |
| `node scripts/anim-audit.mjs --dir docs/public/figures --font-scale 1.08` | 46 张题图通过 | 0 |
| `python mcu-book/tools/art_guard.py --dir docs/public/figures` | 46 枚 0 违规 | 0 |
| `python -m unittest discover mcu-book/tests` | 59 tests OK | 0 |
| `python mcu-book/build_html.py --pdf` + `check_pdf.py` | 印前契约全过：1211 页、字体全可嵌（源文 860,380 字 / PDF 907,035 字 ×1.05） | 0 |
| `python mcu-book/build_print.py` + downloads 链 | downloads 7 文件 + `--verify` PASS | 0 |
| GNU `sha256sum -c SHA256SUMS.txt`（staging/mcu/downloads） | PDF 两项 FAILED = **Git for Windows 文本模式已知误报**（workflow 注释有载）；手工二进制比对 manifest 与实际一致（`874477ef…`）✓；权威口径由 CI（Linux）执行 | 0（手工口径） |
| `npm run firmware:check`（ARM-host） | All ARM/host projects passed；FreeRTOS V11.1.0 / RT-Thread sparse / CMSIS 双头 sha256 锁定全 OK | 0 |
| `ruff check --config mcu/ruff.toml mcu` | All checks passed! | 0 |
| staging 组装 + 终检 + 挂载冒烟 | assemble 655 文件/10015 引用；pages-check 136 页/8921 锚点；search-check 2124 标题；mount-smoke Chromium 12/12 | 0 |

### BLOCKED / CI-pending（诚实记录）

| 项 | 原因 | 处置 |
|---|---|---|
| ESP32 normal/faults 矩阵 | 本地无 ESP-IDF（CI 容器 `espressif/idf:v5.5.2`） | PR 合入后取 CI run 留证 |
| 双语 PDF 版式审计 `audit_pdf_layout` | 重构建（各 10+ min）+ Linux 字体度量口径 | CI 侧（book.yml） |
| 动画审计 Linux 字体度量 | 本地 Windows 度量已跑（111 张过）；CI 口径另跑 | CI 侧 |
| GNU sha256sum 权威口径 | Windows 文本模式误报 PDF（已手工二进制比对） | CI（Linux）run |

## 工具域调整（合并计划内决策）

- `tools/slop_lint.py`：已有 `mcu` 跳过项（92fc917 引入），MCU 文风由 MCU prose 基线自治。
- `tools/check_assets.py`：本轮为 **check_links** 增加同等跳过——mcu/ 链接基准是 MCU 站点根（`/stm32/07-usart.md` 形式），以仓库根拼路径必假败；其链接由 MCU 自有门禁在**构建产物**上校验（docs-check → pages-check → staging 资源落位 10015 条），严格性强于源码启发式。媒体类检查（SVG/GIF/MP4/照片）保留全仓覆盖。
- 该调整修后链接口径 2331/2331 全过；两类工具跳过表注释均说明理由。

## 工作区保护核查

- 候选 worktree：`git status` 仅剩本批证据文档与 check_assets 域调整（将随批 4 提交）。
- 主工作区（`D:\Users\STM32`）：用户 WIP 18 项（9 M + 9 ??）全程未触碰。
- `mcu/.trellis/` 历史任务文档：三个提交 diff 为零；jsonl 未改写。
- 全阶段新增修改均有解释：2 处预存内容缺陷修复（gd32 .md 链接、09-adc 寄存器表误链）+ 2 处证据文档措辞 + 1 处工具域调整。

## P5 发布前置（合入后、部署前必做）

1. **启用 Pages**：`has_pages=false`（gh api 仓库对象实测，owner token——排除「token 不可见」歧义）；`configure-pages` action 不会自动建站，须先在仓库 **Settings → Pages → Source = GitHub Actions** 完成启用（`build_type=workflow`），并回读 `GET /pages` 确认 `status=built`。
2. 部署前快照：记录旧 Pages URL 状态、来源仓维护状态、required checks（当前两分支均无保护规则）。
3. 只使用已验证候选产物；若合入产生新 SHA，核对最终树并重跑受影响 CI。
4. 发布后回读：首页/深链/搜索/动画/导读/下载哈希 + 根入口；旧仓 `/mcu/` 旧站处置决策（重定向或只读保留）。

## 批次 4 变更

`docs(merge): record integration acceptance and migration status` — 本文件 + p3-evidence 措辞修正（消除 checker 误报的链接形态）+ check_assets 链接域调整。
