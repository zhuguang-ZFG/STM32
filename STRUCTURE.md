# 仓库结构

> This file is the map of the repository, not a chapter. The English edition (`docs/en/`) was retired with the merged edition; this map is Chinese only.

读者从 [README.md](README.md) 进来。章节正文在 `docs/`，不要在别的目录再写一份教程。

## 合并书稿与三个根

B5 后两书正文已合为《通往单片机之路》：根 `docs/` 与 `book/` 负责现行书稿和交付；`mcu/` 保留来源固件与任务历史，不再有独立书稿站点。

| 根/身份 | 含义 | 典型路径 |
| --- | --- | --- |
| Git 仓库根 | 版本控制与根域工作区 | `D:\Users\STM32`（候选收口 worktree：`D:\Users\STM32-mcu-merge-p1`） |
| MCU 项目根 | 来源固件与 Trellis 历史上下文（非第二套书籍构建根） | `<Git根>\mcu` |
| 对外站点根 | 合并版在 Pages/staging 下的挂载前缀 | `/STM32/`；其下旧 `/mcu/` 路径为兼容跳转存根 |

现行依据与证据：[`plans/2026-11-12-merged-book/`](plans/2026-11-12-merged-book/)；`plans/2026-11-11-mcu-merge/` 保留早期 subtree 规划。

## 目录各管什么

| 路径 | 作用 | 入口 |
| --- | --- | --- |
| `docs/` | 47 章书稿（`onramp/` + `v0-foundations/` … `v7-delivery/`）+ 附录 A–F，唯一正文 | [docs/README.md](docs/README.md) |
| `docs/public/` | 合并版站点资产：`anim/`（113 SVG + 5 GIF）、`figures/`（123）、`arch/`（28）、`images/`（243 PNG + 5 子目录）、`scenes/`（5 个交互场景 + `stick.js` 运行时）。正文里的 `/anim/…` 等绝对路径都落在这里 | `book/build_html.py` |
| `docs/en/` | 已随合并版下线，未随 47 章重建（英文覆盖停在合并前的 00–28） | — |
| `book/` | 整书构建包：`checks.py` / `contracts.py` / `build_html.py` / `build_epub.py` / `build_print_edition.py` | [构建指南](book/README.md) |
| `stm32-book/` | B5 已退役；本地残留/忽略产物不是现行构建入口 | — |
| `examples/` | STM32 书可编译示例。Wokwi 的 `diagram.json` 放在对应示例里 | [examples/README.md](examples/README.md) |
| `labs/` | 真板证据协议，不是另一套示例 | [labs/README.md](labs/README.md) |
| `sim/` | Renode 脚本。和 Wokwi 工程分开 | [sim/README.md](sim/README.md) |
| `cheatsheets/` | 4 份中文速查表（英文译文随 `docs/en/` 下线，未重建） | [cheatsheets/README.md](cheatsheets/README.md) |
| `assets/` | 合并前的素材库（动画 68、手绘概念图 80、板卡与引脚图 10、实拍 5、GIF 48），供公众号与讲解片复用；**正文不读这里**，站点资产在 `docs/public/` | [assets/README.md](assets/README.md) |
| `assets/video/` | 正片与 AI 续集。早期成片在 `superseded/` | [assets/video/README.md](assets/video/README.md) |
| `tools/` | 生成图片、讲解片、公众号稿的脚本 | [tools/README.md](tools/README.md) |
| `mcu/` | MCU 来源子树：保留 `code/` 固件、任务历史与仓库元信息；旧文档、VitePress 与 `mcu-book/` 已合并退役 | [mcu/README.md](mcu/README.md)、[mcu/AGENTS.md](mcu/AGENTS.md) |
| `video/` | 长课机器可读分镜、实际字幕、联系表与媒体报告；大 MP4 仍在忽略的 `final-videos/` | [video/README.md](video/README.md) |
| `Makefile` | `assets` / `check` / `book` / `book-pdf` / `book-check` / `stats` | 文件头注释 |
| `.github/workflows/book.yml` | 合并书稿门与构建；本次本地结果不能替代远程 CI 证据 | — |

下面两项目录在 [.gitignore](.gitignore) 里，只出现在作者本机，克隆仓库看不到：

| 路径 | 谁写它 |
| --- | --- |
| `wechat-mp/` | `tools/md2mp.py`、`tools/gen_mp_covers.py` |
| `final-videos/` | `tools/gen_tietu.py`；封面源也被 `gen_mp_covers.py` 读取 |

## 不要混用的几条边界

- **内容与固件分域**：现行合并书稿改根域 `docs/`，构建改 `book/`；根 `examples/` 与 `mcu/code/` 按各工程边界维护。`mcu/.trellis/` 的历史状态不因迁移自动改为通过；不要恢复已退役的旧书稿树。
- 改章节：只改 `docs/`。目录数据 `docs/manifest.json` 由 `python -m book.manifest --write` 从 `book/data/toc.tsv` 生成；`book/data/mapping.tsv` 是旧章到新章的映射，`book.mapping --write` 只写 `plans/2026-11-12-merged-book/mapping.json`。
- `examples/` 要能编译。`labs/` 记录一次真板实验怎样才算完成，里面没有固件工程。
- 固件命令按各工程 README 的工作目录执行；根书稿门在 Git 根执行，Trellis 历史上下文以 `mcu/.trellis/` 为准。历史任务记录与状态不得因路径迁移被自动改写为通过（见合并计划 AC6）。
- 6 个教学 GIF 由 `tools/gen_gifs.py` 用标准库生成，文字是 ASCII。`assets/gif/*-zh.gif` 由 `tools/svg2gif.py` 从 SVG 采样，给公众号用，已经提交进 git。
- 讲解正片由 `tools/narration.py` + `tools/gen_narrated.py` 生成，文件名是 `ch{章号}-{slug}`。AI 续集把 `NARRATED_MODULE=narration_ai`，文件名是 `chs{集号}-{slug}`。`chai01-ai-gpio` 是续集第一集的早期成片，在 `assets/video/superseded/`。
- 长课源按 SPECS 迁到 `video/chNN/storyboard.json`，由 `tools/storyboards.py` + `tools/gen_long_lesson.py` 生成。`video/` 只保留可审查的小文件，MP4 留在 `final-videos/`。当前已迁移 ch03，其余章节不能用旧长片冒充可复现。
- 对外讲章节范围时用 **47 章（上手卷 ch00 + 卷 0–7 的 ch01–46）+ 6 附录**。`tools/gen_mp_covers.py` 仍只裁 ch00–ch25，因为封面源在不入库的 `final-videos/`。
- 中文速查表留在仓库根的 `cheatsheets/`（英文速查表随 `docs/en/` 一起下线，未重建），不合并目录。
- 中文章节目录只改 [docs/README.md](docs/README.md)。首页只保留分段入口。
- 公众号二维码在 `assets/wechat/`。板卡图目录只放 SVG。
- 合并收口不跳过或调低 STM32/MCU 既有验证门；发布（P5）需明确指令与 AC1–AC8 证据。

## 这一轮改了什么

- `wechat-mp-qr.png` 从 `assets/boards/` 移到 `assets/wechat/`。全仓库只有首页引用这张图，链接已改。板卡目录只留 SVG。
- 现行中文目录以 `docs/README.md` 与 `docs/manifest.json` 为准；英文已归档，不再将 `docs/en/contents.md` 当作本地可执行入口。
- `assets/README.md` 里 `toolchain-flow.svg` 的关联章节从 01 改成 00，与第 0 章正文一致。

## 后续

1. 这 5 张 SVG 还没有 `*-zh.gif`：`i2c-transaction`、`l4-stop2-evidence`、`network-packet-journey`、`rtos-system-layers`、`g0-boot-swd`。`svg2gif.py` 依赖本机 Chrome，这里不生成。
2. `tools/gen_mp_covers.py` 仍只裁 ch00–ch25。封面源在不入库的 `final-videos/`，仓库里没有 ch26–ch28 的封面，所以这次不把循环改成 29。
