# 可靠性工程规划依据（2026-10-07）

## 本轮状态

- 用户授权接续已有任务并完善规划，当前仍 planning，未 task.py start。
- 基线 main / 314fe33，开始时工作树干净；27 项 npm test、28 个 npm run projects:check 均通过。
- 本轮只更新任务文档与研究记录；新增 C/两板/CLI 尚未实现，未运行新工程构建、未上板。
- 本机 python 命令不可用，python3 可用；gcc、mingw32-make 可定位；本轮 PATH 未找到 arm-none-eabi-gcc/sh。旧缓存脚本提供 IDF 路径，实际 git describe 核实本地为 v5.5.2。实施前需恢复可复现工具链，不能把路径存在当成构建成功。

## 仓库证据与设计影响

| 证据 | 发现 | 方案影响 |
|---|---|---|
| code/stm32/03-uart-dma/main.c:282、:286、:330 | IDLE 只通知、SR/DR 清标志、主循环非阻塞输出 | 复用字节流模型，parser 在任务层，损失显式通知 |
| docs/stm32/07-usart.md:143、:209 | 前文 IDLE 判帧与末尾纠正冲突 | 原位修正，不继续追加相反结论 |
| docs/esp32/05-uart-driver.md:168 | 习题答案仍把 timeout_flag 当应用帧尾 | 同步修正 P5 正文/自测 |
| code/stm32/03-uart-dma/README.md:11、:78 | 同一工程说明前后冲突 | 配套文档一起修 |
| code/esp32/02-uart-events/main/main.c:27、:110 | UART1 GPIO10/11，RX driver ring/事件队列，TX ring=0 | 新适配保留已用引脚，发送改有界状态机 |
| code/rtos/01-freertos-lab/FreeRTOSConfig.h | 16MHz、1kHz tick、ARM_CM4F、32 位 tick | F407 watchdog 复用固定内核/时基，不能混用 IDF tick |
| scripts/project-catalog.mjs | scenes 只允许 arm-make [1,2,3,4,5] | 新模式不滥用 scenes |
| scripts/check-firmware.mjs | 场景 hash 路径硬编码 freertos-lab.bin，已有 ELF/bin 复位向量核验 | 新增独立模式入口并复用核验 |
| .github/workflows/quality.yml | S3 矩阵从清单生成，容器 v5.5.2；独立 sdkconfig 并查 target | 登记两新 S3 工程，同时增加故障配置验证 |
| ../10-07-knowledge-capstone/design.md | SAMPLE 恰好 64 字节，INFO/STATUS 后续含更多业务字段 | 响应首状态计入容量，固定前缀后 TLV 扩展；基础阶段不实现记录器 |

表中代码路径均相对于仓库根；capstone 路径相对于任务目录。

## 一手资料与核对结果

### ESP-IDF v5.5.2

- [官方 Watchdogs 文档](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-reference/system/wdts.html)，本轮已通过 curl 下载读取，缓存 .trellis/ref/idf-5.5.2-watchdogs.html。
- 本地源码根 C:/Users/zhugu/.espressif/v5.5.2/esp-idf，git describe 输出 v5.5.2。
- components/esp_system/include/esp_task_wdt.h:24/39/44/60/105/131：trigger_panic、调度器启动后初始化、init 已初始化与 reconfigure 未初始化的 INVALID_STATE 语义、add_user/reset_user。
- components/esp_driver_uart/src/uart.c:1321–1325、1467–1471：内部事件发送失败仅记日志，不能假定应用获得精确事件丢失计数；:1545 为 uart_tx_chars；:1940 核对 TX ring=0 配置允许。
- 设计结论：显式触发 panic/reset、保留 idle 监督并单独健康 user、周期查询 RX，避免默认警告或事件漏通知造成错误教学；断开 OpenOCD 后重启再验收 watchdog。
- [立创官方板卡介绍](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/introduction.html)：本地既有官方 HTML 缓存写明多功能口 GPIO10/11；现有 UART 工程相同引脚。本轮沿用，不宣称重新核对了所有板卡修订的端子顺序。

### ST 官方资料

- [IWDG HAL v1.8.5](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/v1.8.5/Src/stm32f4xx_hal_iwdg.c)：本轮从官方 raw 下载并读取，说明 LSI 驱动、启动后不可停、寄存器更新等待、调试冻结和名义时钟容差。
- [WWDG HAL v1.8.5](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/v1.8.5/Src/stm32f4xx_hal_wwdg.c)：本轮读取，说明 APB1 分频、窗口、EWI、早/晚服务复位。这些 HAL 文件仅供逐字段对照，F407 实现仍为寄存器级。
- .trellis/ref/cmsis/stm32f407xx.h:943–944、10332–10337、12783 起：WWDG/IWDG 基址、RCC 原因位、DBGMCU freeze 位。
- 有效 datasheet/RM0090 尚未获取：既有 f407-ds.pdf 仅 7351 字节，f407-ds.txt 仅 22 字节且不是手册正文；本轮 ST datasheet 下载返回 HTTP 567。不能把旧缓存当已核实 LSI 极值证据。
- [RM0090 官方入口](https://www.st.com/resource/en/reference_manual/rm0090-stm32f405415-stm32f407417-stm32f427437-and-stm32f429439-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)、[STM32F407 datasheet 官方入口](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf) 是实施前待获取资料。本轮未宣称读取其章节/页码。
- 设计结论：2s 仅候选名义计算，WWDG 取窗口中间；参数落代码前必须补齐时序/容差原始证据。下载失败不阻止完成其余规划。

### 访问方式说明

web 搜索工具本轮返回代理 HTTP 404；改用官方 HTTPS curl。首个沙箱联网失败后按权限规则请求提权重试成功。网络异常与官方资料内容无关，不作为技术判断依据。

## 本轮关闭的设计歧义

1. 超时/丢字节后 DISCARD 至下一个 0，明确噪声后的第一帧可能被舍弃。
2. init 不伪造任务首次进展；启动宽限永久结束，避免完整时间回绕后复活。
3. 纯健康状态可恢复，平台首次不健康后的停喂狗决定锁存。
4. 100ms TX 截止期、4 帧队列、半帧失败后补同步分隔符。
5. 同一 UART 不混日志；只宣称实际可观察的错误计数。
6. capstone INFO/STATUS 使用可扩展前缀，64 字节响应容量包含状态码。
7. 五个新工程，既有 scenes 合同不变，新增配置独立构建；硬件观测单列 pending。

## 审阅结论

PRD 保留 W1–W6 与 W-A1–W-A6，全映射到实施步骤。当前没有需要用户补充的产品范围问题；待用户审阅三份文档后进入实现。资料获取、工具链和板上可用性是明确实施检查项，不假定已完成。
