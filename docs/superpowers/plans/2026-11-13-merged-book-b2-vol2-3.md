# 双书合并 B2（卷 2–3：可靠性与 RTOS）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把卷 2《可靠性与故障》（ch18–ch20）与卷 3《RTOS》（ch21–ch27）共 10 章从旧源改写为合并书新稿，资产与测验落位，映射状态同步，本地与 CI 门禁可校验。

**Architecture:** 沿用 B1 的质量门（`book/checks.py` 章节契约/链接锚点/资产/测验、`book/build_html.py --check` 临时站、`book/mapping.py` 状态机）。10 章正文只写进 `docs/v2-reliability/` 与 `docs/v3-rtos/`；资产从 `mcu/docs/public/`（原路径）与仓库根 `assets/`（改名入 `/figures`、`/images`）复制进 `docs/public/`；3 组测验复制进 `docs/.vitepress/data/quizzes/`（`s14-pwr` 带勘误）；`book/data/mapping.tsv` 逐行推进状态。旧书与旧站零改动。

**Tech Stack:** Python 3.13 + `markdown==3.11`（既有）、Node.js 20（沿用既有 `node:test`）、GitHub Actions。本批不新增任何依赖。

**Spec:** [docs/superpowers/specs/2026-11-12-merged-book-design.md](../specs/2026-11-12-merged-book-design.md)

## Global Constraints

- 仅中文书稿；不处理英文版（B5 归档）。
- 旧树零改动：`docs/00-28*.md`、`docs/en/**`、`stm32-book/**`、`mcu/**`、`scripts/legacy-redirects.mjs` 一律不改；本批新增 `docs/v2-reliability/`、`docs/v3-rtos/`，并只改 `docs/public/`、`docs/.vitepress/data/quizzes/`、`book/data/mapping.tsv`、`plans/2026-11-12-merged-book/`（`mapping.json`、`README.md`、`evidence/b2-local.md`）、`.github/workflows/merge-check.yml`。B1 章节 `docs/v0-foundations/*.md`、`docs/v1-drivers/*.md` 仅允许在 Task 12 做引用式链接内联清扫，不做其它改动。
- 依赖不变：不新增、不升级任何依赖，不改任何 lock 文件，不新增 Node 依赖（`markdown==3.11` 已在 `book/requirements.txt`）。
- 站点临时构建 = `python -m book.build_html --check`；生产 VitePress 站点配置与 `/STM32/` base 切换仍属 B5，本批不建 `docs/.vitepress/config.*`。
- 章节文件名、标题、平台来自 `book/data/toc.tsv`，不许改 toc 迁就正文。
- 章节结构固定：frontmatter（`title`、`platforms`）→ `# 标题` → `## 本章罗盘`（**问题** / **交付** / **边界** / **依据锚点**）→ `## 先做出来` → `## 机制` → `## 测量与证据` → `## 失败分支` → `## 离开检查`；多平台章可在「失败分支」后加 `## 跨平台边界`。
- 折叠块用原生 `<details><summary>…</summary>`；测验用 `<QuizBank chapter="..." />`；不使用 `:::` 容器。
- 图片引用根绝对路径（如 `/figures/x.svg`，对应 `docs/public/`）或同目录相对路径；`alt` 必填；禁止外链图片；禁止 `../assets/...`（在 `docs/v2-reliability/` 下会被解析成 `docs/assets/` 而失败）。
- 章间链接一律**内联**相对 `.md` 路径（可带 `#锚点`）；禁止根绝对页面链接；禁止新增引用式链接定义（`[chNN]: ...`）。
- 证据标签固定四类（沿用已发布 ch11 的「读数来路表」）：**实测记录**（可复跑读数或断言输出，含宿主 probe）、**来源说法(未复核)**、**文档推导**、**未实测**。任何「待实测」必须显式留在正文，不得改写成结论；不得编造故障经历、读数或实验结果。
- 全书记忆口径红线（来源文件与此冲突时按红线改写，并在正文标注「来源说法有误，已按 RM/DS 更正」）：HSI F103 8 MHz / F407 16 MHz；LSI F103 40 kHz（30/60）/ F407 32 kHz（17/47）；IWDG 超时公式统一含 `(RLR+1)`；RTC 唤醒定时器在 F407 是 EXTI22（EXTI18 是 USB OTG FS 唤醒）；VOS 编码 `0b11`=168 MHz、`0b10`=144、`0b01`=120；备份寄存器 F103 10×16 bit / F407 20×32 bit。
- mapping 状态机：`planned`（无目标章文件）→ `partial`（部分目标章已写）→ `migrated`（全部目标章已写）；与章节文件存在性不一致即失败。多目标行 `docs/11-RTC与看门狗.md`→ch11;ch19、`docs/15-FreeRTOS入门.md`→ch21;ch22 在全部目标存在后才能置 `migrated`；`mcu/docs/lab/e04-priority-inversion.md`→ch24;ch40 与 `mcu/docs/lab/e06-lowpower-current.md`→ch18;ch40 在本批结束保持 `partial`（ch40 属 B4）。
- 所有提交按显式路径暂存，禁止 `git add -A` / `git add .`。
- 远程推送、PR 合入与 Pages 切换需另行授权；本计划只做本地提交。

---

### Task 1: B2 共享资产迁移（52 个文件）

**Files:**
- Create: `docs/public/anim/*.svg`、`docs/public/arch/*.png`、`docs/public/figures/*.svg`、`docs/public/images/**`

**Interfaces:**
- Consumes: 现有 `docs/public/`（B1 后共 92 个文件）
- Produces: 卷 2–3 章节可引用的 52 个根绝对路径资产；`book.checks` 的 `missing asset` 检查以此为准；`docs/public` 文件总数变为 144。

- [ ] **Step 1: 复制资产（来源一：`mcu/docs/public/`，保持原相对路径）**

Run:

```bash
python - <<'EOF'
from pathlib import Path
import shutil

MCU_ASSETS = """
/anim/stm32-pwr-three-modes.svg
/arch/pwr-domains.png
/figures/stm32-14-pwr.svg
/anim/esp32-sleep-matrix.svg
/images/tools/multimeter-dt830d.jpg
/images/labs/e06-current-meter.svg
/figures/stm32-16-cfsr-bits.svg
/anim/hardfault-forensics.svg
/anim/watchdog-window.svg
/figures/stm32-17-watchdog-reset.svg
/anim/esp32-twdt-chain.svg
/figures/esp32-13-four-wdt.svg
/anim/swd-debug-chain.svg
/anim/why-rtos.svg
/anim/task-create-stack.svg
/anim/list-insert.svg
/arch/scheduler-structs.png
/figures/rtos-03-scheduler.svg
/anim/context-switch.svg
/arch/context-switch.png
/figures/rtos-02-fake-frame.svg
/anim/freertos-port.svg
/anim/queue-passing.svg
/anim/semaphore-mutex.svg
/anim/priority-inversion.svg
/figures/rtos-04-queue.svg
/figures/rtos-freertos-05-sem-mutex.svg
/images/labs/e04-timeline.svg
/anim/heap4-coalesce.svg
/arch/heap-free-list.png
/figures/rtos-freertos-07-heap.svg
/anim/rtt-mem-alloc.svg
/anim/rtt-device-chain.svg
/arch/device-ops.png
/anim/rtt-finsh-dispatch.svg
/anim/menuconfig-flow.svg
/anim/dual-os-compare.svg
/anim/rtos-decision-tree.svg
/arch/rtos-side-by-side.png
""".split()

src_root = Path("mcu/docs/public")
dst_root = Path("docs/public")
for asset in MCU_ASSETS:
    relative = asset.lstrip("/")
    target = dst_root / relative
    if target.exists():
        raise SystemExit(f"refusing to overwrite: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_root / relative, target)
print(len(MCU_ASSETS), "mcu assets copied")
EOF
```

Expected: `39 mcu assets copied`

- [ ] **Step 2: 复制资产（来源二：仓库根 `assets/`，改名入 `/figures`、`/images`）**

Run:

```bash
python - <<'EOF'
from pathlib import Path
import shutil

ROOT_ASSETS = [
    ("assets/diagrams/sample-16-stop-wake.svg", "docs/public/figures/sample-16-stop-wake.svg"),
    ("assets/diagrams/lowpower-current-evidence.svg", "docs/public/figures/lowpower-current-evidence.svg"),
    ("assets/diagrams/watchdog-reset-evidence.svg", "docs/public/figures/watchdog-reset-evidence.svg"),
    ("assets/diagrams/fault-triage-ladder.svg", "docs/public/figures/fault-triage-ladder.svg"),
    ("assets/diagrams/sample-15-task-states.svg", "docs/public/figures/sample-15-task-states.svg"),
    ("assets/diagrams/sample-28-os-compare.svg", "docs/public/figures/sample-28-os-compare.svg"),
    ("assets/illustrations/handraw/ch16-acceptance-record.png", "docs/public/images/ch16-acceptance-record.png"),
    ("assets/illustrations/handraw/ch17-dwt-window.png", "docs/public/images/ch17-dwt-window.png"),
    ("assets/illustrations/handraw/ch17-stack-frame.png", "docs/public/images/ch17-stack-frame.png"),
    ("assets/illustrations/handraw/ch15-two-priority-rules.png", "docs/public/images/ch15-two-priority-rules.png"),
    ("assets/illustrations/handraw/ch15-stack-watermark.png", "docs/public/images/ch15-stack-watermark.png"),
    ("assets/illustrations/handraw/ch15-psp-msp.png", "docs/public/images/ch15-psp-msp.png"),
    ("assets/illustrations/handraw/ch28-os-compare.png", "docs/public/images/ch28-os-compare.png"),
]

for source, target in ROOT_ASSETS:
    destination = Path(target)
    if destination.exists():
        raise SystemExit(f"refusing to overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(source), destination)
print(len(ROOT_ASSETS), "root assets copied")
EOF
```

Expected: `13 root assets copied`

- [ ] **Step 3: 验证文件数与来源一致**

Run: `find docs/public -type f | wc -l`
Expected: `144`

校验 52 个新目标全部非空：

```bash
python - <<'EOF'
from pathlib import Path
targets = [line.strip().lstrip("/") for line in """
/anim/stm32-pwr-three-modes.svg
/arch/pwr-domains.png
/figures/stm32-14-pwr.svg
/anim/esp32-sleep-matrix.svg
/images/tools/multimeter-dt830d.jpg
/images/labs/e06-current-meter.svg
/figures/stm32-16-cfsr-bits.svg
/anim/hardfault-forensics.svg
/anim/watchdog-window.svg
/figures/stm32-17-watchdog-reset.svg
/anim/esp32-twdt-chain.svg
/figures/esp32-13-four-wdt.svg
/anim/swd-debug-chain.svg
/anim/why-rtos.svg
/anim/task-create-stack.svg
/anim/list-insert.svg
/arch/scheduler-structs.png
/figures/rtos-03-scheduler.svg
/anim/context-switch.svg
/arch/context-switch.png
/figures/rtos-02-fake-frame.svg
/anim/freertos-port.svg
/anim/queue-passing.svg
/anim/semaphore-mutex.svg
/anim/priority-inversion.svg
/figures/rtos-04-queue.svg
/figures/rtos-freertos-05-sem-mutex.svg
/images/labs/e04-timeline.svg
/anim/heap4-coalesce.svg
/arch/heap-free-list.png
/figures/rtos-freertos-07-heap.svg
/anim/rtt-mem-alloc.svg
/anim/rtt-device-chain.svg
/arch/device-ops.png
/anim/rtt-finsh-dispatch.svg
/anim/menuconfig-flow.svg
/anim/dual-os-compare.svg
/anim/rtos-decision-tree.svg
/arch/rtos-side-by-side.png
/figures/sample-16-stop-wake.svg
/figures/lowpower-current-evidence.svg
/figures/watchdog-reset-evidence.svg
/figures/fault-triage-ladder.svg
/figures/sample-15-task-states.svg
/figures/sample-28-os-compare.svg
/images/ch16-acceptance-record.png
/images/ch17-dwt-window.png
/images/ch17-stack-frame.png
/images/ch15-two-priority-rules.png
/images/ch15-stack-watermark.png
/images/ch15-psp-msp.png
/images/ch28-os-compare.png
""".splitlines() if line.strip()]
missing = [t for t in targets if not (Path("docs/public") / t).is_file() or (Path("docs/public") / t).stat().st_size == 0]
print("missing or empty:", missing)
EOF
```

Expected: `missing or empty: []`

- [ ] **Step 4: 暂存、复核并提交**

```bash
git add docs/public
git diff --cached --name-only docs/public | wc -l
git commit -m "feat(assets): migrate volume 2-3 shared assets into docs/public (B2)"
```

Expected: 暂存清单计数 `52`（全部为新增文件；`git status` 中不得出现改动既有资产）

---

### Task 2: 第 18 章 低功耗设计

**Files:**
- Create: `docs/v2-reliability/18-low-power.md`
- Create: `docs/.vitepress/data/quizzes/s14-pwr.json`（自 `mcu/docs/.vitepress/data/quizzes/s14-pwr.json` 复制并按下述 4 处勘误）
- Modify: `book/data/mapping.tsv`（4 行状态）、regenerate `plans/2026-11-12-merged-book/mapping.json`

**Sources（只读）:** `docs/16-低功耗设计.md`、`mcu/docs/stm32/14-pwr.md`、`mcu/docs/esp32/11-lowpower.md`、`mcu/docs/lab/e06-lowpower-current.md`

**Interfaces:**
- Consumes: Task 1 资产、`book.checks`、`book.build_html`
- Produces: manifest 中 `ch18` 页面；`docs/16`、`mcu/stm32/14-pwr`、`esp32/11` 状态 `migrated`；`mcu/lab/e06` 状态 `partial`

- [ ] **Step 1: 写章节 `docs/v2-reliability/18-low-power.md`**

frontmatter：

```yaml
---
title: "低功耗设计"
platforms: [f407, f103, esp32]
---
```

正文必须覆盖：

- 三档定档只由 `SCB->SCR.SLEEPDEEP`(bit2) 与 `PWR_CR.PDDS`(bit1) 决定；`LPDS/FPDS/VOS` 只是 Stop 下的省电选项。把 `docs/16` 的 PA0 下降沿实验（EXTI 配置）与 WKUP 引脚上升沿（`PWR_CSR.EWUP` 管）一句区分，不许并排成矛盾。
- F407 VOS 编码：`VOS[15:14]`，`0b11`=168 MHz、`0b10`=144、`0b01`=120；**禁止照抄** `14-pwr:232` 的「VOS=0 → 144」与 `14-pwr:33` 的 `CR=0x4200`（该值只置 bit14，等于 Scale3/120 MHz）；示例值必须体现 `[15:14]=0b11`。
- 唤醒映射：WKUP=EXTI0（由 `PWR_CSR.EWUP` 单独管，不进 `EXTI_IMR`）、PVD=16、RTC 闹钟=17、**RTC 唤醒定时器在 F407 上是 EXTI22**；`14-pwr:54,362` 与 `mcu/code/stm32/14-pwr/main.c:119` 的 line18 是错的（line18=USB OTG FS 唤醒），禁止照抄。
- Stop 退出时钟重建：PLL 被硬件清掉，HSI 起振（F103 8 MHz / F407 16 MHz）→ 重配 PLL → Flash latency → 外设重初始化；「醒来 PLL 自动恢复」是错误说法；F1/F4 两段恢复序列要点分列、不可互抄。
- 备份域：`PWR_CR.DBP`(bit8) 解锁 → `RCC_BDCR.BDRST` 复位 → 写 → 清 DBP；`PWR_CSR.BRE`(bit9)/`BRR`(bit3)；F103 10×16 bit BKP vs F407 20×32 bit + 4 KB BKPSRAM（`0x40024000`，AHB1ENR bit18 + DBP）。
- 电流口径：F103 Sleep 14.4/5.5 mA@72 MHz、Stop 14/24 µA、Standby 2/3.2/3.4 µA、VBAT 1.4 µA、唤醒 1.8–5.4 µs 且 PLL 锁定 ≤200 µs——统一标「DS5319 表 16/26 手册值（来源转引）」；F407 只写「百 µA 量级（待复核）」，**禁止出现 nA**（`e06:57`、`14-pwr:87` 与 DS 冲突）。
- 测量方法学：DT830D 200 µA 档底噪与压降、量程切换瞬态、平均 vs 峰值；万用表测不了 µs 级唤醒电流；e06 来源状态 `code_status: planned`/`hardware_status: pending`，所有读数标「待实测」。
- 续航算术：0.11 mA / 90 天不自洽——按同段模型（200 mA×2 s + 10 µA×3598 s）/3600 s ≈ 0.121 mA，220 mAh ÷ 0.121 mA ≈ 76 天；给出正反两算。
- ESP32：light/deep sleep 与 STM32 三档「最接近但不等价」；deep sleep 是复位、`esp_deep_sleep_start()` 不返回；跨睡眠只有 `RTC_DATA_ATTR/RTC_NOINIT_ATTR/RTC_SLOW_ATTR/RTC_FAST_ATTR` 四类；型号未定处（classic vs S3 的 RTC 内存量）标「按型号 TRM 待核」。
- 图片引用（至少 4 张）：`/anim/stm32-pwr-three-modes.svg`、`/figures/stm32-14-pwr.svg`、`/figures/sample-16-stop-wake.svg`、`/figures/lowpower-current-evidence.svg`；测量段可加 `/images/tools/multimeter-dt830d.jpg`、`/images/labs/e06-current-meter.svg`。
- 至少 2 条指向其它新章/已发布章的相对 `.md` 链接，例如 `./19-watchdog-reset-hardfault.md`、`../v1-drivers/11-systick-timebase-rtc.md`、`../v1-drivers/13-uart-framed-protocol.md`。
- 结尾放 `<QuizBank chapter="s14-pwr" />`（唯一引用者）。

- [ ] **Step 2: 复制测验并勘误 `docs/.vitepress/data/quizzes/s14-pwr.json`**

从 `mcu/docs/.vitepress/data/quizzes/s14-pwr.json` 复制，保持 `"chapter": "s14-pwr"`（必须与文件名一致）与 6 题结构，按下列 4 处勘误：

1. Q1 的 `a`：删去以 `CR=0x4200` 作为硅片依据的表述（该值只置 bit14 = VOS `0b01`/120 MHz）；保留「三档差别只有 SLEEPDEEP+PDDS」结论，并指出 VOS 必须 `0b11` 才能跑 168 MHz。
2. Q2 选项 C 与 `a`：把「差 5%」改为「约差 90%（10973 vs 115200），对端收到帧错」。
3. Q4 的 `a`：把「RTC 唤醒是线 18」改为「RTC 唤醒定时器在 F407 上是线 22；线 18 是 USB OTG FS 唤醒」。
4. Q5：按 `(RLR+1)` 重算——`256×(4095+1)/32000 = 32768 ms`；选项与答案改为「32768 ms；漏掉 `(RLR+1)` 会算成 32760 ms——正是旧表的坑」，并更新 ±5% 下界（约 31130 ms）。

- [ ] **Step 3: 更新映射状态**

`docs/16-低功耗设计.md`、`mcu/docs/stm32/14-pwr.md`、`mcu/docs/esp32/11-lowpower.md` → `migrated`；`mcu/docs/lab/e06-lowpower-current.md`（目标 `ch18;ch40`）→ `partial`。

Run: `python -m book.mapping --write`

- [ ] **Step 4: 验证**

Run: `python -m book.checks --chapter ch18`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v2-reliability/18-low-power.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 18 pages, 34 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 5: 提交**

```bash
git add docs/v2-reliability/18-low-power.md docs/.vitepress/data/quizzes/s14-pwr.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch18): rewrite low-power chapter with corrected EXTI/VOS/RLR findings (B2)"
```

---

### Task 3: 第 19 章 看门狗、复位与 HardFault

**Files:**
- Create: `docs/v2-reliability/19-watchdog-reset-hardfault.md`
- Modify: `book/data/mapping.tsv`（4 行状态）、regenerate `plans/2026-11-12-merged-book/mapping.json`

**Sources（只读）:** `docs/11-RTC与看门狗.md`（只取看门狗段：36–135、209–260、386–418；RTC 段 148–208、371–379 回链已发布 ch11）、`mcu/docs/stm32/16-debug-hardfault.md`、`mcu/docs/stm32/17-watchdog-reset.md`、`mcu/docs/esp32/13-watchdog-health.md`

**Interfaces:**
- Consumes: Task 1 资产、已发布 `docs/v1-drivers/11-systick-timebase-rtc.md`
- Produces: manifest 中 `ch19` 页面；`docs/11`、`mcu/stm32/16-debug-hardfault`、`mcu/stm32/17-watchdog-reset`、`mcu/esp32/13-watchdog-health` 状态 `migrated`

- [ ] **Step 1: 写章节 `docs/v2-reliability/19-watchdog-reset-hardfault.md`**

frontmatter：

```yaml
---
title: "看门狗、复位与 HardFault"
platforms: [f407, f103, esp32]
---
```

正文必须覆盖：

- 两只狗的时间基准不同：IWDG 由独立 LSI 驱动、只罚「太晚」；WWDG 由 PCLK1 驱动、早喂也复位。LSI 必须带容差：F103 40 kHz（30/60）、F407 32 kHz（17/47）；超时表给「设计值 / 最坏值」两列。
- IWDG 生命周期：`0xCCCC` 启动 → `0x5555` 解锁 → 写 PR/RLR → `0xAAAA` 喂狗；默认 /4；启动后软件关不掉。超时 `t = (4·2^PR)·(RLR+1)/f_LSI` **必须含 `(RLR+1)`**——`14-pwr:56,241` 的 511…32760 表与 s14-pwr 旧题是反例，禁止照抄；给 RLR=999 → 2.00 s（32 kHz）与 ±LSI 区间。
- WWDG 窗口契约：`0x3F < T < W`；58.25 ms 必带「PCLK1=36 MHz、/8、T=0x7F」，F407 例 131 ms 必带「16 MHz、/8」；脱离条件即错数。
- 复位源是位图：`RCC_CSR` bit31..25 + `RMVF` bit24，先一次读全再清；POR 会同时置 PINRSTF；内部复位也拉 NRST 脉冲（≥20 µs）——「看到 PINRSTF 就是按了复位键」不成立。
- 复位记录原子写：`.noinit` + magic `0x57444731` + 版本 + 有效掩码 + CRC-16，写序「先清有效位 → 写体 → 最后置有效位」；三种载体取舍（`.noinit` / BKP / `RTC_NOINIT_ATTR`）；Flash 参数区回链 ch17，不重讲擦写时序。
- HardFault 取证流水线：CFSR 19 位分区（MMFSR 6 + BFSR 7 + UFSR 6）、HFSR.FORCED(bit30)、MMARVALID(bit7)/BFARVALID(bit15)、栈帧 32 B 且 `PC = ((uint32_t*)sp)[6]`、`EXC_RETURN` bit2 选 MSP/PSP、裸函数入口 `tst lr,#4 / ite eq / mrseq r0,msp / mrsne r0,psp`（机器码 `f01e 0f04 / bf0c / f3ef 8008|8009`）、addr2line；IMPRECISERR 的 PC 不可靠、STKERR/MSTKERR 压栈可能不完整。异常机制回链 ch10。
- 调试器会改变故障现场：`DBGMCU` 冻结位（F1 惯用 bit8/9；F4 `DBGMCU_APB1_FZ` bit11/12）、OpenOCD 默认关狗——「调试下从不复位」是假阴性；回链 ch20。
- ESP32：四类狗（TWDT/IWDT/RTC_WDT/XTWDT）、TWDT 是任务级契约（不是写键值寄存器）、`esp_reset_reason()`、`RTC_NOINIT_ATTR`；HardFault 是 Cortex-M 概念，ESP32 只有 panic/backtrace，禁止平移。
- 证据分级：`17-watchdog` 与 `13-watchdog` 实验表体「待实测」；`16-debug` 274/274 是宿主 probe（含反汇编与 addr2line 全链），无板级现场——三类标签分开写。
- 图片引用（至少 4 张）：`/figures/stm32-17-watchdog-reset.svg`、`/anim/watchdog-window.svg`、`/anim/hardfault-forensics.svg`、`/figures/stm32-16-cfsr-bits.svg`；可加 `/figures/watchdog-reset-evidence.svg`、`/anim/esp32-twdt-chain.svg`。
- 至少 3 条相对 `.md` 链接：`./18-low-power.md`、`../v1-drivers/11-systick-timebase-rtc.md`、`../v1-drivers/10-interrupts-nvic-exti.md`、`../v1-drivers/17-flash-iap-ota.md`。

- [ ] **Step 2: 更新映射状态**

`docs/11-RTC与看门狗.md`（目标 `ch11;ch19`，ch11 已发布、ch19 本章创建）→ `migrated`；`mcu/docs/stm32/16-debug-hardfault.md`、`mcu/docs/stm32/17-watchdog-reset.md`、`mcu/docs/esp32/13-watchdog-health.md` → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch19`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v2-reliability/19-watchdog-reset-hardfault.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 19 pages, 33 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v2-reliability/19-watchdog-reset-hardfault.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch19): rewrite watchdog/reset/HardFault chapter (B2)"
```

---

### Task 4: 第 20 章 调试、性能与测量

**Files:**
- Create: `docs/v2-reliability/20-debug-performance.md`
- Modify: `book/data/mapping.tsv`（2 行状态）、regenerate `plans/2026-11-12-merged-book/mapping.json`

**Sources（只读）:** `docs/17-调试与性能优化.md`、`mcu/docs/build/06-flash-debug.md`

**Interfaces:**
- Consumes: Task 1 资产、`/images/tools/logic-analyzer-8ch.jpg` 与 `/images/tools/oscilloscope-ds1054z.jpg`（B1 已就位）、已发布 `docs/v0-foundations/05-toolchain-four-steps.md`
- Produces: manifest 中 `ch20` 页面；`docs/17`、`mcu/build/06-flash-debug` 状态 `migrated`

- [ ] **Step 1: 写章节 `docs/v2-reliability/20-debug-performance.md`**

frontmatter：

```yaml
---
title: "调试、性能与测量"
platforms: [f407, f103]
---
```

正文必须覆盖（与 ch19 的分工：ch19 讲 HardFault 寄存器取证，本章只讲工具链段——CFSR→VALID→栈帧 PC→`EXC_RETURN`→addr2line/GDB，并回链 ch19，不重复寄存器细节）：

- 调试链分层：IDE → GDB → OpenOCD → DP/AP → 总线；halt 只是「请求停」，内存访问由调试器代办；SWD 三线（SWDIO/SWCLK/GND）是最小集，实际还需 VTref 与可选 NRST。
- 断点两类：FPB 指令比较器（M3/M4=6、M7=8）vs `BKPT 0xBE00` 替换指令（RAM 断点）；**M0=4、M0+=2**——`06-flash:112` 的「M0/M0+ 2 个」是错的，禁止照抄；给「断点打不上」的三种原因。
- SWO/ITM 四前提：引脚复用、`DBGMCU_CR.TRACE_IOEN/TRACE_MODE`、TRACECLK 有源、调试器接 SWO；缺一即静默。
- DWT 计时流水线：`DEMCR.TRCENA`(bit24) → `DWT->CYCCNT=0` → `CYCCNTENA` → 读 `0xE0001004`；`cycles = µs × f_cpu`，给 72 MHz 与 168 MHz 两个代入例（禁止只写「72 cycles=1 µs」当通例）；Cortex-M7 需 `DWT->LAR=0xC5ACCE55` 解锁（两个来源未提，只作边界提示）。
- 优化等级与可调试性：`-O0/-Og/-O2/-Os` 取舍；`-g3` 不解决内联与重排；给「同一段代码两档汇编对照 + 断点漂移验证」方法。
- 测量三件套分工：逻辑分析仪=协议/时序，示波器=信号质量/边沿/噪声，万用表=平均电流；探头接地与带宽纪律；「逻辑分析仪可替代示波器」不成立。
- 证据分级：寄存器 dump / 反汇编 / 时间戳三者互相对上才算证据；来源无实测（`docs/17` 无读数、`06-flash` 无会话记录），一律标「未实测 / 厂商标称」。
- 调试与看门狗交叉：OpenOCD 默认关狗造成假阴性，回链 ch19。
- 图片引用（至少 4 张）：`/anim/swd-debug-chain.svg`、`/figures/fault-triage-ladder.svg`、`/images/ch17-dwt-window.png`、`/images/ch17-stack-frame.png`；测量段可加已就位的 `/images/tools/oscilloscope-ds1054z.jpg`、`/images/tools/logic-analyzer-8ch.jpg`。
- 至少 2 条相对 `.md` 链接：`./19-watchdog-reset-hardfault.md`、`../v0-foundations/05-toolchain-four-steps.md`、`../v1-drivers/12-timers-pwm.md`。

- [ ] **Step 2: 更新映射状态**

`docs/17-调试与性能优化.md`、`mcu/docs/build/06-flash-debug.md` → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch20`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v2-reliability/20-debug-performance.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 20 pages, 32 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v2-reliability/20-debug-performance.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch20): rewrite debug/performance/measurement chapter (B2)"
```

---

### Task 5: ch21《为什么需要 RTOS》

**Files:**
- Create: `docs/v3-rtos/21-why-rtos.md`
- Modify: `book/data/mapping.tsv`（`docs/15-FreeRTOS入门.md` → `partial`；`mcu/docs/rtos/freertos/00-why-rtos.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Consumes: Task 1 资产（`/anim/why-rtos.svg`、`/figures/sample-15-task-states.svg`、`/images/ch15-two-priority-rules.png`）；已发布 ch10/ch11
- Produces: ch21 正文；mapping 状态推进（`docs/15` = partial，等 ch22 才 migrated）

- [ ] **Step 1: 写章节**

frontmatter：`title: 为什么需要 RTOS`、`platforms: f407,f103`；结构按 Global Constraints（罗盘 → 先做出来 → 机制 → 测量与证据 → 失败分支 → 跨平台边界 → 离开检查）。平台差异集中在 `## 跨平台边界`：f103 为 Cortex-M3/72 MHz/无 FPU/ARM_CM3；f407 为 Cortex-M4F/标称 168 MHz/lab 跑 HSI 16 MHz/ARM_CM4F。

必须覆盖：

- 超级循环的失败是**阻塞传染**，不是「慢」：`uart_echo` 死等 RXNE，等字节期间 `led_tick`/`key_scan` 不被调用，响应上界=最长单圈（`F0:112,130,137,147`）。
- 宿主事件表的 3.299 s 单圈与 5.47 ms 改良版（`F0:79,137,147,182,189,271-275`）一律标「来源说法(未复核)」，**禁止写成 F103/F407 板上实测**；`115200 8N1 → 86.805 µs/字符 ×40 = 3.472 ms` 标「文档推导」。
- 调换代码行序不是优先级：五局最坏迟到中位 1.49 ms vs 1.60 ms，区间互相包住，上界不变（`F0:178-189`）。
- RTOS 三件套与 RAM 成本：每任务私有栈、TCB、PendSV 换魂；先算账再上 OS（`F0:207-233,312`）。
- 两套优先级方向：FreeRTOS 任务「数值大者先」；NVIC「数值小者急」；FromISR 约束 = NVIC **逻辑优先级 ≥5**，即寄存器原始值 `5<<(8-4)=0x50`。**禁止照抄 `F8:160,296` 的「数值 ≥80 才允许 FromISR」**——80 是 8 位 IP 原始值，不是 NVIC 逻辑值；回链 `../v1-drivers/10-interrupts-nvic-exti.md` 的 PRIGROUP/IP 字节，不重讲 EXTI。
- 时基所有权：SysTick 给内核 1 kHz，HAL 时基改 TIM4；两者共占 SysTick 会让 `HAL_Delay` 卡死（`R15:29,42,89,168-176`）；回链 `../v1-drivers/11-systick-timebase-rtc.md`，不重列 SysTick 寄存器。
- `vTaskDelay(n)` 从调用时刻再等 n 个 tick，1 kHz 下 `vTaskDelay(1)` 是 (0,1] ms 区间而不是精确 1 ms；固定周期用 `vTaskDelayUntil` 以上次唤醒点为锚（`R15:55,467-478`；`F3:194,230-231`）。
- 栈按字不按字节：F103 根书例程 128/192/256 字 = 512/768/1024 B；水位 `uxTaskGetStackHighWaterMark()`，溢出检查 `configCHECK_FOR_STACK_OVERFLOW=2` 用 0xA5 填充（`R15:53,242-266`；`F1:106,125`）。F407 lab 是 256/256/320 字，两个工程数字不可互换。
- heap 是池子：池尽 `xTaskCreate` 失败；F103 例程 10240 B vs F407 lab 16 KiB，引用时标工程（`R15:293-301`；`CFG:36`）。
- WCET 判据：裸机可行性看 `ΣWCET ≤ min(T)`；平均 CPU 利用率不能替代最坏响应（`F0:235-245`）。
- 版本口径：引用根书 V11.3.2 的结论时在章首注明「行号与宏语义按 lab 的 V11.1.0 对账」，两版行号不得混排。
- 证据标签：`R15` 的四个上板实验、F0 四步 probe 全部标「未实测 / 来源说法(未复核)」，仓库无日志、无产物。

- 图片引用（至少 3 张）：`/anim/why-rtos.svg`、`/figures/sample-15-task-states.svg`、`/images/ch15-two-priority-rules.png`。
- 至少 2 条相对 `.md` 链接：`../v1-drivers/10-interrupts-nvic-exti.md`、`../v1-drivers/11-systick-timebase-rtc.md`、`./22-tasks-tcb-scheduler.md`。
- 不引用 `<QuizBank>`（源无测验；ch21–23 不新造 quiz id）。

- [ ] **Step 2: 更新映射状态**

`docs/15-FreeRTOS入门.md` → `partial`（ch21 已存在、ch22 未建）；`mcu/docs/rtos/freertos/00-why-rtos.md` → `migrated`。mapping.tsv 状态列手工改，JSON 由脚本生成。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch21`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v3-rtos/21-why-rtos.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 21 pages, 31 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v3-rtos/21-why-rtos.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch21): rewrite why-RTOS chapter (B2)"
```

---

### Task 6: ch22《任务、TCB 与调度》

**Files:**
- Create: `docs/v3-rtos/22-tasks-tcb-scheduler.md`
- Modify: `book/data/mapping.tsv`（`docs/15-FreeRTOS入门.md` → `migrated`；`mcu/docs/rtos/freertos/01-task-tcb.md`、`03-scheduler.md`、`mcu/docs/rtos/rtthread/01-thread-sched.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Consumes: ch21 已发布（优先级方向、栈/heap 预算基线）；Task 1 资产（`/anim/task-create-stack.svg`、`/anim/list-insert.svg`、`/arch/scheduler-structs.png`、`/figures/rtos-03-scheduler.svg`、`/images/ch15-stack-watermark.png`）
- Produces: ch22 正文；TCB/首帧/就绪表事实供 ch23 引用

- [ ] **Step 1: 写章节**

frontmatter：`title: 任务、TCB 与调度`、`platforms: f407`。全部 FreeRTOS 行号与宏语义按 **V11.1.0** 对账，章首一句注明。

必须覆盖：

- TCB 第一字段硬约束：`pxTopOfStack` 在 `tskTaskControlBlock` 偏移 0；PendSV 的 `str r0,[r2]` 按 TCB 地址直接写栈顶，因此不能在前面加字段（`tasks.c:358,360`；`F1:63-78`；`F2:196`）。
- 新任务首帧是「化妆」：xPSR=`0x01000000`、PC=入口、LR=`prvTaskExitError`、R0=参数、EXC_RETURN=`0xFFFFFFFD`；任务函数不许 return（`port.c:92-125,202-231`；`F1:82-100`）。
- 首帧长度 18 字=72 B：硬件 8 + 软件 9 + 对齐 1；源码回退 17 字后停在对齐槽之下（`F2:254-255,328`）。
- `xTaskCreate` 六步：分栈→分 TCB→初始化栈→初始化 TCB→挂就绪表→**条件**触发调度（`taskYIELD_IF_USING_PREEMPTION()`，只在抢占开启且新任务更高时让出，不是无条件立即切换；`F1:104-111`）。
- 栈深单位是 `StackType_t`（4 B）：128 字=512 B；`StackType_t` 在 V11.1.0 ARM_CM4F 的 `portmacro.h:58`，**不是 `F1:106,218` 写的 `:55`**。
- 就绪表是按优先级分格的链表数组：`pxReadyTasksLists[configMAX_PRIORITIES]`，`vListInsertEnd` 挂队尾 + `listGET_OWNER_OF_NEXT_ENTRY` 从上次下一个取 = 同优先级轮转（`F3:100-112`）。
- 选最高就绪的两副面孔：通用路径 `uxTopReadyPriority` 标量递减扫描；M4F 优化路径 32 位位图 `31 - CLZ(bitmap)`。`configMAX_PRIORITIES≤32` **只约束优化路径**；`FreeRTOS.h` 通用默认 0 但 `portmacro.h:144-145` 在 ARM_CM4F 上 `#ifndef` 设为 1，只看前者会误判（`F3:55-96`；`portmacro.h:144-145,161-162`；`tasks.c:160-200`）。
- tick 三段：节拍++→用 `xNextTaskUnblockTime` 剪枝只看延时表队首→必要时返回 `pdTRUE` 请求切换（`F3:140-170`）。
- `vTaskDelay` 是「搬家」不是等待：挂进按唤醒时刻排序的延时表、恢复调度让出 CPU；`vTaskDelay(1)` 区间 (0,1] tick；周期性任务用 `vTaskDelayUntil`（`F3:172-194,230-231`）。
- 动态/静态创建：`xTaskCreate` 用 `pvPortMalloc`；`xTaskCreateStatic` 由调用者给 `StaticTask_t`+栈数组（`F1:155-158`）。
- `INCLUDE_*` 不是「默认全关」：`INCLUDE_vTaskDelay`/`vTaskSuspend` 默认 0，但 `INCLUDE_xTaskGetCurrentTaskHandle` 默认 1；写「部分默认 0，按 API 开启」（`F1:203` 来源说法待核）。
- RT-Thread 对照（按 lab 真实配置，不照抄源文）：`rt_thread` 首成员 `parent`（`rt_object`）、`sp` 对应 `pxTopOfStack`、`current_priority` **数值越小越高**、线程内嵌 `rt_timer`；`create/init` 之后必须 `startup`（`R1:50-59,72-110`）。
- RT-Thread 选位方向必须写对：**找最低置位**用 `__rt_ffs`（FFS/CTZ，ARM 上可 RBIT+CLZ）；`R1:15,79,180,188` 反复写「CLZ 找最低置位/第一个非空字节」方向反了，禁止照抄。
- RT-Thread 级数条件：lab `RT_THREAD_PRIORITY_MAX=32`（`RTCFG:17`），是单级 32 位组；`rt_thread_ready_table[32]` 二级位图只在 >32 时启用，`R1:10,77,89` 把 256 级当本工程事实是范围错位。
- RT-Thread tick：`rt_tick_increase` 递减线程剩余 tick、检查内嵌定时器、必要时 `rt_schedule`（`R1:117-141`；`BOARD:73-78`）。
- 证据标签：GDB 首帧、F3 七步 probe、串口日志、`list_thread` 全部「来源说法(未复核)/未实测」；`List_t` 20 B 为文档推导。

- 图片引用（至少 5 张）：`/anim/task-create-stack.svg`、`/anim/list-insert.svg`、`/arch/scheduler-structs.png`、`/figures/rtos-03-scheduler.svg`、`/images/ch15-stack-watermark.png`。
- 至少 2 条相对 `.md` 链接：`./21-why-rtos.md`、`./23-context-switch-porting.md`、`../v1-drivers/11-systick-timebase-rtc.md`。
- 不引用 `<QuizBank>`。

- [ ] **Step 2: 更新映射状态**

`docs/15-FreeRTOS入门.md`、`mcu/docs/rtos/freertos/01-task-tcb.md`、`03-scheduler.md`、`mcu/docs/rtos/rtthread/01-thread-sched.md` 全部 → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch22`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v3-rtos/22-tasks-tcb-scheduler.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 22 pages, 30 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v3-rtos/22-tasks-tcb-scheduler.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch22): rewrite tasks/TCB/scheduler chapter (B2)"
```

---

### Task 7: ch23《上下文切换与移植》

**Files:**
- Create: `docs/v3-rtos/23-context-switch-porting.md`
- Modify: `book/data/mapping.tsv`（`mcu/docs/rtos/freertos/02-context-switch.md`、`08-port-f407.md`、`mcu/docs/rtos/rtthread/00-arch.md`、`07-port-f407.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Consumes: ch22（TCB 偏移 0、首帧 18 字）；ch10（异常进出、EXC_RETURN）；ch11（SysTick）
- Produces: ch23 正文；三异常接管与两份优先级事实供 ch24/ch27 引用

- [ ] **Step 1: 写章节**

frontmatter：`title: 上下文切换与移植`、`platforms: f407`。FreeRTOS 按 V11.1.0。

必须覆盖：

- 三异常接管：SVC 启第一个任务、PendSV 切换、SysTick 报时；源码名 `vPortSVCHandler`/`xPortPendSVHandler`/`xPortSysTickHandler`，向量槽位见启动文件；三行 `#define` 映射在 `FreeRTOSConfig.h:75-77`（`F8:116,268` 写 `74-77`，`:74` 是注释）（`port.c:260,505,562`；`startup_stm32f407xx.s:108,111,112`；`F8:88-136`）。
- PendSV 必须最低：V11.1.0 ARM_CM4F 把 `portMIN_INTERRUPT_PRIORITY=255` 直接写进 SHPR3 的 PendSV/SysTick 槽（0xFF），**不再读 `configKERNEL_INTERRUPT_PRIORITY`**。写「配置里留着无害，改它不影响行为」；`F8:15,149,154` 把它当活宏是错的（`port.c:65,434-435`；`F2:81,303`）。
- 挂起位：ICSR=`0xE000ED04` bit28 PENDSVSET；`portYIELD` 置位，PendSV 在异常返回后排到最低优先级执行（`portmacro.h:99-100`；`F2:54,61-62`）。
- 软硬分工：硬件自动压 8 字（R0–R3、R12、LR、PC、xPSR）；软件补压 R4–R11+EXC_RETURN 共 9 字；恢复顺序相反，最后 `bx r14`（`F2:95-101,119,233,242`；回链 ch10 的 8 字帧）。
- FPU 行李：EXC_RETURN bit4=0 → 硬件扩展帧带 s0–s15+FPSCR，软件再存 s16–s31；bit4=1 跳过；懒堆叠「先占座、后写真」（`F2:103-105,116-119,264`）。
- PendSV 十一条语义步骤（读 PSP→取 TCB→条件存 s16–s31→存 9 字→写回栈顶→BASEPRI 临界→`vTaskSwitchContext`→恢复 BASEPRI→取新 TCB→弹 9 字→条件弹 FPU→写 PSP→`bx r14`）；`vTaskSwitchContext` 只改 `pxCurrentTCB`（`F2:107-207`；`port.c:505-560`；`tasks.c:5056`）。
- port 选型：F407 用 `ARM_CM4F`（`-mfpu=fpv4-sp-d16 -mfloat-abi=hard`），F103 用 `ARM_CM3`；选错 FPU 端口会在切换时丢浮点寄存器（`F8:65-86`；`R15:187`）。
- 两份优先级：PendSV/SysTick 均 0xFF；`configMAX_SYSCALL_INTERRUPT_PRIORITY=0x50`=逻辑 5。正确大小关系 `0x50 < 0xFF`（syscall 阈值数值更小、urgency 更高）。**`F8:160,296` 的「≥80」、`F8:164`「更小是错的」、`F8:274`「大于才对却给 0x50<255」三处互相打架，全部禁抄**（`CFG:61-62`；`R15:46`）。
- `xTaskCreate` 堆尽返回 `errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY`（负值），不是 `pdFAIL`（0）（`F8:214`；`tasks.c`）。
- 奇数优先级断言只在 `ulImplementedPrioBits==8` 分支执行，F407 只有 4 位（`configPRIO_BITS=4`），不走该分支——不要写成 F407 通用三连断言（`port.c:405-415`；`F2:89,305`；`CFG:18`）。
- `F2:79`「SysTick 优先级高」与同页「两者都填 0xFF」自相矛盾；按 ARM_CM4F port：PendSV/SysTick 都最低（`port.c:65,434-435`）。
- 两条 NOP=6 字节的字节账缺反汇编原文，标「来源说法待核」，不要当校验过的字节账（`F2:158-178,337`）。
- HardFault 归属：ARM_CM4F port **不实现** `HardFault_Handler`；启动文件是 weak，FreeRTOS 只提供任务 return 的 `prvTaskExitError`。`R7:145` 说「FreeRTOS 自带 HardFault」是错的（`startup_stm32f407xx.s:100`；`port.c:125,234`）。
- RT-Thread Nano 对照：四件套（内核 src+libcpu、`rtconfig.h`、`board.c`、异常接管）；`context_gcc.S`（**不是 `context_rvds.S`**，配套 Makefile 编 `context_gcc.o`）里的 `PendSV_Handler`/`HardFault_Handler`（不是 `rt_hw_pendsv` 等虚构符号）；`board.c` 提供 `SysTick_Handler`；**不用 SVC**——`rt_hw_context_switch_to` 置 PendSV 后自然进入；堆符号 `&__bss_end__`→`&_estack`（不是 `HEAP_BEGIN/HEAP_END`）（`R7:14,59-68,75,103-147`；`BOARD:10-11,73-78,90-94`；`Makefile:75`）。
- RT-Thread lab 实况：HSI 16 MHz（不是 25 MHz 母本晶振）；`SysTick` 直接写 `LOAD=16000000/1000-1`、`VAL=0`、`CTRL=0x7`；Nano「约 3KB」是来源说法，不是固定值（`BOARD:5,90-92`；`R7:10,59,163,220`）。
- size 三段 43156/2168/19208 合计 64532 为构建产物（来源说法）；F407 RAM 192 KB=128 SRAM+64 CCM，bss 19208 不是总 RAM（`F8:41,199,204-206`）。
- 证据标签：F2 五步 probe、GDB 软件帧、F8 size/nm、上板状态表全部「未实测/来源说法(未复核)」。
- 平台边界：`## 跨平台边界` 写清 F103（ARM_CM3、无 FPU、SVC/PendSV/SysTick 同机制但无 FPU 行李）与 F407（ARM_CM4F、硬浮点 ABI）的移植差异。

- 图片引用（至少 5 张）：`/anim/context-switch.svg`、`/arch/context-switch.png`、`/figures/rtos-02-fake-frame.svg`、`/anim/freertos-port.svg`、`/images/ch15-psp-msp.png`。
- 至少 2 条相对 `.md` 链接：`./22-tasks-tcb-scheduler.md`、`./24-queue-semaphore-notification.md`、`../v1-drivers/10-interrupts-nvic-exti.md`。
- 不引用 `<QuizBank>`。

- [ ] **Step 2: 更新映射状态**

四个源文件 → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch23`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v3-rtos/23-context-switch-porting.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 23 pages, 29 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v3-rtos/23-context-switch-porting.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch23): rewrite context-switch/porting chapter (B2)"
```

---

### Task 8: ch24《队列、信号量与通知》

**Files:**
- Create: `docs/v3-rtos/24-queue-semaphore-notification.md`
- Create: `docs/.vitepress/data/quizzes/f4-queue.json`（从 `mcu/docs/.vitepress/data/quizzes/f4-queue.json` 复制并修 Q5）
- Modify: `book/data/mapping.tsv`（`mcu/docs/rtos/freertos/04-queue.md`、`05-sem-mutex.md`、`06-notify-event-timer.md`、`mcu/docs/rtos/rtthread/02-ipc.md` → `migrated`；`mcu/docs/lab/e04-priority-inversion.md` → `partial`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Consumes: ch22/ch23（优先级、等待/唤醒、PendSV）；ch10（FromISR 约束）；Task 1 资产
- Produces: ch24 正文 + quiz `f4-queue`；E04 理论摘要（完整实验留 ch40）

- [ ] **Step 1: 写章节**

frontmatter：`title: 队列、信号量与通知`、`platforms: f407`。FreeRTOS 按 V11.1.0。

必须覆盖：

- 一个结构体三种人生：`QueueDefinition` 的 `pcHead/pcWriteTo`、`union{QueuePointers_t;SemaphoreData_t;}`、两条等待名单、`uxMessagesWaiting/uxLength/uxItemSize/cRxLock/cTxLock`；摘录之外补 `uxQueueType` 并标注「节选」（`F4:53-73,88`）。
- `prvCopyDataToQueue` 三件事：`uxItemSize=0` 是信号量/互斥锁分岔口；数据项**单次 memcpy 整项**到 `pcWriteTo`，然后写指针 += item size，到 `pcTail` 才把**指针**回绕到 `pcHead`——**单条数据从不拆两段**（U:queue.c:2420-2425；`F4:85-111`）。互斥锁分支先 `xTaskPriorityDisinherit` 再清 holder。
- 发送三分支：有空位→拷贝并叫醒取件人；`queueOVERWRITE`→覆盖；满且非覆盖→挂 `xTasksWaitingToSend`；`queueOVERWRITE` 时上游 `configASSERT(uxLength==1)`，是硬约束不是建议（U:queue.c:952,1170；`F4:119-146`）。
- 等待名单按优先级叫号，唤醒者更高则当场 `queueYIELD_IF_USING_PREEMPTION`（U:tasks.c:5341；`F4:148-152`）。
- FromISR 只做「延迟让出」：不阻塞、满返回 `errQUEUE_FULL`、把是否换任务写进 `pxHigherPriorityTaskWoken`、中断末尾 `portYIELD_FROM_ISR` 一次结算；ISR 优先级约束 = 逻辑 ≥5 / 原始 0x50，回链 ch10（`F4:154-173`；`CFG:62`）。
- 宏血缘：`xSemaphoreTake→xQueueSemaphoreTake`、`xSemaphoreGive→xQueueGenericSend(...,NULL,0,queueSEND_TO_BACK)`、`xSemaphoreCreateMutex→xQueueCreateMutex`；互斥锁出生即 give 一次；继承三步（判→改优先级→搬就绪表）；还锁回落；二值信号量**没有**继承；递归互斥锁要 `xSemaphoreCreateRecursiveMutex`（`F5:61-131,151`）。
- ISR 里 take 互斥锁是**禁止/未定义用法**（不写 holder、不继承），ISR 只能 give/notify；`F5:172` 把它讲成路径，改写为禁令（U:semphr.h:675→U:queue.c:2035）。
- 通知 vs 信号量：通知写 TCB 的 `ulNotifiedValue[]/ucNotifyState[]`，有计数/覆盖两种；事件组 24 位有**条件**（16 位 tick→8 位、32 位→24 位、64 位→56 位；lab 是 24 位），ANY/ALL、`xEventGroupSetBits` 汇总清位；软件定时器只有一个守护任务，回调串行、禁阻塞；给出三者选型判据（`F6:71-181`；`event_groups.h:133-146`；`CFG:42`）。
- 「通知快约 45%」（`F6:88`）与「快一个数量级」都无版本/配置/引用：只写「更快，幅度依配置，需同板基准」，禁止写 10×（`X0:63,91` 也不得搬入）。
- RAM 账：深度 10、项 16 B → `10×16=160` + `Queue_t=80` + heap_4 块头 8 = **248 B**；`Queue_t=80` 是本源 probe 声称值（未复核），不是跨工程常数（`F4:177`；`F6:201-210,274`）。定时器固定账 1312 B、每定时器 56 B、最小任务 616 B、`(16384-1312)/56=269` 算术自洽但标「来源说法(未复核)」。
- RT-Thread IPC 对照（按上游真实名字）：`rt_ipc_object` 字段是 `suspend_thread`（**不是 `suspend_list`**）；恢复函数是 `rt_ipc_list_resume`（**不是 `rt_ipc_resume`**）；`rt_mutex` 字段 `owner/hold/priority/ceiling_priority/taken_list`（**没有 `original_priority`**）；0 最高；邮箱 4 B；消息队列槽宽 `msg_size` 固定、实发长度 ≤ `msg_size`——**不是「变长队列」**；邮箱 RAM=size×4 正确，消息队列每条至少 +4 B 的 next 指针，源文低估（`R2:48-94` 需按此改写）。
- E04 优先级反转：理论 6000/2500 ms 算术自洽；但 `F5:143`「L 才轮到跑满 3000ms」按字面得 6500，必须写「跑完**剩余 2500 ms**」（`E04:90`）；继承数值按 lab 是 22→20（RT-Thread 小者优先），`R2:103`「1 变 3」方向与数值双错；lab `hardware_status: pending`、实测表全空——只写「理论 + 模型 + 待实测」，完整实验归 ch40（`E04:3-9,72,78-108`）。
- 证据标签：E04 零实测、F6 五幕模拟与 RAM 账为来源说法、源码摘录为文档推导。

- 图片引用（至少 6 张）：`/anim/queue-passing.svg`、`/anim/semaphore-mutex.svg`、`/anim/priority-inversion.svg`、`/images/labs/e04-timeline.svg`、`/figures/rtos-04-queue.svg`、`/figures/rtos-freertos-05-sem-mutex.svg`。
- 至少 2 条相对 `.md` 链接：`./23-context-switch-porting.md`、`./25-memory-management.md`、`../v1-drivers/10-interrupts-nvic-exti.md`、`../v1-drivers/11-systick-timebase-rtc.md`。
- 结尾放 `<QuizBank chapter="f4-queue" />`。

- [ ] **Step 2: 复制并勘误测验**

```bash
mkdir -p docs/.vitepress/data/quizzes
cp mcu/docs/.vitepress/data/quizzes/f4-queue.json docs/.vitepress/data/quizzes/f4-queue.json
```

在副本中修 **Q5（阻断性错误）**：题干保留「写指针已到尾端」，把正确选项改为「单次 memcpy 整项后把写指针回绕到 pcHead；单条数据不跨尾拆分」，解析删掉「分两段 memcpy」并注明落点 `queue.c:2420-2425`；其余选项（拒绝写入/自动扩容）保留作干扰项。Q2 建议把「队首旧值」改为「唯一槽位旧值」（非强制）。Q1/Q3/Q4 通过，不改。

- [ ] **Step 3: 更新映射状态**

`freertos/04`、`05`、`06`、`rtthread/02` → `migrated`；`mcu/docs/lab/e04-priority-inversion.md`（ch24;ch40）→ `partial`（ch40 属 B4）。

Run: `python -m book.mapping --write`

- [ ] **Step 4: 验证**

Run: `python -m book.checks --chapter ch24`
Expected: `checks passed`（含 quiz schema）

Run: `python tools/slop_lint.py docs/v3-rtos/24-queue-semaphore-notification.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 24 pages, 28 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 5: 提交**

```bash
git add docs/v3-rtos/24-queue-semaphore-notification.md docs/.vitepress/data/quizzes/f4-queue.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch24): rewrite queue/semaphore/notification chapter with quiz (B2)"
```

---

### Task 9: ch25《内存管理》

**Files:**
- Create: `docs/v3-rtos/25-memory-management.md`
- Create: `docs/.vitepress/data/quizzes/f7-heap.json`（从 `mcu/docs/.vitepress/data/quizzes/f7-heap.json` 复制，Q4 措辞微调）
- Modify: `book/data/mapping.tsv`（`mcu/docs/rtos/freertos/07-heap.md`、`mcu/docs/rtos/rtthread/03-mem.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Consumes: ch22（TCB/最小栈）、ch24（队列 RAM 账）
- Produces: ch25 正文 + quiz `f7-heap`

- [ ] **Step 1: 写章节**

frontmatter：`title: 内存管理`、`platforms: f407`。FreeRTOS 按 V11.1.0。

必须覆盖：

- 五版能力阶梯，不把 heap_4 说成唯一正确：heap_1 只分配（`vPortFree` 仍在但断言 pv==NULL）；heap_2 可释放、空闲表按大小排序（best fit）且不合并；heap_3 直接包 `malloc/free` 且无任何 `xPortGet` 统计；heap_4 释放+相邻合并；heap_5 多区同 heap_4 算法（U:heap_1.c:130-136；heap_2.c:130-155；heap_3.c:65,89；heap_4.c:247,492；`F7:60-68`）。
- heap_4 合并算法：空闲链表按**地址升序**，插入时前邻接尾、后邻接头都合并；分配是**首次适配**；只有「相邻且空闲」才合并——这就是碎片的物理来源（U:heap_4.c:247,492；`F7:76-120`）。
- **不是「边界标记法」**：heap_4 只有块头（next+size），**没有 footer**；前邻块靠地址序空闲表遍历找到，不是靠「前块地址+大小」反推。`F7:118-120` 术语用错，禁止照抄。
- 块头与对齐：`xHeapStructSize=(sizeof(BlockLink_t)+portBYTE_ALIGNMENT-1)&~mask`；32 位指针 + CM4F `portBYTE_ALIGNMENT=8` → 每次分配 8 B 头 + 对齐余量（U:heap_4.c:158；`F6:209-210`）。
- 两个指标分清：当前空闲 vs 历史最低水位；`xPortGetMinimumEverFreeHeapSize` 只在 heap_4/5 有；heap_3 两个都没有；`F7:358` 把 `heap_4:413`（MinimumEver）当 Free（407）是行号错位（U 逐文件；`F7:203-206` 表正确）。
- 补 `vPortGetHeapStats`（heap_4 独有，含 `xSizeOfLargestFreeBlockInBytes`）：最大连续块**可直读**；heap_5 无此函数，「碎片只能试探」不完整（U:heap_4.c:560,597；`F7:257-263`）。
- 静态分配：`xTaskCreateStatic` 由调用方给 `StaticTask_t`+栈数组；「不因堆耗尽失败」≠「任何参数都成功」；Idle/Timer 钩子真实签名是**三参数**（TCB**、Stack**、`configSTACK_DEPTH_TYPE*`），照抄 `F7:160-167` 的两参版本**编译不过**（U:tasks.c:8584-8586）。
- 栈溢出 canary：`configCHECK_FOR_STACK_OVERFLOW=2` 在切换时检查 0xA5 填充，踩线调 `vApplicationStackOverflowHook`（`F7:189-193`；`CFG:31`）。
- heap_5 多区：`vPortDefineHeapRegions()` 必须在任何 `pvPortMalloc` 之前；区域数组按地址从低到高、以 `{NULL,0}` 结尾；可含普通 SRAM 与 CCM；**CCM 不可 DMA**——正确句是「CCM 不能放 DMA 缓冲」，不是「heap_5 的前提是区域 DMA 够不着」（U:heap_5.c:40-66；`F7:195-197` 前提句明显可疑）。
- 预算公式：栈×字数×4 + TCB + 队列 + 信号量/事件组 + 30% 余量；TCB 取本工程 **88 B（+8 B 头）**，不是 `F7:220` 的「~400B」（`F6:274` 同书冲突，400 B 只能标「其他 trace/MPU 配置粗值」）。
- F407 内存：128 KiB SRAM + **64 KiB CCM**（共 192 KiB），`F7:230`「SRAM 只有 128KB」不完整；堆本体 `ucHeap` 在 `.bss`，与全局变量抢 SRAM，与 Flash 大小无关（`docs/v1-drivers/08-architecture-memory-clock.md:64`；`CFG:36`）。
- RT-Thread 真实堆家族：`mem.c`（small memory）、`memheap.c`、`slab.c`、`mempool.c` 四件；**`src/tlsf.c` 不存在（404）**，TLSF 是论文/软件包，不是 5.x 内核自带；TLSF 选档方向：`fls/CLZ` 只做「size→第一级档位」，选可用块用 `ffs/CTZ` 找最低有效位，`R3:63-67` 写反（RT master 源码；`src/Kconfig:305-347`）。
- slab「碎片免疫」过强：同尺寸类内**不产生外部碎片**，但固定尺寸类带来内部碎片、zone 扩张可能失败（`R3:52,135` 需改写）。
- `rt_mp` 固定块池摘/挂链表头 O(1)、超时可挂起；`RT_USING_HEAP` 关闭后 `*_create` 不编译、`*_init` 仍可用，「零堆固件」成立（`R3:71-95`）。finsh 堆监控命令真实名是 `memheapcheck`/`memheaptrace`/`memcheck`/`memtrace`，`list_memheap` 只是 msh.c 内部函数（`R3:97-112` 需按此改写）。
- 证据标签：场景 5 代码存在（`mcu/code/rtos/01-freertos-lab/main.c:249-264`）但无落盘日志；probe 的 88 B/固定账、R3 的「1 万次耗时」全为来源说法。

- 图片引用（至少 4 张）：`/anim/heap4-coalesce.svg`、`/arch/heap-free-list.png`、`/figures/rtos-freertos-07-heap.svg`、`/anim/rtt-mem-alloc.svg`。
- 至少 2 条相对 `.md` 链接：`./24-queue-semaphore-notification.md`、`./26-device-framework-shell.md`、`../v1-drivers/17-flash-iap-ota.md`。
- 结尾放 `<QuizBank chapter="f7-heap" />`。

- [ ] **Step 2: 复制并微调测验**

```bash
cp mcu/docs/.vitepress/data/quizzes/f7-heap.json docs/.vitepress/data/quizzes/f7-heap.json
```

无阻断勘误。Q4 解析把「从 heap_4 的池子」改为「从所选 heap_x（本工程 heap_4）分配」；Q2 解析补一句「代码可复跑、落盘日志待补」。Q1/Q3 不改。

- [ ] **Step 3: 更新映射状态**

`mcu/docs/rtos/freertos/07-heap.md`、`mcu/docs/rtos/rtthread/03-mem.md` → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 4: 验证**

Run: `python -m book.checks --chapter ch25`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v3-rtos/25-memory-management.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 25 pages, 27 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 5: 提交**

```bash
git add docs/v3-rtos/25-memory-management.md docs/.vitepress/data/quizzes/f7-heap.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch25): rewrite memory-management chapter with quiz (B2)"
```

---

### Task 10: ch26《设备框架、shell 与配置系统》

**Files:**
- Create: `docs/v3-rtos/26-device-framework-shell.md`
- Modify: `book/data/mapping.tsv`（`mcu/docs/rtos/rtthread/04-device.md`、`05-finsh.md`、`06-env-menuconfig.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Consumes: ch22（线程/优先级）、ch23（ISR→任务边界）、ch24（ring+sem）、ch25（设备对象分配）
- Produces: ch26 正文（设备框架 + shell + 构建配置，不是 RTT 全书）

- [ ] **Step 1: 写章节**

frontmatter：`title: 设备框架、shell 与配置系统`、`platforms: f407`。RT-Thread 按 **v5.3.0** 对账；默认 F407 BSP 指 `bsp/stm32/stm32f407-atk-explorer`（`R6:30,147` 的 `stm32f407-zeo` 不存在，禁止照抄）。

必须覆盖：

- 对象模型：`rt_object` 继承、`RT_Object_Class_Device` 容器、`register/find` 名字契约；`RT_USING_DEVICE_OPS` 的两套接口（开→`ops` 表；关→`struct rt_device` 内的内联函数指针），把 ops 画成无条件成员是错的（`R4:79-117`；`rtdef.h:1408-1424`；`device.c:67-126`）。
- `open/read/write/control` 分发与 `ref_count`：open 先 init/open，成功后才 `ref_count++`（`R4:115` 说反了）；read/write 返回 **`rt_ssize_t`**（不是 `rt_size_t`，负值可表达错误）；设备类枚举只作分类，不是容器键（`R4:105-117`；`rtdef.h:1332-1344`；`device.c:222-283`）。
- PIN：真实宏是 `GET_PIN(A,5)`、`GET_PIN(C,12)`——参数是**记号**不是字符，`GET_PIN('A',5)` 不能编译；`RT_PIN_A` 不存在；`port×16` 在 STM32 普通 GPIO 上成立（实际宏用基地址差 `(16*((GPIOx_BASE-GPIOA_BASE)/0x400))+PIN`），MP1 用 `0x1000`、GPIOZ 特判 `176+PIN`；`rt_pin_attach_irq` 与设备框架的关系（`R4:137-145`；`drv_gpio.h:80-82`）。
- UART：v1 默认 `RT_DEVICE_FLAG_INT_RX(0x100)`，v2 才有 `RX_NON_BLOCKING(0x2000)`；默认 F407 BSP 是 V1；正确结构是「ISR 搬字节→ring→释放 sem→任务处理」；`R4:171-181` 的 `while(size)` 回调示例在 `rt_device_read` 返回 0 时死循环，必须写 `n==0` 退出或改为驱动填 ring、回调只释放 sem；`R4:198` 与 `R4:294` 对 ISR 上下文自相矛盾，按 v1/v2/DMA 分开写（`R4:162-208`；`serial/Kconfig:5-14`；`dev_serial_v2.h:172-175`）。
- I2C/SPI：总线设备/从设备两级；总线锁是 `struct rt_mutex lock` + `rt_i2c_bus_lock/unlock`，**不是 ops 的 acquire/release**；ops 是 `master_xfer/slave_xfer/i2c_bus_control`；`rt_i2c_transfer` 的消息语义（`R4:210-228`；`dev_i2c.h:226-268,416-423`）。
- 自定义设备：默认 F407 BSP 的 `rtconfig.h` **没有** `RT_USING_DEVICE_OPS`，此时 `parent.ops` 与 `struct rt_device_ops` 都不存在——`R4:262` 的示例不能编译；给「条件编译」与「直接填 `parent.init/open/close/read/write/control`」两种写法，示例必须在默认配置下可编译；`RT_Device_Class_Miscellaneous`、注册名唯一、`INIT_DEVICE_EXPORT`（`R4:230-276`；`rtdef.h:1408-1424`；atk BSP rtconfig）。
- finsh/MSH：`FSymTab` 链接段 + `KEEP`；真实结构是 `struct finsh_syscall { name; desc; opt?; func; }`，宏生成 `__fsym_##cmd`——**没有 `struct msh_cmd_entry`**；`MSH_CMD_EXPORT` 是可变参数宏；查找是线性 `msh_get_cmd`（不是「少时线性、多时二分」）；`list_thread` 原型是 `long list_thread(void)`（`R5:96` 的 `int list_thread(int,char**)` 与源码不符）；默认 `FINSH_THREAD_STACK_SIZE=4096`（不是 2–4 KiB）、`FINSH_THREAD_PRIORITY=20`、`FINSH_ARG_MAX=10`、`FINSH_CMD_SIZE=80`、history 5 行（`R5:47-107,145-160`；`finsh.h:82,153-194`；`Kconfig:1-97`；`cmd.c:215,927,1188`）。
- finsh 裁剪开关：5.3.0 **没有 `FINSH_USING_MSH_ONLY`**；总开关是 `RT_USING_MSH`（其下 `FINSH_USING_MSH` 默认 y）；`RT_DEBUG` 不是 shell 总开关；删除 `msh_cmd.c`（不存在）与「16–24 B entry」说法（32 位默认 16 B 含 opt，关 option 12 B，字符串另计）（`Kconfig:1-97`；`finsh.h:182-194`）。
- 配置与构建：Kconfig→`.config`→`rtconfig.h`；**menuconfig 写 `.config`，scons 生成 `rtconfig.h`**（`R6:16` 把两步并成一步，自相矛盾）；`depend=['RT_USING_DEVICE']` 是 Kconfig 与 scons 的接合点；`rtconfig.h` 是生成物；`RT_USING_I2C` 是**无值宏**（`#define RT_USING_I2C`，不是 `... 1`）；`Environment(tools=['gccarm'], ARM_GCC_PATH=...)` 不是 5.x 标准写法，工具链路径由 `rtconfig.py` 的 `EXEC_PATH/PREFIX` 提供（标「按目标 BSP 复核」）（`R6:70-126,142-166`）。
- 不编造默认值：RT-Thread 没有统一「默认线程栈」（`rt_thread_create` 的 `stack_size` 必填；idle 默认 256、soft timer 默认 512）；命令数无固定上限（受 Flash/链接脚本约束）（六源缺口）。
- lab 实况：`mcu/code/rtos/02-rt-thread-lab/rtconfig.h` 是 Nano 式裁剪（无 `RT_USING_DEVICE`/`RT_USING_FINSH`）——设备/shell 实验必须切标准 BSP 或显式打开组件，**不能宣称该 lab 固件已跑通**。
- 证据标签：六源零实测；「168 MHz 上纳秒级」「整套 msh 10–20KB Flash」为来源说法；三段实验只写设计与判据，标「未实测」。

- 图片引用（至少 4 张）：`/anim/rtt-device-chain.svg`、`/arch/device-ops.png`、`/anim/rtt-finsh-dispatch.svg`、`/anim/menuconfig-flow.svg`。
- 至少 2 条相对 `.md` 链接：`./22-tasks-tcb-scheduler.md`、`./23-context-switch-porting.md`、`./24-queue-semaphore-notification.md`、`../v1-drivers/10-interrupts-nvic-exti.md`。
- 不引用 `<QuizBank>`（无可用 JSON，不新造）。

- [ ] **Step 2: 更新映射状态**

`rtthread/04`、`05`、`06` → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch26`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v3-rtos/26-device-framework-shell.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 26 pages, 26 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v3-rtos/26-device-framework-shell.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch26): rewrite device/shell/config chapter (B2)"
```

---

### Task 11: ch27《双 OS 对照与选型》

**Files:**
- Create: `docs/v3-rtos/27-rtos-comparison-selection.md`
- Modify: `book/data/mapping.tsv`（`docs/28-嵌入式系统与RTOS生态.md`、`mcu/docs/rtos/compare/00-side-by-side.md`、`01-choose.md` → `migrated`）
- Generated: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Consumes: ch21–ch26 全部机制章；ch10（中断延迟边界）
- Produces: ch27 正文（只做对照 + 选型，不重教机制）

- [ ] **Step 1: 写章节**

frontmatter：`title: 双 OS 对照与选型`、`platforms: f407`。版本钉住：FreeRTOS V11.3.2（根书口径）/ lab V11.1.0 差异注明；RT-Thread v5.3.0。

必须覆盖：

- 选型顺序：硬约束（平台/认证/内存/工具链/维护周期）→ 驱动与生态 → 团队熟悉度兜底（`D28:68,84-94`；`X1:41-45`）。
- 调度器对照必须带条件：优先级方向（FreeRTOS 大=高、RT-Thread 小=高）；数量由配置/端口决定——FreeRTOS lab 只有 5 级（合法 0..4），CM4F 优化路径上限 32；RT-Thread 默认 32，>32 才二级位图；**删除「RT-Thread 总是 256/二级位图」与「FreeRTOS 常 32/上限 32」的无条件说法**（`X0:36-38`；`src/Kconfig:94-110`；`src/scheduler_up.c:46-51,107-116`；`CFG:23`；`RTCFG:17`；`R1:2,10,77,89`）。
- IPC 对照：FreeRTOS 队列 item size 创建时固定（条目数可变，不是「变长队列」）；RT-Thread 消息队列槽宽 `msg_size` 固定、**实发长度 ≤ `msg_size`**（是「固定最大块的变长消息」）；邮箱 4 B；通知无 RT-Thread 直接等价（用 sem/event 替代，不写「完全没有轻量机制」）；事件位宽有 tick 宽度条件（16→8、32→24、64→56，lab 为 24），RT-Thread 事件集 32 位；**`D28:253,263` 把 RT-Thread 消息队列写成「定长」是错的，`R2:94` 把 FreeRTOS 队列说成「变长」也是错的**（`X0:42-45`；`src/ipc.c:3432,3526-3528`；`R2:15,85,159`；`event_groups.h:133-146`）。
- 内存对照：heap_1–5、静态创建（API 存在但 lab `configSUPPORT_STATIC_ALLOCATION=0`，举例须注明配置）；RT-Thread small mem/slab/memheap + 内存池；**TLSF 是软件包/第三方，不在 5.3.0 内核**（`src/tlsf.c` 不存在）；F407 128 KiB SRAM + 64 KiB CCM 且 CCM 不可 DMA；资源账按 map/水位，不套 `D28:586-599` 的 256 KiB 示例（算术自洽但平台错）（`X0:47-48`；`src/Kconfig:305-347`；`stm32f407xx.ld:5-7`；`CFG:35`）。
- 设备/配置/许可：FreeRTOS 裸内核 + `FreeRTOSConfig.h`（ESP-IDF 用 Kconfig 是混合形态，不把「手改」说成唯一方式）；RT-Thread `rt_device` + Kconfig/scons；许可证 FreeRTOS-Kernel MIT vs RT-Thread Apache-2.0（上游 LICENSE 实读）；生态数量必须带抓取日期与来源，否则只写「覆盖联网/存储/UI」（`X0:49-52,83`；上游 `LICENSE.md:1`/`LICENSE:1`）。
- 实时性：六源无中断延迟/切换时延实测；写清测试条件（内核、主频、Flash 等待、临界区、ISR 优先级），用 `R=B+C+S` 与 `U<1` 的边界，**不写「µs 级」空话**（`D28:178-246`）。
- 选型树修正：ESP32 平台绑定 IDF 自带 FreeRTOS（S3 双核 **SMP**，不能外推到单核 F407）；STM32「需要 3+ 组件」是经验阈值（不是测量），标准版 vs Nano 要给组件清单+map；**「不需要组件→标准版」分支错，应 FreeRTOS/Nano**；**「安全认证→静态 FreeRTOS」错，静态分配≠认证，需认证内核/证据链**；团队熟悉度作为工程判断保留（`X1:24-39,43-65,122-128`；`D28:317`）。
- 迁移坑：优先级方向、通知→sem、队列语义、heap API、静态 API、事件位宽、版本钉住；**「优先级 5 可迁移」示例在 lab 越界**（`configMAX_PRIORITIES=5` → 合法 0..4），必须先读最大值再给映射（`X0:87-88,120-126`；`CFG:23`）。
- 定量说法处置：32K/3K/10 倍/「省几个月」/「数百个包」/µA 睡眠/通知 10×/「读懂一周」全部「来源说法(未复核)」——要么删除，要么带版本/配置/日期；通知速度只写「更快，幅度依配置」（`X0:63,91`；`X1:36-37,44,55,57,74,83,91,97,100,127`；`F6:88`）。
- `D28:233`「任务优先级数值越大越高」只对 FreeRTOS 成立，写成「方向随内核，不能当通则」；Zephyr 红黑树细节未复核，删除或只留「Kconfig+Devicetree+设备模型」（`D28:233`；`X0:100`；`D28:388-446`）。
- 证据标签：两 OS 的切换时延、中断延迟、ROM/RAM 占用、包数量、迁移工时全为「未实测」；选型结论落在「约束/证据/风险」上。

- 图片引用（至少 5 张）：`/anim/dual-os-compare.svg`、`/anim/rtos-decision-tree.svg`、`/arch/rtos-side-by-side.png`、`/figures/sample-28-os-compare.svg`、`/images/ch28-os-compare.png`。
- 至少 2 条相对 `.md` 链接：`./21-why-rtos.md`、`./22-tasks-tcb-scheduler.md`、`./24-queue-semaphore-notification.md`、`./25-memory-management.md`、`./26-device-framework-shell.md`。
- 不引用 `<QuizBank>`。

- [ ] **Step 2: 更新映射状态**

`docs/28-嵌入式系统与RTOS生态.md`、`mcu/docs/rtos/compare/00-side-by-side.md`、`01-choose.md` → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch27`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v3-rtos/27-rtos-comparison-selection.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 27 pages, 25 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v3-rtos/27-rtos-comparison-selection.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch27): rewrite dual-OS comparison/selection chapter (B2)"
```

---

### Task 12: B1 前向引用清扫（reference-style → inline）

**Files:**
- Modify: `docs/v0-foundations/02-c-volatile-ub.md`（`:396` 定义 `[ch19]`）
- Modify: `docs/v0-foundations/04-function-pointer-state-machine.md`（`:370-372` 定义 `[ch19]/[ch23]/[ch24]`）
- Modify: `docs/v0-foundations/05-toolchain-four-steps.md`（`:396` 定义 `[ch20]`）
- Modify: `docs/v0-foundations/06-linker-startup-map.md`（`:389` 定义 `[ch20]`）
- Modify: `docs/v1-drivers/08-architecture-memory-clock.md`（`:334-336` 定义 `[ch18]/[ch19]/[ch20]`）
- Modify: `docs/v1-drivers/10-interrupts-nvic-exti.md`（`:408-410` 定义 `[ch19]/[ch23]/[ch24]`）
- Modify: `docs/v1-drivers/11-systick-timebase-rtc.md`（`:353-356` 定义 `[ch18]/[ch19]/[ch21]/[ch23]`）
- Modify: `docs/v1-drivers/15-adc-dac-sampling.md`（`:307` 定义 `[ch18]`）
- Modify: `docs/v1-drivers/16-i2c-spi.md`（`:470` 定义 `[ch18]`）
- Modify: `docs/v1-drivers/17-flash-iap-ota.md`（`:685-686` 定义 `[ch18]/[ch19]`）

**Interfaces:**
- Consumes: Task 5–11 已让 ch18–ch24 目标文件全部存在（inline 链接可通过检查）
- Produces: B1 章节只含 inline 相对 `.md` 链接，无遗留 reference-style 定义

- [ ] **Step 1: 盘点**

Run:

```bash
grep -rn "^\[ch1[89]\]:\|^\[ch2[0-7]\]:\|^\[ch2[0-7]\]:" docs/v0-foundations docs/v1-drivers
grep -rno "\]\[ch1[89]\]\|\]\[ch2[0-7]\]" docs/v0-foundations docs/v1-drivers
```

当前基线：**20 条定义、10 个文件**；引用点约 35 处（含 `:14` 罗盘行与 `:200/:247/:311/:326/:656/:658` 同行多处）。以实测输出为准，下列步骤清到 grep 无输出为止。

- [ ] **Step 2: 改写为 inline 链接**

对每一处 `[文本][chNN]`：

- 目标为 ch18–ch20 → `[文本](../v2-reliability/<文件名>)`；
- 目标为 ch21/ch23/ch24 → `[文本](../v3-rtos/<文件名>)`；
- 具体目标见上方各文件定义行（如 `[ch18]` → `../v2-reliability/18-low-power.md`、`[ch23]` → `../v3-rtos/23-context-switch-porting.md`）。

然后删除这 10 个文件中所有指向 ch18–ch27 的定义行。**只动这 6 个 id（ch18/19/20/21/23/24）与它们的定义；其它残留定义（如 ch10、ch17、ch29、ch30、ch31、ch34、ch40）一律不动。**

- [ ] **Step 3: 验证**

Run:

```bash
grep -rn "\]\[ch1[89]\]\|\]\[ch2[0-7]\]" docs/v0-foundations docs/v1-drivers
```

Expected: 无输出（exit 1）。

Run: `python -m book.checks --check`
Expected: `checks passed`（inline 链接指向已存在的 ch18–ch24 文件）

Run: `python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md`
Expected: exit 0，无命中

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/02-c-volatile-ub.md docs/v0-foundations/04-function-pointer-state-machine.md docs/v0-foundations/05-toolchain-four-steps.md docs/v0-foundations/06-linker-startup-map.md docs/v1-drivers/08-architecture-memory-clock.md docs/v1-drivers/10-interrupts-nvic-exti.md docs/v1-drivers/11-systick-timebase-rtc.md docs/v1-drivers/15-adc-dac-sampling.md docs/v1-drivers/16-i2c-spi.md docs/v1-drivers/17-flash-iap-ota.md
git commit -m "docs(links): inline B1 forward references to volumes 2-3 (B2)"
```

---

### Task 13: CI 接入、批次记录与 B2 证据

**Files:**
- Modify: `.github/workflows/merge-check.yml`（`Run book checks` 的 slop 行）
- Modify: `plans/2026-11-12-merged-book/README.md`
- Create: `plans/2026-11-12-merged-book/evidence/b2-local.md`

**Interfaces:**
- Consumes: Task 1–12 全部产物
- Produces: main 上可执行的 B2 质量门；批次记录与本地证据

- [ ] **Step 1: 扩展 CI slop glob**

把 `Run book checks` 中的：

```yaml
          python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md
```

改为：

```yaml
          python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md
```

`pull_request.paths` 与 `push.paths` 已含 `docs/**`，不动。

- [ ] **Step 2: 更新批次记录 `plans/2026-11-12-merged-book/README.md`**

- B2 行状态改为 `本批完成（本地）`。
- 「本批校验命令」的 slop 行同步为四个 glob。
- 「数据文件」补充：B2 结束时 `mapping.tsv` 中 `docs/15`、`docs/16`、`docs/11`、`docs/17`、`docs/28` 等已 `migrated`；`mcu/docs/lab/e04-priority-inversion.md` 与 `e06-lowpower-current.md` 仍 `partial`（等 B4 的 ch40）。

- [ ] **Step 3: 全量本地验收并写证据 `plans/2026-11-12-merged-book/evidence/b2-local.md`**

依次运行并记录真实输出与退出码：

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
python -m book.checks --check
python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md
python -m book.build_html --check
node --test scripts/tests/legacy-redirects.test.mjs
```

证据文件格式对齐 `b1-local.md`：分支名、HEAD 提交、Python/Node 版本、每条命令的真实输出摘要与退出码、10 个新章文件名（ch18–ch27）、13 组测验 id（B1 的 10 个 + `s14-pwr`、`f4-queue`、`f7-heap`）、`built 27 pages, 25 planned chapters missing`、mapping 迁移摘要、以及「未验证：CI 远程运行结果；未执行任何远程推送或 Pages 切换；VitePress 站点切换仍归 B5」。

- [ ] **Step 4: 提交**

```bash
git add .github/workflows/merge-check.yml plans/2026-11-12-merged-book/README.md plans/2026-11-12-merged-book/evidence/b2-local.md
git commit -m "chore(ci): enable B2 chapter gates and record local evidence (B2)"
```

---

## Self-Review 记录

- **Spec 覆盖**：B2 出口的「卷 2–3 共 10 章改写」→ Task 2–11（ch18→Task 2、ch19→3、ch20→4、ch21→5、ch22→6、ch23→7、ch24→8、ch25→9、ch26→10、ch27→11）；「罗盘/结构」→ 每章 Step 1 + `validate_chapter_file`；「资产」→ Task 1（52 文件，docs/public 92→144）+ 每章图片检查；「测验」→ Task 2（s14-pwr 勘误）、Task 8（f4-queue Q5 阻断性勘误）、Task 9（f7-heap 微调）+ Task 13 全量 schema/孤儿/重复检查；「mapping 逐源状态」→ 每章 Step 2 + `--check`；「slop」→ 每章 slop + Task 12/13 四 glob；「CI」→ Task 13；「B1 前向引用」→ Task 12（20 定义、10 文件、6 个 id）；「本地证据」→ Task 13。
- **Placeholder 扫描**：无 TBD/TODO/「稍后补」；每步均含命令与期望输出，每章含具体锚点与禁止照抄清单。
- **类型一致性**：quiz id 统一为 `s14-pwr` / `f4-queue` / `f7-heap`；章节路径与 `book/data/toc.tsv:18-27` 完全一致；`build_html` 计数按 17→27 单调推进（18/34→27/25）；mapping 状态机遵守 planned（目标不存在）→partial（部分存在）→migrated（全部存在）。
- **已知边界**：`e04`/`e06` 保持 `partial` 直到 B4 的 ch40；VitePress 配置与 Pages 切换仍归 B5；本批不含任何远程推送/PR/发布动作（需另行授权）。
