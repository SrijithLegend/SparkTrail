// Copy the TVA multi-domain simulator from the repo's viz3d/ into public/viz3d so the
// site serves the real tool at /viz3d/multidomain.html. viz3d/ stays the source of truth;
// runs before `dev` and `build`.
import { cpSync, rmSync } from "node:fs";

const src = new URL("../../viz3d/", import.meta.url);
const dst = new URL("../public/viz3d/", import.meta.url);

rmSync(dst, { recursive: true, force: true });
for (const p of ["multidomain.html", "scenes", "models"]) {
  cpSync(new URL(p, src), new URL(p, dst), { recursive: true });
}
console.log("synced viz3d -> public/viz3d");
