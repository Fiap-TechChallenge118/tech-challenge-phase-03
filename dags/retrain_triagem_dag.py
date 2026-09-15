"""DAG de retreino do modelo de triagem médica (FASE 6 — Etapa 2 do PDF).

Ciclo orquestrado: ``ingest >> train >> save``.

- **ingest** — lê os CSVs de ``data/raw/``, valida colunas e rótulos e
  salva as cópias processadas em ``data/processed/``.
- **train**  — treina o classificador chamando ``python -m src.train``
  (LogisticRegression, o melhor modelo do baseline).
- **save**   — versiona o artefato em ``models/`` com timestamp e mantém o
  ``model.pkl`` atualizado como o modelo vigente.

Execução local (Airflow em Docker):

    docker compose -f docker-compose.airflow.yml up --build -d

Depois, abrir http://localhost:8080, ativar a DAG e disparar manualmente.
Instruções completas: ``docs/dag_execucao.md``.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Raiz do projeto dentro do container Airflow (montada via docker-compose).
PROJECT_DIR = os.environ.get("PROJECT_DIR", "/opt/airflow")

RAW_DIR = Path(PROJECT_DIR) / "data" / "raw"
PROCESSED_DIR = Path(PROJECT_DIR) / "data" / "processed"
MODELS_DIR = Path(PROJECT_DIR) / "models"

REQUIRED_COLUMNS = {"medical_abstract", "condition_label"}
VALID_LABELS = {1, 2, 3, 4, 5}

# Arquivo de entrada -> nome do arquivo processado.
SOURCE_FILES = {"medical_tc_train.csv": "train.csv", "medical_tc_test.csv": "test.csv"}


def ingest(**context) -> dict:
    """Lê ``data/raw/``, valida e salva as cópias processadas em ``data/processed/``.

    Validações:
      * colunas obrigatórias presentes (``medical_abstract``, ``condition_label``);
      * sem valores nulos nas colunas-chave;
      * ``condition_label`` dentro de 1..5.
    """
    import pandas as pd  # import local: não atrasa o parse da DAG no scheduler

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict] = {}

    for src_name, out_name in SOURCE_FILES.items():
        src = RAW_DIR / src_name
        if not src.exists():
            raise FileNotFoundError(f"Arquivo de entrada ausente: {src}")

        df = pd.read_csv(src)

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"{src_name}: colunas obrigatórias ausentes: {sorted(missing)}")

        if df[list(REQUIRED_COLUMNS)].isna().any().any():
            raise ValueError(f"{src_name}: valores nulos nas colunas-chave")

        labels = set(df["condition_label"].dropna().unique())
        if not labels.issubset(VALID_LABELS):
            raise ValueError(f"{src_name}: rótulos fora de 1..5: {sorted(labels - VALID_LABELS)}")

        out = PROCESSED_DIR / out_name
        df.to_csv(out, index=False)
        summary[out_name] = {"rows": int(len(df)), "columns": list(df.columns)}

    report = {"source": "data/raw", "ingested": summary}
    (PROCESSED_DIR / "ingest_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


def save(**context) -> dict:
    """Versiona o artefato treinado em ``models/`` com timestamp.

    Copia ``model.pkl`` / ``metrics.json`` / ``classification_report.txt`` para
    ``<nome>_<timestamp>.<ext>`` e registra a versão em ``models/versions.json``.
    O ``model.pkl`` permanece como o artefato vigente (o ``train`` já o sobrescreve).
    """
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    versioned: list[str] = []

    for stem in ("model.pkl", "metrics.json", "classification_report.txt"):
        src = MODELS_DIR / stem
        if src.exists():
            dest = MODELS_DIR / f"{Path(stem).stem}_{timestamp}{Path(stem).suffix}"
            shutil.copy2(src, dest)
            versioned.append(dest.name)

    manifest_path = MODELS_DIR / "versions.json"
    versions = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else []
    )
    versions.append({"timestamp": timestamp, "artifacts": versioned})
    manifest_path.write_text(json.dumps(versions, indent=2), encoding="utf-8")

    return {"timestamp": timestamp, "artifacts": versioned}


# Comando de treino (caminhos relativos a PROJECT_DIR).
TRAIN_CMD = (
    "python -m src.train "
    "--data data/processed/train.csv "
    "--test-data data/processed/test.csv "
    "--model models/model.pkl "
    "--metrics models/metrics.json "
    "--report models/classification_report.txt "
    "--classifier logistic "
    "--random-state 42"
)

default_args = {
    "owner": "dev-c",
    "depends_on_past": False,
    "start_date": datetime(2026, 9, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="retrain_triagem_dag",
    description="Ciclo de retreino do modelo de triagem: ingest -> train -> save",
    default_args=default_args,
    schedule="0 3 * * *",  # diário às 03:00 (hora local do scheduler)
    catchup=False,
    max_active_runs=1,
    tags=["triagem", "ml", "retrain"],
) as dag:
    ingest_task = PythonOperator(
        task_id="ingest",
        python_callable=ingest,
        doc_md="Lê `data/raw/`, valida colunas/rótulos e salva em `data/processed/`.",
    )

    train_task = BashOperator(
        task_id="train",
        bash_command=TRAIN_CMD,
        cwd=PROJECT_DIR,
        doc_md="Treina o classificador via `python -m src.train` (LogisticRegression).",
    )

    save_task = PythonOperator(
        task_id="save",
        python_callable=save,
        doc_md="Versiona o artefato em `models/` com timestamp e mantém `model.pkl` vigente.",
    )

    ingest_task >> train_task >> save_task
