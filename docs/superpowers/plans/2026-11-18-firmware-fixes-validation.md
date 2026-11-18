# 既有固件缺陷修复与验收计划

## 约束与基线

本轮仅在D:\Users\STM32现有main工作区操作，HEAD=51c415864a9cd3b5fb4b12b9e950a80f6da2d605。保留前轮9份文档及审查记录、.qoder。按用户指定不切云代理/工作树，不stage/commit/push，不连接或复位硬件。源码、既有文档及标准PDF已定向备份；备份路径记录在仓库外STM32-firmware-fix-current.txt。初始book现有88测试OK。

## 根因复核与可验证标准

- 当前01-rcc-clock的mco1_init确实写MODER=01，未选MCO源；官方HAL_RCC_MCOConfig使用AF_PP/AF0/VERY_HIGH与源+分频。验收：实际函数在受控寄存器中正确配置PA8，HSI16为/1、PLL168为/4，保留其它引脚/CFGR位。
- clock_init确实在SW切PLL后才写APB；flash_config缺PWR时钟门，PLL等待无超时。对照本轮已打开ST官方HAL_RCC_ClockConfig（Flash等待读回、切源前保护APB）。验收：实际C函数所有切PLL事件之前已有Flash5WS/PWR与APB1=/4/APB2=/2；正常168/42/84可回读，HSE/PLL/SWS失败有界退出、不伪报成功。仅支持冷复位HSI16升频，不新增任意运行时换源功能。
- clock_tree_readback对PLLP只区分2/4、PPRE非零就倍频。验收：PLLP四编码与PPRE的0xx=/1按真实字段解码；外部时钟仍由HSE_VALUE_HZ人工正确配置。
- F407 EXTI ISR读取BSRR当状态，独立追踪表明无法交替。验收：执行实际ISR，BSRR读回0模型下从ODR高/低都分别翻转，只写对应BSRR位，不改触发沿/消抖。
- F103 key_process对偶数cnt又WritePin，覆盖TogglePin结果。验收：执行实际函数，两个有效低电平事件产生两次翻转，无偶数强制写；未消除抖动/一次按压多事件等既有边界。
- F103 DMA_NORMAL回调在HT=32与IDLE=40时分别复制前缀，忽略活动期间HAL_BUSY与终止后重装失败。官方F1 HAL明确普通模式HT不终止接收。最小方案仅忽略HT，IDLE/TC终止事件各复制一次并检查重装返回；ErrorCallback也不忽略失败。验收：HT不入队、不重装；随后IDLE40仅40字节；TC64只复制一次；重装失败进入既有error_handler，不增加恢复架构或声称无损。

## 执行顺序

- [x] 先建tools/check_firmware_regressions.py：从当前生产C抽取原函数体，受控MMIO/HAL测试替身仅替代硬件边界，不复制一份业务模型；产物统一仓库外。
- [x] mco用例先红→修mco1_init→绿。
- [x] clock/readback/失败用例逐项红→最小修复→绿。
- [x] F407翻灯先红→只改状态读取→绿。
- [x] F103按键先红→移除偶数强制写→绿。
- [x] F103 HT与重装失败分别红→分别修回调→绿。
- [x] 全回归、相关宿主测试、F407现有all纯编译（先dry-run，外部BUILD）；F103缺完整HAL/启动/链接工程则只报函数级宿主验证，不编造全固件构建。
- [x] 同步工程README及08/10/13当前缺陷警告，不改前轮审查历史；保留pending与未测读数。
- [x] book全套88、manifest/checks/mapping/资产门、diff --check；失败不放宽。
- [ ] 全部可执行门通过后，按book/README.md两阶段管线在备份输出新PDF；检查溢出、字体、抽取、页数/大小并实际目检封面及修改章代表页，通过后才替换标准PDF。
- [x] 记录源码/二进制/PDF哈希、实际命令结果、缺依赖与硬件未测边界，确认HEAD/index未改，停止。

## 权威依据

沿用本轮实际打开的ST官方cmsis-device-f4/stm32f407xx.h、stm32f4xx-hal-driver的HAL_RCC_ClockConfig/HAL_RCC_MCOConfig，以及stm32f1xx-hal-driver的HAL_UARTEx_GetRxEventType、UART_DMARxHalfCplt和ReceiveToIdle_DMA状态判断；具体URL见前轮six-topic-technical-review。源码为2026-11-18默认分支读取，未固定commit；未取得RM0090/RM0008 PDF原件，不虚构Rev或把寄存器替身当硅片验证。

## 执行证据

以下结果在实际执行后追加，未执行项不得勾选或写通过。

### 修复与红绿结果

- 最初12例在任何生产代码修改前运行：11例按断言失败，原有HSE超时路径1例已通过。分别保存red-baseline及每项red-* / green-*日志，逐项修复后运行对应例。
- 随后对SWS=HSE被报成HSI新增实际函数反例，先红后修正；补Flash等待写入拒绝、MCO电气字段及其它GPIO位保留覆盖。
- 最终14例全部PASS。用同一最终测试套再执行备份中的原始生产C（不替换工作区），13例FAIL、原HSE失败处理1例PASS；这是反事实回归能力对照，不冒充后来补充用例在修改前已执行。原源码身份在red-frozen-final-suite/results.json。
- tools/check_firmware_regressions.py只从当前源码抽取原函数体和原宏/全局声明，并为MMIO地址及HAL边界提供显式受控替身；不是grep断言，也没有手抄一份正确业务逻辑。生成的C/EXE/日志全部在仓库外。替身中的硬件ready、SWS与error_handler停机可观察计数不能证明硅片、HAL ABI或中断真实时序。
- MCO：PA8改AF0推挽/Very High/无上下拉，明确选源与分频；默认HSI理论16MHz，不再写默认4MHz。
- PLL：PWREN读回后配VOS；Flash等待单次RMW并读回；安全APB分频在请求PLL SYSCLK之前，留旧低频传播窗口；PLL停机/锁定均有界退出。不把失败等同于已退HSI，SWS读回决定实际频率。另纠正PLLP四编码、PPRE的0xx=/1与HSE直接源回读。不新增任意运行时换源功能；3.3V/冷复位前提及晶振实值仍需现场确认。
- F407：只把ISR状态读取改为ODR，输出仍是一次BSRR写；不改触发沿、不新增消抖。宿主从两种初值连续翻转并保留其它ODR位，但不能宣称物理按键一次只触发一次。
- F103按键：只移除cnt局部值及偶数强制写，保留原始计数与既有两点复核；未声称完成释放状态机。
- F103 UART：保持DMA_NORMAL；HT不复制/不重装，IDLE/TC终止后各复制一次；两个回调检查重装返回，失败进入既有错误停机。没有改成循环模式、自动恢复架构或承诺连续无损。

### 构建、依赖与发布停止原因

F407以现有all目标先dry-run，只允许gcc/objcopy/size配方，再实际纯编译；BUILD指向本备份firmware目录，清除子进程MAKEFLAGS等。GCC为GNU Arm Embedded 10.3.1 20210824，Make为4.4.1。00、01默认HSI/PLL8/PLL25、02、03、04-board共7个现有目标全部exit0、零warning；ELF/BIN/HEX/MAP齐全，BIN初始SP/Thumb复位向量与ELF Reset_Handler核对通过。最后HSE读回修正后已重编三个01变体。

两个F103目录实际只有main.c/README/diagram.json/wokwi.toml，无完整HAL/启动/链接工程；本轮仅执行真实生产函数的受控HAL宿主测试，**没有F103全固件编译通过结论**。未伪造CMSIS或device-console占位依赖。mcu/.trellis/ref/cmsis和mcu/scripts/device-console.py仍缺失，NVIC原52断言/Python交叉self-test未执行；共享behavior、reliability宿主C测试及codec-tool编译通过。

指定book检查：manifest/checks/mapping全部exit0，资产543项及merged-book PASS，现有book88项OK，HTML --check生成临时53页且0缺章，diff --check通过，13份修改/记录Markdown链接零错误。

**未进入PDF构建：**额外执行仓库内容指南要求的全仓`python tools/slop_lint.py`时exit1，14项全部来自用户已有未跟踪.qoder/worktrees/.../.superpowers历史笔记。按“不动.qoder、不放松门禁”，没有修改这些笔记、lint过滤器或豁免，也没有把失败当通过。另以原规则检查48个明确指定的章节/示例README文件，exit0、0命中；它只证明失败归因，不替代全仓失败。故未启动两阶段印刷命令、未生成新候选、未覆盖标准PDF；本轮新的溢出/字体/抽取/目检QA均未执行，不能沿用旧验收冒充新结果。

另一次定向lint误将docs目录作为文件参数，返回exit2“没有这个文件”，随后改为显式文件清单才通过；保留失败记录，不将误调用算通过。

### 身份记录

记录时间：2026-11-18 19:13:56 Asia/Shanghai。

定向备份：`D:\Users\STM32-firmware-fix-backup-20261118-185755`。

修改源码SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `mcu/code/stm32/01-rcc-clock/main.c` | `adf75dc7ca90153a36db678e1d3697484da1b5cd47e0a0e1b1cfa28deb8e5b98` |
| `mcu/code/stm32/04-nvic-exti-board/main.c` | `149e4ff0e9a1e5ec6b11fa28cd680c556829296359c03badedccef0c28e20d50` |
| `examples/exti-key/main.c` | `88dc29d100c5386b8ad6b5532e31b1d2cadd62e0639ff0e676c40abb8761a662` |
| `examples/uart-dma-idle/main.c` | `c29cf18eae0a759e637087ade7fc45d90acfdbe51a312a630d40d96604d9ea63` |

本轮BIN身份（所有ELF/HEX/MAP与完整源输入哈希见备份firmware-build-results.json及firmware-source-inputs.json）：

| 构建 | 字节数 | BIN SHA-256 |
| --- | --- | --- |
| 00-blink 默认 | 660 | `1b5f38c54d3a65140bdaa02bfc1480d2deaf591e95c4992220b29a5087ffe71e` |
| 01-rcc-clock 默认 | 1684 | `55fae088ec5567f11bda3a7d102d2d4c4a6c24b24f8cfc53442c810ef0600bf9` |
| 01-rcc-clock USE_HSE_PLL=1 | 2576 | `45998214c6b9696c2b1de981bc14cfdc72a2d3a2e6370cf74615423862947e84` |
| 01-rcc-clock USE_HSE_PLL=1,HSE_VALUE_HZ=25000000 | 2576 | `258f4d28a89a317b95fe227c9de0e6cb7d6dcaf0ce8b3f9d0213fca46ccd4bb9` |
| 02-tim-pwm 默认 | 2900 | `b770c4d305750f608ee66530678da67e8fbf580c10a4afe1739543871024709a` |
| 03-uart-dma 默认 | 3248 | `5ed489549d7b531f26a99863ac33cedba88427b5106749f1e7774583fedbfbc1` |
| 04-nvic-exti-board 默认 | 860 | `96a7fe1437a7e9d214483384e5cccf368603904cfeab4b9a4318e845704bced3` |

**保留的旧PDF，非本轮更新：**`D:\Users\STM32\book\dist\print\merged-book.pdf`，833页、29200885字节；原修改时间2026-11-18T17:53:19.351488+08:00（Asia/Shanghai），SHA-256 `8e92425a9904beb87a7cdf7947b1835e28019d741c95cd16707448700bb1f0fc`。与本轮备份逐字节哈希一致。

未stage/commit/push；停止在固件/文档修复已落盘、发布门未全部通过的状态。前轮审查记录保留为当时事实，不重写成当前仍有缺陷；当前正文/README已同步。全部上板证据仍pending，未开始新批次。最终状态和输入稳定性以备份final-review.json为准。
