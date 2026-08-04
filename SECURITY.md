# Security Policy

## Reporting a vulnerability

If you discover a security issue in WingSaver, please **do not** open a public GitHub issue.

Email **sadnanalmanir@gmail.com** with:

- A description of the issue and impact
- Steps to reproduce (or a proof of concept)
- Affected component (`apps/api`, `apps/web`, deploy config, etc.)

You should receive an acknowledgment within a few business days.

## Scope notes

- This is a **search-only** demo/product slice; do not send real payment data or production airline credentials to mock endpoints.
- Never commit secrets. Use `.env.example` as the template; real values stay in gitignored `.env` / `.env.local` or host secret stores.
- Production should keep `/docs` and OpenAPI disabled (default when `ENVIRONMENT=production`).
