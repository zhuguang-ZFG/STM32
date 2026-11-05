# Spec 覆盖审计

核对日期：2026-11-05。基线分支 `feat/video-v2-remaster`，HEAD `8b992fb`。本审计依据工作树源码、规范、测试和 workflow；没有运行产品全量回归，也不以历史日志证明当前产物有效。

## 维护面与现有覆盖

| 维护面 | 当前规范 | 核对来源 | 判定 |
|---|---|---|---|
| 站点、正文、动画、架构图 | `.trellis/spec/docs-site/` 的 structure/content/animation/architecture-diagram | `docs/.vitepress/config.mts`、`CONTRIBUTING.md` | 已有覆盖，保留结构与事实纪律 |
| 导读与金句卡 | `.trellis/spec/docs-site/presentation-assets.md` | `scripts/book-guide/`、`scripts/social-cards/`、`tests/book-guide.test.mjs` | 已有完整合同，其他层引用即可 |
| 质量与元数据 | `.trellis/spec/docs-site/quality-contract.md` | `scripts/project-catalog.mjs`、`scripts/check-firmware.mjs`、`.github/workflows/quality.yml` | 已有合同，工程字段与矩阵签名需更新 |
| STM32 | `.trellis/spec/firmware-stm32/index.md` | `code/stm32/`、`code/stm32/platform/` | 基础规则齐，缺公共模块与 RTOS 路由 |
| ESP32 | `.trellis/spec/firmware-esp32/index.md` | `code/esp32/`、quality workflow 的 esp32 job | 基础规则齐，需精确版本、变体构建与跨层路由 |
| 离线书与印前 | 质量合同中的少量条目 | `mcu-book/build_html.py`、`build_print.py`、`check_pdf.py`、`publish_downloads.py` | 缺少本层入口与完整生产契约 |
| C、工具链和通用行为取证 | 分散在章节与 README | `code/c/`、`code/toolchain/`、`code/common/behavior/` | 缺少工具链、证据等级与跳过语义合同 |
| 共用协议、健康监测和 logger | docs-site/logger 覆盖 logger | `code/common/reliability/`、`code/common/logger/`、`scripts/device-console.py` | logger 已覆盖；底层协议与 CLI 缺正式规范 |
| RTOS | 散见 content 与质量合同 | `code/rtos/`、两种 RTOS 的 Makefile | 缺内核版本、端口、场景及参数缓存边界 |
| GD32 | 无独立层 | `code/gd32/01-rcu-clock/`、`docs/gd32/` | 缺 GD32F4/GD32VF 的边界与未核验口径 |
| 视频渲染与发布包 | video/layout-contract、v2-contract | `video/src/cli.mjs`、`package.mjs`、`video/tests/` | v2 入口缺失，生产命令描述陈旧 |
| 平台发布 | 本地 video-release skill 与 publish 台账 | `.agents/skills/video-release/SKILL.md`、`video/publish/repost/` | 保持其权威；spec 只补边界指引 |

## 缺口登记

优先级表示规范失真可能造成的影响，P1 为接口/产物/兼容风险，P2 为维护可发现性与证据规范。编号在设计、实施与后续报告中保持不变。

| 编号 | 优先级 | 证据与具体缺口 | 目标文件（均相对 `.trellis/spec/`） | 完成断言 |
|---|---|---|---|---|
| S01 | P1 | `index.md:3` 只声明四层；`video/index.md:6` 的表未登记已存在的 v2 合同 | 总索引、video/index、各新增层 index | 总入口可走到所有规范；v1/v2 阅读触发明确 |
| S02 | P1 | `docs-site/quality-contract.md:17` 矩阵仅写 path/target；`scripts/project-catalog.mjs:37` 实际还输出 variant/defaults；同文件第 21、22 行接受 variants 和三种 scenes 形状 | docs-site/quality-contract.md | 准确描述 `{include:[{path,target,variant,defaults}]}`、场景数组、构建变体、错误分支及 sdkconfig 隔离 |
| S03 | P1 | `package.json:44-46` 中 book:html 与 book:pdf 使用不同构建器；书籍尚无 spec 层 | book/index.md、book/build-contract.md | 单文件 HTML、A4 PDF、印前 PDF、下载包各有真源、输出和匹配检查 |
| S04 | P1 | `mcu-book/build_print.py:845` 有 sample/bleed/html/fonts 等入口；`check_pdf.py:583` 位图预算按注册架构图计数；现有规范未覆盖印前冻结/正文保护 | book/print-contract.md；引用 docs-site/architecture-diagram | 明确矢量与合法位图来源、字体、两遍索引、正文保护及真正的 PDF 检查目标 |
| S05 | P1 | `code/common/reliability/README.md` 已描述 74B wire、CRC、状态码与 CLI 退出码；现有 logger 合同只覆盖其上层 | firmware-common/reliability-contract.md、firmware-common/index.md | 从生产头文件/CLI 核实协议、超时、错误、并发归属、暖复位记录与序列化边界 |
| S06 | P2 | `code/c/03-volatile/probe.sh:21-24` 缺交叉工具时只跳过交叉段；`code/toolchain/03-linker/probe.sh:20` 接受 ARM_PREFIX；取证不是上板结果 | firmware-common/probe-contract.md | 按实际脚本登记工具/env、输出、版本、跳过及可支持的结论，不凭退出码零宣布全证据通过 |
| S07 | P1 | `code/rtos/01-freertos-lab/Makefile` 接受场景 1–6；RT-Thread 仅 1/6，USE_MUTEX 的目录处理也不同；`content.md:32` 已区分上游 FreeRTOS 与 IDF SMP | firmware-rtos/index.md、firmware-rtos/kernel-contract.md；原固件层引用 | 两种内核、版本/缓存来源、配置宏、场景/参数/构建目录逐项准确；未固定来源如实记录 |
| S08 | P2 | `code/gd32/01-rcu-clock/README.md` 明列 FMC 等待、内存布局及 CK_OUT0 待核验；教学还包括另一 ISA 的 GD32VF | firmware-gd32/index.md、firmware-gd32/build-contract.md | 区分已有 GD32F4 工程与 GD32VF 章节，理论与实测分开，不虚构 VF 工程 |
| S09 | P1 | `video/index.md:16-23` 仍推荐 `.temp/` 补封面；`video/src/cli.mjs:604/640` 已有 cover/pack；`v2-contract.md:247` 的追加文件命令仍会保留 npm 脚本的 glob | video/index.md、video/build-package-contract.md、video/v2-contract.md | 正式生产命令、四平台母版映射、只读/写入边界清楚；单文件测试直接用 node --test；历史计数不充当前门禁 |
| S10 | P2 | 总索引的占位禁令未注明模板例外，而 content 已注明；guides 的视频数量是历史快照，现有层入口缺统一阅读触发和质量入口 | 总索引、guides/index.md、既有与新增层 index | 模板例外一致；指南指向正式合同；所有层有动手前必读和按变更选择的检查，不复制合同细节 |

## 需单独跟踪的实现疑点

### F01：CI 的 PDF 生产与校验目标不匹配

- `.github/workflows/book.yml:44/47` 与 `.github/workflows/quality.yml:51/55`：先执行 `build_html.py --pdf`，随后执行无参数 `check_pdf.py`。
- `build_html.py` 的 A4 输出是 `mcu-deep-book.pdf`；`check_pdf.py:41/638` 默认读取 `mcu-deep-book-print.pdf`，其验收基于印前格式。
- `package.json` 的 `book:pdf` 才调用 `build_print.py`。因此不能在规范中把现有 workflow 描述为已经构建并验证印前产物。
- `publish_downloads.py:28/88` 从 build_html 导入 OUTPUT_NAME/PDF_NAME，当前打包的是离线 HTML 与 A4 PDF；印前 PDF 尚不属于该默认下载包。
- 本轮只确认静态接口矛盾，未触发远端 workflow，不能声称某次 CI 已失败。后续补规范时记录真实状态；若要修 CI，单列范围、确认构建耗时与发布目标后再做，不把“修改默认 PDF 路径”当成足够修复。

### F02：FreeRTOS 场景 6 的 USE_MUTEX 构建目录

- FreeRTOS Makefile 的 `BUILD := build/scene-$(DEMO_SCENE)` 未把 USE_MUTEX 编入目录，而 RT-Thread 添加 `-mutex` 后缀。
- 这是静态缓存风险信号，尚未跑 0→1→0 切换试验。规范应按实际行为记录适用参数与验证边界；不能宣称“所有参数变更均自动隔离”。若证实缓存错误，再另列修复。

## 保留边界

- `docs-site/logger-contract.md` 保留原路径；新增 common 入口链接到它，避免旧任务引用失效。
- `docs-site/presentation-assets.md` 已覆盖导读/卡片，不因补计划重做设计和产物。
- video v1 夹具、已发布视频、正文与硬件状态不随规范整理改变。
- `11-02-skill-remaster/specs.md` 是既有历史计划且有用户未提交修改；本轮不追加、不重排、不回写完成状态。
- 未来目标文件在本报告中用代码路径表达，不用指向尚不存在文件的 Markdown 链接；实施时文件和索引同批补齐。

## 规划环境说明

`trellis-brainstorm` 的用户级目录为空，已从本机 Trellis 安装包读取 codex 模板：`C:/Users/zhugu/AppData/Roaming/npm/node_modules/@mindfoldhq/trellis/dist/templates/codex/skills/brainstorm/SKILL.md`。只读取模板，没有重装技能或更新框架。
