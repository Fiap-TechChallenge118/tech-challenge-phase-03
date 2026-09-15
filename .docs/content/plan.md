# Plano de Execução — Pipeline Completo de ML (EDA → Deploy AWS ECS/Fargate)

> Fonte de verdade dos requisitos: `tech-challenge.md`. Este plano é a proposta de execução, ajustável.
> Legenda: **[PDF]** = requisito obrigatório que vale nota · **[EXT]** = extensão de arquitetura (AWS/ECS/Terraform), não exigida pelo PDF mas é o tema central "deploy em produção".

---

## Arquitetura decidida (100% ECS + Fargate)

```
TREINO (batch, sob demanda / agendado)
  Airflow (DAG)  →  ECS Fargate Task (roda src/train.py)
                 →  lê dataset do S3 (raw)
                 →  grava model.onnx + model.pkl no S3 (models/)

INFERENCIA (real-time, servico persistente)
  Client  →  ALB  →  ECS Fargate Service (container FastAPI + uvicorn)
          →  baixa model.onnx do S3 no startup
          →  /predict, /health, /metrics

MONITORAMENTO (rubrica do PDF = stack local, e coerente em producao)
  Prometheus faz scrape do /metrics do servico  →  Grafana dashboard (>=4 paineis)
  Local: docker-compose (API + Prometheus + Grafana)
  Producao: mesmo modelo de scrape, pois o servico ECS e persistente

REGISTRO DE IMAGENS
  ECR: imagem unica (mesma imagem serve o ECS Service de inferencia
       e a ECS Task de treino, via override de comando)

IaC
  Terraform unico em infra/ (sem ambientes) compondo modulos:
  networking, s3, ecr, ecs (service + task), alb, iam, monitoring
```

### Decisoes tecnicas travadas
1. Inferencia = **ECS Fargate Service persistente** atras de **ALB** (sem Lambda, sem API Gateway).
2. Servico **baixa model.onnx do S3 no startup** (nao embutido na imagem; retreino atualiza o S3).
3. Treino = **ECS Fargate Task** efemera disparada pela DAG do Airflow.
4. Monitoramento = **Prometheus + Grafana** (scrape do /metrics). Sem CloudWatch.
5. **Terraform unico** (sem dev/staging/prod).
6. **Uma imagem Docker** e **uma base de codigo FastAPI** — mesma logica local e em producao.
7. Infra concentrada no **Dev B** (eixo Infra/CI/CD/Cloud), por decisao do proprio Dev B.

---

## Passo a passo (ordem de execucao) — com responsavel

### ETAPA 0 — Fundacao do repositorio  ·  Dev A
- [x] Estrutura de pastas (feita) + `.gitkeep`
- [x] `pyproject.toml` com dependencias fixadas: runtime (`fastapi`, `uvicorn`, `scikit-learn`, `joblib`, `prometheus-client`, `onnxruntime`, `skl2onnx`, `numpy`, `pandas`, `boto3`) + extra `dev` (`pytest`, `httpx`, `ruff`)
- [x] Instalacao: `pip install -e ".[dev]"`
- [x] `.gitignore`, `.dockerignore`, `.env.example`
- [x] `CONTRIBUTING.md`, README esqueleto
- [x] Criar repo publico + convidar devs + branch protection + commit inicial (acoes no GitHub)

### ETAPA 1 — EDA  ·  Dev C   [EXT — lacuna preenchida]
- [ ] `notebooks/01_eda.ipynb`: distribuicao de classes, comprimento de texto, nulos, duplicatas
- [ ] `docs/eda_resumo.md` com achados que alimentam o mapeamento das 3 classes

### ETAPA 2 — Dataset + Feature Engineering + Modelo  ·  Dev C   [PDF]
- [ ] Dataset publico >= 2.000 amostras → `data/raw/`  **[PDF]**
- [ ] `src/preprocess.py`: limpeza, lowercase, stopwords  **[PDF]**
- [ ] Feature engineering: `TfidfVectorizer(ngram_range, max_features)` + `class_weight="balanced"`  **[PDF]**
- [ ] `src/train.py` (CLI): pipeline TF-IDF + LogisticRegression, split, `classification_report`, `joblib.dump`  **[PDF]**
- [ ] `data/processed/dataset.csv` + `docs/metricas_modelo.txt`  **[PDF]**

### ETAPA 3 — API FastAPI (servico de inferencia)  ·  Dev A   [PDF]
- [ ] `app/schemas.py`: `PredictRequest`, `PredictResponse`  **[PDF]**
- [ ] `app/model_loader.py`: baixa `model.onnx`/`model.pkl` do S3 no startup (fallback local), carrega uma vez  **[EXT]**
- [ ] `app/main.py`: `POST /predict`, `GET /health`  **[PDF]**
- [ ] Instrumentacao `prometheus_client`: `/metrics`, Counter + Histogram + erros  **[PDF]**
- [ ] Decisao arquitetural no README: real-time vs batch; justificar **ECS Fargate + ALB** para inferencia e **ECS Task** para treino  **[PDF]**

### ETAPA 4 — Testes + Lint  ·  Dev A   [PDF]
- [ ] `ruff` no `pyproject.toml`  **[PDF]**
- [ ] `tests/`: health, predict valido, vazio/longo/malformado (422), fixture mock  **[PDF]**
- [ ] `pytest -v` 100% verde  **[PDF]**

### ETAPA 5 — Dockerfile + baseline de latencia  ·  Dev B   [PDF]
- [ ] `Dockerfile` multi-stage, non-root, HEALTHCHECK em /health (imagem unica: inferencia e treino)  **[PDF]**
- [ ] `scripts/benchmark.py`: N requisicoes, p50/p95/p99, throughput  **[PDF: otimizacao]**
- [ ] `docs/latencia_baseline.md`: baseline do .pkl  **[PDF]**

### ETAPA 6 — CI/CD GitHub Actions  ·  Dev B   [PDF]
- [ ] `.github/workflows/ci.yml`: lint → test → build  **[PDF]**
- [ ] Build da imagem e push para **ECR**  **[EXT]**
- [ ] Badge no README  **[PDF]**

### ETAPA 7 — DAG Airflow (treino via ECS)  ·  Dev C   [PDF]
- [ ] `dags/retrain_triagem_dag.py`: `ingest >> train >> save`  **[PDF]**
- [ ] Task `train` dispara **ECS Fargate Task** (`EcsRunTaskOperator`) rodando `src/train.py`  **[EXT]**
- [ ] Task `save` versiona artefato no **S3** e atualiza `model.onnx` corrente  **[EXT]**
- [ ] `retries`, `retry_delay`, `catchup=False`; print do grafo verde em `docs/`  **[PDF]**

### ETAPA 8 — Monitoramento Prometheus + Grafana  ·  Dev B (apoio Dev A na instrumentacao)   [PDF 20%]
- [ ] `docker-compose.yml`: API + Prometheus + Grafana  **[PDF]**
- [ ] `monitoring/prometheus.yml`: scrape `api:8000/metrics`  **[PDF]**
- [ ] Grafana provisionado (datasource + dashboard)  **[PDF]**
- [ ] Dashboard >= 4 paineis: total requisicoes, latencia p95, taxa de erro, distribuicao por classe  **[PDF]**
- [ ] `monitoring/dashboard.json` versionado + print  **[PDF]**

### ETAPA 9 — Otimizacao ONNX + comparativo  ·  Dev C   [PDF 20%]
- [ ] `src/export_onnx.py`: converte pipeline → `model.onnx`  **[PDF]**
- [ ] Validacao de paridade sklearn vs ONNX (0 divergencias)  **[PDF]**
- [ ] Benchmark comparativo → `docs/latencia_comparativo.md`  **[PDF]**

### ETAPA 10 — Infra Terraform AWS  ·  Dev B   [EXT — tema central]
- [ ] `infra/modules/networking`: VPC, subnets, SG
- [ ] `infra/modules/s3`: buckets datasets + artefatos de modelo
- [ ] `infra/modules/ecr`: repositorio da imagem
- [ ] `infra/modules/ecs`: Service de inferencia (Fargate) + Task Definition de treino
- [ ] `infra/modules/alb`: Application Load Balancer → ECS Service
- [ ] `infra/modules/iam`: roles ECS task/service, acesso S3/ECR
- [ ] `infra/modules/monitoring`: log groups minimos (opcional)
- [ ] `infra/main.tf` compoe os modulos; `terraform apply`
- [ ] Smoke test na URL do ALB: `GET /health`, `POST /predict`

### ETAPA 11 — README final + Video STAR  ·  Dev A   [PDF: Docs 15% + Video 15%]
- [ ] README completo: arquitetura, execucao, latencia, CI/CD, monitoramento, deploy AWS, video
- [ ] Video STAR <= 5 min

---

## Distribuicao por participante

| Dev | Eixo | Etapas | Peso PDF |
|---|---|---|---|
| **Dev A — Alexandre** | Fundacao, API, Testes, Documentacao | 0, 3, 4, 11 (+ apoio instrumentacao na 8) | Documentacao 15% + Video 15% = 30% |
| **Dev B — Matheus Santos** | Infra, CI/CD, Observabilidade, Cloud (ECS/Terraform) | 5, 6, 8, 10 | CI/CD 15% + Monitoramento 20% = 35% |
| **Dev C — Matheus Ferreira** | Dataset, EDA, Modelo, Airflow, ONNX | 1, 2, 7, 9 | Modelagem 20% + Airflow 15% = 35% |

---

## Mapa de cobertura do PDF

| Requisito PDF | Etapa | Dev |
|---|---|---|
| CI/CD GitHub Actions (>=2 automacoes) | 6 | B |
| DAG Airflow (dados → treino → salvar) | 7 | C |
| Dockerfile funcional | 5 | B |
| Stack local API+Prometheus+Grafana | 8 | B/A |
| Scikit-Learn | 2 | C |
| FastAPI | 3 | A |
| Prometheus-client | 3 + 8 | A/B |
| Airflow | 7 | C |
| Dashboard Grafana >=3 paineis | 8 | B |
| Otimizacao (ONNX) | 9 | C |
| Video STAR <=5min | 11 | A |
| Decisao arquitetural cloud no README | 3 + 11 | A |

Todos os requisitos do `tech-challenge.md` cobertos. Etapas [EXT] (EDA, ECS, ALB, Terraform, S3) fortalecem o tema central "deploy de modelo em producao" sem conflitar com a rubrica.

## Projeto de ML completo — checagem

| Fase ML | Coberto | Onde |
|---|---|---|
| Problema definido | sim | tech-challenge.md |
| Ingestao de dados | sim | 2 + 7 (ingest) |
| EDA | sim | 1 |
| Feature engineering | sim | 2 |
| Treino | sim | 2 |
| Avaliacao (classification_report) | sim | 2 |
| Serializacao | sim | 2 |
| Empacotamento API | sim | 3 + 5 |
| Otimizacao inferencia | sim | 9 |
| Testes/qualidade | sim | 4 |
| CI/CD | sim | 6 |
| Orquestracao/retreino | sim | 7 |
| Deploy producao | sim | 10 |
| Monitoramento | sim | 8 |
| Documentacao | sim | 11 |
