# WingSaver deploy guide

## Targets

| App | Host | Deploy root | Default CD |
|-----|------|-------------|------------|
| API | [FastAPI Cloud](https://fastapicloud.com/) | `apps/api` | GitHub Actions → `fastapi deploy` |
| Web | [Vercel](https://vercel.com/) | `apps/web` (Vite SPA) | Vercel Git integration (preferred) |

Design default (v1): **Actions + `FASTAPI_CLOUD_TOKEN`** for API; **Vercel Git** for web.

---

## One-time setup

### 1. FastAPI Cloud (API)

1. Create **two** apps if possible: `wingsaver-api-staging` and `wingsaver-api-prod` (or one app + separate projects).
2. Deploy root / project directory: contents of `apps/api` (`pyproject.toml` with `[tool.fastapi] entrypoint = "wingsaver_api.main:app"`).
3. Connect **Redis Cloud** → injects `REDIS_URL`.
4. Set environment variables (dashboard or `fastapi cloud env set`):

| Variable | Staging | Production | Secret? |
|----------|---------|------------|---------|
| `ENVIRONMENT` | `staging` | `production` | no |
| `REDIS_URL` | from integration | from integration | yes |
| `JWT_SECRET` | random ≥32 chars | random ≥32 chars | **yes** |
| `CORS_ORIGINS` | staging web URL(s) | production web URL(s) | no |
| `CORS_ORIGIN_REGEX` | Vercel preview regex (optional) | usually unset | no |
| `FLIGHT_PROVIDER` | `mock` | `mock` until Amadeus | no |
| `SENTRY_DSN` | project DSN | project DSN | yes |
| `TRUSTED_PROXY_HOPS` | `1` until verified | verified value | no |
| `AUTH_REGISTRATION_ENABLED` | `false` | `false` | no |

5. Create a CLI token and store as GitHub secret **`FASTAPI_CLOUD_TOKEN`**:
   - Repository secret, **or**
   - Per-environment secret under Environments `staging` / `production`.
6. Optional but recommended: set **`FASTAPI_CLOUD_APP_ID`** per environment so staging and production deploy to different FastAPI Cloud apps (`--app-id`).
7. Protect `production` environment with required reviewers (GitHub → Settings → Environments).

### 2. GitHub Actions (API)

Workflow: [`.github/workflows/deploy-api.yml`](../.github/workflows/deploy-api.yml)

| Trigger | Target |
|---------|--------|
| Push to `main` touching `apps/api/**` | **staging** |
| `workflow_dispatch` → staging | **staging** |
| `workflow_dispatch` → production | **production** (manual) |

Local dry-run (with token):

```bash
cd apps/api
export FASTAPI_CLOUD_TOKEN=...
# optional: export FASTAPI_CLOUD_APP_ID=...
uv sync
uv run fastapi deploy --no-wait
```

### 3. Vercel (Web)

**Preferred:** Import the GitHub repo in Vercel.

| Setting | Value |
|---------|--------|
| Root Directory | `apps/web` |
| Framework | Vite |
| Production branch | `main` |
| Output directory | `dist` |
| Env `VITE_API_BASE_URL` | Staging/prod API HTTPS origin (no trailing slash) |

Previews deploy per PR automatically. Configure CORS on the API (`CORS_ORIGINS` + optional `CORS_ORIGIN_REGEX`) to allow the Vercel host(s).

**Optional Actions path:** [`.github/workflows/deploy-web.yml`](../.github/workflows/deploy-web.yml) needs `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`. Skip if dashboard Git deploy is enough.

---

## Post-deploy verification

### API

```bash
# Liveness (uptime monitors should use this)
curl -sS "$API_BASE/health"

# Readiness (Redis required in staging/production)
curl -sS "$API_BASE/api/v1/ready"

# Search smoke (mock provider)
curl -sS -X POST "$API_BASE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"trip_type":"one_way","origin":"JFK","destination":"LHR","departure_date":"2026-09-10","passengers":{"adults":1,"children":0,"infants":0},"cabin_class":"economy","currency":"USD","page":1,"page_size":5}'
```

### X-Forwarded-For / `TRUSTED_PROXY_HOPS`

Platform hop count is **not assumed final**. On first staging deploy:

1. Call search (or any route) through the public URL.
2. Temporarily log or inspect the client IP chosen for rate limiting.
3. Adjust `TRUSTED_PROXY_HOPS` (default `1`) so rate limits key on the real client, not the proxy.
4. Re-deploy and re-check.

### Web

1. Open the Vercel URL.
2. Confirm `VITE_API_BASE_URL` points at the staging API.
3. Browser network tab: search requests succeed (CORS OK).

---

## Rollback

| Layer | Action |
|-------|--------|
| Web | Vercel → promote previous deployment |
| API | Re-run deploy for previous commit, or redeploy last known good SHA via Actions |
| Provider outage | Set `FLIGHT_PROVIDER=mock` on FastAPI Cloud and redeploy / update env |

---

## CI vs CD

| Workflow | Role |
|----------|------|
| `ci.yml` | Lint, typecheck, test, web build on PR/push |
| `deploy-api.yml` | Push API image/code to FastAPI Cloud |
| `deploy-web.yml` | Optional Vercel CLI deploy |

CD does **not** replace CI — keep PRs green before merge to `main`.
