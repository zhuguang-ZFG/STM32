# 小红书：视频系列 17 条批量上传（文案派生 + 逐集发布）

## Goal

把视频系列还缺的 17 条竖版成片传上小红书、逐条发布并挂进合集「通往单片机之路」——
对齐 B站/抖音的系列覆盖（小红书此前只有 F5、S5 两条）。用户 2026-10-17 在对话里选「今晚 17 条连跑全发」。

## 前置（本轮之前已完成）

- 合集「通往单片机之路」已建成（见 `10-17-xhs-series-collection`）。
- `xhs-step.mjs` 已具备 `open / upload / fill / topics / coverset / coverapply / attach / publish --go`；
  其中 `publish` 的点击位置用 **CDP `DOM.getDocument(pierce:true)` + `DOM.getBoxModel`** 量内部「发布」那半颗
  （宿主 `<xhs-publish-btn>` 的正中落在「暂存离开/发布」两颗之间的空隙，点中心什么都不会发生——实测踩过）。
- `video/publish/xhs-batch.sh`：逐集七步表单 + 挂集 + 发布，任一步非零即停。

## 文案派生（不新编一个字；用户已看过标题表）

- 标题：各集抖音候选里**最短的 ≤20 字**那条；`f0-why-rtos`、`p4-iram` 两条人工指定（p4 三条候选全超 20）。
- 正文：抖音 `intro` 去掉含 站内/全篇/全文/免费/仓库/通往单片机之路 的句子，尾巴接「复现：<repro>」。
- 置顶：抖音 `pinned` 同规则删句。话题：抖音 `tags` 前三个。合集：「通往单片机之路」。
- 生成器 `.temp/xhs-blocks-gen.mjs`：按花括号配平定位 `publish` 对象插入（根键顺序不定，别按文件尾锚），
  写回后 JSON.parse + 深比对「除新块外一切不变」，不满足不落盘。
- 全量留档 `.temp/xhs-run/xhs-blocks-17.md`。

## Requirements

- 逐集闸门 `I_HAVE_USER_OK=<ep>`（内容=用户原话 + 该集 id），`publish --go` 才点。
- 任一步失败即停，不跳步、不把「看起来成功」当成功；失败集与首个失败点原样留在日志里。
- 每集留下：`<ep>-filled/-topics/-attach/-published.png`；发布判据 URL `?source=&published=true`。
- 批后统一核**笔记管理「已发布」**（权威信号）——检索框会偶发空结果、虚拟列表只渲染可视区约 10 条，
  **实际采用整列对账**（`Ctrl+Minus` 缩小 + `PageDown`/滚轮/scrollTop 三件套收全卡片）；抽 3 条核合集归属（编辑页回读那一行）。

## Acceptance Criteria

- [x] 17 条全部发布：笔记管理「已发布」整列 43 张卡片收齐、17 条新标题逐条在列（2026-10-17 22:22–22:49）
- [x] 抽样编辑页回读那一行 =「通往单片机之路」：`f0-why-rtos`、`c3-volatile`、`f6-timers` **3/3 全中**（`.temp/xhs-run/xhs-sample-*.png`）
- [x] 失败集与原因：零失败（17/17；批跑 1608s，日志 16 个「完成」标记 + 首条单跑）
- [x] 台账更新：`xhs-plan.md` 批量一节（含结果与两个核对坑）、`.temp/xhs-run/xhs-series-collection-20261017.txt` 收口、journal 见当天条目

## 硬约束

- 不动 F5/S5；不动章节合集「STM32 零基础自学」；不改已发布成片与 `video/out/`；不碰其它平台。
- 发布点击必须走 `findPublishButtonBox`（CDP 穿透），不点宿主中心、不用 `_onPublish` 硬触发。
