"""
Single place that owns the Neo4j connection.
Everything else (ingest script, retriever) imports from here.
"""
from langchain_neo4j import Neo4jGraph

from app.core.config import settings


def get_graph() -> Neo4jGraph:
    return Neo4jGraph(
        url=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
    )
