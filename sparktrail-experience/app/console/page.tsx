import Navbar from "@/components/Navbar";
import AttackConsole from "@/components/AttackConsole";

// The five EV attacks, one at a time, on the live cyber→control→physics graph.
// (/simulator is the TVA simulator, EV charging hub only.)
export default function Console() {
  return (
    <main className="sim-shell">
      <Navbar />
      <div className="sim-bar glass">
        <span className="t"><span className="ring" style={{ ["--s" as string]: "16px" }} />TVA attack console · EV charging</span>
        <span className="live">Red root · orange direct · amber cascade · cyan defender</span>
      </div>
      <AttackConsole />
    </main>
  );
}
