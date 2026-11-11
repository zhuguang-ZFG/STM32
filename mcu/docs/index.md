---
layout: home

features:
  - icon: 💡
    title: STM32F407 寄存器主线
    details: 野火霸天虎板上，从 RCC 时钟到 GPIO 七个寄存器，手写每一行启动代码，点亮的不是灯，是对芯片的理解。
    link: /stm32/
    linkText: 进入路线
  - icon: 📡
    title: ESP32-S3 + ESP-IDF
    details: 立创实战派 S3 板上，从 GPIO Matrix 到 Wi-Fi 状态机到音频链路，把"小智"的看家本领拆给你看。
    link: /esp32/
    linkText: 进入路线
  - icon: 🧠
    title: C 语言精髓
    details: 为什么 *(volatile uint32_t *)0x40021418 = 1UL << 22 能点灯？指针、volatile、ABI、栈帧——嵌入式 C 是另一种 C。
    link: /c/
    linkText: 进入路线
  - icon: ⚙️
    title: 构建与运行全过程
    details: 预处理到链接四步开盒、ELF 解剖、链接脚本逐行、上电到 main 的每一条指令——你的代码经历了什么。
    link: /build/
    linkText: 进入路线
  - icon: 🧵
    title: RTOS 双精讲
    details: FreeRTOS 内核源码级剖析 + RT-Thread 设备框架与生态，上下文切换动画演示，双 OS 对照选型。
    link: /rtos/
    linkText: 进入路线
  - icon: 🔁
    title: GD32 双系对照
    details: G 篇 GD32F4xx（Cortex-M4，RCU/200MHz）逐字段对剖 STM32F407；V 篇 GD32VF103（RISC-V Bumblebee）丈量 CLIC 与 MTIME。
    link: /gd32/
    linkText: 进入路线
  - icon: 🔬
    title: 实物实验中心
    details: 逻辑分析仪抓 UART、示波器看 PWM、优先级反转复现——眼见为实，每章都有能上手的实验。
    link: /lab/
    linkText: 进入实验
---

<div class="mcu-start">

## 先挑一条适合自己的路

同一个站点，五种上路方式——**先见现象，再挖原理**，别从最难的那章硬啃。

<PathFinder />

## 学习地图

下图的成稿数、动画数、实验数、工程数由 `npm run docs:gen` 扫全站章节 frontmatter 算出，不手写。**实心=成稿可读，虚线=骨架建设中**（结构、目标、先修都已定，正文待补）。

<LearningMap />

> 每章同一个循环：**手册 → 寄存器 → 库源码 → 实物**。看不懂的那一环，就是该回去补的那一环。

<McuUpdates />

</div>

