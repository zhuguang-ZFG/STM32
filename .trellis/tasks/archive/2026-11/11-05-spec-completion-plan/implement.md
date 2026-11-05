# Spec 补全实施计划

状态：2026-11-05 规划已编写；同日按用户"执行 spec 计划"完成 B1–B6 规范实施与轻量验证。
重命令（firmware:check、docs:build、全量 video:check、重构建印前 PDF）与产品回归仍未执行，见 [research/validation.md](research/validation.md)。
需求见 [prd.md](prd.md)，文件结构见 [design.md](design.md)，缺口依据见 [审计](research/spec-audit.md)。主会话 inline 实施与检查，不派发子代理，不生成无用途 JSONL。

## 计划交付检查

- [x] 读取四层规范、产品脚本、关键测试和 CI，登记 S01–S10 与 F01/F02。
- [x] 写明需求、技术设计、分批计划和未执行边界。
- [x] 核对任务 JSON、规划本地链接、来源路径、命令和需求覆盖。
- [x] 回读 PRD 收敛需求，记录实际验证结果，提供最终审阅入口；见 [research/validation.md](research/validation.md)。

## 启动门

- [x] 用户审阅本轮三份主文档并明确要求实施。当前“继续完善计划”的授权已经使用，无需重复询问建任务。
- [x] 刷新 git status 和来源证据，保留原有图片、PPT、specs.md 及其他会话修改。
- [x] 读取 inline 的 trellis-before-dev 与 Phase 1.4；再执行 `python ./.trellis/scripts/task.py start spec-completion-plan`。

到达以上门后已执行任务启动与 B1–B6；以下批次均已完成规范落地。重命令与产品回归未执行，状态见验证报告。

## 批次与依赖

| 批次 | 覆盖编号 | 前置 | 修改目标 | 完成判据 |
|---|---|---|---|---|
| B1 已有接口纠偏 | S01/S02/S09 | 启动门 | docs-site/quality-contract、video/index、video/v2-contract | 矩阵字段/场景/变体一致；v2 已索引；单文件命令准确；移除正式流程对临时封面工具的依赖 |
| B2 书籍生产契约 | S03/S04 | B1 | 新 book/index、build-contract、print-contract；总索引同批登记 | HTML/A4/印前三条链路清楚；F01 如实登记；正文/字体/索引/位图规则有断言来源 |
| B3 公共代码与取证 | S05/S06 | B1 | 新 firmware-common/index、probe-contract、reliability-contract；总索引同批登记 | 生产 C/Python 协议可互核；错误码/超时/并发归属齐；工具缺失不伪装通过；复用原 logger 合同 |
| B4 内核与 GD32 | S07/S08 | B3 | 新 firmware-rtos/index、kernel-contract；firmware-gd32/index、build-contract；更新 STM32/ESP32 入口和总索引 | 两内核场景/版本准确；F02 不作已修承诺；F4/VF 与待核验事实有明确界限 |
| B5 视频生产合同 | S09 | B1 | 新 video/build-package-contract；更新 video/index、v2-contract 的相关入口 | 正式 cover/pack/numbers/calib 接口与副作用准确；历史兼容、跳过和平台边界可验 |
| B6 索引与总体验收 | S01/S10 | B1–B5 | 总索引、guides/index、八层 index，相关合同去重 | 每层包含动手前和质量入口；无悬空链接、重复真源、无日期的历史计数或错误跳过承诺 |

依次执行 B1 → B2 → B3 → B4 → B5 → B6。每批回读本批源码与测试，再补文档并运行最小相关检查；上表的逻辑依赖不会因为文件夹层级自动成立。

需求覆盖：R1/R2 → 审计全表与 B1–B6；R3 → 真源表、F01/F02 与每批核验；R4 → 批次依赖及验证命令表；R5 → 七部分合同结构和逐合同断言；R6 → 权责表及 B6 去重；R7 → 本轮验证记录与以下未执行检查的分界。最终验收对应 PRD 的 AC1–AC7。

## 每批执行清单

### B1：签名与入口（P1）

- [x] 对照 project-catalog 的 parser 和 stdout，补 `{path,target,variant,defaults}`；覆盖 variants 与三种 scenes 形状，区分工具与宿主检查。
- [x] 核对 S3 normal/faults 的 SDKCONFIG、SDKCONFIG_DEFAULTS 与构建目录，不把分号组合写成数组。
- [x] 视频索引登记既存 v2 合同，补 cover/pack/numbers/calib 正式命令及读写副作用。
- [x] 把旧集数/平台数标为历史样本，当前预期从目标 episode 配置计算；检查 `跳过` 数量。
- [x] 修正单文件测试示例，不改 v1 夹具与 schema。

### B2：书籍（P1）

- [x] build-contract 覆盖 manifest/罗盘/测验/附录/内嵌资源/slug 与装配失败；列出 CLI、输入、输出、退出行为。
- [x] print-contract 覆盖 A4 与印前区别、字体来源、冻结、SVG/位图预算、目录/术语索引、正文保护、sample/bleed 的适用范围。
- [x] 列出 build_html、build_print、check_pdf、publish_downloads 的准确参数与默认目标；显式核实打包 PDF 类型。
- [x] F01 保持为静态已确认的接口冲突；未运行 CI，不记录为远端失败或已修复。
- [x] 将 book index 与总入口同时加入；文档提到的测试名必须真实存在。

### B3：公共代码（P1/P2）

- [x] probe-contract 按脚本核实 HOSTCC/ARM_PREFIX 等变量，不把某脚本支持的 env 扩展成全局约定。
- [x] 区分宿主语义、ABI/汇编、芯片编译与板上测量；冻结工具链结论注明版本与跳过分支。
- [x] reliability-contract 从 protocol/transport/health/record 及 device-console 实现提取边界；核对 CRC、COBS、长度、状态码、超时、回绕和暖复位有效性。
- [x] 规范 CLI 不自动选端口，串口退出码按实际分支写；自测与打开真实设备的命令分开。
- [x] common index 链接 logger 原合同；不搬迁、不重复 SAMPLE/存储数据布局。

### B4：RTOS 与 GD32（P1/P2）

- [x] 上游 FreeRTOS、IDF SMP 与 RT-Thread 的 revision、端口和配置分别说明，RT-Thread 未锁定 revision 如实记录。
- [x] 场景/USE_MUTEX/产物目录逐 Makefile 描述；F02 的实验待办与已实现行为分开。
- [x] GD32 引官方库冻结点，注明时钟回退、SCSS 读回与理论输出；保留 FMC/内存待核验。
- [x] GD32VF 仅覆盖现有章节与工具链事实；新增索引不虚构 RISC-V 可构建工程。
- [x] STM32/ESP32 index 增加公共代码、RTOS、工程登记及验证入口，保留板卡和寄存器纪律。

### B5：视频（P1）

- [x] 按 cli 与 package 的当前实现提取 cover/pack/build/check/numbers/calib 的准确签名及产物目录。
- [x] 四尺寸与知乎/小红书母版映射指向 package 导出；cover 候选写隔离目录，pack/build 的写入提示清楚。
- [x] 区分 schema lint、数字证据、已有时间轴排版审计与真实渲染；缺 timeline 的零退出必须标为未验。
- [x] v1 输出/状态键/滤镜夹具不动，v2 合同只补发现的文档缺口。
- [x] 指向 video-release 与台账作为外部动作入口，不运行 prepare/publish/delete 等平台命令。

### B6：集成（P2）

- [x] 根索引与八层索引、guides 路由同批核对；guide 只保留短检查项。
- [x] 占位禁令统一为正文不得留占位，模板教学示例显式例外；不扩大或削弱现有产品检查器。
- [x] 检查本地链接可达、每条规则来源与断言、日期/历史计数、环境副作用和所有 S 编号闭环。
- [x] 产出后续验收报告，按“已执行/失败/跳过/未执行”分别记载；F01/F02 保留真实状态。

## 验证命令与执行条件

本轮只执行规划文档与来源接口的静态检查。下表为规范实施时的选择表，所有产品回归当前均未执行。

| 范围 | 命令 | 环境、前置与副作用 | 断言 |
|---|---|---|---|
| 文档/任务 | `git diff --check`；`python ./.trellis/scripts/task.py current --source` | 只读；还须单独检查未跟踪规划文件和所有本地链接 | 无空白错误、任务/状态正确、改动范围清楚 |
| 工程清单 | `npm run projects:check`；`node scripts/project-catalog.mjs --matrix`；`node --test tests/catalog.test.mjs` | Node/npm；矩阵只输出 JSON，测试会建临时夹具 | 矩阵字段与 normal/faults 读 stdout 核验；已有测试覆盖非法登记/目标/probe，不虚称已覆盖全部变体 |
| 公共 CLI | `node --test tests/device-cli.test.mjs tests/logger-cli.test.mjs`；`python scripts/device-console.py self-test` | Node/Python；仅离线，不开串口 | 参数位置、64B SAMPLE、TLV/配置拒绝、自测 |
| 生产公共 C | `sh code/common/reliability/probe.sh`；`sh code/common/logger/probe.sh`；`sh code/common/behavior/probe.sh` | C11 编译器、sh、Python；写各自 build，Linux sanitizer 分支单列 | C/Python 双向向量、恢复切点、并发模型和实际断言 |
| 全固件 | `npm run firmware:check` | make/Git sh、ARM/host 编译器、所需内核/CMSIS 缓存；会写各工程 build，不烧录 | 登记工程、场景切换、SP/Thumb/ELF；记录跳过段；不冒充 S3 构建 |
| S3 构建 | 采用 quality.yml 的 `idf.py -B build/ci-<variant> -D SDKCONFIG=... -D SDKCONFIG_DEFAULTS=... set-target esp32s3`，继而 `build size` | IDF v5.5.2，工作于清单对应工程；写隔离 sdkconfig/build，不 flash | project_description target 与变体 defaults；覆盖 normal/faults |
| 书籍离线 | `python -m unittest discover mcu-book/tests -v`；`npm run book:check` | Python 依赖按 requirements；测试临时文件可能存在，未必需要浏览器 | manifest/静态化/链接/矢量/冻结/打包的已有断言 |
| 正文/题图保护 | `python mcu-book/tools/prose_guard.py --single <待核实章节路径>`；`python mcu-book/tools/art_guard.py --dir mcu-book/book/assets/chapter-art` | Python；只读输入；原文保真比较另按 prose_guard 的双文件或 --additions 接口 | 区分单文件口癖计数与原文对照，不能用前者证明事实零删改；题图检查按源码规则 |
| 印前 PDF | `python mcu-book/build_print.py --out-dir .temp/spec-plan-print`；`python mcu-book/check_pdf.py .temp/spec-plan-print/mcu-deep-book-print.pdf` | Python/Chromium/字体/paged.js；耗时构建，只在产物规则修改或验证未决时跑 | 真实完整印前产物的现有检查；sample 不能替代全书验收 |
| 下载包 | `python mcu-book/publish_downloads.py --out-dir .temp/spec-plan-downloads`；随后 `python mcu-book/publish_downloads.py --verify .temp/spec-plan-downloads` | 需要当前默认源产物；首命令整体替换该隔离下载目录 | 清单摘要、源文件齐备；不得读取旧包证明新构建 |
| 视频兼容 | `node --test video/tests/spec-v2.test.mjs video/tests/layout-v1.test.mjs video/tests/layout-v2.test.mjs video/tests/package-covers.test.mjs` | Node；部分测试需浏览器，产生临时夹具；不重渲成片 | schema、v1 夹具、封面尺寸/映射、已有发布包案例 |
| 视频源 | `npm run video:lint`；`npm run video:numbers -- <已核实集号>` | Node；数字证据必须存在；只读输入 | 全配置契约与目标集数字证据 |
| 视频版式 | `npm run video:check -- <已有timeline集号> --platform <bilibili或douyin>` | Chromium、现有 timeline；不合成音频/成片 | 预期目标平台实际通过，无 timeline 跳过不计 |
| 站点回归 | `npm run quality`；`npm run test:browser` | Node/Chromium；quality 会生成站点；仅正文/主题/质量实现发生改动或有未决漂移时跑 | 已有站点门；不误称含 cards:check、video 或全固件 |

纯规范文件改动优先做路径、签名和相关轻量命令核对；无需机械重建所有视频/PDF。遇到失败先区分既有失败和本批引入，不修改阈值以制造通过。任何需要下载依赖或外部权限的命令按当时环境处理，不预先假设可用。

## 完成与回退

- 本轮计划完成：PRD 的 AC1–AC7 有记录；任务保持 planning；所有后续批次不打完成勾。
- 后续规范实施完成：S01–S10 各有目标文档与核对记录，索引可达、实际签名一致、无新占位和悬空引用，必要相关检查通过或明确未解决项；F01/F02 不隐去。
- 每批失败只回退本批自己写入的文档段落；不覆盖用户文件，不做整仓 reset/clean。
- 没有新用户指令前，不提交、推送、部署或触发平台动作。提交/归档按后续已授权的 Trellis 阶段执行，不以计划写完代替规范实施完成。
