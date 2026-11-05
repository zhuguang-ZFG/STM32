# AI 视频工具清单社媒成片（B站/抖音/小红书/视频号）

## Goal

把 369 仓库 AI 视频工具清单（快照 `research/source-snapshot-369-repos.md`，数据 2026-10-27 GitHub API）中的**四大框架**做成一条手绘口播短视频，交付四平台成片、封面与文案。用户已定三项：创建本任务、用 sweety-handdraw-video 管线（非自建）、内容口径=四大框架深挖。

## Requirements

1. **内容口径**：四大框架各一段 + 选型收尾——lemo-opuscar（8,322★，59 种 Opus 5.5 调优风格、纯代码渲染、代表作 OPUSCAR 98 样片 6 分 31 秒 98 种视觉风格）、huashu-art-motion（5,418★，36 艺术风格 + 9 解说语法 + 8 参数化片段、马里奥 65 秒/Clawd 博物馆 98 秒样片）、huashu-motion（1,766★，ABC 记谱合成动画）、sweety-handdraw-video（903★，手绘涂鸦口播管线）；结尾给「拿清单」钩子。事实只出自快照，星数须带快照口径。
2. **制作管线**：sweety-handdraw-video v2.0.2 官方契约——job 目录（job.json + design.json + design/art-direction.json + inputs/…），跑 doctor → build → render → verify → finalize。风格走涂鸦信息图方向；插画由本会话自绘 SVG→PNG（宿主无生图工具，插画提供方=本会话，美术记录按契约全量填写）。
3. **配音**：edge-tts 云扬 zh-CN-YunyangNeural（与既有 18 集同音色家族），`boundary='WordBoundary'` 逐字时间戳实测可用；语速候选 +0%/+2%（沿用 v2 探针结论）。
4. **画幅**：双母版——9:16 1080×1920（抖音/视频号/小红书）+ 16:9 1920×1080（B站），30fps，H.264 yuv420p。
5. **Windows 适配零源码修改**：字体在 job.json 显式指定（手写=simkai.ttf 楷体、字幕=msyh.ttc 雅黑，cmap 逐字覆盖实证）；skill 依赖走 `PYTHONPATH=video/pydeps` 遮蔽；语音注入走自写 runner。
6. **平台约束**（沿用本仓库实测）：视频号码率 ≤10Mbps、MP4/H.264、≤60fps；抖音标题 ≤30 字；小红书标题 ≤20 字、正文 ≤1000 字；B站简介纯文本。
7. **不自动发布**：发布沿用 `I_HAVE_USER_OK=<ep>` 闸门（见 research/wx-plan.md），本任务只交付文件。

## Acceptance Criteria

- [ ] doctor `ready`：tools（ffmpeg/ffprobe）✓、fonts 全角色覆盖 ✓、inputs 无缺失 ✓、art_direction 验证 ✓（voice_backends 缺席不阻断——narration 以文件形态就位）
- [ ] build → render → verify → finalize 全绿（黄金 5 秒、audio_gate、image_gate/lineart_gate、字幕覆盖、产物哈希清单）
- [ ] 成片两条：竖版 60–90s + 横版同内容重排（非裁切）；四平台文件齐（douyin/wx/xhs 用竖版，bili 用横版）
- [ ] 每图美术记录完整：brief/prompt 文件 + sha256 + status/evidence；隐私清洗（clean_image 等价处理）
- [ ] 字体覆盖：楷体覆盖全部手写文本、雅黑覆盖全部字幕（fonts.py check_coverage 实证，缺字则换字）
- [ ] 视频号交付版实测码率 ≤10Mbps；四平台封面 + 文案清单交付（`publish/copy-ai4fw.md`）
- [ ] 全程未修改 skill 仓库源码；所有适配落在 job 配置与本仓库自写脚本

## Out of Scope

- 四平台之外的分发（YouTube 等）；369 清单全量盘点（只深挖四框架）；skill 的 macOS 专属能力（mlx_whisper/mlx_audio、VoiceStudio/VoxCPM 合成通道）
