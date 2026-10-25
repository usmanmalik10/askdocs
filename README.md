# AskDocs

Your documents. Clear answers.

AskDocs is a commercial SaaS project for individuals and teams to ask questions about private documents and receive answers with source citations.

## Current status

Repository initialized. The applications are not implemented yet. Follow the linked Jira tickets for planned work and progress; design prototypes are not working product features.

## Why one repository?

AskDocs uses a monorepo: one Git repository containing separate applications and shared packages. This lets a backend contract change, its matching frontend change and their tests be reviewed together. Each application keeps its own responsibilities and can run and deploy separately.

A workspace is the package-manager configuration connecting these folders. It enables shared dependencies and commands; it does not mean the frontend and backend are one process. Workspace configuration will be implemented in ASKDOCS-8.

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

Use pnpm workspaces for the TypeScript applications and uv for the Python service. Runtime versions, dependencies and startup commands will be pinned and documented in the configuration tickets.

## MVP journey

1. Sign in and create a private workspace.
2. Upload a text-based PDF, TXT or Markdown document.
3. Wait for document processing to finish.
4. Ask questions and verify answers against cited passages.
5. Manage members, usage and workspace settings.

## Planning

- [Sprint 1 board](https://usmanmaliksahib2611.atlassian.net/jira/software/projects/ASKDOCS/boards/1)
- [Repository creation: ASKDOCS-2](https://usmanmaliksahib2611.atlassian.net/browse/ASKDOCS-2)
- [Monorepo configuration: ASKDOCS-8](https://usmanmaliksahib2611.atlassian.net/browse/ASKDOCS-8)
- [Project Setup & Infrastructure](https://usmanmaliksahib2611.atlassian.net/browse/ASKDOCS-1)
- [Secure Sign-in](https://usmanmaliksahib2611.atlassian.net/browse/ASKDOCS-23)
- [Private Workspaces](https://usmanmaliksahib2611.atlassian.net/browse/ASKDOCS-24)

FE, BE, DB, infrastructure, configuration and CI work have separate small tickets. Dependencies flow from database work to backend APIs to frontend integration.

## Development workflow

Use the Jira key in branch names and commit messages. Keep changes focused on one ticket, explain the relevant concepts, and record the checks actually run. Add startup and test commands as each application is scaffolded.

Do not commit credentials, local environment files, uploaded documents or generated build artifacts. Keep project files private unless sharing is explicitly approved.

## Designs

The editable AskDocs MVP designs currently live in a local FigCraft file named AskDocs-MVP.figcraft, with an AskDocs-Design-Review.html gallery. They are not yet published or copied into this repository.

## Getting started

Clone this repository, then begin ASKDOCS-8. There is no application start command yet.
