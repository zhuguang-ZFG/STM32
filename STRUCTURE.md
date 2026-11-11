# 仓库结构

> English readers: start at [docs/en/README.md](docs/en/README.md). This file is the map of the repository, not a chapter.

读者从 [README.md](README.md) 进来。章节正文在 `docs/`，不要在别的目录再写一份教程。

## 双书与三个根

仓库为 **单仓双书**（subtree 收口）：STM32 知识库与 MCU 姊妹书《通往单片机之路》并存，分域维护、互不覆盖。

| 根/身份 | 含义 | 典型路径 |
| --- | --- | --- |
| Git 仓库根 | 版本控制与根域工作区 | `D:\Users\STM32`（候选收口 worktree：`D:\Users\STM32-mcu-merge-p1`） |
| MCU 项目根 | MCU 子树独立项目上下文（Trellis、脚本、站点/书籍/固件门） | `<Git根>\mcu` |
| 对外站点根 | MCU 站点在 Pages/staging 下的挂载前缀 | `/STM32/mcu/`（旧 `/mcu/` 仅作迁移负例，不得作为新身份） |

依据与证据：[`plans/2026-11-11-mcu-merge/`](plans/2026-11-11-mcu-merge/)。

## 目录各管什么

| 路径 | 作用 | 入口 |
| --- | --- | --- |
| `docs/` | 中文 00–28 章，唯一正文（STM32 书） | [docs/README.md](docs/README.md) |
| `docs/en/` | 英文 00–28 章，以及英文速查表 | [docs/en/README.md](docs/en/README.md) |
| `stm32-book/` | 用 `docs/` 打成离线 HTML / PDF，附录在 `stm32-book/book/` | [stm32-book/README.md](stm32-book/README.md) |
| `examples/` | STM32 书可编译示例。Wokwi 的 `diagram.json` 放在对应示例里 | [examples/README.md](examples/README.md) |
| `labs/` | 真板证据协议，不是另一套示例 | [labs/README.md](labs/README.md) |
| `sim/` | Renode 脚本。和 Wokwi 工程分开 | [sim/README.md](sim/README.md) |
| `cheatsheets/` | 4 份中文速查表。英文在 `docs/en/cheatsheets/` | [cheatsheets/README.md](cheatsheets/README.md) |
| `assets/` | 动画、章首手绘概念图、板卡图、实拍、GIF、讲解视频、公众号二维码 | [assets/README.md](assets/README.md) |
| `assets/video/` | 正片与 AI 续集。早期成片在 `superseded/` | [assets/video/README.md](assets/video/README.md) |
| `tools/` | 生成图片、讲解片、公众号稿的脚本 | [tools/README.md](tools/README.md) |
| `mcu/` | MCU 姊妹书子树（寄存器级 STM32F407 × ESP32-S3、RTOS、VitePress 站点、`mcu-book/`、固件与任务历史）；独立项目根与维护边界 | [mcu/README.md](mcu/README.md)、[mcu/AGENTS.md](mcu/AGENTS.md) |
| `video/` | 长课机器可读分镜、实际字幕、联系表与媒体报告；大 MP4 仍在忽略的 `final-videos/` | [video/README.md](video/README.md) |
| `Makefile` | `assets` / `check` / `book` / `book-pdf` / `book-check` / `stats` | 文件头注释 |
| `.github/workflows/book.yml` | 在 CI 里编 SPL 示例，并构建整书 HTML/PDF | — |

下面两项目录在 [.gitignore](.gitignore) 里，只出现在作者本机，克隆仓库看不到：

| 路径 | 谁写它 |
| --- | --- |
| `wechat-mp/` | `tools/md2mp.py`、`tools/gen_mp_covers.py` |
| `final-videos/` | `tools/gen_tietu.py`；封面源也被 `gen_mp_covers.py` 读取 |

## 不要混用的几条边界

- **双书分域**：STM32 书只改根域（`docs/`、`stm32-book/`、根 `examples/` 等）；MCU 书只改 `mcu/`（`mcu/docs/`、`mcu/code/`、`mcu/mcu-book/` 等）。同名文件不覆盖式合并，跨书引用用交叉链接；`mcu/README.md` 的内容边界与 `mcu/AGENTS.md` 不被根说明替换。
- 改章节：只改 `docs/`（以及对应的 `docs/en/`）。整书通过 `stm32-book/manifest.json` 引用这些文件。
- `examples/` 要能编译。`labs/` 记录一次真板实验怎样才算完成，里面没有固件工程。
- MCU 工作流/脚本在 MCU 项目根 `mcu/` 执行；Trellis 任务与 spec 以 `mcu/.trellis/` 为准。历史任务记录与状态不得因路径迁移被自动改写为通过（见合并计划 AC6）。
- 6 个教学 GIF 由 `tools/gen_gifs.py` 用标准库生成，文字是 ASCII。`assets/gif/*-zh.gif` 由 `tools/svg2gif.py` 从 SVG 采样，给公众号用，已经提交进 git。
- 讲解正片由 `tools/narration.py` + `tools/gen_narrated.py` 生成，文件名是 `ch{章号}-{slug}`。AI 续集把 `NARRATED_MODULE=narration_ai`，文件名是 `chs{集号}-{slug}`。`chai01-ai-gpio` 是续集第一集的早期成片，在 `assets/video/superseded/`。
- 长课源按 SPECS 迁到 `video/chNN/storyboard.json`，由 `tools/storyboards.py` + `tools/gen_long_lesson.py` 生成。`video/` 只保留可审查的小文件，MP4 留在 `final-videos/`。当前已迁移 ch03，其余章节不能用旧长片冒充可复现。
- 对外讲章节范围时用 **00–28，共 29 章**。`tools/gen_mp_covers.py` 仍只裁 ch00–ch25，因为封面源在不入库的 `final-videos/`。
- 中文速查表留在仓库根的 `cheatsheets/`。英文速查表留在 `docs/en/cheatsheets/`。两处都已经有链接，不合并目录。
- 中文章节目录只改 [docs/README.md](docs/README.md)。英文只改 [docs/en/contents.md](docs/en/contents.md)。首页只保留分段入口。
- 公众号二维码在 `assets/wechat/`。板卡图目录只放 SVG。
- 合并收口不跳过或调低 STM32/MCU 既有验证门；发布（P5）需明确指令与 AC1–AC8 证据。

## 这一轮改了什么

- `wechat-mp-qr.png` 从 `assets/boards/` 移到 `assets/wechat/`。全仓库只有首页引用这张图，链接已改。板卡目录只留 SVG。
- 首页和英文首页不再各维护一份 29 行关键词表。中文以 `docs/README.md` 为准，英文以 `docs/en/contents.md` 为准。两个首页只留三段入口。
- `assets/README.md` 里 `toolchain-flow.svg` 的关联章节从 01 改成 00，与第 0 章正文一致。

## 后续

1. 这 5 张 SVG 还没有 `*-zh.gif`：`i2c-transaction`、`l4-stop2-evidence`、`network-packet-journey`、`rtos-system-layers`、`g0-boot-swd`。`svg2gif.py` 依赖本机 Chrome，这里不生成。
2. `tools/gen_mp_covers.py` 仍只裁 ch00–ch25。封面源在不入库的 `final-videos/`，仓库里没有 ch26–ch28 的封面，所以这次不把循环改成 29。
