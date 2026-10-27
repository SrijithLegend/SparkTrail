import Navbar from "@/components/Navbar";
import ScrollSequence from "@/components/ScrollSequence";
import GraphSection from "@/components/GraphSection";
import TVAMarquee from "@/components/TVAMarquee";
import TVAStatsGrid from "@/components/TVAStatsGrid";
import TVAFooter from "@/components/TVAFooter";
import ScrollHint from "@/components/ScrollHint";

export default function Home() {
  return (
    <main>
      <Navbar />

      {/* ACT 1 — the machine on the sacred timeline (pre-rendered image sequence) */}
      <ScrollSequence
        heroGlow
        heightVh={520}
        anchors={[{ id: "components", at: 0.242 }]} /* machine beat: p = at·520/420 ≈ 0.3 */
        sequences={[
          { dir: "/sequences/charger-explode", count: 48 },
          { dir: "/sequences/microgrid-explode", count: 48 },
        ]}
        beats={[
          {
            align: "center", a: 0.0, b: 0.0, c: 0.11, d: 0.17, titleTag: "h1",
            stamp: "TVA · Classified",
            title: "SparkTrail",
            sub: "The attack you can't see — in the heat you can. Temporal variance detection for EV charging & microgrids.",
          },
          {
            align: "left", a: 0.20, b: 0.28, c: 0.40, d: 0.48,
            kicker: "Sacred timeline · the machine",
            title: "Built to deliver 350 kW.",
            sub: "Connector, power stage, contactors, controller — every part does its job the instant it's told to.",
          },
          {
            align: "right", a: 0.56, b: 0.64, c: 0.82, d: 0.92,
            kicker: "Sacred timeline · the grid",
            title: "Dozens of commands a second.",
            sub: "Transformer, storage, inverter, feeder — and every one of those commands is trusted. That's the problem.",
          },
        ]}
      />

      <TVAMarquee
        items={["Timeline breach detected", "Variant on the sacred timeline", "Cyber → control → physics"]}
        speed={28} accent="var(--red)"
      />

      {/* ACT 2 — the variant, traced on the live causal graph */}
      <GraphSection />

      <TVAStatsGrid />
      <TVAFooter />
      <ScrollHint />
    </main>
  );
}
