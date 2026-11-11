# 极其精品：传播力 · 可证性能 · 无障碍 · 可信度

## Goal

把「通往单片机之路」从「读者能学」提升到**「值得被看见、可被证明、人人可用、可信可续」**。
前一轮（10-08-premium-polish）已把内容四维（看得懂/找得到/学得下去/有兴趣）做到精品级；
本轮补齐**工程与传播层面**距「极其精品」的四个真实缺口。

## Requirements

### 实测证据（缺口不是推测）

| 缺口 | 证据 |
|---|---|
| 传播力 = 0 | 线上 `https://zhuguang-zfg.github.io/mcu/`：`sitemap.xml` → 404、`robots.txt` → 404；`<head>` 仅 `<title>` + 站点级 description，**无任何 `og:` / `twitter:` / `canonical`** |
| 性能无门禁 | `scripts/measure-site.mjs` 存在但未接入 `quality`/CI，且**无预算阈值** |
| 无障碍无体系 | `prefers-reduced-motion`、111 张图 alt 全覆盖、VitePress 语义默认已达标；缺显式 `:focus-visible`、skip-link、自动审计 |
| 可信度天花板 | 10 个实验 + 2 个综合项目全部 `hardware_status: pending`；README 记「上板验证 0 项」，而项目主打「全程实物实验」 |

### 范围（4 批，可独立验收）

- **A 传播力**：`sitemap.xml` + `robots.txt` + 每页 `og:`/`twitter:` 分享卡 + `canonical` + 站点级分享图（确定性生成，非 AI 生图）+ `seo:check` 闸门。
- **B 可证性能**：纯静态体积预算脚本（JS/CSS raw+gzip+brotli、总体积、最大分块），无需浏览器 → 接入 `quality`/CI。
- **C 无障碍**：主题层 `:focus-visible` 与 skip-link；`a11y:check` 静态审计（lang/alt/按钮可访问名/标题层级/链接文本/landmark）接入 `quality`。
- **D 可信度**：读者侧「如何在真实硬件上验证并回填证据」指南；实验总览展示「X/N 已上板验证」与入口；K5（GD32 规划/统计口径）剩余问题收口。

## Acceptance Criteria

- [x] 每批：本地可验证的闸门与构建全绿；新增脚本配单元测试；`.trellis/spec/docs-site/` 规范同步登记
- [x] A：构建产物含 `sitemap.xml`、`robots.txt`；每页 HTML 含 `og:title`/`og:description`/`og:url`/`og:image`/`twitter:card`/`canonical`
- [x] B：`perf:budget` 超预算即非零退出；当前基线全绿
- [x] C：`a11y:check` 全绿；键盘焦点可见；页面首元素含 skip-link
- [x] D：指南页可达且进 nav/sidebar（受 `nav:check` 保护）；实验总览显示验证进度与入口

## Notes

- **绝不伪造任何硬件验证**；无真板子就不把 `hardware_status` 改成 `verified`。
- 不新增芯片路线；不改动并行会话（`10-07-knowledge-capstone`）的在途文件。
- 不引入重型运行时依赖；分享图生成器保持可复现且产物入库。
