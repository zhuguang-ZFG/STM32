"""Link-check behaviour pinned to what each renderer really emits."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import md_links


class GithubSlugTests(unittest.TestCase):
    """Samples come from id="user-content-..." on rendered github.com pages.

    They were read off the site instead of re-derived, which is how the
    double-hyphen rule was found in the first place.
    """

    CASES = (
        ("HAL 速查表", "hal-速查表"),
        ("1. 系统与时钟（HAL / RCC）", "1-系统与时钟hal--rcc"),
        ("3. 中断（EXTI / NVIC / SysTick）", "3-中断exti--nvic--systick"),
        ("10. RTC 与备份域（RTC / RTC_EX / PWR）", "10-rtc-与备份域rtc--rtc_ex--pwr"),
        ("4. 常见现象 → 原因 → 定位手段", "4-常见现象--原因--定位手段"),
        ("3.1 FLASH（`HAL_FLASH_GetError()`）", "31-flashhal_flash_geterror"),
    )

    def test_matches_rendered_ids(self) -> None:
        for title, expected in self.CASES:
            with self.subTest(title=title):
                self.assertEqual(md_links.github_slug(title), expected)

    def test_duplicate_headings_get_suffix(self) -> None:
        anchors = md_links.github_anchors("## 重复\n\n## 重复\n")
        self.assertEqual(anchors, {"重复", "重复-1"})

    def test_quoted_headings_count(self) -> None:
        # The root README links its badge to this card; github.com emits the id.
        anchors = md_links.github_anchors("> ### 公众号连载版\n")
        self.assertIn("公众号连载版", anchors)

    def test_fenced_headings_are_not_anchors(self) -> None:
        text = "```md\n# Fake\n```\n"
        self.assertEqual(md_links.github_anchors(text), set())

    def test_fenced_heading_does_not_steal_duplicate_suffix(self) -> None:
        text = "```md\n## Dup\n```\n\n## Dup\n"
        self.assertEqual(md_links.github_anchors(text), {"dup"})


class CheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_check(self, rel: str) -> list[str]:
        return md_links.check(self.root, [self.root / rel])

    def test_flags_missing_target(self) -> None:
        page = self.write("README.md", "[x](gone.md)\n")
        self.assertTrue(page.exists())
        errors = self.run_check("README.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("missing link target: gone.md", errors[0])

    def test_existing_target_passes(self) -> None:
        self.write("README.md", "[x](other.md)\n")
        self.write("other.md", "# 标题\n")
        self.assertEqual(self.run_check("README.md"), [])

    def test_public_paths_resolve_under_docs_public(self) -> None:
        self.write("docs/public/images/a.png", "png")
        self.write("docs/page.md", "![a](/images/a.png)\n")
        self.assertEqual(self.run_check("docs/page.md"), [])

    def test_html_attributes_are_checked(self) -> None:
        self.write("README.md", '<img src="assets/missing.svg" alt="x">\n')
        errors = self.run_check("README.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("assets/missing.svg", errors[0])

    def test_docs_fragments_follow_vitepress(self) -> None:
        heading = "## 1. 系统与时钟（HAL / RCC）\n"
        self.write("docs/page.md", heading + "\n[回到](#1-系统与时钟hal-rcc)\n")
        self.assertEqual(self.run_check("docs/page.md"), [])
        self.write("docs/page.md", heading + "\n[回到](#1-系统与时钟hal--rcc)\n")
        self.assertEqual(len(self.run_check("docs/page.md")), 1)

    def test_site_duplicate_headings_get_underscore_suffixes(self) -> None:
        """VitePress renames repeated slugs as `重复标题_1`, never `-1`."""
        self.write("docs/page.md", "## 重复\n\n## 重复\n\n[到](#重复_1)\n")
        self.assertEqual(self.run_check("docs/page.md"), [])
        self.write("docs/page.md", "## 重复\n\n## 重复\n\n[到](#重复-1)\n")
        errors = self.run_check("docs/page.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("missing anchor in docs/page.md: #重复-1", errors[0])

    def test_other_files_follow_github(self) -> None:
        heading = "## 1. 系统与时钟（HAL / RCC）\n"
        self.write("README.md", heading + "\n[回到](#1-系统与时钟hal--rcc)\n")
        self.assertEqual(self.run_check("README.md"), [])
        self.write("README.md", heading + "\n[回到](#1-系统与时钟hal-rcc)\n")
        self.assertEqual(len(self.run_check("README.md")), 1)

    def test_code_fences_are_ignored(self) -> None:
        self.write("README.md", "```\n[x](gone.md)\n```\n")
        self.assertEqual(self.run_check("README.md"), [])

    def test_deploy_artifacts_are_allowlisted(self) -> None:
        self.write("docs/index.md", "[PDF](book/merged-book.pdf)\n")
        self.assertEqual(self.run_check("docs/index.md"), [])

    def test_missing_anchor_is_reported(self) -> None:
        self.write("README.md", "[x](other.md#absent)\n")
        self.write("other.md", "# 标题\n")
        errors = self.run_check("README.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("missing anchor in other.md: #absent", errors[0])

    def test_fenced_heading_is_not_a_link_target(self) -> None:
        self.write("README.md", "```md\n# Fake\n```\n\n[到](#fake)\n")
        errors = self.run_check("README.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("missing anchor in README.md: #fake", errors[0])

    def test_inline_code_stays_in_heading_slug(self) -> None:
        self.write("README.md", "## FLASH（`HAL_FLASH_GetError()`）\n\n[到](#flashhal_flash_geterror)\n")
        self.assertEqual(self.run_check("README.md"), [])


class PathDecodingTests(unittest.TestCase):
    @unittest.skipUnless(
        shutil.which("git") and sys.getfilesystemencoding().lower() in ("utf-8", "utf8"),
        "needs git and a UTF-8 filesystem encoding to reach the path lookup",
    )
    def test_utf8_paths_survive_a_non_utf8_locale(self) -> None:
        """git emits UTF-8 path bytes; decoding them with the codepage fails.

        The child starts with a UTF-8 filesystem encoding and then narrows
        only ``LC_CTYPE``: the filesystem encoding is frozen at startup, while
        ``subprocess`` asks ``locale.getencoding()`` on every call, so the
        pipe decode turns ASCII while ``stat`` still reaches Chinese names.
        A stock Windows shell does the same split through its codepage
        (utf8_mode off, cp936 for pipes), which is the bug this pins.

        Turning utf8_mode off on POSIX would otherwise let an inherited C
        locale strip the child's filesystem encoding, so the child is given
        ``LC_ALL=C.UTF-8``; if it still starts non-UTF-8 it reports SKIP and
        the test is skipped, because it could not stat the filename at all.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "中文 示例.md").write_text("# 标题\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(root), "add", "-A"], check=True, capture_output=True
            )
            env = dict(os.environ, PYTHONUTF8="0")
            if os.name == "posix":
                # utf8_mode off downgrades the child's startup locale to whatever
                # LC_ALL says; C.UTF-8 keeps the filesystem encoding UTF-8 while
                # the later setlocale still narrows the per-call pipe decoding.
                env["LC_ALL"] = "C.UTF-8"
                env.pop("PYTHONCOERCECLOCALE", None)
            script = "\n".join(
                [
                    "import locale, pathlib, sys",
                    "sys.path.insert(0, sys.argv[1])",
                    "if sys.getfilesystemencoding().lower() not in ('utf-8', 'utf8'):",
                    "    print('SKIP')",
                    "    sys.exit(0)",
                    "locale.setlocale(locale.LC_CTYPE, 'C')",
                    "from book import md_links",
                    "print(len(md_links.markdown_files(pathlib.Path(sys.argv[2]))))",
                ]
            )
            result = subprocess.run(
                [sys.executable, "-c", script, str(ROOT), str(root)],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if result.stdout.strip() == "SKIP":
                self.skipTest(
                    "child started without a UTF-8 filesystem encoding; "
                    "it cannot stat the Chinese filename, so this bug class is unreachable"
                )
            self.assertEqual(result.stdout.strip(), "1")


if __name__ == "__main__":
    unittest.main()
