# 双板记录器合同

## 1. Scope / Trigger

修改 code/common/logger、F407/S3 记录器、device-console.py 或 J1/J2 教程时适用。本文记录最终实现，不把宿主模型当作上板证据。

## 2. Signatures

- `sh code/common/logger/probe.sh`：生产核心与每个EEPROM写入切点的恢复断言，Linux附加ASan/UBSan。
- `python3 scripts/device-console.py configure --period 200 --filter-shift 2 --port COMx`：应用到控制状态，下一周期采用；独立 `save` 才持久化。
- `record --seconds 10 --output samples.csv --port COMx`：解码64字节SAMPLE并写CSV；端口必须显式指定，输出路径应为新文件。
- F407 `make MODE=0 FAULTS=0/1`；S3普通/故障独立sdkconfig，target=esp32s3。

## 3. Contracts

- SAMPLE：u32序号/u32毫秒/u32配置代次/u8传感器/u8有效位/u16状态/6×i32原始/6×i32滤波，精确64B、全部LE。
- 配置：schema=1，周期100–1000ms且为10ms倍数，filter_shift=0..6；相同设置不增长generation，相同保存不重复擦写。
- INFO/STATUS保留协议模块固定前缀；TLV 1=传感器/运行，2=配置/代次，3=统计，4=原码比例，5=上次故障有效性/mask。未知tag跳过，截断TLV拒绝，响应≤64B。
- 状态锁只包围纯逻辑；存储IO在锁外。采样优先级高于通信；16槽队列满丢新记录并计数，旧generation在途数据丢弃计数。
- F407真实ADC1由TIM2 TRGO触发、DMA2 Stream0采样，UART在Stream5；EEPROM双128B槽，先失效后写内容、校验、最后提交标记。
- S3真实QMI8658、独立NVS namespace/key；不因NVS初始化失败自动擦整片分区。
- 暖复位故障记录读取后消费一次；后续无新记录的复位不得重复引用旧mask。

## 4. Validation & Error Matrix

| 输入 | 结果 |
|---|---|
| 坏配置/非法schema | BAD_PAYLOAD，原配置保留 |
| SAVE失败 | INTERNAL_ERROR，saved_generation不变 |
| 传感器失败 | 有效位清零、计数，正常进展仍喂狗 |
| STOP | 暂停采样，保留控制/监督进展 |
| 队列满/在途代次过期 | 丢弃且计数，不堵塞采样 |
| 任务停止进展 | 监督锁存停喂狗，记录原因 |
| 断电中断写入 | 模型恢复旧/新完整镜像；实际掉电另验 |

## 5. Good / Base / Bad

Good：真实硬件路径+模型故障测试+待上板标记。Base：正常采样、显式保存与恢复。Bad：用随机数代替传感器，或把成功应答放在落盘前。

## 6. Tests Required

logger/tests.c 测滤波/失效恢复、队列满、代次回绕、配置拒绝和所有写切点；logger-cli.test.mjs 独立解码64B、截断TLV和非法配置本地拒绝；浏览器验证J1/J2可达、完整源码、移动端与实测标记。

## 7. Wrong vs Correct

Wrong：暂停任务就删掉watchdog user。Correct：保留监测来源但停止刷新。
Wrong：NVS错误就erase全分区。Correct：报告错误、使用默认或旧有效配置，不删除其他命名空间。
Wrong：状态锁内做整段EEPROM写入。Correct：先快照后释放锁，外设完成后再更新保存状态。
