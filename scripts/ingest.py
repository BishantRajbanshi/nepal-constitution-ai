"""
One-time ingestion: read data/articles/*.md, have the LLM extract a
knowledge graph from each article, store it in Neo4j.

Each extracted node/relationship is tagged with its source article so
answers can cite them. Run: python -m scripts.ingest
"""
from pathlib import Path

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.services.graph import get_graph

ARTICLES_DIR = Path("data/articles")

# Constraining node/relationship types = cleaner graph.
# Without this, the LLM invents dozens of inconsistent labels.
ALLOWED_NODES = ["Right", "Person", "Group", "Institution", "Restriction", "Concept"]
ALLOWED_RELS = [
    "GUARANTEES", "APPLIES_TO", "RESTRICTED_BY", "PROTECTS",
    "PROHIBITS", "REQUIRES", "RELATED_TO",
]


def load_articles() -> list[Document]:
    """One Document per clause-sized chunk, not per article.
    Small chunks -> the LLM extracts every fact instead of just the headline."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=50,
        separators=["\n(", "\n", ". ", " "],  # prefer clause boundaries like (2), (a)
    )
    docs = []
    for path in sorted(ARTICLES_DIR.glob("article_*.md")):
        text = path.read_text(encoding="utf-8")
        article_id = path.stem.replace("_", " ").title()
        title = text.splitlines()[0].lstrip("# ")  # keep article title as context
        for chunk in splitter.split_text(text):
            content = f"{title}\n{chunk}" if not chunk.startswith("#") else chunk
            docs.append(Document(page_content=content, metadata={"article": article_id}))
    return docs


def main() -> None:
    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0,  # extraction must be deterministic, not creative
        format="json",  # force valid JSON output — qwen wraps it in markdown otherwise
    )
    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=ALLOWED_NODES,
        allowed_relationships=ALLOWED_RELS,
        ignore_tool_usage=True,
        additional_instructions=(
            "Extract EVERY right, freedom, group, restriction and condition "
            "mentioned. Legal text is dense: one clause often contains several "
            "facts. Prefer many small triples over one summary triple."
        ),   # qwen2.5 function-calling is unreliable; use prompt+JSON parsing
    )
    graph = get_graph()

    docs = load_articles()
    print(f"Ingesting {len(docs)} articles...")

    for i, doc in enumerate(docs, 1):
        article = doc.metadata["article"]
        try:
            graph_docs = transformer.convert_to_graph_documents([doc])
            # include_source=True creates a (:Document) node per article,
            # linked to every entity via MENTIONS — our citation trail
            graph.add_graph_documents(graph_docs, include_source=True)
            n = len(graph_docs[0].nodes)
            r = len(graph_docs[0].relationships)
            print(f"[{i}/{len(docs)}] {article}: {n} nodes, {r} relationships")
        except Exception as e:
            print(f"[{i}/{len(docs)}] {article}: FAILED — {e}")

    print("Done. Inspect at http://localhost:7474")


if __name__ == "__main__":
    main()
