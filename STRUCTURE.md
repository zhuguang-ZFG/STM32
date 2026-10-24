# 仓库结构

> English readers: start at [docs/en/README.md](docs/en/README.md). This file is the map of the repository, not a chapter.

读者从 [README.md](README.md) 进来。章节正文在 `docs/`，不要在别的目录再写一份教程。

## 目录各管什么

| 路径 | 作用 | 入口 |
| --- | --- | --- |
| `docs/` | 中文 00–28 章，唯一正文 | [docs/README.md](docs/README.md) |
| `docs/en/` | 英文 00–28 章，以及英文速查表 | [docs/en/README.md](docs/en/README.md) |
| `stm32-book/` | 用 `docs/` 打成离线 HTML / PDF，附录在 `stm32-book/book/` | [stm32-book/README.md](stm32-book/README.md) |
| `examples/` | 14 个可编译示例。Wokwi 的 `diagram.json` 放在对应示例里 | [examples/README.md](examples/README.md) |
| `labs/` | 真板证据协议，不是另一套示例 | [labs/README.md](labs/README.md) |
| `sim/` | Renode 脚本。和 Wokwi 工程分开 | [sim/README.md](sim/README.md) |
| `cheatsheets/` | 4 份中文速查表。英文在 `docs/en/cheatsheets/` | [cheatsheets/README.md](cheatsheets/README.md) |
| `assets/` | 动画、板卡图、实拍、GIF、讲解视频 | [assets/README.md](assets/README.md) |
| `assets/video/` | 正片、AI 续集、一部未挂脚本的旧片 | [assets/video/README.md](assets/video/README.md) |
| `tools/` | 生成图片、讲解片、公众号稿的脚本 | [tools/README.md](tools/README.md) |
| `Makefile` | `assets` / `check` / `book` / `book-pdf` / `book-check` / `stats` | 文件头注释 |
| `.github/workflows/book.yml` | 在 CI 里编 SPL 示例，并构建整书 HTML/PDF | — |

下面两项目录在 [.gitignore](.gitignore) 里，只出现在作者本机，克隆仓库看不到：

| 路径 | 谁写它 |
| --- | --- |
| `wechat-mp/` | `tools/md2mp.py`、`tools/gen_mp_covers.py` |
| `final-videos/` | `tools/gen_tietu.py`；封面源也被 `gen_mp_covers.py` 读取 |

## 不要混用的几条边界

- 改章节：只改 `docs/`（以及对应的 `docs/en/`）。整书通过 `stm32-book/manifest.json` 引用这些文件。
- `examples/` 要能编译。`labs/` 记录一次真板实验怎样才算完成，里面没有固件工程。
- 6 个教学 GIF 由 `tools/gen_gifs.py` 用标准库生成，文字是 ASCII。`assets/gif/*-zh.gif` 由 `tools/svg2gif.py` 从 SVG 采样，给公众号用，已经提交进 git。
- 讲解正片由 `tools/narration.py` + `tools/gen_narrated.py` 生成，文件名是 `ch{章号}-{slug}`。AI 续集把 `NARRATED_MODULE=narration_ai`，文件名是 `chs{集号}-{slug}`。
- 中文速查表留在仓库根的 `cheatsheets/`。英文速查表留在 `docs/en/cheatsheets/`。两处都已经有链接，这一轮不合并目录。

## 这一轮改了什么

- 补上 `sim/`、`labs/`、`cheatsheets/`、`assets/video/` 的索引，打开目录不再只有散文件。
- 首页「仓库结构」补上英文版、仿真、讲解视频，以及两个不入库的本机目录。原先把 `tools/` 里每个脚本都列在首页，和 `tools/README.md` 重复，而且漏了公众号脚本，现已改成指到工具说明。
- 中文首页的板卡表补上 G0 / L4 / H7 三张引脚图。英文首页原来就有。
- 原理动画按目录实数改为 25（含 `g0-boot-swd.svg`）。首页徽章、英文首页、`CREDITS.md`、`tools/README.md` 一起改。
- `tools/README.md` 写明 `md2mp.py`、`svg2gif.py`、`gen_mp_covers.py`、`gen_tietu.py`、`narration_ai.py` 的产出位置。
- 中英文章节目录加上整书、实验、仿真和本文件的入口。
- `make stats` 只数 `docs/NN-*.md`，不再把 `docs/README.md` 和 `CONTENT_GUIDE.md` 算进章节篇数。
- `tools/md2mp.py` 的用法注释改为「转换全部编号章节」。页脚里面向读者的「26 章」没有改，见下方后续。

没有移动或删除图片、视频和示例。没有改章节教什么。远程分支 `cursor/roadmap-finish-cac9` 和 `cline/2r69bzmk` 没有并进来。

## 后续（这一轮不做）

1. `assets/video/chai01-ai-gpio.*` 对不上当前 `narration_ai.py`（续集文件名是 `chsNN-*`）。确认它是否已被 `chs01-ai-basics` 取代后，再决定保留、改名或移出。不要当垃圾直接删。
2. 这 5 张 SVG 还没有 `*-zh.gif`：`i2c-transaction`、`l4-stop2-evidence`、`network-packet-journey`、`rtos-system-layers`、`g0-boot-swd`。`svg2gif.py` 依赖本机 Chrome，这里不生成。
3. 首页公众号导语和 `md2mp.py` 页脚仍写「26 章」，仓库正文已是 00–28。先确认公众号实际连载到哪一章，再改对外句子。
4. `assets/boards/wechat-mp-qr.png` 和板卡图放在同一目录。挪走会改首页图片地址，单独做。
5. 首页和 `docs/README.md` 各有一份章节关键词表。首页适合扫读，所以这次两份都留着。若以后只维护一份，以 `docs/README.md` 为准。
6. `tools/gen_videos.py` 是旧的五帧幻灯，正片已改走 `gen_narrated.py`。确认没有人再跑它之后，再从主路径拿掉。
