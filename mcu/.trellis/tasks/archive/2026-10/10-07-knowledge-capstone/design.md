# 双板记录器设计

## 责任划分

公共 protocol/health 复用阶段 3。新增平台无关 logger 核心（记录结构、过滤、配置校验、队列策略、存储镜像校验）由两板和宿主模型共同调用；驱动、调度与存储写入为平台适配。
目录候选：code/stm32/07-sensor-logger、code/esp32/08-sensor-logger；讲解使用 docs/projects/index.md、01-f407-logger.md（J1）、02-s3-logger.md（J2）。登记 J 前缀、导航、计划清单与生成器 track；不把新项目伪装为已完成的旧章节。

## 数据流与任务

- F407：ADC1/PA0 候选输入，定时触发（外设选型与引脚实施前查 RM0090/数据手册）；DMA/ISR 发布有界样本，采集处理任务做滤波后入队。
- S3：QMI8658 GPIO1/2 I2C，复用已核实地址和量程；每 100ms 取最新样本，不等于传感器内部 250Hz 无损流。
- 两板：采集任务、通信任务、配置服务、监督任务各有明确进展点；记录队列容量初定 16，满时丢新记录并计数，通信慢不让采集无限阻塞。
- 滤波默认整数一阶 IIR（1/4 更新），使用足够宽的中间量；失效数据不当作零值推进滤波，重新有效时重新初始化。

## 对外合同

沿用阶段 3 帧格式，不改变 version/type/CRC。SAMPLE payload 固定不超过 64 字节：
sample_sequence:u32、timestamp_ms:u32、config_generation:u32、sensor_type:u8、valid_mask:u8、status:u16、raw[6]:i32、filtered[6]:i32，共 64 字节，均 LE。
ADC sensor_type=1，仅通道 0 有效，单位为原始 ADC 码值；IMU sensor_type=2，六通道有效，按协议说明区分加速度与角速度原始码；INFO 返回量程/换算关系，不把不同传感器的数字直接比较。

SET_CONFIG 最小字段：schema_version、sample_period_ms、filter_shift；周期范围 100–1000ms（10ms 步进），filter_shift 范围 0–6（0 为直通）。非法输入拒绝且不更改当前配置。响应区分 APPLIED 与 SAVED；记录带 generation 供主机判断切换边界。
STATUS 包括运行状态、接收错误、丢样、队列高水位、存储错误、复位原因与健康状态。

## 参数存储

STM32：AT24C02 的 256 字节作为实验专用配置存储，双 128 字节槽；包含 magic/schema/generation/length/CRC/commit marker。先使目标槽无效，再写完整内容，最后写提交标记，启动选择最新有效槽。按器件页边界写入并 ACK polling，不跨页回绕写。占用空间与会覆盖旧实验数据在说明中显式提示。

S3：独立 NVS namespace/key 保存同一逻辑配置 blob，提交成功后才报告 SAVED。错误不自动擦整片分区，不影响其它命名空间。不可用或损坏时报告并使用安全默认值。

generation 比较使用有界模序号规则；旧 schema 明确迁移或拒绝，不按新布局解释任意旧字节。宿主故障模型逐步中断写入，重启必须得到旧/新完整配置或清晰默认状态。

## 失效处理

传感器失联仅影响 valid_mask/status，通信和健康监督继续；不可用数据不通过填零伪装正常。
通信积压有丢弃计数，主机重连能重新查询状态。
任务卡死导致监督不喂狗，硬件复位并报告原因；测试命令受测试构建开关保护。
用户 STOP 停采样但监督/通信继续，不能误触发看门狗。

## 验证、兼容和回退

两板都用 scripts/device-console.py 的同一脚本化验收，板卡差异仅在端口和 sensor_type。
配置损坏/中断写入的模型调用同一镜像校验逻辑，真实 EEPROM/NVS 写入另做实际测试。硬件没接时构建/模型必须完成，结果标 pending。
主机工具不自动发现后立即写配置或烧录；必须显式选设备和命令。公共契约改动需同步两板、CLI 和文档后再提交。
