# AskDocs

**Your documents. Clear answers.**

AskDocs is an open-source document assistant. Upload a text-based PDF, UTF-8 text file, or Markdown note, ask a question, and inspect the passages cited in the answer. No sign-in or registration is required.

## Release status

The guest MVP is live at **[askdocs-self.vercel.app](https://askdocs-self.vercel.app)**. The real production upload-to-answer flow, citations, history, guest isolation, deletion, and cleanup authorization have been verified. The implementation is delivered through [PR #4](https://github.com/usmanmalik10/askdocs/pull/4) in twenty feature commits.

CI checks Python/PostgreSQL behavior, guest-boundary unit tests, desktop/mobile browser scenarios, lint, TypeScript, and the production build. See the [release record](docs/release-verification.md) for dated test evidence, scope, and remaining limits.

## What you can do

- Upload PDF, TXT, and Markdown files up to 3 MB, 50 PDF pages, and 100,000 extracted characters.
- Ask questions about one selected document and revisit its most recent 30 saved answers.
- Open cited quotes and full extracted passages, with original PDF page numbers.
- Delete a document and its saved answers, or erase the entire guest workspace.
- Work in a temporary browser workspace that expires after 24 hours.

Use public or non-sensitive documents. Google Gemini processes text and questions; its free tier may use submitted content to improve Google products. AskDocs checks that quoted citations exist in retrieved passages. This does not independently prove every generated claim. Read the [data-handling notice](docs/engineering-handbook.md#data-handling).

## Architecture

Next.js provides the responsive interface and same-origin guest API boundary. A private Python FastAPI service handles extraction, semantic retrieval, answer generation, and PostgreSQL/pgvector persistence. Vercel Services deploys both runtimes together; this Vercel feature is currently Beta.

The Python service has no public route. Unpredictable HttpOnly cookies identify guests, while every database operation is scoped to a hashed guest identity. Database-backed atomic budgets cap public usage without a Redis dependency. Original uploaded files are not retained.

## Run and contribute

Use Node.js 22.23.4, pnpm 9.15.0, Python 3.13.2, and uv 0.13.5. Start with the [development setup](docs/development/setup.md), then read the [engineering handbook](docs/engineering-handbook.md) for contracts, security boundaries, operations, and limitations.

```bash
pnpm install --frozen-lockfile
uv sync --project apps/backend --frozen
pnpm lint
pnpm typecheck
pnpm test:unit
pnpm test:api
pnpm build
pnpm exec playwright install chromium
pnpm test:browser
```

The database integration tests need a separate local test database. CI creates one automatically. See setup instructions before running them; tests refuse production databases.

## Scope and roadmap

This release delivers the guest document-question-answer journey. The earlier enterprise roadmap—including accounts, team administration, sharing, billing, background ingestion, and commercial operations—remains future work. Existing design prototypes are references, not evidence that those features are implemented.

Report reproducible bugs through [GitHub Issues](https://github.com/usmanmalik10/askdocs/issues). Never include real documents, API keys, cookies, or database credentials in an issue or PR.

## License

Copyright 2026 Usman Malik. Licensed under the [Apache License, Version 2.0](LICENSE). Dependencies retain their licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).
