# Spec 补全设计

需求见 [prd.md](prd.md)，仓库依据与缺口编号见 [审计](research/spec-audit.md)，批次和验证见 [implement.md](implement.md)。本文件描述已实施的方案；新增规范文件已于 2026-11-05 创建，落地位置与验证见 [validation.md](research/validation.md)。

## 组织与权责

沿用 `.trellis/spec/<layer>/index.md + 主题合同`。保留现有 docs-site、firmware-stm32、firmware-esp32、video；补 book、firmware-common、firmware-rtos、firmware-gd32 四个真实维护面，不添加 Web 前后端等无对应代码的层。

| 层 | 唯一维护内容 | 与其他层的关系 |
|---|---|---|
| docs-site | 正文、导航、站点元数据/交互、共享工程清单、质量总入口、导读/卡片 | CONTRIBUTING 保持内容最高法；其余层链接到工程登记与实验状态合同 |
| book | manifest→离线 HTML/A4、同源印前、A4 下载包、字体与 PDF 验证 | 正文事实仍归 docs/；图层来源引用 architecture-diagram，不复制其制图规范 |
| firmware-common | C/工具链/behavior 取证，协议/健康监测/串口 CLI | logger 暂保留 docs-site 原路径并引用；平台同步和外设规则仍归对应固件层 |
| firmware-stm32 | F407 启动、链接、寄存器、平台适配 | 共用协议与 RTOS 引向相应层，不复制协议字节布局 |
| firmware-esp32 | S3/IDF target、组件、IRAM、双核、变体配置 | 工程 schema 引质量合同；内核来源区分由 RTOS 合同维护 |
| firmware-rtos | FreeRTOS/RT-Thread 版本、端口、配置、场景、证据边界 | 内核无板行为与板级外设分开，引用公共取证合同 |
| firmware-gd32 | 当前 GD32F4 工程、GD32VF 章节的适用范围、事实不确定性 | 共享 ARM 启动规则用链接；不把 F4 的构建器套到 RISC-V 章节 |
| video | episode schema→声音/时间轴/渲染→封面/发布包 | 平台外部动作继续归 video-release skill 与平台台账；新合同只描述代码接口和放行边界 |

新增合同清单：book/{build-contract,print-contract}.md；firmware-common/{probe-contract,reliability-contract}.md；firmware-rtos/kernel-contract.md；firmware-gd32/build-contract.md；video/build-package-contract.md。新增层均补 index.md。

## 阅读路由

总索引用“修改路径/行为 → 必读层”表；每层 index 包含适用范围、动手前必读、金样例及质量检查。细节合同只维护一次。

跨层路径必须有明确路由：

- 修改 `code/common/` 或 `scripts/device-console.py` → common；涉及 logger 再读原 logger 合同；修改板级 port 再读 STM32/ESP32。
- 修改 `code/rtos/` → RTOS + 对应板级规范；修改 `docs/rtos/` 还读 docs-site/content。
- 修改 `mcu-book/` → book；修改构建输入章节则再读 docs-site；改发布下载包要复核质量与部署合同。
- 修改 `video/src/` → video；`formatVersion`、节拍、相位、状态键必须先读 v2 合同，v1 夹具始终有效。
- 修改 guides 只放简短检查项与合同指针；历史任务中的测量记录保留日期和范围。

## 合同深度与真源

新增的跨层或 CLI 合同按七部分编排：适用场景、签名、数据/环境契约、校验与错误矩阵、正常/边界/错误案例、现有测试及断言、错误与正确做法。已有 v2/layout 等专题结构清楚的文件只补缺口，无需机械重排。

| 事实 | 核对依据 | 禁止替代来源 |
|---|---|---|
| npm 命令与默认参数 | package.json + 对应 CLI 解析 | 过往聊天或只看 README |
| 工程矩阵与构建分支 | project-catalog.mjs + projects.json + workflow 消费端 | 根据现有 schema 文案反推代码 |
| 字节协议与状态码 | C 头文件/实现 + Python codec + 交叉验证测试 | 在规范里设计新协议 |
| 内核/编译器版本 | Makefile、probe、CI 与本地缓存来源记录 | 把注释中的“固定”当作精确 revision 已锁定 |
| PDF 目标与检查规则 | build_html/build_print/check_pdf 的参数及默认输出 | “PDF 都叫一本书”或把两个生产链混成一条 |
| 视频封面与母版映射 | package.mjs 的 COVER_SIZES/packJobs + cli.mjs | 旧 `.temp/` 工具或历史截图尺寸 |
| 数量与完成状态 | manifest/progress/工程清单/episode 配置/实测产物 | 把 18/19/20 集或旧 PDF 页数写成永久门禁 |

每条新增规则需至少一个源码位置和一个可检查断言。若现有测试没有覆盖，写“待增补/待人工核验”，不能编造测试名或声称已有保护。本轮不添加产品测试。

## 三组关键接口

### 工程登记与证据（S02、S05–S08）

矩阵输出为 `{include:[{path,target,variant,defaults}]}`。工程登记的 kind/entry、probe、variants、scenes、faults 以当前 parser 为准；普通与故障版 S3 的 defaults 组合以及 sdkconfig 输出目录按 workflow 描述。

host 编译断言、ARM 交叉反汇编、目标芯片构建、板上测量分别注明。缺工具跳过某段时，报告实际未验证的结论。上板状态只由实验元数据与证据支撑，不从 make 成功推导。

USE_MUTEX 及内核 revision 先核验再写承诺；已发现的 F02 不在文档中“修好”。不在 spec 中引入现有 parser 未接受的字段。

### 书籍与产物（S03、S04）

| 入口 | 产物与副作用 | 匹配验证 |
|---|---|---|
| `npm run book:check` | 临时目录生成 HTML，完成后清理 | HTML 装配与链接合同 |
| `npm run book:html` | 写 mcu-book/dist/mcu-deep-book.html | build_html 测试与源章节覆盖 |
| `python mcu-book/build_html.py --pdf` | 写离线 HTML 与 A4 mcu-deep-book.pdf | 现有 A4 构建与测试；不冒充印前 13 门 |
| `npm run book:pdf` | build_print 写 mcu-deep-book-print.pdf 等印前文件 | check_pdf 默认印前目标；可用 --out-dir 隔离 |
| `python mcu-book/check_pdf.py <印前PDF路径>` | 读指定 PDF | 裁切/字体/目录索引/页眉页码/密度/矢量与位图预算等实际检查 |
| `python mcu-book/publish_downloads.py --out-dir <目录>` | staging 后整体替换该下载包目录 | --verify 读既有包；CI 用 GNU 摘要双口径 |

输入正文/manifest/图片/测验 → build_html 静态化 → HTML/A4；同一 HTML → build_print 冻结、嵌入字体、分页与索引 → 印前 PDF。publish_downloads 当前导入 build_html 的 OUTPUT_NAME/PDF_NAME，打包离线 HTML 与 A4 PDF；印前 PDF 是独立产物，规范更新不得擅自替换发布规格。

F01 作为实现疑点登记。规范可以明确现在的矛盾和验证前置，但本轮不修 workflow，也不宣称 CI 与设计目标一致。涉及 CI 的后续修复必须先确定发布产物、执行成本及失败传播。

### 视频生成与平台外部动作（S09）

`lint/test/numbers/check` 与 `cover/pack/build` 分开标注副作用：check 依赖已有 timeline，缺失会跳过；cover 和 pack 可写文件；build 会重新产生音视频。四平台封面尺寸与知乎/小红书母版映射均引用 package.mjs 当前导出。

示例封面命令将候选输出放 `.temp/spec-covers/`，避免覆盖排队中的正式资产。pack 虽预检输入，不应被描述为对所有 release 文案错误保证跨平台原子写入。`npm run video:test -- 某文件` 不表示只跑该文件，单文件改用 `node --test video/tests/spec-v2.test.mjs`。

平台“准备/发布/删除”不进入自动验收命令。schema、台账结构或封面改动不能授权任何平台动作；如需平台操作，进入其技能与现有授权流程。

## 兼容、迁移与回退

- 不移动旧规范或 logger 合同；新增层入口只增加链接。现有 archive/任务引用保持有效。
- 主题文档与层 index 同批落地；总索引只链接已经存在的文件，不提前制造断链。
- 先校对已漂移的签名和危险操作，再补缺失领域，最后收口路由与重复内容。
- 每批回退只撤销该批新文档或本会话自己的具体修改段。保留工作区基线，不使用整文件恢复或 git reset 覆盖用户修改。
- 本轮规范实施已完成，无需子任务树。后续若按领域拆成独立实施任务，先继承 S 编号、需求和本文边界，并在各自计划显式写依赖。

## 设计取舍

采用四个额外领域入口，是因为它们有独立源目录和构建/验收边界。复用已有 quality/logger/presentation 合同，减少协议与清单事实多处复制。暂不添加通用 spec lint 或改 CI：先把维护规则与已存在检查建立对应关系，有真实自动化缺口时再单列实施。
