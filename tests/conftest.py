"""
Test config. Set env before anything imports app.core.config, which
instantiates `settings` at import time and requires NEO4J_PASSWORD.
Tests never touch a real Neo4j or Ollama — those are mocked per test.
"""
import os

os.environ.setdefault("NEO4J_PASSWORD", "test-password")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
