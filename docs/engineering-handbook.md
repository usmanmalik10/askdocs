# AskDocs engineering handbook

## Product contract

AskDocs answers questions about a visitor’s selected document, with inspectable citations and no account requirement. This release is a bounded public demonstration of the guest workflow. It is not the earlier enterprise product with authentication, organization administration, sharing, billing, or durable background ingestion.

The user journey is browser upload → same-origin Next.js API → private Python extraction and retrieval → PostgreSQL and Gemini → validated answer and sources → browser. A successful build or an attractive screen is insufficient evidence that this complete journey works.

## Services and trust boundaries

The browser never receives database credentials, model keys, or the internal service secret. Next.js validates mutation origins, limits request bytes, manages the guest cookie, and forwards only documented guest endpoints. Client-supplied owner and authorization headers are not forwarded.

The private Python service authenticates its caller independently of Vercel’s network binding. It accepts a hashed guest identity and keyed network-address hash from Next.js. All document reads, searches, writes, history, and deletion enforce ownership. A missing or foreign document returns the same not-found response.

Vercel Services deploys the Next.js and FastAPI runtimes atomically. Only Next.js is exposed by public ingress. The Python service is reached through a deployment-aware binding and has no public rewrite. Services is currently Beta; verify its current limits and behavior before expanding this release.

## Guest lifecycle

A fresh browser receives 32 random bytes encoded as a cookie token. The cookie is HttpOnly, SameSite Strict, scoped to the root path, and Secure in production. Production uses the host-prefixed cookie name. PostgreSQL stores a SHA-256 hash, not the raw token.

The database records a fixed 24-hour expiration. Reads use the current wall clock rather than the transaction start time. Long-running provider calls re-check expiry before persisting their result. Cookie clearing, changing browsers, or expiration loses access; there is no recovery identity.

Creating new workspaces also has a shared daily budget. Guest mutations take a database advisory lock; competing operations return a retryable conflict rather than racing uploads, questions, and deletion. Database connections are opened for each operation and closed by context managers, avoiding stale in-process connection state after a serverless freeze or outage.

## Ingestion

Accepted inputs are text-based PDFs, UTF-8 text, and Markdown. The request boundary counts actual streamed bytes, even when Content-Length is absent or incorrect. Python checks the real uploaded size again. Extension and PDF signature checks are independent of browser-provided MIME types.

Limits are 3 MB per file, 50 PDF pages, 100,000 extracted characters, five retained documents per guest, and 120 passages per document. Encrypted, corrupt, empty, binary, oversized, and image-only documents fail clearly. A compressed PDF stream has an 8 MB decompression cap. File size and parser limits reduce risk but do not turn PDF parsing into an unrestricted document service.

Passages are at most 1,400 characters, overlap by up to 150 characters, and preserve the original PDF page number. Blank pages do not renumber subsequent citations. Text files use page 1. No OCR, image reasoning, office-file parsing, or external-URL fetching occurs.

Original files are processed temporarily and discarded. Only metadata, extracted passages, embeddings, and answers are persisted. Uploads are synchronous and atomic: failed extraction or embeddings do not leave a partially searchable document.

## Retrieval and answers

The embedding model is `gemini-embedding-001`, with 768 dimensions normalized to unit length. Empty, incomplete, non-finite, or incorrect-dimension embeddings are rejected. Changing the embedding model or dimension requires a deliberate re-embedding migration; it is not a runtime setting.

Retrieval embeds the question and performs exact cosine-distance search over at most 120 passages from the selected, owned, unexpired document. The six nearest passages form the evidence context. No cross-document or cross-guest search occurs. At this size, an approximate vector index adds complexity without an established benefit.

The generation model defaults to `gemini-3.5-flash-lite` and can be changed through the server-side model setting after checking availability, free-tier eligibility, and output compatibility. The prompt treats document text and questions as untrusted data, disables external tools by omission, and requests structured output.

Before returning an answer, the service validates numeric citation references and verifies every quoted excerpt against a retrieved passage after whitespace normalization. Every answer paragraph must contain a citation. Unknown references, fabricated quotes, duplicate citations, unreadable JSON, and incomplete responses fail rather than being displayed as successful answers. An unsupported question produces a fixed abstention message without unverified model claims.

Each provider request retries one temporary transport or server failure after a short delay. Quota and credential failures are not retried. The full AI operation has a 65-second deadline; timeout cancels it and rolls back unfinished document or answer writes. This keeps retry behavior within the website’s request window and does not introduce another model or paid fallback.

Citation validation checks provenance, not semantic entailment. A real quote can still be interpreted incorrectly. Users must inspect sources, and evaluation must include irrelevant questions and documents containing hostile instructions. Questions are retrieved independently; the most recent 30 saved answers are displayed, but there is no hidden conversation rewrite or model memory.

## Public budgets

Counters are atomic database upserts committed before expensive external work. Failed attempts consume the budget deliberately. The three reservations commit together or roll back together. Limits reset on the database’s UTC date and are separate from provider quotas.

| Operation | Guest per day | Network address per day | Whole site per day |
| --- | ---: | ---: | ---: |
| New workspace attempts | 5 | 30 | 500 |
| Upload attempts | 5 | 10 | 20 |
| Question attempts | 30 | 60 | 100 |

Network identity is a keyed hash of Vercel’s forwarded client-address header. Local development uses a shared local identity. These limits provide a bounded free demonstration; they are not a complete defense against distributed denial of service. Upstream platform limits also apply. There is no automatic paid fallback, external search tool, Redis service, or unlimited model endpoint.

## API contract

The browser talks only to these same-origin routes:

```http
GET    /api/workspace
POST   /api/documents                 multipart: file, consent=true
POST   /api/documents/{uuid}/ask      JSON: question
GET    /api/documents/{uuid}/answers
DELETE /api/documents/{uuid}
DELETE /api/workspace
POST   /api/session/reset
```

Workspace responses include owned document metadata, expiration, AI configuration readiness, and user-facing limits. Upload responses contain the persisted document metadata. Question and history responses contain the question, answer, validated citations, grounding flag, and timestamps. A citation includes its displayed ID, original page, passage ordinal, document name, checked quote, and full extracted passage.

Mutations require a matching Origin header. Question text is trimmed and limited to 3–1,200 characters. UUIDs are validated by the backend. Responses containing guest data are private and non-cacheable. Errors distinguish invalid input, missing data, expiry, conflict, quota exhaustion, provider failure, and unavailable storage without returning credentials or raw provider responses.

The protected maintenance route is separate from the browser proxy:

```http
GET /api/maintenance/cleanup
Authorization: Bearer <CRON_SECRET>
```

It calls the private cleanup endpoint using the service secret. Unknown browser proxy paths, including private health and maintenance endpoints, are rejected.

## Data handling

Use public or non-sensitive material. Document passages go to Google for embeddings. Questions and retrieved passages go to Google for generation. Gemini’s free tier may use this content to improve its products. Upload consent and the in-app privacy page explain this before processing.

Workspace access ends after 24 hours. Daily cleanup removes expired guest rows and cascades through documents, passages, and answers. Physical removal can therefore lag expiration by up to the cleanup interval; a failed cleanup requires operator intervention. Old usage counters are removed after their date is more than two days old. Infrastructure backups and provider retention remain subject to their own policies.

Deleting a document cascades through its passages and saved answers. Erasing the workspace removes all guest data and clears the cookie. It cannot retract text already processed by an AI provider. The implementation does not deliberately log source text, questions, raw guest cookies, or credentials; platform request and error logs still exist.

## Deployment and operations

Provision only the approved free Neon plan. Keep database, Gemini, internal service, and cleanup secrets in Vercel’s server-side environment settings for the intended environments. Do not override the generated backend service binding in Vercel. Enable Corepack so builds honor the repository’s exact pnpm version; Vercel’s bundled patch version otherwise fails the strict engine check.

The deployment source excludes local credentials, Git configuration, dependency caches, old discarded application folders, and test artifacts. Inspect source selection before deploying a local working tree. CI uses immutable GitHub Action release commits, frozen JavaScript/Python lockfiles, isolated PostgreSQL, real SQL integration tests, and browser accessibility checks.

Apply migrations explicitly to the verified intended database before enabling uploads. The migration runner takes a transaction-level migration lock and records applied versions. Do not roll back schema changes blindly. For destructive future migrations, prepare an additive compatibility phase and a tested data backup first.

Deploy an explicit preview, verify the complete flow, and then deploy or promote the intended production revision. Verify the account, project, source commit, and environment before every release. A first CLI deployment may otherwise default to production. Keep the PR draft until the release gates pass.

Daily cleanup is scheduled at 03:00 UTC. Check its result and expired-row counts after deployment and after credential changes. Investigate a failed cleanup promptly. Missing maintenance authorization must return unauthorized, never run the deletion job publicly.

For an outage: check whether the failure is at Next.js, the private binding, PostgreSQL, embeddings, or generation. Verify key names and resource status without logging values. Retry a harmless read before a write. A database connection or model outage must not produce a fabricated answer or partially indexed document.

## Testing strategy

Unit tests cover guest identity, origin enforcement, proxy endpoint allowlisting, streamed size caps, extraction, page provenance, chunking, embeddings, citation validation, provider failures, and the Windows event loop. Real PostgreSQL tests cover ownership, retrieval and history, cascade deletion, expiry, cleanup, atomic concurrent budgets, new-session limits, consent, failed ingestion, and recovery after model failure.

Desktop and mobile browser tests cover upload consent, questions, source inspection, Escape and focus restoration, history reload, deletion, expiry recovery, service errors, and API boundary rejection. Accessibility scans check the upload flow and source dialog. These automated tests use explicit model/UI test doubles and cannot establish real model quality or cloud wiring.

The release gate additionally requires an actual deployed browser to upload the public fixture, ask a question, inspect a matching citation, test an irrelevant question, verify an independent guest cannot access the first guest’s data, and delete the fixture. Record the exact source revision, environment, CI run, deployment, and observed result in the release record.

## Scope left for later

OCR, large asynchronous uploads, cross-document questions, contextual query rewriting, sharing, user accounts, teams, feedback analysis, billing, commercial availability guarantees, and enterprise compliance are separate future work. Do not mark those older roadmap tickets complete because this guest release works.

## Primary references

- [Vercel Services configuration](https://vercel.com/docs/services/config-reference)
- [Vercel package managers](https://vercel.com/docs/package-managers)
- [Vercel request headers](https://vercel.com/docs/headers/request-headers)
- [Gemini embeddings](https://aistudio.google.com/docs/embeddings)
- [Gemini API keys](https://aistudio.google.com/docs/api-key)
- [Gemini API pricing and data-use terms](https://aistudio.google.com/docs/pricing)
- [Neon free-plan limits](https://neon.com/pricing)
