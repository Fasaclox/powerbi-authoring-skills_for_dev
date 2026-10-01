// Render assets/previews/*.svg to PNG (2x) and assets/gallery.html to gallery.png.
// Run after build_styles.py:  node scripts/render_previews.js
// Needs Playwright with Chromium (npm i -g playwright; NODE_PATH=$(npm root -g)).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const assets = path.join(__dirname, '..', 'assets');
  const dir = path.join(assets, 'previews');
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  for (const f of fs.readdirSync(dir).filter((n) => n.endsWith('.svg')).sort()) {
    const svg = fs.readFileSync(path.join(dir, f), 'utf8');
    await page.setContent(`<body style="margin:0;background:#fff">${svg}</body>`);
    await page.locator('body > svg').screenshot({ path: path.join(dir, f.replace(/\.svg$/, '.png')) });
  }
  await page.setViewportSize({ width: 1100, height: 800 });
  await page.goto('file://' + path.join(assets, 'gallery.html'));
  await page.screenshot({ path: path.join(assets, 'gallery.png'), fullPage: true });
  await browser.close();
})();
