/* Disposable fixture QA only. No real credentials, speech, students or Azure calls. */
const { createServer } = require('node:http');
const { readFile, mkdir, writeFile } = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { readdir } = require('node:fs/promises');
const { chromium } = require(path.join(process.env.TEMP, 'aqlith-voice-qa/node_modules/playwright'));
const root = path.resolve('apps/tutor-mobile/dist-voice-qa');
const output = path.resolve('docs/qa/voice');
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.ttf': 'font/ttf', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  try {
    const file = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
    if (!file.startsWith(root + path.sep) && file !== root) { res.writeHead(403).end(); return; }
    const target = file === root ? path.join(root, 'index.html') : file;
    const body = await readFile(target);
    res.writeHead(200, { 'content-type': mime[path.extname(target)] || 'application/octet-stream' }).end(body);
  } catch { res.writeHead(404).end(); }
});
const report = { browser: 'Installed Google Chrome (channel: chrome)', fixtureData: true, realSpeechTested: false, checks: [], screenshots: [] };
const check = name => report.checks.push(name);
async function fileHashes(paths) {
  const entries = [];
  async function visit(target) {
    const info = await require('node:fs/promises').stat(target);
    if (info.isDirectory()) for (const name of (await readdir(target)).sort()) await visit(path.join(target, name));
    else entries.push([path.relative(process.cwd(), target).replaceAll('\\', '/'), createHash('sha256').update(await readFile(target)).digest('hex')]);
  }
  for (const target of paths) await visit(target);
  return Object.fromEntries(entries);
}
const sourcePaths = ['apps/tutor-mobile/App.tsx', 'apps/tutor-mobile/app.json', 'apps/tutor-mobile/package.json',
  'apps/tutor-mobile/package-lock.json', 'apps/tutor-mobile/src', 'apps/tutor-mobile/assets', 'packages/voice',
  'packages/presentation', 'packages/contracts', 'tools/qa/voice-browser.cjs'];
(async () => {
  await mkdir(output, { recursive: true });
  report.sourceSha256 = await fileHashes(sourcePaths);
  report.bundleSha256 = await fileHashes([path.join(root, '_expo')]);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  // Never install or fall back to bundled Chromium.
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    for (const language of ['ar', 'en']) for (const appearance of ['light', 'dark']) for (const width of [360, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 1 });
      const page = await context.newPage();
      const failures = [];
      page.on('pageerror', error => failures.push(error.message));
      let requests = 0;
      let offline = false;
      await context.addInitScript(({ language, appearance }) => {
        localStorage.setItem('aqlith.preferences.v1', JSON.stringify({ language, appearance }));
        // Explicitly simulated recognition; tests UI events only, never audio accuracy.
        class FixtureSpeech {
          start() { window.__qaSpeech = this; this.onstart?.(); }
          stop() { this.onaudioend?.(); }
          abort() { this.onend?.(); }
        }
        window.SpeechRecognition = FixtureSpeech;
      }, { language, appearance });
      await page.route('http://localhost:8000/**', async route => {
        const url = new URL(route.request().url());
        if (route.request().method() === 'OPTIONS') return route.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*' } });
        requests++;
        if (offline) return route.abort('failed');
        let body;
        if (url.pathname === '/auth/login') body = { access_token: 'disposable-ui-fixture' };
        else if (url.pathname.endsWith('/classroom/me')) body = { id: 999999, role: 'STUDENT' };
        else if (url.pathname.endsWith('/progress')) body = { attempts: 0, accuracy_percent: 0 };
        else if (url.pathname.endsWith('/recommendation')) return route.fulfill({ status: 404, json: {}, headers: { 'access-control-allow-origin': '*' } });
        else body = [];
        return route.fulfill({ json: body, headers: { 'access-control-allow-origin': '*' } });
      });
      const ar = language === 'ar';
      const label = (a, e) => ar ? a : e;
      await page.goto(origin);
      await page.getByLabel(label('البريد الإلكتروني', 'Email'), { exact: true }).fill('voice-qa@example.invalid');
      await page.getByLabel(label('كلمة المرور', 'Password'), { exact: true }).fill('disposable-fixture-only');
      await page.getByRole('button', { name: label('دخول', 'Sign in'), exact: true }).click();
      await page.getByRole('button', { name: /Voice commands|الأوامر الصوتية/ }).click();
      const input = page.getByLabel(label('نص الأمر القابل للتعديل', 'Editable command transcript'), { exact: true });
      await input.waitFor();
      assert.equal(await page.locator('html').getAttribute('dir'), ar ? 'rtl' : 'ltr');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const speak = page.getByRole('button', { name: label('● اضغط واتكلم', '● Tap to speak'), exact: true });
      assert.equal(await speak.isDisabled(), true);
      const filename = `${language}-${appearance}-${width}.png`;
      await page.screenshot({ path: path.join(output, filename), fullPage: true });
      report.screenshots.push(filename);
      check(`${language}/${appearance}/${width}: RTL, viewport fit, Cairo UI, mic off and consent required`);
      await input.fill(ar ? 'وريني تقدمي' : 'show my progress');
      const before = requests;
      await page.getByRole('button', { name: label('مراجعة التنفيذ', 'Review action'), exact: true }).click();
      assert.equal(requests, before);
      await page.getByRole('button', { name: label('رجوع للتعديل', 'Keep editing'), exact: true }).click();
      assert.equal(await page.getByRole('button', { name: label('تأكيد', 'Confirm'), exact: true }).count(), 0);
      await page.getByRole('button', { name: label('مراجعة التنفيذ', 'Review action'), exact: true }).click();
      if (width === 390) {
        const review = `${language}-${appearance}-${width}-review.png`;
        await page.screenshot({ path: path.join(output, review), fullPage: true }); report.screenshots.push(review);
      }
      await page.getByRole('button', { name: label('تأكيد', 'Confirm'), exact: true }).click();
      await page.getByText(ar ? '0 محاولة، الدقة 0%' : '0 attempts, 0% accuracy', { exact: true }).waitFor();
      check(`${language}/${appearance}/${width}: transcript editing, review cancellation, explicit confirmation and fixture-only progress`);
      await input.fill('افتح فصولي كمدرس');
      await page.getByRole('button', { name: label('مراجعة التنفيذ', 'Review action'), exact: true }).click();
      await page.getByRole('button', { name: label('تأكيد', 'Confirm'), exact: true }).click();
      await page.getByText(label('الأمر ده للمدرس فقط بحساب موثّق.', 'This command requires a verified teacher account.'), { exact: true }).waitFor();
      check(`${language}/${appearance}/${width}: student teacher-command denied`);
      await page.getByLabel(label('الموافقة على استخدام خدمة التعرف على الكلام', 'Consent to speech service processing'), { exact: true }).check();
      await speak.click();
      await page.getByText(label('● بنسمعك — ١٥ ثانية بحد أقصى', '● Listening — 15 second maximum'), { exact: true }).waitFor();
      await page.getByRole('button', { name: label('إلغاء', 'Cancel'), exact: true }).click();
      assert.equal(await input.inputValue(), '');
      assert.equal(await page.evaluate(() => window.__qaSpeech.onresult === null && window.__qaSpeech.onend === null), true);
      await speak.click();
      await page.evaluate(() => window.__qaSpeech.onerror({ error: 'not-allowed' }));
      await page.getByText(label('إذن الميكروفون مرفوض. غيّره من الإعدادات أو اكتب الأمر.', 'Microphone permission denied. Change it in settings or type instead.'), { exact: true }).waitFor();
      await page.getByRole('button', { name: label('حاول تاني', 'Retry'), exact: true }).click();
      await page.getByRole('button', { name: label('■ إيقاف', '■ Stop'), exact: true }).click();
      await page.evaluate(() => { window.__qaSpeech.onresult({ results: [[{ transcript: 'وريني تقدمي' }]] }); window.__qaSpeech.onend(); });
      await page.waitForFunction(() => document.querySelector('textarea')?.value === 'وريني تقدمي');
      assert.equal(await input.inputValue(), 'وريني تقدمي');
      assert.equal(await page.getByRole('button', { name: label('تأكيد', 'Confirm'), exact: true }).count(), 0);
      check(`${language}/${appearance}/${width}: SIMULATED mic denied, retry, stop, transcript review and cancel`);
      await page.getByRole('button', { name: label('مراجعة التنفيذ', 'Review action'), exact: true }).click();
      offline = true;
      await page.getByRole('button', { name: label('تأكيد', 'Confirm'), exact: true }).click();
      await page.getByText(label('تعذر إكمال الطلب. تحقق من الاتصال وخدمة الكلام وحاول تاني، أو استخدم الكتابة.', 'Request failed. Check your connection and speech service, retry, or type instead.'), { exact: true }).waitFor();
      check(`${language}/${appearance}/${width}: connection error handled without provider details`);
      // Browser accessibility semantics and minimum hit areas on visible actionable controls.
      const violations = await page.getByRole('button').evaluateAll(nodes => nodes.filter(node => {
        const rect = node.getBoundingClientRect();
        return rect.width && rect.height && (rect.width < 44 || rect.height < 44 || !node.textContent.trim());
      }).map(node => node.textContent));
      assert.deepEqual(violations, []); assert.deepEqual(failures, []);
      check(`${language}/${appearance}/${width}: named buttons >=44px, labeled transcript/switches, no JS errors`);
      await context.close();
    }
    // Real Chrome permission denial: OS/browser microphone access is denied by CDP.
    // No fake recognizer in this context and no microphone audio is captured.
    const deniedContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const deniedPage = await deniedContext.newPage();
    const qaLesson = { id: 'qa-math-lesson', subject_code: 'mathematics', curriculum_version: 'qa-curriculum',
      title_en: 'Disposable equation lesson', title_ar: 'درس تجريبي', summary_en: '2x + 3 = 7',
      summary_ar: '٢س + ٣ = ٧', content_language: 'ar', skill_codes: [] };
    let tutorMessages = 0;
    let tutorBody;
    let sessionBody;
    let holdIdentity = false;
    let releaseIdentity;
    let announceIdentity;
    await deniedContext.addInitScript(() => {
      localStorage.setItem('aqlith.preferences.v1', JSON.stringify({ language: 'en', appearance: 'light' }));
    });
    await deniedPage.route('http://localhost:8000/**', async route => {
      const request = route.request();
      const url = new URL(request.url());
      const headers = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*' };
      if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
      if (url.pathname.endsWith('/recommendation')) return route.fulfill({ status: 404, json: {}, headers });
      if (url.pathname.endsWith('/classroom/me') && holdIdentity) {
        announceIdentity();
        await new Promise(resolve => { releaseIdentity = resolve; });
      }
      let body = [];
      if (url.pathname === '/auth/login') body = { access_token: 'disposable-ui-fixture' };
      else if (url.pathname.endsWith('/classroom/me')) body = { id: 999999, role: 'STUDENT' };
      else if (url.pathname.endsWith('/progress')) body = { attempts: 0, accuracy_percent: 0 };
      else if (url.pathname.endsWith('/lessons')) body = [qaLesson];
      else if (url.pathname.endsWith('/sessions')) { sessionBody = request.postDataJSON(); body = { id: 'qa-session' }; }
      else if (url.pathname.endsWith('/messages')) { tutorMessages++; tutorBody = request.postDataJSON(); body = { answer: { content: 'Disposable Tutor response: x = 2' } }; }
      return route.fulfill({ json: body, headers: { 'access-control-allow-origin': '*' } });
    });
    const cdp = await deniedContext.newCDPSession(deniedPage);
    await cdp.send('Browser.setPermission', { permission: { name: 'microphone' }, setting: 'denied', origin });
    await deniedPage.goto(origin);
    await deniedPage.getByLabel('Email', { exact: true }).fill('voice-qa@example.invalid');
    await deniedPage.getByLabel('Password', { exact: true }).fill('disposable-fixture-only');
    await deniedPage.getByRole('button', { name: 'Sign in', exact: true }).click();
    await deniedPage.getByRole('button', { name: /Voice commands/ }).click();
    await deniedPage.getByLabel('Consent to speech service processing', { exact: true }).check();
    await deniedPage.getByRole('button', { name: '● Tap to speak', exact: true }).click();
    await deniedPage.getByText('Microphone permission denied. Change it in settings or type instead.', { exact: true }).waitFor();
    await deniedPage.getByLabel('Editable command transcript', { exact: true }).fill('show my progress');
    await deniedPage.getByText('Microphone permission denied. Change it in settings or type instead.', { exact: true }).waitFor({ state: 'hidden' });
    check('Real installed Chrome: microphone permission denied via browser policy, safe fallback to editable text; no audio captured');
    report.realPermissionDeniedTested = true;
    // Capture the blank denied state after retry, never the disposable login form.
    await deniedPage.getByRole('button', { name: 'Cancel', exact: true }).click();
    await deniedPage.getByRole('button', { name: '● Tap to speak', exact: true }).click();
    await deniedPage.getByText('Microphone permission denied. Change it in settings or type instead.', { exact: true }).waitFor();
    await deniedPage.getByRole('alert').scrollIntoViewIfNeeded();
    await deniedPage.screenshot({ path: path.join(output, 'en-light-390-permission-denied.png'), fullPage: true });
    report.screenshots.push('en-light-390-permission-denied.png');
    // Cancel a pending authenticated read: editing must unlock before it returns.
    holdIdentity = true;
    let holdTimer;
    const identityHeld = new Promise((resolve, reject) => {
      holdTimer = setTimeout(() => reject(Error('Identity fixture was not requested')), 5000);
      announceIdentity = () => { clearTimeout(holdTimer); resolve(); };
    });
    await deniedPage.getByLabel('Editable command transcript', { exact: true }).fill('show my progress');
    await deniedPage.getByRole('button', { name: 'Review action', exact: true }).click();
    await deniedPage.getByRole('button', { name: 'Confirm', exact: true }).click();
    await identityHeld;
    await deniedPage.getByRole('button', { name: 'Cancel', exact: true }).click();
    const editable = deniedPage.getByLabel('Editable command transcript', { exact: true });
    assert.equal(await editable.isEditable(), true);
    assert.equal(await editable.inputValue(), '');
    holdIdentity = false;
    const released = deniedPage.waitForResponse(response => response.url().endsWith('/classroom/me'));
    releaseIdentity(); await released;
    const question = 'اشرحلي ٢س + ٣ = ٧';
    await deniedPage.getByLabel('Editable command transcript', { exact: true }).fill(question);
    await deniedPage.getByRole('button', { name: 'Review action', exact: true }).click();
    await deniedPage.getByRole('button', { name: 'Confirm', exact: true }).click();
    await deniedPage.getByRole('button', { name: qaLesson.title_ar, exact: true }).click();
    const tutorInput = deniedPage.getByLabel('Your lesson question', { exact: true });
    await tutorInput.waitFor();
    assert.equal(await tutorInput.inputValue(), question);
    assert.equal(tutorMessages, 0);
    await deniedPage.getByRole('button', { name: 'Ask', exact: true }).click();
    await deniedPage.getByText('Disposable Tutor response: x = 2', { exact: true }).waitFor();
    assert.equal(tutorMessages, 1);
    assert.deepEqual(sessionBody, { subject_code: 'mathematics', curriculum_version: 'qa-curriculum' });
    assert.deepEqual(tutorBody, { content: question, lesson_id: qaLesson.id, locale: 'ar-EG' });
    check('Cancellation unlocks a pending authenticated read; Tutor handoff preserves exact Arabic math, official Arabic lesson title and ar-EG under English UI; explicit Ask and curriculum preserved; inference mocked');
    await deniedContext.close();
  } finally { await browser.close(); }
  assert.deepEqual(await fileHashes(sourcePaths), report.sourceSha256, 'Source changed while browser QA was running');
  report.screenshotsSha256 = await fileHashes(report.screenshots.map(file => path.join(output, file)));
  report.completedAt = new Date().toISOString();
  await writeFile(path.join(output, 'browser-results.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ checks: report.checks.length, screenshots: report.screenshots.length, browser: report.browser, realSpeechTested: false }));
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
