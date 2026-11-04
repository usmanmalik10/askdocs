import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// UI fixtures verify browser behavior only. Live model verification is a separate release gate.
const doc = { id: "00000000-0000-4000-8000-000000000001", name: "policy.txt", byte_size: 86, chunk_count: 1, created_at: "2026-11-04T12:00:00Z" };
const text = "Employees receive 20 working days of paid annual leave. Requests need manager approval.";
const answer = { id: "00000000-0000-4000-8000-000000000002", question: "How much annual leave?", answer: "Employees receive 20 working days of paid annual leave. [1]", grounded: true, created_at: doc.created_at,
  citations: [{ id: 1, name: doc.name, page: 1, ordinal: 0, quote: text, passage: text }] };

test("upload, question, source inspection, reload, and deletion", async ({ page }, testInfo) => {
  let documents: typeof doc[] = [];
  let answers: typeof answer[] = [];
  await page.route("**/api/**", async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    let data: unknown;
    if (path === "/api/workspace") data = { documents, expires_at: new Date(Date.now() + 86400000).toISOString(), ai_ready: true, provider: "Google Gemini", model: "fixture", limits: { file_bytes: 3145728, documents: 5, questions_per_day: 30 } };
    else if (path === "/api/documents" && request.method() === "POST") { documents = [doc]; data = doc; }
    else if (path.endsWith("/answers")) data = { answers };
    else if (path.endsWith("/ask")) { expect(request.postDataJSON().question).toBe(answer.question); answers = [answer]; data = answer; }
    else if (request.method() === "DELETE") { documents = []; answers = []; data = { deleted: true }; }
    else throw new Error(`Unexpected test request ${request.method()} ${path}`);
    await route.fulfill({ json: data });
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Your next answer/ })).toBeVisible();
  await expect(page.getByText("No account needed")).toBeVisible();
  await expect(page.getByRole("button", { name: /Sign in/i })).toHaveCount(0);
  await page.getByLabel("Document file", { exact: true }).setInputFiles({ name: doc.name, mimeType: "text/plain", buffer: Buffer.from(text) });
  await expect(page.getByRole("button", { name: /Upload and start/ })).toBeDisabled();
  await page.getByRole("checkbox").check();
  await expect(new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze().then(r => r.violations)).resolves.toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("upload.png"), fullPage: true });
  await page.getByRole("button", { name: /Upload and start/ }).click();
  await expect(page.getByRole("heading", { name: doc.name, exact: true })).toBeVisible();
  await page.getByLabel("Ask a question", { exact: true }).fill(answer.question);
  await page.getByRole("button", { name: /Ask your docs/ }).click();
  await expect(page.getByText("Sources checked", { exact: true })).toBeVisible();
  const source = page.getByRole("button", { name: "Open source 1, policy.txt, page 1", exact: true });
  await source.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("dialog").getByRole("blockquote")).toHaveText(text);
  await expect(new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze().then(r => r.violations)).resolves.toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("source.png"), fullPage: true });
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(source).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.reload();
  await expect(page.getByText("Sources checked", { exact: true })).toBeVisible();
  page.once("dialog", dialog => void dialog.accept());
  await page.getByRole("button", { name: "Delete document", exact: true }).click();
  await expect(page.getByRole("heading", { name: /Your next answer/ })).toBeVisible();
});

test("service errors are clear and writes require a matching origin", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.getByRole("main").getByRole("alert")).toContainText(/service/);
  expect((await request.post("/api/documents", { headers: { Origin: "https://unrelated.example" }, data: "invalid" })).status()).toBe(403);
  expect((await request.get("/api/health")).status()).toBe(404);
  expect((await request.get("/api/maintenance/cleanup")).status()).toBe(401);
});

test("expired guest can reset without a login", async ({ page }) => {
  let reset = false;
  await page.route("**/api/**", async route => {
    if (route.request().url().endsWith("/session/reset")) { reset = true; await route.fulfill({ json: { reset: true } }); }
    else if (!reset) await route.fulfill({ status: 410, json: { detail: "This guest workspace has expired." } });
    else await route.fulfill({ json: { documents: [], expires_at: new Date(Date.now() + 86400000).toISOString(), ai_ready: true, limits: { documents: 5, questions_per_day: 30 } } });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Start a fresh workspace" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Choose a document", exact: true })).toBeEnabled();
  expect(reset).toBe(true);
});
