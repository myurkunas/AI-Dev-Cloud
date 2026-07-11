"""End-to-end /ask tests via the FastAPI TestClient.

The stub backend is forced so these tests need no API key or network.
"""

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def force_stub_backend(monkeypatch):
    monkeypatch.setattr(config, "GENERATION_BACKEND", "stub")


def test_supported_question_returns_grounded_answer_with_sources():
    res = client.post("/ask", json={"question": "Is the GRE required?"})
    assert res.status_code == 200
    body = res.json()
    assert body["support_status"] == "supported"
    assert body["sources"], "a supported answer must cite at least one source"
    assert body["escalation"] is None


def test_unsupported_question_refuses_instead_of_inventing():
    res = client.post("/ask", json={"question": "What is the capital of France?"})
    body = res.json()
    assert body["support_status"] == "unsupported"
    assert body["sources"] == []
    assert body["escalation"] is not None


def test_applicant_specific_question_is_escalated():
    res = client.post("/ask", json={"question": "What are my chances of getting in?"})
    body = res.json()
    assert body["support_status"] == "escalated"
    assert body["escalation"] is not None


def test_empty_question_is_rejected_by_validation():
    res = client.post("/ask", json={"question": ""})
    assert res.status_code == 422


def test_health_endpoint():
    from app.retrieval import load_documents

    res = client.get("/health")
    assert res.status_code == 200
    # documents count should match the loaded corpus, whatever its size.
    assert res.json()["documents"] == len(load_documents())
