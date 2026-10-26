# TVA component models and asset attribution

The multi-domain viewer (`viz3d/multidomain.html`) now builds **procedural 3D
assemblies** from Three.js geometry and shared TVA materials. Components are
actual scene meshes with depth, perspective, lighting, and physical details—not
flat images stretched into camera-facing billboards.

## Procedural models

The current model builder creates distinct TVA-inspired silhouettes:
- **Anomaly / attacker:** faceted containment core, brass guard cage, concentric rings, red warning lamp.
- **Battery pack:** ribbed cassette, terminal caps, thermal indicator and status lamp.
- **EV charger:** pedestal cabinet, CRT-style face, cable loop, connector and indicator.
- **Transformer / breaker / feeder:** finned metal cabinet, porcelain bushings, analog gauge and warning lamp.
- **Server / CSMS / SCADA / PLC / BMS / monitor / fusion:** walnut relay rack, stacked modules, vents, rotary controls and lamps.
- **Water / HVAC / pump / valve / other process equipment:** vessel, flanges, pipe stub, pressure gauge and indicator.
- **Fallback nodes:** ribbed instrumented equipment cabinet instead of a generic sphere.

The scene shares a restrained material library: walnut, worn enamel, brass, aged paper, dark CRT glass, TVA amber, danger red and muted teal. A per-node plinth is tinted by propagation depth, while the model's main materials retain their TVA finish.

## Existing image assets

The original generated images remain available in the existing paths and are now
used as **small inset instrument/CRT faceplates** on corresponding 3D models.
They no longer replace the whole object as a billboard. Node ids without an
image still receive a complete procedural model.

Existing image paths referenced by `NODE_IMG`:
- `shared/` — attacker, plc, monitor, fusion, transformer
- `ev_hub/` — csms, cp1, bms, pack
- `power_sub/` — scada, rtu, breaker, tap_changer, feeder, loads

## Optional authored GLB upgrades

Procedural meshes are self-contained and need no downloaded 3D assets. For a
higher-fidelity authored model, a domain can still provide a licence-clean
single-file `.glb` under `viz3d/models/<domain>/<name>.glb` and map the node
in `scene_models` in the relevant domain module. The generated scene JSON
already carries the optional `models` mapping; GLB loading can be added to the
viewer as a separate enhancement.

## Attribution

The procedural geometry and material assembly are implemented in
`viz3d/multidomain.html` and use Three.js primitives. No third-party GLB models
were added by this change, so no new external model licence or author attribution
is required. The existing component renders are retained from the repository's
prior assets.
