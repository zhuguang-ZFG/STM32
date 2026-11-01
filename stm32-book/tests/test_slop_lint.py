"""The plain-voice gate: no AI-flavoured writing, and the detector works.

A clean report only means something if the checker can fail, so the detector is
exercised on planted text as well as on the repository.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINT_PATH = ROOT / "tools" / "slop_lint.py"


def load_linter():
    if "slop_lint" in sys.modules:
        return sys.modules["slop_lint"]
    spec = importlib.util.spec_from_file_location("slop_lint", LINT_PATH)
    module = importlib.util.module_from_spec(spec)
    # The linter holds a frozen dataclass, and resolving its annotations needs
    # the module to be findable by name while it executes.
    sys.modules["slop_lint"] = module
    spec.loader.exec_module(module)
    return module


class SlopLintDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lint = load_linter()

    def groups(self, text: str) -> set[str]:
        return {hit.group for hit in self.lint.lint(text, "planted.md")}

    def test_catches_chinese_stock_phrases_and_marketing(self) -> None:
        self.assertIn("中文套话", self.groups("让我们一起看看这个外设。"))
        self.assertIn("中文套话", self.groups("综上所述，时钟配置值得注意的是分频。"))
        self.assertIn("中文营销词", self.groups("这个库赋能开发者，一站式解决所有问题。"))
        self.assertIn("中文虚假坦诚", self.groups("说实话，这里划重点。"))

    def test_catches_english_tells(self) -> None:
        self.assertIn("英文 AI 词典", self.groups("Let's delve into this robust peripheral."))
        self.assertIn("英文 AI 词典", self.groups("A comprehensive and seamless solution."))
        self.assertIn(
            "英文虚假坦诚与软收尾", self.groups("Hope this helps! Let me know if you need more.")
        )

    def test_catches_glyphs_standing_in_for_words(self) -> None:
        self.assertIn("判定符号应写成文字", self.groups("| FPU | ❌ | ✅ 单精度 |"))
        self.assertIn("警告请用 > [!WARNING]", self.groups("> ⚠️ 不要关掉 SWD。"))
        self.assertIn("装饰性 emoji", self.groups("- 📱 手机阅读版：链接"))

    def test_catches_emoji_in_headings(self) -> None:
        self.assertIn("标题里的 emoji", self.groups("## 📌 学习目标"))
        self.assertIn("标题里的 emoji", self.groups("## 🧠 核心原理"))

    def test_catches_a_fence_with_no_language(self) -> None:
        self.assertIn("代码块没写语言", self.groups("```\n1 LSB = Vref / 2^N\n```\n"))
        self.assertEqual(set(), self.groups("```text\n1 LSB = Vref / 2^N\n```\n"))
        self.assertEqual(set(), self.groups("```c\nint x = 0;\n```\n"))
        # A closing fence is bare by definition and must not be reported.
        self.assertEqual(1, len(self.lint.lint("```\nx\n```\n", "t.md")))

    def test_star_ratings_and_plain_headings_are_allowed(self) -> None:
        """★ is the project chapter's rating scale, and it is contract-tested."""
        self.assertEqual(set(), self.groups("## 1. 蓝牙小车（★★ 入门级）"))
        self.assertEqual(set(), self.groups("## 7. 简易逻辑分析仪（★★★★ 挑战）"))
        self.assertEqual(set(), self.groups("## 学习目标"))

    def test_correct_typography_is_not_flagged(self) -> None:
        """An empty table cell, a numeric range, and 破折号 are all correct."""
        self.assertEqual(set(), self.groups("| PA13 | SWDIO | — | 调试数据线 |"))
        self.assertEqual(set(), self.groups("48–72 MHz 这一档是 2 个等待。"))
        self.assertEqual(set(), self.groups("底层都是同一条工具链——编译、链接、烧录。"))

    def test_technical_verbs_are_not_flagged(self) -> None:
        """unlock and 支持 are the right words for what they describe."""
        self.assertEqual(set(), self.groups("Walk the sequence: unlock (KEY1 / KEY2) then erase."))
        self.assertEqual(set(), self.groups("| STM32 支持 | 支持，推荐 | 支持但少用 |"))

    def test_code_links_and_quotes_are_scrubbed(self) -> None:
        """A banned word is legitimate inside code, a link target, or a quote."""
        self.assertEqual(set(), self.groups("调用 `leverage_robust()` 之后再读状态。"))
        self.assertEqual(set(), self.groups("见 [robust](https://example.com/comprehensive)。"))
        self.assertEqual(set(), self.groups("手册把它叫做「一站式」，这里照抄原词。"))

    def test_fences_and_directives_are_respected(self) -> None:
        fenced = "```c\n/* let's delve into robust code */\n```\n"
        self.assertEqual(set(), self.groups(fenced))
        self.assertEqual(set(), self.groups("让我们开始。 <!-- slop-lint: ignore -->"))
        off = "<!-- slop-lint: off -->\n让我们开始。\n<!-- slop-lint: on -->\n"
        self.assertEqual(set(), self.groups(off))


class PlainVoiceSkillTests(unittest.TestCase):
    """The skill states how the build behaves, so it must not drift from it."""

    SKILL = ROOT / ".claude" / "skills" / "plain-voice" / "SKILL.md"

    def setUp(self) -> None:
        self.text = self.SKILL.read_text(encoding="utf-8")

    def frontmatter(self) -> dict[str, str]:
        """Read the frontmatter under the rules a YAML loader would apply.

        Deliberately hand-rolled: the book's requirements do not carry a YAML
        parser, and the failure worth guarding is narrow. In an unquoted scalar
        a ``": "`` reopens the mapping, so the whole block stops parsing.
        """
        match = re.match(r"^---\n(.*?)\n---\n", self.text, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md must open with YAML frontmatter")
        data: dict[str, str] = {}
        for line in match.group(1).split("\n"):
            self.assertNotEqual("", line.strip(), "no blank line in frontmatter")
            self.assertFalse(line[:1].isspace(), f"no indented line: {line!r}")
            key, _, value = line.partition(":")
            self.assertTrue(_, f"frontmatter line needs a key: {line!r}")
            value = value.strip()
            quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
            if not quoted:
                self.assertNotIn(
                    ": ",
                    value,
                    f"unquoted {key!r} holds ': ', which reopens the mapping",
                )
            data[key.strip()] = value
        return data

    def test_frontmatter_parses_and_names_the_skill(self) -> None:
        data = self.frontmatter()
        self.assertEqual("plain-voice", data["name"])
        self.assertEqual({"name", "description", "license"}, set(data))
        self.assertIn("docs/en/", data["description"])
        self.assertTrue(data["license"])

    def test_the_alert_tokens_it_documents_are_the_ones_the_build_reads(self) -> None:
        builder_path = ROOT / "stm32-book" / "build_html.py"
        spec = importlib.util.spec_from_file_location("build_html_skill", builder_path)
        builder = importlib.util.module_from_spec(spec)
        sys.modules["build_html_skill"] = builder
        spec.loader.exec_module(builder)
        for token, kind in builder._ALERT_KIND.items():
            self.assertIn(f"[!{token.upper()}]", self.text)
            self.assertIn(kind, self.text)

    def test_the_escape_directives_it_documents_actually_work(self) -> None:
        lint = load_linter()
        for directive in ("slop-lint: ignore", "slop-lint: off", "slop-lint: on"):
            self.assertIn(directive, self.text)
        self.assertEqual([], lint.lint("让我们开始。 <!-- slop-lint: ignore -->", "s.md"))

    def test_the_skill_passes_its_own_gate(self) -> None:
        lint = load_linter()
        self.assertEqual([], lint.lint(self.text, self.SKILL.name))


class SlopLintRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lint = load_linter()

    def test_every_markdown_file_in_the_repo_is_clean(self) -> None:
        hits = []
        for path in self.lint.targets([]):
            rel = path.relative_to(ROOT).as_posix()
            hits += self.lint.lint(path.read_text(encoding="utf-8"), rel)
        detail = "\n".join(
            f"{hit.path}:{hit.line_no} [{hit.group}] {hit.match!r}" for hit in hits[:40]
        )
        self.assertEqual([], hits, f"AI 味命中 {len(hits)} 处：\n{detail}")

    def test_the_gate_actually_scans_the_book(self) -> None:
        """Guard against a skip list that quietly empties the scan."""
        scanned = {path.relative_to(ROOT).as_posix() for path in self.lint.targets([])}
        for required in (
            "README.md",
            "CONTRIBUTING.md",
            "docs/03-GPIO与LED.md",
            "docs/en/03-gpio-and-led.md",
            "docs/19-项目实战合集.md",
            "cheatsheets/外设总线与引脚速查表.md",
            "stm32-book/book/D-术语表.md",
            ".claude/skills/plain-voice/SKILL.md",
        ):
            self.assertIn(required, scanned)
        self.assertGreater(len(scanned), 80)

    def test_only_the_vendored_skill_is_skipped_under_claude(self) -> None:
        """sepia quotes banned words in its rule tables; the house skill does not."""
        scanned = {path.relative_to(ROOT).as_posix() for path in self.lint.targets([])}
        self.assertFalse(any(p.startswith(".claude/skills/sepia") for p in scanned))
        self.assertTrue((ROOT / ".claude" / "skills" / "sepia" / "LICENSE").is_file())


if __name__ == "__main__":
    unittest.main()
