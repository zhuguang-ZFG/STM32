# STM32 批次执行清单

## 进入实施前

- [x] 父任务方案已由用户审阅并批准实施（2026-10-06）。
- [x] 用户授权安装 GNU Arm Embedded 工具链；确认手上有霸天虎 F407ZGT6。
- [ ] 工具链就绪并记录版本：`arm-none-eabi-gcc --version`、`mingw32-make --version` 写入 research。
- [ ] `trellis-before-dev` 与 docs-site 规范已读。

## 步骤

1. **事实核验**
   - [ ] 从 ST CMSIS 头文件核对 RCC/TIM/USART/DMA 相关位定义与基址，记入 research（锁 commit）。
   - [ ] 核对 PA6/PA7/PA8/PA9/PA10 的复用表条目与 AF 号。
   - [ ] 核对 DMA1 stream/channel 映射（USART1_RX / USART1_TX）。
   - [ ] 记录 HSE 事实状态：公开资料无法确认即标“以板卡规格书/实测为准”。
2. **工程**
   - [ ] `code/stm32/01-rcc-clock`：HSI 默认 + HSE/PLL 编译开关 + 回读分频 + MCO1。
   - [ ] `code/stm32/02-tim-pwm`：PWM 输出 + 输入捕获回环。
   - [ ] `code/stm32/03-uart-dma`：USART1 回显 + DMA 循环接收 + IDLE 帧边界。
   - [ ] 每个工程 README：入口、工具链、引脚、构建命令、预期观察、排查。
3. **章节**
   - [ ] S2 RCC 成稿（含 S-F1）。
   - [ ] S6 TIM 成稿（含 S-F2，quick win 改 PA6）。
   - [ ] S7 USART 成稿（含 S-F3，0x41 统一 + f_PCLK 前提）。
   - [ ] S8 DMA 成稿（含 S-F4 位宽/位置、S-F5 处理期限）。
4. **动画**
   - [ ] 六张新图，逐张写明“表达结论一句话”，数值与正文一致。
   - [ ] 修订 `dma-pingpong.svg`（所有者/截止点/覆盖）。
   - [ ] 图形核验：XML 解析、viewBox=720、字号 ≥12px、SMIL 阶段值、浏览器目检关键阶段。
5. **同步**
   - [ ] `docs/lab/e02-logic-uart.md`、`docs/lab/e03-scope-pwm.md` 事实修正。

## 门禁

- 构建：`mingw32-make` 在三个工程下零错误零警告（`-Wall -Wextra`），并用 `arm-none-eabi-nm`/`objdump` 留证。
- 站点：`npm run docs:build` 零错误，`ignoreDeadLinks` 保持 false。
- 事实：寄存器/引脚结论均有一手来源与版本；无“若不支持则换脚”式把核实推给读者的表述。
- 上板：区分“已实测”与“待上板实测”，实测值必须为真实读数。

## 失败处理

工具链安装或板上连接受阻时，不降低门禁：继续完成不依赖硬件参数的内容与工程构建，把受阻项记为待办并明确写出缺失条件。