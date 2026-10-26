const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
  const errs = [];
  p.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
  p.on('pageerror', e => errs.push('PAGEERR: ' + e.message));

  // HOME
  await p.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(2000);
  const home = await p.evaluate(() => {
    const cv = document.querySelector('canvas');
    let drawn = false, sample = null;
    if (cv) { const ctx = cv.getContext('2d'); if (ctx) { const d = ctx.getImageData(cv.width/2, cv.height/2, 1, 1).data; sample = [...d]; drawn = d[0]+d[1]+d[2] > 10; } }
    const beat = document.querySelector('.beat');
    const cs = beat ? getComputedStyle(beat) : null;
    return { hasCanvas: !!cv, cw: cv&&cv.width, ch: cv&&cv.height, ctx2d: cv? !!cv.getContext('2d') : false, sample, drawn,
             firstBeatOpacity: cs && cs.opacity, firstBeatText: beat && beat.innerText.slice(0,40) };
  });

  // SIMULATOR
  await p.goto('http://localhost:3000/simulator', { waitUntil: 'networkidle' });
  await p.waitForTimeout(3000);
  const sim = await p.evaluate(() => {
    const cv = document.querySelector('.graph-mount canvas');
    const loading = document.body.innerText.includes('LOADING TRACE');
    return { hasGlCanvas: !!cv, cw: cv&&cv.width, ch: cv&&cv.height, loading };
  });

  console.log('HOME', JSON.stringify(home));
  console.log('SIM', JSON.stringify(sim));
  console.log('ERRORS', JSON.stringify(errs.slice(0,8)));
  await b.close();
})();
