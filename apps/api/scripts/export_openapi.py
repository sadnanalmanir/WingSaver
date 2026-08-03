#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to packages/openapi/openapi.json.

Usage (from apps/api):
  uv run python scripts/export_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure package import works when run as a script
API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(API_ROOT / "src"))

from wingsaver_api.config import Settings, clear_settings_cache  # noqa: E402
from wingsaver_api.main import create_app  # noqa: E402

REPO_ROOT = API_ROOT.parents[1]
OUTPUT = REPO_ROOT / "packages" / "openapi" / "openapi.json"


def main() -> None:
    clear_settings_cache()
    settings = Settings(
        environment="local",
        redis_url=None,
        cors_origins=["http://localhost:3000"],
        flight_provider="mock",
    )
    app = create_app(settings)
    schema = app.openapi()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)} ({len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
