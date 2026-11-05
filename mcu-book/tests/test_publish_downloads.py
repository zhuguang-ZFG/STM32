"""publish_downloads.py 的契约测试：产物齐备、校验和自洽、失败不动旧包、升版不残留。"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOOK_DIR))  # 与 `python mcu-book/publish_downloads.py` 的导入路径一致

import publish_downloads  # noqa: E402

HTML_BYTES = b"<html>fake book html fixture</html>"
PDF_BYTES = b"%PDF-1.4 fake book pdf fixture"


def write_manifest(path: Path, version: str = "1.0.0", title: str = "合成样书") -> None:
    path.write_text(
        json.dumps({"title": title, "version": version, "date": "2026-10-25"}, ensure_ascii=False),
        encoding="utf-8",
    )


def make_source(path: Path, *, with_pdf: bool = True) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "mcu-deep-book.html").write_bytes(HTML_BYTES)
    if with_pdf:
        (path / "mcu-deep-book.pdf").write_bytes(PDF_BYTES)


def run_publish(*args: str) -> tuple[int, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = publish_downloads.main(list(args))
    return code, stdout.getvalue() + stderr.getvalue()


class PublishDownloadsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.source = tmp / "dist"
        self.manifest_path = tmp / "manifest.json"
        self.out_dir = tmp / "downloads"
        make_source(self.source)
        write_manifest(self.manifest_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def publish(self, *extra: str) -> tuple[int, str]:
        return run_publish(
            "--out-dir", str(self.out_dir),
            "--source-dir", str(self.source),
            "--manifest", str(self.manifest_path),
            *extra,
        )

    def snapshot(self) -> dict[str, bytes]:
        return {p.name: p.read_bytes() for p in sorted(self.out_dir.iterdir())}

    def test_products_complete(self) -> None:
        code, output = self.publish()
        self.assertEqual(0, code, output)
        names = sorted(p.name for p in self.out_dir.iterdir())
        self.assertEqual(
            [
                "SHA256SUMS.txt",
                "book-downloads.json",
                "index.html",
                "mcu-deep-book-v1.0.0.html",
                "mcu-deep-book-v1.0.0.pdf",
                "mcu-deep-book.html",
                "mcu-deep-book.pdf",
            ],
            names,
        )
        listing = json.loads((self.out_dir / "book-downloads.json").read_text(encoding="utf-8"))
        self.assertEqual("合成样书", listing["title"])
        self.assertEqual("1.0.0", listing["version"])
        self.assertEqual("2026-10-25", listing["date"])
        self.assertEqual(4, len(listing["files"]))
        self.assertEqual(
            {"html": str(self.source / "mcu-deep-book.html"), "pdf": str(self.source / "mcu-deep-book.pdf")},
            listing["generatedFrom"],
        )
        # 落地页自包含：无外链、相对路径指到同目录文件。
        landing = (self.out_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="mcu-deep-book.html"', landing)
        self.assertIn('href="mcu-deep-book.pdf"', landing)
        self.assertIn('href="SHA256SUMS.txt"', landing)
        self.assertNotIn("http://", landing)
        self.assertNotIn("https://", landing)

    def test_sha256sums_match_hashlib(self) -> None:
        code, output = self.publish()
        self.assertEqual(0, code, output)
        lines = (self.out_dir / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(4, len(lines))  # 恰好覆盖 4 个下载文件
        for line in lines:
            digest, rest = line.split(" ", 1)
            # `*` 是二进制模式标记（见 publish_downloads.py 的注释：文本模式会让
            # sha256sum -c 按 CRLF 翻译读文件，PDF 的 \r\n 被改写后校验必挂）
            name = rest.strip().lstrip("*")
            actual = hashlib.sha256((self.out_dir / name).read_bytes()).hexdigest()
            self.assertEqual(actual, digest, name)

    def test_missing_input_keeps_previous_package(self) -> None:
        code, output = self.publish()
        self.assertEqual(0, code, output)
        before = self.snapshot()
        (self.source / "mcu-deep-book.pdf").unlink()
        with self.assertRaises(SystemExit) as caught:
            self.publish()
        self.assertEqual(1, caught.exception.code)
        self.assertEqual(before, self.snapshot())  # 旧包一个字节都没动

    def test_version_upgrade_leaves_no_stale_files(self) -> None:
        code, output = self.publish()
        self.assertEqual(0, code, output)
        write_manifest(self.manifest_path, version="1.1.0")
        code, output = self.publish()
        self.assertEqual(0, code, output)
        names = [p.name for p in self.out_dir.iterdir()]
        self.assertIn("mcu-deep-book-v1.1.0.html", names)
        self.assertIn("mcu-deep-book-v1.1.0.pdf", names)
        self.assertNotIn("mcu-deep-book-v1.0.0.html", names)
        self.assertNotIn("mcu-deep-book-v1.0.0.pdf", names)

    def test_non_semver_version_is_rejected(self) -> None:
        write_manifest(self.manifest_path, version="1.0")
        with self.assertRaises(SystemExit) as caught:
            self.publish()
        self.assertEqual(1, caught.exception.code)
        self.assertFalse(self.out_dir.exists())  # 前置校验失败时不落任何文件

    def test_missing_title_is_rejected(self) -> None:
        write_manifest(self.manifest_path, title="")
        with self.assertRaises(SystemExit) as caught:
            self.publish()
        self.assertEqual(1, caught.exception.code)
        self.assertFalse(self.out_dir.exists())

    def test_verify_accepts_fresh_package(self) -> None:
        code, output = self.publish()
        self.assertEqual(0, code, output)
        # 走 hashlib 口径：Windows 的 sha256sum -c 会按文本模式读 PDF 而误报，这是可用的自证方式
        code, output = run_publish("--verify", str(self.out_dir))
        self.assertEqual(0, code, output)
        self.assertIn("校验通过", output)

    def test_verify_names_tampered_file(self) -> None:
        code, output = self.publish()
        self.assertEqual(0, code, output)
        (self.out_dir / "mcu-deep-book.pdf").write_bytes(PDF_BYTES + b"tampered")
        code, output = run_publish("--verify", str(self.out_dir))
        self.assertEqual(1, code, output)
        self.assertIn("mcu-deep-book.pdf", output)

    def test_neither_out_dir_nor_verify_is_rejected(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            run_publish()
        self.assertEqual(2, caught.exception.code)  # argparse 用法错误


if __name__ == "__main__":
    unittest.main()
