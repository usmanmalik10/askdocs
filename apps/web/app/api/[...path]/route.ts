import { NextRequest, NextResponse } from "next/server";
import { addressIdentity, allowedPath, boundedBody, GUEST_SECONDS, guestIdentity, sameOrigin } from "@/lib/guest";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 90;
const cookieName = process.env.NODE_ENV === "production" ? "__Host-askdocs_guest" : "askdocs_guest";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const path = (await context.params).path.join("/");
  const write = request.method !== "GET";
  if (write && !sameOrigin(request.headers.get("origin"), request.url)) {
    return NextResponse.json({ detail: "Please make this request from the AskDocs website." }, { status: 403 });
  }
  if (path === "session/reset" && request.method === "POST") {
    const response = NextResponse.json({ reset: true });
    response.cookies.set(cookieName, "", { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict", path: "/", maxAge: 0 });
    response.headers.set("Cache-Control", "private, no-store");
    return response;
  }
  if (!allowedPath(request.method, path)) return NextResponse.json({ detail: "Endpoint not found." }, { status: 404 });
  const backend = process.env.BACKEND_INTERNAL_URL;
  const secret = process.env.INTERNAL_API_SECRET;
  if (!backend || !secret || secret.length < 32) {
    return NextResponse.json({ detail: "The document service is not connected yet. Please try again later." }, { status: 503 });
  }
  const guest = guestIdentity(request.cookies.get(cookieName)?.value);
  const address = process.env.VERCEL ? request.headers.get("x-vercel-forwarded-for") || "unknown" : "local-development";
  try {
    const body = write ? await boundedBody(request) : undefined;
    const result = await fetch(new URL(`/${path}`, backend), {
      method: request.method,
      headers: {
        "Authorization": `Bearer ${secret}`,
        "X-Guest-Id": guest.owner,
        "X-Guest-Address": addressIdentity(address, secret),
        ...(request.headers.get("content-type") ? { "Content-Type": request.headers.get("content-type")! } : {}),
      },
      body: body?.byteLength ? body : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(75_000),
    });
    const data = await result.json();
    const response = NextResponse.json(data, { status: result.status, headers: { "Cache-Control": "private, no-store" } });
    if (guest.fresh) response.cookies.set(cookieName, guest.token, { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict", path: "/", maxAge: GUEST_SECONDS });
    return response;
  } catch (error) {
    const oversized = error instanceof RangeError;
    return NextResponse.json({ detail: oversized ? error.message : "The document service did not respond. Please retry shortly." }, { status: oversized ? 413 : 503, headers: { "Cache-Control": "no-store" } });
  }
}

export { proxy as GET, proxy as POST, proxy as DELETE };
