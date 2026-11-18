"""Repository ownership regressions using real temporary Git indexes/worktrees.

The fixtures never commit, stage, or change anything in the user's checkout.
A separate-git-dir checkout exercises the same .git-file ownership boundary as
linked worktrees; the live end-to-end reproduction also covers linked worktrees.
"""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import slop_lint


class SlopScopeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="slop-scope-")
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)
        self.root = self.tmp / "root"
        self.root.mkdir()
        self.git("init", "--quiet", "--template=", str(self.root))
        empty = self.tmp / "empty-ignore"
        empty.write_text("", encoding="utf-8")
        self.git("config", "core.excludesFile", str(empty))
        self.git("config", "core.autocrlf", "false")
        patched = patch.object(slop_lint, "ROOT", self.root)
        patched.start()
        self.addCleanup(patched.stop)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def write(self, name, text="普通技术说明。\n"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def names(self):
        return {p.relative_to(self.root).as_posix()
                for p in slop_lint.targets([])}

    def run_lint(self, files=None):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return slop_lint.main(files or [])

    def test_nested_git_directory_is_not_parent_repository_source(self):
        self.write("docs/current.md")
        nested = self.root / "local" / "foreign"
        self.git("init", "--quiet", "--template=", str(nested))
        self.write("local/foreign/research.md", "综上所述。\n")
        self.assertEqual(self.names(), {"docs/current.md"})
        self.assertEqual(self.run_lint(), 0)

    def test_nested_gitfile_checkout_is_not_parent_repository_source(self):
        nested = self.root / "local" / "worktree"
        self.git("init", "--quiet", "--template=", "--separate-git-dir",
                 str(self.tmp / "worktree-git"), str(nested))
        self.assertTrue((nested / ".git").is_file())
        self.write("local/worktree/research.md", "综上所述。\n")
        self.assertEqual(self.names(), set())
        self.assertEqual(self.run_lint(), 0)

    def test_parent_index_source_survives_nested_repository_marker(self):
        self.write("local/foreign/published.md", "综上所述。\n")
        self.git("add", "local/foreign/published.md")
        self.git("init", "--quiet", "--template=",
                 str(self.root / "local" / "foreign"))
        self.write("local/foreign/private.md", "综上所述。\n")
        # An overlapping parent index makes Git conservatively retain pending
        # siblings too. Never prune the directory merely because .git exists.
        self.assertEqual(self.names(), {"local/foreign/published.md",
                                        "local/foreign/private.md"})
        self.assertEqual(self.run_lint(), 1)

    def test_ignored_untracked_output_is_not_source(self):
        self.write(".gitignore", "local-output/\n")
        self.write("local-output/research.md", "综上所述。\n")
        self.assertEqual(self.names(), set())
        self.assertEqual(self.run_lint(), 0)

    def test_tracked_source_under_later_ignore_rule_is_still_checked(self):
        self.write("local-output/published.md", "综上所述。\n")
        self.git("add", "local-output/published.md")
        self.write(".gitignore", "local-output/\n")
        self.write("local-output/private.md", "综上所述。\n")
        self.assertIn("local-output/published.md", self.names())
        self.assertEqual(self.run_lint(), 1)

    def test_nonignored_pending_documents_including_qoder_name_are_checked(self):
        self.write("docs/pending.md", "综上所述。\n")
        self.write(".qoder/published.md", "综上所述。\n")
        self.assertEqual(self.names(), {"docs/pending.md", ".qoder/published.md"})
        self.assertEqual(self.run_lint(), 1)

    def test_tracked_source_violations_still_fail(self):
        self.write("docs/published.md", "综上所述。\n")
        self.git("add", "docs/published.md")
        self.assertEqual(self.names(), {"docs/published.md"})
        self.assertEqual(self.run_lint(), 1)

    def test_explicit_ignored_file_is_still_checked(self):
        self.write(".gitignore", "local-output/\n")
        source = self.write("local-output/research.md", "综上所述。\n")
        self.assertEqual(slop_lint.targets([str(source)]), [source])
        self.assertEqual(self.run_lint([str(source)]), 1)

    def test_deleted_index_entry_is_not_an_existing_source_file(self):
        source = self.write("docs/deleted.md", "综上所述。\n")
        self.git("add", "docs/deleted.md")
        source.unlink()
        self.assertEqual(self.names(), set())
        self.assertEqual(self.run_lint(), 0)

    def test_archive_without_git_keeps_filesystem_scan(self):
        archive = self.tmp / "archive"
        (archive / "ignored-name").mkdir(parents=True)
        (archive / ".gitignore").write_text("ignored-name/\n", encoding="utf-8")
        source = archive / "ignored-name" / "source.md"
        source.write_text("综上所述。\n", encoding="utf-8")
        with patch.object(slop_lint, "ROOT", archive):
            self.assertEqual(slop_lint.targets([]), [source])
            self.assertEqual(self.run_lint(), 1)

    def test_git_error_never_becomes_a_clean_result(self):
        failure = subprocess.CalledProcessError(128, ["git", "ls-files"],
                                                stderr=b"fixture Git failure")
        with patch("subprocess.check_output", side_effect=failure):
            self.assertEqual(self.run_lint(), 2)

    def test_missing_git_at_git_root_never_becomes_a_clean_result(self):
        with patch("subprocess.check_output", side_effect=FileNotFoundError("git")):
            self.assertEqual(self.run_lint(), 2)

    def test_unicode_and_space_in_source_names_are_not_lost(self):
        name = "docs/章节 with space.md"
        self.write(name, "综上所述。\n")
        self.assertEqual(self.names(), {name})
        self.assertEqual(self.run_lint(), 1)


if __name__ == "__main__":
    unittest.main()
