import Navbar from "@/components/Navbar";
import TVAFooter from "@/components/TVAFooter";

export default function Specs() {
  return (
    <main className="tva-grid">
      <Navbar />
      <div className="page">
        <div className="head reveal">
          <span className="tva-stamp">Temporal variance report · TVA-101</span>
          <h1>How SparkTrail works</h1>
        </div>
        <p className="lead reveal">A forged command becomes real heat. SparkTrail models the whole chain — and
          shows where a physics-aware check would have pruned the variant.</p>

        <section className="reveal">
          <h2>The three layers</h2>
          <p><b>Cyber</b> — the forged command or spoofed sensor frame. <b>Control</b> — the charger and battery
            management system that obey it. <b>Physics</b> — the heat, current, transformer load and voltage that
            actually result. SparkTrail ties all three into one timestamped causal graph.</p>
        </section>

        <section className="reveal">
          <h2>Reference scenario — DC-fast overcurrent + temperature spoof</h2>
          <div className="report glass">
            <div className="bar"><span>Case file TVA-101</span><span className="tva-stamp red">Variant</span></div>
            <table className="specs">
              <thead><tr><th>Quantity</th><th>Normal</th><th>Under attack</th></tr></thead>
              <tbody>
                <tr><td>Pack temperature (peak)</td><td className="n">40.1 °C</td><td className="n"><span className="pill hot">57.7 °C</span></td></tr>
                <tr><td>Reported temperature</td><td className="n">real</td><td className="n">pinned 30 °C (spoofed)</td></tr>
                <tr><td>Charge current</td><td className="n">125 A</td><td className="n">forced 250 A</td></tr>
                <tr><td>Spoof flagged (sensor fusion)</td><td className="n">—</td><td className="n"><span className="pill ok">2 s after attack</span></td></tr>
                <tr><td>Residual alarm (physics monitor)</td><td className="n">—</td><td className="n">at attack onset</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="reveal">
          <h2>The two defenses</h2>
          <p><b>Zero-Trust Physics Proxy</b> — refuses a command that violates a hard physical limit, even when it
            is perfectly authenticated. With the proxy on, the 250 A command is blocked and the pack peaks at 43.2 °C instead of 57.7 °C.</p>
          <p><b>Sensor-Fusion Validator</b> — cross-checks the electrical load against the thermal response via Joule
            heating. If current is high but the reported temperature barely moves, the sensor is being spoofed.</p>
        </section>

        <section className="reveal">
          <h2>Honest limits</h2>
          <p>Every model is lumped and first-order — directionally right, not engineering-accurate. The defenses share
            the plant model&apos;s form, so their detection times are optimistic; real model mismatch is slower. An
            &quot;injection&quot; is a wrong value on a modelled link — how an attacker reaches that link is out of scope by design.</p>
        </section>
      </div>
      <TVAFooter />
    </main>
  );
}
