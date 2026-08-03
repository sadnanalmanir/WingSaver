# WingSaver Web

Next.js App Router frontend for WingSaver. Deploy root for [Vercel](https://vercel.com/) (`apps/web`).

## Local development

```bash
# From repo root
pnpm install
pnpm dev:web
# http://localhost:3000
```

Set `NEXT_PUBLIC_API_BASE_URL` (see root `.env.example`) to point at the API.

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Search form |
| `/search?...` | Results (URL = source of truth; server-side filters) |
| `/flights/[offerId]` | Offer detail |

```bash
# terminal 1
cd apps/api && uv run fastapi dev
# terminal 2
pnpm dev:web
```
