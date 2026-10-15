import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.TUTOR_API_URL ?? "http://localhost:8000";
const COOKIE = "nexora_access_token";
const routes: Record<string, RegExp[]> = {
  GET: [/^me$/, /^classes$/, /^classes\/[\w-]+\/(assignments|students|results|live)$/, /^progress$/, /^books$/, /^live\/capabilities$/, /^live\/[\w-]+$/, /^live\/[\w-]+\/(participants|audit|recording\/playback)$/],
  POST: [/^classes$/, /^join$/, /^classes\/[\w-]+\/(invite|assignments|live)$/, /^assignments\/[\w-]+\/start$/, /^attempts\/[\w-]+\/submit$/, /^books$/, /^live\/[\w-]+\/(start|join|end|leave|heartbeat|consent|hand|recording\/start|recording\/stop)$/, /^live\/[\w-]+\/participants\/\d+\/(audio|revoke)$/],
  PATCH: [/^classes\/[\w-]+$/],
  PUT: [/^teacher-profile$/],
  DELETE: [/^classes\/[\w-]+\/students\/\d+$/],
};

async function handle(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const resource = path.join("/");
  const method = request.method;
  if (method !== "GET" && request.headers.get("origin") !== request.nextUrl.origin) {
    return NextResponse.json({ detail: "Invalid request origin" }, { status: 403 });
  }
  const session = resource === "session";
  if (session && method === "DELETE") {
    const response = NextResponse.json({ signed_out: true });
    response.cookies.set(COOKIE, "", { httpOnly: true, sameSite: "strict", path: "/", maxAge: 0, secure: process.env.NODE_ENV === "production" });
    return response;
  }
  if (!(session && method === "POST") && !routes[method]?.some((rule) => rule.test(resource))) {
    return NextResponse.json({ detail: "Route not found" }, { status: 404 });
  }
  const token = request.cookies.get(COOKIE)?.value;
  if (!session && !token) return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  const body = method === "GET" || method === "DELETE" ? undefined : await request.text();
  if (body && body.length > 100000) return NextResponse.json({ detail: "Request too large" }, { status: 413 });
  try {
    const upstream = await fetch(`${API_URL}${session ? "/auth/login" : `/api/v1/classroom/${resource}`}`, {
      method, body, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(10000),
      headers: { "Content-Type": "application/json", ...(!session ? { Authorization: `Bearer ${token}` } : {}) },
    });
    if (method === "GET" && /^live\/[\w-]+\/recording\/playback$/.test(resource) && upstream.ok) {
      return new NextResponse(upstream.body, { status: upstream.status, headers: {
        "Content-Type": "video/mp4", "Cache-Control": "private, no-store",
        "Content-Disposition": "inline", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
      } });
    }
    const data = await upstream.json();
    if (session && upstream.ok) {
      if (typeof data.access_token !== "string") throw new Error("Invalid session response");
      const response = NextResponse.json({ signed_in: true }, { headers: { "Cache-Control": "no-store" } });
      response.cookies.set(COOKIE, data.access_token, {
        httpOnly: true, sameSite: "strict", secure: process.env.NODE_ENV === "production", path: "/", maxAge: 3600,
      });
      return response;
    }
    return NextResponse.json(data, { status: upstream.status, headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ detail: "Classroom service unavailable" }, { status: 502 });
  }
}

export { handle as GET, handle as POST, handle as PATCH, handle as PUT, handle as DELETE };
