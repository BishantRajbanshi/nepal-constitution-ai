"""
One-time (rerun after each ingest): compute an embedding for every entity
node and create a Neo4j vector index over them.
Run: python -m scripts.embed_nodes
"""
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings
from app.services.graph import get_graph

INDEX_NAME = "entity_embeddings"
DIM = 768  # nomic-embed-text output dimension


def main() -> None:
    graph = get_graph()
    embedder = OllamaEmbeddings(model=settings.embed_model, base_url=settings.ollama_base_url)

    nodes = graph.query(
        "MATCH (n) WHERE NOT n:Document RETURN elementId(n) AS eid, n.id AS id"
    )
    print(f"Embedding {len(nodes)} entity nodes...")

    texts = [n["id"] for n in nodes]
    vectors = embedder.embed_documents(texts)  # one batched call

    for node, vec in zip(nodes, vectors):
        graph.query(
            "MATCH (n) WHERE elementId(n) = $eid SET n.embedding = $vec",
            {"eid": node["eid"], "vec": vec},
        )

    # vector indexes support only ONE label -> tag all entities :Entity
    graph.query("MATCH (n) WHERE NOT n:Document SET n:Entity")
    graph.query(f"""
        CREATE VECTOR INDEX {INDEX_NAME} IF NOT EXISTS
        FOR (n:Entity) ON (n.embedding)
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {DIM},
            `vector.similarity_function`: 'cosine'
        }}}}
    """)
    print("Vector index ready.")


if __name__ == "__main__":
    main()
