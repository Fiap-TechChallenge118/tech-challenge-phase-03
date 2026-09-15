"""Configuração e fixtures compartilhadas para a suíte de testes.

Estratégia de isolamento:
  - O `model_loader` é substituído por um mock que retorna ("normal", 0.95)
    para qualquer texto, sem depender de S3, arquivo local ou modelo real.
  - O override é feito via `monkeypatch` aplicado ao módulo `app.model_loader`,
    garantindo que o lifespan do FastAPI use o mock desde o startup.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Garante que src/ está no path para o joblib/sklearn não reclamar de preprocess
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture()
def client(monkeypatch):
    """TestClient com model_loader mockado.

    O mock:
      - `load_model()` → não faz nada (sem S3, sem arquivo local)
      - `predict(texto)` → retorna sempre ("normal", 0.95)
      - `model_status()` → retorna "mock"
    """
    import app.model_loader as loader

    monkeypatch.setattr(loader, "load_model", lambda: None)
    monkeypatch.setattr(loader, "predict", lambda texto: ("normal", 0.95))
    monkeypatch.setattr(loader, "model_status", lambda: "mock")

    from app.main import app

    with TestClient(app) as c:
        yield c
