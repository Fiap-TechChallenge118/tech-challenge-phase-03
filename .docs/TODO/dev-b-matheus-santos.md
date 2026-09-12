# TODO — Dev B: Matheus Santos

**Eixo de responsabilidade:** Infraestrutura, CI/CD, Observabilidade e Cloud (ECS/Fargate + Terraform)
**Etapas cobertas:** ETAPA 5 → ETAPA 6 → ETAPA 8 → ETAPA 10
**Peso na nota (PDF):** CI/CD 15% + Monitoramento 20% = **35%**

> Arquitetura do projeto: **100% ECS + Fargate**. Inferência = ECS Fargate Service (FastAPI) atrás de ALB, baixando `model.onnx` do S3 no startup. Treino = ECS Fargate Task disparada pela DAG. Imagem única no ECR. Monitoramento = Prometheus + Grafana. Sem Lambda/API Gateway. Terraform único (sem ambientes).
> A ETAPA 0 (Fundação do repositório) foi transferida para o Dev A.
> Fonte de verdade: `.docs/content/tech-challenge.md`. Plano: `.docs/content/plan.md`.

---

## Estado da execução — 12/09/2026

**Branch de trabalho: `develop` para todo o trabalho e publicação.**
**Janela AWS autorizada: duas semanas, até 26/09/2026.**
Instruções, valores GitHub, comandos de operação e handoff: [docs/dev-b-operacao.md](../../docs/dev-b-operacao.md).
Baseline pendente e método: [docs/latencia_baseline.md](../../docs/latencia_baseline.md).

- [x] Instalados Python 3.11, Terraform, actionlint, dependências e ambiente local.
- [x] Docker ARM64/AMD64 construído; processo UID 10001; API em mock e CLI de treino validadas.
- [x] 10 testes existentes + 3 testes do benchmark passaram; Ruff/actionlint sem erros.
- [x] Compose ativo; Prometheus target UP; Grafana com quatro painéis e captura `docs/grafana_dashboard_mock.png`.
- [x] Benchmark recusa mock por padrão. Smoke de 200 chamadas salvo separadamente, sem alegar baseline real.
- [x] Bootstrap AWS aplicado: ECR, OIDC restrito à develop, bucket de state com locking/versionamento. State migrado para S3.
- [x] Imagem inicial `bootstrap-20260912` publicada no ECR (AMD64); publicação pelo Actions ainda pendente.
- [x] Infra base aplicada: rede dedicada, buckets privados/versionados, roles, cluster, Task Definitions e logs com retenção de 14 dias.
- [x] Terraform sem diferenças após apply (bootstrap e infra).
- [x] Smoke Fargate real: download da imagem e `python -m src.train --help`, exit code 0. Evidências em `docs/infra_validacao.md` e outputs em `docs/aws_outputs.json`.
- [x] CI ampliado com validação Terraform/Compose; publicação reaproveita exatamente a imagem testada via artifact, sem rebuild.
- [x] Recebido `.pkl` do Dev C; SHA-256 e incompatibilidade sklearn 1.9.0 → 1.4.2 registrados.
- [x] Import `preprocess` contemplado no PYTHONPATH do Docker; validador de versão/contrato implementado.
- [ ] Receber artefato regenerado com sklearn 1.4.2, medir baseline real e repetir evidência Grafana.
- [ ] Configurar as três variables GitHub, publicar na develop e obter Actions verde.
- [ ] Dev C concluir ingestão/upload S3 do treino e entregar ONNX/paridade.
- [ ] Ativar ALB/Service com modelo real e registrar smoke/benchmark AWS.
- [ ] Dev A integrar evidências/badge/documentação ao README final e vídeo.

`enable_inference=false`: não há endpoint ALB ativo enquanto falta um artefato compatível.
Tags de expiração não desligam recursos automaticamente; procedimento de encerramento está no guia.
Autoria Git configurada: Matheus Santos <matheussantosjjj@gmail.com>. TODOs A/C preservados.

## Auditoria inicial e plano — 12/09/2026

A tabela abaixo preserva a auditoria anterior às instalações; o estado atual está acima.

### Escopo combinado

- Executar exclusivamente as responsabilidades do Dev B: etapas 5, 6, 8 e 10, tendo `.docs/content/tech-challenge.md` como requisito de entrega.
- Dev A mantém API, testes, README final e vídeo; Dev C mantém dataset, treino, Airflow e ONNX. Entregar instruções e evidências para integração, sem assumir essas tarefas.
- Commits/push e configuração GitHub fazem parte do escopo do Dev B; dependem da autenticação da conta.
- Marcar itens apenas com validação efetiva.

### Ambiente verificado

| Item | Evidência / situação |
|---|---|
| Checkout | `develop`, commit `8c13368`; referências locais indicam `origin/HEAD -> origin/master`. Os exemplos antigos com `main` precisam ser adaptados ao fluxo real. |
| Alterações preexistentes | `AWSCLIV2.pkg` não versionado; preservar e não incluir no commit da entrega. |
| Docker | Cliente/servidor 29.7.2 ativos; Compose v5.5.1. |
| Máquina | macOS 15.6.1, ARM64, 8 CPUs lógicas, 16 GiB RAM. Definir explicitamente arquitetura da imagem/ECS e registrar condições do benchmark. |
| AWS CLI | 2.36.44; STS respondeu. Identidade atual é root: preparar identidade de trabalho e role OIDC para CI; não transferir credenciais root ao GitHub. STS não comprova que a infraestrutura existe. |
| Terraform | Não encontrado no PATH; instalar e validar antes da etapa 10. |
| GitHub CLI | Instalado, sem autenticação; secrets, variables, proteções e execuções remotas ainda não verificados. |
| Python local | `python3` disponível; `.venv` e `.env` ausentes. Preparar Python 3.11/dependências e executar lint/testes. |
| Modelo | `models/` contém relatórios, mas não `model.pkl` ou `model.onnx`. Baseline real depende do artefato do Dev C. |
| Aplicação | API, loader, testes e treino presentes. Inspeção estática feita; testes não reexecutados nesta auditoria. |
| Infra/observabilidade | Dockerfile, Compose, workflow e módulos Terraform ainda precisam ser implementados. |

### Ordem de execução e critérios de aceite

1. **Preparar ambiente e contratos.** Instalar Terraform; preparar dependências Python e `.env` local; confirmar branch de integração/publicação; validar lint e testes existentes. Receber do Dev C o `.pkl` e registrar hash/versões. Fixar versões de ferramentas/imagens durante a implementação.
2. **Etapa 5 — container e baseline.** Criar Dockerfile multi-stage Python 3.11, usuário não-root, diretórios graváveis para treino e healthcheck; ajustar `.dockerignore` para excluir também instaladores e artefatos que serão montados/baixados. Validar imagem única para API e CLI de treino. Montar o modelo local, exigir `/health` com `model=loaded` e testar `/predict`. Implementar benchmark com aquecimento, timeout, validação de respostas, p50/p95/p99, throughput e dados brutos; registrar 500 requisições, tamanho/digest da imagem e condições da máquina. Não aceitar modo mock como baseline do modelo.
3. **Etapa 8 — monitoramento local.** Pode avançar antes da publicação no GitHub. Criar Compose com API, Prometheus e Grafana provisionados; fixar versões; configurar scrape de 15 s e quatro painéis. Respeitar a unidade existente do histograma (ms). Validar target UP, dados após carga, JSON e captura do dashboard. Documentar que o contador atual cobre erros de inferência, não todas as respostas HTTP 422; não apresentar o painel como contagem de todos os erros HTTP.
4. **Etapa 6 — CI/CD.** Preparar YAML com lint → testes → build validado em PRs, e publicação ECR somente na branch de entrega definida. Usar OIDC/role AWS e tags de imagem por commit. Configurar variables, acesso e publicação. Só marcar Actions concluído após execução remota verde e evidência; preparar badge/instruções para o README do Dev A.
5. **Etapa 10 — bootstrap AWS e deploy.** Resolver a dependência circular: criar primeiro backend de state, ECR e role do CI; publicar imagem pelo CI; disponibilizar artefato S3; então criar/ativar Service ECS + ALB. Implementar módulos de rede, S3, ECR, IAM, ECS e ALB; definir arquitetura compatível com a imagem, IAM por função e integração do treino. Preferir state remoto S3 com versionamento e locking suportado pela versão escolhida. Executar fmt/validate/plan, revisar recursos/custos e aplicar dentro da janela de demonstração definida. Validar `/health` com modelo carregado, `/docs`, `/predict`, benchmark de 100 requisições e instruções de rollback/remoção dos recursos da entrega.
6. **Handoff.** Consolidar evidências de Docker, benchmark, Grafana, Actions e AWS; entregar ao Dev A conteúdo técnico para README/vídeo e ao Dev C parâmetros de ECS/S3. Publicar commits e acompanhar resultados e corrigir problemas do escopo B.

### Dependências e decisões a resolver

- **Dev C — modelo:** regenerar `model.pkl` com sklearn 1.4.2. Arquivo recebido em 1.9.0; incompatibilidade detectada no validador.
- **Dev C — treino ECS:** `src/train.py` exige `--data`; não há integração S3 identificada no script atual. Definir caminho de entrada/saída, download/upload, comando completo e contrato com a DAG antes de declarar a Task funcional. Infra B fornece imagem, roles, buckets, subnets, security groups e Task Definition; lógica de treino/DAG permanece C.
- **Dev C — ONNX:** usar `.pkl` no baseline; habilitar ONNX no deploy após entrega e paridade validada pelo Dev C.
- **Dev A — saúde:** `/health` retorna 200 também em mock; verificações de aceite B precisam conferir `model=loaded` explicitamente.
- **GitHub:** trabalhar e publicar exclusivamente na `develop`, conforme decisão do time; manter o nome da branch padrão remota.
- **AWS:** região `us-east-1`, janela até 26/09/2026 autorizada. Recursos tc03 separados dos projetos anteriores. Inferência aguarda modelo.
- **Logs:** documentos alternam entre “sem CloudWatch” e log groups opcionais. Proposta: Prometheus/Grafana para métricas; CloudWatch Logs somente para logs operacionais ECS, explicitando a decisão na documentação B.

### Dependências externas

- [x] Branch `develop` e janela de infraestrutura mínima por duas semanas definidas.
- Executar a configuração GitHub e commits/push com o roteiro que será entregue após os arquivos estarem preparados e verificados.
- Viabilizar com o Dev C a entrega do artefato treinado e contrato de treino/S3; essas dependências não impedem preparar Docker, Compose, CI e Terraform.

---

## ETAPA 5 — Dockerfile e baseline de latência

**Objetivo:** empacotar a API em Docker (imagem única para inferência e treino) e registrar o baseline de latência.

**Entregável:** `Dockerfile` funcional + `docs/latencia_baseline.md`.

**Dependências:** Requer ETAPA 2 (modelo) e ETAPA 3 (`app/main.py`). Bloqueia ETAPA 6, 8 e 9.

**Branch:** `develop`

---

### Checklist

#### Dockerfile
- [x] Multi-stage (builder + runtime) com `python:3.11-slim`
- [x] Copiar `app/` e `src/` (a mesma imagem serve inferência e treino via override de comando)
- [x] Usuário não-root; `EXPOSE 8000`
- [x] `HEALTHCHECK` para `/health`
- [x] `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` (default = inferência)
- [x] `.dockerignore` exclui `data/`, `tests/`, `infra/`, `.git`, `.venv` *(`.dockerignore` já existe e está correto)*

#### Build e validação
- [x] `docker build -t triagem-api:latest .` + registrar tamanho da imagem
- [x] `docker run -p 8000:8000` → validar `/health` e `POST /predict` dentro do container
- [x] Confirmar processo como não-root (`docker exec <id> whoami`)

#### Benchmark (`scripts/benchmark.py`)
- [x] Args `--n` (default 500) e `--url` (default `http://localhost:8000/predict`)
- [x] N requisições sequenciais, coletar latência individual
- [x] Calcular p50/p95/p99 (ms) + throughput (req/s); salvar bruto em `docs/benchmark_raw.json`

#### Documentação e finalização
- [ ] `docs/latencia_baseline.md`: tabela p50/p95/p99 + throughput, specs da máquina, versão da imagem, data
- [x] Nota: "baseline do `.pkl`; comparado com ONNX na ETAPA 9"
- [ ] Commit: `feat(docker): add multi-stage Dockerfile and latency baseline`; commit/push por Matheus Santos na `develop`

### ✅ Definition of Done — ETAPA 5
- Build/run, não-root e endpoints em mock validados ✅; baseline com modelo real pendente.
- Tamanho da imagem registrado; `docs/latencia_baseline.md` com tabela e specs ⬜
- Commit/push por Matheus Santos pendente ⬜

---
---

## ETAPA 6 — CI/CD GitHub Actions (lint → test → build → push ECR)

**Objetivo:** automatizar lint, testes e build/push da imagem para o ECR a cada push/PR.

**Entregável:** `.github/workflows/ci.yml` verde + badge no README.

**Dependências:** Requer ETAPA 5 (Dockerfile) e ETAPA 4 (testes/lint, Dev A). Bloqueia ETAPA 10 (deploy usa a imagem do ECR).

**Branch:** `develop`

---

### Checklist

#### Workflow (`.github/workflows/ci.yml`)
- [x] Triggers: push/PR em `develop` e `workflow_dispatch`.
- [x] **Job lint:** checkout, `setup-python@3.11`, cache pip, `pip install ruff`, `ruff check app/ src/`
- [x] **Job test** (`needs: lint`): `pip install -e ".[dev]"`, `pytest -v`
- [x] Job build após testes, incluindo smoke da imagem; job publish separado com OIDC/ECR, somente push/dispatch na develop, tag SHA imutável e rerun idempotente.
- [ ] Configurar Variables `AWS_REGION`, `AWS_ROLE_ARN`, `ECR_REPOSITORY`; sem access keys em Secrets (OIDC).

#### Validação e badge
- [ ] Push de teste dispara o workflow; jobs lint, test, infra, build e publish verdes na aba Actions
- [ ] Print da execução verde (para o vídeo)
- [ ] Badge do workflow no topo do README
- [ ] Commit: `ci: add GitHub Actions workflow (lint, test, build, push ECR)`; commit/push por Matheus Santos na `develop`

### ✅ Definition of Done — ETAPA 6
- Jobs lint/test/infra/build/publish verdes no Actions ⬜
- Push para ECR pelo Actions na `develop` ⬜ (push local de bootstrap validado).
- Badge no README; print salvo ⬜

---
---

## ETAPA 8 — Monitoramento: Prometheus + Grafana

**Objetivo:** stack de observabilidade com `docker compose up`, dashboard Grafana com ≥4 painéis.

**Entregável:** `docker-compose.yml` + `monitoring/prometheus.yml` + `monitoring/dashboard.json` + print.

**Dependências:** Requer ETAPA 5. Apoio: Dev A instrumenta a API com `prometheus_client`.

**Branch:** `develop`

---

### Checklist

#### Instrumentação (com Dev A)
- [x] Confirmar `/metrics` exposto em `app/main.py` (Counter req com label `classe_predita`, Histogram latência, Counter erros) — **já implementado**
- [x] `curl localhost:8000/metrics` retorna formato Prometheus — **validado**

#### Prometheus (`monitoring/prometheus.yml`)
- [x] `scrape_interval: 15s`; `job triagem-api` → target `api:8000`, `metrics_path: /metrics`

#### Docker Compose (`docker-compose.yml`)
- [x] Serviço `api`: `build: .`, `ports 8000:8000`, `env_file .env`, healthcheck `/health`, network `monitoring`
- [x] Serviço `prometheus`: `prom/prometheus`, volume do `prometheus.yml`, `ports 9090:9090`, `depends_on api`
- [x] Serviço `grafana`: `grafana/grafana`, `ports 3000:3000`, `GF_SECURITY_ADMIN_PASSWORD=admin`, volume de provisioning, `depends_on prometheus`
- [x] Network `monitoring` (bridge)

#### Provisionamento e dashboard
- [x] `monitoring/grafana/provisioning/datasources/prometheus.yml` (datasource Prometheus default)
- [x] `monitoring/grafana/provisioning/dashboards/dashboard.yml` (provider file)
- [x] Dashboard com 4 painéis: total requisições, latência p95 (`histogram_quantile`), taxa de erro (`rate`), distribuição por classe (label `classe_predita`)
- [x] Carga de 200 chamadas HTTP + warmup e painéis validados em mock; repetir com modelo real antes da entrega.
- [x] JSON versionável e provisioning; print em `docs/grafana_dashboard_mock.png`.
- [ ] Commit: `feat(monitoring): add docker-compose with Prometheus and Grafana`; commit/push por Matheus Santos na `develop`

### ✅ Definition of Done — ETAPA 8
- `docker compose up` sobe os 3 serviços sem passo manual ✅
- `/metrics` e dashboard com 4 painéis validados com tráfego real em mock ✅; captura com classificador real pendente.
- JSON e print prontos; commit por Matheus Santos pendente.

---
---

## ETAPA 10 — Infra Terraform AWS (ECS/Fargate)

**Objetivo:** provisionar a infra AWS via Terraform — serviço de inferência (ECS Service + ALB) e treino (ECS Task), com imagem no ECR e artefatos no S3.

**Entregável:** `infra/` aplicável (`terraform apply`) + URL pública do ALB respondendo + seção de deploy no README.

**Dependências:** Requer ETAPA 6 (imagem no ECR) e ETAPA 8 (compose validado). Bloqueia ETAPA 11.

**Branch:** `develop`

---

### Checklist

#### Módulos Terraform (`infra/modules/`)
- [x] `networking`: VPC, subnets públicas/privadas, security groups (ALB → ECS)
- [x] `s3`: bucket de datasets (raw/processed) + bucket de artefatos de modelo
- [x] `ecr`: repositório da imagem única
- [x] `iam`: execution role + task role do ECS (acesso a S3, ECR, CloudWatch Logs)
- [ ] `ecs`:
  - Cluster Fargate
  - **Service de inferência**: Task Definition (imagem ECR, env `MODEL_BUCKET`/`MODEL_KEY`/`USE_ONNX`), desired_count ≥ 1, healthcheck `/health`
  - **Task Definition de treino**: mesma imagem, comando override `python src/train.py`
- [x] Módulo ALB + target group + listener implementado; criação condicionada a `enable_inference=true` após entrega do modelo.
- [x] `monitoring`: log groups (opcional)

#### Composição e apply
- [x] `infra/main.tf` compõe os módulos; `variables.tf`, `outputs.tf` (expor DNS do ALB, nomes de bucket, repo ECR)
- [x] `backend.tf`: state remoto no S3 (recomendado) ou local para a demo
- [x] init/plan/apply do bootstrap e da infra base; ALB/Service aguardam modelo.

#### Smoke test e documentação
- [ ] `GET http://<alb-dns>/health` → 200; `GET /docs` carrega; `POST /predict` com laudo real retorna `{classe, confianca, tempo_ms}`
- [ ] Rodar `scripts/benchmark.py --n 100 --url http://<alb-dns>/predict`; registrar latência de produção em `docs/latencia_baseline.md`
- [ ] README: URL do ALB + passo a passo de deploy (`terraform apply`) e rollback
- [ ] Commit: `feat(infra): add Terraform for ECS/Fargate, ALB, ECR, S3`; commit/push por Matheus Santos na `develop`

### ✅ Definition of Done — ETAPA 10
- `terraform apply` da infra base concluído ✅; ALB/Service ainda não aplicados.
- URL do ALB respondendo `/health`, `/docs`, `/predict` ⬜
- ECS Service baixa o modelo do S3 e serve inferência ⬜
- Nenhum segredo hardcoded; README com URL e deploy/rollback ⬜
- Commit/push por Matheus Santos pendente ⬜

---

## ⚠️ Pontos em aberto — Dev B
- [x] State remoto S3 com versionamento, criptografia e locking nativo; bootstrap separado.
- [x] Nomes das variáveis de ambiente do modelo (`MODEL_BUCKET`/`MODEL_KEY`) — definidos e documentados no `.env.example` pelo Dev A
- [ ] Task Definition de treino: comando e variáveis S3 — alinhar com Dev C (ETAPA 7)
- [x] Versões fixadas: Prometheus 3.5.0 e Grafana 12.1.1.
- [x] Janela autorizada até 26/09/2026; configuração mínima sem NAT Gateway, retenção 14 dias. Encerramento documentado, não automático.
