# TODO — Dev B: Matheus Santos

**Eixo de responsabilidade:** Infraestrutura, CI/CD, Observabilidade e Cloud (ECS/Fargate + Terraform)
**Etapas cobertas:** ETAPA 5 → ETAPA 6 → ETAPA 8 → ETAPA 10
**Peso na nota (PDF):** CI/CD 15% + Monitoramento 20% = **35%**

> Arquitetura do projeto: **100% ECS + Fargate**. Inferência = ECS Fargate Service (FastAPI) atrás de ALB, baixando `model.onnx` do S3 no startup. Treino = ECS Fargate Task disparada pela DAG. Imagem única no ECR. Monitoramento = Prometheus + Grafana. Sem Lambda/API Gateway. Terraform único (sem ambientes).
> A ETAPA 0 (Fundação do repositório) foi transferida para o Dev A.
> Fonte de verdade: `.docs/content/tech-challenge.md`. Plano: `.docs/content/plan.md`.

---

## ETAPA 5 — Dockerfile e baseline de latência

**Objetivo:** empacotar a API em Docker (imagem única para inferência e treino) e registrar o baseline de latência.

**Entregável:** `Dockerfile` funcional + `docs/latencia_baseline.md`.

**Dependências:** Requer ETAPA 2 (modelo) e ETAPA 3 (`app/main.py`). Bloqueia ETAPA 6, 8 e 9.

**Branch:** `etapa-5-docker-baseline`

---

### Checklist

#### Dockerfile
- [ ] Multi-stage (builder + runtime) com `python:3.11-slim`
- [ ] Copiar `app/` e `src/` (a mesma imagem serve inferência e treino via override de comando)
- [ ] Usuário não-root; `EXPOSE 8000`
- [ ] `HEALTHCHECK` para `/health`
- [ ] `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` (default = inferência)
- [ ] `.dockerignore` exclui `data/`, `tests/`, `infra/`, `.git`, `.venv`

#### Build e validação
- [ ] `docker build -t triagem-api:latest .` + registrar tamanho da imagem
- [ ] `docker run -p 8000:8000` → validar `/health` e `POST /predict` dentro do container
- [ ] Confirmar processo como não-root (`docker exec <id> whoami`)

#### Benchmark (`scripts/benchmark.py`)
- [ ] Args `--n` (default 500) e `--url` (default `http://localhost:8000/predict`)
- [ ] N requisições sequenciais, coletar latência individual
- [ ] Calcular p50/p95/p99 (ms) + throughput (req/s); salvar bruto em `docs/benchmark_raw.json`

#### Documentação e finalização
- [ ] `docs/latencia_baseline.md`: tabela p50/p95/p99 + throughput, specs da máquina, versão da imagem, data
- [ ] Nota: "baseline do `.pkl`; comparado com ONNX na ETAPA 9"
- [ ] Commit: `feat(docker): add multi-stage Dockerfile and latency baseline`; PR → `main`

### ✅ Definition of Done — ETAPA 5
- `docker build`/`run` sem erro, container não-root, `/health` e `/predict` respondendo
- Tamanho da imagem registrado; `docs/latencia_baseline.md` com tabela e specs
- PR aberto e revisado

---
---

## ETAPA 6 — CI/CD GitHub Actions (lint → test → build → push ECR)

**Objetivo:** automatizar lint, testes e build/push da imagem para o ECR a cada push/PR.

**Entregável:** `.github/workflows/ci.yml` verde + badge no README.

**Dependências:** Requer ETAPA 5 (Dockerfile) e ETAPA 4 (testes/lint, Dev A). Bloqueia ETAPA 10 (deploy usa a imagem do ECR).

**Branch:** `etapa-6-ci-github-actions`

---

### Checklist

#### Workflow (`.github/workflows/ci.yml`)
- [ ] Triggers: `push` em `[main, "etapa-*"]` e `pull_request` em `[main]`
- [ ] **Job lint:** checkout, `setup-python@3.11`, cache pip, `pip install ruff`, `ruff check app/ src/`
- [ ] **Job test** (`needs: lint`): `pip install -e ".[dev]"`, `pytest -v`
- [ ] **Job build** (`needs: test`): checkout, buildx, login no **ECR** (`aws-actions/configure-aws-credentials` + `amazon-ecr-login`), `docker build`, `docker push` — condicionado a `if: github.ref == 'refs/heads/main'`
- [ ] Secrets AWS configurados no repositório (nada hardcoded)

#### Validação e badge
- [ ] Push de teste dispara o workflow; 3 jobs verdes na aba Actions
- [ ] Print da execução verde (para o vídeo)
- [ ] Badge do workflow no topo do README
- [ ] Commit: `ci: add GitHub Actions workflow (lint, test, build, push ECR)`; PR → `main`

### ✅ Definition of Done — ETAPA 6
- 3 jobs (lint → test → build) verdes no Actions
- Push para ECR funcionando na `main`
- Badge no README; print salvo

---
---

## ETAPA 8 — Monitoramento: Prometheus + Grafana

**Objetivo:** stack de observabilidade com `docker compose up`, dashboard Grafana com ≥4 painéis.

**Entregável:** `docker-compose.yml` + `monitoring/prometheus.yml` + `monitoring/dashboard.json` + print.

**Dependências:** Requer ETAPA 5. Apoio: Dev A instrumenta a API com `prometheus_client`.

**Branch:** `etapa-8-monitoramento-stack`

---

### Checklist

#### Instrumentação (com Dev A)
- [ ] Confirmar `/metrics` exposto em `app/main.py` (Counter req com label `classe_predita`, Histogram latência, Counter erros)
- [ ] `curl localhost:8000/metrics` retorna formato Prometheus

#### Prometheus (`monitoring/prometheus.yml`)
- [ ] `scrape_interval: 15s`; `job triagem-api` → target `api:8000`, `metrics_path: /metrics`

#### Docker Compose (`docker-compose.yml`)
- [ ] Serviço `api`: `build: .`, `ports 8000:8000`, `env_file .env`, healthcheck `/health`, network `monitoring`
- [ ] Serviço `prometheus`: `prom/prometheus`, volume do `prometheus.yml`, `ports 9090:9090`, `depends_on api`
- [ ] Serviço `grafana`: `grafana/grafana`, `ports 3000:3000`, `GF_SECURITY_ADMIN_PASSWORD=admin`, volume de provisioning, `depends_on prometheus`
- [ ] Network `monitoring` (bridge)

#### Provisionamento e dashboard
- [ ] `monitoring/grafana/provisioning/datasources/prometheus.yml` (datasource Prometheus default)
- [ ] `monitoring/grafana/provisioning/dashboards/dashboard.yml` (provider file)
- [ ] Dashboard com 4 painéis: total requisições, latência p95 (`histogram_quantile`), taxa de erro (`rate`), distribuição por classe (label `classe_predita`)
- [ ] Gerar carga (`scripts/benchmark.py --n 200`) e confirmar painéis com dados
- [ ] Exportar JSON → `monitoring/dashboard.json` (e provisioning); print em `docs/`
- [ ] Commit: `feat(monitoring): add docker-compose with Prometheus and Grafana`; PR → `main`

### ✅ Definition of Done — ETAPA 8
- `docker compose up` sobe os 3 serviços sem passo manual
- `/metrics` em formato Prometheus; dashboard com 4 painéis com dados reais
- `monitoring/dashboard.json` versionado; print salvo

---
---

## ETAPA 10 — Infra Terraform AWS (ECS/Fargate)

**Objetivo:** provisionar a infra AWS via Terraform — serviço de inferência (ECS Service + ALB) e treino (ECS Task), com imagem no ECR e artefatos no S3.

**Entregável:** `infra/` aplicável (`terraform apply`) + URL pública do ALB respondendo + seção de deploy no README.

**Dependências:** Requer ETAPA 6 (imagem no ECR) e ETAPA 8 (compose validado). Bloqueia ETAPA 11.

**Branch:** `etapa-10-infra-terraform`

---

### Checklist

#### Módulos Terraform (`infra/modules/`)
- [ ] `networking`: VPC, subnets públicas/privadas, security groups (ALB → ECS)
- [ ] `s3`: bucket de datasets (raw/processed) + bucket de artefatos de modelo
- [ ] `ecr`: repositório da imagem única
- [ ] `iam`: execution role + task role do ECS (acesso a S3, ECR, CloudWatch Logs)
- [ ] `ecs`:
  - Cluster Fargate
  - **Service de inferência**: Task Definition (imagem ECR, env `MODEL_BUCKET`/`MODEL_KEY`/`USE_ONNX`), desired_count ≥ 1, healthcheck `/health`
  - **Task Definition de treino**: mesma imagem, comando override `python src/train.py`
- [ ] `alb`: Application Load Balancer + target group + listener → ECS Service
- [ ] `monitoring`: log groups (opcional)

#### Composição e apply
- [ ] `infra/main.tf` compõe os módulos; `variables.tf`, `outputs.tf` (expor DNS do ALB, nomes de bucket, repo ECR)
- [ ] `backend.tf`: state remoto no S3 (recomendado) ou local para a demo
- [ ] `terraform init` + `terraform plan` + `terraform apply`

#### Smoke test e documentação
- [ ] `GET http://<alb-dns>/health` → 200; `GET /docs` carrega; `POST /predict` com laudo real retorna `{classe, confianca, tempo_ms}`
- [ ] Rodar `scripts/benchmark.py --n 100 --url http://<alb-dns>/predict`; registrar latência de produção em `docs/latencia_baseline.md`
- [ ] README: URL do ALB + passo a passo de deploy (`terraform apply`) e rollback
- [ ] Commit: `feat(infra): add Terraform for ECS/Fargate, ALB, ECR, S3`; PR → `main`

### ✅ Definition of Done — ETAPA 10
- `terraform apply` provisiona a stack sem erro
- URL do ALB respondendo `/health`, `/docs`, `/predict`
- ECS Service baixa o modelo do S3 e serve inferência
- Nenhum segredo hardcoded; README com URL e deploy/rollback
- PR aberto e revisado

---

## ⚠️ Pontos em aberto — Dev B
- [ ] Backend do Terraform state: S3 remoto (recomendado) vs local para a demo — decidir
- [ ] Nomes das variáveis de ambiente do modelo (`MODEL_BUCKET`/`MODEL_KEY`) — alinhar com Dev A (ETAPA 3)
- [ ] Task Definition de treino: comando e variáveis S3 — alinhar com Dev C (ETAPA 7)
- [ ] Versões das imagens no Compose (`prometheus`/`grafana`): fixar vs `latest`
- [ ] Custo AWS: ECS Service persistente + ALB geram custo contínuo — confirmar orçamento/janela da demo e destruir (`terraform destroy`) após a entrega
