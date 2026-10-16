// Trust only configured public authorities, never forwarded request headers.
export function trustedOrigins(environment: Record<string, string | undefined>): string[] {
  const configured = (environment.CLASSROOM_TRUSTED_ORIGINS ?? "").split(",").map(value => value.trim());
  const local = environment.NODE_ENV === "production" ? [] : [
    "http://localhost:3000", "http://127.0.0.1:3000",
    ...(environment.AQLITH_DEV_HOSTS ?? "").split(",").map(value => value.trim())
      .filter(value => /^[a-zA-Z0-9.-]+$/.test(value)).map(host => `http://${host}:3000`),
  ];
  return [...new Set([...configured, ...local].filter(value => {
    try {
      const url = new URL(value);
      return ["http:", "https:"].includes(url.protocol) && url.origin === value && !url.username && !url.password;
    } catch { return false; }
  }))];
}

export function validRequestOrigin(host: string | null, origin: string | null, method: string, allowed: readonly string[]): boolean {
  if (!host || host !== host.trim()) return false;
  const candidates = allowed.filter(value => new URL(value).host === host.toLowerCase());
  if (!candidates.length) return false;
  // Read-only navigation may omit Origin. Every mutation must supply an exact origin.
  return method === "GET" || (origin !== null && candidates.includes(origin));
}
