# 双书合并 B1（卷 0–1 改写与临时站点）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 51 个旧源文件改写为卷 0–1 的 17 章新书稿，并让章节契约、内链锚点、资产、测验与临时静态站构建在本地和 CI 全部可校验。

**Architecture:** `book/checks.py` 新增章节质量检查器（契约/链接锚点/图片资产/QuizBank 测验）；`book/build_html.py` 在 `book/dist/site/` 生成临时静态站（每章一页，可回读）；`book/mapping.tsv` 增加 `purpose`/`status` 两列并由 `book/mapping.py` 校验状态与章节文件存在性一致（R8）。17 章正文只写进 `docs/v0-foundations/` 与 `docs/v1-drivers/`，资产复制进 `docs/public/`，测验复制进 `docs/.vitepress/data/quizzes/`；旧书与旧站零改动。

**Tech Stack:** Python 3.13 + `markdown==3.11`（唯一新增依赖，仅用于临时站构建）、Node.js 20（沿用既有 `node:test`）、GitHub Actions。

**Spec:** [docs/superpowers/specs/2026-11-12-merged-book-design.md](../specs/2026-11-12-merged-book-design.md)

## Global Constraints

- 仅中文书稿；不处理英文版（B5 归档）。
- 旧树零改动：`docs/00-28*.md`、`docs/en/**`、`stm32-book/**`、`mcu/**`、`scripts/legacy-redirects.mjs` 一律不改；本批只新增 `docs/v0-foundations/`、`docs/v1-drivers/`、`docs/public/`、`docs/.vitepress/data/quizzes/`，并修改 `book/`、`.github/workflows/merge-check.yml`、`plans/2026-11-12-merged-book/`。
- 新增依赖仅 `markdown==3.11`（`book/requirements.txt`，本地已验证该版本）；不升级任何既有依赖、不改任何 lock 文件、不新增 Node 依赖。
- 站点临时构建 = `python -m book.build_html --check`（生成临时静态站并回读）；生产 VitePress 站点配置与 `/STM32/` base 切换仍属 B5，本批不建 `docs/.vitepress/config.*`。
- 章节文件名、标题、平台来自 `book/data/toc.tsv`，不许改 toc 迁就正文。
- 章节结构固定：frontmatter（`title`、`platforms`）→ `# 标题` → `## 本章罗盘`（**问题** / **交付** / **边界** / **依据锚点**）→ `## 先做出来` → `## 机制` → `## 测量与证据` → `## 失败分支` → `## 离开检查`；多平台章可在「失败分支」后加 `## 跨平台边界`。
- 折叠块用原生 `<details><summary>…</summary>`；测验用 `<QuizBank chapter="..." />`；不使用 `:::` 容器。
- 图片引用根绝对路径（如 `/arch/x.png`，对应 `docs/public/`）或同目录相对路径；`alt` 必填；禁止外链图片。
- 章间链接用相对 `.md` 路径（可带 `#锚点`）；禁止根绝对页面链接。
- 不编造故障经历、测试数据与实验结果；跨平台事实必须来自来源文件，无来源的平台差异只写边界并指向卷 4（第 28–29 章），不得泛化寄存器名、时钟或引脚。
- mapping 状态机：`planned`（无目标章文件）→ `partial`（部分目标章已写）→ `migrated`（全部目标章已写）；与章节文件存在性不一致即失败。
- 所有提交按显式路径暂存，禁止 `git add -A` / `git add .`。
- 远程推送、PR 合入与 Pages 切换需另行授权；本计划只做本地提交。

---

### Task 1: 映射 schema 升级（用途 + 状态，R8）

**Files:**
- Modify: `book/mapping.py`
- Modify: `book/tests/test_mapping.py`
- Modify: `book/data/mapping.tsv`（141 行，4 列 → 6 列）
- Regenerate: `plans/2026-11-12-merged-book/mapping.json`

**Interfaces:**
- Produces: `load_rows()` 每行含 `book/source/targets/purpose/status/note`；`validate(rows, manifest, docs_root=None) -> list[str]`；`ALLOWED_STATUSES = {"planned", "partial", "migrated"}`。后续章节任务依赖该状态机。

- [ ] **Step 1: 先跑现有测试确认基线**

Run: `python -m unittest book.tests.test_mapping -v`
Expected: 6 tests PASS

- [ ] **Step 2: 修改 `book/mapping.py` 的加载与校验**

把 `load_rows` 改为 6 列（`book`、`source`、`targets`、`purpose`、`status`、`note`），并在文件顶部加入状态集合：

```python
ALLOWED_STATUSES = {"planned", "partial", "migrated"}


def load_rows(path: Path = MAPPING_TSV) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 6:
            raise ValueError(f"{path}:{number}: expected 6 columns, got {len(columns)}")
        book, source, targets, purpose, status, note = columns
        rows.append(
            {
                "book": book,
                "source": source,
                "targets": [target for target in targets.split(";") if target],
                "purpose": purpose,
                "status": status,
                "note": note,
            }
        )
    return rows
```

把 `validate` 替换为下面版本（保留原有重复源、未知目标、缺失源文件、双向覆盖逻辑，新增用途/状态与文件存在性一致性）：

```python
def validate(rows: list[dict], manifest: dict, docs_root: Path | None = None) -> list[str]:
    docs_root = Path(docs_root) if docs_root is not None else ROOT / "docs"
    errors = []
    seen = set()
    for row in rows:
        key = (row["book"], row["source"])
        if key in seen:
            errors.append(f"duplicate source: {row['book']}:{row['source']}")
        seen.add(key)
    files: dict[str, str] = {}
    for part in manifest["parts"]:
        for chapter in part["chapters"]:
            files[chapter["id"]] = chapter["file"]
    for appendix in manifest["appendices"]:
        files[appendix["id"]] = appendix["file"]
    for row in rows:
        if not row["targets"]:
            errors.append(f"empty targets: {row['source']}")
        for target in row["targets"]:
            if target not in files:
                errors.append(f"unknown target {target} for {row['source']}")
        if not (ROOT / row["source"]).exists():
            errors.append(f"missing source file: {row['source']}")
        if not row["purpose"].strip():
            errors.append(f"missing purpose: {row['source']}")
        if row["status"] not in ALLOWED_STATUSES:
            errors.append(f"unknown status {row['status']}: {row['source']}")
            continue
        known = [target for target in row["targets"] if target in files]
        existing = [target for target in known if (docs_root / files[target]).exists()]
        if row["status"] == "migrated" and len(existing) != len(known):
            missing = sorted(set(known) - set(existing))
            errors.append(f"migrated but missing chapters: {row['source']} -> {missing}")
        elif row["status"] == "partial" and not (0 < len(existing) < len(known)):
            errors.append(f"partial status inconsistent: {row['source']}")
        elif row["status"] == "planned" and existing:
            errors.append(f"planned but target exists: {row['source']}")
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
```

- [ ] **Step 3: 数据迁移脚本（purpose 按来源类别，status 一律 `planned`）**

Run:

```bash
python - <<'EOF'
from pathlib import Path

PATH = Path("book/data/mapping.tsv")
PURPOSE = {
    ("root", "chapters"): "根书原章",
    ("root", "appendix"): "根书附录素材",
    ("root", "route"): "学习路线收束",
    ("mcu", "c"): "语言深潜",
    ("mcu", "build"): "构建链深潜",
    ("mcu", "stm32"): "外设深潜",
    ("mcu", "esp32"): "平台对照（ESP32）",
    ("mcu", "gd32"): "平台对照（GD32）",
    ("mcu", "rtos"): "RTOS 深潜",
    ("mcu", "ai"): "AI 工程方法",
    ("mcu", "projects"): "项目案例",
    ("mcu", "lab"): "实验方法与证据",
    ("mcu", "mcu-book"): "附录素材",
    ("motor", "motor"): "电机控制草稿",
}


def category(book: str, source: str) -> tuple[str, str]:
    parts = source.split("/")
    if book == "mcu":
        return book, parts[2] if parts[1] == "docs" else "mcu-book"
    if book == "root":
        if source == "stm32-book/book/F-学习路线收束.md":
            return book, "route"
        return book, "appendix" if parts[0] == "stm32-book" else "chapters"
    return book, "motor"


lines = []
for line in PATH.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    book, source, targets, note = line.split("\t")
    purpose = PURPOSE[category(book, source)]
    lines.append("\t".join([book, source, targets, purpose, "planned", note]))
PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(lines), "rows")
EOF
```

Expected: `141 rows`

- [ ] **Step 4: 补测试并运行**

在 `book/tests/test_mapping.py` 顶部 import 区加入 `import tempfile`，并在 `MappingTest` 类内增加以下三个方法（保留原 6 个测试）：

```python
    def test_missing_purpose_detected(self):
        rows = [dict(row) for row in self.rows]
        rows[0] = {**rows[0], "purpose": ""}
        errors = mp.validate(rows, self.manifest)
        self.assertTrue(any("missing purpose" in error for error in errors), errors)

    def test_unknown_status_detected(self):
        rows = [dict(row) for row in self.rows]
        rows[0] = {**rows[0], "status": "done"}
        errors = mp.validate(rows, self.manifest)
        self.assertTrue(any("unknown status" in error for error in errors), errors)

    def test_status_must_match_written_chapters(self):
        row = next(r for r in self.rows if r["source"] == "docs/02-芯片选型与存储器时钟.md")
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            (docs / "v0-foundations").mkdir()
            (docs / "v0-foundations" / "01-c-memory-model.md").write_text("x", encoding="utf-8")
            planned = mp.validate([{**row, "status": "planned"}], self.manifest, docs_root=docs)
            partial = mp.validate([{**row, "status": "partial"}], self.manifest, docs_root=docs)
            migrated = mp.validate([{**row, "status": "migrated"}], self.manifest, docs_root=docs)
        self.assertTrue(any("planned but target exists" in error for error in planned), planned)
        self.assertFalse(any("status" in error for error in partial), partial)
        self.assertTrue(any("migrated but missing chapters" in error for error in migrated), migrated)
```

Run: `python -m book.mapping --write && python -m unittest book.tests.test_mapping -v`
Expected: 9 tests PASS；`plans/2026-11-12-merged-book/mapping.json` 每项含 `purpose`、`status`

- [ ] **Step 5: 提交**

```bash
git add book/mapping.py book/tests/test_mapping.py book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(mapping): record per-source purpose and migration status (B1)"
```

---

### Task 2: 章节质量检查器 `book/checks.py`

**Files:**
- Create: `book/checks.py`
- Create: `book/tests/test_checks.py`

**Interfaces:**
- Consumes: `book.contracts.validate_chapter_file`、`book.manifest.load_toc/build_manifest`
- Produces: `cjk_slugify(value, separator="-")`（渲染器与检查器共用）、`heading_anchors(text)`、`validate_quiz(path)`、`check_file(path, docs_root, quiz_dir) -> tuple[list[str], list[str]]`、`check_book(docs_root=DOCS, quiz_dir=QUIZ_DIR, only=None) -> list[str]`、CLI `python -m book.checks [--chapter ch01 ...]`

- [ ] **Step 1: 写失败测试 `book/tests/test_checks.py`**

```python
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import checks
from book import manifest as mf


def chapter_text(title: str, platforms: str, body: str = "") -> str:
    return (
        "---\n"
        f'title: "{title}"\n'
        f"platforms: [{platforms}]\n"
        "---\n\n"
        f"# {title}\n\n"
        "## 本章罗盘\n\n"
        "- **问题**：测试问题。\n"
        "- **交付**：测试交付。\n"
        "- **边界**：测试边界。\n"
        "- **依据锚点**：测试锚点。\n\n"
        f"{body}"
    )


class ChecksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name)
        self.quiz_dir = self.docs / ".vitepress" / "data" / "quizzes"
        self.quiz_dir.mkdir(parents=True)
        self.rows = {row["id"]: row for row in mf.load_toc()}
        (self.docs / "public" / "arch").mkdir(parents=True)
        (self.docs / "public" / "arch" / "demo.svg").write_text("<svg/>", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_chapter(self, chapter_id: str, body: str = "") -> Path:
        row = self.rows[chapter_id]
        path = self.docs / row["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        platforms = ", ".join(row["platforms"])
        path.write_text(chapter_text(row["title"], platforms, body), encoding="utf-8")
        return path

    def write_quiz(self, quiz_id: str, answer: int = 0) -> Path:
        path = self.quiz_dir / f"{quiz_id}.json"
        options = ["A", "B"]
        path.write_text(
            '{"title": "自测", "chapter": "%s", "questions": ['
            '{"q": "题?", "options": ["A", "B"], "answer": %d, "a": "解析"}]}'
            % (quiz_id, answer),
            encoding="utf-8",
        )
        return path

    def test_valid_chapter_passes(self):
        self.write_chapter(
            "ch01",
            '![图](/arch/demo.svg)\n\n<a id="self"></a>\n\n'
            "## 小节\n\n[本章](#小节)\n\n<QuizBank chapter=\"q1\" />\n",
        )
        self.write_quiz("q1")
        self.assertEqual(checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir), [])

    def test_missing_anchor_detected(self):
        self.write_chapter("ch01", "## 小节\n\n[跳到](#不存在)\n")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("missing anchor" in error for error in errors), errors)

    def test_missing_image_detected(self):
        self.write_chapter("ch01", "![图](/arch/nope.svg)\n")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("missing asset" in error for error in errors), errors)

    def test_external_image_detected(self):
        self.write_chapter("ch01", "![图](https://example.com/a.png)\n")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("external image" in error for error in errors), errors)

    def test_quiz_schema_detected(self):
        self.write_chapter("ch01", '<QuizBank chapter="q1" />\n')
        self.write_quiz("q1", answer=5)
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("answer out of range" in error for error in errors), errors)

    def test_orphan_quiz_detected(self):
        self.write_chapter("ch01")
        self.write_quiz("q1")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("orphan quiz" in error for error in errors), errors)

    def test_duplicate_quiz_reference_detected(self):
        self.write_chapter("ch01", '<QuizBank chapter="q1" />\n')
        self.write_chapter("ch02", '<QuizBank chapter="q1" />\n')
        self.write_quiz("q1")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("multiple chapters" in error for error in errors), errors)

    def test_code_spans_are_not_scanned_as_links(self):
        self.write_chapter(
            "ch01",
            "函数指针调用 `callbacks[i](arg)` 不是链接。\n\n"
            "```c\nint x = table[i](arg);\n// [文档](./missing.md) 在代码块里\n```\n\n"
            "<QuizBank chapter=\"q1\" />\n",
        )
        self.write_quiz("q1")
        self.assertEqual(checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir), [])

    def test_title_or_platform_mismatch_detected(self):
        self.write_chapter("ch01")
        path = self.docs / self.rows["ch01"]["file"]
        path.write_text(chapter_text("错标题", "f407"), encoding="utf-8")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("frontmatter title" in error for error in errors), errors)
        self.assertTrue(any("frontmatter platforms" in error for error in errors), errors)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m unittest book.tests.test_checks -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'book.checks'`）

- [ ] **Step 3: 实现 `book/checks.py`**

```python
"""Chapter quality checks: contracts, links, anchors, assets and quizzes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from book import manifest as manifest_module
from book.contracts import parse_list, split_frontmatter, validate_chapter_file

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
QUIZ_DIR = DOCS / ".vitepress" / "data" / "quizzes"

FENCE_RE = re.compile(r"^(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CUSTOM_ID_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
QUIZ_RE = re.compile(r"<QuizBank\s+chapter=\"([^\"]+)\"\s*/>")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def cjk_slugify(value: str, separator: str = "-") -> str:
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s-]+", separator, value) or "section"


def heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = match.group(2)
        custom = CUSTOM_ID_RE.search(title)
        if custom:
            anchors.add(custom.group(1))
            continue
        anchors.add(cjk_slugify(title))
    return anchors


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strip_code(text: str) -> str:
    """Blank fenced blocks and inline code so scans keep true line numbers."""
    out = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(newline)
        elif in_fence:
            out.append(newline)
        else:
            out.append(INLINE_CODE_RE.sub(lambda match: " " * len(match.group(0)), line))
    return "".join(out)


def validate_quiz(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.name}: invalid JSON: {exc}"]
    if data.get("chapter") != path.stem:
        errors.append(f"{path.name}: chapter field must be {path.stem!r}")
    if not str(data.get("title", "")).strip():
        errors.append(f"{path.name}: missing title")
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append(f"{path.name}: questions must be a non-empty list")
        return errors
    for number, question in enumerate(questions, 1):
        options = question.get("options")
        answer = question.get("answer")
        if not str(question.get("q", "")).strip():
            errors.append(f"{path.name}: Q{number} missing q")
        if not isinstance(options, list) or len(options) < 2:
            errors.append(f"{path.name}: Q{number} needs at least 2 options")
        elif not isinstance(answer, int) or not 0 <= answer < len(options):
            errors.append(f"{path.name}: Q{number} answer out of range")
        if not str(question.get("a", "")).strip():
            errors.append(f"{path.name}: Q{number} missing a")
    return errors


def check_file(path: Path, docs_root: Path, quiz_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    scan = strip_code(text)
    anchored = heading_anchors(text)
    quiz_ids: list[str] = []
    for match in IMAGE_RE.finditer(scan):
        alt, target = match.group(1), match.group(2)
        line = _line_of(scan, match.start())
        if not alt.strip():
            errors.append(f"{path}:{line}: image missing alt")
        if target.startswith(("http://", "https://", "//")):
            errors.append(f"{path}:{line}: external image not allowed: {target}")
            continue
        if target.startswith("/"):
            candidate = docs_root / "public" / target.lstrip("/")
        else:
            candidate = (path.parent / target).resolve()
        if not candidate.exists():
            errors.append(f"{path}:{line}: missing asset: {target}")
    for match in LINK_RE.finditer(scan):
        target = match.group(2)
        line = _line_of(scan, match.start())
        if target.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        if target.startswith("/"):
            errors.append(f"{path}:{line}: root-absolute page link not allowed: {target}")
            continue
        target_path, _, fragment = target.partition("#")
        if not target_path:
            if fragment and fragment not in anchored:
                errors.append(f"{path}:{line}: missing anchor: #{fragment}")
            continue
        if not target_path.endswith(".md"):
            errors.append(f"{path}:{line}: link must target a .md file: {target}")
            continue
        candidate = (path.parent / target_path).resolve()
        try:
            candidate.relative_to(docs_root.resolve())
        except ValueError:
            errors.append(f"{path}:{line}: link escapes docs/: {target}")
            continue
        if not candidate.exists():
            errors.append(f"{path}:{line}: missing chapter file: {target_path}")
            continue
        if fragment and fragment not in heading_anchors(candidate.read_text(encoding="utf-8")):
            errors.append(f"{path}:{line}: missing anchor in {target_path}: #{fragment}")
    for match in QUIZ_RE.finditer(scan):
        quiz_id = match.group(1)
        line = _line_of(scan, match.start())
        quiz_ids.append(quiz_id)
        if not (quiz_dir / f"{quiz_id}.json").exists():
            errors.append(f"{path}:{line}: missing quiz: {quiz_id}")
    return errors, quiz_ids


def check_book(
    docs_root: Path = DOCS,
    quiz_dir: Path = QUIZ_DIR,
    only: list[str] | None = None,
) -> list[str]:
    manifest = manifest_module.build_manifest(manifest_module.load_toc())
    entries = [chapter for part in manifest["parts"] for chapter in part["chapters"]]
    entries += manifest["appendices"]
    if only:
        known = {entry["id"] for entry in entries}
        unknown = sorted(set(only) - known)
        if unknown:
            return [f"unknown chapter: {item}" for item in unknown]
        entries = [entry for entry in entries if entry["id"] in set(only)]
    errors: list[str] = []
    existing = 0
    quiz_refs: dict[str, set[str]] = {}
    for entry in entries:
        path = docs_root / entry["file"]
        if not path.exists():
            if only:
                errors.append(f"{entry['id']}: missing file: {entry['file']}")
            continue
        existing += 1
        errors.extend(f"{entry['id']}: {error}" for error in validate_chapter_file(path))
        text = path.read_text(encoding="utf-8")
        meta, _ = split_frontmatter(text)
        if meta.get("title", "").strip().strip("\"'") != entry["title"]:
            errors.append(f"{entry['id']}: frontmatter title must be {entry['title']!r}")
        expected_platforms = entry.get("platforms")
        if expected_platforms is not None:
            actual = set(parse_list(meta.get("platforms", "")))
            if actual != set(expected_platforms):
                errors.append(f"{entry['id']}: frontmatter platforms must be {expected_platforms}")
        file_errors, quiz_ids = check_file(path, docs_root, quiz_dir)
        errors.extend(file_errors)
        for quiz_id in quiz_ids:
            quiz_refs.setdefault(quiz_id, set()).add(entry["id"])
    if not only and existing == 0:
        errors.append(f"no chapter files found under {docs_root}")
    if only:
        for quiz_id in sorted(quiz_refs):
            quiz_path = quiz_dir / f"{quiz_id}.json"
            if quiz_path.exists():
                errors.extend(validate_quiz(quiz_path))
    elif quiz_dir.exists():
        for quiz_path in sorted(quiz_dir.glob("*.json")):
            errors.extend(validate_quiz(quiz_path))
            owners = quiz_refs.get(quiz_path.stem, set())
            if not owners:
                errors.append(f"orphan quiz: {quiz_path.name}")
            elif len(owners) > 1:
                errors.append(f"quiz referenced by multiple chapters: {quiz_path.name} -> {sorted(owners)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验章节契约、链接锚点、资产与测验。")
    parser.add_argument("--chapter", action="append", default=[], help="只检查指定章 id，可重复")
    parser.add_argument("--check", action="store_true", help="兼容 CI 的显式开关")
    args = parser.parse_args(argv)
    errors = check_book(only=args.chapter or None)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行测试**

Run: `python -m unittest book.tests.test_checks -v`
Expected: 9 tests PASS

- [ ] **Step 5: 提交**

```bash
git add book/checks.py book/tests/test_checks.py
git commit -m "feat(checks): validate chapter links, anchors, assets and quizzes (B1)"
```

---

### Task 3: 临时静态站构建器 `book/build_html.py`

**Files:**
- Create: `book/build_html.py`
- Create: `book/tests/test_build_html.py`
- Create: `book/requirements.txt`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `book.checks.cjk_slugify`、`book.contracts.split_frontmatter`、`book.manifest.build_manifest/load_toc`
- Produces: `build(out_dir=DEFAULT_OUT, docs_root=DOCS, quiz_dir=QUIZ_DIR, manifest=None) -> tuple[list[str], list[str]]`（返回已生成页面相对路径与缺失章 id）、CLI `python -m book.build_html [--out-dir PATH] [--check]`

- [ ] **Step 1: 写失败测试 `book/tests/test_build_html.py`**

```python
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import build_html

CHAPTER = """---
title: "测试章"
platforms: [generic]
---

# 测试章

## 本章罗盘

- **问题**：测试。
- **交付**：测试。
- **边界**：测试。
- **依据锚点**：测试。

## 先做出来

![演示图](/arch/demo.svg)

[去第二章](./02-other.md)

## 机制

<QuizBank chapter="q1" />
"""

MANIFEST = {
    "title": "测试书",
    "subtitle": "",
    "version": "0.1.0",
    "language": "zh",
    "parts": [
        {
            "id": "v0",
            "title": "卷 0",
            "goal": "",
            "chapters": [
                {
                    "id": "ch01",
                    "title": "测试章",
                    "file": "v0-foundations/01-a.md",
                    "status": "planned",
                    "platforms": ["generic"],
                },
                {
                    "id": "ch02",
                    "title": "缺章",
                    "file": "v0-foundations/02-other.md",
                    "status": "planned",
                    "platforms": ["generic"],
                },
            ],
        }
    ],
    "appendices": [],
}


class BuildHtmlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.quiz_dir = self.docs / ".vitepress" / "data" / "quizzes"
        self.quiz_dir.mkdir(parents=True)
        (self.docs / "v0-foundations").mkdir(parents=True)
        (self.docs / "public" / "arch").mkdir(parents=True)
        (self.docs / "public" / "arch" / "demo.svg").write_text("<svg/>", encoding="utf-8")
        (self.docs / "v0-foundations" / "01-a.md").write_text(CHAPTER, encoding="utf-8")
        (self.quiz_dir / "q1.json").write_text(
            '{"title": "自测", "chapter": "q1", "questions": ['
            '{"q": "题?", "options": ["A", "B"], "answer": 0, "a": "解析"}]}',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_renders_pages(self):
        out = Path(self.tmp.name) / "out"
        pages, missing = build_html.build(
            out, docs_root=self.docs, quiz_dir=self.quiz_dir, manifest=MANIFEST
        )
        self.assertEqual(pages, ["v0-foundations/01-a.html"])
        self.assertEqual(missing, ["ch02"])
        page = (out / "v0-foundations" / "01-a.html").read_text(encoding="utf-8")
        self.assertIn('id="先做出来"', page)
        self.assertIn('<section class="quiz">', page)
        self.assertIn('src="../arch/demo.svg"', page)
        self.assertIn('href="./02-other.html"', page)
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "arch" / "demo.svg").exists())

    def test_build_requires_at_least_one_chapter(self):
        (self.docs / "v0-foundations" / "01-a.md").unlink()
        with self.assertRaises(ValueError):
            build_html.build(
                Path(self.tmp.name) / "out",
                docs_root=self.docs,
                quiz_dir=self.quiz_dir,
                manifest=MANIFEST,
            )
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m unittest book.tests.test_build_html -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'book.build_html'`）

- [ ] **Step 3: 创建 `book/requirements.txt` 并安装依赖**

```text
markdown==3.11
```

Run: `python -m pip install -r book/requirements.txt`
Expected: `markdown==3.11` 安装成功（唯一新增依赖；不动既有依赖）

- [ ] **Step 4: 实现 `book/build_html.py`**

```python
"""Build the merged book as a temporary static site."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import posixpath
import re
import shutil
import sys
import tempfile
from pathlib import Path

import markdown

from book import manifest as manifest_module
from book.checks import cjk_slugify
from book.contracts import split_frontmatter

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
QUIZ_DIR = DOCS / ".vitepress" / "data" / "quizzes"
DEFAULT_OUT = ROOT / "book" / "dist" / "site"

QUIZ_RE = re.compile(r'<QuizBank\s+chapter="([^"]+)"\s*/>')
MD_HREF_RE = re.compile(r'href="([^"]*?)\.md(#[^"]*)?"')
ROOT_SRC_RE = re.compile(r'(src|href)="(/[^"]*)"')
STYLE = """
body { max-width: 48rem; margin: 0 auto; padding: 2rem 1rem 4rem; font-family: system-ui, sans-serif; line-height: 1.75; color: #1f2328; }
nav.book-nav { border-bottom: 1px solid #d0d7de; margin-bottom: 2rem; padding-bottom: 1rem; font-size: 0.9rem; }
nav.book-nav ol { display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; list-style: none; padding: 0; }
pre { background: #f6f8fa; padding: 0.75rem; overflow-x: auto; }
code { background: #f6f8fa; padding: 0.1rem 0.25rem; }
table { border-collapse: collapse; }
th, td { border: 1px solid #d0d7de; padding: 0.35rem 0.6rem; }
.quiz { border: 1px solid #d0d7de; border-radius: 6px; padding: 1rem; margin: 1.5rem 0; }
img { max-width: 100%; }
"""
PRINT_SCRIPT = """<script>
window.addEventListener('beforeprint', () => {
  document.querySelectorAll('details').forEach((item) => { item.open = true; });
});
</script>"""


def quiz_html(quiz_id: str, quiz_dir: Path) -> str:
    data = json.loads((quiz_dir / f"{quiz_id}.json").read_text(encoding="utf-8"))
    parts = [f'<section class="quiz"><h3>{html_lib.escape(data["title"])}</h3>']
    for index, item in enumerate(data["questions"], 1):
        parts.append(f'<p class="quiz-q"><strong>Q{index}.</strong> {html_lib.escape(item["q"])}</p>')
        parts.append('<ol class="quiz-options">')
        parts.extend(f"<li>{html_lib.escape(option)}</li>" for option in item["options"])
        parts.append("</ol>")
        parts.append(
            '<details class="quiz-answer"><summary>答案与解析</summary>'
            f'<p>{html_lib.escape(item["a"])}</p></details>'
        )
    parts.append("</section>")
    return "\n".join(parts)


def render_markdown(text: str, quiz_dir: Path) -> str:
    text = QUIZ_RE.sub(lambda match: quiz_html(match.group(1), quiz_dir), text)
    return markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": cjk_slugify, "permalink": False}},
    ).convert(text)


def relativize(html_text: str, depth: int) -> str:
    prefix = "../" * depth
    return ROOT_SRC_RE.sub(
        lambda match: f'{match.group(1)}="{prefix}{match.group(2).lstrip("/")}"', html_text
    )


def nav_html(items: list[tuple[str, str, str]], current_path: str) -> str:
    current_dir = posixpath.dirname(current_path)
    links = []
    for _, title, path in items:
        href = posixpath.relpath(path, current_dir or ".")
        links.append(f'<li><a href="{href}">{html_lib.escape(title)}</a></li>')
    return "<ol>" + "".join(links) + "</ol>"


def page_shell(title: str, body: str, nav: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html_lib.escape(title)}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n"
        f'<nav class="book-nav">{nav}</nav>\n<main>\n{body}\n</main>\n{PRINT_SCRIPT}\n'
        "</body>\n</html>\n"
    )


def index_body(manifest: dict, present: set[str], page_paths: dict[str, str]) -> str:
    blocks = [f"<h1>{html_lib.escape(manifest['title'])}</h1>"]
    for part in manifest["parts"]:
        chapters = [chapter for chapter in part["chapters"] if chapter["id"] in present]
        if not chapters:
            continue
        items = "".join(
            f'<li><a href="{page_paths[chapter["id"]]}">{html_lib.escape(chapter["title"])}</a></li>'
            for chapter in chapters
        )
        blocks.append(f'<h2>{html_lib.escape(part["title"])}</h2><ol>{items}</ol>')
    appendices = [appendix for appendix in manifest["appendices"] if appendix["id"] in present]
    if appendices:
        items = "".join(
            f'<li><a href="{page_paths[appendix["id"]]}">{html_lib.escape(appendix["title"])}</a></li>'
            for appendix in appendices
        )
        blocks.append(f"<h2>附录</h2><ol>{items}</ol>")
    return "\n".join(blocks)


def build(
    out_dir: Path = DEFAULT_OUT,
    docs_root: Path = DOCS,
    quiz_dir: Path = QUIZ_DIR,
    manifest: dict | None = None,
) -> tuple[list[str], list[str]]:
    manifest = manifest or manifest_module.build_manifest(manifest_module.load_toc())
    entries = [chapter for part in manifest["parts"] for chapter in part["chapters"]]
    entries += manifest["appendices"]
    present = [entry for entry in entries if (docs_root / entry["file"]).exists()]
    missing = [entry["id"] for entry in entries if not (docs_root / entry["file"]).exists()]
    if not present:
        raise ValueError(f"no chapter files found under {docs_root}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    public = docs_root / "public"
    if public.exists():
        shutil.copytree(public, out_dir, dirs_exist_ok=True)
    page_paths = {
        entry["id"]: Path(entry["file"]).with_suffix(".html").as_posix() for entry in present
    }
    items = [(entry["id"], entry["title"], page_paths[entry["id"]]) for entry in present]
    pages = []
    for entry in present:
        text = (docs_root / entry["file"]).read_text(encoding="utf-8")
        _, body = split_frontmatter(text)
        content = render_markdown(body, quiz_dir)
        content = MD_HREF_RE.sub(
            lambda match: f'href="{match.group(1)}.html{match.group(2) or ""}"', content
        )
        depth = len(Path(entry["file"]).parts) - 1
        content = relativize(content, depth)
        page_path = out_dir / page_paths[entry["id"]]
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(
            page_shell(entry["title"], content, nav_html(items, page_paths[entry["id"]])),
            encoding="utf-8",
        )
        pages.append(page_paths[entry["id"]])
    index = index_body(manifest, {entry["id"] for entry in present}, page_paths)
    (out_dir / "index.html").write_text(
        page_shell(manifest["title"], index, nav_html(items, "index.html")), encoding="utf-8"
    )
    return pages, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把统一 manifest 渲染为临时静态站。")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check:
            with tempfile.TemporaryDirectory() as tmp:
                pages, missing = build(Path(tmp))
                absent = [page for page in pages if not (Path(tmp) / page).exists()]
        else:
            pages, missing = build(args.out_dir)
            absent = [page for page in pages if not (args.out_dir / page).exists()]
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    if absent:
        print("missing output pages: " + ", ".join(absent), file=sys.stderr)
        return 1
    print(f"built {len(pages)} pages, {len(missing)} planned chapters missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 忽略构建产物**

在 `.gitignore` 的 `stm32-book/dist/` 一行后加入：

```text
book/dist/
```

- [ ] **Step 6: 运行测试**

Run: `python -m unittest book.tests.test_build_html -v`
Expected: 2 tests PASS

- [ ] **Step 7: 提交**

```bash
git add book/build_html.py book/tests/test_build_html.py book/requirements.txt .gitignore
git commit -m "feat(build): render merged book as temporary static site (B1)"
```

---

### Task 4: 共享资产迁移（92 个文件）

**Files:**
- Create: `docs/public/anim/*.svg`、`docs/public/arch/*.png`、`docs/public/figures/*.svg`、`docs/public/images/**`

**Interfaces:**
- Produces: 卷 0–1 章节可引用的 92 个根绝对路径资产；`book.checks` 的 `missing asset` 检查以此为准。

- [ ] **Step 1: 复制资产**

Run:

```bash
python - <<'EOF'
from pathlib import Path
import shutil

ASSETS = """
/anim/bitband-alias.svg
/anim/boot-sequence.svg
/anim/build-dep-graph.svg
/anim/build-four-steps.svg
/anim/bus-matrix.svg
/anim/c08-frame-parse.svg
/anim/dac-trio.svg
/anim/data-vma-lma.svg
/anim/dma-circular-buffer.svg
/anim/dma-hal-en-window.svg
/anim/dma-pingpong.svg
/anim/elf-sections.svg
/anim/elf-two-views.svg
/anim/env-setup-flow.svg
/anim/esp32-ota-rollback.svg
/anim/gpio-config.svg
/anim/i2c-timing.svg
/anim/iap-handoff.svg
/anim/iram-discipline.svg
/anim/irq-entry.svg
/anim/map-size-audit.svg
/anim/memory-two-homes.svg
/anim/nvic-preempt-arbitration.svg
/anim/pointer-arrows.svg
/anim/rcc-clock-tree.svg
/anim/rcc-six-gates.svg
/anim/ring-buffer.svg
/anim/sar-successive.svg
/anim/spi-timing.svg
/anim/spl-gpio-init.svg
/anim/stack-frame.svg
/anim/struct-alignment.svg
/anim/systick-tick.svg
/anim/tim-hal-init-path.svg
/anim/tim-input-capture.svg
/anim/tim-pwm-counter.svg
/anim/uart-frame.svg
/anim/uart-hal-init-path.svg
/anim/ub-compiler-trap.svg
/anim/usart-txe-tc.svg
/anim/volatile-as-if.svg
/arch/boot-sequence.png
/arch/dma-paths.png
/arch/exti-chain.png
/arch/i2c-bus.png
/arch/linker-map.png
/arch/map-audit.png
/arch/memory-map.png
/arch/ota-slots.png
/arch/spl-anatomy.png
/arch/toolchain-pipeline.png
/figures/c-01-memory-model.svg
/figures/c-02-pointer.svg
/figures/c-03-volatile.svg
/figures/c-04-struct-abi.svg
/figures/c-05-fsm-table.svg
/figures/c-06-abi-stack.svg
/figures/c-07-strict-alias.svg
/figures/c-08-framed-protocol.svg
/figures/esp32-04-int-alloc.svg
/figures/esp32-10-flash-nvs-ota.svg
/figures/stm32-01-m4-core.svg
/figures/stm32-03-gpio-input.svg
/figures/stm32-03-slew.svg
/figures/stm32-04-nvic-addr.svg
/figures/stm32-05-tick-wrap.svg
/figures/stm32-06-encoder.svg
/figures/stm32-06-tim.svg
/figures/stm32-07-usart-brr.svg
/figures/stm32-07-usart.svg
/figures/stm32-08-dma-stream.svg
/figures/stm32-08-dma.svg
/figures/stm32-09-adc-groups.svg
/figures/stm32-09-adc.svg
/figures/stm32-10-r2r-pwm.svg
/figures/stm32-11-ee-repeated-start.svg
/figures/stm32-11-i2c-event.svg
/figures/stm32-11-i2c.svg
/figures/stm32-12-spi-modes.svg
/figures/stm32-12-spi.svg
/figures/stm32-13-flash-iap.svg
/figures/stm32-13-flash-seq.svg
/figures/stm32-15-spl-tiers.svg
/images/boards/stm32f407-board.jpg
/images/labs/e01-rgb-led.svg
/images/labs/e02-uart-capture.svg
/images/labs/e03-pwm-probe.svg
/images/labs/e05-i2c-wiring.svg
/images/labs/e07-qmi8658-axes.svg
/images/tools/eeprom-24c02.jpg
/images/tools/logic-analyzer-8ch.jpg
/images/tools/oscilloscope-ds1054z.jpg
""".split()

src_root = Path("mcu/docs/public")
dst_root = Path("docs/public")
for asset in ASSETS:
    relative = asset.lstrip("/")
    target = dst_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_root / relative, target)
print(len(ASSETS), "assets copied")
EOF
```

Expected: `92 assets copied`

- [ ] **Step 2: 验证文件数与来源一致**

Run: `find docs/public -type f | wc -l`
Expected: `92`

- [ ] **Step 3: 暂存、复核并提交**

```bash
git add docs/public
git diff --cached --name-only docs/public | wc -l
git commit -m "feat(assets): migrate volume 0-1 shared assets into docs/public (B1)"
```

Expected: 暂存清单计数 `92`（全部为新增文件）

---

### Task 5: 第 1 章 嵌入式 C 的内存模型与指针

**Files:**
- Create: `docs/v0-foundations/01-c-memory-model.md`
- Modify: `book/data/mapping.tsv`（4 行状态）、regenerate `plans/2026-11-12-merged-book/mapping.json`

**Sources（只读）:** `mcu/docs/c/00-c-in-mcu.md`、`mcu/docs/c/01-memory-model.md`、`mcu/docs/c/02-pointer.md`、`docs/02-芯片选型与存储器时钟.md`（仅存储器部分；时钟部分留给第 8 章）

**Interfaces:**
- Consumes: Task 2 `book.checks`、Task 3 `book.build_html`、Task 4 资产
- Produces: manifest 中 `ch01` 页面；`docs/02` 状态变为 `partial`

- [ ] **Step 1: 写章节 `docs/v0-foundations/01-c-memory-model.md`**

frontmatter：

```yaml
---
title: "嵌入式 C 的内存模型与指针"
platforms: [generic]
---
```

正文必须覆盖：

- 没有 OS 的世界：内存按 KB 计、C 与硬件的直线关系、工具链即世界观（C0）。
- 五段内存地图：`.text`/`.rodata`/`.data`/`.bss`/堆/栈；Flash 与 RAM 的分工。
- `int g_init = 5;` 的三段旅程与 `.data` 初值在 Flash 的副本。
- `const` 的 RAM 经济学（“一个词值 256 字节 RAM”的账）。
- 指针声明阅读法、步长真相（`int *` 加一 4 字节）、野指针三宗罪。
- 根书第 02 章的存储器容量与地址边界（只写该来源可对账的事实；具体型号地图留给第 8 章）。
- 图片引用（至少 3 张）：`/arch/memory-map.png`、`/figures/c-01-memory-model.svg`、`/anim/memory-two-homes.svg`、`/anim/pointer-arrows.svg`、`/figures/c-02-pointer.svg`。
- 至少 1 条指向其它新章（如 `./02-c-volatile-ub.md`）的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`docs/02-芯片选型与存储器时钟.md` → `partial`（第 8 章未写）；`mcu/docs/c/00-c-in-mcu.md`、`01-memory-model.md`、`02-pointer.md` → `migrated`。

Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch01`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v0-foundations/01-c-memory-model.md`
Expected: exit 0，无命中

Run: `python -m book.build_html --check`
Expected: `built 1 pages, 51 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/01-c-memory-model.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch01): rewrite embedded C memory model chapter (B1)"
```

---

### Task 6: 第 2 章 volatile、const 与未定义行为

**Files:**
- Create: `docs/v0-foundations/02-c-volatile-ub.md`
- Create: `docs/.vitepress/data/quizzes/c03-volatile.json`（从 `mcu/docs/.vitepress/data/quizzes/c03-volatile.json` 原样复制）
- Modify: `book/data/mapping.tsv`（2 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/c/03-volatile.md`、`mcu/docs/c/07-ub-misra.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "volatile、const 与未定义行为"
platforms: [generic]
---
```

必须覆盖：as-if 规则与优化器世界观；volatile 的访存合同与四个现场取证；`const`/`volatile` 组合语义；UB 优化逻辑；移位雷区；严格别名（`float`/`uint32` 互看用 `union`/`memcpy`）；MISRA 边界。
图片（至少 3 张）：`/figures/c-03-volatile.svg`、`/anim/volatile-as-if.svg`、`/figures/c-07-strict-alias.svg`、`/anim/ub-compiler-trap.svg`。
正文放置 `<QuizBank chapter="c03-volatile" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
mkdir -p docs/.vitepress/data/quizzes
cp mcu/docs/.vitepress/data/quizzes/c03-volatile.json docs/.vitepress/data/quizzes/c03-volatile.json
```

`mcu/docs/c/03-volatile.md`、`mcu/docs/c/07-ub-misra.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch02`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v0-foundations/02-c-volatile-ub.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 2 pages, 50 planned chapters missing`

Run: `python -m book.mapping --check`
Expected: exit 0

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/02-c-volatile-ub.md docs/.vitepress/data/quizzes/c03-volatile.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch02): rewrite volatile and undefined behavior chapter (B1)"
```

---

### Task 7: 第 3 章 结构体、ABI 与寄存器映射

**Files:**
- Create: `docs/v0-foundations/03-struct-abi-registers.md`
- Modify: `book/data/mapping.tsv`（1 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/c/04-struct-abi.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "结构体、ABI 与寄存器映射"
platforms: [f407, f103]
---
```

必须覆盖：`GPIO_TypeDef` 解剖；对齐三规则；填充可视化；位域陷阱；结构体作为寄存器映射的边界（结构体传参与返回约定留给第 4 章）。
图片（至少 2 张）：`/figures/c-04-struct-abi.svg`、`/anim/struct-alignment.svg`。
至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`mcu/docs/c/04-struct-abi.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch03`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v0-foundations/03-struct-abi-registers.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 3 pages, 49 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/03-struct-abi-registers.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch03): rewrite struct ABI and register mapping chapter (B1)"
```

---

### Task 8: 第 4 章 函数指针、状态机与调用约定

**Files:**
- Create: `docs/v0-foundations/04-function-pointer-state-machine.md`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/c/05-func-pointer.md`、`mcu/docs/c/06-abi-stack.md`、`docs/04-中断与NVIC.md`（仅驱动基本功/中断服务函数签名部分；NVIC 细节留给第 10 章）

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "函数指针、状态机与调用约定"
platforms: [f407, f103]
---
```

必须覆盖：声明阅读法与 `typedef`；向量表=Flash 里的函数指针数组；查表法状态机 `fsm_feed`；环形缓冲满/空判定两派；AAPCS 参数落位（r0–r3、第 5 个起走栈、64 位偶奇寄存器对）；栈帧；中断服务函数签名为何必须符合调用约定。
图片（至少 3 张）：`/figures/c-05-fsm-table.svg`、`/anim/ring-buffer.svg`、`/anim/stack-frame.svg`、`/figures/c-06-abi-stack.svg`。
至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`mcu/docs/c/05-func-pointer.md`、`mcu/docs/c/06-abi-stack.md` → `migrated`；`docs/04-中断与NVIC.md` → `partial`（第 10 章未写）。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch04`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v0-foundations/04-function-pointer-state-machine.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 4 pages, 48 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/04-function-pointer-state-machine.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch04): rewrite function pointers and calling convention chapter (B1)"
```

---

### Task 9: 第 5 章 工具链与四步构建

**Files:**
- Create: `docs/v0-foundations/05-toolchain-four-steps.md`
- Modify: `book/data/mapping.tsv`（5 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/build/00-toolchain.md`、`mcu/docs/build/01-four-steps.md`、`mcu/docs/build/02-elf.md`、`mcu/docs/stm32/00-env.md`、`docs/01-开发环境搭建.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "工具链与四步构建"
platforms: [generic]
---
```

必须覆盖：build/host/target 三胞胎；binutils 七件兵器；newlib 与钩子；`gcc -###` 调度员；`-E`/`-S`/`-c`/链接四步；ELF 头五字段与节表；环境搭建五步（交叉编译器、make、OpenOCD、ST-Link 驱动、SWD 接线）。
图片（至少 3 张）：`/arch/toolchain-pipeline.png`、`/anim/build-four-steps.svg`、`/anim/elf-sections.svg`、`/anim/elf-two-views.svg`、`/anim/env-setup-flow.svg`、`/images/boards/stm32f407-board.jpg`。
至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`docs/01-开发环境搭建.md`、`mcu/docs/build/00-toolchain.md`、`01-four-steps.md`、`02-elf.md`、`mcu/docs/stm32/00-env.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch05`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v0-foundations/05-toolchain-four-steps.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 5 pages, 47 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/05-toolchain-four-steps.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch05): rewrite toolchain and four-step build chapter (B1)"
```

---

### Task 10: 第 6 章 链接脚本、启动与 map 体积审计

**Files:**
- Create: `docs/v0-foundations/06-linker-startup-map.md`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/build/03-linker-script.md`、`mcu/docs/build/04-startup.md`、`mcu/docs/build/05-map-size.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "链接脚本、启动与 map 体积审计"
platforms: [f407]
---
```

必须覆盖：链接脚本 136 行三段结构（契约头、MEMORY、SECTIONS）；向量表必须住头排；`.data` 的 VMA/LMA 双地址；启动五站（硬件两读、开 FPU、搬 `.data`、清 `.bss`、`bl main`）；size 三列账；map 三板斧；nm 按大小审计。
图片（至少 3 张）：`/arch/linker-map.png`、`/anim/data-vma-lma.svg`、`/arch/boot-sequence.png`、`/anim/boot-sequence.svg`、`/arch/map-audit.png`、`/anim/map-size-audit.svg`。
至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`mcu/docs/build/03-linker-script.md`、`04-startup.md`、`05-map-size.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch06`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v0-foundations/06-linker-startup-map.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 6 pages, 46 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/06-linker-startup-map.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch06): rewrite linker script and startup chapter (B1)"
```

---

### Task 11: 第 7 章 构建系统与遗留栈

**Files:**
- Create: `docs/v0-foundations/07-build-systems-legacy.md`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/build/07-build-system.md`、`docs/26-STM32F10x标准外设库SPL.md`、`mcu/docs/stm32/15-spl-anatomy.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "构建系统与遗留栈"
platforms: [f103, esp32]
---
```

必须覆盖：Make 依赖图三要素与局部重建；CMake 生成层与 Ninja；IDF/scons 同骨架；Kconfig 是独立一维；SPL 最小闭环（版本钉死、工程骨架、调用模型、中断/DMA 模型）；`GPIO_Init` 逐行解剖与 SPL 三层。
图片（至少 2 张）：`/anim/build-dep-graph.svg`、`/anim/spl-gpio-init.svg`、`/arch/spl-anatomy.png`、`/figures/stm32-15-spl-tiers.svg`。
至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`mcu/docs/build/07-build-system.md`、`docs/26-STM32F10x标准外设库SPL.md`、`mcu/docs/stm32/15-spl-anatomy.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch07`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v0-foundations/07-build-systems-legacy.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 7 pages, 45 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v0-foundations/07-build-systems-legacy.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch07): rewrite build systems and legacy stack chapter (B1)"
```

---

### Task 12: 第 8 章 架构、存储器地图与时钟树

**Files:**
- Create: `docs/v1-drivers/08-architecture-memory-clock.md`
- Create: `docs/.vitepress/data/quizzes/s02-rcc-clock.json`（从 MCU 原目录原样复制）
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/01-arch.md`、`mcu/docs/stm32/02-rcc-clock.md`、`docs/02-芯片选型与存储器时钟.md`（时钟部分）

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "架构、存储器地图与时钟树"
platforms: [f407, f103, gd32]
---
```

必须覆盖：4GB 地图；总线矩阵与五次访问；位带；四个时钟源；PLL 手算 M/N/P/Q；时钟树六闸门；根书时钟树部分。GD32 只写边界并指向第 28–29 章，不编造差异。
图片（至少 3 张）：`/arch/memory-map.png`、`/anim/bus-matrix.svg`、`/anim/bitband-alias.svg`、`/anim/rcc-clock-tree.svg`、`/anim/rcc-six-gates.svg`、`/figures/stm32-01-m4-core.svg`。
正文放置 `<QuizBank chapter="s02-rcc-clock" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s02-rcc-clock.json docs/.vitepress/data/quizzes/s02-rcc-clock.json
```

`mcu/docs/stm32/01-arch.md`、`02-rcc-clock.md` → `migrated`；`docs/02-芯片选型与存储器时钟.md` → `migrated`（第 1 章已完成）。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch08`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/08-architecture-memory-clock.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 8 pages, 44 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/08-architecture-memory-clock.md docs/.vitepress/data/quizzes/s02-rcc-clock.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch08): rewrite architecture and clock chapter (B1)"
```

---

### Task 13: 第 9 章 GPIO

**Files:**
- Create: `docs/v1-drivers/09-gpio.md`
- Create: `docs/.vitepress/data/quizzes/s03-gpio.json`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/03-gpio.md`、`docs/03-GPIO与LED.md`、`mcu/docs/lab/e01-blink.md`（实验拆入本章；方法论文本留给第 40 章）

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "GPIO"
platforms: [f407, f103, gd32, esp32]
---
```

必须覆盖：时钟先行（`RCC_AHB1ENR`）；MODER/OTYPER/OSPEEDR/PUPDR 四维；BSRR 原子置位与 `ODR |=` 的读改写风险；复用 AF；输入采样与消抖边界；F1 与 F4 寄存器差异；实验 e01 点亮 RGB（接线、现象、记录格式）。GD32/ESP32 只写边界并指向卷 4。
图片（至少 3 张）：`/anim/gpio-config.svg`、`/figures/stm32-03-gpio-input.svg`、`/figures/stm32-03-slew.svg`、`/images/labs/e01-rgb-led.svg`。
正文放置 `<QuizBank chapter="s03-gpio" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s03-gpio.json docs/.vitepress/data/quizzes/s03-gpio.json
```

`mcu/docs/stm32/03-gpio.md`、`docs/03-GPIO与LED.md` → `migrated`；`mcu/docs/lab/e01-blink.md` → `partial`（第 40 章未写）。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch09`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/09-gpio.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 9 pages, 43 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/09-gpio.md docs/.vitepress/data/quizzes/s03-gpio.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch09): rewrite GPIO chapter (B1)"
```

---

### Task 14: 第 10 章 中断、NVIC/EXTI、CLIC 与双核

**Files:**
- Create: `docs/v1-drivers/10-interrupts-nvic-exti.md`
- Create: `docs/.vitepress/data/quizzes/s04-nvic.json`
- Modify: `book/data/mapping.tsv`（4 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/04-nvic-exti.md`、`docs/04-中断与NVIC.md`、`mcu/docs/esp32/04-irq-dualcore.md`（双核部分入本章；Cache 部分留给第 34 章）

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "中断、NVIC/EXTI、CLIC 与双核"
platforms: [f407, f103, gd32, esp32]
---
```

必须覆盖：三层链路（EXTI→NVIC→向量表）；`IRQn/32` 与 `IRQn%32` 寻址；优先级 4 位字段、分组与 `0x5FA`；向量表槽号 `IRQn + 16`、weak 顶替的实证；EXTI 链；ESP32 中断分配器、`IRAM_ATTR` 与双核分工（对照边界，Cache 一致性指向第 34 章）。GD32 只写边界。
图片（至少 3 张）：`/arch/exti-chain.png`、`/figures/stm32-04-nvic-addr.svg`、`/anim/irq-entry.svg`、`/anim/nvic-preempt-arbitration.svg`、`/anim/iram-discipline.svg`、`/figures/esp32-04-int-alloc.svg`。
正文放置 `<QuizBank chapter="s04-nvic" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s04-nvic.json docs/.vitepress/data/quizzes/s04-nvic.json
```

`mcu/docs/stm32/04-nvic-exti.md` → `migrated`；`docs/04-中断与NVIC.md` → `migrated`；`mcu/docs/esp32/04-irq-dualcore.md` → `partial`（第 34 章未写）。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch10`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/10-interrupts-nvic-exti.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 10 pages, 42 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/10-interrupts-nvic-exti.md docs/.vitepress/data/quizzes/s04-nvic.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch10): rewrite interrupts and NVIC chapter (B1)"
```

---

### Task 15: 第 11 章 SysTick 与时基（含 RTC）

**Files:**
- Create: `docs/v1-drivers/11-systick-timebase-rtc.md`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/05-systick.md`、`docs/05-定时器与PWM.md`（时基部分）、`docs/11-RTC与看门狗.md`（RTC 部分；看门狗留给第 19 章）

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "SysTick 与时基（含 RTC）"
platforms: [f407, f103]
---
```

必须覆盖：SysTick 四寄存器固定在 `0xE000E010`；CTRL 四位的开关/中断/时钟源与“读过就清”的 COUNTFLAG；周期 = LOAD + 1（167999 的来历与忘减一的账）；24 位上限；节拍换算与溢出；RTC 独立/备份域、LSE 与时间戳边界。
图片（至少 2 张）：`/anim/systick-tick.svg`、`/figures/stm32-05-tick-wrap.svg`。
至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`mcu/docs/stm32/05-systick.md` → `migrated`；`docs/05-定时器与PWM.md` → `partial`（第 12 章未写）；`docs/11-RTC与看门狗.md` → `partial`（第 19 章未写）。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch11`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/11-systick-timebase-rtc.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 11 pages, 41 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/11-systick-timebase-rtc.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch11): rewrite SysTick and timebase chapter (B1)"
```

---

### Task 16: 第 12 章 定时器与 PWM

**Files:**
- Create: `docs/v1-drivers/12-timers-pwm.md`
- Create: `docs/.vitepress/data/quizzes/s06-tim.json`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/06-tim.md`、`docs/05-定时器与PWM.md`（PWM 部分）、`mcu/docs/lab/e03-scope-pwm.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "定时器与 PWM"
platforms: [f407, f103, esp32]
---
```

必须覆盖：时基三件套 PSC/CNT/ARR；PWM 占空比；定时中断与 SysTick 的分工；输入捕获/编码器界面；HAL 三段初始化（MspInit / ConfigChannel / Start）与手写落位对账；实验 e03 用示波器测 PWM（接线、现象、记录）。ESP32 只写边界并指向第 31 章。
图片（至少 3 张）：`/anim/tim-pwm-counter.svg`、`/figures/stm32-06-tim.svg`、`/anim/tim-input-capture.svg`、`/figures/stm32-06-encoder.svg`、`/anim/tim-hal-init-path.svg`、`/images/labs/e03-pwm-probe.svg`、`/images/tools/oscilloscope-ds1054z.jpg`。
正文放置 `<QuizBank chapter="s06-tim" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s06-tim.json docs/.vitepress/data/quizzes/s06-tim.json
```

`mcu/docs/stm32/06-tim.md` → `migrated`；`docs/05-定时器与PWM.md` → `migrated`；`mcu/docs/lab/e03-scope-pwm.md` → `partial`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch12`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/12-timers-pwm.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 12 pages, 40 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/12-timers-pwm.md docs/.vitepress/data/quizzes/s06-tim.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch12): rewrite timers and PWM chapter (B1)"
```

---

### Task 17: 第 13 章 UART 与可恢复帧协议

**Files:**
- Create: `docs/v1-drivers/13-uart-framed-protocol.md`
- Create: `docs/.vitepress/data/quizzes/s07-usart.json`
- Modify: `book/data/mapping.tsv`（4 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/07-usart.md`、`docs/06-串口UART.md`、`mcu/docs/c/08-framed-protocol.md`、`mcu/docs/lab/e02-logic-uart.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "UART 与可恢复帧协议"
platforms: [f407, f103, esp32, gd32]
---
```

必须覆盖：一帧结构（起始/数据/停止）；`baud = PCLK / BRR`；TXE/TC 与中断/DMA 收发边界；HAL Init/Transmit 与手写落位对账（MspInit + SetConfig 两层）；可恢复帧协议（定界、COBS、CRC-16/CCITT-FALSE、逐字节状态机）；实验 e02 逻辑分析仪抓帧；与第 14 章 DMA 分工。GD32/ESP32 只写边界。
图片（至少 4 张）：`/anim/uart-frame.svg`、`/figures/stm32-07-usart-brr.svg`、`/figures/stm32-07-usart.svg`、`/anim/usart-txe-tc.svg`、`/anim/uart-hal-init-path.svg`、`/anim/c08-frame-parse.svg`、`/figures/c-08-framed-protocol.svg`、`/images/labs/e02-uart-capture.svg`、`/images/tools/logic-analyzer-8ch.jpg`。
正文放置 `<QuizBank chapter="s07-usart" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s07-usart.json docs/.vitepress/data/quizzes/s07-usart.json
```

`mcu/docs/stm32/07-usart.md`、`mcu/docs/c/08-framed-protocol.md`、`docs/06-串口UART.md` → `migrated`；`mcu/docs/lab/e02-logic-uart.md` → `partial`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch13`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/13-uart-framed-protocol.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 13 pages, 39 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/13-uart-framed-protocol.md docs/.vitepress/data/quizzes/s07-usart.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch13): rewrite UART and framed protocol chapter (B1)"
```

---

### Task 18: 第 14 章 DMA

**Files:**
- Create: `docs/v1-drivers/14-dma.md`
- Create: `docs/.vitepress/data/quizzes/s08-dma.json`
- Modify: `book/data/mapping.tsv`（2 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/08-dma.md`、`docs/10-DMA.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "DMA"
platforms: [f407, f103]
---
```

必须覆盖：流与通道的二级选择；PAR/M0AR/NDTR 三地址一长度；循环模式；乒乓/双缓冲；HAL 使能窗口；与 UART/ADC 联动的边界。
图片（至少 3 张）：`/arch/dma-paths.png`、`/figures/stm32-08-dma-stream.svg`、`/figures/stm32-08-dma.svg`、`/anim/dma-circular-buffer.svg`、`/anim/dma-pingpong.svg`、`/anim/dma-hal-en-window.svg`。
正文放置 `<QuizBank chapter="s08-dma" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s08-dma.json docs/.vitepress/data/quizzes/s08-dma.json
```

`mcu/docs/stm32/08-dma.md`、`docs/10-DMA.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch14`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/14-dma.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 14 pages, 38 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/14-dma.md docs/.vitepress/data/quizzes/s08-dma.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch14): rewrite DMA chapter (B1)"
```

---

### Task 19: 第 15 章 ADC/DAC 与采样

**Files:**
- Create: `docs/v1-drivers/15-adc-dac-sampling.md`
- Create: `docs/.vitepress/data/quizzes/s09-adc.json`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/09-adc.md`、`mcu/docs/stm32/10-dac.md`、`docs/09-ADC与DAC.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "ADC/DAC 与采样"
platforms: [f407, f103]
---
```

必须覆盖：ADC 版图；SAR 逐次逼近 12 次二分；一个 LSB = 805.7 µV；采样时间与多通道扫描/分组；DAC 电阻网络 vs PWM+RC；静态输出先写一个数量一个电压。
图片（至少 3 张）：`/anim/sar-successive.svg`、`/figures/stm32-09-adc.svg`、`/figures/stm32-09-adc-groups.svg`、`/anim/dac-trio.svg`、`/figures/stm32-10-r2r-pwm.svg`。
正文放置 `<QuizBank chapter="s09-adc" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s09-adc.json docs/.vitepress/data/quizzes/s09-adc.json
```

`mcu/docs/stm32/09-adc.md`、`10-dac.md`、`docs/09-ADC与DAC.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch15`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/15-adc-dac-sampling.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 15 pages, 37 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/15-adc-dac-sampling.md docs/.vitepress/data/quizzes/s09-adc.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch15): rewrite ADC and DAC chapter (B1)"
```

---

### Task 20: 第 16 章 I2C 与 SPI

**Files:**
- Create: `docs/v1-drivers/16-i2c-spi.md`
- Create: `docs/.vitepress/data/quizzes/s11-i2c.json`、`docs/.vitepress/data/quizzes/s12-spi.json`
- Modify: `book/data/mapping.tsv`（6 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/11-i2c.md`、`mcu/docs/stm32/12-spi.md`、`docs/07-I2C总线.md`、`docs/08-SPI总线.md`、`mcu/docs/lab/e05-i2c-eeprom.md`、`mcu/docs/lab/e07-qmi8658.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "I2C 与 SPI"
platforms: [f407, f103, esp32]
---
```

必须覆盖：I2C 礼仪三件套 START/STOP/ACK；地址与方向；repeated start 读 EEPROM；事件寄存器；SPI 移位环、CPOL/CPHA 四模式与 Mode 0 采样；实验 e05 EEPROM 与 e07 QMI8658（接线、现象、记录）。ESP32 只写边界并指向第 31 章。
图片（至少 4 张）：`/arch/i2c-bus.png`、`/anim/i2c-timing.svg`、`/figures/stm32-11-i2c.svg`、`/figures/stm32-11-ee-repeated-start.svg`、`/figures/stm32-11-i2c-event.svg`、`/anim/spi-timing.svg`、`/figures/stm32-12-spi.svg`、`/figures/stm32-12-spi-modes.svg`、`/images/labs/e05-i2c-wiring.svg`、`/images/labs/e07-qmi8658-axes.svg`、`/images/tools/eeprom-24c02.jpg`。
正文放置 `<QuizBank chapter="s11-i2c" />` 与 `<QuizBank chapter="s12-spi" />`；至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 复制测验并更新映射状态**

```bash
cp mcu/docs/.vitepress/data/quizzes/s11-i2c.json docs/.vitepress/data/quizzes/s11-i2c.json
cp mcu/docs/.vitepress/data/quizzes/s12-spi.json docs/.vitepress/data/quizzes/s12-spi.json
```

`mcu/docs/stm32/11-i2c.md`、`12-spi.md`、`docs/07-I2C总线.md`、`docs/08-SPI总线.md` → `migrated`；`mcu/docs/lab/e05-i2c-eeprom.md`、`e07-qmi8658.md` → `partial`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch16`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/16-i2c-spi.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 16 pages, 36 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/16-i2c-spi.md docs/.vitepress/data/quizzes/s11-i2c.json docs/.vitepress/data/quizzes/s12-spi.json book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch16): rewrite I2C and SPI chapter (B1)"
```

---

### Task 21: 第 17 章 Flash、IAP 与 OTA

**Files:**
- Create: `docs/v1-drivers/17-flash-iap-ota.md`
- Modify: `book/data/mapping.tsv`（3 行状态）、regenerate `mapping.json`

**Sources（只读）:** `mcu/docs/stm32/13-flash-iap.md`、`docs/12-Flash与IAP升级.md`、`mcu/docs/esp32/10-flash-nvs-ota.md`

- [ ] **Step 1: 写章节**

frontmatter：

```yaml
---
title: "Flash、IAP 与 OTA"
platforms: [f407, f103, esp32]
---
```

必须覆盖：扇区地图与参数区选择；解锁序列（两把钥匙与并行度）；擦写寿命；IAP 跳转与向量表重定位；OTA 双槽与回滚；ESP32 分区表/NVS 对照（只写来源事实）。
图片（至少 3 张）：`/anim/iap-handoff.svg`、`/figures/stm32-13-flash-iap.svg`、`/figures/stm32-13-flash-seq.svg`、`/arch/ota-slots.png`、`/anim/esp32-ota-rollback.svg`、`/figures/esp32-10-flash-nvs-ota.svg`。
至少 1 条指向其它新章的相对 `.md` 链接。

- [ ] **Step 2: 更新映射状态**

`mcu/docs/stm32/13-flash-iap.md`、`docs/12-Flash与IAP升级.md`、`mcu/docs/esp32/10-flash-nvs-ota.md` → `migrated`。
Run: `python -m book.mapping --write`

- [ ] **Step 3: 验证**

Run: `python -m book.checks --chapter ch17`
Expected: `checks passed`

Run: `python tools/slop_lint.py docs/v1-drivers/17-flash-iap-ota.md`
Expected: exit 0

Run: `python -m book.build_html --check`
Expected: `built 17 pages, 35 planned chapters missing`

- [ ] **Step 4: 提交**

```bash
git add docs/v1-drivers/17-flash-iap-ota.md book/data/mapping.tsv plans/2026-11-12-merged-book/mapping.json
git commit -m "feat(ch17): rewrite Flash and OTA chapter (B1)"
```

---

### Task 22: CI 接入、批次记录与 B1 证据

**Files:**
- Modify: `.github/workflows/merge-check.yml`
- Modify: `plans/2026-11-12-merged-book/README.md`
- Create: `plans/2026-11-12-merged-book/evidence/b1-local.md`

**Interfaces:**
- Consumes: Task 1–21 全部产物
- Produces: main 分支可运行的 B1 质量门；批次记录与本地证据

- [ ] **Step 1: 扩展 `merge-check.yml`**

在 `pull_request.paths` 与 `push.paths` 两个列表中都加入（保持两处一致）：

```yaml
      - 'tools/slop_lint.py'
```

在 `Set up Python` 之后、`Run book checks` 之前插入：

```yaml
      - name: Install book build deps
        run: python -m pip install -r book/requirements.txt
```

把 `Run book checks` 的脚本替换为：

```yaml
        run: |
          python -m book.manifest --check
          python -m book.mapping --check
          python -m unittest discover book/tests -v
          python -m book.checks --check
          python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md
          python -m book.build_html --check
```

- [ ] **Step 2: 更新批次记录 `plans/2026-11-12-merged-book/README.md`**

- B1 行状态改为 `本批完成（本地）`。
- 「本批校验命令」更新为：

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
python -m book.checks --check
python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md
python -m book.build_html --check
node --test scripts/tests/legacy-redirects.test.mjs
```

- 「数据文件」补充：`book/data/mapping.tsv` 含 `purpose`、`status`（planned/partial/migrated），状态必须与章节文件存在性一致；`book/requirements.txt` 固定 `markdown==3.11`。
- 「说明」补充：临时静态站由 `book/build_html.py` 生成到 `book/dist/site/`（已 gitignore）；VitePress 站点切换仍归 B5。

- [ ] **Step 3: 全量本地验收并写证据 `plans/2026-11-12-merged-book/evidence/b1-local.md`**

依次运行并记录真实输出与退出码：

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
python -m book.checks --check
python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md
python -m book.build_html --check
node --test scripts/tests/legacy-redirects.test.mjs
```

证据文件必须如实包含：分支名、HEAD 提交、Python/Node 版本、上述命令的真实输出摘要与退出码、17 章文件名清单、10 组测验 id 清单、`built 17 pages, 35 planned chapters missing`、以及“未验证：CI 远程运行结果；未执行任何远程推送或 Pages 切换”。

- [ ] **Step 4: 提交**

```bash
git add .github/workflows/merge-check.yml plans/2026-11-12-merged-book/README.md plans/2026-11-12-merged-book/evidence/b1-local.md
git commit -m "chore(ci): enable B1 chapter gates and record local evidence (B1)"
```

---

## Self-Review 记录

- **Spec 覆盖**：B1 出口的「17 章改写」→ Task 5–21；「罗盘」→ Task 2 `validate_chapter_file` + 每章 Step 3；「slop_lint」→ 每章 Step 3 + Task 22 CI；「锚点」→ Task 2 链接/锚点检查；「资产」→ Task 4 + Task 2 资产检查；「测验」→ 各章测验复制 + Task 2 schema/孤儿/重复检查；「站点临时构建」→ Task 3 `build_html --check`。R8（mapping 逐源用途/状态）→ Task 1。R10（B0 构建证据顺延）→ Task 22 证据文件。
- **占位符扫描**：无 TBD/TODO；所有代码块为完整实现；章节任务给出 frontmatter、必覆盖要点、资产清单、测验与状态更新。
- **类型一致性**：`load_rows` 的 6 字段、`check_file` 返回 `(errors, quiz_ids)`、`check_book(only=...)`、`build(...) -> (pages, missing)` 在测试、CLI 与后续任务中一致；`cjk_slugify(value, separator)` 同时供检查器与 Markdown toc 使用。
- **已知边界**：状态机按章节文件存在性推导，附录章（apA–apF）在 B4 前保持 `planned`；临时站是 `book/build_html.py` 产物，不是 VitePress 站（B5 切换）；测验只迁移卷 0–1 相关的 10 组，`f4-queue`、`f7-heap`、`s14-pwr` 留给 B2/B3。
