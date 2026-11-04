import { createHash, timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function GET(request: NextRequest) {
  const cronSecret = process.env.CRON_SECRET || "";
  const expected = Buffer.from(`Bearer ${cronSecret}`);
  const actual = Buffer.from(request.headers.get("authorization") || "");
  if (cronSecret.length < 32 || expected.length !== actual.length || !timingSafeEqual(expected, actual)) return NextResponse.json({ detail: "Unauthorized." }, { status: 401 });
  const url = process.env.BACKEND_INTERNAL_URL;
  const secret = process.env.INTERNAL_API_SECRET;
  if (!url || !secret) return NextResponse.json({ detail: "Maintenance service is not connected." }, { status: 503 });
  try {
    const identity = createHash("sha256").update("askdocs-maintenance").digest("hex");
    const response = await fetch(new URL("/maintenance/cleanup", url), {
      method: "POST", headers: { "Authorization": `Bearer ${secret}`, "X-Guest-Id": identity, "X-Guest-Address": identity },
      cache: "no-store", signal: AbortSignal.timeout(45_000),
    });
    return NextResponse.json(await response.json(), { status: response.status, headers: { "Cache-Control": "no-store" } });
  } catch { return NextResponse.json({ detail: "Cleanup could not run. Please retry." }, { status: 503 }); }
}
