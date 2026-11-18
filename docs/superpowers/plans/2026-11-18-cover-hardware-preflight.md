# 封面声明修正与真实上板前准备检查

## 范围与结论

- 工作目录：`D:\Users\STM32`；main基线HEAD `476e409dfe143ad82dea83070ddc62b21cef18ef`。
- 日期：2026-11-18，时间均为Asia/Shanghai。初始状态为前轮17份文档改动与`.qoder/`；已按哈希冻结并保留，未改写前轮记录/历史归档。
- 本轮生产代码只有封面显示短句一处修正，另加相关最小回归测试；固件源码、启动、链接脚本、Makefile与本轮已记录的本地头文件未修改。
- 三工程已完成**纯编译/链接**，未烧录、未实测。没有打开串口、没有probe attach/halt/reset、没有读写目标Flash，也未改接线/电源/引脚。
- 本轮不stage/commit/push，不生成整本PDF或视频。测试仅构造无章节/无附录的封面HTML夹具，不运行整书印刷构建。

## 封面与测试

`book/build_print_edition.py:221`由「寄存器级深度教学 · 全程实物实验 · 双书合并版」改成「**原理讲解 · 工程示例 · 实验指南**」。不改布局、生成逻辑或历史引文；实验协议的`hardware_status: pending`和所有待测栏保持原样。

`book/tests/test_print_sections.py`增加CoverCopyTests：通过空manifest调用真实build，只读回封面短句，断言新文案并排除旧的无条件硬件验证承诺。先以旧文案运行，1项测试按预期FAIL（不是导入错误）；仅替换生产短句后转绿，受影响三个测试模块20项全部OK，全套88项OK。红/绿日志在外部备份中保留。

## 只读设备盘点（2026-11-18 17:29 Asia/Shanghai）

| 类别 | 实际枚举结果 | 不能由此推出 |
| --- | --- | --- |
| 串口 | COM4、COM5均为“蓝牙链接上的标准串行” | 不当作STM32或USB-TTL，不打开端口/触发DTR |
| USB | 根集线器、XiaoMi WebCam/同组复合设备、MediaTek Bluetooth Adapter/同组复合设备、Camera DFU Device | Camera DFU属于摄像头描述，不是已确认STM32 DFU |
| 调试器/目标板 | 本次未识别到ST-Link/J-Link或可确认的STM32目标，未定位USB-TTL描述 | 不是断言设备绝不存在；板型、芯片、供电、接线与探针型号仍待现场确认 |

仅使用Windows PnP/串口设备描述枚举，保存描述、状态及VID/PID，不回显或保存设备序列号。没有连接硬件会话。

## 工具可用性（只运行版本查询）

- PATH的ARM GCC：GNU Arm Embedded Toolchain **10.3.1 20210824**，目录`C:\Users\zhugu\tools\gcc-arm-none-eabi-10.3-2021.10\bin`；gcc/objcopy/size均可定位，本轮三个工程使用此版本。
- 另一已知目录的xPack ARM GCC：**15.2.1 20251203**，`D:\zhugu-home\tools\armgcc\xpack-arm-none-eabi-gcc-15.2.1-1.1\bin`；仅验证版本，未拿它替换本轮构建。
- `mingw32-make`：GNU Make **4.4.1**。PATH未定位`make`或`sh`；本轮预建外部输出目录，避免触发Makefile的`mkdir -p`，不修改用户环境或工程配置。
- OpenOCD：PATH为Espressif版 **v0.12.0-esp32-20260304**；仅执行`--version`。包内`interface/stlink.cfg`与`target/stm32f4x.cfg`存在，但未init/attach，不能宣称ST-Link驱动或STM32兼容性已硬件验证。
- ST-LINK_CLI/STM32_Programmer_CLI：PATH、相关卸载登记与已检查标准ST厂商目录未定位；不是穷尽用户磁盘后的“未安装”断言。没有安装驱动、下载依赖或提权。

## 三个现有工程的安全隔离编译

先完整审阅三个Makefile：all只依赖ELF/BIN/HEX，配方只有GCC编译/链接、objcopy和size。排除解析期shell/include/递归Make，再对每个实际all做`-n`；输出命令白名单仅GCC/objcopy/size，无OpenOCD、gdb、flash/debug目标。随后执行同一all，使用现有BUILD变量将所有产物放仓库外；清除子进程的MAKEFLAGS/MFLAGS/MAKEOVERRIDES/MAKEFILES以避免外部隐式配方，不改用户持久配置。

| 工程目录（仓库内） | 本次实际命令（在对应目录） | 结果 | GNU size text/data/bss（字节） |
| --- | --- | --- | --- |
| `mcu/code/stm32/00-blink` | `mingw32-make all BUILD=D:/Users/STM32-hardware-preflight-backup-20261118-172758/firmware/00-blink`（先加`-n`审核） | dry-run和构建退出0；ELF/BIN/HEX/MAP齐全 | 660 / 0 / 1536 |
| `mcu/code/stm32/02-tim-pwm` | `mingw32-make all BUILD=D:/Users/STM32-hardware-preflight-backup-20261118-172758/firmware/02-tim-pwm`（先加`-n`审核） | dry-run和构建退出0；ELF/BIN/HEX/MAP齐全 | 2900 / 0 / 1592 |
| `mcu/code/stm32/03-uart-dma` | `mingw32-make all BUILD=D:/Users/STM32-hardware-preflight-backup-20261118-172758/firmware/03-uart-dma`（先加`-n`审核） | dry-run和构建退出0；ELF/BIN/HEX/MAP齐全 | 3248 / 0 / 2680 |

以上size是构建产物节大小，包含链接保留区，不是运行时RAM水位实测。默认-O0 -g3、Cortex-M4/hard-float选项均沿用现有Makefile，没有给F103补工程或改固件行为。构建日志中未出现警告/错误；它只能证明该工具链下编译链接成功，不能证明时钟、接线、外设功能或实时期限。

BIN产物身份：

| 产物 | 字节数 | SHA-256 |
| --- | --- | --- |
| 00-blink/blink.bin | 660 | `1b5f38c54d3a65140bdaa02bfc1480d2deaf591e95c4992220b29a5087ffe71e` |
| 02-tim-pwm/tim-pwm.bin | 2900 | `b770c4d305750f608ee66530678da67e8fbf580c10a4afe1739543871024709a` |
| 03-uart-dma/uart-dma.bin | 3248 | `5ed489549d7b531f26a99863ac33cedba88427b5106749f1e7774583fedbfbc1` |

完整ELF/BIN/HEX/MAP哈希、命令、Makefile哈希在外部`firmware-build-results.json`；主源码、启动、链接脚本、Makefile及递归本地include头文件哈希在`firmware-source-inputs.json`。这些固件尚未写入任何板卡，不能把旧实测绑定到新二进制。

## 旧证据检索与鉴别

- 仅检索本项目仓库及两处已知取证目录：`D:\Users\STM32-local-review-backup-20261118-154000`、`D:\Users\STM32-learning-review-backup-20261118-170810`。没有扫用户整个磁盘；仓库枚举排除.git、.qoder、node_modules、.venv、__pycache__与video。
- 仓库内发现37份原有log，来源为.temp构建/排版/CI/渲染/测试及mcu站点测试；两个旧取证目录发现43份log，来源为书稿门禁与PDF验收，不是上板证据。未发现可与这三个工程的具体板型/固件哈希绑定的串口实测日志、烧录verify日志或原始示波器/逻辑分析仪波形。
- 现有ch09/ch12/ch13及三个协议明确pending/记录待测。mcu的E04测量任务虽然标题写“跑完并回填”，task.json仍为planning、completedAt为空，PRD验收未勾选；且不是本轮三个样板，不能当已执行证据，更不能照其指令额外操作硬件。
- 资料图、源码公式、宿主模型和本轮编译都不改写成板上读数。范围内未见VCD/Saleae/示波器原始格式文件；此结论不覆盖未检查目录或仓库外未知记录。

## 继续上板前确切需要的信息与证据（本轮仅登记，不直接开始）

1. 实际板卡正反面照片、厂家/型号/版本、芯片完整丝印与封装、BOOT/供电跳线位置；确认是否确为目标STM32F407ZGT6/霸天虎，不凭驱动或工程名推定。
2. 电源来源/标称电压与接法、是否存在USB/调试器双供电，原理图对应版本；明确SWD参考电压不是默认供电输出。
3. 调试器品牌/型号、USB识别描述、与板卡SWDIO/PA13、SWCLK/PA14、GND和电压参考的逐针接线；若以后需要复位线，也须先确认接法，当前不操作。
4. UART的3.3V TTL适配器型号/逻辑电平、实际端口、TX→PA10/RX←PA9/GND接线图；COM4/5蓝牙口不自动选用，不接适配器VCC。
5. 示波器/逻辑分析仪型号、探头倍率/输入耐压/接地、可用采样率，以及PWM PA6→PA0接线照片；确定允许误差与原始波形保存方式。
6. 后续执行前明确选用本轮哪份固件哈希与写板授权。真正验收仍缺冷复位/verify、点灯10周期、PWM波形/回读、UART双方向位宽及跨圈原始字节/计数。固定PWM和受控积压若需改代码/工具，另行确认，当前未实施。

## 最终验证与保留

| 检查 | 本次结果 |
| --- | --- |
| 最小封面回归 | 旧文案FAIL→新文案PASS；仅空manifest封面HTML夹具，无整书/PDF |
| 受影响模块test_print_sections/test_print_links/test_build_entrypoints | 20 tests OK，退出0 |
| 全套book/tests | 88 tests OK，退出0 |
| book.manifest --check / book.checks --check / book.mapping --check | 均退出0，checks passed |
| tools/check_assets.py | 543 public assets PASS，merged-book assets PASS |
| git diff --check | 退出0；LF→CRLF提示是原有行尾配置提示 |
| 保留检查 | 前轮17文档哈希未变；已记录固件/构建配置哈希未变；.qoder未编辑 |

本轮新增/修改仅`book/build_print_edition.py`、`book/tests/test_print_sections.py`及本记录；其他工作区差异属于前轮保留内容。记录、日志、产物与原文备份在`D:\Users\STM32-hardware-preflight-backup-20261118-172758`，未加入Git。

本轮停在准备检查完成：仍全部未实测，未提交/推送；不自动开始硬件采集或下一批。

检查记录时间：2026-11-18T17:32:07.023696+08:00（Asia/Shanghai）。
