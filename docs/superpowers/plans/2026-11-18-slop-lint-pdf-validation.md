# slop_lint 仓库边界修复与本轮 PDF 验收

状态：已完成可证实的扫描边界修复、全套检查及新PDF自动/实际目检验收，已替换标准三文件；全部停在未暂存、未提交、未推送。以下均为本轮实测结果，不沿用旧验收。

- 工作区：`D:\Users\STM32`，main HEAD `51c415864a9cd3b5fb4b12b9e950a80f6da2d605`。本轮不暂存、不提交、不推送、不碰硬件、不生成视频。
- 定向备份：`D:\Users\STM32-lint-pdf-backup-20261118-192012`（Asia/Shanghai）。初始18份固件/文档/回归 WIP、原 lint、旧 HTML/meta/PDF 共22文件，有 baseline SHA-256。未备份/改写 .qoder 内容；对其中405份参与旧发现的 Markdown 作只读哈希留证。

## 根因与准确边界

旧 `targets()` 对 ROOT.rglob("*.md") 做既有目录过滤，不识别当前 Git 仓库所有权。Make 的 `lint-voice` 无参数调用；原注释已区分正文与构建、第三方、本地操作材料；历史 a796c363 建立此边界，92fc917c 又明确 mcu 子树另行治理。这不是把任意磁盘上的另一工作树也当作当前仓库待交付正文的契约。

当前 Git 实际登记 .qoder/worktrees/merged-book-b1、b2 两个独立工作树及不同 HEAD；.qoder 本身并未被忽略，当前主仓库索引也没有其文件。旧全仓扫描实测 exit1、14命中，全部位于 b2 的 .superpowers/sdd 内部资料。原规则不变，不能以改笔记或新增 .qoder 名称豁免解决。

最小修改只替换默认发现数据源为 `git ls-files --cached --others --exclude-standard -z`：保留已跟踪文件与非忽略的待提交文档，遵循 Git 对独立嵌套仓库/工作树的边界；已跟踪文件即使位于后来忽略的目录，也不被丢弃。若父索引与嵌套 Git 标记覆盖范围重叠，保留 Git 返回的已跟踪内容及待提交同级文件，不根据 .git 标记粗暴剪枝。无 Git 元数据的源码归档保持原文件系统发现；有 Git 元数据而 Git 执行失败/缺失则 exit2，不退化成假绿。显式给文件仍直接检查，包括忽略文件。

原发现555份、修复后148份；差集精确为405份独立工作树文档、2份已被各自 .pytest_cache/.gitignore 忽略的缓存 README（含 stm32-book 下残留），没有其他源文档被移除。未新增 SKIP_DIRS、忽略标记或词语例外。AST 比较证明 SKIP_DIRS、RULES、HOUSE_STYLE、lint、scrub 均与备份原版一致。

## RED / GREEN

`book/tests/test_slop_lint.py` 新增13项，均在真实临时 Git 索引/checkout 中执行；没有在用户仓库暂存或创建提交。覆盖 .git 目录、独立 .git 文件 checkout（与 linked worktree 同一所有权边界）、非忽略未跟踪文档、普通 .qoder 名称源文档、忽略目录中的已跟踪源文档、父索引与嵌套仓库重叠、真实违规仍 exit1、显式忽略文件仍检查、已删除索引项、Unicode/空格文件名、无 Git 归档及 Git 失败 exit2。

先写测试：首轮6失败、0错误；首次 GREEN 12/13，发现一个测试错误地要求 Git 在父索引重叠时也隐藏待提交同级文件。真实 Git 单独实验表明 Git 保守保留此文件；修正断言与边界说明，未给生产逻辑加例外。最终13项对冻结原版重新执行为5个预期失败、0错误，对修复版13/13通过。原全仓14命中重现日志与最终全仓 exit0 日志均保留。不是只扫正文或复制到无 .qoder 的目录运行门禁。

## 已完成的本轮前置验证

- 默认无参数全仓 slop_lint：exit0，0命中，148份适用 Markdown。
- manifest/checks/mapping、资产543项、book全部101项（原88+新增13，零跳过）、HTML --check 53页：全部 exit0。
- 生产固件函数 MMIO/HAL 边界替身14项：全部通过，不是硬件测量或F103全工程编译。
- F407现有7个 all 目标分别先 -n dry-run，只允许 gcc/objcopy/size，再在备份目录独立编译：00、01 HSI/PLL8/PLL25、02、03、04-board；全部 exit0、无 warning，ELF/BIN/HEX/MAP齐全，SP/Thumb复位向量与nm Reset_Handler吻合。
- common behavior/reliability 原有宿主回归、codec工具构建：全部 exit0。
- 印刷前核对：670个 book/docs 输入、34个固件输入、405份 .qoder Markdown、原18份WIP及旧标准PDF/HTML/meta未变。

一次印刷前置脚本误把通过测试的 docstring 中 skipped 一词当作跳过；实际 summary 为101/OK、无跳过记录。已按 unittest 结果行语义修正外部脚本；没有修改测试门禁，那次未启动打印。期间一次远程 Read 临时不可达，确认机器仍在线后同工具成功重试，未重放写操作。

## PDF 本轮结果

现有标准两阶段管线从真实工作区完整47章+6附录构建，先输出仓库外候选；没有复制无 .qoder 仓库绕过内容门。82个既有SVG动画只取内存静帧，显式等待预算608.12秒，含浏览器启动等实际总构建约718秒；不生成视频，不覆盖源图。旧标准三文件在所有自动检查、实际目检和再次全套门禁通过前一直保持原哈希。

- 标准路径：`book/dist/print/merged-book.pdf`。
- 新PDF：837页，29227244字节。
- 文件时间：`2026-11-18T19:40:59.812443+08:00`，Asia/Shanghai；替换核验时间：`2026-11-18T19:45:32.019082+08:00`，Asia/Shanghai。
- SHA-256：`d4a646acf4f6dec6722ac5fc5531d34e71ead5b79e5fa74b4d7f130749613d9c`。
- 旧PDF保留于备份 original/book/dist/print/merged-book.pdf：833页、29200885字节，SHA-256 `8e92425a9904beb87a7cdf7947b1835e28019d741c95cd16707448700bb1f0fc`。
- 新HTML/meta/PDF均与通过验收的候选逐字节哈希相同，见 delivery-result.json。已验证源输入670项/固件输入34项/原18份WIP/.qoder的405份Markdown均未变；HEAD未变，索引无暂存改动。

### 自动QA与实际目检

既有打印管线176mm横向溢出门通过；独立浏览器资源探测版心665.1875px、327张图片无坏图、9个字体面均loaded。全837页抽取829519字符、U+FFFD和NUL均0；63书签与meta逐项对应；空页0、越页文字0（沿用既有1pt浮点容差）；17嵌入字体资源，非标准字体未嵌入0。全六章本轮特有文句已在各自章节内定位：时钟131、GPIO150、中断171、定时器207、UART233、DMA266页；既有47章路径/阶段验收与封面修正也均能抽取。

**实际打开并查看12张候选PDF渲染图**，不是仅生成图片：封面1、目录2–3、六章代码/表格129/145/168/207/226/250、密集图161、修正时钟安全顺序132、当前UART边界233页。未见缺字、裁剪、横向压缩或图边丢失；封面不再声称全程实物实验，UART当前HT/重装与未上板边界可见。完整QA与具体目检备注见 qa/analysis.json、qa/*.png、qa/full-text.txt。仅对这12页作人工目检，不能说837页全逐页人工审校。

PDF完成后、替换前再次运行全部8项主门：仍为全仓lint0命中、manifest/checks/mapping/资产543通过、book101/101零跳过、HTML53页无缺章、生产函数14/14。日志独立为 logs/gate-final-*.log，结果 gate-results-final.json，没有覆盖印刷前证据。

## 证据及未执行边界

完整命令、cwd、退出码及日志见备份内 gate-results.json、firmware-results.json、print-results.json，run_gates.py/run_firmware.py/run_print.py，以及 logs/；原规则历史、工作树及 ignore 证据见 ownership-history-evidence.json，范围差集 scope-before.json，最终测试冻结原版 RED 与 GREEN 日志分列。

不执行：刷写/连接/复位/测量硬件、OpenOCD/GDB、物理按键消抖/波形/电流/UART无损验证、视频、make assets/verify（会生成素材/视频）。F103示例仍缺完整HAL/启动/链接工程及真实ReceiveToIdle接口集成证据，不冒充全固件构建。保留所有之前未提交文件与 .qoder；最终HEAD仍为51c415864a9cd3b5fb4b12b9e950a80f6da2d605；最终状态清单及完整复跑命令见下。

## 本轮完整复跑命令与结果

解释器、cwd、开始/结束Asia/Shanghai时间以及对应完整stdout/stderr日志均在上述JSON。下列不是计划，而是实际退出码。额外QA实际命令为 `python "D:\Users\STM32-lint-pdf-backup-20261118-192012\qa_pdf.py"`，exit0；原版冻结RED/最终GREEN日志分别见 logs/slop-final-suite-frozen-red.log、logs/slop-scope-green-final.log。

### 印刷前主门

```text
cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe tools/slop_lint.py
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.manifest --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.checks --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.mapping --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe tools/check_assets.py
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m unittest discover -s book/tests -v
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.build_html --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe tools/check_firmware_regressions.py --cc D:/zhugu-home/mingw64/mingw64/bin/gcc.exe --out D:\Users\STM32-lint-pdf-backup-20261118-192012\firmware-regressions
exit=0

```

### ARM安全dry-run/构建及宿主检查

```text
cwd=D:\Users\STM32\mcu\code\stm32\00-blink
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE -n all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/0-00-blink
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\00-blink
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/0-00-blink
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\01-rcc-clock
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE -n all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/1-01-rcc-clock
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\01-rcc-clock
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/1-01-rcc-clock
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\01-rcc-clock
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE -n all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/2-01-rcc-clock USE_HSE_PLL=1
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\01-rcc-clock
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/2-01-rcc-clock USE_HSE_PLL=1
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\01-rcc-clock
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE -n all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/3-01-rcc-clock USE_HSE_PLL=1 HSE_VALUE_HZ=25000000
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\01-rcc-clock
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/3-01-rcc-clock USE_HSE_PLL=1 HSE_VALUE_HZ=25000000
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\02-tim-pwm
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE -n all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/4-02-tim-pwm
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\02-tim-pwm
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/4-02-tim-pwm
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\03-uart-dma
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE -n all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/5-03-uart-dma
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\03-uart-dma
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/5-03-uart-dma
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\04-nvic-exti-board
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE -n all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/6-04-nvic-exti-board
exit=0

cwd=D:\Users\STM32\mcu\code\stm32\04-nvic-exti-board
D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.EXE all BUILD=D:/Users/STM32-lint-pdf-backup-20261118-192012/firmware/6-04-nvic-exti-board
exit=0

cwd=D:\Users\STM32\mcu\code\common\behavior
D:\zhugu-home\mingw64\mingw64\bin\gcc.exe -std=c11 -Wall -Wextra -Werror -O2 tests.c -o D:\Users\STM32-lint-pdf-backup-20261118-192012\host-common\behavior.exe
exit=0

cwd=D:\Users\STM32
D:\Users\STM32-lint-pdf-backup-20261118-192012\host-common\behavior.exe
exit=0

cwd=D:\Users\STM32\mcu\code\common\reliability
D:\zhugu-home\mingw64\mingw64\bin\gcc.exe -std=c11 -Wall -Wextra -Werror -O2 protocol.c health.c transport.c service.c query.c record.c tests.c -o D:\Users\STM32-lint-pdf-backup-20261118-192012\host-common\reliability.exe
exit=0

cwd=D:\Users\STM32
D:\Users\STM32-lint-pdf-backup-20261118-192012\host-common\reliability.exe
exit=0

cwd=D:\Users\STM32\mcu\code\common\reliability
D:\zhugu-home\mingw64\mingw64\bin\gcc.exe -std=c11 -Wall -Wextra -Werror -O2 protocol.c codec-tool.c -o D:\Users\STM32-lint-pdf-backup-20261118-192012\host-common\codec-tool.exe
exit=0

```

### 两阶段候选构建

```text
cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.build_print_edition --out D:\Users\STM32-lint-pdf-backup-20261118-192012\build\merged-book.html
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.print_pdf --html D:\Users\STM32-lint-pdf-backup-20261118-192012\build\merged-book.html --meta D:\Users\STM32-lint-pdf-backup-20261118-192012\build\merged-book.meta.json --out D:\Users\STM32-lint-pdf-backup-20261118-192012\build\merged-book.pdf
exit=0

```

### 替换前复跑主门

```text
cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe tools/slop_lint.py
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.manifest --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.checks --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.mapping --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe tools/check_assets.py
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m unittest discover -s book/tests -v
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe -m book.build_html --check
exit=0

cwd=D:\Users\STM32
C:\Users\zhugu\scoop\apps\python313\current\python.exe tools/check_firmware_regressions.py --cc D:/zhugu-home/mingw64/mingw64/bin/gcc.exe --out D:\Users\STM32-lint-pdf-backup-20261118-192012\firmware-regressions-final
exit=0

```

## 剩余未提交文件

以下包括用户原有全部WIP；本轮新增/修改仅lint工具、新13项测试、本记录，另更新被Git忽略的标准HTML/meta/PDF产物。未自动暂存/提交/推送，未开始下一批。

```text
 M docs/v1-drivers/08-architecture-memory-clock.md
 M docs/v1-drivers/09-gpio.md
 M docs/v1-drivers/10-interrupts-nvic-exti.md
 M docs/v1-drivers/12-timers-pwm.md
 M docs/v1-drivers/13-uart-framed-protocol.md
 M docs/v1-drivers/14-dma.md
 M examples/exti-key/README.md
 M examples/exti-key/main.c
 M examples/uart-dma-idle/README.md
 M examples/uart-dma-idle/main.c
 M labs/timer-pwm/README.md
 M mcu/code/stm32/01-rcc-clock/README.md
 M mcu/code/stm32/01-rcc-clock/main.c
 M mcu/code/stm32/04-nvic-exti-board/README.md
 M mcu/code/stm32/04-nvic-exti-board/main.c
 M tools/slop_lint.py
?? .qoder/
?? book/tests/test_slop_lint.py
?? docs/superpowers/plans/2026-11-18-firmware-fixes-validation.md
?? docs/superpowers/plans/2026-11-18-six-topic-technical-review.md
?? docs/superpowers/plans/2026-11-18-slop-lint-pdf-validation.md
?? tools/check_firmware_regressions.py
```

## 替换后最终核验

2026-11-18T19:46:48.333430+08:00（Asia/Shanghai）：再次无参数全仓lint exit0、git diff --check exit0（仅原有LF→CRLF提醒，无空白错误）、git diff --cached --quiet exit0；HEAD、670/34/405项源哈希以及标准PDF SHA-256再次一致。额外逐页检查标准PDF共258个图像放置实例，越页图像0（同一1pt浮点容差）。结果见备份final-verification.json。所有旧WIP和旧PDF备份保留，无硬件/视频/提交/推送，停止本批。
