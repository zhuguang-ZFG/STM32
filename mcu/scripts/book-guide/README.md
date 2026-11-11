# 精排书籍导读

正文唯一来源是 `docs/reference/book.md`，正式产物在 `docs/public/book-guide/index.html`。章节事实、插图数量和附录名称全部从当前 Markdown 原样渲染；只把「参与校对与贡献」列表升格为 checklist，行号按节名动态定位，避免改文后错位。

```sh
npm run guide:generate
npm run guide:check
```

生成需本机安装 `guizang-page-skill`，默认查找当前用户的 `.agents/skills/` 与 `.codex/skills/`，也可设置 `GUIZANG_PAGE_SKILL` 指定目录；不在仓库内复制 skill 的运行时。检查只需 Node，可在 CI 中运行。

产物提供 canonical/分享元数据和 main 地标，以 `/mcu/` 为站点 base，使用仓库已有 STM32 板卡照片和系统字体，不请求远端默认头图及在线字体。发布页关闭就地编辑，文字只能从 Markdown 维护。页面设置面板仍能选择系统字体与主题。

manifest 核对正文、生成器和 HTML 哈希，记录渲染器来源摘要。更新源文后须重新生成，否则 `guide:check` 非零退出；`docs:build` 前置这道检查，不会带着陈旧导读发布。源文件使用 LF 归一化摘要，兼容 Windows 检出。
