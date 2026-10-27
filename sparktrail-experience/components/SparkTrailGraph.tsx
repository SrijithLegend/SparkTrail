"use client";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { mono } from "@/app/fonts";

type Node = { id: string; label: string; pos: [number, number, number] };
type Scenes = { nodes: Node[]; links: [string, string][] };
type Trace = { node_depths: Record<string, number>; events: any[]; meta?: any };

// TVA palette: hop colour by depth from the root cause; defenders cyan; pruned (cooled) green.
const RED = 0xff3b3b, ORANGE = 0xff6b00, AMBER = 0xf0a836, IDLE = 0x2a2320, CYAN = 0x00d6ff, PRUNED = 0x2ee6a8;
const BG = 0x0a0a0f;
const DEFENDERS = new Set(["FUSION", "MONITOR", "PROXY"]);

function depthColor(d: number) {
  if (d === 0) return RED;
  if (d === 1) return ORANGE;
  return AMBER;
}

// Subtle CRT: barrel distortion, scanlines and vignette over the rendered graph.
const CRTShader = {
  uniforms: { tDiffuse: { value: null }, lines: { value: 300 }, bg: { value: new THREE.Color(BG) } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float lines; uniform vec3 bg; varying vec2 vUv;
    void main(){
      vec2 c = vUv * 2.0 - 1.0;
      c *= 1.0 + 0.04 * dot(c, c);
      vec2 uv = c * 0.5 + 0.5;
      if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) { gl_FragColor = vec4(bg, 1.0); return; }
      vec3 col = texture2D(tDiffuse, uv).rgb;
      // shade only what differs from the background, so empty space stays exactly --bg
      float k = (0.92 + 0.08 * sin(uv.y * lines * 3.14159)) * mix(0.72, 1.0, smoothstep(1.4, 0.5, length(c)));
      gl_FragColor = vec4(bg + (col - bg) * k, 1.0);
    }`,
};

function haloTexture() {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d")!, r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(0.25, "rgba(255,255,255,.45)"); r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r; g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}

const STEP_MS = 500; // interactive playback: one hop every half second

/** Scroll-driven (progress) on the home page; time-driven playback when interactive (the
 *  console), restarted whenever playKey changes. src = which attack trace to show. */
export default function SparkTrailGraph({
  progress, src = "/trace/trace.json", interactive = false, playKey = 0,
}: { progress?: number; src?: string; interactive?: boolean; playKey?: number }) {
  const mount = useRef<HTMLDivElement>(null);
  const progRef = useRef(progress ?? 0);
  const t0 = useRef(0);
  const [ready, setReady] = useState(false);

  useEffect(() => { progRef.current = progress ?? 0; }, [progress]);
  useEffect(() => { t0.current = performance.now(); }, [playKey, src]);

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
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    renderer.setPixelRatio(dpr);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(BG);
    const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    cam.position.set(0, 1, 18);
    scene.add(new THREE.AmbientLight(0xffe6cc, 0.7));
    const key = new THREE.PointLight(0xffb27a, 120, 0); key.position.set(4, 8, 10); scene.add(key);

    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, cam));
    const crt = new ShaderPass(CRTShader);
    composer.addPass(crt);
    composer.addPass(new OutputPass());

    const sizeTo = () => {
      const w = el.clientWidth, h = el.clientHeight || 1;
      renderer.setSize(w, h); composer.setPixelRatio(dpr); composer.setSize(w, h);
      crt.uniforms.lines.value = h / 1.5; // a scanline every ~3 CSS px
      cam.aspect = w / h;
      // back the camera off on narrow screens so the whole graph (x ≈ ±10.5) fits
      cam.position.z = Math.max(18, 10.5 / (Math.tan((cam.fov / 2) * Math.PI / 180) * cam.aspect));
      cam.updateProjectionMatrix();
    };
    el.appendChild(renderer.domElement);
    sizeTo();
    window.addEventListener("resize", sizeTo);

    const nodeMeshes: Record<string, THREE.Mesh> = {};
    const halos: Record<string, THREE.Sprite> = {};
    const haloTex = haloTexture();
    let depths: Record<string, number> = {};
    let maxDepth = 1;
    let posOf: Record<string, THREE.Vector3> = {};
    const hops: { a: THREE.Vector3; b: THREE.Vector3; d: number }[] = []; // links that carry the attack d -> d+1
    const beadPool: THREE.Mesh[] = [];
    const beadGeo = new THREE.SphereGeometry(0.16, 16, 16);
    const beadMat = new THREE.MeshBasicMaterial({ color: 0xffb36b });
    const fontFamily = mono.style.fontFamily;

    function label(text: string, p: [number, number, number]) {
      const c = document.createElement("canvas"); c.width = 512; c.height = 64;
      const x = c.getContext("2d")!;
      x.fillStyle = "rgba(255,236,214,.88)"; x.font = `28px ${fontFamily}`; x.fillText(text, 8, 40);
      const tex = new THREE.CanvasTexture(c);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
      sp.position.set(p[0], p[1] + 0.95, p[2]); sp.scale.set(4, 0.5, 1); scene.add(sp);
    }

    Promise.all([
      fetch("/scenes.json").then((r) => r.json()),
      fetch(src).then((r) => r.json()),
      document.fonts.load(`28px ${fontFamily}`).catch(() => null), // labels are drawn once; wait for the font
    ]).then(([sc, tr]: [Scenes, Trace, unknown]) => {
      if (disposed) return;
      depths = tr.node_depths || {};
      maxDepth = Math.max(1, ...Object.values(depths));
      sc.nodes.forEach((n) => (posOf[n.id] = new THREE.Vector3(...n.pos)));

      // links
      const linkMat = new THREE.LineBasicMaterial({ color: 0x3a2a1e });
      sc.links.forEach(([a, b]) => {
        const pa = posOf[a], pb = posOf[b]; if (!pa || !pb) return;
        const g = new THREE.BufferGeometry().setFromPoints([pa, pb]);
        scene.add(new THREE.Line(g, linkMat));
        const da = depths[a], db = depths[b];
        if (da !== undefined && db === da + 1) hops.push({ a: pa, b: pb, d: da });
      });
      // nodes + additive glow halos (cheap bloom)
      sc.nodes.forEach((n) => {
        const inGraph = n.id in depths;
        const geo = new THREE.SphereGeometry(inGraph ? 0.6 : 0.46, 32, 32);
        const mat = new THREE.MeshStandardMaterial({
          color: IDLE, emissive: IDLE, emissiveIntensity: 0.35, roughness: 0.5, metalness: 0.35,
        });
        const m = new THREE.Mesh(geo, mat); m.position.copy(posOf[n.id]);
        scene.add(m); nodeMeshes[n.id] = m;
        const halo = new THREE.Sprite(new THREE.SpriteMaterial({
          map: haloTex, color: IDLE, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
        }));
        halo.position.copy(posOf[n.id]); halo.scale.setScalar(3.4); scene.add(halo); halos[n.id] = halo;
        label(n.label + (inGraph ? `  ·d${depths[n.id]}` : ""), n.pos);
      });

      setReady(true);
    });

    const tmp = new THREE.Color(), prunedCol = new THREE.Color(PRUNED);
    function animate() {
      raf = requestAnimationFrame(animate);
      const now = performance.now();
      const p = progRef.current;

      // activation by depth
      let activeDepth: number;
      let cooling = 0;
      const el = (now - t0.current) / STEP_MS;      // interactive: hops elapsed since (re)play
      if (interactive) activeDepth = Math.floor(el);
      else if (p < 0.33) activeDepth = -1;          // reveal: all idle
      else if (p < 0.85) activeDepth = Math.floor(((p - 0.33) / 0.52) * (maxDepth + 1));
      else { activeDepth = maxDepth; cooling = (p - 0.85) / 0.15; } // defense prunes: heat cools to green

      Object.entries(nodeMeshes).forEach(([id, m]) => {
        const mat = m.material as THREE.MeshStandardMaterial;
        const hm = halos[id].material as THREE.SpriteMaterial;
        const d = depths[id];
        const defender = DEFENDERS.has(id);
        if (d === undefined || d > activeDepth) {
          mat.color.setHex(IDLE); mat.emissive.setHex(IDLE); mat.emissiveIntensity = 0.38;
          hm.color.setHex(ORANGE); hm.opacity = 0.03;
        } else {
          let col = defender ? CYAN : depthColor(d);
          if (cooling > 0 && !defender) {
            tmp.setHex(depthColor(d)).lerp(prunedCol, cooling);
            col = tmp.getHex();
          }
          mat.color.setHex(col); mat.emissive.setHex(col);
          const pulse = 0.65 + 0.35 * Math.sin(now / 320 + d);
          mat.emissiveIntensity = (defender ? 0.9 : 0.8) * pulse;
          const s = 1 + 0.06 * Math.sin(now / 300 + d);
          m.scale.setScalar(s);
          hm.color.setHex(col); hm.opacity = 0.75 * pulse;
        }
      });

      // interactive: a bead runs along each hop as it fires
      beadPool.forEach((b) => (b.visible = false));
      if (interactive) {
        let bi = 0;
        for (const h of hops) {
          const u = el - h.d; if (u < 0 || u > 1) continue;
          let bead = beadPool[bi++];
          if (!bead) { bead = new THREE.Mesh(beadGeo, beadMat); scene.add(bead); beadPool.push(bead); }
          bead.visible = true; bead.position.lerpVectors(h.a, h.b, u);
        }
      }

      scene.rotation.y = Math.sin(now / 6000) * 0.12;
      composer.render();
    }
    animate();

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", sizeTo);
      composer.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
    };
  }, [src, interactive]);

  return (
    <div className="graph-mount" ref={mount}>
      {!ready && (
        <div className="mono" style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center",
          justifyContent: "center", color: "var(--text3)", fontSize: 13, letterSpacing: ".2em" }}>
          LOADING TRACE…
        </div>
      )}
    </div>
  );
}
