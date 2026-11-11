#include "protocol.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int unhex(const char *s,uint8_t *dst,size_t cap)
{
    size_t n=strlen(s); if(n%2 || n/2>cap)return -1;
    for(size_t i=0;i<n/2;i++) {
        unsigned v; char pair[3]={s[i*2],s[i*2+1],0}, *end;
        v=(unsigned)strtoul(pair,&end,16); if(end!=pair+2)return -1; dst[i]=(uint8_t)v;
    }
    return (int)(n/2);
}
int main(int argc,char **argv)
{
    frame_t f={0}; uint8_t b[74]; size_t n;
    if(argc==5 && !strcmp(argv[1],"encode")) {
        f.type=(uint8_t)strtoul(argv[2],NULL,0); f.sequence=(uint16_t)strtoul(argv[3],NULL,0);
        int length=unhex(argv[4],f.payload,64); if(length<0)return 2; f.length=(uint16_t)length;
        n=protocol_encode(&f,b,sizeof(b)); if(!n)return 2;
        for(size_t i=0;i<n;i++)printf("%02x",b[i]);
        puts(""); return 0;
    }
    if(argc==3 && !strcmp(argv[1],"decode")) {
        int count=unhex(argv[2],b,sizeof(b));
        if(count<1 || b[count-1] || protocol_decode(b,(size_t)count-1,&f)!=PROTO_OK)return 2;
        printf("%u %u ",f.type,f.sequence);
        for(unsigned i=0;i<f.length;i++)printf("%02x",f.payload[i]);
        puts(""); return 0;
    }
    return 2;
}
