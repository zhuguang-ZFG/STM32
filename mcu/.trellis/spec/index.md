# Trellis 规范索引：通往单片机之路

本仓库是 **VitePress 教学站点 + 嵌入式示例代码 + 成片生产线 + 整书生产**，不是 Web 应用。
规范按**真实维护面**分八层，每层都有自己的入口与质量检查：

| 层 | 目录 | 什么时候读 |
|---|---|---|
| 站点与内容 | [docs-site/](docs-site/index.md) | 改 `docs/` 页面、`config.mts`、主题、动画、图片、工程登记与站点质量门前 |
| 整书生产 | [book/](book/index.md) | 改 `mcu-book/` 的整书 HTML/A4/印前 PDF、manifest、附录、字体、下载包前 |
| 公共固件 | [firmware-common/](firmware-common/index.md) | 改 `code/common/`、`scripts/device-console.py`、`code/c/` 或 `code/toolchain/` 取证前 |
| STM32 固件 | [firmware-stm32/](firmware-stm32/index.md) | 改 `code/stm32/` 下寄存器级工程前 |
| ESP32 固件 | [firmware-esp32/](firmware-esp32/index.md) | 改 `code/esp32/` 下 IDF 工程前 |
| RTOS | [firmware-rtos/](firmware-rtos/index.md) | 改 `code/rtos/` 的内核移植、场景、配置、上板实验前 |
| GD32 | [firmware-gd32/](firmware-gd32/index.md) | 改 `code/gd32/` 工程或 `docs/gd32/` 的 G/V 篇事实前 |
| 成片生产线 | [video/](video/index.md) | 改 `video/src/`、`episodes/`、封面/发布包或动 `video/out/` 前 |

## 修改路径 → 必读层

| 修改路径/行为 | 必读 |
|---|---|
| `docs/**`、`docs/.vitepress/**`、动画/架构图/导读资产 | docs-site；`code/` 路径与工程 ID 对账读 quality-contract |
| `code/common/**`、`scripts/device-console.py` | firmware-common；logger 另读 [logger-contract](docs-site/logger-contract.md) |
| `code/c/**`、`code/toolchain/**` 的 probe | firmware-common/probe-contract；不把宿主机结果当上板 |
| `code/stm32/**` | firmware-stm32；共用协议读 common，RTOS 场景读 rtos |
| `code/esp32/**` | firmware-esp32；共用代码读 common，内核版本口径读 rtos |
| `code/rtos/**` | firmware-rtos + 对应板级层；IDF 内置内核与上游 V11 不混读 |
| `code/gd32/**`、`docs/gd32/**` | firmware-gd32；V 篇只写文档事实，当前无可构建的 VF 工程 |
| `mcu-book/**`、`docs/reference/glossary.md` | book；正文事实仍归 docs-site |
| `video/src/**`、`video/episodes/**`、`video/out/**`、`video/publish/**` | video；平台动作另进 `.agents/skills/video-release/SKILL.md` |
| `code/projects.json`、`.github/workflows/**`、`scripts/project-catalog.mjs` | docs-site/quality-contract + 对应固件层 |

## 全局纪律

- 内容质量的最高法是仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)（四件套、风格契约、动画/图片规范）；spec 只补充"AI 在此仓库怎么干活"。
- 验收构建：`npm run docs:build`（死链检查开启，必须零错误）。
- 禁占位：正文不得留 `TODO`、`待补充`、`placeholder`；`docs/lab/template.md` 的教学元说明是唯一例外。
  代码块里的教学占位必须明确标成示例，不得让读者以为产物已存在。
- 事实纪律：寄存器地址/引脚号必须有出处（RM0090 章节号/datasheet/官方原理图/板厂 wiki），
  写不进正文的标注"以 XX 为准"，禁止编造。历史任务中的测量记录保留日期与范围，不改写成当前事实。
- 唯一维护位置：同一事实只在一层写完整合同，其他层用链接引用；发现重复先删副本再加新内容。
- 验证分级：命令退出码 0 不等于通过；打印"跳过/降级"的段没有证据。上板状态只由实测记录支撑。

## 各层入口与质量门

每层 index 都包含"动手前必读"和"质量检查"；常用总门：

```bash
npm run docs:build        # 站点装配 + 死链
npm run quality           # 站点/元数据/CI 静态门（不含 video、book、firmware 全量）
npm run test              # Node 单元回归
npm run firmware:check    # 非 ESP 固件工程 + 场景/变体 + 登记 probe
npm run book:check        # 整书 HTML 装配契约
npm run video:test        # 视频产线单元/夹具；单文件用 node --test
```

门禁集合与跳过语义见 [quality-contract](docs-site/quality-contract.md)；不要把本索引当命令清单的替代。
