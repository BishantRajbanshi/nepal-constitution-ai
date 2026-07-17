from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Nepal Constitution Assistant",
    description="GraphRAG Q&A over Part 3 (Fundamental Rights) — not legal advice.",
)
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
