# TODO — Dev A: Alexandre Araújo

**Eixo de responsabilidade:** Fundação do repositório, API, Testes e Documentação
**Etapas cobertas:** ETAPA 0 → ETAPA 3 → ETAPA 4 → ETAPA 11 (+ apoio na instrumentação da ETAPA 8)
**Peso na nota (PDF):** Documentação 15% + Vídeo STAR 15% = **30%**

> Arquitetura do projeto: **100% ECS + Fargate**. Inferência = ECS Fargate Service (FastAPI persistente) atrás de ALB, baixando `model.onnx` do S3 no startup. Treino = ECS Fargate Task. Monitoramento = Prometheus + Grafana. Sem Lambda, sem API Gateway.
> Fonte de verdade dos requisitos: `.docs/content/tech-challenge.md`. Plano de execução: `.docs/content/plan.md`.

---

## ETAPA 0 — Fundação do repositório

**Objetivo:** repositório pronto para os outros devs começarem em paralelo.

**Entregável:** repositório com estrutura de pastas, dependências, padrões e README esqueleto.

**Dependências:** nenhuma. Bloqueia ETAPA 1 (Dev C) e ETAPA 3 (a própria API do Dev A).

**Branch:** `etapa-0-fundacao-repo`

---

### Checklist

#### Repositório e estrutura
- [x] Criar repositório público; convidar os 3 devs com permissão `Write`
- [x] Estrutura de pastas (já criada) com `.gitkeep`: `app/`, `src/`, `dags/`, `tests/`, `data/raw/`, `data/processed/`, `models/`, `monitoring/grafana/provisioning/`, `scripts/`, `docs/`, `notebooks/`, `.github/workflows/`, `infra/modules/{networking,s3,ecr,ecs,alb,iam,monitoring}`

#### Arquivos de configuração raiz
- [x] `.gitignore`: `__pycache__/`, `*.pyc`, `.env`, `*.pkl`, `*.onnx`, `data/raw/*`, `data/processed/*` (com `!.gitkeep`), `.venv/`, `dist/`, `*.egg-info/`, `.terraform/`, `*.tfstate*`
- [x] `.dockerignore`: `.git`, `.venv`, `__pycache__`, `*.pyc`, `data/`, `tests/`, `.env`, `infra/`, `notebooks/`
- [x] `.env.example`: `MODEL_BUCKET=`, `MODEL_KEY=models/model.onnx`, `USE_ONNX=true`, `AWS_REGION=`, `LOG_LEVEL=INFO`

#### Dependências
- [x] `pyproject.toml` com todas as dependências fixadas:
  - runtime (`[project].dependencies`): `fastapi`, `uvicorn[standard]`, `scikit-learn`, `joblib`, `prometheus-client`, `onnxruntime`, `skl2onnx`, `numpy`, `pandas`, `boto3`
  - dev (`[project.optional-dependencies].dev`): `pytest`, `httpx`, `ruff`
- [x] Instalação documentada: `pip install -e ".[dev]"`

#### Padrões e README
- [x] `CONTRIBUTING.md`: Conventional Commits (`feat`/`fix`/`docs`/`chore`/`test`/`refactor`), branch `etapa-N-descricao`, PR obrigatório em `main`
- [x] Branch protection em `main`: require PR + status checks
- [x] README esqueleto: Visão Geral, Decisão Arquitetural, Pré-requisitos, Como Executar (local/Docker/Compose), Resultados de Latência, CI/CD, Monitoramento, Deploy em Produção, Vídeo STAR, Time
- [x] Commit inicial: `chore: initial repo structure and standards`; notificar Dev B e Dev C

### ✅ Definition of Done — ETAPA 0
- Repositório público acessível pelos 3 membros
- Estrutura completa rastreada pelo Git; `.gitignore`/`.dockerignore`/`.env.example` presentes
- `pyproject.toml` com dependências fixadas (runtime + dev); `CONTRIBUTING.md` + README esqueleto
- Dev B e Dev C notificados

---
---

## ETAPA 3 — API FastAPI (serviço de inferência)

**Objetivo:** API REST de triagem que recebe o texto do laudo e devolve a classificação de urgência. É o serviço que roda como ECS Fargate Service em produção e como container local na stack de monitoramento.

**Entregável:** `app/main.py` funcional + seção "Decisão Arquitetural" no `README.md`.

**Dependências:**
- Requer: ETAPA 0 (estrutura, `pyproject.toml`) e ETAPA 2 (`model.onnx`/`model.pkl` no S3 — até estar disponível, usar mock)
- Bloqueia: ETAPA 4 (testes) e ETAPA 5 (Dockerfile)

**Branch:** `etapa-3-api-fastapi`

---

### Checklist

#### Schemas Pydantic (`app/schemas.py`)
- [ ] `PredictRequest` com `texto: str` (validar não vazio, `max_length=5000`)
- [ ] `PredictResponse` com `classe` (`normal`/`atenção`/`urgente`), `confianca: float` (0.0–1.0), `tempo_ms: float`

#### Carregamento do modelo (`app/model_loader.py`)
- [ ] Baixar o artefato do **S3 no startup** (bucket/key via variável de ambiente `MODEL_BUCKET`/`MODEL_KEY`)
- [ ] Cachear localmente e carregar **uma única vez** no startup (não a cada request)
- [ ] Suportar `USE_ONNX` (true → `onnxruntime`; false → `.pkl` via joblib)
- [ ] Fallback: se o S3 não estiver acessível ou o modelo não existir, usar mock que responde `{"classe": "normal", "confianca": 1.0}`
- [ ] Logar (com `logging`) o modo ativo: modelo real (onnx/pkl) ou mock

#### Endpoints (`app/main.py`)
- [ ] `app = FastAPI(title="Triagem Médica API", version="1.0.0")`
- [ ] `@app.on_event("startup")` chama o `model_loader`
- [ ] `POST /predict`: recebe `PredictRequest`, mede tempo com `time.perf_counter()`, retorna `PredictResponse`; `HTTPException(422)` se texto vazio após strip
- [ ] `GET /health`: retorna `{"status": "ok", "model": "loaded"|"mock"}`, HTTP 200
- [ ] Logging estruturado com `logging.getLogger(__name__)` — **sem `print()`**
- [ ] Exemplo de request no schema para o Swagger (`/docs`)

#### Decisão arquitetural no README
- [ ] Análise **batch vs real-time**: por que triagem hospitalar exige resposta síncrona (real-time)
- [ ] Justificar **ECS Fargate + ALB** para inferência e **ECS Fargate Task** para treino (custo, container persistente, scrape do Prometheus, escalabilidade)
- [ ] Diagrama textual: `Client → ALB → ECS Fargate Service → model.onnx (do S3)`

#### Validação local
- [ ] `uvicorn app.main:app --reload` sobe sem erro
- [ ] `/docs` mostra os schemas; testar `POST /predict` e `GET /health`
- [ ] Confirmar ausência de `print()` — apenas logs estruturados

#### Finalização
- [ ] Commit: `feat(api): add /predict and /health endpoints`
- [ ] PR de `etapa-3-api-fastapi` → `main`

---

### ✅ Definition of Done — ETAPA 3
- `POST /predict` retorna `{classe, confianca, tempo_ms}` para laudo válido
- `GET /health` retorna 200
- Schemas rejeitam texto vazio com 422
- Modelo carregado do S3 no startup (com fallback mock) — sem `print()`
- Seção "Decisão Arquitetural" no README (real-time + ECS/ALB justificados)
- PR aberto e revisado

---
---

## ETAPA 4 — Testes automatizados e qualidade de código

**Objetivo:** suíte pytest + lint funcionando localmente, para a ETAPA 6 (CI/CD) apenas automatizar.

**Entregável:** `tests/` passando + `ruff` configurado no `pyproject.toml`.

**Dependências:** Requer ETAPA 3. Bloqueia ETAPA 6.

**Branch:** `etapa-4-testes-lint`

---

### Checklist

#### Lint e pytest (`pyproject.toml`)
- [ ] `[tool.ruff]` com `line-length = 88`, `select = ["E","F","W","I"]`, `exclude = ["dags/","data/"]`
- [ ] `ruff check app/ src/` → `All checks passed.`
- [ ] `[tool.pytest.ini_options]` com `testpaths = ["tests"]`; criar `tests/__init__.py`

#### Fixture mock (`tests/conftest.py`)
- [ ] Fixture `client` com `TestClient(app)` e override do `model_loader` por mock que retorna `("normal", 0.95)`
- [ ] **Testes não dependem do modelo real do S3 nem de `.pkl` local**

#### Testes (`tests/test_health.py`, `tests/test_predict.py`)
- [ ] `test_health_returns_200` + `test_health_body_has_status_key`
- [ ] `test_predict_valid_text_returns_valid_class` (classe ∈ 3 categorias, confianca 0–1, tempo_ms ≥ 0)
- [ ] `test_predict_empty_text_returns_422`
- [ ] `test_predict_blank_text_returns_422` (só espaços)
- [ ] `test_predict_missing_field_returns_422`
- [ ] `test_predict_text_too_long_returns_422` (6000 chars)

#### Validação e finalização
- [ ] `pytest -v` 100% (mínimo 7 testes) + `ruff check app/ src/` zero erros
- [ ] Anotar comandos para a ETAPA 6: `ruff check app/ src/` e `pytest -v`
- [ ] Commit: `test(api): add pytest suite and ruff lint config`; PR → `main`

---

### ✅ Definition of Done — ETAPA 4
- `pytest -v` 100% (≥7 testes), `ruff check` zero erros
- Nenhum teste usa modelo real — só fixture mock
- Comandos de lint/teste documentados para o Dev B
- PR aberto e revisado

---
---

## ETAPA 11 — Consolidação final: README e vídeo STAR

**Objetivo:** README completo e coerente + vídeo STAR ≤ 5 min.

**Entregável:** `README.md` final + link do vídeo funcional.

**Dependências:** Requer todas as etapas anteriores (especialmente ETAPA 9 para latência e ETAPA 10 para a URL do ALB). Bloqueia a submissão.

**Branch:** `etapa-11-readme-video`

---

### Checklist

#### README
- [ ] Seções: Decisão Arquitetural (ECS/ALB, atualizada com o deploy real), Como Executar, Resultados de Latência (tabela da ETAPA 9), CI/CD (badge + link Actions), Monitoramento (print Grafana), Deploy em Produção (URL do ALB da ETAPA 10 + passo a passo), Vídeo
- [ ] Três modos de execução documentados e testados:
  - Local: `pip install -e ".[dev]" && uvicorn app.main:app --reload`
  - Docker isolado: `docker build -t triagem-api . && docker run -p 8000:8000 triagem-api`
  - Stack completa: `docker compose up`
- [ ] Todos os comandos testados copiando e colando

#### Roteiro STAR
- [ ] **S (~45s):** problema clínico — triagem automática de laudos, volume alto, risco de atraso
- [ ] **T (~45s):** requisitos — latência, CI/CD, monitoramento Grafana, retreino Airflow
- [ ] **A (~2min):** arquitetura ECS/Fargate, CI/CD verde, `docker compose up` com Grafana, DAG Airflow verde, comparativo sklearn vs ONNX
- [ ] **R (~45s):** números — latência p95, ganho ONNX, URL do ALB funcionando, lições

#### Gravação
- [ ] Vídeo ≤ 5 min, publicado, link testado em aba anônima, inserido no README
- [ ] Commit: `docs: finalize README and add video link`; PR → `main`

---

### ✅ Definition of Done — ETAPA 11
- README com todas as seções preenchidas, comandos testados, sem links quebrados
- Vídeo ≤ 5 min (STAR), link acessível em aba anônima
- Repositório público com merges concluídos

---

## Apoio — Instrumentação da ETAPA 8 (com Dev B)
- [ ] Adicionar `prometheus_client` em `app/main.py`: Counter de requisições (label `classe_predita`), Histogram de latência, Counter de erros
- [ ] Expor `/metrics` (`make_asgi_app` montado em `/metrics`)
- [ ] Confirmar que `curl localhost:8000/metrics` retorna formato Prometheus antes de Dev B configurar o scrape

---

## ⚠️ Pontos em aberto — Dev A
- [ ] Limite de tamanho do texto: 5.000 caracteres (sugerido) — confirmar com o time
- [ ] Plataforma do vídeo: confirmar se YouTube é aceito
- [ ] Variáveis de ambiente do S3 (`MODEL_BUCKET`/`MODEL_KEY`): alinhar nomes com Dev B (Terraform/ECS)
