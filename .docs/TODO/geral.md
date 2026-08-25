# TODO — Geral do Time

> Este arquivo cobre apenas: (a) o setup inicial que precede qualquer dev, (b) tarefas que dependem de mais de um dev ou exigem alinhamento do time, e (c) o checklist final de submissão.
> As tarefas individuais de cada fase estão nos TODOs de cada dev — **não são duplicadas aqui**, apenas referenciadas.

---

## 1. Setup inicial (antes de qualquer dev começar)

> Responsável: **Dev B (Matheus Santos)** — ver checklist completo em `TODO/dev-b-matheus-santos.md → FASE 0`

- [ ] **[Dev B]** FASE 0 concluída: repositório criado, estrutura de pastas, `requirements.txt`, `CONTRIBUTING.md` e README esqueleto no ar
- [ ] **[Dev B]** Dev A e Dev C adicionados como colaboradores com permissão de `Write`
- [ ] **[Dev B]** Comunicar ao Dev A e Dev C via canal do time que podem criar suas branches

**Nenhuma outra fase pode começar antes deste item estar marcado.**

---

## 2. Alinhamento do time — decisões a tomar antes de começar

> Estas decisões impactam múltiplas fases e múltiplos devs. Resolver em reunião ou sincronia antes do início.

### 2.1 Provedor de nuvem para deploy (bloqueia FASE 2 e FASE 9)

- [ ] Definir qual serviço de deploy será usado (escolher 1):
  - `[ ]` Google Cloud Run
  - `[ ]` Azure Container Apps
  - `[ ]` AWS App Runner
  - `[ ]` Render
- [ ] **Dev A** usa o serviço escolhido na análise arquitetural da FASE 2 (README)
- [ ] **Dev B** usa o mesmo serviço na execução real da FASE 9

### 2.2 Responsabilidade pela instrumentação da API com `prometheus_client` (bloqueia FASE 7)

> O `plan.md` define FASE 7 como responsabilidade do Dev B com "apoio do Dev A". Definir quem escreve o quê:

- [ ] Decidir: Dev A adiciona `prometheus_client` em `app/main.py` (durante FASE 2 ou FASE 4), ou Dev B adiciona ao iniciar a FASE 7?
- [ ] Decisão registrada aqui: ______________________________________
- [ ] Dev responsável notificado

### 2.3 Classificador a usar no modelo (bloqueia FASE 1 e FASE 8)

> `skl2onnx` tem compatibilidade variável com diferentes classificadores. Confirmar antes do Dev C escolher:

- [ ] `LogisticRegression` — compatível com `skl2onnx` e `predict_proba` nativo ✅ (recomendado)
- [ ] `LinearSVC` — requer `CalibratedClassifierCV` para `predict_proba` e pode ter problemas no export ONNX ⚠️
- [ ] `RandomForestClassifier` — compatível, mas mais lento ⚠️
- [ ] Decisão registrada aqui: ______________________________________

### 2.4 Airflow: instalação local vs. arquivo no repositório (bloqueia FASE 6)

- [ ] Decidir se o repositório terá um `docker-compose.airflow.yml` dedicado para facilitar a reprodução pela banca
- [ ] Decisão registrada aqui: ______________________________________

### 2.5 Datas de entrega por fase

> O `plan.md` deixa as datas em aberto. Preencher abaixo:

| Fase | Responsável | Data alvo de conclusão |
|---|---|---|
| FASE 0 | Dev B | ___/___/___ |
| FASE 1 | Dev C | ___/___/___ |
| FASE 2 | Dev A | ___/___/___ |
| FASE 3 | Dev B | ___/___/___ |
| FASE 4 | Dev A | ___/___/___ |
| FASE 5 | Dev B | ___/___/___ |
| FASE 6 | Dev C | ___/___/___ |
| FASE 7 | Dev B | ___/___/___ |
| FASE 8 | Dev C | ___/___/___ |
| FASE 9 | Dev B | ___/___/___ |
| FASE 10 | Dev A | ___/___/___ |

- [ ] Tabela de datas preenchida e comunicada ao time
- [ ] Data limite de submissão do Tech Challenge confirmada com a instituição: ___/___/___

### 2.6 Configurações do board (pendências manuais do `plan.md`)

- [ ] Atribuir os membros nos cards do board (arrastar avatares)
- [ ] Renomear labels padrão para `FASE 0..10`, `TIME` e `FINALIZADO`

---

## 3. Pontos de sincronização entre fases (checkpoints de alinhamento)

> Momentos em que dois ou mais devs precisam sincronizar antes de a próxima fase começar.

### Checkpoint A — após FASE 0 e antes de FASE 1 e FASE 2

**Quem participa:** Dev B (entregou FASE 0) + Dev A e Dev C (vão começar)
- [ ] Dev B confirmou: repositório público, estrutura criada, `requirements.txt` commitado
- [ ] Dev A confirmou: consegue criar branch `fase-2-api-fastapi` e acessar o repositório
- [ ] Dev C confirmou: consegue criar branch `fase-1-dataset-modelo-baseline` e acessar o repositório

### Checkpoint B — após FASE 1 e FASE 2 e antes de FASE 3

**Quem participa:** Dev C (entregou FASE 1) + Dev A (entregou FASE 2) + Dev B (vai começar FASE 3)
- [ ] Dev C confirmou: `models/model.pkl` gerado e disponível localmente; `src/train.py` funciona via CLI
- [ ] Dev A confirmou: `app/main.py` com `/predict` e `/health` funcionando; PR mergeado em `main`
- [ ] Dev B confirma que pode prosseguir com o Dockerfile

### Checkpoint C — após FASE 4 e antes de FASE 5

**Quem participa:** Dev A (entregou FASE 4) + Dev B (vai começar FASE 5)
- [ ] Dev A confirmou: `pytest -v` passa 100% e `ruff check app/ src/` retorna zero erros
- [ ] Dev A comunicou a Dev B os comandos exatos a usar no workflow:
  - Lint: `ruff check app/ src/`
  - Testes: `pytest -v`

### Checkpoint D — antes de FASE 7 (instrumentação da API)

**Quem participa:** Dev A + Dev B
- [ ] Decisão 2.2 foi tomada (quem escreve a instrumentação prometheus)
- [ ] `/metrics` está exposto e retornando dados no formato Prometheus antes de Dev B configurar o Prometheus

### Checkpoint E — após FASE 3 e antes de FASE 8 (benchmark comparativo)

**Quem participa:** Dev C (vai executar FASE 8) + Dev B (apoiará a medição dentro do container)
- [ ] `docs/latencia_baseline.md` com tabela p50/p95/p99 do modelo sklearn disponível (FASE 3)
- [ ] Dev B e Dev C combinaram data e máquina para rodar o benchmark ONNX nas mesmas condições

### Checkpoint F — revisão final antes de FASE 10

**Quem participa:** todos os 3 devs
- [ ] FASE 8 concluída: tabela comparativa sklearn vs ONNX pronta
- [ ] FASE 9 concluída: URL pública funcionando
- [ ] Dev A pode iniciar a consolidação do README e o vídeo STAR

---

## 4. Revisão dos entregáveis oficiais do PDF

> Um membro do time (sugestão: Dev A) deve revisar cada entregável antes da submissão final. Marcar quando cada um estiver aceito pelo time.

### 📦 Entregável 1 — API funcional em Docker + decisão arquitetural no README
**Cobre:** FASE 0 (Dev B) + FASE 2 (Dev A) + FASE 3 (Dev B)
**Critérios de aceite:**
- [ ] `POST /predict` dentro do container retorna `{classe, confianca, tempo_ms}`
- [ ] `GET /health` retorna HTTP 200 dentro do container
- [ ] Seção "Decisão Arquitetural" no README com análise batch vs real-time e justificativa do provedor
- [ ] `docs/latencia_baseline.md` com tabela p50/p95/p99 commitada

**Revisado e aceito por:** _____________ em ___/___/___

---

### 📦 Entregável 2 — Workflow GitHub Actions + DAG Airflow funcionando
**Cobre:** FASE 4 (Dev A) + FASE 5 (Dev B) + FASE 6 (Dev C)
**Critérios de aceite:**
- [ ] `.github/workflows/ci.yml` com mínimo 2 jobs automatizados (lint + test) rodando verde
- [ ] Badge de status no README apontando para o workflow
- [ ] `dags/retrain_triagem_dag.py` presente no repositório
- [ ] Print do grafo Airflow com todas as tasks verdes em `docs/dag_execucao.png`

**Revisado e aceito por:** _____________ em ___/___/___

---

### 📦 Entregável 3 — Stack completa via Docker Compose + dashboard Grafana
**Cobre:** FASE 7 (Dev B com apoio Dev A)
**Critérios de aceite:**
- [ ] `docker compose up` sobe API + Prometheus + Grafana sem passo manual adicional
- [ ] Dashboard com mínimo 3 painéis (o plano entrega 4) exibindo dados reais
- [ ] `monitoring/dashboard.json` versionado no repositório
- [ ] Print do dashboard com dados visíveis em `docs/`

**Revisado e aceito por:** _____________ em ___/___/___

---

### 📦 Entregável 4 — Modelo otimizado + comparativo de latência + vídeo STAR
**Cobre:** FASE 1 (Dev C) + FASE 8 (Dev C) + FASE 9 (Dev B) + FASE 10 (Dev A)
**Critérios de aceite:**
- [ ] Classificador treinado com métricas (accuracy e F1) documentadas
- [ ] `src/export_onnx.py` funcionando e `models/model.onnx` gerado sem erro
- [ ] `docs/latencia_comparativo.md` com tabela comparativa sklearn vs ONNX
- [ ] Vídeo STAR de até 5 minutos publicado e linkado no README
- [ ] Link do vídeo testado em aba anônima

**Revisado e aceito por:** _____________ em ___/___/___

---

## 5. Checklist final de submissão

> Executar na ordem abaixo apenas quando todos os 4 entregáveis estiverem aceitos.

### Repositório
- [ ] Todos os PRs das fases mergeados em `main`
- [ ] Repositório definido como **público** nas configurações do GitHub
- [ ] Acessar o repositório em aba anônima e confirmar que está visível sem login
- [ ] Confirmar que nenhum arquivo com segredos (`.env`, chaves, senhas) foi commitado:
  ```bash
  git log --all --full-history -- "*.env" "*.key" "*secret*"
  ```

### Código e execução
- [ ] `docker compose up` sobe a stack completa do zero (testar em máquina limpa ou pasta nova)
- [ ] `pytest -v` passa 100% no repositório clonado do zero
- [ ] `ruff check app/ src/` retorna zero erros
- [ ] Workflow CI/CD está verde na branch `main` no momento da submissão

### Documentação
- [ ] README com todas as seções preenchidas (nenhuma seção vazia)
- [ ] URL pública na seção "Deploy em Produção" do README
- [ ] Todos os comandos do README testados copiando e colando em terminal limpo
- [ ] `docs/latencia_baseline.md` e `docs/latencia_comparativo.md` presentes
- [ ] `docs/dag_execucao.png` (print da DAG verde) presente

### Vídeo
- [ ] Vídeo com duração ≤ 5 minutos
- [ ] Método STAR respeitado: Situation → Task → Action → Result
- [ ] Link do vídeo inserido no README
- [ ] Link testado em aba anônima — acesso sem login

### Submissão
- [ ] Confirmar o link/formulário de submissão com a instituição
- [ ] Submeter o link do repositório GitHub no portal indicado
- [ ] Confirmar recebimento da submissão

---

## ⚠️ Pontos em aberto — Time

- [ ] **Plataforma do vídeo:** o PDF não especifica onde publicar o vídeo. Confirmar com a instituição se YouTube (não listado) é aceito ou se há portal específico.
- [ ] **Dataset:** confirmar com Dev C qual dataset será usado e se o mapeamento para as 3 classes é viável antes de começar a FASE 1.
- [ ] **Airflow na entrega:** o PDF pede evidência de execução da DAG (print do grafo verde), mas não especifica se a banca vai executar o Airflow. Confirmar se é necessário incluir um `docker-compose.airflow.yml` no repositório para reprodutibilidade.
- [ ] **Limite de tamanho do texto na API:** não especificado no PDF. Decisão atual (Dev A): 5.000 caracteres. Validar se faz sentido para o contexto clínico.
