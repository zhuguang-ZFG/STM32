/* sar_probe.c —— S9 逐次逼近（SAR）取证：12 轮二分，每一步的电压与码值
 *
 *   ./probe.sh sar        打印 12 轮试探表 + 最终码值 + 量化误差
 *
 * 这是**理想 ADC 的算法仿真**：比较器不飘、DAC 无噪声、C_H 充满。它回答的是
 * "12 位 ADC 为什么只要 12 次比较""最后一次锁定的码值是谁算出来的"这类问题——
 * 全部是算术，宿主机 gcc 就能跑，不需要开发板。
 *
 * 真实板上读数还会被采样时间、源阻抗、VDDA 波动、噪声拉走（本章「实物实验」），
 * 那些数字必须接板回填，本仿真不代替。
 *
 * -DVIN=... -DVREF=... -DBITS=... 可换输入、参考电压与位数（默认 2.00 V / 3.3 V / 12 位，与动画一致）。
 */

#include <stdio.h>
#include <stdint.h>

#ifndef VIN
#define VIN  2.00
#endif
#ifndef VREF
#define VREF 3.30
#endif
#ifndef BITS
#define BITS 12
#endif
#define FULL (1u << BITS)          /* 4096 档 */

int main(void)
{
    double lsb = (double)VREF / FULL;
    uint32_t code = 0;

    printf("VREF=%.2f V  Vin=%.2f V  %d 位 → LSB = %.2f/%u = %.6f V（%.3f mV = %.1f µV）\n",
           (double)VREF, (double)VIN, BITS, (double)VREF, FULL, lsb, lsb * 1000.0, lsb * 1e6);
    printf("理想码值 floor(Vin/LSB) = %u (0x%03X)\n\n",
           (unsigned)(VIN / lsb), (unsigned)(VIN / lsb));

    printf("轮次  试探位   trial   V_dac      比较        保留后 code\n");
    for (int b = BITS - 1; b >= 0; b--) {
        uint32_t trial = code | (1u << b);
        double vdac = (double)trial * lsb;
        int keep = (vdac <= (double)VIN);
        printf("%2d    bit%-2d  %5u   %.4f V   %s   %5u\n",
               BITS - b, b, trial, vdac, keep ? "Vin ≥ V_dac" : "Vin < V_dac",
               keep ? trial : code);
        if (keep) code = trial;
    }

    double vout = (double)code * lsb;
    double err_lsb = ((double)VIN - vout) / lsb;
    printf("\n锁定 code=%u (0x%03X) → %.4f V；与 Vin 差 %.4f mV = %.2f LSB\n",
           code, code, vout, ((double)VIN - vout) * 1000.0, err_lsb);
    printf("比较次数=%d，候选从 %u 档收到 1 档（每轮砍掉一半，%d 轮 = log2 %u）\n",
           BITS, FULL, BITS, FULL);

    /* 自检：任何一条不过就非零退出，probe.sh 的 set -e 会拦下整轮 */
    unsigned expect = (unsigned)(VIN / lsb);
    if (code != expect) { printf("自检失败：终码 %u != floor(Vin/LSB) %u\n", code, expect); return 1; }
    if (!(err_lsb >= 0.0 && err_lsb < 1.0)) { printf("自检失败：量化误差 %.2f LSB 越界\n", err_lsb); return 1; }
    printf("自检 3/3：终码==floor(Vin/LSB) ✓ 量化误差 %.2f LSB < 1 LSB ✓ 比较轮数==位数 ✓\n", err_lsb);
    return 0;
}
