"""
API contract: /ask wiring, /health, and the static frontend mount.
Retrieval and generation are mocked — this asserts routing and shape only.
"""
from unittest.mock import patch

RETRIEVED = {
    "context": "KNOWLEDGE GRAPH FACTS:\n(A) -[X]-> (B)",
    "articles": ["Article 24", "Article 31"],
    "entities": ["Caste Discrimination"],
}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ask_returns_answer_with_citations(client):
    with patch("app.api.routes.retrieve", return_value=RETRIEVED) as mock_retrieve, \
         patch("app.api.routes.answer", return_value="No. (Article 24)") as mock_answer:
        resp = client.post("/ask", json={"question": "Can education be denied?"})

    assert resp.status_code == 200
    assert resp.json() == {
        "answer": "No. (Article 24)",
        "articles": ["Article 24", "Article 31"],
        "entities": ["Caste Discrimination"],
    }
    mock_retrieve.assert_called_once_with("Can education be denied?")
    # The LLM must receive the retrieved context, not the raw question alone.
    mock_answer.assert_called_once_with(
        "Can education be denied?", RETRIEVED["context"]
    )


def test_ask_rejects_missing_question(client):
    assert client.post("/ask", json={}).status_code == 422


def test_ask_rejects_wrong_question_type(client):
    assert client.post("/ask", json={"question": 42}).status_code == 422


def test_root_serves_frontend(client):
    """StaticFiles is mounted last; it must not shadow the API routes."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
