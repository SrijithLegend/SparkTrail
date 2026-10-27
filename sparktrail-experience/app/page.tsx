import Navbar from "@/components/Navbar";
import ScrollSequence from "@/components/ScrollSequence";
import GraphSection from "@/components/GraphSection";

export default function Home() {
  return (
    <main>
      <Navbar />

      {/* ACT 1 — the machine (pre-rendered image sequence) */}
      <ScrollSequence
        heroGlow
        heightVh={520}
        sequences={[
          { dir: "/sequences/charger-explode", count: 48 },
          { dir: "/sequences/microgrid-explode", count: 48 },
        ]}
        beats={[
          {
            align: "center", a: 0.0, b: 0.0, c: 0.11, d: 0.17, titleTag: "h1",
            title: "SparkTrail",
            sub: "The attack you can't see — in the heat you can. Cyber-to-physical impact visibility for EV charging & microgrids.",
          },
          {
            align: "left", a: 0.20, b: 0.28, c: 0.40, d: 0.48,
            kicker: "The machine",
            title: "Built to deliver 350 kW.",
            sub: "Connector, power stage, contactors, controller — every part does its job the instant it's told to.",
          },
          {
            align: "right", a: 0.56, b: 0.64, c: 0.82, d: 0.92,
            kicker: "The grid",
            title: "Dozens of commands a second.",
            sub: "Transformer, storage, inverter, feeder — and every one of those commands is trusted. That's the problem.",
          },
        ]}
      />

      <div id="components" />
      {/* ACT 2 — SparkTrail (live graph) */}
      <GraphSection />

      <div className="scroll-hint">scroll</div>
    </main>
  );
}
