# 技术设计

## 组织与依赖

采用一个集成任务，由主会话实施。已考虑父子任务拆分：工程清单、实验状态、CI 矩阵和首页统计共享契约，本次统一验收以避免分散维护。
D1 构建与清单 → D2 实验与说明 → D3 门禁与站点收尾。D2 消费 D1 清单；D3 必须等待 D1、D2 工程与命令稳定，不以任务树隐含依赖。

## D1：构建与工程清单（R2、R4）

- FreeRTOS 使用 build/scene-1 至 build/scene-5，仍处原 build 忽略范围；校验 DEMO_SCENE ∈ 1..5，flash 使用同一变量解析产物，默认场景 1。增加头文件依赖跟踪。
- code/projects.json 显式登记 id、path、kind、entry、target/场景。kind 至少区分 arm-make、esp-idf、host-probe。
- 统计仅计入清单内有效工程，页面叫“示例工程”。构建证据另记 research/validation.md：版本、命令、日期、提交/工作区状态和结果；未经执行不显示已验证。
- 临时 build 或空目录不计数。检查未登记的构建入口时报告待登记；B3 由原工作保留，最终按真实入口登记。

## D2：实验与说明（R1、R5、R6）

- code/stm32/04-i2c-eeprom：沿用启动与链接结构，寄存器级 AT24C02 写/读；有界等待、错误日志、ACK polling，单字节读 ACK/ADDR/STOP 顺序以 ST 官方资料核对，板卡引脚给来源。
- code/esp32/04-qmi8658：新版 I2C master，ID 检查、初始化、连续读与量程换算。寄存器、字节序、比例和引脚依 datasheet/板卡官方资料确认，不能用占位值声称完整实现。
- code/esp32/05-audio-play：固定版本的 ES8311 初始化实现，优先厂商维护组件；PCM 正弦/音符生成、I2S TX、MCLK/功放控制和错误处理。有效数据率与物理帧时钟分别说明。
- ESP32 固定 esp32s3 与已核实 IDF 版本；配置进入 sdkconfig.defaults/Kconfig 或集中配置。既有 sdkconfig 提交策略与规范不同，保持兼容并确保干净 CI 可重建，不批量删除配置。
- 三个新工程及三个既有 ESP32 工程 README 均含版本、引脚一手来源、命令、预期观察、排查和真实验证状态；实验/章节用源码导入呈现实现。
- status 保留文稿 done/building 语义；实验另记录代码就绪状态与 hardware verification（pending/verified），verified 必须有证据链接。对照审计 E01–E08，包括 E04/E06，缺少复现条件要明确显示，不能因新增三个工程就误标全部可运行。
- 实验卡时长/难度由 frontmatter 渲染，难度保留 1–3 规范；总览消费同源数据，消除重复星数/时长。
- 元数据检查：status 枚举、difficulty ∈ 1/2/3、minutes 正整数；失败不输出貌似有效的进度数据。

## D3：门禁、站点和性能（R3、R7、R8）

- quality.yml 支持 workflow_call；PR 自身运行，deploy.yml 对当前提交调用相同门禁，发布显式依赖检查成功和站点 artifact，避免跨 workflow_run 的提交竞态。
- PR 只读权限；仅 main push/手动部署开放 Pages。并发组区分调用来源，避免调用方/被调用方互相取消。
- 编译矩阵消费工程清单：ARM 完整工程、FreeRTOS 五场景、四个既有及两个新增 IDF 工程；probe 依类型单独执行。固定 FreeRTOS/IDF 版本，记录 ARM 编译器版本，缓存不得替代干净构建证据。
- 高亮先检查已安装 VitePress/Shiki 支持，显式载入语言/合理别名；若不支持再引入可维护语法，不假称原生支持。
- 递归盘点 dist JS/CSS 与压缩体积，测首页、动画页初始加载、导航和搜索；按证据调整分包、搜索延迟加载或 SVG 重复内容。不关警告，不牺牲本地搜索、无障碍或动画功能。
- 同步 README/首页/总览，去掉“全部成稿”固定文案；保持 ignoreDeadLinks=false。

## 风险与回退

- 实机验证依赖可访问板卡/仪器；若官方资料无法取得，记录具体缺口，不猜默认值，不用 pending 标签替代未完成实现。
- 新工程、场景隔离、统计、CI、主题分组检查，回退单组同时处理清单引用；不使用全仓 reset/clean。
- 最终重新检查 git diff，B3 变化不算本任务源码交付；README 仅同步最终统计。
