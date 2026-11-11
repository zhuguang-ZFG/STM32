idf_component_register(SRCS "main.c" "port.c" "../../../common/reliability/protocol.c" "../../../common/reliability/transport.c" "../../../common/reliability/service.c" "../../../common/reliability/health.c" "../../../common/reliability/record.c" "../../../common/reliability/query.c" "../../../common/logger/logger.c" "../../../common/logger/store.c" "../../../common/logger/runtime.c"
 INCLUDE_DIRS "../../../common/logger" "../../../common/reliability"
 PRIV_REQUIRES esp_driver_uart esp_driver_i2c esp_timer esp_system nvs_flash)
