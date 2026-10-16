// Requires playwright-core in a temporary tools directory; uses installed Chrome.
const { chromium } = require(process.env.AQLITH_PLAYWRIGHT || require('node:path').join(require('node:os').tmpdir(), 'aqlith-preview-qa/node_modules/playwright-core'));
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const output = path.join(os.tmpdir(), 'aqlith-preview-qa', process.env.AQLITH_PREVIEW_URL ? 'lan-artifacts' : 'artifacts');
fs.mkdirSync(output, { recursive: true });
const accounts = JSON.parse(fs.readFileSync(path.join(os.tmpdir(), 'aqlith-preview-accounts.json'), 'utf8'));
const base = process.argv[2] || process.env.AQLITH_PREVIEW_URL || 'http://localhost:3000';
const findings = [];
const className = 'الرياضيات — Mobile QA ' + new Date().toISOString().slice(11, 19);

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const teacher = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const student = await browser.newContext({ viewport: { width: 360, height: 800 } });
    const noJs = await browser.newContext({ javaScriptEnabled: false });
    const fallback = await noJs.newPage();
    await fallback.goto(base + '/classroom');
    await fallback.getByLabel('البريد الإلكتروني', { exact: true }).fill('nojs@preview.example.com');
    await fallback.getByLabel('كلمة المرور', { exact: true }).fill('not-a-real-credential');
    const [fallbackRequest] = await Promise.all([
      fallback.waitForRequest(r => r.isNavigationRequest() && r.method() === 'POST'),
      fallback.getByRole('button', { name: 'تسجيل الدخول', exact: true }).click(),
    ]);
    assert.equal(new URL(fallbackRequest.url()).search, '');
    await noJs.close();
    const tp = await teacher.newPage(), sp = await student.newPage();
    async function openClassroom(page) {
      await Promise.all([page.waitForResponse(r => r.url() === base + '/api/classroom/me'), page.goto(base + '/classroom')]);
      await page.getByRole('button', { name: 'English / EN', exact: true }).click();
    }
    async function snapshot(page, name) {
      await page.screenshot({ path: path.join(output, name + '.png'), fullPage: true });
      const sizes = await page.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth }));
      findings.push({ name, ...sizes });
      assert(sizes.page <= sizes.viewport, `${name}: horizontal overflow ${JSON.stringify(sizes)}`);
      const small = await page.locator('.classroom button:enabled, .classroom input:not([type="checkbox"]), .classroom .topbar a, .live-classroom button:enabled, .live-classroom input:not([type="checkbox"]), .live-classroom select, .live-classroom .topbar a').evaluateAll(elements => elements.filter(e => {
        const rect = e.getBoundingClientRect(); return rect.width > 0 && rect.height > 0 && rect.height < 44;
      }).map(e => e.tagName + ':' + (e.getAttribute('name') || e.textContent)));
      assert.deepEqual(small, [], 'Touch targets below 44px');
    }
    async function login(page, account) {
      await openClassroom(page);
      await page.getByLabel('Email', { exact: true }).fill(account.email);
      await page.getByLabel('Password', { exact: true }).fill(account.password);
      await page.getByRole('button', { name: 'Sign in', exact: true }).click();
      await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    }
    await openClassroom(tp);
    await snapshot(tp, 'login-390');
    await tp.getByLabel('Email', { exact: true }).fill(accounts.teacher.email);
    await tp.getByLabel('Password', { exact: true }).fill('deliberately-wrong-password');
    await tp.getByRole('button', { name: 'Sign in', exact: true }).click();
    await tp.getByRole('status').filter({ hasText: /invalid|incorrect/i }).waitFor();
    await login(tp, accounts.teacher);
    const cookie = (await teacher.cookies()).find(c => c.name === 'nexora_access_token');
    assert(cookie && cookie.httpOnly && cookie.sameSite === 'Strict');
    assert(!(await tp.evaluate(() => document.cookie)).includes('nexora_access_token'));
    const csrf = await teacher.request.post(base + '/api/classroom/classes', { headers: { origin: 'https://evil.example' }, data: { name: 'Forbidden' } });
    assert.equal(csrf.status(), 403);
    const missingOrigin = await teacher.request.post(base + '/api/classroom/classes', { data: { name: 'Forbidden' } });
    assert.equal(missingOrigin.status(), 403);
    const unknown = await teacher.request.get(base + '/api/classroom/not-allowed');
    assert.equal(unknown.status(), 404);
    await tp.getByLabel('New classroom name').fill(className);
    await tp.getByRole('button', { name: 'Create classroom', exact: true }).click();
    await tp.getByText('Share privately with your students:', { exact: false }).waitFor();
    const invite = await tp.locator('code').innerText();
    await tp.getByLabel('Title', { exact: true }).fill('جمع الأعداد — Original addition');
    await tp.getByLabel('Original lesson', { exact: true }).fill('نجمع الكميات: 17 + 26 = 43. هذا شرح أصلي للاختبار المحلي.');
    await tp.getByLabel('Original question', { exact: true }).fill('ما ناتج 17 + 26؟');
    await tp.getByLabel('Numeric answer', { exact: true }).fill('43');
    await tp.getByRole('checkbox', { name: /I authored/ }).check();
    await tp.getByRole('button', { name: 'Assign assessment', exact: true }).click();
    await tp.getByRole('status').filter({ hasText: 'Assessment assigned.' }).waitFor();
    await snapshot(tp, 'teacher-390');
    await login(sp, accounts.student);
    await sp.getByLabel('Classroom join code').fill(invite);
    await sp.getByRole('button', { name: 'Join classroom', exact: true }).click();
    await sp.getByRole('button', { name: className, exact: true }).click();
    await sp.getByLabel('Classroom join code').fill('');
    await sp.getByRole('button', { name: 'Start / resume exam' }).click();
    await sp.getByLabel('ما ناتج 17 + 26؟').fill('43');
    await snapshot(sp, 'student-exam-360');
    await sp.getByRole('button', { name: 'Submit final answers' }).click();
    await sp.getByRole('status').filter({ hasText: 'Result: 1/1' }).waitFor();
    const progress = await (await student.request.get(base + '/api/classroom/progress')).json();
    assert(progress.completed >= 1 && progress.earned === progress.possible);
    assert(await sp.getByText(`${progress.completed} completed · ${progress.earned}/${progress.possible} points`, { exact: true }).isVisible());
    await snapshot(sp, 'student-progress-360');
    await tp.getByRole('button', { name: 'Refresh results' }).click();
    await tp.getByRole('cell', { name: '1/1', exact: true }).waitFor();
    await snapshot(tp, 'teacher-results-390');
    const [curriculumResponse] = await Promise.all([
      tp.waitForResponse(r => r.url() === base + '/api/tutor/lessons'), tp.goto(base + '/'),
    ]);
    assert.equal(curriculumResponse.status(), 200);
    assert(Array.isArray(await curriculumResponse.json()));
    await tp.getByRole('heading', { name: 'Available lessons' }).waitFor();
    await snapshot(tp, 'curriculum-390');
    for (const page of [tp, sp]) {
      await page.goto(base + '/classroom/live');
      await page.getByRole('button', { name: 'العربية / AR', exact: true }).click();
      await page.getByRole('heading', { name: 'الفصل المباشر', exact: true }).waitFor();
      await page.getByLabel('الفصل الدراسي').selectOption({ label: className });
      await snapshot(page, 'live-ar-' + page.viewportSize().width);
      assert.equal(await page.locator('main').getAttribute('dir'), 'rtl');
    }
    await tp.getByRole('button', { name: 'English', exact: true }).click();
    const classId = (await (await teacher.request.get(base + '/api/classroom/classes')).json()).find(item => item.name === className).id;
    await tp.getByLabel('Your classroom').selectOption(classId);
    await tp.getByLabel('Session title', { exact: true }).fill('Local mathematics control preview');
    await tp.getByRole('button', { name: 'Schedule', exact: true }).click();
    await tp.getByRole('heading', { name: 'Local mathematics control preview', exact: true }).waitFor();
    await tp.getByRole('button', { name: 'Start control preview', exact: true }).click();
    await tp.getByRole('button', { name: 'Join control preview', exact: true }).click();
    await tp.getByText('Control panel connected; media unavailable', { exact: true }).waitFor();
    for (const name of ['Teacher camera', 'Teacher microphone', 'Share screen']) {
      assert(await tp.getByRole('button', { name, exact: true }).isDisabled());
    }
    await snapshot(tp, 'live-connected-390');
    await sp.reload();
    await sp.getByRole('button', { name: 'العربية / AR', exact: true }).click();
    await sp.getByLabel('الفصل الدراسي').selectOption({ label: className });
    await sp.getByRole('button', { name: 'English', exact: true }).click();
    await sp.getByLabel('Your classroom').selectOption(classId);
    const liveList = await student.request.get(base + `/api/classroom/classes/${classId}/live`);
    const liveItems = await liveList.json();
    console.log('Student live list:', liveList.status(), 'sessions:', liveItems.length, 'selected class matches:', (await sp.getByLabel('Your classroom').inputValue()) === classId);
    assert(liveItems.some(item => item.title === 'Local mathematics control preview'));
    console.log('Font inspection:', await sp.locator('main').evaluate(element => ({ computedFamily: getComputedStyle(element).fontFamily,
      loadedFonts: [...document.fonts].map(font => font.family) })));
    await sp.getByRole('button', { name: /Local mathematics control preview/ }).click();
    await sp.getByRole('button', { name: 'Join control preview', exact: true }).click();
    await sp.getByText('Control panel connected; media unavailable', { exact: true }).waitFor();
    await sp.getByRole('button', { name: 'Raise hand', exact: true }).click();
    await tp.getByRole('button', { name: 'Allow microphone (preview)', exact: true }).click();
    await tp.getByRole('button', { name: 'Block microphone (preview)', exact: true }).waitFor();
    await snapshot(sp, 'student-live-360');
    await tp.getByRole('button', { name: 'Revoke access', exact: true }).click();
    await sp.getByText('Access revoked or sign-in expired', { exact: true }).waitFor();
    await tp.getByRole('button', { name: 'End session', exact: true }).click();
    await tp.getByText('Session ended or expired', { exact: true }).waitFor();
    await sp.goto(base + '/classroom');
    await sp.getByRole('button', { name: 'Sign out', exact: true }).click();
    await sp.getByRole('button', { name: 'Sign in', exact: true }).waitFor();
    assert(!(await student.cookies()).some(c => c.name === 'nexora_access_token'));
    const report = { result: 'passed', base, journey: 'UI login, create, join, assign original math, submit, grade 1/1, results, progress, live start/join/end', security: 'HttpOnly, SameSite Strict, token absent from document.cookie, foreign/missing Origin 403, route allowlist, logout', findings };
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
