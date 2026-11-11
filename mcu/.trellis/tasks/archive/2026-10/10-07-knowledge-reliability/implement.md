# 可靠性工程执行计划

状态：规划待审阅；实现项均未执行。依赖 knowledge-fact-corrections、knowledge-prerequisites 已完成。主会话按顺序实施/检查，不分派 implement/check 子代理。

## 0. 审阅与实施前检查

- [x] 复用已有任务，记录用户本轮规划授权；任务保持 planning。
- [x] 核对公共协议与后续 capstone 的 64 字节 SAMPLE/响应容量边界。
- [x] 读取生产 UART、FreeRTOS 配置、工程清单与 CI；记录帧边界旧文冲突。
- [x] 核对本地 IDF v5.5.2 头文件、官方 watchdog 文档和 ST 官方 HAL 参考。
- [x] PRD 收敛为目标/背景/需求/验收/边界，保留 W1–W6、W-A1–W-A6 与原文证据。
- [ ] 用户审阅 prd.md、design.md、implement.md 后执行 task.py start。
- [ ] 加载 trellis-before-dev，读取 docs-site/firmware-stm32/firmware-esp32 相关规范。
- [ ] 在写 watchdog 参数前获取有效 STM32F407 datasheet/RM0090：核对 LSI min/max、IWDG 更新时序、WWDG 刷新边界与调试冻结条件，保存版本/页码/来源。当前旧缓存不能作为证据；不编造最短/最长复位时间。
- [ ] 确认 ARM GCC、make/sh、FreeRTOS V11.1.0、IDF 5.5.2 的可复现环境；不得将本机旧 sdkconfig 或隐藏缓存当成正确构建。Python 使用可用的 python3，CI 可用 python。

## 1. 公共协议与健康模块（W1/W4）

- [ ] 建 code/common/reliability，冻结容量常量、frame_t、错误计数、CRC/COBS 向量与健康 API。
- [ ] 编码校验先于写入，解析 EMPTY/COLLECT/DISCARD 状态；添加 poll、transport-loss 输入。
- [ ] 测全部单切分点/固定种子随机分块、连续多帧、非法长度/版本/CRC/COBS、丢字节/恢复、100ms 边界、uint32 回绕。
- [ ] 实现健康配置校验、首次进展、永久结束宽限、过期边界；测恢复状态和平台重启锁存分别生效。
- [ ] probe.sh 编译执行生产 C 测试；Linux sanitizer 强制，Windows 普通运行；随后登记 common-reliability 为 host-probe。

检查点：公共模块测试失败不进入两板适配；不得以字符串匹配代码替代行为测试。

## 2. 主机 codec 和最小命令（W1/W6）

- [ ] 编写 scripts/device-console.py：标准库离线 codec、自测、显式串口命令、有限等待、日志、匹配 type/sequence。
- [ ] pyserial 仅用于实际串口命令，独立依赖文件固定验证过的版本。
- [ ] C 编码→Python 解码、Python 编码→C 解码双向向量；CRC 除固定向量外可用标准库独立 oracle。
- [ ] 确认 INFO 5 字节、STATUS 25 字节固定前缀，TLV 截断/未知字段处理；普通构建未知/故障请求返回明确状态。
- [ ] 测无关响应不延期、错误 type/sequence 拒绝、重连清待处理、65535→0、超时重试前同步、fault 禁止自动重试。

检查点：两种 codec 不一致时不调板端“迁就”；先定位 wire 布局/端序/长度合同。

## 3. 双板协议工程（W2/W3）

- [ ] F407 05-framed-protocol：复用 DMA 位置算法，256 字节 DMA/512 字节 RX、有界 ISR、单消费者与失步通知。
- [ ] S3 06-framed-protocol：UART1 GPIO10/11，RX ring/事件服务与周期取数；不依赖每个 UART_DATA 必然送达。
- [ ] 实现 4 帧 TX 队列、部分写入/零进展、有界截止期、超时后同步分隔符；整帧有序，不混文本日志。
- [ ] 用生产状态机+注入 transport 测 RX/TX 满、服务延迟、DMA 积压、UART 已报告错误与恢复。
- [ ] 两工程登记真实入口；F407 实际编译/初始 SP/Thumb Reset 校验，S3 干净 target=esp32s3 构建。
- [ ] README 明确接线、端口、源文件依赖与待上板项；未接板时不填通信成功。

## 4. 双板 watchdog 工程（W3/W4/W5）

- [ ] F407 06-watchdog-health：FreeRTOS worker/communication/supervisor，IWDG 有限初始化、健康后服务、首次失败锁存。
- [ ] 单独 WWDG normal/early/late 模式：窗口计算+计数检查；EWI 不无条件续命；默认不触发故障。
- [ ] S3 07-watchdog-health：TWDT init/reconfigure 精确错误分支、idle+health user、panic/reset；保留 IWDT。
- [ ] 读取并保留平台原始 reset reason；故障详情记录带 magic/version/CRC，与冷启动有效性分开。
- [ ] .noinit/RTC 保留段审查启动/链接脚本；暖复位、冷启动、坏 CRC 模型分别验证，有板再测真实保留。
- [ ] 普通构建拒绝 TEST_FAULT；测试构建显式注入单任务停止/监督停止，不上电自动故障。
- [ ] 验证无流量、传感器返回错误、正常暂停不误触发；恢复进展不清平台重启锁存。
- [ ] 实际编译 IWDG/WWDG、S3 默认/故障模式，记录每种配置和产物。

## 5. 教材与集成（W6）

- [ ] 完成 C8/S17/P13：机制、源码分析、配置、接线、主机命令、反例、自测、完整源码站内内嵌。
- [ ] 原位修正 S7/P5/旧 UART README 的 IDLE/timeout 判帧表述，并核对相关习题/动画文字。
- [ ] 同步课程规划事实源、sidebar、板块 index、工程清单；运行 readme:sync，不手写统计。
- [ ] 三篇内含实验记录表，上板部分标 pending；不新建 E 编号，不提升旧实验验证状态。
- [ ] 把公共 INFO/STATUS 前缀/TLV、health API 的最终合同交给 capstone；实现 capstone 前重读，不在本批顺便开发记录器。

## 6. CI 与全面验收

- [ ] 为公共 probe 增加 Python 交叉验证和 Linux ASan/UBSan，缺工具不能静默略过。
- [ ] 保留既有 scenes=[1,2,3,4,5] 合同；新 watchdog 模式使用独立显式校验入口和隔离 build 目录，复用 ELF/bin 起始 SP 与 Thumb Reset 校验。
- [ ] 正常→故障→正常切换检查产物隔离；非法 mode 拒绝；既有 FreeRTOS 场景回归保留。
- [ ] IDF 清单自动扩展两个新工程，新增独立默认/故障 sdkconfig 构建，检查实际 target。
- [ ] 运行 trellis-check，逐项核对全部受影响层，填写 research/validation.md。
- [ ] 完成后审查规范更新需要、提交与远端同一 HEAD 的 CI；不提前把本任务标完成。

### 验证命令与证据

以下含计划新增入口，必须实现后才可报告执行成功；现有 npm test/projects:check 基线结果见研究记录。

| 阶段 | 命令/动作 | 证据 |
|---|---|---|
| 公共 C/Python | cd code/common/reliability；sh probe.sh | 固定向量、生产行为断言、Linux sanitizer |
| CLI 离线 | python3 scripts/device-console.py self-test | 交叉解码、坏帧/等待/序号 |
| 教材生成 | npm run readme:sync | 生成块同步 |
| 全站质量 | npm run quality | 单元/元数据/清单/站点/动画/统计/链接 |
| ARM/host | npm run firmware:check | 既有工程及新增模式实际构建、向量核验 |
| S3 | 每工程 idf.py -B build/ci -D SDKCONFIG=<独立路径> set-target esp32s3，随后 build size | 版本、配置、target、体积；故障构建另目录 |
| 浏览器 | npm run test:browser（docs:build 后） | 搜索、动画、移动端及新增页可达 |
| 两板硬件 | 同一 CLI info/status/fault，独立日志/波形记录 | 无调试器下通信、复位原因、窗口/时间；无板则 pending |
| 集成 | 交付 HEAD 对应 CI 所有必需 jobs | 不复用旧成功 run |

### 故障矩阵

| 类别 | 必测输入 | 通过标准 |
|---|---|---|
| codec | 0/1/64/65、每个切分点、连续帧、坏编码/CRC/version/length | 有效帧一致；无越界/无限循环 |
| 恢复 | 噪声、截断、超长、transport-loss、同步 0 后合法帧 | 按状态合同恢复，不拼接损坏尾部 |
| 时间 | 99/100/101ms、uint32 回绕、宽限退出后完整回绕 | 边界一致，宽限不复活 |
| 健康 | 未首报、单任务停、全员活跃、恢复、无通信、传感器错误 | 原因/掩码准确，首次失败锁存 |
| 背压 | RX/TX 满、partial/zero write、任务消费延迟 | 计数、有限等待、后续同步正确 |
| 构建 | 默认/故障/WWDG 场景、正常→故障→正常 | 真实构建且产物隔离 |
| 上板 | 卡死→复位→原因、断开调试器、冷启动、WWDG 早/晚 | 实测原始证据；无板明确 pending |

## 回退边界

每一阶段以可复验的行为/构建检查收口，失败先修该阶段。主要风险文件为公共 codec/health、平台 transport、启动/链接保留段、scripts/check-firmware.mjs、CI。回退仅撤销本任务新增文件及它们的清单/导航/教程改动，不回退已完成的前置任务或用户其他改动。
