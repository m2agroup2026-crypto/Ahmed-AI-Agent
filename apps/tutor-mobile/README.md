# Nexora Tutor Mobile

The first student-facing shell for secondary learners. It is Arabic-first,
mobile-first, and consumes the versioned Tutor API through `src/api/client.ts`.

## Local run

```bash
npm install
EXPO_PUBLIC_API_URL=http://localhost:8000 EXPO_PUBLIC_ACCESS_TOKEN=<token> npm run start
```

The shell uses the shared `/auth/login` flow and keeps the access token in
memory for this foundation slice. Secure device storage will be added before
the public beta.
