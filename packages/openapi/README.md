# `@wingsaver/openapi`

Exported OpenAPI document and generated TypeScript types for the WingSaver API.

## Layout

| Path | Role |
|------|------|
| `openapi.json` | Committed snapshot from FastAPI |
| `src/schema.ts` | Generated types (`openapi-typescript`) |
| `src/index.ts` | Re-exports |

## Commands (from repo root)

```bash
# Export schema + regenerate types
pnpm openapi:sync

# Fail CI if committed files are stale
pnpm openapi:check
```

From this package:

```bash
pnpm --filter @wingsaver/openapi export
pnpm --filter @wingsaver/openapi generate
pnpm --filter @wingsaver/openapi check
```

## Usage (web app)

```ts
import type { paths } from "@wingsaver/openapi/schema";

type SearchBody = paths["/api/v1/search"]["post"]["requestBody"]["content"]["application/json"];
type SearchResponse =
  paths["/api/v1/search"]["post"]["responses"]["200"]["content"]["application/json"];
```

## When to re-sync

After any change to API routes, request/response models, or error schemas that appear in OpenAPI.
