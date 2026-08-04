# WingSaver Web

Vite + React + TypeScript SPA for WingSaver airline search. Deploy root for [Vercel](https://vercel.com/) (`apps/web`).

## Local development

```bash
# From repo root
pnpm install
pnpm dev:web
# http://localhost:3000
```

Set `VITE_API_BASE_URL` (see root `.env.example`) to point at the API.

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Search form |
| `/search?...` | Results (URL = source of truth; server-side filters) |
| `/flights/:offerId` | Offer detail |

```bash
# terminal 1
cd apps/api && uv run fastapi dev
# terminal 2
pnpm dev:web
```

## Stack

- **Vite 6** bundler / dev server
- **React 19** + **TypeScript**
- **React Router 7** client routing
- **TanStack Query** for API state
- **@wingsaver/openapi** generated types
