# 双书合并 B0（脚手架与映射）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立合并新书的唯一 manifest、123 源章节到 46 章的机器可校验映射、章节契约检查器、旧 URL 跳转存根生成器与 CI 门，同时不改动旧书与旧站。

**Architecture:** 新增 `book/data/*.tsv` 作为人工维护的数据源，`book/manifest.py` 与 `book/mapping.py` 生成并校验 `docs/manifest.json` 与 `plans/2026-11-12-merged-book/mapping.json`；`book/contracts.py` 定义后续批次逐章验收的契约；`scripts/legacy-redirects.mjs` 从映射生成旧 `/mcu/**` 跳转存根；新增 `merge-check.yml` 在 CI 运行全部校验。旧 `stm32-book/`、`mcu/mcu-book/`、`mcu/docs/` 在 B0 零改动。

**Tech Stack:** Python 3.13（stdlib，无新依赖）、Node.js 20+（`node:test`）、GitHub Actions。

**Spec:** [docs/superpowers/specs/2026-11-12-merged-book-design.md](../specs/2026-11-12-merged-book-design.md)

## Global Constraints

- 仅中文书稿；英文版在 B5 归档，本计划不处理。
- 不修改旧书与旧站：`docs/00-28*.md`、`docs/en/**`、`stm32-book/`、`mcu/mcu-book/`、`mcu/docs/**`、既有 workflow 文件一律零改动；只新增文件（外加 Task 5 新建 workflow）。
- 不新增第三方依赖；Python 只用标准库，Node 只用内置模块。
- 站点 base 常量在新代码中一律写 `/STM32/`，测试里写同一字面量，禁止从实现 import 常量做预期值。
- 所有提交按显式路径暂存，禁止 `git add -A` / `git add .`。
- 远程推送、PR 合入与 Pages 切换需另行授权；本计划只做本地提交。
- 章节文件命名 `NN-slug.md`，编号 `01`–`46` 连续；卷目录固定为 `v0-foundations/` … `v7-delivery/`。
- 语言与平台标记固定集合：`f103`、`f407`、`gd32`、`esp32`、`generic`。

---

### Task 1: 统一 manifest 数据与校验器

**Files:**
- Create: `book/__init__.py`
- Create: `book/data/toc.tsv`
- Create: `book/manifest.py`
- Create: `book/tests/test_manifest.py`
- Create: `docs/manifest.json`（由脚本生成）

**Interfaces:**
- Consumes: 无。
- Produces: `book.manifest.load_toc(path) -> list[dict]`；`build_manifest(rows) -> dict`；`dumps(manifest) -> str`；`validate(manifest, rows) -> list[str]`；常量 `ROOT`、`TOC`、`OUT`、`ALLOWED_PLATFORMS`、`VOL_DIR`、`VOLUMES`；CLI `python -m book.manifest --write|--check`。

- [ ] **Step 1: 写失败测试**

创建 `book/tests/test_manifest.py`：

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import manifest as m


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.rows = m.load_toc()
        self.manifest = m.build_manifest(self.rows)

    def test_counts(self):
        self.assertEqual([p["id"] for p in self.manifest["parts"]], [f"v{i}" for i in range(8)])
        chapters = [c for p in self.manifest["parts"] for c in p["chapters"]]
        self.assertEqual(len(chapters), 46)
        self.assertEqual(len(self.manifest["appendices"]), 6)

    def test_chapter_ids_sequential(self):
        chapters = [c["id"] for p in self.manifest["parts"] for c in p["chapters"]]
        self.assertEqual(chapters, [f"ch{i:02d}" for i in range(1, 47)])

    def test_files_match_volume_dirs(self):
        for part in self.manifest["parts"]:
            prefix = m.VOL_DIR[part["id"]]
            for chapter in part["chapters"]:
                self.assertTrue(chapter["file"].startswith(prefix), chapter)
        for appendix in self.manifest["appendices"]:
            self.assertTrue(appendix["file"].startswith("appendix/"), appendix)

    def test_platforms_valid(self):
        for part in self.manifest["parts"]:
            for chapter in part["chapters"]:
                self.assertTrue(chapter["platforms"])
                self.assertLessEqual(set(chapter["platforms"]), m.ALLOWED_PLATFORMS)

    def test_status_planned(self):
        for part in self.manifest["parts"]:
            for chapter in part["chapters"]:
                self.assertEqual(chapter["status"], "planned")

    def test_committed_manifest_current(self):
        self.assertEqual(m.OUT.read_text(encoding="utf-8"), m.dumps(self.manifest))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover book/tests -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'book'` 或 `book.manifest`。

- [ ] **Step 3: 写数据文件 `book/data/toc.tsv`**

制表符分隔，五列：`id	卷	标题	文件	平台`。内容如下（每行之间是真实 TAB）：

```text
ch01	v0	嵌入式 C 的内存模型与指针	v0-foundations/01-c-memory-model.md	generic
ch02	v0	volatile、const 与未定义行为	v0-foundations/02-c-volatile-ub.md	generic
ch03	v0	结构体、ABI 与寄存器映射	v0-foundations/03-struct-abi-registers.md	f407,f103
ch04	v0	函数指针、状态机与调用约定	v0-foundations/04-function-pointer-state-machine.md	f407,f103
ch05	v0	工具链与四步构建	v0-foundations/05-toolchain-four-steps.md	generic
ch06	v0	链接脚本、启动与 map 体积审计	v0-foundations/06-linker-startup-map.md	f407
ch07	v0	构建系统与遗留栈	v0-foundations/07-build-systems-legacy.md	f103,esp32
ch08	v1	架构、存储器地图与时钟树	v1-drivers/08-architecture-memory-clock.md	f407,f103,gd32
ch09	v1	GPIO	v1-drivers/09-gpio.md	f407,f103,gd32,esp32
ch10	v1	中断、NVIC/EXTI、CLIC 与双核	v1-drivers/10-interrupts-nvic-exti.md	f407,f103,gd32,esp32
ch11	v1	SysTick 与时基（含 RTC）	v1-drivers/11-systick-timebase-rtc.md	f407,f103
ch12	v1	定时器与 PWM	v1-drivers/12-timers-pwm.md	f407,f103,esp32
ch13	v1	UART 与可恢复帧协议	v1-drivers/13-uart-framed-protocol.md	f407,f103,esp32,gd32
ch14	v1	DMA	v1-drivers/14-dma.md	f407,f103
ch15	v1	ADC/DAC 与采样	v1-drivers/15-adc-dac-sampling.md	f407,f103
ch16	v1	I2C 与 SPI	v1-drivers/16-i2c-spi.md	f407,f103,esp32
ch17	v1	Flash、IAP 与 OTA	v1-drivers/17-flash-iap-ota.md	f407,f103,esp32
ch18	v2	低功耗设计	v2-reliability/18-low-power.md	f407,f103,esp32
ch19	v2	看门狗、复位与 HardFault	v2-reliability/19-watchdog-reset-hardfault.md	f407,f103,esp32
ch20	v2	调试、性能与测量	v2-reliability/20-debug-performance.md	f407,f103
ch21	v3	为什么需要 RTOS	v3-rtos/21-why-rtos.md	f407,f103
ch22	v3	任务、TCB 与调度	v3-rtos/22-tasks-tcb-scheduler.md	f407
ch23	v3	上下文切换与移植	v3-rtos/23-context-switch-porting.md	f407
ch24	v3	队列、信号量与通知	v3-rtos/24-queue-semaphore-notification.md	f407
ch25	v3	内存管理	v3-rtos/25-memory-management.md	f407
ch26	v3	设备框架、shell 与配置系统	v3-rtos/26-device-framework-shell.md	f407
ch27	v3	双 OS 对照与选型	v3-rtos/27-rtos-comparison-selection.md	f407
ch28	v4	芯片迁移方法论与引脚/外设差异	v4-platforms/28-chip-migration-differences.md	f407,f103
ch29	v4	GD32 系列对照（ARM + RISC-V）	v4-platforms/29-gd32-arm-riscv.md	gd32
ch30	v4	ESP32-S3 架构、启动与工程	v4-platforms/30-esp32s3-architecture-boot.md	esp32
ch31	v4	ESP32 外设、驱动框架与音频链路	v4-platforms/31-esp32-drivers-audio.md	esp32
ch32	v4	Wi-Fi、蓝牙与 ESP-NOW	v4-platforms/32-esp32-wifi-ble-espnow.md	esp32
ch33	v4	网络与协议栈	v4-platforms/33-network-protocol-stack.md	f407,esp32
ch34	v4	多核、Cache 与内存一致性	v4-platforms/34-multicore-cache.md	esp32,f407
ch35	v4	现场总线与 USB	v4-platforms/35-can-usb-fieldbus.md	f103,f407
ch36	v5	电机驱动与供电	v5-motion/36-motor-driver-power.md	f103
ch37	v5	直流电机开环调速	v5-motion/37-dc-motor-openloop.md	f103
ch38	v5	编码器与转速测量	v5-motion/38-encoder-speed-measurement.md	f103
ch39	v5	速度闭环与 PI	v5-motion/39-speed-closed-loop-pi.md	f103
ch40	v6	实物实验方法与仪器证据	v6-labs-projects/40-lab-method-instruments.md	generic
ch41	v6	双板综合项目	v6-labs-projects/41-dual-board-logger-project.md	f407,esp32
ch42	v6	项目实战与交付验收	v6-labs-projects/42-project-delivery-acceptance.md	generic
ch43	v7	AI 结对开发与提示词工作流	v7-delivery/43-ai-pair-programming.md	generic
ch44	v7	手册对账与幻觉防御	v7-delivery/44-manual-reconciliation-hallucination.md	generic
ch45	v7	常见故障排查手册	v7-delivery/45-troubleshooting-handbook.md	generic
ch46	v7	资料、学习路线与开源地图	v7-delivery/46-resources-roadmap-open-source.md	generic
apA	ap	工程深读	appendix/A-engineering-deep-read.md	generic
apB	ap	配套工程索引	appendix/B-project-index.md	generic
apC	ap	习题与自测答案	appendix/C-exercises-answers.md	generic
apD	ap	术语表	appendix/D-glossary.md	generic
apE	ap	来源、版本与许可	appendix/E-sources-version-license.md	generic
apF	ap	开源项目与社区地图	appendix/F-open-source-community-map.md	generic
```

- [ ] **Step 4: 写 `book/__init__.py` 与 `book/manifest.py`**

`book/__init__.py` 为空文件。

`book/manifest.py`：

```python
"""Build and validate docs/manifest.json from book/data/toc.tsv."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOC = ROOT / "book" / "data" / "toc.tsv"
OUT = ROOT / "docs" / "manifest.json"

TITLE = "通往单片机之路"
SUBTITLE = "从点亮一颗灯到交付一个系统"
VERSION = "0.1.0"

ALLOWED_PLATFORMS = {"f103", "f407", "gd32", "esp32", "generic"}

VOLUMES = [
    ("v0", "卷 0 · 语言与构建", "把 C、工具链与固件构建的地基打牢：能解释一段代码如何变成可烧录的固件。"),
    ("v1", "卷 1 · 裸机驱动", "从寄存器与 HAL 两条路径驱动真实外设，并能用波形、寄存器读回与最小可见结果对账。"),
    ("v2", "卷 2 · 可靠性与故障", "处理掉电、升级、看门狗、低功耗与崩溃现场，能复现失败并留下可定位证据。"),
    ("v3", "卷 3 · RTOS", "从内核源码理解任务、调度、IPC 与内存，能在 FreeRTOS 与 RT-Thread 之间做出有依据的选型。"),
    ("v4", "卷 4 · 多平台与连接", "迁移芯片与软件栈：处理 GD32、ESP32-S3、多核、Cache、网络与现场总线的差异。"),
    ("v5", "卷 5 · 运动控制", "完成电机驱动、开环调速、编码器测速与闭环控制的完整证据链。"),
    ("v6", "卷 6 · 实验与项目", "用仪器与项目验收把“能跑”推进到“能测量、能交付”。"),
    ("v7", "卷 7 · 交付与资料", "用 AI 结对、手册对账与资料体系把学习与维护变成可持续的工程流程。"),
]

VOL_DIR = {
    "v0": "v0-foundations/",
    "v1": "v1-drivers/",
    "v2": "v2-reliability/",
    "v3": "v3-rtos/",
    "v4": "v4-platforms/",
    "v5": "v5-motion/",
    "v6": "v6-labs-projects/",
    "v7": "v7-delivery/",
}


def load_toc(path: Path = TOC) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 5:
            raise ValueError(f"{path}:{number}: expected 5 columns, got {len(columns)}")
        chapter_id, volume, title, file, platforms = columns
        rows.append(
            {
                "id": chapter_id,
                "volume": volume,
                "title": title,
                "file": file,
                "platforms": [item.strip() for item in platforms.split(",") if item.strip()],
            }
        )
    return rows


def build_manifest(rows: list[dict]) -> dict:
    parts = []
    for volume_id, volume_title, goal in VOLUMES:
        chapters = [
            {
                "id": row["id"],
                "title": row["title"],
                "file": row["file"],
                "status": "planned",
                "platforms": row["platforms"],
            }
            for row in rows
            if row["volume"] == volume_id
        ]
        parts.append({"id": volume_id, "title": volume_title, "goal": goal, "chapters": chapters})
    appendices = [
        {"id": row["id"], "title": row["title"], "file": row["file"], "status": "planned"}
        for row in rows
        if row["volume"] == "ap"
    ]
    return {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "version": VERSION,
        "language": "zh",
        "parts": parts,
        "appendices": appendices,
    }


def validate(manifest: dict, rows: list[dict]) -> list[str]:
    errors = []
    chapter_ids = [chapter["id"] for part in manifest["parts"] for chapter in part["chapters"]]
    appendix_ids = [appendix["id"] for appendix in manifest["appendices"]]
    all_ids = chapter_ids + appendix_ids
    if len(all_ids) != len(set(all_ids)):
        errors.append("duplicate ids across parts and appendices")
    expected = [f"ch{i:02d}" for i in range(1, 47)]
    if chapter_ids != expected:
        errors.append(f"chapter ids must be ch01..ch46 in order, got {chapter_ids[:3]}...{chapter_ids[-1:]}")
    if appendix_ids != [f"ap{x}" for x in "ABCDEF"]:
        errors.append(f"appendix ids must be apA..apF, got {appendix_ids}")
    for row in rows:
        if not row["platforms"]:
            errors.append(f"{row['id']}: empty platforms")
        elif not set(row["platforms"]) <= ALLOWED_PLATFORMS:
            errors.append(f"{row['id']}: unknown platforms {row['platforms']}")
        if row["volume"] == "ap":
            if not row["file"].startswith("appendix/"):
                errors.append(f"{row['id']}: appendix file must live under appendix/")
        elif row["volume"] not in VOL_DIR:
            errors.append(f"{row['id']}: unknown volume {row['volume']}")
        elif not row["file"].startswith(VOL_DIR[row["volume"]]):
            errors.append(f"{row['id']}: file must start with {VOL_DIR[row['volume']]}")
    return errors


def dumps(manifest: dict) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rows = load_toc()
    manifest = build_manifest(rows)
    errors = validate(manifest, rows)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    text = dumps(manifest)
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("docs/manifest.json is stale; run python -m book.manifest --write", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 生成 manifest 并运行测试**

```bash
python -m book.manifest --write
python -m book.manifest --check
python -m unittest discover book/tests -v
```

Expected: `--check` 退出 0；6 个测试 PASS。

- [ ] **Step 6: 提交**

```bash
git add book/__init__.py book/data/toc.tsv book/manifest.py book/tests/test_manifest.py docs/manifest.json
git commit -m "feat(book): add unified manifest and validator (B0)"
```

---

### Task 2: 迁移映射数据与覆盖率校验

**Files:**
- Create: `book/data/mapping.tsv`
- Create: `book/mapping.py`
- Create: `book/tests/test_mapping.py`
- Create: `plans/2026-11-12-merged-book/mapping.json`（由脚本生成）

**Interfaces:**
- Consumes: `book.manifest`（Task 1）、`stm32-book/manifest.json`、`mcu/mcu-book/manifest.json`、`plans/2026-11-11-motor-control/chapters-draft/*.md`。
- Produces: `book.mapping.load_rows() -> list[dict]`；`build(rows) -> dict`；`dumps(mapping) -> str`；`validate(rows, manifest) -> list[str]`；`expected_root_sources()`、`expected_mcu_sources()`、`expected_motor_sources()`；CLI `python -m book.mapping --write|--check`。

- [ ] **Step 1: 写失败测试**

创建 `book/tests/test_mapping.py`：

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import manifest as mf
from book import mapping as mp


class MappingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = mp.load_rows()
        cls.manifest = mf.build_manifest(mf.load_toc())

    def test_total_rows(self):
        self.assertEqual(len(self.rows), 141)

    def test_coverage_clean(self):
        self.assertEqual(mp.validate(self.rows, self.manifest), [])

    def test_duplicate_source_detected(self):
        rows = self.rows + [dict(self.rows[0])]
        errors = mp.validate(rows, self.manifest)
        self.assertTrue(any("duplicate source" in error for error in errors), errors)

    def test_unknown_target_detected(self):
        rows = [dict(row) for row in self.rows]
        rows[0] = {**rows[0], "targets": ["ch99"]}
        errors = mp.validate(rows, self.manifest)
        self.assertTrue(any("unknown target" in error for error in errors), errors)

    def test_every_target_has_source(self):
        used = {target for row in self.rows for target in row["targets"]}
        manifest = self.manifest
        all_ids = {chapter["id"] for part in manifest["parts"] for chapter in part["chapters"]}
        all_ids |= {appendix["id"] for appendix in manifest["appendices"]}
        self.assertEqual(all_ids - used, set())

    def test_committed_mapping_current(self):
        self.assertEqual(mp.MAPPING_JSON.read_text(encoding="utf-8"), mp.dumps(mp.build(self.rows)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover book/tests -v`
Expected: FAIL，`book.mapping` 不存在。

- [ ] **Step 3: 写 `book/data/mapping.tsv`**

四列：`book	source	targets	note`。`targets` 用 `;` 分隔，第一个为主目标（旧 URL 跳转用）。

```text
root	docs/00-如何学习STM32.md	ch46	
root	docs/01-开发环境搭建.md	ch05	
root	docs/02-芯片选型与存储器时钟.md	ch01;ch08	存储器→ch01，时钟→ch08
root	docs/03-GPIO与LED.md	ch09	
root	docs/04-中断与NVIC.md	ch04;ch10	驱动基本功→ch04，NVIC→ch10
root	docs/05-定时器与PWM.md	ch11;ch12	时基→ch11，PWM→ch12
root	docs/06-串口UART.md	ch13	
root	docs/07-I2C总线.md	ch16	
root	docs/08-SPI总线.md	ch16	
root	docs/09-ADC与DAC.md	ch15	
root	docs/10-DMA.md	ch14	
root	docs/11-RTC与看门狗.md	ch11;ch19	RTC→ch11，看门狗→ch19
root	docs/12-Flash与IAP升级.md	ch17	
root	docs/13-CAN总线.md	ch35	
root	docs/14-USB.md	ch35	
root	docs/15-FreeRTOS入门.md	ch21;ch22	入门→ch21，任务→ch22
root	docs/16-低功耗设计.md	ch18	
root	docs/17-调试与性能优化.md	ch20	
root	docs/18-常见问题FAQ.md	ch45	
root	docs/19-项目实战合集.md	ch42	
root	docs/20-学习资源与工具链.md	ch46	
root	docs/21-原理图与实物图鉴.md	ch40	
root	docs/22-仿真实验Wokwi与Renode.md	ch40	
root	docs/23-STM32G0引脚.md	ch28	
root	docs/24-STM32L4引脚.md	ch28	
root	docs/25-STM32H7引脚.md	ch28;ch34	Cache→ch34
root	docs/26-STM32F10x标准外设库SPL.md	ch07	
root	docs/27-网络与协议栈.md	ch33	
root	docs/28-嵌入式系统与RTOS生态.md	ch27	
root	stm32-book/book/A-工程深读.md	apA	
root	stm32-book/book/B-例程索引.md	apB	
root	stm32-book/book/C-习题答案.md	apC	
root	stm32-book/book/D-术语表.md	apD	
root	stm32-book/book/E-参考资料.md	apE	
root	stm32-book/book/F-学习路线收束.md	apF	书稿专有收束页
root	stm32-book/book/F-开源地图.md	apF	
mcu	mcu/docs/c/00-c-in-mcu.md	ch01	
mcu	mcu/docs/c/01-memory-model.md	ch01	
mcu	mcu/docs/c/02-pointer.md	ch01	
mcu	mcu/docs/c/03-volatile.md	ch02	
mcu	mcu/docs/c/04-struct-abi.md	ch03	
mcu	mcu/docs/c/05-func-pointer.md	ch04	
mcu	mcu/docs/c/06-abi-stack.md	ch04	
mcu	mcu/docs/c/07-ub-misra.md	ch02	
mcu	mcu/docs/c/08-framed-protocol.md	ch13	
mcu	mcu/docs/build/00-toolchain.md	ch05	
mcu	mcu/docs/build/01-four-steps.md	ch05	
mcu	mcu/docs/build/02-elf.md	ch05	
mcu	mcu/docs/build/03-linker-script.md	ch06	
mcu	mcu/docs/build/04-startup.md	ch06	
mcu	mcu/docs/build/05-map-size.md	ch06	
mcu	mcu/docs/build/06-flash-debug.md	ch20	
mcu	mcu/docs/build/07-build-system.md	ch07	
mcu	mcu/docs/stm32/00-env.md	ch05	
mcu	mcu/docs/stm32/01-arch.md	ch08	
mcu	mcu/docs/stm32/02-rcc-clock.md	ch08	
mcu	mcu/docs/stm32/03-gpio.md	ch09	
mcu	mcu/docs/stm32/04-nvic-exti.md	ch10	
mcu	mcu/docs/stm32/05-systick.md	ch11	
mcu	mcu/docs/stm32/06-tim.md	ch12	
mcu	mcu/docs/stm32/07-usart.md	ch13	
mcu	mcu/docs/stm32/08-dma.md	ch14	
mcu	mcu/docs/stm32/09-adc.md	ch15	
mcu	mcu/docs/stm32/10-dac.md	ch15	
mcu	mcu/docs/stm32/11-i2c.md	ch16	
mcu	mcu/docs/stm32/12-spi.md	ch16	
mcu	mcu/docs/stm32/13-flash-iap.md	ch17	
mcu	mcu/docs/stm32/14-pwr.md	ch18	
mcu	mcu/docs/stm32/15-spl-anatomy.md	ch07	
mcu	mcu/docs/stm32/16-debug-hardfault.md	ch19	
mcu	mcu/docs/stm32/17-watchdog-reset.md	ch19	
mcu	mcu/docs/rtos/freertos/00-why-rtos.md	ch21	
mcu	mcu/docs/rtos/freertos/01-task-tcb.md	ch22	
mcu	mcu/docs/rtos/freertos/02-context-switch.md	ch23	
mcu	mcu/docs/rtos/freertos/03-scheduler.md	ch22	
mcu	mcu/docs/rtos/freertos/04-queue.md	ch24	
mcu	mcu/docs/rtos/freertos/05-sem-mutex.md	ch24	
mcu	mcu/docs/rtos/freertos/06-notify-event-timer.md	ch24	
mcu	mcu/docs/rtos/freertos/07-heap.md	ch25	
mcu	mcu/docs/rtos/freertos/08-port-f407.md	ch23	
mcu	mcu/docs/rtos/rtthread/00-arch.md	ch23	
mcu	mcu/docs/rtos/rtthread/01-thread-sched.md	ch22	
mcu	mcu/docs/rtos/rtthread/02-ipc.md	ch24	
mcu	mcu/docs/rtos/rtthread/03-mem.md	ch25	
mcu	mcu/docs/rtos/rtthread/04-device.md	ch26	
mcu	mcu/docs/rtos/rtthread/05-finsh.md	ch26	
mcu	mcu/docs/rtos/rtthread/06-env-menuconfig.md	ch26	
mcu	mcu/docs/rtos/rtthread/07-port-f407.md	ch23	
mcu	mcu/docs/rtos/compare/00-side-by-side.md	ch27	
mcu	mcu/docs/rtos/compare/01-choose.md	ch27	
mcu	mcu/docs/esp32/00-env.md	ch30	
mcu	mcu/docs/esp32/01-arch-boot.md	ch30	
mcu	mcu/docs/esp32/02-gpio-matrix.md	ch31	
mcu	mcu/docs/esp32/03-idf-anatomy.md	ch30	
mcu	mcu/docs/esp32/04-irq-dualcore.md	ch10;ch34	双核→ch10，Cache→ch34
mcu	mcu/docs/esp32/05-uart-driver.md	ch31	
mcu	mcu/docs/esp32/06-spi-i2c-driver.md	ch31	
mcu	mcu/docs/esp32/07-timer-ledc.md	ch31	
mcu	mcu/docs/esp32/08-wifi.md	ch32	
mcu	mcu/docs/esp32/09-bt-espnow.md	ch32	
mcu	mcu/docs/esp32/10-flash-nvs-ota.md	ch17	
mcu	mcu/docs/esp32/11-lowpower.md	ch18	
mcu	mcu/docs/esp32/12-audio-path.md	ch31	
mcu	mcu/docs/esp32/13-watchdog-health.md	ch19	
mcu	mcu/docs/gd32/00-env.md	ch29	
mcu	mcu/docs/gd32/01-rcu-clock.md	ch29	
mcu	mcu/docs/gd32/02-gpio-af.md	ch29	
mcu	mcu/docs/gd32/03-usart.md	ch29	
mcu	mcu/docs/gd32/04-periph-diff.md	ch28	
mcu	mcu/docs/gd32/05-riscv-toolchain.md	ch29	
mcu	mcu/docs/gd32/06-clic-irq.md	ch29	
mcu	mcu/docs/gd32/07-rcu-108m.md	ch29	
mcu	mcu/docs/gd32/08-mtime-delay.md	ch29	
mcu	mcu/docs/gd32/09-gpio-minimal.md	ch29	
mcu	mcu/docs/lab/e01-blink.md	ch09;ch40	实验拆入ch09，方法→ch40
mcu	mcu/docs/lab/e02-logic-uart.md	ch13;ch40	
mcu	mcu/docs/lab/e03-scope-pwm.md	ch12;ch40	
mcu	mcu/docs/lab/e04-priority-inversion.md	ch24;ch40	
mcu	mcu/docs/lab/e05-i2c-eeprom.md	ch16;ch40	
mcu	mcu/docs/lab/e06-lowpower-current.md	ch18;ch40	
mcu	mcu/docs/lab/e07-qmi8658.md	ch16;ch40	
mcu	mcu/docs/lab/e08-audio-play.md	ch31;ch40	
mcu	mcu/docs/projects/01-f407-logger.md	ch41	
mcu	mcu/docs/projects/02-s3-logger.md	ch41	
mcu	mcu/docs/ai/00-pair-not-ghost.md	ch43	
mcu	mcu/docs/ai/01-prompt-patterns.md	ch43	
mcu	mcu/docs/ai/02-manual-reconciliation.md	ch44	
mcu	mcu/docs/ai/03-toolflow-mcp.md	ch43	
mcu	mcu/docs/ai/04-hallucination-defense.md	ch44	
mcu	mcu/docs/ai/05-this-book-pipeline.md	ch44	
mcu	mcu-book/book/A-工程深读.md	apA	
mcu	mcu-book/book/B-例程索引.md	apB	
mcu	mcu-book/book/C-习题答案.md	apC	
mcu	mcu-book/book/D-术语表.md	apD	
mcu	mcu-book/book/E-参考资料.md	apE	
mcu	mcu-book/book/F-常见问题.md	ch45	
mcu	mcu-book/book/G-开源地图.md	apF	
motor	plans/2026-11-11-motor-control/chapters-draft/29-电机驱动与供电.md	ch36	
motor	plans/2026-11-11-motor-control/chapters-draft/30-直流电机开环调速.md	ch37	
motor	plans/2026-11-11-motor-control/chapters-draft/31-编码器与转速测量.md	ch38	
motor	plans/2026-11-11-motor-control/chapters-draft/32-直流电机速度闭环.md	ch39	
```

- [ ] **Step 4: 写 `book/mapping.py`**

```python
"""Build and validate the source-to-chapter mapping for the merged book."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPING_TSV = ROOT / "book" / "data" / "mapping.tsv"
MAPPING_JSON = ROOT / "plans" / "2026-11-12-merged-book" / "mapping.json"


def load_rows(path: Path = MAPPING_TSV) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 4:
            raise ValueError(f"{path}:{number}: expected 4 columns, got {len(columns)}")
        book, source, targets, note = columns
        rows.append(
            {
                "book": book,
                "source": source,
                "targets": [target for target in targets.split(";") if target],
                "note": note,
            }
        )
    return rows


def build(rows: list[dict]) -> dict:
    return {
        "version": 1,
        "policy": {"english": "archive", "primary_target": "first"},
        "sources": rows,
    }


def dumps(mapping: dict) -> str:
    return json.dumps(mapping, ensure_ascii=False, indent=2) + "\n"


def expected_root_sources() -> list[str]:
    manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
    sources = [f"docs/{name}" for part in manifest["parts"] for name in part["files"]]
    sources += [f"stm32-book/book/{name}" for name in manifest["appendices"]]
    sources.append("stm32-book/book/F-学习路线收束.md")
    return sources


def expected_mcu_sources() -> list[str]:
    manifest = json.loads((ROOT / "mcu" / "mcu-book" / "manifest.json").read_text(encoding="utf-8"))
    sources = [f"mcu/docs/{name}" for part in manifest["parts"] for name in part["files"]]
    sources += [f"mcu/mcu-book/book/{name}" for name in manifest["appendices"]]
    return sources


def expected_motor_sources() -> list[str]:
    drafts = ROOT / "plans" / "2026-11-11-motor-control" / "chapters-draft"
    return sorted(path.relative_to(ROOT).as_posix() for path in drafts.glob("*.md"))


def validate(rows: list[dict], manifest: dict) -> list[str]:
    errors = []
    seen = set()
    for row in rows:
        key = (row["book"], row["source"])
        if key in seen:
            errors.append(f"duplicate source: {row['book']}:{row['source']}")
        seen.add(key)
    target_ids = {chapter["id"] for part in manifest["parts"] for chapter in part["chapters"]}
    target_ids |= {appendix["id"] for appendix in manifest["appendices"]}
    for row in rows:
        if not row["targets"]:
            errors.append(f"empty targets: {row['source']}")
        for target in row["targets"]:
            if target not in target_ids:
                errors.append(f"unknown target {target} for {row['source']}")
        if not (ROOT / row["source"]).exists():
            errors.append(f"missing source file: {row['source']}")
    for book, expected in (
        ("root", expected_root_sources()),
        ("mcu", expected_mcu_sources()),
        ("motor", expected_motor_sources()),
    ):
        actual = {row["source"] for row in rows if row["book"] == book}
        for source in sorted(set(expected) - actual):
            errors.append(f"unmapped {book} source: {source}")
        for source in sorted(actual - set(expected)):
            errors.append(f"unexpected {book} source: {source}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    from book import manifest as manifest_module

    rows = load_rows()
    manifest = manifest_module.build_manifest(manifest_module.load_toc())
    errors = validate(rows, manifest)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    text = dumps(build(rows))
    if args.write:
        MAPPING_JSON.parent.mkdir(parents=True, exist_ok=True)
        MAPPING_JSON.write_text(text, encoding="utf-8")
    if args.check:
        current = MAPPING_JSON.read_text(encoding="utf-8") if MAPPING_JSON.exists() else ""
        if current != text:
            print("mapping.json is stale; run python -m book.mapping --write", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 生成映射并运行测试**

```bash
python -m book.mapping --write
python -m book.mapping --check
python -m unittest discover book/tests -v
```

Expected: 映射生成成功；`--check` 退出 0；12 个测试全部 PASS。

- [ ] **Step 6: 提交**

```bash
git add book/data/mapping.tsv book/mapping.py book/tests/test_mapping.py plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(book): add source mapping and coverage validator (B0)"
```

---

### Task 3: 章节契约检查器与模板

**Files:**
- Create: `book/contracts.py`
- Create: `book/data/chapter-template.md`
- Create: `book/tests/test_contracts.py`
- Create: `book/tests/fixtures/valid-chapter.md`
- Create: `book/tests/fixtures/invalid-missing-compass.md`
- Create: `book/tests/fixtures/invalid-platform.md`

**Interfaces:**
- Consumes: 无（纯文件检查）。
- Produces: `book.contracts.REQUIRED_COMPASS`、`ALLOWED_PLATFORMS`；`split_frontmatter(text) -> tuple[dict, str]`；`parse_list(value) -> list[str]`；`validate_chapter_file(path) -> list[str]`。B1–B4 每章验收调用该函数，返回空列表才算通过。

- [ ] **Step 1: 写失败测试与 fixtures**

`book/tests/fixtures/valid-chapter.md`：

```markdown
---
title: "GPIO"
platforms: [f407, f103]
---

# GPIO

## 本章罗盘

- **问题**：为什么同一个引脚配置在 F103 与 F407 上行为不同？
- **交付**：用寄存器与 HAL 各点亮一次 LED，并读出 IDR。
- **边界**：只覆盖推挽输出；开漏与复用功能留给下一节。
- **依据锚点**：RM0008 §9；RM0090 §8；S3；03。

## 先做出来

略。
```

`book/tests/fixtures/invalid-missing-compass.md`：

```markdown
---
title: "缺少罗盘"
platforms: [generic]
---

# 缺少罗盘

没有本章罗盘。
```

`book/tests/fixtures/invalid-platform.md`：

```markdown
---
title: "平台错误"
platforms: [esp8266]
---

# 平台错误

## 本章罗盘

- **问题**：x
- **交付**：x
- **边界**：x
- **依据锚点**：x
```

`book/tests/test_contracts.py`：

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import contracts as c

FIXTURES = Path(__file__).parent / "fixtures"


class ContractsTest(unittest.TestCase):
    def test_valid_fixture_passes(self):
        self.assertEqual(c.validate_chapter_file(FIXTURES / "valid-chapter.md"), [])

    def test_missing_compass_detected(self):
        errors = c.validate_chapter_file(FIXTURES / "invalid-missing-compass.md")
        self.assertTrue(any("本章罗盘" in error for error in errors), errors)

    def test_unknown_platform_detected(self):
        errors = c.validate_chapter_file(FIXTURES / "invalid-platform.md")
        self.assertTrue(any("platform" in error for error in errors), errors)

    def test_missing_file_detected(self):
        errors = c.validate_chapter_file(FIXTURES / "does-not-exist.md")
        self.assertTrue(any("missing file" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover book/tests -v`
Expected: FAIL，`book.contracts` 不存在。

- [ ] **Step 3: 写模板与实现**

`book/data/chapter-template.md`：

```markdown
---
title: "章标题"
platforms: [f407, f103]
---

# 章标题

## 本章罗盘

- **问题**：读者带着什么具体问题进入本章。
- **交付**：本章先做出什么最小可见结果。
- **边界**：哪些结论不适用于哪些型号、条件或场景。
- **依据锚点**：手册章节号、来源 ID 与对应旧章节号。

## 先做出来

最小可运行步骤与预期观察结果。

## 机制

寄存器、时序、数据结构或内核源码的逐层解释。

## 测量与证据

波形、寄存器读回、日志或仪器读数，以及如何判断“真的会了”。

## 失败分支

常见误判、最短排查路径与迁移边界。

## 离开检查

读者离开本章前应能回答的问题。
```

`book/contracts.py`：

```python
"""Chapter contract checks shared by every migration batch (B1-B4)."""

from __future__ import annotations

from pathlib import Path

REQUIRED_COMPASS = ("问题", "交付", "边界", "依据锚点")
ALLOWED_PLATFORMS = {"f103", "f407", "gd32", "esp32", "generic"}


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip().strip("\"'") for item in value.split(",") if item.strip()]


def validate_chapter_file(path: Path) -> list[str]:
    path = Path(path)
    if not path.exists():
        return [f"missing file: {path}"]
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    if not meta.get("title"):
        errors.append("frontmatter missing title")
    platforms = parse_list(meta.get("platforms", ""))
    if not platforms:
        errors.append("frontmatter missing platforms")
    elif not set(platforms) <= ALLOWED_PLATFORMS:
        errors.append(f"unknown platform(s): {sorted(set(platforms) - ALLOWED_PLATFORMS)}")
    if "## 本章罗盘" not in body:
        errors.append("missing section: ## 本章罗盘")
    for label in REQUIRED_COMPASS:
        if f"**{label}**" not in body:
            errors.append(f"compass missing label: {label}")
    return errors
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover book/tests -v`
Expected: 16 个测试全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add book/contracts.py book/data/chapter-template.md book/tests/test_contracts.py book/tests/fixtures/valid-chapter.md book/tests/fixtures/invalid-missing-compass.md book/tests/fixtures/invalid-platform.md
git commit -m "feat(book): add chapter contract checker and template (B0)"
```

---

### Task 4: 旧 URL 跳转存根生成器

**Files:**
- Create: `scripts/legacy-redirects.mjs`
- Create: `scripts/tests/legacy-redirects.test.mjs`

**Interfaces:**
- Consumes: `plans/2026-11-12-merged-book/mapping.json`（Task 2）、`docs/manifest.json`（Task 1）。
- Produces: `oldUrlFor(source) -> str`、`targetUrlFor(file) -> str`、`generate({mappingPath, manifestPath, outDir}) -> Promise<number>`；CLI `node scripts/legacy-redirects.mjs --mapping … --manifest … --out …`。

- [ ] **Step 1: 写失败测试**

`scripts/tests/legacy-redirects.test.mjs`：

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { generate, oldUrlFor } from '../legacy-redirects.mjs'

const ROOT = fileURLToPath(new URL('../../', import.meta.url))
const mappingPath = join(ROOT, 'plans/2026-11-12-merged-book/mapping.json')
const manifestPath = join(ROOT, 'docs/manifest.json')

test('old URL keeps mcu prefix and .html suffix', () => {
  assert.equal(oldUrlFor('mcu/docs/stm32/03-gpio.md'), '/mcu/stm32/03-gpio.html')
})

test('generates one stub per mcu chapter with canonical target', async () => {
  const outDir = await mkdtemp(join(tmpdir(), 'legacy-redirects-'))
  try {
    const count = await generate({ mappingPath, manifestPath, outDir })
    assert.equal(count, 94)
    const html = await readFile(join(outDir, 'mcu/stm32/03-gpio.html'), 'utf8')
    assert.match(html, /rel="canonical" href="https:\/\/zhuguang-zfg\.github\.io\/STM32\/v1-drivers\/09-gpio\.html"/)
    assert.match(html, /http-equiv="refresh" content="0; url=\/STM32\/v1-drivers\/09-gpio\.html"/)
    assert.match(html, /location\.replace\("\/STM32\/v1-drivers\/09-gpio\.html" \+ location\.hash\)/)
  } finally {
    await rm(outDir, { recursive: true, force: true })
  }
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test scripts/tests/legacy-redirects.test.mjs`
Expected: FAIL，`Cannot find module '../legacy-redirects.mjs'`。

- [ ] **Step 3: 写实现**

`scripts/legacy-redirects.mjs`：

```js
#!/usr/bin/env node
/**
 * 从 mapping.json 生成旧 /mcu/** 路径的跳转存根。
 * 约定：每个源文件的主目标 = targets[0]；旧 URL 保留 mcu 前缀与 .html 后缀。
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HOST = 'https://zhuguang-zfg.github.io'
const NEW_BASE = '/STM32/'
const OLD_BASE = '/mcu/'

export function oldUrlFor(source) {
  if (!source.startsWith('mcu/docs/')) {
    throw new Error(`not an mcu docs source: ${source}`)
  }
  return OLD_BASE + source.slice('mcu/docs/'.length).replace(/\.md$/, '.html')
}

export function targetUrlFor(file) {
  return NEW_BASE + file.replace(/\.md$/, '.html')
}

function stub(target) {
  const canonical = HOST + target
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>页面已迁移</title>
<link rel="canonical" href="${canonical}">
<meta http-equiv="refresh" content="0; url=${target}">
</head>
<body>
<p>本页已迁移到 <a href="${target}">${target}</a>。</p>
<script>location.replace(${JSON.stringify(target)} + location.hash);</script>
</body>
</html>
`
}

export async function generate({ mappingPath, manifestPath, outDir }) {
  const mapping = JSON.parse(await readFile(mappingPath, 'utf8'))
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
  const files = new Map()
  for (const part of manifest.parts) {
    for (const chapter of part.chapters) {
      files.set(chapter.id, chapter.file)
    }
  }
  let count = 0
  for (const row of mapping.sources) {
    if (row.book !== 'mcu') continue
    const target = files.get(row.targets[0])
    if (!target) {
      throw new Error(`unknown target ${row.targets[0]} for ${row.source}`)
    }
    const outPath = join(outDir, oldUrlFor(row.source).slice(1))
    await mkdir(dirname(outPath), { recursive: true })
    await writeFile(outPath, stub(targetUrlFor(target)), 'utf8')
    count += 1
  }
  return count
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]
if (isMain) {
  const args = new Map()
  for (let index = 2; index < process.argv.length; index += 2) {
    args.set(process.argv[index], process.argv[index + 1])
  }
  const count = await generate({
    mappingPath: args.get('--mapping'),
    manifestPath: args.get('--manifest'),
    outDir: args.get('--out'),
  })
  console.log(`generated ${count} legacy redirect stubs`)
}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
node --test scripts/tests/legacy-redirects.test.mjs
```

Expected: 2 个测试 PASS。

- [ ] **Step 5: 本地生成一次存根并抽查**

```bash
node scripts/legacy-redirects.mjs --mapping plans/2026-11-12-merged-book/mapping.json --manifest docs/manifest.json --out .temp/legacy-redirects
cat .temp/legacy-redirects/mcu/stm32/03-gpio.html
```

Expected: 输出 `generated 94 legacy redirect stubs`；HTML 含 canonical 与 refresh。

- [ ] **Step 6: 提交**

```bash
git add scripts/legacy-redirects.mjs scripts/tests/legacy-redirects.test.mjs
git commit -m "feat(scripts): generate legacy /mcu URL redirect stubs (B0)"
```

---

### Task 5: CI 接入与批次记录

**Files:**
- Create: `.github/workflows/merge-check.yml`
- Create: `plans/2026-11-12-merged-book/README.md`
- Create: `plans/2026-11-12-merged-book/evidence/b0-local.md`

**Interfaces:**
- Consumes: Task 1–4 的全部 CLI 与测试。
- Produces: CI 门 `merge-check`；批次状态与命令记录，供 B1–B5 复用。

- [ ] **Step 1: 写 CI workflow**

`.github/workflows/merge-check.yml`：

```yaml
name: Merge Check

on:
  pull_request:
    paths:
      - 'book/**'
      - 'docs/**'
      - 'plans/2026-11-12-merged-book/**'
      - 'scripts/legacy-redirects.mjs'
      - 'scripts/tests/**'
      - 'stm32-book/manifest.json'
      - 'mcu/mcu-book/manifest.json'
  push:
    branches: [main]
    paths:
      - 'book/**'
      - 'docs/**'
      - 'plans/2026-11-12-merged-book/**'
      - 'scripts/legacy-redirects.mjs'
      - 'scripts/tests/**'
      - 'stm32-book/manifest.json'
      - 'mcu/mcu-book/manifest.json'
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: merge-check-${{ github.ref }}
  cancel-in-progress: true

jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Check out repository
        uses: actions/checkout@v7
      - name: Set up Python
        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
        with:
          python-version: "3.13"
      - name: Run book checks
        run: |
          python -m book.manifest --check
          python -m book.mapping --check
          python -m unittest discover book/tests -v
      - name: Set up Node
        uses: actions/setup-node@v7
        with:
          node-version: "20"
      - name: Run redirect generator tests
        run: node --test scripts/tests/legacy-redirects.test.mjs
```

- [ ] **Step 2: 写批次 README**

`plans/2026-11-12-merged-book/README.md`：

```markdown
# 双书合并执行记录

设计规格：[docs/superpowers/specs/2026-11-12-merged-book-design.md](../../docs/superpowers/specs/2026-11-12-merged-book-design.md)

## 批次状态

| 批次 | 内容 | 状态 |
| --- | --- | --- |
| B0 | manifest、mapping、契约检查器、跳转存根、CI 门 | 本批完成（本地） |
| B1 | 卷 0–1（17 章）改写 | 待开始 |
| B2 | 卷 2–3（10 章） | 待开始 |
| B3 | 卷 4–5（12 章 + motor 合流） | 待开始 |
| B4 | 卷 6–7 + 6 附录 | 待开始 |
| B5 | `/STM32/` 切换、旧链归档 | 待开始；需发布指令 |

## 本批校验命令

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
node --test scripts/tests/legacy-redirects.test.mjs
```

## 数据文件

- `book/data/toc.tsv`：46 章 + 6 附录的目录数据。
- `book/data/mapping.tsv`：两书 123 章 + 附录 + motor 草稿的逐文件去向。
- `docs/manifest.json`、`mapping.json`：由脚本生成，不手工编辑。

## 说明

- 英文版策略固定为 `archive`，B5 删除前打 tag。
- 旧 URL 跳转的站点级页面（guide/reference 等）在 B5 扩展，本批只覆盖 94 个 MCU 章节。
```

- [ ] **Step 3: 本地运行完整校验**

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
node --test scripts/tests/legacy-redirects.test.mjs
```

Expected: 全部退出 0；unittest 16 个 PASS；node 2 个 PASS。

- [ ] **Step 4: 写本地证据**

`plans/2026-11-12-merged-book/evidence/b0-local.md` 记录日期、commit SHA、命令、退出码与测试计数：

```markdown
# B0 本地验收证据

- 日期：2026-11-12
- 分支：feat/merged-book-b0
- commit：`<git rev-parse HEAD>`
- 环境：Windows + Git Bash；Python 3.13；Node 20

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m book.manifest --check` | 0 | manifest 与 toc.tsv 一致 |
| `python -m book.mapping --check` | 0 | 141 行映射覆盖全部源 |
| `python -m unittest discover book/tests -v` | 0 | 16 passed |
| `node --test scripts/tests/legacy-redirects.test.mjs` | 0 | 2 passed；94 存根 |

未验证：CI 远程运行结果（本批只做本地；推送需另行授权）。
```

- [ ] **Step 5: 确认旧树零改动**

```bash
git status --porcelain=v1
git diff --stat HEAD~4 -- docs/00-28*.md docs/en stm32-book mcu/mcu-book mcu/docs
```

Expected: `git status` 只显示新增文件；`git diff` 为空（旧书与旧站无改动）。

- [ ] **Step 6: 提交**

```bash
git add .github/workflows/merge-check.yml plans/2026-11-12-merged-book/README.md plans/2026-11-12-merged-book/evidence/b0-local.md
git commit -m "chore(ci): wire merge-check gate and B0 evidence (B0)"
```

---

## 后续计划拆分（不在本计划内）

| 计划 | 范围 | 依赖 |
| --- | --- | --- |
| B1 | 卷 0–1（ch01–ch17）逐章改写、资产与锚点迁移、`book/build_html.py` 真实渲染 | B0 |
| B2 | 卷 2–3（ch18–ch27） | B1 |
| B3 | 卷 4–5（ch28–ch39）含 motor 合流与数值断言迁移 | B2 |
| B4 | 卷 6–7 + 6 附录（ch40–ch46 + apA–apF）与 HTML/PDF/EPUB 契约 | B3 |
| B5 | base 切 `/STM32/`、站点级跳转、CI/部署收敛、删旧树、英文归档 | B4 + 发布指令 |

每批开始前用 `superpowers:writing-plans` 单独成文；本计划只锁定 B0 的接口与数据契约。

## Self-Review 记录

- Spec 覆盖：B0 行的 manifest、mapping、构建器底座（契约检查器）、跳转生成器、CI 门均有对应 Task；旧书/旧站零改动由 Task 5 Step 5 验证。
- 占位符扫描：无 TBD/TODO；所有数据文件与代码块为完整内容。
- 类型一致性：`mapping.json` 的 `sources[].targets`、manifest 的 `parts[].chapters[].file` 与跳转生成器读取字段一致；`validate_chapter_file` 的返回类型在 Task 3 测试与后续批次中统一为 `list[str]`。
- 已知边界：B0 只生成 94 个 MCU 章节存根；站点级页面跳转、base 切换与构建器完整能力按计划拆分到 B5/B1。
