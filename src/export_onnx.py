"""Exporta o pipeline treinado para ONNX (FASE 8) e valida paridade.

O modelo ``.pkl`` é um ``Pipeline(preprocess -> tfidf -> clf)``. O passo
``preprocess`` é um ``FunctionTransformer`` em Python (regex + stopwords) que
não converte bem para ONNX; por isso exportamos apenas ``tfidf -> clf`` e o
pré-processamento permanece em Python — aplicado ANTES de chamar o runtime ONNX
(o mesmo fluxo que ``_predict_onnx`` fará na API).

Uso (dentro da imagem da API, python 3.11):

    python -m src.export_onnx \
        --model models/model.pkl \
        --output models/model.onnx \
        --data data/raw/medical_tc_test.csv \
        --n 200
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocess import preprocess_texts  # noqa: E402


def export_onnx(pipeline: Pipeline, output: Path):
    """Exporta o sub-pipeline ``tfidf -> clf`` para ONNX.

    Entrada esperada: coluna de texto JÁ pré-processado (StringTensor [None, 1]).
    Saída: rótulo predito (condition_label 1..5) + matriz de probabilidades.
    """
    import onnx  # noqa: PLC0415
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import StringTensorType

    steps = dict(pipeline.named_steps)
    sub = Pipeline([("tfidf", steps["tfidf"]), ("clf", steps["clf"])])

    onx = convert_sklearn(
        sub,
        initial_types=[("input", StringTensorType([None, 1]))],
        options={id(sub): {"zipmap": False}},
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    onnx.save_model(onx, str(output))
    return onx


def check_parity(pipeline: Pipeline, onnx_path: Path, texts: list[str]) -> dict:
    """Compara classe predita pelo ``.pkl`` (bruto) vs ``.onnx`` (pré-processado)."""
    import onnxruntime as ort  # noqa: PLC0415

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    y_pkl = np.asarray(pipeline.predict(texts), dtype=int)
    proba_pkl = np.asarray(pipeline.predict_proba(texts), dtype=float)

    y_onnx = []
    proba_onnx = []
    for t in texts:
        pre = preprocess_texts([t])[0]
        out = session.run(None, {input_name: np.array([[pre]])})
        y_onnx.append(out[0][0])
        proba_onnx.append(out[1][0])
    y_onnx = np.asarray(y_onnx, dtype=int)
    proba_onnx = np.asarray(proba_onnx, dtype=float)

    mismatch_idx = [i for i in range(len(texts)) if y_pkl[i] != y_onnx[i]]
    max_abs_diff = float(np.max(np.abs(proba_pkl - proba_onnx)))

    return {
        "n": len(texts),
        "matched": len(texts) - len(mismatch_idx),
        "mismatches": len(mismatch_idx),
        "match_rate": round((len(texts) - len(mismatch_idx)) / len(texts), 6),
        "max_abs_proba_diff": max_abs_diff,
        "mismatch_idx": mismatch_idx,
        "labels_pkl": y_pkl.tolist(),
        "labels_onnx": y_onnx.tolist(),
    }


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="models/model.pkl")
    p.add_argument("--output", default="models/model.onnx")
    p.add_argument(
        "--data",
        default="data/raw/medical_tc_test.csv",
        help="CSV com coluna medical_abstract para o teste de paridade.",
    )
    p.add_argument("--n", type=int, default=200)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    pipeline = joblib.load(args.model)
    print(f"Pipeline carregado: {args.model}")

    export_onnx(pipeline, Path(args.output))
    print(f"ONNX exportado -> {args.output}")

    if args.data:
        import pandas as pd  # noqa: PLC0415

        df = pd.read_csv(args.data).dropna(subset=["medical_abstract"])
        texts = df["medical_abstract"].head(args.n).tolist()
        result = check_parity(pipeline, Path(args.output), texts)
        print(
            f"Paridade: {result['matched']}/{result['n']} classes idênticas "
            f"({result['match_rate'] * 100:.2f}%) — "
            f"{result['mismatches']} divergências — "
            f"max|Δproba|={result['max_abs_proba_diff']:.2e}"
        )
        for i in result["mismatch_idx"]:
            print(
                f"  DIVERGÊNCIA #{i}: pkl={result['labels_pkl'][i]} "
                f"onnx={result['labels_onnx'][i]}  texto={texts[i][:60]!r}"
            )
        return 0 if result["mismatches"] == 0 else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
