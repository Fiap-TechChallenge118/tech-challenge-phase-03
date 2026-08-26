"""Carregamento do modelo de triagem médica.

Estratégia de inicialização (executada uma única vez no startup):
  1. Tenta baixar o artefato do S3 (MODEL_BUCKET / MODEL_KEY).
  2. Se USE_ONNX=true  → carrega com onnxruntime.InferenceSession.
     Se USE_ONNX=false → carrega pipeline sklearn com joblib.
  3. Se o S3 não estiver acessível ou o arquivo não existir, ativa o
     fallback mock (retorna "normal" com confiança 1.0 para qualquer entrada).

Variáveis de ambiente relevantes (ver .env.example):
  MODEL_BUCKET  — bucket S3 onde o artefato está armazenado
  MODEL_KEY     — chave do objeto  (ex.: models/model.onnx)
  USE_ONNX      — "true" | "false"
  AWS_REGION    — região do bucket
"""

import logging
import os
import tempfile
from typing import Literal

logger = logging.getLogger(__name__)

# Tipo das classes suportadas
ClasseUrgencia = Literal["normal", "atenção", "urgente"]

# Estado interno do loader — preenchido no startup, imutável depois
_model = None          # InferenceSession (ONNX) ou pipeline sklearn
_model_type: str = "mock"  # "onnx" | "sklearn" | "mock"


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def load_model() -> None:
    """Baixa e carrega o modelo no startup. Ativa mock em caso de falha."""
    global _model, _model_type

    use_onnx = os.getenv("USE_ONNX", "true").lower() == "true"
    bucket = os.getenv("MODEL_BUCKET", "")
    key = os.getenv("MODEL_KEY", "models/model.onnx")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not bucket:
        logger.warning(
            "MODEL_BUCKET não configurado — ativando modo mock. "
            "Defina MODEL_BUCKET para usar o modelo real."
        )
        _activate_mock()
        return

    suffix = ".onnx" if use_onnx else ".pkl"

    try:
        artifact_path = _download_from_s3(bucket, key, region, suffix)
    except Exception as exc:
        logger.warning(
            "Falha ao baixar artefato do S3 (bucket=%s, key=%s): %s — "
            "ativando modo mock.",
            bucket, key, exc,
        )
        _activate_mock()
        return

    try:
        if use_onnx:
            _load_onnx(artifact_path)
        else:
            _load_sklearn(artifact_path)
    except Exception as exc:
        logger.warning(
            "Falha ao carregar artefato (%s): %s — ativando modo mock.",
            artifact_path, exc,
        )
        _activate_mock()


def predict(texto: str) -> tuple[ClasseUrgencia, float]:
    """Retorna (classe_predita, confiança) para o texto de entrada.

    Args:
        texto: Texto do laudo médico (já validado pelo schema).

    Returns:
        Tupla (classe, confiança) onde confiança ∈ [0.0, 1.0].
    """
    if _model_type == "mock":
        return _mock_predict()

    if _model_type == "onnx":
        return _predict_onnx(texto)

    return _predict_sklearn(texto)


def model_status() -> str:
    """Retorna o modo ativo: 'loaded' (onnx/sklearn) ou 'mock'."""
    return "mock" if _model_type == "mock" else "loaded"


# ---------------------------------------------------------------------------
# Internos — download
# ---------------------------------------------------------------------------

def _download_from_s3(bucket: str, key: str, region: str, suffix: str) -> str:
    """Baixa o artefato do S3 para um arquivo temporário e retorna o caminho."""
    import boto3  # importação local para não atrasar o módulo quando não usado

    s3 = boto3.client("s3", region_name=region)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    logger.info("Baixando s3://%s/%s → %s", bucket, key, tmp.name)
    s3.download_fileobj(bucket, key, tmp)
    tmp.close()
    logger.info("Download concluído: %s", tmp.name)
    return tmp.name


# ---------------------------------------------------------------------------
# Internos — carregamento
# ---------------------------------------------------------------------------

def _load_onnx(path: str) -> None:
    global _model, _model_type
    import onnxruntime as ort  # noqa: PLC0415

    session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
    _model = session
    _model_type = "onnx"
    logger.info("Modelo ONNX carregado: %s", path)


def _load_sklearn(path: str) -> None:
    global _model, _model_type
    import joblib  # noqa: PLC0415

    pipeline = joblib.load(path)
    _model = pipeline
    _model_type = "sklearn"
    logger.info("Modelo sklearn carregado: %s", path)


def _activate_mock() -> None:
    global _model, _model_type
    _model = None
    _model_type = "mock"
    logger.warning(
        "Modo MOCK ativo — todas as predições retornarão 'normal' com confiança 1.0."
    )


# ---------------------------------------------------------------------------
# Internos — predição
# ---------------------------------------------------------------------------

# Mapeamento índice → classe (deve ser coerente com o label encoder do treino)
_CLASSES: list[ClasseUrgencia] = ["normal", "atenção", "urgente"]


def _mock_predict() -> tuple[ClasseUrgencia, float]:
    return "normal", 1.0


def _predict_onnx(texto: str) -> tuple[ClasseUrgencia, float]:
    """Executa inferência com onnxruntime."""
    import numpy as np  # noqa: PLC0415

    input_name = _model.get_inputs()[0].name
    # O pipeline sklearn exportado para ONNX espera array 2-D de strings
    result = _model.run(None, {input_name: np.array([[texto]])})

    # result[0] = label predito (string ou int), result[1] = mapa de probabilidades
    label_raw = result[0][0]

    if isinstance(label_raw, bytes):
        label_raw = label_raw.decode()

    classe: ClasseUrgencia = str(label_raw)  # type: ignore[assignment]

    # Probabilidades: dict {label: prob} ou array dependendo do opset
    if len(result) > 1:
        prob_map = result[1][0]  # dict ou array
        if isinstance(prob_map, dict):
            confianca = float(prob_map.get(label_raw, 1.0))
        else:
            idx = _CLASSES.index(classe) if classe in _CLASSES else 0
            confianca = float(prob_map[idx])
    else:
        confianca = 1.0

    return classe, confianca


def _predict_sklearn(texto: str) -> tuple[ClasseUrgencia, float]:
    """Executa inferência com pipeline sklearn."""
    import numpy as np  # noqa: PLC0415

    classe = str(_model.predict([texto])[0])  # type: ignore[union-attr]
    proba = _model.predict_proba([texto])[0]  # type: ignore[union-attr]

    classes_list: list[str] = list(_model.classes_)  # type: ignore[union-attr]
    idx = classes_list.index(classe) if classe in classes_list else 0
    confianca = float(np.max(proba)) if idx >= len(proba) else float(proba[idx])

    return classe, confianca  # type: ignore[return-value]
