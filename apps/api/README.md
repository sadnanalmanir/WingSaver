# WingSaver API

FastAPI backend for WingSaver airline search. Deploy root for [FastAPI Cloud](https://fastapicloud.com/).

## Local development

```bash
# From repo root: start Postgres + Redis
docker compose up -d

# Install and run
cd apps/api
uv sync
uv run fastapi dev
# OpenAPI: http://127.0.0.1:8000/docs
```

Acceptance check (installable package, no `PYTHONPATH` hacks):

```bash
uv run python -c "from wingsaver_api.main import app; print(app.title)"
uv run fastapi dev   # OpenAPI at /docs without a path argument
```

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness (no deps) |
| GET | `/api/v1/health` | Versioned liveness |
| GET | `/api/v1/ready` | Readiness (Redis required in staging/production) |
| POST | `/api/v1/search` | Flight search (cache + stampede + rate limit; server filter/sort/page) |
| GET | `/api/v1/offers/{offer_id}` | Offer detail from Redis/`offer:v1:*` or in-memory store |

### Redis

Set `REDIS_URL` (see root `.env.example` / `docker compose up -d`). Without Redis, local uses in-memory store and **fail-open** rate limits. Production requires Redis (`validate_runtime`).

### Observability & security

| Item | Behavior |
|------|----------|
| **Sentry** | Set `SENTRY_DSN` to enable; no-op when unset. `send_default_pii=False`. |
| **Logs** | structlog JSON outside local; sensitive keys (`password`, `token`, `secret`, …) redacted; emails partially masked. |
| **Security headers** | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`. |
| **Docs lockdown** | Production: `/docs` and `/openapi.json` disabled. |

#### Ops runbook (errors)

1. Check Sentry (if DSN set) for exception spikes before Amadeus go-live.
2. Correlate with `X-Request-ID` / log `request_id`.
3. Uptime: probe unversioned `GET /health` (not `/ready` alone).
4. Live provider incident: set `FLIGHT_PROVIDER=mock` and redeploy (rollback path).

### Deploy

- Staging: push to `main` (paths under `apps/api/**`) → [`.github/workflows/deploy-api.yml`](../../.github/workflows/deploy-api.yml)
- Production: Actions → **Deploy API** → `workflow_dispatch` → `production` (protect the GitHub Environment)
- Secret: `FASTAPI_CLOUD_TOKEN`
- Details: [`docs/deploy.md`](../../docs/deploy.md)

## Layout

- `src/wingsaver_api/` — application package
- `tests/` — pytest suite
- `pyproject.toml` — dependencies, hatchling packaging, `[tool.fastapi] entrypoint`
