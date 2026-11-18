# 六块技术准确性与练习质量审查（2026-11-18）

## 范围、基线与真值边界

- 本地 `D:\Users\STM32`，分支main，基线HEAD `51c415864a9cd3b5fb4b12b9e950a80f6da2d605`。时间均为Asia/Shanghai。
- 以当前47章manifest为目录，本轮只针对第08/09/10/12/13/14章六块，交叉阅读三个既有实验协议/lab、F407现有工程、F103两个对照示例及common行为/协议代码；不是47章全部技术审定，也未穷尽六章的全部型号、引文和练习。
- 初始工作区只有未跟踪的`.qoder/`。九份定向编辑文件原件与哈希已备份至 `D:\Users\STM32-technical-review-backup-20261118-181350`；baseline另冻结385个受保护文件（book工具/测试、固件与标准PDF等）。不进入或修改`.qoder/`。
- 仅改九份Markdown并新增本记录。未改固件、启动、链接、Makefile、工具或测试实现；没有新增软件功能，因此不伪造TDD红绿过程。以下固件缺陷是静态证据，修复须另行设计验证。
- 没有连接/打开串口、attach/halt/reset探针、烧录、读写Flash、改接线/电源；没有固件构建、PDF重建、图像或视频生成。点灯/PWM/UART仍全部未实测，历史纯编译不能当成硬件通过。

## 分类与主要整改证据

“确认错误”指正文/实际代码/本轮打开的官方源码或可复算算术存在可定位矛盾；“需限定条件”不是新增通过结论；“教学改进”只补现有题/实验；“待核实”不靠记忆或硬件想象裁决。

| 模块 | 分类与发现 | 本轮改动位置及依据 |
| --- | --- | --- |
| GPIO | 确认错误：clock stretching拉的是SCL，不是SDA；OSPEEDR不是唯一涉及电气的字段 | `docs/v1-drivers/09-gpio.md`“四维配置”“开漏”：区分SDA数据/ACK、SCL时钟拉伸；说明速度档是边沿能力且OTYPER/PUPDR也影响电气行为 |
| GPIO | 需限定条件：未开时钟读回全0不是唯一指纹；BSRR不等于多写者所有权锁 | 同章时钟门、BSRR与折叠答案：联合核RCC门位、基址、执行位置；保留单次置/清无RMW窗口的边界 |
| GPIO | 确认错误/教学改进：e01根目录路径错误；没有来源支持1Hz±30%；删nop不保证删除volatile忙等 | 同章e01、故障表、题1/7；实际 `mcu/code/stm32/00-blink/main.c` 的delay参数是volatile。改用第1至第11同极性边沿测十周期，不预填读数；说明长按重复事件和缺释放状态 |
| 时钟 | 确认错误：PLLP漏/6与/8；MCO1不能直接选SYSCLK；先切168MHz后设APB会产生危险中间态 | `08-architecture-memory-clock.md`“PLL”“提频六步”“MCO1”及题6/答案。官方RCC头提供四种PLLP；HAL_RCC_ClockConfig在切源前保护APB；HAL_RCC_MCOConfig配置AF0/源/预分频 |
| 时钟 | 需限定条件：参数助手拒绝11.0592MHz不等于芯片不支持该HSE；精确定时不是一律必选HSE | 同章助手与时钟源表：区分助手策略和硬件能力，按误差预算选源；冷复位HSI16→168且VDD=2.7–3.6V才对应本文升频示例 |
| 中断 | 确认错误：ISER不是按键事件位；PF6演算脚不是板级PA0按键；-12..-1并非每个整数都可设优先级 | `10-interrupts-nvic-exti.md`最小步骤、NVIC、EXTI清单；官方F407 IRQ枚举、__NVIC_PRIO_BITS=4、Arm SetPriority/EncodePriority。共享IRQ示例按PR&IMR分发，只W1C已处理位 |
| 中断 | 需限定条件/教学改进：8字基本帧不是所有FPU/嵌套返回情形；宿主52断言不能因脚本结束就算本轮跑过 | 同章基本帧段、宿主步骤与题4：限定返回Thread/基本帧，说明缺CMSIS缓存会跳过；补相同抢占位不能因子优先级更高就抢占的判据 |
| 定时器 | 确认错误：现有呼吸不是0–100%，而是CCR10–1000/1%–100%；84MHz/PSC83不是当前HSI16/PSC15默认 | `12-timers-pwm.md`开头、PWM、实验；`02-tim-pwm/main.c` phase公式与时钟路径；`labs/timer-pwm/README.md`补APB /1↔/2对照仅限冷复位HSI16，168MHz下不可照搬 |
| 定时器 | 确认错误/需限定条件：F103C8没有TIM5；C结构体uint32_t不是外设有效位宽；CNT坐标符号不是转向；1秒事件并非必用TIM | 同章型号段、编码器注释与离开检查：官方stm32f103xb.h只列TIM1/2/3/4且32位计数器实例判定为0；F4 TIM_TypeDef存储类型不能代替有效位宽。增量方向须处理模差且采样位移小于半量程；SysTick可1ms累计1秒 |
| 定时器 | 需限定条件/教学改进：频率/占空比公式要有模式与极性；100%时没有周期性边沿；16位ARR=65535时不能直接写CCR65536 | 同章公式、PWM、原题2及折叠答案：限定内部时钟、向上/边沿对齐、PWM1正极性、RCR=0；TIM与SysTick按资源归属分工，固定PWM改码属于另行设计 |
| UART | 确认错误：1MHz、16倍过采样不能用BRR9做115200；OVER8=1的BRR不是线性整数分母 | `13-uart-framed-protocol.md`误差表、OVER8、来路表与题3/答案。官方UART_BRR_SAMPLING8加AN4908过采样范围；分母17编码0x21，理论941176/+2.124%，0x23分母19而非17.5 |
| UART | 需限定条件：0.5/8.5所得5.882%不是整帧接收保证、更不能自动均分每端2.941%；IDLE不是应用帧边界 | 同章预算与IDLE：停止位、起始检测、采样窗口另需适用型号接收容限表；保留SR→DR仅适用本章F1/F4，不给ESP-IDF套寄存器清旗流程 |
| UART | 确认错误/教学改进：当前工程名义PCLK16/BRR139，不是84MHz；回显工程不能直接短TX/RX；当前协议测试不是Unity | 同章HAL对账、e02、排错、社区测试：位宽理论8.6875µs、8N1帧86.875µs；F103/F407 USART1门位分别14/4；F1 HAL有OverSampling成员但F103必须16，不误删合法字段 |
| DMA | 确认错误/需限定条件：NDTR是项数和本圈位置；恰好一整圈也无法由模差辨别；F1固定通道是一组请求，不是独占一个外设 | `14-dma.md`最小步骤、固定请求、循环与题5：首次/同宽条件；64字节位置60→4在能排除整圈丢失时为8；F1同通道请求须排冲突 |
| DMA | 确认错误/需限定条件：当前F407半区复制在ISR不是主循环；DBM非活动地址可运行时更新；无DCache不等于无同步需求 | 同章期限/EN窗口/缓冲区：当前consume_rx及MCU_DMB；官方HAL_DMAEx_ChangeMemory仅允许更新非活动M0/M1；2.778ms包含中断响应与复制，不是主循环轮询周期的保证 |
| DMA | 教学改进：生命周期比“必须全局”更准确；section名不证明落CCM；原4KB实验函数不存在，单数组大小不能代表总预算 | 同章地址、台架方案：F407普通SRAM 0x20000000–0x2001FFFF，CCM不可达；F103C8普通SRAM至0x20004FFF。看链接脚本/map核真实落址；记录断点会改变CPU/DMA相对进度，零值可能无法抓到；DMA_MemCopy仅为待设计入口 |

## 现有固件问题：本轮不实施修复

以下位置均为当前HEAD的原始固件行号，文件哈希应保持不变。

1. `mcu/code/stm32/01-rcc-clock/main.c:186–197`：mco1_init将PA8 MODER写01（普通输出），未写MCO1源选择；默认16MHz分频助手返回/1。现有README的默认4MHz与PLL42MHz不能作为现码验收。`main.c:361–377`先切SW/SWS后配APB，PLL路径在最终分频前可能超APB上限。README已标阻塞；须另行设计升频安全态与MCO配置、超时/恢复测试。
2. 同文件 `:301` 以PPRE字段非零判断TIM倍频，0xx中非零编码仍代表/1；推荐按解码后的除数判断，不在本轮改。HSE等待有超时，但PLL停止/锁定等while仍无超时；README不再宣称全部等待已有保护。
3. `mcu/code/stm32/04-nvic-exti-board/main.c:91–96`：以读取只写BSRR决定翻转，不能取得输出状态；`:129`是PA0释放上升沿。README现将“每松一次必交替”改为尚未满足的验收目标，建议ODR/软件状态决定一次BSRR并单独设计消抖。
4. `examples/exti-key/main.c:97–112`：F103下降沿置事件，处理时计数偶数又强制LED复位/点亮；即使忽略抖动也不能承诺10按10次严格交替。题目保留目标，不冒充示例已满足。
5. `examples/uart-dma-idle/main.c:229–235,306`：DMA_NORMAL，回调每次从起点rb_push(Size)，又忽略ReceiveToIdle重启返回值。本轮打开的官方F1 HAL明确普通模式HT不停止接收、HT回调Size=N/2，活动接收重启返回HAL_BUSY。对64字节缓冲，HT=32随后IDLE=40的合法事件序列会复制32+40而非40字节，前缀重复；HT时重装也被忽略。此为源码与当前官方HAL语义下的静态反例，未锁定本地示例实际链接的HAL版本、未上板复现。后续应先设计事件类型/增量与正常终止后的重装，不直接把F407循环策略机械搬过来。
6. `03-uart-dma/main.c:347–375`：当前实际消费在ISR，主循环排TX；本文只是纠正文档归属，不承诺该代码对任意迟到、多圈或物理故障都无损。

## 先修与已有练习的可执行性

沿用现有章节编号与旅程导航，不把“上一章”自动当作硬先修，不新建第二套课程：

| 块 | 真正需要/可按需回看 | 现有练习的增补条件、观测与判据 |
| --- | --- | --- |
| 时钟 | 第03章寄存器、第06章启动/链接；PLL和存储器地图不是必须一次线性学完 | 原题6给HSI16→168、原PPRE=/1和目标/4,/2，先纸算非法中间PCLK=168；判据是安全次序及CR/CFGR/FLASH_ACR回读计划，不运行有问题的PLL路径 |
| GPIO | 第03章寄存器；查实际外设时钟回看08 | 原题1联合排查RCC/基址/执行路径；原题7给长按500ms判断重复事件/释放状态。e01改真实工程路径、十个同极性完整周期和t10，不设伪造1Hz容差 |
| 中断 | 第09章输入/边沿、第03章位域；调试启动回看06 | 原题4给PRIGROUP5与A(2,3)/B(2,0)/C(1,3)，先算逻辑/IP再判B不抢占、C可抢占，答案仍在原折叠区；本轮不把CMSIS缺失跳过当通过 |
| 定时器 | 第08章时钟树、第09章AF；只有中断方案才需要10 | 原题2保留F103 1秒预算并追加PWM1/正极性/1MHz、端点与16位溢出；理论与实际HSI默认分开，100%平台无边沿不作为捕获失败；固定CCR实验需另行设计 |
| UART | 第09章TX/RX复用、第08章PCLK；中断接收再回看10，DMA用14 | 原BRR练习先独立作答，答案挪至原折叠区；原题3先判合法性、再编OVER8。e02区分理想115200与当前BRR139位宽，并保留原始边沿/解码双证据，未填写任何读数 |
| DMA | 第08章可达性、第03章地址/项宽、第13章UART或对应外设请求；ISR再用10 | 原题5补60→4与整圈歧义；原题6的半区期限仍为理论。CCM/内存搬运只列待设计方案，无法由NDTR单快照/不存在函数判定已经完成实验 |

## 本轮实际打开的权威依据及边界

以下均为2026-11-18读取的官方默认分支内容，未固定commit，不虚构文档Rev；行号会随上游移动，按函数/宏查找。

- ST F4器件头：[stm32f407xx.h](https://github.com/STMicroelectronics/cmsis-device-f4/blob/master/Include/stm32f407xx.h)：__NVIC_PRIO_BITS、IRQ枚举、RCC字段、TIM_TypeDef。适用F407，不因F4后缀相同就推广TIMPRE规则。
- ST F1器件头：[stm32f103xb.h](https://github.com/STMicroelectronics/cmsis-device-f1/blob/master/Include/stm32f103xb.h)：中密度F103x8/xB实例，TIM1/2/3/4与IS_TIM_32B_COUNTER_INSTANCE=0；不推广到所有F103密度。
- ST RCC：[stm32f4xx_hal_rcc.h](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/master/Inc/stm32f4xx_hal_rcc.h) 的RCC_PLLP_DIV2/4/6/8、MCO源；[stm32f4xx_hal_rcc.c](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/master/Src/stm32f4xx_hal_rcc.c) 的HAL_RCC_ClockConfig、HAL_RCC_MCOConfig。实现供交叉核对，不代替所有型号的电气限制。
- Arm CMSIS：[core_cm4.h](https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Include/core_cm4.h) 的NVIC_SetPriority、NVIC_EncodePriority、EXC_RETURN定义。结合F407四位实现，而非把Arm最大位宽当实际位宽。
- ST UART：[F4 hal_uart.h](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/master/Inc/stm32f4xx_hal_uart.h) 的UART_BRR_SAMPLING8；[F1 hal_uart.h](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Inc/stm32f1xx_hal_uart.h) 的OverSampling限定；[F1 hal_uart.c](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Src/stm32f1xx_hal_uart.c) 的HAL_UARTEx_GetRxEventType、UART_DMARxHalfCplt、HAL_UARTEx_ReceiveToIdle_DMA与HAL_BUSY分支。
- ST [AN4908，Error calculation for ABR](https://www.st.com/content/st_com/en/technical-documents/an4908-getting-started-with-usart-automatic-baud-rater-detection-for-stm32-mcus-stmicroelectronics_asset/chunk-002-topic-an4908-automatic-baud-rate-detection-modes.html)：16倍上限fCK/16、8倍上限fCK/8。该文示例为F303，不能据此宣称F103/F407有同样硬件自动波特率功能。
- ST [stm32f4xx_hal_dma_ex.c](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/master/Src/stm32f4xx_hal_dma_ex.c) 的HAL_DMAEx_ChangeMemory注释：更新非活动M0/M1。调用者仍需核CT与更新期限。
- ST [stm32f4xx_hal_tim.h](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/master/Inc/stm32f4xx_hal_tim.h)：读到编码器模式1/2的TI1/TI2注释，但尚未拿到RM原件解决输入语义疑点，故没有武断翻转原表。

RM0090（F405/407等，DM00031020）、RM0008（F101/102/103/105/107）的官方PDF下载本轮失败（HTTP/2错误；HTTP/1.1超时且0字节），**未取得可读原件**。正文既有RM/DS章号与Rev仍为历史转引，不宣称本轮核过原件。USART1_RX流/通道映射、接收容限表、编码器模式1/2语义及勘误覆盖仍待适用型号手册/勘误原件，未虚构Rev或引用结论。

旧提频顺序图、UART误差预算图未重绘；已在相邻文字/图注标明旧图不可当执行次序或合法参数依据。旧来源、历史归档与附录未机械全量改写，后续需专门同步，不宣称图文及全书技术全部消歧。

## 实际检查与可复跑命令

以下在本地执行，未跳过失败、未改宽门禁或测试期望。最终复跑日志与保护核对结果保存在外部备份的tests目录。

| 命令/检查 | 实际结果 |
| --- | --- |
| python -m book.manifest --check | exit 0 |
| python -m book.checks --check | checks passed，exit 0 |
| python -m book.mapping --check | exit 0 |
| python tools/check_assets.py | public 543项PASS；merged-book assets PASS；只检查既有资产，不构建PDF |
| python -m unittest discover -s book/tests -v | 88项OK，exit 0；含临时空封面HTML夹具，不是整书/PDF生成 |
| git diff --check | exit 0；Git的LF→CRLF提示不是内容门禁失败 |
| 既有behavior/tests.c | GCC -std=c11 -Wall -Wextra -Werror -O2编译/运行exit 0；覆盖capture/clocks/circular |
| 既有reliability/tests.c | 同flags编译protocol/health/transport/service/query/record/tests，运行exit 0，协议/健康/背压/服务/reset-record通过 |
| 既有codec-tool.c | 与protocol.c按同flags编译exit 0；未据此冒称Python交叉自测已执行 |

宿主GCC为 `D:\zhugu-home\mingw64\mingw64\bin\gcc.exe`，版本16.1.0，目标x86_64-w64-mingw32。上述三个宿主产物都输出到备份tests目录，不把exe/build临时物加入仓库。等价编译命令：

```text
# cwd=mcu/code/common/behavior；OUT为上述外部备份的tests绝对路径
gcc -std=c11 -Wall -Wextra -Werror -O2 tests.c -o OUT/behavior-tests.exe
OUT/behavior-tests.exe
# cwd=mcu/code/common/reliability
gcc -std=c11 -Wall -Wextra -Werror -O2 protocol.c health.c transport.c service.c query.c record.c tests.c -o OUT/reliability-tests.exe
OUT/reliability-tests.exe
gcc -std=c11 -Wall -Wextra -Werror -O2 protocol.c codec-tool.c -o OUT/codec-tool.exe
```

明确未执行/不能算通过：

- reliability/probe.sh所指 `mcu/scripts/device-console.py` 在当前仓库缺失，无法运行其Python self-test；只运行上述真实存在的C测试，没有补造脚本或修改probe。Windows不运行probe的Linux ASan/UBSan分支。
- `mcu/.trellis/ref/cmsis`缓存缺失，NVIC脚本第0–2段52断言未在本轮执行，也未为其下载依赖；本轮用官方源码阅读与现有宿主行为测试，不以交叉链接替代这52断言。
- 三个实验的接线/电源/板型确认、真实引脚位宽/周期、UART字节捕获、DMA压力/丢失轨迹仍待硬件取证。所有空值继续待测。

## 停止点

停在本轮文档修订，未stage/commit/push。最终HEAD、index、九份修改文档和本记录之外的工作区变动，及385个受保护文件哈希，以同备份tests/final-review.json的实读核对为准；若不符即应报告而非覆盖。没有自动开始固件修复、硬件实测、下一批章节或PDF更新。
