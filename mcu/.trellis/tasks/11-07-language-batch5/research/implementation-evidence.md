# 第五批B7实施证据

## 授权和范围

用户在四处方案、设计和实施验收计划交付后要求“继续改进优化”；本轮沿用11-07-language-batch5，不重复创建。task.py validate实际8+7通过，task.py start成功planning→in_progress。仅本地实施与验收，不继承上一批提交/推送/发布授权，不进入S篇。

正文仅docs/build/07-build-system.md原27/51/116/134，方向逐字来自既有reading-evidence/source-evidence。代码、表格、引文、数字、标题锚点、链接、图/动画、实验/答案、章节骨架和五组技术疑点保持。

## 逐处理解收益

| ID | 原行 | 实际调整 | 收益 |
|---|---:|---|---|
| B7-A | 27 | 只将中间问句中的“路径变脏”改为受影响的目标 | 预测对象可指向构建目标，不需先懂行话；原引文仍在 |
| B7-B | 51 | 关系/时间判断之后给出沿图找受影响目标的动作 | 读图知道看什么，不再只说“核心价值”；不宣称实验成功 |
| B7-C | 116 | 用原有两百/二十例子说明目录管理，再将两命令写成先生成后构建 | 原四段行内代码和顺序不变，代价与动作对应 |
| B7-D | 134 | 将三工具分工展开为完整主谓句 | CMake/组件、Kconfig/配置、idf.py/调度直接对应，B1四步保持 |

前后逐字对照见reading-evidence；before/candidate纯LF文件保留，来源和最终哈希见source-evidence/final-source-evidence。

## 字节保护证明

- 27来源输入、214验证/runner/CI文件在编辑前逐项SHA核对；用户42文件成员和SHA与规划相同。
- before及candidate初始副本逐字节等于当时正式docs，纯LF；原文SHA3de591b83b328e2358ea050aa665387186f15f293f2df59b55af9715ebb1176d。
- candidate改后实际before→candidate strict CLI：“不可动清单：全部一致”，未用additions；白名单恰27/51/116/134，四行外完全一致，引文与容器精确相同，逐行等于获审方向。
- 落盘后另实际before→最终docs strict CLI：“不可动清单：全部一致”；最终docs字节==已验candidate，不以candidate互验冒充正文检查。
- 最终正文SHA99d91a5fd257f24d16cd1bb2cc71689c834d08568781cfb5d731b3589169090c。26冻结来源（含B0–B6）和214固定输入在落盘复核未变。

## 已执行检查

- strict guard：候选和正式正文两次均exit0、全部一致。
- prose-readability --check：78章，平均长句占比10.1%，通过；未更新baseline。
- reading-time --check：78篇均在模型±40%内，通过。
- docs-check：138文件、6类检查，通过。
- build_html.py --check：94章、题图94/94、10803529 bytes，whole-book HTML contract PASS，写临时目录，不重建完整PDF。
- task_verify(action=run)：unverified / project-or-git-baseline-unavailable / checks=[]；没有operator通过项，不把手动检查冒充配置覆盖。
- 站点构建及真实页面结果须在实际完成后另记，不以前批结果冒充。

## 指标旁证

| 状态 | 句数 | 长句占比 | 平均句长 |
|---|---:|---:|---:|
| before | 95 | 9.5% | 35.2 |
| final | 96 | 9.4% | 34.9 |

调用原metrics()，不设新阈值。读者能否明确观察对象、命令先后和角色分工由逐处对照与文字验收判断，不由数字下降证明。

## 验证边界

无新增/修改测试、runner、CI、策略、阈值或基线；没有执行章内make clean、touch、改依赖、flash或固件/硬件实验。保留已登记技术疑点，不把语言编辑当事实修订。本轮不提交、推送、合并、发布、归档或跨入S篇。

## 正文站点构建

bg_40实际完成：guide-check PASS，docs-gen统计86/86章节、8/8实验、111动画、47示例工程；VitePress v1.6.4 build40.01s成功。保留h/kconfig高亮回退、gpiof-moder.json静动态同时导入和chunk>500kB告警，未改策略。该次尚未包含待烟测后补的配套日志；日志后须再构建。

## 真实页面与交互

bg_40成功后启动本任务preview4198。启动参数的ready.log误用Local:，而preview实际日志是Built site served，因此工具等待标记超时；未计ready通过。服务进程仍在，实际浏览器成功打开http://localhost:4198/mcu/build/07-build-system.html并读到正文，以实际加载/交互为证，不重新启动绕过或修改站点。

- 四行新文逐一在渲染正文中找到，四行旧文均不在；原页7个pre、2个内联svg、4个details，图片失败0。
- 桌面1440×960：实际点击quick win、依赖动画及CMake目录，hash与标题可视性均确认；答案默认false，点击后open:true且答案可见。截图观察预测、依赖动画、CMake段与代码、IDF分工及相邻表格/代码。
- 手机390×844：先应用emulate并确认实际innerWidth390、不再goto；实际展开“本页目录”，点击quick win及动画链接，目标hash与标题可视性确认。首答案先关闭再点击打开，false→true且内容可见。截图观察四处新文、依赖动画及CMake/IDF代码。
- 手机document.scrollWidth390，散文段落不越界；长代码块client308/scroll451、表格client310/scroll732，均overflow-x:auto，实际scrollLeft0→80→0；横向滚动不扩文档宽。
- page errors0、失败图片0，桌面document宽1440。验证tab已关闭，preview已停止。

配套changelog烟测后补入，含日志最终docs-check/guide-check/docs-gen/build待实际执行完成另记，不拿bg_40当最终含日志证据。

## 含日志最终构建与交付

bg_41实际成功：docs-check扫描138文件、6类检查通过；guide-check PASS；docs-gen成功；VitePress最终build48.78s成功（wall50.55s）。保留原有高亮/import/chunk告警，未修改门禁或策略。该次构建包含本批changelog，不借用bg_40冒充。

结束时最终docs仍等于已验candidate；26冻结来源、214验证输入、用户42文件成员与内容全部保持。上下文validate实际8+7通过。task_verify最终仍unverified / project-or-git-baseline-unavailable / checks=[]，没有配置通过项。四处前后对照与收益保留供用户文字验收，任务保持in_progress；没有提交推送发布或归档。
