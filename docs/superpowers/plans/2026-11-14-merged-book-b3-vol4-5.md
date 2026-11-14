# 双书合并 B3（卷 4–5：多平台与连接 + 运动控制）Implementation Plan

**Scope:** 卷 4（ch28–35，8 章）与卷 5（ch36–39，motor 合流，4 章）共 12 章；资产迁移 148 处引用；新手绘板 4 块；motor 数值断言测试迁移；B1/B2 前向引用清扫；CI 扩量与批次证据。

**Architecture:** 沿用 B1/B2 的质量门（`book/checks.py` 章节契约/链接锚点/资产/测验、`book/build_html.py --check` 临时站、`book/mapping.py` 状态机、`tools/slop_lint.py` 平实文风）。12 章正文只写进 `docs/v4-platforms/` 与 `docs/v5-motion/`；资产按 Task 1 底表迁入 `docs/public/`；ch29–32 缺手绘源，Task 2 用确定性 kit 生成 4 块新板；motor 手绘板从 `feat/motor-ch29-32-placement` 分支按文件取件（该分支未并入 main，禁合并）。章节结构固定为罗盘/先做出来/机制/测量与证据/失败分支（多平台章加跨平台边界），测验沿用「无可用 JSON 不新造」的 B2 ch26/27 先例，ch28–39 全部不挂 QuizBank。

**来源研究：** `.superpowers/sdd/2026-11-14-merged-book-b3-vol4-5/research/` 下四份：`b3-migration-gd32-sources.md`（ch28/29）、`b3-esp32-sources.md`（ch30/31/32）、`b3-network-multicore-fieldbus-sources.md`（ch33/34/35）、`b3-motor-sources.md`（ch36–39 + 测试迁移方案）。各章「必须覆盖」与禁抄清单以研究文档为准，本计划逐章内联要点；冲突时以研究文档的上游核对结论为准。

## Global Constraints

- 仅中文书稿；不处理英文版（B5 归档）。
- 旧树零改动：`docs/00-28*.md`、`docs/en/**`、`stm32-book/**`、`mcu/**`、`scripts/legacy-redirects.mjs` 一律不改；本批新增 `docs/v4-platforms/`、`docs/v5-motion/`，并只改 `docs/public/`、`book/data/mapping.tsv`、`plans/2026-11-12-merged-book/`（`mapping.json`、`README.md`、`evidence/b3-local.md`）、`.github/workflows/merge-check.yml`、`book/tests/test_motor_numbers.py`（新增）。**唯一例外（显式授权）**：Task 15 删除 `stm32-book/tests/test_motor_draft_numbers.py`——设计规格（merged-book-design.md §5）明文「motor 数值断言测试随新章迁移」，且旧测试断言对象是 chapters-draft 草稿路径，落位后守卫对象必须换成新书章节；删除与新测试加入遵循「先加后删」，任一中间状态都有哨兵。
- 依赖不变：不新增、不升级任何依赖；新板渲染用 `tools/handraw_track/render.py`（playwright，已在旧书工具链，不进 `book/requirements.txt`）。
- 站点临时构建 = `python -m book.build_html --check`；生产 VitePress 站点与 `/STM32/` base 切换仍属 B5。
- 章节文件名、标题、平台来自 `book/data/toc.tsv`，不许改 toc 迁就正文。
- 章节结构固定：frontmatter（`title`、`platforms`）→ `# 标题` → `## 本章罗盘`（**问题** / **交付** / **边界** / **依据锚点**）→ `## 先做出来` → `## 机制` → `## 测量与证据` → `## 失败分支` → `## 离开检查`；多平台章（ch28/29/33/34/35）在「失败分支」后加 `## 跨平台边界`。
- 图片引用根绝对路径（`/figures/x.svg`、`/images/x.png`、`/anim/x.svg`、`/arch/x.png`）；`alt` 必填；禁止外链图片；禁止 `../assets/...`。
- 章间链接一律**内联**相对 `.md` 路径；禁止根绝对页面链接；禁止新增引用式链接定义。
- 证据标签固定四类：实测记录 / 来源说法(未复核) / 文档推导 / 未实测。ch28–39 六源零实测、motor「实验待执行（实物未到）」全数保留，不得改写成结论。
- 版本钉：ESP32 三章按 **ESP-IDF v5.5.2**（研究实取核对）；GD32 按 **GD32 官方固件库 @10d02f4**、**gd32vf103 固件库 @bc2be118**、NMSIS；lwIP 按 **stm32-mw-lwip @07680c81（lwIP 2.2.1，ST fork）**；H7 按 RM0433/RM0399/AN4891/AN5557；bxCAN 按 RM0008 §24 / RM0090 §32；motor 按 hardware-freeze v1.2 + TB6612FNG datasheet（Pololu 0J86 镜像）+ RM0008 + DS5319。行号引用只写研究文档真实取到的，写不出行号就标「来源说法待核」。
- mapping 状态机：`planned` → `partial` → `migrated`，与章节文件存在性一致。双目标行落位规则：`docs/25-STM32H7引脚.md`→ch28;ch34 在两章都写完后于 ch34 任务置 `migrated`；`mcu/docs/esp32/04-irq-dualcore.md`→ch10;ch34 同理；`mcu/docs/lab/e08-audio-play.md`→ch31;ch40 本批结束保持 `partial`（ch40 属 B4）。
- 所有提交按显式路径暂存，禁止 `git add -A` / `git add .`。
- 远程推送、PR 合入与 Pages 切换需另行授权；本计划只做本地提交。

---

### Task 1: B3 共享资产迁移（145 个文件）

**Files:**
- Create: `docs/public/anim/*.svg`（36 项中 2 个已在库）、`docs/public/figures/*.svg`（37 项）、`docs/public/arch/*.png`（5 项）、`docs/public/images/**`（70 项中 1 个已在库）
- Modify: `book/data/mapping.tsv`（无——mapping 在各章任务里推进）
- Generated: 无

**Interfaces:**
- Consumes: 根书 `assets/{diagrams,animations,illustrations,boards,photos,gif}/`、MCU 站 `mcu/docs/public/{anim,figures,arch,images}/`、motor 分支 `feat/motor-ch29-32-placement:assets/illustrations/handraw/`
- Produces: `docs/public/` 供 12 章引用；0 缺失资产

**底表：** `.superpowers/sdd/2026-11-14-merged-book-b3-vol4-5/task1-assets.md`（148 行映射，去重后 145 个待迁）。改名规范：

| 源树 | 目标 |
| --- | --- |
| `mcu/docs/public/anim/*.svg` | `docs/public/anim/` |
| `mcu/docs/public/figures/*.svg` | `docs/public/figures/` |
| `mcu/docs/public/arch/*.png` | `docs/public/arch/` |
| `mcu/docs/public/images/**` | `docs/public/images/` |
| 根书 `assets/animations/*.svg`、`assets/gif/*.gif` | `docs/public/anim/` |
| 根书 `assets/diagrams/*.svg` | `docs/public/figures/` |
| 根书 `assets/illustrations/handraw/*.png` | `docs/public/images/` |
| 根书 `assets/boards/*.svg` | `docs/public/images/boards/` |
| 根书 `assets/photos/*.jpg` | `docs/public/images/photos/` |

已在库跳过 3 个：`anim/env-setup-flow.svg`、`anim/iram-discipline.svg`、`figures/esp32-04-int-alloc.svg`。

**motor 手绘板取件（15 块，从 motor 分支按文件取，禁合并该分支）：**

```bash
for f in ch29-current-tiers ch29-fault-triage ch29-five-states ch29-two-supplies \
         ch30-no-spin-triage ch30-pwm-math ch30-signed-duty ch30-stop-triage \
         ch31-quadrature ch31-rpm-formula ch31-wrap-triage \
         ch32-loop-fault-triage ch32-pi-step ch32-state-machine ch32-tuning-ladder; do
  git show feat/motor-ch29-32-placement:assets/illustrations/handraw/$f.png > docs/public/images/$f.png
done
```

注意命名口径：这些板沿用旧书章号前缀（ch29→合并书 ch36、ch30→ch37、ch31→ch38、ch32→ch39），与既有 `ch15-*`、`ch28-*` 的用法一致；alt 文本里写清对应关系。

- [ ] **Step 1: 按底表复制 145 个文件（脚本化，逐文件存在性断言）**
- [ ] **Step 2: 验证**

Run: `python -m book.build_html --check`（页数不变：`built 27 pages, 25 planned chapters missing`）

Run: `git status --short` 确认只新增 `docs/public/**`。

- [ ] **Step 3: 提交**

```bash
git add docs/public
git commit -m "feat(assets): migrate volume 4-5 shared assets into docs/public (B3)"
```

---

### Task 2: 新手绘板生成（ch29–32 各 1 块）

**Files:**
- Create: `tools/handraw_track/fig_merged_b3.py`（确定性生成脚本，import `hd.Fig`，输出 SVG 到 `.temp/b3-plates/` 再用 `render.py` 截 PNG 到 `docs/public/images/`）
- Create: `docs/public/images/mc29-gd32-contrast.png`、`mc30-s3-boot-chain.png`、`mc31-matrix-audio.png`、`mc32-wifi-espnow.png`（+ `.temp` 内 SVG 中间产物，不入库）
- Modify: 无旧书文件（`assets/illustrations/handraw/` census 不动，protected contract）

**Interfaces:**
- Consumes: `tools/handraw_track/hd.py`（`Fig`/`save`，1152×864，米纸/墨线/普鲁士蓝·灰绿·砖红·拿波黄，wobbly polyline，`Segoe Print` 字系）
- Produces: 4 块中文标注手绘板，每块角标「原理示意 / 非实拍」

**板面主题（对应研究文档锚点）：**

1. `mc29-gd32-contrast`：GD32 与 STM32 的时钟树/外设对照——RCU vs RCC 的三条差异（PLL1/PLL2 配而不用、APB2/APB1 分频上限、IRC48M），USART0=APB2@0x40011000 的落点标注（研究 §3.b）。
2. `mc30-s3-boot-chain`：三棒接力启动链——ROM `rst:` → bootloader `boot:` → app `app_start:`，每棒一条卡点判据；XIP/Cache 窗口注记（研究 §2 必写第 1、3 条）。
3. `mc31-matrix-audio`：音频双面范式——控制面 I2C（ES8311/ES7210 寄存器）+ 数据面 I2S（MCLK=256×fs），MCLK/采样率/缓冲三笔账一处画清（研究 §3 必写第 7 条）。
4. `mc32-wifi-espnow`：Wi-Fi 事件循环六步骨架 + 重连退避 1→60s 刻度 + ESP-NOW 直连旁路对照（研究 §4 必写第 1、2、8 条）。

- [ ] **Step 1: 写 `fig_merged_b3.py`（每板独立 seed，逐板文本内容写进脚本注释并对照研究锚点）**
- [ ] **Step 2: 生成 4 块 SVG → render.py 出 PNG → 复制到 `docs/public/images/`**

Run: `python tools/handraw_track/fig_merged_b3.py && python tools/handraw_track/render.py .temp/b3-plates/mc29-gd32-contrast.svg .temp/b3-plates/mc30-s3-boot-chain.svg .temp/b3-plates/mc31-matrix-audio.svg .temp/b3-plates/mc32-wifi-espnow.svg`

- [ ] **Step 3: 提交**

```bash
git add tools/handraw_track/fig_merged_b3.py docs/public/images/mc29-gd32-contrast.png docs/public/images/mc30-s3-boot-chain.png docs/public/images/mc31-matrix-audio.png docs/public/images/mc32-wifi-espnow.png
git commit -m "feat(figures): generate four handraw plates for merged ch29-32 (B3)"
```

---

### Task 3: ch28《芯片迁移方法论与引脚/外设差异》

**Files:**
- Create: `docs/v4-platforms/28-chip-migration-differences.md`
- Modify: `book/data/mapping.tsv`（`docs/23-STM32G0引脚.md`→ch28、`docs/24-STM32L4引脚.md`→ch28、`mcu/docs/gd32/04-periph-diff.md`→ch28 → `migrated`；`docs/25-STM32H7引脚.md`→ch28;ch34 保持 planned）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 芯片迁移方法论与引脚/外设差异`、`platforms: [f407, f103]`。

**必须覆盖（锚点见研究 §2）：**

- 迁移方法论四步：引脚与供电 → 时钟与启动 → 外设复用 → 证据对账；每步一个「第一处失效点」。
- G0：BOOT 采样在第四个 SYSCLK 上升沿锁存、BOOT0 专用脚（F103 是 PB 引脚复用）与 NRST 专用化；`sample-23-boot-latch` 机制的转述。
- G0 与 F1 的 SWD 复用冲突（PA13/PA14/PA15、PB3/PA4 重映射）与「先取证再动选项字节」。
- L4：引脚编号从第 1 脚 VBAT（G0 是 PC11）起数的方法论；HSE 在 PH0/PH1（F103 的 PD0/PD1 陷阱）；Shutdown 档的保留域。
- H7：第 1 脚与 LQFP144 数法、VCAP 电容、电源域 D1/D2/D3 概览（Cache 细节归 ch34，一句划界）。
- 迁移分诊四层（引脚与供电/时钟启动/外设/软件），`sample-25-migrate-triage` 与 `ch24-migrate-boundary` 的方法论转述。
- GD32 对照的口径：G4 讲的是 **GD32F4xx 系列**（禁抄「GD32F407」芯片名笔误）；外设差异表按 G4:79-117 重述。
- 数据手册电流数值带「指定条件典型值」限定转述（禁抄封面电流当实测）。
- PLLN=480 不是官方示例（CubeH7 基线 400），引用必须带 Rev V + 8 MHz bypass + LDO 板三前提。
- VBAT 脚位问题：P25 自测问了没答，ch28 补 DS12110 出处或删问。
- SYSCFG_CFGR1 重映射说法按 RM0444 复核后再落表（研究未能核对 CubeG0 头文件）。

**图片引用（至少 4 张）：** `/images/ch24-migrate-boundary.png`（手绘）、`/anim/gd32-periph-diff.svg`、`/figures/sample-25-migrate-triage.svg`、`/figures/h7-pinmux-conflicts.svg`。

**至少 3 条相对 `.md` 链接：** `../v1-drivers/09-gpio.md`、`../v1-drivers/08-architecture-memory-clock.md`、`./34-multicore-cache.md`（ch34 落位后该链接在本章提交时即可用——ch28 在 ch34 之前提交，此时只链已存在的；写 `./34-multicore-cache.md` 会红，故先链 `../v1-drivers/17-flash-iap-ota.md`，ch34 落位后的交叉链接归 Task 16）。

**验证：** `python -m book.checks --chapter ch28`、`python tools/slop_lint.py docs/v4-platforms/28-chip-migration-differences.md`、`python -m book.build_html --check`（`built 28 pages, 24 planned chapters missing`）、`python -m book.mapping --check`。

**提交：** `feat(ch28): rewrite chip-migration methodology chapter (B3)`

---

### Task 4: ch29《GD32 系列对照（ARM + RISC-V）》

**Files:**
- Create: `docs/v4-platforms/29-gd32-arm-riscv.md`
- Modify: `book/data/mapping.tsv`（`gd32/00-env`、`01-rcu-clock`、`02-gpio-af`、`03-usart`、`05-riscv-toolchain`、`06-clic-irq`、`07-rcu-108m`、`08-mtime-delay`、`09-gpio-minimal` → `migrated`，共 9 行）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: GD32 系列对照（ARM + RISC-V）`、`platforms: [gd32]`。版本钉：GD32F4xx 官方固件库 @10d02f4、gd32vf103 固件库 @bc2be118、NMSIS。

**必须覆盖（锚点见研究 §3）：**

- 双核两条产品线：GD32F4xx（Cortex-M4，<数百 MHz）与 GD32VF103（RV32IMAC，Bumblebee N200 核）；一句「同一外设骨架，两套指令集与中断控制器」。
- RCU vs RCC：PLL1/PLL2「配置并使能了、但不在时钟路径」（修正 V2「没使能」）；APB1/APB2 分频上限差异；IRC48M。
- SystemInit 默认 168 MHz（官方库 `system_gd32f4xx.c:56`），200M 是可选预设档——禁抄「官方默认 200MHz」。
- GPIO AF 模型差异与 `gd32-af-mux` 动画机制转述。
- USART：STAT0@0x00、CTL0@0x0C（上游 `gd32f4xx_usart.h:51-60` 定谳；禁抄 G3 错位表）；USART0=0x40011000（APB2），APB1+0x4400 是 USART1。
- CLIC/ECLIC vs NVIC：向量表组织、中断级数、`n200_eclic.h` 行号按研究第 4 节修正锚引用。
- mtime/mtimecmp 延时与 SysTick 的对照（`riscv-mtime-tick` 动画）；`n200_timer.h` 行号修正。
- 108 MHz 超频前提与官方标称关系（VF103 库 @bc2be118）。
- 工具链差异：`riscv-none-embed`/`riscv-none-elf` 三元组与调试器链路（`riscv-toolchain-flow` 动画）。
- F470 240MHz 与 F4xx 200MHz 两口径矛盾：择一并以原件为准，另一处标存疑（研究 §3.e 第 7 条）。
- V 篇行号整体偏移 1–3 行：引用一律按研究第 4 节修正锚落笔。

**图片引用（至少 5 张）：** `/anim/gd32-rcu-clock.svg`、`/arch/rcu-tree.png`、`/anim/gd32-af-mux.svg`、`/images/mc29-gd32-contrast.png`（Task 2 新板）、`/anim/riscv-clic-priority.svg`、`/anim/riscv-mtime-tick.svg`、`/arch/usart-rename-map.png`。

**至少 3 条相对 `.md` 链接：** `../v1-drivers/08-architecture-memory-clock.md`、`../v1-drivers/10-interrupts-nvic-exti.md`、`../v1-drivers/13-uart-framed-protocol.md`。

**验证：** checks ch29、slop、`built 29 pages, 23 planned chapters missing`、mapping。

**提交：** `feat(ch29): rewrite GD32 ARM+RISC-V comparison chapter (B3)`

---

### Task 5: ch30《ESP32-S3 架构、启动与工程》

**Files:**
- Create: `docs/v4-platforms/30-esp32s3-architecture-boot.md`
- Modify: `book/data/mapping.tsv`（`esp32/00-env`、`01-arch-boot`、`03-idf-anatomy` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: ESP32-S3 架构、启动与工程`、`platforms: [esp32]`。版本钉：ESP-IDF v5.5.2。

**必须覆盖（锚点见研究 §2）：**

- 三棒接力启动链与日志分诊法（`rst:`/`boot:`/`app_start:`）；每棒一条卡点判据。
- `app_main` 真实身份：main task 一次调用，优先级 1、栈 **3584** 起（+`TASK_EXTRA_STACK_SIZE`）、默认 CPU0、返回即 `vTaskDelete(NULL)`（上游 `app_startup.c:83,158,206-210`）。
- XIP/Cache 映射与 IRAM 纪律的由来：关 Cache 期间 Flash 不可取指；与 F407「原地执行」的架构差。
- 分区表是数据化的 MEMORY：四列、Offset 留空、`idf.py partition-table` 回读；OTA 地基。
- 组件化三板斧与依赖拓扑；main 是自动收集的项目组件——**行号 `project.cmake:465`，禁抄 `build.cmake:465`**。
- Kconfig 三段论（菜单→`sdkconfig`→`sdkconfig.h/.cmake/.json`）、`DO NOT EDIT`、`sdkconfig.defaults`；`CONFIG_IDF_TARGET_ESP32S3` 闭环。
- 双核默认分工与 SMP 口径回链 ch27（不重新论证）；PRO_CPU/APP_CPU 是默认分工不是硬约束（可钉核）。
- 目标守卫：残留错目标 `sdkconfig` 会静默编错芯片。

**禁抄：**「main task 默认栈 8KB」；`ESP_TASK_MAIN_STACK = CONFIG_ESP_MAIN_TASK_STACK_SIZE`（漏 EXTRA）；「main 组件收集在 build.cmake:465」；把 `.trellis/ref/idf-00-hello.log`、890 项、size 数字当仓库现存证据（要引就标「来源说法(未复核)」）。

**图片引用（至少 5 张）：** `/images/mc30-s3-boot-chain.png`（新板）、`/anim/esp32-boot-relay.svg`、`/arch/boot-relay.png`、`/anim/kconfig-pipeline.svg`、`/anim/iram-discipline.svg`、`/images/boards/esp32s3-wroom1-module.jpg`。

**至少 3 条相对 `.md` 链接：** `../v1-drivers/08-architecture-memory-clock.md`、`../v0-foundations/05-toolchain-four-steps.md`、`./31-esp32-drivers-audio.md`。

**验证：** checks ch30、slop、`built 30 pages, 22 planned chapters missing`、mapping。

**提交：** `feat(ch30): rewrite ESP32-S3 architecture/boot chapter (B3)`

---

### Task 6: ch31《ESP32 外设、驱动框架与音频链路》

**Files:**
- Create: `docs/v4-platforms/31-esp32-drivers-audio.md`
- Modify: `book/data/mapping.tsv`（`esp32/02-gpio-matrix`、`05-uart-driver`、`06-spi-i2c-driver`、`07-timer-ledc`、`12-audio-path` → `migrated`；`e08-audio-play`→ch31;ch40 保持 partial）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: ESP32 外设、驱动框架与音频链路`、`platforms: [esp32]`。

**必须覆盖（锚点见研究 §3）：**

- IO_MUX 与 GPIO Matrix 分工与「任意引脚四前提」；45=22+23 算术与 `SOC_GPIO_PIN_COUNT=49` 编号口径并存。
- 占用脚与 strapping 清单：IO35/36/37（八线 PSRAM）、GPIO0/45/46；「一碰就崩」是物理层失败。
- UART 三层缓冲与三个溢出点、事件≠数据、timeout_flag 判帧；`uart_driver_install` 六参数按 v5.5.2 签名。
- SPI 两级模型与事务队列、DC/CS 之别、异步事务 buffer 生命周期。
- I2C 新驱动句柄模型与 `transmit_receive` 末参毫秒超时；7 位地址不左移。
- LEDC 两级配置、S3 边界（8 通道/14 位/仅低速）、双缓冲 update、硬件 fade；禁套经典 ESP32 结论；`LEDC_FADE_*` 在 `hal/ledc_types.h`。
- 音频「控制面 I2C + 数据面 I2S」范式与 MCLK=256×fs；512kbps/4.096MHz/10ms 三笔账一起算。
- 单声道走 stereo 双槽位、PA_EN 在扩展器、先静音后发声三段纪律。
- 延迟账与缓冲容量算法（采样率×容忍延迟×2），BLOCK_FRAMES=160→20ms 往返。
- ES7210「四通道用其三」与双麦对不上：器件细节须 wiki 核对，核不到标待核；esp_codec_dev 1.3.4 是 managed component 不是 IDF 自带。
- 「学时序手写、做产品用框架」收尾回链 ch16。

**禁抄：** 板级常数（ST7789 引脚、QMI8658 寄存器、ES8311/PCA9557 地址）当通用常数；「40MHz 理论带宽 5MB/s」当实测（是算术）；「毛刺过滤 S3 新增」当已核对结论。

**图片引用（至少 6 张）：** `/images/mc31-matrix-audio.png`（新板）、`/anim/gpio-matrix-routing.svg`、`/figures/esp32-02-pad-attrs.svg`、`/anim/idf-uart-events.svg`、`/figures/esp32-05-uart-config.svg`、`/anim/ledc-timer-channel.svg`、`/anim/esp32-audio-path.svg`、`/figures/esp32-12-i2s-clock.svg`、`/images/labs/e08-audio-chain.svg`。

**至少 3 条相对 `.md` 链接：** `../v1-drivers/13-uart-framed-protocol.md`、`../v1-drivers/16-i2c-spi.md`、`../v1-drivers/12-timers-pwm.md`、`./32-esp32-wifi-ble-espnow.md`。

**验证：** checks ch31、slop、`built 31 pages, 21 planned chapters missing`、mapping。

**提交：** `feat(ch31): rewrite ESP32 peripherals/drivers/audio chapter (B3)`

---

### Task 7: ch32《Wi-Fi、蓝牙与 ESP-NOW》

**Files:**
- Create: `docs/v4-platforms/32-esp32-wifi-ble-espnow.md`
- Modify: `book/data/mapping.tsv`（`esp32/08-wifi`、`09-bt-espnow` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: Wi-Fi、蓝牙与 ESP-NOW`、`platforms: [esp32]`。

**必须覆盖（锚点见研究 §4）：**

- Wi-Fi 状态机 + 事件循环世界观；handler 不能阻塞、长操作外置定时器/任务。
- 骨架六步顺序铁律与每步失败后果；`esp_wifi_start` 异步、connect 等 STA_START。
- DISCONNECTED 分诊：reason 201 找不到 AP、15 四次握手超时、202 认证失败、203 关联失败；指数退避 1→60s。**禁抄「4=关联被拒」**（4=ASSOC_EXPIRE 且已弃用）。
- NVS 是 Wi-Fi/BT 第一依赖（校准数据 + MAC）；`NO_FREE_PAGES`/`NEW_VERSION_FOUND` 自愈路径。
- S3 单模 BLE + BLE 5.0（`soc_caps.h:594-596`）；Controller/Host/HCI 分层与「协议栈是预编译巨人」。
- NimBLE/Bluedroid 二选一：choice 互斥、**默认 Bluedroid**、符号 `CONFIG_BT_NIMBLE_ENABLED`/`CONFIG_BT_BLUEDROID_ENABLED`；S3 选 NimBLE 的理由是「没有经典蓝牙可跑」不是默认值。
- GATT 三级容器与 CCC 订阅；GAP 四角色与广播间隔权衡。
- ESP-NOW 三步顺序、peer 结构、双回调签名（v5.x info 结构体版）、250/1470 分片、加密 peer 6/总 peer 20；`ESP_ERR_ESPNOW_CHAN` 分诊；recv_info 临时变量纪律。
- 共存信道规则一句带过。

**禁抄：** 旧版 ESP-NOW 回调签名；`WIFI_EVENT_*` 出处写 `esp_wifi_types.h`（v5.5 实体在 `esp_wifi_types_generic.h`）；「handler 里 vTaskDelay 丢 BLE 事件」当实测（机制推论）；E8 的 `wifi:state: init...` 日志逐字当真实串口输出。

**图片引用（至少 4 张）：** `/images/mc32-wifi-espnow.png`（新板）、`/arch/wifi-stack.png`、`/figures/esp32-08-backoff.svg`、`/anim/esp32-espnow-direct.svg`。

**至少 3 条相对 `.md` 链接：** `./31-esp32-drivers-audio.md`、`./33-network-protocol-stack.md`、`../v3-rtos/22-tasks-tcb-scheduler.md`。

**验证：** checks ch32、slop、`built 32 pages, 20 planned chapters missing`、mapping。

**提交：** `feat(ch32): rewrite Wi-Fi/BLE/ESP-NOW chapter (B3)`

---

### Task 8: ch33《网络与协议栈》

**Files:**
- Create: `docs/v4-platforms/33-network-protocol-stack.md`
- Modify: `book/data/mapping.tsv`（`docs/27-网络与协议栈.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 网络与协议栈`、`platforms: [f407, esp32]`。版本钉：lwIP 按 **stm32-mw-lwip @07680c81（2.2.1，ST fork）**。

**必须覆盖（锚点见研究 §2）：**

- 五条网络路径边界表与决策顺序；「CubeMX 能勾选」不是上内置 Ethernet 的理由。
- RMII 六组信号核对与「link LED 只是线索」：MDIO 读不到 PHY 就停在硬件层；PHY 地址/strap/磁性件逐板核对。
- DMA 看见的内存 ≠ CPU 看见的内存：H7 DTCM 禁区（AN4891 口径）与 F407 CCM 禁区（回链 ch14/v1 ch25；**禁把 DTCM 写进 F407 半场**）。
- Cache 所有权交接：TX clean、RX invalidate，32 B 行对齐独占；禁对未对齐窄区间直接 invalidate；**禁把两者写成同一个「刷新」**。
- lwIP 三套 API 调用上下文与 IRQ 禁令；`LWIP_ASSERT_CORE_LOCKED()` 保留；lwIP 行号钉 `stm32-mw-lwip@07680c81`。
- pbuf 所有权：链结构、`tot_len` 不变式（`pbuf.h:198`）、free 恰好一次；zero-copy RX 的 DMA 覆写窗口。
- TCP 字节流自定帧（0x534E 帧头）+ 单截止点 `send_all_until`；`LWIP_SOCKET_SELECT=1`/`LWIP_SO_SNDTIMEO=0` 默认值随写随核（`opt.h:2168,2086`）。
- RAM_net 七项账与四本账（goodput/丢包率/恢复时间），峰值不报平均值。
- ESP32 半场：esp_netif→lwIP 适配、GOT_IP 才能 socket、WiFi 卸载后状态机仍在；从 ch32 接手，不重教 esp_event。

**禁抄：** 「lwIP 版本按仓库为准」不给版本；把 `07680c81` 写成 lwip-tcpip/lwip 的 commit（ST fork 的）；「lwIP Common pitfalls」当行级出处（wiki 在 fandom，raw 404）；把 `labs/ethernet-24h` 的 localhost smoke 当真板记录；重教 WiFi 事件循环（ch32）与 RTOS 堆策略（ch25）。

**图片引用（至少 5 张）：** `/images/ch27-pbuf-chain.png`（手绘）、`/anim/network-packet-journey.svg`、`/images/ch27-tcp-framing.png`（手绘）、`/figures/sample-27-tcp-framing.svg`、`/images/ch27-api-context.png`（手绘）、`/figures/tcp-byte-stream.svg`、`/images/ch27-four-ledgers.png`（手绘）。

**至少 3 条相对 `.md` 链接：** `../v1-drivers/14-dma.md`、`./32-esp32-wifi-ble-espnow.md`、`../v3-rtos/25-memory-management.md`。

**验证：** checks ch33、slop、`built 33 pages, 19 planned chapters missing`、mapping。

**提交：** `feat(ch33): rewrite network/protocol-stack chapter (B3)`

---

### Task 9: ch34《多核、Cache 与内存一致性》

**Files:**
- Create: `docs/v4-platforms/34-multicore-cache.md`
- Modify: `book/data/mapping.tsv`（`docs/25-STM32H7引脚.md`→ch28;ch34、`mcu/docs/esp32/04-irq-dualcore.md`→ch10;ch34 → `migrated`，两行在 ch28 已 migrated 后翻转）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 多核、Cache 与内存一致性`、`platforms: [esp32, f407]`。

**必须覆盖（锚点见研究 §3）：**

- 第一性差异开场：F1/F4 无 cache、H7 有 16+16 KB L1（32 B 行）、S3 靠 cache 映射窗口执行外部 Flash——三平台内存模型三种。
- Cache/DMA 所有权交接表（TX clean/RX invalidate）与 32 B 对齐纪律；未对齐窄区间 invalidate 的危险操作。
- 内存可达性矩阵：H7 DTCM（仅 CPU/MDMA）→ 描述符/缓冲放 AXI/D2 SRAM；F407 CCM；每条禁区配「链接 map 核对」动作。
- D1/D2/D3 归属表：CM7@D1、CM4@D2、D3 低功耗；「D1 有 Cache」改写为「cache 在 CM7 核内、CM7 在 D1」。
- MPU 两条解法（Non-Cacheable 区 vs 显式维护）+ M7 16 区上限 + CMSIS 维护函数；仓库无实例，写法属设计口径。
- H745 AMP 五层契约（从 ch27 旁注展开）：共享存储/所有权可见性/HSEM 同步/消息协议/启动恢复各冻结什么；HSEM 只管「谁先来」不管「货到没到」；D28:336 自认非实测，故障注入列是验收要求。
- AMP/SMP 语义分界：S3=SMP 单实例（回链 ch10），H745=AMP（本章展开）；「有两颗核」推不出「一个内核管两个核」。
- ESP32 半场：关 Cache 窗口的内存模型读法 + S3 writeback 支持位（`soc_caps.h:140`，**禁写「S3 是 write-through」**，默认模式标 TRM 待核）+ esp_cache C2M/M2C 与 STM32 clean/invalidate 方向对照。
- 一致性证据位：链接 map、MPU 配置、维护调用点、跨核序号回读进评审记录。

**禁抄：** 「D1 有 Cache」当域属性；F407 CCM 与 H7 DTCM 混写（地址/原因/手册都不同）；把 H7 时钟/VOS/480MHz 内容带进本章（归 ch28）；重教 NVIC/`esp_intr_alloc`/`portMUX`/`volatile` 边界；把 E4 的 IDF 行号用到其他版本。

**图片引用（至少 5 张）：** `/images/ch27-cache-dma.png`（手绘）、`/figures/sample-25-dcache-dma.svg`、`/images/ch25-power-domains.png`（手绘）、`/figures/network-cache-ownership.svg`、`/figures/esp32-04-int-alloc.svg`。

**至少 3 条相对 `.md` 链接：** `../v1-drivers/10-interrupts-nvic-exti.md`、`./28-chip-migration-differences.md`、`../v3-rtos/27-rtos-comparison-selection.md`、`../v1-drivers/14-dma.md`。

**验证：** checks ch34、slop、`built 34 pages, 18 planned chapters missing`、mapping。

**提交：** `feat(ch34): rewrite multicore/cache/coherence chapter (B3)`

---

### Task 10: ch35《现场总线与 USB》

**Files:**
- Create: `docs/v4-platforms/35-can-usb-fieldbus.md`
- Modify: `book/data/mapping.tsv`（`docs/13-CAN总线.md`、`docs/14-USB.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 现场总线与 USB`、`platforms: [f103, f407]`。

**必须覆盖（锚点见研究 §4）：**

- CAN 位时间三段式与采样点公式；同一波特率先验算预分频是否整数（450k/7.2 反例完整推理链）。
- 两平台两套位时序表：F103@36 MHz 五档表 + **F407@42 MHz 新表（500k=P6×14 或 P7×12，本章新增并复算）**；「分母不同，数字不能互抄」。
- 过滤器组数按平台：F103 14 组、**F407 28 组（修正 D13:257）**；掩码/列表、32/16 位、FIFO 分配；标准 ID 左移 5 位。RM 章节号按现版：RM0008 §24 bxCAN、USB §23（禁抄「第 21 章」）。
- TEC 阶梯与恢复：128 进被动且不再涨、>255 才 Bus-Off、128×11 隐性位、ABOM 与手动重启两条路。
- 回环→双节点的证明边界：回环不证明收发器/终端/差分总线；120 Ω 两端各一只、60 Ω 不是特性阻抗。
- USB 48 MHz 两平台来源：F1 `USBPRE=0`（72/1.5）、F4 PLLQ（336/7）；48 MHz 不准就是「未知设备」。
- 描述符树与 18+67 字节账（67 是配置集合 `wTotalLength` 不是本体）；VID/PID：本仓库 `0x1209/0x0001` 是占位，`0x0483/0x5740` 是 ST 例程对，禁写成本仓库量产号；PMA 512 B/EP0-7/BTABLE。
- 枚举 7 步与卡点分诊表；CDC/HID 选型一句话收尾；1023 是全速等时上限，不是批量/中断上限。
- PA11/PA12 资源冲突（F103 CAN/USB 同脚+同向量）与重映射出口；F411 无 CAN 的对照；CAN/USB 同工程编译冲突。
- FDCAN 划界：H7 的 FDCAN 是另一外设，归 ch28/H7 场，本章不写。

**图片引用（至少 6 张）：** `/images/ch13-can-bit.png`（手绘）、`/figures/sample-13-can-bit.svg`、`/anim/can-arbitration.svg`、`/figures/sample-13-bit-quanta.svg`、`/images/ch13-bit-quanta.png`（手绘）、`/images/ch13-filter-fifo.png`（手绘）、`/figures/sample-13-filter-fifo.svg`、`/images/ch14-usb-enum.png`（手绘）、`/figures/sample-14-usb-enum.svg`、`/anim/usb-enumeration.svg`、`/figures/sample-14-usbpre-48.svg`、`/images/ch14-usb-can-conflict.png`（手绘）。

**至少 3 条相对 `.md` 链接：** `../v1-drivers/13-uart-framed-protocol.md`、`../v1-drivers/08-architecture-memory-clock.md`、`./28-chip-migration-differences.md`。

**验证：** checks ch35、slop、`built 35 pages, 17 planned chapters missing`、mapping。

**提交：** `feat(ch35): rewrite CAN/USB fieldbus chapter (B3)`

---

### Task 11: ch36《电机驱动与供电》

**Files:**
- Create: `docs/v5-motion/36-motor-driver-power.md`
- Modify: `book/data/mapping.tsv`（`plans/2026-11-11-motor-control/chapters-draft/29-电机驱动与供电.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 电机驱动与供电`、`platforms: [f103]`。版本钉：hardware-freeze v1.2 + TB6612FNG datasheet（Pololu 0J86 镜像）。

**必须覆盖（锚点见研究 §2）：**

- 控制信号与动力电流分层（毫安 vs 安培，两个数量级）；「上电/复位/下载三时刻驱动必须关闭」的证明责任与三步检查法。
- TB6612 官方真值表 **7 行全保留**（含 IN1=IN2=H 短接制动行），五种输出态逐一给电流路径；禁用五行压缩表。
- 待机是默认态的硬件依据：STBY 内部 200 kΩ 下拉 + 复位期 GPIO 高阻；补待机电流 ≤1 µA（datasheet）。
- 「PWM=L ≠ 滑行」：方向有效时 PWM=L 是短接制动；滑行必须 IN1=IN2=L 且 PWM=H；三种停止语义的耗能路径区分。
- 双电源轨与共地：Vcc 2.7–5.5 V、**VM 2.5–13.5 V（4.5 V 是 1.0 A 电流边界不是电压下限，修正三口径冲突）**、工程冻结 6–12 V，三层分开写。
- 电流三档：连续 ≤1.0 A（唯一可进连续预算）/ 绝对最大 1.2 A / 3.2 A 单脉冲；补 2 A 连续脉冲档（tw 配对，M29 表漏列的完整性缺口）；堵转 ≤0.8 A 目标的 20% 余量算法。
- 输入门限 VIH≥0.7×Vcc（3.3 V→2.31 V）、VIL≤0.3×Vcc；3.3 V 逻辑直驱合规依据。
- 启动/堵转机理与对策三件：限流电源、VM 近端 0.1 µF+10 µF、软起动爬坡。
- 再生与回流：续流二极管 VF≤1.1 V、母线抬升；M29-C 观察项保持「待执行」。
- PD 拆开写：0.78 W IC only / 0.89–1.36 W 板上（HF 拆分口径）。
- GPIO「几十毫安」与启动电流「几倍」是未复核说法，引用前核 DS5319/电机规格页。

**图片引用（至少 4 张，全部手绘，从 motor 分支取件）：** `/images/ch29-five-states.png`、`/images/ch29-two-supplies.png`、`/images/ch29-current-tiers.png`、`/images/ch29-fault-triage.png`。

**至少 2 条相对 `.md` 链接：** `../v1-drivers/09-gpio.md`、`../v1-drivers/12-timers-pwm.md`、`./37-dc-motor-openloop.md`。

**验证：** checks ch36、slop、`built 36 pages, 16 planned chapters missing`、mapping。

**提交：** `feat(ch36): migrate motor drive/power chapter (B3)`

---

### Task 12: ch37《直流电机开环调速》+ 数值断言测试加入

**Files:**
- Create: `docs/v5-motion/37-dc-motor-openloop.md`
- Create: `book/tests/test_motor_numbers.py`（沿研究 §6.3 方案 (b)：`from book import manifest as mf`，行索引 `{r["id"]: r for r in mf.load_toc()}`——**注意 `load_toc()` 返回 `list[dict]` 不是 dict**，研究文档此处笔误，以本计划为准；附带断言 `rows["ch37"]["file"] == "v5-motion/37-dc-motor-openloop.md"`）
- Modify: `book/data/mapping.tsv`（`chapters-draft/30-直流电机开环调速.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 直流电机开环调速`、`platforms: [f103]`。

**必须覆盖（锚点见研究 §3）：**

- 占空比与转速四层区分：平均电压、电机参数、负载、静摩擦门槛。
- 可复算 PWM 表（72 MHz/PSC 0/ARR 3599/20 kHz）与换时钟树的三条重算理由；与 v1 ch12 的 20 kHz 表行对账（同一组数）。
- 端点语义：CCR=0、**CCR=ARR 差一格（3599/3600≈99.97%）**、满压写 CCR=3600；0% 端点与「撤销驱动」语义对应。
- 带符号占空比表示法与单点映射（`motor_bridge.c`）；方向幅值分离防两类漂移 bug。
- 输出限幅 900‰ 与积分限幅 500‰ 分离；`params_valid` 拒 ≥1000 的校验点。
- 斜坡 ±50‰/10 ms 与受控起动；命令一到就跳变为何不可接受。
- 500 ms 租约（F01）与「断串口必停机」安全论证；STOP 豁免会话检查的例外设计。
- REVERSING 合同四阶段与 3 s 超时；「直翻换向=回流尖峰来源」与 ch36 回流段呼应。
- 协议 v1 带宽账三步复算：43 B/帧 × 100 Hz × 8N1(10 bit) = 4300 B/s → **43 kbit/s ≈ 115200 的 37.3%（不是 4%）**；「扩遥测先算总线」纪律。
- 控制时基纪律（TIM4 硬件心跳 vs 软件延时）与上 RTOS 的所有权边界（回链 ch22/24，不重教）。

**测试断言（沿研究 §6，先加）：** 算术断言原样搬（`arr=72_000_000//20_000-1==3599`、`counts=3600`、`43000 bit/s`、`37.3%±0.05`、`4300 B/s`）；文案锚点随 ch37 落位文案改写，**负向哨兵必须保留或等价改写**（`3600=ARR`、`CCR≥ARR`、`100%（CCR=ARR）`、`带宽的 4%`）。旧测试 `stm32-book/tests/test_motor_draft_numbers.py` 本任务不删（Task 15 收口）。

**图片引用（至少 4 张，全部手绘）：** `/images/ch30-signed-duty.png`、`/images/ch30-pwm-math.png`、`/images/ch30-stop-triage.png`、`/images/ch30-no-spin-triage.png`。

**至少 2 条相对 `.md` 链接：** `./36-motor-driver-power.md`、`../v1-drivers/12-timers-pwm.md`、`./38-encoder-speed-measurement.md`。

**验证：** checks ch37、slop、`built 37 pages, 15 planned chapters missing`、mapping、`python -m unittest discover book/tests`（31 tests OK）。

**提交：** `feat(ch37): migrate dc-motor open-loop chapter with numeric test (B3)`

---

### Task 13: ch38《编码器与转速测量》

**Files:**
- Create: `docs/v5-motion/38-encoder-speed-measurement.md`
- Modify: `book/data/mapping.tsv`（`chapters-draft/31-编码器与转速测量.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 编码器与转速测量`、`platforms: [f103]`。

**必须覆盖（锚点见研究 §4；草稿与必写清单以研究文档为准）：**

- 正交编码器四倍频计数与 TIM 编码器模式（SMS=3）；A/B 相位与计数方向。
- CPR 440 示例的口径：**必须带减速比 G 说明（研究 §7 的口径矛盾修正）**——「110×4」与「440×G」两条口径择一并写清出处。
- 转速公式与量化：60/(440×0.01)≈13.636 rpm/计数的分辨率账。
- 计数回绕：65530→100 = +106 的有符号差值算法（16 位计数器回绕）。
- 10 ms 采样窗与「600 rpm 窗内 44 计数」——**修正草稿 4400 的 100 倍错误（zh/en 同错）**。
- 速度平滑与量化噪声：滑动平均的相位代价一句带过。
- 测量误差链：非整数分频、采样抖动、机械容差。
- 证据口径：全部「待执行（实物未到）」保留。

**图片引用（至少 3 张，全部手绘）：** `/images/ch31-quadrature.png`、`/images/ch31-rpm-formula.png`、`/images/ch31-wrap-triage.png`。

**至少 2 条相对 `.md` 链接：** `./37-dc-motor-openloop.md`、`../v1-drivers/11-systick-timebase-rtc.md`、`./39-speed-closed-loop-pi.md`。

**验证：** checks ch38、slop、`built 38 pages, 14 planned chapters missing`、mapping。

**提交：** `feat(ch38): migrate encoder/rpm-measurement chapter (B3)`

---

### Task 14: ch39《速度闭环与 PI》

**Files:**
- Create: `docs/v5-motion/39-speed-closed-loop-pi.md`
- Modify: `book/data/mapping.tsv`（`chapters-draft/32-直流电机速度闭环.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**frontmatter:** `title: 速度闭环与 PI`、`platforms: [f103]`。

**必须覆盖（锚点见研究 §5）：**

- PI 结构与离散化：误差→比例项→积分累加→输出；10 ms 控制周期与 TIM4 心跳对齐。
- 冻结参数：Kp 2.0 / Ki 0.5 / 输出限幅 900‰ / 积分限幅 500‰（HF v1.2），参数身份是「冻结配置值」不是「调优结论」。
- PI 手算例：误差 −20.05 的复算路径（研究 §5 数值表）。
- 限幅对齐：900‰→CCR 3240 < 3599 的映射算术。
- 积分抗饱和（限幅 500‰ 的双重角色）；回绕计数进 PI 前的有符号化。
- 状态机五态（含 REVERSING 四阶段合同与 3 s 超时）与 `ch32-state-machine` 板转述。
- 调参阶梯（`ch32-tuning-ladder`）：先 P 后 I，每步只动一个参数。
- 闭环故障分诊（`ch32-loop-fault-triage`）：不转、单向、抖动、超限各自的 first-check。
- 证据口径：全部「待执行（实物未到）」；协议 v1 遥测字段不扩（扩遥测先算总线，回链 ch37）。

**图片引用（至少 4 张，全部手绘）：** `/images/ch32-pi-step.png`、`/images/ch32-state-machine.png`、`/images/ch32-tuning-ladder.png`、`/images/ch32-loop-fault-triage.png`。

**至少 2 条相对 `.md` 链接：** `./38-encoder-speed-measurement.md`、`./37-dc-motor-openloop.md`、`../v3-rtos/22-tasks-tcb-scheduler.md`。

**验证：** checks ch39、slop、`built 39 pages, 13 planned chapters missing`、mapping。

**提交：** `feat(ch39): migrate speed closed-loop/PI chapter (B3)`

---

### Task 15: motor 数值断言测试迁移收口

**Files:**
- Delete: `stm32-book/tests/test_motor_draft_numbers.py`（设计规格 §5 明文迁移；Global Constraints 的唯一旧树改动例外）
- Modify: `plans/2026-11-11-motor-control/implement.md` 不动（旧树）；登记行写入 `plans/2026-11-12-merged-book/README.md`

**Interfaces:**
- Consumes: Task 12 已加入的 `book/tests/test_motor_numbers.py`（先加后删时序的「删」半）
- Produces: 数值断言守卫对象换到新书章节；B3 出口条件「motor 数值断言测试迁移通过」达成

- [ ] **Step 1: 确认新测试绿**

Run: `python -m unittest discover book/tests -v`（31 tests，含 2 条 motor 数值断言）

- [ ] **Step 2: 删旧测试并跑旧书套件**

Run: `git rm stm32-book/tests/test_motor_draft_numbers.py`；`python -m unittest discover stm32-book/tests` 确认删除后旧套件自身仍绿（测试计数 −2，在批次记录里声明）。

- [ ] **Step 3: 提交**

```bash
git rm stm32-book/tests/test_motor_draft_numbers.py
git commit -m "test(motor): retire draft-path numeric test, guard moved to book/tests (B3)"
```

---

### Task 16: B1/B2 前向引用清扫（ch28–ch39 方向）

**Files:**
- Modify: 13 个 B1 章节文件（实测清单见下），删除 `[ch28]/[ch29]/[ch30]/[ch31]/[ch34]/[ch35]/[ch38]` 定义并把引用改 inline：

```text
docs/v0-foundations/03-struct-abi-registers.md     [ch28][ch29]
docs/v0-foundations/04-function-pointer-state-machine.md  [ch28][ch29]
docs/v0-foundations/07-build-systems-legacy.md     [ch28][ch29][ch30]
docs/v1-drivers/08-architecture-memory-clock.md    [ch28][ch29][ch30]
docs/v1-drivers/09-gpio.md                         [ch28][ch29][ch30][ch31]
docs/v1-drivers/10-interrupts-nvic-exti.md         [ch28][ch29][ch30][ch31][ch34]
docs/v1-drivers/11-systick-timebase-rtc.md         [ch29][ch30]
docs/v1-drivers/12-timers-pwm.md                   [ch30][ch31][ch34][ch38]
docs/v1-drivers/13-uart-framed-protocol.md         [ch29][ch30][ch31][ch35]
docs/v1-drivers/14-dma.md                          [ch29][ch31][ch34]
docs/v1-drivers/15-adc-dac-sampling.md             [ch29][ch31]
docs/v1-drivers/16-i2c-spi.md                      [ch31]
docs/v1-drivers/17-flash-iap-ota.md                [ch31]
```

（36 条定义；引用点以 `grep -rno "\]\[ch2[89]\]\|\]\[ch3[0-9]\]"` 实测为准。替换映射：ch28→`../v4-platforms/28-chip-migration-differences.md`、ch29→29-gd32-arm-riscv.md、ch30→30-esp32s3-architecture-boot.md、ch31→31-esp32-drivers-audio.md、ch34→34-multicore-cache.md、ch35→35-can-usb-fieldbus.md、ch38→`../v5-motion/38-encoder-speed-measurement.md`。其余残留 id（ch32/33/36/37/39 无定义；ch40 等归 B4）一律不动。）

- 同批补交叉链接：ch25 补 `./26` 类似的正式前链不存在；本任务只把 v4/v5 已存在章的正式前链补进 B1/B2 正文引用点（Task 3–14 各章已写回链，此任务只清引用式写法）。

- [ ] **Step 1: 改写为 inline 并删定义行（脚本化，同 Task 12 of B2 的做法；先 `--dry-run` 打印替换数）**
- [ ] **Step 2: 验证**

Run: `grep -rn "\]\[ch2[89]\]\|\]\[ch3[0-9]\]" docs/v0-foundations docs/v1-drivers` → exit 1。

Run: `python -m book.checks --check`；`python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md docs/v4-platforms/*.md docs/v5-motion/*.md`。

- [ ] **Step 3: 提交**

```bash
git add docs/v0-foundations docs/v1-drivers
git commit -m "docs(links): inline B1/B2 forward references to volumes 4-5 (B3)"
```

---

### Task 17: CI 接入、批次记录与 B3 证据

**Files:**
- Modify: `.github/workflows/merge-check.yml`（slop 行扩到六个 glob）
- Modify: `plans/2026-11-12-merged-book/README.md`（B3 行改「本批完成（本地）」；校验命令 slop 行同步；数据文件补 B3 迁移摘要）
- Create: `plans/2026-11-12-merged-book/evidence/b3-local.md`（格式对齐 b1-local/b2-local：分支、HEAD、Python/Node 版本、七条命令真实输出与退出码、12 章文件名、13 组测验 id 不变（B3 无新 quiz）、`built 39 pages, 13 planned chapters missing`、mapping 迁移摘要、motor 测试迁移记录、未验证声明）

**Step 1 slop glob：**

```yaml
          python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md docs/v4-platforms/*.md docs/v5-motion/*.md
```

**Step 3 全量本地验收命令（与 B2 同表）：**

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
python -m book.checks --check
python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md docs/v4-platforms/*.md docs/v5-motion/*.md
python -m book.build_html --check
node --test scripts/tests/legacy-redirects.test.mjs
```

**提交：** `chore(ci): enable B3 chapter gates and record local evidence (B3)`

---

## Self-Review 记录

- **Spec 覆盖**：B3 出口「卷 4–5 共 12 章 + motor 合流」→ Task 3–14；「motor 数值断言测试迁移通过」→ Task 12（加）+ Task 15（删）双段时序；「映射状态同步」→ 各章 Step 与 Task 9/11 的双目标行规则；「资产」→ Task 1（145 文件 + motor 分支 15 板取件）+ Task 2（4 块新板，补齐 ch29–32 手绘覆盖）；「链接清扫」→ Task 16（36 定义/13 文件实测清单）；「CI/证据」→ Task 17。
- **Placeholder 扫描**：每章必写清单来自研究文档实锚（repo@ref 只写真实取到的）；ch38 必写清单标注「以研究文档为准」——研究 §4 已含完整锚点表，写作时照抄其行号修正。
- **类型一致性**：quiz 全批不挂（沿用 B2 ch26/27 先例，不新造 id）；章节路径与 `book/data/toc.tsv:30-41` 一致；build_html 计数按 27→39 单调推进；mapping 双目标行（docs/25、esp32/04、e08）状态机规则显式。
- **已知边界**：`e08` 保持 partial 到 B4 ch40；esp32/04 的双核半已属 ch10，本批只翻转 Cache 半；VitePress/Pages 切换归 B5；本批不含远程推送/PR/发布（需另行授权）；motor 分支本体不合入（只按文件取件手绘板与后续正文参考）。
- **研究文档勘误**：`b3-motor-sources.md` §6.2 的 `mf.load_toc()["ch37"]["file"]` 写法不可用（`load_toc()` 返回 `list[dict]`），Task 12 已按 `{r["id"]: r for r in mf.load_toc()}` 修正；其余以研究文档为准。
