# 全书版式统一与首批配图补强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在活动样式面上落地 `fig-s/m/l` 图尺寸分档与版式基线，并为 5 个目标章节补首批 Handraw 机制图，使每章 `visual_anchor_deficit` 与 `max_visual_gap_chars` 相对基线只降不升。

**Architecture:** 薄片交付。先固化审计基线与阈值测试骨架，再只改 `book/print_css.py` + `docs/.vitepress/theme/style.css` 增加尺寸档位（默认 M = 现状），再用现有 Handraw 发布链为一个试点章补图并验证锚点增加，最后扩到 5 章并跑窄门/印刷布局审计。所有图为 Handraw 原理示意，引用走现有 `<figure class="book-figure">`/Markdown 图片包装；L 档只在 landscape 且受 170mm 块高预算约束。

**Tech Stack:** Python 3.13（book 构建/测试）、Node/VitePress（docs:build）、Playwright Chromium（Handraw render / print PDF）、unittest、PyMuPDF（pdf_audit/layout）。

**Spec:** `docs/superpowers/specs/2026-11-26-book-visual-layout.md` — 计划从 spec 推导，执行者同时读 spec 与 plan。

## Global Constraints

- 只改活动面：`book/print_css.py`、`docs/.vitepress/theme/style.css`；**不改** `book/print/book-print.css`（dead legacy）。
- 视口契约字面值不变：`table-layout: fixed`、`p:has(img) { text-indent: 0; }`、`code, a { overflow-wrap: anywhere; }`、`width: 176mm`、`font-size: 10.2pt` body 基线不改。
- `CoverCopyTests` pin 的封面文案字面值不变：`原理讲解 · 工程示例 · 实验指南`。
- 图尺寸档位：S = 72mm print / 28rem site；M = 现状 150mm print / `min(100%, 42rem)` site；L = landscape only，figure 块高 ≤170mm（210−21−19），图片 `max-height` ≤150mm（或 PDF 实测更小值），禁止 190mm。
- 默认无档位类 = M；现有图片行为不变。`figure.landscape` 既有语义不改。
- 审计锚点只认 `<figure>`/`<p align=center>`/`<img>`/`![]()`（`tools/audit_book.py:extract_visual_anchors`）；`<!-- stick-scene -->` 不计数。
- 新增图必须：`tools/handraw_track/fig_*.py` 有确定性生成函数、`assets/illustrations/staged/*.svg` 有源、`docs/public/images/*.png` 发布、`publish_staged.py --check` 绿、图注含四要素 + `原理示意/非实拍`；不伪造实拍，不复制参考书图。
- `book.md_links` 当前已知 20 个问题属 #179/#180/#183；本批不得新增。gate 接线仍是 PR body 提案。
- 验证命令不存在：`npm run perf:budget`、`npm run test:browser`；不得引用。缺 `merged-book.pdf` 不得记绿。
- 文件编辑用 `edit`/`write`；Markdown 用中文 prose；不加 reviewer-facing wording；`tools/slop_lint.py` 干净。

## Review Focus

- Figure class 被站点 markdown 包装吞掉：作者写 `<figure class="book-figure fig-s">` 时，build_html/print 路径应保留类名；站点路径若经 markdown-it 包装，`fig-s/m/l` 不能丢失。用测试钉住。
- L 档在非 landscape 页面溢出：L 必须同时带 `landscape` 语义并受 170mm 块预算；仅 CSS 字符串测试不够，布局变更必须跑真实 PDF + `audit_pdf_layout.py`。
- 阈值测试把“当前缺口”钉死导致合法重排失败：阈值应是上限（只许下降/持平），不是等于；基线来自当前 audit JSON 快照。
- 新图 PNG 无 staged SVG 源：`test_figure_sources.py` 会失败；计划要求先落 fig 模块 + staged SVG，再发布 PNG，再引用 Markdown。
- 审计计数不涨：插图若写成 stick-scene/非 figure HTML 形式，`audit_book.py` 不认；每张新增图用 `python tools/audit_book.py --format json` 验证目标章锚点增量。

## File Structure

- `book/print_css.py` — 印刷样式唯一活动源；加 `fig-s/m/l` 尺寸规则，保持 176mm/视口契约。
- `docs/.vitepress/theme/style.css` — 站点样式；加 `.vp-doc figure.book-figure.fig-s/m/l` 尺寸规则。
- `book/tests/test_print_sections.py` — 既有视口/封面契约；扩展断言 fig 档位存在且默认行为不变。
- `book/tests/test_book_audit_thresholds.py` — **新建**，提案 A：冻结 5 章 deficit/gap 与全书 anchors/below_target/photos 上限。
- `tools/handraw_track/fig_reading.py`（或按需新建 `fig_visual_layout.py`）— 新增 5 章 Handraw 机制图生成函数；注册进 `publish_staged.py`。
- `tools/handraw_track/publish_staged.py` — 仅在新增模块时把模块名加入 `MODULES`。
- `assets/illustrations/staged/<stem>.svg` — 生成的 SVG 源（tracked）。
- `docs/public/images/<stem>.png` — 发布 PNG（tracked）。
- `docs/v0-foundations/06-linker-startup-map.md`、`docs/v1-drivers/11-systick-timebase-rtc.md`、`docs/v3-rtos/26-device-framework-shell.md`、`docs/v7-delivery/46-resources-roadmap-open-source.md`、`docs/appendix/D-glossary.md` — 插入图引用与四要素图注。
- `.temp/audit_book.baseline.json` — S1 基线快照（gitignored，PR 附件/记录用）。

---

### Task 1: 基线快照与审计阈值测试骨架（S1/S5-prep）

**Files:**
- Create: `.temp/audit_book.baseline.json` (gitignored artifact, 可选留档；阈值以测试常量为准)
- Create: `book/tests/test_book_audit_thresholds.py`
- Read: `tools/audit_book.py`, `.temp/audit_book.current.json` (generate if absent)

**Interfaces:**
- Produces: baseline numbers used by threshold tests; `python -m unittest book.tests.test_book_audit_thresholds` passes on current tree.
- Consumes: `tools/audit_book.py` JSON schema — `summary.zh.pdf_visual_anchors`, `summary.zh.chapters_below_target`, `summary.zh.chapters_with_photos`; per chapter `chapters[].id`, `chapters[].zh.visual_anchor_deficit`, `chapters[].zh.max_visual_gap_chars`.

- [ ] **Step 1: Write the threshold test**

```python
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / ".temp" / "audit_book.current.json"

# Baseline captured 2026-11-26 from tools/audit_book.py --format json.
# Ceilings: values may improve (deficit/gap/below_target down; anchors/photos up), never regress.
BASELINE = {
    "summary_zh": {"pdf_visual_anchors": 345, "chapters_below_target": 21, "chapters_with_photos": 0},
    "chapters": {
        "ch06": {"visual_anchor_deficit": 3, "max_visual_gap_chars": 5826},
        "ch11": {"visual_anchor_deficit": 5, "max_visual_gap_chars": 4829},
        "ch26": {"visual_anchor_deficit": 3, "max_visual_gap_chars": 5313},
        "ch46": {"visual_anchor_deficit": 4, "max_visual_gap_chars": 8846},
        "apD":  {"visual_anchor_deficit": 5, "max_visual_gap_chars": 5954},
    },
}


class BookAuditThresholdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUDIT.exists():
            raise unittest.SkipTest("missing .temp/audit_book.current.json; run: python tools/audit_book.py --format json --write .temp/audit_book.current.json")
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))
        cls.summary_zh = cls.data["summary"]["zh"]
        cls.by_id = {c["id"]: c["zh"] for c in cls.data["chapters"]}

    def test_global_metrics_do_not_regress(self):
        base = BASELINE["summary_zh"]
        self.assertGreaterEqual(self.summary_zh["pdf_visual_anchors"], base["pdf_visual_anchors"])
        self.assertLessEqual(self.summary_zh["chapters_below_target"], base["chapters_below_target"])
        self.assertGreaterEqual(self.summary_zh["chapters_with_photos"], base["chapters_with_photos"])

    def test_target_chapters_do_not_regress(self):
        for cid, base in BASELINE["chapters"].items():
            self.assertIn(cid, self.by_id, cid)
            got = self.by_id[cid]
            self.assertLessEqual(got["visual_anchor_deficit"], base["visual_anchor_deficit"], cid)
            self.assertLessEqual(got["max_visual_gap_chars"], base["max_visual_gap_chars"], cid)
```

- [ ] **Step 2: Run test to verify behavior before baseline file exists**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -m unittest book.tests.test_book_audit_thresholds -v`
Expected: SKIP "missing .temp/audit_book.current.json..." if absent; PASS if audit json already present and metrics are at/above baseline.

- [ ] **Step 3: Generate audit JSON**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python tools/audit_book.py --format json --write .temp/audit_book.current.json`
Expected: exit 0; `summary.zh.pdf_visual_anchors >= 345`, `chapters_below_target <= 21`, `chapters_with_photos >= 0`.

- [ ] **Step 4: Run threshold test**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -m unittest book.tests.test_book_audit_thresholds -v`
Expected: PASS (2 tests). If a number drifted, update BASELINE only after confirming improvement or an explained pre-existing state; never raise a deficit/gap ceiling or lower an anchor/photo floor.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add book/tests/test_book_audit_thresholds.py docs/superpowers/plans/2026-11-26-book-visual-layout.md docs/superpowers/specs/2026-11-26-book-visual-layout.md
git commit -m "test(book): add audit threshold baseline for visual layout work"
```

Expected: commit created; `.temp/audit_book.current.json` remains untracked. Test skips cleanly when the snapshot is absent.

### Task 2: Print CSS 尺寸档位（S2-print）

**Files:**
- Modify: `book/print_css.py` (figure sizing block near `figure img, figure svg { max-height: 150mm ... }`)
- Modify: `book/tests/test_print_sections.py`

**Interfaces:**
- Produces: `.book-figure.fig-s img/svg { max-height: 72mm }`; `.book-figure.fig-m` explicit 150mm (same as default M); `.book-figure.fig-l.landscape` block `max-height: 170mm; overflow: hidden;` and image cap 150mm.
- Consumes: existing `build_css()` contract; all existing `PrintCssTests` remain green.

- [ ] **Step 1: Extend PrintCssTests with failing fig-tier assertions**

Add to `PrintCssTests` in `book/tests/test_print_sections.py`:

```python
    def test_figure_size_tiers_default_m_and_bounded_l(self):
        css = build_css()
        # Default/M remains the existing 150mm cap.
        self.assertIn(
            "figure img,\n    figure svg {\n      max-height: 150mm;\n      max-width: 100%;\n      width: auto;\n    }",
            css,
        )
        # S tier.
        self.assertIn("figure.book-figure.fig-s img,", css)
        self.assertIn("max-height: 72mm;", css)
        # M tier explicit (same cap as default; class makes intent visible).
        self.assertIn("figure.book-figure.fig-m img,", css)
        # L tier: landscape only, block budget 170mm, image cap 150mm, never 190mm.
        self.assertIn("figure.book-figure.fig-l.landscape {", css)
        self.assertIn("max-height: 170mm;", css)
        self.assertRegex(
            css,
            r"figure\.book-figure\.fig-l\.landscape img,\s*figure\.book-figure\.fig-l\.landscape svg \{(?s:.*?)max-height: 150mm;",
        )
        self.assertNotIn("max-height: 190mm", css)
        # Existing landscape semantics preserved.
        self.assertIn("@page plate-landscape { size: A4 landscape; margin: 21mm 17mm 19mm; }", css)
        self.assertIn("figure.landscape { page: plate-landscape; break-before: page;", css)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -m unittest book.tests.test_print_sections.PrintCssTests.test_figure_size_tiers_default_m_and_bounded_l -v`
Expected: FAIL — missing `fig-s` / `fig-l.landscape` / `170mm`.

- [ ] **Step 3: Implement minimal CSS tiers in `book/print_css.py`**

Insert after the existing default figure sizing rule (`figure img, figure svg { max-height: 150mm; max-width: 100%; width: auto; }`):

```css
    figure.book-figure.fig-s img,
    figure.book-figure.fig-s svg {
      max-height: 72mm;
      max-width: 100%;
      width: auto;
    }
    figure.book-figure.fig-m img,
    figure.book-figure.fig-m svg {
      max-height: 150mm;
      max-width: 100%;
      width: auto;
    }
    figure.book-figure.fig-l.landscape {
      max-height: 170mm;
      overflow: hidden;
    }
    figure.book-figure.fig-l.landscape img,
    figure.book-figure.fig-l.landscape svg {
      max-height: 150mm;
      max-width: 100%;
      width: auto;
    }
```

Do **not** change the existing generic `figure img, figure svg { max-height: 150mm; max-width: 100%; width: auto; }` line. Do **not** add `max-height: 190mm`. The `fig-l` image cap stays 150mm until a PDF-measured caption budget proves a safe larger value; the 170mm block budget is enforced by the block rule + landscape page margins and verified by real PDF layout audit.

- [ ] **Step 4: Run tests to verify pass**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -m unittest book.tests.test_print_sections -v`
Expected: PASS (all tests in file, including existing viewport/cover-copy tests).

- [ ] **Step 5: Commit**

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add book/print_css.py book/tests/test_print_sections.py
git commit -m "style(print): add fig-s/m/l size tiers"
```

Expected: only print CSS + print test changed.

---

### Task 3: Site CSS 尺寸档位（S2-site）

**Files:**
- Modify: `docs/.vitepress/theme/style.css` (after `.vp-doc figure.book-figure img { ... }`)
- Modify: `book/tests/test_print_sections.py` (add `SiteStyleTests`)

**Interfaces:**
- Produces: `.vp-doc figure.book-figure.fig-s img { max-width: min(100%, 28rem); }`, `.fig-m ... min(100%, 42rem)`, `.fig-l ... 100%`.
- Consumes: existing `.vp-doc figure.book-figure img { display:block; margin:0 auto; max-width:100%; height:auto; border-radius:4px; }` remains the default.

- [ ] **Step 1: Add a failing style-contract test**

Add to `book/tests/test_print_sections.py`:

```python
class SiteStyleTests(unittest.TestCase):
    def test_figure_size_tiers_present(self):
        css = (ROOT / "docs" / ".vitepress" / "theme" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".vp-doc figure.book-figure.fig-s img", css)
        self.assertIn("max-width: min(100%, 28rem);", css)
        self.assertIn(".vp-doc figure.book-figure.fig-m img", css)
        self.assertIn("max-width: min(100%, 42rem);", css)
        self.assertIn(".vp-doc figure.book-figure.fig-l img", css)
        # Default figure remains responsive.
        self.assertIn(".vp-doc figure.book-figure img {", css)
        self.assertIn("max-width: 100%;", css)
```

- [ ] **Step 2: Run to verify fail**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -m unittest book.tests.test_print_sections.SiteStyleTests -v`
Expected: FAIL — missing fig-s/m/l selectors.

- [ ] **Step 3: Implement site CSS tiers**

In `docs/.vitepress/theme/style.css`, immediately after the existing `.vp-doc figure.book-figure img { ... }` rule, add:

```css
.vp-doc figure.book-figure.fig-s img {
  max-width: min(100%, 28rem);
}

.vp-doc figure.book-figure.fig-m img {
  max-width: min(100%, 42rem);
}

.vp-doc figure.book-figure.fig-l img {
  max-width: 100%;
}
```

Do not remove or narrow the default `.vp-doc figure.book-figure img` rule.

- [ ] **Step 4: Run tests and build**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -m unittest book.tests.test_print_sections -v`
Expected: PASS.

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && npm run docs:build`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add docs/.vitepress/theme/style.css book/tests/test_print_sections.py
git commit -m "style(site): add fig-s/m/l figure size tiers"
```

Expected: only site CSS + test changed.

---

### Task 4: 试点图模块 + 发布链验证（S3-pilot）

**Files:**
- Modify: `tools/handraw_track/fig_reading.py` (add builder + register in `FIGS`)
- Create (generated): `assets/illustrations/staged/reading-pass/figures/ch06-size-audit-flow.svg`
- Create (generated): `docs/public/images/ch06-size-audit-flow.png`
- Modify: `docs/v0-foundations/06-linker-startup-map.md`

**Interfaces:**
- Produces: one new Handraw figure referenced by ch06; `audit_book` shows ch06 `visual_anchor_deficit` or `max_visual_gap_chars` improved versus baseline.
- Consumes: `fig_reading.py` helpers (`plate`, `note`, `Fig`, `save`, `STAGE`, `FIGS`); `publish_staged.py` already includes `fig_reading` in `MODULES`; `test_figure_sources.py` requires tracked staged SVG for referenced PNGs.

- [ ] **Step 1: Capture ch06 baseline**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -c "import json; d=json.load(open('.temp/audit_book.current.json',encoding='utf-8')); c=[x['zh'] for x in d['chapters'] if x['id']=='ch06'][0]; print(c['visual_anchor_deficit'], c['max_visual_gap_chars'], c['max_visual_gap_from'])"`
Expected: `3 5826 size 三列：Flash 与 RAM 各吃哪份` (or equal/better than baseline).

- [ ] **Step 2: Add pilot figure builder**

In `tools/handraw_track/fig_reading.py`, add a deterministic builder and register in `FIGS`:

```python
def ch06_size_audit_flow():
    figure, label = plate(
        "ch06-size-audit-flow",
        "三份证据对一笔账",
        "size 看总量，nm 看大符号，map 看段与地址；三者一致才下结论。",
    )
    inputs = [
        (64, "arm-none-eabi-size", "text/data/bss\n总量与余量", BLUE_D, BLUE_FILL),
        (404, "nm --size-sort -r", "谁最大\n符号级证据", GREEN_D, GREEN_FILL),
        (744, "map / ld", "落在哪一段\n地址与归属", AMBER_STROKE, AMBER_PALE),
    ]
    for x, title, body, stroke, fill in inputs:
        figure.rect(x, 214, 304, 168, color=stroke, fill=fill)
        label(x + 20, 252, title, size=24, color=stroke, weight="bold")
        for i, line in enumerate(body.split("\n")):
            label(x + 20, 296 + i * 34, line, size=22, color=INK)
        figure.arrow(x + 152, 388, x + 152, 444, color=stroke, bend=0)
    figure.rect(248, 450, 656, 104, color=RED, fill=RED_FILL)
    label(576, 492, "对账：总量、最大对象、段归属能否互相解释？", size=27, color=RED, anchor="middle", weight="bold")
    label(576, 528, "不能解释 = 先补证据，不先下结论", size=22, color=INK, anchor="middle")
    figure.arrow(416, 560, 276, 612, color=BLUE_D, bend=0)
    figure.arrow(736, 560, 876, 612, color=GREEN_D, bend=0)
    figure.rect(96, 618, 360, 92, color=BLUE_D, fill=BLUE_FILL)
    figure.rect(696, 618, 360, 92, color=GREEN_D, fill=GREEN_FILL)
    label(276, 656, "Flash 余量 / .text .rodata", size=24, color=BLUE_D, anchor="middle", weight="bold")
    label(276, 690, "看常量、代码、库函数", size=21, color=INK, anchor="middle")
    label(876, 656, "RAM 余量 / .data .bss .stack", size=24, color=GREEN_D, anchor="middle", weight="bold")
    label(876, 690, "看大数组、堆栈、保留区", size=21, color=INK, anchor="middle")
    note(figure, label, "原理示意/非实拍；字段名与阈值以实际工具输出、链接脚本和芯片手册为准。")
    return figure
```

Add to `FIGS`: `"ch06-size-audit-flow": ch06_size_audit_flow`.

- [ ] **Step 3: Generate staged SVG and publish PNG**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python tools/handraw_track/fig_reading.py`
Expected: wrote N reading plates (N increased by 1).

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python tools/handraw_track/publish_staged.py`
Expected: rebuilt log includes `ch06-size-audit-flow`.

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python tools/handraw_track/publish_staged.py --check`
Expected: exit 0, missing 0, stale 0.

- [ ] **Step 4: Insert figure reference in ch06**

Edit `docs/v0-foundations/06-linker-startup-map.md`. Insert the figure near the max-gap start (`size 三列：Flash 与 RAM 各吃哪份`), after that section’s evidence table/paragraph and before the next `##` heading that begins the long tail. Use raw HTML so `fig-m` class survives site/print wrappers:

```html
<figure class="book-figure fig-m">
  <img src="/images/ch06-size-audit-flow.png" alt="size、nm、map 三份证据对账流程：总量、最大符号、段归属三层交叉确认；原理示意，非实拍" loading="lazy" decoding="async" />
  <figcaption>图：size、nm、map 三份证据对账流程。看哪里：左侧三份工具输出，中间对账判定，右侧 Flash/RAM 结论。证明什么：单一数字不足以下结论，三份证据一致时才能定位超限层。不能证明什么：不代表具体工程的真实余量，也不替代链接脚本和 map 文件。出处：本章正文审计流程；工具行为以 arm-none-eabi-binutils 输出为准。原理示意/非实拍。</figcaption>
</figure>
```

- [ ] **Step 5: Verify narrow gates and audit delta**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python -m unittest book.tests.test_figure_sources book.tests.test_figure_mirrors book.tests.test_handraw_layout book.tests.test_handraw_chrome -v`
Expected: PASS.

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python tools/audit_book.py --format json --write .temp/audit_book.current.json && python -c "import json; d=json.load(open('.temp/audit_book.current.json',encoding='utf-8')); c=[x['zh'] for x in d['chapters'] if x['id']=='ch06'][0]; print(c['visual_anchor_deficit'], c['max_visual_gap_chars'])"`
Expected: deficit <= 2 or max gap < 5826.

- [ ] **Step 6: Commit**

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add tools/handraw_track/fig_reading.py assets/illustrations/staged/reading-pass/figures/ch06-size-audit-flow.svg docs/public/images/ch06-size-audit-flow.png docs/v0-foundations/06-linker-startup-map.md
git commit -m "docs(ch06): add size-audit handraw figure"
```

---

### Task 5: 扩展其余 4 章首批图（S4）

**Files:**
- Modify: `tools/handraw_track/fig_reading.py`
- Create (generated): 8 staged SVGs + 8 PNGs
- Modify: `docs/v1-drivers/11-systick-timebase-rtc.md`, `docs/v3-rtos/26-device-framework-shell.md`, `docs/v7-delivery/46-resources-roadmap-open-source.md`, `docs/appendix/D-glossary.md`

**Interfaces:**
- Produces: 8 figures covering spec §4.2.2 max gaps.
- Consumes: same contracts as Task 4.

- [ ] **Step 1: ch11 — two builders**

Add `ch11_timebase_decision()` (睡眠保持/掉电保持/1ms 节拍/低功耗唤醒 -> SysTick/HAL tick/RTC/LPTIM 选择；原理示意，口径以 RM0008/芯片手册为准) and `ch11_systick_isr_chain()` (`SysTick_Handler -> HAL_IncTick -> uwTick++ -> HAL_GetTick/HAL_Delay`；ISR 优先级风险由正文约束，不在图里伪造具体优先级数)。Register `ch11-timebase-decision`, `ch11-systick-isr-chain`.

- [ ] **Step 2: ch11 — publish, insert, verify, commit**

Generate/publish/check. Insert two `fig-m` figures in `docs/v1-drivers/11-systick-timebase-rtc.md` around `## SysTick 与 RTC 的分工` and before 章末, splitting the 4829-char gap. Captions include 看哪里/证明什么/不能证明什么/出处/原理示意/非实拍.

Run narrow figure tests + audit; `ch11` deficit <= 5, max gap <= 4829.

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add tools/handraw_track/fig_reading.py assets/illustrations/staged/reading-pass/figures/ch11-*.svg docs/public/images/ch11-*.png docs/v1-drivers/11-systick-timebase-rtc.md
git commit -m "docs(ch11): add timebase handraw figures"
```

- [ ] **Step 3: ch26 — two builders, publish, insert, verify, commit**

Builders: `ch26_finsh_dispatch_path()` (输入行 -> FinSH 解析 -> 命令/符号表 -> 执行 -> 输出) and `ch26_device_lifecycle()` (register/find/open/read-write/ioctl/close；refcount/ops 语义，原理示意，不抄内部源码细节). Register `ch26-finsh-dispatch-path`, `ch26-device-lifecycle`. Insert in `docs/v3-rtos/26-device-framework-shell.md` around `## 两条命令的分工` to 章末.

Narrow tests + audit; `ch26` deficit <= 3, max gap <= 5313.

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add tools/handraw_track/fig_reading.py assets/illustrations/staged/reading-pass/figures/ch26-*.svg docs/public/images/ch26-*.png docs/v3-rtos/26-device-framework-shell.md
git commit -m "docs(ch26): add finsh and device handraw figures"
```

- [ ] **Step 4: ch46 — two builders, publish, insert, verify, commit**

Builders: `ch46_gate_checklist_map()` (L0-L5 门禁：能构建/烧录/观测/回归/交付/维护；每格给证据形态；默认 fig-m) and `ch46_route_branching()` (裸机驱动/RTOS/联网/电机控制路线分叉与前置条件；原理示意). Register `ch46-gate-checklist-map`, `ch46-route-branching`. Insert in `docs/v7-delivery/46-resources-roadmap-open-source.md` to split the 8846-char gap after `## 1. 三阶段路线与过关判据`.

Narrow tests + audit; `ch46` deficit <= 4, max gap <= 8846.

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add tools/handraw_track/fig_reading.py assets/illustrations/staged/reading-pass/figures/ch46-*.svg docs/public/images/ch46-*.png docs/v7-delivery/46-resources-roadmap-open-source.md
git commit -m "docs(ch46): add roadmap and gate handraw figures"
```

- [ ] **Step 5: apD — two builders, publish, insert, verify, commit**

Builders: `apd_bus_selection_matrix()` (UART/I2C/SPI/CAN/USB 典型场景/拓扑/速率或距离量级/复杂度；量级用“典型”表述并指向正文/手册，不伪造精确上限) and `apd_debug_symptom_map()` (现象 -> 首查对象：无日志/乱码/丢包/总线挂死/枚举失败 -> 对应层/时钟/电平/协议). Register `apd-bus-selection-matrix`, `apd-debug-symptom-map`. Insert in `docs/appendix/D-glossary.md` around `UART、I2C、SPI、CAN 与 USB` and before `## 工程习惯`.

Narrow tests + audit; `apD` deficit <= 5, max gap <= 5954.

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add tools/handraw_track/fig_reading.py assets/illustrations/staged/reading-pass/figures/apd-*.svg docs/public/images/apd-*.png docs/appendix/D-glossary.md
git commit -m "docs(apD): add glossary bus and debug handraw figures"
```

- [ ] **Step 6: Batch sanity**

Run: `cd /c/Users/zhugu/orca/workspaces/STM32/gourami && python tools/handraw_track/publish_staged.py --check`
Expected: exit 0, missing 0, stale 0.

---

### Task 6: 全量窄门、印刷 PDF 构建与布局审计（S6）

**Files:**
- Modify (if needed): `book/tests/test_book_audit_thresholds.py` only to confirm baseline values still represent old ceiling; never loosen.
- Read/Report: `.temp/audit_book.current.json`, `.temp/pdf-layout.json`, `book/dist/print/merged-book.{html,pdf}`

**Interfaces:**
- Produces: green narrow gates; real PDF layout audit result recorded; before/after delta ready for PR body.
- Consumes: all prior tasks; `build_print_edition.py`, `print_pdf.py`, `tools/audit_pdf_layout.py`.

- [ ] **Step 1: Run repo narrow gates**

Run:

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
python tools/slop_lint.py docs/superpowers/specs/2026-11-26-book-visual-layout.md docs/superpowers/plans/2026-11-26-book-visual-layout.md
python -m book.build_html --check
python -m book.checks --check
python -m book.md_links
npm run docs:build
python -m unittest book.tests.test_print_sections book.tests.test_figure_sources book.tests.test_figure_mirrors book.tests.test_handraw_layout book.tests.test_handraw_chrome book.tests.test_book_audit_thresholds -v
python tools/handraw_track/publish_staged.py --check
```

Expected: slop clean; build_html 53 pages; checks passed; md_links reports same pre-existing 20 problems or fewer, no new files; docs:build exit 0; all selected tests PASS/SKIP only where environment-missing and documented.

- [ ] **Step 2: Build actual print HTML/PDF**

Run:

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
python book/build_print_edition.py
python book/print_pdf.py --html book/dist/print/merged-book.html --meta book/dist/print/merged-book.meta.json --out book/dist/print/merged-book.pdf
```

Expected: both files exist. If fonts missing, run `python book/build_fonts.py` first (environment prerequisite; report, do not silently skip green).

- [ ] **Step 3: Run print layout audit**

Run:

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
python tools/audit_pdf_layout.py --max-gap-pages 200 --max-large-gap-pages 120 --json .temp/pdf-layout.json
```

Expected: exit 0. Record summary counts; if any page-gap/overflow regression appears, fix the offending figure/CSS before proceeding.

- [ ] **Step 4: Capture before/after audit delta**

Run: `python tools/audit_book.py --format json --write .temp/audit_book.current.json`

Report in PR body / final message: for each target chapter, baseline vs current `pdf_visual_anchors`, `visual_anchor_deficit`, `max_visual_gap_chars`, `max_visual_gap_from/to`; global summary delta. Do not claim "达标" unless deficit is 0.

- [ ] **Step 5: Commit verification artifacts only if policy allows**

Do **not** commit `.temp/*` or `book/dist/*` outputs. Commit only source/tests/docs changes. If threshold test baseline numbers changed because metrics improved, update the hard-coded BASELINE to the new better-or-equal ceiling only with explicit PR-body note "threshold tightened".

```bash
cd /c/Users/zhugu/orca/workspaces/STM32/gourami
git add book/print_css.py docs/.vitepress/theme/style.css   book/tests/test_print_sections.py book/tests/test_book_audit_thresholds.py   tools/handraw_track/fig_reading.py tools/handraw_track/publish_staged.py   assets/illustrations/staged docs/public/images   docs/v0-foundations/06-linker-startup-map.md   docs/v1-drivers/11-systick-timebase-rtc.md   docs/v3-rtos/26-device-framework-shell.md   docs/v7-delivery/46-resources-roadmap-open-source.md   docs/appendix/D-glossary.md   docs/superpowers/specs/2026-11-26-book-visual-layout.md   docs/superpowers/plans/2026-11-26-book-visual-layout.md
git status --short --branch
git commit -m "book: unify figure tiers and add first visual-layout batch"
```

Expected: only intended source/docs/tests/staged-svg/published-png files committed.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-11-26-book-visual-layout.md`. Please review the plan. Which execution approach would you prefer?

- **Subagent-driven** - A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review.
- **Native** - I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end. Runs well with a mid-tier session model, since the plan carries the design.

For this plan I recommend **Native**, because the tasks are a short linear S1→S6 chain with shared style/figure contracts and only 2 active style files plus 5 Markdown chapters; the main risk is contract regression, which narrow gates and a final whole-branch review catch well without paying per-task subagent overhead. Does the plan capture what you want, and which approach should we use?
