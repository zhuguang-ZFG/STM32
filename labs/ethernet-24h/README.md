# STM32 Ethernet 24-hour evidence run

This lab turns chapter 27's long-run requirement into a reproducible evidence package. It does **not** contain a claimed hardware result: a run is complete only when the target board, PHY, firmware commit, topology, PCAP, JSONL, resource telemetry, and fault timestamps are all present.

## Acceptance boundary

Target behavior:

- one deadline-bounded framed TCP request every second;
- exact echo of magic, payload length, sequence, client monotonic timestamp, and deterministic payload;
- cable removal, peer stall/close, service restart, DHCP/DNS changes, and TLS failures remain distinguishable;
- the device reconnects with capped backoff;
- minimum heap, pbuf peak, and each critical task's minimum stack do not degrade monotonically with reconnect count;
- no credential, private key, token, or customer payload appears in evidence.

A ping-only run does not satisfy this contract. A green link LED proves only the PHY link boundary.

## Wire frame

`tools/ethernet_soak.py` uses network byte order:

```text
magic[4] = "ST32"
payload_length: uint32
sequence: uint64
client_monotonic_ns: uint64
payload[payload_length]
```

The echo server returns the exact frame. The STM32 implementation must reject bad magic, lengths over its configured maximum, incomplete frames at the shared deadline, and stale connections after link loss.

## 1. Record the immutable run metadata

Before starting, create a run directory outside the Git working tree and record:

```text
run_id / UTC start
board product and PCB revision
MCU ordering code and silicon revision
PHY model, address, clock source, strap and reset scheme
firmware Git commit and dirty/clean state
compiler, STM32Cube package, lwIP, Mbed TLS and RTOS versions
linker map path and ETH descriptor/RX/TX buffer addresses
MAC/IP/mask/gateway/DNS; redact credentials
switch/router model and port; capture point
expected fault schedule and acceptance limits
```

The chapter 27 H7 invariants still apply: no Ethernet DMA buffer in DTCM, 32-byte cache-line ownership where cached, and final addresses verified from the map.

## 2. Smoke the host peer before connecting hardware

Start a finite local server:

```bash
python tools/ethernet_soak.py serve \
  --bind 127.0.0.1 --port 9000 --max-connections 5
```

In another terminal:

```bash
python tools/ethernet_soak.py probe \
  --host 127.0.0.1 --port 9000 \
  --duration 3 --interval 0.5 --timeout 1 \
  --log D:/captures/ethernet-smoke.jsonl \
  --summary D:/captures/ethernet-smoke-summary.json
```

This validates the host harness only. It is not STM32 Ethernet evidence.

## 3. Stable 24-hour run

When the STM32 exposes the framed echo service:

```bash
python tools/ethernet_soak.py probe \
  --host 192.0.2.10 --port 9000 \
  --duration 86400 --interval 1 --timeout 2 \
  --payload-size 256 \
  --log D:/captures/RUN_ID/echo.jsonl \
  --summary D:/captures/RUN_ID/echo-summary.json
```

Replace the documentation address with the assigned test-network address. Capture traffic at the same time. Example with TShark, after discovering the actual interface number:

```bash
tshark -D
tshark -i INTERFACE -f "host DEVICE_IP" -w D:/captures/RUN_ID/traffic.pcapng
```

Do not guess an interface number. Record where the capture was taken; a switch mirror port, host NIC, and device-side trace observe different boundaries.

## 4. Deterministic peer faults

To exercise an STM32 **client**, run the host peer with explicit faults:

```bash
python tools/ethernet_soak.py serve \
  --bind 0.0.0.0 --port 9000 \
  --close-every 37 \
  --stall-every 53 --stall-seconds 3 \
  --delay-every 29 --delay-ms 750
```

Expected device evidence:

| Injection | Expected first result | Required recovery |
| --- | --- | --- |
| close before frame | connect/send/receive close, not generic “network error” | close local socket, capped backoff, new sequence |
| stalled reply beyond deadline | one timeout at the original transaction deadline | no per-loop timeout reset; no stuck task |
| delayed reply within deadline | success with higher latency | no duplicate command |
| cable removed for 10 s | PHY link-down precedes socket failures | stop opening sockets until link returns |
| server process restart | reset/refused/timeout according to timing | reconnect without leaking pbuf/socket state |
| DHCP lease/address change | addressing state changes before reconnect | old sockets discarded; DNS rerun |
| wrong DNS answer | TCP or host-name verification failure | error remains attributed to DNS/TLS layer |
| expired/wrong-host/unknown-CA certificate | TLS verification failure | never fall back to `VERIFY_NONE` |

Manual cable, switch, DHCP, DNS, and certificate injections must include UTC and device monotonic timestamps in `faults.jsonl` so PCAP and firmware logs can be correlated.

## 5. Device telemetry

Emit a compact line at least once per minute and on every state transition:

```text
monotonic_ms boot_id net_state reason reconnect_count
heap_free heap_min pbuf_used pbuf_used_max
rx_drop tx_error last_sequence
stack_min:eth stack_min:tcpip stack_min:app
```

Use stable numeric result enums in addition to human text. The watchdog supervisor should refresh only when the network task and all other critical tasks have advanced their health epochs; it must not require the Internet to be online if offline operation is an allowed product state.

## 6. Acceptance report

The report contains:

1. immutable metadata and fault schedule;
2. firmware log, host JSONL/summary, PCAPNG, linker map, and telemetry;
3. attempts, successes, failures by layer, latency min/p50/p95/p99/max, and worst recovery time;
4. heap/pbuf/stack low-water values plotted against reconnect count;
5. one timeline per injected fault from physical/link evidence through the first application success;
6. every deviation, residual unknown, and whether it blocks release.

Pass only if every named failure is distinguishable, all deadlines terminate, recovery stays within the product limit, sequence/idempotency holds, and resources do not show monotonic loss. Otherwise preserve the artifacts and report the first failed boundary; do not “fix” the report by deleting failed intervals.
