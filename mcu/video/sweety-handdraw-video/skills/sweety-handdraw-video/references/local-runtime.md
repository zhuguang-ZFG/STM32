# 声音与本机依赖

运行需要 Python 3.9+、Pillow、NumPy、SciPy、requests、fontTools、ffmpeg/ffprobe，`scripts/setup.sh` 在 macOS 与 Linux 上一次装好（`--check` 只检查）。正文手写字体优先 macOS Hannotate；字幕使用独立的常规中文字体，Linux 经 fontconfig 选用 Noto CJK。构建前 `scripts/fonts.py` 按手写、字幕、水印逐字核对字形，缺字时依次换备用字体，全部缺字则列出缺失字符与已尝试字体并停止。字体回退不能当作手写风格已验收，不把系统商业字体复制进包。

## 配音后端：本地优先，云端可选

`voice_backends.voice_backends_report()`（`python3 scripts/voice_backends.py`）列出本机已安装的能力，不安装、不下载、不读取密钥内容：

| 后端 | 条件 | 命令 |
|---|---|---|
| 本地 VoxCPM2（默认） | 装有 `mlx-audio` 的 Python（`HANDDRAW_MLX_PYTHON`）与已安装模型（`voxcpm.model_path` 或 `HANDDRAW_VOXCPM_MODEL`） | `python scripts/voxcpm_voice.py JOB` |
| 本地 VoiceStudio | 用户自行启动的 `http://127.0.0.1:3900`；适配器不启动应用、不改引擎 | `python3 scripts/voice_studio.py JOB [--transcribe]` |
| 火山引擎豆包语音合成 2.0（可选） | 用户自己的 `VOLC_TTS_API_KEY`，或 `VOLC_TTS_APP_ID` + `VOLC_TTS_ACCESS_KEY` | `python3 scripts/volcengine_tts.py JOB` |
| Gemini TTS（可选） | 用户自己的 `GEMINI_API_KEY` | `python3 scripts/gemini_tts.py JOB` |

云端只在用户配置了自己的密钥并明确选择时使用，永远不是默认，也不在本地失败时自动改用。云端输出不能作为克隆参考。两个云端适配器按官方文档实现、用模拟 HTTP 测试，本仓库未做真实调用。火山引擎：`volcengine:{"speaker":"zh_male_cixingjieshuonan_uranus_bigtts","resource_id":"seed-tts-2.0","speech_rate":0}`，返回的字级时间戳直接用于字幕；Gemini：`gemini_tts:{"model":"gemini-3.8-flash-tts","voice":"Iapetus","style":"沉稳的纪录片旁白"}`，没有时间戳，字幕由本地 ASR 或停顿切分。

所有后端都按[语义段落](continuous-narration.md)逐段生成、门禁、重试并拼接母带，写 `alignment.json`；按文本、参数、模型、参考哈希缓存，未追踪的现有音频不覆盖。VoiceStudio 适配器显式发送 Qwen3-TTS 官方采样参数（temperature 0.9、top_p 1.0、top_k 50、repetition_penalty 1.05），但 VoiceStudio 0.5.x 的 `/generate` 没有这些字段，实际使用模型默认值；`max_chunk_chars=0`，分段由本流程完成。

辅助工具（找到才用）：HTDemucs（`HANDDRAW_DEMUCS_PYTHON`、`HANDDRAW_HTDEMUCS_WEIGHTS`）、DeepFilterNet3（`HANDDRAW_DFN_MODEL`，默认 `~/.local/share/sweety-handdraw-video/voices/models/DeepFilterNet3`）、Whisper（`HANDDRAW_ASR_MODEL`，默认 HF 缓存中的 `mlx-community/whisper-large-v3-turbo`）、强制对齐模型（`HANDDRAW_ALIGNER_MODEL`）。子进程以离线模式运行，不会隐式下载。

## 声音目录

`assets/voices/catalog.json`：

| 名称 | ID | 参考 |
|---|---|---|
| 逼真男声 | `realistic-man` | 《那条死于愤怒的蛇》原始录音经清理后的参考，只在本机个人声音库 |
| 逼真女声 | `bilibili-outro` | 《快乐囚禁你的方式》原片提取人声，只在本机个人声音库 |
| 磁性解说男声 | `magnetic-narrator` | VoxCPM2 文字描述设计的合成声音，可分发 |
| 儒雅青年 | `scholarly-young-man` | 同上 |
| 温柔知性女声 | `gentle-intellectual-woman` | 同上 |
| 悬疑故事解说 | `suspense-storyteller` | 同上 |

公共默认是可分发的合成声音；个人目录的 `default` 可改为本机主力音色。来源与授权见[声音来源](voice-sources.md)。两款逼真声音在公共包里只有成片节选试听，没有导入原始参考时不能生成。

## 参考导入与自定义声音

参考在导入和每次使用时都要通过：未改动（哈希）、`audio_gate` 短片段门禁（嗡声/单频、停顿深度、直流、削波）、逐字稿覆盖整段（语速 2.5–8 字/秒）。不通过时先清理：

```bash
python3 scripts/clean_reference.py source.wav --start 31.6 --end 46.0 --transcript exact.txt --output NEW_DIR
python3 scripts/import_voice.py JOB --id realistic-man --name "逼真男声" --audio NEW_DIR/reference.wav --transcript NEW_DIR/transcript.txt --kind source_recording
python3 scripts/import_voice.py JOB --id my-voice --name "我的声音" --audio me.wav --transcript me.txt --consent self
```

`clean_reference.py` 可选 HTDemucs 人声分离与 DeepFilterNet3 降噪，裁成 8–15 秒、句末结束、尾部 0.5 秒以上静音，峰值 −3 dBFS；原文件不改动，新目录已存在参考时拒绝覆盖，`clean-record.json` 记录源哈希、使用区间、各步模型权重哈希、门禁前后数值和 ASR 覆盖。请求的起止点附近找不到句子边界时报错，不在句中切。

自定义声音不限数量：个人目录 `~/.local/share/sweety-handdraw-video/voices/catalog.json` 或任务 `options/local-voices.json` 中，新 ID 的条目须有 `name`、`reference_audio`、`reference_text` 与 `"consent": "self"`（本人声音）或 `"authorized"`（说话人授权）。没有同意声明的条目会被忽略。不要克隆他人、主播或平台音色。包内预设的名称、描述和原片要求不能被本地目录改写。

## 本机个人声音库

个人目录与可分发的 Skill 包分开，记录实际参考、逐字稿、哈希、清理过程、试听样本和验收状态；未经听感验收的条目标 `pending_listening`，暂用声音不得记为通过。修改前先备份目录与原文件（本次备份在 `backups/2026-10-14-before-v1.3/`），新文件与原文件并存，不删除原始录音。`enhancement_model_path` 可指向已安装的 DeepFilterNet3，对生成结果做保长度的 48 kHz 后处理，权重哈希纳入缓存。

## 原片音色验收

先检查原片参考本身是否混有配乐、风声、底噪。清理会伤及音色，不能只凭门禁或 ASR 判定合格。指定原片音色先做同文对照与另一段正文短样，再做完整旁白；按相近响度比较原片、清理后原声、合成短样与长段开头/中间/结尾。未实际听音或没有用户反馈时，状态保持待听感验收，不能宣称音色一致或绝对无杂音。

## 六款手、仅画笔与广告

`assets/hands/catalog.json` 提供六款手臂与 `pen-only`，全部有美术与隐私记录。`pen-only` 由 `assets/hands/prompts/pen-only.py` 从 `navy.png` 去掉手指得到：同一支笔、同一握笔角度与笔尖坐标，笔杆广告位置也相同；渲染器给 `kind:pen` 加以笔尖为接触点的投影（笔杆越远离笔尖，影子偏得越远）。手臂按笔尖到手腕距离校准尺度，让最上方落笔时前臂底边仍在画外。`pen-only` 的 `kind:pen` 不执行前臂检查，但笔尖仍须对齐。

`hand.pen_text` 最多16个字符，只在实测笔杆段排版。保留原文、不自动缩写；上限不等于细笔杆上一定可读，须在正常尺寸检查。`pen_text_color` 可覆盖预设颜色。自定义手提供 `source/nib/wrist`，广告再提供 `label_segment/label_height`；自定义仅画笔提供 `kind:pen/source/nib/scale`。所有缩放必须为正的有限数。

## 图像隐私

执行 `python3 scripts/clean_image.py image.png --audit privacy.json`：纯 Python 重写 PNG / JPEG / WebP 容器，只保留图像数据块（像素不重新编码，替换前核对像素一致），去除 EXIF、GPS、XMP、IPTC、ICC、文本注释与 C2PA 等字段，清除 macOS 来源扩展属性与 Linux `user.*` 属性，不写入模拟相机字段。不需要 Bun 或 ExifTool；结果与旧流程（随包 `main.ts` + `exiftool -all=`）逐字节一致，审计格式不变。其他格式保持原样并报错，提示先转为 PNG、JPEG 或 WebP。
