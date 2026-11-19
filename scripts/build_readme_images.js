// Gera as imagens PNG do README a partir de scripts/readme-sections.html.
// Cada [data-shot] vira assets/readme/<nome>.png, com o fundo do painel e estrelas nas margens.
// Uso: node scripts/build_readme_images.js   (precisa do Playwright com Chromium)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const src = path.join(__dirname, 'readme-sections.html');
const out = path.join(root, 'assets', 'readme');

(async () => {
  fs.rmSync(out, { recursive: true, force: true });
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 940, height: 900 }, deviceScaleFactor: 2 });
  await page.goto('file://' + src, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  // Altura inteira: borda fracionária deixa a última linha do PNG semitransparente (vira um fio claro no README).
  await page.evaluate(() => document.querySelectorAll('[data-shot]').forEach(el => {
    el.style.height = Math.ceil(el.getBoundingClientRect().height) + 'px';
  }));
  // Estrelas determinísticas (semente = nome da peça), só fora do conteúdo.
  await page.evaluate(() => {
    const colors = ['#9ecbff', '#e6f1ff', '#58a6ff', '#3fb950'];
    for (const el of document.querySelectorAll('[data-shot]')) {
      let s = [...el.dataset.shot].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
      const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32);
      const box = el.getBoundingClientRect();
      const inner = [...el.children].map(c => c.getBoundingClientRect());
      const n = Math.round(box.width * box.height / 9000);
      for (let i = 0, tries = 0; i < n && tries < 2000; tries++) {
        const x = rnd() * box.width, y = rnd() * box.height;
        if (inner.some(r => x >= r.left - box.left - 3 && x <= r.right - box.left + 3 && y >= r.top - box.top - 3 && y <= r.bottom - box.top + 3)) continue;
        const d = 1 + rnd() * 1.4, star = document.createElement('i');
        star.className = 'star';
        Object.assign(star.style, { left: x + 'px', top: y + 'px', width: d + 'px', height: d + 'px',
          background: colors[Math.floor(rnd() * colors.length)], opacity: (0.25 + rnd() * 0.45).toFixed(2) });
        el.appendChild(star); i++;
      }
    }
  });
  const shots = await page.$$eval('[data-shot]', els => els.map(e => e.dataset.shot));
  for (const name of shots) {
    await (await page.$(`[data-shot="${name}"]`)).screenshot({ path: path.join(out, `${name}.png`), omitBackground: true });
  }
  console.log(`wrote ${shots.length} images to assets/readme/`);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
