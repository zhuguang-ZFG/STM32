# 规划与实施验证

日期：2026-11-05。规划交付之后，用户要求"执行 spec 计划"；以下同时记录规划验收与 B1–B6 实施结果。
未执行的检查单独列出，不把跳过或未跑写成通过。

## 实施执行（2026-11-05）

| 检查 | 方法 | 结果 |
|---|---|---|
| 任务启动 | `python ./.trellis/scripts/task.py start spec-completion-plan` | `planning → in_progress`；来源为本会话 |
| 规范本地链接 | Python 剥离围栏/行内代码后，按父目录解析所有 `](...)` 相对链接 | 0 断链（站点绝对路径与教学示例不计） |
| 文档卫生 | `git diff --check`；新增文件行尾空白扫描 | 通过；仅 `firmware-esp32/index.md` 有既有 CRLF 提示，无空白错误 |
| 工程登记 | `npm run projects:check` | 47 个工程通过 |
| 工程矩阵 | `node scripts/project-catalog.mjs --matrix` | 输出确为 `{include:[{path,target,variant,defaults}]}`；normal/faults 行与契约一致 |
| 登记的单元测试 | `node --test tests/catalog.test.mjs tests/device-cli.test.mjs tests/logger-cli.test.mjs` | 8/8 通过 |
| 整书装配 | `npm run book:check` | PASS；94 章、题图 94/94、HTML 10,635,199 字节 |
| 印前 PDF | `python mcu-book/check_pdf.py mcu-book/dist/mcu-deep-book-print.pdf` | 13/13 项通过；1193 页；源文 856,071 字 / PDF 900,835 字 |
| 视频 episode 契约 | `npm run video:lint` | 19/20 通过；`ai4fw` 报缺 `voice`/`platforms`/`cover.line1`，为存量内容缺口 |
| 视频单元/夹具 | `node --test video/tests/package-covers.test.mjs video/tests/spec-v2.test.mjs` | 23/23 通过（含真浏览器四平台封面出图） |

## 规划交付验证（先前轮次）

| 检查 | 方法 | 结果 |
|---|---|---|
| Trellis 上下文与任务归属 | get_context 的默认/phase/packages；task.py current --source | 规划轮状态为 planning；规划本地链接全部可达 |
| 引用路径与关键行号 | 源文件存在性 + 11 个核心行号字符串断言 | 通过（矩阵生成、cover/pack 入口、PDF 默认目标、两份 CI 命令） |
| 命令名 | 规划中的 npm run 名称对 `package.json` 核对 | 11 个脚本名均存在；参数另对 CLI 源码回读 |
| 需求与批次覆盖 | S01–S10、B1–B6、R1–R7 映射检查 | 全部覆盖，无丢失编号 |
| 文档卫生 | UTF-8、占位标记、行尾空白、末换行、控制字符 | 通过 |
| Git 差异 | `git diff --check`、`git status --short` | 仅新增任务目录；11-02 的修改与 PPT 未跟踪目录保留 |

## S01–S10 落地位置

| 编号 | 落地文件 |
|---|---|
| S01 | [总索引](../../../spec/index.md)、各新层 index、[video/index.md](../../../spec/video/index.md) |
| S02 | [quality-contract.md](../../../spec/docs-site/quality-contract.md) 的矩阵/场景/变体/CI 契约与错误矩阵 |
| S03 | [book/build-contract.md](../../../spec/book/build-contract.md) |
| S04 | [book/print-contract.md](../../../spec/book/print-contract.md) |
| S05 | [firmware-common/reliability-contract.md](../../../spec/firmware-common/reliability-contract.md) |
| S06 | [firmware-common/probe-contract.md](../../../spec/firmware-common/probe-contract.md) |
| S07 | [firmware-rtos/index.md](../../../spec/firmware-rtos/index.md)、[kernel-contract.md](../../../spec/firmware-rtos/kernel-contract.md) |
| S08 | [firmware-gd32/index.md](../../../spec/firmware-gd32/index.md)、[build-contract.md](../../../spec/firmware-gd32/build-contract.md) |
| S09 | [video/build-package-contract.md](../../../spec/video/build-package-contract.md)、video 索引与 v2 命令修正 |
| S10 | [guides/index.md](../../../spec/guides/index.md)、[总索引](../../../spec/index.md) 的占位例外与八层路由 |

F01（CI 的 A4/印前目标不匹配）与 F02（FreeRTOS USE_MUTEX 目录未隔离）保持登记状态：
未修改 workflow，未跑 0→1→0 切换实验，不写成已修复或已复现。

## 未执行

- 没有运行 `npm run firmware:check`、`npm run docs:build`、`npm run quality`、全量 `video:check`。
- 没有重新构建印前 PDF；只对现有 `mcu-deep-book-print.pdf` 跑了 13 项检查。
- 没有运行 `publish_downloads.py`、平台准备/发布/删除、串口或远端 CI。
- 没有提交、推送、部署或归档。

## PRD 验收对应

| 标准 | 证据 | 结论 |
|---|---|---|
| AC1 维护面与依据 | [spec-audit.md](spec-audit.md) 的覆盖表、缺口表 | 满足 |
| AC2 文件/优先级/依赖/断言 | 审计 S 表与 [implement.md](../implement.md) 的批次表、执行清单 | 满足 |
| AC3 三文档职责 | [prd.md](../prd.md)、[design.md](../design.md)、implement | 满足 |
| AC4 命令与副作用 | design 接口表、implement 验证表、对应 CLI/CI 源码；本轮实际命令 | 静态核对 + 轻量实跑；重命令标未执行 |
| AC5 路由与权责 | design 分层/阅读路由/真源表；八层索引 | 已落地，链接可达 |
| AC6 路径/JSON/差异 | 本轮链接、JSON、`git diff --check` | 通过 |
| AC7 实施边界 | 任务已启动；F01/F02 保持登记；未执行项列明 | 通过 |
