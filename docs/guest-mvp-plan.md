# AskDocs guest document assistant

## Release contract

Visitors can upload a PDF or UTF-8 text/Markdown document, ask questions, inspect the passages behind an answer, and delete their data. No account, login, team administration, or billing is part of this release. The existing enterprise roadmap is not a claim that those features are implemented.

The application must use real retrieval and a connected language model. Missing credentials or exhausted quotas produce an actionable error, never a simulated successful answer.

## Architecture

- Next.js provides the responsive interface and same-origin API boundary.
- A private Python FastAPI service extracts text, chunks it, retrieves evidence, calls the model, and persists document and conversation records.
- Managed PostgreSQL stores extracted passages and conversation history. Original uploaded files are processed temporarily and are not retained.
- Vercel Services deploys the two runtimes together. Services is currently Beta. Only the Next.js service has public ingress; Python also requires an internal service secret.
- An unpredictable HttpOnly guest cookie identifies a browser. Only its hash reaches storage. Every data operation is scoped to that hash and a fixed 24-hour expiry. Another browser cannot recover a guest workspace.
- Database-backed atomic quotas cap uploads and questions per guest, IP, and deployment. Redis is unnecessary for this bounded release unless measured demand justifies a second service.

Service provisioning is restricted to free plans. Provider connections, usable model quotas, and deployment access must be verified before declaring the product complete. No credentials belong in Git or chat.

## Twenty commits, one branch, one PR

Branch: `feat/guest-rag-mvp`. Base: `8b10aa7f3eb7971cb0d3e44098543f54190b94da`.

1. Record release scope, architecture, and completion criteria.
2. Establish the Next.js application and reproducible dependencies.
3. Implement the accessible responsive guest workspace shell.
4. Add the guest identity and protected same-origin API boundary.
5. Add PostgreSQL migrations and owner-scoped persistence.
6. Define the Python service contract and upload boundaries.
7. Extract bounded PDF and text content with page provenance.
8. Chunk documents and build semantic representations.
9. Retrieve owner-scoped evidence for a question.
10. Generate grounded answers and validate citation references.
11. Persist and recover guest conversation history.
12. Connect the upload and question interface to real endpoints.
13. Add accessible source inspection and citation navigation.
14. Complete document deletion and recoverable error flows.
15. Enforce anonymous quotas, expiry, and privacy choices.
16. Verify API behavior, isolation, and failure paths.
17. Verify browser behavior and responsive accessibility.
18. Configure repeatable CI and the Vercel deployment.
19. Address review findings and publish operating documentation.
20. Record live verification and complete final release corrections.

Commit boundaries may shift to keep each change coherent; the final branch must contain exactly twenty meaningful commits and one PR. Reserve the last commits for review and actual deployment findings.

## Definition of done

- Clean dependency installation, lint, TypeScript checks, Python tests, production build, and browser tests pass.
- A real deployed browser uploads a fixture, asks a question, gets an answer supported by the fixture, and opens a matching cited passage.
- Unsupported, corrupt, image-only, empty, and oversized files fail clearly.
- Two independent guest browsers cannot read, ask about, or delete one another's records.
- Deletion removes derived passages and associated answers; expiry denies access and scheduled cleanup removes expired records.
- Provider failures and quota exhaustion are visible and do not create fabricated answers.
- Mobile layout, keyboard operation, visible focus, input contrast, and status announcements are checked.
- GitHub CI and deployment results, the PR, the final URL, setup instructions, data handling, limits, and remaining gaps are documented honestly.

## Deliberate limits

PDF text extraction is not OCR. Audio, images, office files, account recovery, sharing, enterprise permissions, and commercial billing are out of scope. Generated claims can still be wrong; visitors must inspect sources. Free-tier capacity is bounded and is not a production availability guarantee.
