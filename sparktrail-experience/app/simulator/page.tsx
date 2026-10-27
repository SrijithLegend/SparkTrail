import Navbar from "@/components/Navbar";

// The full TVA multi-domain simulator (repo viz3d/, synced into public/viz3d at build):
// six domains, MITRE-tagged manipulations, playback, defended toggle, damage report.
export default function Simulator() {
  return (
    <main className="sim-shell">
      <Navbar />
      <iframe className="sim-frame" src="/viz3d/multidomain.html" title="SparkTrail multi-domain simulator" />
    </main>
  );
}
