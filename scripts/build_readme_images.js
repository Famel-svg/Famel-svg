// Gera os PNGs (fundo transparente) das seções do README a partir de scripts/readme-sections.html.
// Cada [data-shot] vira assets/readme/src/<nome>.png. Depois rode: python scripts/build_readme.py
// Uso: node scripts/build_readme_images.js   (precisa do Playwright com Chromium)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
// uso: node build_readme_images.js [en]  -> idioma padrão pt
const lang = process.argv[2] || 'pt';
const src = path.join(__dirname, lang === 'pt' ? 'readme-sections.html' : `readme-sections-${lang}.html`);
const out = path.join(root, 'assets', 'readme', ...(lang === 'pt' ? [] : [lang]), 'src');

(async () => {
  fs.rmSync(out, { recursive: true, force: true });
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 940, height: 900 }, deviceScaleFactor: 2 });
  await page.goto('file://' + src, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  // Altura inteira (borda fracionária deixa um fio no README); peças do mesmo data-group
  // (colunas lado a lado) ficam com a mesma altura.
  await page.evaluate(() => {
    const els = [...document.querySelectorAll('[data-shot]')];
    const h = el => Math.ceil(el.getBoundingClientRect().height);
    const groups = {};
    els.forEach(el => { if (el.dataset.group) groups[el.dataset.group] = Math.max(groups[el.dataset.group] || 0, h(el)); });
    els.forEach(el => { el.style.height = (groups[el.dataset.group] || h(el)) + 'px'; });
  });
  const shots = await page.$$eval('[data-shot]', els => els.map(e => e.dataset.shot));
  for (const name of shots) {
    await (await page.$(`[data-shot="${name}"]`)).screenshot({ path: path.join(out, `${name}.png`), omitBackground: true });
  }
  console.log(`wrote ${shots.length} images to ${out}`);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
