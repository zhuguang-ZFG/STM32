# 思考导引：在本仓库动手之前

本仓库的"层"不是 Web 前后端，而是：**内容（docs/）↔ 示例代码（code/）↔ 整书工艺（mcu-book/）↔ 成片（video/）↔ 真实硬件**。
跨层问题集中在这几者的接口上。

## 动手前自问清单

### 改章节内容时

- [ ] 新增页面进 sidebar 了吗？进本板块 index 路线表了吗？（三处同步，见 [structure.md](../docs-site/structure.md)）
- [ ] 页面里引用的 code/ 路径真实存在吗？
- [ ] 每个寄存器地址/引脚号有出处吗？没核实的写"以手册为准"了吗？
- [ ] 四件套（配置/引脚/库解析/代码分析）在小节结构表里落位了吗？
- [ ] 改的是正文而不是书稿工艺？整书装配规则见 [book/build-contract.md](../book/build-contract.md)。

### 改示例代码时

- [ ] 对应章节页需要同步改吗？（代码变了，"代码分析"小节可能失真）
- [ ] 编译验证跑了吗（make / idf.py build）？无板时标"待上板实测"了吗？
- [ ] 事实与 [firmware-stm32](../firmware-stm32/index.md) / [firmware-esp32](../firmware-esp32/index.md) 的已核实清单冲突吗？
- [ ] 改的是共用代码/协议吗？先读 [firmware-common](../firmware-common/index.md)，C 与 Python 两侧要同时改。
- [ ] 改的是 RTOS 内核/场景吗？先读 [firmware-rtos](../firmware-rtos/index.md)，注意 FreeRTOS/RT-Thread/IDF 三份内核不同源。
- [ ] 改的是 GD32 吗？先读 [firmware-gd32](../firmware-gd32/index.md)，F4 工程与 VF 文档线不能混。

### 改成片版式（video/）时

- [ ] 判据是**截图**还是分数？填充比这类面积分数能靠"把内容拆开"刷高，见 [video/layout-contract.md](../video/layout-contract.md) §5。
- [ ] 改前存了一份 `video:check` 输出、改后 `diff` 过了吗？旧集页头 DOM 必须逐字节不变。
- [ ] 新加的审计判据，造过一次故意的失败抓到它了吗？
- [ ] 有没有对已发布的集跑 `video:build`（会重渲整集）？已发布集只应跑 `video:check` / `video:cover` / `video:pack`。
- [ ] 单文件测试用的是 `node --test video/tests/<file>.test.mjs` 吗？`npm run video:test -- <file>` 会跑全套。

### 改整书/印刷时

- [ ] 先分清产物：离线 HTML/A4（`build_html.py`）≠ 16 开印前 PDF（`build_print.py`）≠ 下载包（`publish_downloads.py`）。
- [ ] 改 manifest 后，章节文件、`chapter_guides`、`sources`、附录是否仍一一对应？
- [ ] 改印前版式后，跑过 `book:pdf` + `book:pdfcheck` 吗？`--sample` 不能替代全书。
- [ ] 题图是否仍是纯矢量？滤镜会在印前被光栅化。

### 改站点配置/主题时

- [ ] `ignoreDeadLinks` 仍是 false 吗？
- [ ] `npm run docs:build` 零错误吗？
- [ ] 新增 public 资源被至少一个页面引用吗？（孤儿资源不进仓库）

## 常见跨层翻车史（本仓库真实教训）

1. **相对链接深度错**：rtos 子目录跨板块链接写 `../` 应为 `../../`——死链检查兜住（2026-10 奠基批次）。
2. **模板占位图片被 Vite 当 import 解析**：示例图片路径要写进代码块，不能裸放 `<img>`/`![]()`。
3. **子代理读大文件被压缩成图片**：长中文设计文档让子代理用 `:raw` 分段读，或直接把所需内容写进任务书——15 分钟时限内"读文档"能吃掉全部预算（2026-10 骨架分派失败教训：worker 切片 ≤5 页/个，上下文内联优先）。
4. **A4 当印前**：CI 先 `build_html.py --pdf` 再跑无参数 `check_pdf.py`，目标文件不是同一个（F01）。规范只登记矛盾，不把它当已修复。
5. **USE_MUTEX 复用场景目录**：FreeRTOS 的 `build/scene-6` 不带互斥量后缀，手动切换可能复用旧对象（F02，未证实）。构建互斥量版用 `-B` 或清目录。

## 规范细目

- [docs-site/](../docs-site/index.md)：站点结构、内容、动画、架构图、导读、质量合同
- [book/](../book/index.md)：整书装配、A4、16 开印前 PDF、下载包
- [firmware-common/](../firmware-common/index.md)：可靠性协议、日志、取证脚本
- [firmware-stm32/](../firmware-stm32/index.md)：寄存器级工程纪律
- [firmware-esp32/](../firmware-esp32/index.md)：IDF 工程纪律
- [firmware-rtos/](../firmware-rtos/index.md)：FreeRTOS / RT-Thread 移植与场景
- [firmware-gd32/](../firmware-gd32/index.md)：GD32F4 工程与 VF 文档边界
- [video/](../video/index.md)：版式、v2 schema、封面与发布包

跨层冲突先回到唯一维护位置；同一事实不在两层各写一份。
