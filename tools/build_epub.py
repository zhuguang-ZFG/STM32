#!/usr/bin/env python3
"""Package the built book HTML into EPUB 3.

Reads the print-edition HTML produced by ``stm32-book/build_html.py``
(the variant with video blocks already stripped), splits ``<main>`` into
its top-level sections, converts each to XHTML, extracts data-URI images
to real files, and writes a valid EPUB 3 container with a nav document
plus an EPUB 2 NCX for older readers.

The book HTML is the single source of truth: whatever it contains at
build time is what the EPUB contains, so the two editions cannot drift.

Usage::

    python tools/build_epub.py                    # both dist languages
    python tools/build_epub.py --html PATH --out PATH
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
import sys
import uuid
import zipfile
from pathlib import Path

from lxml import etree, html as lhtml

REPO = Path(__file__).resolve().parents[1]
DIST = REPO / "stm32-book/dist"

BOOKS = (
    (DIST / "stm32-practical-book.html",
     DIST / "stm32-practical-book.epub",
     "zh-CN"),
    (DIST / "stm32-practical-book-en.html",
     DIST / "stm32-practical-book-en.epub",
     "en"),
)

NAV_CSS = """\
body { margin: 0; padding: 0; background: #fbfaf7; color: #17202a;
       font-family: serif; line-height: 1.6; }
main.book, section, article { display: block; }
.kicker, .eyebrow { font-size: 0.72em; letter-spacing: 0.12em;
                    text-transform: uppercase; color: #5e6872; }
h1 { font-size: 1.45em; line-height: 1.3; margin: 1.2em 0 0.6em; color: #17202a; }
h2 { font-size: 1.2em; margin: 1.6em 0 0.5em; color: #075e84; }
h3 { font-size: 1.05em; margin: 1.2em 0 0.4em; }
p, li { orphans: 2; widows: 2; }
p { margin: 0 0 0.7em; }
figure { margin: 1em 0; padding: 0.5em 0.3em; border: 1px solid #d7dce1;
         border-radius: 0.5em; text-align: center; page-break-inside: avoid; }
figure img, p[align="center"] img, img { max-width: 100%; height: auto; }
figcaption { font-size: 0.85em; color: #5e6872; line-height: 1.4;
             margin-top: 0.4em; text-align: center; }
sub { font-size: 0.85em; color: #5e6872; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #f6f6f6;
      border-left: 3px solid #075e84; border-radius: 0.4em;
      padding: 0.6em 0.7em; font-size: 0.82em; line-height: 1.5; }
code { font-family: monospace; font-size: 0.92em; background: #f2f4f5;
       padding: 0 0.2em; border-radius: 0.2em; }
pre code { background: transparent; padding: 0; }
.table-scroll { overflow: visible; }
table { border-collapse: collapse; width: 100%; font-size: 0.82em;
        margin: 0.8em 0; }
th, td { border: 1px solid #d7dce1; padding: 0.35em 0.45em;
         vertical-align: top; overflow-wrap: anywhere; }
thead th { background: #edf3f6; }
blockquote { border-left: 3px solid #075e84; margin: 0.8em 0;
             padding: 0.1em 0.9em; color: #2c3540; }
.source-card { border: 1px solid #d7dce1; border-top: 3px solid #075e84;
               border-radius: 0.5em; padding: 0.6em 0.8em; margin: 0.9em 0;
               font-size: 0.85em; overflow-wrap: anywhere; }
.chapter-compass, .quick-check, .callout-tip, .callout-note, .callout-warning {
  border: 1px solid #d7dce1; border-radius: 0.5em;
  padding: 0.6em 0.8em; margin: 0.9em 0; }
.cover { background: #10242e; color: #f4f1ea; padding: 2em 1em; }
.cover h1 { color: #f4f1ea; }
.part-divider { border-top: 4px solid #075e84; padding: 2.5em 0.2em; }
.part-divider h1 { color: #075e84; }
.contents ol { list-style: none; padding-left: 0; }
.chapter > header { border-bottom: 1px solid #d7dce1; padding-bottom: 0.6em; }
a { color: #075e84; text-decoration: none; }
"""


def _top_level_segments(main_html: str) -> list[tuple[str, str, str]]:
    """Split the inner HTML of <main> into (class, id, html) top-level blocks."""
    segments: list[tuple[str, str, str]] = []
    depth = 0
    start = 0
    cur_class = cur_id = ""
    for m in re.finditer(r"<(/?)(section|article|div|nav|footer)\b([^>]*)>", main_html):
        closing, tag, attrs = m.groups()
        if not closing:
            if depth == 0:
                start = m.start()
                cur_class = (re.search(r'class="([^"]*)"', attrs) or [None, ""])[1]
                cur_id = (re.search(r'id="([^"]*)"', attrs) or [None, ""])[1]
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                segments.append((cur_class, cur_id, main_html[start:m.end()]))
            elif depth < 0:
                raise SystemExit(f"unbalanced closing tag {tag!r} at offset {m.start()}")
    if depth != 0:
        raise SystemExit("unbalanced tags at end of <main>")
    return segments


def _segment_title(segment_html: str) -> str:
    doc = lhtml.fromstring(segment_html)
    for xp in ("//h1", "//h2", "//p[contains(@class,'kicker')]"):
        node = doc.xpath(xp)
        if node and "".join(node[0].itertext()).strip():
            return re.sub(r"\s+", " ", "".join(node[0].itertext()).strip())
    return ""


class _ImageStore:
    def __init__(self) -> None:
        self.paths: dict[str, str] = {}
        self.counter = 0
        self.by_hash: dict[str, str] = {}

    def add(self, mime: str, payload: bytes) -> str:
        key = hashlib.sha1(mime.encode() + payload).hexdigest()
        if key in self.by_hash:
            return self.by_hash[key]
        ext = {"image/svg+xml": ".svg", "image/png": ".png",
               "image/gif": ".gif", "image/jpeg": ".jpg"}[mime]
        self.counter += 1
        rel = f"images/img{self.counter:04d}{ext}"
        self.paths[rel] = payload
        self.by_hash[key] = rel
        return rel


def _extract_images(fragment_html: str, store: _ImageStore) -> str:
    def replace(m: re.Match[str]) -> str:
        attr, mime, payload_b64 = m.group(1), m.group(2), m.group(3)
        try:
            payload = base64.b64decode(payload_b64)
        except Exception:
            return m.group(0)
        rel = store.add(mime, payload)
        return f'{attr}="{rel}"'
    return re.sub(
        r'(src|href|poster)="data:(image/(?:svg\+xml|png|gif|jpeg));base64,([^"]+)"',
        replace, fragment_html)


XHTML_NS = "http://www.w3.org/1999/xhtml"
SVG_NS = "http://www.w3.org/2000/svg"


def _to_xhtml_document(body_html: str, title: str, css_href: str) -> tuple[bytes, bool]:
    wrapped = f"<html><head><title>{title}</title></head><body>{body_html}</body></html>"
    doc = lhtml.fromstring(wrapped)
    head = doc.find("head")
    link = etree.SubElement(head, "link")
    link.set("rel", "stylesheet")
    link.set("type", "text/css")
    link.set("href", css_href)
    body = doc.find("body")
    body.set("class", "epub-body")
    # strip interactive helpers that have no meaning in EPUB
    for bad in doc.xpath("//a[contains(@class,'toc-jump') or contains(@class,'back-to-toc') or contains(@class,'skip-link')]"):
        bad.getparent().remove(bad)
    for bad in doc.xpath("//script | //form | //button | //input"):
        bad.getparent().remove(bad)
    # the build wraps chapter titles in <span> phrasing containers; the
    # XHTML schema forbids headings there, so hoist them up
    phrasing = {"span", "em", "strong", "b", "i", "small", "u", "sub",
                "sup", "code", "a"}
    for h in doc.xpath("//*[local-name()='h1' or local-name()='h2' or "
                       "local-name()='h3' or local-name()='h4' or "
                       "local-name()='h5' or local-name()='h6']"):
        while True:
            par = h.getparent()
            if par is None or par.tag.rsplit("}", 1)[-1] not in phrasing:
                break
            grand = par.getparent()
            if grand is None:
                break
            grand.insert(grand.index(par) + 1, h)
    # zoom links around figures point at image resources; EPUB <a> hrefs
    # must target spine items, so unwrap them and keep the content
    for a in doc.xpath("//a[starts-with(@href,'images/') or starts-with(@href,'data:')]"):
        parent = a.getparent()
        if parent is None:
            continue
        idx = parent.index(a)
        for child in list(a):
            parent.insert(idx, child)
            idx += 1
        parent.remove(a)
    # HTML parsing puts every element in no namespace; EPUB XHTML requires
    # the XHTML namespace on everything and the SVG namespace inside <svg>.
    for el in doc.iter():
        if isinstance(el.tag, str) and not el.tag.startswith("{"):
            el.tag = "{%s}%s" % (XHTML_NS, el.tag)
    for svgel in doc.xpath("//*[local-name()='svg']"):
        for el in svgel.iter():
            if isinstance(el.tag, str):
                el.tag = "{%s}%s" % (SVG_NS, el.tag.rsplit("}", 1)[-1])
    has_svg = bool(doc.xpath("//*[local-name()='svg']"))
    out = etree.tostring(doc, method="xml", encoding="utf-8",
                         xml_declaration=True, pretty_print=False)
    return out, has_svg


def _collect_ids(body_html: str) -> set[str]:
    return set(re.findall(r'id="([^"]+)"', body_html))


def _rewrite_anchors(body_html: str, id_to_file: dict[str, str],
                     own_file: str) -> str:
    def replace(m: re.Match[str]) -> str:
        # the regex captures a bare fragment (no '#', no file part)
        frag = m.group(1)
        if not frag or frag not in id_to_file:
            return m.group(0)
        target_file = id_to_file[frag]
        if target_file == own_file:
            return f'href="#{frag}"'
        return f'href="{target_file}#{frag}"'
    return re.sub(r'href="#([^"]*)"', replace, body_html)


def build_epub(book_html: str, out_path: Path, language: str,
               title: str | None = None) -> dict:
    main_m = re.search(r"<main class=\"book\">(.*)</main>", book_html, re.S)
    if not main_m:
        raise SystemExit("book HTML has no <main class=\"book\">")
    doc_title = title or re.search(r"<title>(.*?)</title>", book_html, re.S).group(1)
    segments = _top_level_segments(main_m.group(1))
    if not segments:
        raise SystemExit("no top-level segments found")

    store = _ImageStore()
    files: dict[str, bytes] = {}
    spine: list[tuple[str, str, str]] = []  # (href, class, title)
    id_to_file: dict[str, str] = {}

    # pass 1: raw segment -> file bodies with images extracted; collect ids
    bodies: list[tuple[str, str, str, str]] = []
    for idx, (klass, seg_id, seg_html) in enumerate(segments, 1):
        if klass.startswith("index-group") or klass == "source-card":
            continue  # nested content captured by their parents
        name = f"seg{idx:02d}.xhtml"
        body = _extract_images(seg_html, store)
        bodies.append((name, klass, seg_id, body))
        for anchor in _collect_ids(seg_html):
            id_to_file.setdefault(anchor, name)

    # pass 2: rewrite cross-file anchors and serialize
    svg_files: set[str] = set()
    for name, klass, seg_id, body in bodies:
        body = _rewrite_anchors(body, id_to_file, name)
        seg_title = _segment_title(body) or seg_id or name
        payload, has_svg = _to_xhtml_document(body, seg_title, "epub.css")
        files[f"OEBPS/{name}"] = payload
        if has_svg:
            svg_files.add(name)
        spine.append((name, klass, seg_title))

    css = f"/* {doc_title} — EPUB stylesheet */\n" + NAV_CSS
    files["OEBPS/epub.css"] = css.encode("utf-8")
    for rel, payload in store.paths.items():
        files[f"OEBPS/{rel}"] = payload

    uid = str(uuid.uuid5(uuid.NAMESPACE_URL,
                         f"urn:stm32-practical-book:{language}:{doc_title}"))
    modified = "2000-01-01T00:00:00Z"  # deterministic build

    nav_items = []
    for name, klass, seg_title in spine:
        if klass.startswith("part-divider"):
            nav_items.append(("part", name, seg_title))
        elif klass == "chapter":
            nav_items.append(("chapter", name, seg_title))
        elif klass == "appendix":
            nav_items.append(("appendix", name, seg_title))
        elif klass in ("cover", "imprint", "frontmatter", "back-matter",
                       "source-registry", "part-closing"):
            nav_items.append(("front", name, seg_title))

    nav = ['<?xml version="1.0" encoding="utf-8"?>',
           '<!DOCTYPE html>',
           '<html xmlns="http://www.w3.org/1999/xhtml" '
           'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="' + language + '" lang="' + language + '">',
           '<head><title>TOC</title><link rel="stylesheet" type="text/css" href="epub.css"/></head>',
           '<body><nav epub:type="toc" id="toc"><h1>' + ("目录" if language.startswith("zh") else "Contents") + '</h1><ol>']
    in_part = False
    li_open = False
    for kind, name, seg_title in nav_items:
        if kind == "part":
            if li_open:
                nav.append("</li>")
                li_open = False
            if in_part:
                nav.append("</ol></li>")
                in_part = False
            nav.append(f'<li><a href="{name}">{_x(seg_title)}</a><ol>')
            in_part = True
            continue
        if kind in ("appendix", "front") and in_part:
            if li_open:
                nav.append("</li>")
                li_open = False
            nav.append("</ol></li>")
            in_part = False
        if li_open:
            nav.append("</li>")
            li_open = False
        nav.append(f'<li><a href="{name}">{_x(seg_title)}</a>')
        li_open = True
    if li_open:
        nav.append("</li>")
    if in_part:
        nav.append("</ol></li>")
    nav.append("</ol></nav>")
    nav.append('<nav epub:type="landmarks" id="landmarks" hidden="hidden"><ol>'
               f'<li><a epub:type="cover" href="{spine[0][0]}">Cover</a></li>'
               f'<li><a epub:type="toc" href="{spine[4][0] if len(spine) > 4 else spine[0][0]}">TOC</a></li>'
               f'<li><a epub:type="bodymatter" href="{spine[5][0] if len(spine) > 5 else spine[0][0]}">Start</a></li>'
               '</ol></nav>')
    nav.append("</body></html>")
    files["OEBPS/nav.xhtml"] = "\n".join(nav).encode("utf-8")

    ncx = ['<?xml version="1.0" encoding="utf-8"?>',
           '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
           '<head><meta name="dtb:uid" content="urn:uuid:' + uid + '"/>'
           '<meta name="dtb:depth" content="1"/>'
           '<meta name="dtb:totalPageCount" content="0"/>'
           '<meta name="dtb:maxPageNumber" content="0"/></head>',
           '<docTitle><text>' + _x(doc_title) + '</text></docTitle>',
           '<navMap>']
    for i, (kind, name, seg_title) in enumerate(nav_items, 1):
        ncx.append(f'<navPoint id="np{i}" playOrder="{i}">'
                   f'<navLabel><text>{_x(seg_title)}</text></navLabel>'
                   f'<content src="{name}"/></navPoint>')
    ncx.append('</navMap></ncx>')
    files["OEBPS/toc.ncx"] = "\n".join(ncx).encode("utf-8")

    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
                '<item id="css" href="epub.css" media-type="text/css"/>']
    for i, (name, klass, seg_title) in enumerate(spine, 1):
        props = ' properties="svg"' if name in svg_files else ""
        manifest.append(f'<item id="s{i:02d}" href="{name}" media-type="application/xhtml+xml"{props}/>')
    for rel, payload in store.paths.items():
        mime = {"svg": "image/svg+xml", "png": "image/png", "gif": "image/gif",
                "jpg": "image/jpeg"}[rel.rsplit(".", 1)[1]]
        fkey = hashlib.sha1(payload).hexdigest()[:10]
        manifest.append(f'<item id="img{fkey}" href="{rel}" media-type="{mime}"/>')
    opf = ['<?xml version="1.0" encoding="utf-8"?>',
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="' + language + '">',
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">',
           f'<dc:identifier id="bookid">urn:uuid:{uid}</dc:identifier>',
           f'<dc:title>{_x(doc_title)}</dc:title>',
           '<dc:language>' + language + '</dc:language>',
           '<dc:source>stm32-book/build_html.py</dc:source>',
           '<meta property="dcterms:modified">' + modified + '</meta>',
           '<meta name="cover" content="cover-image"/>',
           '</metadata>',
           '<manifest>' + "".join(manifest) + '</manifest>',
           '<spine toc="ncx">' + "".join(f'<itemref idref="s{i:02d}"/>' for i in range(1, len(spine) + 1)) + '</spine>',
           '</package>']
    files["OEBPS/content.opf"] = "\n".join(opf).encode("utf-8")
    files["META-INF/container.xml"] = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    ).encode("utf-8")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip",
                    compress_type=zipfile.ZIP_STORED)
        for name in sorted(files):
            zf.writestr(name, files[name], compress_type=zipfile.ZIP_DEFLATED)

    return {
        "out": str(out_path),
        "title": doc_title,
        "language": language,
        "spine": len(spine),
        "images": len(store.paths),
        "bytes": out_path.stat().st_size,
    }


def _x(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def _validate(out_path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(out_path) as zf:
        names = zf.namelist()
        if names[0] != "mimetype":
            errors.append("mimetype is not the first entry")
        info = zf.getinfo("mimetype")
        if info.compress_type != zipfile.ZIP_STORED:
            errors.append("mimetype must be stored uncompressed")
        if zf.read("mimetype") != b"application/epub+zip":
            errors.append("mimetype content wrong")
        opf = zf.read("OEBPS/content.opf").decode("utf-8")
        etree.fromstring(zf.read("OEBPS/content.opf"))
        etree.fromstring(zf.read("OEBPS/nav.xhtml"))
        etree.fromstring(zf.read("OEBPS/toc.ncx"))
        spine_refs = re.findall(r'itemref idref="(s\d+)"', opf)
        id_hrefs = dict(re.findall(r'item id="(s\d+)" href="([^"]+)"', opf))
        for ref in spine_refs:
            href = id_hrefs.get(ref)
            if not href or f"OEBPS/{href}" not in names:
                errors.append(f"spine {ref} missing {href}")
                continue
            etree.fromstring(zf.read(f"OEBPS/{href}"))  # well-formed XHTML
        for name in names:
            if name.endswith(".xhtml"):
                etree.fromstring(zf.read(name))
        # every internal anchor target exists somewhere
        all_ids: set[str] = set()
        for name in names:
            if name.endswith(".xhtml"):
                all_ids |= set(re.findall(r'id="([^"]+)"',
                                          zf.read(name).decode("utf-8")))
        for name in names:
            if not name.endswith(".xhtml"):
                continue
            text = zf.read(name).decode("utf-8")
            for target in re.findall(r'href="([^"]+)"', text):
                if target.startswith(("http", "mailto:")):
                    continue
                file_part, _, frag = target.partition("#")
                fp = "OEBPS/" + file_part if file_part else name
                if fp not in names:
                    errors.append(f"{name}: broken href {target}")
                elif frag and frag not in all_ids:
                    errors.append(f"{name}: missing anchor #{frag}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="single book HTML to convert")
    parser.add_argument("--out", type=Path, help="EPUB output path")
    parser.add_argument("--lang", default="zh-CN")
    parser.add_argument("--title")
    args = parser.parse_args(argv)

    jobs = ([(args.html, args.out, args.lang, args.title)]
            if args.html else
            [(h, o, lang, None) for h, o, lang in BOOKS])
    failed = False
    for html_path, out_path, language, title in jobs:
        if not html_path.exists():
            print(f"missing {html_path}")
            failed = True
            continue
        book_html = html_path.read_text(encoding="utf-8")
        info = build_epub(book_html, out_path, language, title)
        errors = _validate(out_path)
        print(f"{html_path.name} -> {info['out']}: spine={info['spine']} "
              f"images={info['images']} {info['bytes']} bytes "
              f"errors={len(errors)}")
        for e in errors:
            print("   !", e)
        if errors:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
