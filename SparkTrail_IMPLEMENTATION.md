# SparkTrail — Implementation Specification

**What this document is:** a build spec for SparkTrail, a *simulation* that traces how a cyber event on EV-charging and microgrid infrastructure propagates into physical effects (temperature, current, voltage, frequency), and renders the whole propagation path in 3D.

**What this is not:** an attack tool. SparkTrail never touches a real charger, backend, or vehicle. Everything is a software model. "Attacks" are abstract events injected into a simulated message bus so you can *observe and rank their physical consequences* — the exact gap the problem statement asks you to close.

Scope rule for the whole build: **model behaviour, not exploitation.** A simulated attack is "a bad value appears on this link at time T." How a real attacker would obtain access to that link is deliberately out of scope and is not documented here.

---

## 0. Guiding principles

1. **One event graph.** Every component (cyber, control, physical) writes time-stamped events into a single store. The trace *is* the product.
2. **Plant vs. monitor separation.** The physics simulation (the "plant") and any detector must use *different* models, or detection results are fake. Keep them in separate modules with separate parameters.
3. **Pick one chain, do it fully.** The taxonomy below is broad on purpose. For a demo, implement *one complete path end-to-end* before adding breadth. One full chain beats five stubs.
4. **Honesty in the UI.** Every physical number shown carries a flag: `modelled` (from a real model) vs `illustrative` (hand-set). Judges trust a tool that marks its own uncertainty.

---

## 1. Target taxonomy (what you can simulate)

Each target is a **plugin**: a Python class implementing a common interface (§6). You don't need all of them. Build the ones with `priority: P0` first.

### 1.1 EV charger types

| Type | Power range | Protocols modelled | Key physical state | Priority |
|---|---|---|---|---|
| **AC Level 1** (domestic, ~2 kW) | 1.4–2.4 kW | OCPP (backend), basic pilot signal | cable temp, onboard-charger temp | P2 |
| **AC Level 2** (home/workplace, 7–22 kW) | 7–22 kW | OCPP 1.6/2.0.1, IEC 61851 pilot | cable temp, connector temp | P1 |
| **DC fast (CCS/CHAdeMO), 50–150 kW** | 50–150 kW | OCPP, ISO 15118, internal CAN | pack temp, cable temp, converter temp | **P0** |
| **DC ultra-fast / HPC, 150–350 kW** | 150–350 kW | OCPP, ISO 15118, liquid-cooled cable telemetry | pack temp, coolant temp, converter load | P1 |
| **Battery-buffered charger** (has its own storage) | varies | OCPP + internal BMS | buffer SoC, buffer temp, pack temp | P2 |
| **Bidirectional / V2G charger** | 11–50 kW | OCPP, ISO 15118-20 | pack temp, export power, local voltage | P1 |

> Build **DC fast** first. It has the richest physics (real thermal risk) and the clearest attack-to-impact story.

### 1.2 Microgrid / grid-side types

| Type | What it is | Physical state modelled | Priority |
|---|---|---|---|
| **Single-feeder charging hub** | N chargers behind one transformer | transformer load %, bus voltage | **P0** |
| **LV distribution microgrid** | chargers + loads + one PV/inverter + grid tie | voltage profile, feeder current, power balance | P1 |
| **Islanded microgrid** | diesel/battery/PV, no grid tie | frequency, voltage, generator loading | P1 |
| **Microgrid with BESS** | adds a battery energy storage system | BESS SoC, inverter setpoints, frequency | P2 |
| **Campus/fleet depot** | many high-power DC chargers, scheduled | aggregate demand, peak load, transformer thermal | P1 |

---

## 2. Attack-path taxonomy (modelled as injected events)

Each path is expressed as **where in the model a wrong value enters**, plus **what the wrong value is**. No access/exploitation detail — that's intentionally absent.

Represent every attack as a declarative object:

```yaml
attack:
  id: A-DCFAST-OVERCURRENT-01
  entry_point: cyber.backend_link        # which modelled link
  mechanism: command_override            # see mechanism list below
  field: charging_profile.limit_A
  from: 125
  to: 250
  start_s: 60
  companion:                             # optional simultaneous event
    - field: sensor.pack_temp_C
      mechanism: sensor_spoof
      hold_value: 30
```

### 2.1 Entry points (where the bad value appears)

| Entry point | Modelled link | Typical fields affected |
|---|---|---|
| `cyber.backend_link` | backend (CSMS) ↔ charger | charging profile, start/stop, firmware flag |
| `cyber.vehicle_link` | charger ↔ EV (ISO 15118 / CAN) | requested current, SoC report, temp report |
| `cyber.sensor_bus` | sensor → controller | pack temp, current, voltage readings |
| `cyber.hub_controller` | site controller ↔ many chargers | broadcast setpoints, load-shed signals |
| `cyber.inverter_link` | microgrid controller ↔ inverter | frequency setpoint, power setpoint |
| `cyber.firmware_state` | charger config/firmware flags | safety-limit enable flags, calibration |

### 2.2 Mechanisms (what kind of wrong value)

| Mechanism | Meaning in the model | Example |
|---|---|---|
| `command_override` | a control value is replaced | current limit 125 → 250 A |
| `sensor_spoof` | a reading is frozen or shifted | pack temp held at 30 °C |
| `setpoint_drift` | a value ramps slowly to evade thresholds | voltage setpoint +0.1%/s |
| `replay` | a stale-but-valid value is re-applied | old "charging OK" state |
| `mass_command` | one command fans out to N units | all hub chargers → max power |
| `desync` | timing/order of messages disturbed | delayed load-shed signal |
| `dos_blackhole` | a control message is dropped | safety stop never arrives |

### 2.3 Attacks available on the **DC-fast → hub** chain (P0 set)

These are the ones to implement first, as events — each is just a row in §2 format.

1. **Overcurrent via profile override** — `command_override` on `charging_profile.limit_A`.
2. **Overcurrent masked by temp spoof** — the above **+** `sensor_spoof` on `pack_temp` (the headline demo).
3. **Cooling suppression** — `sensor_spoof` making temp read *low* so cooling logic stays idle.
4. **Mass max-power command** — `mass_command` on a 12-charger hub → transformer overload.
5. **Load-shed suppression** — `dos_blackhole` on the hub's load-shed signal during peak.
6. **Setpoint-drift overvoltage** — `setpoint_drift` on inverter voltage (microgrid variant).
7. **Frequency-setpoint push** — `command_override` on inverter frequency (islanded variant).

---

## 3. Physical effects modelled

### 3.1 Battery / charging thermal

State variables: `pack_temp_C`, `current_A`, `coolant_temp_C` (HPC only), `SoC`.

Lumped thermal model (the P0 model — simple, defensible):

```
dT/dt = ( I²·R  −  h·(T − T_ambient) ) / C
```

- `I` = current (A), set by control logic from the (possibly spoofed) readings
- `R` = effective internal resistance (Ω)
- `h` = cooling coefficient (W/K), raised by the BMS only when *reported* temp is high
- `C` = lumped heat capacity (J/K)
- `T_ambient` = ambient (°C) — expose as a scenario knob (Chennai afternoon ≈ 35 °C)

Outputs to trace: time-to-45 °C, time-to-55 °C, peak temp, Δ vs baseline.

### 3.2 Charger electrical / converter

State: `converter_load_pct`, `cable_temp_C`. Cable temp uses the same I²R form with its own R and cooling (liquid-cooled for HPC).

### 3.3 Hub transformer / feeder

```
load_pct   = 100 · P_total / S_rated
v_drop_pct = 100 · Z · P_total / S_rated
```

- `P_total` = sum of all charger powers (kW), each of which an attack can raise
- `S_rated` = transformer rating (kVA)
- `Z` = per-unit impedance

Outputs: load %, voltage drop %, overload duration.

### 3.4 Microgrid frequency (islanded)

Single-bus swing approximation:

```
df/dt = ( P_gen − P_load ) / (2·H·S_base)
```

- `H` = inertia constant (s), `P_gen`/`P_load` in per-unit. A mass-charging event raises `P_load`; a frequency-setpoint attack shifts `P_gen` response.

Outputs: frequency nadir, rate-of-change-of-frequency (RoCoF), time outside 49.5–50.5 Hz.

> Later: swap each hand-rolled model for a real library — **PyBaMM** (battery), **pandapower** (steady-state grid), optionally **GridLAB-D**. Keep the interface identical so the 3D layer doesn't change.

---

## 4. The propagation tracer (core of the project)

Every module emits events into one append-only log; the tracer links them into a graph.

```python
@dataclass
class Event:
    t: float                 # sim seconds
    layer: str               # "attack" | "cyber" | "control" | "physics" | "monitor"
    node: str                # e.g. "charger_03", "hub_tx"
    kind: str                # "command", "reading", "state", "alert"
    field: str               # "limit_A", "pack_temp_C", ...
    value: float | str
    caused_by: str | None    # id of the event that produced this one
```

- `caused_by` is what turns a flat log into a **propagation path**: injector event → control reaction → physics change → threshold crossing.
- Store events in a list during the run; build a `networkx.DiGraph` at the end for replay and for the 3D layer to walk.
- **Impact score** per attack = weighted combo of: peak deviation, time-to-impact (faster = worse), number of physical nodes affected, detection delay.

### 4.1 Physics-aware monitor (separate model!)

Runs a *reduced* thermal model off **measured current** and compares to the **reported** temperature. Raises an `alert` event when they diverge beyond a threshold (e.g. 3 °C). This is the one piece of "defense" in the tool — it only alerts, it never blocks. Keep its R/C/h different from the plant's, and show the detection delay honestly.

---

## 5. 3D simulation & visualization

Goal: an **elegant, readable 3D scene** where the attack visibly travels from a network node to a glowing-hot battery, synced to the trace timeline.

### 5.1 Recommended stack

| Option | Use when | Notes |
|---|---|---|
| **Three.js + React (R3F)** in the browser | you want a shareable, slick demo | best "elegant" result; runs anywhere; pairs with a FastAPI backend streaming events over WebSocket |
| **PyVista / VTK** (Python) | you want it all in Python, offline | fast to wire to the sim; less polished motion |
| **Plotly 3D / Dash** | minimum effort, still 3D | weakest aesthetics, quickest |

> For a hackathon demo that must look good: **Three.js + React Three Fiber**, backend in Python (the sim), events streamed to the browser.

### 5.2 Scene design

- **Nodes as 3D objects:** backend (server rack), charger (pillar), vehicle (battery pack), hub transformer (box), microgrid bus (ring). Keep them low-poly and consistent — one material system.
- **Links as tubes** between nodes. A travelling attack = an emissive pulse moving along the tube from entry point to target.
- **Heat as colour + emission:** map `pack_temp_C` to a blue→amber→red ramp on the battery mesh; intensity ramps with temperature. Transformer overload pulses the box red; voltage drop dims the bus ring.
- **Timeline scrubber** bound to sim time: dragging it replays the trace; events pop as labelled markers.
- **Side panel:** the live trace (the §4 event list) and the impact score, updating as the scrubber moves.

### 5.3 Visual-polish rules (so it reads as designed, not a tech demo)

- One accent colour for "attack", one ramp for "heat", one for "electrical stress". Don't exceed three.
- Camera: a gentle default orbit, plus click-to-focus on a node.
- Motion: ease in/out, nothing linear. Pulses travel at a readable speed (~1–2 s per hop), not instant.
- Dark scene, high-contrast labels, generous spacing. Let the glow carry the drama.

---

## 6. Software architecture

```
sparktrail/
├── core/
│   ├── events.py          # Event dataclass, EventStore, DiGraph builder
│   ├── clock.py           # fixed-step sim loop (dt = 1 s default)
│   └── scenario.py        # loads YAML scenario → objects
├── targets/
│   ├── base.py            # Target interface (step, read, apply_command)
│   ├── charger_dcfast.py  # P0
│   ├── charger_ac2.py
│   ├── hub_feeder.py      # P0
│   ├── microgrid_islanded.py
│   └── ...
├── physics/
│   ├── battery_thermal.py # lumped model; PyBaMM adapter later
│   ├── feeder.py          # transformer/voltage
│   └── swing.py           # frequency
├── control/
│   ├── bms.py             # derating + cooling logic (reads sensors)
│   └── hub_controller.py  # setpoints, load-shed
├── attacks/
│   ├── schema.py          # the §2 attack object + validation
│   └── injector.py        # applies attack events to the right link at the right time
├── monitor/
│   └── physics_aware.py   # separate-model detector (alerts only)
├── scoring/
│   └── impact.py          # impact score from the event graph
├── api/
│   └── server.py          # FastAPI: run scenario, stream events over WebSocket
├── viz3d/                 # React Three Fiber front-end
│   ├── Scene.tsx
│   ├── nodes/ links/ panels/
│   └── useTraceStream.ts
├── scenarios/
│   ├── dcfast_overcurrent_tempspoof.yaml   # the headline demo
│   ├── hub_mass_command.yaml
│   └── microgrid_freq_push.yaml
└── cli.py                 # run a scenario headless → trace.json
```

### 6.1 Target interface (the contract every plugin honours)

```python
class Target(Protocol):
    def read(self) -> dict: ...                  # sensor readings (attack may have altered these upstream)
    def apply_command(self, field: str, value) -> None: ...
    def step(self, dt: float) -> list[Event]: ...# advance physics, emit events
    def true_state(self) -> dict: ...            # ground truth (never visible to control/monitor)
```

Keeping `true_state` separate from `read` is what makes sensor-spoof attacks meaningful.

---

## 7. Build order (so you always have something that runs)

Each phase ends with something demoable.

- **Phase 1 — headless core.** Event store, clock, DC-fast charger + battery thermal, one attack (overcurrent + temp spoof). Output `trace.json`. *Demoable: the numbers from the deck, reproducible.*
- **Phase 2 — hub + scoring.** Add `hub_feeder`, the mass-command attack, impact scoring. *Demoable: "one command → 174% transformer."*
- **Phase 3 — monitor.** Physics-aware detector with its own model; detection-delay metric. *Demoable: alert fires ~3 min in.*
- **Phase 4 — 3D.** FastAPI streams events; R3F scene with nodes, links, heat ramp, timeline scrubber. *Demoable: the elegant visual.*
- **Phase 5 — breadth.** More chargers/microgrids and more attacks, each a new plugin/YAML. Swap in PyBaMM/pandapower.

---

## 8. Scenario file example (the headline demo)

```yaml
name: DC-fast overcurrent, temperature spoofed
ambient_C: 35
target:
  type: charger_dcfast
  pack:   { C: 450000, R: 0.10, cool_low: 150, cool_high: 300 }
  limits: { normal_A: 125, max_A: 250 }
hub:
  type: hub_feeder
  chargers: 1
  transformer_kVA: 500
  impedance_pu: 0.05
attacks:
  - id: A-OVERCURRENT
    entry_point: cyber.backend_link
    mechanism: command_override
    field: charging_profile.limit_A
    to: 250
    start_s: 60
  - id: A-TEMPSPOOF
    entry_point: cyber.sensor_bus
    mechanism: sensor_spoof
    field: sensor.pack_temp_C
    hold_value: 30
    start_s: 60
monitor:
  physics_aware: { divergence_C: 3, model: { C: 430000, R: 0.11 } }
run_s: 2400
```

---

## 9. What to say about limits (keep it in the README and the demo)

- Lumped single-temperature battery model; no cell-level or spatial detail.
- Monitor shares the *form* of the plant model, so its detection time is optimistic; real model mismatch slows it.
- Hardware thermal cut-offs / fuses not yet modelled — add as a `safety_interlock` that trips at a set temp.
- Steady-state grid math (algebraic), not full dynamic power-flow, until pandapower is wired in.
- Attack entry is modelled as "a wrong value on a link"; obtaining that access in reality is out of scope by design.

---

## 10. Stretch goals

- Replace models with PyBaMM (battery) and pandapower (grid); keep interfaces fixed.
- Monte-Carlo over ambient temp / impedance to produce an impact *distribution*, not one number.
- A ranked "attack impact leaderboard" across all scenarios — directly answers the PS's "rank by physical effect."
- Export each run as a shareable 3D replay.
