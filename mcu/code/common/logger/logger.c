#include "logger.h"
#include <string.h>
bool logger_config_valid(logger_config_t c){return c.period_ms>=100&&c.period_ms<=1000&&c.period_ms%10==0&&c.filter_shift<=6;}
bool generation_after(uint32_t a,uint32_t b){return a!=b && (uint32_t)(a-b)<0x80000000UL;}
void config_encode(uint8_t out[128],logger_config_t cfg,uint32_t generation){
    memset(out,0,128);memcpy(out,"LOG1",4);out[4]=1;write_le16(out+5,cfg.period_ms);out[7]=cfg.filter_shift;
    write_le32(out+8,generation);write_le16(out+125,protocol_crc(out,125));out[127]=0xa5;
}
bool config_decode(const uint8_t in[128],logger_config_t *cfg,uint32_t *generation){
    if(!in||memcmp(in,"LOG1",4)||in[4]!=1||in[127]!=0xa5||read_le16(in+125)!=protocol_crc(in,125))return false;
    logger_config_t c={read_le16(in+5),in[7]};
    if(!logger_config_valid(c)||!read_le32(in+8))return false;
    *cfg=c;*generation=read_le32(in+8);return true;
}
void logger_init(logger_t *l,uint8_t sensor,const uint8_t *image){
    memset(l,0,sizeof(*l));l->sensor_type=sensor;l->config=(logger_config_t){100,2};l->generation=1;l->running=true;
    if(config_decode(image,&l->config,&l->generation))l->saved_generation=l->generation;
}
void logger_sample(logger_t *l,const int32_t raw[6],uint8_t valid,uint32_t timestamp,uint32_t generation){
    if(!l->running)return;
    if(generation!=l->generation){l->dropped=sat_add(l->dropped,1);return;}
    frame_t f={.type=0x10,.length=64,.sequence=(uint16_t)l->sequence};
    write_le32(f.payload,l->sequence++);write_le32(f.payload+4,timestamp);write_le32(f.payload+8,generation);
    valid &= l->sensor_type==1?1U:63U;f.payload[12]=l->sensor_type;f.payload[13]=valid;
    if(valid!=(l->sensor_type==1?1U:63U)){l->sensor_errors=sat_add(l->sensor_errors,1);write_le16(f.payload+14,1);}
    for(unsigned i=0;i<6;i++){
        uint8_t bit=(uint8_t)(1U<<i);
        if(valid&bit){
            if(!(l->filter_valid&bit)||!l->config.filter_shift)l->filtered[i]=raw[i];
            else l->filtered[i]+=(int32_t)(((int64_t)raw[i]-l->filtered[i])/(1UL<<l->config.filter_shift));
            l->filter_valid|=bit;
            write_le32(f.payload+16+4*i,(uint32_t)raw[i]);
            write_le32(f.payload+40+4*i,(uint32_t)l->filtered[i]);
        }else l->filter_valid&=(uint8_t)~bit;
    }
    if(l->count==LOGGER_SLOTS){l->dropped=sat_add(l->dropped,1);return;}
    l->samples[(l->head+l->count)%LOGGER_SLOTS]=f;++l->count;if(l->count>l->high_water)l->high_water=l->count;
}
bool logger_pop(logger_t *l,frame_t *out){if(!l->count)return false;*out=l->samples[l->head];l->head=(uint8_t)((l->head+1)%LOGGER_SLOTS);--l->count;return true;}
bool logger_command(logger_t *l,const frame_t *req,frame_t *response){
    *response=(frame_t){.type=(uint8_t)(req->type|0x80),.sequence=req->sequence,.length=1};
    if(req->type==3||req->type==4){
        if(req->length)response->payload[0]=2;
        else {l->running=req->type==3;l->head=l->count=0;l->filter_valid=0;}
        return true;
    }
    if(req->type==5){
        if(req->length!=4||req->payload[0]!=1){response->payload[0]=2;return true;}
        logger_config_t cfg={read_le16(req->payload+1),req->payload[3]};
        if(!logger_config_valid(cfg)){response->payload[0]=2;return true;}
        if(cfg.period_ms!=l->config.period_ms||cfg.filter_shift!=l->config.filter_shift){
            l->config=cfg;if(++l->generation==0)l->generation=1;
            l->filter_valid=0;l->head=l->count=0;
        }
        response->length=6;response->payload[1]=1; /* APPLIED to control state; next cycle uses it */
        write_le32(response->payload+2,l->generation);return true;
    }
    return false;
}
void logger_extend(const logger_t *l,frame_t *f){
    unsigned at=f->length;
    f->payload[at++]=1;f->payload[at++]=2;f->payload[at++]=l->sensor_type;f->payload[at++]=l->running;
    f->payload[at++]=2;f->payload[at++]=13;write_le16(f->payload+at,1);at+=2;
    write_le16(f->payload+at,l->config.period_ms);at+=2;f->payload[at++]=l->config.filter_shift;
    write_le32(f->payload+at,l->generation);at+=4;write_le32(f->payload+at,l->saved_generation);at+=4;
    if(f->type==0x82){
        f->payload[at++]=3;f->payload[at++]=18;
        write_le32(f->payload+at,l->sequence);write_le32(f->payload+at+4,l->dropped);
        write_le32(f->payload+at+8,l->sensor_errors);write_le32(f->payload+at+12,l->storage_errors);
        write_le16(f->payload+at+16,l->high_water);at+=18;
    }else{f->payload[at++]=4;f->payload[at++]=8;write_le32(f->payload+at,l->sensor_type==2?8192:1);write_le32(f->payload+at+4,l->sensor_type==2?64:1);at+=8;}
    f->length=(uint16_t)at;
}
