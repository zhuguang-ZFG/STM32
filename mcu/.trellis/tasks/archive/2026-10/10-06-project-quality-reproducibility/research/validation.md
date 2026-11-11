# 本地与远端验收记录

记录时间：2026-10-06T23:54:33。基线提交 d3958c7，该时间对应本地快照；后续已于 2026-10-07 完成提交、推送与远端 CI。硬件测量仍未执行。

## 结果

| 验收 | 结果 | 证据 |
|---|---|---|
| A1 / 实验复现 | 本地通过 | E05/E07/E08 独立工程及说明完成；E01–E08 文稿/代码/实测状态分离；E04/E06 缺配套工程如实标建设中 |
| A2 / 场景切换 | 通过 | 1→2→1、五场景实际构建、二进制 hash、flash 目标、非法值测试 |
| A3 / 发布门禁 | 远端通过 | 25 个单元测试、3 个浏览器回归、ARM/host、六项 IDF 矩阵与 Pages 全部成功 |
| A4 / 工程统计 | 通过 | 清单 19 项；空目录、未登记入口、重复/缺失入口、错误 target 回归通过 |
| A5 / ESP32 README | 通过 | 三个既有工程独立说明，六个 IDF 工程均按 S3 重建并运行 size；见下表 |
| A6 / 内容/元数据 | 通过 | 数据率、实验步骤、时长难度统一；元数据与实验验证状态失败案例已测 |
| A7 / 全站检查 | 通过 | npm run quality：25 单元测试、工程清单、docs build、34 SVG lint、README、88 根文档链接 |
| A8 / 高亮与浏览器 | 通过 | ld/gdb 实际高亮 token 测试；3 浏览器测试；搜索索引测量见 performance.md |

## 固件工具链与命令

- ARM：xPack GNU Arm Embedded GCC 15.2.1，PATH 中的 mingw32-make + Git usr/bin。
- FreeRTOS：上游 V11.1.0，ARM_CM4F，内核路径 .trellis/ref/freertos-v11/kernel。
- `npm run firmware:check` 成功：7 个 ARM 工程（其中 RTOS 五场景）、6 个宿主/工具链工程。
- 检查读取 bin 前两个字与 ELF 符号对照，覆盖初始 SP 与复位 Thumb 位。GD32 原复位字为偶数，已用 .thumb_func 修复；FPU 使能补齐。
- B3 probe 的 RAM 越界/非法区域属性例子会故意产生链接错误；脚本捕获预期失败并退出 0，不是未修复的构建失败。
- IDF：源码 v5.5.2，独立 build/quality 与 SDKCONFIG，显式 IDF_TARGET=esp32s3，执行 build size。
- 原有三份 sdkconfig 为 esp32，已提供明确 set-target 说明、CI 独立配置和 CMake 芯片检查，防止错误目标静默通过；未批量覆盖旧 sdkconfig。

| 工程 | IDF 版本 | 实际 target | app bin 字节 | SHA-256 前 16 位 |
|---|---|---|---:|---|
| esp32-00-hello | v5.5.2 | esp32s3 | 190240 | `fa8585968163f064` |
| esp32-01-gpio-matrix | v5.5.2 | esp32s3 | 200512 | `9aaad1e830fd7805` |
| esp32-02-uart-events | v5.5.2 | esp32s3 | 211664 | `5cd66c8f32b16b3b` |
| esp32-03-ledc-fade | v5.5.2 | esp32s3 | 202560 | `52a981c389f2253c` |
| esp32-04-qmi8658 | v5.5.2 | esp32s3 | 212448 | `a50f6e13a3369fdf` |
| esp32-05-audio-play | v5.5.2 | esp32s3 | 268960 | `e6f3aec6b7296fc1` |

可复跑命令：

~~~text
npm run quality
npm run firmware:check
npx playwright install chromium
npm run test:browser
npm run site:measure -- current
~~~

本机浏览器使用 `PLAYWRIGHT_CHANNEL=msedge`；CI 使用 Chromium。CI IDF 镜像 espressif/idf:v5.5.2，清单生成六项矩阵。checkout@v7、setup-node@v7、deploy-pages@v5 标签已通过官方 GitHub API 确認存在。

## 一手依据

- [立创板卡介绍](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/introduction.html)：扩展口 GPIO10/11。
- [立创 QMI8658 教程](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/attitude-sensor.html)：I2C GPIO1/2、0x6A、ID、寄存器图与读取路径；示例改用新 I2C master，配置关闭自测试。
- [立创 ES8311 教程](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/audio-output-es8311.html)：I2S GPIO38/14/13/45、PCA9557 0x19 bit1 控功放。
- 本机 IDF v5.5.2 i2s_es8311 示例与 esp_codec_dev 1.3.4 源码；组件哈希在新音频 dependencies.lock 固定。
- [ST HAL I2C 源码](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/master/Src/stm32f4xx_hal_i2c.c)：HAL_I2C_Mem_Read 单字节接收先关 ACK、清 ADDR、STOP、再等 RXNE。

## 未执行与集成事项

- 没有上板或测量仪器结果。串口枚举仅见两个 Bluetooth COM 端口，未识别到本次 ESP32 USB 调试口；无烧录操作。
- 已推送代码提交 `286d692e124f484557c8fb8c1c1780c0fc7dccd3`，全部 9 个远端 jobs 成功：[CI 与部署记录](https://github.com/zhuguang-ZFG/mcu/actions/runs/37492733587)。
- 用户明确授权提交推送后，B3 原有正文和取证工程原样作为独立提交 `50d6e5e` 集成；质量修复为 `286d692`。远端清单引用完整，没有遗漏原未跟踪文件。
- npm audit 当前仍报告既有 VitePress/Vite/esbuild 开发工具链 3 项传递漏洞（2 moderate、1 high），npm 给出无自动修复。新增 yaml 使用修复后的 2.8.3；未越过方案范围强升 VitePress 主版本。生产交付为静态文件，这不等于开发服务器漏洞已修复。
- 软件修复、集成与 CI 验收完成，可归档本任务。上板验证为明确保留的后续实测，不把 CI 当硬件证据。

## 2026-10-07 提交与发布

用户授权“提交推送，并 CI 通过”。首轮运行的完整状态摘要见 ci-first-success.json；文档、浏览器、ARM/host、六个 ESP32-S3 工程和 Pages 均为 success。
