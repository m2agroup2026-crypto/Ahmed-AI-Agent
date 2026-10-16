// Real local backend + installed Chrome. No assets, secrets, or remote services created.
const { chromium } = require(process.env.AQLITH_PLAYWRIGHT || require('node:path').join(require('node:os').tmpdir(), 'aqlith-preview-qa/node_modules/playwright-core'));
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const accounts = JSON.parse(fs.readFileSync(path.join(os.tmpdir(), 'aqlith-preview-accounts.json'), 'utf8'));
const output = path.join(os.tmpdir(), 'aqlith-brand-qa');
fs.mkdirSync(output, { recursive: true });
const base = process.env.AQLITH_PREVIEW_URL || 'http://localhost:3000';
const findings = [];
const key = 'aqlith.preferences.v1';
const official = 'شرح أصلي للاختبار: 17 - 26 = -9.';
const prompt = 'احسب 17 - 26';

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    for (const language of ['ar', 'en']) for (const appearance of ['light', 'dark']) {
      const label = (ar, en) => language === 'ar' ? ar : en;
      const context = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: 'light' });
      const page = await context.newPage();
      const pageErrors = [];
      page.on('pageerror', e => pageErrors.push(e.message));
      const changeLanguage = async (p, lang) => {
        await p.getByRole('button', { name: lang === 'ar' ? 'العربية / AR' : 'English / EN', exact: true }).click();
        await p.waitForFunction(lang => document.documentElement.lang === lang, lang);
      };
      const snapshot = async (p, name) => {
        const logo = p.locator('.brand-logo img:visible');
        await logo.evaluate(image => image.decode());
        const renderedLogo = await logo.evaluate(image => ({ source: image.getAttribute('src'), width: image.naturalWidth,
          frame: getComputedStyle(image.closest('.brand-logo')).backgroundColor }));
        assert(renderedLogo.source.endsWith(`aqlith-logo-${appearance}.png`));
        assert(renderedLogo.width > 1000);
        assert.equal(renderedLogo.frame, appearance === 'dark' ? 'rgb(14, 22, 37)' : 'rgb(255, 255, 255)');
        for (const width of [360, 390]) {
          await p.setViewportSize({ width, height: width === 360 ? 800 : 844 });
          await p.screenshot({ path: path.join(output, `${language}-${appearance}-${name}-${width}.png`), fullPage: true });
          const result = await p.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth,
            theme: document.documentElement.dataset.theme, direction: document.documentElement.dir,
            small: [...document.querySelectorAll('button:enabled, input:not([type=checkbox]), select, .topbar a')].filter(e => {
              const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.height < 44;
            }).map(e => e.tagName) }));
          assert.equal(result.page, width, `${name}: overflow`);
          assert.equal(result.theme, appearance);
          assert.deepEqual(result.small, [], `${name}: touch target`);
          findings.push({ language, appearance, name, logo: renderedLogo, ...result });
        }
      };
      await Promise.all([page.waitForResponse(r => r.url() === base + '/api/classroom/me'), page.goto(base + '/classroom')]);
      assert.equal(await page.locator('html').getAttribute('lang'), 'ar');
      await page.emulateMedia({ colorScheme: 'dark' });
      await page.waitForFunction(() => document.documentElement.dataset.theme === 'dark');
      await page.getByRole('group', { name: 'Appearance / المظهر' }).getByRole('button', { name: 'فاتح', exact: true }).click();
      await page.waitForFunction(() => document.documentElement.dataset.theme === 'light');
      await page.emulateMedia({ colorScheme: 'dark' });
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
      await changeLanguage(page, language);
      await page.getByRole('group', { name: 'Appearance / المظهر' }).getByRole('button', { name: appearance === 'light' ? label('فاتح', 'Light') : label('داكن', 'Dark'), exact: true }).click();
      await page.reload();
      await page.waitForFunction(({ language, appearance }) => document.documentElement.lang === language && document.documentElement.dataset.theme === appearance, { language, appearance });
      assert.deepEqual(await page.evaluate(k => JSON.parse(localStorage.getItem(k)), key), { language, appearance });
      await snapshot(page, 'login');
      async function login(p, account) {
        await p.getByLabel(label('البريد الإلكتروني', 'Email'), { exact: true }).fill(account.email);
        await p.getByLabel(label('كلمة المرور', 'Password'), { exact: true }).fill(account.password);
        await p.getByRole('button', { name: label('تسجيل الدخول', 'Sign in'), exact: true }).click();
        await p.getByRole('button', { name: label('تسجيل الخروج', 'Sign out'), exact: true }).waitFor();
      }
      await login(page, accounts.teacher);
      const cookie = (await context.cookies()).find(c => c.name === 'nexora_access_token');
      assert(cookie.httpOnly && cookie.sameSite === 'Strict');
      const classroomName = `QA ${language}/${appearance} ${Date.now()}`;
      await page.getByLabel(label('اسم الفصل الجديد', 'New classroom name')).fill(classroomName);
      await page.getByRole('button', { name: label('إنشاء فصل', 'Create classroom'), exact: true }).click();
      await page.locator('code').waitFor();
      const invite = await page.locator('code').innerText();
      await page.getByLabel(label('العنوان', 'Title'), { exact: true }).fill('Original 17 - 26');
      await page.getByLabel(label('الدرس الأصلي', 'Original lesson'), { exact: true }).fill(official);
      await page.getByLabel(label('السؤال الأصلي', 'Original question'), { exact: true }).fill(prompt);
      await page.getByLabel(label('الإجابة الرقمية', 'Numeric answer'), { exact: true }).fill('-9');
      await changeLanguage(page, language === 'ar' ? 'en' : 'ar');
      await page.getByRole('group', { name: 'Appearance / المظهر' }).getByRole('button', { name: appearance === 'light' ? label('Dark', 'داكن') : label('Light', 'فاتح'), exact: true }).click();
      assert.equal(await page.locator('textarea[name=lesson]').inputValue(), official);
      assert.equal(await page.locator('input[name=title]').inputValue(), 'Original 17 - 26');
      await changeLanguage(page, language);
      await page.getByRole('group', { name: 'Appearance / المظهر' }).getByRole('button', { name: appearance === 'light' ? label('فاتح', 'Light') : label('داكن', 'Dark'), exact: true }).click();
      await page.getByRole('checkbox', { name: language === 'ar' ? /أنا مؤلف/ : /I authored/ }).check();
      await page.getByRole('button', { name: label('إسناد الاختبار', 'Assign assessment'), exact: true }).click();
      await page.getByRole('status').filter({ hasText: label('تم إسناد الاختبار.', 'Assessment assigned.') }).waitFor();
      assert.equal(await page.locator('article.lesson-card p').first().textContent(), official);
      assert.equal(await page.locator('article.lesson-card bdi').first().textContent(), '17 - 26 = -9');
      await snapshot(page, 'teacher');

      const student = await browser.newContext({ viewport: { width: 360, height: 800 } });
      await student.addInitScript(({ key, language, appearance }) => localStorage.setItem(key, JSON.stringify({ language, appearance })), { key, language, appearance });
      const sp = await student.newPage();
      await sp.goto(base + '/classroom');
      await sp.waitForFunction(lang => document.documentElement.lang === lang, language);
      await login(sp, accounts.student);
      await sp.getByLabel(label('رمز الانضمام للفصل', 'Classroom join code')).fill(invite);
      await sp.getByRole('button', { name: label('الانضمام للفصل', 'Join classroom'), exact: true }).click();
      await sp.getByRole('button', { name: classroomName, exact: true }).click();
      await sp.getByLabel(label('رمز الانضمام للفصل', 'Classroom join code')).fill('');
      await sp.getByRole('button', { name: label('بدء / استئناف الاختبار', 'Start / resume exam'), exact: true }).click();
      await sp.getByLabel(prompt, { exact: true }).fill('-9');
      await changeLanguage(sp, language === 'ar' ? 'en' : 'ar');
      assert.equal(await sp.getByLabel(prompt, { exact: true }).inputValue(), '-9');
      await changeLanguage(sp, language);
      assert.equal(await sp.getByLabel(prompt, { exact: true }).getAttribute('dir'), 'ltr');
      await snapshot(sp, 'practice');
      await sp.getByRole('button', { name: label('إرسال الإجابات النهائية', 'Submit final answers'), exact: true }).click();
      await sp.getByRole('status').filter({ hasText: label('النتيجة:', 'Result:') }).waitFor();
      assert((await sp.getByRole('status').textContent()).includes('1/1'));
      await snapshot(sp, 'progress');
      await page.getByRole('button', { name: label('تحديث النتائج', 'Refresh results'), exact: true }).click();
      await page.getByRole('cell', { name: '1/1', exact: true }).waitFor();
      await snapshot(page, 'results');

      const [lessonsResponse] = await Promise.all([page.waitForResponse(r => r.url() === base + '/api/tutor/lessons'), page.goto(base + '/')]);
      assert.equal(lessonsResponse.status(), 200);
      const lessons = await lessonsResponse.json();
      await page.getByRole('heading', { name: label('الدروس المتاحة', 'Available lessons'), exact: true }).waitFor();
      if (lessons.length) await page.locator('article.lesson-card').first().waitFor();
      for (const lesson of lessons.filter(item => ['ar', 'en'].includes(item.content_language))) {
        assert(await page.getByRole('heading', { name: lesson['title_' + lesson.content_language], exact: true }).isVisible());
      }
      await snapshot(page, 'curriculum');
      await page.goto(base + '/classroom/live');
      await page.getByLabel(label('الفصل الدراسي', 'Your classroom')).selectOption({ label: classroomName });
      await page.getByLabel(label('عنوان الحصة', 'Session title'), { exact: true }).fill('Local control preview');
      await page.getByRole('button', { name: label('جدولة', 'Schedule'), exact: true }).click();
      await page.getByRole('heading', { name: 'Local control preview', exact: true }).waitFor();
      await page.getByRole('button', { name: label('بدء معاينة التحكم', 'Start control preview'), exact: true }).click();
      await page.getByRole('button', { name: label('الانضمام لمعاينة التحكم', 'Join control preview'), exact: true }).click();
      await page.getByRole('status').filter({ hasText: label('لوحة التحكم متصلة؛ الوسائط غير متاحة', 'Control panel connected; media unavailable') }).waitFor();
      assert(await page.getByRole('button', { name: label('كاميرا المعلم', 'Teacher camera'), exact: true }).isDisabled());
      await snapshot(page, 'live');
      await page.getByRole('button', { name: label('إنهاء الحصة', 'End session'), exact: true }).click();
      assert.deepEqual(pageErrors, []);
      await student.close(); await context.close();
      console.log(`PASS ${language}/${appearance}: login, draft retention, original math, exam, grading, progress, curriculum, live; 360 + 390`);
    }
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({ base, findings, result: 'passed' }, null, 2));
    console.log('Screenshots and results: ' + output);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
