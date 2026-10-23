# spl-f1-blink — SPL V3.5.0 + CMake + CLion / VS Code

> 目标：STM32F103C8T6 BluePill，PC13 低有效 LED 约 1 Hz 闪烁。对应[第 26 章](../../docs/26-STM32F10x标准外设库SPL.md)。

这个目录只保存本项目原创代码和构建定义，不再分发 ST 的 SPL 源码。构建时通过 `SPL_ROOT` 指向冻结的 STM32F10x Standard Peripheral Library V3.5.0：

```text
commit afa743577f2784e95be2d5003380fdb84a702519
https://github.com/wajatimur/stm32f10x-stdperiph-lib
```

该仓库是社区镜像，不是规范来源；API 语义仍以 STSW-STM32054、RM0008 和目标芯片数据手册为准。

## 1. 已验证边界

- 使用冻结版本真实的 `stm32f10x.h`、`system_stm32f10x.c`、GPIO/RCC 驱动与 `startup_stm32f10x_md.s`。
- 使用本目录面向 F103C8 的 64 KiB Flash / 20 KiB RAM 链接脚本。
- `src/stm32f10x_it.c` **替换** V3.5.0 模板文件；不要同时编译模板的 `stm32f10x_it.c`，否则两个非 weak `SysTick_Handler` 会链接冲突。
- 冻结镜像把 `core_cm3.h` 保存成 `core_cm3.h.old`；CMake 只在缺少正式文件名时复制到构建目录，不修改上游检出。
- 本机已用 GNU Arm Embedded 10.3.1 完成编译链接。没有连接真板时，只能证明构建闭合，不能声称 LED 已实测闪烁。

## 2. 命令行构建

前置：CMake、Ninja、GNU Arm Embedded Toolchain。先检出冻结源码：

```bash
git clone https://github.com/wajatimur/stm32f10x-stdperiph-lib.git ../stm32f10x-spl
git -C ../stm32f10x-spl checkout afa743577f2784e95be2d5003380fdb84a702519
```

设置环境变量后构建：

```powershell
$env:SPL_ROOT = (Resolve-Path ../stm32f10x-spl)
cmake --preset debug
cmake --build --preset debug
arm-none-eabi-size build/debug/spl-f1-blink.elf
```

Linux/macOS：

```bash
export SPL_ROOT="$(realpath ../stm32f10x-spl)"
cmake --preset debug
cmake --build --preset debug
```

输出：`build/debug/spl-f1-blink.elf`、`.hex`、`.bin` 和 `.map`。

## 3. CLion 开发方式

CLion 官方嵌入式流程以 CMake、GNU Arm Toolchain 和 OpenOCD 为核心：

1. 安装 GNU Arm Embedded、CMake/Ninja、OpenOCD，并确保命令行能执行 `arm-none-eabi-gcc`、`arm-none-eabi-gdb`、`openocd`。
2. 在启动 CLion 前设置 `SPL_ROOT`，然后直接打开本目录。CLion 会发现 `CMakePresets.json`。
3. `Settings | Build, Execution, Deployment | Toolchains` 选择/新建工具链，C/C++ 编译器由 preset 的 toolchain file 固定为 `arm-none-eabi-gcc`。
4. 选择 `BluePill SPL Debug` preset，执行 Build；产物必须是 `build/debug/spl-f1-blink.elf`。
5. `Run | Edit Configurations` 新建 **OpenOCD Download & Run**：
   - Target：`spl-f1-blink`
   - Executable：生成的 ELF
   - Board config：`openocd/bluepill-stlink.cfg`
   - GDB：GNU Arm 工具链的 `arm-none-eabi-gdb`
6. Run 会下载并复位；Debug 会下载、复位并附加 GDB。若 CLion 只索引不构建，先看 CMake Profile 是否继承到了 `SPL_ROOT`。

官方依据：[CLion Embedded development](https://www.jetbrains.com/help/clion/embedded-overview.html)、[OpenOCD support](https://www.jetbrains.com/help/clion/openocd-support.html)。

## 4. VS Code 开发方式

推荐扩展已写入 `.vscode/extensions.json`：C/C++、CMake Tools、Cortex-Debug。

1. 从已设置 `SPL_ROOT` 的终端运行 `code .`，让 VS Code 继承环境变量。
2. `Ctrl+Shift+B` 调用 `.vscode/tasks.json`：先 `cmake --preset debug`，再构建。
3. 打开 Run and Debug，选择 **BluePill SPL: OpenOCD**。
4. `.vscode/launch.json` 使用同一个 ELF、同一个 `openocd/bluepill-stlink.cfg` 和 `arm-none-eabi-gdb`，启动前自动执行构建任务。
5. 若 Cortex-Debug 报找不到 OpenOCD，在扩展设置中填写 OpenOCD 路径；若只报红波浪线但 CMake 能编译，执行 `CMake: Configure` 生成 `compile_commands.json`，不要手工复制一套 includePath。

如果改用 PlatformIO，应在 `platformio.ini` 明确 `board`、`framework`、`upload_protocol = stlink` 和 `debug_tool = stlink`。PlatformIO 自带 Core，不要再混用另一套全局 Core。官方依据：[PlatformIO IDE for VS Code](https://docs.platformio.org/en/stable/integration/ide/vscode.html)、[ST-LINK 配置](https://docs.platformio.org/en/stable/plus/debug-tools/stlink.html)。

## 5. 烧录与验收

```bash
openocd -f openocd/bluepill-stlink.cfg \
  -c "program build/debug/spl-f1-blink.elf verify reset exit"
```

验收顺序：

1. 构建日志无 warning，ELF/HEX/BIN/MAP 全部生成。
2. OpenOCD 报 verify success，并复位运行。
3. PC13 板载 LED 约 1 Hz 闪烁；逻辑分析仪测得完整周期约 1 s。
4. 在 `SysTick_Handler` 下断点，确认每 1 ms 进入一次；随后移除断点再测周期，避免调试器改变时序。

## 6. 常见失败

| 现象 | 第一边界 | 处理 |
| --- | --- | --- |
| CMake 报 `SPL_ROOT` 空 | IDE 没继承环境变量 | 从设置过变量的终端启动 IDE，或在 CMake Profile 显式设置 |
| 找不到 `core_cm3.h` | 冻结镜像使用 `.old` 后缀 | 必须经本项目 CMake fallback 复制到 build，不改上游检出 |
| `multiple definition of SysTick_Handler` | 同时编译模板和本示例 `stm32f10x_it.c` | 只编译本示例文件，它替换模板文件 |
| 编译通过、链接找不到 GPIO/RCC | 只加 inc，没加驱动 `.c` | 由 CMakeLists 固定加入 `stm32f10x_gpio.c`、`stm32f10x_rcc.c` |
| IDE 能索引但不能构建 | IDE 自己选了宿主编译器 | 使用 preset 和 toolchain file，检查日志中的编译器路径 |
| OpenOCD 找不到目标 | cfg 或驱动错误 | ST-Link 接 SWDIO/SWCLK/GND，目标配置用 `stm32f1x.cfg` |
| 下载后灯不闪 | PC13 极性、时钟或 SysTick 不对 | 检查高电平灭/低电平亮、`SystemCoreClock` 与 SysTick 频率 |
