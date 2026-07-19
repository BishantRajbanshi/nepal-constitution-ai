"""
Retrieval is the part of GraphRAG most likely to break silently — a bad
Cypher result shape or a formatting slip degrades answers without erroring.
These tests pin the contract: what goes into the LLM, and what gets cited.
"""
from contextlib import contextmanager
from unittest.mock import patch

from app.services import retriever

HITS = [{"entity": "Right to Education", "score": 0.9},
        {"entity": "Caste Discrimination", "score": 0.8}]
RELS = [{"source": "Right to Education", "rel": "GUARANTEED_BY", "target": "Article 31"}]
ARTICLES = [{"article": "Article 31", "text": "Every citizen shall have the right..."},
            {"article": "Article 24", "text": "No person shall be subjected to..."}]


def _fake_graph(hits=HITS, rels=RELS, articles=ARTICLES):
    """Neo4jGraph stub — returns each canned result in query order."""
    class G:
        def __init__(self):
            self.results = [hits, rels, articles]
            self.calls = []

        def query(self, cypher, params=None):
            self.calls.append((cypher, params))
            return self.results.pop(0)
    return G()


@contextmanager
def _patched(graph, vec=(0.1, 0.2, 0.3)):
    """Patches both external deps: Neo4j and the embedding model."""
    with patch.object(retriever, "get_graph", return_value=graph), \
         patch.object(retriever, "_embedder") as mock_embedder:
        mock_embedder.return_value.embed_query.return_value = list(vec)
        yield


def test_retrieve_returns_context_articles_and_entities():
    graph = _fake_graph()
    with _patched(graph):
        result = retriever.retrieve("Can education be denied?")

    assert set(result) == {"context", "articles", "entities"}
    assert result["entities"] == ["Right to Education", "Caste Discrimination"]
    # Citations are sorted and de-duplicated.
    assert result["articles"] == ["Article 24", "Article 31"]


def test_context_contains_graph_facts_and_article_text():
    graph = _fake_graph()
    with _patched(graph):
        context = retriever.retrieve("q")["context"]

    assert "KNOWLEDGE GRAPH FACTS:" in context
    assert "(Right to Education) -[GUARANTEED_BY]-> (Article 31)" in context
    assert "CONSTITUTIONAL TEXT:" in context
    assert "[Article 31]" in context
    assert "Every citizen shall have the right..." in context


def test_context_omits_facts_header_when_no_relationships():
    """A vector hit with no edges should still return usable article text."""
    graph = _fake_graph(rels=[])
    with _patched(graph):
        context = retriever.retrieve("q")["context"]

    assert "KNOWLEDGE GRAPH FACTS:" not in context
    assert "CONSTITUTIONAL TEXT:" in context


def test_no_matches_yields_empty_citations():
    graph = _fake_graph(hits=[], rels=[], articles=[])
    with _patched(graph):
        result = retriever.retrieve("something unrelated")

    assert result["entities"] == []
    assert result["articles"] == []


def test_articles_with_null_values_are_dropped_from_citations():
    """d.article can be null for stray Document nodes — never cite those."""
    graph = _fake_graph(articles=[{"article": None, "text": "orphan text"},
                                  {"article": "Article 31", "text": "real text"}])
    with _patched(graph):
        result = retriever.retrieve("q")

    assert result["articles"] == ["Article 31"]


def test_vector_query_uses_configured_index_and_top_k():
    graph = _fake_graph()
    with _patched(graph, vec=(0.4, 0.5)):
        retriever.retrieve("q")

    _, params = graph.calls[0]
    assert params["index"] == retriever.INDEX_NAME
    assert params["k"] == retriever.TOP_K
    assert params["vec"] == [0.4, 0.5]
