# 3D model attribution & drop-in (SPARKTRAIL_MULTIDOMAIN §5)

The multi-domain viewer renders every node from **primitives** (TVA analog
boxes / cylinders / octahedra) so the scene always renders with **no downloads**.
Real glTF models are an optional, licence-clean upgrade — drop-in, no code change.

## How to add a model (two steps)
1. Put a single-file `.glb` (textures embedded, ≤ ~2–3 MB, `draco`-compressed if
   heavier) under `viz3d/models/<domain>/<name>.glb`.
2. In that domain module (`sparktrail/domains/<domain>.py`) set
   `scene_models = {"NODE_ID": "models/<domain>/<name>.glb"}`, then regenerate:
   `python -m sparktrail.domains`.

The viewer loads `GLTFLoader` lazily; any node with a `model` path uses the glb,
and **any node without one keeps its primitive** — so partial model sets are fine.

## Sourcing (licence-clean only)
- **Sketchfab** — filter *Downloadable* + Creative Commons. Prefer **CC0 / CC-BY**.
- **Poly Pizza** — mostly CC0/CC-BY low-poly.
- **Khronos glTF Sample Assets** — permissively licensed references.
- Convert `.gltf` / `.obj` / `.fbx` → `.glb` with `gltf-pipeline` / `obj2gltf`.

> This container's network may block model hosts; if a download is blocked, drop
> the `.glb` into the folder yourself — the scene already renders without it.

## Suggested signature model per domain (fill the licence line when you add one)
| Domain | Node | Model | Author | Licence | Source URL |
|---|---|---|---|---|---|
| ev_hub | CP_1 | charger.glb | — | — | — |
| power_sub | TAP_CHANGER | transformer.glb | — | — | — |
| water | DOSING_PUMP | pump.glb | — | — | — |
| robot_cell | ROBOT_AXIS | robot_arm.glb | — | — | — |
| hvac | CHILLER | chiller.glb | — | — | — |
| pipeline | PUMP | pump_station.glb | — | — | — |

*(No models are bundled yet — every row above is a placeholder. Primitives render in the meantime.)*
