# WingSaver

[![CI](https://github.com/sadnanalmanir/WingSaver/actions/workflows/ci.yml/badge.svg)](https://github.com/sadnanalmanir/WingSaver/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg)](https://vitejs.dev/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)

**Production-minded airline search** — FastAPI backend + React (Vite/TypeScript) frontend, built as a monorepo with Redis caching, rate limiting, OpenAPI-typed clients, and CI that keeps the contract honest.

Search is **search-only** (no booking). Inventory uses a **provider adapter** (mock today; Amadeus/Duffel path designed in).

| | |
|---|---|
| **API** | FastAPI · Redis · structlog · Sentry · pytest/ruff/mypy |
| **Web** | Vite · React 19 · React Router · TanStack Query · TypeScript |
| **Contract** | OpenAPI export → generated TS types · drift check in CI |
| **Deploy** | FastAPI Cloud (API) · Vercel (web) · GitHub Actions CD |

Design notes: [`docs/design-airline-search.md`](docs/design-airline-search.md) · Deploy: [`docs/deploy.md`](docs/deploy.md)

---

## Why this project exists

A realistic full-stack slice of a flight meta-search product, emphasizing **backend discipline** recruiters care about:

- Adapter pattern for flight inventory (`mock` now; live providers without rewriting consumers)
- Canonical cache keys, Redis TTL cache, and **stampede protection** on cache miss
- Server-side filter / sort / pagination (not only client-side UX)
- Rate limiting, request IDs, security headers, log redaction, readiness probes
- Monorepo OpenAPI sync so frontend types cannot silently drift from the API

---

## Features (current)

- One-way and round-trip search (cabin class, passenger counts)
- Results with URL-driven filters, sort, and pagination
- Offer detail view with fare disclaimer (estimates, not a booking lock)
- Health / readiness endpoints; production docs lockdown
- Local Postgres + Redis via Docker Compose

**Not in v1:** booking/payments, accounts (designed, not shipped), multi-city builder, live GDS.

---

## Architecture

```text
┌─────────────────┐     POST /api/v1/search      ┌──────────────────────┐
│  React SPA (web)│ ───────────────────────────► │  FastAPI (api)       │
│  Vite · Vercel  │     GET  /api/v1/offers/:id  │  · SearchService     │
└─────────────────┘ ◄─────────────────────────── │  · RateLimiter       │
                                                 │  · FlightProvider    │
                                                 └──────────┬───────────┘
                                                            │
                                              ┌─────────────┴─────────────┐
                                              ▼                           ▼
                                         Redis cache                 Mock provider
                                      (offers + search)            (Amadeus later)
```

| Path | Role |
|------|------|
| `apps/api` | Installable `wingsaver_api` package; FastAPI Cloud deploy root |
| `apps/web` | Vite + React SPA; Vercel project root |
| `packages/openapi` | Exported `openapi.json` + generated TypeScript types |
| `docs/` | System design and deploy runbook |

---

## Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/)
- **Node 20+** and [pnpm](https://pnpm.io/) 9
- **Docker** (optional) for local Redis + Postgres

---

## Quick start

```bash
# Infrastructure
docker compose up -d

# API — http://127.0.0.1:8000/docs  ·  GET /health
cd apps/api
uv sync
uv run fastapi dev

# Web — another terminal, from repo root — http://localhost:3000
pnpm install
pnpm dev:web
```

Copy [`.env.example`](.env.example) to `apps/api/.env` and `apps/web/.env.local` as needed.  
Never commit real secrets (`.env` / `.env.local` are gitignored).

### Try a search

1. Open http://localhost:3000  
2. Pick origin/destination/dates and search  
3. Inspect filterable results and offer detail  
4. Browse interactive API docs at http://127.0.0.1:8000/docs  

With `FLIGHT_PROVIDER=mock` (default), no third-party API keys are required.

---

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev:web` | Vite dev server (port 3000) |
| `pnpm build:web` | Production SPA build (`apps/web/dist`) |
| `pnpm lint:web` / `typecheck:web` | Frontend checks |
| `pnpm openapi:sync` | Export OpenAPI + regenerate TS types |
| `pnpm openapi:check` | Fail if OpenAPI artifacts are stale (CI) |
| `pnpm test:api` / `cd apps/api && uv run pytest` | API tests |
| `cd apps/api && uv run fastapi dev` | API dev server |

---

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness (no dependencies) |
| `GET` | `/api/v1/ready` | Readiness (Redis required outside local) |
| `POST` | `/api/v1/search` | Search + cache + stampede + rate limit |
| `GET` | `/api/v1/offers/{offer_id}` | Offer detail |

More detail: [`apps/api/README.md`](apps/api/README.md).

---

## Deploy

| App | Host | Notes |
|-----|------|--------|
| `apps/api` | [FastAPI Cloud](https://fastapicloud.com/) | Entrypoint `wingsaver_api.main:app` |
| `apps/web` | [Vercel](https://vercel.com/) | Project root = `apps/web` |

CI runs lint, typecheck, tests, OpenAPI drift, and web build on every PR.  
Full env matrix, secrets, and CD: **[`docs/deploy.md`](docs/deploy.md)**.

---

## Project status

| Area | Status |
|------|--------|
| Mock search, results, detail | Done |
| Redis cache, stampede, rate limits | Done |
| Observability & security headers | Done |
| CI + deploy workflows | Done |
| Auth + Postgres accounts | Designed — not shipped |
| Live provider (Amadeus/Duffel) | Designed — not shipped |
| Playwright e2e | Planned |

---

## License

[MIT](LICENSE) © Mohammad Sadnan Al Manir
