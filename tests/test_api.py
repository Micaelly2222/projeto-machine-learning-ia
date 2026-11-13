from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_case


def client():
    return TestClient(app)


def test_health():
    with client() as c:
        body = c.get("/health").json()
    assert body["status"] == "ok"
    assert body["llm_enabled"] is False


def test_policies():
    with client() as c:
        ids = [p["id"] for p in c.get("/policies").json()]
    assert ids == [f"POL-{i}" for i in range(1, 9)]


def test_analyze():
    with client() as c:
        response = c.post("/analyze", json=make_case())
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "approved"
    assert body["documents"][0]["document_type"] == "sentenca"


def test_analyze_valida_entrada():
    with client() as c:
        response = c.post("/analyze", json={"classe": "sem número"})
    assert response.status_code == 422


def test_analyze_valor_negativo():
    with client() as c:
        response = c.post("/analyze", json=make_case(valorCondenacao=-10))
    assert response.status_code == 422


def test_batch():
    with client() as c:
        response = c.post("/analyze/batch", json={"processos": [make_case(), make_case(valorCondenacao=100)]})
    body = response.json()
    assert body["total"] == 2
    assert body["summary"] == {"approved": 1, "rejected": 1}
