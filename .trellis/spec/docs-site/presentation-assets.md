# 导读与传播资产契约

## 1. Scope / Trigger

精排导读、书籍金句卡的同源维护，以及独立 HTML 接入 VitePress。适用于 `scripts/book-guide/`、`scripts/social-cards/`、`docs/public/book-guide/` 和 `video/assets/social-cards/book/`。

## 2. Signatures

- `npm run guide:generate`：使用已安装的 guizang-page-skill 渲染 `docs/reference/book.md`；可设 `GUIZANG_PAGE_SKILL` 指定 skill 根目录。
- `npm run guide:check`：只用 Node 核对源文、生成器与 HTML 摘要，以及分享/无障碍基线。
- `npm run cards:render` / `cards:check`：用 Playwright 生成/核对 29 张竖版卡及 1 张横版封面。
- `docs:build` 前置 `guide:check`，CI 不需安装设计 skill。

## 3. Contracts

- 导读正文只改 `docs/reference/book.md`；升格行号按节标题定位，禁止复用旧行号或让自造摘要替换原文。
- 生成件位于 `docs/public/book-guide/index.html`；入口使用相对链接 `../book-guide/index.html` 和 `target="_self"`。后者使 VitePress 不拦截成 SPA 路由，否则 URL 看似正确却加载 404。
- 导读使用当前站点 base，canonical 指向原书籍入口；照片来自站内，初次打开不依赖远端字体/默认图片。main 地标、标题与主题前景色必须保持可见。共享模板的深色 hero 样式不能直接套在浅色背景。
- 导读发布件关闭 `contenteditable`；原 source/generator 摘要按 LF 归一化，产物字节摘要记录到 `manifest.json`。本地 renderer 来源与摘要另行登记，不复制 skill 运行时到项目。
- 金句卡源在 `scripts/social-cards/`，正式资产在 `video/assets/social-cards/book/`；`.temp/` 仅作生成中间输出，不能作为源码输入。
- 卡片主句及小注保持接收基线。来源判据允许排版分隔符差异；G1 原句的括注省略只允许明确登记的两段原文按序匹配。
- 竖版 750×1000 CSS px、2 倍像素输出 1500×2000；横版 2560×1440。内容组与台账间距固定，页脚独立，禁止 `.rows{margin-top:auto}` 再造中部断层；最长标签独立列，列内文本可换行。

## 4. Validation & Error Matrix

| 输入/事件 | 结果 |
|---|---|
| 源 Markdown、生成器或 site.css 改了但未重生成 | guide:check 非零退出，阻止站点发布 |
| HTML 人工篡改、丢 canonical/main 或含可编辑正文 | 点名并退出 |
| GitHub 上的 README.md 外链 | 保留；只拒绝尚未转为页面的本地 .md 链接 |
| 卡片主句离开章节、全卡文字偏离基线、文字越列或压页脚 | 点名卡 ID 并中止正式输出 |
| 正文块之间空隙超过 100px / 小于 20px，PNG 尺寸或摘要不符 | cards:check 非零退出 |
| pages:check 遇到脚本/CSS 里的 `a[href="#'+id+'"]` | 不算链接；清空 script/style 文本时保留换行与字符位置，真实链接错误行号不变 |

## 5. Good / Base / Bad Cases

- Good：改书籍入口源文 → guide:generate → 390px/1440px 真点击入口与目录 → guide:check + quality。
- Base：仅复验已生成资源，用 guide:check/cards:check，无需重新调用外部渲染器。
- Bad：只检查 URL 变化；VitePress 的 404 也可能保留目标 URL。必须断言独立页 `html[data-medium="page"]` 和 main 内标题。

## 6. Tests Required

- `tests/book-guide.test.mjs`：源/生成器漂移、产物篡改、GitHub 外链放行、本地 .md 拒绝、外部图片/字体、可编辑正文、元数据与地标缺失。
- `tests/browser/book-guide.spec.mjs`：390px/1440px 从书籍入口真实载入；独立页标识、标题与背景异色、无横向溢出、目录跳转与手机关闭目录。
- `tests/pages-check.test.mjs`：script/style 内伪 href 不进入统计，真实断链仍报正确行号。
- 卡片产线自校验：29 张文字、主句来源、组内间距、文字范围、安全区、30 张 PNG 摘要及尺寸；浏览器联系表全图载入。

## 7. Wrong vs Correct

- Wrong：独立 HTML 在文件地址打开正常，就宣布站点入口可用。Correct：构建后从 VitePress 原入口实际点击，核对页面标识与内容。
- Wrong：CSS 检查通过就认为标题可读。Correct：检查截图及计算前景/背景色，hero 必须与当前主题配套。
- Wrong：改卡片只覆盖 PNG，源 HTML 仍在个人 `.temp/`。Correct：源码、共享 CSS、命令与摘要一并保存，旧交付保留历史。
