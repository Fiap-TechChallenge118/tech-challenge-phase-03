"""Triagem Médica — API FastAPI de inferência.

Endpoints:
  POST /predict  — classifica um laudo médico em normal / atenção / urgente
  GET  /health   — liveness probe (usado pelo HEALTHCHECK do Docker e pelo ALB)
  GET  /metrics  — métricas no formato Prometheus (scraped pelo Prometheus)

Instrumentação (prometheus_client):
  triagem_requests_total          Counter  — total de predições por classe
  triagem_request_errors_total    Counter  — total de erros nas predições
  triagem_inference_duration_ms   Histogram — duração da inferência em ms
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

from app import model_loader
from app.schemas import PredictRequest, PredictResponse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Métricas Prometheus
# ---------------------------------------------------------------------------

REQUESTS_TOTAL = Counter(
    "triagem_requests_total",
    "Número total de predições realizadas.",
    ["classe_predita"],
)

ERRORS_TOTAL = Counter(
    "triagem_request_errors_total",
    "Número total de erros durante a predição.",
)

INFERENCE_DURATION = Histogram(
    "triagem_inference_duration_ms",
    "Duração da inferência em milissegundos.",
    buckets=[1, 2, 5, 10, 25, 50, 100, 250, 500, 1000],
)

# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN001
    """Carrega o modelo uma única vez no startup."""
    logger.info("Startup: carregando modelo...")
    model_loader.load_model()
    logger.info("Startup concluído — modo: %s", model_loader.model_status())
    yield
    logger.info("Shutdown: encerrando serviço de triagem.")


# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Triagem Médica API",
    version="1.0.0",
    description=(
        "Classificação automática de urgência de laudos médicos.\n\n"
        "Retorna uma das três classes: **normal**, **atenção** ou **urgente**."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/predict",
    response_model=PredictResponse,
    summary="Classifica um laudo médico",
    response_description="Classe de urgência predita com confiança e tempo de inferência.",
)
async def predict(request: PredictRequest) -> PredictResponse:
    """Recebe o texto de um laudo médico e retorna a classificação de urgência.

    - **texto**: texto do laudo (1 – 5.000 caracteres, não pode ser só espaços)
    - **classe**: `normal` | `atenção` | `urgente`
    - **confianca**: probabilidade da classe predita (0.0 – 1.0)
    - **tempo_ms**: tempo de inferência em milissegundos
    """
    texto = request.texto.strip()

    # Dupla checagem pós-strip (o validator do schema já bloqueia, mas mantemos
    # a guarda aqui para clareza e cobertura em testes de integração)
    if not texto:
        raise HTTPException(status_code=422, detail="O campo 'texto' não pode ser vazio.")

    t0 = time.perf_counter()
    try:
        classe, confianca = model_loader.predict(texto)
    except Exception as exc:
        ERRORS_TOTAL.inc()
        logger.exception("Erro durante a inferência: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno durante a inferência.") from exc
    finally:
        elapsed_ms = (time.perf_counter() - t0) * 1000

    REQUESTS_TOTAL.labels(classe_predita=classe).inc()
    INFERENCE_DURATION.observe(elapsed_ms)

    logger.info(
        "Predição: classe=%s confianca=%.3f tempo_ms=%.2f",
        classe, confianca, elapsed_ms,
    )

    return PredictResponse(classe=classe, confianca=confianca, tempo_ms=elapsed_ms)


@app.get(
    "/health",
    summary="Liveness probe",
    response_description="Status do serviço e do modelo.",
)
async def health() -> dict:
    """Retorna `200 OK` quando o serviço está no ar.

    O campo `model` indica se o modelo real foi carregado (`loaded`) ou se
    o fallback mock está ativo (`mock`).
    """
    return {"status": "ok", "model": model_loader.model_status()}


@app.get(
    "/metrics",
    summary="Métricas Prometheus",
    response_description="Métricas no formato text/plain exposition do Prometheus.",
    include_in_schema=False,  # não poluir o /docs com esse endpoint interno
)
async def metrics(request: Request) -> Response:
    """Endpoint de scrape para o Prometheus.

    Expõe:
    - `triagem_requests_total` (Counter, label `classe_predita`)
    - `triagem_request_errors_total` (Counter)
    - `triagem_inference_duration_ms` (Histogram)
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
