// Populate Expo's ordinary SDK schema cache using its public unauthenticated API.
// No node_modules patches, schema substitutions, credentials, or cache deletion.
process.env.EXPO_OFFLINE = '0';
const { createCachedFetch } = require('../../apps/tutor-mobile/node_modules/expo/node_modules/@expo/cli/build/src/api/rest/client.js');
const read = createCachedFetch({ cacheDirectory: 'schema-cache', ttl: 604800000,
  fetch: (resource, options) => {
    if (resource !== 'project/configuration/schema/54.0.0') throw new Error('Unexpected schema resource');
    return fetch('https://api.expo.dev/v2/' + resource, { ...options, headers: { Accept: 'application/json' },
      redirect: 'error', signal: AbortSignal.timeout(20000) });
  },
});
read('project/configuration/schema/54.0.0').then(async response => {
  if (!response.ok) throw new Error('Schema HTTP ' + response.status);
  const body = await response.json();
  if (!body.data?.schema) throw new Error('Missing official SDK schema');
  console.log('Official SDK 54 schema cached; no authentication supplied. Offline manifest assets can now resolve.');
}).catch(error => { console.error(error.message); process.exitCode = 1; });
