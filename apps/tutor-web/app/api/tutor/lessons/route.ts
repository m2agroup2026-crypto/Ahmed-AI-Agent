import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.TUTOR_API_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const token = request.cookies.get("nexora_access_token")?.value;
  if (!token) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  const response = await fetch(`${API_URL}/api/v1/tutor/lessons`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const body = await response.text();
  return new NextResponse(body, {
    status: response.status,
    headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/json" },
  });
}
