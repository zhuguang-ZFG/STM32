#include "record.h"
void fault_record_save(volatile fault_record_t *dst, uint32_t mask)
{
    uint8_t b[12]={0};
    write_le32(b,0x57444731UL); b[4]=1; write_le32(b+6,mask);
    write_le16(b+10,protocol_crc(b,10));
    /* Invalidate before update; publish magic last. A reset mid-write yields no valid record. */
    for (unsigned i=0;i<4;i++) dst->bytes[i]=0;
    for (unsigned i=4;i<12;i++) dst->bytes[i]=b[i];
    for (unsigned i=0;i<4;i++) dst->bytes[i]=b[i];
}
bool fault_record_read(const volatile fault_record_t *src, bool warm_watchdog_reset, uint32_t *mask)
{
    if (!src || !mask || !warm_watchdog_reset) return false;
    uint8_t b[12]; for (unsigned i=0;i<12;i++) b[i]=src->bytes[i];
    if (read_le32(b)!=0x57444731UL || b[4]!=1 || b[5]!=0 || read_le16(b+10)!=protocol_crc(b,10)) return false;
    *mask=read_le32(b+6); return true;
}
bool fault_record_take(volatile fault_record_t *src,bool warm,uint32_t *mask)
{
    bool valid=fault_record_read(src,warm,mask);
    if(src)src->bytes[0]=0; /* A later unrelated warm reset must not reuse old evidence. */
    return valid;
}
