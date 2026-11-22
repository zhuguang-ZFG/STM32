"""`mcu/CITATION.cff` 必须描述真实存在的那本书。

合并计划的 AC7 要求「CITATION、manifest、站点仓库入口相互一致」。B5 把 MCU
正文并入根书稿后，这份引用元数据留在原地没跟着改，四处断言已经不对：

- `identifiers[0]` 指向 `mcu/mcu-book`，该目录已整树删除，链接必然 404；
- `url` 指向 `/STM32/mcu/`，那里现在是 396 字节的 `meta refresh` 跳转存根；
- `version: 1.0.0` 与 `docs/manifest.json` 的 `0.1.0` 冲突；
- 摘要称「88 章」，而合并书是 47 章 + 6 附录。

四处都是人工通读才发现的，没有一个门会失败。本文件把它们变成断言，并顺手
把可复算的数字（章数、附录数、工程数）绑到真源上，避免再手写漂移。

为什么不 import 一个 YAML 解析器：`book/requirements.txt` 只钉了 `markdown`，
内容门要在没有 PyYAML 的环境里跑。下面只读它需要的几个顶层标量，形态一变
就直接抛断言失败，不会静默跳过。
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import manifest as manifest_module

CITATION = ROOT / "mcu" / "CITATION.cff"
PROJECTS = ROOT / "mcu" / "code" / "projects.json"

SCALAR_RE = r"^{key}:[ \t]*(.+)$"
FOLDED_RE = r"^{key}:[ \t]*(?:>-?|\|-?)[ \t]*\n((?:[ \t]+\S.*\n)+)"
IDENTIFIER_RE = re.compile(
    r"^[ \t]*- type:[ \t]*\S+\n"
    r"[ \t]+value:[ \t]*\"?([^\"\n]+)\"?\n"
    r"[ \t]+description:",
    re.MULTILINE,
)
GITHUB_TREE_RE = re.compile(r"^https://github\.com/[^/]+/[^/]+/tree/[^/]+/(.+)$")


def scalar(text: str, key: str) -> str:
    """Read one top-level `key: value` scalar, quotes stripped."""
    match = re.search(SCALAR_RE.format(key=re.escape(key)), text, re.MULTILINE)
    if not match:
        raise AssertionError(f"CITATION.cff: 缺少顶层键 {key!r}（或格式已变）")
    return match.group(1).strip().strip("\"'")


def folded(text: str, key: str) -> str:
    """Read one folded block scalar (`abstract: >-`) as a single line."""
    match = re.search(FOLDED_RE.format(key=re.escape(key)), text, re.MULTILINE)
    if not match:
        raise AssertionError(f"CITATION.cff: {key!r} 不是折叠块（>-）写法")
    return " ".join(line.strip() for line in match.group(1).splitlines())


class CitationTest(unittest.TestCase):
    def setUp(self):
        self.text = CITATION.read_text(encoding="utf-8")
        self.manifest = manifest_module.build_manifest(manifest_module.load_toc())

    def chapters(self) -> int:
        return sum(len(part["chapters"]) for part in self.manifest["parts"])

    def test_title_matches_manifest(self):
        self.assertEqual(scalar(self.text, "title"), self.manifest["title"])

    def test_version_matches_manifest(self):
        self.assertEqual(scalar(self.text, "version"), self.manifest["version"])

    def test_repository_is_the_canonical_one(self):
        self.assertEqual(
            scalar(self.text, "repository-code").rstrip("/"),
            "https://github.com/zhuguang-ZFG/STM32",
        )

    def test_url_is_the_site_root_not_the_mcu_stub(self):
        """`/STM32/mcu/` 只剩跳转存根，指过去等于把引用信息指向一个壳。"""
        self.assertEqual(scalar(self.text, "url"), "https://zhuguang-zfg.github.io/STM32/")

    def test_identifier_targets_exist_in_the_tree(self):
        """指针要落在真实目录上：旧的 `mcu/mcu-book` 就是这样烂掉的。"""
        values = IDENTIFIER_RE.findall(self.text)
        self.assertTrue(values, "CITATION.cff: identifiers 应至少含一条 url")
        for value in values:
            match = GITHUB_TREE_RE.match(value.strip())
            if not match:
                continue
            target = ROOT / match.group(1)
            self.assertTrue(
                target.exists(),
                f"identifiers 指向的路径不存在: {match.group(1)}（{value}）",
            )

    def test_license_text_matches_the_declared_identifier(self):
        declared = scalar(self.text, "license")
        self.assertEqual(declared, "Apache-2.0")
        text = (ROOT / "mcu" / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0", text)

    def test_abstract_chapter_and_appendix_counts(self):
        abstract = folded(self.text, "abstract")
        claimed = {int(n) for n in re.findall(r"(\d+)\s*章", abstract)}
        self.assertEqual(claimed, {self.chapters()}, abstract)
        self.assertEqual(
            {int(n) for n in re.findall(r"(\d+)\s*个附录", abstract)},
            {len(self.manifest["appendices"])},
            abstract,
        )

    def test_abstract_project_count_matches_projects_json(self):
        """「N 个可构建工程」的真源是 `mcu/code/projects.json`，不是手写数字。"""
        projects = json.loads(PROJECTS.read_text(encoding="utf-8"))
        claimed = {int(n) for n in re.findall(r"(\d+)\s*个可构建工程", folded(self.text, "abstract"))}
        self.assertEqual(claimed, {len(projects)}, f"projects.json 现有 {len(projects)} 个工程")


if __name__ == "__main__":
    unittest.main()
