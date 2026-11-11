# 技术设计

## 边界与来源

本任务直接承接旧 spec 的 L3/L5/L6 收口，因此保持单任务，逐项验收并做集成复核。旧目录保留为历史交付与变更基线，不迁移用户已有文件。

## 卡片

把样张、第二批和批 7 的 HTML 源迁入 `scripts/social-cards/`，共享 CSS。页头与页脚固定在安全区，中间内容作为一组在可用空间居中；主句、已有引句与表格之间使用固定间距，去掉 `.rows{margin-top:auto}`。长行允许在同行内容区域换行，标签保留独立宽度。

Playwright 等待字体后按元素截图，输出 `video/assets/social-cards/book/` 与本轮任务内联系表，默认保留 2 倍像素。复验同时对照基线文字、几何边界及 PNG 尺寸。旧产物不删除；旧联系表增加正式交付入口。

## 导读

保留 Markdown 为唯一正文源。由 `scripts/book-guide/generate.mjs` 按节标题动态生成 annotations，使用本机 guizang-page renderer 更新；只升格贡献清单，原 gallery 的摘要替换会缩减原句，正式版弃用。生成件放 `docs/public/book-guide/index.html`，从 `docs/reference/book.md` 入口链接，入口使用相对地址与 `target="_self"` 避开 VitePress 路由拦截。标注行号随源定位，不复制过期事实。

生成器负责站点 base 与相对 Markdown 链接规范化，记录源文件哈希及生成器版本/来源。`--check` 核对源哈希与产物必需结构。导读不进入书籍 manifest，不改在线书正文。

实现约束收敛：当前源只含 GitHub Markdown 外链，原样保留；本地 `.md` 链接不自动猜路由，校验直接拒绝，维护者必须明确页面地址。`site.css` 单独覆盖深色 hero 继承，使用站内 STM32 照片与系统字体；发布件关闭就地编辑，补 SEO 与 main 地标。生成器、契约与 CSS 摘要共同守住过期检查。

## 产物锚点检查器

独立页内联滚动定位脚本带 `a[href="#'+id+'"]`，原纯正则检查器误把它计为断链。本轮在抽取 href 之前屏蔽 script/style 内容并保留字符位置；新增正反例覆盖伪 href 不计数、真实缺锚点仍报原行号。没有修改实际页面链接来迎合检查器。

## PPT

保留旧任务内 13 页 HTML 与 7 张图片，调用已有 skill 校验器；核验 13 条 speaker notes、图片与演讲者运行时。警告保留其适用理由，必要时只修实际错误。

## 回滚与兼容

旧卡片和旧导读均保留；新增入口和正式资源可独立撤回。当前 base `/mcu/` 必须通过构建产物实际访问验证。无远端部署或投稿。
