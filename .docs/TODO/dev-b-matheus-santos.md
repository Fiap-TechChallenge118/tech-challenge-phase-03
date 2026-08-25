# TODO — Dev B: Matheus Santos

**Eixo de responsabilidade:** Infraestrutura, CI/CD, Observabilidade e Cloud
**Fases cobertas:** FASE 0 → FASE 3 → FASE 5 → FASE 7 → FASE 9
**Peso na nota (PDF):** CI/CD 15% + Monitoramento 20% = **35%**

---

## FASE 0 — Fundação do repositório e padrões de trabalho

**Etapa PDF:** (sem etapa correspondente — pré-requisito universal)

**Objetivo:** Deixar o repositório pronto para os outros dois devs começarem em paralelo, sem conflito de estrutura ou convenções.

**Entregável:** Repositório GitHub público com estrutura de pastas, branch protection e padrão de commit definido.

**Dependências:**
- Requer: nada (ponto de partida)
- Bloqueia: FASE 1 (Dev C) e FASE 2 (Dev A)

**Branch:** `fase-0-fundacao-repo` (depois mergear em `main` como commit inicial)

---

### Checklist

#### Criação e configuração do repositório
- [ ] Criar repositório público no GitHub com nome definido pelo time (ex.: `tech-challenge-03`)
- [ ] Convidar os 3 membros como colaboradores com permissão de `Write`
- [ ] Não inicializar com README via interface do GitHub — fazer o primeiro commit manualmente

#### Estrutura de pastas
- [ ] Criar as seguintes pastas com um `.gitkeep` em cada uma para o Git rastrear:
  ```
  app/
  src/
  dags/
  tests/
  data/raw/
  data/processed/
  models/
  monitoring/
  docs/
  scripts/
  .github/workflows/
  ```
- [ ] Confirmar que todas as pastas aparecem no `git status`

#### Arquivos de configuração raiz
- [ ] Criar `.gitignore` incluindo ao menos:
  ```
  __pycache__/
  *.pyc
  .env
  *.pkl
  *.onnx
  data/raw/*
  data/processed/*
  !data/raw/.gitkeep
  !data/processed/.gitkeep
  .venv/
  dist/
  *.egg-info/
  ```
- [ ] Criar `.dockerignore` incluindo ao menos:
  ```
  .git
  .venv
  __pycache__
  *.pyc
  data/
  tests/
  .env
  ```
- [ ] Criar `.env.example` com as variáveis de ambiente esperadas:
  ```
  MODEL_PATH=models/model.pkl
  USE_ONNX=false
  LOG_LEVEL=INFO
  ```

#### Dependências (`requirements.txt`)
- [ ] Criar `requirements.txt` com versões **fixadas** (usar `==`):
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.29.0
  scikit-learn==1.4.2
  joblib==1.4.2
  prometheus-client==0.20.0
  onnxruntime==1.18.0
  skl2onnx==1.17.0
  numpy==1.26.4
  pandas==2.2.2
  ```
- [ ] Criar `requirements-dev.txt` para dependências de desenvolvimento:
  ```
  pytest==8.2.0
  httpx==0.27.0
  ruff==0.4.4
  ```

#### Padrão de commits e contribuição (`CONTRIBUTING.md`)
- [ ] Criar `CONTRIBUTING.md` com as seguintes seções:
  - [ ] **Conventional Commits:** tipos aceitos: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`
  - [ ] **Formato:** `tipo(escopo): descrição curta` — ex.: `feat(api): add /predict endpoint`
  - [ ] **Branch strategy:** `main` protegida + feature branches com padrão `fase-N-descricao-curta`
  - [ ] **PR obrigatório:** nenhum merge direto em `main`

#### Branch protection no GitHub
- [ ] Acessar Settings → Branches → Add rule para `main`:
  - [ ] Habilitar "Require a pull request before merging"
  - [ ] Habilitar "Require status checks to pass" (adicionar o workflow CI quando existir)
  - [ ] Habilitar "Do not allow bypassing the above settings"

#### README esqueleto (`README.md`)
- [ ] Criar `README.md` com as seguintes seções **vazias** (títulos e subtítulos, sem conteúdo ainda):
  ```markdown
  # Triagem Médica — Sistema de Classificação de Urgência
  ## Visão Geral
  ## Decisão Arquitetural
  ## Pré-requisitos
  ## Como Executar
  ### Desenvolvimento local
  ### Docker isolado
  ### Stack completa (Docker Compose)
  ## Resultados de Latência
  ## CI/CD
  ## Monitoramento
  ## Deploy em Produção
  ## Vídeo STAR
  ## Time
  ```

#### Primeiro commit
- [ ] Fazer o commit inicial: `chore: initial repo structure and standards`
- [ ] Fazer push para `main`
- [ ] Comunicar ao Dev A e Dev C que podem criar suas branches

---

### ✅ Definition of Done — FASE 0
- Repositório público acessível pelos 3 membros
- Estrutura de pastas completa e rastreada pelo Git
- `.gitignore`, `.dockerignore` e `.env.example` presentes
- `requirements.txt` com versões fixadas
- `CONTRIBUTING.md` com padrão de commits e branch strategy
- README esqueleto com todas as seções (vazias)
- Dev A e Dev C notificados para começar

---

---

## FASE 3 — Containerização da API e baseline de latência

**Etapa PDF:** Etapa 1 — Decisão Arquitetural e API Inicial

**Objetivo:** Empacotar a API em Docker e registrar o baseline de latência local, número que será comparado contra o modelo ONNX na FASE 8.

**Entregável:** `Dockerfile` funcional + tabela de baseline (p50/p95/p99) em `docs/latencia_baseline.md`.

**Dependências:**
- Requer: FASE 1 (`models/model.pkl` gerado) e FASE 2 (`app/main.py` pronto)
- Bloqueia: FASE 5 (Dockerfile necessário para o job de build), FASE 7 (compose usa esta imagem) e FASE 8 (baseline é o ponto de comparação)

**Branch:** `fase-3-docker-baseline`

---

### Checklist

#### Dockerfile multi-stage
- [ ] Criar `Dockerfile` na raiz com dois estágios:
  ```dockerfile
  # Estágio 1: builder
  FROM python:3.11-slim AS builder
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir --upgrade pip \
      && pip install --no-cache-dir -r requirements.txt

  # Estágio 2: runtime
  FROM python:3.11-slim AS runtime
  WORKDIR /app
  # Copiar dependências instaladas do builder
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY --from=builder /usr/local/bin /usr/local/bin
  # Copiar código e artefato
  COPY app/ ./app/
  COPY models/ ./models/
  # Usuário não-root
  RUN useradd -m appuser && chown -R appuser /app
  USER appuser
  EXPOSE 8000
  HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- [ ] Confirmar que o `Dockerfile` usa `python:3.11-slim` (não `python:3.11` completo)
- [ ] Verificar que o `.dockerignore` exclui `data/`, `tests/`, `.git` e `.venv`

#### Build e validação da imagem
- [ ] Buildar a imagem: `docker build -t triagem-api:latest .`
- [ ] Registrar o tamanho da imagem: `docker images triagem-api:latest`
- [ ] Subir o container: `docker run -p 8000:8000 triagem-api:latest`
- [ ] Validar `GET /health` respondendo dentro do container:
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Validar `POST /predict` com laudo real:
  ```bash
  curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"texto": "Paciente com dor torácica intensa e sudorese"}'
  ```
- [ ] Confirmar que o processo roda como usuário não-root: `docker exec <id> whoami`

#### Script de benchmark (`scripts/benchmark.py`)
- [ ] Criar `scripts/benchmark.py` com as seguintes funcionalidades:
  - [ ] Parâmetro `--n` para número de requisições (padrão: 500)
  - [ ] Parâmetro `--url` para o endpoint (padrão: `http://localhost:8000/predict`)
  - [ ] Enviar N requisições **sequenciais** com o mesmo payload de laudo de teste
  - [ ] Coletar latência de cada requisição individualmente
  - [ ] Calcular e imprimir: p50, p95, p99 (em ms) e throughput (req/s)
  - [ ] Salvar os resultados brutos em `docs/benchmark_raw.json`
- [ ] Rodar o benchmark com o container ativo:
  ```bash
  python scripts/benchmark.py --n 500 --url http://localhost:8000/predict
  ```

#### Documentação do baseline (`docs/latencia_baseline.md`)
- [ ] Criar `docs/latencia_baseline.md` com:
  - [ ] Tabela com colunas: `Métrica | Valor (ms)`
    - p50, p95, p99 e Throughput (req/s)
  - [ ] Especificação da máquina de teste: CPU, RAM, OS
  - [ ] Versão da imagem Docker usada
  - [ ] Data/hora da medição
  - [ ] Nota: "Este é o baseline do modelo `.pkl`. Será comparado com ONNX na FASE 8."

#### Finalização
- [ ] Commitar: `feat(docker): add multi-stage Dockerfile and latency baseline`
- [ ] Abrir PR de `fase-3-docker-baseline` → `main`

---

### ✅ Definition of Done — FASE 3
- `docker build` e `docker run` funcionam sem erro
- Container roda como usuário não-root
- `/health` e `/predict` respondem corretamente de dentro do container
- Tamanho da imagem registrado
- `docs/latencia_baseline.md` com tabela p50/p95/p99 e specs da máquina
- PR aberto e revisado

---

---

## FASE 5 — Pipeline CI/CD no GitHub Actions (lint → test → build)

**Etapa PDF:** Etapa 2 — CI/CD e Pipeline Automatizado

**Objetivo:** Automatizar lint, testes e build da imagem Docker a cada push/PR, garantindo que o repositório esteja sempre em estado deployável.

**Entregável:** `.github/workflows/ci.yml` rodando verde + badge de status no README.

**Dependências:**
- Requer: FASE 3 (Dockerfile pronto) e FASE 4 (testes e lint configurados pelo Dev A)
- Bloqueia: FASE 9 (deploy usa imagem publicada pelo CI)

**Branch:** `fase-5-ci-github-actions`

---

### Checklist

#### Workflow CI (`/.github/workflows/ci.yml`)
- [ ] Criar o arquivo `.github/workflows/ci.yml`
- [ ] Configurar triggers:
  ```yaml
  on:
    push:
      branches: [main, "fase-*"]
    pull_request:
      branches: [main]
  ```
- [ ] Definir 3 jobs na sequência:

**Job 1 — lint:**
- [ ] `runs-on: ubuntu-latest`
- [ ] Step: `actions/checkout@v4`
- [ ] Step: `actions/setup-python@v5` com `python-version: '3.11'`
- [ ] Step: cache de dependências (`actions/cache@v4` para `~/.cache/pip`)
- [ ] Step: `pip install ruff==0.4.4`
- [ ] Step: `ruff check app/ src/`

**Job 2 — test:**
- [ ] `needs: lint` (só executa se lint passar)
- [ ] `runs-on: ubuntu-latest`
- [ ] Steps: checkout, setup-python, cache
- [ ] Step: `pip install -r requirements.txt -r requirements-dev.txt`
- [ ] Step: `pytest -v`

**Job 3 — build:**
- [ ] `needs: test` (só executa se testes passarem)
- [ ] `runs-on: ubuntu-latest`
- [ ] Step: checkout
- [ ] Step: `actions/setup-buildx-action@v3` (para build eficiente)
- [ ] Step: `docker/login-action@v3` com `registry: ghcr.io`, usando `GITHUB_TOKEN`
  - [ ] Condicionado a: `if: github.ref == 'refs/heads/main'`
- [ ] Step: build da imagem:
  ```bash
  docker build -t ghcr.io/${{ github.repository }}:latest .
  ```
- [ ] Step: push para GHCR (apenas na branch `main`):
  ```bash
  docker push ghcr.io/${{ github.repository }}:latest
  ```

#### Validação do workflow
- [ ] Fazer push em uma branch de teste e confirmar que o workflow dispara
- [ ] Verificar que os 3 jobs aparecem verdes na aba "Actions" do GitHub
- [ ] Salvar print da execução verde (será usado no vídeo STAR)

#### Badge no README
- [ ] Obter a URL do badge na aba Actions → escolher o workflow → "Create status badge"
- [ ] Inserir o badge no topo do `README.md`:
  ```markdown
  ![CI](https://github.com/ORG/REPO/actions/workflows/ci.yml/badge.svg)
  ```

#### Finalização
- [ ] Commitar: `ci: add GitHub Actions workflow (lint, test, build, push)`
- [ ] Abrir PR de `fase-5-ci-github-actions` → `main`

---

### ✅ Definition of Done — FASE 5
- Workflow com 3 jobs (lint → test → build) rodando verde no GitHub Actions
- Push para GHCR funcionando na branch `main`
- Badge de status visível no README
- Print da execução verde salvo para o vídeo

---

---

## FASE 7 — Stack de observabilidade: Prometheus + Grafana

**Etapa PDF:** Etapa 3 — Monitoramento e Observabilidade

**Objetivo:** Subir a stack completa de observabilidade com um único `docker compose up`, com dashboard Grafana exibindo ao menos 4 painéis com dados reais.

**Entregável:** `docker-compose.yml` + `monitoring/prometheus.yml` + `monitoring/dashboard.json` + print do dashboard populado.

**Dependências:**
- Requer: FASE 3 (imagem da API construída)
- Apoio: Dev A adiciona a instrumentação `prometheus_client` na API (alinhar antes de começar)
- Bloqueia: FASE 9 (compose validado é base do deploy)

**Branch:** `fase-7-monitoramento-stack`

---

### Checklist

#### Instrumentação da API (em conjunto com Dev A)
- [ ] Verificar com Dev A se `/metrics` já foi adicionado em `app/main.py`
- [ ] Caso não esteja, adicionar em `app/main.py`:
  ```python
  from prometheus_client import Counter, Histogram, make_asgi_app
  import time

  REQUEST_COUNT = Counter(
      "triagem_requests_total",
      "Total de requisições ao /predict",
      ["classe_predita", "status"]
  )
  REQUEST_LATENCY = Histogram(
      "triagem_request_latency_seconds",
      "Latência das requisições ao /predict",
      buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
  )
  ERROR_COUNT = Counter(
      "triagem_errors_total",
      "Total de erros no /predict"
  )
  ```
- [ ] Montar a app de métricas e adicionar rota `/metrics`:
  ```python
  metrics_app = make_asgi_app()
  app.mount("/metrics", metrics_app)
  ```
- [ ] Atualizar o endpoint `/predict` para chamar `REQUEST_COUNT.inc(...)`, `REQUEST_LATENCY.observe(...)` e `ERROR_COUNT.inc(...)` nas situações corretas
- [ ] Testar localmente: `curl http://localhost:8000/metrics` deve retornar métricas no formato Prometheus

#### Configuração do Prometheus (`monitoring/prometheus.yml`)
- [ ] Criar `monitoring/prometheus.yml`:
  ```yaml
  global:
    scrape_interval: 15s

  scrape_configs:
    - job_name: 'triagem-api'
      static_configs:
        - targets: ['api:8000']
      metrics_path: '/metrics'
  ```

#### Docker Compose (`docker-compose.yml`)
- [ ] Criar `docker-compose.yml` na raiz com os 3 serviços:

**Serviço `api`:**
- [ ] `build: .` (ou `image: ghcr.io/...`)
- [ ] `ports: ["8000:8000"]`
- [ ] `env_file: .env`
- [ ] `healthcheck` apontando para `/health`
- [ ] `networks: [monitoring]`

**Serviço `prometheus`:**
- [ ] `image: prom/prometheus:v2.52.0`
- [ ] `volumes: ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"]`
- [ ] `ports: ["9090:9090"]`
- [ ] `depends_on: [api]`
- [ ] `networks: [monitoring]`

**Serviço `grafana`:**
- [ ] `image: grafana/grafana:10.4.2`
- [ ] `ports: ["3000:3000"]`
- [ ] `environment: GF_SECURITY_ADMIN_PASSWORD=admin`
- [ ] `volumes: ["./monitoring/grafana/provisioning:/etc/grafana/provisioning"]`
- [ ] `depends_on: [prometheus]`
- [ ] `networks: [monitoring]`

- [ ] Definir a network:
  ```yaml
  networks:
    monitoring:
      driver: bridge
  ```

#### Provisionamento automático do Grafana
- [ ] Criar `monitoring/grafana/provisioning/datasources/prometheus.yml`:
  ```yaml
  apiVersion: 1
  datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus:9090
      isDefault: true
  ```
- [ ] Criar `monitoring/grafana/provisioning/dashboards/dashboard.yml`:
  ```yaml
  apiVersion: 1
  providers:
    - name: default
      folder: ''
      type: file
      options:
        path: /etc/grafana/provisioning/dashboards
  ```

#### Dashboard Grafana (4 painéis obrigatórios)
- [ ] Subir a stack: `docker compose up`
- [ ] Acessar `http://localhost:3000` (admin/admin)
- [ ] Criar dashboard com os 4 painéis:
  - [ ] **Painel 1 — Total de requisições:** `triagem_requests_total` (stat ou time series)
  - [ ] **Painel 2 — Latência p95:** `histogram_quantile(0.95, rate(triagem_request_latency_seconds_bucket[5m]))` (gauge)
  - [ ] **Painel 3 — Taxa de erros:** `rate(triagem_errors_total[5m])` (time series)
  - [ ] **Painel 4 — Distribuição por classe:** `triagem_requests_total` com label `classe_predita` (bar chart ou pie)
- [ ] Gerar carga com o benchmark: `python scripts/benchmark.py --n 200`
- [ ] Confirmar que todos os 4 painéis exibem dados reais
- [ ] Tirar print/screenshot do dashboard com dados visíveis

#### Exportação do dashboard
- [ ] Acessar o dashboard no Grafana → Share → Export → Export for sharing externally
- [ ] Salvar o JSON em `monitoring/dashboard.json`
- [ ] Mover o arquivo `monitoring/dashboard.json` para `monitoring/grafana/provisioning/dashboards/dashboard.json` para provisionamento automático

#### Finalização
- [ ] Commitar: `feat(monitoring): add docker-compose with Prometheus and Grafana`
- [ ] Abrir PR de `fase-7-monitoramento-stack` → `main`

---

### ✅ Definition of Done — FASE 7
- `docker compose up` sobe os 3 serviços sem passo manual
- `/metrics` expõe dados no formato Prometheus
- Dashboard com 4 painéis exibindo dados reais após gerar carga
- `monitoring/dashboard.json` versionado no repositório
- Print do dashboard salvo em `docs/`

---

---

## FASE 9 — Deploy do serviço de inferência em produção (cloud)

**Etapa PDF:** (tema central do desafio — bônus de diferenciação)

**Objetivo:** Colocar o modelo em produção com URL pública acessível para a banca testar.

**Entregável:** URL pública respondendo em `/docs` e `/predict` + seção de deploy no README.

**Dependências:**
- Requer: FASE 5 (imagem publicada no GHCR) e FASE 7 (compose validado)
- Bloqueia: FASE 10 (README final precisa da URL)

**Branch:** `fase-9-deploy-cloud`

---

### Checklist

#### Escolha do serviço de deploy
- [ ] Confirmar com o time o serviço escolhido — deve ser **o mesmo** citado na análise arquitetural da FASE 2 (Dev A)
- [ ] Opções recomendadas (escolher 1):
  - [ ] **Google Cloud Run** — aceita imagem de container, escala a zero, free tier generoso
  - [ ] **Azure Container Apps** — similar ao Cloud Run
  - [ ] **AWS App Runner** — integra com ECR/GHCR, simples de configurar
  - [ ] **Render** — mais simples, deploy direto do GHCR sem configuração de cloud provider

#### Provisionamento do serviço
- [ ] Criar conta/projeto no serviço escolhido (se ainda não existir)
- [ ] Apontar o serviço para a imagem publicada no GHCR: `ghcr.io/ORG/REPO:latest`
- [ ] Configurar as variáveis de ambiente no serviço (não hardcoded):
  - `MODEL_PATH=models/model.pkl`
  - `USE_ONNX=false` (ou `true` se FASE 8 já estiver concluída)
  - `LOG_LEVEL=INFO`
- [ ] Definir limites de recurso:
  - CPU: mínimo 0.5 vCPU
  - Memória: mínimo 512 MB
- [ ] Configurar healthcheck apontando para `/health`
- [ ] Definir número mínimo de instâncias: 1 (para evitar cold start no smoke test da banca)

#### Smoke test na URL pública
- [ ] Testar `GET https://<URL>/health` → deve retornar HTTP 200
- [ ] Testar `GET https://<URL>/docs` → deve carregar o Swagger UI
- [ ] Testar `POST https://<URL>/predict` com laudo real:
  ```bash
  curl -X POST https://<URL>/predict \
    -H "Content-Type: application/json" \
    -d '{"texto": "Paciente inconsciente com queda de pressão arterial"}'
  ```
- [ ] Confirmar resposta com `classe`, `confianca` e `tempo_ms`

#### Medição de latência em produção
- [ ] Rodar `scripts/benchmark.py --n 100 --url https://<URL>/predict`
- [ ] Registrar p50/p95/p99 em produção
- [ ] Comparar com latência local e anotar a diferença de rede em `docs/latencia_baseline.md`

#### Documentação no README
- [ ] Inserir a URL pública na seção "Deploy em Produção" do README
- [ ] Documentar o passo a passo de deploy (serviço usado, configurações, comandos)
- [ ] Documentar o procedimento de rollback (como voltar para a versão anterior)

#### Finalização
- [ ] Commitar: `docs: add production URL and deploy instructions`
- [ ] Abrir PR de `fase-9-deploy-cloud` → `main`

---

### ✅ Definition of Done — FASE 9
- URL pública acessível e respondendo `/health`, `/docs` e `/predict`
- Smoke test executado com sucesso (sem erros)
- Latência em produção medida e documentada
- README com URL pública e passo a passo de deploy/rollback
- Nenhum segredo hardcoded no repositório

---

## ⚠️ Pontos em aberto — Dev B

- [ ] **Serviço de deploy (FASE 9):** qual provedor usar? Deve ser o mesmo que Dev A citar na análise arquitetural da FASE 2. Alinhar antes da FASE 2 ser escrita.
- [ ] **Instrumentação da API (FASE 7):** o plan.md coloca a instrumentação com `prometheus_client` como responsabilidade do Dev B com "apoio do Dev A". Definir quem escreve o código de métricas antes de começar a FASE 7.
- [ ] **Versões das imagens Docker no Compose:** as versões sugeridas aqui (`prom/prometheus:v2.52.0`, `grafana/grafana:10.4.2`) são sugestões. Confirmar com o time se prefere `latest` ou versões fixadas.
- [ ] **GHCR público ou privado:** se o repositório GitHub for público, o GHCR pode requerer configuração extra para pull anônimo. Verificar nas configurações do pacote.
