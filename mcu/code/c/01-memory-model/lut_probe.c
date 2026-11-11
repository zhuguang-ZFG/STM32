/* lut_probe.c —— const 经济学对照实验（C1 章）
 *
 * 同一个 256 字节的查找表，只差一个 const：
 *   ./probe.sh lut        跑 rw 与 ro 两次构建，把 size/nm/readelf 三张对照摆出来
 *
 * -DLUT_CONST 决定这张表走哪条路。其余源码完全一致。
 */

#include <stdint.h>

#ifdef LUT_CONST
const uint8_t lut[256] = {1, 2, 3};   /* 只读 → 留在 Flash，RAM 一分钱不花 */
#else
uint8_t lut[256] = {1, 2, 3};         /* 可写 → Flash 存初值，RAM 再存一份活的 */
#endif

int get(int i)
{
    return lut[i & 255];
}

int main(void)
{
    return get(1);
}
