# Nexora Tutor Web Companion

This workspace is the guardian, content, and authorized administration
experience. It consumes the same `packages/contracts` and Tutor API as the
mobile application. The first implementation slice keeps it read-only until
the guardian relationship and consent APIs are available.

Planned surfaces:

- guardian progress summaries;
- curriculum operations;
- permission-scoped aggregate analytics.

## Local run

```bash
npm install
TUTOR_API_URL=http://localhost:8000 npm run dev
```

The web shell expects an HttpOnly `nexora_access_token` cookie from the shared
identity flow. It never exposes a bearer token through a public client-side
environment variable.
