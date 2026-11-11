# S5 v2 试点报告（Task 11）

日期：2026-10-22
集数：`s5-systick`《SysTick：是谁在给 RTOS 数那一毫秒？》
状态：母版、封面、发布包已产出；用户看片门（Step 12）待点头。

## 1. 用户选择（Step 10）

| 项 | 选择 | 落盘 |
|---|---|---|
| 封面版本 | A 对比版（`vs`） | `episode.json` `cover.variant: "vs"` |
| 背景音 | `lab-ambient` | 构建默认，未切 `ambient-pad` |
| 语速 | `+2%` | `episode.json` `rate: "+2%"` |
| 音色 | 云扬 `zh-CN-YunyangNeural` | `episode.json` `voice` |

## 2. 成片

| 平台 | 路径 | 时长 | 帧数 | fps | 音画漂移 |
|---|---|---|---|---|---|
| B站横版 | `video/out/s5-systick/bilibili.mp4` | 653.466667s（10:53） | 19604 | 30 | 0s |
| 抖音竖版 | `video/out/s5-systick/douyin.mp4` | 60.966667s（01:00） | 1829 | 30 | 0s |

时长由 `ffprobe` 读取；漂移 = |容器时长 − 帧数/fps|，两版均为 0，低于 0.15s 上限。

## 3. 音频

| 项 | B站 | 抖音 |
|---|---|---|
| 响度（ebur128 实测） | -14.8 LUFS | -14.8 LUFS |
| 目标 | -14 ±1 LUFS | -14 ±1 LUFS |
| 第一遍测量 | -25.5 LUFS | -25.3 LUFS |
| 校正方式 | 两遍 loudnorm + 线性校正 | 同左 |
| SFX 事件 | 266 条 | 24 条 |
| BGM | `lab-ambient`，旁白侧链 ducking | 同左 |

## 4. 产能基线

| 项 | B站 | 抖音 |
|---|---|---|
| 整集构建用时 | 664s（11m04s） | 74s（1m14s） |
| 逐帧渲染用时 | 572.9s，34.2 fps | 63.6s，28.7 fps |
| 截图/复用 | 2764 张 / 复用 16840 帧（省 86%） | 274 张 / 复用 1555 帧（省 85%） |
| 自动抽帧 | 13 张 | 12 张 |
| 节拍 | 266 拍，最长静止 4.2s | 24 拍，最长静止 4.1s |

构建日志：`.temp/v2-pilot/s5-build.log`。

## 5. 审计

- `npm run video:check -- s5-systick`：B站 25 场、抖音 10 场，越界/裁切/压字幕/版式相叠/字号不可读/顶穿容器/标题孤字/进度杠重复均为 0。
- `npm run video:numbers -- s5-systick`：89 个数字都有依据，未命中 0。
- `npm run video:lint -- s5-systick`：通过（25 + 10 场）。
- 独立复核：`video/research/s5-systick-review-r2.md` → 整改 → `s5-systick-review-r3.md`，Verdict **APPROVED**，2 条 Low 为证据底稿措辞，已在 r3 后修正（`0xd29` 的发行标注、`3369` 的 dec 列措辞）。

## 6. 抽帧检查

- 构建自动抽帧：`video/out/s5-systick/{bilibili,douyin}/stills/`。
- 每场 75% 处抽帧（绕过入场/揭示暗帧）：`.temp/v2-pilot/frames/{bilibili,douyin}/`，contact sheet 为同目录 `bilibili-sheet.png`、`douyin-sheet.png`。
- 重点复核：hook 首帧/揭示后、6 个 section 首帧、code 场行号与高亮、code-09 交叉段 3361/3369/d29、code-14 只剩 S4 链路、card-07 未取证声明、cta、四尺寸封面与 336px 人检表。
- 四尺寸封面：`video/out/s5-systick/{bilibili,douyin,zhihu,xiaohongshu}-cover.png`；336px 人检表 `cover-contact-336.png`。

## 7. 已知边界

- 板上逻辑分析仪百分数、真实中断抖动仍不上屏（`card-07` 明示）。
- 抖音 code 场最小字号 26.9px（1080×1920），在手机全屏可读但偏小；后续 wave 可视情况用 `set` 缩代码行数。
- `S9` 词表键已无命中文本，属无害残留；`14` exception 的旧措辞不影响上屏。

## 8. 用户结论

2026-10-22 Step 12 看片门：用户明确「通过，进入 Wave A」。本报告作为 Wave A–C 的产能与阈值基线：横版 -14.8 LUFS、竖版 -14.8 LUFS、drift 0、check 0 问题、numbers 0 未命中、横版 664s/竖版 74s 构建。
