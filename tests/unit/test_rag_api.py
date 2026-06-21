from fastapi.testclient import TestClient

from app.api.app import app

_OPERATOR = {"X-API-Key": "dev-key-operator"}


def test_rag_index_and_query_flow():
    with TestClient(app) as client:
        indexed = client.post(
            "/rag/index",
            json={"documents": [{"doc_id": "d1", "text": "Claude is a language model."}]},
            headers=_OPERATOR,
        )
        assert indexed.status_code == 200
        assert indexed.json()["indexed_chunks"] >= 1

        answer = client.post(
            "/rag/query", json={"question": "what is claude", "top_k": 1}, headers=_OPERATOR
        )
    assert answer.status_code == 200
    body = answer.json()
    assert body["sources"]
    assert body["sources"][0]["doc_id"] == "d1"


def test_rag_query_empty_corpus_returns_422():
    with TestClient(app) as client:
        response = client.post("/rag/query", json={"question": "anything"}, headers=_OPERATOR)
    assert response.status_code == 422


def test_rag_index_requires_documents():
    with TestClient(app) as client:
        response = client.post("/rag/index", json={"documents": []}, headers=_OPERATOR)
    assert response.status_code == 422


def test_rag_index_idempotency_key_dedupes_replays():
    body = {"documents": [{"doc_id": "d1", "text": "idempotent content here"}]}
    headers = {**_OPERATOR, "Idempotency-Key": "k-1"}
    with TestClient(app) as client:
        first = client.post("/rag/index", json=body, headers=headers)
        second = client.post("/rag/index", json=body, headers=headers)
    assert first.status_code == 200
    assert first.json()["indexed_chunks"] >= 1
    assert second.status_code == 200
    assert second.json()["indexed_chunks"] == 0
