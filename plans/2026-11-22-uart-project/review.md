# 从点灯到串口命令：完整工程与丢失后的同步

上一轮已将 GPIO 工程合入主线，本轮推进 UART DMA 的构建、协议边界和配套讲解。前轮属于实质进展，整书目标仍未完成。

## Sepia review（先审后改）

类型：中文技术教程。范围：UART README、上手卷串口步骤、第 13/14 章 F103 对照、例程索引。作者模型未知；执行模型 GPT-6（未提供子版本）。Prose layer：author=none，executor=prior。依据 professional-pass、tech-articles、discourse §1–3、style-pass 与 zh；参考语域取已有 GPIO README、上手卷与第 13 章。

| 证据 | 缺陷 | 对应修订 |
| --- | --- | --- |
| README「缺完整 HAL/启动/链接工程」 | AT→OK 之前仍需读者补整个工程 | 固定 CubeF1 v1.8.6，提供 CMake / 启动 / 链接 / 时基及三条 IRQ 的实际向量检查 |
| 「head/tail 都是 volatile，天然适配…无锁模型」 | volatile 不提供 C 内存模型的发布/获取顺序 | 单生产者 / 单消费者用 C11 acquire/release，明确中断同抢占级及目标无锁条件 |
| 「超长，丢弃整行」 | 实际仅清零长度，后缀仍会执行 | DISCARD 到 CR/LF；严格校验 LED/ECHO 参数，拒绝 NUL 等无效输入 |
| 「满则丢」 | 没有丢失计数与协议重同步，可能拼接前后残片 | 有序 gap 标记进入队列；丢失后丢弃到行结束，计数可查 |
| 章正文「不是 F103 全工程验证」 | 工程化完成后将过期 | 以实际 ARM / 宿主 / 硬件三档证据更新，不预填硬件成功 |

Style scan：没有需要单独修饰的语气问题，首要问题是事实、可执行性与过量复制代码。保留数字、接线、公式与既有来源身份；缩短 README 的同义代码抄写，构建步骤紧接接线。Deferred：真实写板、冷复位、连续流吞吐和仪器故障注入。Passed：中性语域、无口号结尾；Verdict：refactor，按缺陷逐项修正。用户已授权持续修改，不增加确认环节。

## 来源与对比

- 本地两份 zlib 参考书核验沿用 `.temp/reference-books/REFERENCE_REVIEW.md`：野火样本物理第 210 页的下载验证组织、Mastering STM32 第二版的 DMA 解释顺序；原书文件不发布，板型不照搬。
- 一手源码：STM32CubeF1 `42472d601caa457b02d849c7de5f9792629ee324` / v1.8.6，HAL `77fbb30b7a1d02533980400083e48c559aae5a4f`。实际检查 `stm32f1xx_hal_uart.c` 的 ReceiveToIdle、HT/IDLE/TC、UART_EndRxTransfer、UART_DMAAbortOnError 和 AbortReceive。
- 社区对照：MaJerle/stm32-usart-uart-dma-rx-tx，2026-11-22 查询提交 `c242589d766eada3ad1d795630f2b1c2482a2af8`。比较事件与消费边界，不能把其循环 DMA 实现当成本普通模式已经无损的证据。
- Context7 检索返回 monthly quota exceeded；转查已固定提交的官方 GitHub 源码与本地检出，不把检索失败记作已获取文档。

## 设计与验收

1. 普通 DMA 64 字节，HT 不消费或重装；IDLE/TC 只交付当前前缀一次。重装失败进入可诊断停机。
2. 软件环保留一个空槽，511 个 uint16 项：字节 0–255，额外值 256 表示字节流有缺口。生产者在首个丢失后的字节之前放入标记；消费者按原顺序丢弃当前残行，到 CR/LF 恢复。已排队的完整前行仍可执行。
3. UART 错误记录 ErrorCode、标记缺口，AbortReceive 后清状态并重装；失败不伪装恢复。普通模式重装间隙与线路物理丢失仍须实测。
4. 主循环拥有解析器和执行器；两个接收 IRQ 同抢占优先级，生产者不嵌套。环的 head/tail 用 acquire/release；编译要求 short 原子无锁，ARM 实际链接检查不得依赖 libatomic。
5. 完整生产 main、解析器、回调参与宿主回归；实际 ARM 二进制核验 SRAM/Flash、SysTick/USART1/DMA1_Channel5 三个向量和许可证。原有回归入口继续覆盖旧三项，并扩展新失败边界。
6. 新原创图展示命令在 DMA 段之间拼接与丢失后 DISCARD；#001、IG-004 双列对比、C-22 既有配色。数字和 CR/LF 仍在正文，非测量截图。

全书剩余：其他外设完整工程、RTOS 状态图文与可执行证据、L3–L5 故障与交付材料、实体板与阅读器验证。不得以本轮 CI 代替整书验收。
