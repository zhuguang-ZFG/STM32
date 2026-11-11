# 协议与健康监测设计

状态：规划待审阅，2026-10-07。证据见 [planning-evidence.md](research/planning-evidence.md)。本文拥有公共 wire/API 合同；业务配置和 SAMPLE 内容由后续 capstone design 拥有。

## 1. 交付与复用边界

| 新增工程 | 清单类型 | 责任 |
|---|---|---|
| code/common/reliability | host-probe / probe.sh | protocol.h/.c、health.h/.c、向量与宿主行为测试 |
| code/stm32/05-framed-protocol | arm-make | USART1 字节流、INFO/STATUS、非阻塞响应 |
| code/stm32/06-watchdog-health | arm-make | FreeRTOS 进展监督、IWDG 主例、WWDG 对照、复位原因 |
| code/esp32/06-framed-protocol | esp-idf / esp32s3 | UART1 适配、同一命令路径 |
| code/esp32/07-watchdog-health | esp-idf / esp32s3 | IDF 进展监督、TWDT/IWDT 边界、复位原因 |

后续 STM32 07-sensor-logger、S3 08-sensor-logger 保留给 capstone。公共 C 只依赖标准库，不包含 RTOS/芯片头、不动态分配。Python 独立实现 codec，通过共享向量交叉验证。

平台协议工程将 transport 与 main 分文件；同平台 watchdog 工程通过源文件列表复用 transport，不复制 codec。干净 checkout 所需项目文件全部入库，上游 FreeRTOS 内核仍按既有固定版本获取。

## 2. 帧格式与内存所有权

线上为 COBS(raw) + 0x00，raw 按字节序列化，不强转 packed struct：

| 偏移 | 字段 | 格式 |
|---|---|---|
| 0 | version | u8，固定 1 |
| 1 | type | u8 |
| 2 | sequence | u16 LE |
| 4 | payload_length | u16 LE，0..64 |
| 6 | payload | 0..64 字节 |
| 6 + length | CRC | u16 LE |

CRC-16/CCITT-FALSE：poly=0x1021，init=0xffff，refin/refout=false，xorout=0，覆盖 CRC 之前全部 raw 字节；检查串 123456789 得 0x29b1。最大 raw=72、COBS 部分=73、含分隔符=74 字节，容量以常量计算并静态断言。

编码接口接受调用者 buffer/capacity，返回状态与实际长度；先校验容量/负载/指针再写输出，失败不能留下可发送的半帧。frame_t 自有 64 字节 payload。逐字节 feed 返回无帧/有效帧/错误；调用者在下次 feed 前消费或复制 frame，不让异步任务保存 scratch 指针，不使用可重入回调。

### 最小命令合同

type 保持原规划：INFO=0x01、STATUS=0x02、START=0x03、STOP=0x04、SET_CONFIG=0x05、SAVE_CONFIG=0x06、SAMPLE=0x10、TEST_FAULT=0x7f。响应为 request type|0x80，回显 sequence，payload 首字节为状态。

状态码：OK=0、UNSUPPORTED=1、BAD_PAYLOAD=2、BUSY=3、INTERNAL_ERROR=4。64 字节上限包含响应状态字节，不能把 64 字节请求直接加一字节返回。未知请求返回 UNSUPPORTED，收到响应类型不再应答。SAMPLE 为设备主动上报，基础工程不发送。

INFO/STATUS 请求负载为空。INFO 成功响应前缀为 status:u8、schema:u8=1、platform:u8、capabilities:u16LE；platform 1=F407、2=S3；能力 bit0=protocol、bit1=health、bit2=test_fault，其余保留。

STATUS 成功响应前缀为 status:u8、schema:u8=1、uptime_ms:u32LE、reset_reason:u32LE、required_mask:u8、overdue_mask:u8、flags:u8、rx_ok:u32LE、rx_error:u32LE、tx_drop:u32LE，共 25 字节。flags bit0=grace、bit1=restart_latched，其余保留；无 health 时掩码/flags 为 0。reset_reason 保留平台原始原因，CLI 根据 platform 解释。

capstone 的量程/队列/存储扩展采用固定前缀后的 tag:u8、length:u8、value[length]；未知 tag 跳过，截断 TLV 拒绝，总负载仍≤64。tag 由 capstone 冻结，基础工程不添加。START/STOP/SET/SAVE 本批返回 UNSUPPORTED；后续设置命令使用目标状态，不用 toggle，不承诺跨重启 exactly-once。

## 3. 解析状态与恢复

状态：EMPTY、COLLECT、DISCARD；初始化 EMPTY。

| 输入/事件 | 行为 |
|---|---|
| EMPTY 收到 0 | 忽略空分隔符 |
| EMPTY/COLLECT 非零字节 | 收集，最多 73 字节，更新最后活动时间 |
| COLLECT 收到 0 | 解码，依次验证编码/最小长度/version/声明长度/CRC；成功交付，否则只记首个拒绝原因；回 EMPTY |
| 第 74 个非零字节 | oversize 加一，进入 DISCARD |
| COLLECT 间隔达到阈值 | timeout 加一，进入 DISCARD；当前到来字节也按 DISCARD 处理 |
| 已知 UART 丢失/错误、DMA 不可信积压、软件 RX 满 | transport_loss 加一，清部分帧，进入 DISCARD |
| DISCARD 收到非零 | 丢弃，不对同一坏片段重复计 oversize/timeout |
| DISCARD 收到 0 | 重新同步完成，回 EMPTY |

默认间隔阈值 100ms，elapsed >= timeout 即过期；poll(now) 在无新字节时也处理过期。阈值为 1..2^31-1，无符号差值处理回绕；poll 间隔必须小于半个计时周期。

恢复保证是“坏片段后一个分隔符，再之后的完整合法帧可接受”。噪声/残留与下一帧直接粘连时，下一帧可能被丢弃；CLI 连接与超时重试前先发送额外 0。超时不能立即把残留尾部当新帧。

cobs/version/length/crc/oversize/timeout/transport_loss 使用饱和 uint32 计数，rx_error 为饱和聚合。序号不代替 CRC/认证，CRC 有碰撞概率。

时间标记表示适配层观察到字节/块的单调时间，不声称逐字节物理到达时刻。同一带时间标记的字节序列以不同分块 feed 应等价；驱动积压后不能倒推真实线上空闲，应用定界仍依赖分隔符。

## 4. 平台传输与背压

两端 115200 8N1、无硬件流控。F407 USART1：PA9 TX/PA10 RX、AF7；S3 UART1：GPIO10 TX/GPIO11 RX。USB-TTL TX 接板 RX、RX 接板 TX，3.3V 电平、共地。S3 扩展口还带 5V 电源脚，配图需按板卡修订核对，不能猜端子顺序。

F407 协议口只发二进制，调试走 SWD/内存变量；S3 文本日志保留默认 UART0。故障构建不改变端口用途。

F407 复用已有 DMA 环形位置模型、HT/TC/IDLE 服务语义，默认 DMA 256 字节、软件 RX 512 字节。ISR 有界搬运/通知，单一主循环或任务解析。索引与失步标记用短临界区或既有正确发布规则；调用 FreeRTOS FromISR 时遵守优先级阈值，不用裸 volatile 冒充同步。

115200 8N1 为 11520 字节/秒：半 DMA 128 字节约 11.11ms，512 字节约 44.44ms；计划消费者至少每 5ms 服务一次。它们是配置预算，需故障注入和板上测量验证。HT/TC 同时积压、UART 错误或 RX 满使当前片段失效，进入 DISCARD。

S3 RX ring=1024 字节、事件队列=20，UART task 独占 parser/TX。等待事件≤5ms，并周期调用 uart_get_buffered_data_len、分块读取，避免通知丢失后永远不取数。每轮服务量有上限；FIFO_OVF/BUFFER_FULL/FRAME_ERR/PARITY_ERR/BREAK 经错误路径处理，溢出时 flush、清事件积压并通知 parser 失步。

IDF 内部事件队列满可能只写驱动日志，没有公共精确丢失计数。只统计实际观察的事件与自有队列丢弃，不能把计数零解释成线上无错。周期取数、长度/CRC 和同步机制共同处理后果。

TX 固定 4 个完整帧槽位，满时丢新响应并记 tx_drop，不能覆盖正在发送的帧。单一发送者分段推进：F407 查 TXE，S3 TX ring=0 时使用 uart_tx_chars 返回的实际数量。零进展就让出执行，不忙等。

每帧总发送期限 100ms；超时丢弃余部，下一帧之前先发同步分隔符，防止前帧尾部污染后帧。最大帧正常线时约 6.43ms。partial/zero write、超时、队列满用 transport stub 驱动真实发送状态机测试。

## 5. 健康监测 API 与时间

- bool health_init(health_t *ctx, uint32_t required_mask, const uint32_t deadline_ms[8], uint32_t startup_grace_ms, uint32_t now_ms)
- bool health_progress(health_t *ctx, uint8_t task_id, uint32_t now_ms)
- health_result_t health_evaluate(health_t *ctx, uint32_t now_ms)

相对旧草案，init 返回成败，evaluate 接受可变 ctx 以永久结束宽限。required_mask 非零且仅低 8 位，必需项 deadline 在 1..2^31-1，grace 在 0..2^31-1。非法配置不可喂狗，非法 ID/空指针拒绝。result 含 may_feed、overdue_mask、in_grace、config_valid。

记录 seen_mask、各项最后进展与 grace_active，初始化不伪造任务已经运行。宽限内允许监督喂狗；全体必需任务首次上报或 now-start >= grace 时永久关闭宽限。结束后未上报项立即过期，已上报项在 now-last >= deadline 时过期。永久关闭位避免完整 uint32 回绕后宽限重新生效；仍要求周期调用小于半个计时周期。

公共模块不加锁。平台用短临界区串行化 progress/evaluate，S3 同一 portMUX 保护跨核；进入锁后再采时间，避免等待锁后写入旧时间。F407 本例 1kHz tick；S3 由 esp_timer_get_time()/1000 截为 uint32 毫秒，不能把 IDF tick 当毫秒。

默认 worker/communication 每≤100ms 完成一次有界工作，各 deadline=500ms，监督周期=50ms，启动宽限=1000ms。工作周期完成后上报；通信无数据但完成服务检查仍算进展；传感器报错但正常处理并让出执行也算进展。STOP 不停止控制任务服务循环。

health 纯逻辑可显示“任务恢复后当前状态健康”，但平台首次观察不健康后锁存 restart_latched、保存首个 overdue_mask、停止喂狗，迟到进展不能解除。锁存只随本次复位消失，避免间歇心跳撤销重启决定。

## 6. 看门狗与复位证据

### F407

FreeRTOS V11.1.0/ARM_CM4F；寄存器级外设；HSI/PCLK1=16MHz、tick=1kHz。IWDG 使用 LSI，启动后不能按普通计时器停止。候选 prescaler=64、reload=999，在名义 32kHz 下为 2s；不是实测或精度保证。PVU/RVU 等待有时限，失败不可报告成功。

复位先保存 RCC_CSR 再清 RMVF，多标志原样上报。可增加普通 SRAM .noinit 故障记录（magic/version/overdue_mask/CRC），从 bss 清零范围排除；冷启动、原因不匹配或 CRC 失败都标无效。只辅助暖复位诊断，不宣称掉电保存，启动保留行为须上板验证。

WWDG 与 IWDG 主例分构建模式。候选 PCLK1=16MHz、prescaler=8、Counter=0x7f、Window=0x5f，100ms 为窗口中间服务点；写入前检查计数，边界按 RM0090 确认。normal/early/late 三场景；EWI 仅留有界证据，不无条件喂狗。不要把 IWDG 的 500ms 健康期限照搬到 WWDG 短窗口。

DBGMCU IWDG/WWDG freeze 位与外部调试器设置分别记录。硬件参数实现前必须补齐器件 LSI min/max 和 WWDG 窗口原始手册依据；当前缓存不是有效 datasheet，不能据此写保证值。见执行计划证据检查。

### S3

在调度器启动后由单任务配置 TWDT；先 init，仅“已初始化”的 INVALID_STATE 分支改用 reconfigure，其他错误进入失败路径。timeout_ms=2000、idle_core_mask 覆盖启用核、trigger_panic=true，配置选择 panic 后复位。保留 idle 监督，另注册专属 health user，只有 may_feed 且未锁存才 reset_user。

保留 IWDT 处理禁中断/长临界区，按 IDF 版本核对 tick/PSRAM 相关限制。任务故障采用停止进展但让出 CPU，使实验命中 TWDT；监督任务停止也必须留下未服务的 health user。

启动保存 esp_reset_reason()。可用 RTC_NOINIT_ATTR 保存有 magic/version/CRC 的故障记录，仅匹配的暖复位原因和 CRC 通过时解释。panic/reset 原因以实际返回为准，不将所有 TWDT 故障硬编码成同一原因。OpenOCD 可禁用 watchdog 且继续运行后不重启它；复位验收须断开调试器并重新启动。

### 故障开关

默认 RELIABILITY_TEST_FAULTS=0 / IDF Kconfig disabled。TEST_FAULT 请求为 fault:u8、task_id:u8，仅测试构建支持：1=暂停某任务进展、2=暂停监督服务。WWDG early/late 为独立测试构建场景。非法参数拒绝，普通构建返回 UNSUPPORTED；故障需显式命令启动，响应入队后有界延迟执行，不能上电自行卡死。没有任意地址读写/执行命令。

## 7. CLI 与教材

scripts/device-console.py 支持 self-test、info、status、command、fault、log；参数包括 port/baud/timeout/output。仅串口子命令加载 pyserial，依赖在独立 requirements 文件固定版本；离线 codec 测试只用标准库。

一次只挂起一个请求，绝对单调响应期限，必须匹配 sequence 和 response type；无关帧不能延长期限。序号模 65536；INFO/STATUS 有限重试、重试前发同步 0，fault 不自动重试。重连先 INFO/STATUS，废弃旧挂起请求；不承诺序号跨会话唯一。

不自动探测后写配置/烧录；开口不主动拉 RTS/DTR 复位，并说明转串口驱动仍可能产生瞬态。CSV 保存时间戳、方向、type、sequence、payload hex、解析状态并正确转义。超时/串口故障/设备拒绝有非零退出码，不把无响应写成成功。

教材：docs/c/08-framed-protocol.md（C8）、docs/stm32/17-watchdog-reset.md（S17）、docs/esp32/13-watchdog-health.md（P13）。完整源码 VitePress import 内嵌；同步 sidebar、各 track index、课程规划事实源与 README 生成块。直接修正 S7/P5 与原工程 README 的 IDLE/timeout 判帧旧答案。实验在三篇内列步骤、预期、实际/pending，不新增 E 编号。

## 8. CI 与回退

公共 probe.sh 跑生产 C 行为测试和 Python 交叉向量；Linux CI 必跑 ASan/UBSan，Windows 普通构建。缺工具不静默跳过后报全绿。固定种子随机分块加全部单切分点，覆盖解析失步、时间回绕、健康首报/宽限、TX partial write/背压。

catalog.scenes 只支持 FreeRTOS 固定 1..5，check-firmware 还硬编码 freertos-lab.bin。新增模式不能塞入 scenes。保留默认 build/ 核验，为 watchdog 增加显式构建/校验入口：build/iwdg-test、build/wwdg-normal、build/wwdg-early、build/wwdg-late，复用 SP/Reset ELF/bin 验证；正常→故障→正常切换不能复用旧对象。

S3 清单自动增加两个工程；CI 在独立 sdkconfig/build 下构建默认和启用故障模式，并验证 target=esp32s3，不用旧本地 sdkconfig 证明目标正确。公共 wire/API 变化同步 C、Python、两板、教材和 capstone 调用方。

阶段验证失败先修该阶段，不推进依赖工程。回退只覆盖本任务新增模块及登记/文档，不回退已有 UART/RTOS 或其他任务成果；无上板证据时只报告软件验收。
