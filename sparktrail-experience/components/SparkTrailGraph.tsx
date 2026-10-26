"use client";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

type Node = { id: string; label: string; pos: [number, number, number] };
type Scenes = { nodes: Node[]; links: [string, string][] };
type Trace = { node_depths: Record<string, number>; events: any[]; meta?: any };

const RED = 0xff3b3b, AMBER = 0xf0a836, YELLOW = 0xffe14d, IDLE = 0x33414f, CYAN = 0x00d6ff;
const DEFENDERS = new Set(["FUSION", "MONITOR", "PROXY"]);

function depthColor(d: number) {
  if (d === 0) return RED;
  if (d === 1) return AMBER;
  return YELLOW;
}

export default function SparkTrailGraph({
  progress, interactive = false,
}: { progress?: number; interactive?: boolean }) {
  const mount = useRef<HTMLDivElement>(null);
  const progRef = useRef(progress ?? 0);
  const replayRef = useRef<() => void>(() => {});
  const [log, setLog] = useState<{ t: number; s: string; k: string; cls: string }[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => { progRef.current = progress ?? 0; }, [progress]);

  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    let raf = 0, disposed = false;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch (e) {
      setReady(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050505);
    const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    cam.position.set(0, 1, 18);
    scene.add(new THREE.AmbientLight(0xffffff, 0.75));
    const key = new THREE.PointLight(0x9fd8ff, 120, 0); key.position.set(4, 8, 10); scene.add(key);

    const sizeTo = () => {
      const w = el.clientWidth, h = el.clientHeight || 1;
      renderer.setSize(w, h); cam.aspect = w / h; cam.updateProjectionMatrix();
    };
    el.appendChild(renderer.domElement);
    sizeTo();
    window.addEventListener("resize", sizeTo);

    const nodeMeshes: Record<string, THREE.Mesh> = {};
    let depths: Record<string, number> = {};
    let maxDepth = 1;
    let links: [string, string][] = [];
    let posOf: Record<string, THREE.Vector3> = {};
    let beads: { a: THREE.Vector3; b: THREE.Vector3; start: number; dur: number }[] = [];
    const beadPool: THREE.Mesh[] = [];
    const beadGeo = new THREE.SphereGeometry(0.16, 16, 16);
    const beadMat = new THREE.MeshBasicMaterial({ color: 0xffce6e });

    function label(text: string, p: [number, number, number], col: number) {
      const c = document.createElement("canvas"); c.width = 512; c.height = 64;
      const x = c.getContext("2d")!;
      x.fillStyle = "#f0e4ca"; x.font = "28px Inter, monospace"; x.fillText(text, 8, 40);
      const tex = new THREE.CanvasTexture(c);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
      sp.position.set(p[0], p[1] + 0.95, p[2]); sp.scale.set(4, 0.5, 1); scene.add(sp);
    }

    Promise.all([
      fetch("/scenes.json").then((r) => r.json()),
      fetch("/trace/trace.json").then((r) => r.json()),
    ]).then(([sc, tr]: [Scenes, Trace]) => {
      if (disposed) return;
      depths = tr.node_depths || {};
      maxDepth = Math.max(1, ...Object.values(depths));
      links = sc.links;
      sc.nodes.forEach((n) => (posOf[n.id] = new THREE.Vector3(...n.pos)));

      // links
      const linkMat = new THREE.LineBasicMaterial({ color: 0x24303c });
      sc.links.forEach(([a, b]) => {
        const pa = posOf[a], pb = posOf[b]; if (!pa || !pb) return;
        const g = new THREE.BufferGeometry().setFromPoints([pa, pb]);
        scene.add(new THREE.Line(g, linkMat));
      });
      // nodes
      sc.nodes.forEach((n) => {
        const inGraph = n.id in depths;
        const geo = new THREE.SphereGeometry(inGraph ? 0.6 : 0.46, 32, 32);
        const mat = new THREE.MeshStandardMaterial({
          color: IDLE, emissive: IDLE, emissiveIntensity: 0.35, roughness: 0.5, metalness: 0.35,
        });
        const m = new THREE.Mesh(geo, mat); m.position.copy(posOf[n.id]);
        scene.add(m); nodeMeshes[n.id] = m;
        label(n.label + (inGraph ? `  ·d${depths[n.id]}` : ""), n.pos, IDLE);
      });

      // event log (interactive)
      if (interactive) {
        const seen = new Set<string>();
        const rows = (tr.events || [])
          .filter((e) => ["attack", "monitor"].includes(e.layer) ||
            /overload|trip|reject|spoof|alarm/.test(e.kind))
          .filter((e) => { const s = e.source + e.kind; if (seen.has(s)) return false; seen.add(s); return true; })
          .slice(0, 30)
          .map((e) => ({
            t: e.t, s: e.source, k: e.kind,
            cls: e.layer === "attack" ? "atk"
              : /alarm|spoof|trip/.test(e.kind) ? "alert" : "ok",
          }));
        setLog(rows);
      }

      // bead replay
      const buildBeads = () => {
        beads = [];
        links.forEach(([a, b]) => {
          const da = depths[a], db = depths[b];
          if (da === undefined || db === undefined) return;
          beads.push({ a: posOf[a], b: posOf[b], start: performance.now() + Math.min(da, db) * 480, dur: 560 });
        });
      };
      replayRef.current = buildBeads;
      setReady(true);
      if (interactive) buildBeads();
    });

    const tmp = new THREE.Color();
    function animate() {
      raf = requestAnimationFrame(animate);
      const now = performance.now();
      const p = progRef.current;

      // activation by depth
      let activeDepth: number;
      let cooling = 0;
      if (interactive) {
        activeDepth = maxDepth;
      } else {
        if (p < 0.33) activeDepth = -1;                 // reveal: all idle
        else if (p < 0.85) activeDepth = Math.floor(((p - 0.33) / 0.52) * (maxDepth + 1));
        else { activeDepth = maxDepth; cooling = (p - 0.85) / 0.15; } // defense cools
      }

      Object.entries(nodeMeshes).forEach(([id, m]) => {
        const mat = m.material as THREE.MeshStandardMaterial;
        const d = depths[id];
        const defender = DEFENDERS.has(id);
        if (d === undefined || d > activeDepth) {
          mat.color.setHex(IDLE); mat.emissive.setHex(IDLE); mat.emissiveIntensity = 0.38;
        } else {
          let col = defender ? CYAN : depthColor(d);
          if (cooling > 0 && !defender) {
            tmp.setHex(depthColor(d)).lerp(new THREE.Color(CYAN), cooling);
            col = tmp.getHex();
          }
          mat.color.setHex(col); mat.emissive.setHex(col);
          const pulse = 0.65 + 0.35 * Math.sin(now / 320 + d);
          mat.emissiveIntensity = (defender ? 0.9 : 0.8) * pulse;
          const s = 1 + 0.06 * Math.sin(now / 300 + d);
          m.scale.setScalar(s);
        }
      });

      // beads
      beadPool.forEach((b) => (b.visible = false));
      let bi = 0;
      for (const bd of beads) {
        const t = (now - bd.start) / bd.dur;
        if (t < 0 || t > 1) continue;
        let bead = beadPool[bi++];
        if (!bead) { bead = new THREE.Mesh(beadGeo, beadMat); scene.add(bead); beadPool.push(bead); }
        bead.visible = true; bead.position.lerpVectors(bd.a, bd.b, t);
      }

      scene.rotation.y = Math.sin(now / 6000) * 0.12;
      renderer.render(scene, cam);
    }
    animate();

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", sizeTo);
      renderer.dispose();
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
    };
  }, [interactive]);

  return (
    <div className="graph-mount" ref={mount}>
      {interactive && (
        <>
          <button className="btn" style={{ position: "absolute", top: 18, right: 18, zIndex: 10 }}
                  onClick={() => replayRef.current()}>▸ Replay propagation</button>
          <div style={{
            position: "absolute", bottom: 18, left: 18, width: 340, maxHeight: 180,
            overflow: "auto", background: "rgba(10,13,16,.8)", border: "1px solid rgba(0,214,255,.25)",
            borderRadius: 10, padding: "12px 14px", fontFamily: "monospace", fontSize: 11, lineHeight: 1.6,
          }}>
            {log.map((r, i) => (
              <div key={i} style={{ color: r.cls === "atk" ? "#ff5252" : r.cls === "alert" ? "#ff9f43" : "#9ccc65" }}>
                {String(Math.floor(r.t / 60)).padStart(2, "0")}:{String(Math.floor(r.t % 60)).padStart(2, "0")}
                {"  "}{r.s.padEnd(10)} {r.k}
              </div>
            ))}
          </div>
        </>
      )}
      {!ready && (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center",
          justifyContent: "center", color: "rgba(255,255,255,.3)", fontSize: 13, letterSpacing: ".2em" }}>
          LOADING TRACE…
        </div>
      )}
    </div>
  );
}
