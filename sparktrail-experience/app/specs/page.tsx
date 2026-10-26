import Navbar from "@/components/Navbar";

export default function Specs() {
  return (
    <main>
      <Navbar />
      <div className="page">
        <h1>How SparkTrail works</h1>
        <p className="lead">A forged command becomes real heat. SparkTrail models the whole chain — and
          shows where a physics-aware check would have caught it.</p>

        <h2>The three layers</h2>
        <p><b>Cyber</b> — the forged command or spoofed sensor frame. <b>Control</b> — the charger and battery
          management system that obey it. <b>Physics</b> — the heat, current, transformer load and voltage that
          actually result. SparkTrail ties all three into one timestamped causal graph.</p>

        <h2>Reference scenario — DC-fast overcurrent + temperature spoof</h2>
        <table className="specs">
          <thead><tr><th>Quantity</th><th>Normal</th><th>Under attack</th></tr></thead>
          <tbody>
            <tr><td>Pack temperature (peak)</td><td className="n">38.5 °C</td><td className="n"><span className="pill hot">55.4 °C</span></td></tr>
            <tr><td>Reported temperature</td><td className="n">real</td><td className="n">pinned 30 °C (spoofed)</td></tr>
            <tr><td>Charge current</td><td className="n">125 A</td><td className="n">forced 250 A</td></tr>
            <tr><td>Spoof flagged (sensor fusion)</td><td className="n">—</td><td className="n"><span className="pill ok">~1 s</span></td></tr>
            <tr><td>Residual alarm (physics monitor)</td><td className="n">—</td><td className="n">~239 s</td></tr>
          </tbody>
        </table>

        <h2>The two defenses</h2>
        <p><b>Zero-Trust Physics Proxy</b> — refuses a command that violates a hard physical limit, even when it
          is perfectly authenticated. With the proxy on, the 250 A command is blocked and the pack stays at 38.5 °C.</p>
        <p><b>Sensor-Fusion Validator</b> — cross-checks the electrical load against the thermal response via Joule
          heating. If current is high but the reported temperature barely moves, the sensor is being spoofed.</p>

        <h2>Honest limits</h2>
        <p>Every model is lumped and first-order — directionally right, not engineering-accurate. The defenses share
          the plant model's form, so their detection times are optimistic; real model mismatch is slower. An
          "injection" is a wrong value on a modelled link — how an attacker reaches that link is out of scope by design.</p>
      </div>
    </main>
  );
}
