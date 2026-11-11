// usage: node shot.js in.html out.(png|pdf) [width]
const { chromium } = require('playwright');
(async () => {
  const [inp, out, width] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: +(width || 1400), height: 800 } });
  await pg.goto('file://' + require('path').resolve(inp));
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(300);
  if (out.endsWith('.pdf')) await pg.pdf({ path: out, width: '8.5in', height: '11in', printBackground: true, preferCSSPageSize: true });
  else await pg.screenshot({ path: out, fullPage: true });
  await b.close();
})();
