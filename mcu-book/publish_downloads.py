#!/usr/bin/env python3
"""整书下载打包器——把 dist 里的 html/pdf 变成可发布的下载包。

为什么需要它：发布物要有凭据。本脚本产出稳定名 + 版本名双份文件、
SHA256SUMS.txt 校验和、book-downloads.json 机器可读清单、自包含落地页，
且用“staging 整体替换”保证下载页永远不会指到半个包：
任一前置校验失败时已有输出原样保留（留上一份完整包）。

用法：python mcu-book/publish_downloads.py --out-dir <dir> [--source-dir mcu-book/dist] [--manifest mcu-book/manifest.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BOOK_DIR))  # 允许从仓库根直接 `python mcu-book/publish_downloads.py`

from build_html import OUTPUT_NAME, PDF_NAME, load_manifest  # noqa: E402

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

LANDING_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 离线版下载</title>
<style>
  body {{ font-family: system-ui, "Microsoft YaHei", sans-serif; margin: 0 auto; max-width: 40em; padding: 3rem 1.2rem; color: #1c2321; line-height: 1.7; }}
  h1 {{ font-size: 1.6rem; margin-bottom: .2rem; }}
  .meta {{ color: #5a6560; font-size: .95rem; margin-bottom: 2rem; }}
  .format {{ display: block; padding: 1rem 1.2rem; margin: .8rem 0; border: 1px solid #c9d4cf; border-radius: .6rem; text-decoration: none; color: inherit; }}
  .format:hover {{ border-color: #0e6e5c; }}
  .format b {{ color: #0e6e5c; }}
  .format small {{ display: block; color: #5a6560; }}
  .checksums {{ font-size: .9rem; }}
  code {{ background: #f0f4f2; padding: .1em .4em; border-radius: .3em; }}
</style>
</head>
<body>
<h1>{title} · 离线版下载</h1>
<p class="meta">版本 v{version} · 构建日期 {date}</p>
<a class="format" href="{html_name}"><b>单文件 HTML</b>（{html_size}）<small>双击即可离线阅读，图片全部内嵌</small></a>
<a class="format" href="{pdf_name}"><b>A4 PDF</b>（{pdf_size}）<small>带书签大纲与页眉页码，适合打印</small></a>
<p class="checksums">校验和见 <a href="SHA256SUMS.txt">SHA256SUMS.txt</a>（<code>sha256sum -c</code> 可验）；机器可读清单见 <a href="book-downloads.json">book-downloads.json</a>。历史版本文件以 <code>-v{version}</code> 后缀并存。</p>
</body>
</html>
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _human_size(num_bytes: int) -> str:
    return f"{num_bytes / (1 << 20):.1f} MB"


def _fail(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr)
    raise SystemExit(1)


def publish(out_dir: Path, source_dir: Path, manifest_path: Path) -> int:
    manifest = load_manifest(manifest_path)

    # 前置校验全部在动 out_dir 之前：任何一条不过，已有输出一个字节都不动。
    title = str(manifest.get("title", "")).strip()
    if not title:
        _fail(f"manifest 缺少 title → {manifest_path}")
    version = str(manifest.get("version", "")).strip()
    if not VERSION_PATTERN.match(version):
        _fail(f"manifest version → 实际 {version!r} vs 期望 ^\\d+\\.\\d+\\.\\d+$（{manifest_path}）")
    date = str(manifest.get("date", "")).strip()

    source_html = source_dir / OUTPUT_NAME
    source_pdf = source_dir / PDF_NAME
    missing = [str(p) for p in (source_html, source_pdf) if not p.is_file()]
    if missing:
        _fail("源产物缺失（先跑 python mcu-book/build_html.py --pdf）→ " + "、".join(missing))

    base_html = OUTPUT_NAME                       # mcu-deep-book.html（稳定名）
    base_pdf = PDF_NAME                           # mcu-deep-book.pdf
    versioned_html = f"mcu-deep-book-v{version}.html"
    versioned_pdf = f"mcu-deep-book-v{version}.pdf"

    parent = out_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    # staging 与 out_dir 同父目录，保证 replace 是同设备 rename（真原子）。
    staging = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.staging-", dir=parent))
    try:
        downloads: list[tuple[str, Path]] = [
            (base_html, source_html),
            (base_pdf, source_pdf),
            (versioned_html, source_html),
            (versioned_pdf, source_pdf),
        ]
        file_entries = []
        for name, source in downloads:
            target = staging / name
            shutil.copyfile(source, target)
            file_entries.append({"name": name, "bytes": target.stat().st_size, "sha256": _sha256(target)})

        # 用 " *"（GNU 的二进制模式标记）。实测（2026-10-25，本机 Git for Windows）：
        #   · `sha256sum <file>`（Git Bash 0.8.0）算出的就是二进制摘要，正确；
        #   · 但 `sha256sum -c` 在这个实现里**忽略 "*" 标记、一律按文本模式读**，
        #     PDF 里的 \r\n 被翻译后必然 FAILED；GNU coreutils（Linux/macOS/WSL）上同样的文件是 OK。
        # 所以：清单按 GNU 口径写（*），Windows 本地自证走 `--verify`（hashlib，平台无关），
        # CI 额外用 GNU sha256sum 过一道。
        sums = "".join(f"{entry['sha256']} *{entry['name']}\n" for entry in file_entries)
        (staging / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")

        listing = {
            "title": title,
            "version": version,
            "date": date,
            "files": file_entries,
            "generatedFrom": {"html": str(source_html), "pdf": str(source_pdf)},
        }
        (staging / "book-downloads.json").write_text(
            json.dumps(listing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        (staging / "index.html").write_text(
            LANDING_PAGE.format(
                title=title,
                version=version,
                date=date,
                html_name=base_html,
                pdf_name=base_pdf,
                html_size=_human_size(file_entries[0]["bytes"]),
                pdf_size=_human_size(file_entries[1]["bytes"]),
            ),
            encoding="utf-8",
        )

        # 整体替换：旧包先挪到旁边，staging 就位后再删——中途失败也不会留半个包。
        trash: Path | None = None
        if out_dir.exists():
            trash = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.old-", dir=parent))
            trash.rmdir()
            out_dir.rename(trash)
        try:
            staging.rename(out_dir)
        except Exception:
            if trash is not None:
                trash.rename(out_dir)  # 回滚：把旧包放回原位
            raise
        if trash is not None:
            shutil.rmtree(trash)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    names = sorted(p.name for p in out_dir.iterdir())
    print(f"✓ 下载包已发布 → {out_dir}（{len(names)} 个文件：{'、'.join(names)}）")
    return 0


def verify(package_dir: Path) -> int:
    """逐条核对既有下载包里的 SHA256SUMS.txt（用 hashlib，平台无关）。

    为什么需要它：`sha256sum -c` 在 Git for Windows 上是另一套实现，实测忽略 "*"
    二进制标记、一律按文本模式读，PDF 必然 FAILED（同一个包在 GNU coreutils 上是 OK）。
    给 Windows 用户一个能用的自证方式，CI 侧再用 GNU sha256sum 过一道。
    """
    sums = package_dir / "SHA256SUMS.txt"
    if not sums.is_file():
        print(f"✗ 找不到 {sums}", file=sys.stderr)
        return 1
    problems: list[str] = []
    checked = 0
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rest = line.split(" ", 1)
        name = rest.strip().lstrip("*")
        target = package_dir / name
        if not target.is_file():
            problems.append(f"{name} 不在包里")
            continue
        actual = _sha256(target)
        checked += 1
        if actual != digest:
            problems.append(f"{name}: 实际 {actual} ≠ 记录 {digest}")
    if problems:
        print(f"✗ 下载包校验失败 {len(problems)} 处：", file=sys.stderr)
        for item in problems:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print(f"✓ 下载包校验通过：{checked} 个文件与 SHA256SUMS.txt 一致")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, help="下载包输出目录（整体原子替换）")
    parser.add_argument(
        "--verify",
        type=Path,
        metavar="DIR",
        help="校验既有下载包（hashlib 口径，Windows 上也准）",
    )
    parser.add_argument("--source-dir", type=Path, default=BOOK_DIR / "dist", help="build_html.py 的产物目录")
    parser.add_argument("--manifest", type=Path, default=BOOK_DIR / "manifest.json", help="manifest.json 路径")
    options = parser.parse_args(argv)
    if options.verify:
        return verify(options.verify)
    if not options.out_dir:
        parser.error("要么用 --out-dir 打包，要么用 --verify 校验既有包")
    return publish(options.out_dir, options.source_dir, options.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
