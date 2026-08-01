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
```

## Layout

- `src/wingsaver_api/` — application package
- `tests/` — pytest suite
- `pyproject.toml` — dependencies, hatchling packaging, `[tool.fastapi] entrypoint`
