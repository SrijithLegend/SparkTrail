# SparkTrail — Multi-Domain Cyber-to-Physical Impact Simulator

**Build spec for the multi-domain expansion.** This extends the existing EV-charger
engine (`Tracer`, `PhysicsProxy`, `SensorFusionValidator`, `viz3d/`) to cover the
whole class of cyber-physical infrastructure, wrapped in a TVA-styled playground.

---

## 0. What this is — and the hard scope line

SparkTrail is a **visibility and education tool**. It answers one question: *when a
digital signal to a physical process is corrupted, what breaks, how fast, and what
could have caught it?* It runs entirely on **models**. Nothing touches real hardware.

An "attack" in SparkTrail is **an out-of-range value placed on a modelled link at
time T** — never a real exploit, a protocol sequence, or a device-specific command.
The educational payload is the **physical propagation and the defense**, not how an
attacker would gain access. That boundary is load-bearing; the whole product is built
around it.

**Two deliberate design rules that follow from that line:**

1. **Playable domains are OT / infrastructure only** — the consequence lands on
   *equipment and process* (a transformer, a tank, a robot cell), not on a human
   body. These are the canonical cyber-physical domains and the right fit for a
   physics-aware-defense demo.
2. **The "attack menu" is an abstract manipulation taxonomy**, taken from the public
   **MITRE ATT&CK for ICS** framework — categories, not recipes — and each scenario is
   anchored to a **publicly documented incident**. No scenario describes an operational
   mechanism.

Domains where the harm is to people (implanted medical devices, occupied vehicles,
aircraft) appear as a **non-playable case-study gallery** (§10): context that proves
the pattern generalizes, with citations to public reporting — no harm animation, no
command list.

---

## 1. Product flow (what the user does)

```
┌────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐   ┌────────────┐
│ 1. Domain  │ → │ 2. Scene     │ → │ 3. Pick a     │ → │ 4. Run +     │ → │ 5. Case    │
│    select  │   │    loads     │   │  manipulation │   │  watch 3D    │   │  file      │
│ (TVA desk) │   │ (3D rig)     │   │  (from menu)  │   │  propagation │   │  (report)  │
└────────────┘   └──────────────┘   └───────────────┘   └──────────────┘   └────────────┘
```

1. **Domain select** — a TVA "case intake" drawer of infrastructure domains (§3).
2. **Scene loads** — the domain's 3D rig appears in the main playground (the TVA screen).
3. **Pick a manipulation** — a short, plain-English list of manipulation *categories*
   that apply to this domain (§4), each with a one-line description of the *consequence*
   it is known to cause.
4. **Run** — the engine simulates it; the 3D scene animates the propagation
   (node lights by depth, spark-trail bead, consequence meters climb to red).
5. **Case file** — a report: what moved physically, the peak values, the timeline,
   whether a defense caught or blocked it, and the public incident it mirrors.

Every screen is TVA-skinned (§6). The whole thing is one click per step — no config,
no code, no jargon the user has to decode.

---

## 2. Architecture — generalize, don't rewrite

The EV engine already has the right bones. We add a **domain registry** and a
**Domain interface**; everything else (Tracer, proxy, fusion, viz3d, Streamlit) is reused.

```
sparktrail/
  events.py          Tracer + Event        (UNCHANGED — causal graph, depth, JSON)
  proxy.py           PhysicsProxy          (generalize limits to be per-domain)
  detector.py        PhysicsMonitor + SensorFusionValidator (reused per-domain)
  domains/
    __init__.py      REGISTRY: dict[str, Domain]
    base.py          Domain, Scene, Scenario, ConsequenceMetric  (new interfaces)
    ev_hub.py        existing EV physics, wrapped as a Domain
    power_sub.py     power substation / feeder
    water.py         water-treatment dosing + tank level
    robot_cell.py    manufacturing robot cell (unoccupied)
    hvac.py          building HVAC / cold-storage
    pipeline.py      pumping station / pressure
  simulate.py        generic run(domain, scenario) -> trace   (refactor of run_session/run_hub)
  injector.py        loads a (domain, scenario) and writes trace.json  (extend)
scenarios/
  <domain>/*.yaml    abstract injection definitions, one folder per domain
viz3d/
  scenes/<domain>.json   node/link layout per domain (replaces single scenes.json)
  models/<domain>/*.glb  downloaded 3D models (§5)
  index.html             domain-aware loader (reads ?domain= / dropdown)
app.py                   Streamlit TVA console, domain selector added
```

### The `Domain` interface (`domains/base.py`)

```python
@dataclass
class ConsequenceMetric:
    key: str            # "pack_temp_c", "transformer_load_pct", "tank_level_pct"
    label: str          # "Pack temperature"
    unit: str           # "°C"
    safe_max: float     # red line for the UI meter
    normal: float       # baseline value

@dataclass
class Scenario:
    id: str
    title: str                  # plain-English, consequence-framed
    description: str            # one line: what physically happens
    mitre_ics: str              # taxonomy tag, e.g. "T0836 Modify Parameter"
    incident_ref: str           # public incident this mirrors (name + year)
    injection: dict             # abstract: {link, setpoint, value, at_s, spoof:{...}}
    proxy_enabled: bool = False
    fusion_enabled: bool = True

class Domain(Protocol):
    id: str
    title: str
    scene_file: str                       # viz3d/scenes/<id>.json
    metrics: list[ConsequenceMetric]
    def scenarios(self) -> list[Scenario]: ...
    def run(self, sc: Scenario) -> dict:  # returns {tracer, series, consequence, flags}
        ...
```

A domain's `run()` builds a `Tracer`, steps its own physics model, emits
`attack → cyber → control → physics → monitor` events exactly like the EV engine,
and optionally routes commands through `PhysicsProxy.guard()` and sensor readings
through `SensorFusionValidator.guard()`. **The trace format is identical across
domains**, so `viz3d/` and the Streamlit log work unchanged.

---

## 3. Playable domains

Each is an infrastructure process where a corrupted setpoint or spoofed sensor drives
equipment past a physical limit. For each: the 3D scene nodes, a one-line physics
model, its consequence metric, the manipulation categories that apply, and the public
incident it mirrors. **No operational detail** — the injection is always an abstract
value on a link.

### 3.1 EV charging hub *(existing — already built)*
- **Nodes:** ATTACKER → CSMS → CP_1…CP_n → BMS → PACK → TRANSFORMER; MONITOR, FUSION.
- **Physics:** lumped battery thermal `C dT/dt = I²R − h(T−T_amb)`; hub load `100·P/S_rated`.
- **Consequence:** pack temperature (°C), transformer loading (%), bus voltage drop (%).
- **Incident anchor:** OCPP/charger-security research disclosures (public, 2021–2023).

### 3.2 Power substation / feeder
- **Nodes:** ATTACKER → SCADA → RTU → BREAKER / TAP_CHANGER → FEEDER → LOADS.
- **Physics:** feeder power balance; a breaker-open or bad tap setpoint sheds/overloads load; simple `V = 1 − Z·P/S` bus estimate.
- **Consequence:** served load (MW), bus voltage (pu), customers dropped.
- **Incident anchor:** **Ukraine grid, 2015/2016** (remote breaker operation → blackout).

### 3.3 Water treatment
- **Nodes:** ATTACKER → HMI → PLC → DOSING_PUMP / VALVE → TANK → OUTFLOW.
- **Physics:** tank mass balance `dL/dt = Qin − Qout`; dosing concentration setpoint vs a safe band.
- **Consequence:** tank level (%), dosing concentration vs safe band, overflow/dry flag.
- **Incident anchor:** **Oldsmar, FL, 2021** (dosing setpoint pushed out of safe range; caught by an operator).

### 3.4 Manufacturing robot cell *(unoccupied)*
- **Nodes:** ATTACKER → CELL_CTRL → PLC → ROBOT_AXIS / CONVEYOR → PART; SAFETY_ZONE sensor.
- **Physics:** position/offset model — an injected sub-range offset accumulates into an out-of-tolerance part; interlock state.
- **Consequence:** positional error (mm), parts out of tolerance, interlock tripped (y/n).
- **Incident anchor:** ICS robotics-security research (public academic demonstrations).

### 3.5 Building HVAC / cold storage
- **Nodes:** ATTACKER → BMS → CONTROLLER → CHILLER / DAMPER → ZONE / COLDROOM.
- **Physics:** first-order zone temperature toward a (possibly corrupted) setpoint; cold-room excursion timer.
- **Consequence:** zone/cold-room temperature (°C), minutes outside safe band.
- **Incident anchor:** building-automation compromise via third-party BMS access (public breach reporting).

### 3.6 Pumping / pipeline station
- **Nodes:** ATTACKER → SCADA → PLC → PUMP / PRV → SEGMENT; PRESSURE sensor.
- **Physics:** segment pressure vs pump speed setpoint; relief-valve state; over/under-pressure band.
- **Consequence:** line pressure (bar), seconds over the pressure limit, relief activations.
- **Incident anchor:** pipeline-sector disruption reporting (public, 2021).

---

## 4. The manipulation taxonomy (the "menu", done safely)

Instead of a per-domain list of harm-causing commands, the menu is a fixed set of
**abstract manipulation categories** mapped to **MITRE ATT&CK for ICS**. Each domain
exposes the subset that applies to it. The user picks a *category*; the engine applies
the matching abstract injection defined in that domain's scenario YAML.

| # | Category (UI label) | MITRE ICS | What it does, abstractly | Defense that catches it |
|---|---|---|---|---|
| 1 | **Push a setpoint out of range** | T0836 Modify Parameter | A control value is driven past its safe band | Physics proxy (hard-limit check) |
| 2 | **Freeze / fake a sensor** | T0856 Spoof Reporting Message | A reading is pinned to a safe-looking value while the process drifts | Sensor-fusion cross-check |
| 3 | **Broadcast a mass command** | T0831 Manipulation of Control | Many devices driven at once past an aggregate limit | Proxy aggregate-limit check |
| 4 | **Suppress a protection signal** | T0878 Alarm Suppression / T0804 | A safety/alarm/shed signal is dropped | Proxy refuses to drop safety signals |
| 5 | **Replay / delay a command** | T0839 Module Firmware / T0857 | A stale value is re-applied or held past validity | Residual monitor (model vs reported) |

- Each menu item shows: the plain label, a one-line **consequence** ("tank overfills",
  "transformer overloads"), the **MITRE tag** (credibility for judges), and the
  **incident** it mirrors.
- "Most likely" ranking = order the categories per domain by how directly they hit that
  domain's consequence metric. This replaces "top 10 harm commands" with a defensible,
  framework-backed ranking of *consequence severity*, not attack efficacy.

**Scenario YAML (abstract injection — the only "attack" representation):**
```yaml
# scenarios/water/dosing_setpoint_out_of_band.yaml
domain: water
title: "Dosing setpoint pushed out of safe band"
mitre_ics: "T0836 Modify Parameter"
incident_ref: "Oldsmar water treatment, 2021"
injection:
  link: "PLC->DOSING_PUMP"     # a modelled link, not a real bus
  setpoint: "dose_ppm"
  value: 11000                 # out-of-band value, abstract
  at_s: 60
proxy_enabled: false           # flip true for the 'defended' variant
fusion_enabled: true
```

---

## 5. 3D models — sourcing from the internet

Good models, properly licensed, loaded as glTF/`.glb`.

- **Source:** Sketchfab (filter **Downloadable + CC**), Poly Pizza, Khronos glTF sample
  assets. Prefer **CC0 / CC-BY**; keep an `ATTRIBUTION.md` in `viz3d/models/` listing
  each model, author, and licence. (Container network is allowlisted; if a host is
  blocked, I'll flag it and you drop the `.glb` into `viz3d/models/<domain>/` yourself.)
- **Format:** `.glb` only (single-file, embeds textures). Convert `.gltf`/`.obj`/`.fbx`
  with `gltf-pipeline` / `obj2gltf` if needed.
- **Per domain, grab:** the signature device (charger, transformer, pump, robot arm,
  chiller, valve stand) + a generic controller box + a tank/pipe primitive.
- **Loader:** `GLTFLoader` from the already-vendored three.js (`viz3d/vendor/`). Each
  `scenes/<domain>.json` node gets an optional `"model": "models/<domain>/x.glb"`;
  nodes without one fall back to the current emissive sphere, so the scene always
  renders even before models land.
- **Budget:** keep each `.glb` under ~2–3 MB; `draco`-compress if heavier. Lazy-load per
  domain so the first paint stays fast.

---

## 6. TVA playground UI

Reuse the existing TVA design tokens (`--paper #D6BF96`, `--walnut #2B1E12`,
`--amber #F0A836`, `--cream #F0E4CA`; Oswald/Bahnschrift display, IBM Plex Mono data).

- **Main playground = the TVA screen.** The 3D scene sits inside a CRT-bezel frame
  (amber phosphor glow, faint scanlines, vignette) — the "Temporal Loom" monitor. The
  propagation animation plays *on* this screen.
- **Domain select = "Case Intake" drawer.** Left rail of stamped file tabs, one per
  domain, each with a seal and a case number. Selecting one slides the scene in.
- **Manipulation menu = "Requisition form."** The §4 categories as form rows with a
  typewriter-stamp "EXECUTE" button (reuse the existing distressed-stamp asset).
- **Case file = the report.** A stamped dossier: consequence meters (climbing to a red
  TVA "VARIANCE DETECTED" state), the event timeline as a ticker log, the incident
  citation as a "PRIOR OCCURRENCE" footnote.
- **Motion/sound:** amber bead spark-trail along links (already built), Nixie-style
  rolling counters for the consequence metrics, soft analog clunk on stamp. Keep it
  smooth: all transitions eased, 60fps target, no layout jank.

---

## 7. Driving the effect animation from the trace

The trace already carries everything the animation needs — no new data model.

1. **On run**, `injector.inject(domain, scenario)` writes `trace.json`
   (`node_depths`, `events[]` with `t`, `propagation_depth`, `source_node`, `detail`).
2. **Scene build** colours each node by `node_depths` (root red → direct orange →
   cascade yellow → idle slate), same as now, but on the loaded `.glb` material
   (set `emissive`), falling back to the sphere.
3. **Timeline scrub:** the replay button walks events in `t` order; as each physics
   event fires, its node pulses and the matching consequence meter animates toward the
   event's reported value. The spark-trail bead travels the causal link
   (`cause → event`) staggered by `propagation_depth * delay`.
4. **Red-line moment:** when a metric crosses `safe_max`, the CRT frame flashes the TVA
   variance state and the case-file header stamps "VARIANCE". If a defense fired
   (`proxy.reject` / `monitor.sensor_spoof`), show the block/catch instead and keep the
   process in-band.
5. **Defended vs undefended** is the money shot: run the same scenario with
   `proxy_enabled` on/off and show both consequence curves side by side.

---

## 8. Build order + repo push checkpoints

Push to `github.com/SrijithLegend/<repo>` at each ✅. *(I can't reach your repo from
this container unless it's attached; I'll commit locally at each checkpoint and tell
you what's ready to push, or push once the repo is connected.)*

1. ✅ `domains/base.py` + registry; wrap existing EV engine as `domains/ev_hub.py`;
   refactor `simulate.run(domain, scenario)`. Everything still green on EV.
2. ✅ `viz3d` becomes domain-aware (dropdown + `?domain=`, per-domain `scenes/*.json`,
   glTF loader with sphere fallback). EV scene renders through the new path.
3. ✅ Add `power_sub` + `water` domains with physics, scenarios, scenes. Two new
   playable domains end-to-end.
4. ✅ Add `robot_cell`, `hvac`, `pipeline`. All six playable.
5. ✅ Download + wire `.glb` models per domain (+ `ATTRIBUTION.md`).
6. ✅ TVA skin pass on playground, intake drawer, requisition form, case file.
7. ✅ Consequence-meter animation + defended/undefended compare view.
8. ✅ §10 case-study gallery (static, cited). README + honest-limits pass.

---

## 9. Honest limits (put these in the README and say them to judges first)

- Every physics model is **lumped / first-order** — directionally right, not
  engineering-accurate. A real transformer, tank, or robot cell is far more complex.
- The **defenses share the plant model's form**, so their catch/block times look
  optimistic; real model mismatch makes detection slower and noisier.
- An **"injection" is a value on a modelled link.** How an attacker would actually
  reach that link is deliberately out of scope — this tool shows *impact and defense*,
  not intrusion.
- Domains are **archetypes**, not models of any specific real facility.
- The case-study gallery (§10) is **reporting, not simulation** — no physics behind it.

---

## 10. Case-study reference gallery (non-playable, cited)

A static "Prior Occurrences" wall proving the pattern spans beyond infrastructure.
Each card: domain, the public incident, the one-line physical consequence, a citation.
**No simulation, no animation, no mechanism** — context only.

- **Industrial safety systems** — Stuxnet (2010): spoofed "normal" readings while
  centrifuges were driven to physical failure. *(The archetype for sensor-spoof + overdrive.)*
- **Power grid** — Ukraine (2015/2016): remote breaker operation → ~230k people lost power.
- **Water** — Oldsmar, FL (2021): dosing setpoint pushed out of safe range; caught manually.
- **Fuel logistics** — Colonial Pipeline (2021): IT ransomware → precautionary physical
  shutdown → regional fuel shortage.
- **Automotive** — Jeep remote-control research (2015): networked entry reached
  drive-critical systems. *(Human-harm domain: cited, not simulated.)*
- **Maritime / aviation** — GPS/GNSS spoofing: navigation led off course.
  *(Human-harm domain: cited, not simulated.)*
- **Medical devices** — connected insulin pumps / pacemakers: research disclosures and
  FDA recalls over remote-command risk. *(Human-harm domain: cited, not simulated.)*

**The through-line (one sentence for the pitch):** across every one of these, the
control layer *trusted a command or a sensor instead of checking it against physics* —
which is exactly the gap SparkTrail's proxy and fusion validator close, in any domain.
