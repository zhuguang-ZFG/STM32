---
title: 整书离线版
description: 94 章成书：单文件 HTML（动画即播）与 16 开印前 PDF（带页码目录、索引、版权页），随站点发布，与在线内容同源同契约。
---

# 整书离线版：把 94 章装订成一本书

> 🎯 网页适合跳读，书适合通读。这一页是整书的入口：同一份 94 章正文，装订成 11 个分部 + 7 份附录的单文件 HTML 与 16 开印前 PDF——断网可读、打印不丢内容，与在线站点同一份数据源。

<a href="../book-guide/index.html" target="_self">打开精排导读</a>：宽屏单页版，保留本页完整内容，支持目录跳转。

## 两个产物

| 产物 | 适合 | 特性 |
|---|---|---|
| [📖 HTML 版](https://zhuguang-zfg.github.io/mcu/book/mcu-deep-book.html) | 屏幕通读 | 单文件约 6 MB，所有图片内嵌，**断网可读**；181 张机制动画与架构图随文呈现（动画打开即播）；每章开头有「本章罗盘」，章末自测答案集中在附录 C |
| [📄 PDF 版](https://zhuguang-zfg.github.io/mcu/book/mcu-deep-book-print.pdf) | 打印 / 平板批注 | **16 开 185×260 mm**（非 A4），衬线正文 + 黑体标题 + 等宽代码，全部真字体嵌入；带页码的纸面目录、版权页、术语索引、勘误与贡献页；正文页码从 1 起，末页 N/N |

两个文件都由 CI 在每次 push 时从仓库源文档重新构建并随站点发布。书没有"过期副本"，永远是 main 的快照。

## 这本书和站点是什么关系

- **同一份正文**：94 章 markdown 一字不改，站点读它、书也读它；站点方言（提示容器、测验、实验信息卡、视频与交互计算器）在书里被替换为离线等价物。
- **同一份罗盘**：每章页顶的「本章罗盘」（问题 / 交付 / 边界 / 依据锚点）与整书共用 [mcu-book/manifest.json](https://github.com/zhuguang-ZFG/mcu/blob/main/mcu-book/manifest.json)，站点展示与成书内容天然同源。
- **七份附录**：A 工程深读（从 IDLE 中断到帧协议的五个契约）· B 47 个配套工程索引 · C 自测参考答案 · D 术语速查 · E 来源注册表（75 项冻结来源）· F 常见问题 · G 开源项目与社区地图。
- **同一套纪律**：凡是没接仪器量过的现象，书里与站点一样标「待上板实测」；构建契约保证章节、罗盘、测验、工程索引四向对账，缺一个就出版失败。

## 本地构建

```bash
npm run book:check      # 临时目录验证整书契约
npm run book:pdf        # 产出 mcu-book/dist/ 下的 HTML 与 PDF（需本机 Chrome/Edge）
```

构建器、manifest 与七份附录的维护说明见 [mcu-book/README](https://github.com/zhuguang-ZFG/mcu/blob/main/mcu-book/README.md)。
## 参与校对与贡献

- **勘误**：到 [仓库 Issues](https://github.com/zhuguang-ZFG/mcu/issues) 提交，注明章节号（如 S7）、原文一句、建议改法与出处；书内「勘误与贡献」页也是同一个入口。
- **校对**：正文错别字、事实错误、失效链接都欢迎提 PR；改动只落在 `docs/` 正文或 `mcu-book/` 书稿工艺层，两端同源构建。
- **翻译**：先开 Issue 讨论目标语言与范围，避免与正文冻结节奏冲突。
- **参与约定**：见仓库 `CONTRIBUTING.md`；书稿排版与印前工艺的讨论见 `mcu-book/README.md`。

## 版本口径

当前 **v1.0.0**（manifest `version`，2026-10-23 冻结）。书的版本跟着 manifest 走：新增章节需同步登记分部与罗盘，漏登会被构建契约拦下。

## 你做到了

- 知道书在哪、为什么它不会过期（CI 随 push 重出）；
- 通读时有了页码与书签，引用章节可以落到"第几部第几章"而不是一个 URL；
- 想改书时知道唯一入口：改 `docs/` 正文或 `mcu-book/`，两端一起变。
