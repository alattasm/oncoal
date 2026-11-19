// Render ep1.html to PNG frames with N parallel pages.
const { chromium } = require('playwright');
const FPS = 30, out = process.argv[2], N = 6;
(async () => {
  const b = await chromium.launch();
  const page0 = await b.newPage(); await page0.goto('file://' + __dirname + '/ep1.html');
  const total = Math.round(await page0.evaluate(() => DUR) * FPS); await page0.close();
  await Promise.all([...Array(N).keys()].map(async w => {
    const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
    await p.goto('file://' + __dirname + '/ep1.html'); await p.evaluate(() => document.fonts.ready);
    for (let i = w; i < total; i += N) {
      await p.evaluate(t => render(t), i / FPS);
      await p.screenshot({ path: `${out}/${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 93 });
    }
  }));
  await b.close(); console.log('frames', total);
})();
