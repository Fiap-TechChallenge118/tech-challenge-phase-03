"""Integração do runtime real com o contrato HTTP da API."""

import numpy as np
from fastapi.testclient import TestClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from app import model_loader
from app.main import app
from src.export_onnx import export_onnx
from src.preprocess import preprocess_texts


def test_api_defaults_to_onnx_and_matches_sklearn(tmp_path, monkeypatch):
    texts = [
        "Tumor neoplasm cancer growth",
        "Digestive stomach bowel disease",
        "Nervous brain seizure disorder",
        "Cardiovascular heart chest pain",
        "General pathological fever symptoms",
    ]
    pipeline = Pipeline([
        ("preprocess", FunctionTransformer(preprocess_texts)),
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression()),
    ]).fit(texts, [1, 2, 3, 4, 5])
    model_path = tmp_path / "models" / "model.onnx"
    export_onnx(pipeline, model_path)
    monkeypatch.chdir(tmp_path)
    for name in ("USE_ONNX", "MODEL_PATH", "MODEL_BUCKET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(model_loader, "_model", None)
    monkeypatch.setattr(model_loader, "_model_type", "mock")

    with TestClient(app) as client:
        assert model_loader._model_type == "onnx"
        assert client.get("/health").json()["model"] == "loaded"
        for text in texts:
            response = client.post("/predict", json={"texto": text})
            assert response.status_code == 200
            label = str(pipeline.predict([text])[0])
            expected = model_loader._CONDITION_TO_URGENCY[label]
            assert response.json()["classe"] == expected
            np.testing.assert_allclose(
                response.json()["confianca"],
                pipeline.predict_proba([text]).max(),
                rtol=1e-5,
                atol=1e-6,
            )
