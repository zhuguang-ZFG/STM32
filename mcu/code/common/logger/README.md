# Shared sensor logger

`logger.c` owns the fixed 64-byte SAMPLE layout, explicit endian encoding, integer IIR,
16-slot queue and configuration validation. `store.c` owns two-slot EEPROM recovery;
the same production functions run in the fault-injection tests.

Run `sh code/common/logger/probe.sh`. Linux also runs ASan/UBSan. `runtime.c` is the
shared FreeRTOS/ESP-IDF application layer; the host tests use only the pure core.
Platform functions in `port.h` provide actual ADC/I2C/UART/storage/watchdog access.

The caller serializes core calls with a mutex. Slow storage is outside that mutex,
and the sample task has higher priority than communication. Changed configuration
generations discard old in-flight samples rather than mislabeling them.

The default queue drops new samples when full; counters saturate except intentional
sequence/timestamp wrap. Filter state is reset on invalid channels and STOP/restart.
CRC verifies accidental corruption, not authenticity. All physical measurements remain pending.
