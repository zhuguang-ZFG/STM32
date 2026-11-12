# 技术设计：四大框架手绘口播成片

## 1. 布局

```
video/
  sweety-handdraw-video/     # skill 克隆（只读，零修改）
  pydeps/                    # pip --target 隔离依赖（Pillow 11.3.0 等）
  jobs/ai4fw/                # 主 job：9:16 1080×1920（抖音/视频号/小红书）
  jobs/ai4fw-bili/           # B站 job：16:9 1920×1080（storyboard 重排）
  publish/copy-ai4fw.md      # 四平台文案清单
  out/ai4fw/                 # 平台交付文件（mp4/封面）
```

运行入口统一：`PYTHONPATH=D:/Users/STM32/mcu/video/pydeps python <skill>/scripts/handdraw_video.py <cmd> <job>`（harness 只认裸 `python`，钉在 scoop 3.13 基座；基座 edge-tts/ffmpeg 仍可用，pydeps 遮蔽 PIL/numpy/scipy 版本）。

## 2. 内容结构（60–90s，~200 字旁白）

钩子（黄金 5 秒：「不用视频大模型，代码直接出片」）→ 四框架各一节（每节 1–2 beat：定位一句话 + 独有证据）→ 收尾选型表（要现成风格 lemo / 要讲解语法 huashu-art / 要记谱合成 huashu-motion / 要手绘口播 sweety）→ 清单钩子（369 仓库清单在公众号/评论区）。

每 beat ≤100 字（skill 旁白分段契约），beat 间停顿按官方档（0.20/0.30/0.40/0.60s）。

## 3. 语音链（Windows 无 VoiceStudio/VoxCPM 的注入路径）

自写 runner `jobs/ai4fw/tools/edge_runner.py`：
1. 从 job.json 读旁白 beats → 逐 beat 调 edge-tts（云扬，`boundary='WordBoundary'`，mp3 24kHz）
2. ffmpeg 转 wav 48k mono → 套用官方尾修剪/停顿规则（对齐 narration_master 产物契约：`outputs/narration/master.wav` + `outputs/narration/alignment.json`，字段格式抄 skill 的 narration_master.py）
3. audio_gate 实测响度/静音门通过

备选（若 runner 与 verify 不兼容）：直接调 `narration_master.build_master(root, manifest, synthesize=…)`，synthesize 回调内嵌 edge-tts——官方管线原生路径，优先尝试。

## 4. 插画链（插画提供方=本会话）

- 风格：涂鸦信息图（白底、黑墨线 #1a1a1a 统一笔宽、扁平色块、小豆人角色）——匹配工具盘点内容与「代码出片」气质
- 每节 1 幅 + 封面 1 幅 + 选型表 1 幅，共 6–8 幅 1920×1920 白底 PNG（SVG 手写 → 渲染 PNG）
- 自检过 lineart_gate 精神：闭合区域、连续墨线、文字不穿线；图内文字极简（真文字走 job text action，用楷体）
- 美术记录：design/art-direction.json 每图 brief_file/prompt_file/sha256/status/evidence 全量填写（自绘 = 方法记自绘，脚本只验结构/哈希/像素）
- 隐私：PNG 无 EXIF，仍按契约跑 clean_image

## 5. 双画幅策略

9:16 主 job 完成后，B站 16:9 为**独立 job**：同一旁白 master/alignment 复用（软链或复制），storyboard 重排（横向布局：左右分区而非上下堆叠），不走裁切。skill 的 aspect_ratio.py 预设 16:9 = 1920×1080。

## 6. 平台交付

- 抖音/视频号/小红书 ← 竖版母版；B站 ← 横版母版
- 视频号：render 后实测码率，超 10Mbps 则 ffmpeg 重编码（CRF 上调）
- 封面：竖版 3:4（抖音/小红书）、9:16（视频号另做一版，204px 展示宽下主体可读——见 wx-plan.md §6）、16:9（B站 16:10 实际展示）
- 文案：publish/copy-ai4fw.md 按四平台限制分节

## 7. 已实证的适配事实（写死，防回归）

- harness 拒绝一切路径形式首 token（127）——只用裸命令名；MSYS `/d/…` 路径不进 Windows 程序 argv——一律 `D:/…`
- `python` 钉死 scoop 基座；`source venv/Scripts/activate` 无效 → venv 方案废弃，`pip --target` + PYTHONPATH 遮蔽为准
- fonts.py 无 Windows 分支 → job.json 必须显式 `font.path`（手写 `C:/Windows/Fonts/simkai.ttf`、字幕 `C:/Windows/Fonts/msyh.ttc` index 0），否则 fontconfig 空链直接报错
- edge-tts 7.3.1：`Communicate(..., boundary='WordBoundary')` 才有逐字时间戳（默认 SentenceBoundary 为空）
- doctor 的 missing_inputs 会查 cover.source、旁白源、插画 action sources、hand.source——文件必须先就位再跑 doctor

## 8. 风险与对策

| 风险 | 对策 |
|---|---|
| build_master 回调路径与官方契约偏差 | 先读 narration_master.py 全文再写 runner；fallback 到手工对齐官方产物格式 |
| 楷体缺个别生僻字 | check_coverage 报缺字清单 → 换词（不动字体）；雅黑兜底字幕 |
| render 超时/长任务 | bash 显式 timeout 0 + async；单命令单次跑 |
| skill 门禁在自绘图上误报 | 按 gate 报告修 SVG（闭合/墨线），不放宽门禁 |
