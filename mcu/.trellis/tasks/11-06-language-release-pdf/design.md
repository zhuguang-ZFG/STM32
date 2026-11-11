# 收尾设计

远端main已fetch到f34a534；现有分支2825cbf是已合并PR12的head。新建分支基于origin/main，保留未提交三章与所有用户工作，不reset/stash。暂存显式白名单：docs/build/00-toolchain.md、01-four-steps.md、02-elf.md，以及11-06-spec-plan-continuation、11-06-language-batch2、当前任务目录。

PDF直接调用build_print.py --out-dir mcu-book/dist/language-release-20261106，独立目录避免覆盖旧交付；重新装配全书，沿用字体与两遍索引。校验实际PDF，必要时只诊断失败不放宽。

gh使用已授权账户，PR成功后匹配head sha合并；后台watch等待真正完成。main推送工作流全部success才宣称发布完成。PDF本地生成与远端CI可独立推进，不下载远端PDF替代。
