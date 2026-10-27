# Development setup

## Tool versions

Use the same versions on Windows and Ubuntu:

- Node.js: 22.23.4
- pnpm: 9.15.0
- Python: 3.13.2
- uv: 0.13.5

Node and Python versions are recorded in .nvmrc and .python-version.
The pnpm version is recorded in package.json.
.npmrc enables strict Node and pnpm engine checks during installation.
uv's own version is documented here; it is not automatically installed or enforced.
Install uv 0.13.5 separately before using Python service commands.

## Windows and Ubuntu

Keep a separate Git clone and installed dependencies on each operating system.
Commit and push before switching systems, then pull the same branch in the
other clone. Uncommitted changes do not synchronize.

For Ubuntu, open the Linux clone using VS Code's WSL connection and use Bash.
For Windows, use the Windows clone with PowerShell or Git Bash.
Do not use Windows Git against the Linux clone through a WSL network path.

Personal Git identity, authentication, signing, and hooks must be configured
separately in each clone. Local safeguards are not included by cloning.

## Install JavaScript dependencies

From the repository root:

```text
pnpm workspace:install
pnpm workspace:list
```

`pnpm workspace:install` runs `pnpm install --frozen-lockfile`. It fails if dependency
manifests and the committed lockfile disagree, rather than updating the lockfile.
It does not install Node, pnpm, Python or uv, create local secrets, or start services.

`pnpm workspace:list` lists the packages pnpm currently recognizes. It should
include the root workspace and `@askdocs/config`. Future app bootstrap tickets
will add package manifests for the applications; empty folders are not packages.

In Ubuntu with nvm installed, run `nvm use` first. On Windows, select Node.js
22.23.4 using your Windows installation or version manager. These two root
commands work in PowerShell, Git Bash, and Ubuntu Bash.

pnpm manages apps/web, apps/api, apps/worker, and packages/*.
apps/ai is managed separately with uv.

## Python conventions

Use uv for the AI service's dependencies and virtual environment.
Do not install project dependencies into Ubuntu's system Python.
The service's pyproject.toml and uv.lock belong in apps/ai and will be
introduced by its bootstrap ticket.

## Environment configuration

.env.example contains placeholders for planned local services.
It is documentation, not a working infrastructure setup.

Local .env files are ignored by Git. Example files may be committed.
Environment loading and service-specific validation will be configured
when each application is bootstrapped.

## Docker

Start Docker Desktop and enable integration for Ubuntu-24.04.
Check availability with `docker info` and `docker compose version`.

Application containers and local service definitions are separate tickets.

## Current limitations

There are no application startup commands yet.
Only the shared configuration package currently has a package manifest.
Empty application folders are not tracked by Git.
TypeScript settings have not yet been checked by an application build.
