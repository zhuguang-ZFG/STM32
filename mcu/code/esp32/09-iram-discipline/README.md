# IRAM 落址取证探针

基准：**ESP-IDF v5.5.2、ESP32-S3**。这一集不需要开发板：问题全在链接器怎么摆段落，编译完查 ELF 就能定案。

## 工程想摆什么

P4 讲的纪律是"关 Cache 期间只有内部存储取得到"。一个 ISR 能不能在那时候跑，不取决于本体有没有标 `IRAM_ATTR`，而取决于整条链——本体、被调用的函数、读到的常量——每一环是否都落在内部存储。

main/main.c 用七个符号一次摆全四种断法：`isr_plain`（不标，掉进 Flash）、`isr_leaky` + `helper_far`（只标本体，链子在被调用函数断）、`isr_tight` + `helper_near`（整条链都标，真 IRAM-safe）、`isr_rodata` + `k_table`（代码进了 IRAM，常量还在 DROM）。

helper 全部强制 `noinline`：内联与否则编译器当天决定，`nm` 就看不见链条断在哪了。

## 构建与取证

仓库根执行 `sh code/esp32/09-iram-discipline/probe.sh`，一次跑完八段：从 IDF 源码现挖 `IRAM_ATTR` / `ESP_INTR_FLAG_IRAM` 两个宏、把整个中断源枚举交给宿主机编译器打印（`ETS_MAX_INTR_SOURCE` 与保留位、同值别名一并算出来，不数行数）、`idf.py build`、读 `.map` 的 Memory Configuration、`nm` 指认七个符号并按区间归类、查每个符号真正落在哪个输入段、拆四个 ISR 的反汇编看跳转落在哪、`idf.py size` 的整本账，最后用前面读回来的区间做断言——外加核对 `ESP_INTR_FLAG_LEVELn` 的位移量确实等于 `n`。

也可手工：`idf.py set-target esp32s3 && idf.py build`，产物在 `build/iram-discipline.elf` 与 `build/iram-discipline.map`。

Windows 上 probe.sh 里那三处绕法是针对 Git Bash 的既有坑，换平台可以删掉：Git Bash 的 `MSYSTEM` 会让 `idf_tools.py` 直接拒绝启动（`env -u` 无效，MSYS 会重新注入，只能在 PowerShell 里 `Remove-Item Env:\MSYSTEM`）；`~/.espressif/tools/ccache/4.11.2` 是个坏掉的 msys 软链，`export.ps1` 会报"tool ccache has no installed versions"，脚本自动找一个真实 `ccache.exe` 塞进 PATH 前端；取证用的 binutils 从本次构建的 `CMakeCache.txt` 里解出目录，不假设 PATH 上装的是哪套工具链。

## 两个必须记住的读数

**判据地址按芯片分**：esp32s3 的 IRAM 取指窗口起点是 `0x40374000`（`iram0_0_seg`），Flash 映射代码段从 `0x42000020` 起（`iram0_2_seg`）；初代 ESP32 是 `0x400xxxxx` 一片。两代数字不能互借，所以脚本不硬编码，区间一律从本工程自己的 `.map` 读。

**`--gc-sections` 会把没人引用的 ISR 收掉**：IDF 默认开着它，探针工程没有真挂中断，链接器会把整段当垃圾清除——实测不钉住时七个符号一个都不在 ELF 里，`nm` 只剩 `app_main` 和 `g_hits`。所以 `app_main` 里填了一张 `g_isr_table` 充当 `esp_intr_alloc(...)` 的角色。真项目不会踩到，因为驱动确实引用了它们；写成探针时必须钉住。

## 验证状态

本机（Windows + Git Bash + IDF 5.5.2）实跑通过，八段全绿，`probe.sh` 退出码 0；上面的地址与字节数取自那次实跑输出。这是静态取证，不涉及上板：Cache 真的关掉时这些函数各自什么表现，仍需上板实测。
