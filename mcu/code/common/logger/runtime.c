#include "port.h"
#include "../reliability/service.h"
#include "../reliability/health.h"
#include "freertos_compat.h"
#ifdef ESP_PLATFORM
#include "sdkconfig.h"
#define TEST_FAULTS CONFIG_RELIABILITY_TEST_FAULTS
#define STACK(n) (n)
#else
#define TEST_FAULTS FAULTS
#define STACK(n) ((n)/sizeof(StackType_t))
#endif
static logger_t logger;
static health_t health;static health_supervisor_t supervisor;
static device_service_t service;
static SemaphoreHandle_t mutex;
static uint8_t pause_mask,pending_kind,pending_id;
static bool supervisor_stop;
static uint32_t fault_at,sensor_fault_until,tx_pause_until;
static bool sensor_fault,tx_pause;
static bool prior_valid;
static uint32_t prior_fault;
volatile uint32_t logger_boot_error;
static uint32_t now(void){return logger_port_now();}
static void lock(void){xSemaphoreTake(mutex,portMAX_DELAY);}
static void unlock(void){xSemaphoreGive(mutex);}
static void progress(uint8_t id){lock();health_progress(&health,id,now());unlock();}
#if TEST_FAULTS
static void fault_marker(void *u,uint8_t k,uint8_t id){(void)u;(void)k;(void)id;}
#endif
static void sample_task(void *u){
    (void)u;bool was_running=true;
    for(;;){
        lock();logger_config_t cfg=logger.config;uint32_t generation=logger.generation;bool run=logger.running,paused=(pause_mask&1U)!=0;bool inject=sensor_fault;unlock();
        if(paused){vTaskDelay(1);continue;}
        if(!run){if(was_running)logger_port_pause(true);was_running=false;progress(0);vTaskDelay(1);continue;}
        if(!was_running){logger_port_pause(false);was_running=true;}
        int32_t raw[6]={0};uint8_t valid=0;uint32_t timestamp=now();
        bool ok=logger_port_sample(cfg.period_ms,raw,&valid,&timestamp);
        if(!ok||inject)valid=0;
        lock();logger_sample(&logger,raw,valid,timestamp,generation);health_progress(&health,0,now());unlock();
    }
}
static void command(const frame_t *q){
    if(q->type&0x80U)return;
    if(service.tx.count==4){service.tx.dropped=sat_add(service.tx.dropped,1);return;}
    frame_t response={.type=(uint8_t)(q->type|0x80),.sequence=q->sequence,.length=1};
    lock();
    if(device_service_query(&service,q,&response,now())){
        if(!response.payload[0]){
            if(q->type==1)response.payload[3]|=8U;
            logger_extend(&logger,&response);
            if(q->type==1){unsigned at=response.length;response.payload[at++]=5;response.payload[at++]=5;response.payload[at++]=prior_valid;write_le32(response.payload+at,prior_fault);response.length=(uint16_t)(at+4);}
        }
    }else if(logger_command(&logger,q,&response)){
        /* Accepted in-memory state; in-flight old-generation samples are dropped. */
    }else if(q->type==6){
        if(q->length)response.payload[0]=2;
        else{
            uint8_t image[128];uint32_t generation=logger.generation;
            config_encode(image,logger.config,generation);
            bool already=logger.saved_generation==generation;
            unlock();bool saved=already||logger_port_save(image);lock();
            if(saved)logger.saved_generation=generation;else logger.storage_errors=sat_add(logger.storage_errors,1);
            response.length=6;response.payload[0]=saved?0:4;response.payload[1]=2;write_le32(response.payload+2,generation);
        }
    }else if(q->type==0x7f){
#if TEST_FAULTS
        if(q->length!=2||q->payload[0]<1||q->payload[0]>4||q->payload[1]>(q->payload[0]==1?1:0))response.payload[0]=2;
        else{pending_kind=q->payload[0];pending_id=q->payload[1];fault_at=now()+200U;}
#else
        response.payload[0]=1;
#endif
    }else response.payload[0]=1;
    unlock();protocol_tx_enqueue(&service.tx,&response);
}
static void communication_task(void *u){
    (void)u;
    for(;;){
        lock();bool paused=(pause_mask&2U)!=0;bool stopped_tx=tx_pause;unlock();
        if(!paused){
            for(unsigned i=0;i<512;i++){
                uint8_t b;bool loss;bool got=logger_port_read(&b,&loss);
                if(loss)protocol_rx_loss(&service.rx);
                if(!got)break;
                frame_t q;if(protocol_rx_feed(&service.rx,b,now(),&q)){command(&q);break;}
            }
            protocol_rx_poll(&service.rx,now());progress(1);
        }
        if(service.tx.count<2){frame_t f;lock();bool ready=logger_pop(&logger,&f);unlock();if(ready)protocol_tx_enqueue(&service.tx,&f);}
        if(!stopped_tx)protocol_tx_step(&service.tx,now(),logger_port_write,NULL);
        vTaskDelay(1);
    }
}
static void supervisor_task(void *u){
    (void)u;bool recorded=false;
    if(!logger_port_watchdog_start()){logger_boot_error=2;for(;;)vTaskDelay(1);}
    for(;;){
        lock();uint32_t time=now();
        if(pending_kind&&(int32_t)(time-fault_at)>=0){
            if(pending_kind==1)pause_mask|=(uint8_t)(1U<<pending_id);
            if(pending_kind==2)supervisor_stop=true;
            if(pending_kind==3){sensor_fault=true;sensor_fault_until=time+1000U;}
            if(pending_kind==4){tx_pause=true;tx_pause_until=time+2000U;}
            pending_kind=0;
        }
        if(sensor_fault&&(int32_t)(time-sensor_fault_until)>=0)sensor_fault=false;
        if(tx_pause&&(int32_t)(time-tx_pause_until)>=0)tx_pause=false;
        health_result_t h=health_evaluate(&health,time);
        bool feed=!supervisor_stop&&health_supervise(&supervisor,h);
        service.required=3;service.overdue=(uint8_t)h.overdue_mask;service.flags=(h.in_grace?1U:0U)|(supervisor.restart_latched?2U:0U);
        uint32_t mask=supervisor_stop?0x80:supervisor.first_overdue;
        unlock();
        if(feed)logger_port_watchdog_feed();else if(!recorded){logger_port_fault(mask);recorded=true;}
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
static void bootstrap(void *u){
    (void)u;uint8_t image[128];uint32_t reset=logger_port_reset();
    prior_fault=logger_port_previous_fault(&prior_valid);
    if(!logger_port_init()){logger_boot_error=1;for(;;)vTaskDelay(1);}
    bool loaded=logger_port_load(image);logger_init(&logger,logger_port_sensor(),loaded?image:NULL);
    device_service_init(&service,logger_port_platform(),reset,true,
#if TEST_FAULTS
    fault_marker,
#else
    NULL,
#endif
    NULL);
    uint32_t deadlines[8]={2500,1500};health_init(&health,3,deadlines,3000,now());
    if(xTaskCreate(sample_task,"sample",STACK(4096),NULL,3,NULL)!=pdPASS||xTaskCreate(communication_task,"comm",STACK(6144),NULL,2,NULL)!=pdPASS||xTaskCreate(supervisor_task,"supervisor",STACK(3072),NULL,4,NULL)!=pdPASS){logger_boot_error=3;for(;;)vTaskDelay(1);}
    vTaskDelete(NULL);
}
void logger_create_tasks(void){mutex=xSemaphoreCreateMutex();if(!mutex||xTaskCreate(bootstrap,"logger-init",STACK(4096),NULL,4,NULL)!=pdPASS){logger_boot_error=4;for(;;){}}}
