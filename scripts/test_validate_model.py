"""Contratos de compatibilidade do artefato antes do deploy."""

import warnings

import numpy as np
import pytest
from sklearn.exceptions import InconsistentVersionWarning

from scripts.validate_model import validate


def test_rejects_model_from_another_sklearn_version(monkeypatch, tmp_path):
    def load(_):
        warnings.warn(
            InconsistentVersionWarning(
                estimator_name="Pipeline",
                current_sklearn_version="1.4.2",
                original_sklearn_version="1.9.0",
            )
        )

    monkeypatch.setattr("scripts.validate_model.joblib.load", load)
    with pytest.raises(InconsistentVersionWarning):
        validate(tmp_path / "model.pkl")


@pytest.mark.parametrize("invalid", [False, True])
def test_probability_contract(monkeypatch, tmp_path, invalid):
    class Model:
        classes_ = np.arange(1, 6)

        def predict(self, texts):
            return np.ones(len(texts), dtype=int)

        def predict_proba(self, texts):
            values = np.full((len(texts), 5), 0.2)
            if invalid:
                values[0, 0] = np.nan
            return values

    path = tmp_path / "model.pkl"
    path.write_bytes(b"test fixture")
    monkeypatch.setattr("scripts.validate_model.joblib.load", lambda _: Model())
    if invalid:
        with pytest.raises(ValueError, match="Probabilidades"):
            validate(path)
    else:
        assert validate(path)["status"] == "compatible"
