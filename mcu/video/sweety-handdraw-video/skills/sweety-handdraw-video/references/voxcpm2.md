# VoxCPM2 制作要点（按官方教程）

本页是官方资料的执行摘要，冲突时以官方为准：

- 使用指南：https://voxcpm.readthedocs.io/en/latest/usage_guide.html
- 声音食谱（Voice Design 写法）：https://voxcpm.readthedocs.io/en/latest/cookbook.html
- FAQ：https://voxcpm.readthedocs.io/en/latest/faq.html
- 模型卡与许可（Apache-2.0）：https://huggingface.co/openbmb/VoxCPM2
- 源码与已知问题：https://github.com/OpenBMB/VoxCPM 、https://github.com/OpenBMB/VoxCPM/issues
- 本机运行的 MLX 移植：https://github.com/Blaizzy/mlx-audio （已验证 0.5.8）

## 三种模式与本流程的对应

| 官方模式 | 官方参数（PyTorch） | MLX 参数 | `voxcpm.mode` |
|---|---|---|---|
| Voice Design：文字描述生成新声音 | `text="(描述)正文"` | `instruct="描述"` | `design` |
| 可控克隆：参考定音色，括号指令调语气/语速 | `reference_wav_path` + `(指令)正文` | `ref_audio` + `instruct` | `reference`（`style`） |
| Hi-Fi 克隆：参考 + 逐字稿，相似度最高 | `prompt_wav_path`+`prompt_text`+`reference_wav_path` | `prompt_audio`+`prompt_text`+`ref_audio` | `combined`（默认） |

- Hi-Fi 模式下括号指令被忽略；要调语气用 `reference` 模式。
- `prompt_text` 必须与参考音频逐字一致，不一致是首尾杂音、漏读开头的最常见原因。官方建议用 ASR 取逐字稿，再人工核对；本流程在导入时用语速校验覆盖程度，有本地 ASR 时再核对 CER。
- Voice Design 每次调用都会得到略有不同的人（官方："像每次换一位配音演员"）。要固定音色：先设计、挑选，再把选中的那段作为参考，之后都用克隆模式。包内合成音色就是这样做的。

## 参数

| 参数 | 官方默认 | 说明 |
|---|---|---|
| `cfg_value` | 2.0 | 1.0–2.0 更自然但可能偏离文本；2.0–3.0 更贴文本但难句易出噪声。长段出现噪声/嗡声时，官方建议降到 1.5–1.6 |
| `inference_timesteps` | 10 | 推荐 4–30；步数多细节更好、更慢。已验收的逼真男声用 16，逼真女声用 24 |
| `retry_badcase` | True | 官方在音频长度异常时自动重试；最长约为“文本 token×6+10”个 patch。MLX 移植没有该功能，适配器按同一公式设置 `max_tokens`，并由本流程的分段门禁替代重试 |
| `denoise` | False | 只清理**参考音频**（16 kHz 管线，可能改变音色），不清理生成结果。参考已干净时保持关闭 |
| `normalize` | False | 数字、日期读法异常时开启；MLX 移植不提供，需在稿件里写成汉字 |

MLX 移植没有 `seed` 参数，适配器在每次生成前调用 `mx.random.seed(seed)`，同一参数、同一种子结果可复现（已在本机验证两次运行逐段一致）。

## 参考音频

- 时长 5–30 秒可用；本流程取 8–15 秒、在句末结束、尾部保留 0.5–1 秒静音。
- 越干净越好：官方 issue 中的嗡声、底噪、配乐残留会被克隆并在长段中放大。导入前必须通过 `audio_gate.py`；不通过时用 `clean_reference.py`（HTDemucs 人声分离 + DeepFilterNet3）重新切取。
- 同一声音每次复用同一参考文件；需要更稳定可考虑官方 LoRA 微调（本流程未使用）。

## 文本与长段

- 标点是韵律信号：句号/问号停顿更明显，逗号短停，省略号拖尾；需要更长停顿时拆句，不要堆标点。
- 太短的句子（“好的”）声音偏弱：训练最短约 1 秒，至少要能读出几秒。
- 长文本最容易出问题：逐渐加速、嗡声、显存增长、停不下来。官方做法是**分段生成再拼接**。本流程按语义段落合成，规则见[连续旁白约定](continuous-narration.md)：每段不超过约 100 字、只在句末切、逐段门禁并单独重生成。
- 方言要写成方言用词；本流程默认普通话。

## Voice Design 写法

官方建议一句描述里组合三类信息：

1. 基础：性别、年龄、角色（中年男性解说员）
2. 质感：音高、音色（低沉、磁性、略带沙哑）
3. 场景：情绪、节奏、用途（沉稳有力，适合知识与故事解说）

中英文描述都可以。只描述声音特征，不写真人、主播、平台音色或“像某某”，包内四款合成音色均只用文字描述生成（描述原文见 `assets/voices/catalog.json` 的 `design_prompt`）。

## 本流程命令

```bash
# 参考门禁与清理
python3 scripts/audio_gate.py --short-clip reference.wav
python3 scripts/clean_reference.py source.m4a --start 31.6 --end 46.0 --transcript exact.txt --output NEW_DIR

# 生成（在装有 mlx-audio 的环境中）：逐段生成、门禁、拼接，写 master、逐段记录和 alignment.json
python scripts/voxcpm_voice.py JOB
```

任务配置示例：`"voxcpm": {"voice": "magnetic-narrator", "mode": "combined", "cfg_value": 2.0, "timesteps": 10, "seed": 2026}`；`model_path` 指向已安装模型（也可来自个人目录的已验证参数）。适配器不下载模型。

## 已知限制

- 官方说明：声音克隆仅用于本人或已授权的声音，严禁冒充、诈骗和虚假信息，并建议明确标注 AI 生成内容。
- 信号门禁、ASR 和语速只能发现明显故障，不能代替听感验收。
