# SparkTrail

A **simulation** that traces how a cyber event on EV-charging / microgrid
infrastructure propagates into physical effects (temperature, current, voltage,
frequency) and renders the propagation path in 3D.

It never touches a real charger, backend, or vehicle. Everything is a software
model. An "attack" is an abstract event — *a bad value appears on this modelled
link at time T* — injected so you can observe and rank its physical
consequences. How a real attacker would obtain that access is out of scope by
design.

## Run it

```bash
pip install -r requirements.txt

# headless: one scenario -> trace.json + printed summary
python -m sparktrail.cli scenarios/dcfast_overcurrent_tempspoof.yaml

# build the compact timeline the 3D viewer replays (all scenarios)
python -m sparktrail.viz

# self-checks
python test_sparktrail.py
```

The 3D viewer is `viz3d/index.html`; it loads `viz3d/scenes.json` from the same
folder. Serve the folder (`cd viz3d && python -m http.server`) or open the
published artifact. Drag to orbit, scroll to zoom, **click a node to focus**,
`⟲` to reset, step/▶/speed on the transport bar, dropdown to switch scenarios.

## Coverage

**All 6 charger types** (`targets/charger.py`, one parametrized plugin):
AC Level 1, AC Level 2, DC fast, DC ultra-fast / HPC (liquid coolant node),
battery-buffered (buffer SoC), bidirectional / V2G (export).

**All 5 microgrid types** (`targets/microgrid.py`): single-feeder hub,
LV distribution (with PV), islanded (frequency via swing), microgrid with BESS,
campus/fleet depot.

**All 7 attack mechanisms** (`attacks/`): `command_override`, `sensor_spoof`,
`setpoint_drift`, `mass_command`, `dos_blackhole`, `replay`, `desync`.

**All 6 entry points**: `backend_link`, `vehicle_link`, `sensor_bus`,
`hub_controller`, `inverter_link`, `firmware_state`.

**All physical effects**: pack temp (true vs reported), coolant temp (HPC),
current, transformer load %, bus voltage % (under/overvoltage), frequency
(nadir / peak / RoCoF), BESS SoC, V2G export power.

## How it's wired

- **Event store** (`core/events.py`) — one append-only log; `caused_by` links
  events into a propagation `networkx.DiGraph`. The trace *is* the product.
- **Plant vs. monitor separation** — the physics-aware monitor
  (`monitor/physics_aware.py`) runs a *different* R/C model and only alerts,
  never blocks; detection delay reported honestly.
- **Impact scoring** (`scoring/impact.py`) — ranks a scenario by physical effect
  (peak temp, load, voltage excursion, frequency excursion, speed, nodes).
- **3D tracer** (`viz3d/`) — Three.js scene: type-aware node shapes, link tubes,
  additive attack pulses, heat ramp, overload glow, islanded ring / PV / BESS
  decor, live gauges, timeline scrubber, `modelled`/`illustrative` flags.

### Scenarios (`scenarios/*.yaml`) — the §2.3 attack set, across types
| File | Chain · attack |
|---|---|
| `dcfast_overcurrent_tempspoof.yaml` | DC-fast · overcurrent + temp spoof (headline, 57 °C). |
| `cooling_suppression.yaml` | DC-fast · temp read low, cooling never engages. |
| `ac_level1.yaml` / `ac_level2.yaml` | AC L1 / L2 · overcurrent. |
| `hpc_overcurrent_tempspoof.yaml` | HPC 350 kW · overcurrent, coolant climbs (pack 77 °C). |
| `buffered_overcurrent.yaml` | Battery-buffered · overcurrent drains the buffer. |
| `v2g_forced_export.yaml` | V2G · vehicle-link forced into export. |
| `hub_mass_command.yaml` | Single-feeder · mass max-power → ~174 % transformer. |
| `hub_loadshed_suppression.yaml` | Single-feeder · dropped load-shed → overload pinned. |
| `desync_loadshed.yaml` | Single-feeder · shed signal 90 s late → recurring overload. |
| `lv_distribution_masscommand.yaml` | LV distribution · mass command overwhelms the PV offset. |
| `depot_mass.yaml` | Fleet depot · mass command across 20 DC chargers. |
| `microgrid_freq_push.yaml` | Islanded · inverter frequency setpoint pushed to 51.5 Hz (#7). |
| `microgrid_bess_freq.yaml` | BESS · same push, BESS holds it to ~50.9 Hz. |
| `microgrid_overvoltage_drift.yaml` | Islanded · voltage setpoint drifts up to ~110 % (#6). |

## Honesty in the UI
Every physical number is flagged `modelled` (from a real model) or
`illustrative` (hand-set). The monitor uses a *different* R/C from the plant,
so its detection time isn't faked by sharing the plant's model.

## Limits (by design)
- Lumped single-temperature battery model; no cell-level or spatial detail.
- Monitor shares the *form* of the plant model, so its detection is optimistic.
- Steady-state feeder math (algebraic); single-bus swing for frequency.
- Governor / droop constants are illustrative, hand-tuned (marked in code).
- Hardware thermal cut-offs / fuses modelled only as a firmware flag.
- Attack entry is "a wrong value on a link"; obtaining that access is out of scope.

## Stretch (interfaces are fixed, so these are drop-in)
- Swap models for PyBaMM (battery) / pandapower (grid), same `Target` interface.
- FastAPI WebSocket streaming instead of `scenes.json` replay (`api/server.py`).
- Monte-Carlo over ambient / impedance for an impact *distribution*.
