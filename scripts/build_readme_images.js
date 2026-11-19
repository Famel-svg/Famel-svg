// Gera as imagens de seção do README (PNG) a partir de scripts/readme-sections.html.
// Uso: node scripts/build_readme_images.js
const path = require('path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const src = path.join(__dirname, 'readme-sections.html');
const out = path.join(root, 'assets', 'readme');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 900, height: 800 }, deviceScaleFactor: 2 });
  await page.goto('file://' + src, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const shots = await page.$$eval('[data-shot]', els => els.map(e => e.dataset.shot));
  for (const name of shots) {
    const el = await page.$(`[data-shot="${name}"]`);
    await el.screenshot({ path: path.join(out, `${name}.png`), omitBackground: true });
    console.log(`wrote assets/readme/${name}.png`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
