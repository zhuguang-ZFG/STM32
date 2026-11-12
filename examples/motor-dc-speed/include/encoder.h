/* 编码器计数差分（design §6，H01）。
 * 模 2^w 差分恢复有符号增量；恰好半模判为不可消歧。
 * 一个采样间隔内绝对位移必须严格小于 2^(w-1)（最大速度约束，P2 核验）。
 */
#ifndef MOTOR_ENCODER_H
#define MOTOR_ENCODER_H

#include <stdint.h>
#include <stdbool.h>

/* 计算 (now - prev) mod 2^width 的有符号值。
 * width ∈ [2,32]。返回是否可消歧；不可消歧（恰好半模）时 *out=0。
 * 实现不依赖超范围强转（用足够宽的无符号运算）。
 */
bool enc_delta(uint32_t now, uint32_t prev, uint32_t width, int32_t *out);

#define ENC_AMBIGUOUS_HALF_TURN INT32_MIN  /* 内部哨兵，不返回给调用方 */

#endif
