# 第四批实施与页面验证证据

## 授权与范围

用户先选择“同意，建任务并进入规划”，审阅七行白名单、方向样例与验证计划后选择“通过，开始实施”。task.py start实际成功：planning→in_progress。本轮仅本地实施与验证，没有提交、推送、发布或归档授权。

正文仅B5原行15/18/35/47、B6原行19/50/101，另在docs/reference/changelog.md增加本批说明。原句、方向样例与逐处理解收益见reading-evidence.md；实施前及最终SHA见source-evidence.json与final-source-evidence.json。

## 七处改动与收益

| ID | 位置 | 实际改动 | 读者能多做什么 |
|---|---|---|---|
| B5-A | 05-map-size:15 | 三个区块的括号解释改为“各查一件事”，名字顺序保持 | 根据库里引进谁、符号落哪、哪些段被丢弃选择区块 |
| B5-B | 05-map-size:18 | 用“解释……；再解释……”分开学习目标中的两组现象 | 将data/const归属问题与bin大小问题分开复述 |
| B5-C | 05-map-size:35 | “算清/一目了然”改为占用、大符号、丢弃段与工具对应 | 遇到具体审计问题时定位已有命令；不增加排序或完整占用保证 |
| B5-D | 05-map-size:47 | 保留需求和两条链接，明确查现状与改布局两件事 | 知道为什么要回看分区和段布局，引号内原文未改 |
| B6-A | 06-flash-debug:19 | “常驻 + 连上”改为先让OpenOCD常驻、再用GDB连上 | 读操作流之前知道哪一个等待连接、哪一个连入 |
| B6-B | 06-flash-debug:50 | 保留读RAM命令，指出从左边GDB沿箭头读到右侧地址 | 带着现有命令和目标读图，不先背一串角色名 |
| B6-C | 06-flash-debug:101 | 修正“前缀是命令”的主宾关系，用接收对象对照原例子 | 区分OpenOCD与GDB处理的命令，不涉及断点类型纠正 |

## 双重保护与来源证明

- 实施前15个来源输入SHA、七行逐字原句均未漂移。before和candidate初始副本逐字节等于当时docs，均纯LF。
- before→candidate两章分别实际执行strict prose_guard，均“不可动清单：全部一致”；未用additions模式。
- 候选逐行比较只命中B5四行、B6三行，其余行完全相同。候选与审阅方向逐字一致。
- 落盘后before→最终docs两章再次独立strict guard，全过；最终docs逐字节等于已验candidate，不以两份候选互验冒充落盘验证。
- 七行外完全相同，因此冻结疑点、标题/锚点、代码、表格、include、图/动画、HTML/Vue/:::容器、自测和答案均未改。七行中原行内代码顺序、链接目标、引号内内容与数字事实也保持。
- 本批15个来源中的另外13个输入（8个验证输入与已发布B0–B4）在最终复核中SHA均相同；未编辑测试、runner、CI、策略、阈值或prose baseline。
- 11-02目录42个现存文件的成员与内容SHA最终均与规划开始时相同。用户原有16项未提交工作未触碰。

## 指标旁证

| 章节 | 句数前→后 | 长句占比前→后 | 平均句长前→后 |
|---|---|---|---|
| B5 | 96→96 | 8.3%→8.3% | 32.1→32.2 |
| B6 | 84→85 | 15.5%→15.3% | 40.2→40.0 |

来自原有metrics()只读调用。B5均长略增仍在原门禁内，未为压数字扩大改写或刷新基线；数字不证明文字质量。

## 实际命令结果

- 两章before→candidate strict guard：exit0，全部一致。
- 两章before→docs strict guard：exit0，全部一致。
- node scripts/prose-readability.mjs --check：78章通过，平均长句占比10.1%。
- node scripts/reading-time.mjs --check：78篇均在模型±40%内。
- node scripts/docs-check.mjs：138文件、6类检查通过。
- python mcu-book/build_html.py --check：94章、题图94/94，whole-book HTML contract PASS；产物在程序临时目录，不重建完整PDF。
- bg_33：guide-check PASS→docs-gen成功→VitePress build成功62.72s。保留h/kconfig高亮回退、JSON静动态import与chunk体积告警，未改策略。
- bg_34：配套更新日志后实际运行docs-check（138文件）/guide-check/docs-gen/VitePress build全部成功，最终build49.50s。未复用日志前构建证据；既有告警保持，未改门禁策略。
- task_verify(action=run)本轮实际返回unverified / project-or-git-baseline-unavailable / checks=[]，没有operator通过项，手动检查不冒充配置覆盖。

## 真实预览与交互

bg_33完成后启动本任务preview服务，实际就绪URL为http://localhost:4197/mcu/。两页用真实浏览器打开，不以请求200或DOM存在替代交互。

- 两页全部七处新文均在渲染正文中找到；B5页面4个pre、2个内联svg、4个details，B6为3/2/4。已加载图片失败0。
- 桌面1440×960：B5实际点击size三列目录链接、B6点击链路全图链接，hash均变为目标且标题进入可视区域；两页首个答案均false→true，内容可见。已截图观察B5体积账与B6链路动画、代码及段落。
- 手机390×844：实际展开“本页目录”，B5点击quick win链接，B6点击GDB十命令链接；hash与目标可视性均确认。两页答案分别由关闭变打开且内容可见（桌面已打开的B6先实际关闭，再验证打开）。
- 手机截图观察B5改写35/47与审计动画、B6命令表/改写101与链路动画/改写50。页面document.scrollWidth均390，散文段落不越界。
- 两页长代码块实际内部横向滚动scrollLeft 0→80，再复原0：B5 clientWidth308/scrollWidth543，B6为308/482。代码内部滚动不扩大文档宽度。
- 两页page errors均0，已加载图片失败0。两个本任务tab与preview服务均已关闭。

## 验证过程问题与边界

一次emulate(390×844)后goto导致视口状态丢失，随后observe超时；不同证据（page.viewport=null、innerWidth1422、document宽1422、服务仍ready）说明当时不能计作390px手机验证。重新emulate且不再导航后实际innerWidth=390，并据此完成上述交互与截图。工具行为已上报；未修改站点配置、CSS或弱化检查。

本轮没有执行章内烧录、擦除、调试或固件命令，没有上板、技术事实考证、完整PDF或整站浏览器套件。既有技术疑点按design冻结；页面验证只证明呈现与交互，不证明这些硬件结论。文字效果仍待用户验收。

## 后续发布授权与提交前复核

用户在本地交付后明确要求提交、推送、合并并确认CI全绿，随后确认三笔提交分组（正文、任务归档、日志），并同意发布完成后创建下一批规划任务。这是新的发布授权，取代本文件前述“尚无发布授权”的历史状态；下一批尚未授权实施。

- 发布前fetch后本地HEAD与origin/main均6742ab5546f009acfe5f72022e847689864cb7c5，无开放PR。
- 两章当前SHA仍匹配final-source-evidence.json；13冻结输入、42用户文件均与原证据相同。
- 本轮额外固定214个验证/runner/CI文件SHA，不修改测试、输入或策略。11-02原16项用户工作排除提交。
- 本轮实际重跑两章before→docs strict prose_guard，均“不可动清单：全部一致”；prose78章、reading78篇、docs138文件均通过。
- 本轮task_verify实际unverified / project-or-git-baseline-unavailable / checks=[]，未计通过。
- GitNexus当前仍只有无关clideck（落后11 commits），mcu无索引，未查询或重建无关图。
- 主分支未启用branch protection（查询返回404 Branch not protected），仍主动等待全部PR检查通过才合并，不使用管理员绕过。

远端PR、合并及主分支运行结果在发布完成后以PR评论留存，不能将本段提交前记录当作远端CI成功证明。
