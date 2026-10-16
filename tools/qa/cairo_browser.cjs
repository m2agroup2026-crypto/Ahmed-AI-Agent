// Focused rendering regression. Screenshots contain blank login forms only.
const { chromium } = require(process.env.AQLITH_PLAYWRIGHT || require('node:path').join(require('node:os').tmpdir(), 'aqlith-preview-qa/node_modules/playwright-core'));
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const output = path.join(require('node:os').tmpdir(), 'aqlith-cairo-qa');
fs.mkdirSync(output, { recursive: true });
const findings = [];
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    for (const platform of ['next', 'expo']) for (const language of ['ar', 'en']) for (const appearance of ['light', 'dark']) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: 'light' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(platform === 'next' ? 'http://localhost:3000/classroom' : 'http://localhost:8081');
      const role = platform === 'next' ? 'button' : 'radio';
      const control = name => platform === 'next' ? page.getByRole('group', { name: 'Appearance / المظهر' }).getByRole(role, { name, exact: true }) : page.getByRole(role, { name, exact: true });
      await page.getByRole(role, { name: 'العربية / AR', exact: true }).waitFor();
      await page.emulateMedia({ colorScheme: 'dark' });
      await control('النظام').click();
      await page.waitForFunction(() => getComputedStyle(document.documentElement).colorScheme === 'dark');
      await page.emulateMedia({ colorScheme: 'light' });
      await page.waitForFunction(() => getComputedStyle(document.documentElement).colorScheme === 'light');
      await page.getByRole(role, { name: language === 'ar' ? 'العربية / AR' : 'English / EN', exact: true }).click();
      const label = (ar, en) => language === 'ar' ? ar : en;
      await control(appearance === 'light' ? label('فاتح', 'Light') : label('داكن', 'Dark')).click();
      const input = page.getByRole('textbox', { name: label('البريد الإلكتروني', 'Email'), exact: true });
      await input.fill('draft@example.invalid');
      await page.getByRole(role, { name: language === 'ar' ? 'English / EN' : 'العربية / AR', exact: true }).click();
      assert.equal(await page.getByRole('textbox', { name: label('Email', 'البريد الإلكتروني'), exact: true }).inputValue(), 'draft@example.invalid');
      await page.getByRole(role, { name: language === 'ar' ? 'العربية / AR' : 'English / EN', exact: true }).click();
      await page.reload();
      await page.getByRole('textbox', { name: label('البريد الإلكتروني', 'Email'), exact: true }).waitFor();
      await page.waitForFunction(({ language, appearance }) => document.documentElement.lang === language && getComputedStyle(document.documentElement).colorScheme === appearance, { language, appearance });
      assert.equal(await page.locator('html').getAttribute('dir'), language === 'ar' ? 'rtl' : 'ltr');
      await page.evaluate(() => document.fonts.ready);
      // CDP reports fonts actually used to paint glyphs, rather than CSS intent.
      const cdp = await context.newCDPSession(page);
      await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
      const heading = platform === 'next' ? page.locator('h1').first() : page.getByText(label('ابدأ رحلة التعلم', 'Start your learning journey'), { exact: true });
      await heading.evaluate(element => element.setAttribute('data-cairo-probe', 'true'));
      const doc = await cdp.send('DOM.getDocument');
      const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: doc.root.nodeId, selector: '[data-cairo-probe]' });
      const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId });
      assert(fonts.some(font => /Cairo/i.test(font.familyName) && font.isCustomFont && font.glyphCount > 0), JSON.stringify(fonts));
      for (const width of [360, 390]) {
        await page.setViewportSize({ width, height: width === 360 ? 800 : 844 });
        const logo = platform === 'next' ? page.locator('.brand-logo img:visible') : page.locator('[aria-label="AQLITH"] img');
        await logo.evaluate(image => image.decode());
        const rendered = await logo.evaluate(image => ({ source: image.src, naturalWidth: image.naturalWidth }));
        assert(rendered.source.includes(`aqlith-logo-${appearance}`)); assert(rendered.naturalWidth > 1000);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width);
        const small = await page.getByRole(role).evaluateAll(elements => elements.filter(e => { if (e.getRootNode() !== document) return false; const r = e.getBoundingClientRect(); return r.width > 0 && (r.height < 44 || r.width < 44); }).map(e => ({ name: e.getAttribute('aria-label') || e.textContent, width: e.getBoundingClientRect().width, height: e.getBoundingClientRect().height })));
        assert.deepEqual(small, []);
        const screenshot = `${platform}-${language}-${appearance}-${width}.png`;
        await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
        findings.push({ platform, language, appearance, width, fonts, screenshot, logo: rendered });
      }
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`PASS ${platform} ${language}/${appearance}: actual Cairo glyphs, logo, system changes, independent preferences, draft retention, 360/390`);
    }
    fs.writeFileSync(path.join(output, 'cairo-results.json'), JSON.stringify({ result: 'passed', nativeDeviceTested: false, findings }, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
