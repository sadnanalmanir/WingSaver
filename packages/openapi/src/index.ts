/**
 * WingSaver API OpenAPI package.
 *
 * - `openapi.json` — source of truth exported from FastAPI
 * - `schema.ts` — generated types via openapi-typescript
 *
 * Web (PR 8+) can import paths/components types:
 *   import type { paths } from "@wingsaver/openapi/schema";
 */

export type { paths, components, operations, webhooks } from "./schema";
