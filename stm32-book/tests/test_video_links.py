"""Recommended videos: one data file, checked links, generated chapter text.

Every link in stm32-book/video-links.json was opened through the platform's
own API on the date it records. A chapter holds only what
tools/gen_video_links.py renders from that file, so a hand-typed link or a
section left stale after the data changed fails here. The checker is also
run on planted bad entries, because a clean result means nothing unless the
checker can fail.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN_PATH = ROOT / "tools" / "gen_video_links.py"
VIDEO_URL = re.compile(r"bilibili\.com/video|youtube\.com/watch|youtu\.be/")


def load_generator():
    if "gen_video_links" in sys.modules:
        return sys.modules["gen_video_links"]
    spec = importlib.util.spec_from_file_location("gen_video_links", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_video_links"] = module
    spec.loader.exec_module(module)
    return module


# Obviously fake ids: these entries only feed the checker and never reach a chapter.
PLANTED = {
    "platform": "bilibili",
    "url": "https://www.bilibili.com/video/BV0000000000?p=3",
    "id": "BV0000000000",
    "part": 3,
    "title": "示例合集",
    "part_title": "示例分集",
    "author": "示例作者",
    "duration_s": 1835,
    "lang": "zh",
    "why_zh": "先看接线，再回来对照本章的表。",
    "why_en": "Watch the wiring first, then come back to the table.",
    "verified_at": "2026-10-31",
    "verify": "bilibili view+pagelist API",
}
PLANTED_YT = {
    "platform": "youtube",
    "url": "https://www.youtube.com/watch?v=00000000000",
    "id": "00000000000",
    "part": None,
    "title": "Sample talk",
    "part_title": None,
    "author": "Sample channel",
    "duration_s": None,
    "lang": "en",
    "why_zh": "英文讲解，配合本章的寄存器表看。",
    "why_en": "An English walk-through to read next to the register table.",
    "verified_at": "2026-10-30",
    "verify": "youtube oembed",
}
CHAPTER = """## 学习目标

- 目标

## 自测

1. 题目

## 原理与适用范围

> [!NOTE]
> 深入部分。

## 相关资源

- 资源
"""


def entries_in(data: dict) -> list[dict]:
    return [item for items in data["chapters"].values() for item in items]


class VideoLinkCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gen = load_generator()

    def errors_for(self, **changes) -> list[str]:
        item = copy.deepcopy(PLANTED)
        item.update(changes)
        return self.gen.validate({"chapters": {"03": [item]}})

    def test_planted_good_entries_pass(self) -> None:
        self.assertEqual([], self.gen.validate({"chapters": {"03": [PLANTED, PLANTED_YT]}}))

    def test_catches_bad_entries(self) -> None:
        self.assertTrue(self.errors_for(url="https://b23.tv/BV0000000000"))
        self.assertTrue(self.errors_for(part=4))
        self.assertTrue(self.errors_for(id="BV1111111111"))
        self.assertTrue(self.errors_for(part_title=None))
        self.assertTrue(self.errors_for(lang="ja"))
        self.assertTrue(self.errors_for(verify="looked at it"))
        self.assertTrue(self.errors_for(verified_at="yesterday"))
        self.assertTrue(self.errors_for(author=" "))
        self.assertTrue(self.errors_for(duration_s=0))
        self.assertTrue(self.errors_for(why_zh="长" * 61))
        self.assertTrue(self.errors_for(why_en="word " * 31))
        self.assertTrue(self.errors_for(why_zh="好看\U0001F44D"))
        self.assertTrue(self.gen.validate({"chapters": {"03": [PLANTED, PLANTED]}}))
        self.assertTrue(self.gen.validate({"chapters": {"29": [PLANTED]}}))
        broken = copy.deepcopy(PLANTED)
        del broken["verify"]
        self.assertTrue(self.gen.validate({"chapters": {"03": [broken]}}))

    def test_section_round_trips(self) -> None:
        once = self.gen.patch(CHAPTER, "03", [PLANTED_YT, PLANTED], "zh")
        self.assertEqual(once, self.gen.patch(once, "03", [PLANTED_YT, PLANTED], "zh"))
        self.assertEqual(CHAPTER, self.gen.patch(once, "03", [], "zh"))
        self.assertLess(once.index("## 自测"), once.index("## 推荐视频"))
        self.assertLess(once.index("## 推荐视频"), once.index("## 原理与适用范围"))
        # The Chinese edition lists Bilibili first, and the lead carries the newest check date.
        self.assertLess(once.index("bilibili.com"), once.index("youtube.com"))
        self.assertIn("2026-10-31", once)
        self.assertIn("第 3 集「示例分集」", once)
        self.assertIn("30:35", once)

    def test_section_falls_back_to_the_resources_heading(self) -> None:
        plain = "## 学习目标\n\n- 目标\n\n## 相关资源\n\n- 资源\n"
        once = self.gen.patch(plain, "20", [PLANTED], "zh")
        self.assertLess(once.index("## 推荐视频"), once.index("## 相关资源"))

    def test_crlf_is_kept(self) -> None:
        crlf = CHAPTER.replace("\n", "\r\n")
        once = self.gen.patch(crlf, "03", [PLANTED], "zh")
        self.assertNotIn("\n", once.replace("\r\n", ""))
        self.assertEqual(crlf, self.gen.patch(once, "03", [], "zh"))


class VideoLinkDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gen = load_generator()
        cls.data = cls.gen.load()

    def test_data_file_is_valid(self) -> None:
        self.assertEqual([], self.gen.validate(self.data))

    def test_videos_are_not_source_cards(self) -> None:
        # The numbers in the text come from the manuals; a video never backs a claim.
        manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        source_urls = {card.get("url", "") for card in manifest["sources"].values()}
        self.assertEqual(set(), {item["url"] for item in entries_in(self.data)} & source_urls)
        self.assertEqual([], [url for url in source_urls if VIDEO_URL.search(url)])

    def test_chapters_match_the_data(self) -> None:
        stale = []
        for num, paths in sorted(self.gen.chapter_files().items()):
            entries = self.data["chapters"].get(num, [])
            for lang, path in paths.items():
                text = path.read_bytes().decode("utf-8")
                if self.gen.patch(text, num, entries, lang) != text:
                    stale.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], stale, "运行 python3 tools/gen_video_links.py")

    def test_video_links_live_only_in_generated_blocks(self) -> None:
        loose = []
        for paths in self.gen.chapter_files().values():
            for path in paths.values():
                text = path.read_text(encoding="utf-8")
                outside = re.sub(r"<!-- links:ch\d\d -->.*?<!-- /links:ch\d\d -->", "", text, flags=re.S)
                if VIDEO_URL.search(outside):
                    loose.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], loose)

    def test_both_editions_list_the_same_videos(self) -> None:
        for num, paths in self.gen.chapter_files().items():
            if len(paths) != 2:
                continue
            found = []
            for path in (paths["zh"], paths["en"]):
                block = re.search(r"<!-- links:ch\d\d -->.*?<!-- /links:ch\d\d -->", path.read_text(encoding="utf-8"), re.S)
                found.append(sorted(re.findall(r"\]\((https://[^)]+)\)", block.group())) if block else [])
            self.assertEqual(found[0], found[1], num)


if __name__ == "__main__":
    unittest.main()
