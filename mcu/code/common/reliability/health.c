#include "health.h"
#include <string.h>
bool health_init(health_t *h, uint32_t required, const uint32_t deadlines[8], uint32_t grace, uint32_t now)
{
    if (!h) return false;
    memset(h,0,sizeof(*h));
    if (!deadlines || !required || (required&~255UL) || grace>=0x80000000UL) return false;
    for (unsigned i=0;i<8;i++)
        if ((required&(1UL<<i)) && (!deadlines[i] || deadlines[i]>=0x80000000UL)) return false;
    h->required_mask=required; memcpy(h->deadline_ms,deadlines,sizeof(h->deadline_ms));
    h->grace_ms=grace; h->start_ms=now; h->grace_active=grace!=0; h->valid=true;
    return true;
}
bool health_progress(health_t *h, uint8_t id, uint32_t now)
{
    if (!h || !h->valid || id>=8 || !(h->required_mask&(1UL<<id))) return false;
    h->last_ms[id]=now; h->seen_mask|=1UL<<id;
    return true;
}
health_result_t health_evaluate(health_t *h, uint32_t now)
{
    health_result_t out={false,false,false,0};
    if (!h || !h->valid) return out;
    out.config_valid=true;
    if (h->grace_active && ((h->seen_mask&h->required_mask)==h->required_mask ||
        (uint32_t)(now-h->start_ms)>=h->grace_ms)) h->grace_active=false;
    out.in_grace=h->grace_active;
    if (out.in_grace) { out.may_feed=true; return out; }
    for (unsigned i=0;i<8;i++) {
        uint32_t bit=1UL<<i;
        if ((h->required_mask&bit) && (!(h->seen_mask&bit) ||
            (uint32_t)(now-h->last_ms[i])>=h->deadline_ms[i])) out.overdue_mask|=bit;
    }
    out.may_feed=out.overdue_mask==0;
    return out;
}
bool health_supervise(health_supervisor_t *s, health_result_t result)
{
    if (!s) return false;
    if (!result.may_feed && !s->restart_latched) {
        s->restart_latched=true; s->first_overdue=result.overdue_mask;
    }
    return !s->restart_latched && result.may_feed;
}
