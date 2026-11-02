# 可复现长课源

当前已迁移：`ch03`（GPIO 与 LED）。其余章节仍按 SPECS 分批迁移，不以旧长片的存在冒充可复现。

## 单一分镜源

`chNN/storyboard.json` 保存每个场景的：

- `scene_id` / `title` / `purpose` / `prerequisite`
- `narration` / `on_screen` / `visual_source` / `fact_source`
- `memory_anchor` / `evidence_type`

`purpose` 只允许 `hook`、`mechanism`、`failure`、`experiment`、`recall`。`visual_source` 相对 `assets/`，可以是 SVG、PNG、JPG、WebP 或 `null`。技术事实仍以对应章节与手册为准，分镜不是另一份手册。

`tools/storyboards.py` 校验源并计算预计 `start`、`duration`、`subtitle_ref`。实际时长以配音探测结果为准，写入 `storyboard-rendered.json`。

## 命令

```bash
python tools/gen_long_lesson.py --check 03       # schema + 1080p 排版，无配音
python tools/gen_long_lesson.py --posters 03     # 28 张场景海报，写到 .temp/
python tools/gen_long_lesson.py --speak 03       # 配音、关键帧、MP4、SRT、联系表、报告
python tools/gen_long_lesson.py --report 03      # 复核已有成片
```

Windows 示例环境：

```powershell
$env:NARRATED_FONT = 'C:/Windows/Fonts/msyh.ttc'
$env:NARRATED_CHROME = 'C:/path/to/chrome.exe'
```

依赖：Pillow、Playwright + Chromium、edge-tts、ffmpeg/ffprobe，以及配音时的网络访问。`NARRATED_SCALE` 默认 2，`NARRATED_FPS` 不改变长片的 30 fps；`LESSON_CRF` 可覆盖视频质量。

## 产物边界

- 可审查源：`storyboard.json`、`storyboard-rendered.json`、`chNN.srt`、`contact-sheet.jpg`、`media-report.json`。
- 本地大文件：`final-videos/chNN/chNN-bilibili-safe.mp4` 与派生发布包。该目录被 Git 忽略。
- `contact-sheet.jpg` 从实际 MP4 的开场、机制、失败、实验、回忆五类场景抽帧，不用海报替代成片证据。
- `media-report.json` 记录 MP4 与 storyboard 的 SHA-256、1080p/30fps、时长、字幕数、响度与检查结果。

配音采用既有 `zh-CN-XiaoxiaoNeural`。在线合成不保证逐比特一致，报告中的 MP4 哈希用于证明某一次本地生成，不用于宣称跨机器字节一致。
