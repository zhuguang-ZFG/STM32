# 已退役的无源 PNG（2026-11-18）

`handraw/` 现在只放**成对**的资产：每张 PNG 都有同名 SVG 源，仓库里能重建。
这里记录被移走的那批，供日后查账。

## 移走了什么

| 项 | 值 |
|---|---|
| 文件数 | 89 张 PNG |
| 体积 | 72.2 MB |
| 判据 | 目录里没有同名 `.svg`，无法从仓库重建 |
| 去向 | 全部在 git 历史里，`git log --diff-filter=D -- assets/illustrations/handraw` 可查 |
| 恢复单张 | `git show <删除前提交>:assets/illustrations/handraw/<名字>.png > <目标路径>` |

删前实测：89 张中 88 张零引用（章节、工具、脚本都不提），68 张在
`docs/public/images/` 里没有副本——它们是工作区里的唯一一份，但都在 git 历史内。

## 其中 6 张是被新版取代，不是丢失

| 名字 | 现状 |
|---|---|
| `ch00-three-api-lanes` | 由 `staged/learning-plates/` 的 SVG 重绘，发布图更新 |
| `ch13-bit-quanta` | 同上 |
| `ch13-can-bit` | 同上 |
| `ch13-filter-fifo` | 同上 |
| `ch14-usb-enum` | 同上 |
| `ch14-usbpre-48` | 同上 |

这 6 张的旧 PNG 与已发布版本字节不同，属于改稿前的底稿；章节显示的是新版。

## 1 张仍被计划文档提到

`ch00-roadmap-three-stages` 只出现在
`docs/superpowers/plans/2026-11-14-merged-book-b4-vol6-7-appendices.md` 的插图清单里。
该计划已执行完毕，清单是当时的写法；正文没有任何引用。

## 判定规则（以后照这个来）

- PNG 有同名 SVG → 保留，属可重建资产。
- PNG 无同名 SVG 且被正文引用 → **不许删**，先补 SVG 源或补 staged 源。
  `book/tests/test_figure_sources.py` 会拦。
- PNG 无同名 SVG 且无人引用 → 退役，记到这里。
