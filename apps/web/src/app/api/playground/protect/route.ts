import { NextRequest, NextResponse } from "next/server";

// BFF: the Protect API key stays server-side and is never sent to the browser.
export async function POST(req: NextRequest) {
  const base = process.env.SECUREAI_API_BASE_URL;
  const key = process.env.SECUREAI_PROTECT_KEY;
  if (!base || !key) {
    return NextResponse.json(
      { error: { code: "CONFIG", message: "SECUREAI_API_BASE_URL / SECUREAI_PROTECT_KEY not set" } },
      { status: 500 },
    );
  }

  let payload: { text?: string; rules?: Record<string, boolean> };
  try {
    payload = await req.json();
  } catch {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" } },
      { status: 400 },
    );
  }

  const upstream = await fetch(`${base}/v1/protect`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      text: payload.text ?? "",
      options: { returnEntities: true, rules: payload.rules ?? null },
    }),
    cache: "no-store",
  });

  const data = await upstream.json();
  return NextResponse.json(data, { status: upstream.status });
}
