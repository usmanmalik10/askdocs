import assert from "node:assert/strict";
import test from "node:test";
import { addressIdentity, allowedPath, boundedBody, guestIdentity, MAX_REQUEST_BYTES, sameOrigin } from "../apps/web/lib/guest.ts";

test("guest tokens are unpredictable, validated, and hashed before forwarding", () => {
  const first = guestIdentity();
  const second = guestIdentity();
  assert.notEqual(first.token, second.token);
  assert.notEqual(first.owner, first.token);
  assert.equal(guestIdentity(first.token).owner, first.owner);
  assert.equal(guestIdentity(first.token).fresh, false);
  assert.equal(guestIdentity("attacker-controlled").fresh, true);
  assert.notEqual(addressIdentity("same-ip", "key1"), addressIdentity("same-ip", "key2"));
});

test("write origin must match the application exactly", () => {
  assert.equal(sameOrigin(null, "https://askdocs.example/api/documents"), false);
  assert.equal(sameOrigin("https://evil.example", "https://askdocs.example/api/documents"), false);
  assert.equal(sameOrigin("https://askdocs.example", "https://askdocs.example/api/documents"), true);
});

test("proxy only exposes the documented guest endpoints", () => {
  assert.equal(allowedPath("GET", "workspace"), true);
  assert.equal(allowedPath("POST", "health"), false);
  assert.equal(allowedPath("GET", "../health"), false);
  assert.equal(allowedPath("DELETE", "documents/00000000-0000-0000-0000-000000000001"), true);
  assert.equal(allowedPath("GET", "documents/00000000-0000-0000-0000-000000000001"), false);
});

test("body cap counts streamed bytes even without Content-Length", async () => {
  const stream = new ReadableStream({ start(c) { c.enqueue(new Uint8Array(MAX_REQUEST_BYTES)); c.enqueue(new Uint8Array(1)); c.close(); } });
  await assert.rejects(boundedBody(new Request("http://localhost", { method: "POST", body: stream, duplex: "half" })), RangeError);
  assert.equal((await boundedBody(new Request("http://localhost", { method: "POST", body: "hello" }))).byteLength, 5);
});
