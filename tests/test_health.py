"""Testes do endpoint GET /health."""


def test_health_returns_200(client):
    """O endpoint /health deve retornar HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body_has_status_key(client):
    """O corpo de /health deve conter a chave 'status'."""
    response = client.get("/health")
    body = response.json()
    assert "status" in body
    assert body["status"] == "ok"


def test_health_body_has_model_key(client):
    """O corpo de /health deve conter a chave 'model'."""
    response = client.get("/health")
    body = response.json()
    assert "model" in body
