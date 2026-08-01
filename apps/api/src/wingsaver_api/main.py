"""Application entrypoint for FastAPI Cloud and local `fastapi dev`."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Build the FastAPI application (expanded in later PRs)."""
    app = FastAPI(
        title="WingSaver API",
        version="0.1.0",
        description="Airline search API (scaffold)",
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Unversioned liveness probe (no dependency checks)."""
        return {"status": "ok"}

    return app


app = create_app()
