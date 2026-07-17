from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Nepal Constitution Assistant",
    description="GraphRAG Q&A over Part 3 (Fundamental Rights) — not legal advice.",
)
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Mounted last so API routes above win; html=True serves index.html at "/".
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
