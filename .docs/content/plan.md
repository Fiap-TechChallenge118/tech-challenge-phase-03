# Plano de Execução — Tech Challenge Fase 3

> Sistema de triagem automática de laudos médicos (NLP) com deploy em produção, pipeline CI/CD, orquestração de retreino e monitoramento.

---

## 1. Como usar o board

- Cada lista **FASE N** contém **1 card (atividade)** com o checklist completo a ser seguido.
- O responsável está identificado no nome do card e na descrição, no formato:
  `Etapa: N | Responsável: Dev X`
- **Ao iniciar** uma fase: mover o card para a lista **"Doing"**.
- **Ao concluir** todos os itens do checklist: marcar o card como concluído e devolvê-lo para a lista da fase.
- A lista **"Review - Entregáveis"** contém 1 card por etapa oficial do Tech Challenge (Etapas 1 a 4 do PDF), usada como critério de aceite antes da entrega final.

### Pendências manuais (não automatizadas)

- [ ] Atribuir os membros nos cards (arrastar avatares)
- [ ] Renomear as labels padrão para `FASE 0..10`, `TIME` e `FINALIZADO`
- [ ] Definir as datas de entrega de cada fase

---

## 2. Dependências entre fases

```
FASE 0
  └──> FASE 1 ──┐
  └──> FASE 2 ──┴──> FASE 3 ──> FASE 4 ──> FASE 5 ──┐
                                                        ├──> FASE 8 ──> FASE 9
                                        FASE 6 ─────────┘
                                        FASE 7 (após FASE 3)
```

Leitura simplificada da cadeia principal:

**FASE 0** → **FASE 1** e **FASE 2** (em paralelo) → **FASE 3** → **FASE 4** → **FASE 5** → **FASE 6** e **FASE 7** (em paralelo) → **FASE 8** → **FASE 9** → **FASE 10**

---

## 3. Time e responsabilidades

### 🔵 Dev A — Alexandre Araújo
**Eixo:** API, Testes e Documentação · **3 fases** (2, 4, 10)

| Item | Detalhe |
|---|---|
| Escopo | API FastAPI (`/predict`, `/health`, `/metrics`) · Schemas Pydantic e tratamento de erro · Instrumentação com `prometheus_client` · Suíte pytest + lint (`ruff`) · Decisão arquitetural (batch vs real-time) no README · README final e roteiro/gravação do vídeo STAR |
| Peso na nota (PDF) | Documentação 15% + Vídeo STAR 15% = **30%** |

### 🟢 Dev B — Matheus Santos
**Eixo:** Infraestrutura, CI/CD, Observabilidade e Cloud · **5 fases** (0, 3, 5, 7, 9)

| Item | Detalhe |
|---|---|
| Escopo | Setup do repositório, branch strategy e commits semânticos · Dockerfile multi-stage do serviço de inferência · Medição de baseline de latência (p50/p95/p99) · Workflow GitHub Actions (lint → test → build → push) · docker-compose com API + Prometheus + Grafana · Deploy em nuvem (URL pública funcionando) |
| Peso na nota (PDF) | CI/CD 15% + Monitoramento 20% = **35%** |

### 🟠 Dev C — Matheus Ferreira
**Eixo:** Dataset, Modelo NLP, Airflow e Otimização (ONNX) · **3 fases** (1, 6, 8)

| Item | Detalhe |
|---|---|
| Escopo | Seleção e preparação do dataset (mín. 2.000 amostras, coluna texto + coluna target) · Pipeline TF-IDF + classificador leve (Random Forest / LinearSVC / LogisticRegression) · Métricas de avaliação e serialização do artefato · DAG Airflow (ingestão → treino → salvamento) · Exportação para ONNX / quantização + benchmark comparativo |
| Peso na nota (PDF) | Modelagem e Otimização 20% + Airflow 15% = **35%** |

---

## 4. Fases detalhadas

### FASE 0 — Fundação do repositório e padrões de trabalho
**Responsável:** Dev B (Matheus Santos)

- **Objetivo:** deixar o repositório pronto para os outros dois devs começarem em paralelo, sem conflito.
- **Entregável:** repositório GitHub público com estrutura de pastas, branch protection e padrão de commit definido.
- **Bloqueia:** FASE 1 e FASE 2.

**Checklist**
- [ ] Criar repo GitHub + convidar os 3 devs como colaboradores
- [ ] Estrutura de pastas: `app/`, `src/`, `dags/`, `tests/`, `data/`, `models/`, `monitoring/`, `.github/workflows/`
- [ ] `.gitignore`, `.dockerignore` e `.env.example`
- [ ] Definir Conventional Commits (`feat`/`fix`/`docs`/`chore`) e documentar no `CONTRIBUTING.md`
- [ ] Branch strategy: `main` protegida + feature branches + PR obrigatório
- [ ] README esqueleto com seções vazias (arquitetura, execução, resultados, vídeo)
- [ ] `requirements.txt` (ou `pyproject`) com dependências fixadas: `fastapi`, `uvicorn`, `scikit-learn`, `prometheus-client`, `onnxruntime`

---

### FASE 1 — Dataset e modelo baseline de classificação de urgência
**Responsável:** Dev C (Matheus Ferreira) · **Corresponde à Etapa 4 do PDF**

- **Objetivo:** ter um classificador de urgência funcionando e serializado, para a API consumir.
- **Entregável:** `models/model.pkl` (pipeline TF-IDF + classificador) + relatório de métricas no README.
- **Depende de:** FASE 0. **Bloqueia:** FASE 3, FASE 6 e FASE 8.
- **Dataset sugerido pelo PDF:** Medical Abstracts TC Corpus (Kaggle), recortes do MIMIC-III, ou qualquer CSV com coluna de texto + coluna de target (mínimo 2.000 amostras).

**Checklist**
- [ ] Escolher dataset público (≥ 2.000 amostras) e commitar em `data/raw/` (ou script de download)
- [ ] Mapear classes para as 3 categorias de urgência: `normal` / `atenção` / `urgente`
- [ ] Pré-processamento de texto (lowercase, stopwords, limpeza) em `src/preprocess.py`
- [ ] Pipeline sklearn: `TfidfVectorizer` + classificador leve (RandomForest / LinearSVC / LogisticRegression)
- [ ] Train/test split com `random_state` fixo + avaliar accuracy, precision, recall e F1 por classe
- [ ] Serializar pipeline completo com `joblib` em `models/model.pkl` (vetorizador incluído)
- [ ] Expor `src/train.py` como script CLI reutilizável (será chamado pela DAG na FASE 6)

---

### FASE 2 — API FastAPI de triagem + decisão arquitetural de nuvem
**Responsável:** Dev A (Alexandre Araújo) · **Corresponde à Etapa 1 do PDF**

- **Objetivo:** API REST que recebe o texto do laudo e devolve a classificação de urgência, além de documentar a decisão de arquitetura em nuvem.
- **Entregável:** `app/main.py` funcional + seção "Decisão Arquitetural" no README.
- **Depende de:** FASE 0 (estrutura) e FASE 1 (`model.pkl`). Até o modelo ficar pronto, usar um mock que retorna classe fixa.
- **Ponto de atenção do PDF:** a análise batch vs real-time vale nota em "Documentação (15%)". Justificar por que a triagem clínica exige inferência real-time (síncrona) e qual serviço gerenciado seria usado (ex.: Azure Container Apps, AWS ECS Fargate ou Cloud Run).

**Checklist**
- [ ] Endpoint `POST /predict` recebendo `{texto: str}` e retornando `{classe, confianca, tempo_ms}`
- [ ] Endpoint `GET /health` para healthcheck do container e do orquestrador
- [ ] Schemas Pydantic de request/response + validação de texto vazio e limite de tamanho
- [ ] Carregar o `model.pkl` uma única vez no startup (não a cada request)
- [ ] Tratamento de erro com `HTTPException` + logging estruturado (sem `print`)
- [ ] Escrever no README a análise batch vs real-time e justificar o provedor/serviço escolhido
- [ ] Validar Swagger em `/docs` com exemplo de laudo preenchido

---

### FASE 3 — Containerização da API e baseline de latência
**Responsável:** Dev B (Matheus Santos) · **Corresponde à Etapa 1 do PDF**

- **Objetivo:** empacotar a API em Docker e registrar o baseline de latência local — número que será comparado na FASE 8.
- **Entregável:** Dockerfile funcional + tabela de baseline (p50/p95/p99) em `docs/latencia_baseline.md`.
- **Depende de:** FASE 1 e FASE 2. **Bloqueia:** FASE 7 e FASE 8 (sem baseline não há comparativo).

**Checklist**
- [ ] Dockerfile multi-stage (builder + runtime) com imagem base `python:slim`
- [ ] Rodar como usuário não-root + `HEALTHCHECK` apontando para `/health`
- [ ] Build + run local validando `/predict` respondendo dentro do container
- [ ] Reduzir tamanho da imagem (`.dockerignore`, camadas, `--no-cache-dir`) e registrar o tamanho final
- [ ] Criar `scripts/benchmark.py` disparando N=500 requisições sequenciais em `/predict`
- [ ] Medir e registrar baseline: p50, p95, p99 e throughput (req/s) do modelo `.pkl`
- [ ] Commitar `docs/latencia_baseline.md` com a tabela + specs da máquina de teste

---

### FASE 4 — Testes automatizados e qualidade de código
**Responsável:** Dev A (Alexandre Araújo) · **Corresponde à Etapa 2 do PDF**

- **Objetivo:** ter testes e lint funcionando localmente **antes** de automatizar no GitHub Actions — o workflow da FASE 5 só chama o que for definido aqui.
- **Entregável:** pasta `tests/` com suíte pytest passando + configuração de lint no `pyproject.toml`.
- **Depende de:** FASE 2. **Bloqueia:** FASE 5.
- **Requisito do PDF:** "CI/CD contendo pelo menos 2 automações (verificação de código e testes)" — esta fase produz as duas.

**Checklist**
- [ ] Configurar `ruff` (ou `flake8`) no `pyproject.toml` e garantir zero erros em `app/` e `src/`
- [ ] `tests/test_health.py` — `/health` retorna 200
- [ ] `tests/test_predict.py` — laudo válido retorna uma das 3 classes esperadas
- [ ] Testes de borda: texto vazio, payload malformado e texto muito longo retornam 422
- [ ] Usar `TestClient` do FastAPI + fixture com modelo mock (teste não pode depender do `.pkl` real)
- [ ] Rodar `pytest -v` localmente com 100% dos testes passando antes de abrir PR

---

### FASE 5 — Pipeline CI/CD no GitHub Actions (lint → test → build)
**Responsável:** Dev B (Matheus Santos) · **Corresponde à Etapa 2 do PDF**

- **Objetivo:** automatizar lint, testes e build da imagem a cada push/PR.
- **Entregável:** `.github/workflows/ci.yml` rodando verde + badge de status no README.
- **Depende de:** FASE 3 (Dockerfile) e FASE 4 (testes e lint). **Bloqueia:** FASE 9.
- **Critério de avaliação:** CI/CD (GitHub Actions) = 15% da nota. O PDF exige no mínimo 2 automações (lint + test); o build da imagem entra como terceira e reforça a nota.

**Checklist**
- [ ] Criar `.github/workflows/ci.yml` com triggers `on: push` e `on: pull_request` para `main`
- [ ] Job 1 (lint): `setup-python` + cache de deps + `ruff check`
- [ ] Job 2 (test): `pytest` com `needs: lint` (só roda se o lint passar)
- [ ] Job 3 (build): `docker build` validando que a imagem sobe sem erro
- [ ] Push da imagem para GHCR (`ghcr.io`) usando `GITHUB_TOKEN`, apenas na branch `main`
- [ ] Validar execução verde no Actions + print da run para o vídeo STAR
- [ ] Adicionar badge do workflow no topo do README

---

### FASE 6 — DAG Airflow de treino/retreino do modelo
**Responsável:** Dev C (Matheus Ferreira) · **Corresponde à Etapa 2 do PDF**

- **Objetivo:** DAG que simula o ciclo de retreino: ingestão de dados → treino → salvamento do modelo.
- **Entregável:** `dags/retrain_triagem_dag.py` + print da DAG executada com sucesso no Airflow UI.
- **Depende de:** FASE 1 (`src/train.py` precisa existir e ser chamável).
- **Critério de avaliação:** Orquestração (Airflow) = 15% da nota. O avaliador quer ver a DAG **rodando**, não só o arquivo `.py` — guarde o print do grafo todo verde.

**Checklist**
- [ ] Subir Airflow local (docker-compose oficial ou standalone) e validar acesso à UI
- [ ] Task 1 - `ingest`: ler o CSV de `data/raw/`, validar colunas e salvar em `data/processed/`
- [ ] Task 2 - `train`: chamar `src/train.py` com os dados processados
- [ ] Task 3 - `save`: versionar o artefato em `models/` com timestamp e atualizar o `model.pkl` atual
- [ ] Encadear as tasks (`ingest >> train >> save`) com schedule definido e `catchup=False`
- [ ] Configurar `retries` e `retry_delay` nas tasks
- [ ] Executar a DAG end-to-end e salvar print do grafo verde em `docs/`

---

### FASE 7 — Stack de observabilidade: Prometheus + Grafana
**Responsável:** Dev B (Matheus Santos) · **Apoio:** Dev A (Alexandre) na instrumentação do código da API · **Corresponde à Etapa 3 do PDF**

- **Objetivo:** stack de observabilidade completa subindo com um único `docker compose up`.
- **Entregável:** `docker-compose.yml` + `prometheus.yml` + dashboard Grafana exportado em `monitoring/dashboard.json` + print do dashboard com dados.
- **Depende de:** FASE 3.
- **Critério de avaliação:** Monitoramento = 20% da nota, o maior peso junto com Modelagem. O PDF exige no mínimo 3 painéis; este checklist entrega 4.

**Checklist**
- [ ] Instrumentar a API com `prometheus_client` e expor `/metrics` (Counter de requisições + Histogram de latência + Counter de erros)
- [ ] Adicionar label por classe predita nas métricas (permite painel de distribuição de urgência)
- [ ] `docker-compose.yml` com 3 serviços: `api`, `prometheus` e `grafana` na mesma rede
- [ ] `monitoring/prometheus.yml` com `scrape_config` apontando para `api:8000/metrics`
- [ ] Provisionar datasource Prometheus no Grafana via arquivo (sem configurar na mão)
- [ ] Dashboard com 4 painéis: total de requisições, latência p95, taxa de erro e distribuição das classes
- [ ] Gerar carga com `scripts/benchmark.py` e confirmar os gráficos populando
- [ ] Exportar o JSON do dashboard para `monitoring/dashboard.json` + print para a entrega

---

### FASE 8 — Otimização de latência: export ONNX e comparativo
**Responsável:** Dev C (Matheus Ferreira) · **Apoio:** Dev B (Matheus Santos) na medição dentro do container · **Corresponde à Etapa 4 do PDF**

- **Objetivo:** aplicar uma técnica de otimização vista em aula e comprovar ganho de latência com números.
- **Entregável:** `models/model.onnx` + tabela comparativa (sklearn vs ONNX) em `docs/latencia_comparativo.md`.
- **Depende de:** FASE 1 (modelo treinado) e FASE 3 (baseline medido).
- **Critério de avaliação:** Modelagem e Otimização = 20% da nota. O PDF pede "melhoria de latência demonstrada" — sem o comparativo numérico a nota cai, mesmo com o ONNX funcionando.

**Checklist**
- [ ] Instalar `skl2onnx` + `onnxruntime` e fixar as versões no `requirements`
- [ ] Converter o pipeline completo (TF-IDF + classificador) para ONNX em `src/export_onnx.py`
- [ ] Validar paridade de predição: mesmas N amostras devem dar a mesma classe no `.pkl` e no `.onnx`
- [ ] Adaptar a API para carregar o runtime ONNX via variável de ambiente (fallback para `.pkl`)
- [ ] Rodar o mesmo benchmark da FASE 3 no modelo ONNX (mesma máquina, mesmo N)
- [ ] Montar tabela comparativa: p50/p95/p99, throughput, tamanho do artefato e % de ganho
- [ ] Commitar `docs/latencia_comparativo.md` com gráfico ou tabela e conclusão

---

### FASE 9 — Deploy do serviço de inferência em produção (cloud)
**Responsável:** Dev B (Matheus Santos) · **Bônus / Tema central do PDF**

- **Objetivo:** colocar o modelo em produção de fato, com URL pública acessível para a banca testar.
- **Entregável:** URL pública respondendo em `/docs` e `/predict` + seção de deploy no README com o passo a passo.
- **Depende de:** FASE 5 (imagem publicada no GHCR) e FASE 7 (compose validado).
- **Nota:** o tema central da fase é "Deploy de Modelo em Produção". Mesmo sendo bônus na grade de critérios, é o que sustenta a narrativa do vídeo STAR e diferencia a entrega.
- **Sugestão de serviço** (escolher 1, o mais barato/rápido): Azure Container Apps, AWS App Runner, Google Cloud Run ou Render. Todos aceitam imagem de container direto.

**Checklist**
- [ ] Escolher o serviço de deploy e confirmar que bate com a decisão arquitetural escrita na FASE 2
- [ ] Provisionar o recurso e apontar para a imagem publicada no GHCR
- [ ] Configurar variáveis de ambiente e secrets no serviço (nada hardcoded no repo)
- [ ] Definir limites de CPU/memória e healthcheck apontando para `/health`
- [ ] Smoke test na URL pública: `/health`, `/docs` e um `POST /predict` real
- [ ] Medir latência em produção e comparar com a medição local (registrar a diferença de rede)
- [ ] Documentar no README a URL pública + passo a passo do deploy e do rollback

---

### FASE 10 — Consolidação final: README e vídeo STAR
**Responsável:** Dev A (Alexandre Araújo)

> Referenciada nos entregáveis finais, embora não tenha checklist detalhado no board original. Recomenda-se consolidar aqui:
- [ ] Revisão final do README (arquitetura, execução, resultados, link do vídeo)
- [ ] Roteirização segundo o método STAR (Situation, Task, Action, Result)
- [ ] Gravação e publicação do vídeo (≤ 5 minutos)
- [ ] Teste do link do vídeo em aba anônima

---

## 5. Mapeamento para os Entregáveis oficiais do PDF

### 📦 Entregável 1 — API funcional em Docker + decisão arquitetural no README
**[Etapa 1 do PDF]** Decisão Arquitetural e API Inicial — *Disciplina: Deploy em Nuvem*
**Cobre:** FASE 0, FASE 2 e FASE 3

**Critérios de aceite:**
- API FastAPI respondendo `/predict` dentro do container
- Análise batch vs real-time escrita no README com justificativa do provedor
- Baseline de latência local medido e documentado

**Peso indireto:** parte dos 15% de Documentação.

---

### 📦 Entregável 2 — Workflow GitHub Actions + DAG Airflow funcionando
**[Etapa 2 do PDF]** CI/CD e Pipeline Automatizado — *Disciplinas: CI/CD e Pipeline de Treino*
**Cobre:** FASE 4, FASE 5 e FASE 6

**Critérios de aceite:**
- Workflow YAML no repositório executando lint e pytest automaticamente no push
- Mínimo de 2 automações funcionando (requisito obrigatório)
- Arquivo `.py` da DAG Airflow + evidência de execução bem-sucedida

**Peso direto:** CI/CD 15% + Orquestração 15% = **30%**

---

### 📦 Entregável 3 — Stack completa via Docker Compose + dashboard Grafana
**[Etapa 3 do PDF]** Monitoramento e Observabilidade — *Disciplinas: Monitoração de Performance e Serviços*
**Cobre:** FASE 7

**Critérios de aceite:**
- `docker compose up` sobe API + Prometheus + Grafana juntos, sem passo manual
- Dashboard com no mínimo 3 painéis exibindo dados reais
- JSON do dashboard versionado + print anexado

**Peso direto:** Monitoramento = **20%** (maior peso da grade, junto com Modelagem).

---

### 📦 Entregável 4 — Modelo otimizado + comparativo de latência + vídeo STAR
**[Etapa 4 do PDF]** Otimização de Latência e Entrega — *Disciplina: Latência em Modelos Não Estruturados*
**Cobre:** FASE 1, FASE 8, FASE 9 e FASE 10

**Critérios de aceite:**
- Classificador treinado com métricas documentadas
- Técnica de otimização aplicada (ONNX ou quantização) e funcionando
- Comparativo numérico original vs otimizado
- Vídeo STAR de até 5 minutos publicado e linkado

**Peso direto:** Modelagem e Otimização 20% + Vídeo STAR 15% = **35%**

---

## 6. Checklist final antes de submeter

- [ ] Todos os requisitos obrigatórios do PDF marcados
- [ ] Repositório público e acessível
- [ ] Link do vídeo testado em aba anônima