# STM32 实战：从点亮一颗灯到交付一个系统

这是一份由仓库 29 章中文教程构建的**独立整书版**，不是把文章直接拼接：

- 7 个分部，各有共同目标和递进顺序；第七部分在第 28 章后有一页书稿专有的「学习路线收束」，不改 `docs/`；
- 29 章逐章加入“问题 / 交付 / 边界 / 来源锚点”；
- 视频、字幕与重复旁白不进入书稿，原 `docs/` 保持不变；
- 构建时去掉二级、三级标题开头的表情符号；章末「相关资源」里的公众号链接、上一篇 / 下一篇和重复免责声明不进书，手册编号保留；
- 封面是内嵌的 `cover.svg` 插画加书名页，不引用外部字体；封面后有一页版本与许可，接着是版本与修订；文前有一处「配套资源」；
- 附录和第七部分收束页之后有书末主题索引，条目链到章内小节；PDF 在索引条目旁盖上物理页码；
- 构建时把已知的居中 `<img>` + `<sub>` 图注收成 `<figure>` / `<figcaption>`，不改 `docs/` 正文；
- 目录用每章 Markdown 的一级标题，仍按七个分部排列；读者看到的章号是第 1–29 章（英文 Chapter 1–29），文件名和 `#chapter-00` 这类锚点仍是 00–28；目录不展开章内二级标题；
- 附录包含 UART+DMA 工程深读、14 例验证索引、29 章答案、按主题加厚的术语表、来源与许可；术语表文末先是 BluePill 的数字账，接着是换系列时要重算的时序、寄存器和勘误级边界；第七部分收束页用前一张账写第一块板，再用后一张账写换芯片时的三行；
- HTML 把本地图片内嵌为 data URI，断网后仍可单文件阅读；
- PDF 使用同一份 HTML 打印。书签只保留分部、章、附录、版本与修订和主题索引，不展开章内二、三级标题；另有完整出版元数据、奇偶页眉、带页码目录和页脚页码。

当前版本：**v1.1.0 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后再打。

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
- 已有的引用块分成注意、提示、说明三种 callout，中英文标签成对；
- 分部、章节、附录的眉题用对应语言；屏幕上目录分部标题滚动时贴顶，并有固定的「目录 / Contents」；
- 打印时图注跟着图，过高的图限制在一页高度内；页眉页脚共用细线，英文书名在冒号处截成短页眉，附录续页也有页眉；
- 章首罗盘是问题 / 交付 / 边界三张卡片，标题不是标题标签，避免 PDF 书签里每章都多一条「本章罗盘」；章末三问同样不进书签；
- 代码块在屏幕上保留缩进并可横向滚动，打印时允许跨页折行；术语表第三列标出常见误解，来源卡用标识作眉题；
- 窄于 960px 时罗盘、来源卡和版本页定义列表改成一列；分部大号不压住标题；封面信号色与正文强调色同一路青；
- 章内二级标题有左侧色条，列表标记用强调色，图版有边框和浅底；打印时图版去掉底色，表格斑马纹也不进纸面；
- 窄于 720px 时术语表第一列在横向滚动中贴住；术语表里只有三列表的第三列、四列表的第四列才涂成误解色；
- 代码块两端的滚动提示用浅色，在深色代码底上能看见；选中文字用强调色的浅底；
- 附录 D 文末有 BluePill（STM32F103C8T6）的数字账；附录 A、B、E、F 用同一组订货号、BRR 和微秒，不改 `docs/`；
- 附录 D 还有一页换系列的账：1 kHz 的 PSC/ARR、约 167 ns 的入栈、FromISR 的 `0x50`、500 与 450 kbit/s、1 KB 页与两把钥匙、G0 第四个 SYSCLK 上升沿、L4 封面 1.1 µA、H7 的 400/480 MHz。附录 E 用同一笔 CAN 账填过一张证据格子。附录 F 在第一块板的四行之后有换芯片的三行；
- 附录 D 还有第三张账：SPI 的 9 MHz 与 `0xEF4017`、F103 的 DMA1 通道与半字 NDTR、USB 的 48 MHz 与 67 字节、`0xE000ED28` 起的故障寄存器、17.2% 的示例利用率、RMII 的 50 MHz 与 MSS 1460。附录 A 第 8 节和附录 C 的对账用同一组数；
- `--lang en` 产出 29 章英文书，章末的 Previous / Next 和插画免责声明不进书；
- 缺图、漏罗盘、坏锚点和未闭合视频块会让构建失败。

## 发布 GitHub Release

版本号已经是 1.1.0。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0。

这次提交进入 `main` 并且 Book CI 变绿之后，由有权限的人：

1. 下载这次 `main` 运行的两个 artifact：`stm32-practical-book` 和 `stm32-practical-book-en`，各含 HTML 与 PDF，保留 14 天。
2. 核对四份文件来自同一次绿色构建，文件名是 `stm32-practical-book.html`、`stm32-practical-book.pdf`、`stm32-practical-book-en.html`、`stm32-practical-book-en.pdf`。
3. 在该提交上打 tag `v1.1.0`，创建 GitHub Release，并附上这四份文件。

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
| 版本与修订条目 | `stm32-book/revisions.json` |
| 书末主题索引 | `stm32-book/subject-index.json` |

新增或重命名章节时，构建器会要求同时更新 manifest；不能通过漏掉章节来让构建继续。GitHub 参考实现必须登记 tag 或完整 commit，社区文章必须标注其非规范边界和访问日期。

## 许可

- 书稿原创正文、版式和原创图片：CC BY 4.0；
- `assets/photos/` 两张第三方 Nucleo-64 实拍：保持原 CC0 1.0，作者、原图页和处理记录见该目录 README；
- 构建器、测试与代码片段：MIT；
- 外部手册和仓库只作链接与事实引用，不随本书再分发；各自权利归原权利人。

组织方式参考同一工作区 BMS-Z 书籍的分部目标、章节罗盘和离线构建方法；未复制其正文。
