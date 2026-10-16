// Browser rendering of the actual Expo components. This is not native-device QA.
const { chromium } = require(process.env.AQLITH_PLAYWRIGHT || require('node:path').join(require('node:os').tmpdir(), 'aqlith-preview-qa/node_modules/playwright-core'));
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const accounts = JSON.parse(fs.readFileSync(path.join(os.tmpdir(), 'aqlith-preview-accounts.json'), 'utf8'));
const output = path.join(os.tmpdir(), 'aqlith-brand-qa');
const findings = [];

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    for (const language of ['ar', 'en']) for (const appearance of ['light', 'dark']) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto('http://localhost:8081');
      await page.getByRole('radio', { name: language === 'ar' ? 'العربية / AR' : 'English / EN', exact: true }).click();
      const label = (ar, en) => language === 'ar' ? ar : en;
      await page.getByRole('radio', { name: appearance === 'light' ? label('فاتح', 'Light') : label('داكن', 'Dark'), exact: true }).click();
      const snapshot = async name => {
        await page.waitForFunction(() => {
          const logo = document.querySelector('[aria-label="AQLITH"]');
          const image = logo?.querySelector('img');
          return image?.complete && image.naturalWidth > 1000;
        });
        const logo = await page.locator('[aria-label="AQLITH"]').evaluate(element => ({
          src: element.querySelector('img').src, width: element.querySelector('img').naturalWidth,
          height: element.getBoundingClientRect().height,
        }));
        assert(logo.src.includes(`aqlith-logo-${appearance}`));
        assert(logo.height > 30);
        for (const width of [360, 390]) {
          await page.setViewportSize({ width, height: width === 360 ? 800 : 844 });
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width);
          await page.screenshot({ path: path.join(output, `expo-${language}-${appearance}-${name}-${width}.png`), fullPage: true });
          findings.push({ language, appearance, name, width, logo });
        }
      };
      await page.getByRole('textbox', { name: label('البريد الإلكتروني', 'Email'), exact: true }).fill('draft@preview.example.com');
      await page.getByRole('radio', { name: language === 'ar' ? 'English / EN' : 'العربية / AR', exact: true }).click();
      assert.equal(await page.getByRole('textbox', { name: label('Email', 'البريد الإلكتروني'), exact: true }).inputValue(), 'draft@preview.example.com');
      await page.getByRole('radio', { name: language === 'ar' ? 'العربية / AR' : 'English / EN', exact: true }).click();
      await page.getByRole('textbox', { name: label('البريد الإلكتروني', 'Email'), exact: true }).fill('');
      await snapshot('login');
      await page.reload();
      await page.getByRole('textbox', { name: label('البريد الإلكتروني', 'Email'), exact: true }).waitFor();
      assert.equal(await page.getByRole('radio', { name: appearance === 'light' ? label('فاتح', 'Light') : label('داكن', 'Dark'), exact: true }).getAttribute('aria-checked'), 'true');
      await page.getByRole('textbox', { name: label('البريد الإلكتروني', 'Email'), exact: true }).fill(accounts.student.email);
      await page.getByLabel(label('كلمة المرور', 'Password'), { exact: true }).fill(accounts.student.password);
      const data = Promise.all([
        page.waitForResponse(r => r.url().endsWith('/api/v1/tutor/lessons')),
        page.waitForResponse(r => r.url().endsWith('/api/v1/tutor/progress')),
      ]);
      await page.getByRole('button', { name: label('دخول', 'Sign in'), exact: true }).click();
      for (const response of await data) assert.equal(response.status(), 200, response.url());
      await page.getByText(label('دروسك المتاحة', 'Available lessons'), { exact: true }).waitFor();
      assert.equal(await page.getByText(label('تعذر تحميل الدروس. تحقق من الاتصال ثم أعد المحاولة.', 'Lessons could not be loaded. Check your connection and retry.'), { exact: true }).count(), 0);
      await snapshot('home');
      await page.getByRole('radio', { name: language === 'ar' ? 'English / EN' : 'العربية / AR', exact: true }).click();
      await page.getByText(label('Available lessons', 'دروسك المتاحة'), { exact: true }).waitFor();
      assert.equal(await page.getByRole('button', { name: /^(دخول|Sign in)$/ }).count(), 0);
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`PASS Expo web ${language}/${appearance}: original logo on login/home, persisted preferences, draft and authenticated-state retention`);
    }
    fs.writeFileSync(path.join(output, 'expo-browser-results.json'), JSON.stringify({ result: 'passed', platform: 'Expo web; no physical device', findings }, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
