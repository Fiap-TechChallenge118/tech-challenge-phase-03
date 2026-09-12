"""Valida versão e contrato do pickle antes do benchmark ou upload para S3."""

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import InconsistentVersionWarning


def validate(path):
    # Compatibilidade com o import `from preprocess` usado pelo treino atual.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        model = joblib.load(path)
    texts = [
        "Patient presents with acute chest pain and shortness of breath.",
        "Routine examination with no significant pathological findings.",
    ]
    labels = model.predict(texts)
    probabilities = model.predict_proba(texts)
    classes = {str(label) for label in model.classes_}
    if classes != {"1", "2", "3", "4", "5"}:
        raise ValueError(f"Classes incompatíveis com o loader atual: {classes}")
    if len(labels) != len(texts) or probabilities.shape != (len(texts), 5):
        raise ValueError("Formato de saída incompatível com a API")
    if (
        not np.isfinite(probabilities).all()
        or (probabilities < 0).any()
        or (probabilities > 1).any()
        or not np.allclose(probabilities.sum(axis=1), 1)
    ):
        raise ValueError("Probabilidades inválidas")
    return {
        "model": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sklearn_version": sklearn.__version__,
        "classes": sorted(classes),
        "predictions": [str(label) for label in labels],
        "status": "compatible",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", type=Path, default=Path("models/model.pkl"))
    args = parser.parse_args()
    try:
        result = validate(args.model)
    except InconsistentVersionWarning as exc:
        parser.exit(
            2,
            f"Modelo incompatível: treino sklearn={exc.original_sklearn_version}; "
            f"runtime sklearn={exc.current_sklearn_version}. "
            "Regenerar com as dependências do projeto.\n",
        )
    except Exception as exc:
        parser.exit(2, f"Modelo inválido: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
