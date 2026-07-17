"""
Query-time retrieval:
  question -> embedding -> top-k similar entity nodes (vector index)
           -> expand: explicit relationships + source article text
           -> formatted context string for the LLM
"""
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings
from app.services.graph import get_graph

INDEX_NAME = "entity_embeddings"
TOP_K = 5


def _embedder() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.embed_model, base_url=settings.ollama_base_url
    )


def retrieve(question: str) -> dict:
    """Returns {'context': str, 'articles': [..], 'entities': [..]}"""
    graph = get_graph()
    q_vec = _embedder().embed_query(question)

    # 1. vector search: which entities is this question about?
    hits = graph.query(
        """
        CALL db.index.vector.queryNodes($index, $k, $vec)
        YIELD node, score
        RETURN node.id AS entity, score
        """,
        {"index": INDEX_NAME, "k": TOP_K, "vec": q_vec},
    )
    entities = [h["entity"] for h in hits]

    # 2. explicit relationships around those entities (1 hop)
    rels = graph.query(
        """
        MATCH (e:Entity)-[r]-(other:Entity)
        WHERE e.id IN $ids AND type(r) <> 'MENTIONS'
        RETURN DISTINCT e.id AS source, type(r) AS rel, other.id AS target
        LIMIT 30
        """,
        {"ids": entities},
    )

    # 3. source articles that mention those entities (our citation trail)
    articles = graph.query(
        """
        MATCH (d:Document)-[:MENTIONS]->(e:Entity)
        WHERE e.id IN $ids
        RETURN DISTINCT d.article AS article, d.text AS text
        LIMIT 6
        """,
        {"ids": entities},
    )

    # 4. format for the LLM
    rel_lines = [f"({r['source']}) -[{r['rel']}]-> ({r['target']})" for r in rels]
    art_blocks = [f"[{a['article']}]\n{a['text']}" for a in articles]

    context = ""
    if rel_lines:
        context += "KNOWLEDGE GRAPH FACTS:\n" + "\n".join(rel_lines) + "\n\n"
    context += "CONSTITUTIONAL TEXT:\n" + "\n\n".join(art_blocks)

    return {
        "context": context,
        "articles": sorted({a["article"] for a in articles if a["article"]}),
        "entities": entities,
    }
