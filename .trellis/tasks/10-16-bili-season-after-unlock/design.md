# 设计：权益就绪后的逐条合集写入

本补充由historical-spec-closure规划授权产生；原PRD、17条目标和planning状态不变，尚未执行平台操作。

## 边界与数据

先从原bvid台账形成只读目标清单，记录目标17条的bvid/aid/cid/标题与当前series差异。当前series有18正片，不能自动把第18条加入原范围。合集标题以当前series真源为准；原PRD关于尾空格是历史记录，实际当前值已无尾空格，接入前将差异交审，不手改站内或线上名称。

权益只读season/new_season；HTTP成功、Lv4或错误20082的字面文案都不能代替权益位。权益缺失时只保留阻塞，不换账号、伪造参数或重试create。

## 写入与回读

逐条动作分为候选、授权、已发送、回读确认；创建合集与每条join的许可来自当前对话，不由脚本/旧闸门文件自授。ID、封面URL和section只取平台实际返回。网络结果不明时先查seasons/view，不重新发送重复写入。每条以对应bvid的ugc_season回显为完成，不按标题相似匹配。

## 契约与风险

简介纯文本、封面为线上URL、17条不漏；凭据不进证据或stdout。原任务历史命令路径可能过期，实施时先核实际video/publish工具与只读help，不能直接照跑.temp旧脚本。总任务research/task-cards.md第1项保留逐项AC。
