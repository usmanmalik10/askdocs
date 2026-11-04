# Development setup

## Prerequisites

- Node.js 22.23.4; compatible Node 22 security patches are allowed by the engine range.
- pnpm 9.15.0, recorded in the root package-manager field.
- Python 3.13.2 and uv 0.13.5.
- PostgreSQL with the vector extension, plus a usable Gemini API free-tier key.
- Docker Desktop only if you want the isolated local database tests.

Run all root commands from the repository root. Windows instructions below use PowerShell. In Command Prompt, use `cd /d D:\askdocs\askdocs`; in Git Bash use `cd /d/askdocs/askdocs`.

```powershell
Set-Location D:\askdocs\askdocs
pnpm install --frozen-lockfile
uv sync --project apps/backend --frozen
```

## Connect configuration

Use your own development database and AI key when self-hosting. Maintainers with access to the AskDocs Vercel project can pull its development configuration after checking the account and project:

```powershell
pnpm dlx vercel@65.11.0 whoami
pnpm dlx vercel@65.11.0 project inspect askdocs --scope usman-malik --non-interactive
pnpm dlx vercel@65.11.0 env pull .env.local --yes --scope usman-malik
```

For a separate installation, copy the environment example to a new local file and supply your own values. Preserve existing environment files until you have checked which project they belong to. The discarded application’s root `.env` is not used by this implementation.

Required values are the PostgreSQL connection URL, Gemini API key, internal-service secret, cleanup secret, and local backend URL. Both secrets must be independently generated random strings of at least 32 characters. The local backend URL is shown here; Vercel supplies its own service binding automatically in deployed functions.

```dotenv
DATABASE_URL=your-development-postgresql-url
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash-lite
INTERNAL_API_SECRET=your-random-internal-secret
CRON_SECRET=your-independent-random-cleanup-secret
BACKEND_INTERNAL_URL=http://127.0.0.1:8000
```

Do not put a secret in a variable starting with `NEXT_PUBLIC_`. The student Gemini app subscription does not configure the API key or its project’s quota. Use a project marked Free and leave paid billing disabled for this installation.

## Apply migrations and start Python

Verify the intended database and required key names first. Migrations are explicit, versioned, idempotent, and run under a database migration lock. The application does not modify the schema during a request.

```powershell
Set-Location D:\askdocs\askdocs\apps\backend
uv run --env-file ../../.env.local python migrate.py
uv run --env-file ../../.env.local python serve.py
```

Keep that terminal open. The Python service listens on the loopback address at port 8000. Its endpoints require the internal service secret; opening them directly in a browser should fail authorization. The local entry point selects the socket-compatible event loop required by PostgreSQL on Windows. Restart it after changing Python code.

## Start the website

In a second PowerShell terminal:

```powershell
Set-Location D:\askdocs\askdocs
pnpm dev
```

Visit [localhost:3000](http://localhost:3000). The website loads the ignored root `.env.local`; it calls Python through its own API routes. No login screen should appear. There is no need to start Keycloak, Redis, or the discarded application’s containers.

## Run checks

```powershell
pnpm lint
pnpm typecheck
pnpm test:unit
uv run --project apps/backend ruff check apps/backend
pnpm test:api
pnpm build
pnpm exec playwright install chromium
pnpm test:browser
```

Browser tests start a production server on port 3100 and explicitly use test-only backend configuration. They mock UI responses to test interaction and accessibility. Python database tests exercise the real SQL and routes with an explicit model test double. Neither substitutes for real model/deployment verification.

## Isolated PostgreSQL tests

The following starts a dedicated temporary database on port 55432. The password is a committed test-only value and must never be used in production. No application database or persistent volume is touched.

```powershell
docker compose -f compose.test.yml -p askdocs-tests up -d --wait
$env:TEST_DATABASE_URL = 'postgresql://postgres:askdocs-test-only@127.0.0.1:55432/askdocs_test'
pnpm test:api
Remove-Item Env:TEST_DATABASE_URL
docker compose -f compose.test.yml -p askdocs-tests down
```

The test suite refuses databases outside the local host or with any name other than `askdocs_test`. It truncates that dedicated test database between tests. Without the test URL, integration tests are explicitly skipped. GitHub CI runs them against its own PostgreSQL/pgvector service.

## Common problems

- **Docker pipe not found:** start Docker Desktop and wait for its Linux engine. Docker is optional when using managed PostgreSQL for the app; only local integration tests require it.
- **Service not connected:** check both processes, the local backend URL, and matching internal secrets. Never print credentials while diagnosing configuration.
- **AI quota exhausted:** the application and model provider both enforce limits. Wait for the relevant reset; refreshing or changing cookies does not bypass shared limits.
- **No readable PDF text:** upload an unlocked, text-based PDF. OCR and image extraction are outside this release.
- **Workspace expired:** start a fresh workspace. There is no login-based recovery after expiry or cookie removal.
- **Port 3100 busy during tests:** stop the process using that port. Tests deliberately refuse to reuse an unknown server.
