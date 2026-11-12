#include "encoder.h"

bool enc_delta(uint32_t now, uint32_t prev, uint32_t width, int32_t *out)
{
    if (out == 0 || width < 2u || width > 32u) return false;

    const uint64_t mask = (width >= 32u) ? 0xFFFFFFFFull : ((1ull << width) - 1ull);
    const uint64_t half = 1ull << (width - 1u);

    uint64_t diff = ((uint64_t)now - (uint64_t)prev) & mask;

    if (diff == half) {
        /* 恰好半模：位移恰为 ±half 无法区分，判不可消歧（design §6）。 */
        *out = 0;
        return false;
    }
    if (diff < half) {
        *out = (int32_t)diff;                 /* 正向小幅 */
    } else {
        *out = (int32_t)(diff - (uint64_t)(1ull << width));  /* 负向：模差转负 */
    }
    /* 注意：diff > half 时 diff-(1<<width) 在 (-half, 0) 内，int32 安全 */
    return true;
}
