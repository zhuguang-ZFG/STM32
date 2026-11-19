# 合并版构建与验收

当前正文唯一入口是 `docs/manifest.json`：中文 47 章 + 6 附录。英文按归档策略保留于历史标签，未随合并版重建；`stm32-book/` 的本地残留不是现行构建入口。

在 Git 仓库根运行（Windows 使用 `python`；Make 的默认解释器可用 `PY=python` 覆盖）：

```sh
python -m book.manifest --check
python -m book.mapping --check
python -m book.checks --check
python tools/check_assets.py
python -m unittest discover book/tests -v
python -m book.build_html --check
```

`--check` 的 HTML 构建会在系统临时目录写入并清理站点，不覆盖 `book/dist/site`。其他上述检查不生成书稿或资产。`check_assets` 检查现行章节完整性、链接/锚点/测验，以及 `docs/public/` 的 SVG XML、PNG/JPEG/GIF/WebP 解码，不再要求已下线的英文旧章引用短视频。归档旧布局仍保留原像素/视频检查。

站点 CI 的最小依赖仍是 `book/requirements.txt`。新增回归中的位图/印刷集成项仅在 Pillow / Playwright / PyMuPDF 对应模块可用时执行；缺依赖会明确显示 `skipped`，不能把这种最小 CI 结果当作 PDF 验收。本次本地完整验收已具备依赖，87 项均实际执行，无跳过。运行真实浏览器回归还需要已安装的 Chromium/Edge。

## 站点（VitePress）、内容渲染器与印刷 PDF

依赖分三层：站点只需 Node（`npm ci`）；内容门与渲染契约只需 `book/requirements.txt`（Markdown）；印刷 HTML / PDF / EPUB 需要 `book/requirements-print.txt`（`lxml`、Pillow、Playwright、PyMuPDF）加上 Playwright Chromium 与可用中文字体。`book/print_pdf.py` 会检查中文页眉字体，找不到即失败；浏览器依赖需另行准备，构建脚本不会自动安装。

```sh
npm run docs:build                    # 站点 → docs/.vitepress/dist（base /STM32/）
npm run site:pages                    # 页面集合必须与 docs/manifest.json 一一对应
npm run site:images                   # 每张 <img> 必须 loading="lazy" + decoding="async"
npm run site:prune                    # 剪掉 dist 里未被任何页面/运行时引用的位图
npm run site:stubs && npm run site:assemble && npm run site:smoke
python -m book.build_html --check     # 内容渲染契约：53 页可渲染（不产站点）
python -m book.build_print_edition    # 单文件印刷 HTML → book/dist/print/
python -m book.print_pdf --html book/dist/print/merged-book.html --meta book/dist/print/merged-book.meta.json --out book/dist/print/merged-book.pdf
python -m book.build_epub             # EPUB 3（与 PDF 同源输入）
```

站点是 VitePress 多页站；`book.build_html` 的完整构建（不带 `--check`）只用于兼容旧的静态站点产物，页面与锚点由 `book/checks.py` 与站点构建共同校验，两者共享 `cjk_slugify` 与 `docs/.vitepress/data/scenes.json`。后三条生成自包含印刷 HTML/元数据，再打印并后处理 PDF（页码、目录、书签、空页与横向溢出检查）。动画仅截取现有 SVG 的静帧用于印刷，不生成动画或视频。

`make book`、`make book-pdf`、`make book-epub`、`make book-check`、`make site-check` 和 `make check` 分别封装站点、PDF、EPUB、书稿门、站点门和资产门。PDF 会覆盖指定输出；有 WIP 时先备份并将两阶段 `--out` 指向仓库外的新目录。禁止把历史验收页数当成本次结果，须记录实际文件大小、页数、哈希、源输入稳定性和抽查页。

`make assets` / `make verify` 会重新生成资产，且依赖视频目标；视频暂停或有资产 WIP 时不要运行。当前回归与 PDF 验收不需要它们。
