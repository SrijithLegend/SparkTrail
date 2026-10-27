# SparkTrail — Experience Site

TVA-themed scrollytelling site for SparkTrail. One EV domain, **five attacks**, a part-by-part EV
charger internals reveal that shows **where SparkTrail sits**, a live Three.js propagation graph,
an attack console, and the EV charging simulator — real tools, not videos.

## Run

```bash
npm install
npm run dev        # http://localhost:3000
# production: npm run build && npm start
```

## Routes

| Route | What it is |
|---|---|
| `/` | **Act 1** (scroll): EV charger internals revealed part by part — connector, power module, contactor, controller, comms — then the SparkTrail monitor on the control link, then the microgrid. **Act 2** (scroll): the live cyber→control→physics graph with a **5-attack selector** (reveal → attack → defense), then the Temporal Variance Report. |
| `/console` | **Attack console** — pick one of the 5 attacks, watch it propagate hop by hop, replay, read the event log and metrics. |
| `/simulator` | The TVA simulator from the repo's `viz3d/multidomain.html`, opened with `?only=ev_hub` so it shows the **EV charging hub only**: MITRE-tagged manipulations, play/scrub/speed, defended toggle, damage report, prior occurrences. `npm run dev`/`build` copy it into `public/viz3d` first (`scripts/sync-viz3d.mjs`); edit it in `viz3d/`, not here. |
| `/specs` | The physics numbers, the two defenses, honest limits. |

## The 5 attacks

Generated from the real engine by `gen_attacks.py` at the repo root — each run undefended and with
the Zero-Trust proxy on. Traces live in `public/trace/attacks/`, with `index.json` driving the UI.
Simulation only.

| # | Attack | MITRE ATT&CK for ICS | Undefended | First flagged | Proxy on |
|---|---|---|---|---|---|
| 01 | Forced overcurrent + temperature spoof | T0836 + T0856 | pack 57.7 °C | at onset (physics monitor) | 43.2 °C |
| 02 | Thermal-sensor drift | T0856 | pack 51.0 °C | +2 s (sensor fusion) | 43.2 °C |
| 03 | Sensor replay / stale freeze | T0857 / T0856 | pack 52.6 °C | +2 s (sensor fusion) | 43.2 °C |
| 04 | False-data synthesis | T0856 (model-aware) | pack 54.2 °C | at onset (physics monitor) | 43.2 °C |
| 05 | Mass max-power broadcast | T0831 | transformer 174 %, bus −8.7 % | — | 104 % |

Regenerate after changing the engine or the attack definitions:

```bash
# from the repo root
python gen_attacks.py
```

## Acts

- **Act 1 — image sequence.** `components/ScrollSequence.tsx` plays frames from
  `public/sequences/charger-internals/` (72) and `.../microgrid-explode/` (48). These are
  **procedural placeholders** (`scripts/gen_frames.py`, rendered on the site's `#0A0A0F`). Swap in
  Veo→Ezgif frames with the same `frame_NNN.jpg` naming and update `count` in `app/page.tsx`.
- **Act 2 — live graph.** `components/SparkTrailGraph.tsx` reads a per-attack trace and
  `public/scenes.json`. Red = root · orange = direct · amber = cascade · cyan = defender · green =
  pruned (defense succeeded).

## Notes

- Fonts (Outfit, Share Tech Mono) are self-hosted at build time via `next/font`.
- Three.js is a normal npm dep — no CDN, works offline.
- Honest limit for judges: Act 1 is cinema; **Act 2, the console and the simulator are the real tool**.
