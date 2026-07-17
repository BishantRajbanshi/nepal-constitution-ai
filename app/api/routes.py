from fastapi import APIRouter
from pydantic import BaseModel

from app.services.llm import answer
from app.services.retriever import retrieve

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    articles: list[str]     # citations
    entities: list[str]     # matched graph nodes (transparency/debug)


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    retrieved = retrieve(req.question)
    text = answer(req.question, retrieved["context"])
    return AskResponse(
        answer=text,
        articles=retrieved["articles"],
        entities=retrieved["entities"],
    )
