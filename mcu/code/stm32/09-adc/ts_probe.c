/* ts_probe.c —— S9 采样时间 vs 源阻抗：RC 充电推导 + 8 档 SMP 选择
 *
 *   sh probe.sh ts     打印 4 个源阻抗下的最少采样周期数与选中档位
 *
 * 推导（一阶 RC，纯算术可复算，不需要开发板）：
 *   采样保持电容 C_ADC 经 (R_s + R_ADC) 充电，时间常数 τ = (R_s + R_ADC)·C_ADC；
 *   要沉到半 LSB（N 位）以内：e^(-t/τ) < 2^-(N+1)  →  t > (N+1)·ln2·τ ≈ 9.01·τ（N=12）；
 *   换算成 ADC 时钟周期数：cycles > 9.01·τ·f_ADC。
 *
 * 芯片相关常数 R_ADC / C_ADC 是**假设值**（真实值以 datasheet "ADC characteristics"
 * 表为准，本轮未取到表正文）；8 档可选采样时间 {3,15,28,56,84,112,144,480} 则来自
 * ST 官方头文件（章节对照表给出 file:line）。换假设：-DRADC= -DCADC= -DFADC= -DBITS=。
 */

#include <stdio.h>
#include <math.h>

#ifndef RADC
#define RADC 2000.0      /* Ω，假设值——以 datasheet 为准 */
#endif
#ifndef CADC
#define CADC 4e-12       /* F，假设值——以 datasheet 为准 */
#endif
#ifndef FADC
#define FADC 21e6        /* Hz：PCLK2 84 MHz 经 ADCPRE /4（时钟树见 S2，/4 档位见 HAL 头） */
#endif
#ifndef BITS
#define BITS 12
#endif

/* F4 ADC 的 8 档采样时间（周期数），ST HAL 头文件 stm32f4xx_hal_adc.h 可证 */
static const int SMP[8] = { 3, 15, 28, 56, 84, 112, 144, 480 };

int main(void)
{
    static const double RS_TAB[] = { 1e3, 10e3, 50e3, 100e3 };
    const double k = (BITS + 1) * log(2.0);            /* 9.0117 */
    int pass = 0, total = 0;

    printf("假设常数：R_ADC=%.0f Ω、C_ADC=%.0f pF、f_ADC=%.0f MHz（PCLK2/4）——R_ADC/C_ADC 以 datasheet 为准\n",
           RADC, CADC * 1e12, FADC / 1e6);
    printf("沉降条件：e^(-t/τ) < 2^-%d（半 LSB）→ t > %.2f·τ，τ=(R_s+R_ADC)·C_ADC\n\n",
           BITS + 1, k);
    printf("源阻抗 R_s      τ       最少周期   选中档   该档残差      若只给 3 拍\n");

    for (unsigned i = 0; i < sizeof(RS_TAB) / sizeof(RS_TAB[0]); i++) {
        double rs   = RS_TAB[i];
        double tau  = (rs + RADC) * CADC;
        double need = k * tau * FADC;                  /* 最少 ADC 周期数 */
        double res3 = exp(-3.0 / FADC / tau) * (1u << BITS);
        int pick = -1;
        for (int j = 0; j < 8; j++)
            if (SMP[j] >= need) { pick = SMP[j]; break; }

        total++;
        if (pick < 0) {
            printf("%8.0f Ω  %6.0f ns  %8.1f   超出 480 档——降 f_ADC 或降源阻抗\n",
                   rs, tau * 1e9, need);
            continue;                                  /* 这一行自检不过 */
        }
        double resp = exp(-(double)pick / FADC / tau) * (1u << BITS);
        printf("%8.0f Ω  %6.0f ns  %8.1f   %3d 拍   %7.4f LSB   %8.1f LSB\n",
               rs, tau * 1e9, need, pick, resp, res3);
        if ((double)pick >= need && resp < 0.5) pass++;
    }

    printf("\n自检：选中档 ≥ 最少周期 且 该档沉降残差 < 0.5 LSB：%d/%d\n", pass, total);
    if (pass != total) return 1;
    printf("== 自检通过 %d/%d ==\n", pass, total);
    return 0;
}
