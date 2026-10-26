# SparkTrail — Implementation Specification

**What this is:** a build spec for SparkTrail, a *simulation* where a user picks tampering actions against a modelled EV charger / microgrid, runs it, and sees the physical damage that results — what overheated or overloaded, how bad, and how long it took.

**What this is not:** a real attack tool. Nothing here touches a real charger, backend, or vehicle. Every "attack" is a value changed inside a software model so the user can *see the physical consequence*. How a real attacker would gain access to a link is deliberately out of scope.

---

## 0. The user flow (the whole product in three steps)

```
STEP 1  Choose attack commands        →  e.g. "set charging limit to 250 A"
STEP 2  Override features / sensors    →  e.g. "force pack-temp sensor to read 30 °C"
STEP 3  Run → see the damage report    →  what broke, how bad, how long it took
```

A clarification worth keeping in your head: **Step 1 and Step 2 are the same mechanism** — injecting a wrong value somewhere in the model. Step 1 changes a *command* the system obeys; Step 2 changes a *reading* the system trusts. The UI presents them as two pickers because that's intuitive, but internally both produce the same kind of `Injection` object (§3).

---

## 1. STEP 1 — Choose attack commands

The user first picks a **target** (which charger / microgrid), then adds one or more **command injections** — values the system will be forced to obey.

### 1.1 Targets the user can pick

| Target | Power | Why pick it | Priority |
|---|---|---|---|
| **DC fast charger (50–150 kW)** | 50–150 kW | richest thermal risk, clearest demo | **P0** |
| **DC ultra-fast / HPC (150–350 kW)** | 150–350 kW | liquid-cooled, high stakes | P1 |
| **AC Level 2 (7–22 kW)** | 7–22 kW | common home/workplace unit | P1 |
| **Bidirectional / V2G charger** | 11–50 kW | can push power back to grid | P1 |
| **Single-feeder charging hub (N chargers + 1 transformer)** | site | shows grid-level overload | **P0** |
| **Islanded microgrid (PV + battery + diesel)** | site | frequency/voltage effects | P1 |

### 1.2 Command injections the user can choose

Each is a control value the system will accept and act on.

| Command | Field changed | Example value | Hits which target |
|---|---|---|---|
| **Raise charging current limit** | `charging_profile.limit_A` | 125 → **250 A** | any charger |
| **Raise charging power setpoint** | `charging_profile.power_kW` | 20 → **60 kW** | any charger |
| **Disable charge derating** | `control.derate_enabled` | on → **off** | any charger |
| **Disable active cooling** | `control.cooling_enabled` | on → **off** | DC / HPC |
| **Mass max-power command** | `hub.broadcast_power_kW` | → **max on all N** | hub |
| **Suppress load-shed signal** | `hub.load_shed` | sent → **dropped** | hub |
| **Shift inverter frequency setpoint** | `inverter.freq_setpoint_Hz` | 50.0 → **50.5 Hz** | microgrid |
| **Shift inverter voltage setpoint** | `inverter.voltage_setpoint_pu` | 1.00 → **1.06 pu** | microgrid |

Each selection becomes an `Injection` with `kind: command`.

---

## 2. STEP 2 — Override features / sensors

Now the user can tamper with what the system *sees or assumes*, so the attack from Step 1 goes unnoticed. These are what make a command dangerous.

| Override | Field changed | Example | Effect |
|---|---|---|---|
| **Spoof pack-temperature sensor** | `sensor.pack_temp_C` | hold at **30 °C** | BMS thinks it's cool, never derates or cools |
| **Spoof current sensor** | `sensor.current_A` | report low | hides the overcurrent from logs |
| **Spoof voltage reading** | `sensor.voltage_pu` | hold at 1.00 | hides a sag or swell |
| **Spoof State-of-Charge** | `sensor.soc_pct` | hold mid-range | hides an over/undercharge |
| **Freeze a stale "OK" state (replay)** | `sensor.status` | replay "normal" | safety logic stays idle |
| **Shift ambient assumption** | `env.ambient_C` | 25 → 45 | model runs hotter |
| **Disable a safety interlock flag** | `safety.interlock_enabled` | on → off | removes the hardware cut-off from the model |

Each selection becomes an `Injection` with `kind: sensor_spoof` (or `replay` / `flag`).

> The pattern: **Step 1 pushes the system too hard; Step 2 blinds the part that would have stopped it.** The headline demo is "raise to 250 A" + "spoof temp to 30 °C" together.

---

## 3. How a selection is represented

Both steps produce the same object, so the engine treats them uniformly:

```yaml
injection:
  id: INJ-01
  step: 1                      # 1 = command, 2 = feature/sensor (UI grouping only)
  kind: command               # command | sensor_spoof | replay | flag
  entry_point: cyber.backend_link   # which modelled link the value enters on
  field: charging_profile.limit_A
  to: 250                     # new value (or hold_value for a spoof)
  start_s: 60                 # when it begins, in sim seconds
```

A full run is just a list of these plus the chosen target. Example:

```yaml
run:
  target: charger_dcfast
  ambient_C: 35
  injections:
    - { kind: command,     field: charging_profile.limit_A, to: 250, start_s: 60 }   # Step 1
    - { kind: sensor_spoof, field: sensor.pack_temp_C,      hold: 30, start_s: 60 }   # Step 2
  run_s: 2400
```

---

## 4. STEP 3 — The damage report

When the user hits **Run**, the engine steps the simulation second-by-second and produces a report answering the user's three questions: **what broke, how bad, how long.**

### 4.1 What the report shows

| Section | Contents |
|---|---|
| **Components damaged** | each affected part with a status: `ok` / `stressed` / `damaged`, and the peak value it reached |
| **How bad** | peak temperature, peak current, transformer load %, voltage/frequency deviation vs a normal baseline |
| **How long** | time from attack start to each threshold crossing (e.g. "reached 55 °C at 39:01"), and total time in the danger zone |
| **Detected?** | whether the physics-aware monitor (§6) caught it, and after how long |
| **Trace** | the hop-by-hop event list: forged command → control reaction → physical change → threshold crossing |

### 4.2 Example report (250 A + temp spoof on a DC-fast charger)

```
COMPONENTS
  Battery pack ....... DAMAGED    peak 55.4 °C   (normal 38.5 °C)
  Charging cable ..... STRESSED   peak 71 °C
  Hub transformer .... ok         38% load (single charger)

HOW LONG
  crossed 45 °C  at  14:40
  crossed 55 °C  at  39:01
  time in danger zone (>45 °C):  25 min

DETECTION
  physics-aware monitor ALERTED at 03:59  (spoof caught ~3 min in)

IMPACT SCORE  8.4 / 10   (fast onset, pack damage, delayed detection)
```

For the hub target, the same report instead shows the transformer at **174% load** and **8.7% voltage drop** when all 12 chargers are commanded to max.

### 4.3 Impact score

A single number so the user can compare attacks:

```
score = w1·(peak deviation)  +  w2·(1 / time-to-impact)  +  w3·(# components damaged)  +  w4·(detection delay)
```

Faster onset, more components, later detection → higher score. This is what fulfils "rank attacks by physical impact."

---

## 5. Physics models (what turns an injection into damage)

Keep each model in its own module; the user never edits these, the engine runs them.

**Battery / pack thermal** (P0):
```
dT/dt = ( I²·R  −  h·(T − T_ambient) ) / C
```
- `I` from control logic (driven by the possibly-spoofed readings), `R` internal resistance, `h` cooling (raised only when *reported* temp is high), `C` heat capacity.

**Cable / converter thermal:** same I²R form, own `R` and cooling.

**Hub transformer / feeder:**
```
load_pct   = 100 · P_total / S_rated
v_drop_pct = 100 · Z · P_total / S_rated
```

**Microgrid frequency (islanded):**
```
df/dt = ( P_gen − P_load ) / (2·H·S_base)
```

Later: swap these for **PyBaMM** (battery), **pandapower** (grid) behind the same interface.

---

## 6. The one piece of defense: physics-aware monitor

Runs a **second, independent** thermal model off the *measured current* and compares it to the *reported* temperature. If they diverge by more than a threshold (e.g. 3 °C), it raises an alert in the trace. It only alerts — it never blocks.

> Keep its `R/C/h` different from the plant's, or the detection time is fake. Report the delay honestly.

---

## 7. 3D simulation & visualization

An elegant 3D scene where the chosen attack visibly travels from a network node to a glowing-hot component, synced to the damage timeline.

**Stack:** Three.js + React Three Fiber (browser) with a Python/FastAPI backend streaming events over WebSocket. (PyVista if you want pure-Python offline.)

**Scene:**
- **Nodes as low-poly 3D objects:** backend (server), charger (pillar), battery (pack), transformer (box), microgrid bus (ring).
- **Links as tubes;** an injection is an emissive pulse travelling from its entry point to the target.
- **Damage as colour:** `pack_temp` → blue→amber→red ramp on the battery mesh; transformer overload pulses red; voltage drop dims the bus ring.
- **Timeline scrubber** bound to sim time; drag to replay. Side panel shows the live trace and the damage report building up.

**Polish rules:** one accent colour for "attack", one ramp for "heat", one for "electrical stress" — no more than three. Ease all motion. Pulses travel ~1–2 s per hop. Dark scene, high-contrast labels.

---

## 8. Software architecture

```
sparktrail/
├── core/
│   ├── events.py        # Event dataclass, store, DiGraph builder (the trace)
│   ├── clock.py         # fixed-step loop (dt = 1 s)
│   └── run.py           # loads a run (target + injections) → objects
├── targets/
│   ├── base.py          # Target interface (read / apply_command / step / true_state)
│   ├── charger_dcfast.py   # P0
│   ├── hub_feeder.py       # P0
│   └── ...
├── physics/             # battery_thermal, feeder, swing
├── control/             # bms (reads sensors), hub_controller
├── injections/
│   ├── schema.py        # the §3 Injection object + validation
│   └── engine.py        # applies injections to the right link at the right time
├── monitor/physics_aware.py
├── report/
│   ├── damage.py        # builds the Step-3 report from the trace
│   └── scoring.py       # impact score
├── api/server.py        # FastAPI: run + stream events
├── viz3d/               # React Three Fiber front-end (pickers + scene + report)
└── runs/                # saved YAML runs, incl. the headline demo
```

**Target interface** (keeps sensor-spoof meaningful — `true_state` is never shown to control or monitor):
```python
class Target(Protocol):
    def read(self) -> dict: ...            # readings (an injection may have altered these)
    def apply_command(self, field, value) -> None: ...
    def step(self, dt: float) -> list[Event]: ...
    def true_state(self) -> dict: ...      # ground truth, hidden from control/monitor
```

---

## 9. Build order (always something runnable)

- **Phase 1 — core + one chain.** Event store, clock, DC-fast charger + battery thermal, the two headline injections, a text damage report. *Demoable: the deck's numbers, reproducible.*
- **Phase 2 — hub + scoring.** Add hub_feeder, mass-command, transformer load, impact score. *Demoable: "one command → 174%."*
- **Phase 3 — monitor + report UI.** Physics-aware detector, full damage report. *Demoable: alert fires ~3 min in.*
- **Phase 4 — 3D.** FastAPI stream + R3F scene with the two pickers, heat ramp, scrubber. *Demoable: the elegant visual.*
- **Phase 5 — breadth.** More targets and injections (each a plugin/YAML); swap in PyBaMM / pandapower.

---

## 10. Honest limits (keep in README + demo)

- Lumped single-temperature battery model; no cell-level detail.
- Monitor shares the *form* of the plant model → optimistic detection time; real mismatch is slower.
- Hardware thermal fuses only modelled if the user adds the `safety.interlock` override.
- Steady-state grid math until pandapower is wired in.
- Injection = "a wrong value on a link"; gaining that access in reality is out of scope by design.