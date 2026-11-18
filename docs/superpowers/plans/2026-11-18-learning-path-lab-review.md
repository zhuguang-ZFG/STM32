# 47章学习路径与三个基础实验协议审阅记录

## 范围与状态

- 日期：2026-11-18（Asia/Shanghai）；工作目录 `D:\Users\STM32`，分支main，基线HEAD `476e409dfe143ad82dea83070ddc62b21cef18ef`。
- 本轮只有书稿/README/实验协议编辑，停在**文档已完善、未提交**；没有stage/commit/push，没有硬件连接/固件构建/下载/刷写，没有PDF、视频或新图片输出。
- 中断恢复时仍是已知6份文档差异和`.qoder/`；恢复前后定向保存原文与状态，没有重放覆盖。`.qoder/`未编辑。
- 外部备份 `D:\Users\STM32-learning-review-backup-20261118-170810`：`original/`为编辑前原文，`resume-1716/`为恢复快照，`before-docs-boundary-fix/`为链接修复前快照；未加入Git。

## 学习路径与独立内容检查

第46章沿用三阶段周计划、既有L0–L5、章罗盘与旅程导航，将能力目标展开为五阶段，不另建评级。逐行链接真实manifest章节，区分直接先修、条件先修和推荐回看；为五阶段补动作、证据、失败回退，不以章数判升级。

- 独立从最终Markdown表解析，而非仅信任生成数据：**47/47章**，无遗漏/重复；六附录不算章节覆盖数。
- 主归属：入门1、基础18、进阶15、项目6、深入7；必修27、参考/分支20。数量不是时长或验证完成数。
- 直接依赖83条；条件先修3条。直接图无环，合并条件边后也无环；推荐回看不参加硬依赖判定。
- 已检查505个仓库内相对链接/图像引用目标，缺失0；章内锚点与书稿边界另由book.checks验证。这里不把外部互联网链接可用性计入结果。
- 人工审阅：入门须留独立构建/verify/复位及串口证据；基础还须ADC/中断/DMA记录，不能用三样板替代全部基础；进阶按字节与计数验并发/归属；项目选分支交付五件套；深入补手册核对、性能开销、预算、恢复与取舍。缺板/仪器只能验计算/方案，硬件保持待测。
- 最初正文直链labs文件触发`link escapes docs/`，checks和资产门失败；已按现有规则改经附录B索引，仓库README/工程README保留直接协议链接。没有放宽检查器或伪造站内页面，最后全量复验通过。

## 三个样板实际达成状态

共同安全/身份/构建前提/空白证据表在`labs/README.md`；三个协议各含源码路径、板型边界、接线/供电、现有Makefile步骤、理论与测法、通过/失败判据、排错、独立练习和待采集项。所有`hardware_status`仍为pending。

| 样板 | 当前源码核对与文档结论 | 仍缺证据/阻塞项 |
| --- | --- | --- |
| 点灯 | F407的`00-blink`为PF6低亮，HSI名义16MHz、软件忙等，不能把源码校准注释当精确1Hz | 实际板卡/芯片、构建/verify/冷复位、PF6高低电平与灯对应、10完整周期原始计时/波形、复测 |
| PWM | `02-tim-pwm`为PA6/AF2/TIM3输出→PA0/AF1/TIM2捕获；16MHz条件理论PSC15/ARR999→1kHz；动态CCR10–1000即1%–100%，约4秒包络 | 时钟/寄存器回读、原始波形/探头设置、捕获增量、误差预算；固定CCR与改ARR需后续另行确认代码实验，当前未实施 |
| UART | `03-uart-dma`为PA9/PA10 AF7、115200 8N1；16MHz条件理论BRR139、位宽8.6875µs；IDLE不是应用帧边界，overruns并非只计ORE | 双方向0x55/0x41原始边沿/解码、启动行/回显日志、63/64/65和256字节跨圈比对及rx/IDLE/HT/TC/错误增量；受控积压工具/负载只留设计，未实现/执行 |

F103的两个examples明确为待集成HAL源码、缺完整工程骨架/时基中断文件；PC13/HSE72MHz/PSC71不与F407混用。GPIO自检可能过早判HAL_GetTick为0，仅登记风险不改行为；PWM文档按实际ARR/2=499、动态CCR会到1000纠正。工程README旧章链接、PA7/同定时器捕获、IDLE帧与“已经实测”的误导已收敛到真实代码边界。

## 本次实际检查

所有下列命令在仓库根执行，使用本机现有Python。完整日志保存在外部备份`verification-final/`，首轮失败日志保留在`verification/`，不是硬件日志。

| 命令/检查 | 最终结果 |
| --- | --- |
| 备份目录中的`audit_learning_docs.py` | 退出0；47章/依赖图/505本地引用/源码参数/固件配置哈希核对通过；只是本轮仓库外内容检查脚本，不是新增仓库工具 |
| `python -m book.manifest --check` | 退出0 |
| `python -m book.checks --check` | 退出0，checks passed |
| `python -m book.mapping --check` | 退出0 |
| `python tools/check_assets.py` | 退出0，543 public assets PASS，merged-book assets PASS |
| `python -m unittest discover -s book/tests -v` | 退出0，87 tests OK；没有新增功能代码，不强造测试 |
| `python -m book.build_html --check` | 退出0，临时构建53页，0 planned chapters missing；未重建PDF/覆盖发布目录 |
| `git diff --check` | 退出0；Git的LF→CRLF提示是行尾配置提示，不是门禁失败 |

检查开始到结束，16份内容文档哈希稳定，无并发改写；基线记录的固件/工程配置文件哈希未变，Git已跟踪差异全为Markdown。可从仓库根复跑外部备份里的`run_final_checks.py`；检查不触碰硬件。

## 未做事项与已知矛盾

- 不宣称已硬件复现：实际板卡身份、固件构建/verify、仪器原始证据和复测均未做；空读数全部待测，不拿理论填实测栏。
- 不安装/下载工具，不连接硬件，不运行make/flash/debug/gdb；本轮的87测试是书稿/构建工具测试，不是固件编译或板上测试。
- 封面旧承诺位于`book/build_print_edition.py:221`：`寄存器级深度教学 · 全程实物实验 · 双书合并版`，与pending状态矛盾。建议后续单独审定为「含实物实验方法与待验证协议」等如实措辞；本轮只报告，不修改封面或生成PDF。
- 学习阶段验收是读者后续要执行的标准，不是本轮已授予能力等级。固定PWM与UART积压所需代码/工具变更未授权，留设计不实施。

## 文档变更清单

- `docs/README.md`
- `docs/v7-delivery/46-resources-roadmap-open-source.md`
- `labs/README.md`
- `labs/gpio-blink/README.md`
- `labs/timer-pwm/README.md`
- `labs/uart-dma/README.md`
- `examples/gpio-blink/README.md`
- `examples/timer-pwm/README.md`
- `mcu/code/stm32/00-blink/README.md`
- `mcu/code/stm32/02-tim-pwm/README.md`
- `mcu/code/stm32/03-uart-dma/README.md`
- `docs/v1-drivers/09-gpio.md`
- `docs/v1-drivers/12-timers-pwm.md`
- `docs/v1-drivers/13-uart-framed-protocol.md`
- `docs/v6-labs-projects/40-lab-method-instruments.md`
- `docs/appendix/B-project-index.md`
- `docs/superpowers/plans/2026-11-18-learning-path-lab-review.md`（本记录）

共17份Markdown文档：13份已跟踪文件修改、4份新文档（3份实验协议及本记录）；`.qoder/`继续保留未跟踪。不自动提交/推送，不自动开始实测或下一批。

最终门禁记录时间：2026-11-18T17:23:53.303403+08:00（Asia/Shanghai）。
