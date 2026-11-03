---
title: 动画演示中心
---

# 动画演示中心

把全站**机制动画**集中到一页：每一张都是构建期内联的 SMIL 动画，可播放/暂停、跟随深浅主题换色。只把图当"装饰"就辜负了它们——**动画本身就是结论**：读的时候看它怎么"动"，暂停在想不通的那一步。

> 每张动画一轮 8–18s，四个阶段循环。点播放/暂停，或直接看进度条走。下划线文字是给读屏和"关掉动效"读者看的完整因果，没在动也能看懂。

## 怎么看：三件武器

动画不是配图，是"把因果关系演给你看"。全站动画只用三件武器，看懂它们就懂所有图：

| 武器 | 长什么样 | 它在说什么 | 样板 |
|---|---|---|---|
| **爬线** | 波形/连线像被逻辑分析仪逐点抓出来 | 数据在**顺序流过**，不是瞬间出现 | [USART 帧](/stm32/07-usart.md)、[I2C 时序](/stm32/11-i2c.md) |
| **生长箭头** | 线条从发端插到收端 | 报文/指针"在路上"，到尖端才算抵达 | [TCP 握手](/esp32/08-wifi.md)、[上下文切换](/rtos/freertos/02-context-switch.md) |
| **节拍脉冲** | 一个点或灯按固定频率闪 | 某事"**重复发生**"，周期本身就是结论 | [volatile 访存](/c/03-volatile.md)、[SysTick](/stm32/05-systick.md) |
| **接力流转** | 一个对象沿路径持续移动 | 流程/接力在**持续进行**，不是快照 | [四步构建](/build/01-four-steps.md)、[ESP32 启动](/esp32/01-arch-boot.md) |

判断标准只有一条：**运动本身就是结论的一部分**——把动画停在任何一帧，画面都要能自己说话。

## 各板块动画

按板块分组陈列；每张图对应的正文章节在板块标题与图注里都能对上号，点导航栏对应板块即可回去接着读。

## C 语言精髓

![C 篇路线总览：从嵌入式 C 到帧协议的 8 站精要](/anim/c-roadmap.svg)

![volatile 的访存合同：读一次 vs 每次读](/anim/volatile-as-if.svg)

![删掉三处 volatile，-O2 把 37 条的 main 删成 2 条](/anim/volatile-main-collapse.svg)

![全局变量在 .bss/.data 的两地生活](/anim/memory-two-homes.svg)

![指针三件事：取地址 · 存门牌 · 解引用登门](/anim/pointer-arrows.svg)

![环形缓冲两派：满/空判定与回绕](/anim/ring-buffer.svg)

![C8 帧协议：逐字节解析状态机与重新同步](/anim/c08-frame-parse.svg)

![函数指针与状态机：查表派发的机器码](/anim/fsm-dispatch.svg)

![结构体与 ABI：对齐、填充与位域陷阱](/anim/struct-alignment.svg)

![函数调用栈帧：压栈与弹栈](/anim/stack-frame.svg)

![C0 嵌入式 C vs 应用 C：四个维度的差异](/anim/embedded-c-diff.svg)

![UB 编译器优化陷阱：源代码 → 推理 → 汇编 → 运行时偏离](/anim/ub-compiler-trap.svg)

## 构建与运行全过程

![B 篇路线总览：从四步构建到 SWD 调试的 8 站流水线](/anim/build-roadmap.svg)

![ELF 的两副目录：文件视图与段视图](/anim/elf-two-views.svg)

![上电到 main 的启动时序](/anim/boot-sequence.svg)

![B1 四步构建：main.c 到 blink.elf 的流水线](/anim/build-four-steps.svg)

![B3 链接脚本：.data 的两个住址（VMA/LMA）](/anim/data-vma-lma.svg)

![B2 ELF 双重视角：节表给链接器，程序头给装载器](/anim/elf-sections.svg)

![B7 构建系统：依赖图与局部重建](/anim/build-dep-graph.svg)

![B0 工具链接力赛：预处理→编译→汇编→链接](/anim/toolchain-relay.svg)

![通用环境搭建五步闭环：安装→配置→编译→烧录→点灯](/anim/env-setup-flow.svg)

![B5 map 与体积审计：size → map → nm 三板斧](/anim/map-size-audit.svg)

![B6 SWD 调试链路：GDB → OpenOCD → ST-Link → DP/AP → 内存](/anim/swd-debug-chain.svg)

## STM32F407 寄存器主线

![S 篇路线总览：从 RCC 到 IAP 的 17 站闭环](/anim/stm32-roadmap.svg)

![RCC 时钟树：168MHz 从哪来](/anim/rcc-clock-tree.svg)

![提频六步：先降速，再提速](/anim/rcc-six-gates.svg)

![GPIO 配置流程：从寄存器到点亮](/anim/gpio-config.svg)

![总线矩阵：内核与外设怎么连](/anim/bus-matrix.svg)

![位带别名：位操作到字操作](/anim/bitband-alias.svg)

![中断现场入场：硬件压栈八字](/anim/irq-entry.svg)

![NVIC PRIGROUP：4 位优先级的切法](/anim/nvic-prigroup.svg)

![NVIC 抢占判定：谁能打断谁](/anim/nvic-preempt-arbitration.svg)

![SysTick 倒数与 COUNTFLAG 读清](/anim/systick-tick.svg)

![USART 帧：逐位抓出来的波形](/anim/uart-frame.svg)

![USART TXE/TC 发送节拍](/anim/usart-txe-tc.svg)

![HAL UART 初始化对账：MspInit → SetConfig → 使能](/anim/uart-hal-init-path.svg)

![DMA 环形缓冲搬运](/anim/dma-circular-buffer.svg)

![DMA 双缓冲乒乓切换](/anim/dma-pingpong.svg)

![DMA EN 可改窗口与 HAL 两段式](/anim/dma-hal-en-window.svg)

![EXTI 信号路由：GPIO → SYSCFG → NVIC](/anim/exti-signal-routing.svg)

![SAR 逐次逼近：12 轮二分](/anim/sar-successive.svg)

![DAC 三重奏：TIM 打拍、DMA 递谱、DAC 开嗓](/anim/dac-trio.svg)

![I2C 时序：起始/停止/应答](/anim/i2c-timing.svg)

![SPI 时序：主从沿采样](/anim/spi-timing.svg)

![SPI 移位寄存器环：为什么发送 == 接收](/anim/spi-shift-register.svg)

![TIM PWM：计数器到占空比](/anim/tim-pwm-counter.svg)

![TIM 输入捕获：边沿定格](/anim/tim-input-capture.svg)

![HAL TIM 三段初始化对账](/anim/tim-hal-init-path.svg)

![HardFault 取证：故障升级与栈帧挖 PC](/anim/hardfault-forensics.svg)

![IAP 跳转接力：关断、换栈、改向量、跳 reset](/anim/iap-handoff.svg)

![低功耗三档对比：Sleep/Stop/Standby](/anim/stm32-pwr-three-modes.svg)

![看门狗双雄：IWDG 只管活着，WWDG 还管节奏](/anim/watchdog-window.svg)

![S15 GPIO_Init 解剖：结构体 → 位偏移 → 寄存器](/anim/spl-gpio-init.svg)

## FreeRTOS 精讲

![为什么需要 RTOS：超级循环 vs 平行世界](/anim/why-rtos.svg)

![超级循环里的接收死等：串口等一个字节，LED 也停止翻转](/anim/superloop-uart-block.svg)

![任务创建与栈初始化](/anim/task-create-stack.svg)

![FreeRTOS GDB 调试实战：指认 TCB 与栈内容](/anim/freertos-gdb-debug.svg)

![上下文切换：PendSV 偷梁换柱](/anim/context-switch.svg)

![就绪链表插入：O(1) 调度](/anim/list-insert.svg)

![队列传送：生产到消费](/anim/queue-passing.svg)

![信号量与互斥锁](/anim/semaphore-mutex.svg)

![优先级反转与继承](/anim/priority-inversion.svg)

![优先级继承协议：互斥锁如何消除反转](/anim/priority-inheritance.svg)

![任务通知：轻量信号量](/anim/task-notification.svg)

![事件组等待](/anim/event-group-wait.svg)

![软件定时器服务](/anim/software-timer-service.svg)

![heap_4 内存合并](/anim/heap4-coalesce.svg)

![vTaskDelay 生命周期：阻塞、调度与唤醒](/anim/vtaskdelay-lifecycle.svg)

![移植 FreeRTOS：三异常改名接管](/anim/freertos-port.svg)

## ESP32-S3 + ESP-IDF

![P 篇路线总览：从环境搭建到音频全链路的 13 站纵深](/anim/esp32-roadmap.svg)

![上电三棒接力：ROM → bootloader → app](/anim/esp32-boot-relay.svg)

![IRAM 纪律：Cache 一关，Flash 里就没有代码了](/anim/iram-discipline.svg)

![GPIO 引脚矩阵路由](/anim/gpio-matrix-routing.svg)

![IDF UART 驱动事件](/anim/idf-uart-events.svg)

![IDF 总线驱动两级模型：先配线，再认人](/anim/esp32-driver-layers.svg)

![LEDC 定时器与通道](/anim/ledc-timer-channel.svg)

![TCP 握手：报文在路上](/anim/tcp-handshake.svg)

![ESP-NOW 三步：init → add_peer → send](/anim/esp32-espnow-direct.svg)

![OTA 双槽轮流坐庄：下载 → 切槽 → 自检 → 回滚](/anim/esp32-ota-rollback.svg)

![NVS 页面生命周期：追加写、搬迁与擦除](/anim/nvs-page-lifecycle.svg)

![ESP32 睡眠矩阵：Light 眯一会 · Deep 睡死 · ULP 守夜](/anim/esp32-sleep-matrix.svg)

![实战派音频全链路：控制走 I2C，声音走 I2S](/anim/esp32-audio-path.svg)

![ESP32 任务看门狗：TWDT 的订阅、喂狗与超时链条](/anim/esp32-twdt-chain.svg)

![P3 Kconfig 三阶管线：定义 → sdkconfig → sdkconfig.h](/anim/kconfig-pipeline.svg)

## GD32 双系对照

![GD32 路线总览：G 篇对照 + V 篇 RISC-V 双线并行](/anim/gd32-roadmap.svg)

![GD32 RCU 时钟树：与 STM32 逐字段对照](/anim/gd32-rcu-clock.svg)

![GD32VF103 108MHz：殊途同归的 4MHz 家族](/anim/gd32-vf103-clk108.svg)

![GD32 AF 复用：每脚 4 位的选择器，16 选 1 过门](/anim/gd32-af-mux.svg)

![ECLIC 两维优先级：level 定抢占，priority 定序](/anim/riscv-clic-priority.svg)

![MTIME 64 位读写纪律：hi-lo-hi 防撕裂](/anim/riscv-mtime-tick.svg)

![RISC-V 点灯闭环：五步装配](/anim/riscv-blink-closed.svg)

![GD32 外设差异对照：编号差 1，数量同](/anim/gd32-periph-diff.svg)

![V0 RISC-V 工具链流程：GCC→链接脚本→启动→入口](/anim/riscv-toolchain-flow.svg)

## RT-Thread 精讲

![R0 对象模型：万物继承 rt_object](/anim/rtt-object-model.svg)

![R1 二级位图：32×8 实现 256 级优先级选优](/anim/rtt-bitmap-256.svg)

![R2 IPC 五种武器一副骨架](/anim/rtt-ipc-skeleton.svg)

![RT-Thread 内存池：块大小一刀切，换 O(1) 的确定性](/anim/rtt-mem-alloc.svg)

![R4 设备框架调用链：应用 → 框架 → 驱动 → 寄存器](/anim/rtt-device-chain.svg)

![R5 finsh 命令分发：宏钉进段，shell 按名翻牌](/anim/rtt-finsh-dispatch.svg)

![R6 menuconfig 点单流水线：Kconfig → .config → rtconfig.h → 构建](/anim/menuconfig-flow.svg)

![R7 Nano 移植四件套装配](/anim/rtt-port-nano.svg)

## 双 OS 对照与选型

![X1 RTOS 选型决策树：资源→功能→生态→选择](/anim/rtos-decision-tree.svg)

![双 OS 同概念对照：通知 vs 无 / 设备框架 / 配置哲学](/anim/dual-os-compare.svg)

![双核自旋锁：互斥、自旋与释放](/anim/dual-core-spinlock.svg)

## AI 辅助开发

![A0 工具地图：MCP 是路，三个 agent 工具是岛](/anim/ai-tool-map.svg)

![A1 提示词解剖：上下文、约束、验收三段式](/anim/ai-prompt-anatomy.svg)

![A2 手册对账闭环：生成 → 对账 → 上板 → 回喂](/anim/ai-reconcile-loop.svg)

![A3 MCP 工具流：模型读手册、跑构建、看串口](/anim/ai-mcp-toolflow.svg)

![A4 幻觉防御决策树：正确性定义在哪，验证动作就在哪](/anim/ai-hallucination-tree.svg)

![A5 生产线全景：源文、构建、门禁与产物](/anim/ai-book-pipeline.svg)

## 动画规范

动画都是"裸 SVG"：不带脚本、颜色写成属性，构建期由 `AnimFigure` 包装内联进页面，跟随站点深浅主题换色。动效与版式规范见仓库内 `.trellis/spec/docs-site/animation.md`，批量自查跑 `npm run anim:lint`。

想批量核版式（出界/压字），用仓库内 `scripts/anim-audit.html`（用法见动画规范 §7）。
