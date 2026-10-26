# SparkTrail — TVA Design System & UI Spec

The whole simulation is styled as a **Time Variance Authority field terminal**: a 1970s government agency that processes time, running cosmic tech on worn analog hardware. Cool, glossy, "modern dashboard" is wrong. Warm, tactile, bureaucratic, amber-lit is right.

This spec pairs with `SparkTrail_IMPLEMENTATION.md` (the functional 3-step flow). That file says *what the app does*; this file says *what every pixel looks like*. Read them together.

**Framing stays the same:** nothing touches real hardware. "Attacks" are values injected into a model. The TVA skin reframes that flow as case work — pick a tampering action, file it, watch the damage logged — but the engine underneath is unchanged.

---

## 1. Design tokens (use these exact values)

### 1.1 Colour

```css
:root{
  /* surfaces — warm, faded, never pure */
  --paper:      #D6BF96;   /* main background, manila */
  --paper-2:    #C4A878;   /* panel fill */
  --walnut:     #2B1E12;   /* header/footer bars, deep panels */
  --brown:      #3A2A1A;   /* primary text on paper */
  --brown-2:    #5C4226;   /* metal casing */

  /* amber — the signature "powered / active" glow */
  --amber:      #F0A836;
  --amber-hi:   #FFCE6E;   /* highlights, active lamps */
  --orange:     #D67828;   /* drop-shadows, warnings */

  /* accents — use sparingly */
  --olive:      #787842;   /* secondary state */
  --teal:       #467874;   /* rare cool accent */
  --cream:      #F0E4CA;   /* text on dark bars */

  /* status */
  --danger:     #B03428;   /* stamps, ALERT, damaged */
  --ok:         #787842;
}
```

Rules:
- **70% warm neutral, 20% walnut/brown structure, 10% amber accent.** Amber is a spotlight, not a fill.
- Nothing is `#000` or `#fff`. Darkest is `--walnut`, lightest is `--cream`.
- Danger red appears **only** on stamps and ALERT states.

### 1.2 Type

| Role | Font | Fallback stack | Notes |
|---|---|---|---|
| **Display / wordmarks** | Bahnschrift (condensed) or Oswald | `"Bahnschrift","Oswald","Arial Narrow",sans-serif` | heavy, condensed, all-caps, tight tracking |
| **Headers / labels** | Bahnschrift SemiBold | same | all-caps, `letter-spacing: .08em` |
| **Readouts / data / CRT** | IBM Plex Mono or Consolas | `"IBM Plex Mono","Consolas",monospace` | all numbers, logs, form fields |
| **Body (rare)** | IBM Plex Mono | monospace | keep body text short; this UI is labels + data |

> Everything reads as **stamped, printed, or computed** — no soft modern geometric sans for data. Mono carries the "machine" feel.

Type scale (px): display 64/48, H1 34, H2 24, label 15 (caps), data 15–18 mono, caption 12.

### 1.3 Shape, texture, depth

- **Corners:** panels `border-radius: 6–10px`; screens `12–16px`. Nothing fully sharp, nothing pill-round except lamps.
- **Borders:** 2–4px, `--amber` or `--brown-2`. Double-line borders (outer + thin inner) for official plaques.
- **No flat fills.** Every surface gets: a subtle paper-grain noise overlay (`opacity .05`), a soft inner vignette, and warm drop shadows (`0 4px 0 rgba(0,0,0,.25)`, hard not blurry — like printed ink).
- **NO accent stripes or thin edge bars** — use plaques, stamps and seals to set things apart instead.

---

## 2. Global chrome (every screen)

- **Top bar** (`--walnut`, 64px, amber underline): left = `TIME VARIANCE AUTHORITY`, right = live `CASE FILE  TVA-###` + clock. Mono.
- **Indicator lamp row** under the top bar: 6 round amber lamps; lit ones glow (`box-shadow: 0 0 12px var(--amber-hi)`), reflecting live system state (sim running, alert raised, etc).
- **Bottom bar:** left = `CHENNAI INSTITUTE OF TECHNOLOGY · CSBS`, right = `AMBIENT 35°C · T +MM:SS` sim clock.
- **Agency seal** (the circular badge, §6) pinned top-right of the landing/title screen and on exported reports.
- **Background:** `--paper` with faint 64px grid (subtract-blend, very low opacity) + grain + corner vignette.

---

## 3. Screen-by-screen (the 3-step flow, TVA-skinned)

The functional flow is unchanged; only the metaphor and styling change.

### 3.1 Landing — "Case Intake"

- Full TVA title treatment (as the mockup): condensed `SPARKTRAIL` wordmark with an orange offset shadow, plaque subtitle `CYBER-TO-PHYSICAL IMPACT TRACING UNIT`, seal, CRT panel, stamp.
- Primary action is a chunky labelled button, not a flat CTA: `[ OPEN NEW CASE FILE ]` — beveled, `--amber` face, `--walnut` text, hard shadow, presses down 2px on click.

### 3.2 STEP 1 — "Requisition: Attack Commands"

Styled as filling out a **requisition form**.

- Target picker = a row of **ID-card tiles** (charger / hub / microgrid). Each tile: paper card, mono spec block, a small photo-less schematic icon, a punch-hole graphic in the corner. Selected tile gets a red `SELECTED` ink stamp across it.
- Command list = form rows with mono labels and physical-style inputs:
  - toggles rendered as **real switches** (sliding knob, amber when on),
  - numeric values as **segmented/Nixie-style readouts** (e.g. current limit `[2][5][0] A`) with up/down dials, not slider tracks.
- Each chosen command drops a line into a running **"FORM 29-B"** panel on the right (mono, like carbon copy).

### 3.3 STEP 2 — "Override: Sensor & Feature Falsification"

Same form language, visually distinguished as the **"tampering"** page — slightly darker panel, a red `CLASSIFIED` corner tab.

- Sensor overrides as gauge faces the user can falsify: the gauge shows the *spoofed* reading in amber with a small red `FORGED` tag, and the *true* value hidden behind a flip.
- Reinforce the concept in the UI copy: a one-line note under each override, e.g. *"BMS will trust this value."*

### 3.4 STEP 3 — "Case File: Damage Report"

The payoff screen, styled as a **stamped case file**.

- **Run button:** `[ ▸ EXECUTE TEMPORAL EVENT ]`, big amber, with a mechanical press + a short lamp-sweep animation while the sim steps.
- **Components damaged:** a table of ID-card rows; each component gets an ink status stamp — green `CLEARED`, amber `STRESSED`, red `DAMAGED` — rotated a few degrees like a real stamp.
- **How bad / how long:** large Nixie-style readouts for peak temp, load %, and time-to-threshold (`39:01`).
- **Detection:** a CRT panel replaying the trace log line by line (amber phosphor, scanlines, ALERT in red).
- **Impact score:** a big dial/meter, 0–10, needle swinging to the value, with a `VARIANT LOGGED` stamp slapping down on completion.
- **Export:** `[ FILE REPORT ]` → a PDF/PNG laid out as an official TVA case document.

---

## 4. The 3D scene (TVA-skinned)

The scene is the centrepiece: the attack visibly travels from a network node to a component that physically fails, on a retro-terminal diorama.

### 4.1 Look

- **Environment:** a dark walnut "control room" void with a warm amber key light and a faint grid floor. Not space, not neon — a lamp-lit workshop.
- **Nodes as analog devices**, low-poly, metal-and-amber:
  - backend = a server rack / reel-to-reel cabinet,
  - charger = a chunky pillar with a CRT face and lamps,
  - battery/EV = a ribbed pack that can glow with heat,
  - transformer = a finned metal box with a gauge,
  - microgrid bus = a ring console.
- **Materials:** brushed metal (low metalness, mid roughness), enamel paint, wood veneer accents, amber-emissive screens and lamps. No chrome, no glass, no iridescence.

### 4.2 Showing the attack and the damage

- **Injection pulse:** an amber energy bead travels along a tube/cable from entry node to target, ~1–2 s per hop, easing. A faint afterglow trail marks the path already taken (the "spark trail").
- **Heat:** map `pack_temp_C` to an emissive ramp on the battery mesh — `--teal`→`--amber`→`--danger` — plus rising heat-shimmer and a lamp on the unit going from green to red.
- **Overload:** transformer box pulses red, its gauge needle pegs, a buzzing vignette.
- **Trace tie-in:** each 3D event flashes the matching line in the side CRT log, and the timeline scrubber marker.

### 4.3 Camera & motion

- Default: slow 15° orbit. Click a node to dolly-focus. Scrubbing the timeline replays pulses and heat.
- All motion eased, slightly mechanical (a tiny overshoot/settle), never springy-modern.

### 4.4 Tech

- **Three.js + React Three Fiber.** Post-processing: mild bloom on emissives only, subtle film-grain + scanline pass, slight chromatic aberration at the edges (sells the CRT/vintage feel). Keep bloom low or the warm palette turns to mud.
- Models: low-poly GLTF; bake the worn-metal look into textures. Reuse one material library across nodes for consistency.

---

## 5. Motion & sound (optional but on-theme)

- UI transitions: pages slide like paper being pulled; stamps **slam** down (scale 1.2→1 + small rotate + dust puff).
- Lamps flicker on boot. CRT text types in character by character.
- Optional audio: relay clicks, a soft 60Hz hum, a stamp thunk, an alarm buzz on ALERT. Ship muted with a toggle.

---

## 6. The agency seal (reusable asset)

Round badge, used on landing + exported reports:
- Outer brass ring + 60 tick marks (every 5th longer).
- Ring text: `★ TIME VARIANCE AUTHORITY ★` (top arc), `TEMPORAL INFRASTRUCTURE DIV` (bottom arc), mono, cream.
- Inner dark disc with an amber **lightning-bolt + concentric radiating arcs** (the spark-on-a-timeline motif).
- Build as SVG so it scales; animate the arcs faintly when the sim runs.

---

## 7. Component cheat-sheet (CSS sketch)

```css
.tva-panel{
  background: var(--paper-2);
  border: 3px solid var(--brown-2);
  border-radius: 8px;
  box-shadow: 0 4px 0 rgba(0,0,0,.28), inset 0 0 60px rgba(60,40,20,.25);
  position: relative;
}
.tva-panel::after{ /* grain */
  content:""; position:absolute; inset:0; border-radius:inherit;
  background:url(noise.png); opacity:.05; mix-blend-mode:multiply; pointer-events:none;
}
.tva-plaque{
  background: var(--walnut); color: var(--amber-hi);
  font: 600 15px/1 "IBM Plex Mono",monospace; letter-spacing:.1em;
  text-transform:uppercase; padding:14px 20px; border-radius:6px;
}
.tva-btn{
  background: var(--amber); color: var(--walnut);
  border:none; border-radius:6px; box-shadow:0 4px 0 var(--orange);
  font:700 16px "Bahnschrift","Oswald",sans-serif; letter-spacing:.08em;
  text-transform:uppercase; padding:14px 26px; cursor:pointer;
}
.tva-btn:active{ transform:translateY(3px); box-shadow:0 1px 0 var(--orange); }
.crt{
  background:#120C06; border:14px solid var(--brown-2); border-radius:14px;
  color: var(--amber-hi); font:15px/1.5 "IBM Plex Mono",monospace;
  text-shadow:0 0 6px rgba(255,170,60,.5); padding:20px; position:relative; overflow:hidden;
}
.crt::after{ /* scanlines */
  content:""; position:absolute; inset:0;
  background:repeating-linear-gradient(#0000 0 2px,#00000055 2px 3px); pointer-events:none;
}
.stamp{ color:var(--danger); border:6px double var(--danger); border-radius:8px;
  font:700 28px "Bahnschrift",sans-serif; letter-spacing:.12em; text-transform:uppercase;
  padding:8px 18px; transform:rotate(-8deg); opacity:.85; }
```

---

## 8. Asset checklist

- [ ] Agency seal — SVG (ring text, ticks, bolt, radiating arcs)
- [ ] Paper-grain noise PNG (tileable, subtle)
- [ ] Stamp set — `SELECTED`, `FORGED`, `CLASSIFIED`, `CLEARED`, `STRESSED`, `DAMAGED`, `VARIANT LOGGED`
- [ ] Nixie / seven-segment digit sprites or a web font
- [ ] Low-poly GLTF nodes — server, charger pillar, battery pack, transformer, bus console
- [ ] Shared worn-metal / enamel / veneer PBR texture set
- [ ] CRT + film-grain + scanline post FX shader
- [ ] Lamp component (on/off + glow)
- [ ] Fonts: Bahnschrift/Oswald (display) + IBM Plex Mono (data) — self-host; **embed in any exported PDF**

---

## 9. Pitfalls (so it doesn't look like a theme pack)

- **Don't drown it in brown.** The amber accent and the cream text are what keep it legible; a wall of mud reads as a mistake, not a style.
- **Don't mix in cool blues or neon.** One stray neon gradient breaks the whole 1970s illusion.
- **Keep text short.** This UI is labels, stamps and readouts. Long paragraphs fight the aesthetic — push narrative into the CRT log or a separate case document.
- **Readability first on the data.** The temperature chart and the damage numbers must stay crisp amber-on-dark; decorate *around* them, never *over* them.
- **Performance:** bloom + grain + scanline passes are cheap individually but stack up. Budget them, test on a mid laptop (demo machine), and give a "reduce effects" toggle.
```