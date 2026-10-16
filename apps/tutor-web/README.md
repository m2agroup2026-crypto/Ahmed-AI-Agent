# AQLITH Learn Web Companion

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

Classroom requests accept only explicit authorities. Development defaults to
`http://localhost:3000` and `http://127.0.0.1:3000`. For a private LAN preview,
set `AQLITH_DEV_HOSTS` to the computer's exact private IP before starting Next.js.
Production must configure `CLASSROOM_TRUSTED_ORIGINS` as comma-separated exact
public origins (for example `https://learn.example.com`). No wildcard is accepted.
Forwarded headers never extend this allowlist. Mutations require an exact Origin.

Cairo is self-hosted from `app/fonts/cairo`; the accompanying OFL license must
be retained. Arabic UI defaults to RTL; UI preferences never translate curriculum.
