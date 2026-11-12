# motor-dc-speed：带编码器直流电机速度闭环（V1 第一期）

状态：**P1 可复现工程——可构建、主机测试全绿；未上板验证（全部板级配置标 CANDIDATE）**。
设计合同见 `plans/2026-11-11-motor-control/`（prd/curriculum/design/acceptance/implement）。
硬件档案：`boards/f103c8-tb6612/hardware.md` + 采购冻结 `plans/.../research/hardware-freeze.md` v1.2。

## 目录

```text
CMakePresets.json               # host-tests / dc-openloop / dc-encoder / dc-speed
cmake/arm-none-eabi.cmake       # ARM 工具链
dependencies.lock.json          # STM32CubeF1 v1.8.6 + 子模块 SHA + 工具链版本
boards/f103c8-tb6612/           # board.json / hardware.md / board_config.h / 链接脚本 / hal_conf
include/ src/                   # 控制核心（HAL 无关，主机可测）+ ARM 胶合
tests/host_tests.c              # H01–H10 + 桥真值表 + E2E 薄切片
```

## 构建（从干净检出）

前置：CMake ≥3.20、Ninja；ARM 构建需 `arm-none-eabi-gcc` 与 STM32CubeF1 v1.8.6
（获取与校验见 dependencies.lock.json；CI 有完整可复现流程）。

```powershell
cmake --preset host-tests && cmake --build --preset host-tests && ctest --preset host-tests --output-on-failure

git clone --depth 1 --branch v1.8.6 https://github.com/STMicroelectronics/STM32CubeF1.git C:\CubeF1
cd C:\CubeF1 && git submodule update --init Drivers/STM32F1xx_HAL_Driver Drivers/CMSIS/Device/ST/STM32F1xx

cmake --preset dc-openloop -DCUBEF1_PATH=C:\CubeF1
cmake --build --preset dc-openloop        # 产出 ELF/HEX/BIN/map（预算：Flash≤56KiB，静态RAM≤12KiB）
cmake --preset dc-encoder   -DCUBEF1_PATH=C:\CubeF1 && cmake --build --preset dc-encoder
cmake --preset dc-speed     -DCUBEF1_PATH=C:\CubeF1 && cmake --build --preset dc-speed
```

## 命令协议 v1（MC-104 冻结）

ASCII 行，≤96 B（含 `\n`）；115200 8N1（候选）。

```text
HELLO                                → +OK <sess:8hex>（新会话；复位/断开须重协商）
<sess> <seq> ARM                     → 配置完整且静止才 +OK（F06 拦截未标定配置）
<sess> <seq> SET_DUTY <±‰>           → 开环；|‰|≤1000，日常上限 duty_limit<1000
<sess> <seq> SET_RPM  <±rpm>         → 闭环；|rpm|≤target_limit_rpm
<sess> <seq> HEARTBEAT               → 刷新命令租约（F01 窗口 500 ms 初值）
<sess> <seq> STOP                    → 始终有效且幂等（会话不匹配也执行）→ DISABLED
<sess> <seq> CLEAR                   → 两步清故障：先清位，条件解除后再次 CLEAR 回 DISABLED
<sess> <seq> CONFIG k=v              → 仅 DISABLED；数值范围与有限性校验
<sess> <seq> STATUS                  → 状态/故障/输出快照
```

规则：除 HELLO/STOP/STATUS 外必须带本会话 `sess` 且 `seq` 严格递增；重复、倒序、
未知命令、非法参数 → `-NACK` 且**不刷新租约**；seq 耗尽重新 HELLO。半帧超时不刷新租约。

## 遥测帧 v1（MC-104 冻结）

二进制，小端：`AA 55 ver=1 type len(LE) seq(LE) t_ms(LE) payload... CRC8`。
type=1 SAMPLE，payload 28 B（43 B/帧 @100 Hz = 4.3 kB/s，预算 ≤6.4 kB/s 内）：
target_ramp/delta_count/rpm_raw/rpm_filt/integral（0.1 单位定点）、out_duty(‰)、
state、fault、flags（饱和/反馈无效）、exec_us、dropped。CRC8（poly 0x07）。
解码工具与 golden vectors 属 MC-304（P3）。

## 停止语义（官方真值表核验版，v1.2 冻结）

默认停止/故障 = **STBY=L**（Standby 高阻+节电）；方向切换间隙高阻 = IN1=IN2=L & PWM=H
（Stop）；**短接制动 = 方向保持 + PWM=L（显式选项，V1 默认不开）**。禁止把 PWM=0 写成
「滑行/机械急停」。物理断能开关独立于软件（hardware.md）。

## 当前边界（诚实声明）

- CPR 默认 0 → F06 禁止 ARM：未标定不上电转。CPR 标定（B03）后写 `board.json` + `CONFIG`。
- IWDG 喂狗逻辑未启用（P2 冻结后按 design §4 接入）；遥测发送主循环侧为占位（P2 完善队列）。
- 板上电气、时序、波形全部 CANDIDATE，P2/P3 真板验收前不得引用为已验证结论。
