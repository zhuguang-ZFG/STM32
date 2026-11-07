# B34：长课收尾拍去同构（ch05 / ch18）

日期：2026-11-07（Asia/Shanghai）。基线为已合并并通过双语 CI 的 `3167d8b`（PR #78，B33）。
合同依据：`audits/video-regen-plan.md` 的反同构邻接规则（相邻两章不得用同一收尾
模板「口诀 / 合上书，三问」）；`BOOK_VIDEO_CLASSIC_SPECS.md` 的旁白与响度合同。

## 状态复核（先证伪两处过期挂账）

`video-regen-plan.md`（2026-11-04）列的开放项多数已完成，逐项实测：

- 29 章长课证据（storyboard / storyboard-rendered / media-report / srt）与
  `final-videos/chNN/*.mp4`：29/29 全存在；media-report 全部 Xiaoxiao 语音，
  无 Huihui 回退残留。
- ch21–28 短片：ffprobe 实测全部 1920×1080，不再是 960×540 legacy。
- 短片收尾拍（`tools/narration.py` CHAPTERS）：29 章尾段标题无相邻重复。
- 剩余反同构缺陷只有长课收尾拍两对：**ch04–ch05** 同用「合上书，三问」，
  **ch17–ch18** 同用「合上书三问」。
- task_verify 复跑：passed 9 / failed 0 / unverified 3，三项 unverified 均为
  `kind: manual`（真板 PC13 特写、NUCLEO-L476RG 电流实测、外部框架工具本体），
  本环境无真板，按合同继续分列记账，不冒充通过。

## 改动（只动两章长课最后一拍）

- `video/ch05/storyboard.json` ch05-s28：`合上书，三问`（recall）→
  `把时基交给波特率`（failure / diagnosis）。旁白把本章已验收的三件事
  （PSC×ARR 分出 1 kHz、CCR 定占空比、输入捕获锁 CNT）收拢，再把同一套
  72 MHz 分频思路交给第 06 章的波特率发生器；fact_source 增加
  `docs/06-串口UART.md#核心原理`（锚点实测存在）。
- `video/ch18/storyboard.json` ch18-s28：`合上书三问` →
  `把铁律带进项目现场`。旁白收拢排错五步与三条铁律，
  把方法论交给第 19 章多模块项目现场；fact_source 增加
  `docs/19-项目实战合集.md#原理与适用范围`（锚点实测存在）。
  purpose/evidence_type 保持 recall 不变：ch16–20 的五类角色计数是
  `test_classic_l5` 冻结合同（recall 必须为 2），首轮 CI（run
  42331186877）踩中该断言后已改回，收尾拍的去同构改标题与旁白即足。
- 两章的 s27 recall 拍保留，五类 purpose（hook/mechanism/failure/experiment/
  recall）在各自分镜中仍齐备。

## 重生成与验证

- 本机装 `wqy-microhei.ttc`（GPL-3 带嵌入例外，与 CI 同一字体），经
  `NARRATED_FONT` 注入，`gen_long_lesson.py 05|18 --speak` 全量重合成
  （edge-tts `zh-CN-XiaoxiaoNeural`，rate −5%，pitch −4Hz，合同声底），
  1080p 30fps 重渲染并重写 `storyboard-rendered.json`、`chNN.srt`、
  `media-report.json`、`contact-sheet.jpg`。
- media-report 两章均为全 True：28 场、五类角色、1080p、30fps、字幕数、
  时长与分镜一致、时长界内、集成响度（−15.8 LUFS）与真峰值（−3.4 / −4.1 dBTP）
  合同、联系表 5 帧实取。成片 ch05 616.9s / ch18 660.1s。
- 反同构邻接扫描：28 对相邻收尾拍，重复 0。
- `test_storyboard_facts` 3 项通过；`tools/check_assets.py` 全部通过
  （29 章视频与字幕合同、5/5 实拍哈希、2014/2014 链接）。
- 结尾帧目视（ch05 @600s、ch18 @645s）：新标题、新旁白字幕、诚实徽章
  「程序生成画面 · 不是实拍」渲染正常。注：两处手绘收尾板的角标
  （ch05 板标 CH 06、ch18 板标 CH 19）为既有资产状态，本批未改 visual_source，
  留给资产批次核对。
- 书稿正文与构建输入零改动，本地 PDF 无需重建。
