const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport:{width:1280,height:800} });
  await p.goto('http://localhost:3000/', { waitUntil:'domcontentloaded' });
  await p.waitForTimeout(2500);
  const r = await p.evaluate(() => {
    const wrap = document.querySelector('.pin-wrap');
    const cv = document.querySelector('canvas');
    const beat = document.querySelector('.beat');
    const rect = wrap.getBoundingClientRect();
    return {
      scrollY: window.scrollY, innerH: window.innerHeight,
      wrapTop: rect.top, wrapH: rect.height,
      canvasClientW: cv.clientWidth, canvasClientH: cv.clientHeight,
      canvasAttrW: cv.width, canvasAttrH: cv.height,
      beatOpacity: beat && getComputedStyle(beat).opacity,
    };
  });
  console.log(JSON.stringify(r,null,0));
  await b.close();
})();
