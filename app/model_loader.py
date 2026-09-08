"""Carregamento do modelo de triagem médica.

Estratégia de inicialização (executada uma única vez no startup):
  1. Se MODEL_BUCKET estiver definido → baixa o artefato do S3 (MODEL_KEY).
  2. Se MODEL_BUCKET não estiver definido → tenta carregar o artefato local
     indicado por MODEL_PATH (padrão: "models/model.pkl" ou "models/model.onnx"
     dependendo de USE_ONNX).
  3. Se o arquivo local não existir → ativa o fallback mock (retorna "normal"
     com confiança 1.0 para qualquer entrada).

Variáveis de ambiente relevantes (ver .env.example):
  MODEL_BUCKET  — bucket S3 onde o artefato está armazenado (deixar vazio para
                  usar o modelo local)
  MODEL_KEY     — chave do objeto no S3  (ex.: models/model.onnx)
  MODEL_PATH    — caminho local do artefato quando MODEL_BUCKET não está
                  definido (ex.: models/model.pkl)
  USE_ONNX      — "true" | "false"
  AWS_REGION    — região do bucket
"""

import logging
import os
import tempfile
from pathlib import Path
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
    """Carrega o modelo no startup. Ativa mock em último caso."""
    global _model, _model_type

    use_onnx = os.getenv("USE_ONNX", "false").lower() == "true"
    bucket = os.getenv("MODEL_BUCKET", "").strip()

    if bucket:
        _load_from_s3(use_onnx, bucket)
    else:
        _load_from_local(use_onnx)


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
# Internos — estratégias de carregamento
# ---------------------------------------------------------------------------

def _load_from_s3(use_onnx: bool, bucket: str) -> None:
    """Baixa o artefato do S3 e carrega o modelo."""
    key = os.getenv("MODEL_KEY", "models/model.onnx")
    region = os.getenv("AWS_REGION", "us-east-1")
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

    _load_artifact(artifact_path, use_onnx)


def _load_from_local(use_onnx: bool) -> None:
    """Carrega o artefato do sistema de arquivos local.

    Resolução do caminho (em ordem de prioridade):
      1. Variável MODEL_PATH, se definida.
      2. models/model.onnx  se USE_ONNX=true.
      3. models/model.pkl   se USE_ONNX=false.
    """
    default = "models/model.onnx" if use_onnx else "models/model.pkl"
    model_path = Path(os.getenv("MODEL_PATH", default))

    if not model_path.exists():
        logger.warning(
            "MODEL_BUCKET não configurado e arquivo local não encontrado: %s — "
            "ativando modo mock.",
            model_path,
        )
        _activate_mock()
        return

    logger.info(
        "MODEL_BUCKET não configurado — carregando modelo local: %s", model_path
    )
    _load_artifact(str(model_path), use_onnx)


def _load_artifact(path: str, use_onnx: bool) -> None:
    """Carrega o artefato de acordo com o runtime escolhido."""
    try:
        if use_onnx:
            _load_onnx(path)
        else:
            _load_sklearn(path)
    except Exception as exc:
        logger.warning(
            "Falha ao carregar artefato (%s): %s — ativando modo mock.",
            path, exc,
        )
        _activate_mock()


# ---------------------------------------------------------------------------
# Internos — download S3
# ---------------------------------------------------------------------------

def _download_from_s3(bucket: str, key: str, region: str, suffix: str) -> str:
    """Baixa o artefato do S3 para um arquivo temporário e retorna o caminho."""
    import boto3  # noqa: PLC0415

    s3 = boto3.client("s3", region_name=region)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    logger.info("Baixando s3://%s/%s → %s", bucket, key, tmp.name)
    s3.download_fileobj(bucket, key, tmp)
    tmp.close()
    logger.info("Download concluído: %s", tmp.name)
    return tmp.name


# ---------------------------------------------------------------------------
# Internos — carregamento de artefato
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

# Mapeamento condition_label (1–5) → classe de urgência
# Fonte: data/raw/medical_tc_labels.csv + docs/dataset.md
_CONDITION_TO_URGENCY: dict[str, ClasseUrgencia] = {
    "1": "atenção",   # neoplasms
    "2": "normal",    # digestive system diseases
    "3": "atenção",   # nervous system diseases
    "4": "urgente",   # cardiovascular diseases
    "5": "normal",    # general pathological conditions
}


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
    """Executa inferência com pipeline sklearn.

    O modelo retorna condition_label (1–5). Aplicamos o mapeamento
    _CONDITION_TO_URGENCY para converter para as 3 classes de urgência.
    """
    import numpy as np  # noqa: PLC0415

    label_raw = str(_model.predict([texto])[0])  # type: ignore[union-attr]
    proba = _model.predict_proba([texto])[0]  # type: ignore[union-attr]

    classes_list: list[str] = [str(c) for c in _model.classes_]  # type: ignore[union-attr]
    idx = classes_list.index(label_raw) if label_raw in classes_list else 0
    confianca = float(np.max(proba)) if idx >= len(proba) else float(proba[idx])

    # Converte condition_label → urgência (normal / atenção / urgente)
    classe: ClasseUrgencia = _CONDITION_TO_URGENCY.get(
        label_raw, "normal"  # type: ignore[arg-type]
    )

    return classe, confianca
