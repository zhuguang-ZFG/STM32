#!/usr/bin/env python3
"""Markdown -> 微信公众号图文 HTML。

产出「内联样式 HTML」：可直接喂 wechat-mp MCP（wechat_web_write_draft），
也可在浏览器全选复制粘贴进公众号编辑器。
- 表格 / 代码块 / 引用全部内联样式（编辑器只认内联）
- 列表转「• / 序号」独立段落（公众号不渲染 ul/li，MCP 预检 fail-closed）
- SVG 插图用 headless Chrome 转成 PNG（2x 清晰度），GIF/PNG 直接拷贝
- 插图用绝对路径 src（MCP 自动上图床 / file:// 预览均可解析）
- <video> 块转成「插入视频」占位框（公众号视频必须从素材库手动插入）
- 每张图带一行灰色小字标注插图文件名，丢图时按名字从 images/ 补

用法：
    python tools/md2mp.py                 # 全部 26 章 + 4 速查表
    python tools/md2mp.py --only 00       # 只转某一章（调试用）
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "wechat-mp"
IMG_DIR = OUT / "images"
ART_DIR = OUT / "articles"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
REPO_URL = "https://github.com/zhuguang-ZFG/STM32"

CS_DIGESTS = {
    "HAL速查表": "HAL 常用函数一页查：GPIO / UART / TIM / ADC",
    "寄存器速查表": "RCC / GPIO / UART / TIM 寄存器一页查",
    "外设总线与引脚速查表": "总线挂载与引脚复用一页查，接线不翻手册",
    "错误码与排查速查表": "常见报错：现象 → 原因 → 解决一页查",
}

ACCENT = "#0c7ea4"      # 青（与封面一致）
INK = "#1f2937"         # 正文
MUTED = "#6b7280"
DARK = "#0f172a"

STYLES = {
    "h2": f"margin:34px 0 16px;padding-left:12px;border-left:5px solid {ACCENT};"
          f"font-size:21px;font-weight:700;color:{DARK};line-height:1.4;",
    "h3": f"margin:26px 0 12px;font-size:18px;font-weight:700;color:{DARK};",
    "h4": f"margin:20px 0 10px;font-size:16px;font-weight:700;color:{DARK};",
    "p": "margin:14px 0;line-height:1.9;",
    "blockquote": f"margin:18px 0;padding:12px 16px;background:#f0f9ff;"
                  f"border-left:4px solid {ACCENT};color:#4b5563;font-size:15px;",
    "table": "margin:18px 0;width:100%;border-collapse:collapse;font-size:14px;line-height:1.6;",
    "th": f"padding:9px 10px;background:{DARK};color:#fff;font-weight:600;"
          f"border:1px solid {DARK};text-align:left;white-space:nowrap;",
    "td": "padding:8px 10px;border:1px solid #e5e7eb;color:#374151;vertical-align:top;",
    "code_inline": "padding:2px 6px;background:#f3f4f6;color:#c026d3;border-radius:4px;"
                   "font-family:Consolas,Menlo,monospace;font-size:0.88em;",
    "a": f"color:{ACCENT};text-decoration:none;",
    "strong": f"color:{DARK};font-weight:700;",
    "hr": "margin:28px 0;border:none;border-top:1px solid #e5e7eb;",
}

VIDEO_BOX = (
    '<!-- 视频位：{name}｜源文件 {src}（编辑器流程：在文末插入素材库视频；本注释对读者不可见） -->'
)

FIGURE = (
    '<figure style="margin:22px 0;text-align:center;">'
    '<img src="{src}" alt="{alt}" style="max-width:100%;border-radius:8px;" />'
    '<figcaption style="margin-top:8px;font-size:13px;color:{muted};line-height:1.6;">{caption}'
    '<span style="display:block;font-size:12px;color:#c4c9d1;">插图文件：{file}</span>'
    '</figcaption></figure>'
)


def fig_src(name: str) -> str:
    """插图绝对路径（正斜杠）：MCP 上图床与浏览器预览都能解析。"""
    return (IMG_DIR / name).as_posix()


def slugify(prefix: str, name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-").lower()
    return f"{prefix}-{stem}"


def svg_size(path: Path) -> tuple[int, int]:
    head = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    m = re.search(r'width="(\d+)"[^>]*height="(\d+)"', head)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', head)
    if m:
        return int(float(m.group(1))), int(float(m.group(2)))
    return 900, 600


class ImageResolver:
    """收集插图：SVG 用 Chrome 截图转 PNG，其余直接拷贝。"""

    def __init__(self, prefix: str, tmp_profile: Path):
        self.prefix = prefix
        self.tmp_profile = tmp_profile
        self.files: list[str] = []

    def resolve(self, src: str) -> str | None:
        """返回 images/ 下的文件名；源文件不存在返回 None。"""
        src_path = (ROOT / src.replace("../", "")).resolve()
        if not src_path.exists():
            print(f"  [warn] 缺图 {src}", file=sys.stderr)
            return None
        ext = src_path.suffix.lower()
        if ext == ".svg":
            # 动画 SVG：优先用 tools/svg2gif.py 生成的中文动图（真动画），否则退回静态 PNG 快照
            zh_gif = ROOT / "assets" / "gif" / f"{src_path.stem}-zh.gif"
            if zh_gif.exists():
                name = slugify(self.prefix, src_path.stem) + ".gif"
                dst = IMG_DIR / name
                if not dst.exists():
                    shutil.copy2(zh_gif, dst)
            else:
                name = slugify(self.prefix, src_path.stem) + ".png"
                dst = IMG_DIR / name
                if not dst.exists():
                    self._svg2png(src_path, dst)
        else:
            name = slugify(self.prefix, src_path.stem) + ext
            dst = IMG_DIR / name
            if not dst.exists():
                shutil.copy2(src_path, dst)
        self.files.append(name)
        return name

    def _svg2png(self, src: Path, dst: Path):
        w, h = svg_size(src)
        cmd = [
            CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
            f"--user-data-dir={self.tmp_profile}",
            f"--screenshot={dst}", f"--window-size={w},{h}",
            "--force-device-scale-factor=2",
            src.as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)


def preprocess(text: str, resolver: ImageResolver, placeholders: dict[str, str]) -> str:
    """视频块/HTML 图块 -> 占位 token；返回清理后的 markdown。"""
    # 去掉英文版链接行
    text = re.sub(r"^> English:.*\n?", "", text, flags=re.M)

    # <!-- video:chNN --> ... <!-- /video:chNN -->（含旁白稿则只去掉 video 标签本身）
    def video_sub(m: re.Match) -> str:
        block = m.group(0)
        src = re.search(r'src="(\.\./assets/video/[^"]+\.mp4)"', block)
        name = Path(src.group(1)).stem if src else "本章讲解"
        tok = f"MPVIDEO{len(placeholders)}TOKEN"
        placeholders[tok] = VIDEO_BOX.format(
            accent=ACCENT, dark=DARK, muted=MUTED, name=name,
            src=src.group(1) if src else "")
        # 去掉 <p align><video>...</video><br><sub>...</sub></p>，保留块内其余文字（旁白稿）
        cleaned = re.sub(
            r'<p align="center">\s*<video.*?</video>\s*(?:<br\s*/?>\s*<sub>.*?</sub>)?\s*</p>',
            f"\n\n⟦{tok}⟧\n\n", block, flags=re.S)
        return cleaned

    text = re.sub(r"<!--\s*video:.*?<!--\s*/video:.*?-->", video_sub, text, flags=re.S)

    # 残留的裸 <video> 块（无注释包裹）
    def bare_video(m: re.Match) -> str:
        src = re.search(r'src="([^"]+\.mp4)"', m.group(0))
        tok = f"MPVIDEO{len(placeholders)}TOKEN"
        name = Path(src.group(1)).stem if src else "本章讲解"
        placeholders[tok] = VIDEO_BOX.format(
            accent=ACCENT, dark=DARK, muted=MUTED, name=name,
            src=src.group(1) if src else "")
        return f"\n\n⟦{tok}⟧\n\n"

    text = re.sub(r'<p align="center">\s*<video.*?</p>', bare_video, text, flags=re.S)

    # <p align="center"><img ...><br><sub>caption</sub></p>
    def html_img(m: re.Match) -> str:
        attrs, caption = m.group(1), m.group(2) or ""
        src = re.search(r'src="([^"]+)"', attrs)
        alt = re.search(r'alt="([^"]*)"', attrs)
        if not src:
            return ""
        name = resolver.resolve(src.group(1))
        if not name:
            return ""
        caption_txt = re.sub(r"<[^>]+>", "", caption).strip() or (alt.group(1) if alt else "")
        tok = f"MPIMG{len(placeholders)}TOKEN"
        placeholders[tok] = FIGURE.format(src=fig_src(name), file=name, alt=caption_txt,
                                          caption=caption_txt, muted=MUTED)
        return f"\n\n⟦{tok}⟧\n\n"

    text = re.sub(
        r'<p align="center">\s*<img([^>]+)>\s*(?:<br\s*/?>\s*<sub>(.*?)</sub>)?\s*</p>',
        html_img, text, flags=re.S)
    return text


def plainify_lists(html: str) -> str:
    """<ul>/<ol> 转「• / 序号」独立段落：公众号编辑器不渲染列表标签，MCP 预检 fail-closed。"""
    def block(m: re.Match) -> str:
        ordered = m.group(1) == "ol"
        items = re.findall(r"<li[^>]*>(.*?)</li>", m.group(2), flags=re.S)
        out = []
        for i, it in enumerate(items, 1):
            it = re.sub(r"</?p[^>]*>", "", it.strip())
            it = re.sub(r"^\s*\[ \]\s*", "☐ ", it)
            it = re.sub(r"^\s*\[[xX]\]\s*", "☑ ", it)
            out.append(f'<p>{f"{i}. " if ordered else "• "}{it}</p>')
        return "\n".join(out)
    return re.sub(r"<(ul|ol)[^>]*>(.*?)</\1>", block, html, flags=re.S)


CODE_LINE = ("margin:0;color:#e2e8f0;font-family:Consolas,Menlo,monospace;"
             "font-size:13px;line-height:1.7;white-space:pre-wrap;")


def mpify_code(html: str) -> str:
    """<pre><code> 逐行转独立段落：公众号编辑模型会坍缩 pre 内换行（API 直写路径实测）。"""
    def repl(m: re.Match) -> str:
        lines = m.group(1).split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        ps = "".join(
            f'<p style="{CODE_LINE}">{ln if ln.strip() else "&nbsp;"}</p>' for ln in lines)
        return (f'<section style="margin:18px 0;padding:14px 16px;background:{DARK};'
                f'border-radius:8px;overflow-x:auto;">{ps}</section>')
    return re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", repl, html, flags=re.S)


def style_html(html: str) -> str:
    """给标签注入内联样式。"""
    for tag in ("h2", "h3", "h4", "blockquote", "table", "th", "td",
                "hr", "strong"):
        html = re.sub(rf"<{tag}([^>]*)>", rf'<{tag}\1 style="{STYLES[tag]}">', html)
    html = re.sub(r"<a ([^>]*)>", rf'<a \1 style="{STYLES["a"]}">', html)
    html = re.sub(r"<code>", f'<code style="{STYLES["code_inline"]}">', html)
    html = re.sub(r"<p>", f'<p style="{STYLES["p"]}">', html)
    html = re.sub(r"<img ([^>]*)>", rf'<img \1 style="max-width:100%;border-radius:8px;" />', html)
    return html


def md_images(html: str, resolver: ImageResolver) -> str:
    """markdown 语法产生的 <img>（主要是 GIF/PNG）-> figure。"""
    def sub(m: re.Match) -> str:
        attrs = m.group(1)
        src_m = re.search(r'src="([^"]+)"', attrs)
        alt_m = re.search(r'alt="([^"]*)"', attrs)
        if not src_m:
            return m.group(0)
        src, alt = src_m.group(1), alt_m.group(1) if alt_m else ""
        if src.startswith("images/") or src.startswith("http"):
            return m.group(0)  # 已处理 / 外链徽章
        name = resolver.resolve(src)
        if not name:
            return ""
        return FIGURE.format(src=fig_src(name), file=name, alt=alt, caption=alt, muted=MUTED)

    return re.sub(r"<img ([^>]*)/?>", sub, html)


def convert(md_path: Path, prefix: str, tmp_profile: Path) -> dict:
    raw = md_path.read_text(encoding="utf-8")
    title_m = re.search(r"^# (.+)$", raw, flags=re.M)
    h1 = title_m.group(1).strip() if title_m else md_path.stem
    raw = raw.replace(title_m.group(0), "", 1) if title_m else raw  # 标题进公众号标题栏，正文不重复

    placeholders: dict[str, str] = {}
    resolver = ImageResolver(prefix, tmp_profile)
    text = preprocess(raw, resolver, placeholders)

    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    body = plainify_lists(body)
    body = mpify_code(body)
    body = style_html(body)
    body = md_images(body, resolver)

    for tok, frag in placeholders.items():
        body = body.replace(f"<p style=\"{STYLES['p']}\">⟦{tok}⟧</p>", frag)
        body = body.replace(f"⟦{tok}⟧", frag)

    footer = (
        f'<hr style="{STYLES["hr"]}" />'
        f'<section style="margin:22px 0;padding:16px 18px;border:1px solid #e5e7eb;border-radius:10px;background:#f9fafb;">'
        f'<p style="margin:0 0 8px;font-size:15px;color:{DARK};font-weight:700;">'
        f'❤️ 觉得有用？三件小事，让这份教程被更多自学的朋友看到</p>'
        f'<p style="margin:0;font-size:14px;color:{MUTED};line-height:2;">'
        f'1️⃣ 点右下角「👍 赞」——让平台把它推荐给同样在学的人；<br/>'
        f'2️⃣ 点右上角「⋯ → 收藏 / 转发」——需要时随查随用，转给同学一起进步；<br/>'
        f'3️⃣ 点「☆ 在看」或把「SIAI小宇宙」设为<b>星标⭐</b>——更新第一时间送到你面前。</p>'
        f'</section>'
        f'<p style="{STYLES["p"]}font-size:14px;color:{MUTED};">'
        f'本文配套源码、速查表与可视化动画都在开源仓库（已公开），点左下角「阅读原文」直达 GitHub。</p>'
        f'<p style="{STYLES["p"]}font-size:14px;color:{MUTED};">'
        f'📌 <strong>关注「SIAI小宇宙」</strong>：26 章图文 + 每章讲解视频持续连载；'
        f'进入合集「STM32零基础自学」从第 00 章连续看，回复「资料」可领速查表。</p>'
    )
    html = (
        f'<section style="font-family:-apple-system,BlinkMacSystemFont,'
        f'&quot;Helvetica Neue&quot;,&quot;PingFang SC&quot;,&quot;Microsoft YaHei&quot;,sans-serif;'
        f'font-size:16px;color:{INK};line-height:1.9;letter-spacing:.3px;">'
        + body + footer + "</section>"
    )

    out = ART_DIR / f"{md_path.stem}.html"
    out.write_text(html, encoding="utf-8")
    return {"id": prefix, "h1": h1, "html": f"articles/{out.name}", "images": resolver.files}


def load_digests() -> dict[str, str]:
    """从 docs/README.md 表格抽每章「一句话」作为公众号摘要。"""
    digests: dict[str, str] = {}
    readme = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    for m in re.finditer(r"\| \d+ \| \[[^\]]+\]\((\d+-[^)]+)\.md\) \| ([^|]+) \|", readme):
        digests[m.group(1)] = m.group(2).strip()
    return digests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只转某一章（如 00）")
    args = ap.parse_args()

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)
    digests = load_digests()
    manifest: list[dict] = []

    targets: list[tuple[Path, str]] = []
    for p in sorted((ROOT / "docs").glob("[0-9][0-9]-*.md")):
        targets.append((p, f"ch{p.name[:2]}"))
    for p in sorted((ROOT / "cheatsheets").glob("*.md")):
        targets.append((p, f"cs-{p.stem[:6]}"))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_profile = Path(tmp) / "chrome-profile"
        for md_path, prefix in targets:
            if args.only and not md_path.name.startswith(args.only):
                continue
            print(f"[md2mp] {md_path.name}")
            meta = convert(md_path, prefix, tmp_profile)
            stem = md_path.stem
            key = stem.split("-")[0] + "-" + stem.split("-", 1)[1] if "-" in stem else stem
            digest = digests.get(stem) or CS_DIGESTS.get(stem) or meta["h1"]
            if md_path.parent.name == "docs":
                num, name = stem[:2], stem[3:]
                meta["title"] = f"STM32零基础自学 · 第{num}章 | {name}"
            else:
                meta["title"] = f"STM32速查表 | {stem}"
            meta["digest"] = digest
            meta["cover"] = f"covers/{prefix}.jpg"
            meta["url"] = f"{REPO_URL}/blob/main/{md_path.parent.name}/{md_path.name}"
            manifest.append(meta)

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[md2mp] 完成 {len(manifest)} 篇 -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
