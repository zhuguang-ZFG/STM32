/*
 * alias-violate.c —— 严格别名违规现场（专供 -Wstrict-aliasing 抓人）
 *
 * 本文件的存在意义就是"被警告"。编译它时不开 -Werror，让警告全文亮出来：
 *   gcc -std=c11 -O2 -Wstrict-aliasing -c alias-violate.c
 * probe.sh 负责取证。别在真实固件里这么写——用 memcpy（见 probe.c）。
 */
#include <stdint.h>

/* 违规：用 uint32_t* 解引用 float 对象——不兼容类型互访，严格别名规则管的就是这一刀 */
uint32_t bits_reinterpret(float f)
{
    return *(uint32_t *)&f;
}

/* 对比组：走 char*——char 是别名规则的例外，永远允许 */
uint32_t bits_bytewise(float f)
{
    unsigned char *p = (unsigned char *)&f;
    return (uint32_t)p[0]
         | ((uint32_t)p[1] << 8)
         | ((uint32_t)p[2] << 16)
         | ((uint32_t)p[3] << 24);
}
