import Navbar from "@/components/Navbar";
import Intro from "@/components/Intro";
import ScrollSequence from "@/components/ScrollSequence";
import GraphSection from "@/components/GraphSection";
import TVAMarquee from "@/components/TVAMarquee";
import TVAStatsGrid from "@/components/TVAStatsGrid";
import TVAFooter from "@/components/TVAFooter";
import ScrollHint from "@/components/ScrollHint";

// the five attacks in public/trace/attacks (gen_attacks.py)
const TICKER = ["Forced overcurrent", "Thermal-sensor drift", "Sensor replay",
  "False-data synthesis", "Mass max-power broadcast"];

export default function Home() {
  return (
    <main>
      <Intro />
      <Navbar />

      {/* ACT 1 — EV charger internals, part by part, then where SparkTrail sits, then the grid */}
      <ScrollSequence
        heroGlow
        heightVh={560}
        anchors={[{ id: "components", at: 0.222 }]} /* "inside the charger" beat: p = at·560/460 ≈ 0.27 */
        sequences={[
          { dir: "/sequences/charger-internals", count: 72 },
          { dir: "/sequences/microgrid-explode", count: 48 },
        ]}
        beats={[
          {
            align: "center", a: 0.0, b: 0.0, c: 0.10, d: 0.16, titleTag: "h1",
            stamp: "TVA · Classified",
            title: "SparkTrail",
            sub: "The attack you can't see — in the heat you can. Temporal variance detection for EV charging & microgrids.",
          },
          {
            align: "left", vpos: "bottom", a: 0.16, b: 0.22, c: 0.32, d: 0.40,
            kicker: "Sacred timeline · inside the charger",
            title: "Every part obeys on command.",
            sub: "Connector, power module, contactor, controller, comms — the charger does whatever a well-formed message says. That trust is the attack surface.",
          },
          {
            align: "left", vpos: "bottom", a: 0.40, b: 0.46, c: 0.54, d: 0.60,
            kicker: "Where SparkTrail works",
            title: "On the link between command and cell.",
            sub: "SparkTrail sits on the control path — watching the physics, not just the packets, so a dangerous command shows up as heat, not a green checkmark.",
          },
          {
            align: "right", vpos: "bottom", a: 0.66, b: 0.74, c: 0.92, d: 1.0,
            kicker: "Sacred timeline · the grid behind it",
            title: "One hub. Dozens of commands a second.",
            sub: "Transformer, storage, inverter, feeder — every command trusted, every one a path to physical damage.",
          },
        ]}
      >
        <div className="ticker" aria-hidden>
          <div className="ticker-track mono">
            {[...TICKER, ...TICKER].map((t, i) => <span key={i}><b>▸</b> {t}</span>)}
          </div>
        </div>
      </ScrollSequence>

      <TVAMarquee
        items={["Timeline breach detected", "Five variants on the sacred timeline", "Cyber → control → physics"]}
        speed={28} accent="var(--red)"
      />

      {/* ACT 2 — the live causal graph, five attacks from the engine */}
      <GraphSection />

      <TVAStatsGrid />
      <TVAFooter />
      <ScrollHint />
    </main>
  );
}
