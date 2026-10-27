import Navbar from "@/components/Navbar";

// The full TVA multi-domain simulator (repo viz3d/, synced into public/viz3d at build):
// six domains, MITRE-tagged manipulations, playback, defended toggle, damage report.
export default function Simulator() {
  return (
    <main className="sim-shell">
      <Navbar />
      <div className="sim-bar glass">
        <span className="t"><span className="ring" style={{ ["--s" as string]: "16px" }} />TVA simulation terminal</span>
        <span className="live">Temporal loom online</span>
      </div>
      <div className="sim-monitor crt">
        <iframe src="/viz3d/multidomain.html" title="SparkTrail multi-domain simulator" />
      </div>
    </main>
  );
}
