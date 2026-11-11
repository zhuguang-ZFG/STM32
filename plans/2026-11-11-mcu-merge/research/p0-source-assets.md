# P0 外部来源（D:\Users\mcu）未跟踪/忽略资产盘点

日期：2026-11-11（Asia/Shanghai）
范围：`git -C D:/Users/mcu ls-files --others --ignored --exclude-standard`（64673 项）+ `--others --exclude-standard`（2 项）。本文件仅分类与风险标记，不迁移、不删除、不纳入目标仓库。

## 总览（按顶层目录计数，忽略/未跟踪总计）

| 顶层 | 数量 | 初步分类 | 说明 |
|---|---:|---|---|
| `code/` | 25649 | 可再生（需工具链） | 大量 `.obj/.o/.a/.elf/.map/.bin/.pyc` 等构建产物/缓存；源码与工程应由已跟踪内容提供，产物可在对应工具链环境重建。 |
| `video/` | 15088 | 混合：可再生缓存/构建输出，需复核母版 | 含 `video/.cache/tts/*.mp3`（TTS 缓存，按脚本/服务可再生）、`video/out/**` 与渲染中间物（构建输出，耗时可再生，若依赖外部 TTS/素材需确认）；未发现未跟踪非忽略的视频工程源文件差异证据。 |
| `node_modules/` | 10331 | 可再生 | 依赖目录，按 lock `npm ci` 重建；禁止整树导入。 |
| `.temp/` | 9976 | 临时/可再生构建产物（含需复核项） | 大量临时 PDF/字体副本/探针输出；含 `.temp/v2-baseline-20261022/masters/*.mp4` 等历史基线媒体副本（见下）。 |
| `.superpowers/` | 1667 | 可再生/工作快照 | SDD/实现快照与任务基底副本，非权威源码；通常不作为资产迁移。 |
| `.trellis/` | 1009 | 混合：本地状态 + 参考资料（重点） | 含 `.trellis/ref/**` 参考 PDF（GD32/ST datasheet/RM 等），需单独归类。 |
| `docs/` | 665 | 可再生 | VitePress cache、生成数据等。 |
| `mcu-book/` | 60 | 构建输出/可恢复 | `dist/**/*.pdf`、字体子集、`__pycache__` 等；优先从构建或已发布 release 恢复/校验。 |
| 其他 | 少量 | 本地配置/缓存 | `.claude/.qoder/.pytest_cache/.ruff_cache/.perch` 等。 |

## 重点资产分类

### 1) 可再生（依赖/缓存/构建产物）
- `node_modules/`：按 `package-lock`/`package.json` 重装。
- `docs/.vitepress/cache/`、`**/__pycache__/`、`.pytest_cache/`、`.ruff_cache/`、`test-results/`：缓存/测试临时。
- `code/` 下编译中间物与二进制产物（`.o/.obj/.a/.elf/.map/.hex/.bin` 等）：在具备 ARM/GCC/ESP-IDF/构建脚本的环境可重建；环境缺失时标记 `BLOCKED`，不等同资产丢失。
- `video/.cache/tts/`：TTS 音频缓存，可按集数/脚本重生成（依赖 TTS 配置与服务可用性）。
- `video/out/**`、`mcu-book/dist/**`：渲染/排版产物；可从源码与构建链路重生成，或与已发布制品哈希比对后恢复。

### 2) 可由公开资料或已发布制品恢复（需按需获取/核对）
- `.trellis/ref/st-docs/*.pdf`（如 `rm0090.pdf`, `stm32f407vg-ds.pdf`）、`.trellis/ref/gd32/*.pdf`、`.trellis/ref/f407-ds.pdf`：厂商公开文档镜像/参考资料。**不建议整树搬入目标仓库的通用资产区**；保留本地引用或记录来源/版本，按需重新下载并核对。
- `mcu-book/dist/language-release-20261106/*`、`mcu-book/dist/*.pdf`：若与 GitHub Release/发布记录一致，可从发布产物恢复；迁移时以发布版本与哈希为准（P4/P5 核实）。

### 3) 不可再生风险 / 需人工复核（未确认）
- `.temp/v2-baseline-20261022/masters/**/*.mp4`（bilibili/douyin 母版样本，位于临时目录）：若无其他权威母版或发布源对应，存在丢失风险；执行前需与目标仓库/发布存档/原始工程对照确认来源与必要性。
- `.temp/backup-c2/douyin.mp4`、`.temp` 中零散音视频/字体下载件（如 `NotoEmoji.ttf` 等）：多为临时下载或中间产物，但个别可能缺少可追溯来源；逐项确认后再决定保留/丢弃，不默认迁移。
- `.perch/PERCH.md`、`.perch/mcp.json`（未跟踪、非忽略）：小型本地状态/配置，是否为后续工具所需需人工判断；当前不视为仓库内容。

### 4) 明确不整树导入
- `node_modules/`、`.temp/`、`.superpowers/` 快照、各类 cache/out 中间目录：遵循计划约束，不因“存在于来源目录”而整树搬入目标 `mcu/`。

## 结论与阻塞
- 已完成来源侧规模与类别盘点（证据：本次 `git ls-files --others --ignored --exclude-standard` 分类统计）。**未发现**可直接证明“仅存在于忽略区且无任何可恢复途径的唯一视频母版/硬件证据文件”的确证记录，但 `.temp` 内历史 master 样本与 `.trellis/ref` 文档需在 P4/P5 前按需复核与留痕。
- 依赖/缓存/构建产物不构成 Git subtree 内容迁移阻塞；不可再生风险项需在后续发布与资产收口阶段显式决策，不在本轮静默丢弃或复制。
