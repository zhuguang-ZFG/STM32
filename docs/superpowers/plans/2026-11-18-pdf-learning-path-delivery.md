# 学习路径、实验协议与新封面PDF交付验收

## 授权范围与源状态

2026-11-18（Asia/Shanghai），按本轮授权在本地`D:\Users\STM32`重建当前合并版PDF，并提交学习路径/实验协议/封面及对应验收记录。初始main与fetch后的origin/main均为`476e409dfe143ad82dea83070ddc62b21cef18ef`，截至验收记录时的fetch均未发现远端前进。仅处理已审阅的20份文件及本记录；`.qoder/`保留，IDE/外部备份/临时日志/固件二进制不纳入Git。

前轮记录中的“未提交/未构建/未更新PDF”描述的是当时阶段，本记录登记后续交付，不回改历史事实。硬件仍全部未实测，本轮没有打开串口、操作探针、读写目标Flash或刷写，没有视频工作。

## 标准交付文件（不藏在备份目录）

- PDF：`D:\Users\STM32\book\dist\print\merged-book.pdf`
- 配套HTML与meta：同目录`merged-book.html`、`merged-book.meta.json`。
- 实际页数：**833页**；字节数：**29200885**。
- 生成/文件时间：**2026-11-18T17:53:19.351488+08:00（Asia/Shanghai）**。
- SHA-256：`8e92425a9904beb87a7cdf7947b1835e28019d741c95cd16707448700bb1f0fc`。
- 旧标准PDF已完整备份到`D:\Users\STM32-pdf-delivery-backup-20261118-174116\original-standard-merged-book.pdf`，原文件SHA-256为`37ea76a4a35ab159ec84e1ff77535d4ec54988d160ad2ec6ea9920d11034fe24`；同时备份了旧HTML/meta与20份范围文件。
- 先在外部新目录按现有两阶段管线构建，全部验收成功后校验源输入/旧PDF未被并发改写，再逐文件临时复制、校验哈希、原子替换标准文件；标准PDF与已验收候选哈希完全一致。
- `book/dist/`被现有.gitignore忽略，PDF/HTML/meta**不进入Git**，不force-add，不上传release或网站。仓库提交包含源文档、测试与本验收记录。

## 可复现构建与门禁

在仓库根、现有环境中执行（完整命令/退出码/日志在外部备份`verification/results.json`）：

1. `python -m book.manifest --check`、`python -m book.checks --check`、`python -m book.mapping --check`均退出0。
2. `python tools/check_assets.py`退出0，543项public assets PASS，merged-book assets PASS。
3. `python -m unittest discover -s book/tests -v`：**88 tests OK**，无跳过。
4. `python -m book.build_html --check`：临时构建53页，0 planned chapters missing。
5. `python -m book.build_print_edition --out "D:\Users\STM32-pdf-delivery-backup-20261118-174116\build\merged-book.html"`：47章、63条outline。
6. `python -m book.print_pdf --html "D:\Users\STM32-pdf-delivery-backup-20261118-174116\build\merged-book.html" --meta "D:\Users\STM32-pdf-delivery-backup-20261118-174116\build\merged-book.meta.json" --out "D:\Users\STM32-pdf-delivery-backup-20261118-174116\build\merged-book.pdf"`：退出0，833页。
7. `git diff --check`与提交前范围/秘密/忽略规则检查；不跳过hook，不放宽门禁。

印刷过程仅按原管线截取现有SVG静帧，没有重绘/再生成源插图或视频。构建前后676份已登记源输入哈希一致。管线未修改，仅沿用已审阅的新封面文案与回归测试。

## PDF真实检查与目视抽查

| 检查 | 实际结果 |
| --- | --- |
| 真实PDF封面 | 含“原理讲解 · 工程示例 · 实验指南”，封面无“全程实物实验”/“全程实测” |
| 文本抽取 | 824151字符，U+FFFD替换字符0 |
| 字体 | 17项字体资源均有嵌入数据，含NotoSansSC/NotoSerifSC、CascadiaMono、SimSun、MicrosoftYaHei/Consolas等 |
| 目录与书签 | 63条书签；实际查看p2目录，页码与正常版心可见 |
| 横向溢出 | 原Chromium的176mm版心硬门通过，未更改阈值 |
| 空页/越界 | 原空白页门通过，独立复查空页0；逐文本span检查超出物理页面0（1pt浮点容差） |
| 新学习路径 | p738起出现“五阶段能力目标与47章依赖索引”；p739覆盖声明47/47，p739–744依赖表；p744起阶段验收；该表区域可抽取ch00–ch46全部ID |
| 实际查看的PNG渲染 | p1封面、p2目录、p73工具链文字/命令、p74密集工具链图、p117密集C代码、p738路径导入、p741依赖表、p744阶段验收；未见本轮新增裁切、遮挡或乱码，表头跨页重复正常 |

抽查并非逐页编辑审校；p73既有重复“机制”小标题仍可见，属于原正文的编辑问题，本轮不扩展重写。新PDF不是硬件实测证明，所有空白读数与pending状态保持原边界。

## 提交范围与后续边界

计划分两个语义提交：学习路径/实验协议与其审阅记录；封面文案/回归及准备、PDF交付记录。使用原git作者配置，提交前再次fetch检查关系，只正常push main，不force/no-verify/rebase/amend已推历史。具体commit与远端确认以最终交付报告和Git记录为准，不将尚未推送的结果写成已成功。

标准PDF已经更新；未安装依赖、未触碰硬件、未发布网站/Release。验收材料留在外部备份`D:\Users\STM32-pdf-delivery-backup-20261118-174116`，Git工作区预期仅剩明确保留的`.qoder/`。停止本轮，不自动开始测量或新批次。
