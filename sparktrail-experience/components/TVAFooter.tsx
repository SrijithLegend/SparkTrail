import Link from "next/link";
import TVAMarquee from "./TVAMarquee";

export default function TVAFooter() {
  return (
    <footer className="footer">
      <TVAMarquee items={["For all time. Always.", "Sacred timeline secured", "Variants pruned: 15 / 15"]} speed={36} />
      <div className="inner tva-grid">
        <div className="wrap">
          <div className="always">For all time.<br />Always.</div>
          <div className="fstats">
            <div><b>15</b><span>Variants detected</span></div>
            <div><b>15</b><span>Timelines pruned</span></div>
            <div><b>6</b><span>Domains watched</span></div>
            <div><b>7</b><span>Attack mechanisms</span></div>
          </div>
          <div className="row">
            <span className="mono">SparkTrail · a simulation — it never touches a real charger, grid or vehicle.</span>
            <nav aria-label="Footer">
              <Link href="/simulator">Simulator</Link>
              <Link href="/specs">Specs</Link>
              <a href="https://github.com/SrijithLegend/SparkTrail">GitHub</a>
            </nav>
          </div>
        </div>
        <div className="watermark" aria-hidden>CLASSIFIED</div>
      </div>
    </footer>
  );
}
