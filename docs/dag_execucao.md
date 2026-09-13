## O que a DAG faz

```
ingest  ──▶  train  ──▶  save
```

| Task | O que faz |
|---|---|
| `ingest` | Lê `data/raw/medical_tc_{train,test}.csv`, valida colunas (`medical_abstract`, `condition_label`), ausência de nulos e rótulos em 1–5; salva `data/processed/{train,test}.csv` + `ingest_report.json`. |
| `train` | Chama `python -m src.train --classifier logistic` sobre os dados processados, gerando `models/model.pkl`, `models/metrics.json` e `models/classification_report.txt`. |
| `save` | Versiona o artefato em `models/` com timestamp (`model_<ts>.pkl`, `metrics_<ts>.json`, `classification_report_<ts>.txt`) e registra em `models/versions.json`; mantém `model.pkl` vigente. |

- `schedule="0 3 * * *"` (diário às 03:00), `catchup=False`, `retries=2`, `retry_delay=2min`.

## Como executar localmente

Pré-requisito: Docker.

```bash
docker compose -f docker-compose.airflow.yml up --build -d
```

O `standalone` sobe scheduler + webserver + worker num só container (executor sequencial).
A primeira subida baixa a imagem oficial do Airflow e instala as deps de ML — pode levar alguns minutos.

**Senha do admin** (usuário `admin`):

```bash
docker compose -f docker-compose.airflow.yml logs airflow | grep -iE "password|admin"
```

**UI:** http://localhost:8080

## Executar a DAG end-to-end

1. Abra a UI (http://localhost:8080) e faça login com `admin` + senha do log.
2. Vá em **DAGs** → `retrain_triagem_dag` → botão **Trigger DAG** (▶) → **Trigger**.
3. Acompanhe o grafo (aba **Graph**): `ingest` → `train` → `save` devem ficar **verdes**.
4. Confira as evidências no host:
   - `data/processed/train.csv`, `test.csv`, `ingest_report.json`
   - `models/model.pkl` (atualizado), `models/model_<ts>.pkl`, `models/versions.json`

## Captura do grafo verde

```bash
docker compose -f docker-compose.airflow.yml up -d
# disparar a DAG e aguardar as 3 tasks ficarem verdes; então capturar a tela do
# grafo (Graph) e salvar como docs/dag_execucao.png
```

## Encerrar

```bash
docker compose -f docker-compose.airflow.yml down
```

> `down` sem `-v` preserva o estado do Airflow (DB SQLite) no volume do container,
> permitindo reexecutar sem re-inicializar. Para recomeçar do zero: `down -v`.
