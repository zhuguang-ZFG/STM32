"""索引生成：从术语表抽术语，在分页后的页面树里定位出现页码，生成附录 H。

两遍法（实现在 build_print.py）：
  第一遍正常分页，然后对 .pagedjs_page 逐页扫文本，记录每个术语的命中页码
  （结构页——封面/版权/导读/目录/书尾/附录 D/G——按容器类名整页排除）；
  第二遍把收集结果渲染成附录 H 注入 </main> 前，重新分页产出最终 PDF。
  索引在书尾，不移动任何正文页码，两遍页码自洽。

每条最多列 6 个页码。索引样式由 book-print.css 的 .index-entries 两栏声明控制。
"""

from __future__ import annotations

import re
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BOOK_DIR.parent

GLOSSARY_PATH = REPO_ROOT / "docs" / "reference" / "glossary.md"

# 从术语表表格的"术语"列抽取；跳过表头与分隔行
def extract_terms(glossary_path: Path = GLOSSARY_PATH) -> list[str]:
    text = glossary_path.read_text(encoding="utf-8")
    terms: list[str] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| 术语"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 2 or not cells[1]:
            continue
        term = re.sub(r"`([^`]+)`", r"\1", cells[1])
        term = re.sub(r"[🔧⚠️💡🎯✅❌▶️]", "", term).strip()
        if term:
            terms.append(term)
    return sorted(set(terms))


# 把术语列表渲染成附录 H 的 HTML 片段（页码由第二遍填入）
def render_index_html(entries: list[tuple[str, list[int]]], book_title: str = "") -> str:
    """entries: [(term, [page1, page2, ...]), ...] 已按码位序排序。"""
    import html as _html
    lines = ['<article class="appendix" id="appendix-index">',
             f'<header><span class="book-title-marker" aria-hidden="true">{_html.escape(book_title)}</span><p class="chapter-number">附录 H</p><h1>术语索引</h1></header>',
             '<p class="part-goal">按 Unicode 码位序。仅收录在正文中出现过的术语；'
             '只在术语表定义的词请直接查附录 D。每条最多列 6 个页码。</p>',
             '<div class="index-entries">']
    for term, pages in entries:
        page_str = "、".join(str(p) for p in sorted(set(pages))[:6])
        if len(pages) > 6:
            page_str += " …"
        lines.append(f'<div class="index-entry"><span class="term">{_html.escape(term)}</span><span class="pages">{page_str}</span></div>')
    lines.append("</div></article>")
    return "\n".join(lines)
