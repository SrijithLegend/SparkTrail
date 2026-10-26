import Navbar from "@/components/Navbar";
import SparkTrailGraph from "@/components/SparkTrailGraph";

export default function Simulator() {
  return (
    <main className="sim-shell">
      <Navbar />
      <div className="sim-head">
        <h1>SparkTrail — Propagation Simulator</h1>
        <p>DC-fast overcurrent with a spoofed temperature sensor. Nodes coloured by hops from the root cause.
          Red = root · amber = direct · yellow = cascade · cyan = defender.</p>
      </div>
      <div className="sim-graph">
        <SparkTrailGraph interactive />
      </div>
    </main>
  );
}
