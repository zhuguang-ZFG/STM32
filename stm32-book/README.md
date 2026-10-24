# STM32 实战：从点亮一颗灯到交付一个系统

这是一份由仓库 29 章中文教程构建的**独立整书版**，不是把文章直接拼接：

- 7 个分部，各有共同目标和递进顺序；第七部分在第 28 章后有一页书稿专有的「学习路线收束」，不改 `docs/`；
- 29 章逐章加入“问题 / 交付 / 边界 / 来源锚点”；
- 视频、字幕与重复旁白不进入书稿，原 `docs/` 保持不变；
- 构建时去掉二级、三级标题开头的表情符号；章末「相关资源」里的公众号链接、上一篇 / 下一篇和重复免责声明不进书，手册编号保留；
- 封面是内嵌的 `cover.svg` 插画加书名页，不引用外部字体；封面后有一页版本与许可；文前有一处「配套资源」；
- 构建时把已知的居中 `<img>` + `<sub>` 图注收成 `<figure>` / `<figcaption>`，不改 `docs/` 正文；
- 目录用每章 Markdown 的一级标题，仍按七个分部排列；目录不展开章内二级标题，以免 PDF 页码目录过长；
- 附录包含 UART+DMA 工程深读、14 例验证索引、29 章答案、按主题加厚的术语表、来源与许可；
- HTML 把本地图片内嵌为 data URI，断网后仍可单文件阅读；
- PDF 使用同一份 HTML 打印，保留标题书签、完整出版元数据、奇偶页眉、带页码目录和页脚页码。

当前版本：**v1.0.0-rc.8 · 2026-10-24**。这还不是 GitHub Release。中文整书和英文整书共用这一版号。

## 构建

从仓库根目录运行：

```bash
python stm32-book/build_html.py
python stm32-book/build_html.py --pdf
python stm32-book/build_html.py --lang en
python stm32-book/build_html.py --lang en --pdf
```

`--lang` 默认 `zh`。英文版读 `manifest-en.json`、`docs/en/` 和 `stm32-book/book/en/`。

默认输出：

```text
stm32-book/dist/stm32-practical-book.html
stm32-book/dist/stm32-practical-book.pdf
stm32-book/dist/stm32-practical-book-en.html
stm32-book/dist/stm32-practical-book-en.pdf
```

PDF 需要本机 Chrome 或 Edge；也可显式指定：

```bash
python stm32-book/build_html.py --pdf --browser "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
```

依赖版本见 `requirements.txt`。普通 HTML 构建只需要 Python-Markdown；PDF 还需要 Playwright Python 包、可用浏览器和 PyMuPDF。

## 质量检查

```bash
python -m unittest discover stm32-book/tests -v
python stm32-book/build_html.py --check
python stm32-book/build_html.py --lang en --check
```

检查项包括：

- manifest 与 `docs/00–28` 一一对应；
- 29 份章节罗盘都有问题、交付、边界和已登记来源；
- 五份附录都入书；
- 所有本地图片存在并已内嵌；
- 章节 Markdown 链接已变为整书锚点；
- 所有 `#fragment` 都能在同一 HTML 找到目标；
- 手机端宽表进入可聚焦的横向滚动区，列宽不会被压成逐字竖排；
- 打印版保持标题、图注、表格行和代码块的阅读单元，并设置孤行/寡行控制；
- 视频区块完整成对且构建后不残留；
- 书稿不含 `mp.weixin.qq.com`、手机阅读版和章节间的上一篇 / 下一篇导航；
- 目录条目是章节一级标题，第七部分目录含「学习路线收束」；
- 术语表按主题覆盖时钟、引脚、中断、定时器、总线、采样、Flash、低功耗、RTOS、网络和调试；
- 版本页带 manifest 版本号，封面插画内嵌，不请求外部字体；
- 已知居中图注变成 `figure` / `figcaption`，正文里不再留下 `align="center"`；
- `--lang en` 产出 29 章英文书，章末的 Previous / Next 和插画免责声明不进书；
- 缺图、漏罗盘、坏锚点和未闭合视频块会让构建失败。

## 离正式 1.0.0 还差

rc.8 把已知图注收成语义化 figure，换上内嵌封面插画，并加上英文离线整书。这一版停在 rc.8。构建脚本不会自己创建 GitHub Release。

rc.8 合并进 `main` 并且 Book CI 绿了之后，由有权限的人再发 1.0.0：

1. 另开一个版本提交，把 `stm32-book/manifest.json`、`stm32-book/manifest-en.json` 的 `version`，以及本 README 的版本行，从 `1.0.0-rc.8` 改成 `1.0.0`。不要把 rc.8 的产物标成 1.0.0。
2. 等这次提交在 `main` 上的 Book CI 变绿。它会给出两个 artifact：`stm32-practical-book` 和 `stm32-practical-book-en`，各含 HTML 与 PDF，保留 14 天。
3. 核对四份文件来自同一次绿色构建，文件名是 `stm32-practical-book.html`、`stm32-practical-book.pdf`、`stm32-practical-book-en.html`、`stm32-practical-book-en.pdf`。
4. 在该提交上打 tag `v1.0.0`，创建 GitHub Release，并附上这四份文件。

## 内容维护

| 内容 | 唯一维护位置 |
| --- | --- |
| 29 章中文正文 | `docs/00–28` |
| 29 章英文正文 | `docs/en/00–28` |
| 中文分部、罗盘、来源快照 | `stm32-book/manifest.json` |
| 英文分部、罗盘、来源快照 | `stm32-book/manifest-en.json` |
| 中文附录与第七部分收束页 | `stm32-book/book/` |
| 英文附录与收束页 | `stm32-book/book/en/` |
| 封面插画 | `stm32-book/cover.svg` |
| 构建与 PDF 输出 | `stm32-book/build_html.py` |
| 整书契约回归 | `stm32-book/tests/test_build.py` |

新增或重命名章节时，构建器会要求同时更新 manifest；不能通过漏掉章节来让构建继续。GitHub 参考实现必须登记 tag 或完整 commit，社区文章必须标注其非规范边界和访问日期。

## 许可

- 书稿原创正文、版式和原创图片：CC BY 4.0；
- `assets/photos/` 两张第三方 Nucleo-64 实拍：保持原 CC0 1.0，作者、原图页和处理记录见该目录 README；
- 构建器、测试与代码片段：MIT；
- 外部手册和仓库只作链接与事实引用，不随本书再分发；各自权利归原权利人。

组织方式参考同一工作区 BMS-Z 书籍的分部目标、章节罗盘和离线构建方法；未复制其正文。
