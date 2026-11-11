# 执行计划：B站17条合集

状态planning；当前仅补规划，未获平台写入许可。

1. 核账号与原17个bvid台账，仅只读；与当前18正片比较，明确第18条归属。
2. 只读查season/new_season，任一true才进入候选创建；false记录权限阻塞，不调用create。
3. 交用户看标题/简介/封面/目标清单，获取创建及每条join的具体许可后才task.py start并执行。
4. 查实际工具help/参数；合集创建后读取真实season/section，逐条resolve→join→view.ugc_season回读。一次只处理一条，结果不明先查不重发。
5. 窄验：每条bvid回显同合集id；seasons state=0，17项无漏重；简介无Markdown、封面线上URL。失败两次换证据，权限只合法解决。
6. task_verify分类；保存ID/日期/动作与非敏感回读，用户接受后另审归档/提交，不自动执行。
