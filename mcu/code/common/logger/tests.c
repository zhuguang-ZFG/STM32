#include "logger.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
typedef struct {uint8_t mem[256];int budget;unsigned writes;} disk_t;
static bool rd(void *u,uint16_t at,uint8_t *p,size_t n){disk_t *d=u;if(at+n>256)return false;memcpy(p,d->mem+at,n);return true;}
static bool wr(void *u,uint16_t at,const uint8_t *p,size_t n){
    disk_t *d=u;assert(at+n<=256);assert(at/8==(at+n-1)/8);
    d->writes++;
    for(size_t i=0;i<n;i++){if(d->budget==0)return false;if(d->budget>0)--d->budget;d->mem[at+i]=p[i];}
    return true;
}
int main(void){
    uint8_t old[128],next[128],loaded[128];logger_config_t cfg={100,2},result;uint32_t gen;
    config_encode(old,cfg,UINT32_MAX);config_encode(next,(logger_config_t){200,0},1);
    assert(config_decode(old,&result,&gen)&&gen==UINT32_MAX);
    disk_t original={.budget=-1};memset(original.mem,0xff,256);memcpy(original.mem,old,128);
    for(int cut=0;cut<=130;cut++){
        disk_t d=original;d.budget=cut;
        config_slots_save(rd,wr,&d,next);
        assert(config_slots_load(rd,&d,loaded));assert(!memcmp(loaded,old,128)||!memcmp(loaded,next,128));
    }
    disk_t d=original;assert(config_slots_save(rd,wr,&d,next));assert(config_slots_load(rd,&d,loaded)&&!memcmp(loaded,next,128));
    unsigned writes=d.writes;assert(config_slots_save(rd,wr,&d,next)&&writes==d.writes);
    for(unsigned i=0;i<128;i++){loaded[i]^=1;assert(!config_decode(loaded,&result,&gen));loaded[i]^=1;}
    logger_t l;logger_init(&l,1,old);frame_t out;
    int32_t raw[6]={100};logger_sample(&l,raw,1,99,UINT32_MAX);assert(logger_pop(&l,&out));
    assert(out.length==64&&out.payload[12]==1&&read_le32(out.payload+16)==100&&read_le32(out.payload+40)==100);
    raw[0]=200;logger_sample(&l,raw,1,199,UINT32_MAX);assert(logger_pop(&l,&out)&&read_le32(out.payload+40)==125);
    logger_sample(&l,raw,0,299,UINT32_MAX);assert(logger_pop(&l,&out)&&out.payload[13]==0&&l.sensor_errors==1);
    raw[0]=300;logger_sample(&l,raw,1,399,UINT32_MAX);assert(logger_pop(&l,&out)&&read_le32(out.payload+40)==300);
    for(unsigned i=0;i<20;i++)logger_sample(&l,raw,1,500+i,UINT32_MAX);
    assert(l.count==16&&l.dropped==4);
    frame_t req={.type=4};assert(logger_command(&l,&req,&out));logger_sample(&l,raw,1,600,UINT32_MAX);assert(l.count==0);
    req=(frame_t){.type=5,.length=4,.payload={1,200,0,0}};assert(logger_command(&l,&req,&out)&&!out.payload[0]&&l.generation==1);
    assert(logger_command(&l,&req,&out)&&l.generation==1); /* same SET idempotent */
    req.payload[1]=99;assert(logger_command(&l,&req,&out)&&out.payload[0]==2&&l.config.period_ms==200);
    out=(frame_t){.type=0x82,.length=25};logger_extend(&l,&out);assert(out.length==64);
    out=(frame_t){.type=0x81,.length=5};logger_extend(&l,&out);assert(out.length<=64);
    logger_init(&l,2,NULL);raw[0]=INT32_MIN;logger_sample(&l,raw,63,0,1);raw[0]=INT32_MAX;logger_sample(&l,raw,63,100,1);
    assert(l.count==2); /* UBSan checks wide filter intermediate */
    puts("logger framing/filter/backpressure and every EEPROM write-cut recovery passed");
    return 0;
}
