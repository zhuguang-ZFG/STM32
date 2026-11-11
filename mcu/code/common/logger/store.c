#include "logger.h"
#include <string.h>
static int choose(const uint8_t a[128],const uint8_t b[128]){
    logger_config_t cfg;uint32_t ga=0,gb=0;
    bool va=config_decode(a,&cfg,&ga),vb=config_decode(b,&cfg,&gb);
    if(!va&&!vb)return -1;
    return vb&&(!va||generation_after(gb,ga))?1:0;
}
bool config_slots_load(store_read_fn read,void *user,uint8_t out[128]){
    uint8_t a[128],b[128];
    if(!read(user,0,a,128)||!read(user,128,b,128))return false;
    int latest=choose(a,b);if(latest<0)return false;
    memcpy(out,latest?b:a,128);return true;
}
bool config_slots_save(store_read_fn read,store_write_fn write,void *user,const uint8_t image[128]){
    logger_config_t cfg;uint32_t generation;
    if(!config_decode(image,&cfg,&generation))return false;
    uint8_t a[128],b[128],verify[128],invalid=0;
    if(!read(user,0,a,128)||!read(user,128,b,128))return false;
    int latest=choose(a,b);
    if(latest>=0 && !memcmp(latest?b:a,image,128))return true; /* identical save does not wear EEPROM */
    uint16_t base=latest==0?128:0;
    if(!write(user,base+127,&invalid,1))return false; /* must complete invalidation first */
    for(unsigned i=0;i<127;i+=8){
        size_t n=127-i;if(n>8)n=8;
        if(!write(user,(uint16_t)(base+i),image+i,n))return false;
    }
    if(!read(user,base,verify,128)||memcmp(verify,image,127))return false;
    if(!write(user,base+127,image+127,1))return false;
    if(!read(user,base,verify,128))return false;
    return !memcmp(verify,image,128);
}
