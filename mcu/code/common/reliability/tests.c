#include "service.h"
#include "health.h"
#include "record.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static size_t feed(protocol_rx_t *rx,const uint8_t *p,size_t n,uint32_t now,frame_t *out)
{
    size_t count=0; for(size_t i=0;i<n;i++) count+=protocol_rx_feed(rx,p[i],now,out); return count;
}
static void codec_tests(void)
{
    assert(protocol_crc((const uint8_t *)"123456789",9)==0x29b1);
    frame_t f={.type=1,.sequence=65535}, out={0}; uint8_t wire[74], raw[72], encoded[73];
    for(unsigned length=0;length<=64;length++) {
        f.length=(uint16_t)length;
        for(unsigned i=0;i<length;i++) f.payload[i]=(uint8_t)((i%3)?i:0);
        size_t n=protocol_encode(&f,wire,sizeof(wire));
        assert(n==length+10 && wire[n-1]==0);
        assert(protocol_decode(wire,n-1,&out)==PROTO_OK);
        assert(out.sequence==65535 && out.length==length && !memcmp(out.payload,f.payload,length));
        for(size_t split=0;split<=n;split++) {
            protocol_rx_t rx; protocol_rx_init(&rx,100);
            size_t count=feed(&rx,wire,split,1,&out)+feed(&rx,wire+split,n-split,1,&out);
            assert(count==1 && rx.stats.ok==1);
        }
        memset(encoded,0xa5,sizeof(encoded));
        assert(!protocol_encode(&f,encoded,n-1));
        assert(encoded[0]==0xa5); /* No partial output on insufficient capacity. */
    }
    f.length=65; assert(!protocol_encode(&f,wire,sizeof(wire)));
    f.length=64; size_t n=protocol_encode(&f,wire,sizeof(wire));
    size_t r=protocol_cobs_decode(wire,n-1,raw,sizeof(raw)); assert(r==72);
    for(unsigned error=0;error<3;error++) {
        uint8_t copy[72]; memcpy(copy,raw,r);
        if(error==0) copy[0]=2;
        if(error==1) copy[4]=65;
        if(error==2) copy[7]^=1;
        size_t count=protocol_cobs_encode(copy,r,encoded,sizeof(encoded));
        frame_t sentinel={.type=99};
        protocol_error_t expect[]={PROTO_VERSION,PROTO_LENGTH,PROTO_CRC};
        assert(protocol_decode(encoded,count,&sentinel)==expect[error]);
        assert(sentinel.type==99);
    }
    const uint8_t bad[]={3,1}; assert(protocol_decode(bad,sizeof(bad),&out)==PROTO_COBS);
    assert(!protocol_rx_init(NULL,100));
    protocol_rx_t rx; assert(!protocol_rx_init(&rx,0)); assert(!protocol_rx_init(&rx,0x80000000UL));
    protocol_rx_init(&rx,100);
    assert(feed(&rx,wire,n,0,&out)==1 && feed(&rx,wire,n,0,&out)==1);
    /* Exact timeout, wraparound and one synchronization delimiter. */
    for(unsigned delta=99;delta<=101;delta++) {
        protocol_rx_init(&rx,100); uint32_t start=UINT32_MAX-50;
        assert(!feed(&rx,wire,3,start,&out));
        size_t got=feed(&rx,wire+3,n-3,start+delta,&out);
        assert(got==(delta<100?1U:0U));
        assert(rx.stats.timeout==(delta<100?0U:1U));
        assert(feed(&rx,wire,n,start+delta,&out)==1);
    }
    protocol_rx_init(&rx,100);
    for(unsigned i=0;i<500;i++) protocol_rx_feed(&rx,1,0,&out);
    assert(rx.stats.oversize==1 && rx.state==RX_DISCARD);
    protocol_rx_feed(&rx,0,0,&out); assert(feed(&rx,wire,n,0,&out)==1);
    feed(&rx,wire,2,1,&out); protocol_rx_loss(&rx);
    assert(!feed(&rx,wire,n,1,&out)); /* First frame supplies only a new boundary. */
    assert(feed(&rx,wire,n,1,&out)==1);
    rx.stats.crc=UINT32_MAX; rx.stats.length=1; assert(protocol_errors(&rx.stats)==UINT32_MAX);
    /* Deterministic fuzz executes the production parser, guarded against overwrites. */
    struct { uint32_t before; protocol_rx_t parser; uint32_t after; } guard={0};
    guard.before=0xabcdef01; guard.after=0x76543210; protocol_rx_init(&guard.parser,100);
    uint32_t random=0x1badf00d;
    for(unsigned i=0;i<200000;i++) {
        random=random*1664525UL+1013904223UL;
        if(protocol_rx_feed(&guard.parser,(uint8_t)(random>>24),i/50,&out)) assert(out.length<=64);
    }
    assert(guard.before==0xabcdef01 && guard.after==0x76543210);
}
static void health_tests(void)
{
    uint32_t deadlines[8]={500,500}; health_t h; health_supervisor_t supervisor={0};
    assert(!health_init(&h,0,deadlines,1000,0)); assert(!health_evaluate(&h,0).may_feed);
    assert(!health_init(&h,256,deadlines,1000,0));
    assert(!health_init(&h,1,deadlines,0x80000000UL,0));
    deadlines[0]=0; assert(!health_init(&h,1,deadlines,0,0)); deadlines[0]=500;
    assert(health_init(&h,3,deadlines,1000,0));
    assert(health_evaluate(&h,999).may_feed);
    health_result_t r=health_evaluate(&h,1000); assert(!r.may_feed && r.overdue_mask==3);
    assert(!health_supervise(&supervisor,r));
    assert(!health_progress(&h,8,1000)); assert(!health_progress(&h,2,1000));
    health_progress(&h,0,1000); health_progress(&h,1,1000);
    r=health_evaluate(&h,1000); assert(r.may_feed && !r.in_grace);
    assert(!health_supervise(&supervisor,r) && supervisor.first_overdue==3);
    /* Even at the same modular time next epoch, a closed grace never reopens. */
    health_progress(&h,0,0); health_progress(&h,1,0);
    assert(!health_evaluate(&h,0).in_grace);
    uint32_t start=UINT32_MAX-200;
    health_init(&h,3,deadlines,1000,start);
    health_progress(&h,0,start); health_progress(&h,1,start);
    assert(health_evaluate(&h,start+499).may_feed);
    assert(health_evaluate(&h,start+500).overdue_mask==3);
    /* Sensor errors/empty UART still count when the bounded work cycle completes. */
    for(unsigned i=0;i<2000;i+=100) {
        health_progress(&h,0,start+i); health_progress(&h,1,start+i);
        assert(health_evaluate(&h,start+i).may_feed);
    }
    health_init(&h,3,deadlines,0,0); assert(!health_evaluate(&h,0).may_feed);
}
typedef struct { uint8_t bytes[4096]; size_t used, limit; } sink_t;
static size_t write_sink(void *user,const uint8_t *p,size_t n)
{
    sink_t *s=user; if(n>s->limit)n=s->limit; assert(s->used+n<=sizeof(s->bytes));
    memcpy(s->bytes+s->used,p,n); s->used+=n; return n;
}
static unsigned faults;
static void on_fault(void *u,uint8_t kind,uint8_t id) { (void)u; assert(kind==1 && id==0); ++faults; }
static void transport_tests(void)
{
    protocol_tx_t tx; protocol_tx_init(&tx); frame_t f={.type=1}; sink_t sink={.limit=3};
    for(unsigned i=0;i<4;i++) { f.sequence=(uint16_t)i; assert(protocol_tx_enqueue(&tx,&f)); }
    assert(!protocol_tx_enqueue(&tx,&f) && tx.dropped==1);
    for(unsigned i=0;i<50;i++) protocol_tx_step(&tx,i,write_sink,&sink);
    protocol_rx_t rx; protocol_rx_init(&rx,100); frame_t out; unsigned count=0;
    for(size_t i=0;i<sink.used;i++) if(protocol_rx_feed(&rx,sink.bytes[i],0,&out)) assert(out.sequence==count++);
    assert(count==4);
    protocol_tx_init(&tx); sink.used=0; sink.limit=1; protocol_tx_enqueue(&tx,&f);
    protocol_tx_step(&tx,UINT32_MAX-20,write_sink,&sink);
    protocol_tx_step(&tx,UINT32_MAX-19,write_sink,&sink);
    sink.limit=0; protocol_tx_step(&tx,79,write_sink,&sink);
    assert(tx.dropped==1 && tx.sync && !tx.count);
    sink.limit=74; protocol_tx_enqueue(&tx,&f);
    protocol_tx_step(&tx,80,write_sink,&sink); protocol_tx_step(&tx,81,write_sink,&sink);
    protocol_rx_init(&rx,100); assert(feed(&rx,sink.bytes,sink.used,0,&out)==1);
    byte_queue_t q={0}; uint8_t byte; bool loss;
    for(unsigned i=0;i<512;i++) assert(byte_queue_push(&q,(uint8_t)i));
    assert(!byte_queue_push(&q,1)); assert(!byte_queue_pop(&q,&byte,&loss) && loss);
    assert(byte_queue_push(&q,7)); assert(byte_queue_pop(&q,&byte,&loss) && byte==7 && !loss);
    device_service_t service; uint8_t wire[74];
    device_service_init(&service,1,123,true,on_fault,NULL);
    frame_t request={.type=0x7f,.length=2,.payload={1,0}};
    size_t n=protocol_encode(&request,wire,74);
    for(unsigned j=0;j<5;j++) for(size_t i=0;i<n;i++) device_service_feed(&service,wire[i],0);
    assert(faults==4 && service.tx.dropped==1); /* Full queue must not execute command 5. */
    device_service_init(&service,1,123,false,NULL,NULL);
    for(size_t i=0;i<n;i++) device_service_feed(&service,wire[i],0);
    assert(protocol_decode(service.tx.wire[0],service.tx.length[0]-1,&out)==PROTO_OK && out.payload[0]==1);
    request.type=2; request.length=0; n=protocol_encode(&request,wire,74);
    for(size_t i=0;i<n;i++) device_service_feed(&service,wire[i],1);
    assert(protocol_decode(service.tx.wire[1],service.tx.length[1]-1,&out)==PROTO_OK);
    assert(out.length==25 && read_le32(out.payload+6)==123 && read_le32(out.payload+13)==2);
}
static void record_tests(void)
{
    fault_record_t r={{0}}; uint32_t mask=99;
    assert(!fault_record_read(&r,true,&mask));
    fault_record_save(&r,3); assert(fault_record_read(&r,true,&mask) && mask==3);
    assert(!fault_record_read(&r,false,&mask));
    for(unsigned i=0;i<12;i++) {
        r.bytes[i]^=1; assert(!fault_record_read(&r,true,&mask)); r.bytes[i]^=1;
    }
    assert(fault_record_take(&r,true,&mask));
    assert(!fault_record_take(&r,true,&mask));
}
int main(void) { codec_tests(); health_tests(); transport_tests(); record_tests(); puts("protocol, health, TX/RX backpressure, service and reset-record tests passed"); return 0; }
