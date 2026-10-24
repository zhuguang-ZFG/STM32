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
| `assets/video/` | 正片与 AI 续集。早期成片在 `superseded/` | [assets/video/README.md](assets/video/README.md) |
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
- 讲解正片由 `tools/narration.py` + `tools/gen_narrated.py` 生成，文件名是 `ch{章号}-{slug}`。AI 续集把 `NARRATED_MODULE=narration_ai`，文件名是 `chs{集号}-{slug}`。`chai01-ai-gpio` 是续集第一集的早期成片，在 `assets/video/superseded/`。
- 对外讲章节范围时用 **00–28，共 29 章**。`tools/gen_mp_covers.py` 仍只裁 ch00–ch25，因为封面源在不入库的 `final-videos/`。
- 中文速查表留在仓库根的 `cheatsheets/`。英文速查表留在 `docs/en/cheatsheets/`。两处都已经有链接，不合并目录。

## 这一轮改了什么

- `chai01-ai-gpio` 与 `chs01-ai-basics` 字幕逐段对照后，确认是同一集的早期成片（两处用词不同，时间轴是重新配音的）。三个文件移到 `assets/video/superseded/`，主目录只留现行续集。没有删除。
- 首页公众号导语和 `tools/md2mp.py` 页脚改为「00–28 共 29 章」。`md2mp.py` 本来就会转换全部编号章节；「26 章」是系列还停在 ch25 时留下的。`narration_ai.py` 的模块说明改为「正片 00–28 之后」。
- `tools/gen_videos.py` 确认没有被 Makefile、CI 或 `check_assets.py` 调用。文件保留，默认直接运行会退出，避免写出旧 GIF 或改写章节。说明写在 `tools/README.md`。
- `md2mp.py` 只转换文件名以「速查表」结尾的中文速查表，不再把 `cheatsheets/README.md` 当成一篇公众号稿。

## 后续

1. 这 5 张 SVG 还没有 `*-zh.gif`：`i2c-transaction`、`l4-stop2-evidence`、`network-packet-journey`、`rtos-system-layers`、`g0-boot-swd`。`svg2gif.py` 依赖本机 Chrome，这里不生成。
2. `tools/gen_mp_covers.py` 仍只裁 ch00–ch25。封面源在不入库的 `final-videos/`。本地有 ch26–ch28 封面后再把循环改成 29。
3. `assets/boards/wechat-mp-qr.png` 和板卡图放在同一目录。挪走会改首页图片地址，单独做。
4. 首页和 `docs/README.md` 各有一份章节关键词表。首页适合扫读，所以两份都留着。若以后只维护一份，以 `docs/README.md` 为准。
