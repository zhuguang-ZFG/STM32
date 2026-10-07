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
import subprocess
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


def _check_gif_builders(builders, folder, label):
    ok = True
    for name, builder in builders.items():
        path = os.path.join(ROOT, "assets", folder, name + ".gif")
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
        print(f"[{flag}] {label}/{name}.gif  {w}×{h}  {len(frames)} 帧  "
              f"{size:6.1f} KB  每帧 {frames[0][1] / 100:.2f}s")
    return ok


def check_gif():
    import gen_gifs
    return _check_gif_builders(gen_gifs.BUILDERS, "gif", "gif")


def check_videos():
    """讲解 MP4：海报可重画、时长在 2–4 分钟、字幕与旁白稿一致、有人声。"""
    import gen_narrated
    from PIL import Image
    ok = True
    video = os.path.join(ROOT, "assets", "video")
    docs = os.path.join(ROOT, "docs")
    for ch in gen_narrated.CHAPTERS:
        name = gen_narrated.chapter_name(ch)
        png = os.path.join(video, name + ".png")
        mp4 = os.path.join(video, name + ".mp4")
        srt = os.path.join(video, name + ".srt")
        gif = os.path.join(video, name + ".gif")
        if os.path.isfile(gif):
            print(f"[FAIL] {name}.gif 仍在，讲解已改为 MP4")
            ok = False
        if not os.path.isfile(png):
            print(f"[FAIL] 缺少海报 {name}.png")
            ok = False
        else:
            got = Image.open(png).convert("RGB")
            want = gen_narrated.render_poster(ch)
            if got.size != (gen_narrated.W, gen_narrated.H) or got.tobytes() != want.tobytes():
                print(f"[FAIL] {name}.png 与脚本画出的海报不一致")
                ok = False
            got.close()
        if not os.path.isfile(mp4) or not os.path.isfile(srt):
            print(f"[FAIL] 缺少 {name} 的 mp4 或 srt")
            ok = False
            continue
        dur, streams = _probe_av(mp4)
        if streams.get("v") != ("h264", gen_narrated.W, gen_narrated.H):
            print(f"[FAIL] {name} 视频流不是 960×540 H.264：{streams.get('v')}")
            ok = False
        if streams.get("a") != "aac":
            print(f"[FAIL] {name} 没有 AAC 音轨")
            ok = False
        if not 120 <= dur <= 240:
            print(f"[FAIL] {name} 时长 {dur:.1f}s 不在 2–4 分钟")
            ok = False
        cues = _parse_srt(open(srt, encoding="utf-8").read())
        says = [s["say"] for s in ch["segments"]]
        if len(cues) != len(says):
            print(f"[FAIL] {name} 字幕 {len(cues)} 条，旁白 {len(says)} 段")
            ok = False
        else:
            for i, (cue, say) in enumerate(zip(cues, says), start=1):
                if _flat(cue[2]) != _flat(say):
                    print(f"[FAIL] {name} 第 {i} 条字幕和旁白稿不一致")
                    ok = False
                    break
            if cues and (cues[0][0] > 0.05 or abs(cues[-1][1] - dur) > 1.0):
                print(f"[FAIL] {name} 字幕没有盖住成片 "
                      f"({cues[0][0]:.2f}–{cues[-1][1]:.2f}s，片长 {dur:.2f}s)")
                ok = False
            for prev, cur in zip(cues, cues[1:]):
                if cur[0] + 0.05 < prev[1] or cur[0] - prev[1] > 0.05:
                    print(f"[FAIL] {name} 字幕时间不连续")
                    ok = False
                    break
        if not _has_voice(mp4):
            print(f"[FAIL] {name} 前 20 秒几乎没有人声")
            ok = False
        else:
            print(f"[ok] {name}.mp4  {dur:.0f}s  字幕 {len(cues)} 条")
        for folder in (docs, os.path.join(docs, "en")):
            hit = False
            for fn in os.listdir(folder):
                if fn.startswith(ch["id"] + "-") and fn.endswith(".md"):
                    text = open(os.path.join(folder, fn), encoding="utf-8").read()
                    hit = (name + ".mp4") in text and (name + ".srt") in text
                    break
            if not hit:
                print(f"[FAIL] {folder} 章节 {ch['id']} 未引用 {name}.mp4")
                ok = False
    if ok:
        print(f"讲解视频检查完成：{len(gen_narrated.CHAPTERS)} 章 MP4 + SRT + 海报")
    return ok


def _flat(text):
    return "".join(text.split())


def _parse_srt(text):
    import re
    cues = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        a, b = [p.strip() for p in lines[1].split("-->")]
        cues.append((_srt_sec(a), _srt_sec(b), "\n".join(lines[2:])))
    return cues


def _srt_sec(stamp):
    hms, ms = stamp.split(",")
    h, m, s = [int(x) for x in hms.split(":")]
    return h * 3600 + m * 60 + s + int(ms) / 1000


def _probe_av(path):
    import json
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", path],
        text=True,
    )
    data = json.loads(raw)
    streams = {}
    for st in data.get("streams", []):
        if st.get("codec_type") == "video":
            streams["v"] = (st.get("codec_name"), st.get("width"), st.get("height"))
        elif st.get("codec_type") == "audio":
            streams["a"] = st.get("codec_name")
    return float(data["format"]["duration"]), streams


def _has_voice(path):
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-t", "20", "-i", path,
         "-af", "volumedetect", "-f", "null", "-"],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    for line in proc.stderr.splitlines():
        if "mean_volume:" in line:
            db = float(line.split("mean_volume:")[1].split("dB")[0])
            return db > -40
    return False


def check_sim():
    """Wokwi 图必须是合法 JSON，Renode 脚本必须点名官方 repl。"""
    import json
    ok = True
    examples = os.path.join(ROOT, "examples")
    required = [
        "gpio-blink", "exti-key", "timer-pwm",
        "uart-dma-idle", "i2c-oled", "adc-dma",
    ]
    for name in required:
        folder = os.path.join(examples, name)
        diagram = os.path.join(folder, "diagram.json")
        toml = os.path.join(folder, "wokwi.toml")
        if not os.path.isfile(diagram) or not os.path.isfile(toml):
            print(f"[FAIL] {name} 缺少 diagram.json 或 wokwi.toml")
            ok = False
            continue
        try:
            data = json.load(open(diagram, encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[FAIL] {name}/diagram.json 不是合法 JSON：{exc}")
            ok = False
            continue
        if data.get("version") != 1 or "parts" not in data or "connections" not in data:
            print(f"[FAIL] {name}/diagram.json 缺少 version/parts/connections")
            ok = False
        types = [p.get("type") for p in data["parts"]]
        if "board-stm32-bluepill" not in types:
            print(f"[FAIL] {name} 没有 board-stm32-bluepill")
            ok = False
        text = open(toml, encoding="utf-8").read()
        if "[wokwi]" not in text or "firmware" not in text:
            print(f"[FAIL] {name}/wokwi.toml 缺少 [wokwi] 或 firmware")
            ok = False
    for name in ("gpio-blink.resc", "uart-usart1.resc"):
        path = os.path.join(ROOT, "sim", "renode", name)
        if not os.path.isfile(path):
            print(f"[FAIL] 缺少 {path}")
            ok = False
            continue
        body = open(path, encoding="utf-8").read()
        if "platforms/cpus/stm32f103.repl" not in body or "usart1" not in body:
            print(f"[FAIL] {name} 未引用 stm32f103.repl / usart1")
            ok = False
    if ok:
        print(f"仿真配置检查完成：{len(required)} 个 Wokwi 工程 + 2 个 Renode 脚本")
    return ok


def check_pinouts():
    """H7/G0/L4 引脚图必须在，且页脚带上数据手册编号。"""
    ok = True
    expect = {
        "pinout-stm32g071rb-lqfp64.svg": ("DS12232", "PC11", "G071"),
        "pinout-stm32l476rg-lqfp64.svg": ("DS10198", "VBAT", "L476"),
        "pinout-stm32h743zi-lqfp144.svg": ("DS12110", "PE2", "H743"),
    }
    boards = os.path.join(ROOT, "assets", "boards")
    for name, needles in expect.items():
        path = os.path.join(boards, name)
        if not os.path.isfile(path):
            print(f"[FAIL] 缺少引脚图 {name}")
            ok = False
            continue
        text = open(path, encoding="utf-8").read()
        for needle in needles:
            if needle not in text:
                print(f"[FAIL] {name} 未包含 {needle}")
                ok = False
    docs = os.path.join(ROOT, "docs")
    for ch, svg in (
        ("23-", "pinout-stm32g071rb-lqfp64.svg"),
        ("24-", "pinout-stm32l476rg-lqfp64.svg"),
        ("25-", "pinout-stm32h743zi-lqfp144.svg"),
    ):
        hit = False
        for fn in os.listdir(docs):
            if fn.startswith(ch) and fn.endswith(".md"):
                body = open(os.path.join(docs, fn), encoding="utf-8").read()
                hit = svg in body
                break
        if not hit:
            print(f"[FAIL] 章节 {ch} 未引用 {svg}")
            ok = False
    if ok:
        print("引脚图检查完成：G0 / L4 / H7 三张，页脚含手册号")
    return ok


def check_examples():
    """CAN / USB 示例要带上关键路径，避免只留一个空目录。"""
    ok = True
    root = os.path.join(ROOT, "examples")
    need = {
        "can-bxcan/main.c": (
            "CAN_MODE_LOOPBACK",
            "CAN_MODE_NORMAL",
            "FilterIdHigh",
            "AutoBusOff",
            "HAL_CAN_Stop",
            "__HAL_AFIO_REMAP_CAN1_1",
        ),
        "can-bxcan/README.md": ("500 kbit/s", "PB8", "PB9"),
        "usb-cdc/usb_cdc.c": ("0x43", "0x20U", "0x02, 0x02", "0x0A"),
        "usb-cdc/main.c": ("RCC_USBCLKSOURCE_PLL_DIV1_5", "usb_cdc_init"),
        "usb-cdc/README.md": ("48", "stm32f1xx_hal_pcd.c"),
        "usb-hid/usb_hid.c": ("0x3F", "0x09, 0x06", "0x0AU"),
        "usb-hid/main.c": ("0x04U", "RCC_USBCLKSOURCE_PLL_DIV1_5"),
        "usb-hid/README.md": ("PA0", "48"),
    }
    for rel, needles in need.items():
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            print(f"[FAIL] 缺少示例 {rel}")
            ok = False
            continue
        text = open(path, encoding="utf-8").read()
        for needle in needles:
            if needle not in text:
                print(f"[FAIL] {rel} 未包含 {needle}")
                ok = False
    if ok:
        print("示例检查完成：can-bxcan、usb-cdc、usb-hid")
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
    d = check_videos()
    e = check_sim()
    f = check_pinouts()
    g = check_examples()
    c = check_links()
    ok = a and b and c and d and e and f and g
    print("结果：", "全部通过 ✅" if ok else "存在问题 ❌")
    sys.exit(0 if ok else 1)

