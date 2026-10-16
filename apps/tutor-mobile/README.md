# AQLITH Learn Mobile

The first student-facing shell for secondary learners. It is Arabic-first,
mobile-first, and consumes the versioned Tutor API through `src/api/client.ts`.

## Local run

```bash
npm ci
# Set EXPO_PUBLIC_API_URL to a reachable development API, then:
npm run start -- --lan
```

On a physical phone, localhost refers to the phone. Use the computer's LAN IP
for a LAN-accessible development API. Never put tokens or secrets in
`EXPO_PUBLIC_*` variables. Sign in using the login screen.

The shell uses the shared `/auth/login` flow and keeps the access token in
memory for this foundation slice. Secure device storage will be added before
the public beta.

Cairo is bundled locally in `assets/fonts/cairo` with its SIL OFL license.
`src/typography.tsx` maps text weights to static font families for native builds
and Expo web. Keep that license with redistributed fonts. UI preferences use
AsyncStorage; changing language or appearance preserves the current screen.
