# SparkTrail — Experience Site

Apple-style scrollytelling landing page for SparkTrail, built with the same technique as the
tutorial (sticky canvas image-sequence) — but **Act 2 is a live Three.js graph**, not a video, so
the "Launch Simulator" button opens the real propagation tool.

## Run

```bash
npm install
npm run dev        # http://localhost:3000
# or production:
npm run build && npm start
```

## What's here

| Route | What it is |
|---|---|
| `/` | The experience. **Act 1** (scroll) — EV charger + microgrid explode into components (image sequence). **Act 2** (scroll) — the live SparkTrail cyber→control→physics graph: reveal → attack propagation → defense. |
| `/simulator` | The full TVA multi-domain simulator from the repo's `viz3d/multidomain.html`: 6 domains, MITRE-tagged manipulations, play/scrub/speed, defended toggle, damage report, prior occurrences. `npm run dev`/`build` copy it into `public/viz3d` first (`scripts/sync-viz3d.mjs`); edit it in `viz3d/`, not here. |
| `/specs` | Plain editorial page — the physics numbers, the two defenses, honest limits. |

## The two acts

- **Act 1 — image sequence.** `components/ScrollSequence.tsx` plays frames from
  `public/sequences/<name>/frame_NNN.jpg`, scroll-linked. The current frames are **procedural
  placeholders** (`scripts/gen_frames.py`). **Swap in your Veo→Ezgif frames** by dropping them into
  those folders (same naming) and updating `count` in `app/page.tsx`.
- **Act 2 — live graph.** `components/SparkTrailGraph.tsx` is `viz3d` ported to React/Three. It reads
  `public/trace/trace.json` (produced by the SparkTrail engine's `cli.py`) and `public/scenes.json`.
  Nodes are coloured by hops from the root cause: **red** root · **amber** direct · **yellow**
  cascade · **cyan** defender.

## Updating the data

```bash
# in the SparkTrail python repo:
python cli.py dcfast_overcurrent_tempspoof.yaml --out trace.json
# copy trace.json -> this app's public/trace/trace.json
```

## Swapping in real Veo frames (Act 1)

1. Whisk the components (see `ASSET_PROMPTS.md` in the main repo).
2. Veo the explosion; split with Ezgif (`ezgif.com/video-to-jpg`, ~5–8 FPS).
3. Drop frames into `public/sequences/charger-explode/` and `.../microgrid-explode/`
   as `frame_000.jpg …`, update the `count` values in `app/page.tsx`.

## Notes

- The Google Fonts `@import` in `globals.css` needs network at load; swap for `next/font` if you
  want it bundled.
- Three.js is a normal npm dependency — no CDN, works offline.
- Honest limit (say it to judges): Act 1 is cinema; **Act 2 is the real tool**. Keep them consistent.
