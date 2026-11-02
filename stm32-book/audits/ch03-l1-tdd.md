# ch03 L1 TDD 证据与开放门

来源：[`BOOK_VIDEO_CLASSIC_SPECS.md`](../BOOK_VIDEO_CLASSIC_SPECS.md) 的 L1 薄切片。本文只记录实际执行结果，不把计划当证据。

## 用户旅程

1. 初学者看到“写 1 灯灭、写 0 灯亮”时，能把程序写值、PC13 电平和共阳电流路径连起来。
2. 初学者能区分推挽/开漏、HAL/BSRR/ODR、AFIO/AFR、FT 条件和 LCKR 的完整写读序列。
3. 初学者能按专用图和实验证据识别错误接线、抖动、轮询漏检，而不是只看文字卡。
4. 读者在桌面、375px 窄屏和 PDF 中都能读懂图；视频观众能得到同一份旁白、字幕和可复现分镜。

## RED → GREEN 记录

| 行为 | RED（旧行为） | 实现后 GREEN |
| --- | --- | --- |
| 双态图与分镜专属视觉 | 2 FAIL + 1 ERROR：双态标签缺失、专属图被默认图覆盖、无 PNG 加载入口 | 3/3 通过；随后扩到 6/6 |
| stack 控制/电流边界 | HTML 与双语引用不存在，2 FAIL | 5/5 通过；HTML/2000×1200 明暗 PNG 实际生成并目检 |
| 短片学习顺序 | 首段没有双态图和 stack 图，1 FAIL | 6/6 通过；10 段中 8 段有专属视觉 |
| 长片 schema 与关键帧 | 装载器和 28 场 schema 不存在，2 ERROR | 8/8 通过；28 场、五类学习角色、时长边界通过 |
| 独立技术审查 | BSRR 亮灭、LCKR 两次读、s02/s13/s25 机制和 11 个视觉映射共 14 个失败点 | 14/14 通过；11 张新证据 SVG 联系表与重点图目检 |
| 技术字幕换行 | `PC1/3`、`50 M/Hz`、`HAL_Del/ay`，句号独立成行 | token-aware 换行通过，短片/长片排版检查通过 |
| 窄屏与链接图 | class/tabindex 不存在，375px 图缩到约 305px | `<figure class="wide-figure" tabindex="0">` 进入整书；实测图 720px、容器 730px、根页 375px |
| 全量回归 | 初始基线 146 tests OK | 当前 160 tests OK（含新增 L1） |
| 短片实际媒体 | 旧片 960×540、8 fps、文字卡为主、-19.6 LUFS | 1080p/30fps、173.510726 s、10 字幕、-16.1 LUFS、-1.6 dBTP；`check_assets` 全通过 |

关键验证命令：

```bash
python -m unittest discover stm32-book/tests -p test_classic_l1.py -v
python -m unittest discover stm32-book/tests
python tools/check_assets.py
python tools/slop_lint.py
python stm32-book/build_html.py --check
python stm32-book/build_html.py --lang en --check
python tools/gen_long_lesson.py --check 03
```

## 实际产物

- ch03 双态手绘图、stack HTML/明暗 PNG、11 张 `classic-03-*.svg` 证据图。
- 中英文章节与旁白同步；LCKR 代码和图均包含第一次完成读与第二次确认读。
- `assets/video/ch03-gpio.{mp4,srt,png}`：1080p30、真实抽帧、字幕与旁白一致。
- `video/ch03/storyboard.json`：28 场、五类学习角色、视觉/事实来源、先备关系与记忆锚点。

## 新增/修改测试的审查说明

- 新增 `stm32-book/tests/test_classic_l1.py`：消费者可见的双态、专属视觉、stack、storyboard、机制、视觉映射、字幕和窄屏契约。
- 修改 `test_sample_svg_c.py`：只按当前实际 SVG 文本/样式更新冻结值，新增 11 张图，资产数从 161 增至 172；没有删除检查或放宽颜色、线宽、圆角、页脚和禁用元素。
- 修改 `test_book_audit.py` / `test_advanced_visuals.py`：ch03 视觉锚点从 4 增至 5。
- 修改 `test_build.py`：按 LF 口径同步 CSS 哈希。
- **这些新增和变更请求代码审查。`task_verify` 返回 `unverified（project-or-git-baseline-unavailable）`，不记为通过。**

## 长片验证（已完成）

- `final-videos/ch03/ch03-bilibili-safe.mp4`：676.410635 秒、1920×1080、30/1 fps、28 条字幕，H.264 + AAC。
- `video/ch03/media-report.json`：-16.0 LUFS、-2.1 dBTP；28 场、五类角色、时长匹配、1080p、30fps、字幕数、响度、true peak、联系表全部 `true`。
- `video/ch03/contact-sheet.jpg`：从实际 MP4 抽取 hook / mechanism / failure / experiment / recall 五类场景，中文标题可读。
- 独立复核：MP4 SHA-256 `32eb72f571900e3ef07f295e2c81e414d3ba9c6093d018c3871c78f5e33f57e5`；storyboard SHA-256 `d99f173fd6cd0ec63868c23ca13129bffb23dc1fa4ecd3525ef67d59c74d796f`；`--report 03` 重跑通过。

## PDF 验证（已完成）

- 中文：`stm32-book/dist/stm32-practical-book.pdf`，363 页，13,476,428 B；ch03 双态、stack、LCKR、BSRR 页样目检通过。
- 英文：`stm32-book/dist/stm32-practical-book-en.pdf`，416 页，13,792,377 B；对应页样目检通过。
- 两个 HTML 也来自同一提交并放入 `dist/`。英文 raw PDF 后处理单独完成并复核，未把 0 B 临时文件当成交付。

## 尚未关闭的门

- 历史文泉驿字体的全量旧海报逐像素比对仍为 SKIP，不记为通过；本轮新海报使用明确指定的微软雅黑。
- 全书其余 28 章尚未开始，不属于 L1 证据范围。
