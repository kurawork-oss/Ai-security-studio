import { NextRequest, NextResponse } from "next/server";

// BFF proxy to the management API. Forwards the caller's Supabase bearer token
// (sent by the browser), falling back to SECUREAI_DEV_JWT for local dev.
const API_BASE = process.env.SECUREAI_API_BASE_URL;

async function forward(req: NextRequest, path: string[]) {
  if (!API_BASE) {
    return NextResponse.json(
      { error: { code: "CONFIG", message: "SECUREAI_API_BASE_URL not set" } },
      { status: 500 },
    );
  }
  const token =
    req.headers.get("authorization")?.replace(/^Bearer\s+/i, "") ??
    process.env.SECUREAI_DEV_JWT ??
    "";
  if (!token) {
    return NextResponse.json(
      { error: { code: "UNAUTHENTICATED", message: "Sign in required" } },
      { status: 401 },
    );
  }

  const search = req.nextUrl.search;
  const url = `${API_BASE}/v1/${path.join("/")}${search}`;
  const init: RequestInit = {
    method: req.method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    cache: "no-store",
  };
  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = await req.text();
  }
  const upstream = await fetch(url, init);
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
}

type Ctx = { params: { path: string[] } };

export async function GET(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function POST(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function PUT(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function DELETE(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
