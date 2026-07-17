"""
Answer generation: retrieved context + question -> grounded answer.
The prompt forces citation and forbids answering beyond the context —
the anti-hallucination core of any RAG system.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.core.config import settings

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an assistant answering questions about the Constitution of Nepal "
     "(2015), Part 3: Fundamental Rights.\n"
     "Rules:\n"
     "- Answer ONLY from the provided context.\n"
     "- Always cite the article number(s), e.g. (Article 20).\n"
     "- If the context is insufficient, say so — never invent provisions.\n"
     "- This is general information, not legal advice."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])


def answer(question: str, context: str) -> str:
    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,   # near-deterministic; slight room for phrasing
    )
    chain = PROMPT | llm
    return chain.invoke({"context": context, "question": question}).content
