# SparkTrail — Scrollytelling Landing Page Spec

Apple-level, Awwwards-grade scrollytelling landing page for **SparkTrail — Cyber-to-Physical
Impact Visibility for EV Charging & Microgrids**. Mirrors the premium Sony-reveal structure,
rebuilt around SparkTrail's real story: a charging hub explodes into its cyber→control→physics
node graph, an attack propagates, the defense engages, and it reassembles safe.

---

## ACT AS

A world-class **Awwwards-level Creative Developer and Brand Experience Director**, specializing
in ultra-premium web design, Next.js, Framer Motion, advanced scroll-based storytelling, and
3D-inspired product interactions for global deep-tech and infrastructure brands.

## THE TASK

Design and implement a high-end, **Apple-level scrollytelling landing page for SparkTrail**, a
cyber-to-physical impact simulator for EV charging and microgrids.

The experience should feel like a **cinematic product reveal fused with an interactive
engineering/security showcase**, driven entirely by scroll-based image-sequence animation and
premium typography/layout. The core mechanic: as the user scrolls, an image sequence plays where
a **matte EV charging hub explodes (disassembles) into a floating technical node-graph** —
attacker, backend, charger, BMS, battery pack, transformer — an **attack propagates through it
(nodes flaring red→amber by hop)**, the **defense intercepts**, and the hub **reassembles** into
its calm hero state, synchronized with copywriting and storytelling beats.

## TECH STACK INTENT *(for behavior/style, not code generation)*

- **Framework:** Next.js 14 (App Router mental model)
- **Styling:** Tailwind CSS-style utility thinking (tight spacing, consistent scale)
- **Animation:** Framer Motion-style scroll-linked animations, easing, transitions
- **Rendering:** HTML5 Canvas-style image-sequence playback for performance and smoothness

## VISUAL DIRECTION & BRAND AESTHETIC

**Overall vibe:** Apple-level, luxury deep-tech, cinematic, ultra-clean, minimal, editorial,
security-grade corporate.

**Seamless blending:** the page background color MUST perfectly match the background of the image
sequence frames so image edges are 100% invisible and the hub appears to float in a unified void.

### Color palette — Premium Corporate Dark Mode

- **Primary background:** deep near-black charcoal `#050505` (or eyedrop from the hero frame).
- **Secondary background:** `#0A0A0C` subtle variation for sections and overlays.
- **Headings:** `text-white/90` with a subtle soft glow / very subtle shadow for depth.
- **Body text:** `text-white/60` for calm readability.
- **Accent colors — two families, by meaning:**
  - *Safe / defense / tech* — primary deep blue `#0050FF`, secondary electric cyan `#00D6FF`
    (used for the hero, the defense beat, CTAs, interactive highlights).
  - *Alert / attack* — signal amber `#F0A836` and danger red `#FF3B3B`
    (used ONLY during the attack-propagation and consequence beats, so color itself tells the
    story: calm blue → danger red → back to blue).

### Gradients

- Soft radial glow behind hero content: from `#050505` to a deep desaturated blue `#050815`,
  extremely subtle.
- Safe accent gradient (buttons, key labels): `#0050FF → #00D6FF`, premium, glossy-but-minimal.
- Attack accent gradient (danger beats only): `#F0A836 → #FF3B3B`, used sparingly on the
  propagation readouts and the red-line meters.

### Typography

- **Fonts:** Inter, SF Pro Display / SF Pro Text, or a geometric grotesk.
- **Style:** ultra-clean, tracking-tight, medium-to-bold, large scale, strong hierarchy.
- **Headings:** bold, tight line-height, almost editorial — Apple / Sony global-site register.
- **Body:** 16–18px, comfortable line-height, muted color, concise, confident copy.

**Overall layout feeling:** full-bleed, edge-to-edge, generous negative space, no clutter, no
decorative noise, restrained color, everything intentional and premium.

## NAVBAR LIKE APPLE — STRUCTURE & BEHAVIOR

Ultra-minimal top navigation bar, inspired by Apple's product pages. Fixed/sticky, with a
translucent, slightly blurred background (glassmorphism) that subtly appears after scroll.

**Content (left → right):**
- **Left:** simple text logo **"SparkTrail"** in a clean, medium-weight font.
- **Center:** minimalist links — **"Overview", "How it works", "Attack Demo", "Defense", "Specs"**.
- **Right:** primary CTA button **"Launch the simulator"** with a subtle gradient border and soft
  hover glow.

**Styling:** slim/compact height; background semi-transparent black `rgba(5,5,5,0.75)` with
backdrop blur; hover = very subtle underline or opacity shift, no heavy decoration.

**Scroll behavior:** at top, nearly invisible / fully transparent; after a slight scroll, fades
in with a gentle transition.

## CORE INTERACTION: SCROLL-LINKED IMAGE SEQUENCE

A central HTML5 Canvas-style full-screen area pinned/sticky during scroll. Inside it, a
**120-frame image sequence of a matte EV charging hub & microgrid** plays as the user scrolls.

**Sequence behavior:**
- **Start:** fully assembled hero beauty shot of the charging hub.
- **Mid:** gradually explodes / disassembles into internal components and the layered node graph
  (charge connector, cable, BMS, battery-pack cells, CSMS backend, transformer, microgrid feeder).
- **Peak:** fully exploded technical diagram — every component and node floating in perfect
  alignment — with the **attack propagating**: the attacker node ignites, a spark-trail bead runs
  the causal chain, nodes flare **red (root) → amber (direct) → yellow (cascade)**, the battery
  pack glows hot.
- **End:** the **defense intercepts** (proxy + fusion nodes pulse cyan/jade), heat drains out of
  the nodes, and components gracefully reassemble into the final calm hero product.

Each frame is ultra-high resolution, cinematic, photorealistic, 8K-level detail — dramatic rim
lighting, deep blacks, controlled reflections, infrastructure-grade product rendering. The canvas
and the background color are identical, enabling a seamless, edge-free presentation.

## SCROLL LOGIC AND STORYTELLING BEATS (COPYWRITING-DRIVEN)

Scroll is the narrative axis. From 0→100%, text sections appear and disappear, synced to the
state of the hub.

### HERO / INTRO (0–15% scroll)
**Visual:** charging hub fully assembled, three-quarter angle, matte, floating over deep black
with a subtle gradient; cinematic rim light tracing the pedestal and cabinet.
**Copy (centered, bold, minimal):**
- Headline: **"SparkTrail"**
- Subtitle: **"When a hack becomes heat."** *(alt: "See the damage before it happens.")*
- Supporting (smaller, optional): *"Cyber-to-physical impact visibility for EV charging and
  microgrids."*
- Tone: short, confident, high-end deep-tech.

### ENGINEERING REVEAL (15–40% scroll)
**Visual:** the hub begins to separate — charger, cable, battery pack, BMS, transformer drift
apart; the three layers (cyber / control / physics) become visible as a floating structure.
**Copy (left-aligned, emerging from the left):**
- Headline: **"Three layers. One invisible chain."**
- Subcopy:
  - *"A forged command, a controller that obeys, a battery that heats — SparkTrail traces the whole
    path from packet to physical damage."*
  - *"Every component is modelled, every hop is logged — nothing is hand-waved as 'compromised'."*
- Feel: technical yet poetic — engineering language with a clear stake.

### ATTACK & PROPAGATION (40–65% scroll)
**Visual:** components spread further; the attacker node ignites; a spark-trail bead travels the
causal chain; nodes flare red→amber→yellow by propagation depth; the battery pack starts glowing
hot. Amber/red accents active here.
**Copy (right-aligned, sliding from the right):**
- Headline: **"Watch the attack spread."**
- Supporting (short, punchy):
  - *"A spoofed sensor pins the temperature at a safe-looking 30 °C."*
  - *"The pack really climbs to 55.4 °C — and nothing on screen says so."*
  - *"Cyber, control, physics: every hop timestamped on one causal graph."*
- Emphasis: silent escalation, the gap between what's reported and what's real.

### CONSEQUENCE & PHYSICS (65–85% scroll)
**Visual:** battery pack, transformer, and microgrid feeder highlighted in the exploded view, lit
hot; analog meters spike — transformer loading `174%`, bus voltage drop `8.7%` — rolling toward
their red lines.
**Copy (left-aligned or centered):**
- Headline: **"The physics doesn't lie."**
- Subcopy:
  - *"Lumped thermal and grid models turn the attack into real numbers — peak temperature,
    transformer overload, voltage collapse."*
  - *"Not a vague red flag. A measured consequence, with a timeline."*
- Tone: grounded, credible, engineering-forward.

### DEFENSE, REASSEMBLY & CTA (85–100% scroll)
**Visual:** the Zero-Trust physics proxy and the sensor-fusion validator engage (guardian nodes
pulse cyan/jade); the dangerous command is refused; heat drains from the nodes as they cool from
red back to calm blue; the hub reassembles into its iconic hero pose.
**Copy (centered, strong CTA):**
- Headline: **"Catch it in the physics, not the paperwork."**
- Subheadline: **"SparkTrail — cyber-to-physical impact visibility for EV charging and microgrids."**
- Primary CTA: **"Launch the simulator"**
- Secondary: **"Read the architecture"**
- Micro-copy: *"Built for grids that can't afford to find out the hard way."*

## UI & VISUAL POLISH (HEAVY "GOOD" KEYWORDS)

**Emphasize:** cinematic, photorealistic, hyper-detailed, ultra-premium, luxury deep-tech,
editorial, Apple-level, infrastructure-grade, modern, minimalist, corporate high-end,
glassmorphism, gradient glows, smooth, buttery scroll, hardware-accelerated, immersive,
interactive storytelling, scrollytelling, telemetry, causal graph, security-grade, polished,
Awwwards-level.

**Stylistic elements:**
- Soft ambient glows behind the hub and key text blocks (blue in calm beats, amber in attack beats).
- Subtle gradient borders around CTAs and key cards.
- Depth through focus and lighting rather than noisy effects.
- Extremely subtle grid / alignment hints to ground the design.

## TYPOGRAPHY & GRADIENT DETAILS

- **Headings:** large, tight; gradient fill white → very light blue/cyan for the calm beats
  (hero, defense), and white → amber `#F0A836` for the attack/consequence beats — subtle fade at
  the base of the letterforms.
- **Body:** solid `rgba(255,255,255,0.6)`, no gradients, readability first.
- **Button text:** white, semi-bold, subtle drop shadow for legibility over dark backgrounds.

## CANVAS & LAYOUT BEHAVIOR (DESCRIPTIVE, NOT CODE)

- Sticky canvas section with height ~`400vh`, so the user scrolls through multiple story beats
  while the canvas stays pinned.
- Canvas always full-width and full-height of the viewport; the hub sequence centered and scaled
  to fit while preserving aspect ratio.
- Scroll position controls frame index; frame selection uses smooth mapping to avoid flicker/jumps.
- All UI chrome (navbar, text overlays) floats above the canvas with subtle depth and
  non-intrusive presence.

## FINAL PROMPT (COMBINED, READY-TO-USE)

> "Design a hyper-premium, Apple-level, cinematic scrollytelling landing page for **SparkTrail**,
> a cyber-to-physical impact simulator for EV charging and microgrids. The experience should feel
> like a high-end, editorial, security-grade product story with a sticky full-screen canvas
> playing a 120-frame image sequence of a **matte EV charging hub exploding (disassembling) into a
> floating technical node-graph** — attacker, backend, charger, BMS, battery pack, transformer,
> microgrid feeder — through which an **attack visibly propagates** (nodes flaring red→amber→yellow
> by hop, the battery glowing hot) before a **defense intercepts** and the hub **reassembles** into
> a calm hero state, all as the user scrolls. The page uses a pure dark-mode aesthetic with a deep
> charcoal background `#050505` that perfectly matches the image-sequence background so the hub
> appears to float in seamless black space with no visible edges.
>
> Include an Apple-style, ultra-minimal, fixed top navigation bar: a slim glassmorphism nav with
> subtle backdrop blur, near-black translucent background, a simple product title
> ('SparkTrail'), centered links like 'Overview', 'How it works', 'Attack Demo', 'Defense',
> 'Specs', and a right-aligned gradient CTA button reading 'Launch the simulator'. The nav starts
> nearly invisible at the top and gently fades in after a small scroll, mimicking Apple's product
> navigation.
>
> Use premium corporate colors and gradients: primary background `#050505`, secondary `#0A0A0C`,
> headings in `text-white/90`, body in `text-white/60`, a safe/defense accent of deep blue
> `#0050FF` and electric cyan `#00D6FF`, and an attack accent of amber `#F0A836` and danger red
> `#FF3B3B` used only during the attack and consequence beats so color itself tells the story. Add
> extremely subtle radial gradients behind the hero and key sections (soft glow `#050505 →
> #050815`). Typography uses Inter or SF Pro Display/Text, tracking-tight bold headings, clean
> readable body — modern, minimalist, high-tech, editorial.
>
> The scroll-linked canvas animation is the core interaction. At 0–15% scroll, show the hub fully
> assembled in a cinematic hero shot with dramatic rim lighting, deep blacks, photorealistic
> 8K-level detail; center the copy 'SparkTrail' with 'When a hack becomes heat.' and an optional
> line 'Cyber-to-physical impact visibility for EV charging and microgrids.' From 15–40% scroll,
> begin the soft explosion: charger, cable, cushions of cabling, BMS, pack and transformer drift
> apart revealing the three-layer structure; on the left, fade in 'Three layers. One invisible
> chain.' with premium subcopy about tracing the path from forged packet to physical damage.
>
> From 40–65% scroll, emphasize the attack: ignite the attacker node, run a spark-trail bead down
> the causal chain, flare nodes red→amber→yellow by propagation depth, start the pack glowing hot;
> on the right, fade in 'Watch the attack spread.' with concise lines — 'A spoofed sensor pins the
> temperature at a safe-looking 30 °C.', 'The pack really climbs to 55.4 °C.', 'Every hop
> timestamped on one causal graph.' From 65–85% scroll, focus on the physical consequence:
> highlight pack, transformer and feeder, spike analog meters toward their red lines (transformer
> 174%, voltage drop 8.7%), with copy 'The physics doesn't lie.' and subcopy about lumped thermal
> and grid models turning the attack into measured numbers, not a vague flag.
>
> From 85–100% scroll, have the defense intercept — proxy and fusion guardian nodes pulse
> cyan/jade, the dangerous command is refused, heat drains as nodes cool from red back to blue, and
> the hub fully reassembles into its hero pose. Show centered, bold CTA copy 'Catch it in the
> physics, not the paperwork.', subheadline 'SparkTrail — cyber-to-physical impact visibility for
> EV charging and microgrids.', a primary CTA 'Launch the simulator' and a secondary link 'Read the
> architecture'. Scroll transitions must be smooth, buttery, hardware-accelerated, with no stutter.
> All overlays use subtle fades, slides, and eased transitions reinforcing an ultra-premium,
> cinematic feel.
>
> Overall, optimize for an Awwwards-level, luxury deep-tech experience with cinematic lighting,
> photorealistic matte rendering, ultra-clean layout, high-end corporate color schemes, blue→cyan
> and amber→red gradient accents used by meaning, Apple-like navigation, premium copywriting,
> immersive scrollytelling, and a feeling of flagship, infrastructure-grade engineering and
> innovation."

---

## APPENDIX — Producing the 120 frames *(project-specific; not in the original prompt)*

You don't need to hand-render these — you already have the parts.

- **Best path:** render the sequence from your real `viz3d/` Three.js scene. Script one camera
  orbit while driving an "explode" parameter (node positions lerp from assembled → spread), then
  play the attack trace (depth colours + spark-trail), then reverse to reassemble. Capture 120
  frames headless with the same Chromium + swiftshader flags already in the repo. This guarantees
  the landing page and the actual simulator look identical.
- **Alternative:** compose the 34 TVA component PNGs (from `ASSET_PROMPTS.md`) in Blender or After
  Effects on a `#050505` background, keyframe the explode/propagate/reassemble, render 120 PNGs.
- **Either way:** export at `#050505` background (match exactly — eyedrop frame 0 into the page
  `--bg`), 1600×1600 or 1920×1080, sequential names `frame_000.png … frame_119.png`.
- **One honesty note for the pitch:** this page is the *marketing reveal*. The live simulator
  behind "Launch the simulator" is the real deliverable — keep the two visually consistent so the
  click-through doesn't feel like a different product.
