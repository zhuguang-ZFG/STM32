# main 组件：业务 main.c + 公共模块源文件（复用不复制）
idf_component_register(
    SRCS "main.c"
         "../../../common/reliability/protocol.c"
         "../../../common/reliability/transport.c"
         "../../../common/reliability/service.c" "../../../common/reliability/query.c"
         "../../../common/reliability/health.c"
         "../../../common/reliability/record.c"
    PRIV_INCLUDE_DIRS "../../../common/reliability"
    PRIV_REQUIRES driver esp_timer esp_hw_support esp_system
)
