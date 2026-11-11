# 合并技术设计

状态：建议方案；需求和验收编号以 [prd.md](prd.md) 为准。

## 1. 维护边界

| 维护面 | 合并后路径 | 规则来源 |
| --- | --- | --- |
| STM32 中文/英文正文 | `docs/`、`docs/en/` | `docs/CONTENT_GUIDE.md` 与原书 spec |
| STM32 示例与实验 | `examples/`、`labs/`、`sim/` | 各目录说明及原 CI |
| STM32 整书 | `stm32-book/` | `BOOK_CLASSIC_CONVERGE_SPECS.md` 等现行叠加规则 |
| MCU 站点/正文 | `mcu/docs/` | `mcu/.trellis/spec/docs-site/` |
| MCU 固件 | `mcu/code/` | MCU firmware-* 层及 `mcu/code/projects.json` |
| MCU 整书 | `mcu/mcu-book/` | MCU book 层；保持 HTML/A4/印前三类产物区分 |
| 两套视频 | `video/` 与 `mcu/video/` | 各自 spec、媒体清单和发布状态 |
| MCU 任务与规范 | `mcu/.trellis/` | 现有 Trellis workflow 与八层 spec |
| 跨仓整合 | 根 `.github/workflows/`、根导航及本计划 | 本计划约束路径、触发和交付，不替代技术内容规范 |

同名文件不做覆盖式合并。根 `README.md` 是双书入口，`mcu/README.md` 是 MCU 子项目入口；`STRUCTURE.md` 补充 `mcu/` 维护边界。需要共享内容时先建立交叉链接；提取公共实现应另立变更，不能在目录迁移中顺带重构。

既有许可文本按原路径保留；搬出的四个 MCU workflow 保留来源记录。检查第三方资产自身的来源说明，不使用根级摘要覆盖资产元数据。这里规定保存与核对机制，不作重新许可。

## 2. Git 与增量迁移

当前使用非 squash 的 subtree 历史：来源 SHA 已在目标祖先链中。保留该方式，不再执行 `subtree add`，也不把来源根直接 merge 到目标根。

实施基线由三部分组成：来源 Git tree、目标 `HEAD:mcu`、目标当前工作区。现有已提交迁移差异为 10 个路径：4 个 MCU 内嵌 workflow 删除并移至根、README、站点 config 及 4 个检查/测量脚本修改。工作区差异独立记录，不能算成来源丢失或全部视为本任务修改。

来源若在基线后新增提交，先记录新 SHA，确认祖先关系，生成按 `mcu/` 映射的三方差异并检查与目标定制的冲突，再决定是否接纳。不能使用目录镜像或“源文件更新所以源胜出”的规则。外部目录内的未跟踪/忽略文件另做清单：可再生依赖重装；不可再生资产逐项迁移并核对 SHA-256。

验收后的默认开发位置为 STM32 仓库的 `mcu/`，不维持自动双向同步。原目录在验收和资产盘点结束前继续保留。

## 3. 路径合同

必须区分以下三个根：

| 根 | 示例 | 解释 |
| --- | --- | --- |
| Git 仓库根 | `D:\Users\STM32` | Git pathspec、根工作流及 artifacts 的路径起点 |
| MCU 项目根 | `D:\Users\STM32\mcu` | npm、MCU 构建器、Trellis 上下文内 `.trellis/...` 的起点 |
| 对外站点根 | `/STM32/mcu/` | 浏览器、canonical、搜索索引和公开资源 URL 的前缀 |

拟增加 MCU 站点身份配置，作为 host、base、仓库 URL 和源码前缀的运行时唯一维护位置，供 VitePress、检查器、生成器和 Playwright 使用。具体文件建议 `mcu/scripts/site-config.mjs`；主题侧通过可被构建器导入的配置或站点配置消费，不在多个组件各写字面量。

测试须保留独立的预期 `/STM32/mcu/`，防止测试和实现一起导入错误值而假通过。对支持任意 base 的函数，继续使用显式参数测试；旧 `/mcu/` 的历史说明与负例不作机械替换。

需迁移的运行时消费者至少包括：`config.mts`、`seo-check.mjs`、`search-check.mjs`、`pages-check.mjs`、`measure-site.mjs`、Playwright 配置、robots、主题仓库入口、导读/下载生成器、CITATION 和 manifest 中仓库身份。`docs-check.mjs` 的新仓自链解析须把 `STM32/blob/<ref>/mcu/...` 映射回 MCU 项目相对路径；保留旧仓历史引用检查的明确规则，不能重复拼接 `mcu/mcu/`。

当前 CITATION 的 URL 已在已有工作区修改中变为新站点，但 `repository-code` 与 manifest 仍需一起审查。不得只改引用文件而放宽校验器。

## 4. Pages 产物合同

构建器仍输出 MCU 站点自己的 `mcu/docs/.vitepress/dist/`。发布时新增站点组装步骤，形成下列上传根（建议目录 `.temp/pages-site/`）：

```text
pages-site/                 -> /STM32/
  index.html               -> 根入口：保留已有站点，或在确认没有根站后生成双书导航
  mcu/
    index.html             -> /STM32/mcu/
    assets/
    book/
    downloads/
    ...其余 MCU 站点产物
```

上传路径必须是 `pages-site/`，不是 `pages-site/mcu/`。仅把 VitePress base 改为 `/STM32/mcu/`，不能替代 artifact 中真实存在的 `mcu/` 层级。

当前部署文件直接上传 `mcu/site`，静态配置没有增加此层级，因此存在挂载不一致风险；本轮没有构建或上线验证该风险。

部署前先对组装后的 `pages-site/mcu` 跑既有页面/搜索检查，再以整个 `pages-site` 模拟挂载在 `/STM32/` 下，做浏览器冒烟，至少验证首页、一个深链、CSS/JS、搜索、动画、导读和下载。检查器目前主要校验 HTML/锚点，不能代替实际资源请求检查。

Pages 保持一个发布入口。根入口或共享组装脚本变化也必须触发重建/发布；不能仅监听 `mcu/**`。若已有根站，组装时纳入其同一候选提交的产物，禁止以 MCU 站点覆盖根站。

旧独立站 `/mcu/` 的兼容入口需要在旧仓部署侧维护；把重定向文件放进新仓不能接管旧站路由。默认先保留旧站，发布验收后再决定更新迁移提示或按路由重定向；要求保留深链和 fragment，禁止提前下线旧站。

## 5. CI 合同

- 根 STM32 书籍和 MCU 质量门分别执行。公共文件变更按受影响范围触发两侧；文档规划文件不应无故触发固件重编。
- MCU `run` 步骤的 cwd 仍为 `mcu`。Action 的 `with.path`、缓存文件路径和本地 reusable workflow 路径按仓库根计算，不能假设继承 `working-directory`。
- 保留现有 `stm32-practical-book`、`stm32-practical-book-en`、`mcu-deep-book` 产物身份，避免同名覆盖；站点 artifact 明确是纯 MCU 产物还是组装后的 Pages 产物。
- 门禁审查要覆盖根书中英测试、MCU quality、浏览器、动画审计、MCU 整书单测/PDF 合同、ARM-host 和 ESP32 矩阵。根 `release-fetch.yml` 当前仅发布 STM32 的四个文件，MCU 发布不应直接塞入并破坏数量断言。
- 路径过滤可能使未涉及的 job 不运行。发布所需 job 不能被“没有运行”冒充成功；实施时明确 affected 集合和最终汇总门，并检查远程 required checks 是否会等待被过滤掉的 workflow。
- Pages 发布依赖 MCU 站点及书籍相关门；若组装涉及根站产物，也必须依赖对应根门。最终发布批准依赖同一候选提交的完整集成验收记录。

## 6. Trellis 与 spec 兼容

近期方案：保留 `mcu/.trellis`，所有 MCU Trellis 命令从 `mcu/` 运行；根级规划留在 `plans/2026-11-11-mcu-merge/`。建议实施时增加根 `AGENTS.md` 的维护面路由，指向两套现行规范及本计划，不复制 MCU workflow 或自动改写框架脚本。

现有 jsonl 内 `.trellis/...` 是 MCU 项目根相对路径，不因 Git 根位于父目录而批量加 `mcu/`。需逐个验证实际消费者的解析基准。Git 命令则显式声明从根执行还是使用 `git -C mcu`。

审查范围包括活动任务上下文、task parent/children、现有会话指针、hooks 和本机绝对路径。可执行的绝对路径需替换或提供兼容配置；历史日志中的旧路径保留为证据。只迁移任务容器不表示任务已经验收；现有 23 项活动任务与历史收口账中的 22 项是不同统计范围，不强行改成同一数量。

未来若需要根 `.trellis` 管理全部包，另立迁移：定义包命名、转换路径、验证任务与会话解析后再切换。此阶段不维护两份可写的规范真源。

## 7. 冲突裁定与回退

| 冲突类型 | 处理规则 |
| --- | --- |
| 已有未提交工作 | 保留原字节与归属，先生成差异；本任务不代替作者接受或提交 |
| 已导入源码与来源后续修改 | 以上次导入 SHA 为共同基线逐项合并，保留迁移定制 |
| 两书正文/固件规则不同 | 按路径分域；不让某本书的文风门或工具链约束跨域生效 |
| URL 与旧证据 | 更新运行时与新输出；历史引用保留并标识，不改历史哈希来伪造一致 |
| 同名站点/书籍产物 | 使用子目录与现有独立名称；禁止覆盖 |

实施按批次形成独立变更。集成失败停在候选分支，修复后重跑受影响检查；已共享提交需要回退时用可审查的 revert，不重写来源历史。发布失败优先重新部署预先保留的上一个有效 artifact，并回读入口。旧站、来源目录和资产备份保留到 AC8 完成；不以递归删除或 hard reset 作为常规回退步骤。
