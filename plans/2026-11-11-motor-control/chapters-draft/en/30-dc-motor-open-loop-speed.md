# 30 DC motor open-loop speed: duty cycle, ramps, and stop semantics

> 中文：[直流电机开环调速](../30-直流电机开环调速.md)

> The duty cycle sets the fraction of time the drive energizes the motor — it does not set the speed directly. Treating 50% as "half speed" is the most common open-loop illusion.

**Board-level premise of this chapter**: wiring and parameters follow procurement freeze v1.2 (candidate values, verified at P2 on-board bring-up). Command and telemetry behavior refers to the built firmware in `examples/motor-dc-speed/`; the full protocol is in that directory's README.

## Learning goals

- [ ] Recompute the PWM prescaler and duty register values of this chapter and state what the 0% and 100% endpoints mean.
- [ ] Express forward, reverse, and magnitude with a signed duty cycle, and explain what limiting and ramps are for.
- [ ] Choose a stop semantics (coast / short brake / standby) from the official truth table and justify it.
- [ ] Explain why a direction change must wait for standstill, and what the standstill criterion and timeout are.
- [ ] Run a forward → stop → reverse sequence over the command protocol and confirm from telemetry that the drive mode really changed.

---

## The entry question

The duty cycle is set to 50% — why isn't the speed half of top speed?

Because the duty cycle controls the **fraction of time the drive applies voltage**, i.e. approximately the average voltage; the actual speed is settled by average voltage, motor parameters (resistance, back-EMF constant, gear ratio), and load torque together. At no load, 50% may come close to half speed; under load it drops well below; and at the low end there is a static-friction threshold — below some duty the motor just hums. Open loop honestly means: **you command a voltage excitation, the motor decides the speed**. Measuring it and closing the loop is chapter 32.

## Minimal victory (M30-A: three duty steps and the waveform)

**Goal**: under a current-limited supply, start at a low duty, step through medium and high, and confirm PWM frequency and duty with a multimeter/scope at each step while reading the drive mode from telemetry.

1. Complete M29-A/B (logic-side checks and the limited-current trial-spin threshold).
2. Connect the host serial port (USART1, 115200 8N1), send `HELLO`, and establish a session per the protocol.
3. Send `ARM`: the firmware releases STBY and the drive enters standby-ready.
4. Send `SET_DUTY 200` (20%) and watch whether the motor starts; record the `STATUS` reply.
5. Step through `SET_DUTY 400` and `SET_DUTY 700`, recording duty and status word from telemetry `SAMPLE` frames at each step.
6. Send `STOP` and confirm the drive de-energizes.

**Expected evidence**: three monotonically rising speed steps; PWM at 20 kHz (within the chapter 29 ceiling); telemetry shows the drive mode returning to off after `STOP`. Waveforms alone or simulated logs do not count as rotation evidence — record the supply current-limit value and the duration of every trial spin.

> Status: M30-A/B/C run only after the parts arrive and pass the hardware gate; they are candidate steps for now.

## Core ideas

### A PWM configuration you can recompute

This project's frozen values (`boards/f103c8-tb6612/board_config.h`, CANDIDATE):

| Item | Value | Recomputation |
| --- | --- | --- |
| TIM3 clock | 72 MHz (PSC=0, no division) | 8 MHz HSE × PLL9 |
| ARR | 3599 | 72 MHz / 20 kHz − 1 |
| CCR | duty‰ × 3600 / 1000 | 50% → 1800; 100% → 3600, **must exceed ARR** |
| PWM mode | Edge-aligned mode 1 | Active while CNT < CCR |

Endpoint semantics: CCR=0 produces a constant inactive level (0% for an active-high configuration); **CCR>ARR produces constant active (100%)** — with CCR=ARR there is still one inactive tick (3599/3600 ≈ 99.97%), a boundary of the PWM1 "CNT < CCR" definition, so full pressure in software must write CCR=3600. Both endpoints are allowed; the firmware uses them for "release the drive" and "full pressure".

Why 20 kHz: above the audible band (motor and supply whine), far below the TB6612 100 kHz ceiling, and ARR still fits in 16 bits. Changing the clock tree means recomputing ARR/PSC and re-checking all three conditions.

### Signed duty: direction and magnitude separated

Internally the firmware uses a **signed duty** (−1000…+1000, ‰) everywhere: the sign is direction, the absolute value is magnitude. The mapping to pins lives in exactly one place (`motor_bridge.c`): the sign decides which of AIN1/AIN2 is high, the magnitude decides CCR. Every command, PI output, and ramp uses this representation — avoiding the classic bug of a "direction register" and a "magnitude register" drifting apart.

Both limits are applied before sign mapping: output limit |u| ≤ duty_limit (default 900‰; `params_valid` rejects any config ≥1000), and integral limit |I| ≤ i_limit (default 500‰). Chapter 32 shows why these two numbers must stay separate.

### Ramps and stop policy

The duty does not jump the moment a command arrives. Frozen default behavior:

- In open loop the duty ramps toward the target at **±50‰ per 10 ms** — controlled starts and zero-based re-acceleration after a direction change both rely on it;
- `STOP` removes enable and returns to standby-ready; if the command stream is silent for **500 ms** (the lease, F01) the firmware latches a fault and stops — unplugging the serial cable must not leave a spinning motor;
- A direction flip **must** go through the REVERSING contract: ramp duty to 0 → release the drive and wait for standstill (|rpm| ≤ 5) → hold 100 ms → only then allow reversed output, with a 3 s overall timeout. Skipping standstill is one source of the current-spike problems from chapter 29.

The stop semantics are your choice: `motor_bridge` supports both coast and short-brake mappings for PWM=0 (a configuration item); standby is handled uniformly by STBY. The default configuration and the cost of each option are in the chapter 29 three-state table.

## Commands and telemetry (protocol v1, frozen)

| Command | Function | Key constraints |
| --- | --- | --- |
| `HELLO` | Handshake, assigns an 8-bit hexadecimal session number | Sequence numbers increase monotonically within a session; out-of-order/duplicates are dropped per protocol |
| `ARM` | Release STBY, enter standby-ready | Refused with a fault code when configuration is invalid (e.g. encoder not calibrated) |
| `SET_DUTY n` | Open-loop target (−900…900) | Sign flip triggers REVERSING; never an instant reversal |
| `SET_RPM n` | Closed-loop target (±target_limit) | Needs valid feedback; see chapters 31/32 |
| `STOP` | Remove enable, back to standby-ready | Exempt from session checks, but always de-energizes |
| `HEARTBEAT` / `CONFIG` / `STATUS` / `CLEAR` | Lease renewal / parameters / readback / fault clear | CLEAR only valid in DISABLED state |

Telemetry frames are fixed at 43 bytes (`AA 55` header + type + length + sequence + timestamp + payload + CRC8), i.e. 4.3 kB/s at 100 Hz; with 8N1's 10 bits per byte that is 43 kbit/s, **37.3% of the 115200 baud line**. Control traffic is far smaller (a few frames per second), so headroom stays ample; raising the telemetry rate means evaluating bus occupancy first, and lowering the frame rate if needed. The field-by-field layout is defined in `examples/motor-dc-speed/README.md`.

## Failure branches and shortest diagnosis

| Symptom | Distinguishing evidence | Next action |
| --- | --- | --- |
| Hums but does not turn at low duty | Does a higher duty start it? Is the supply at its current limit? | Starts = static-friction threshold; sweep upward with a ramp. At limit = load / jam |
| Large current or spike on a reverse command | Does the status word walk through the REVERSING phases? | Not seen = direct-flip violation; check firmware version. Seen but still spiking = check brake freewheeling and supply absorption |
| STOP over serial has no effect | Did the session expire (NACK code)? | STOP is session-exempt; if ineffective, the command path is fine — check whether the state machine is already in FAULT |
| Motor decelerates quickly even at PWM zero | The current mapping is short brake | Switch the configuration for coast; braking is a feature, not a fault |

## Transfer boundary

- Changing the driver: re-check PWM active polarity, enable-pin logic, and the PWM=0 semantics (chapter 29 transfer items).
- Changing the motor: 20 kHz still applies, but the starting threshold, allowed continuous current, and gear ratio all change — ramp step and limits must be re-set.
- Changing the MCU or clock: recompute ARR/PSC; the TIM4 control timebase is this project's 10 ms heartbeat (PSC 7199/ARR 99) — **do not use the LED-breathing software delay loop as a control timebase**: that period is not guaranteed constant, and the ramp and lease will drift with it.
- Moving to an RTOS: control-output ownership is unique (design §4); the command task and the control task pass a mailbox only, never a shared output variable.

## Memory anchor

**"The duty cycle is how deep you press the accelerator, not the speedometer."**

Where it holds: the depth directly sets engine effort (average voltage), and on the same road (load) a deeper press really is faster.
Where it breaks: change the road and the same depth gives a different speed; and the car has inertia — a direction change must brake to a stop first (REVERSING); the accelerator cannot jump across it.

## Experiment register

| Experiment | Content | Hardware gate | Status |
| --- | --- | --- | --- |
| M30-A | Three duty steps, waveform vs telemetry | M29-B passed | Pending (parts not arrived) |
| M30-B | Full record of forward → standstill → reverse | M30-A passed | Pending |
| M30-C | STOP then silent command stream; verify 500 ms timeout removes enable | M30-A passed | Pending |

## Exit check

1. From memory: which ARR/PSC combination turns 72 MHz into 20 kHz, and the CCR values for 25% and 100%?
2. State the endpoint behavior of 0% (CCR=0) and 100% (CCR must exceed ARR; equal leaves one tick short), and what "valid direction + PWM=L" actually drives.
3. Demonstrate `HELLO→ARM→SET_DUTY→STOP` and explain why the motor always stops 500 ms after the serial link drops (F01 lease).

## Sources

- PWM timer configuration and encoder mapping: [source: rm0008-pwm](#source-rm0008-pwm), [source: rm0008-encoder](#source-rm0008-encoder)
- TB6612 truth table and electrical thresholds: [source: tb6612-truth-table](#source-tb6612-truth-table), [source: tb6612-electrical](#source-tb6612-electrical)
- Firmware protocol and frozen parameters: `examples/motor-dc-speed/README.md`, `boards/f103c8-tb6612/board_config.h`
