# STM32 实战：从点亮一颗灯到交付一个系统

这是一份由仓库 28 章中文教程构建的**独立整书版**，不是把文章直接拼接：

- 6 个分部，各有共同目标和递进顺序；
- 28 章逐章加入“问题 / 交付 / 边界 / 来源锚点”；
- 视频、字幕与重复旁白不进入书稿，原 `docs/` 保持不变；
- 附录包含 UART+DMA 工程深读、14 例验证索引、28 章答案、术语表、来源与许可；
- HTML 把本地图片内嵌为 data URI，断网后仍可单文件阅读；
- PDF 使用同一份 HTML 打印，保留标题书签、完整出版元数据，并在封面后加页码。

当前版本：**v1.0.0-rc.4 · 2026-10-23**。

## 构建

从仓库根目录运行：

```bash
python stm32-book/build_html.py
python stm32-book/build_html.py --pdf
```

默认输出：

```text
stm32-book/dist/stm32-practical-book.html
stm32-book/dist/stm32-practical-book.pdf
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
```

检查项包括：

- manifest 与 `docs/00–27` 一一对应；
- 28 份章节罗盘都有问题、交付、边界和已登记来源；
- 五份附录都入书；
- 所有本地图片存在并已内嵌；
- 章节 Markdown 链接已变为整书锚点；
- 所有 `#fragment` 都能在同一 HTML 找到目标；
- 手机端宽表进入可聚焦的横向滚动区，列宽不会被压成逐字竖排；
- 打印版保持标题、图注、表格行和代码块的阅读单元，并设置孤行/寡行控制；
- 视频区块完整成对且构建后不残留；
- 缺图、漏罗盘、坏锚点和未闭合视频块会让构建失败。

## 内容维护

| 内容 | 唯一维护位置 |
| --- | --- |
| 28 章正文 | `docs/00–27` |
| 分部顺序、章节罗盘、来源快照 | `stm32-book/manifest.json` |
| 五份附录 | `stm32-book/book/` |
| 构建与 PDF 输出 | `stm32-book/build_html.py` |
| 整书契约回归 | `stm32-book/tests/test_build.py` |

新增或重命名章节时，构建器会要求同时更新 manifest；不能通过漏掉章节来让构建继续。GitHub 参考实现必须登记 tag 或完整 commit，社区文章必须标注其非规范边界和访问日期。

## 许可

- 书稿原创正文、版式和原创图片：CC BY 4.0；
- `assets/photos/` 两张第三方 Nucleo-64 实拍：保持原 CC0 1.0，作者、原图页和处理记录见该目录 README；
- 构建器、测试与代码片段：MIT；
- 外部手册和仓库只作链接与事实引用，不随本书再分发；各自权利归原权利人。

组织方式参考同一工作区 BMS-Z 书籍的分部目标、章节罗盘和离线构建方法；未复制其正文。
