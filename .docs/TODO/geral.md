# TODO — Geral do Time

> Este arquivo cobre: (a) o setup inicial que precede qualquer dev, (b) decisões e sincronizações que envolvem mais de um dev, e (c) o checklist final de submissão.
> As tarefas individuais de cada etapa estão nos TODOs de cada dev — não são duplicadas aqui, apenas referenciadas.
> Arquitetura do projeto: **100% ECS + Fargate**. Inferência = ECS Fargate Service (FastAPI) atrás de ALB, baixando `model.onnx` do S3. Treino = ECS Fargate Task disparada pela DAG. Imagem única no ECR. Monitoramento = Prometheus + Grafana. Terraform único. Sem Lambda/API Gateway/CloudWatch.
> Fonte de verdade dos requisitos: `.docs/content/tech-challenge.md`. Plano: `.docs/content/plan.md`.

---

## 1. Setup inicial (antes de qualquer dev começar)

> Responsável: **Dev A (Alexandre)** — ver `TODO/dev-a-alexandre.md → ETAPA 0`

- [x] **[Dev A]** ETAPA 0 concluída: repositório criado, estrutura de pastas, `pyproject.toml`, `CONTRIBUTING.md` e README esqueleto no ar
  - [x] Arquivos locais prontos: estrutura de pastas + `.gitkeep`, `pyproject.toml`, `.gitignore`, `.dockerignore`, `.env.example`, `CONTRIBUTING.md`, README esqueleto
  - [x] GitHub: repo público criado, commit inicial, branch protection em `main`
- [x] **[Dev A]** Dev B e Dev C adicionados como colaboradores com permissão `Write`
- [x] **[Dev A]** Comunicar ao time que podem criar suas branches

**Nenhuma outra etapa pode começar antes deste item estar marcado.**

---

## 2. Alinhamento do time — decisões já tomadas e pendências

### 2.1 Arquitetura de deploy — DECIDIDA
- [x] **100% ECS + Fargate** na AWS, provisionado via **Terraform**
- [x] Inferência = ECS Fargate **Service** persistente atrás de **ALB**
- [x] Treino = ECS Fargate **Task** efêmera disparada pela DAG
- [x] Modelo **baixado do S3** no startup do serviço (não embutido na imagem)
- [x] Imagem **única no ECR** (serve inferência e treino via override de comando)
- [x] **Sem** Lambda, API Gateway ou CloudWatch dashboards
- Dev A escreve a justificativa arquitetural no README (ETAPA 3); Dev B executa a infra (ETAPA 10) — devem ser coerentes.

### 2.2 Instrumentação da API com `prometheus_client` (impacta ETAPA 8)
- [ ] Definir quem escreve o código de métricas: **Dev A** adiciona `prometheus_client` em `app/main.py` durante a ETAPA 3, com **apoio do Dev B** na configuração do scrape na ETAPA 8
- [ ] `/metrics` expõe dados no formato Prometheus **antes** de Dev B configurar o Prometheus

### 2.3 Classificador do modelo (impacta ETAPA 2 e ETAPA 9)
- [ ] **`LogisticRegression`** — recomendado (compatível com `skl2onnx` + `predict_proba` nativo) ✅
- [ ] `LinearSVC` — requer `CalibratedClassifierCV` para `predict_proba` ⚠️
- [ ] `RandomForestClassifier` — compatível, porém mais lento ⚠️
- [ ] Decisão registrada aqui: ______________________________________

### 2.4 Contrato das variáveis de ambiente do modelo (impacta ETAPA 3, 7 e 10)
- [ ] Padronizar os nomes usados pela API, pela DAG e pelo Terraform:
  - `MODEL_BUCKET` — bucket S3 dos artefatos
  - `MODEL_KEY` — chave do artefato (ex.: `models/model.onnx`)
  - `USE_ONNX` — `true`/`false`
  - `AWS_REGION`
- [ ] Nomes confirmados entre Dev A (API), Dev B (Terraform/ECS) e Dev C (DAG/treino)

### 2.5 Terraform state e custo AWS (impacta ETAPA 10)
- [ ] Backend do state: S3 remoto (recomendado) vs local para a demo — decidir
- [ ] Ciente de que ECS Service persistente + ALB geram **custo contínuo** — definir janela da demo e executar `terraform destroy` após a entrega
- [ ] Decisão registrada aqui: ______________________________________

### 2.6 Airflow: instalação local vs. arquivo no repositório (impacta ETAPA 7)
- [ ] Decidir se haverá um `docker-compose.airflow.yml` dedicado para reprodução pela banca
- [ ] Decisão registrada aqui: ______________________________________

### 2.7 Datas de entrega por etapa
| Etapa | Responsável | Data alvo |
|---|---|---|
| ETAPA 0 | Dev A | ___/___/___ |
| ETAPA 1 | Dev C | ___/___/___ |
| ETAPA 2 | Dev C | ___/___/___ |
| ETAPA 3 | Dev A | ___/___/___ |
| ETAPA 4 | Dev A | ___/___/___ |
| ETAPA 5 | Dev B | ___/___/___ |
| ETAPA 6 | Dev B | ___/___/___ |
| ETAPA 7 | Dev C | ___/___/___ |
| ETAPA 8 | Dev B | ___/___/___ |
| ETAPA 9 | Dev C | ___/___/___ |
| ETAPA 10 | Dev B | ___/___/___ |
| ETAPA 11 | Dev A | ___/___/___ |

- [ ] Tabela de datas preenchida e comunicada
- [ ] Data limite de submissão confirmada com a instituição: ___/___/___

---

## 3. Pontos de sincronização entre etapas

### Checkpoint A — após ETAPA 0, antes de ETAPA 1 e ETAPA 3
- [ ] Dev A confirmou: repositório público, estrutura criada, `pyproject.toml` commitado
- [ ] Dev C confirmou: consegue criar branch `etapa-1-eda`
- [ ] Dev A prossegue para a ETAPA 3 (`etapa-3-api-fastapi`)
- [ ] Dev B confirmou acesso ao repositório para as etapas de infra

### Checkpoint B — após ETAPA 2 e ETAPA 3, antes de ETAPA 5
- [ ] Dev C confirmou: `models/model.pkl` gerado; `src/train.py` funciona via CLI; artefato disponível para upload ao S3
- [ ] Dev A confirmou: `app/main.py` com `/predict` e `/health` funcionando (com fallback mock)
- [ ] Dev B pode prosseguir com o Dockerfile

### Checkpoint C — após ETAPA 4, antes de ETAPA 6
- [ ] Dev A confirmou: `pytest -v` 100% e `ruff check app/ src/` zero erros
- [ ] Comandos comunicados ao Dev B: `ruff check app/ src/` e `pytest -v`

### Checkpoint D — antes de ETAPA 8 (instrumentação)
- [ ] Decisão 2.2 tomada; `/metrics` expondo dados antes de Dev B configurar o Prometheus

### Checkpoint E — após ETAPA 5, antes de ETAPA 9 (benchmark comparativo)
- [ ] `docs/latencia_baseline.md` (p50/p95/p99 do `.pkl`) disponível
- [ ] Dev B e Dev C combinaram máquina/condições iguais para o benchmark ONNX

### Checkpoint F — infra pronta (ETAPA 10)
- [ ] Contrato de env vars (2.4) confirmado antes do `terraform apply`
- [ ] Dev C alinhou com Dev B a Task Definition de treino (imagem, comando, S3)
- [ ] URL do ALB funcionando e comunicada ao Dev A para o README (ETAPA 11)

### Checkpoint G — revisão final antes de ETAPA 11
- [ ] ETAPA 9 concluída: comparativo sklearn vs ONNX pronto
- [ ] ETAPA 10 concluída: URL do ALB respondendo
- [ ] Dev A inicia consolidação do README e vídeo STAR

---

## 4. Revisão dos entregáveis oficiais do PDF

> Sugestão: Dev A revisa cada entregável antes da submissão.

### 📦 Entregável 1 — API funcional em Docker + decisão arquitetural no README
**Cobre:** ETAPA 0 (A) + ETAPA 3 (A) + ETAPA 5 (B)
- [ ] `POST /predict` no container retorna `{classe, confianca, tempo_ms}`
- [ ] `GET /health` retorna 200
- [ ] Seção "Decisão Arquitetural" (batch vs real-time + justificativa ECS/ALB)
- [ ] `docs/latencia_baseline.md` com tabela p50/p95/p99

### 📦 Entregável 2 — Workflow GitHub Actions + DAG Airflow
**Cobre:** ETAPA 4 (A) + ETAPA 6 (B) + ETAPA 7 (C)
- [ ] `ci.yml` com ≥2 jobs (lint + test) verdes + push da imagem para ECR
- [ ] Badge no README
- [ ] `dags/retrain_triagem_dag.py` presente
- [ ] Print do grafo Airflow verde em `docs/dag_execucao.png`

### 📦 Entregável 3 — Stack Docker Compose + dashboard Grafana
**Cobre:** ETAPA 8 (B, apoio A)
- [ ] `docker compose up` sobe API + Prometheus + Grafana sem passo manual
- [ ] Dashboard com ≥3 painéis (o plano entrega 4) com dados reais
- [ ] `monitoring/dashboard.json` versionado + print

### 📦 Entregável 4 — Modelo otimizado + comparativo + vídeo STAR
**Cobre:** ETAPA 2 (C) + ETAPA 9 (C) + ETAPA 10 (B) + ETAPA 11 (A)
- [ ] Classificador treinado com métricas (accuracy, F1) documentadas
- [ ] `models/model.onnx` gerado; paridade validada
- [ ] `docs/latencia_comparativo.md` com tabela sklearn vs ONNX
- [ ] Vídeo STAR ≤ 5 min publicado e linkado; testado em aba anônima

---

## 5. Checklist final de submissão

### Repositório
- [ ] Todos os PRs mergeados em `main`
- [ ] Repositório **público**; acessível em aba anônima
- [ ] Nenhum segredo commitado (`.env`, chaves AWS, `*.tfstate`):
  ```bash
  git log --all --full-history -- "*.env" "*.key" "*secret*" "*.tfstate"
  ```

### Código e execução
- [ ] `docker compose up` sobe a stack completa do zero
- [ ] `pytest -v` passa 100% no repositório clonado do zero
- [ ] `ruff check app/ src/` zero erros
- [ ] Workflow CI verde na `main`

### Infra AWS
- [ ] `terraform apply` provisiona a stack; URL do ALB respondendo
- [ ] `terraform destroy` testado/planejado para após a demo (controle de custo)

### Documentação
- [ ] README com todas as seções preenchidas
- [ ] URL do ALB na seção "Deploy em Produção"
- [ ] Comandos do README testados em terminal limpo
- [ ] `docs/latencia_baseline.md`, `docs/latencia_comparativo.md`, `docs/eda_resumo.md`, `docs/dag_execucao.png` presentes

### Vídeo
- [ ] ≤ 5 minutos, método STAR, link no README, testado em aba anônima

### Submissão
- [ ] Link do repositório submetido no portal indicado
- [ ] Recebimento confirmado

---

## ⚠️ Pontos em aberto — Time
- [ ] **Plataforma do vídeo:** confirmar com a instituição se YouTube é aceito.
- [ ] **Dataset:** confirmar com Dev C o dataset e a viabilidade do mapeamento para as 3 classes antes da ETAPA 1.
- [ ] **Airflow na entrega:** confirmar se é necessário `docker-compose.airflow.yml` para reprodutibilidade pela banca.
- [ ] **Limite de tamanho do texto na API:** decisão atual (Dev A): 5.000 caracteres — validar.
- [ ] **Custo AWS:** definir janela da demo e responsável por rodar `terraform destroy` após a entrega.
