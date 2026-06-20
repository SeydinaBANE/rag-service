from fastapi.testclient import TestClient

from app.api.app import app


def test_rag_index_and_query_flow():
    with TestClient(app) as client:
        indexed = client.post(
            "/rag/index",
            json={"documents": [{"doc_id": "d1", "text": "Claude is a language model."}]},
        )
        assert indexed.status_code == 200
        assert indexed.json()["indexed_chunks"] >= 1

        answer = client.post("/rag/query", json={"question": "what is claude", "top_k": 1})
    assert answer.status_code == 200
    body = answer.json()
    assert body["sources"]
    assert body["sources"][0]["doc_id"] == "d1"


def test_rag_query_empty_corpus_returns_422():
    with TestClient(app) as client:
        response = client.post("/rag/query", json={"question": "anything"})
    assert response.status_code == 422


def test_rag_index_requires_documents():
    with TestClient(app) as client:
        response = client.post("/rag/index", json={"documents": []})
    assert response.status_code == 422
