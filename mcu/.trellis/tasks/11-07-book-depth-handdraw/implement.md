# 执行计划与审阅门

状态planning；本轮仅规划。不要将表中的未来动作写成已执行。

## 阶段1 本轮规划交付

- [x] 用户同意总任务；manifest101源、814机制标题候选、先修/罗盘/图引用与SHA台账。
- [x] 记录四scout未完成情况，保留partial/read而不伪造审阅覆盖；主代理形成六类代表方案。
- [x] teaching-contract/illustration-plan、24批无重复路由和独立delivery-closure。
- [x] 两研究SVG经原art_guard通过，390浅/深与1440实际render；只设计证明，未集成正文。
- [x] PRD收敛、四任务context校验、固定输入/用户工作最终核验已完成；交用户审阅，不自动start。

## 阶段2 获批首轮（尚未授权）

先task.py start样章子任务，不start总任务冒充实施。读取该章完整源+保护快照，核用户/runner pins。先C2对象与F3候选资格各一个概念：图文一体薄切片、实际运行可见；源码事实不足就先查当前官方来源，不补猜测。

逐处旧文strict中间稿→获审增补稿/图；两阶段独立对源并记录准确增量。图实际出现在站点/离线HTML，原art/布局门+手机桌面浅深真截图，目录答案滚动仍正常；语言/reading/docs/build/book原门，不刷新baseline。样章两概念用户看文字与手绘后再完善六章所有卡。

## 阶段3 样章后全量

样章通过后依batches.json按分部，每批最多6文件、每章全部知识卡；补无标题点/先修缺口，技术纠错先独立审。保留好解释不为改而改。每批用户抽评至少两章，任何未accepted点仍列账，不能进入“全书完工”。附录按专用职责核生成来源。

## 阶段4 工程收口与最终交付

delivery子任务按告警逐个可区分实验修一个因；LSP可用时refs先行，库API用当前文档。新增回归/runner/策略review后需下一用户回合建立baseline，task_verify未覆盖不算通过。工程47含ESP矩阵另验，硬件按目标身份/接线/授权后逐实验留证。

内容/图冻结后重建新HTML/A4/16开、原13门和下载包自证。最后展示白名单提交分组获确认，PR当前head所有checks成功才match-head merge，main同SHA Book/links/Pages和线上烟测。非硬件结果不能代硬件。

## 常用原门（按变更窄验，不无关全跑）

- 原prose_guard strict或明确获审additions；既有守卫不改。
- node scripts/prose-readability.mjs --check；node scripts/reading-time.mjs --check；node scripts/docs-check.mjs。
- node scripts/book-guide/generate.mjs --check && node scripts/gen-progress.mjs && node node_modules/vitepress/bin/vitepress.js build docs。
- python mcu-book/tools/art_guard.py <本批图>；既有anim-audit布局门；python mcu-book/build_html.py --check。
- task_verify(plan/run)：原样报告passed/failed/unverified，缺检查不算成功。
- firmware:check非ESP；ESP使用catalog矩阵set-target/build/size与独立SDKCONFIG。
- 完整build_html --pdf→build_print --html该新HTML→check_pdf原13门→publish_downloads --verify。

## 停止与回退

当前等待具体样章/工程方案批准，不改生产源。两次同动作失败后写被否证假设换证据；权限失败只授权解决。硬件/基线不可达记录阻塞，不删任务、不改状态伪造绿；其他可达工作继续。保留所有用户工作；回退只本批自写内容。
