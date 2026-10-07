#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


check_assets.py —— 素材自检工具（不需要任何第三方库，也不用打开图片）。

做三件事：
1. 校验 assets/ 下所有 SVG 是合法 XML；
2. 用自己实现的 GIF 解码器把 assets/gif/*.gif 解回来，逐像素与「重新生成的帧」比对，
   确保 LZW 编码、差分帧、透明索引都正确（沙箱里没有浏览器也能验证）；
3. 打印体积统计，超过 500 KB 的 GIF 会告警。

用法::

    python3 tools/check_assets.py
"""

from __future__ import annotations

import os
import struct
import sys
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


# --------------------------------------------------------------------------- GIF 解码


def lzw_decode(data, min_code_size):
    """GIF LZW 解码。注意解码器的码表比编码器慢一格（GIF 的经典不对称）。"""
    clear = 1 << min_code_size
    end = clear + 1
    code_size = min_code_size + 1
    table = {i: [i] for i in range(clear)}
    next_code = end + 1
    out = []
    prev = None
    bitpos = 0
    total_bits = len(data) * 8
    while bitpos + code_size <= total_bits:
        byte = bitpos >> 3
        chunk = int.from_bytes(data[byte:byte + 3], "little")
        code = (chunk >> (bitpos & 7)) & ((1 << code_size) - 1)
        bitpos += code_size
        if code == clear:
            table = {i: [i] for i in range(clear)}
            next_code = end + 1
            code_size = min_code_size + 1
            prev = None
            continue
        if code == end:
            break
        if code in table:
            entry = table[code]
        elif code == next_code and prev is not None:
            entry = prev + [prev[0]]
        else:
            raise ValueError(f"LZW 码流损坏：code={code} next={next_code}")
        out.extend(entry)
        if prev is not None and next_code < 4096:
            table[next_code] = prev + [entry[0]]
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        prev = entry
    return out


def decode_gif(path):
    """返回 (w, h, [(rgb_bytes, delay, disposal), ...])。"""
    raw = open(path, "rb").read()
    assert raw[:6] in (b"GIF89a", b"GIF87a"), "不是 GIF 文件"
    w, h = struct.unpack("<HH", raw[6:10])
    packed = raw[10]
    gct_size = 2 ** ((packed & 0x07) + 1)
    pos = 13
    gct = []
    for _ in range(gct_size):
        gct.append(tuple(raw[pos:pos + 3]))
        pos += 3
    frames = []
    canvas = bytearray(w * h * 3)
    transparent_index = None
    delay = 0
    disposal = 0
    while pos < len(raw):
        blk = raw[pos]
        if blk == 0x3B:
            break
        if blk == 0x21:                      # 扩展块
            label = raw[pos + 1]
            pos += 2
            if label == 0xF9:
                size = raw[pos]
                gce = raw[pos + 1:pos + 1 + size]
                gce_packed = gce[0]
                disposal = (gce_packed >> 2) & 0x07
                transparent_index = gce[3] if (gce_packed & 0x01) else None
                delay = struct.unpack("<H", gce[1:3])[0]
                pos += 1 + size + 1     # 末尾的 0x00 终止符
            else:
                while raw[pos] != 0:
                    pos += 1 + raw[pos]
                pos += 1
            continue
        if blk == 0x2C:                      # 图像描述符
            x0, y0, iw, ih = struct.unpack("<HHHH", raw[pos + 1:pos + 9])
            lpacked = raw[pos + 9]
            pos += 10
            if lpacked & 0x80:
                pos += 3 * 2 ** ((lpacked & 0x07) + 1)
            min_code = raw[pos]
            pos += 1
            data = bytearray()
            while raw[pos] != 0:
                ln = raw[pos]
                data += raw[pos + 1:pos + 1 + ln]
                pos += 1 + ln


            pos += 1
            indices = lzw_decode(bytes(data), min_code)
            assert len(indices) >= iw * ih, "LZW 解码像素数不足"
            for y in range(ih):
                for x in range(iw):
                    idx = indices[y * iw + x]
                    if idx == transparent_index:
                        continue
                    o = ((y0 + y) * w + (x0 + x)) * 3
                    canvas[o:o + 3] = bytes(gct[idx])
            frames.append((bytes(canvas), delay, disposal))
            continue
        raise ValueError(f"未知块 0x{blk:02x} @ {pos}")
    return w, h, frames


# --------------------------------------------------------------------------- 自检


def check_svg():
    bad, total = 0, 0
    for root, _, files in os.walk(os.path.join(ROOT, "assets")):
        for f in sorted(files):
            if not f.endswith(".svg"):
                continue
            p = os.path.join(root, f)
            total += 1
            try:
                tree = xml.dom.minidom.parse(p)
            except Exception as e:            # noqa: BLE001
                print(f"[FAIL] {p}: {e}")
                bad += 1
                continue
            root_el = tree.documentElement
            try:
                w = float(root_el.getAttribute("width"))
                h = float(root_el.getAttribute("height"))
            except ValueError:
                print(f"[FAIL] {p}: 缺少 width/height")
                bad += 1
                continue
            dead = _dead_classes(open(p, encoding="utf-8").read())
            if dead:
                print(f"[WARN] {p}: {len(dead)} 个 class 没有对应样式"
                      f"（动画不会播放）：{sorted(dead)[:4]}")
            over = _overflow(root_el, w, h)
            if over:
                print(f"[WARN] {p}: {len(over)} 个元素超出画布 {w:g}x{h:g}"
                      f"（示例：{over[0]}）")
            if os.path.getsize(p) > 500 * 1024:
                print(f"[WARN] {p} 体积过大")
    print(f"SVG 检查完成：{total - bad}/{total} 合法")
    return bad == 0


def _dead_classes(svg_text):
    """找出「用了 class 但 <style> 里没定义」的元素 —— 这类动画不会播放。"""
    import re
    style = "".join(re.findall(r"<style>(.*?)</style>", svg_text, flags=re.S))
    defined = set(re.findall(r"\.([A-Za-z0-9_-]+)", style))
    used = set()
    for attr in re.findall(r'class="([^"]+)"', svg_text):
        used.update(attr.split())
    return {c for c in used if c not in defined}


def _num(el, name, default=0.0):
    try:
        return float(el.getAttribute(name) or default)
    except ValueError:
        return default


def _overflow(root_el, w, h, tol=2.0):
    """找出明显超出画布的元素（自绘图的常见低级错误）。"""
    out = []
    for el in root_el.getElementsByTagName("*"):
        tag = el.tagName
        if tag in ("rect", "image", "use"):
            x, y = _num(el, "x"), _num(el, "y")
            ww, hh = _num(el, "width"), _num(el, "height")
            if (x < -tol or y < -tol or x + ww > w + tol or y + hh > h + tol):
                out.append((tag, x, y, ww, hh))
        elif tag == "text":
            x, y = _num(el, "x"), _num(el, "y")
            if x < -tol or y < -tol or x > w + tol or y > h + tol:
                out.append((tag, x, y))
        elif tag == "line":
            xs = (_num(el, "x1"), _num(el, "x2"))
            ys = (_num(el, "y1"), _num(el, "y2"))
            if (min(xs) < -tol or max(xs) > w + tol or min(ys) < -tol
                    or max(ys) > h + tol):
                out.append((tag, min(xs), min(ys), max(xs), max(ys)))
    return out


def check_gif():
    import gen_gifs
    ok = True
    for name, builder in gen_gifs.BUILDERS.items():
        path = os.path.join(ROOT, "assets", "gif", name + ".gif")
        if not os.path.exists(path):
            print(f"[FAIL] 缺少 {path}")
            ok = False
            continue
        w, h, frames = decode_gif(path)
        gif = builder()
        want_frames = gif.frames
        if (w, h) != (gif.w, gif.h):
            print(f"[FAIL] {name}: 尺寸不符 {(w, h)} != {(gif.w, gif.h)}")
            ok = False
            continue
        if len(frames) != len(want_frames):
            print(f"[FAIL] {name}: 帧数不符 {len(frames)} != {len(want_frames)}")
            ok = False
            continue
        for i, ((got, _d, _dp), want) in enumerate(zip(frames, want_frames)):
            if got != want:
                for p in range(0, len(want), 3):
                    if got[p:p + 3] != want[p:p + 3]:
                        print(f"[FAIL] {name} 第 {i} 帧第 {p // 3} 像素不符 "
                              f"{tuple(got[p:p + 3])} != {tuple(want[p:p + 3])}")
                        break
                ok = False
                break
        size = os.path.getsize(path) / 1024
        flag = "ok" if size <= 500 else "WARN"
        print(f"[{flag}] {name}.gif  {w}×{h}  {len(frames)} 帧  "
              f"{size:6.1f} KB  每帧 {frames[0][1] / 100:.2f}s")
    return ok


def check_links():
    """校验 Markdown 里的相对链接与图片引用是否真实存在。"""
    import re
    pat_md = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
    pat_html = re.compile(r'(?:src|href)="([^"]+)"')
    bad, total = 0, 0

    for root, dirs, files in os.walk(ROOT):
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            p = os.path.join(root, f)
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
            # 去掉围栏代码块里的示例链接，避免误报
            text = re.sub(r"```.*?```", "", text, flags=re.S)
            urls = [m.group(1) for m in pat_md.finditer(text)]
            urls += [m.group(1) for m in pat_html.finditer(text)]
            for url in urls:
                if url.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                total += 1
                target = url.split("#")[0]
                if not target:
                    continue
                full = os.path.normpath(os.path.join(root, target))
                if not os.path.exists(full):
                    print(f"[FAIL] {os.path.relpath(p, ROOT)} -> {url} 不存在")
                    bad += 1
    print(f"链接检查完成：{total - bad}/{total} 有效")
    return bad == 0


if __name__ == "__main__":
    a = check_svg()
    b = check_gif()
    c = check_links()
    ok = a and b and c
    print("结果：", "全部通过 ✅" if ok else "存在问题 ❌")
    sys.exit(0 if ok else 1)

