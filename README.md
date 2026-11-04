# AskDocs

Your documents. Clear answers.

AskDocs is an open-source SaaS project for individuals and teams to ask questions about private documents and receive answers with source citations.

## Current status

The initial pnpm workspace and shared TypeScript configuration are in place. The applications are not implemented yet. The roadmap below describes planned work; design prototypes are not working product features.

## Why one repository?

AskDocs uses a monorepo: one Git repository containing separate applications and shared packages. This lets a backend contract change, its matching frontend change and their tests be reviewed together. Each application keeps its own responsibilities and can run and deploy separately.

A workspace is the package-manager configuration connecting these folders. It enables shared dependencies and commands; it does not mean the frontend and backend are one process. pnpm connects the TypeScript packages through `pnpm-workspace.yaml`; the Python AI service uses uv separately.

## Planned structure

The following is the target layout, not a claim that these applications already exist:

```text
apps/
  web/          Next.js frontend
  api/          NestJS business API
  ai/           FastAPI internal AI service
  worker/       BullMQ background worker
packages/
  contracts/    API specifications and generated client types
  database/     Database schema and migrations
  config/       Shared development configuration
infra/          Local PostgreSQL/pgvector, Redis and S3-compatible storage
tests/          Integration, browser and AI-evaluation fixtures
docs/           Architecture decisions, learning notes and runbooks
```

Use pnpm workspaces for the TypeScript applications and uv for the Python service. Tool versions and setup commands are documented in [Development setup](docs/development/setup.md). Application dependencies and startup commands will be added in their bootstrap tickets.

## MVP journey

1. Sign in and create a private workspace.
2. Upload a text-based PDF, TXT or Markdown document.
3. Wait for document processing to finish.
4. Ask questions and verify answers against cited passages.
5. Manage members, usage and workspace settings.

## Roadmap

1. Bootstrap the frontend, backend services, local infrastructure and quality checks.
2. Add secure sign-in and private workspaces.
3. Add private document uploads, processing and retrieval.
4. Add grounded answers with citations, history and feedback.
5. Add team administration, usage controls and billing.

Suggestions and bug reports can be discussed in [GitHub Issues](https://github.com/usmanmalik10/askdocs/issues). Development proceeds in small tasks, with database work before the APIs and interfaces that depend on it.

## Development workflow

Reference the relevant issue in branch names and commit messages when available. Keep changes focused on one task, explain the relevant concepts, and record the checks actually run. Add startup and test commands as each application is scaffolded.

Do not commit credentials, local environment files, uploaded documents or generated build artifacts.

## Designs

The editable AskDocs MVP designs currently live in a local FigCraft file named AskDocs-MVP.figcraft, with an AskDocs-Design-Review.html gallery. They are not yet published or copied into this repository.

## Getting started

Install Node.js **22.23.4**, pnpm **9.15.0**, Python **3.13.2**, and uv **0.13.5**. Use the repository root for the following commands on Windows or Ubuntu:

```bash
pnpm workspace:install
pnpm workspace:list
```

`pnpm workspace:install` installs JavaScript dependencies using the committed lockfile; it does not install system tools, configure secrets, or start services. `pnpm workspace:list` lists recognized packages. Currently these are the private root workspace and `@askdocs/config`.

For Ubuntu with nvm, run `nvm use` first. Windows users should select Node.js 22.23.4 with their Windows installation or version manager. Keep a separate clone and dependencies on each operating system; see [Development setup](docs/development/setup.md) for the workflow.

The Node and pnpm versions are enforced during installation. `.python-version` selects Python for uv; uv's own version is documented and must be installed separately. `.env.example` contains placeholders only. There is no application start command yet.

## License

Copyright 2026 Usman Malik.

This repository is licensed under the [Apache License, Version 2.0](LICENSE).
