# 执行计划

依赖顺序执行；每步带验证点。全程不修改 skill 源码。

## Phase 1：内容与契约（旁白先行）

1. 读 skill 契约文档：references/ 的 story-design、opening-design、production-options（含 options/defaults.json）、quality-gates、style-and-drawing、subtitle-design、motion-catalog、voice-sources；scripts/narration_master.py 全文。
   - 验证：design.json/storyboard 字段清单、build_master 签名、黄金 5 秒规则落地方式成竹在胸。
2. 写口播稿 `jobs/ai4fw/inputs/narration-script.md`（60–90s，~200 字，四框架+选型+钩子；事实对照 source-snapshot；星数口径）。
   - 验证：每 beat ≤100 字；总字数对应 60–90s（云扬 ~5.2 字/s）。
3. 写 `jobs/ai4fw/tools/edge_runner.py`（edge-tts→wav 48k→master+alignment，官方格式）。
   - 验证：产出的 master.wav 时长符合预期；audio_gate/verify 通过（或 fallback 走 build_master 回调路径）。

## Phase 2：视觉

4. 画插画 6–8 幅（SVG→PNG 1920²，涂鸦信息图规范）+ 封面。
   - 验证：lineart/image gate 自检；art-direction 记录齐（sha256/brief/prompt/evidence）。
5. 组装 design.json（opening_hook 六法选一）+ job.json 9:16 + storyboard。
   - 验证：`doctor jobs/ai4fw` → ready（fonts 显式 simkai/msyh、inputs 全就位）。

## Phase 3：主片（9:16）

6. `build` → `render`（先低清/局部 preview 迭代）→ `verify` → `finalize`。
   - 验证：全门绿；黄金 5 秒实测；时长 60–90s。

## Phase 4：B站版（16:9）

7. `jobs/ai4fw-bili/`：复用旁白产物，storyboard 横向重排，走同链 build→finalize。
   - 验证：同门绿；两版本内容一致（对白逐句相同）。

## Phase 5：平台交付

8. 封面 ×4（3:4 抖音/小红书、9:16 视频号、16:9 B站）——竖版封面图注意 204px 可读性。
9. 平台文件落 `out/ai4fw/`（douyin.mp4/wx.mp4/xhs.mp4/bili.mp4）+ 码率适配（视频号 ≤10Mbps 实测）。
10. `publish/copy-ai4fw.md`：四平台标题/简介/话题，逐项对限制（抖音 ≤30 字、小红书 ≤20/1000、B站纯文本）。
    - 验证：ffmpeg 实测各交付文件规格；文案逐条数限制。

## Phase 6：收尾

11. 汇总证据（门禁输出、时长/码率实测、哈希）向用户交付；发布决策留给用户（I_HAVE_USER_OK 闸门不在本任务内）。

## 回退点

- runner 与官方管线不合 → 改走 build_master synthesize 回调（仍官方）。
- 楷体缺字 → 换词不动字体。
- 16:9 重排工作量超预期 → 先交 9:16 四平台（B站同竖版兜底），横版顺延——须用户点头。
