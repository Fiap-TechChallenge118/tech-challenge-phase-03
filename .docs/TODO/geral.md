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
- [x] **Dev A** adicionou `prometheus_client` em `app/main.py`: Counter req (label `classe_predita`), Histogram latência, Counter erros
- [x] `/metrics` expõe dados no formato Prometheus — validado com TestClient

### 2.3 Classificador do modelo (impacta ETAPA 2 e ETAPA 9)
- [x] **`LogisticRegression`** (C=0.3, class_weight=balanced) — **ESCOLHIDO**. Macro-F1=0.609, compatível com `skl2onnx` + `predict_proba` nativo ✅
- Decisão registrada: `LogisticRegression` venceu comparativo entre RandomForest, LinearSVC e LogisticRegression em `models/metrics.json`

### 2.4 Contrato das variáveis de ambiente do modelo (impacta ETAPA 3, 7 e 10)
- [x] Nomes padronizados e documentados no `.env.example`:
  - `MODEL_BUCKET` — bucket S3 dos artefatos
  - `MODEL_KEY` — chave do artefato (ex.: `models/model.onnx`)
  - `MODEL_PATH` — caminho local quando `MODEL_BUCKET` não está definido
  - `USE_ONNX` — `true`/`false`
  - `AWS_REGION`
- [ ] Nomes confirmados entre Dev B (Terraform/ECS) e Dev C (DAG/treino)

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
| ETAPA 0 | Dev A | ✅ concluída |
| ETAPA 1 | Dev C | ___/___/___ |
| ETAPA 2 | Dev C | ✅ concluída |
| ETAPA 3 | Dev A | ✅ concluída |
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
- [x] Dev A confirmou: repositório público, estrutura criada, `pyproject.toml` commitado
- [ ] Dev C confirmou: consegue criar branch `etapa-1-eda`
- [x] Dev A prosseguiu para a ETAPA 3 (`etapa-3-api-fastapi`) — concluída
- [ ] Dev B confirmou acesso ao repositório para as etapas de infra

### Checkpoint B — após ETAPA 2 e ETAPA 3, antes de ETAPA 5
- [x] Dev C confirmou: `models/model.pkl` gerado; `src/train.py` funciona via CLI
- [x] Dev A confirmou: `app/main.py` com `/predict` e `/health` funcionando (com fallback mock e modelo local)
- [ ] Dev B pode prosseguir com o Dockerfile *(aguardando Dev B)*

### Checkpoint C — após ETAPA 4, antes de ETAPA 6
- [ ] Dev A confirmar: `pytest -v` 100% e `ruff check app/ src/` zero erros *(ETAPA 4 pendente)*
- [ ] Comandos comunicados ao Dev B: `ruff check app/ src/` e `pytest -v`

### Checkpoint D — antes de ETAPA 8 (instrumentação)
- [x] Decisão 2.2 tomada; `/metrics` expondo dados — **concluído pelo Dev A**

### Checkpoint E — após ETAPA 5, antes de ETAPA 9 (benchmark comparativo)
- [ ] `docs/latencia_baseline.md` (p50/p95/p99 do `.pkl`) disponível *(aguardando ETAPA 5)*
- [ ] Dev B e Dev C combinaram máquina/condições iguais para o benchmark ONNX

### Checkpoint F — infra pronta (ETAPA 10)
- [x] Contrato de env vars (2.4) confirmado — variáveis definidas no `.env.example`
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
- [x] `POST /predict` retorna `{classe, confianca, tempo_ms}` — validado
- [x] `GET /health` retorna 200 — validado
- [x] Seção "Decisão Arquitetural" (batch vs real-time + justificativa ECS/ALB) no README
- [ ] `POST /predict` funcionando **dentro do container** Docker *(Dockerfile pendente)*
- [ ] `docs/latencia_baseline.md` com tabela p50/p95/p99 *(pendente ETAPA 5)*

### 📦 Entregável 2 — Workflow GitHub Actions + DAG Airflow
**Cobre:** ETAPA 4 (A) + ETAPA 6 (B) + ETAPA 7 (C)
- [ ] `ci.yml` com ≥2 jobs (lint + test) verdes + push da imagem para ECR
- [ ] Badge no README
- [ ] `dags/retrain_triagem_dag.py` presente
- [ ] Print do grafo Airflow verde em `docs/dag_execucao.png`

### 📦 Entregável 3 — Stack Docker Compose + dashboard Grafana
**Cobre:** ETAPA 8 (B, apoio A)
- [ ] `docker compose up` sobe API + Prometheus + Grafana sem passo manual
- [ ] Dashboard com ≥3 painéis com dados reais
- [ ] `monitoring/dashboard.json` versionado + print

### 📦 Entregável 4 — Modelo otimizado + comparativo + vídeo STAR
**Cobre:** ETAPA 2 (C) + ETAPA 9 (C) + ETAPA 10 (B) + ETAPA 11 (A)
- [x] Classificador treinado com métricas documentadas (accuracy=0.607, macro-F1=0.609)
- [ ] `models/model.onnx` gerado; paridade validada *(pendente ETAPA 9)*
- [ ] `docs/latencia_comparativo.md` com tabela sklearn vs ONNX *(pendente ETAPA 9)*
- [ ] Vídeo STAR ≤ 5 min publicado e linkado *(pendente ETAPA 11)*

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
- [ ] `ruff check app/ src/` zero erros *(8 erros E501 pendentes)*
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
- [x] **Dataset:** Medical Abstracts TC Corpus — mapeamento para 3 classes definido e documentado.
- [ ] **Airflow na entrega:** confirmar se é necessário `docker-compose.airflow.yml` para reprodutibilidade pela banca.
- [x] **Limite de tamanho do texto na API:** **5.000 caracteres** — definido em `app/schemas.py`.
- [ ] **Custo AWS:** definir janela da demo e responsável por rodar `terraform destroy` após a entrega.
