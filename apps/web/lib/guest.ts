import { createHash, createHmac, randomBytes } from "node:crypto";

export const GUEST_SECONDS = 24 * 60 * 60;
export const MAX_REQUEST_BYTES = 3 * 1024 * 1024 + 64 * 1024;

export function guestIdentity(cookie?: string) {
  const existing = Boolean(cookie && /^[a-f0-9]{64}$/.test(cookie));
  const token = existing ? cookie! : randomBytes(32).toString("hex");
  return { token, owner: createHash("sha256").update(token).digest("hex"), fresh: !existing };
}

export function addressIdentity(address: string, secret: string) {
  return createHmac("sha256", secret).update(address).digest("hex");
}

export function sameOrigin(origin: string | null, url: string) {
  if (!origin) return false;
  try { return new URL(origin).origin === new URL(url).origin; } catch { return false; }
}

export function allowedPath(method: string, path: string) {
  if (path === "workspace") return method === "GET" || method === "DELETE";
  if (path === "documents") return method === "POST";
  const id = "[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}";
  if (new RegExp(`^documents/${id}$`).test(path)) return method === "DELETE";
  if (new RegExp(`^documents/${id}/answers$`).test(path)) return method === "GET";
  if (new RegExp(`^documents/${id}/ask$`).test(path)) return method === "POST";
  return false;
}

export async function boundedBody(request: Request): Promise<ArrayBuffer> {
  const declared = Number(request.headers.get("content-length"));
  if (declared > MAX_REQUEST_BYTES) throw new RangeError("File exceeds the 3 MB upload limit.");
  const reader = request.body?.getReader();
  if (!reader) return new ArrayBuffer(0);
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_REQUEST_BYTES) throw new RangeError("File exceeds the 3 MB upload limit.");
      chunks.push(value);
    }
  } catch (error) {
    await reader.cancel().catch(() => {});
    throw error;
  } finally { reader.releaseLock(); }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
  return body.buffer;
}
