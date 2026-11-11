# 开始时的可选制作设置

主题、故事、附件正文或可读取的明确来源至少有一项。全部缺失才向用户索要内容。其余是偏好，不构成停工条件。

## 配置类型（总闸）

先问一次，不再弹网页：

1. **模型推理（默认）** — 按主题与内容自动选最佳项，写完 `options/defaults.json` 即可继续。
2. **主动选择** — 进入原生逐项选择：比例 → 风格 → 声音 → 字幕。

兼容 Claude Code（AskUserQuestion）、Codex 等价提问、以及终端数字菜单（`production_options.py --mode tty`）。HTML 弹窗仅 `--mode html` 调试保留，不是主路径。

```json
{
  "content": "用户的实际主题或故事摘要",
  "config_type": "model_infer",
  "aspect": {"aspect_ratio": "2:3", "width": 1280, "height": 1920},
  "style": {"mode": "inferred"},
  "hand": {"preset": "pen-only"},
  "voice": {"voice": "magnetic-narrator"},
  "advertising": {"text": ""},
  "watermark": {"text": ""},
  "captions": {"mode": "quiet"},
  "rationale": {
    "style": "按内容推理线稿+平涂讲解风",
    "aspect": "默认竖屏 2:3",
    "voice": "磁性解说男声适合平实讲解",
    "captions": "浅色画面适合无底板短句"
  }
}
```

## 视频比例

| 选项 | 像素 | 说明 |
|---|---|---|
| **2:3（默认，2.0 起）** | 1280×1920 | 竖屏；信息流里比 9:16 更不易被界面遮挡，插画横向更宽 |
| 9:16 | 1080×1920 | 全屏短视频竖屏 |
| 3:4 | 1440×1920 | |
| 16:9 | 1920×1080 | 横屏 |
| 4:3 | 1920×1440 | |
| 3:2 | 1920×1280 | |
| 自定义 | 宽×高 | 每边 720–2160，偶数，总像素有上限 |

模型推理路径也默认 2:3；用户口头指定才改（要全屏短视频就选 9:16）。不因“知识向”擅自改横屏。

## 风格（文字列表，无预览图）

- 默认 **模型推理**（`mode: inferred`）。
- 主动选择时列出全部风格名称为软选项；**列表不约束模型**。
- 可绘制性仍是物理约束：无干净墨线+平涂时，落到可绘制执行面，或用户明确接受 reveal（`reveal_accepted`）。
- 广告/水印/手臂默认：空广告、空水印、`pen-only`；不进主动选择主路径，用户明确要求再改。

## 命令

```bash
# 模型写好 defaults 后
python3 scripts/production_options.py JOB --defaults JOB/options/defaults.json
# 输出 PRODUCTION_OPTIONS_CONTRACT=... 供宿主原生提问；model_infer 会直接 COMPLETE

# 终端数字菜单
python3 scripts/production_options.py JOB --defaults JOB/options/defaults.json --mode tty

# 主动选择逐步提交
python3 scripts/production_options.py JOB --choose aspect --value '{"aspect_ratio":"9:16"}'

# 写入 job.json
python3 scripts/production_options.py JOB --apply
```

`apply` 写入 `canvas.width/height/aspect_ratio`、`hand`、`voice_*`、`watermark`、`captions`。

用户已明确的选择放 `options/explicit.json`。用户说“全部自动”→ `config_type: model_infer`，画风 `confirmation: user_delegated`。
