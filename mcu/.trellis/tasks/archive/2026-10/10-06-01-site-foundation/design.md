# 设计：站点架构与课程契约（最终版）

融合四轮用户要求：①深度精髓(C/RTOS/构建) ②四件套(配置/引脚/库解析/代码分析) ③风格(生动/浅显/记忆/成就) ④RTOS 双精讲(FreeRTOS+RT-Thread)+动画演示。板卡=用户实持：野火 F407 霸天虎、立创·实战派 ESP32-S3。

## 1. 目录架构

```
D:/Users/mcu
├── package.json                 # vitepress devDependency + docs scripts
├── README.md / CONTRIBUTING.md  # 门面 / 内容与风格规范
├── docs/
│   ├── index.md                 # 首页（hero + 板块入口）
│   ├── .vitepress/
│   │   ├── config.mts           # nav + 全量 sidebar（§3 为准，主 agent 统一生成）
│   │   └── theme/               # index.ts + custom.css（动画/实验/记忆锚点样式）
│   ├── public/
│   │   ├── anim/                # SVG+SMIL 动画：stack-frame.svg, irq-entry.svg, context-switch.svg
│   │   └── images/              # SVG 接线图/原理图/波形：labs/, boards/
│   ├── guide/    3 页           # 导读：怎么学 / 实物装备 / 手册地图
│   ├── c/        8 章           # C 语言精髓
│   ├── build/    8 章           # 构建与运行全过程
│   ├── stm32/    17 章          # 野火霸天虎 F407 寄存器主线
│   ├── rtos/     20 章          # freertos/ 9 + rtthread/ 8 + 对照 2 + 导览 1
│   ├── esp32/    13 章          # 立创实战派 S3 + ESP-IDF
│   └── lab/      模板+8 实验     # 实物实验中心
└── code/
    ├── stm32/00-blink/          # 最小寄存器点灯工程【成稿】（PF6 红灯）
    └── esp32/00-hello/          # hello_world 逐行解析【成稿】
```

约定：章节 `docs/<track>/<nn>-<slug>.md`；rtos 子目录 `docs/rtos/freertos/`、`docs/rtos/rtthread/`、`docs/rtos/compare/`；示例代码 `code/<track>/<nn>-<slug>/`。

## 2. 章节页模板（契约，worker 严格遵循）

```markdown
---
title: <编号 标题>
---
# <编号 标题>

> 🎯 一句话钩子：生活化类比或反直觉问题（≤60 字，禁止"本章将介绍"式开场）

## 本章精髓
1-3 个根本问题（回答"为什么"，不是"怎么用"）

## 学习目标
3-5 条可检验目标（能手算…/能逐行讲清…/能在板上观测到…）

## 先修
[链接](相对路径) ×N

## 小节结构
| 小节 | 内容 | 四件套 |
|---|---|---|
逐小节列出；四件套列标注 配置/引脚/库解析/代码分析

## 记忆锚点
口诀 / 对比表 / 反例故事，三选一以上（本章最值得记住的一件事）

## 实物实验
对应 lab 实验或本章内嵌实验：装备、观测点、预期现象一句话

## 常见坑
≥2 条真实坑（手册勘误/社区高频），禁止凑数

## 你做到了
本章完成后读者已获得的能力/现象清单（成就感闭环）
```

骨架即成品：所有表格行、坑、锚点必须是真实内容。禁 TODO/待补充/占位。

## 3. 课程大纲（每章精髓问题 = 内容契约）

### guide/（3 页）
- `index.md` 怎么学：手册→寄存器→库源码→实物四步循环；全景路线图（mermaid）
- `hardware.md` 实物装备（用户实持）：野火 F407 霸天虎、立创·实战派 S3、ST-Link/J-Link（霸天虎不板载仿真器）、USB 转 TTL、24MHz 逻辑分析仪、示波器（可选）、杜邦线耗材；每样标注"哪章用到"
- `manuals.md` 手册地图：RM0090、F407ZGT6 datasheet、PM0214、ESP32-S3 TRM、ESP-IDF 手册、FreeRTOS 源码+官方书、RT-Thread 内核源码+《RT-Thread 内核实现与应用开发实战指南》——官方获取方式+适用章节

### c/（8 章）
- `00-c-in-mcu.md` 精髓：裸机 C 与应用层 C 的本质差异（无 OS 兜底，越界=硬件事故）
- `01-memory-model.md` 精髓：一个全局变量的三段旅程（源码→.data/.bss→上电拷贝）
- `02-pointer.md` 精髓：为什么 `*(volatile uint32_t *)0x40020014` 能点灯——指针=地址+类型=访存宽度
- `03-volatile.md` 精髓：优化如何"优化掉"寄存器读写；volatile 边界（不保证原子/有序）
- `04-struct-abi.md` 精髓：结构体封装寄存器块（GPIO_TypeDef 解剖）；对齐/填充/大小端
- `05-func-pointer.md` 精髓：函数指针+状态机+环形缓冲=中断驱动基本功
- `06-abi-stack.md` 精髓：AAPCS 调用约定；逐汇编指令看一次函数调用（动画 stack-frame.svg）
- `07-ub-misra.md` 精髓：移位/溢出/严格别名高危 UB；MISRA-C 精要

### build/（8 章）
- `00-toolchain.md` 精髓：交叉编译四件套（gcc/binutils/gdb/newlib）各管什么
- `01-four-steps.md` 精髓：预处理/编译/汇编/链接逐步开盒（实验：手动复现构建看中间产物）
- `02-elf.md` 精髓：readelf/objdump 实拆固件；section vs segment
- `03-linker-script.md` 精髓：链接脚本逐行——向量表定位、内存布局、自定义段
- `04-startup.md` 精髓：上电→0x08000004→Reset_Handler→SystemInit→main 逐指令（.data 拷贝/.bss 清零）
- `05-map-size.md` 精髓：map 文件审计——谁吃了 Flash/RAM；裁剪实战
- `06-flash-debug.md` 精髓：SWD 两线协议本质；OpenOCD+GDB；硬件断点 vs 软件断点
- `07-build-system.md` 精髓：手写 Makefile→CMake/Ninja；ESP-IDF/RT-Thread(scons) 构建机制对照

### stm32/（17 章，每章四件套；基准板=霸天虎）
- `00-env.md` 环境搭建【成稿】
- `01-arch.md` 精髓：为什么 0x40020000 是 GPIOA——总线矩阵/存储映射/位带别名
- `02-rcc-clock.md` 精髓：HSE→PLL→168MHz 手算全流程（霸天虎 HSE 频率用时核对规格书）；MCO1 实测
- `03-gpio.md` 精髓：MODER/OTYPER/OSPEEDR/PUPDR/IDR/ODR/BSRR 七寄存器位级图解；AFRL/AFRH；PF6/PF7/PF8 点灯
- `04-nvic-exti.md` 精髓：向量表→NVIC→EXTI；优先级分组/抢占/嵌套；中断现场（动画 irq-entry.svg）
- `05-systick.md` 精髓：内核定时器与精确延时；为 RTOS tick 埋的伏笔
- `06-tim.md` 精髓：PSC/ARR/计数模式；PWM=比较匹配；输入捕获测频；实测波形
- `07-usart.md` 精髓：BRR 小数分频；状态寄存器驱动状态机；printf 重定向；中断+环形缓冲
- `08-dma.md` 精髓：DMA 存在的理由（CPU 卸载+总线仲裁）；流/通道/双缓冲；UART+DMA 实测
- `09-adc.md` 精髓：SAR 逐次逼近；采样时间对精度影响（实测对比）；扫描+DMA
- `10-dac.md` 精髓：TIM 触发+DMA 输出正弦——三外设协作范式
- `11-i2c.md` 精髓：START/STOP/ACK 时序与寄存器对应；逻辑分析仪抓包对照手册；EEPROM 实测
- `12-spi.md` 精髓：全双工=同步移位；CPOL/CPHA 四模式波形；W25Q 读写
- `13-flash-iap.md` 精髓：内部 Flash 擦写规则与选项字节；IAP 概念
- `14-pwr.md` 精髓：三种低功耗唤醒源与功耗实测对比
- `15-spl-anatomy.md` 精髓：stm32f4xx_rcc.c/gpio.c 逐行——库如何封装寄存器；从库 API 反推手册
- `16-debug-hardfault.md` 精髓：HardFault 逐栈帧定位（CFSR/HFSR/BFAR）；时钟/复用高频坑

### rtos/（20 章，双精讲+对照；RTOS 动画演示重点板块）
导览 `index.md`：为什么学两个 RTOS（FreeRTOS=最流行内核、ESP-IDF 自带；RT-Thread=国产生态、设备框架与组件思想）；学习顺序建议。

**freertos/（9 章，内核源码级，基准 FreeRTOS V11.x）**
- `00-why-rtos.md` 精髓：超级循环的极限（实验：写一个必然失败的三任务裸机调度）
- `01-task-tcb.md` 精髓：TCB 解剖；xTaskCreate 逐行走查（栈初始化成"像被中断过"）
- `02-context-switch.md` 精髓：PendSV 逐汇编指令看切换【动画 context-switch.svg】
- `03-scheduler.md` 精髓：就绪列表+优先级位图；tick 与阻塞延时的真相（动画：调度时间线）
- `04-queue.md` 精髓：队列=环形存储+两个阻塞列表（源码级）
- `05-sem-mutex.md` 精髓：优先级反转复现与继承机制【动画：反转时间线】
- `06-notify-event-timer.md` 精髓：任务通知为何比队列快（少一次拷贝）；软件定时器守护任务
- `07-heap.md` 精髓：heap_1~heap_5 对比实验；栈水位检测
- `08-port-f407.md` 精髓：在霸天虎裸机工程上移植 FreeRTOS 全过程（SVC/PendSV/SysTick 三异常接管）

**rtthread/（8 章，基准 RT-Thread 5.x 内核+标准版；成稿时按官方 release 钉版本）**
- `00-arch.md` 精髓：RT-Thread 分层架构（内核层/组件层/软件包）与"万物皆对象"的内核对象模型
- `01-thread-sched.md` 精髓：线程控制块 rt_thread 解剖；256 级优先级位图调度（与 FreeRTOS 位图对照）
- `02-ipc.md` 精髓：信号量/互斥量/事件集/邮箱/消息队列——对象容器+挂起列表的统一范式（源码级）
- `03-mem.md` 精髓：rt_memheap/slab/TLSF 三种堆管理；内存池 mpool 的确定性价值
- `04-device.md` 精髓：I/O 设备框架（rt_device 注册/打开/读写回调）——驱动与应用解耦的精髓；PIN/UART 设备实测
- `05-finsh.md` 精髓：finsh/msh 控制台原理（符号表导出+命令行解析）；板上实操
- `06-env-menuconfig.md` 精髓：Env+scons+menuconfig 构建配置体系（与 ESP-IDF Kconfig 同源对照）
- `07-port-f407.md` 精髓：Nano 版手动移植到霸天虎（在寄存器工程上加 rtthread nano）→标准版 BSP 的两步走

**compare/（2 章）**
- `00-side-by-side.md` 精髓：同一概念双实现对照表（任务/调度/IPC/内存/驱动模型/构建/生态）
- `01-choose.md` 精髓：选型决策树（资源约束/生态需求/实时性/团队积累）；ESP32 上 RT-Thread vs IDF FreeRTOS 位置

### esp32/（13 章，每章四件套；基准板=立创实战派 S3）
- `00-env.md` 环境搭建【成稿】（IDF v5.5，CH340K 串口识别与烧录）
- `01-arch-boot.md` 精髓：LX7 双核+IRAM/DRAM/Cache；Bootloader→分区表→app 启动全过程
- `02-gpio-matrix.md` 精髓：IO_MUX vs GPIO Matrix——为什么 S3 引脚可任意映射；驱动强度/毛刺过滤；用户键+板载外设引脚（以立创 wiki 原理图为准）
- `03-idf-anatomy.md` 精髓：组件化 CMake + Kconfig→sdkconfig 生成机制（ESP 侧库解析）
- `04-irq-dualcore.md` 精髓：中断分配器；IRAM ISR 约束；核间中断
- `05-uart-driver.md` 精髓：driver/uart.c 逐行；事件队列+环形缓冲驱动范式
- `06-spi-i2c-driver.md` 精髓：配置结构体逐字段；板载 ST7789(SPI) 与 QMI8658(I2C) 是最好的实物教材
- `07-timer-ledc.md` 精髓：GPTimer vs LEDC 选型；呼吸灯/背光调光实测
- `08-wifi.md` 精髓：esp_event 事件循环；station 连接状态机逐状态
- `09-bt-espnow.md` 精髓：协议栈架构；ESP-NOW 互传实验
- `10-flash-nvs-ota.md` 精髓：分区表 CSV 逐字段（N16R8 16MB 布局）；OTA 与防变砖回滚
- `11-lowpower.md` 精髓：Light/Deep sleep 唤醒源矩阵；电流实测；ULP 概念
- `12-audio-path.md` 精髓：ES8311+ES7210 音频链路（I2S 时序+codec 配置）——小智板的看家本领，从寄存器到"hello 语音"

### lab/（模板+8 实验）
- `template.md` 实验模板【成稿】（目标/装备/接线/步骤/预期现象/实测记录表/故障排查/思考题）
- `index.md` 实验总览（与章节交叉引用表）
- `e01-blink.md`【成稿】霸天虎 PF6 红灯：寄存器版+SVG 原理接线图+实测要点
- 骨架：e02 逻辑分析仪抓 UART 帧 / e03 示波器看 PWM 与占空比 / e04 RTOS 优先级反转复现（FreeRTOS 与 RT-Thread 各一遍）/ e05 I2C 抓包读 EEPROM / e06 低功耗电流实测 / e07 S3 板载传感器(QMI8658)读取 / e08 S3 音频链路放音

## 4. 动画规范

- 形式：独立 `.svg` 于 `docs/public/anim/`，SMIL（`<animate>`/`<animateTransform>`），`repeatCount="indefinite"`，viewBox 宽 720；页面 `<img src="/anim/xxx.svg">` 引用（无 JS 依赖）。
- 固定配色：浅底 #f6f8fa，主色 #3451b2，强调 #3eaf7c，警示 #d97706；字号≥13px 保证构建后可读。
- 本任务交付 3 个：
  1. `stack-frame.svg`：BL→压栈→局部变量→LR 返回，四阶段循环（c/06 用）；
  2. `irq-entry.svg`：主程序→IRQ→硬件压栈 r0-r3/r12/LR/PC/xPSR→ISR→EXC_RETURN 弹栈（stm32/04 用）；
  3. `context-switch.svg`：TaskA↔TaskB——PendSV 保存/恢复两任务栈帧与 PSP 切换（rtos/freertos/02 用）。
- 后续任务动画清单（骨架页注明引用关系，文件随后续成稿补齐）：scheduler-timeline.svg、priority-inversion.svg、rtthread-object-model.svg、i2c-timing.svg、dma-pingpong.svg。
- CONTRIBUTING 写明：新动画须附"表达结论一句话"，禁装饰性动画。

## 5. 板卡事实（已核实出处，写作唯一基准）

- 霸天虎：F407ZGT6(144 脚)；RGB 红=PF6/绿=PF7/蓝=PF8 共阳低电平点亮；RCC_AHB1ENR bit5=GPIOF 时钟；出处 doc.embedfire.com《寄存器点亮LED》。HSE 频率、KEY、串口引脚用时以霸天虎硬件规格书/原理图核对后在正文注明。
- 立创实战派 S3：N16R8(16MB Flash/8MB PSRAM)；外设清单见 PRD；引脚分配以 wiki.lckfb.com/zh-hans/szpi-esp32s3/ 原理图页为准（第 02/06/12 章成稿时核对并截图引用规范见 CONTRIBUTING）。

## 6. 写作风格契约（所有作者+worker 必须遵守）

1. 钩子开场：每章第一段是生活化类比或反直觉问题（"你家的电灯开关，其实是一颗寄存器里的一个 bit"），禁"本章将介绍"。
2. 三层递进：直觉（类比+图）→机制（框图/时序）→实现（寄存器位/源码行）；不许跳过直觉层直接堆寄存器。
3. 记忆锚点：每章一个（口诀如"先时钟、再模式、后数据"；对比表如 IO_MUX vs Matrix；反例如"忘了开 RCC 时钟，寄存器写了等于没写"）。
4. 成就感闭环：章首 quick win（10 分钟内可见现象）+章末"你做到了"清单；实验必须给"眼见为实"的观测手段（LED/串口/逻辑分析仪）。
5. 生动≠啰嗦：每段有信息增量；禁鸡汤/表情轰炸/水字数；术语首次出现=类比+精确定义双轨。
6. 参考节奏：野火《实战指南》"硬件连接→启动文件→逐寄存器→下载验证"的动手节奏；但我们讲透"为什么"，不止"怎么做"。

## 7. 版本基准

- VitePress 1.x / Node ≥ 20。
- Arm GNU Toolchain 14.x（arm-none-eabi）；OpenOCD ≥ 0.12；make（xpack）。
- ESP-IDF v5.5.x（支持期内）。
- FreeRTOS Kernel V11.x（源码解析基准）。
- RT-Thread 5.x（内核+标准版；rtthread 章节成稿时按 github.com/RT-Thread/rt-thread releases 钉具体版本并注明）。

## 8. 分工与集成

单一集成负责人（主 agent）。骨架页分派 4 个 worker（目录互不重叠）：

| Worker | 范围 | 页数 |
|---|---|---|
| A | docs/c/ + docs/build/ + docs/lab/ 骨架 | 23 |
| B | docs/stm32/（除 00-env） | 16 |
| C | docs/rtos/（全部 20） | 20 |
| D | docs/esp32/（除 00-env）+ docs/guide/ | 15 |

Worker 输入：本 design.md（§2 模板、§3 精髓问题、§6 风格契约）、金标准样例页（主 agent 先写 `docs/c/06-abi-stack.md`）。禁止新增 §3 之外页面；禁止占位词；每章引用 §4 动画时只写文件名不造文件。

主 agent 亲写：脚手架（package.json/config/theme/首页）、金标准样例、stm32/00-env、esp32/00-env、code/stm32/00-blink、code/esp32/00-hello、动画×3、lab/template.md + e01-blink.md、README、CONTRIBUTING、config.mts 全量 sidebar、构建验证与抽查修订。

## 9. 风险与对策

- worker 产出套话 → 金标准样例+验收 grep+主 agent 抽查重写。
- 寄存器/引脚事实错误 → §5 为唯一基准；worker 不得自创地址引脚；stm32/00-env 与 e01 由主 agent 逐位核对 RM0090。
- sidebar 死链 → config 在全部页面就位后统一生成+build 验证。
- SMIL 兼容 → Chrome/Firefox 实测（Safari 16.4+ 亦支持）。
- RT-Thread 版本漂移 → 骨架只写内核机制（稳定），版本号成稿时钉。
