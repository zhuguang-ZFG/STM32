# 三路线深化：共同设计

## 责任与顺序

本轮是一个包含三项可独立验收交付的总任务。采用 STM32 → FreeRTOS → ESP32-S3 → 集成顺序，由主会话直接实现及检查。
子任务必须写明依赖；树的排列不构成依赖。总任务在三批完成后才实施共享入口与最终规范同步。

共同上下文：CONTRIBUTING.md、.trellis/spec/docs-site/{index,content,structure}.md、两份 firmware 索引及 research/baseline-and-sources.md。
动画引用规范发生冲突时遵循 CONTRIBUTING.md 的 Markdown 图片语法，让 VitePress 处理 base。现有 structure.md 的 raw img 旧描述由总任务统一修正。

## 内容组织

沿用现有页面路径和编号，补齐正文，不新建平行课程。
顺序：钩子→精髓→怎么读→学习目标→先修→quick win→动画→板卡/版本前提→小节结构→实质正文→记忆锚点→实验→常见坑→自测→概念/源码对照→下一站。
多个动画可在前部给出索引，具体解释放到对应正文，避免读者在动画和寄存器说明之间反复跳页。
quick win 的“10 分钟”以环境、依赖、编译工具已就绪为前提；首次安装时间单独说明。

每章走通一次因果链：
- STM32：输入时钟/控制位 → 硬件状态 → 引脚或内存变化。
- FreeRTOS：调用 API → 内核对象变化 → 就绪/阻塞/内存状态 → 观察结果。
- ESP-IDF：配置对象 → 驱动/HAL/芯片能力 → ISR/缓冲/用户任务或输出引脚。

## 动画合同

保持独立 SVG+SMIL、viewBox 宽 720、既有四色和不少于 12px 字号；不引入播放器、动画库或位图生成。
每图提供 title/desc、阶段编号、箭头及文字标签。阶段切换采用离散时间，阶段与寄存器值绑定；不用颜色单独传递状态。
布局为简图与短字幕，窄屏下长推导由图外文字承担。未播放时也能看到足够解释机制的静态布局；逐阶段文字另在正文列出。
这轮不承诺暂停/拖拽控制；若后续要交互控制，需单独设计组件，不能仅给 img 加按钮却无法控制内部 SMIL。

| 编号/文件 | 章节 | 动作与必须表达的结论 |
|---|---|---|
| S-A1 rcc-clock-tree.svg | S2 | HSE 示例→M/N/P/Q→总线；分清系统、外设、TIM 三种时钟 |
| S-A2 tim-pwm-counter.svg | S6 | CNT 递增、ARR 回绕、CCR 比较；频率和占空比分工不同 |
| S-A3 tim-input-capture.svg | S6 | 两个边沿锁存 CCR；一次回绕下的模差和适用前提 |
| S-A4 uart-frame.svg | S7 | 0x55 与 0x41 对照，起始/停止和 LSB 顺序逐位显示 |
| S-A5 usart-txe-tc.svg | S7 | 数据寄存器与移位寄存器两级；可写下一字节不等于最后一位发完 |
| S-A6 dma-circular-buffer.svg | S8 | 写位置、读位置、NDTR 回装；生产追上消费会覆盖 |
| F-A1 task-create-stack.svg | F1 | 栈与 TCB 分配/初始化→就绪；初始现场为第一次恢复准备 |
| F-A2 task-notification.svg | F6 | 发送者改值/状态，单个目标任务等待与取走；计数与覆盖不同 |
| F-A3 event-group-wait.svg | F6 | ANY/ALL 两等待者，检查满足条件后再汇总清位 |
| F-A4 software-timer-service.svg | F6 | 命令队列→守护任务→回调；回调串行执行，阻塞导致延迟 |
| F-A5 heap4-coalesce.svg | F7 | 释放相邻块合并，不相邻块仍碎片；总空闲不等于最大可分配块 |
| P-A1 gpio-matrix-routing.svg | P2 | 外设信号→Matrix/IO_MUX→有效焊盘；路由自由受引脚资源约束 |
| P-A2 idf-uart-events.svg | P5 | 字节 FIFO→ring→用户 buf，事件描述另走 queue→task |
| P-A3 ledc-timer-channel.svg | P7 | timer 定频率/分辨率，channel 定 GPIO/duty，fade 更新比较值 |

S8 同时修订 dma-pingpong.svg，加入两块缓冲的当前所有者、CPU 完成期限和超期覆盖反例。

## 源码与版本

STM32 使用现有 GNU Arm 裸机结构和 SPL 对照，新增库引用先取得真实版本文件再逐行解释。资料缓存放已忽略的 .trellis/ref/；记录下载地址、版本/提交与校验，发布正文引用稳定地址。
F 篇固定上游 FreeRTOS-Kernel V11.1.0、ARM_CM4F 单核端口。P 篇建议以本机可用的 IDF v5.5.2 为实施基准，归于仓库已规定的 v5.5.x；开始前用源码版本定义及 git 信息确认。
本机 IDF 头文件标记内核为 V10.5.1 的 SMP 修改版，不能用 F 篇的行号、任务栈参数单位或单核调度结论直接替换 P 篇。
第三方依赖在构建准备步骤获取固定版本；不把机器上的绝对路径写成读者必需配置，不提交大份未引用的源码缓存。

## 兼容性与风险

- 既有 URL 不变，新资源走 /anim/ Markdown 引用；构建 base 为 /mcu/。
- STM32 最小 quick win 优先保留 HSI 默认时钟，避免依赖尚未核实的 HSE 晶振；168MHz 推导是显式条件示例，不能套到 HSI 工程。
- ESP32 引脚必须落实到实战派对应板版本/原理图，再写默认值；当前没有已核实的扩展口映射，不提前填常见开发板引脚。
- 工具链与硬件访问是执行门禁。构建结果与上板结果分栏记录，禁止把编译通过写成实测通过。
- 回滚按子任务的章节/资源/示例成组处理；公共入口最后更新，避免展示尚未通过验收的成稿。
