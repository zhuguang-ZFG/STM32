# 独立交付收口：前提、验收和权限

这条线保留用户“全部要处理完成”的要求，不被全书内容规划吞掉，也不把历史CI结果当本次新范围的证据。当前用户刚批准的是创建全书升级任务并规划；以下为待审执行设计，不声称已收口。

## 1. 构建告警

| 观察/证据 | 两个候选解释 | 区分实验与完成标准 |
|---|---|---|
| h/kconfig被高亮器回退txt；code-languages.mjs仅ld/gdb/armasm | 缺语言加载/别名，或这些围栏实际意图只是纯文本 | 盘点实际围栏与内容，用当前VitePress/Shiki API文档验证语言支持；优先按真实语法加载/别名，不篡改代码块或隐藏warning。构建无该警告且真实代码页仍可读。 |
| RegisterExplorer.vue同时static gpiofModer和dynamic同JSON | static import为残留无用，或有实际同步使用需保留 | 用可用LSP refs/定义追踪后确认读者，实际寄存器组件切换/字段设值/十六进制读数烟测；只消一个原因，不同时重写加载逻辑。 |
| dist/assets中animations页面普通与lean包约1.2MB | 页面内联全量SVG，或共享库/依赖分包问题 | 按构建manifest和产物测量定位首个大包边界；比较JS传输和真实动画页面。修加载/拆页/延迟渲染的必要原因，不提高chunkSizeWarningLimit、设onwarn吞警告或复制新阈值。 |

涉及库API先取当前文档。每个确认bug记录expected/actual、最小复现、首个偏离边界；保留两个假设，单变量实验。回归旧行为失败/修后通过；新测试与runner输入要review且不自动算operator已验证。

## 2. task_verify覆盖

本轮只读status实际unverified/no-checks-run；之前本地实现run曾基线不可用。当前API只有plan/run/status，没有授权注册或修改operator基线的入口。不能改项目git/测试来伪造它已覆盖。

执行时对实际改动调用plan/run，记录原样reason、changes、checks。若仍无基线，交operator一个精确请求：为D:/Users/mcu和该用户回合建立合法项目/git baseline并提供配置检查；在其授权且可操作后再run。只读源码与repo中没有检索到该工具配置不等于整个宿主无配置。不访问未授权omp全局设置，不自行建第二套operator配置。手动/CI证据单列，未覆盖继续unverified。

## 3. 固件

现有code/projects.json47工程：host-probe22、host-make1、arm-make14、esp-idf10。scripts/check-firmware.mjs明确覆盖非ESP；最后一句也明确硬件另验。先核清单与固定版本/工具，执行原firmware:check（含向量/场景复现/probe），ESP另按现有catalog生成normal/faults矩阵逐项build size，核target=esp32s3。不得拿ARM/host成功当47全部构建成功，或拿旧build缓存当新证据。

本机PATH已发现Arm gcc/nm、mingw32-make、OpenOCD、idf.py、cmake、ninja；这只是可执行文件可见，不证明版本、SDK、依赖与全工程实际通过。现有MAKE环境变量接口已足够，不把本机路径写死进runner。

## 4. 上板

本轮Get-CimInstance Win32_SerialPort只见Bluetooth COM4/COM5；Get-PnpDevice名称过滤没有识别出ST-Link/J-Link/DAP或目标板。它不排除未被识别的USB设备，不能据此虚构“板卡已连接”。未进行串口读写、reset、erase或flash。

上板前须有具体目标序列号/型号、探针、原理图接线和可观察仪器；由用户确认可写目标后才能烧录/复位。实验E01–E08与J1/J2各按现有章节验证，不把SIM或编译当HIL。日志/波形/照片和预期-实际逐项对照，尤其E04四臂、低功耗电流、I2C/音频需真实证据。设备/仪器不到位标blocked并给可操作清单，先完成其余可达工作，绝不把hardware_status改verified制造完成。

## 5. 完整PDF和下载物

依赖最终内容与图冻结。先build_html.py --pdf产生新离线HTML+A4，再build_print.py --html该新HTML产生16开PDF，保留两遍索引和widow guard；不使用sample/no-index/no-widow-guard交付。check_pdf.py只校印前目标13项，不拿A4冒充。

核B7和各新增图实际进入HTML/两类PDF的段落，记录页数、文件SHA、目录/索引/图像裁切抽验、原印前13门。publish_downloads.py打包并--verify；Linux GNU sha256sum独立验证。构建产物不手改，生成器不为躲失败调整布局阈值。

## 6. 发布

先按任务白名单展示提交分组，排除11-02用户文件及无关任务；取得一次性确认后分支/PR，等待当前head所有检查实际SUCCESS再精确匹配merge；不admin bypass、不force、不no-verify。合并后同SHA Book/links/Pages均成功，线上图文/目录/答案/手机再烟测，记录PR与run链接。旧PR16绿不覆盖新内容。

## 7. 依赖与阻塞

内容样章→分批内容与图验收→最终PDF/发布；告警可独立修，但最终验证以合并内容为准。operator基线与硬件是外部前提，不阻止来源审查/图文工作；它们未满足时全书内容可局部验收，但“全部交付完成”必须仍报告blocked，不隐去。
