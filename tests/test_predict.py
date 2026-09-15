"""Testes do endpoint POST /predict."""

VALID_TEXT = (
    "Patient presents with severe chest pain radiating to the left arm, "
    "accompanied by shortness of breath and diaphoresis."
)

VALID_CLASSES = {"normal", "atenção", "urgente"}


def test_predict_valid_text_returns_200(client):
    """Texto válido deve retornar HTTP 200."""
    response = client.post("/predict", json={"texto": VALID_TEXT})
    assert response.status_code == 200


def test_predict_valid_text_returns_valid_class(client):
    """Resposta deve conter classe válida, confianca em [0,1] e tempo_ms >= 0."""
    response = client.post("/predict", json={"texto": VALID_TEXT})
    body = response.json()

    assert body["classe"] in VALID_CLASSES
    assert 0.0 <= body["confianca"] <= 1.0
    assert body["tempo_ms"] >= 0.0


def test_predict_empty_text_returns_422(client):
    """Texto vazio deve ser rejeitado com HTTP 422."""
    response = client.post("/predict", json={"texto": ""})
    assert response.status_code == 422


def test_predict_blank_text_returns_422(client):
    """Texto composto apenas de espaços deve ser rejeitado com HTTP 422."""
    response = client.post("/predict", json={"texto": "     "})
    assert response.status_code == 422


def test_predict_missing_field_returns_422(client):
    """Payload sem o campo 'texto' deve ser rejeitado com HTTP 422."""
    response = client.post("/predict", json={})
    assert response.status_code == 422


def test_predict_text_too_long_returns_422(client):
    """Texto com mais de 5.000 caracteres deve ser rejeitado com HTTP 422."""
    response = client.post("/predict", json={"texto": "x" * 6000})
    assert response.status_code == 422


def test_predict_response_fields_present(client):
    """Resposta deve conter exatamente os campos: classe, confianca, tempo_ms."""
    response = client.post("/predict", json={"texto": VALID_TEXT})
    body = response.json()

    assert "classe" in body
    assert "confianca" in body
    assert "tempo_ms" in body
