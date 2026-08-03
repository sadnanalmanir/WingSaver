# WingSaver

Production-quality airline search: **FastAPI** backend (FastAPI Cloud) + **Next.js** frontend (Vercel).

Design: [`docs/design-airline-search.md`](docs/design-airline-search.md)

## Repository layout

```text
apps/
  api/          # FastAPI — FastAPI Cloud deploy root
  web/          # Next.js App Router — Vercel project root
packages/
  openapi/      # OpenAPI export + typed client (later)
docs/           # Design & product docs
```

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node 20+ and [pnpm](https://pnpm.io/) 9
- Docker (optional, for local Postgres + Redis)

## Quick start

```bash
# Infrastructure
docker compose up -d

# API
cd apps/api
uv sync
uv run fastapi dev
# http://127.0.0.1:8000/docs  ·  GET /health

# Web (from repo root, another terminal)
pnpm install
pnpm dev:web
# http://localhost:3000
```

Copy [`.env.example`](.env.example) into `apps/api/.env` and `apps/web/.env.local` as needed.

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev:web` | Next.js dev server |
| `pnpm build:web` | Production web build |
| `pnpm lint:web` / `typecheck:web` | Frontend checks |
| `cd apps/api && uv run fastapi dev` | API dev server |
| `cd apps/api && uv run pytest` | API tests |

## Deploy targets

| App | Host | Notes |
|-----|------|--------|
| `apps/api` | [FastAPI Cloud](https://fastapicloud.com/) | `pyproject.toml` entrypoint `wingsaver_api.main:app`; CD via Actions |
| `apps/web` | [Vercel](https://vercel.com/) | Project root = `apps/web`; prefer Git integration |

Full setup, secrets, env matrix, and XFF verification: **[`docs/deploy.md`](docs/deploy.md)**.

## Status

**PR 6 complete** — staging CD (FastAPI Cloud via Actions; Vercel web wiring). See [`docs/deploy.md`](docs/deploy.md).
Next: OpenAPI export + typed TS client (PR 7).
