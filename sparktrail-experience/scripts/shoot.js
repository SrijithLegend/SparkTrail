const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const shots = [
    ['/', 0, 'home_hero'],
    ['/', 1400, 'home_charger'],
    ['/', 3600, 'home_microgrid'],
    ['/', 6200, 'graph_reveal'],
    ['/', 8600, 'graph_attack'],
    ['/', 12000, 'graph_defense'],
    ['/simulator', 0, 'simulator'],
    ['/specs', 0, 'specs'],
  ];
  for (const [path, y, name] of shots) {
    await page.goto('http://localhost:3000' + path, { waitUntil: 'networkidle' });
    if (y) { await page.evaluate((yy)=>window.scrollTo(0,yy), y); }
    await page.waitForTimeout(1600);
    await page.screenshot({ path: `/tmp/shot_${name}.png` });
    console.log('shot', name);
  }
  await browser.close();
})();
