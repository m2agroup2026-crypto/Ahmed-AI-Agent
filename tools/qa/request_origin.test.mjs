import assert from 'node:assert/strict';
import test from 'node:test';
import { trustedOrigins, validRequestOrigin } from '../../apps/tutor-web/lib/request-origin.ts';
const allowed = trustedOrigins({ NODE_ENV: 'development', AQLITH_DEV_HOSTS: '10.222.35.28' });
test('local and explicitly configured LAN authorities allow exact-origin mutations', () => {
  for (const origin of allowed) assert(validRequestOrigin(new URL(origin).host, origin, 'POST', allowed));
});
test('missing, null, foreign, duplicate, forwarded and malformed origins fail closed', () => {
  for (const origin of [null, 'null', 'https://evil.example', 'http://localhost:3000, http://evil.example', 'http://localhost:3000/', 'https://localhost:3000']) {
    assert.equal(validRequestOrigin('localhost:3000', origin, 'POST', allowed), false);
  }
});
test('spoofed matching Host and Origin, missing Host and unexpected dev authorities fail', () => {
  for (const host of ['evil.example:3000', '0.0.0.0:3000', 'localhost.evil.example:3000', 'localhost:3001', null]) {
    assert.equal(validRequestOrigin(host, `http://${host}`, 'POST', allowed), false);
    assert.equal(validRequestOrigin(host, null, 'GET', allowed), false);
  }
});
test('production has no implicit development authorities; malformed config is ignored', () => {
  assert.deepEqual(trustedOrigins({ NODE_ENV: 'production', AQLITH_DEV_HOSTS: '10.222.35.28' }), []);
  assert.deepEqual(trustedOrigins({ NODE_ENV: 'production', CLASSROOM_TRUSTED_ORIGINS: 'https://learn.example,https://user:pass@evil.example,https://evil.example/path,*' }), ['https://learn.example']);
  assert(validRequestOrigin('learn.example', 'https://learn.example', 'DELETE', ['https://learn.example']));
  assert(validRequestOrigin('localhost:3000', null, 'GET', allowed));
});
