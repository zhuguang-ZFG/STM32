/**
 * 站点身份单一来源：host / base / 仓库 URL / 源码前缀只在这里维护。
 * 所有运行时消费者（config.mts、seo/pages/search/docs-check、measure-site、
 * book-guide 生成器、playwright.config）一律从这里 import，不许再写字面量。
 *
 * 纪律：tests/ 里的预期值必须写字面量 '/STM32/mcu/'，不许 import 本文件——
 * 实现与测试同源会让「改错常量、测试跟着错」变成假绿。
 */
export const HOST = 'https://zhuguang-zfg.github.io'
export const BASE = '/STM32/mcu/'
export const REPO = 'https://github.com/zhuguang-ZFG/STM32'
/** 本项目在合并仓库里的源码子目录：blob/tree/edit 链接都带这层前缀。 */
export const REPO_SUBDIR = 'mcu'

export const SITE_ORIGIN = HOST + BASE

/** 页面相对路径（docs 口径，如 stm32/03-gpio.md）→ 规范绝对 URL。index 归一为目录。 */
export function pageUrl(page) {
  let p = page.replace(/\.md$/, '.html')
  if (p === 'index.html') p = ''
  else p = p.replace(/\/index\.html$/, '/')
  return `${HOST}${BASE}${p}`
}

/** MCU 项目根口径的相对路径（如 code/stm32/00-blink/stm32f407xx.ld）→ blob URL。 */
export function repoBlobUrl(relativePath, ref = 'main') {
  return `${REPO}/blob/${ref}/${REPO_SUBDIR}/${relativePath}`
}

/** 同上 → tree URL（目录用）。 */
export function repoTreeUrl(relativePath, ref = 'main') {
  return `${REPO}/tree/${ref}/${REPO_SUBDIR}/${relativePath}`
}
