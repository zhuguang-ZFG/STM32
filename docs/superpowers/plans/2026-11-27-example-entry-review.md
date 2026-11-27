# 配套工程入口与现行章号核对

范围：`README.md`、`examples/README.md`、`docs/appendix/B-project-index.md`；全仓链接扫描后扩展到 9 个示例 README 的章首链接与 4 份速查表的失效译文链接 / HAL 目录锚点。

## Sepia review（先审后改）

类型：中文技术教程索引。Loaded：Sepia professional-pass、tech-articles、discourse-pass §1–3、style-pass、zh、model-fingerprints 的 GPT prose layer。作者模型未知；执行模型 GPT-6（子版本未知）。Prose layer：author=none，executor=prior。参考语域：现有 GPIO、UART DMA 与 DMA memcopy README；这些文件的作者身份不作推断。

| 原文证据 | 缺陷 | 修订 |
| --- | --- | --- |
| 附录 B「15 条」「14 例程 + 补登」 | 实际有 16 个示例目录，漏登 dma-memcopy | 两份索引补齐 DMA 内存搬运；门户补齐 motor-dc-speed |
| 示例首页「这四个目录直接走各自的 CMake 入口」 | exti-key、timer-pwm、dma-memcopy 已提供完整固件工程，仍被导向 CubeMX | 按 CMakeLists、presets 与 README 分列 7 个完整固件入口、1 个仅宿主入口、8 个待集成源码 |
| 门户 UART「06 / 10」、USB「14」等 | 使用合并前章号，指向当前书中的其他主题 | 按现行章文件与示例总索引核对章号 |
| 附录 B「D 尚未链接」「落位后链接」 | 编写过程残留，两个附录现已存在 | 改为实际站内链接 |
| 示例首页「共享变量加 volatile」「外设一律 3.3V」 | 把编译器访问约束当作同步规则；电机供电与 IO 电平被混为一项 | 写明有界 ISR 与共享访问方式；供电按板卡、模块及电机档案核对 |
| 附录 B 电机只列第 37 章与开环 | 工程已有 dc-openloop、dc-encoder、dc-speed 三个固件预设 | 登记第 36–39 章及三种构建入口，保留硬件待测 |

Failed：#3 relevance（编写过程残留）、#5 specificity（计数、章号和构建入口不符）。Style scan：其余语气中性，表格适合目录比较；没有需要整段风格重写的节奏问题。Passed：1、2、4、6、7、8、9、10。Verdict：isolated hits → refactor。

Deferred：真实板卡下载、波形、吞吐、编码器方向与闭环稳定性仍待硬件取证。Protected：固件代码、依赖 SHA、现有测量数字和历史任务状态；链接只按迁移表校正，本轮不将宿主测试写成板上通过。

## 核对依据

- `examples/*/README.md` 的目录枚举：16 个；门户表、示例表与附录表逐一对照。
- 7 个完整固件入口均有 CMakeLists 与固件 preset：GPIO、EXTI、PWM、UART、DMA memcopy、电机、SPL；FreeRTOS 的 CMake 在非宿主模式明确报错。
- `mcu/code/projects.json` 保持 47 项：host-probe 22、host-make 1、esp-idf 10、arm-make 14。
- DMA memcopy 的 1024 个字 / 4096 B 与 LED 结果取自工程 README；电机三种固件预设取自其 README 与 CMakePresets。
- 全仓 `book.md_links` 首次扫描：139 个 Markdown 文件、19 处问题。按 `book/data/mapping.tsv` 修复 10 个旧章节链接，移除 4 个已退役的英文译文入口，修复 5 个 HAL 目录锚点。
- 链接修复复用开放 PR #180 的提交 `9e75c016` 中示例 / 速查表补丁，以及 PR #183 的提交 `c568b1f6`；核对后仅采用本轮相关路径。ADC 的两条链接另按迁移表修正。没有覆盖这些 PR 之外的固件改动，也不将其历史状态改为通过。

删除检查：删去「尚未链接」「补登」等已过期过程描述；新表仅保留会改变读者构建操作的信息。回退检查：保留既有接线、硬件待测和不能推出的验收边界，未为统一句式重写其他条目。

## 本地验证

- 三份示例表与目录逐一比较：16 个例程各出现一次，构建分类覆盖全部目录；7 个固件入口均有相应 CMake 预设。
- `python -m book.md_links`：139 个 Markdown 文件，0 个问题（修前为 19 个）。
- `python -m book.checks` 与 `python tools/slop_lint.py`：通过。
- `npm.cmd run docs:build`：通过；仅有既有的 ld 高亮回退和 bundle 体积提示。
- 本轮只改入口文字和链接，固件、测量数据与质量门未改动。
