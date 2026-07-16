# Nepal Constitution Assistant (GraphRAG)

Ask questions about the Constitution of Nepal (2015) and get answers
grounded in actual articles — powered by **GraphRAG**: retrieval over a
knowledge graph instead of plain document search.

> "Can a citizen be denied education based on caste?"
> → traverses: (Right to Education) —[GUARANTEED_BY]→ (Article 31),
>   (Caste Discrimination) —[PROHIBITED_BY]→ (Article 24)

## Why GraphRAG?

Classic RAG retrieves text chunks by similarity. Constitutional questions
often need *connected* facts: a right, its article, its exceptions, and
related rights. A knowledge graph stores these links explicitly and
retrieval follows them.

## How it works

1. **Ingestion (once):** an LLM reads constitutional articles and extracts
   entities + relationships (triples) into Neo4j.
2. **Query (per request):**
   - Embed the question (nomic-embed-text)
   - Vector-match it to graph nodes
   - Traverse 2 hops to collect a relevant subgraph
   - qwen2.5 answers using that subgraph, citing articles

## Scope

Starts with **Part 3 — Fundamental Rights (Articles 16–48)**.
Designed to expand to the full constitution.

## Stack

Neo4j 5 (graph + vector index) · Ollama (qwen2.5, nomic-embed-text) ·
LangChain · FastAPI · Docker

## Disclaimer

Educational project — not legal advice.

## Status

🚧 In development
