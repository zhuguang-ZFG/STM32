# 开源项目事实核验记录（2026-10-26）

核验方式：GitHub MCP `search_repositories` 取仓库存在性与活跃度（stars / updated_at）；
许可读各仓库 `LICENSE`（raw.githubusercontent）原文首行。社区入口逐条 GET 验活。

| 项目 | 仓库 | 许可（原文核对） | stars | 最近更新 |
|---|---|---|---|---|
| FreeRTOS 内核 | FreeRTOS/FreeRTOS-Kernel | MIT（freertos.org/licensing 页确认） | 4.6k | 2026-10-26 |
| Zephyr | zephyrproject-rtos/zephyr | Apache-2.0（LICENSE 正文） | 16.9k | 2026-10-26 |
| RT-Thread | RT-Thread/rt-thread | Apache-2.0（LICENSE 正文） | 12.3k | 2026-10-26 |
| NuttX | apache/nuttx | Apache-2.0（LICENSE 正文） | 4.1k | 2026-10-26 |
| RIOT | RIOT-OS/RIOT | LGPL-2.1（LICENSE 正文） | 5.8k | 2026-10-26 |
| littlefs | littlefs-project/littlefs | BSD-3-Clause（LICENSE.md） | 7.0k | 2026-10-25 |
| SPIFFS | pellepl/spiffs | MIT（LICENSE） | 1.6k | 2026-10-20 |
| lwIP | lwip-tcpip/lwip | BSD-3-Clause（COPYING，SICS 版） | 1.8k | 2026-10-25 |
| NimBLE | apache/mynewt-nimble | Apache-2.0（Apache 组织仓库） | 895 | 2026-10-23 |
| TinyUSB | hathach/tinyusb | MIT（LICENSE） | 7.2k | 2026-10-26 |
| LVGL | lvgl/lvgl | MIT（LICENCE.txt） | 25.0k | 2026-10-26 |
| pyOCD | pyocd/pyOCD | Apache-2.0（LICENSE 正文） | 1.5k | 2026-10-22 |
| probe-rs | probe-rs/probe-rs | MIT OR Apache-2.0（LICENSE-MIT 存在） | 3.0k | 2026-10-26 |
| OpenOCD | openocd-org/openocd | GPL-2.0-or-later（COPYING，SPDX 行）；只读镜像 | 2.4k | 2026-10-25 |
| Unity | ThrowTheSwitch/Unity | MIT（LICENSE.txt） | 5.4k | 2026-10-25 |
| CMock | ThrowTheSwitch/CMock | MIT（LICENSE.txt） | 846 | 2026-10-24 |
| ESP-IDF | espressif/esp-idf | Apache-2.0（LICENSE 正文） | 19.3k | 2026-10-26 |
| pico-sdk | raspberrypi/pico-sdk | BSD-3-Clause（LICENSE.TXT） | 5.0k | 2026-10-25 |

社区入口验活：freertos.org/Community ✓（200，页面含社区与许可说明）；docs.zephyrproject.org/latest/ ✓（Zephyr 4.5.0-rc3 main）；
club.rt-thread.org 返回 HTTP 468（反爬），未采用，改指仓库 Issues。
api.github.com 直连 403（需 UA/鉴权）→ 元数据改走 GitHub MCP。
