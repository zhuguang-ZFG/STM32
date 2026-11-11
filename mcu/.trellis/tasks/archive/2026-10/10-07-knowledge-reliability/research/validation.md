# 可靠性阶段验证（2026-10-08）

承接仓库已经提交的 protocol/health/transport/CLI 成果，完成缺失的 F407 watchdog 与 S3 adapter 修复，不重复覆盖已完成教材。

## 已执行

- 公共 C codec、健康宽限/锁存、故障记录、TX/RX 背压、固定种子模糊输入与 Python 双向交叉验证通过。
- Node 28 项回归通过；浏览器4项（含动画总览）通过；55张动画检查、站点构建、README与根链接检查通过。
- F407 MODE=0/1/2/3 × FAULTS=0/1 全部编译链接，检查初始SP与Thumb复位向量；无故障指令时不会自动注入。模式和故障产物目录隔离。
- S3 framed-protocol/watchdog-health 普通/故障配置都实际编译；watchdog仅在healthy返回true时reset_user，任务真正上报进展，保留user以覆盖主管失效。GPIO2不再当LED。
- 共享F407 UART修正Stream5 HISR标志位TE/HT/TC=9/10/11与RCC_CSR偏移0x74；普通协议例补SysTick_Handler，避免默认中断停机。
- CLI支持通用选项在子命令前后，故障响应入队后等待200ms才生效；空闲接收也poll协议超时。

## 依据

- ST DS8626 Rev12 p105 表35：LSI 17/32/47kHz，表列适用电压温度与characterization条件；名义2s不是板上测量。
- RM0090 Rev22 第21、22章，WWDG寄存器与窗口 p709–714；缓存 .trellis/ref/st-docs/ 中的有效完整PDF及页文本。
- ST CMSIS stm32f407xx.h 的DMA_HISR_*IF5和RCC_CSR位，IDF5.5.2 watchdog文档/API。

## 保留事项

尚无本轮物理板卡测量：复位耗时、.noinit/RTC保留、WWDG窗口和真实UART满负荷由后续上板验证，不用构建结果冒充。CI按同一交付HEAD验收。C8/S17/P13已接入导航和课程清单，原实验验证状态不变。

Remote CI: https://github.com/zhuguang-ZFG/mcu/actions/runs/37657967783 — all 13 jobs succeeded for 76b619b.
