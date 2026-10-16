// Validate the live manifest and Android bundle independently, never inferring one from the other.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const base = process.env.AQLITH_EXPO_URL || 'http://10.222.35.28:8081';
const mode = process.argv[2] || 'manifest';
const output = path.join(os.tmpdir(), 'aqlith-brand-qa');
fs.mkdirSync(output, { recursive: true });
(async () => {
  assert(['manifest', 'android-bundle'].includes(mode));
  const response = await fetch(base, { headers: { 'expo-platform': 'android' } });
  assert.equal(response.status, 200);
  const manifest = await response.json();
  const config = manifest.extra.expoClient;
  assert.equal(config.hostUri, new URL(base).host);
  assert.equal(config.userInterfaceStyle, 'automatic');
  let result;
  if (mode === 'manifest') {
    assert(config.iconUrl, 'Manifest asset resolution failed: iconUrl missing');
    assert.equal(new URL(config.iconUrl).origin, base);
    const icon = await fetch(config.iconUrl);
    assert.equal(icon.status, 200);
    const bytes = Buffer.from(await icon.arrayBuffer());
    const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
    assert.equal(sha256, 'd6dea45b853ccfb8b98d9f1243c02c8c563058c586770638229d520180972319');
    result = { result: 'passed', mode, manifestHttp: response.status, iconHttp: icon.status, iconBytes: bytes.length, sha256, iconUrl: config.iconUrl };
  } else {
    const url = new URL(manifest.launchAsset.url);
    url.searchParams.set('lazy', 'false');
    const bundle = await fetch(url);
    const code = await bundle.text();
    assert.equal(bundle.status, 200, code.slice(0, 1200));
    assert(code.includes('aqlith-logo-dark') && code.includes('aqlith-logo-light'));
    assert(code.includes('http://10.222.35.28:8000'));
    assert(!code.includes('EXPO_PUBLIC_ACCESS_TOKEN'));
    result = { result: 'passed', mode, bundleHttp: bundle.status, bytes: Buffer.byteLength(code), bothOfficialLogos: true, publicTokenVariable: false, LAN: true };
  }
  fs.writeFileSync(path.join(output, `expo-${mode}.json`), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
