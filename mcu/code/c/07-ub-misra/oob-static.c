/*
 * oob-static.c —— 编译期就能看穿的越界与未初始化（专供 -Wall 现场抓人）
 *
 * 这些写法在编译器眼里"证据确凿"：常量下标越界、返回未初始化自动变量。
 * 现实里翻车的版本往往下标来自变量——但只要编译器能推出来，它就一定喊。
 * 编译命令由 probe.sh 负责取证，不开 -Werror，让警告全文亮出来。
 */
static int table[4];

int write_oob(void)
{
    table[7] = 1;      /* 常量下标越界：-Warray-bounds 一抓一个准 */
    return table[0];
}

int read_uninit(void)
{
    int x;             /* 未初始化自动变量，直接读——UB */
    return x + 1;
}
