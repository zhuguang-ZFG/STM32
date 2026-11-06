# 发布 B0–B2 与本地印前 PDF

## 目标
用户明确授权提交推送B0/B1/B2，等CI全绿合并、确认main部署，并生成完整本地16开PDF。用户随后批准按该固定范围创建收尾任务。

## 约束
只提交三章散文及相关任务证据；保护11-02用户产物。禁止调门禁、改测试runner策略或prose基线；权限失败不绕过。PDF须重新装配当前正文，不使用旧HTML、不用sample/no-index/no-widow-guard。

## 验收
1. 精确PR head全部必需job成功，无失败/跳过冒充通过。
2. 合并后精确main提交Book、Pages及外链工作流成功。
3. 本地完整185×260mm印前PDF，check_pdf全部13项通过，给出路径/页数/摘要，并核对含新正文。
4. 实际检查与operator unverified分开报告；不提交PDF大文件。
